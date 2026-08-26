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
    from services.search import hybrid_search
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
    except Exception as e:
        logger.error(f"✗ Failed to initialize Qdrant: {e}")
        qdrant_manager = None
    yield
    logger.info("Shutting down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="IntentCloud API",
    description="Intent-aware cognitive cloud memory system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint with full backend status."""
    try:
        qdrant_status = qdrant_manager.health_check() if qdrant_manager else {"status": "unavailable"}
        return JSONResponse({
            "status": "healthy",
            "service": "IntentCloud API",
            "version": "1.0.0",
            "components": {
                "api": "running",
                "qdrant": qdrant_status,
                "uploads_dir": str(UPLOAD_DIR),
                "phase": "1-3 (Data Ingestion, Embeddings, Intent Parsing)"
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
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
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
        if background_tasks:
            background_tasks.add_task(
                process_document_pipeline,
                file_id=file_id,
                file_path=str(file_path),
                filename=original_filename
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
# Phase 2: Semantic Representation - Get Stats
# ============================================================================

@app.get("/stats", tags=["Phase 2: Dashboard"])
async def get_stats():
    """Get statistics about stored documents for dashboard"""
    try:
        if not qdrant_manager:
            metadata = load_metadata()
            return JSONResponse({
                "total_vectors": 0,
                "total_files": len(metadata),
                "collection": "intentcloud_docs",
                "vector_dim": 384,
                "status": "initializing"
            })
        
        stats = qdrant_manager.get_collection_stats()
        return JSONResponse(stats)
    except Exception as e:
        logger.error(f"[Stats] Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Phase 3: Intent-Aware Query Understanding - Search
# ============================================================================

@app.post("/search", tags=["Phase 3: Search"])
async def search_documents(query: str, top_k: int = 5):
    """Semantic search with Phi-3 intent understanding"""
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
        
        results = hybrid_search(
            query=query,
            intent_data=intent_data,
            qdrant_manager=qdrant_manager,
            top_k=top_k
        )
        
        return JSONResponse({
            "query": query,
            "parsed_intent": intent_data,
            "results": results,
            "count": len(results)
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
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue
                qdrant_manager.client.delete(
                    collection_name=QDRANT_COLLECTION,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="file_id",
                                match=MatchValue(value=file_id)
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
                    "extension": info.get("extension", f_target.suffix.replace(".", "").lower())
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
