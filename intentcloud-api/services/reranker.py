"""
IntentCloud - Cross-Encoder Reranking Service (Phase 4 / Week 5)

Responsibilities:
1. Load and manage the cross-encoder model: cross-encoder/ms-marco-MiniLM-L-6-v2.
2. Auto-detect hardware acceleration (Apple Silicon MPS / NVIDIA CUDA / CPU fallback).
3. Score (query, candidate_document) pairs for high-precision top-3 reordering.
4. Extract the most relevant sentence/passage (explainable matched snippet).
5. Generate human-interpretable "Why this matched" explanations.
6. Evaluate confidence scores against a tuned confidence threshold to prevent
   false-positive hallucinated results on irrelevant or out-of-domain queries.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

try:
    import torch
except ImportError:
    torch = None  # type: ignore

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None  # type: ignore

logger = logging.getLogger(__name__)

# Model and configuration
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_CONFIDENCE_THRESHOLD = 0.40  # Sigmoid-normalized score threshold (0.0 to 1.0)
MAX_RERANK_CANDIDATES = 25


def detect_device() -> str:
    """Auto-detect optimal compute device for hardware acceleration."""
    if torch is not None:
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("[Reranker] Hardware acceleration: Apple Silicon (MPS/Metal)")
            return "mps"
        elif torch.cuda.is_available():
            logger.info("[Reranker] Hardware acceleration: NVIDIA CUDA (%s)", torch.cuda.get_device_name(0))
            return "cuda"
    logger.info("[Reranker] Hardware acceleration: CPU fallback")
    return "cpu"


def sigmoid(x: float) -> float:
    """Stable sigmoid function mapping real logit score to (0.0, 1.0)."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def split_into_sentences(text: str) -> List[str]:
    """Split text into individual sentences for snippet extraction."""
    if not text:
        return []
    # Split on sentence terminals or double newlines
    sentences = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    cleaned = [s.strip() for s in sentences if len(s.strip()) > 15]
    return cleaned if cleaned else [text.strip()]


class RerankerManager:
    """Singleton manager for the CrossEncoder reranker model."""

    _instance: Optional["RerankerManager"] = None
    _model: Optional[CrossEncoder] = None
    _device: str = "cpu"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        if self._model is None:
            self._device = detect_device()
            logger.info("[Reranker] Loading cross-encoder model: %s on %s...", model_name, self._device)
            try:
                self._model = CrossEncoder(model_name, device=self._device)
                logger.info("✓ [Reranker] Cross-encoder loaded successfully: %s", model_name)
            except Exception as e:
                logger.warning("[Reranker] Failed loading on %s, falling back to CPU: %s", self._device, e)
                self._device = "cpu"
                self._model = CrossEncoder(model_name, device="cpu")
                logger.info("✓ [Reranker] Cross-encoder loaded on CPU fallback")

    def get_model(self) -> CrossEncoder:
        if self._model is None:
            raise RuntimeError("Cross-encoder model is not initialized.")
        return self._model

    def health_check(self) -> Dict:
        return {
            "status": "ready" if self._model is not None else "unavailable",
            "model_name": DEFAULT_RERANKER_MODEL,
            "device": self._device,
            "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        }

    def rerank_candidates(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 3,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> Tuple[List[Dict], bool, str]:
        """
        Rerank hybrid candidates using the Cross-Encoder.

        Args:
            query: Natural language user query
            candidates: List of candidate dicts from RRF fusion / search
            top_k: Number of final results to return (default: 3)
            confidence_threshold: Minimum normalized confidence score required

        Returns:
            Tuple of (reranked_results, is_confident_match, confidence_message)
        """
        if not candidates:
            return [], False, "No candidates found for query."

        # Cap candidates to rerank for efficiency
        candidates_to_score = candidates[:MAX_RERANK_CANDIDATES]
        model = self.get_model()

        # Build (query, text) pairs
        pairs = []
        for cand in candidates_to_score:
            text = cand.get("chunk_text") or cand.get("sentence_text") or cand.get("filename", "")
            pairs.append((query, text))

        try:
            raw_scores = model.predict(pairs, show_progress_bar=False)
            if isinstance(raw_scores, (int, float, np.floating)):
                raw_scores = [float(raw_scores)]
            else:
                raw_scores = [float(s) for s in raw_scores]
        except Exception as exc:
            logger.error("[Reranker] Cross-encoder scoring failed: %s", exc)
            # Fallback to existing candidate ordering
            return candidates[:top_k], True, "Reranker scoring fallback"

        # Attach scores to candidates
        scored_candidates = []
        for cand, logit_score in zip(candidates_to_score, raw_scores):
            norm_score = sigmoid(logit_score)
            item = dict(cand)
            item["rerank_logit"] = round(logit_score, 4)
            item["rerank_score"] = round(norm_score, 4)
            # Use normalized rerank score as primary relevance score
            item["relevance_score"] = round(norm_score, 4)
            item["relevance_percentage"] = int(round(norm_score * 100))
            scored_candidates.append(item)

        # Sort descending by cross-encoder score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Determine confidence status based on top score
        top_score = scored_candidates[0]["rerank_score"] if scored_candidates else 0.0
        is_confident = top_score >= confidence_threshold

        if is_confident:
            confidence_msg = f"High-confidence match found (relevance: {int(top_score * 100)}%)"
        else:
            confidence_msg = (
                f"No confident match found (top candidate scored {int(top_score * 100)}%, "
                f"threshold is {int(confidence_threshold * 100)}%). Try refining your query."
            )

        # Enrich top_k results with matched snippets and explanations
        final_results = []
        for rank, cand in enumerate(scored_candidates[:top_k], start=1):
            cand["rank"] = rank

            # Extract the best matching sentence for explainable snippet highlighting
            chunk_text = cand.get("chunk_text") or cand.get("sentence_text", "")
            matched_snippet = self.extract_matched_snippet(query, chunk_text)
            cand["matched_snippet"] = matched_snippet
            cand["sentence_text"] = matched_snippet

            # Generate explainable match rationale
            cand["explanation"] = self.generate_rerank_explanation(
                query=query,
                candidate=cand,
                rank=rank,
            )

            final_results.append(cand)

        logger.info(
            "[Reranker] Reranked %d candidates -> top %d (top score: %.3f, confident: %s)",
            len(candidates_to_score),
            len(final_results),
            top_score,
            is_confident,
        )

        return final_results, is_confident, confidence_msg

    def extract_matched_snippet(self, query: str, text: str) -> str:
        """
        Identify the single highest-similarity sentence within the document/chunk
        that triggered the match (explainable relevance snippet).
        """
        sentences = split_into_sentences(text)
        if not sentences:
            return text[:300]
        if len(sentences) == 1:
            return sentences[0]

        # Score candidate sentences with cross-encoder
        sentence_pairs = [(query, s) for s in sentences]
        try:
            model = self.get_model()
            sentence_scores = model.predict(sentence_pairs, show_progress_bar=False)
            best_idx = int(np.argmax(sentence_scores))
            return sentences[best_idx]
        except Exception:
            # Fallback to longest sentence containing query keywords
            query_words = set(query.lower().split())
            best_s = sentences[0]
            max_overlap = -1
            for s in sentences:
                overlap = len(set(s.lower().split()) & query_words)
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_s = s
            return best_s

    def generate_rerank_explanation(self, query: str, candidate: Dict, rank: int) -> str:
        """Generate a human-interpretable 'Why this matched' explanation."""
        rerank_score = candidate.get("rerank_score", 0.0)
        rrf_score = candidate.get("rrf_score", 0.0)
        keywords = candidate.get("keywords", [])
        filename = candidate.get("filename", "")

        keyword_str = ", ".join(keywords[:3]) if keywords else "key document terms"

        if rerank_score >= 0.85:
            return (
                f"Rank #{rank}: Strong semantic & lexical alignment. Cross-encoder verified direct match "
                f"on '{keyword_str}' (RRF score: {rrf_score:.4f}, Confidence: {int(rerank_score*100)}%)."
            )
        elif rerank_score >= 0.65:
            return (
                f"Rank #{rank}: High semantic relevance in {filename}. Verified topical overlap with "
                f"keywords [{keyword_str}]."
            )
        elif rerank_score >= 0.45:
            return (
                f"Rank #{rank}: Moderate conceptual match. Document covers related topics including {keyword_str}."
            )
        else:
            return (
                f"Rank #{rank}: Weak/partial match. Low cross-encoder confidence ({int(rerank_score*100)}%). "
                f"Consider adding specific keywords."
            )


# Global singleton instance helper
_reranker_instance: Optional[RerankerManager] = None


def get_reranker() -> RerankerManager:
    """Get or create the global RerankerManager singleton."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = RerankerManager()
    return _reranker_instance
