"""
Phase 3: Hybrid Search Service
Combines dense semantic search with sparse/keyword search.
Currently implements dense search; hybrid + RRF to be added in Phase 4 (Week 5).
"""

import logging
from typing import Dict, List, Optional
from .embeddings import EmbeddingsManager

logger = logging.getLogger(__name__)


def hybrid_search(
    query: str,
    intent_data: Dict,
    qdrant_manager,
    top_k: int = 3
) -> List[Dict]:
    """
    Hybrid search: combines dense semantic search with keyword search.
    Phase 3: Dense search only
    Phase 4 (Week 5): Will add sparse/BM25 + Reciprocal Rank Fusion
    
    Args:
        query: Natural language query
        intent_data: Parsed intent from Phase 3
        qdrant_manager: Qdrant client instance
        top_k: Number of results to return
    
    Returns:
        List of ranked search results
    """
    try:
        logger.info(f"[Search] Hybrid search for: {query}")
        
        # Step 1: Generate query embedding
        logger.info(f"[Search] Generating query embedding...")
        query_embedding = generate_query_embedding(query)
        
        # Step 2: Dense semantic search
        logger.info(f"[Search] Running dense search...")
        dense_results = qdrant_manager.search(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=0.3
        )
        
        # Step 3: Format and enrich results with explanations
        enriched_results = enrich_results_with_explanation(
            dense_results,
            query,
            intent_data
        )
        
        logger.info(f"[Search] Returning {len(enriched_results)} results")
        return enriched_results
    
    except Exception as e:
        logger.error(f"[Search] Hybrid search failed: {str(e)}")
        return []


def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for search query.
    
    Args:
        query: Search query text
    
    Returns:
        Query embedding vector
    """
    try:
        manager = EmbeddingsManager()
        model = manager.get_model()
        
        # Generate embedding
        embedding = model.encode(query, convert_to_numpy=False)
        
        # Convert to list
        return embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
    
    except Exception as e:
        logger.error(f"[Search] Query embedding generation failed: {str(e)}")
        raise


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
        intent_data: Parsed intent data
    
    Returns:
        Enriched results with explanations
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
        
        enriched_result = {
            **result,
            "rank": idx + 1,
            "explanation": explanation,
            "relevance_percentage": int(result.get("relevance_score", 0) * 100)
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
        intent_data: Parsed intent
        rank: Result ranking
    
    Returns:
        Explanation string
    """
    try:
        relevance = result.get("relevance_score", 0)
        filename = result.get("filename", "Unknown")
        sentence_text = result.get("sentence_text", "")[:100]
        
        # Generate explanation based on relevance score
        if relevance > 0.8:
            explanation = f"Strong semantic match for '{intent_data.get('topic', query)}'"
        elif relevance > 0.6:
            explanation = f"Semantic match for '{intent_data.get('topic', query)}'"
        elif relevance > 0.4:
            explanation = f"Potential match related to: {', '.join(intent_data.get('keywords', [])[:2])}"
        else:
            explanation = "Weak semantic match - you may want to refine your query"
        
        return explanation
    
    except Exception as e:
        logger.warning(f"[Search] Explanation generation failed: {str(e)}")
        return "Search result matching this query"


# Phase 4: Placeholder functions (to be implemented in Week 5)

def sparse_keyword_search(query: str, qdrant_manager, top_k: int = 10) -> List[Dict]:
    """
    Sparse/keyword search using BM25-style scoring.
    TODO: Implement in Phase 4 (Week 5)
    """
    logger.info("[Search] Sparse search not yet implemented (Phase 4)")
    return []


def reciprocal_rank_fusion(dense_results: List[Dict], sparse_results: List[Dict], k: int = 60) -> List[Dict]:
    """
    Merge dense and sparse rankings using Reciprocal Rank Fusion.
    Formula: score(d) = Σ 1/(k + rank_i(d))
    TODO: Implement in Phase 4 (Week 5)
    
    Args:
        dense_results: Results from dense search
        sparse_results: Results from sparse search
        k: RRF parameter (constant for normalization)
    
    Returns:
        Merged ranking
    """
    logger.info("[Search] RRF not yet implemented (Phase 4)")
    return dense_results


def cross_encoder_rerank(candidates: List[Dict], query: str, top_k: int = 3) -> List[Dict]:
    """
    Rerank candidates using cross-encoder (ms-marco-MiniLM).
    TODO: Implement in Phase 4 (Week 5)
    
    Args:
        candidates: Candidate results to rerank
        query: Search query
        top_k: Number of final results
    
    Returns:
        Reranked results
    """
    logger.info("[Search] Cross-encoder reranking not yet implemented (Phase 4)")
    return candidates[:top_k]
