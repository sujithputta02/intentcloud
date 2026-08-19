"""
Phase 2: Qdrant Vector Database Client
Embedded Qdrant for hybrid (dense + sparse) vector search.
Stores documents with metadata: filename, topic_tags, upload_time.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Payload
from typing import Dict, List, Optional
import logging
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
QDRANT_PATH = "./qdrant_storage"
COLLECTION_NAME = "intentcloud_docs"
VECTOR_DIM = 384  # all-MiniLM-L6-v2 dimension
MAX_SIMILARITY_FOR_DUPLICATE = 0.95  # Flag as duplicate if similarity >= this

# Create storage directory
Path(QDRANT_PATH).mkdir(exist_ok=True)


class QdrantIndexManager:
    """Manages Qdrant vector index and document storage."""
    
    def __init__(self):
        """Initialize Qdrant embedded client."""
        try:
            logger.info(f"[Qdrant] Initializing embedded client at {QDRANT_PATH}")
            self.client = QdrantClient(path=QDRANT_PATH)
            
            # Create collection if it doesn't exist
            self._ensure_collection_exists()
            
            logger.info(f"[Qdrant] Client initialized successfully")
        except Exception as e:
            logger.error(f"[Qdrant] Initialization failed: {str(e)}")
            raise
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if COLLECTION_NAME not in collection_names:
                logger.info(f"[Qdrant] Creating collection: {COLLECTION_NAME}")
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_DIM,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"[Qdrant] Collection created successfully")
            else:
                logger.info(f"[Qdrant] Collection already exists: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"[Qdrant] Collection creation failed: {str(e)}")
            raise
    
    def health_check(self) -> Dict:
        """
        Check Qdrant health status.
        
        Returns:
            Health status dict
        """
        try:
            info = self.client.get_collection(COLLECTION_NAME)
            pts = getattr(info, "points_count", getattr(info, "vectors_count", 0))
            return {
                "status": "healthy",
                "collection": COLLECTION_NAME,
                "vectors_count": pts,
                "points_count": pts
            }
        except Exception as e:
            logger.error(f"[Qdrant] Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def upsert_document(
        self,
        file_id: str,
        filename: str,
        text_content: str,
        embeddings_data: Dict
    ) -> bool:
        """
        Upsert document with embeddings into Qdrant.
        Includes duplicate detection before insertion.
        
        Args:
            file_id: Unique document ID
            filename: Original filename
            text_content: Full document text
            embeddings_data: Output from embeddings.generate_embeddings()
        
        Returns:
            True if successful, False if detected as duplicate
        """
        try:
            logger.info(f"[Qdrant] Upserting file_id={file_id}, filename={filename}")
            
            embeddings = embeddings_data["embeddings"]
            sentences = embeddings_data["sentences"]
            
            if not embeddings or not sentences:
                logger.warning(f"[Qdrant] No embeddings to upsert for {file_id}")
                return False
            
            # Step 1: Check for duplicates using first embedding
            if self._check_duplicate(embeddings[0], file_id):
                logger.warning(f"[Qdrant] File {file_id} detected as duplicate or too similar")
                return False
            
            # Step 2: Create points for Qdrant
            points = []
            for idx, (embedding, sentence) in enumerate(zip(embeddings, sentences)):
                point_id = hash((file_id, idx)) % (2**31)  # Ensure positive int
                
                payload = {
                    "file_id": file_id,
                    "filename": filename,
                    "sentence_index": idx,
                    "sentence_text": sentence,
                    "upload_time": datetime.utcnow().isoformat(),
                    "text_preview": sentence[:100]
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Step 3: Upsert to Qdrant
            logger.info(f"[Qdrant] Upserting {len(points)} vectors...")
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            
            logger.info(f"[Qdrant] Successfully upserted {len(points)} vectors")
            return True
        
        except Exception as e:
            logger.error(f"[Qdrant] Upsert failed: {str(e)}")
            raise
    
    def _check_duplicate(self, embedding: List[float], file_id: str) -> bool:
        """
        Check if an embedding is too similar to existing ones (duplicate detection).
        
        Args:
            embedding: Document embedding
            file_id: Current file ID (to exclude from comparison)
        
        Returns:
            True if detected as duplicate, False otherwise
        """
        try:
            # Search for similar embeddings
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=embedding,
                limit=1,
                score_threshold=MAX_SIMILARITY_FOR_DUPLICATE
            )
            
            for result in results:
                # If we found a similar existing point
                if result.score >= MAX_SIMILARITY_FOR_DUPLICATE:
                    existing_file_id = result.payload.get("file_id")
                    if existing_file_id != file_id:
                        logger.warning(
                            f"[Duplicate] Similarity {result.score:.3f} with "
                            f"{existing_file_id} (threshold: {MAX_SIMILARITY_FOR_DUPLICATE})"
                        )
                        return True
            
            return False
        except Exception as e:
            logger.warning(f"[Duplicate Check] Error: {str(e)}, proceeding without check")
            return False
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        score_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Dense semantic search in Qdrant.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            score_threshold: Minimum relevance score
        
        Returns:
            List of search results with metadata
        """
        try:
            logger.info(f"[Qdrant] Searching for top_{top_k}")
            
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "file_id": result.payload.get("file_id"),
                    "filename": result.payload.get("filename"),
                    "sentence_text": result.payload.get("sentence_text"),
                    "relevance_score": result.score,
                    "upload_time": result.payload.get("upload_time")
                })
            
            logger.info(f"[Qdrant] Returned {len(formatted_results)} results")
            return formatted_results
        
        except Exception as e:
            logger.error(f"[Qdrant] Search failed: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """
        Get collection statistics for dashboard.
        
        Returns:
            Stats dict with file count, topics, etc.
        """
        try:
            info = self.client.get_collection(COLLECTION_NAME)
            
            # Get unique file IDs (approximate)
            scroll_results = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000
            )
            
            unique_files = set()
            for point in scroll_results[0]:
                unique_files.add(point.payload.get("file_id"))
            
            pts = getattr(info, "points_count", getattr(info, "vectors_count", 0))
            return {
                "total_vectors": pts,
                "total_files": len(unique_files),
                "collection": COLLECTION_NAME,
                "vector_dim": VECTOR_DIM,
                "status": "ready"
            }
        
        except Exception as e:
            logger.error(f"[Qdrant] Stats retrieval failed: {str(e)}")
            return {
                "total_vectors": 0,
                "total_files": 0,
                "error": str(e)
            }
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """
        Get file path from file_id.
        Used for download endpoint.
        
        Args:
            file_id: Document ID
        
        Returns:
            File path or None
        """
        try:
            uploads_dir = Path("./uploads")
            # Try common extensions
            for ext in [".pdf", ".docx", ".txt"]:
                file_path = uploads_dir / f"{file_id}{ext}"
                if file_path.exists():
                    return str(file_path)
            return None
        except Exception as e:
            logger.error(f"[Qdrant] Get file path failed: {str(e)}")
            return None
