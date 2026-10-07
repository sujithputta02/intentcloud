"""
IntentCloud - Phase 4: Hybrid Retrieval, RRF Fusion & Cross-Encoder Reranking

Architecture:
1. Query Intent Parsing (Phi-3 / Fallback)
2. Dual Query Representation (384-d Dense + 1M-d Sparse Feature Hash)
3. Parallel Vector Candidate Retrieval (Qdrant Dense + Sparse)
4. Reciprocal Rank Fusion (RRF, k=60):
      score(d) = sum_m (1 / (60 + rank_m(d)))
5. Cross-Encoder Reranking (ms-marco-MiniLM-L-6-v2) over Top-N Fused Candidates
6. Sentence-Level Matched Snippet Extraction & Citation
7. Confidence Threshold Assessment ("No Confident Match Found" Fallback)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from services.embeddings import generate_query_representation
from services.reranker import get_reranker, get_reranker_device, DEFAULT_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

# Default constants
RRF_K_CONSTANT = 60
DEFAULT_CANDIDATE_K = 20
DEFAULT_TOP_K = 3

# Baseline-mode gating uses raw Qdrant retrieval scores (cosine / RRF), not cross-encoder sigmoid.
DENSE_BASELINE_MIN_SCORE = 0.35
SPARSE_BASELINE_MIN_SCORE = 0.15
RRF_BASELINE_MIN_SCORE = 0.20


def reciprocal_rank_fusion(
    dense_results: List[Dict],
    sparse_results: List[Dict],
    k: int = RRF_K_CONSTANT,
) -> List[Dict]:
    """
    Perform Reciprocal Rank Fusion (RRF) to merge dense and sparse candidate rankings.

    Formula (PRD §5.4):
        score_RRF(d) = sum_{m in {dense, sparse}} (1 / (k + rank_m(d)))

    Args:
        dense_results: Ordered list of dense search hits
        sparse_results: Ordered list of sparse search hits
        k: Smoothing constant (default: 60)

    Returns:
        Sorted list of fused candidate documents with RRF scores
    """
    rrf_scores: Dict[str, float] = {}
    dense_ranks: Dict[str, int] = {}
    sparse_ranks: Dict[str, int] = {}
    documents: Dict[str, Dict] = {}

    # Accumulate dense rankings
    for rank, item in enumerate(dense_results, start=1):
        doc_key = item.get("chunk_id") or f"{item.get('file_id')}:{item.get('chunk_index', 0)}"
        rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (k + rank))
        dense_ranks[doc_key] = rank
        documents[doc_key] = item

    # Accumulate sparse rankings
    for rank, item in enumerate(sparse_results, start=1):
        doc_key = item.get("chunk_id") or f"{item.get('file_id')}:{item.get('chunk_index', 0)}"
        rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (k + rank))
        sparse_ranks[doc_key] = rank
        if doc_key not in documents:
            documents[doc_key] = item

    # Sort candidates by combined RRF score descending
    sorted_keys = sorted(rrf_scores.keys(), key=lambda key: rrf_scores[key], reverse=True)

    fused_candidates = []
    for rank, key in enumerate(sorted_keys, start=1):
        doc = dict(documents[key])
        doc["rrf_rank"] = rank
        doc["rrf_score"] = round(rrf_scores[key], 6)
        doc["dense_rank"] = dense_ranks.get(key)
        doc["sparse_rank"] = sparse_ranks.get(key)
        fused_candidates.append(doc)

    logger.info(
        "[RRF] Fused %d dense + %d sparse candidates -> %d unique documents",
        len(dense_results),
        len(sparse_results),
        len(fused_candidates),
    )
    return fused_candidates


SPELLING_MAP = {
    "colour": "color",
    "colours": "colors",
    "behaviour": "behavior",
    "synchronise": "synchronize",
    "optimise": "optimize",
}


def normalize_spelling(text: str) -> str:
    """Normalize common UK/US spelling variants for consistent embedding alignment."""
    if not text:
        return ""
    words = text.split()
    return " ".join(SPELLING_MAP.get(w.lower(), w) for w in words)


def build_intent_clean_query(query: str, intent_data: Optional[Dict] = None) -> str:
    """Extract clean intent search query without conversational filler words."""
    import re
    # 1. Strip conversational filler prefix & suffix
    clean = re.sub(
        r"^(i need an?|i want an?|show me|find me|give me|where is|can you find|search for|looking for)\s+",
        "",
        query,
        flags=re.IGNORECASE
    )
    clean = re.sub(r"\s+(file|document|photo|image|picture)\s*\??$", "", clean, flags=re.IGNORECASE).strip(" ?.")
    clean = normalize_spelling(clean)

    # 2. Also check if parsed intent has high-value topical keywords
    intent_data = intent_data or {}
    keywords = intent_data.get("keywords") or []
    meaningful_kw = [
        normalize_spelling(str(k))
        for k in keywords
        if str(k).lower() not in {"need", "want", "file", "document", "photo", "image", "find", "show", "give"}
    ]

    if clean and len(clean.split()) >= 2:
        if "service now" in clean.lower() and "servicenow" not in clean.lower():
            clean = clean.lower().replace("service now", "servicenow")
        return clean

    if meaningful_kw:
        return " ".join(meaningful_kw)

    res = clean or normalize_spelling(query)
    if "service now" in res.lower() and "servicenow" not in res.lower():
        res = res.lower().replace("service now", "servicenow")
    return res


def build_retrieval_query(query: str, intent_data: Optional[Dict] = None) -> str:
    """
    Expand the user query with parsed intent for embedding/sparse retrieval.
    Improves natural-language queries that omit exact document keywords.
    """
    clean_norm = normalize_spelling(query)
    intent_data = intent_data or {}
    topic = str(intent_data.get("topic", "")).strip()
    keywords = intent_data.get("keywords") or []

    parts = [clean_norm]
    if "service now" in clean_norm.lower() and "servicenow" not in clean_norm.lower():
        parts.append("servicenow")
    if topic and topic.lower() not in clean_norm.lower():
        parts.append(normalize_spelling(topic))
    if keywords:
        kw_text = " ".join(normalize_spelling(str(k)) for k in keywords[:6] if k)
        if kw_text and kw_text.lower() not in clean_norm.lower():
            parts.append(kw_text)

    # Detect visual intent and expand with visual search terms
    visual_terms = [
        "color", "colour", "palette", "swatch", "hex",
        "diagram", "topology", "architecture", "image",
        "photo", "slide", "brand deck", "deck", "presentation",
        "dashboard", "workspace", "screenshot", "ui"
    ]
    if any(v in clean_norm.lower() for v in visual_terms):
        parts.append("visual concept dashboard workspace ui image photo")

    return ". ".join(parts)


def group_and_expand_document_evidence(
    candidates: List[Dict],
    qdrant_manager,
    max_files: int = 6,
) -> List[Dict]:
    """
    Document-Memory Evidence Grouping & Context Window Expansion.
    1. Groups multiple candidate chunks by document (file_id).
    2. Identifies the primary salient chunk and all supporting evidence chunks.
    3. Expands primary chunk context with neighboring chunks: [C_{i-1}] + [C_i] + [C_{i+1}].
    4. Aggregates matched sections and calculates multi-chunk evidence coverage.
    """
    file_groups: Dict[str, List[Dict]] = {}
    for cand in candidates:
        fid = cand.get("file_id")
        if fid:
            file_groups.setdefault(fid, []).append(cand)

    document_candidates: List[Dict] = []

    for fid, group in file_groups.items():
        # Highest scoring chunk is primary anchor
        primary = dict(group[0])
        evidence_count = len(group)

        # Collect distinct sections where evidence appeared
        matched_sections = list(dict.fromkeys(
            [c.get("parent_section") for c in group if c.get("parent_section")]
        ))

        primary["evidence_count"] = evidence_count
        primary["matched_sections"] = matched_sections
        primary["evidence_snippets"] = [
            c.get("chunk_text", "")[:200] for c in group[:3]
        ]
        primary["evidence_chunks"] = group

        # Evidence coverage boost: documents matching across multiple sections/chunks get boosted
        if evidence_count > 1:
            evidence_boost = min(0.005, (evidence_count - 1) * 0.0015)
            primary["rrf_score"] = round(primary.get("rrf_score", 0.0) + evidence_boost, 6)

        document_candidates.append(primary)

    # Sort documents by score FIRST before doing any expensive neighbor expansions
    document_candidates.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)
    top_candidates = document_candidates[:max_files]

    # Context Window Expansion: Retrieve surrounding neighbors ONLY for top candidates
    for doc in top_candidates:
        fid = doc.get("file_id")
        chunk_text = doc.get("chunk_text", "")
        if qdrant_manager and hasattr(qdrant_manager, "get_surrounding_chunks"):
            # Only do extra SQLite fetch if chunk text is brief (< 350 chars)
            if len(chunk_text) < 350:
                chunk_idx = doc.get("chunk_index", 0)
                surrounding = qdrant_manager.get_surrounding_chunks(fid, chunk_idx)
                expanded_text = surrounding.get("expanded_text")
                if expanded_text:
                    doc["expanded_text"] = expanded_text
                    doc["expanded_context"] = expanded_text
                if not doc.get("parent_section") and surrounding.get("parent_section"):
                    doc["parent_section"] = surrounding.get("parent_section")
                if not doc.get("section_path") and surrounding.get("section_path"):
                    doc["section_path"] = surrounding.get("section_path")

    return top_candidates


def deduplicate_results_by_file(results: List[Dict], top_k: int) -> List[Dict]:
    """Keep the best-scoring chunk per file so users see distinct documents."""
    seen_files: set[str] = set()
    deduped: List[Dict] = []

    for item in results:
        file_id = item.get("file_id")
        if not file_id or file_id in seen_files:
            continue
        seen_files.add(file_id)
        deduped.append(item)
        if len(deduped) >= top_k:
            break

    for rank, item in enumerate(deduped, start=1):
        item["rank"] = rank

    return deduped


def execute_search_pipeline(
    query: str,
    intent_data: Dict,
    qdrant_manager,
    top_k: int = DEFAULT_TOP_K,
    search_mode: str = "hybrid",
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    candidate_k: int = DEFAULT_CANDIDATE_K,
) -> Dict[str, Any]:
    """
    Execute the full retrieval pipeline with timing and metrics.

    Modes supported:
        - "hybrid": Dense + Sparse + RRF + Cross-Encoder Reranking (Phase 4 Default)
        - "dense": Dense semantic search only
        - "sparse": Sparse keyword search only
        - "rrf_only": Hybrid Dense + Sparse with RRF, without second-stage cross-encoder
    """
    start_time = time.perf_counter()

    try:
        retrieval_query = build_retrieval_query(query, intent_data)
        query_rep = generate_query_representation(retrieval_query)
        dense_vector = query_rep["embedding"]
        sparse_vector = query_rep["sparse_vector"]

        dense_candidates: List[Dict] = []
        sparse_candidates: List[Dict] = []
        fused_candidates: List[Dict] = []
        final_results: List[Dict] = []
        is_confident = True
        confidence_msg = "Match verified"

        search_mode = search_mode.lower().strip()

        if search_mode == "sparse":
            # Sparse / Keyword Only Baseline
            logger.info("[Search] Running Sparse-only search for: %s", query)
            sparse_candidates = qdrant_manager.sparse_search(
                sparse_vector=sparse_vector,
                top_k=candidate_k,
            )
            final_results = _format_baseline_results(
                deduplicate_results_by_file(sparse_candidates, top_k),
                query=query,
                intent_data=intent_data,
                mode_name="Sparse Keyword",
            )
            is_confident = len(final_results) > 0 and final_results[0]["relevance_score"] >= SPARSE_BASELINE_MIN_SCORE
            confidence_msg = "Sparse keyword search completed."
            if not is_confident:
                final_results = []

        elif search_mode == "dense":
            # Dense Only Baseline
            logger.info("[Search] Running Dense-only search for: %s", query)
            dense_candidates = qdrant_manager.dense_search(
                query_vector=dense_vector,
                top_k=candidate_k,
                score_threshold=0.15,
            )
            final_results = _format_baseline_results(
                deduplicate_results_by_file(dense_candidates, top_k),
                query=query,
                intent_data=intent_data,
                mode_name="Dense Semantic",
            )
            is_confident = len(final_results) > 0 and final_results[0]["relevance_score"] >= DENSE_BASELINE_MIN_SCORE
            confidence_msg = "Dense semantic search completed."
            if not is_confident:
                final_results = []

        elif search_mode == "rrf_only":
            # Hybrid RRF without Cross-Encoder Reranking
            logger.info("[Search] Running Hybrid RRF search (no rerank) for: %s", query)
            dense_candidates = qdrant_manager.dense_search(
                query_vector=dense_vector,
                top_k=candidate_k,
                score_threshold=0.10,
            )
            sparse_candidates = qdrant_manager.sparse_search(
                sparse_vector=sparse_vector,
                top_k=candidate_k,
            )
            fused_candidates = reciprocal_rank_fusion(
                dense_results=dense_candidates,
                sparse_results=sparse_candidates,
                k=RRF_K_CONSTANT,
            )
            final_results = _format_baseline_results(
                deduplicate_results_by_file(fused_candidates, top_k),
                query=query,
                intent_data=intent_data,
                mode_name="Hybrid RRF",
            )
            is_confident = len(final_results) > 0 and final_results[0]["relevance_score"] >= RRF_BASELINE_MIN_SCORE
            confidence_msg = "Hybrid RRF fusion completed."
            if not is_confident:
                final_results = []

        else:
            # Phase 4 Hybrid + RRF + Cross-Encoder Rerank (Default & Recommended)
            logger.info("[Search] Running Phase 4 Hybrid + RRF + Rerank pipeline for: %s", query)

            dense_candidates = qdrant_manager.dense_search(
                query_vector=dense_vector,
                top_k=candidate_k,
                score_threshold=0.05,
            )
            sparse_candidates = qdrant_manager.sparse_search(
                sparse_vector=sparse_vector,
                top_k=candidate_k,
            )

            # Reciprocal Rank Fusion
            fused_candidates = reciprocal_rank_fusion(
                dense_results=dense_candidates,
                sparse_results=sparse_candidates,
                k=RRF_K_CONSTANT,
            )

            if not fused_candidates:
                # If no candidates found, fallback to dense or return empty
                logger.warning("[Search] No candidates retrieved from dense or sparse indices")
                return {
                    "results": [],
                    "is_confident_match": False,
                    "confidence_message": "No matching documents found in corpus.",
                    "search_mode": "hybrid",
                    "metrics": {
                        "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                        "dense_candidates": 0,
                        "sparse_candidates": 0,
                        "fused_candidates": 0,
                        "reranked_count": 0,
                    },
                }

            # Objective 3: Query-Aware Metadata Lineage & Recency Conditioning
            lower_q = query.lower()
            intent_type = intent_data.get("intent_type", "find")
            wants_recent = "recent" in lower_q or "latest" in lower_q or "newest" in lower_q or intent_type == "recent"
            wants_historical = "historical" in lower_q or "original" in lower_q or "draft" in lower_q or "v1" in lower_q
            
            for cand in fused_candidates:
                meta_boost = 0.0
                fname = cand.get("filename", "").lower()
                is_latest = cand.get("is_latest", True)
                version_num = cand.get("version_number", 1)
                
                if wants_recent:
                    if is_latest or "_v2" in fname or "_v3" in fname:
                        meta_boost += 0.003
                elif wants_historical:
                    if not is_latest or "_v1" in fname or "draft" in fname:
                        meta_boost += 0.003
                
                if meta_boost > 0:
                    cand["rrf_score"] = round(cand["rrf_score"] + meta_boost, 6)
            
            # Re-sort after metadata lineage adjustment
            fused_candidates.sort(key=lambda x: x.get("rrf_score", 0.0), reverse=True)

            # Objective 5: Cross-Encoder Reranking with dual query alignment (Default Hybrid Pipeline)
            reranker = get_reranker()
            intent_query = build_intent_clean_query(query, intent_data)

            # Adaptive fast-path bypass is strictly reserved for explicit "adaptive" mode
            can_bypass = False
            top_gap: float = 0.0
            if search_mode == "adaptive" and len(fused_candidates) >= 2:
                top_gap = fused_candidates[0]["rrf_score"] - fused_candidates[1]["rrf_score"]
                if top_gap >= 0.02:
                    can_bypass = True

            if can_bypass:
                logger.info("[Adaptive Route] Fast-path routing: Bypassing cross-encoder (margin=%.4f)", top_gap)
                final_results = _format_baseline_results(
                    deduplicate_results_by_file(fused_candidates, top_k),
                    query=query,
                    intent_data=intent_data,
                    mode_name="Adaptive Fast-Path (RRF Bypass)",
                )
                is_confident = len(final_results) > 0 and final_results[0]["relevance_score"] >= RRF_BASELINE_MIN_SCORE
                confidence_msg = "Adaptive Fast-Path match verified."
            else:
                # Deep-Path: Cross-Encoder Reranking with Multi-Chunk Evidence Grouping & Context Expansion
                document_candidates = group_and_expand_document_evidence(
                    fused_candidates,
                    qdrant_manager,
                    max_files=max(top_k * 2, 6),
                )
                final_results, is_confident, confidence_msg = reranker.rerank_candidates(
                    query=query,
                    candidates=document_candidates,
                    top_k=top_k,
                    confidence_threshold=confidence_threshold,
                    intent_query=intent_query,
                )

            if not is_confident:
                final_results = []

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "[Search] Completed %s pipeline in %.2f ms (results: %d, confident: %s)",
            search_mode,
            elapsed_ms,
            len(final_results),
            is_confident,
        )

        return {
            "results": final_results,
            "is_confident_match": is_confident,
            "confidence_message": confidence_msg,
            "search_mode": search_mode,
            "metrics": {
                "latency_ms": elapsed_ms,
                "dense_candidates": len(dense_candidates),
                "sparse_candidates": len(sparse_candidates),
                "fused_candidates": len(fused_candidates),
                "reranked_count": len(final_results),
                "device": get_reranker_device(),
            },
        }

    except Exception as exc:
        logger.exception("[Search] Pipeline execution failed: %s", exc)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "results": [],
            "is_confident_match": False,
            "confidence_message": f"Search execution encountered an error: {exc}",
            "search_mode": search_mode,
            "metrics": {
                "latency_ms": elapsed_ms,
                "dense_candidates": 0,
                "sparse_candidates": 0,
                "fused_candidates": 0,
                "reranked_count": 0,
            },
        }


def hybrid_search(
    query: str,
    intent_data: Dict,
    qdrant_manager,
    top_k: int = DEFAULT_TOP_K,
    search_mode: str = "hybrid",
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> List[Dict]:
    """
    Main entry point for hybrid search in IntentCloud.
    Returns the enriched top_k results list.
    """
    search_output = execute_search_pipeline(
        query=query,
        intent_data=intent_data,
        qdrant_manager=qdrant_manager,
        top_k=top_k,
        search_mode=search_mode,
        confidence_threshold=confidence_threshold,
    )
    return search_output.get("results", [])


def _format_baseline_results(
    raw_results: List[Dict],
    query: str,
    intent_data: Dict,
    mode_name: str,
) -> List[Dict]:
    """Format and enrich raw candidate hits for baseline non-reranked modes."""
    formatted = []
    for rank, item in enumerate(raw_results, start=1):
        rel_score = float(item.get("relevance_score") or item.get("rrf_score") or 0.0)
        # Normalize score to percentage
        pct = int(min(100, max(0, rel_score * 100))) if rel_score <= 1.0 else int(min(100, rel_score))

        chunk_text = item.get("chunk_text") or item.get("sentence_text", "")
        # Pick first 2 sentences as snippet
        snippet = chunk_text[:280] + ("..." if len(chunk_text) > 280 else "")

        topic = intent_data.get("topic", query)
        keywords = intent_data.get("keywords", [])
        kw_str = ", ".join(keywords[:3]) if keywords else "key terms"

        explanation = (
            f"Rank #{rank} ({mode_name}): Direct retrieval match for '{topic}' "
            f"associating keywords [{kw_str}]."
        )

        formatted.append(
            {
                "rank": rank,
                "file_id": item.get("file_id"),
                "filename": item.get("filename"),
                "file_type": item.get("file_type") or "txt",
                "chunk_id": item.get("chunk_id"),
                "chunk_index": item.get("chunk_index", 0),
                "sentence_text": snippet,
                "matched_snippet": snippet,
                "parent_section": item.get("parent_section", ""),
                "section_path": item.get("section_path", []),
                "evidence_count": item.get("evidence_count", 1),
                "matched_sections": item.get("matched_sections", []),
                "expanded_context": item.get("expanded_text") or item.get("expanded_context", ""),
                "relevance_score": round(rel_score, 4),
                "relevance_percentage": pct,
                "rrf_score": item.get("rrf_score", 0.0),
                "rerank_score": round(rel_score, 4),
                "explanation": explanation,
                "upload_time": item.get("upload_time"),
                "keywords": item.get("keywords", []),
                "folder_id": item.get("folder_id"),
                "folder_path": item.get("folder_path", "/"),
            }
        )

    return formatted
