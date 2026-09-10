"""
Phase 1: Multi-Format Text Extraction Service
Extracts text from PDF, DOCX, TXT, Code files, and Photos/Images.
Includes OCR fallback for scanned PDFs and Images (Tesseract / Pillow metadata).
"""

from pathlib import Path
from typing import Optional, Dict
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


def extract_text_from_upload(file_path: str, original_filename: Optional[str] = None) -> str:
    """
    Extract text from uploaded file.
    Supports: PDF, DOCX, TXT, Code files (.py, .ts, .js, .json, .cpp, etc.), and Photos (.png, .jpg, etc.)
    
    Args:
        file_path: Path to the uploaded file on disk
        original_filename: Optional original filename before storage UUID rename
    
    Returns:
        Extracted text content ready for indexing
    """
    effective_name = original_filename or Path(file_path).name
    file_ext = Path(effective_name).suffix.lower() or Path(file_path).suffix.lower()
    
    try:
        if file_ext == ".pdf":
            return extract_pdf(file_path)
        elif file_ext in {".docx", ".doc"}:
            return extract_docx(file_path)
        elif file_ext in IMAGE_EXTENSIONS:
            return extract_image(file_path, original_filename=effective_name)
        elif file_ext in CODE_EXTENSIONS_MAP:
            return extract_code(file_path, original_filename=effective_name)
        elif file_ext in DOCUMENT_EXTENSIONS or file_ext == ".txt":
            return extract_txt(file_path)
        else:
            # Fallback: attempt reading as plain UTF-8 text before erroring
            return extract_txt(file_path)
    except Exception as e:
        logger.error(f"Extraction error for {file_path}: {str(e)}")
        raise


def extract_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF with OCR fallback."""
    try:
        import fitz  # PyMuPDF
        
        logger.info(f"[PDF] Extracting with PyMuPDF: {file_path}")
        doc = fitz.open(file_path)
        text = ""
        
        for page_num, page in enumerate(doc):
            text += str(page.get_text())
            logger.debug(f"[PDF] Page {page_num + 1}: {len(page.get_text())} chars")
        
        doc.close()
        
        # If extraction returned minimal text, try OCR fallback
        if len(text.strip()) < 100:
            logger.warning(f"[PDF] PyMuPDF extracted only {len(text)} chars, trying OCR fallback")
            ocr_text = extract_pdf_with_ocr(file_path)
            if len(ocr_text.strip()) > len(text.strip()):
                return ocr_text
        
        return text if text.strip() else f"[PDF Document: {Path(file_path).name}]\nNo extractable text found."
    except Exception as e:
        logger.error(f"[PDF] PyMuPDF failed: {str(e)}, trying OCR fallback")
        return extract_pdf_with_ocr(file_path)


def extract_pdf_with_ocr(file_path: str) -> str:
    """Extract text from scanned PDF using Tesseract OCR if available."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
        
        logger.info(f"[OCR] Extracting from PDF with Tesseract: {file_path}")
        doc = fitz.open(file_path)
        text = ""
        
        for page_num, page in enumerate(doc):
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
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        
        logger.info(f"[DOCX] Extracting: {file_path}")
        doc = Document(file_path)
        text = ""
        
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        
        logger.info(f"[DOCX] Extracted {len(text)} chars")
        return text if text.strip() else f"[Word Document: {Path(file_path).name}]"
    except Exception as e:
        logger.error(f"[DOCX] Extraction failed: {str(e)}")
        raise


def extract_txt(file_path: str) -> str:
    """Extract text from plain text / markdown / csv / log files."""
    try:
        logger.info(f"[Text] Extracting: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()
        
        logger.info(f"[Text] Extracted {len(text)} chars")
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
    """
    Extract visual text, labels, diagram scene descriptions, and rich metadata
    from photos/images using Apple Vision OCR and Ollama VLM.
    """
    try:
        from services.vision import extract_visual_semantics
        return extract_visual_semantics(file_path, original_filename=original_filename)
    except Exception as e:
        logger.error(f"[Image] Vision extraction failed for {file_path}: {e}")
        p = Path(file_path)
        name = original_filename or p.name
        keywords = Path(name).stem.replace("_", " ").replace("-", " ")
        return f"[Image File: {name}]\nCategory: Photos & Images\nFilename Keywords: {keywords}"
