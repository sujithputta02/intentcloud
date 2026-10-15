"""
Vision and Visual Semantic Understanding Service for IntentCloud.
Provides:
1. Native Apple Vision Neural Engine OCR (blazing fast text/code extraction from images/diagrams).
2. Local Vision-Language Model (VLM) scene captioning via Ollama (Moondream/LLaVA).
3. Dominant pixel color extraction and structured design swatch pairing.
4. Fallback Tesseract / Pillow metadata extraction.
"""

import base64
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import urllib.request
import urllib.error

logger = logging.getLogger("intentcloud.vision")

BASE_DIR = Path(__file__).resolve().parent.parent
APPLE_VISION_BIN = BASE_DIR / "bin" / "apple_vision_ocr"
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
VLM_MODEL_NAME = os.getenv("VLM_MODEL_NAME", "moondream")


def run_apple_vision_ocr(image_path: str) -> str:
    """
    Run native Apple Vision Neural Engine OCR on macOS.
    Extracts text, code snippets, and diagram labels in ~20ms.
    """
    if not APPLE_VISION_BIN.exists() or not os.access(APPLE_VISION_BIN, os.X_OK):
        return ""
    
    try:
        proc = subprocess.run(
            [str(APPLE_VISION_BIN), str(Path(image_path).resolve())],
            capture_output=True,
            text=True,
            timeout=8
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception as e:
        logger.debug(f"[Vision] Apple Vision OCR error: {e}")
    return ""


def run_tesseract_ocr(image_path: str) -> str:
    """
    Run Tesseract OCR via pytesseract or system tesseract CLI.
    Provides fast, cross-platform OCR on Linux (Raspberry Pi ARM64) and macOS.
    """
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        raw_text = pytesseract.image_to_string(img)
        text = str(raw_text).strip() if raw_text else ""
        if len(text) > 3:
            logger.info(f"[Vision] Pytesseract extracted {len(text)} chars from {Path(image_path).name}")
            return text
    except Exception as e:
        logger.debug(f"[Vision] pytesseract module error: {e}")

    try:
        proc = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", "eng"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if proc.returncode == 0 and proc.stdout.strip():
            logger.info(f"[Vision] CLI tesseract extracted {len(proc.stdout)} chars from {Path(image_path).name}")
            return proc.stdout.strip()
    except Exception as e:
        logger.debug(f"[Vision] CLI tesseract error: {e}")

    return ""


def run_vlm_captioning(image_path: str, prompt: Optional[str] = None) -> str:
    """
    Query local Ollama Vision-Language Model (Moondream/LLaVA).
    Returns rich semantic description of diagrams, charts, UI flows, and scenes.
    """
    if not prompt:
        prompt = (
            "What is this image about? Describe any visible text, diagrams, presentation slides, "
            "color swatches or palettes, technical charts, or user interface elements clearly in 2 to 3 sentences."
        )

    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": VLM_MODEL_NAME,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 180,
            }
        }

        req = urllib.request.Request(
            f"{OLLAMA_API_URL}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                result = json.loads(response.read().decode("utf-8"))
                caption = result.get("response", "").strip()
                # Ignore object detection bounding box outputs e.g. "ids: [0.12, 0.6...]"
                if caption and not caption.lower().startswith("ids:") and not caption.startswith("["):
                    logger.info(f"[Vision] VLM generated description using {VLM_MODEL_NAME} ({len(caption)} chars)")
                    return caption
    except urllib.error.URLError as e:
        logger.debug(f"[Vision] Ollama VLM unavailable: {e}")
    except Exception as e:
        logger.debug(f"[Vision] VLM inference failed: {e}")

    return ""


def extract_dominant_colors(image_path: str, max_colors: int = 8) -> List[Dict[str, Any]]:
    """
    Extract prominent palette colors directly from the image pixels via Pillow quantization.
    Returns list of dicts: [{"hex": "#590F1E", "rgb": [89, 15, 30], "count": 12000, "percentage": 14.2}]
    """
    try:
        from PIL import Image
        with Image.open(image_path) as im:
            rgb_im = im.convert("RGB")
            # Downsample for microsecond performance
            rgb_im.thumbnail((240, 240))
            total_pixels = rgb_im.width * rgb_im.height
            if total_pixels <= 0:
                return []

            quantized = rgb_im.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
            colors = quantized.getcolors(maxcolors=256) or []
            colors.sort(key=lambda x: x[0], reverse=True)

            results = []
            for item in colors:
                if not isinstance(item, (tuple, list)) or len(item) != 2:
                    continue
                count, color_val = item[0], item[1]
                if isinstance(color_val, (tuple, list)) and len(color_val) >= 3:
                    r, g, b = color_val[0], color_val[1], color_val[2]
                elif isinstance(color_val, (int, float)):
                    r = g = b = int(color_val)
                else:
                    continue
                pct = round((count / total_pixels) * 100, 1)
                results.append({
                    "hex": f"#{r:02X}{g:02X}{b:02X}",
                    "rgb": [r, g, b],
                    "count": count,
                    "percentage": pct
                })
            return results
    except Exception as e:
        logger.debug(f"[Vision] Dominant color extraction error: {e}")
        return []


def _fix_ocr_hex(raw_str: str) -> Optional[str]:
    """Normalize common OCR character confusions in 6-digit hex codes."""
    has_hash = "#" in raw_str or raw_str.startswith("It") or raw_str.startswith("lt")
    clean = raw_str.replace("It", "#").replace("lt", "#").strip(",;:()[]{}").lstrip("#").upper()
    replacements = {"O": "0", "I": "1", "L": "1", "&": "8", "S": "5", "Z": "2"}
    fixed = "".join(replacements.get(c, c) for c in clean)
    if len(fixed) == 6 and re.match(r"^[0-9A-F]{6}$", fixed):
        # Require an explicit # or pre-existing digit so standard English words like EDABLE are never matched as hex
        if not has_hash and not re.search(r"\d", clean):
            return None
        return f"#{fixed}"
    return None


def extract_swatches_and_palette(image_path: str, ocr_text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Pair color names and hex codes from OCR text, augmented with dominant pixel colors.
    Returns:
      swatches: [{"name": "CHERRY RED", "hex": "#590F1E", "rgb": [89, 15, 30]}, ...]
      dominant_hexes: ["#590F1E", "#0C4338", ...]
    """
    swatches: List[Dict[str, Any]] = []
    dominant_info = extract_dominant_colors(image_path, max_colors=10)
    dominant_hexes = [d["hex"] for d in dominant_info]

    lines = [l.strip() for l in ocr_text.splitlines() if l.strip()] if ocr_text else []
    
    # 1. Search for hex codes and potential color labels
    hex_candidates: List[str] = []
    name_candidates: List[str] = []

    color_words = {
        "red", "teal", "blue", "green", "beige", "black", "white", "yellow",
        "purple", "grey", "gray", "orange", "pink", "gold", "cyan", "magenta",
        "amber", "emerald", "navy", "crimson", "indigo", "pitch", "pure", "dark", "light"
    }

    ui_noise_words = {"home", "insert", "draw", "view", "help", "share", "protected", "editing", "notes", "slide", "show"}

    for line in lines:
        # Check for hex pattern
        clean_line = line.replace("It", "#").replace("l#", "#")
        # Try explicit #HEX
        found_hex = False
        for token in clean_line.split():
            clean_token = token.strip(",;:()[]{}")
            if "#" in clean_token or len(clean_token) == 6:
                fixed = _fix_ocr_hex(clean_token)
                if fixed and fixed not in hex_candidates:
                    hex_candidates.append(fixed)
                    found_hex = True

        if not found_hex and len(line) <= 30:
            lower = line.lower()
            if not any(noise in lower for noise in ui_noise_words):
                if any(w in lower for w in color_words):
                    if line not in name_candidates:
                        name_candidates.append(line)

    # Smart alignment: if "black" or "white" appears in color names, align their canonical hexes
    if any("black" in n.lower() for n in name_candidates) and "#000000" not in hex_candidates:
        black_idx = [i for i, n in enumerate(name_candidates) if "black" in n.lower()][0]
        if black_idx <= len(hex_candidates):
            hex_candidates.insert(black_idx, "#000000")
        else:
            hex_candidates.append("#000000")

    if any("white" in n.lower() for n in name_candidates) and "#FFFFFF" not in hex_candidates:
        white_idx = [i for i, n in enumerate(name_candidates) if "white" in n.lower()][0]
        if white_idx <= len(hex_candidates):
            hex_candidates.insert(white_idx, "#FFFFFF")
        else:
            hex_candidates.append("#FFFFFF")

    # Pair names and hex codes if both found
    paired_count = min(len(name_candidates), len(hex_candidates))
    for i in range(paired_count):
        hex_val = hex_candidates[i]
        # Calculate approximate RGB
        try:
            r = int(hex_val[1:3], 16)
            g = int(hex_val[3:5], 16)
            b = int(hex_val[5:7], 16)
            rgb = [r, g, b]
        except Exception:
            rgb = [0, 0, 0]
        swatches.append({
            "name": name_candidates[i].title(),
            "hex": hex_val,
            "rgb": rgb
        })

    # Add remaining hexes without explicit names
    for h in hex_candidates[paired_count:]:
        try:
            rgb = [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)]
        except Exception:
            rgb = [0, 0, 0]
        swatches.append({
            "name": f"Color {h}",
            "hex": h,
            "rgb": rgb
        })

    # If no swatches detected via OCR but dominant colors found, offer top dominant colors
    if not swatches and dominant_info:
        for d in dominant_info[:6]:
            swatches.append({
                "name": f"Palette {d['hex']}",
                "hex": d["hex"],
                "rgb": d["rgb"]
            })

    return swatches, dominant_hexes


def analyze_image_full(file_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive visual semantic analysis returning structured metadata,
    deep scene descriptions, OCR labels, and color swatch palettes.
    """
    p = Path(file_path)
    effective_name = original_filename or p.name

    # If filename is a raw UUID, look up original filename from metadata.json
    if re.match(r"^[0-9a-fA-F-]{36}(\.[a-zA-Z0-9]+)?$", effective_name):
        try:
            meta_path = BASE_DIR / "uploads" / "metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta_dict = json.load(mf)
                file_uuid = Path(effective_name).stem
                if file_uuid in meta_dict and "filename" in meta_dict[file_uuid]:
                    effective_name = meta_dict[file_uuid]["filename"]
        except Exception:
            pass

    ext = Path(effective_name).suffix.lower() or p.suffix.lower()

    # Image format and dimensions via Pillow
    width, height = 0, 0
    format_name = ext.replace(".", "").upper() or "IMAGE"
    color_mode = "RGB"
    try:
        from PIL import Image
        with Image.open(file_path) as im:
            width, height = im.size
            format_name = im.format or format_name
            color_mode = im.mode
    except Exception as e:
        logger.debug(f"[Vision] Pillow metadata error: {e}")

    # Clean filename of timestamps and camera noise
    stem = Path(effective_name).stem
    stem_clean = re.sub(r"^(WhatsApp\s+Image|Screenshot|Screen\s*Shot)\s*", "", stem, flags=re.IGNORECASE)
    stem_clean = re.sub(r"\d{4}[-_]\d{2}[-_]\d{2}.*", "", stem_clean).strip(" -_")
    stem_keywords = stem_clean.replace("_", " ").replace("-", " ").strip()
    if not stem_keywords:
        stem_keywords = "visual document image"

    # 1. OCR text extraction
    ocr_text = run_apple_vision_ocr(file_path)
    if not ocr_text or len(ocr_text.strip()) < 15:
        tess_text = run_tesseract_ocr(file_path)
        if tess_text:
            ocr_text = (ocr_text + "\n" + tess_text).strip() if ocr_text else tess_text

    # 2. Extract swatches and dominant colors
    swatches, dominant_hexes = extract_swatches_and_palette(file_path, ocr_text)

    # 3. Clean OCR text of application viewer boilerplate
    noise_phrases = [
        "protected view", "be careful-files from the internet", "it's safer to stay in protected view",
        "tell me what you want to do", "tell rne what you want to do", "enable editing", "autosave", "saved to this pc",
        "english (united states)", "notes", "slide show", "record review", "transitions", "animations"
    ]
    cleaned_ocr_lines = []
    if ocr_text:
        for line in ocr_text.splitlines():
            sline = line.strip()
            if sline and not any(n in sline.lower() for n in noise_phrases):
                cleaned_ocr_lines.append(sline)
    clean_ocr = "\n".join(cleaned_ocr_lines)

    # 4. Local VLM scene understanding
    vlm_caption = run_vlm_captioning(file_path)

    # 5. Synthesize visual concepts and semantic tags
    visual_tags: List[str] = ["Image Asset"]
    visual_concepts: List[str] = []

    color_terms = ["color", "colour", "palette", "swatch", "brand", "visual system", "minimal structure"]
    is_color_palette = bool(swatches) or any(k in ocr_text.lower() for k in color_terms)
    if is_color_palette:
        visual_tags.extend(["Color Palette", "Brand Design", "Visual System", "Color Swatches"])
        swatch_summary = ", ".join([f"{s['name']}: {s['hex']}" for s in swatches[:6]])
        visual_concepts.append(
            f"[Visual Concept: Branding Color Palette & Design System]\n"
            f"Identity: Brand Color Palette, Hex Color Swatches, Minimal Structure, Maximum Personality, Visual System Design. "
            f"Active Swatches: {swatch_summary}."
        )

    slide_terms = ["slide", "presentation", "deck", "pptx", "visual system", "keynote"]
    if any(k in ocr_text.lower() for k in slide_terms) or any(k in stem_keywords.lower() for k in slide_terms):
        visual_tags.extend(["Presentation Slide", "Slide Deck"])
        visual_concepts.append(
            "[Visual Concept: Presentation Slide & Brand Deck]\n"
            "Slide Deck: Keynote / PowerPoint Presentation Slide, Brand Guidelines, Minimal Structure."
        )

    ops_terms = ["servicenow", "dashboard", "incident", "workspace", "commander", "operations", "outage", "ticket", "sla"]
    if any(k in ocr_text.lower() for k in ops_terms):
        visual_tags.extend(["Dashboard", "Operations Workspace", "ServiceNow"])
        visual_concepts.append(
            "[Visual Concept: Enterprise Operations Dashboard & Incident Management Workspace]\n"
            "System: ServiceNow Service Operations Workspace, Critical Actions, Major Incidents."
        )

    # Build human-readable scene description
    if vlm_caption:
        scene_description = vlm_caption
    elif is_color_palette and swatches:
        names_str = ", ".join([s["name"] for s in swatches])
        scene_description = (
            f"Design presentation slide displaying a clean brand color palette grid with {len(swatches)} distinct swatches: "
            f"{names_str}. Includes hex color specifications and visual system typography."
        )
    elif clean_ocr:
        first_few = ". ".join(cleaned_ocr_lines[:3])
        scene_description = f"Visual graphic containing embedded text: {first_few}."
    else:
        scene_description = f"{format_name} visual document ({width}x{height} pixels)."

    # 6. Compose full semantics text for search embeddings
    sections = [
        f"[Image Document / Photo: {effective_name}]",
        f"Subject / Filename Keywords: {stem_keywords}",
    ]
    if visual_concepts:
        sections.append("\n" + "\n".join(visual_concepts))
    if scene_description:
        sections.append(f"\n--- DETAILED VISUAL SCENE DESCRIPTION ---\n{scene_description}")
    if swatches:
        swatch_lines = [f"- {s['name']}: {s['hex']} (RGB {s.get('rgb')})" for s in swatches]
        sections.append("\n--- EXTRACTED COLOR SWATCHES & HEX CODES ---\n" + "\n".join(swatch_lines))
    if clean_ocr:
        sections.append(f"\n--- VISUAL TEXT & LABELS EXTRACTED FROM IMAGE (OCR) ---\n{clean_ocr}")
    sections.append(f"\nTechnical Metadata: {format_name}, {width}x{height} pixels, Color Mode: {color_mode}")

    full_semantics = "\n".join(sections)

    return {
        "filename": effective_name,
        "scene_description": scene_description,
        "ocr_text": clean_ocr,
        "swatches": swatches,
        "dominant_colors": dominant_hexes,
        "visual_tags": list(dict.fromkeys(visual_tags)),
        "width": width,
        "height": height,
        "format": format_name,
        "color_mode": color_mode,
        "full_semantics": full_semantics,
    }


def extract_visual_semantics(file_path: str, original_filename: Optional[str] = None) -> str:
    """
    Backward-compatible extraction endpoint used by the ingestion pipeline.
    Returns full semantics string for embedding in Qdrant.
    """
    analysis = analyze_image_full(file_path, original_filename=original_filename)
    return analysis["full_semantics"]
