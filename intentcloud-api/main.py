"""
IntentCloud FastAPI Backend - Phase 1-3 Implementation
Week 1-3: Scaffolding, Data Ingestion, Embeddings, Intent Parsing
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import json
import uuid
import time
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
import asyncio
import logging
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Extension definitions with safe defaults
CODE_EXTENSIONS_MAP: Dict[str, str] = {}
IMAGE_EXTENSIONS: Set[str] = set()
DOCUMENT_EXTENSIONS: Set[str] = {".pdf", ".docx", ".doc", ".txt"}

# Import service modules
try:
    from services.extraction import (
        extract_text_from_upload,
        get_file_category,
        CODE_EXTENSIONS_MAP,
        IMAGE_EXTENSIONS,
        DOCUMENT_EXTENSIONS
    )
    from services.embeddings import generate_embeddings
    from services.qdrant_client import QdrantIndexManager
    from services.intent_parser import parse_intent_with_phi3
    from services.search import execute_search_pipeline, hybrid_search
    from services.reranker import get_reranker, DEFAULT_CONFIDENCE_THRESHOLD
    logger.info("✓ All service modules imported successfully")
except ImportError as e:
    logger.error(f"✗ Failed to import service modules: {e}")

# Configuration
UPLOAD_DIR = Path("./uploads")
ALLOWED_EXTENSIONS = (
    set(CODE_EXTENSIONS_MAP.keys()) |
    IMAGE_EXTENSIONS |
    DOCUMENT_EXTENSIONS
)
QDRANT_COLLECTION = "intentcloud_docs"
METADATA_FILE = UPLOAD_DIR / "metadata.json"
FOLDERS_FILE = UPLOAD_DIR / "folders.json"

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

# Hierarchical folder persistence helpers
def load_folders() -> List[Dict[str, Any]]:
    if FOLDERS_FILE.exists():
        try:
            with open(FOLDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read folders.json: {e}")
    return []

def save_folders(folders: List[Dict[str, Any]]):
    try:
        with open(FOLDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(folders, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write folders.json: {e}")

def get_folder_by_id(folder_id: Optional[str], folders: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    if not folder_id:
        return None
    if folders is None:
        folders = load_folders()
    for f in folders:
        if f.get("id") == folder_id:
            return f
    return None

def compute_folder_path(folder_id: Optional[str], folders: Optional[List[Dict[str, Any]]] = None) -> str:
    if not folder_id or folder_id in {"root", "null"}:
        return "/"
    if folders is None:
        folders = load_folders()
    folder_map = {f["id"]: f for f in folders if "id" in f}
    parts = []
    curr_id = folder_id
    visited = set()
    while curr_id and curr_id in folder_map and curr_id not in visited:
        visited.add(curr_id)
        f_obj = folder_map[curr_id]
        parts.insert(0, f_obj.get("name", "Untitled"))
        curr_id = f_obj.get("parent_id")
    return "/" + "/".join(parts) if parts else "/"

def get_folder_and_subfolder_ids(folder_id: str, folders: Optional[List[Dict[str, Any]]] = None) -> Set[str]:
    """Get folder_id and all its descendant folder IDs recursively."""
    if folders is None:
        folders = load_folders()
    result = {folder_id}
    added = True
    while added:
        added = False
        for f in folders:
            f_id = f.get("id")
            p_id = f.get("parent_id")
            if f_id and p_id in result and f_id not in result:
                result.add(f_id)
                added = True
    return result

# Request models
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = "blue"

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None

class FileMove(BaseModel):
    folder_id: Optional[str] = None

class BatchFileMove(BaseModel):
    file_ids: List[str]
    folder_id: Optional[str] = None

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
    folder_id: Optional[str] = Form(None),
):
    """
    Phase 1 Upload Endpoint:
    1. Validates file
    2. Saves file to disk
    3. Records original filename and folder_id in metadata.json
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
        
        category = get_file_category(original_filename)
        initial_topics = []
        if category == "code":
            lang = CODE_EXTENSIONS_MAP.get(file_ext, "Code")
            initial_topics.extend(["Source Code", lang])
        elif category == "photo":
            initial_topics.append("Photos & Images")

        clean_folder_id = folder_id.strip() if folder_id and folder_id.strip() not in {"", "null", "root", "undefined"} else None
        folders = load_folders()
        folder_path = compute_folder_path(clean_folder_id, folders)

        # Save metadata immediately (topic_tags enriched after extraction).
        metadata = load_metadata()
        metadata[file_id] = {
            "file_id": file_id,
            "filename": original_filename,
            "size_bytes": len(contents),
            "upload_time": time.time(),
            "extension": file_ext.replace(".", "").lower(),
            "file_path": str(file_path),
            "file_type_category": category,
            "topic_tags": initial_topics,
            "folder_id": clean_folder_id,
            "folder_path": folder_path,
        }
        save_metadata(metadata)
        
        # Trigger background processing
        background_tasks.add_task(
            process_document_pipeline,
            file_id=file_id,
            file_path=str(file_path),
            filename=original_filename,
            folder_id=clean_folder_id,
        )
        
        return JSONResponse({
            "status": "received",
            "file_id": file_id,
            "filename": original_filename,
            "size_bytes": len(contents),
            "folder_id": clean_folder_id,
            "folder_path": folder_path,
            "message": "File received. Processing in background..."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def process_document_pipeline(file_id: str, file_path: str, filename: str, folder_id: Optional[str] = None):
    """Background task: Full extraction -> embedding -> storage pipeline"""
    try:
        logger.info(f"[Pipeline] Starting for file_id={file_id}, filename={filename}, folder_id={folder_id}")
        
        if not qdrant_manager:
            logger.error("[Pipeline] Qdrant manager not initialized")
            return
        
        text_content = extract_text_from_upload(file_path, original_filename=filename)
        if not text_content or len(text_content.strip()) < 10:
            logger.error(f"[Error] Extraction failed or insufficient text")
            return
        
        logger.info(f"[Step 1] Extracted {len(text_content)} chars")
        
        # Generate universal embeddings (dense + sparse + keywords)
        representation = generate_embeddings(text_content)
        chunk_count = representation["chunk_count"]
        logger.info(f"[Step 2] Generated {chunk_count} chunks with dense + sparse vectors")
        
        folder_path = compute_folder_path(folder_id)

        # Upsert to Qdrant (includes duplicate detection at document level)
        result = qdrant_manager.upsert_document(
            file_id=file_id,
            filename=filename,
            text_content=text_content,
            file_type=Path(file_path).suffix.lower().replace(".", ""),
            metadata={
                "folder_id": folder_id,
                "folder_path": folder_path,
            }
        )
        
        # Update metadata with results
        metadata = load_metadata()
        if file_id in metadata:
            if result["success"]:
                current_tags = metadata[file_id].get("topic_tags", [])
                merged_tags = list(dict.fromkeys(current_tags + representation.get("document_keywords", [])))
                metadata[file_id]["topic_tags"] = merged_tags
                metadata[file_id]["chunk_count"] = chunk_count
                metadata[file_id]["folder_id"] = folder_id
                metadata[file_id]["folder_path"] = folder_path
                logger.info(f"[Step 3] Updated metadata: keywords={merged_tags}")
            elif result.get("duplicate"):
                metadata[file_id]["status"] = "duplicate"
                logger.warning(f"[Step 3] File marked as duplicate of {result['existing_file']['file_id']}")
            save_metadata(metadata)
        
        logger.info(f"[Pipeline] Complete for file_id={file_id}")
    except Exception as e:
        logger.error(f"[Error] Pipeline failed: {str(e)}")

@app.post("/reindex/{file_id}", tags=["Maintenance"])
async def reindex_file(file_id: str):
    """Re-extract and re-embed a document with updated visual & text models"""
    metadata = load_metadata()
    if file_id not in metadata:
        raise HTTPException(status_code=404, detail="File ID not found in metadata")
    
    file_info = metadata[file_id]
    file_path = file_info.get("file_path", "")
    filename = file_info.get("filename", "")
    
    if not file_path or not Path(file_path).exists():
        # Fallback to search in UPLOAD_DIR
        for candidate in UPLOAD_DIR.glob(f"{file_id}.*"):
            if candidate.is_file():
                file_path = str(candidate)
                break
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"Physical file missing on disk")
        
    # Remove existing Qdrant points for this file so it doesn't get flagged as duplicate
    if qdrant_manager and qdrant_manager.client:
        try:
            from qdrant_client import models
            qdrant_manager.client.delete(
                collection_name=QDRANT_COLLECTION,
                points_selector=models.Filter(
                    must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=file_id))]
                )
            )
            logger.info(f"[Reindex] Cleared old Qdrant points for {file_id}")
        except Exception as q_err:
            logger.warning(f"[Reindex] Could not delete old Qdrant points: {q_err}")

    process_document_pipeline(file_id, file_path, filename)
    return {"status": "reindexed", "file_id": file_id, "filename": filename}

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
        stats["confidence_threshold"] = reranker_info.get("confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD)
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
    folder_id: Optional[str] = None,
    include_subfolders: bool = True,
):
    """
    Phase 4 Hybrid Semantic Retrieval:
    1. Parse natural language intent (Phi-3 Mini / fallback)
    2. Dense semantic candidate retrieval (all-MiniLM-L6-v2)
    3. Sparse universal keyword retrieval (feature hash)
    4. Reciprocal Rank Fusion (RRF, k=60)
    5. Cross-Encoder reranking (ms-marco-MiniLM-L-6-v2)
    6. Sentence-level snippet highlighting & confidence evaluation
    7. Hierarchical folder filtering and path enrichment
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
        
        conf_threshold = threshold if threshold is not None else DEFAULT_CONFIDENCE_THRESHOLD
        
        # If folder filtering requested, fetch more candidates so filtering doesn't prematurely empty the pool
        candidate_multiplier = 4 if folder_id and folder_id.strip() not in {"", "root", "null", "all"} else 1
        effective_top_k = top_k * candidate_multiplier

        search_output = execute_search_pipeline(
            query=query,
            intent_data=intent_data,
            qdrant_manager=qdrant_manager,
            top_k=effective_top_k,
            search_mode=search_mode,
            confidence_threshold=conf_threshold,
        )
        
        raw_results = search_output.get("results", [])
        metadata = load_metadata()
        folders = load_folders()

        clean_folder_id = folder_id.strip() if folder_id and folder_id.strip() not in {"", "root", "null", "all"} else None
        allowed_folder_ids: Optional[Set[str]] = None
        target_folder_name = "Selected Folder"
        target_folder_path = "/"

        if clean_folder_id:
            target_f = get_folder_by_id(clean_folder_id, folders)
            if target_f:
                target_folder_name = target_f.get("name", "Folder")
                target_folder_path = compute_folder_path(clean_folder_id, folders)
            if include_subfolders:
                allowed_folder_ids = get_folder_and_subfolder_ids(clean_folder_id, folders)
            else:
                allowed_folder_ids = {clean_folder_id}

        enriched_results = []
        for item in raw_results:
            file_id = item.get("file_id")
            f_meta = metadata.get(file_id, {})
            doc_folder_id = item.get("folder_id") or f_meta.get("folder_id")
            doc_folder_path = item.get("folder_path") or compute_folder_path(doc_folder_id, folders)

            # Apply folder scope filter if active
            if allowed_folder_ids is not None:
                if not doc_folder_id or doc_folder_id not in allowed_folder_ids:
                    continue

            item["folder_id"] = doc_folder_id
            item["folder_path"] = doc_folder_path
            enriched_results.append(item)

        # Slice back to user's requested top_k
        final_results = enriched_results[:top_k]
        for idx, res in enumerate(final_results, start=1):
            res["rank"] = idx

        is_confident = search_output.get("is_confident_match", True)
        confidence_msg = search_output.get("confidence_message", "")

        if clean_folder_id and len(final_results) == 0 and len(raw_results) > 0:
            is_confident = False
            confidence_msg = f"No confident match found inside '{target_folder_name}' ({target_folder_path}). Other matching documents exist in outside folders."

        return JSONResponse({
            "query": query,
            "search_mode": search_output.get("search_mode", search_mode),
            "parsed_intent": intent_data,
            "folder_id": clean_folder_id,
            "folder_path": target_folder_path if clean_folder_id else "/",
            "is_confident_match": is_confident and len(final_results) > 0,
            "confidence_message": confidence_msg,
            "results": final_results,
            "count": len(final_results),
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


@app.get("/preview/{file_id}", tags=["Phase 5: Preview"])
async def preview_file(file_id: str):
    """Serve file for inline browser preview (images, PDFs, text, code)"""
    try:
        metadata = load_metadata()
        file_meta = metadata.get(file_id)
        file_path: Optional[Path] = None
        orig_name: str = "document"

        if file_meta and Path(file_meta.get("file_path", "")).exists():
            file_path = Path(file_meta["file_path"])
            orig_name = file_meta.get("filename", file_path.name)
        else:
            matching = list(UPLOAD_DIR.glob(f"{file_id}.*"))
            if matching:
                file_path = matching[0]
                orig_name = file_meta["filename"] if file_meta else file_path.name

        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        content_type, _ = mimetypes.guess_type(orig_name)
        ext = file_path.suffix.lower()
        if not content_type:
            if ext in {".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".html", ".css", ".cpp", ".c", ".go", ".rs", ".java", ".sql", ".sh", ".yaml", ".yml", ".md", ".txt"}:
                content_type = "text/plain; charset=utf-8"
            elif ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico"}:
                content_type = f"image/{ext.replace('.', '')}"
            elif ext == ".svg":
                content_type = "image/svg+xml"
            elif ext == ".pdf":
                content_type = "application/pdf"
            else:
                content_type = "application/octet-stream"
        elif ext in {".py", ".ts", ".js", ".tsx", ".jsx", ".json", ".sh", ".yaml", ".yml"}:
            content_type = "text/plain; charset=utf-8"

        return FileResponse(
            path=str(file_path),
            filename=orig_name,
            media_type=content_type,
            content_disposition_type="inline"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_id}/content", tags=["Phase 5: Preview"])
async def get_file_content(file_id: str):
    """Retrieve raw text or code content for in-app code/text preview modal"""
    try:
        metadata = load_metadata()
        file_meta = metadata.get(file_id)
        if not file_meta or not Path(file_meta.get("file_path", "")).exists():
            matching = list(UPLOAD_DIR.glob(f"{file_id}.*"))
            if not matching:
                raise HTTPException(status_code=404, detail="File not found")
            file_path = matching[0]
            filename = file_meta["filename"] if file_meta else file_path.name
            category = get_file_category(filename)
        else:
            file_path = Path(file_meta["file_path"])
            filename = file_meta.get("filename", file_path.name)
            category = file_meta.get("file_type_category", get_file_category(filename))

        ext = file_path.suffix.lower().replace(".", "")
        is_binary = category in {"photo", "pdf"} or ext in {"png", "jpg", "jpeg", "webp", "gif", "pdf", "docx"}

        text_content = ""
        visual_metadata = ""
        if not is_binary or ext == "svg":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    text_content = f.read()
        else:
            # For photos/pdfs, extract any visual text / OCR / VLM description
            try:
                from services.extraction import extract_text_from_upload
                visual_metadata = extract_text_from_upload(str(file_path), original_filename=filename)
            except Exception:
                visual_metadata = ""

        return JSONResponse({
            "file_id": file_id,
            "filename": filename,
            "category": category,
            "extension": ext,
            "is_binary": is_binary,
            "content": text_content,
            "visual_metadata": visual_metadata,
            "preview_url": f"/preview/{file_id}",
            "size_bytes": file_path.stat().st_size
        })
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
        folders = load_folders()
        uploaded_files = []
        
        # Populate from metadata
        disk_files = {f.stem: f for f in UPLOAD_DIR.glob("*") if f.name not in {"metadata.json", "folders.json"}}
        
        # Check metadata entries
        for file_id, info in metadata.items():
            file_path = Path(info.get("file_path", ""))
            if file_path.exists() or file_id in disk_files:
                f_target = file_path if file_path.exists() else disk_files[file_id]
                filename = info.get("filename", f_target.name)
                ext = info.get("extension", f_target.suffix.replace(".", "").lower())
                cat = info.get("file_type_category") or get_file_category(filename)
                f_folder_id = info.get("folder_id")
                uploaded_files.append({
                    "file_id": file_id,
                    "name": filename,
                    "size_bytes": info.get("size_bytes", f_target.stat().st_size),
                    "modified": info.get("upload_time", f_target.stat().st_mtime),
                    "extension": ext,
                    "file_type_category": cat,
                    "topic_tags": info.get("topic_tags", []),
                    "folder_id": f_folder_id,
                    "folder_path": compute_folder_path(f_folder_id, folders),
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
                    "extension": ext,
                    "folder_id": None,
                    "folder_path": "/",
                })
                # Add to metadata for next time
                metadata[file_id] = {
                    "file_id": file_id,
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                    "upload_time": f.stat().st_mtime,
                    "extension": ext,
                    "file_path": str(f),
                    "folder_id": None,
                    "folder_path": "/",
                }
                save_metadata(metadata)

        return JSONResponse({
            "uploaded_files": sorted(uploaded_files, key=lambda x: x["modified"], reverse=True)
        })
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Hierarchical Folders & Finder Endpoints
# ============================================================================

@app.get("/folders", tags=["Folders"])
async def list_folders():
    """List all folders with child counts and computed hierarchical paths"""
    try:
        folders = load_folders()
        metadata = load_metadata()

        # Count files per folder
        file_counts: Dict[str, int] = {}
        for info in metadata.values():
            fid = info.get("folder_id")
            if fid:
                file_counts[fid] = file_counts.get(fid, 0) + 1

        # Count direct child folders per folder
        subfolder_counts: Dict[str, int] = {}
        for f in folders:
            pid = f.get("parent_id")
            if pid:
                subfolder_counts[pid] = subfolder_counts.get(pid, 0) + 1

        enriched = []
        for f in folders:
            raw_id = f.get("id")
            if not raw_id:
                continue
            f_id: str = str(raw_id)
            enriched.append({
                "id": f_id,
                "name": f.get("name", "Untitled"),
                "parent_id": f.get("parent_id"),
                "color": f.get("color", "blue"),
                "created_at": f.get("created_at", time.time()),
                "path": compute_folder_path(f_id, folders),
                "file_count": file_counts.get(f_id, 0),
                "subfolder_count": subfolder_counts.get(f_id, 0),
            })

        # Root stats
        root_files = sum(1 for info in metadata.values() if not info.get("folder_id"))
        root_subfolders = sum(1 for f in folders if not f.get("parent_id"))

        return JSONResponse({
            "folders": sorted(enriched, key=lambda x: x["name"].lower()),
            "root_file_count": root_files,
            "root_subfolder_count": root_subfolders,
        })
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/folders", tags=["Folders"])
async def create_folder(payload: FolderCreate):
    """Create a new folder (root or nested)"""
    try:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        if "/" in name:
            raise HTTPException(status_code=400, detail="Folder name cannot contain '/'")

        folders = load_folders()
        clean_parent_id = payload.parent_id.strip() if payload.parent_id and payload.parent_id.strip() not in {"", "null", "root", "undefined"} else None
        if clean_parent_id and not get_folder_by_id(clean_parent_id, folders):
            raise HTTPException(status_code=404, detail="Parent folder not found")

        # Check duplicate name in same parent
        for f in folders:
            if f.get("parent_id") == clean_parent_id and f.get("name", "").lower() == name.lower():
                raise HTTPException(status_code=400, detail=f"A folder named '{name}' already exists in this location")

        folder_id = str(uuid.uuid4())
        new_folder = {
            "id": folder_id,
            "name": name,
            "parent_id": clean_parent_id,
            "color": payload.color or "blue",
            "created_at": time.time(),
        }
        folders.append(new_folder)
        save_folders(folders)

        new_folder["path"] = compute_folder_path(folder_id, folders)
        new_folder["file_count"] = 0
        new_folder["subfolder_count"] = 0

        logger.info(f"✓ Created folder '{name}' at {new_folder['path']} (id={folder_id})")
        return JSONResponse(new_folder, status_code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/folders/{folder_id}", tags=["Folders"])
async def update_folder(folder_id: str, payload: FolderUpdate):
    """Rename or move a folder"""
    try:
        folders = load_folders()
        target = None
        for f in folders:
            if f.get("id") == folder_id:
                target = f
                break

        if not target:
            raise HTTPException(status_code=404, detail="Folder not found")

        if payload.name is not None:
            new_name = payload.name.strip()
            if not new_name:
                raise HTTPException(status_code=400, detail="Folder name cannot be empty")
            if "/" in new_name:
                raise HTTPException(status_code=400, detail="Folder name cannot contain '/'")
            target["name"] = new_name

        if payload.color is not None:
            target["color"] = payload.color

        if payload.parent_id is not None:
            clean_parent = payload.parent_id.strip() if payload.parent_id.strip() not in {"", "null", "root", "undefined"} else None
            if clean_parent == folder_id:
                raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
            if clean_parent:
                descendants = get_folder_and_subfolder_ids(folder_id, folders)
                if clean_parent in descendants:
                    raise HTTPException(status_code=400, detail="Cannot move folder into one of its own subfolders")
            target["parent_id"] = clean_parent

        save_folders(folders)
        target["path"] = compute_folder_path(folder_id, folders)

        # Update paths in metadata for files in this folder and subfolders
        metadata = load_metadata()
        all_child_ids = get_folder_and_subfolder_ids(folder_id, folders)
        changed = False
        for fid, f_info in metadata.items():
            f_fol = f_info.get("folder_id")
            if f_fol in all_child_ids:
                f_info["folder_path"] = compute_folder_path(f_fol, folders)
                changed = True
                if qdrant_manager:
                    qdrant_manager.update_file_folder(fid, f_fol, f_info["folder_path"])
        if changed:
            save_metadata(metadata)

        return JSONResponse(target)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/folders/{folder_id}", tags=["Folders"])
async def delete_folder(folder_id: str, cascade: bool = False):
    """Delete a folder. If cascade=False, files & child folders are moved to parent/root."""
    try:
        folders = load_folders()
        target = None
        for f in folders:
            if f.get("id") == folder_id:
                target = f
                break

        if not target:
            raise HTTPException(status_code=404, detail="Folder not found")

        parent_id = target.get("parent_id")
        metadata = load_metadata()
        all_affected_folders = get_folder_and_subfolder_ids(folder_id, folders) if cascade else {folder_id}

        files_to_delete = []
        files_to_move = []
        for fid, f_info in metadata.items():
            if f_info.get("folder_id") in all_affected_folders:
                if cascade:
                    files_to_delete.append(fid)
                else:
                    files_to_move.append(fid)

        if cascade:
            for fid in files_to_delete:
                f_path = Path(metadata[fid].get("file_path", ""))
                if f_path.exists():
                    try:
                        f_path.unlink()
                    except Exception:
                        pass
                del metadata[fid]
                if qdrant_manager and qdrant_manager.client:
                    try:
                        from qdrant_client import models
                        qdrant_manager.client.delete(
                            collection_name=QDRANT_COLLECTION,
                            points_selector=models.Filter(
                                must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=fid))]
                            )
                        )
                    except Exception:
                        pass
            folders = [f for f in folders if f.get("id") not in all_affected_folders]
        else:
            # Move files to parent
            for fid in files_to_move:
                metadata[fid]["folder_id"] = parent_id
                new_path = compute_folder_path(parent_id, folders)
                metadata[fid]["folder_path"] = new_path
                if qdrant_manager:
                    qdrant_manager.update_file_folder(fid, parent_id, new_path)
            # Reassign direct child folders to parent
            for f in folders:
                if f.get("parent_id") == folder_id:
                    f["parent_id"] = parent_id
            folders = [f for f in folders if f.get("id") != folder_id]

        save_metadata(metadata)
        save_folders(folders)

        logger.info(f"✓ Deleted folder '{target.get('name')}' (cascade={cascade})")
        return JSONResponse({
            "status": "success",
            "message": f"Folder '{target.get('name')}' deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/files/{file_id}/move", tags=["Folders"])
async def move_file(file_id: str, payload: FileMove):
    """Move a file to a folder or back to root"""
    try:
        metadata = load_metadata()
        if file_id not in metadata:
            raise HTTPException(status_code=404, detail="File not found")

        folders = load_folders()
        clean_folder_id = payload.folder_id.strip() if payload.folder_id and payload.folder_id.strip() not in {"", "null", "root", "undefined"} else None
        if clean_folder_id and not get_folder_by_id(clean_folder_id, folders):
            raise HTTPException(status_code=404, detail="Destination folder does not exist")

        metadata[file_id]["folder_id"] = clean_folder_id
        new_path = compute_folder_path(clean_folder_id, folders)
        metadata[file_id]["folder_path"] = new_path
        save_metadata(metadata)

        if qdrant_manager:
            qdrant_manager.update_file_folder(file_id, clean_folder_id, new_path)

        logger.info(f"✓ Moved file {file_id} to folder {clean_folder_id} ({new_path})")
        return JSONResponse({
            "status": "success",
            "file_id": file_id,
            "folder_id": clean_folder_id,
            "folder_path": new_path,
            "message": f"File moved to {new_path}"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/batch-move", tags=["Folders"])
async def batch_move_files(payload: BatchFileMove):
    """Move multiple files into a destination folder or root"""
    try:
        metadata = load_metadata()
        folders = load_folders()
        clean_folder_id = payload.folder_id.strip() if payload.folder_id and payload.folder_id.strip() not in {"", "null", "root", "undefined"} else None
        if clean_folder_id and not get_folder_by_id(clean_folder_id, folders):
            raise HTTPException(status_code=404, detail="Destination folder does not exist")

        new_path = compute_folder_path(clean_folder_id, folders)
        moved_count = 0

        for file_id in payload.file_ids:
            if file_id in metadata:
                metadata[file_id]["folder_id"] = clean_folder_id
                metadata[file_id]["folder_path"] = new_path
                if qdrant_manager:
                    qdrant_manager.update_file_folder(file_id, clean_folder_id, new_path)
                moved_count += 1

        save_metadata(metadata)
        logger.info(f"✓ Batch moved {moved_count} files to {new_path}")
        return JSONResponse({
            "status": "success",
            "moved_count": moved_count,
            "folder_id": clean_folder_id,
            "folder_path": new_path,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch moving files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[
            "uploads",
            "uploads/*",
            "qdrant_storage",
            "qdrant_storage/*",
            "*.json",
            "*.log"
        ]
    )
