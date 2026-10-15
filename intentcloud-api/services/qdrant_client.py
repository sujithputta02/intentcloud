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

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    SparseIndexParams,
    PayloadSchemaType,
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

# Deterministic UUID namespace for chunk point IDs (Qdrant requires UUID or int).
POINT_ID_NAMESPACE = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

Path(QDRANT_PATH).mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------------------------
# QDRANT MANAGER
# ---------------------------------------------------------------------------

class QdrantIndexManager:
    """Persistent embedded Qdrant index for IntentCloud."""

    @staticmethod
    def _make_point_id(file_id: str, chunk_index: int) -> str:
        """Derive a stable Qdrant-compatible UUID for a file chunk."""
        return str(uuid.uuid5(POINT_ID_NAMESPACE, f"{file_id}:{chunk_index}"))

    def __init__(self, storage_path: Optional[str] = None, collection_name: Optional[str] = None):

        self.storage_path = storage_path or QDRANT_PATH
        self.collection_name = collection_name or COLLECTION_NAME
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        try:

            logger.info(
                "[Qdrant] Initializing embedded client at %s",
                self.storage_path,
            )

            self.client = QdrantClient(
                path=self.storage_path
            )

            self._ensure_collection_exists()

            # Ensure ultra-fast O(1) keyword indexing on file_id and filename
            for field in ["file_id", "filename"]:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                except Exception:
                    pass

            logger.info(
                "[Qdrant] Client initialized successfully with payload indexes"
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

        if self.collection_name in collection_names:

            logger.info(
                "[Qdrant] Collection already exists: %s",
                self.collection_name,
            )

            return

        logger.info(
            "[Qdrant] Creating hybrid collection: %s",
            self.collection_name,
        )

        self.client.create_collection(

            collection_name=self.collection_name,

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
            "[Qdrant] Hybrid collection created: %s",
            self.collection_name,
        )


    # -----------------------------------------------------------------------
    # HEALTH
    # -----------------------------------------------------------------------

    def health_check(self) -> Dict:

        try:

            info = self.client.get_collection(
                self.collection_name
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
                "collection": self.collection_name,
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
    # QUERY HELPERS (qdrant-client 1.19+ uses query_points, not search)
    # -----------------------------------------------------------------------

    def _query_vector(
        self,
        query_vector: Union[List[float], SparseVector],
        using: str,
        limit: int,
        score_threshold: Optional[float] = None,
    ) -> List[Any]:
        """Run a named-vector similarity query and return scored points."""
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using=using,
            limit=limit,
            score_threshold=score_threshold,
        )
        return list(response.points or [])

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

            results = self._query_vector(
                query_vector=document_embedding,
                using="dense",
                limit=5,
                score_threshold=MAX_SIMILARITY_FOR_DUPLICATE,
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
        text_content: Union[str, Dict[str, Any]],
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
            structural graph pointers (prev/next chunk, section path)
            dynamic keywords
        """

        representation = generate_embeddings(
            text_content,
            doc_title=filename,
            doc_category=file_type,
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

        is_duplicate = False
        duplicate_info = None
        if duplicate:
            logger.info(
                "[Duplicate Notice] %s matches %s with %.3f - indexing document to ensure search visibility",
                filename,
                duplicate["filename"],
                duplicate["score"],
            )
            is_duplicate = True
            duplicate_info = duplicate


        # ---------------------------------------------------------------
        # Universal metadata.
        # ---------------------------------------------------------------

        upload_time = datetime.now(timezone.utc).isoformat()

        custom_metadata = metadata or {}

        points: List[PointStruct] = []

        for chunk in chunks:

            chunk_index = chunk["chunk_index"]

            point_id = self._make_point_id(file_id, chunk_index)
            chunk_key = f"{file_id}:{chunk_index}"

            sparse_data = chunk[
                "sparse_vector"
            ]

            prev_idx = chunk.get("prev_chunk_index")
            next_idx = chunk.get("next_chunk_index")

            payload = {

                # File identity.
                "file_id": file_id,
                "filename": filename,
                "file_type": file_type,

                # Chunk identity.
                "chunk_index": chunk_index,
                "chunk_id": chunk_key,

                # Original searchable content & enriched structural context.
                "chunk_text": chunk["text"],
                "enriched_text": chunk.get("enriched_text", chunk["text"]),

                # Document-Memory Structural Graph Pointers
                "section_path": chunk.get("section_path", []),
                "parent_section": chunk.get("parent_section", ""),
                "page": chunk.get("page", 1),
                "prev_chunk_index": prev_idx,
                "next_chunk_index": next_idx,
                "prev_chunk_id": f"{file_id}:{prev_idx}" if prev_idx is not None else None,
                "next_chunk_id": f"{file_id}:{next_idx}" if next_idx is not None else None,
                "unit_type": chunk.get("unit_type", "chunk"),
                "is_figure": chunk.get("is_figure", False),
                "figure_data": chunk.get("figure_data"),

                # Universal dynamic keywords.
                "keywords": chunk["keywords"],


                # Upload information.
                "upload_time": upload_time,

                # Hierarchical folder location
                "folder_id": custom_metadata.get("folder_id"),
                "folder_path": custom_metadata.get("folder_path", "/"),

                # Optional extractor metadata:
                # page, slide, sheet, section, etc.
                **custom_metadata,
            }

            point = PointStruct(
                id=point_id,
                vector={
                    "dense": chunk["dense_vector"],
                    "sparse": SparseVector(
                        indices=sparse_data["indices"],
                        values=sparse_data["values"],
                    ),
                },
                payload=payload,
            )

            points.append(point)


        # ---------------------------------------------------------------
        # Upsert.
        # ---------------------------------------------------------------

        self.client.upsert(

            collection_name=self.collection_name,

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
            "duplicate": is_duplicate,
            "existing_file": duplicate_info,
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

        results = self._query_vector(
            query_vector=query_vector,
            using="dense",
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

        results = self._query_vector(
            query_vector=vector,
            using="sparse",
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

        chunk_id = payload.get("chunk_id") or str(result.id)

        return {

            "chunk_id": chunk_id,

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

            "enriched_text": payload.get(
                "enriched_text",
                payload.get("chunk_text")
            ),

            "section_path": payload.get(
                "section_path",
                []
            ),

            "parent_section": payload.get(
                "parent_section",
                ""
            ),

            "page": payload.get(
                "page",
                1
            ),

            "prev_chunk_index": payload.get("prev_chunk_index"),
            "next_chunk_index": payload.get("next_chunk_index"),
            "prev_chunk_id": payload.get("prev_chunk_id"),
            "next_chunk_id": payload.get("next_chunk_id"),
            "unit_type": payload.get("unit_type", "chunk"),
            "is_figure": payload.get("is_figure", False),
            "figure_data": payload.get("figure_data"),

            "keywords": payload.get(

                "keywords",
                [],
            ),

            "upload_time": payload.get(
                "upload_time"
            ),

            "folder_id": payload.get("folder_id"),
            "folder_path": payload.get("folder_path", "/"),

            "relevance_score": float(
                result.score
            ),
        }

    def get_surrounding_chunks(self, file_id: str, chunk_index: int) -> Dict[str, Any]:
        """
        Fast point retrieval of previous, current, and next chunk
        for Context Window Expansion: [C_{i-1}] + [C_i] + [C_{i+1}].
        """
        target_id = self._make_point_id(file_id, chunk_index)
        prev_id = self._make_point_id(file_id, chunk_index - 1) if chunk_index > 0 else None
        next_id = self._make_point_id(file_id, chunk_index + 1)

        ids_to_fetch = [target_id]
        if prev_id:
            ids_to_fetch.append(prev_id)
        ids_to_fetch.append(next_id)

        try:
            retrieved = self.client.retrieve(
                collection_name=COLLECTION_NAME,
                ids=ids_to_fetch,
                with_payload=True,
            )
            points_by_id = {str(p.id): p.payload for p in retrieved if p.payload}

            target_payload = points_by_id.get(target_id, {})
            prev_payload = points_by_id.get(prev_id, {}) if prev_id else {}
            next_payload = points_by_id.get(next_id, {}) if next_id else {}

            prev_text = prev_payload.get("chunk_text", "")
            curr_text = target_payload.get("chunk_text", "")
            next_text = next_payload.get("chunk_text", "")

            # Compose expanded context window [C_{i-1}] + [C_i] + [C_{i+1}]
            parts = []
            if prev_text:
                parts.append(prev_text)
            if curr_text:
                parts.append(curr_text)
            if next_text:
                parts.append(next_text)

            expanded_text = "\n\n".join(parts) if parts else curr_text

            return {
                "target_chunk": target_payload,
                "prev_chunk": prev_payload if prev_payload else None,
                "next_chunk": next_payload if next_payload else None,
                "expanded_text": expanded_text,
                "section_path": target_payload.get("section_path", []),
                "parent_section": target_payload.get("parent_section", ""),
            }
        except Exception as exc:
            logger.warning("[Qdrant] get_surrounding_chunks failed for %s:%d: %s", file_id, chunk_index, exc)
            return {
                "target_chunk": {},
                "prev_chunk": None,
                "next_chunk": None,
                "expanded_text": "",
                "section_path": [],
                "parent_section": "",
            }

    def get_chunks_for_file(self, file_id: str, limit: int = 50) -> List[Dict]:
        """Fetch all indexed chunks for a file, ordered by chunk_index."""
        try:
            from qdrant_client import models
            points, _ = self.client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_id",
                            match=models.MatchValue(value=file_id),
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
            )
            results = []
            for p in points:
                payload = p.payload or {}
                results.append({
                    "chunk_id": payload.get("chunk_id", str(p.id)),
                    "chunk_index": payload.get("chunk_index", 0),
                    "chunk_text": payload.get("chunk_text", ""),
                    "enriched_text": payload.get("enriched_text", ""),
                    "section_path": payload.get("section_path", []),
                    "parent_section": payload.get("parent_section", ""),
                    "page": payload.get("page", 1),
                    "unit_type": payload.get("unit_type", "chunk"),
                    "keywords": payload.get("keywords", []),
                })
            results.sort(key=lambda x: x["chunk_index"])
            return results
        except Exception as exc:
            logger.warning("[Qdrant] get_chunks_for_file failed for %s: %s", file_id, exc)
            return []

    def update_file_folder(
        self,
        file_id: str,
        folder_id: Optional[str],
        folder_path: Optional[str] = "/",
    ):
        """Update folder_id and folder_path for all indexed chunks of a file."""
        if not self.client:
            return
        try:
            from qdrant_client import models
            self.client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "folder_id": folder_id,
                    "folder_path": folder_path or "/",
                },
                points=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_id",
                            match=models.MatchValue(value=file_id),
                        )
                    ]
                ),
            )
            logger.info("[Qdrant] Updated folder metadata for file_id=%s -> folder_id=%s (%s)", file_id, folder_id, folder_path)
        except Exception as exc:
            logger.warning("[Qdrant] Could not update folder payload for %s: %s", file_id, exc)


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
