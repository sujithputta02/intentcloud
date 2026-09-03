"""
IntentCloud FastAPI Backend - Phase 1-3 Implementation
Week 1-3: Scaffolding, Data Ingestion, Embeddings, Intent Parsing
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import service modules
try:
    from services.extraction import extract_text_from_upload
    from services.embeddings import generate_embeddings
    from services.qdrant_client import QdrantIndexManager
    from services.intent_parser import parse_intent_with_phi3
    from services.search import execute_search_pipeline, hybrid_search
    from services.reranker import get_reranker
    logger.info("✓ All service modules imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import service modules: {e}")

# Configuration
UPLOAD_DIR = Path("./uploads")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
QDRANT_COLLECTION = "intentcloud_docs"
METADATA_FILE = UPLOAD_DIR / "metadata.json"

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

# Metadata persistence helpers
def load_metadata() -> Dict[str, Any]:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read metadata.json: {e}")
    return {}

def save_metadata(data: Dict[str, Any]):
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write metadata.json: {e}")

# Initialize Qdrant manager (global)
qdrant_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qdrant_manager
    try:
        logger.info("Initializing Qdrant manager...")
        qdrant_manager = QdrantIndexManager()
        logger.info("✓ Qdrant manager initialized")
        # Warm up reranker model
        reranker = get_reranker()
        logger.info("✓ Cross-encoder reranker initialized on %s", reranker._device)
    except Exception as e:
        logger.error(f"✗ Failed to initialize Qdrant / Reranker: {e}")
        qdrant_manager = None
    yield
    logger.info("Shutting down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="IntentCloud API",
    description="Intent-aware cognitive cloud memory system with Phase 4 Hybrid Reranking",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3010",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3010",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint with full backend and Phase 4 component status."""
    try:
        qdrant_status = qdrant_manager.health_check() if qdrant_manager else {"status": "unavailable"}
        reranker_status = get_reranker().health_check()
        return JSONResponse({
            "status": "healthy",
            "service": "IntentCloud API",
            "version": "1.0.0",
            "components": {
                "api": "running",
                "qdrant": qdrant_status,
                "reranker": reranker_status,
                "uploads_dir": str(UPLOAD_DIR),
                "phase": "4 (Hybrid Retrieval + RRF + Cross-Encoder Reranking)"
            }
        })
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# ============================================================================
# Phase 1: Upload & Extraction
# ============================================================================

@app.post("/upload", tags=["Phase 1: Upload"])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Phase 1 Upload Endpoint:
    1. Validates file
    2. Saves file to disk
    3. Records original filename in metadata.json
    4. Triggers background extraction and vector indexing
    """
    try:
        original_filename = file.filename or "document.txt"
        file_ext = Path(original_filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed: {ALLOWED_EXTENSIONS}"
            )
        
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        contents = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save metadata immediately (topic_tags filled in after extraction).
        metadata = load_metadata()
        metadata[file_id] = {
            "file_id": file_id,
            "filename": original_filename,
            "size_bytes": len(contents),
            "upload_time": time.time(),
            "extension": file_ext.replace(".", "").lower(),
            "file_path": str(file_path),
            "topic_tags": []
        }
        save_metadata(metadata)
        
        # Trigger background processing
        background_tasks.add_task(
            process_document_pipeline,
            file_id=file_id,
            file_path=str(file_path),
            filename=original_filename,
        )
        
        return JSONResponse({
            "status": "received",
            "file_id": file_id,
            "filename": original_filename,
            "size_bytes": len(contents),
            "message": "File received. Processing in background..."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_pipeline(file_id: str, file_path: str, filename: str):
    """Background task: Full extraction -> embedding -> storage pipeline"""
    try:
        logger.info(f"[Pipeline] Starting for file_id={file_id}, filename={filename}")
        
        if not qdrant_manager:
            logger.error("[Pipeline] Qdrant manager not initialized")
            return
        
        text_content = extract_text_from_upload(file_path)
        if not text_content or len(text_content.strip()) < 10:
            logger.error(f"[Error] Extraction failed or insufficient text")
            return
        
        logger.info(f"[Step 1] Extracted {len(text_content)} chars")
        
        # Generate universal embeddings (dense + sparse + keywords)
        representation = generate_embeddings(text_content)
        chunk_count = representation["chunk_count"]
        logger.info(f"[Step 2] Generated {chunk_count} chunks with dense + sparse vectors")
        
        # Upsert to Qdrant (includes duplicate detection at document level)
        result = qdrant_manager.upsert_document(
            file_id=file_id,
            filename=filename,
            text_content=text_content,
            file_type=Path(file_path).suffix.lower().replace(".", "")
        )
        
        # Update metadata with results
        metadata = load_metadata()
        if file_id in metadata:
            if result["success"]:
                metadata[file_id]["topic_tags"] = representation["document_keywords"]
                metadata[file_id]["chunk_count"] = chunk_count
                logger.info(f"[Step 3] Updated metadata: keywords={representation['document_keywords']}")
            elif result.get("duplicate"):
                metadata[file_id]["status"] = "duplicate"
                logger.warning(f"[Step 3] File marked as duplicate of {result['existing_file']['file_id']}")
            save_metadata(metadata)
        
        logger.info(f"[Pipeline] Complete for file_id={file_id}")
    except Exception as e:
        logger.error(f"[Error] Pipeline failed: {str(e)}")

# ============================================================================
# Phase 2 & 4: Semantic Representation & Stats
# ============================================================================

@app.get("/stats", tags=["Phase 2: Dashboard"])
async def get_stats():
    """Get statistics about stored documents, vectors, and Phase 4 hybrid engine"""
    try:
        metadata = load_metadata()
        reranker_info = get_reranker().health_check()
        
        if not qdrant_manager:
            return JSONResponse({
                "total_vectors": 0,
                "total_files": len(metadata),
                "collection": "intentcloud_docs",
                "vector_dim": 384,
                "sparse_dim": 1000003,
                "fusion_algorithm": "Reciprocal Rank Fusion (RRF, k=60)",
                "reranker_model": reranker_info.get("model_name"),
                "reranker_device": reranker_info.get("device"),
                "status": "initializing"
            })
        
        stats = qdrant_manager.get_collection_stats()
        stats["total_files"] = len([m for m in metadata.values() if m.get("status") != "duplicate"])
        stats["duplicate_files"] = len([m for m in metadata.values() if m.get("status") == "duplicate"])
        stats["fusion_algorithm"] = "Reciprocal Rank Fusion (RRF, k=60)"
        stats["reranker_model"] = reranker_info.get("model_name")
        stats["reranker_device"] = reranker_info.get("device")
        stats["confidence_threshold"] = reranker_info.get("confidence_threshold", 0.40)
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"[Stats] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 4: Intent-Aware Hybrid Search with Cross-Encoder Reranking
# ============================================================================

@app.post("/search", tags=["Phase 4: Search"])
async def search_documents(
    query: str,
    top_k: int = 3,
    search_mode: str = "hybrid",
    threshold: Optional[float] = None,
):
    """
    Phase 4 Hybrid Semantic Retrieval:
    1. Parse natural language intent (Phi-3 Mini / fallback)
    2. Dense semantic candidate retrieval (all-MiniLM-L6-v2)
    3. Sparse universal keyword retrieval (feature hash)
    4. Reciprocal Rank Fusion (RRF, k=60)
    5. Cross-Encoder reranking (ms-marco-MiniLM-L-6-v2)
    6. Sentence-level snippet highlighting & confidence evaluation
    """
    try:
        if not query or len(query.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters"
            )
        
        if not qdrant_manager:
            raise HTTPException(
                status_code=503,
                detail="Search not available - Qdrant not initialized"
            )
        
        try:
            intent_data = parse_intent_with_phi3(query)
        except Exception as e:
            logger.warning(f"[Search] Intent parsing failed: {e}, using fallback")
            intent_data = {
                "topic": query,
                "keywords": query.split(),
                "intent_type": "find",
                "has_time_constraint": False,
                "confidence": 0.5
            }
        
        conf_threshold = threshold if threshold is not None else 0.35
        
        search_output = execute_search_pipeline(
            query=query,
            intent_data=intent_data,
            qdrant_manager=qdrant_manager,
            top_k=top_k,
            search_mode=search_mode,
            confidence_threshold=conf_threshold,
        )
        
        return JSONResponse({
            "query": query,
            "search_mode": search_output.get("search_mode", search_mode),
            "parsed_intent": intent_data,
            "is_confident_match": search_output.get("is_confident_match", True),
            "confidence_message": search_output.get("confidence_message", ""),
            "results": search_output.get("results", []),
            "count": len(search_output.get("results", [])),
            "metrics": search_output.get("metrics", {}),
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Error] Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 5: Download & Delete Operations
# ============================================================================

@app.get("/download/{file_id}", tags=["Phase 5: Download"])
async def download_file(file_id: str):
    """Download stored document by file_id with its original filename"""
    try:
        metadata = load_metadata()
        file_meta = metadata.get(file_id)
        
        # Check metadata first
        if file_meta and Path(file_meta["file_path"]).exists():
            return FileResponse(
                path=file_meta["file_path"],
                filename=file_meta["filename"],
                media_type="application/octet-stream"
            )
        
        # Fallback to scanning directory
        matching = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        if matching:
            target = matching[0]
            orig_name = file_meta["filename"] if file_meta else target.name
            return FileResponse(
                path=str(target),
                filename=orig_name,
                media_type="application/octet-stream"
            )
        
        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{file_id}", tags=["Phase 5: Delete"])
async def delete_file(file_id: str):
    """
    Delete a document:
    1. Remove from disk
    2. Remove from metadata.json
    3. Delete all vector embeddings from Qdrant
    """
    try:
        metadata = load_metadata()
        deleted_name = "document"
        
        # 1. Remove from metadata
        if file_id in metadata:
            deleted_name = metadata[file_id].get("filename", deleted_name)
            file_path = Path(metadata[file_id].get("file_path", ""))
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as fe:
                    logger.warning(f"Could not delete physical file: {fe}")
            del metadata[file_id]
            save_metadata(metadata)
        
        # Also clean up any disk files matching file_id
        for f in UPLOAD_DIR.glob(f"{file_id}.*"):
            if f.is_file() and f.name != "metadata.json":
                try:
                    f.unlink()
                except Exception:
                    pass
        
        # 2. Remove from Qdrant
        if qdrant_manager and qdrant_manager.client:
            try:
                from qdrant_client import models
                qdrant_manager.client.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_id",
                                match=models.MatchValue(value=file_id)
                            )
                        ]
                    )
                )
                logger.info(f"✓ Deleted Qdrant points for file_id={file_id}")
            except Exception as q_err:
                logger.warning(f"Could not delete Qdrant points for {file_id}: {q_err}")
        
        return JSONResponse({
            "status": "success",
            "message": f"File '{deleted_name}' deleted successfully",
            "file_id": file_id
        })
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/files", tags=["Utility"])
async def list_uploaded_files():
    """List all uploaded files using persistent metadata and disk synchronization"""
    try:
        metadata = load_metadata()
        uploaded_files = []
        
        # Populate from metadata
        disk_files = {f.stem: f for f in UPLOAD_DIR.glob("*") if f.name != "metadata.json"}
        
        # Check metadata entries
        for file_id, info in metadata.items():
            file_path = Path(info.get("file_path", ""))
            if file_path.exists() or file_id in disk_files:
                f_target = file_path if file_path.exists() else disk_files[file_id]
                uploaded_files.append({
                    "file_id": file_id,
                    "name": info.get("filename", f_target.name),
                    "size_bytes": info.get("size_bytes", f_target.stat().st_size),
                    "modified": info.get("upload_time", f_target.stat().st_mtime),
                    "extension": info.get("extension", f_target.suffix.replace(".", "").lower()),
                    "topic_tags": info.get("topic_tags", []),
                })
        
        # Catch any stray files on disk not in metadata
        for file_id, f in disk_files.items():
            if file_id not in metadata:
                ext = f.suffix.replace(".", "").lower()
                uploaded_files.append({
                    "file_id": file_id,
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                    "extension": ext
                })
                # Add to metadata for next time
                metadata[file_id] = {
                    "file_id": file_id,
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                    "upload_time": f.stat().st_mtime,
                    "extension": ext,
                    "file_path": str(f)
                }
                save_metadata(metadata)

        return JSONResponse({
            "uploaded_files": sorted(uploaded_files, key=lambda x: x["modified"], reverse=True)
        })
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
