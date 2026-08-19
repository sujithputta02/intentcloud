"""
Phase 2: Embeddings Service
Generates sentence-level embeddings using sentence-transformers.
Model: all-MiniLM-L6-v2 (384-dimensional dense vectors)
"""

from typing import Dict, List
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
SENTENCE_SPLITTER_CHARS = 256  # Max chars per sentence before splitting


class EmbeddingsManager:
    """Manages sentence embedding generation and caching."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            logger.info(f"[Embeddings] Loading model: {MODEL_NAME}")
            self._model = SentenceTransformer(MODEL_NAME)
            logger.info(f"[Embeddings] Model loaded. Dimension: {EMBEDDING_DIM}")
    
    def get_model(self):
        return self._model


def split_into_sentences(text: str, max_length: int = SENTENCE_SPLITTER_CHARS) -> List[str]:
    """
    Split text into sentence chunks.
    Uses simple heuristic: split on periods/newlines, respect max_length.
    
    Args:
        text: Input text
        max_length: Maximum characters per sentence
    
    Returns:
        List of sentence chunks
    """
    sentences = []
    
    # Split on common sentence terminators
    raw_sentences = text.replace("\n", ". ").split(". ")
    
    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        # Split long sentences by character limit
        while len(sent) > max_length:
            # Find a good break point (space)
            break_point = max_length
            while break_point > 0 and sent[break_point] != " ":
                break_point -= 1
            
            if break_point == 0:
                break_point = max_length
            
            sentences.append(sent[:break_point].strip())
            sent = sent[break_point:].strip()
        
        if sent:
            sentences.append(sent)
    
    return [s for s in sentences if s]


def generate_embeddings(text_content: str) -> Dict:
    """
    Generate sentence-level embeddings for document text.
    
    Pipeline:
    1. Split text into sentences
    2. Generate embeddings for each sentence
    3. Return with metadata
    
    Args:
        text_content: Full document text
    
    Returns:
        Dict with embeddings and metadata:
        {
            "embeddings": [embedding_vector, ...],
            "sentences": [sentence_text, ...],
            "sentence_count": int,
            "embedding_dim": int
        }
    """
    try:
        logger.info(f"[Embeddings] Processing {len(text_content)} chars")
        
        # Get embeddings manager (singleton)
        manager = EmbeddingsManager()
        model = manager.get_model()
        
        # Step 1: Split into sentences
        sentences = split_into_sentences(text_content)
        logger.info(f"[Embeddings] Split into {len(sentences)} sentences")
        
        if not sentences:
            logger.warning("[Embeddings] No sentences extracted")
            return {
                "embeddings": [],
                "sentences": [],
                "sentence_count": 0,
                "embedding_dim": EMBEDDING_DIM
            }
        
        # Step 2: Generate embeddings
        logger.info(f"[Embeddings] Generating embeddings for {len(sentences)} sentences")
        embeddings = model.encode(sentences, convert_to_numpy=True)
        
        # Ensure embeddings are float32 for JSON serialization
        embeddings = embeddings.astype(np.float32)
        
        logger.info(f"[Embeddings] Generated embeddings shape: {embeddings.shape}")
        
        return {
            "embeddings": embeddings.tolist(),  # Convert to list for JSON
            "sentences": sentences,
            "sentence_count": len(sentences),
            "embedding_dim": EMBEDDING_DIM
        }
    
    except Exception as e:
        logger.error(f"[Embeddings] Generation failed: {str(e)}")
        raise


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        Cosine similarity score (0-1)
    """
    arr1 = np.array(embedding1, dtype=np.float32)
    arr2 = np.array(embedding2, dtype=np.float32)
    
    # Cosine similarity
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(arr1, arr2) / (norm1 * norm2))
