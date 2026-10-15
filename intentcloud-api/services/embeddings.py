"""
IntentCloud - Universal Embeddings & Keyword Representation Service

Responsibilities:
1. Normalize extracted text from any supported document format.
2. Split content into semantic/overlap chunks.
3. Generate dense embeddings using all-MiniLM-L6-v2.
4. Generate universal keyword/token representations.
5. Generate deterministic sparse vectors using feature hashing.
6. Extract human-readable keywords dynamically from document content.
7. Compute cosine similarity safely.

Important:
- The embedding model operates on TEXT.
- PDF/DOCX/PPTX/XLSX/CSV/HTML/etc. should first be converted into text
  by their respective extractors.
- Images/audio/video require upstream OCR/transcription/content extraction.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any, Union
from collections import Counter
import hashlib
import logging
import math
import re

import numpy as np
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------------

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Character limits for chunking before passing to the model.
CHUNK_SIZE_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200

# Maximum number of dynamic human-readable keywords to expose as metadata.
MAX_KEYWORDS = 20

# Sparse feature-hashing space (must be identical for docs and queries).
SPARSE_HASH_DIM = 1_000_003

# Minimum useful token length.
MIN_TOKEN_LENGTH = 2


# ---------------------------------------------------------------------------
# UNIVERSAL STOPWORDS
# ---------------------------------------------------------------------------
# Generic language stopwords only (no domain-specific terms).
# Allows arbitrary technical/domain vocabulary to survive.
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "also", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "could", "did", "do", "does",
    "doing", "down", "during", "each", "few", "for", "from", "further", "had",
    "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "us", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your", "yours", "yourself", "yourselves",
}


# ---------------------------------------------------------------------------
# MODEL MANAGER
# ---------------------------------------------------------------------------

class EmbeddingsManager:
    """Singleton manager for the sentence-transformers model."""

    _instance: Optional["EmbeddingsManager"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            logger.info("[Embeddings] Loading model: %s", MODEL_NAME)

            self._model = SentenceTransformer(MODEL_NAME)

            logger.info(
                "[Embeddings] Model loaded successfully. Dimension=%d",
                EMBEDDING_DIM,
            )

    def get_model(self) -> SentenceTransformer:
        if self._model is None:
            raise RuntimeError("Embedding model failed to initialize.")
        return self._model


# ---------------------------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize arbitrary extracted text without destroying useful technical
    information.

    Preserves:
    - numbers
    - acronyms
    - punctuation useful for technical terms
    - programming symbols where possible

    Removes:
    - null/control characters
    - excessive whitespace
    - repeated blank lines
    """

    if not text:
        return ""

    # Remove NULL/control characters while preserving newline/tab.
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", text)

    # Normalize common Unicode whitespace.
    text = re.sub(r"[ \t]+", " ", text)

    # Prevent huge blank-line regions.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces around line breaks.
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# SENTENCE DETECTION
# ---------------------------------------------------------------------------

_SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<=[.!?])\s+|\n{2,}"
)


def split_sentences(text: str) -> List[str]:
    """
    Split text into natural sentence/paragraph units.

    More robust than simply replacing '. ' because it:
    - respects ?, !
    - handles paragraph breaks
    - keeps abbreviations reasonably intact
    """

    if not text:
        return []

    parts = _SENTENCE_BOUNDARY_RE.split(text)

    result = []

    for part in parts:
        cleaned = part.strip()

        if cleaned:
            result.append(cleaned)

    return result


# ---------------------------------------------------------------------------
# CHUNKING
# ---------------------------------------------------------------------------

def _split_long_text(text: str, max_chars: int) -> List[str]:
    """
    Split a long sentence/paragraph without cutting words whenever possible.
    """

    if len(text) <= max_chars:
        return [text]

    pieces: List[str] = []
    start = 0

    while start < len(text):

        end = min(start + max_chars, len(text))

        if end < len(text):

            # Search backwards for a natural whitespace boundary.
            break_at = text.rfind(" ", start, end)

            if break_at <= start:
                break_at = end

        else:
            break_at = end

        piece = text[start:break_at].strip()

        if piece:
            pieces.append(piece)

        start = break_at

        while start < len(text) and text[start].isspace():
            start += 1

    return pieces


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> List[str]:
    """
    Create semantic-ish text chunks.

    Strategy:
    1. Normalize text.
    2. Split into sentences/paragraphs.
    3. Group several units until chunk_size is reached.
    4. Carry overlap from the previous chunk.

    This works for arbitrary textual content regardless of subject area.
    """

    text = normalize_text(text)

    if not text:
        return []

    units = split_sentences(text)

    if not units:
        return _split_long_text(text, chunk_size)

    chunks: List[str] = []
    current: List[str] = []
    current_length = 0

    for unit in units:

        if len(unit) > chunk_size:
            long_parts = _split_long_text(unit, chunk_size)

            for part in long_parts:

                if current:
                    chunks.append(" ".join(current))

                    overlap_text = (
                        chunks[-1][-overlap:]
                        if overlap > 0
                        else ""
                    )

                    current = (
                        [overlap_text.strip()]
                        if overlap_text.strip()
                        else []
                    )

                    current_length = len(current[0]) if current else 0

                chunks.append(part)

            current = []
            current_length = 0
            continue

        additional_length = (
            len(unit)
            if not current
            else len(unit) + 1
        )

        if current and current_length + additional_length > chunk_size:

            chunks.append(" ".join(current))

            # Character overlap.
            overlap_text = chunks[-1][-overlap:] if overlap > 0 else ""

            current = (
                [overlap_text.strip()]
                if overlap_text.strip()
                else []
            )

            current_length = len(current[0]) if current else 0

        current.append(unit)
        current_length += (
            len(unit)
            if len(current) == 1
            else len(unit) + 1
        )

    if current:
        chunks.append(" ".join(current))

    return [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]


# ---------------------------------------------------------------------------
# UNIVERSAL TOKENIZATION
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    (?:
        [A-Za-z]+(?:[-_./][A-Za-z0-9]+)*
        |
        [A-Z]{2,}
        |
        \d+(?:\.\d+)?
        |
        [A-Za-z0-9]+(?:[-_./:+#][A-Za-z0-9]+)+
    )
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> List[str]:
    """
    Universal tokenization for arbitrary textual documents.

    Keeps useful terms such as:
        kafka
        python
        c++
        gpt-4
        all-minilm-l6-v2
        aws
        2026
        api/v2
    """

    if not text:
        return []

    raw_tokens = _TOKEN_RE.findall(text.lower())

    tokens = []

    for token in raw_tokens:

        token = token.strip("._/-:")

        if len(token) < MIN_TOKEN_LENGTH:
            continue

        if token in STOPWORDS:
            continue

        tokens.append(token)

    return tokens


# ---------------------------------------------------------------------------
# N-GRAM GENERATION
# ---------------------------------------------------------------------------

def generate_terms(text: str) -> List[str]:
    """
    Generate unigrams + bigrams.

    Bigrams capture domain concepts such as:
        machine learning
        neural network
        cloud computing
        software architecture

    without needing a predefined topic dictionary.
    """

    tokens = tokenize(text)

    terms = list(tokens)

    for i in range(len(tokens) - 1):

        first = tokens[i]
        second = tokens[i + 1]

        terms.append(f"{first} {second}")

    return terms


# ---------------------------------------------------------------------------
# UNIVERSAL HUMAN-READABLE KEYWORDS
# ---------------------------------------------------------------------------

def extract_keywords(
    text: str,
    max_keywords: int = MAX_KEYWORDS,
) -> List[str]:
    """
    Dynamically extract representative keywords.

    No topic allowlist is used.

    Scoring:
        frequency
        + moderate bonus for multi-word phrases
        + moderate bonus for technically structured terms

    Result is deterministic for identical input.
    """

    terms = generate_terms(text)

    if not terms:
        return []

    counts = Counter(terms)

    scored: List[Tuple[str, float]] = []

    for term, frequency in counts.items():
        # Ignore pure digits, timestamps, and numeric noise (e.g., "03 20.25", "12", "200")
        letters_only = re.sub(r"[^a-zA-Z]", "", term)
        if len(letters_only) < 2:
            continue

        token_count = len(term.split())
        score = float(frequency)

        # Multi-word concepts are generally more informative.
        if token_count == 2:
            score *= 1.5

        # Slight boost for technical compound tokens containing letters
        if re.search(r"[\d/_.:+#-]", term) and len(letters_only) >= 3:
            score *= 1.05

        scored.append((term, score))

    scored.sort(
        key=lambda item: (-item[1], item[0])
    )

    return [
        term
        for term, _ in scored[:max_keywords]
    ]


# ---------------------------------------------------------------------------
# DETERMINISTIC SPARSE FEATURE HASHING
# ---------------------------------------------------------------------------

def _hash_term(term: str, dimension: int = SPARSE_HASH_DIM) -> int:
    """
    Stable hash independent of Python process/hash randomization.
    """

    digest = hashlib.md5(
        term.encode("utf-8")
    ).digest()

    number = int.from_bytes(
        digest[:8],
        byteorder="little",
        signed=False,
    )

    return number % dimension


def build_sparse_vector(
    text: str,
    dimension: int = SPARSE_HASH_DIM,
) -> Dict[str, List]:
    """
    Convert arbitrary text into a deterministic sparse vector.

    This is vocabulary-free:
    no predefined topic list,
    no corpus-specific word mapping.

    Features:
        unigram + bigram
        log-scaled TF
        L2 normalization

    Output format matches Qdrant SparseVector:
        {
            "indices": [...],
            "values": [...]
        }

    Important:
    The exact same function must be used for both documents and queries.
    """

    terms = generate_terms(text)

    if not terms:
        return {
            "indices": [],
            "values": [],
        }

    frequencies = Counter(terms)

    hashed_values: Dict[int, float] = {}

    for term, count in frequencies.items():

        index = _hash_term(term, dimension)

        # Sublinear term frequency.
        weight = 1.0 + math.log(float(count))

        # Handle hash collisions by accumulating values.
        hashed_values[index] = (
            hashed_values.get(index, 0.0) + weight
        )

    indices = sorted(hashed_values.keys())

    values = np.array(
        [hashed_values[index] for index in indices],
        dtype=np.float32,
    )

    # L2 normalization.
    norm = np.linalg.norm(values)

    if norm > 0:
        values = values / norm

    return {
        "indices": indices,
        "values": values.tolist(),
    }


# ---------------------------------------------------------------------------
# DENSE EMBEDDINGS
# ---------------------------------------------------------------------------

def generate_dense_embeddings(
    chunks: List[str],
) -> np.ndarray:
    """
    Generate 384-dimensional dense embeddings for chunks.
    """

    if not chunks:
        return np.empty(
            (0, EMBEDDING_DIM),
            dtype=np.float32,
        )

    manager = EmbeddingsManager()
    model = manager.get_model()

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    return embeddings.astype(np.float32)


# ---------------------------------------------------------------------------
# COMPLETE DOCUMENT REPRESENTATION
# ---------------------------------------------------------------------------

def generate_embeddings(
    text_content: Union[str, Dict[str, Any]],
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
    document_title: Optional[str] = None,
    document_category: Optional[str] = None,
    doc_title: Optional[str] = None,
    doc_category: Optional[str] = None,
) -> Dict:
    """
    Complete Document-Memory representation.
    Supports either raw string or rich DocumentTree (from extract_document_tree).

    Produces:
    - Structure-aware semantic chunks enriched with local context (doc title, section path).
    - Chunk sequence graph pointers (prev_chunk_index, next_chunk_index, section_path).
    - Document-level summary node vector for hierarchical matching.
    """
    try:
        final_title = doc_title or document_title
        final_category = doc_category or document_category

        # Determine if input is a structured DocumentTree dict or raw string
        if isinstance(text_content, dict):
            resolved_title = text_content.get("title") or final_title or "Document"
            resolved_category = text_content.get("category") or final_category or "document"
            sections = text_content.get("sections", [])
            normalized_text = normalize_text(text_content.get("full_text", ""))
        else:
            resolved_title = final_title or "Document"
            resolved_category = final_category or "document"
            sections = []
            normalized_text = normalize_text(text_content)

        doc_title = resolved_title
        doc_category = resolved_category

        if not normalized_text and not sections:
            return {
                "chunks": [],
                "chunk_count": 0,
                "embedding_dim": EMBEDDING_DIM,
                "document_keywords": [],
                "document_sparse_vector": {"indices": [], "values": []},
                "document_embedding": [],
            }

        logger.info(
            "[Embeddings] Processing '%s' (%d chars, %d sections)",
            doc_title,
            len(normalized_text),
            len(sections),
        )

        # Build raw chunk candidates with section metadata
        raw_units: List[Dict[str, Any]] = []

        if sections:
            for sec in sections:
                sec_text = normalize_text(sec.get("text", ""))
                sec_title = sec.get("title", "Section")
                sec_path = sec.get("section_path", [doc_title, sec_title])
                sec_page = sec.get("page", 1)
                is_fig = sec.get("is_figure", False)
                fig_data = sec.get("figure_data")

                if not sec_text:
                    continue

                sec_chunks = chunk_text(sec_text, chunk_size=chunk_size, overlap=overlap)
                for sc in sec_chunks:
                    raw_units.append({
                        "raw_text": sc,
                        "section_title": sec_title,
                        "section_path": sec_path,
                        "page": sec_page,
                        "is_figure": is_fig,
                        "figure_data": fig_data,
                    })
        else:
            # Fallback to standard chunking
            flat_chunks = chunk_text(normalized_text, chunk_size=chunk_size, overlap=overlap)
            for sc in flat_chunks:
                raw_units.append({
                    "raw_text": sc,
                    "section_title": "General",
                    "section_path": [doc_title],
                    "page": 1,
                    "is_figure": False,
                    "figure_data": None,
                })

        if not raw_units:
            return {
                "chunks": [],
                "chunk_count": 0,
                "embedding_dim": EMBEDDING_DIM,
                "document_keywords": [],
                "document_sparse_vector": {"indices": [], "values": []},
                "document_embedding": [],
                "figures": text_content.get("figures", []) if isinstance(text_content, dict) else [],
            }

        # Build context-enriched embedding text for each chunk
        # [DOCUMENT: Title | CATEGORY: Category] [SECTION: Path] Content
        total_chunks = len(raw_units)
        enriched_texts: List[str] = []

        for idx, unit in enumerate(raw_units):
            path_str = " > ".join(unit["section_path"])
            fig_prefix = "[EVIDENCE: Figure / Diagram] " if unit.get("is_figure") else ""
            enriched = (
                f"[DOCUMENT: {doc_title} | CATEGORY: {doc_category}]\n"
                f"[SECTION: {path_str} | CHUNK {idx + 1}/{total_chunks}]\n"
                f"{fig_prefix}{unit['raw_text']}"
            )
            enriched_texts.append(enriched)

        # Generate dense embeddings on enriched text (captures document DNA + fine details)
        dense_embeddings = generate_dense_embeddings(enriched_texts)

        chunk_records = []
        for idx, (unit, enriched, embedding) in enumerate(
            zip(raw_units, enriched_texts, dense_embeddings)
        ):
            prev_idx = idx - 1 if idx > 0 else None
            next_idx = idx + 1 if idx < total_chunks - 1 else None

            chunk_records.append({
                "chunk_index": idx,
                "text": unit["raw_text"],
                "enriched_text": enriched,
                "section_path": unit["section_path"],
                "parent_section": unit["section_title"],
                "page": unit.get("page", 1),
                "prev_chunk_index": prev_idx,
                "next_chunk_index": next_idx,
                "unit_type": "figure" if unit.get("is_figure") else "chunk",
                "is_figure": bool(unit.get("is_figure")),
                "figure_data": unit.get("figure_data"),
                "embedding": embedding.tolist(),
                "dense_vector": embedding.tolist(),
                "keywords": extract_keywords(enriched, max_keywords=10),
                "sparse_vector": build_sparse_vector(enriched),
            })


        # Generate Document Summary Node
        document_keywords = extract_keywords(normalized_text, max_keywords=MAX_KEYWORDS)
        document_sparse = build_sparse_vector(normalized_text)

        document_vector = np.mean(dense_embeddings, axis=0)
        norm = np.linalg.norm(document_vector)
        if norm > 0:
            document_vector = document_vector / norm

        # Add top-level Document Summary representation
        summary_text = (
            f"[DOCUMENT SUMMARY: {doc_title} | CATEGORY: {doc_category}]\n"
            f"Key Topics: {', '.join(document_keywords[:12])}\n"
            f"Content Abstract: {normalized_text[:400]}"
        )
        summary_embedding = generate_dense_embeddings([summary_text])[0]

        chunk_records.append({
            "chunk_index": total_chunks,
            "text": summary_text,
            "enriched_text": summary_text,
            "section_path": [doc_title, "Document Overview"],
            "parent_section": "Document Overview",
            "page": 1,
            "prev_chunk_index": None,
            "next_chunk_index": None,
            "unit_type": "document_summary",
            "embedding": summary_embedding.tolist(),
            "dense_vector": summary_embedding.tolist(),
            "keywords": document_keywords,
            "sparse_vector": build_sparse_vector(summary_text),
        })

        logger.info(
            "[Embeddings] Generated %d structural chunks + 1 summary node for '%s'",
            total_chunks,
            doc_title,
        )

        return {
            "chunks": chunk_records,
            "chunk_count": len(chunk_records),
            "embedding_dim": EMBEDDING_DIM,
            "document_embedding": document_vector.astype(np.float32).tolist(),
            "document_keywords": document_keywords,
            "document_sparse_vector": document_sparse,
            "figures": text_content.get("figures", []) if isinstance(text_content, dict) else [],
        }


    except Exception as exc:
        logger.exception("[Embeddings] Generation failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# QUERY REPRESENTATION
# ---------------------------------------------------------------------------

def generate_query_representation(query: str) -> Dict:
    """
    Generate the exact same dense + sparse representation for a search query.

    This symmetry is essential:

        Document → dense + sparse
        Query    → dense + sparse
    """

    normalized_query = normalize_text(query)

    if not normalized_query:
        raise ValueError("Search query cannot be empty.")

    manager = EmbeddingsManager()
    model = manager.get_model()

    dense = model.encode(
        [normalized_query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0].astype(np.float32)

    sparse = build_sparse_vector(normalized_query)

    keywords = extract_keywords(
        normalized_query,
        max_keywords=10,
    )

    return {
        "text": normalized_query,
        "embedding": dense.tolist(),
        "keywords": keywords,
        "sparse_vector": sparse,
    }


# ---------------------------------------------------------------------------
# COSINE SIMILARITY
# ---------------------------------------------------------------------------

def compute_similarity(
    embedding1: List[float],
    embedding2: List[float],
) -> float:
    """
    Safe cosine similarity.

    Because embeddings are normalized before indexing, this is effectively
    equivalent to a dot product but this implementation also handles
    non-normalized external vectors safely.
    """

    arr1 = np.asarray(
        embedding1,
        dtype=np.float32,
    )

    arr2 = np.asarray(
        embedding2,
        dtype=np.float32,
    )

    if arr1.size == 0 or arr2.size == 0:
        return 0.0

    if arr1.shape != arr2.shape:
        raise ValueError(
            f"Embedding dimension mismatch: "
            f"{arr1.shape} vs {arr2.shape}"
        )

    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    score = float(
        np.dot(arr1, arr2) /
        (norm1 * norm2)
    )

    # Numerical safety.
    return max(-1.0, min(1.0, score))
