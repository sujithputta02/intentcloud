"""
Phase 3-4: Hybrid Search Service
Combines dense semantic search with sparse/keyword search and RRF.
Phase 3: Dense search only (current)
Phase 4 (Week 5): Will add RRF and cross-encoder reranking
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def hybrid_search(
    query: str,
    intent_data: Dict,
    qdrant_manager,
    top_k: int = 3
) -> List[Dict]:
    """
    Hybrid search: combines dense semantic search with sparse keyword search.
    
    Phase 3 (current): Dense-only retrieval
    Phase 4 (Week 5): Dense + sparse + RRF + cross-encoder reranking
    
    Args:
        query: Natural language query
        intent_data: Parsed intent from Phase 3 (Phi-3)
        qdrant_manager: Qdrant client instance
        top_k: Number of results to return
    
    Returns:
        List of ranked search results with explanations
    """
    try:
        logger.info(f"[Search] Hybrid search for: {query}")
        
        # Use the unified hybrid_search from Qdrant that handles:
        # - Query representation (dense + sparse)
        # - Dense search
        # - Sparse search
        # - RRF fusion
        results = qdrant_manager.hybrid_search(
            query=query,
            top_k=top_k
        )
        
        # Enrich results with explanations and ranking
        enriched_results = enrich_results_with_explanation(
            results,
            query,
            intent_data
        )
        
        logger.info(f"[Search] Returning {len(enriched_results)} results")
        return enriched_results
    
    except Exception as e:
        logger.error(f"[Search] Hybrid search failed: {str(e)}")
        return []


def enrich_results_with_explanation(
    results: List[Dict],
    query: str,
    intent_data: Dict
) -> List[Dict]:
    """
    Enrich search results with explanations of why they matched.
    
    Args:
        results: Raw search results from Qdrant
        query: Original query
        intent_data: Parsed intent data (topic, keywords, confidence)
    
    Returns:
        Enriched results with explanations and rankings
    """
    enriched = []
    
    for idx, result in enumerate(results):
        # Generate explanation based on relevance score and intent
        explanation = generate_match_explanation(
            result,
            query,
            intent_data,
            rank=idx + 1
        )
        
        relevance_score = result.get("relevance_score", 0)
        
        enriched_result = {
            "rank": idx + 1,
            "file_id": result.get("file_id"),
            "filename": result.get("filename"),
            "sentence_text": result.get("chunk_text", ""),
            "relevance_score": relevance_score,
            "relevance_percentage": int(relevance_score * 100) if relevance_score else 0,
            "explanation": explanation,
            "upload_time": result.get("upload_time"),
            "keywords": result.get("keywords", []),
        }
        
        enriched.append(enriched_result)
    
    return enriched


def generate_match_explanation(
    result: Dict,
    query: str,
    intent_data: Dict,
    rank: int
) -> str:
    """
    Generate human-readable explanation for why a document matched the query.
    
    Args:
        result: Search result from Qdrant
        query: Original query
        intent_data: Parsed intent (topic, keywords)
        rank: Result ranking
    
    Returns:
        Explanation string
    """
    try:
        relevance = result.get("relevance_score", 0)
        topic = intent_data.get("topic", query)
        keywords = intent_data.get("keywords", [])
        
        # Score-based explanation
        if relevance >= 0.8:
            explanation = f"Strong semantic match for '{topic}'"
        elif relevance >= 0.6:
            explanation = f"Semantic match for '{topic}'"
        elif relevance >= 0.4:
            explanation = f"Potential match related to: {', '.join(keywords[:2])}"
        else:
            explanation = "Weak semantic match - you may want to refine your query"
        
        return explanation
    
    except Exception as e:
        logger.warning(f"[Search] Explanation generation failed: {str(e)}")
        return "Search result matching this query"
