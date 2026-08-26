"""
IntentCloud - Qdrant Hybrid Vector Database Client

Stores:
    1. Dense semantic vectors (all-MiniLM-L6-v2, 384-dim)
    2. Sparse universal keyword vectors (deterministic feature hash)
    3. Chunk/document metadata

Dense:
    all-MiniLM-L6-v2 -> 384 dimensions

Sparse:
    deterministic feature-hashed unigram + bigram representation

This module is intentionally domain-independent.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    SparseIndexParams,
)

from services.embeddings import (
    EMBEDDING_DIM,
    SPARSE_HASH_DIM,
    generate_embeddings,
    generate_query_representation,
    compute_similarity,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

QDRANT_PATH = "./qdrant_storage"
COLLECTION_NAME = "intentcloud_docs"

MAX_SIMILARITY_FOR_DUPLICATE = 0.95

Path(QDRANT_PATH).mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------------------------
# QDRANT MANAGER
# ---------------------------------------------------------------------------

class QdrantIndexManager:
    """Persistent embedded Qdrant index for IntentCloud."""

    def __init__(self):

        try:

            logger.info(
                "[Qdrant] Initializing embedded client at %s",
                QDRANT_PATH,
            )

            self.client = QdrantClient(
                path=QDRANT_PATH
            )

            self._ensure_collection_exists()

            logger.info(
                "[Qdrant] Client initialized successfully"
            )

        except Exception as exc:

            logger.exception(
                "[Qdrant] Initialization failed: %s",
                exc,
            )

            raise


    # -----------------------------------------------------------------------
    # COLLECTION
    # -----------------------------------------------------------------------

    def _ensure_collection_exists(self):

        collections = self.client.get_collections()

        collection_names = [
            collection.name
            for collection in collections.collections
        ]

        if COLLECTION_NAME in collection_names:

            logger.info(
                "[Qdrant] Collection already exists: %s",
                COLLECTION_NAME,
            )

            return

        logger.info(
            "[Qdrant] Creating hybrid collection: %s",
            COLLECTION_NAME,
        )

        self.client.create_collection(

            collection_name=COLLECTION_NAME,

            # Dense vector.
            vectors_config={
                "dense": VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                )
            },

            # Sparse vector.
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(
                        on_disk=False
                    )
                )
            },
        )

        logger.info(
            "[Qdrant] Hybrid collection created"
        )


    # -----------------------------------------------------------------------
    # HEALTH
    # -----------------------------------------------------------------------

    def health_check(self) -> Dict:

        try:

            info = self.client.get_collection(
                COLLECTION_NAME
            )

            points = getattr(
                info,
                "points_count",
                getattr(
                    info,
                    "vectors_count",
                    0,
                ),
            )

            return {
                "status": "healthy",
                "collection": COLLECTION_NAME,
                "points_count": points,
                "embedding_dim": EMBEDDING_DIM,
                "sparse_hash_dim": SPARSE_HASH_DIM,
            }

        except Exception as exc:

            logger.error(
                "[Qdrant] Health check failed: %s",
                exc,
            )

            return {
                "status": "unhealthy",
                "error": str(exc),
            }


    # -----------------------------------------------------------------------
    # DUPLICATE DETECTION
    # -----------------------------------------------------------------------

    def _check_duplicate(
        self,
        document_embedding: List[float],
        file_id: str,
    ) -> Optional[Dict]:

        """
        Compare the COMPLETE document representation rather than the first
        sentence.

        Returns:
            Matching point metadata if duplicate detected.
            None otherwise.
        """

        try:

            results = self.client.search(
                collection_name=COLLECTION_NAME,

                query_vector=(
                    "dense",
                    document_embedding,
                ),

                limit=5,
                score_threshold=(
                    MAX_SIMILARITY_FOR_DUPLICATE
                ),
            )

            for result in results:

                existing_file_id = (
                    result.payload.get("file_id")
                    if result.payload
                    else None
                )

                if (
                    existing_file_id
                    and existing_file_id != file_id
                    and result.score >=
                    MAX_SIMILARITY_FOR_DUPLICATE
                ):

                    return {
                        "file_id": existing_file_id,
                        "filename": result.payload.get(
                            "filename"
                        ),
                        "score": float(
                            result.score
                        ),
                    }

            return None

        except Exception as exc:

            logger.warning(
                "[Duplicate Check] Failed: %s",
                exc,
            )

            # Do not block uploads because duplicate detection failed.
            return None


    # -----------------------------------------------------------------------
    # UPSERT DOCUMENT
    # -----------------------------------------------------------------------

    def upsert_document(
        self,
        file_id: str,
        filename: str,
        text_content: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:

        """
        Generate universal document representation and store every chunk.

        One uploaded file can produce many Qdrant points.

        Each point contains:
            dense vector
            sparse vector
            file metadata
            chunk metadata
            dynamic keywords
        """

        representation = generate_embeddings(
            text_content
        )

        chunks = representation["chunks"]

        if not chunks:

            return {
                "success": False,
                "reason": "No textual content extracted.",
                "file_id": file_id,
            }


        # ---------------------------------------------------------------
        # Duplicate detection on the document-level vector.
        # ---------------------------------------------------------------

        duplicate = self._check_duplicate(
            representation["document_embedding"],
            file_id,
        )

        if duplicate:

            logger.warning(
                "[Duplicate] %s matches %s with %.3f",
                filename,
                duplicate["filename"],
                duplicate["score"],
            )

            return {
                "success": False,
                "duplicate": True,
                "file_id": file_id,
                "existing_file": duplicate,
            }


        # ---------------------------------------------------------------
        # Universal metadata.
        # ---------------------------------------------------------------

        upload_time = datetime.utcnow().isoformat()

        custom_metadata = metadata or {}

        points: List[PointStruct] = []

        for chunk in chunks:

            chunk_index = chunk["chunk_index"]

            point_id = (
                f"{file_id}:{chunk_index}"
            )

            sparse_data = chunk[
                "sparse_vector"
            ]

            payload = {

                # File identity.
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,

                # Chunk identity.
                "chunk_index": chunk_index,

                # Original searchable content.
                "chunk_text": chunk["text"],

                # Universal dynamic keywords.
                "keywords": chunk["keywords"],

                # Upload information.
                "upload_time": upload_time,

                # Optional extractor metadata:
                # page, slide, sheet, section, etc.
                **custom_metadata,
            }


            point = PointStruct(

                id=point_id,

                vector={

                    "dense": chunk[
                        "embedding"
                    ],

                    "sparse": SparseVector(
                        indices=sparse_data[
                            "indices"
                        ],
                        values=sparse_data[
                            "values"
                        ],
                    ),
                },

                payload=payload,
            )

            points.append(point)


        # ---------------------------------------------------------------
        # Upsert.
        # ---------------------------------------------------------------

        self.client.upsert(

            collection_name=COLLECTION_NAME,

            points=points,
        )

        logger.info(
            "[Qdrant] Stored %d chunks for %s",
            len(points),
            filename,
        )

        return {
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "chunk_count": len(points),
            "document_keywords": representation[
                "document_keywords"
            ],
        }


    # -----------------------------------------------------------------------
    # DENSE SEARCH
    # -----------------------------------------------------------------------

    def dense_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        score_threshold: float = 0.20,
    ) -> List[Dict]:

        results = self.client.search(

            collection_name=COLLECTION_NAME,

            query_vector=(
                "dense",
                query_vector,
            ),

            limit=top_k,

            score_threshold=score_threshold,
        )

        return [
            self._format_result(result)
            for result in results
        ]


    # -----------------------------------------------------------------------
    # SPARSE SEARCH
    # -----------------------------------------------------------------------

    def sparse_search(
        self,
        sparse_vector: Dict,
        top_k: int = 10,
    ) -> List[Dict]:

        vector = SparseVector(

            indices=sparse_vector[
                "indices"
            ],

            values=sparse_vector[
                "values"
            ],
        )

        results = self.client.search(

            collection_name=COLLECTION_NAME,

            query_vector=(
                "sparse",
                vector,
            ),

            limit=top_k,
        )

        return [
            self._format_result(result)
            for result in results
        ]


    # -----------------------------------------------------------------------
    # HYBRID SEARCH + RRF
    # -----------------------------------------------------------------------

    def hybrid_search(
        self,
        query: str,
        top_k: int = 3,
        candidate_k: int = 20,
    ) -> List[Dict]:

        """
        Hybrid retrieval:

            query
              ↓
        dense representation
              +
        sparse representation
              ↓
        dense search + sparse search
              ↓
            RRF
              ↓
        final candidates
        """

        query_representation = (
            generate_query_representation(
                query
            )
        )


        dense_results = self.dense_search(

            query_representation[
                "embedding"
            ],

            top_k=candidate_k,
        )


        sparse_results = self.sparse_search(

            query_representation[
                "sparse_vector"
            ],

            top_k=candidate_k,
        )


        fused = self._rrf_fusion(

            dense_results,

            sparse_results,
        )


        return fused[:top_k]


    # -----------------------------------------------------------------------
    # RRF
    # -----------------------------------------------------------------------

    @staticmethod
    def _rrf_fusion(
        dense_results: List[Dict],
        sparse_results: List[Dict],
        k: int = 60,
    ) -> List[Dict]:

        """
        Reciprocal Rank Fusion.

        score(d) = sum(1 / (k + rank))
        """

        scores: Dict[str, float] = {}
        documents: Dict[str, Dict] = {}


        for rank, result in enumerate(
            dense_results,
            start=1,
        ):

            key = result["chunk_id"]

            scores[key] = (
                scores.get(key, 0.0)
                + 1.0 / (k + rank)
            )

            documents[key] = result


        for rank, result in enumerate(
            sparse_results,
            start=1,
        ):

            key = result["chunk_id"]

            scores[key] = (
                scores.get(key, 0.0)
                + 1.0 / (k + rank)
            )

            documents[key] = result


        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )


        output = []

        for chunk_id, score in ranked:

            item = dict(
                documents[chunk_id]
            )

            item["rrf_score"] = score

            output.append(item)


        return output


    # -----------------------------------------------------------------------
    # RESULT FORMAT
    # -----------------------------------------------------------------------

    @staticmethod
    def _format_result(result) -> Dict:

        payload = result.payload or {}

        return {

            "chunk_id": str(result.id),

            "file_id": payload.get(
                "file_id"
            ),

            "filename": payload.get(
                "filename"
            ),

            "file_type": payload.get(
                "file_type"
            ),

            "chunk_index": payload.get(
                "chunk_index"
            ),

            "chunk_text": payload.get(
                "chunk_text"
            ),

            "keywords": payload.get(
                "keywords",
                [],
            ),

            "upload_time": payload.get(
                "upload_time"
            ),

            "relevance_score": float(
                result.score
            ),
        }


    # -----------------------------------------------------------------------
    # COLLECTION STATS
    # -----------------------------------------------------------------------

    def get_collection_stats(self) -> Dict:

        try:

            info = self.client.get_collection(
                COLLECTION_NAME
            )

            points = getattr(
                info,
                "points_count",
                getattr(
                    info,
                    "vectors_count",
                    0,
                ),
            )

            return {

                "status": "ready",

                "collection": COLLECTION_NAME,

                "total_vectors": points,

                "embedding_dim": EMBEDDING_DIM,

                "sparse_hash_dim": SPARSE_HASH_DIM,

            }

        except Exception as exc:

            logger.error(
                "[Qdrant] Stats failed: %s",
                exc,
            )

            return {

                "status": "error",

                "total_vectors": 0,

                "error": str(exc),

            }
