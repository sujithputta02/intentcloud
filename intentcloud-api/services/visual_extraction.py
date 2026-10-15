"""
IntentCloud - Visual Extraction & Diagram Detection Service
Extracts first-class visual evidence from PDFs and image documents:
1. Embedded raster image extraction (PyMuPDF xrefs)
2. Vector diagram & chart region detection (rendered high-DPI page crops)
3. Nearby caption & IEEE label extraction
4. High-accuracy OCR (Apple Vision / Tesseract)
5. Visual scene semantics & categorization
"""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from services.visual_evidence import VisualEvidence
from services.asset_store import save_visual_asset
from services.vision import run_apple_vision_ocr, run_tesseract_ocr, run_vlm_captioning

logger = logging.getLogger("intentcloud.visual_extraction")


def detect_diagram_regions(page_image: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Detect visual diagram, chart, or architecture schematic regions from a rendered page.
    Uses pixel density and bounding box heuristics to locate illustrations.
    Returns list of (x0, y0, x1, y1) bounding box rectangles.
    """
    width, height = page_image.size
    # Grayscale conversion
    gray = page_image.convert("L")
    
    # Simple bounding box discovery over grid buckets
    # If the page has non-white content in middle blocks
    # We look for continuous graphic blocks
    regions: List[Tuple[int, int, int, int]] = []
    try:
        # Downscale for fast contour-like scanning
        thumb = gray.resize((200, int(200 * height / width)), Image.Resampling.BOX)
        tw, th = thumb.size
        pixels = thumb.load()
        if pixels is None:
            return []

        # Find row density
        row_density = []
        for y in range(th):
            dark_count = 0
            for x in range(tw):
                val = pixels[x, y]
                px_val = val[0] if isinstance(val, tuple) else (val if isinstance(val, (int, float)) else 255)
                if px_val < 240:
                    dark_count += 1
            row_density.append(dark_count)

        # Look for contiguous dense regions (likely diagrams or charts)
        in_region = False
        start_y = 0
        min_density = tw * 0.15

        for y, dens in enumerate(row_density):
            if dens >= min_density and not in_region:
                in_region = True
                start_y = y
            elif dens < min_density and in_region:
                in_region = False
                region_h = y - start_y
                # If region spans between 12% and 75% of page height
                if 0.12 * th <= region_h <= 0.75 * th:
                    # Map back to full coordinates
                    full_y0 = int((start_y / th) * height)
                    full_y1 = int((y / th) * height)
                    # Add margin
                    full_x0 = int(0.05 * width)
                    full_x1 = int(0.95 * width)
                    regions.append((full_x0, full_y0, full_x1, full_y1))

        # Cap to top 2 diagram regions per page
        return regions[:2]
    except Exception as e:
        logger.debug(f"[DiagramDetect] Region detection error: {e}")
        return []


def find_surrounding_caption(page, bbox: List[float], max_distance_pt: float = 60.0) -> Tuple[str, str]:
    """
    Scan page text blocks near the visual bounding box to identify figure label and caption.
    Returns (figure_label, caption_text).
    """
    detected_label = ""
    caption_text = ""

    try:
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        # Look for blocks within vertical proximity of the figure
        # Bbox is [x0, y0, x1, y1]
        fig_y0 = bbox[1] if len(bbox) >= 4 else 0
        fig_y1 = bbox[3] if len(bbox) >= 4 else 792

        candidate_texts = []
        for block in blocks:
            if block.get("type") == 0:  # Text block
                b_bbox = block.get("bbox", [0, 0, 0, 0])
                b_y0, b_y1 = b_bbox[1], b_bbox[3]

                # Check if block is immediately above (within 40pt) or below (within 60pt)
                dist_below = b_y0 - fig_y1
                dist_above = fig_y0 - b_y1

                if (-10 <= dist_below <= max_distance_pt) or (-10 <= dist_above <= 40):
                    lines = block.get("lines", [])
                    block_str = " ".join(
                        "".join(span.get("text", "") for span in line.get("spans", ""))
                        for line in lines
                    ).strip()
                    if block_str:
                        candidate_texts.append((dist_below if dist_below >= 0 else dist_above, block_str))

        # Sort by distance to image
        candidate_texts.sort(key=lambda x: x[0])

        for _, text in candidate_texts:
            # Check for IEEE / academic figure patterns: Fig. 1, Figure 2, Chart 3, etc.
            match = re.search(r"\b(Fig(?:ure)?\.?\s*\d+[a-zA-Z]?|Chart\s*\d+|Table\s*\d+|Diagram\s*\d+)", text, re.IGNORECASE)
            if match:
                detected_label = match.group(1).title()
                caption_text = text
                break

        if not caption_text and candidate_texts:
            caption_text = candidate_texts[0][1][:180]

    except Exception as e:
        logger.debug(f"[Caption] Proximity caption extraction error: {e}")

    return detected_label, caption_text


def extract_visuals_from_pdf(
    pdf_path: str,
    file_id: str,
    filename: str,
    max_figures_total: int = 24
) -> List[VisualEvidence]:
    """
    Extract first-class VisualEvidence figures, diagrams, and charts from a PDF document.
    """
    if not fitz:
        return []

    visuals: List[VisualEvidence] = []
    seen_hashes: set[str] = set()
    fig_counter = 0

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.warning(f"[VisualExtraction] Could not open PDF {pdf_path}: {e}")
        return []

    try:
        for page_idx, page in enumerate(doc):
            if len(visuals) >= max_figures_total:
                break

            page_num = page_idx + 1
            page_images = page.get_images(full=True)

            # 1. Embedded Raster Images
            if page_images:
                for img_info in page_images[:6]:  # Up to 6 per page
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue

                        raw_bytes = base_image.get("image")
                        if not raw_bytes or not isinstance(raw_bytes, (bytes, bytearray)):
                            continue
                        img_bytes: bytes = bytes(raw_bytes)
                        img_ext = str(base_image.get("ext", "png"))
                        w = int(base_image.get("width", 0))
                        h = int(base_image.get("height", 0))

                        # Skip tiny icons / decorative artifacts
                        if w < 60 or h < 60 or len(img_bytes) < 1024:
                            continue

                        # Resolve bounding box on page
                        rects = page.get_image_rects(xref)
                        bbox = [round(rects[0].x0, 1), round(rects[0].y0, 1), round(rects[0].x1, 1), round(rects[0].y1, 1)] if rects else [0.0, 0.0, float(w), float(h)]

                        # Save and generate thumbnail
                        fig_counter += 1
                        asset_data = save_visual_asset(
                            image_bytes=img_bytes,
                            file_id=file_id,
                            page_num=page_num,
                            fig_index=fig_counter,
                            file_stem=Path(filename).stem,
                            extension=img_ext,
                        )
                        if not asset_data:
                            continue

                        img_hash = asset_data["image_hash"]
                        if img_hash in seen_hashes:
                            continue
                        seen_hashes.add(img_hash)

                        # Detect Caption and Fig label
                        detected_label, caption_text = find_surrounding_caption(page, bbox)
                        figure_label = detected_label or f"Fig. {fig_counter}"
                        if not caption_text:
                            caption_text = f"Embedded diagram on Page {page_num} of {filename}"

                        # Extract OCR text from image
                        img_path = asset_data["image_path"]
                        ocr_text = run_apple_vision_ocr(img_path)
                        if not ocr_text:
                            ocr_text = run_tesseract_ocr(img_path)

                        visual_item = VisualEvidence(
                            visual_id=f"vis_{img_hash[:12]}",
                            file_id=file_id,
                            filename=filename,
                            page_number=page_num,
                            bbox=bbox,
                            image_path=img_path,
                            thumbnail_path=asset_data["thumbnail_path"],
                            image_url=asset_data["image_url"],
                            thumbnail_url=asset_data["thumbnail_url"],
                            image_hash=img_hash,
                            visual_type="figure",
                            figure_label=figure_label,
                            caption=caption_text,
                            ocr_text=ocr_text if ocr_text else None,
                            extraction_method="embedded",
                            width=w,
                            height=h,
                            provenance=f"{filename}, p. {page_num}, {figure_label}",
                        )
                        visuals.append(visual_item)
                    except Exception as err:
                        logger.debug(f"[VisualExtraction] Error on xref {xref}: {err}")

            # 2. Vector Graphics & Non-Embedded Diagram Detection (e.g. vector charts/slides)
            # If no embedded images on this page, or page has drawing paths
            drawings = page.get_drawings()
            if len(page_images) == 0 and drawings and len(visuals) < max_figures_total:
                try:
                    # Render page at 2x resolution
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

                    regions = detect_diagram_regions(page_img)
                    for r_idx, (rx0, ry0, rx1, ry1) in enumerate(regions):
                        crop = page_img.crop((rx0, ry0, rx1, ry1))
                        crop_bytes_io = io.BytesIO()
                        crop.save(crop_bytes_io, format="PNG")
                        crop_bytes = crop_bytes_io.getvalue()

                        fig_counter += 1
                        asset_data = save_visual_asset(
                            image_bytes=crop_bytes,
                            file_id=file_id,
                            page_num=page_num,
                            fig_index=fig_counter,
                            file_stem=f"{Path(filename).stem}_vector",
                            extension="png",
                        )
                        if not asset_data:
                            continue

                        img_hash = asset_data["image_hash"]
                        if img_hash in seen_hashes:
                            continue
                        seen_hashes.add(img_hash)

                        # Normalize bbox to 1x page points
                        norm_bbox = [round(rx0 / 2.0, 1), round(ry0 / 2.0, 1), round(rx1 / 2.0, 1), round(ry1 / 2.0, 1)]
                        detected_label, caption_text = find_surrounding_caption(page, norm_bbox)
                        figure_label = detected_label or f"Diagram {fig_counter}"
                        if not caption_text:
                            caption_text = f"Vector diagram / architectural chart on Page {page_num} of {filename}"

                        img_path = asset_data["image_path"]
                        ocr_text = run_apple_vision_ocr(img_path)
                        if not ocr_text:
                            ocr_text = run_tesseract_ocr(img_path)

                        visual_item = VisualEvidence(
                            visual_id=f"vis_{img_hash[:12]}",
                            file_id=file_id,
                            filename=filename,
                            page_number=page_num,
                            bbox=norm_bbox,
                            image_path=img_path,
                            thumbnail_path=asset_data["thumbnail_path"],
                            image_url=asset_data["image_url"],
                            thumbnail_url=asset_data["thumbnail_url"],
                            image_hash=img_hash,
                            visual_type="diagram",
                            figure_label=figure_label,
                            caption=caption_text,
                            ocr_text=ocr_text if ocr_text else None,
                            extraction_method="rendered",
                            width=crop.width,
                            height=crop.height,
                            provenance=f"{filename}, p. {page_num}, {figure_label}",
                        )
                        visuals.append(visual_item)
                except Exception as vector_err:
                    logger.debug(f"[VisualExtraction] Vector diagram render error: {vector_err}")

    finally:
        try:
            doc.close()
        except Exception:
            pass

    logger.info(f"[VisualExtraction] Extracted {len(visuals)} visual evidence figures from {filename}")
    return visuals


def extract_visual_from_image_file(
    image_path: str,
    file_id: str,
    filename: str
) -> Optional[VisualEvidence]:
    """
    Extract first-class VisualEvidence from a standalone image document (PNG, JPG, WebP, etc.).
    """
    try:
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        ext = Path(image_path).suffix.lstrip(".").lower() or "png"
        asset_data = save_visual_asset(
            image_bytes=img_bytes,
            file_id=file_id,
            page_num=1,
            fig_index=1,
            file_stem=Path(filename).stem,
            extension=ext,
        )
        if not asset_data:
            return None

        # Run OCR
        ocr_text = run_apple_vision_ocr(image_path)
        if not ocr_text:
            ocr_text = run_tesseract_ocr(image_path)

        clean_stem = Path(filename).stem.replace("_", " ").replace("-", " ")
        caption = f"Visual Document / Image: {clean_stem}"

        return VisualEvidence(
            visual_id=f"vis_{asset_data['image_hash'][:12]}",
            file_id=file_id,
            filename=filename,
            page_number=1,
            bbox=[0.0, 0.0, float(asset_data["width"]), float(asset_data["height"])],
            image_path=asset_data["image_path"],
            thumbnail_path=asset_data["thumbnail_path"],
            image_url=asset_data["image_url"],
            thumbnail_url=asset_data["thumbnail_url"],
            image_hash=asset_data["image_hash"],
            visual_type="photo",
            figure_label="Fig. 1",
            caption=caption,
            ocr_text=ocr_text if ocr_text else None,
            extraction_method="embedded",
            width=asset_data["width"],
            height=asset_data["height"],
            provenance=f"{filename}, p. 1, Fig. 1",
        )
    except Exception as e:
        logger.warning(f"[VisualExtraction] Standalone image processing error for {filename}: {e}")
        return None
