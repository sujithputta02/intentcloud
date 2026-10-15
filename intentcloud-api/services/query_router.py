"""
IntentCloud - Query Router & Intent Classifier
Routes queries based on semantic intent: TEXT, VISUAL, IMAGE, or MIXED.
Applies optimal RRF weights for multi-modal evidence fusion.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional
from enum import Enum


class QueryMode(str, Enum):
    TEXT = "TEXT"
    VISUAL = "VISUAL"
    IMAGE = "IMAGE"
    MIXED = "MIXED"


VISUAL_INTENT_PATTERNS = [
    r"\b(diagram|diagrams|flowchart|flow\s*chart)\b",
    r"\b(chart|charts|graph|graphs|plot|plots)\b",
    r"\b(figure|figures|fig\.?\s*\d*)\b",
    r"\b(architecture|topology|schematic|infrastructure)\b",
    r"\b(screenshot|screen\s*shot|mockup|ui\s*mockup)\b",
    r"\b(colou?r\s*palette|colou?rs?|palette|swatches?|hex\s*codes?|brand\s*deck|design\s*system)\b",
    r"\b(picture|photo|illustration|drawing|slide)\b",
    r"\b(visual\s*evidence|visual|image|images)\b",
]


def classify_query_intent(
    query_text: Optional[str] = None,
    query_image_bytes: Optional[bytes] = None,
    explicit_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Classify query intent into TEXT, VISUAL, IMAGE, or MIXED and supply RRF weights.
    """
    if explicit_mode:
        exp = explicit_mode.upper()
        if exp in ("VISUAL", "IMAGE"):
            mode = QueryMode.VISUAL
        elif exp == "TEXT":
            mode = QueryMode.TEXT
        else:
            mode = QueryMode.MIXED
    elif query_image_bytes and not query_text:
        mode = QueryMode.IMAGE
    elif query_image_bytes and query_text:
        mode = QueryMode.MIXED
    else:
        q_lower = (query_text or "").lower()
        has_visual_intent = any(re.search(pat, q_lower) for pat in VISUAL_INTENT_PATTERNS)
        if has_visual_intent:
            mode = QueryMode.VISUAL
        else:
            mode = QueryMode.MIXED

    # Calculate calibrated RRF fusion weights
    if mode == QueryMode.VISUAL:
        weights = {
            "weight_visual": 0.50,
            "weight_dense": 0.30,
            "weight_sparse": 0.20,
            "min_visual_score": 0.15,
        }
    elif mode == QueryMode.IMAGE:
        weights = {
            "weight_visual": 0.80,
            "weight_dense": 0.10,
            "weight_sparse": 0.10,
            "min_visual_score": 0.25,
        }
    elif mode == QueryMode.TEXT:
        weights = {
            "weight_visual": 0.15,
            "weight_dense": 0.45,
            "weight_sparse": 0.40,
            "min_visual_score": 0.10,
        }
    else:  # MIXED / HYBRID default
        weights = {
            "weight_visual": 0.35,
            "weight_dense": 0.35,
            "weight_sparse": 0.30,
            "min_visual_score": 0.12,
        }

    return {
        "mode": mode.value,
        "is_visual_dominant": mode in (QueryMode.VISUAL, QueryMode.IMAGE),
        "weights": weights,
    }
