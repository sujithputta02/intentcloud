"""
Phase 1: Multi-Format Text Extraction & Structural Document Tree Service
Extracts text from PDF, DOCX, TXT, Code files, and Photos/Images.
Builds a rich hierarchical Document Memory Tree with sections, tables, code blocks,
and page coordinates for deep document-level awareness.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import logging
import hashlib
import shutil

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FIGURES_DIR = BASE_DIR / "uploads" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


CODE_EXTENSIONS_MAP: Dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".jsx": "JavaScript React",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".json": "JSON",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".sql": "SQL",
    ".sh": "Shell Script",
    ".bash": "Bash Script",
    ".zsh": "Zsh Script",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".toml": "TOML",
    ".ini": "INI Config",
    ".env": "Environment Variables",
    ".r": "R",
    ".lua": "Lua",
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".tiff", ".tif", ".ico"
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".markdown", ".rtf", ".csv", ".tsv", ".log", ".tex"
}


def get_file_category(file_path_or_name: str) -> str:
    """Classify file into standard category: pdf, docx, presentation, txt, code, photo, document."""
    ext = Path(file_path_or_name).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".docx", ".doc"}:
        return "docx"
    if ext in {".pptx", ".ppt"}:
        return "presentation"
    if ext in IMAGE_EXTENSIONS:
        return "photo"
    if ext in CODE_EXTENSIONS_MAP:
        return "code"
    if ext == ".txt":
        return "txt"
    return "document"


# ---------------------------------------------------------------------------
# STRUCTURAL EXTRACTION & DOCUMENT TREE
# ---------------------------------------------------------------------------

def extract_document_tree(file_path: str, original_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract hierarchical Document Memory Tree from uploaded file.
    Preserves document structure: sections, headings, tables, blocks, and page refs.
    Treats embedded figures and images as first-class evidence with IEEE-style captions,
    provenance attribution, and persistent assets.
    """
    effective_name = original_filename or Path(file_path).name
    file_ext = Path(effective_name).suffix.lower() or Path(file_path).suffix.lower()
    category = get_file_category(effective_name)
    
    sections: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    figures: List[Dict[str, Any]] = []
    full_text = ""
    
    try:
        if file_ext == ".pdf":
            pdf_res = _extract_pdf_tree(file_path, effective_name)
            if len(pdf_res) == 4:
                sections, tables, full_text, figures = pdf_res
            else:
                sections, tables, full_text = pdf_res
        elif file_ext in {".docx", ".doc"}:
            sections, tables, full_text = _extract_docx_tree(file_path, effective_name)
        elif file_ext in {".pptx", ".ppt"}:
            sections, tables, full_text, figures = _extract_pptx_tree(file_path, effective_name)
        elif file_ext in CODE_EXTENSIONS_MAP:
            sections, full_text = _extract_code_tree(file_path, effective_name)
        elif file_ext in IMAGE_EXTENSIONS:
            img_res = _extract_image_tree(file_path, effective_name)
            if len(img_res) == 3:
                sections, full_text, figures = img_res
            else:
                sections, full_text = img_res
        else:
            sections, full_text = _extract_text_tree(file_path, effective_name)
    except Exception as exc:
        logger.error(f"[Extraction] Error building document tree for {effective_name}: {exc}")
        full_text = extract_txt(file_path) if Path(file_path).exists() else f"[Document: {effective_name}]"
        sections = [{
            "section_id": "sec_0",
            "title": effective_name,
            "section_path": [effective_name],
            "text": full_text,
            "page": 1
        }]

    if not sections and full_text:
        sections = [{
            "section_id": "sec_0",
            "title": effective_name,
            "section_path": [effective_name],
            "text": full_text,
            "page": 1
        }]

    return {
        "title": effective_name,
        "filename": effective_name,
        "extension": file_ext,
        "category": category,
        "full_text": full_text,
        "sections": sections,
        "tables": tables,
        "figures": figures,
        "metadata": {
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "section_count": len(sections),
            "table_count": len(tables),
            "figure_count": len(figures),
        }
    }



def extract_text_from_upload(file_path: str, original_filename: Optional[str] = None) -> str:
    """
    Backward-compatible text extraction endpoint.
    Returns full text string extracted from any document.
    """
    doc_tree = extract_document_tree(file_path, original_filename=original_filename)
    return doc_tree.get("full_text", "")


# ---------------------------------------------------------------------------
# INTERNAL FORMAT-SPECIFIC STRUCTURAL PARSERS
# ---------------------------------------------------------------------------

_HEADING_REGEX = re.compile(
    r"^(?:#{1,6}\s+|(?:\d+\.)+\d*\s+|[A-Z0-9_\-\s]{3,40}:|[A-Z\s]{4,35}$)(.+)?",
    re.MULTILINE
)

def _extract_text_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], str]:
    """Parse plain text, Markdown, or CSV into semantic sections."""
    text = extract_txt(file_path)
    if not text.strip():
        return [], ""

    lines = text.splitlines()
    sections: List[Dict[str, Any]] = []
    current_title = "Overview"
    current_lines: List[str] = []
    sec_idx = 0

    for line in lines:
        stripped = line.strip()
        # Detect section break on Markdown # or numbered sections or UPPERCASE headers
        is_heading = False
        header_text = ""
        if stripped.startswith("#"):
            is_heading = True
            header_text = stripped.lstrip("#").strip()
        elif re.match(r"^(?:Section\s+\d+|Chapter\s+\d+|\d+\.\d+|\d+\.)\s+", stripped, re.IGNORECASE):
            is_heading = True
            header_text = stripped
        elif len(stripped) > 3 and len(stripped) < 40 and stripped.isupper() and not stripped.endswith("."):
            is_heading = True
            header_text = stripped

        if is_heading and current_lines:
            sec_text = "\n".join(current_lines).strip()
            if sec_text:
                sections.append({
                    "section_id": f"sec_{sec_idx}",
                    "title": current_title,
                    "section_path": [filename, current_title],
                    "text": sec_text,
                    "page": 1
                })
                sec_idx += 1
            current_title = header_text
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append({
                "section_id": f"sec_{sec_idx}",
                "title": current_title,
                "section_path": [filename, current_title],
                "text": sec_text,
                "page": 1
            })

    return sections, text


def _extract_pdf_pure_fallback(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Fast linear standard-library stream extraction for PDF without fitz."""
    import zlib
    text_chunks: List[str] = []
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        cursor = 0
        streams_found = 0
        max_streams = 50
        while streams_found < max_streams and cursor < len(content):
            s_idx = content.find(b"stream", cursor)
            if s_idx == -1:
                break
            nl_idx = content.find(b"\n", s_idx, s_idx + 12)
            if nl_idx == -1:
                cursor = s_idx + 6
                continue
            e_idx = content.find(b"endstream", nl_idx + 1)
            if e_idx == -1:
                break
            raw_stream = content[nl_idx + 1:e_idx].rstrip(b"\r\n")
            cursor = e_idx + 9
            streams_found += 1

            try:
                decompressed = zlib.decompress(raw_stream)
            except Exception:
                decompressed = raw_stream

            tj_matches = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
            for t in tj_matches:
                try:
                    text_chunks.append(t.decode("latin1", errors="ignore"))
                except Exception:
                    pass

            tj_array_matches = re.findall(rb"\[(.*?)\]\s*TJ", decompressed)
            for arr in tj_array_matches:
                parts = re.findall(rb"\((.*?)\)", arr)
                line = "".join([p.decode("latin1", errors="ignore") for p in parts])
                if line.strip():
                    text_chunks.append(line)

        full_text = "\n".join(text_chunks).strip()
        if not full_text:
            full_text = f"[PDF Document: {filename}]"

        sections = [{
            "section_id": "sec_0",
            "title": filename,
            "section_path": [filename],
            "text": full_text,
            "page": 1
        }]
        return sections, [], full_text
    except Exception as exc:
        logger.warning(f"[PDF] Pure-python fallback failed: {exc}")
        return [], [], f"[PDF Document: {filename}]"


def _extract_pdf_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """
    Parse PDF into pages, headings, sections, and embedded visual images/diagrams with PyMuPDF.
    Extracts embedded figures as first-class visual evidence with IEEE-style captions,
    bounding box coordinates, MD5 deduplication, and visual semantics.
    """
    sections: List[Dict[str, Any]] = []
    figures: List[Dict[str, Any]] = []
    full_text_parts = []
    seen_image_hashes: set[str] = set()
    doc_figure_counter = 0

    try:
        import fitz  # PyMuPDF
        import tempfile
        import os
        import hashlib
        from services.vision import extract_visual_semantics

        doc = fitz.open(file_path)
        sec_idx = 0

        for page_num, page in enumerate(doc):
            page_text = str(page.get_text() or "")
            blocks = page.get_text("blocks")
            image_descriptions: List[str] = []

            # 1. Extract, deduplicate, and analyze embedded figures/diagrams on this page
            try:
                page_images = page.get_images(full=True)
                if page_images:
                    for img_idx, img_info in enumerate(page_images[:8]):  # Process up to 8 figures/page
                        xref = img_info[0]
                        try:
                            base_img = doc.extract_image(xref)
                            if not base_img:
                                continue
                            w = base_img.get("width", 0)
                            h = base_img.get("height", 0)
                            # Ignore tiny icons, bullets, spacers, and 1-pixel borders
                            if w < 80 or h < 80 or (w > 0 and h > 0 and (w / h > 15 or h / w > 15)):
                                continue

                            img_bytes = base_img.get("image")
                            if not img_bytes:
                                continue
                            img_ext = base_img.get("ext", "png").lower()
                            if img_ext == "jpeg":
                                img_ext = "jpg"

                            file_hash = hashlib.md5(img_bytes).hexdigest()
                            if file_hash in seen_image_hashes:
                                # Suppress repeated logos/headers across pages
                                continue
                            seen_image_hashes.add(file_hash)

                            rects = page.get_image_rects(xref)
                            rect = rects[0] if rects else None

                            # Suppress header/footer banners and small logos
                            if rect and h < 220 and (rect.y1 < 100 or rect.y0 > page.rect.height - 80):
                                continue

                            doc_figure_counter += 1

                            # Save persistent figure asset
                            safe_stem = re.sub(r"[^\w\-]", "_", Path(filename).stem)[:40]
                            saved_fig_filename = f"{safe_stem}_p{page_num + 1}_fig{doc_figure_counter}_{file_hash[:8]}.{img_ext}"
                            saved_fig_path = FIGURES_DIR / saved_fig_filename
                            try:
                                with open(saved_fig_path, "wb") as f:
                                    f.write(img_bytes)
                            except Exception as save_err:
                                logger.warning(f"[PDF] Could not write figure asset {saved_fig_filename}: {save_err}")

                            # Spatial caption extraction (scan blocks below and above image bbox)
                            caption_text = ""
                            detected_label = ""
                            if rect:
                                # Primary: IEEE style caption immediately BELOW the image
                                for b in blocks:
                                    if b[1] >= rect.y1 - 15 and b[1] <= rect.y1 + 140:
                                        btext = b[4].strip()
                                        if any(skip_word in btext for skip_word in ["Dayananda Sagar", "School of Engineering", "Department of"]):
                                            continue
                                        m = re.search(r"(?:Fig(?:ure)?\.?\s*(\d+[A-Za-z0-9\.\-]*))(?:\s*[:\.\-]\s*|\s+)(.*)", btext, re.IGNORECASE)
                                        if m:
                                            detected_label = f"Fig. {m.group(1).rstrip('.')}"
                                            caption_text = m.group(2).strip() or btext
                                            break
                                        elif not caption_text and 5 < len(btext) < 300:
                                            caption_text = btext

                                # Secondary: Check title directly ABOVE the image
                                if not caption_text:
                                    for b in blocks:
                                        if b[3] <= rect.y0 + 10 and b[3] >= rect.y0 - 90:
                                            btext = b[4].strip()
                                            if any(skip_word in btext for skip_word in ["Dayananda Sagar", "School of Engineering", "Department of"]):
                                                continue
                                            m = re.search(r"(?:Fig(?:ure)?\.?\s*(\d+[A-Za-z0-9\.\-]*))(?:\s*[:\.\-]\s*|\s+)(.*)", btext, re.IGNORECASE)
                                            if m:
                                                detected_label = f"Fig. {m.group(1).rstrip('.')}"
                                                caption_text = m.group(2).strip() or btext
                                                break
                                            elif not caption_text and 5 < len(btext) < 180:
                                                caption_text = btext

                            figure_label = detected_label or f"Fig. {doc_figure_counter}"
                            if not caption_text:
                                caption_text = f"Visual diagram / embedded figure on Page {page_num + 1} of {filename}"

                            # Run OCR & Visual Semantics (scene understanding)
                            vis_text = ""
                            ocr_text = ""
                            try:
                                vis_text = extract_visual_semantics(
                                    str(saved_fig_path),
                                    original_filename=f"{filename}_{figure_label}.{img_ext}"
                                )
                                if "--- VISUAL TEXT & LABELS EXTRACTED FROM IMAGE (OCR) ---" in vis_text:
                                    parts = vis_text.split("--- VISUAL TEXT & LABELS EXTRACTED FROM IMAGE (OCR) ---")
                                    ocr_text = parts[1].split("---")[0].strip()
                            except Exception as vis_err:
                                logger.debug(f"[PDF] Visual semantics error for {figure_label}: {vis_err}")

                            colorspace = base_img.get("colorspace", 3)
                            color_mode = "grayscale" if colorspace == 1 else "color"

                            figure_obj = {
                                "figure_id": f"fig_{file_hash[:12]}",
                                "figure_label": figure_label,
                                "page": page_num + 1,
                                "caption": caption_text,
                                "ocr_text": ocr_text,
                                "visual_description": vis_text,
                                "combined_caption": f"{figure_label}: {caption_text}" if caption_text else figure_label,
                                "bbox": [round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1)] if rect else None,
                                "width": w,
                                "height": h,
                                "color_mode": color_mode,
                                "mime_type": f"image/{img_ext}",
                                "file_hash": file_hash,
                                "image_path": str(saved_fig_path),
                                "image_url": f"/figures/{saved_fig_filename}",
                                "provenance": f"{filename}, p. {page_num + 1}, {figure_label}",
                            }
                            figures.append(figure_obj)

                            desc_line = f"[{figure_label} on Page {page_num + 1} ({w}x{h} px)]:\nCaption: {caption_text}\n{vis_text.strip()}"
                            image_descriptions.append(desc_line)

                            # Create dedicated Figure evidence section in the Document Memory Tree
                            fig_sec_text = (
                                f"[{figure_label} Evidence - Page {page_num + 1} of {filename}]: {caption_text}\n"
                                f"Provenance: {filename}, Page {page_num + 1}, {figure_label}\n"
                                f"{vis_text}"
                            ).strip()

                            sections.append({
                                "section_id": f"sec_fig_{figure_obj['figure_id']}",
                                "title": f"{figure_label} on Page {page_num + 1}: {caption_text[:60]}",
                                "section_path": [filename, f"Page {page_num + 1}", figure_label],
                                "text": fig_sec_text,
                                "page": page_num + 1,
                                "is_figure": True,
                                "figure_data": figure_obj,
                            })
                            sec_idx += 1

                        except Exception as inner_e:
                            logger.debug(f"[PDF] Image {img_idx} extraction error on p{page_num+1}: {inner_e}")
            except Exception as img_err:
                logger.debug(f"[PDF] get_images error on p{page_num+1}: {img_err}")

            # 2. If page text is very sparse and no embedded images were extracted, OCR the full rendered page
            if len(page_text.strip()) < 50 and not image_descriptions:
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_f:
                        pix.save(tmp_f.name)
                        tmp_path = tmp_f.name
                    try:
                        page_ocr_text = extract_visual_semantics(
                            tmp_path,
                            original_filename=f"{filename}_page_{page_num+1}.png"
                        )
                        if len(page_ocr_text.strip()) > len(page_text.strip()):
                            page_text = page_ocr_text
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                except Exception as err:
                    logger.debug(f"[PDF] Page {page_num + 1} full-page OCR error: {err}")

            # 3. Append image descriptions to page text
            if image_descriptions:
                images_block = "\n\n".join(image_descriptions)
                page_text = f"{page_text}\n\n{images_block}".strip() if page_text.strip() else images_block

            full_text_parts.append(page_text)
            
            blocks = page.get_text("blocks")
            current_title = f"Page {page_num + 1}"
            current_block_lines = []

            for b in blocks:
                block_text = b[4].strip() if len(b) > 4 else ""
                if not block_text:
                    continue

                first_line = block_text.splitlines()[0].strip()
                if len(first_line) < 60 and (first_line.isupper() or first_line.startswith("#") or re.match(r"^\d+\.", first_line)):
                    if current_block_lines:
                        sec_text = "\n\n".join(current_block_lines).strip()
                        if sec_text:
                            sections.append({
                                "section_id": f"sec_{sec_idx}",
                                "title": current_title,
                                "section_path": [filename, f"Page {page_num + 1}", current_title],
                                "text": sec_text,
                                "page": page_num + 1
                            })
                            sec_idx += 1
                    current_title = first_line
                    current_block_lines = [block_text]
                else:
                    current_block_lines.append(block_text)

            if current_block_lines:
                sec_text = "\n\n".join(current_block_lines).strip()
                if sec_text:
                    sections.append({
                        "section_id": f"sec_{sec_idx}",
                        "title": current_title,
                        "section_path": [filename, f"Page {page_num + 1}", current_title],
                        "text": sec_text,
                        "page": page_num + 1
                    })
                    sec_idx += 1
            elif page_text.strip():
                sections.append({
                    "section_id": f"sec_{sec_idx}",
                    "title": current_title,
                    "section_path": [filename, f"Page {page_num + 1}"],
                    "text": page_text.strip(),
                    "page": page_num + 1
                })
                sec_idx += 1

        doc.close()
        full_text = "\n\n".join(full_text_parts)
        if not full_text.strip():
            full_text = extract_pdf_with_ocr(file_path)
            if full_text.strip() and not sections:
                sections.append({
                    "section_id": "sec_0",
                    "title": filename,
                    "section_path": [filename],
                    "text": full_text.strip(),
                    "page": 1
                })
        return sections, [], full_text, figures
    except Exception as e:
        logger.warning(f"[PDF] Structured PyMuPDF extraction unavailable or failed ({e}), using pure-python stream fallback")
        fb_sec, fb_tbl, fb_txt = _extract_pdf_pure_fallback(file_path, filename)
        return fb_sec, fb_tbl, fb_txt, []



def _extract_docx_fallback(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Pure-Python standard library parser for DOCX files using zipfile and ElementTree."""
    import zipfile
    import xml.etree.ElementTree as ET

    sections: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    full_text_lines: List[str] = []

    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)

            ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            current_title = "Document Overview"
            current_paras: List[str] = []
            sec_idx = 0

            for child in tree.iter():
                if child.tag == f"{ns}p":
                    p_texts = [n.text for n in child.iter(f"{ns}t") if n.text and n.text.strip()]
                    if p_texts:
                        para_str = " ".join(p_texts).strip()
                        full_text_lines.append(para_str)

                        is_heading = False
                        for pPr in child.findall(f"{ns}pPr"):
                            for pStyle in pPr.findall(f"{ns}pStyle"):
                                val = pStyle.get(f"{ns}val", "").lower()
                                if "heading" in val or "title" in val:
                                    is_heading = True
                        if not is_heading and len(para_str) < 50 and para_str.isupper():
                            is_heading = True

                        if is_heading and current_paras:
                            sec_text = "\n\n".join(current_paras).strip()
                            if sec_text:
                                sections.append({
                                    "section_id": f"sec_{sec_idx}",
                                    "title": current_title,
                                    "section_path": [filename, current_title],
                                    "text": sec_text,
                                    "page": 1
                                })
                                sec_idx += 1
                            current_title = para_str
                            current_paras = []
                        else:
                            current_paras.append(para_str)
                elif child.tag == f"{ns}tbl":
                    tbl_rows = []
                    for r in child.findall(f"{ns}tr"):
                        row_cells = []
                        for c in r.findall(f"{ns}tc"):
                            c_text = " ".join([n.text for n in c.iter(f"{ns}t") if n.text and n.text.strip()])
                            row_cells.append(c_text)
                        if row_cells:
                            tbl_rows.append(row_cells)
                    if tbl_rows:
                        table_text = "\n".join([" | ".join(r) for r in tbl_rows])
                        tables.append({
                            "table_id": f"tbl_{len(tables)}",
                            "headers": tbl_rows[0],
                            "rows": tbl_rows[1:] if len(tbl_rows) > 1 else [],
                            "table_text": table_text,
                        })
                        full_text_lines.append(table_text)

            if current_paras:
                sec_text = "\n\n".join(current_paras).strip()
                if sec_text:
                    sections.append({
                        "section_id": f"sec_{sec_idx}",
                        "title": current_title,
                        "section_path": [filename, current_title],
                        "text": sec_text,
                        "page": 1
                    })

            full_text = "\n\n".join(full_text_lines)
            return sections, tables, full_text
    except Exception as exc:
        logger.warning(f"[DOCX] Pure-python fallback failed: {exc}")
        return [], [], f"[Word Document: {filename}]"


def _extract_docx_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Parse DOCX paragraphs and tables into structured sections with python-docx, falling back to pure-Python zipfile."""
    try:
        from docx import Document
        doc = Document(file_path)
    except Exception as e:
        logger.info(f"[DOCX] python-docx not available or failed ({e}), using pure-python fallback")
        return _extract_docx_fallback(file_path, filename)
    sections: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    full_text_lines = []

    try:
        current_title = "Document Overview"
        current_paras = []
        sec_idx = 0

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            full_text_lines.append(text)

            is_heading = False
            style_name = p.style.name.lower() if p.style and p.style.name else ""
            if "heading" in style_name or "title" in style_name or (len(text) < 50 and text.isupper()):
                is_heading = True

            if is_heading and current_paras:
                sec_text = "\n\n".join(current_paras).strip()
                if sec_text:
                    sections.append({
                        "section_id": f"sec_{sec_idx}",
                        "title": current_title,
                        "section_path": [filename, current_title],
                        "text": sec_text,
                        "page": 1
                    })
                    sec_idx += 1
                current_title = text
                current_paras = []
            else:
                current_paras.append(text)

        if current_paras:
            sec_text = "\n\n".join(current_paras).strip()
            if sec_text:
                sections.append({
                    "section_id": f"sec_{sec_idx}",
                    "title": current_title,
                    "section_path": [filename, current_title],
                    "text": sec_text,
                    "page": 1
                })

        # Extract structured tables
        for t_idx, table in enumerate(doc.tables):
            rows_data = []
            for row in table.rows:
                rows_data.append([c.text.strip() for c in row.cells])
            if rows_data:
                headers = rows_data[0]
                table_text = "\n".join([" | ".join(r) for r in rows_data])
                tables.append({
                    "table_id": f"tbl_{t_idx}",
                    "headers": headers,
                    "rows": rows_data[1:] if len(rows_data) > 1 else [],
                    "table_text": table_text,
                })
                full_text_lines.append(table_text)

        full_text = "\n\n".join(full_text_lines)
        return sections, tables, full_text
    except Exception as e:
        logger.warning(f"[DOCX] python-docx tree extraction failed: {e}")
        return _extract_docx_fallback(file_path, filename)




def _extract_code_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], str]:
    """Parse source code into module header, class, and function sections."""
    code_text = extract_code(file_path, original_filename=filename)
    lines = code_text.splitlines()
    sections: List[Dict[str, Any]] = []
    
    current_title = "Module Declarations & Imports"
    current_lines = []
    sec_idx = 0

    for line in lines:
        stripped = line.strip()
        is_definition = False
        def_name = ""
        # Match class or def or function declarations
        if re.match(r"^(?:class\s+[A-Za-z0-9_]+|def\s+[A-Za-z0-9_]+|async\s+def\s+[A-Za-z0-9_]+|function\s+[A-Za-z0-9_]+|export\s+(?:default\s+)?(?:function|class)\s+[A-Za-z0-9_]+)", stripped):
            is_definition = True
            def_name = stripped.split("(")[0].replace(":", "").strip()

        if is_definition and current_lines:
            sec_text = "\n".join(current_lines).strip()
            if sec_text:
                sections.append({
                    "section_id": f"sec_{sec_idx}",
                    "title": current_title,
                    "section_path": [filename, current_title],
                    "text": sec_text,
                    "page": 1
                })
                sec_idx += 1
            current_title = def_name
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sec_text = "\n".join(current_lines).strip()
        if sec_text:
            sections.append({
                "section_id": f"sec_{sec_idx}",
                "title": current_title,
                "section_path": [filename, current_title],
                "text": sec_text,
                "page": 1
            })

    return sections, code_text


def _extract_pptx_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """Parse PPTX presentation slides, notes, and embedded visual media into structured sections and figure evidence."""
    import zipfile
    import xml.etree.ElementTree as ET

    sections: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    figures: List[Dict[str, Any]] = []
    full_text_lines: List[str] = []

    try:
        from services.vision import analyze_image_full

        with zipfile.ZipFile(file_path, "r") as z:
            # 1. Extract embedded visual media files (images, diagrams, charts)
            media_files = [f for f in z.namelist() if f.startswith("ppt/media/")]
            for mfile in media_files:
                try:
                    mdata = z.read(mfile)
                    mhash = hashlib.md5(mdata).hexdigest()
                    mext = Path(mfile).suffix.lower().lstrip(".") or "png"
                    mstem = re.sub(r"[^\w\-]", "_", Path(filename).stem)[:30]
                    mname = f"{mstem}_media_{mhash[:8]}.{mext}"
                    mpath = FIGURES_DIR / mname
                    if not mpath.exists():
                        with open(mpath, "wb") as mf:
                            mf.write(mdata)

                    analysis = analyze_image_full(str(mpath), original_filename=Path(mfile).name)
                    fig_obj = {
                        "figure_id": f"fig_{mhash[:12]}",
                        "figure_label": f"Media {len(figures) + 1}",
                        "page": 1,
                        "caption": f"Embedded visual asset in {filename}",
                        "ocr_text": analysis.get("ocr_text", ""),
                        "visual_description": analysis.get("scene_description", ""),
                        "scene_description": analysis.get("scene_description", ""),
                        "swatches": analysis.get("swatches", []),
                        "dominant_colors": analysis.get("dominant_colors", []),
                        "visual_tags": analysis.get("visual_tags", []),
                        "width": analysis.get("width", 0),
                        "height": analysis.get("height", 0),
                        "color_mode": analysis.get("color_mode", "color"),
                        "mime_type": f"image/{mext}",
                        "file_hash": mhash,
                        "image_path": str(mpath),
                        "image_url": f"/figures/{mname}",
                        "provenance": f"{filename}, Media {len(figures) + 1}",
                    }
                    figures.append(fig_obj)
                except Exception as me:
                    logger.debug(f"[PPTX] Media extraction error for {mfile}: {me}")

            # 2. Extract slides in numerical order
            slide_files = sorted(
                [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")],
                key=lambda x: int("".join(filter(str.isdigit, x)) or 0)
            )

            for idx, sfile in enumerate(slide_files, start=1):
                sxml = z.read(sfile)
                root = ET.fromstring(sxml)
                texts = [node.text.strip() for node in root.iter() if node.tag.endswith("}t") and node.text and node.text.strip()]
                slide_text = "\n".join(texts)
                if not slide_text:
                    continue

                full_text_lines.append(f"--- Slide {idx} ---")
                full_text_lines.append(slide_text)

                slide_title = texts[0] if texts else f"Slide {idx}"
                if len(slide_title) > 60:
                    slide_title = slide_title[:60] + "..."

                sec_obj = {
                    "section_id": f"sec_slide_{idx}",
                    "title": f"Slide {idx}: {slide_title}",
                    "section_path": [filename, f"Slide {idx}"],
                    "text": slide_text,
                    "page": idx,
                    "is_figure": False,
                }
                sections.append(sec_obj)

    except Exception as e:
        logger.error(f"[PPTX] Error parsing presentation {filename}: {e}")

    full_text = "\n\n".join(full_text_lines)
    return sections, tables, full_text, figures


def _extract_image_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """Parse images with vision metadata, OCR text, and color palettes into structured sections and first-class figure evidence."""
    from services.vision import analyze_image_full

    analysis = analyze_image_full(file_path, original_filename=filename)
    img_text = analysis["full_semantics"]
    figures: List[Dict[str, Any]] = []

    try:
        with open(file_path, "rb") as f:
            content = f.read()
        fhash = hashlib.md5(content).hexdigest()
        ext = Path(filename).suffix.lower().lstrip(".") or "png"
        safe_stem = re.sub(r"[^\w\-]", "_", Path(filename).stem)[:40]
        saved_fig_filename = f"{safe_stem}_{fhash[:8]}.{ext}"
        saved_fig_path = FIGURES_DIR / saved_fig_filename
        if not saved_fig_path.exists():
            shutil.copy2(file_path, saved_fig_path)

        caption = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        if analysis.get("visual_tags"):
            main_tags = [t for t in analysis["visual_tags"] if t != "Image Asset"]
            if main_tags:
                caption = f"{main_tags[0]}: {caption}"

        fig_obj = {
            "figure_id": f"fig_{fhash[:12]}",
            "figure_label": "Fig. 1",
            "page": 1,
            "caption": caption,
            "ocr_text": analysis.get("ocr_text", ""),
            "visual_description": analysis.get("scene_description", img_text),
            "scene_description": analysis.get("scene_description", ""),
            "swatches": analysis.get("swatches", []),
            "dominant_colors": analysis.get("dominant_colors", []),
            "visual_tags": analysis.get("visual_tags", []),
            "combined_caption": f"Fig. 1: {caption}",
            "bbox": None,
            "width": analysis.get("width", 0),
            "height": analysis.get("height", 0),
            "color_mode": analysis.get("color_mode", "color"),
            "mime_type": f"image/{ext}",
            "file_hash": fhash,
            "image_path": str(saved_fig_path),
            "image_url": f"/figures/{saved_fig_filename}",
            "provenance": f"{filename}, p. 1, Fig. 1",
        }
        figures.append(fig_obj)
    except Exception as e:
        logger.debug(f"[Extraction] Standalone image figure creation error: {e}")

    section = {
        "section_id": "sec_img_0",
        "title": "Visual Analysis & Scene Description",
        "section_path": [filename, "Visual Semantics"],
        "text": img_text,
        "page": 1,
        "is_figure": True,
        "figure_data": figures[0] if figures else None,
    }
    return [section], img_text, figures



# ---------------------------------------------------------------------------
# BASE EXTRACTORS
# ---------------------------------------------------------------------------

def extract_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF with pure-Python stream & OCR fallbacks."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            text += str(doc[page_num].get_text())
        doc.close()
        if len(text.strip()) >= 50:
            return text
    except Exception as e:
        logger.info(f"[PDF] PyMuPDF not available or failed ({e}), trying pure-python stream extractor")

    # Try pure python stream extractor
    try:
        _, _, stream_text = _extract_pdf_pure_fallback(file_path, Path(file_path).name)
        if len(stream_text.strip()) >= 50:
            return stream_text
    except Exception as e:
        logger.info(f"[PDF] Pure-python stream extraction failed: {e}")

    return extract_pdf_with_ocr(file_path)


def extract_pdf_with_ocr(file_path: str) -> str:
    """Extract text from scanned PDF using Tesseract OCR if available."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            page_text = pytesseract.image_to_string(img)
            text += str(page_text)
        doc.close()
        return text
    except Exception as e:
        logger.warning(f"[OCR] OCR unavailable or failed: {e}")
        return f"[Scanned PDF: {Path(file_path).name}]"


def extract_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx with pure-Python fallback."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        if text.strip():
            return text
    except Exception as e:
        logger.info(f"[DOCX] python-docx not available or failed ({e}), using pure-python fallback")

    _, _, pure_text = _extract_docx_fallback(file_path, Path(file_path).name)
    return pure_text if pure_text.strip() else f"[Word Document: {Path(file_path).name}]"


def extract_txt(file_path: str) -> str:
    """Extract text from plain text / markdown / csv / log files."""
    try:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()
        return text
    except Exception as e:
        logger.error(f"[Text] Extraction failed: {str(e)}")
        raise


def extract_code(file_path: str, original_filename: Optional[str] = None) -> str:
    """Extract and semantically label source code documents."""
    p = Path(file_path)
    effective_name = original_filename or p.name
    lang = CODE_EXTENSIONS_MAP.get(Path(effective_name).suffix.lower(), "Code")
    try:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_code = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                raw_code = f.read()
        
        stem_keywords = Path(effective_name).stem.replace("_", " ").replace("-", " ")
        header = (
            f"[Source Code Document: {effective_name}]\n"
            f"[Language: {lang}]\n"
            f"[Subject / Filename Keywords: {stem_keywords}]\n"
            f"[Total Lines: {len(raw_code.splitlines())}]\n\n"
        )
        return header + raw_code
    except Exception as e:
        logger.error(f"[Code] Extraction failed: {str(e)}")
        raise


def extract_image(file_path: str, original_filename: Optional[str] = None) -> str:
    """Extract visual text, labels, and scene descriptions from images."""
    try:
        from services.vision import extract_visual_semantics
        return extract_visual_semantics(file_path, original_filename=original_filename)
    except Exception as e:
        logger.error(f"[Image] Vision extraction failed for {file_path}: {e}")
        p = Path(file_path)
        name = original_filename or p.name
        keywords = Path(name).stem.replace("_", " ").replace("-", " ")
        return f"[Image File: {name}]\nCategory: Photos & Images\nFilename Keywords: {keywords}"
