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

logger = logging.getLogger(__name__)

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
    """Classify file into standard category: pdf, docx, txt, code, photo, document."""
    ext = Path(file_path_or_name).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".docx", ".doc"}:
        return "docx"
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
    """
    effective_name = original_filename or Path(file_path).name
    file_ext = Path(effective_name).suffix.lower() or Path(file_path).suffix.lower()
    category = get_file_category(effective_name)
    
    sections: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    full_text = ""
    
    try:
        if file_ext == ".pdf":
            sections, tables, full_text = _extract_pdf_tree(file_path, effective_name)
        elif file_ext in {".docx", ".doc"}:
            sections, tables, full_text = _extract_docx_tree(file_path, effective_name)
        elif file_ext in CODE_EXTENSIONS_MAP:
            sections, full_text = _extract_code_tree(file_path, effective_name)
        elif file_ext in IMAGE_EXTENSIONS:
            sections, full_text = _extract_image_tree(file_path, effective_name)
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
        "metadata": {
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "section_count": len(sections),
            "table_count": len(tables),
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
    """Pure-Python standard-library stream extraction for PDF without fitz."""
    import zlib
    text_chunks: List[str] = []
    try:
        with open(file_path, "rb") as f:
            content = f.read()

        stream_matches = re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", content, re.DOTALL)
        for m in stream_matches:
            raw_stream = m.group(1)
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


def _extract_pdf_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Parse PDF into pages, headings, and sections with PyMuPDF, falling back to pure-Python stream parser."""
    sections: List[Dict[str, Any]] = []
    full_text_parts = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        sec_idx = 0

        for page_num, page in enumerate(doc):
            page_text = page.get_text()
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

        doc.close()
        full_text = "\n\n".join(full_text_parts)
        if not full_text.strip():
            full_text = extract_pdf_with_ocr(file_path)
        return sections, [], full_text
    except Exception as e:
        logger.warning(f"[PDF] Structured PyMuPDF extraction unavailable or failed ({e}), using pure-python stream fallback")
        return _extract_pdf_pure_fallback(file_path, filename)


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


def _extract_image_tree(file_path: str, filename: str) -> tuple[List[Dict[str, Any]], str]:
    """Parse images with vision metadata and OCR text into structured sections."""
    img_text = extract_image(file_path, original_filename=filename)
    section = {
        "section_id": "sec_img_0",
        "title": "Visual Analysis & Scene Description",
        "section_path": [filename, "Visual Semantics"],
        "text": img_text,
        "page": 1
    }
    return [section], img_text


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
