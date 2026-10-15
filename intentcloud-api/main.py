"""
IntentCloud FastAPI Backend - Phase 1-3 Implementation
Week 1-3: Scaffolding, Data Ingestion, Embeddings, Intent Parsing
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import json
import uuid
import time
import re
import datetime
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
        extract_document_tree,
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
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
FIGURES_DIR = UPLOAD_DIR / "figures"
THUMBNAILS_DIR = FIGURES_DIR / "thumbnails"
ALLOWED_EXTENSIONS = (
    set(CODE_EXTENSIONS_MAP.keys()) |
    IMAGE_EXTENSIONS |
    DOCUMENT_EXTENSIONS
)
QDRANT_COLLECTION = "intentcloud_docs"
METADATA_FILE = UPLOAD_DIR / "metadata.json"
FOLDERS_FILE = UPLOAD_DIR / "folders.json"

# System-reserved files and directories that must never be exposed as user documents
SYSTEM_IGNORED_NAMES: Set[str] = {
    "qdrant_db",
    "qdrant_storage",
    "metadata.json",
    "folders.json",
    "figures",
    ".DS_Store",
    "__pycache__",
    ".git",
    ".gitignore",
}

# Ensure upload and figure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)


# Metadata persistence helpers
def load_metadata() -> Dict[str, Any]:
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    k: v for k, v in data.items()
                    if k not in SYSTEM_IGNORED_NAMES and not k.startswith(".")
                }
        except Exception as e:
            logger.warning(f"Failed to read metadata.json: {e}")
    return {}

def save_metadata(data: Dict[str, Any]):
    try:
        clean_data = {
            k: v for k, v in data.items()
            if k not in SYSTEM_IGNORED_NAMES and not k.startswith(".")
        }
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, indent=2)
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
        # Warm up bi-encoder embedding model
        from services.embeddings import generate_query_representation
        generate_query_representation("warmup query")
        logger.info("✓ Bi-encoder embedding model initialized and warmed up")
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

@app.get("/ports", tags=["Health"])
async def list_serial_ports():
    import glob
    try:
        import serial.tools.list_ports
        comports = [{"device": p.device, "description": p.description, "hwid": p.hwid} for p in serial.tools.list_ports.comports()]
    except Exception as e:
        comports = [str(e)]
    cu_devs = glob.glob("/dev/cu.*")
    tty_devs = glob.glob("/dev/tty.*")
    return JSONResponse({"cu_devs": cu_devs, "tty_devs": tty_devs, "comports": comports})

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
# Edge Hardware OLED Display Telemetry
# ============================================================================

latest_device_oled_state: Dict[str, Any] = {
    "status": "ONLINE",
    "edge_ip": "192.168.2.2",
    "hw_info": "Pi 3B | Qdrant 384D",
    "last_query": "Ready for query",
    "top_result": None,
    "last_updated": time.time(),
}

@app.get("/device/oled", tags=["Edge Hardware"])
@app.get("/device/telemetry", tags=["Edge Hardware"])
async def get_device_telemetry():
    """Retrieve live Edge Device & OLED status matching firmware/main.py"""
    return JSONResponse(latest_device_oled_state)

@app.post("/device/oled/push", tags=["Edge Hardware"])
async def push_device_telemetry(payload: Dict[str, Any]):
    """Update OLED display state and sync to physical edge device"""
    global latest_device_oled_state
    latest_device_oled_state.update(payload)
    latest_device_oled_state["last_updated"] = time.time()
    broadcast_oled_live(
        status=latest_device_oled_state.get("status", "ONLINE"),
        query=latest_device_oled_state.get("last_query", ""),
        hw_info=latest_device_oled_state.get("hw_info", ""),
        match=latest_device_oled_state.get("top_result", {}).get("relevance_percentage") if isinstance(latest_device_oled_state.get("top_result"), dict) else None
    )
    return JSONResponse({"status": "pushed", "telemetry": latest_device_oled_state})

def broadcast_oled_live(status: str, query: str = "", hw_info: str = "", match: Optional[Any] = None):
    """Asynchronously broadcast live OLED telemetry to local ESP32 bridge (http://127.0.0.1:8765/push) and Pi OLED."""
    import urllib.request
    import json
    import threading

    clean_q = (query or latest_device_oled_state.get("last_query", "Ready for query")).strip()
    payload = {
        "status": status or latest_device_oled_state.get("status", "ACTIVE"),
        "query": clean_q[:16],
        "info": hw_info or latest_device_oled_state.get("hw_info", "Pi 3B | Qdrant"),
        "match": match,
        "edge_ip": latest_device_oled_state.get("edge_ip", "192.168.2.2"),
        "last_updated": time.time(),
    }

    def _worker():
        # 1. Local ESP32 bridge (driving USB serial OLED on laptop)
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8765/push",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "IntentCloudAPI"},
            )
            urllib.request.urlopen(req, timeout=0.3)
        except Exception:
            pass

        # 2. Raspberry Pi network endpoint (if active)
        try:
            req_pi = urllib.request.Request(
                "http://192.168.2.2:8000/device/oled/push",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "IntentCloudAPI"},
            )
            urllib.request.urlopen(req_pi, timeout=0.3)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()

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

        # Parse version and lineage metadata (Objective 3)
        v_match = re.search(r"[_\-\.](?:v|version)(\d+)", original_filename, re.IGNORECASE)
        version_num = int(v_match.group(1)) if v_match else 1
        is_latest = True
        base_stem = re.sub(r"[_\-\.](?:v|version)\d+", "", Path(original_filename).stem, flags=re.IGNORECASE)
        parent_id = None

        # Save metadata immediately (topic_tags enriched after extraction).
        metadata = load_metadata()
        for existing_id, existing_meta in metadata.items():
            existing_stem = re.sub(r"[_\-\.](?:v|version)\d+", "", Path(existing_meta.get("filename", "")).stem, flags=re.IGNORECASE)
            if existing_stem and existing_stem.lower() == base_stem.lower():
                parent_id = existing_id
                if version_num > existing_meta.get("version_number", 1):
                    existing_meta["is_latest"] = False

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        metadata[file_id] = {
            "file_id": file_id,
            "filename": original_filename,
            "size_bytes": len(contents),
            "upload_time": time.time(),
            "created_at": now_iso,
            "modified_at": now_iso,
            "version_number": version_num,
            "is_latest": is_latest,
            "parent_id": parent_id,
            "extension": file_ext.replace(".", "").lower(),
            "file_path": str(file_path),
            "file_type_category": category,
            "topic_tags": initial_topics,
            "folder_id": clean_folder_id,
            "folder_path": folder_path,
        }
        save_metadata(metadata)
        
        # Broadcast live OLED telemetry
        broadcast_oled_live("UPLOADING", original_filename[:16], f"{max(1, len(contents)//1024)}KB Ingest")

        # Process immediately so newly uploaded files are instantly searchable
        if len(contents) <= 8 * 1024 * 1024:
            process_document_pipeline(
                file_id=file_id,
                file_path=str(file_path),
                filename=original_filename,
                folder_id=clean_folder_id,
            )
        else:
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
            "message": "File received and indexed into cognitive memory."
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def process_document_pipeline(file_id: str, file_path: str, filename: str, folder_id: Optional[str] = None):
    """Extraction -> embedding -> Qdrant vector storage pipeline with guaranteed fallback"""
    try:
        logger.info(f"[Pipeline] Starting for file_id={file_id}, filename={filename}, folder_id={folder_id}")
        
        if not qdrant_manager:
            logger.error("[Pipeline] Qdrant manager not initialized")
            return
        
        doc_tree = extract_document_tree(file_path, original_filename=filename)
        text_content = (doc_tree.get("full_text") or "").strip()
        
        # Guarantee all files are searchable even if parser returns minimal text
        if len(text_content) < 5:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    direct_text = f.read().strip()
                if direct_text:
                    text_content = direct_text
            except Exception:
                pass

        if len(text_content) < 3:
            clean_stem = Path(filename).stem.replace("_", " ").replace("-", " ")
            text_content = f"{filename}\n{clean_stem}\nUploaded file in IntentCloud cognitive memory."

        doc_tree["full_text"] = text_content
        if not doc_tree.get("sections"):
            doc_tree["sections"] = [{
                "section_id": "sec_0",
                "title": filename,
                "section_path": [filename],
                "text": text_content,
                "page": 1
            }]
        
        logger.info(f"[Step 1] Extracted {len(text_content)} chars and {len(doc_tree.get('sections', []))} sections")
        
        # Generate universal embeddings from structural DocumentTree
        file_cat = Path(file_path).suffix.lower().replace(".", "")
        representation = generate_embeddings(
            doc_tree,
            doc_title=filename,
            doc_category=file_cat,
        )
        chunk_count = representation["chunk_count"]
        logger.info(f"[Step 2] Generated {chunk_count} chunks with dense + sparse vectors")
        
        folder_path = compute_folder_path(folder_id)

        # Upsert to Qdrant (guaranteed storage for search visibility)
        result = qdrant_manager.upsert_document(
            file_id=file_id,
            filename=filename,
            text_content=doc_tree,
            file_type=file_cat,
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
                metadata[file_id]["figures"] = doc_tree.get("figures", [])
                logger.info(f"[Step 3] Updated metadata: keywords={merged_tags}, figures={len(doc_tree.get('figures', []))}")
            elif result.get("duplicate"):
                metadata[file_id]["status"] = "duplicate"
                logger.warning(f"[Step 3] File marked as duplicate of {result.get('existing_file', {}).get('file_id')}")
            save_metadata(metadata)
        
        # Broadcast live indexed status to physical OLED
        broadcast_oled_live("INDEXED", filename[:16], f"{chunk_count} Chunks")
        logger.info(f"[Pipeline] Complete for file_id={file_id}")
    except Exception as e:
        logger.error(f"[Error] Pipeline failed: {str(e)}")

@app.api_route("/reindex/{file_id}", methods=["GET", "POST"], tags=["Maintenance"])
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
# Visual Evidence & Figure Serving Endpoints
# ============================================================================

@app.get("/figures/{filename}", tags=["Evidence"])
async def get_figure(filename: str):
    """Serve extracted figure and diagram images with client-side caching"""
    fig_path = FIGURES_DIR / filename
    if not fig_path.exists() or not fig_path.is_file():
        raise HTTPException(status_code=404, detail=f"Figure '{filename}' not found")
    media_type, _ = mimetypes.guess_type(str(fig_path))
    return FileResponse(
        str(fig_path),
        media_type=media_type or "image/png",
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/figures/thumbnails/{filename}", tags=["Evidence"])
async def get_figure_thumbnail(filename: str):
    """Serve optimized 256px thumbnail for fast UI rendering"""
    thumb_path = THUMBNAILS_DIR / filename
    if not thumb_path.exists() or not thumb_path.is_file():
        # Fallback to full figure if thumbnail not yet cached
        clean_name = filename.replace("_thumb.webp", "").replace(".webp", "")
        # Look for matching base file
        candidates = list(FIGURES_DIR.glob(f"{clean_name}.*"))
        if candidates and candidates[0].is_file():
            media_type, _ = mimetypes.guess_type(str(candidates[0]))
            return FileResponse(str(candidates[0]), media_type=media_type or "image/png")
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(
        str(thumb_path),
        media_type="image/webp",
        headers={"Cache-Control": "public, max-age=604800"}
    )

@app.get("/documents/{file_id}/figures", tags=["Evidence"])
async def get_document_figures(file_id: str):
    """Retrieve all figures and visual evidence extracted from a document"""
    metadata = load_metadata()
    if file_id not in metadata:
        raise HTTPException(status_code=404, detail="File ID not found")
    return {
        "file_id": file_id,
        "filename": metadata[file_id].get("filename"),
        "figures": metadata[file_id].get("figures", [])
    }

@app.get("/documents/{file_id}/pages/{page}/visuals", tags=["Evidence"])
async def get_document_page_visuals(file_id: str, page: int):
    """Retrieve all visual evidence (figures, charts, diagrams) on a specific page"""
    metadata = load_metadata()
    if file_id not in metadata:
        raise HTTPException(status_code=404, detail="File ID not found")
    
    figs = metadata[file_id].get("figures", [])
    page_figs = [f for f in figs if f.get("page") == page or f.get("page_number") == page]
    return {
        "file_id": file_id,
        "filename": metadata[file_id].get("filename"),
        "page": page,
        "count": len(page_figs),
        "visuals": page_figs
    }


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
# Phase 4: Intent-Aware Hybrid & Visual Search with Cross-Encoder Reranking
# ============================================================================

@app.post("/search/visual", tags=["Visual Intelligence"])
def search_visual_documents(
    query: str,
    top_k: int = 3,
    threshold: Optional[float] = None,
    folder_id: Optional[str] = None,
    include_subfolders: bool = True,
):
    """
    Dedicated endpoint for Visual / Diagram / Image retrieval.
    Routes query with visual dominance, weights visual features, and returns exact figure evidence.
    """
    return search_documents(
        query=query,
        top_k=top_k,
        search_mode="visual",
        threshold=threshold,
        folder_id=folder_id,
        include_subfolders=include_subfolders,
    )

@app.api_route("/search", methods=["GET", "POST"], tags=["Phase 4: Search"])
def search_documents(
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
        
        # Stream live OLED telemetry immediately
        clean_q = query.strip()
        latest_device_oled_state["status"] = "SEARCHING"
        latest_device_oled_state["last_query"] = clean_q[:20]
        latest_device_oled_state["hw_info"] = "Hybrid Ingest"
        latest_device_oled_state["last_updated"] = time.time()
        broadcast_oled_live("SEARCHING", clean_q[:16], "Dense + Sparse")
        
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
        
        # Normalize UK/US spelling in parsed intent
        if intent_data:
            from services.search import normalize_spelling
            if "topic" in intent_data:
                intent_data["topic"] = normalize_spelling(str(intent_data["topic"]))
            if "keywords" in intent_data and isinstance(intent_data["keywords"], list):
                intent_data["keywords"] = [normalize_spelling(str(k)) for k in intent_data["keywords"]]
        
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

        # Seamlessly include newly uploaded files or files directly matching query in metadata
        seen_fids = {item.get("file_id") for item in enriched_results if item.get("file_id")}
        q_tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        if q_tokens:
            for fid, fmeta in metadata.items():
                if fid in seen_fids:
                    continue
                fname = fmeta.get("filename", "").lower()
                topic_tags = [str(t).lower() for t in fmeta.get("topic_tags", [])]
                matched_tokens = [tok for tok in q_tokens if tok in fname or any(tok in tag for tag in topic_tags)]
                if len(matched_tokens) >= max(1, len(q_tokens) // 2):
                    doc_folder_id = fmeta.get("folder_id")
                    if allowed_folder_ids is not None and doc_folder_id not in allowed_folder_ids:
                        continue
                    match_pct = min(98, 75 + len(matched_tokens) * 8)
                    meta_hit = {
                        "file_id": fid,
                        "filename": fmeta.get("filename", ""),
                        "relevance_score": match_pct / 100.0,
                        "relevance_percentage": match_pct,
                        "matched_snippet": f"Document: {fmeta.get('filename')} (Topic: {', '.join(fmeta.get('topic_tags', [])[:3])})",
                        "parent_section": "Document Overview",
                        "folder_id": doc_folder_id,
                        "folder_path": fmeta.get("folder_path") or compute_folder_path(doc_folder_id, folders),
                        "file_type": fmeta.get("extension", ""),
                        "file_type_category": fmeta.get("file_type_category", ""),
                        "chunk_index": 0,
                    }
                    enriched_results.insert(0, meta_hit)
                    seen_fids.add(fid)

        # Slice back to user's requested top_k
        final_results = enriched_results[:top_k]
        for idx, res in enumerate(final_results, start=1):
            res["rank"] = idx

        is_confident = search_output.get("is_confident_match", True)
        confidence_msg = search_output.get("confidence_message", "")

        if clean_folder_id and len(final_results) == 0 and len(raw_results) > 0:
            is_confident = False
            confidence_msg = f"No confident match found inside '{target_folder_name}' ({target_folder_path}). Other matching documents exist in outside folders."

        # Update edge OLED telemetry state
        top_match = final_results[0] if final_results else None
        if top_match and is_confident:
            top_pct = top_match.get("relevance_percentage", 0)
            latest_device_oled_state["status"] = "PUSHED"
            latest_device_oled_state["last_query"] = query[:20]
            latest_device_oled_state["top_result"] = {
                "filename": top_match.get("filename", ""),
                "relevance_percentage": top_pct,
                "rank": 1,
            }
            latest_device_oled_state["hw_info"] = f"Pi 3B | {top_pct}% Match"
            latest_device_oled_state["last_updated"] = time.time()
            logger.info("[Edge OLED] Synchronized search result to OLED display: %s (%d%%)", top_match.get("filename"), top_pct)
            broadcast_oled_live("PUSHED", query[:16], f"Pi 3B | {top_pct}% Match", top_pct)
        else:
            cand_score = search_output.get("results", [{}])[0].get("relevance_percentage", 0) if search_output.get("results") else 0
            latest_device_oled_state["status"] = "NO MATCH" if cand_score == 0 else "LOW CONF"
            latest_device_oled_state["last_query"] = query[:20]
            latest_device_oled_state["top_result"] = None
            latest_device_oled_state["hw_info"] = f"Pi 3B | {cand_score}%" if cand_score > 0 else "Pi 3B | Scanned"
            latest_device_oled_state["last_updated"] = time.time()
            broadcast_oled_live("NO MATCH" if cand_score == 0 else "LOW CONF", query[:16], latest_device_oled_state["hw_info"], cand_score if cand_score > 0 else None)

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
            "device_telemetry": latest_device_oled_state,
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
        if file_id in SYSTEM_IGNORED_NAMES or file_id.startswith("."):
            raise HTTPException(status_code=404, detail="File not found")

        metadata = load_metadata()
        file_meta = metadata.get(file_id)
        
        # Check metadata first
        if file_meta and Path(file_meta["file_path"]).is_file():
            return FileResponse(
                path=file_meta["file_path"],
                filename=file_meta["filename"],
                media_type="application/octet-stream"
            )
        
        # Fallback to scanning directory
        matching = [p for p in UPLOAD_DIR.glob(f"{file_id}.*") if p.is_file() and p.name not in SYSTEM_IGNORED_NAMES]
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
        if file_id in SYSTEM_IGNORED_NAMES or file_id.startswith("."):
            raise HTTPException(status_code=404, detail="File not found")

        metadata = load_metadata()
        file_meta = metadata.get(file_id, {})
        file_path: Optional[Path] = None
        orig_name: str = file_meta.get("filename", "document")

        # 1. Search locally
        if file_meta and file_meta.get("file_path") and Path(file_meta["file_path"]).is_file():
            file_path = Path(file_meta["file_path"])
        elif file_meta and file_meta.get("file_path") and (UPLOAD_DIR / file_meta["file_path"]).is_file():
            file_path = UPLOAD_DIR / file_meta["file_path"]
        else:
            matching = [p for p in UPLOAD_DIR.glob(f"{file_id}.*") if p.is_file() and p.name not in SYSTEM_IGNORED_NAMES]
            if matching:
                file_path = matching[0]

        if file_path and file_path.is_file():
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

        # 2. Fallback: Retrieve text chunks from Qdrant vector memory
        q_content = ""
        if qdrant_manager and qdrant_manager.client:
            try:
                from qdrant_client import models
                scroll_res, _ = qdrant_manager.client.scroll(
                    collection_name=QDRANT_COLLECTION,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=file_id))]
                    ),
                    limit=100,
                    with_payload=True,
                )
                if not scroll_res:
                    scroll_res, _ = qdrant_manager.client.scroll(
                        collection_name=QDRANT_COLLECTION,
                        scroll_filter=models.Filter(
                            must=[models.FieldCondition(key="filename", match=models.MatchValue(value=orig_name))]
                        ),
                        limit=100,
                        with_payload=True,
                    )
                if scroll_res:
                    sorted_chunks = sorted(scroll_res, key=lambda p: (p.payload or {}).get("chunk_index", 0))
                    q_content = "\n\n".join([(p.payload or {}).get("chunk_text", "") for p in sorted_chunks if (p.payload or {}).get("chunk_text")])
            except Exception as qe:
                logger.warning(f"Error reading Qdrant preview: {qe}")

        if q_content:
            from fastapi.responses import HTMLResponse
            safe_content = q_content.replace("<", "&lt;").replace(">", "&gt;")
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{orig_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.7; padding: 40px; max-width: 900px; margin: 0 auto; color: #1f2328; background: #ffffff; }}
        .header {{ border-bottom: 1px solid #d0d7de; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ display: inline-block; padding: 4px 10px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; color: #0969da; margin-bottom: 10px; }}
        h1 {{ font-size: 24px; font-weight: 700; margin: 0; color: #1f2328; }}
        .content {{ white-space: pre-wrap; word-wrap: break-word; font-size: 14.5px; line-height: 1.75; color: #24292f; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge">Cognitive Memory Document</span>
        <h1>{orig_name}</h1>
    </div>
    <div class="content">{safe_content}</div>
</body>
</html>"""
            return HTMLResponse(content=html)

        raise HTTPException(status_code=404, detail="File content not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Fast in-memory preview cache to guarantee instant sub-10ms response times
PREVIEW_CONTENT_CACHE: Dict[str, Dict[str, Any]] = {}

@app.get("/files/{file_id}/content", tags=["Phase 5: Preview"])
async def get_file_content(file_id: str):
    """Retrieve raw text or code content for in-app preview modal in sub-10ms"""
    try:
        if file_id in SYSTEM_IGNORED_NAMES or file_id.startswith("."):
            raise HTTPException(status_code=404, detail="File not found")

        if file_id in PREVIEW_CONTENT_CACHE:
            return JSONResponse(PREVIEW_CONTENT_CACHE[file_id])

        metadata = load_metadata()
        file_meta = metadata.get(file_id, {})
        filename = file_meta.get("filename", f"{file_id}.txt")
        category = file_meta.get("file_type_category", get_file_category(filename))
        ext = file_meta.get("extension", Path(filename).suffix.replace(".", "").lower())

        file_path: Optional[Path] = None
        candidates = []
        if file_meta and file_meta.get("file_path"):
            fp = file_meta["file_path"]
            candidates.append(Path(fp))
            candidates.append(UPLOAD_DIR / fp)
            candidates.append(UPLOAD_DIR / fp.replace("uploads/", ""))
            candidates.append(BASE_DIR / fp)
            candidates.append(BASE_DIR / "test_corpus" / fp.replace("uploads/", ""))
            candidates.append(BASE_DIR / "test_corpus" / "real_corpus_150" / fp.replace("uploads/real_corpus_150/", ""))
        candidates.append(UPLOAD_DIR / f"{file_id}.{ext}")
        candidates.append(UPLOAD_DIR / filename)

        for cand in candidates:
            try:
                if cand and cand.is_file() and cand.name not in SYSTEM_IGNORED_NAMES:
                    file_path = cand
                    break
            except Exception:
                continue

        is_binary = category in {"photo", "pdf"} or ext in {"png", "jpg", "jpeg", "webp", "gif", "pdf"}
        text_content = ""
        visual_metadata = ""

        # Extract genuine content from the real physical file on disk (<5ms)
        if file_path and file_path.is_file():
            if ext == "docx":
                try:
                    from services.extraction import extract_docx
                    text_content = extract_docx(str(file_path))
                except Exception as de:
                    logger.warning(f"Failed to extract docx: {de}")
            elif ext == "pdf":
                # For PDFs, do ultra-fast light extraction with fitz (PyMuPDF <20ms)
                try:
                    import fitz
                    with fitz.open(str(file_path)) as doc:
                        pages_text = []
                        for i in range(min(5, len(doc))):
                            raw_val = doc[i].get_text()
                            t_str = str(raw_val or "").strip()
                            if t_str:
                                pages_text.append(t_str)
                        text_content = "\n\n--- Page Break ---\n\n".join(pages_text)
                        visual_metadata = text_content
                except Exception as pe:
                    logger.warning(f"Fast PDF extraction error: {pe}")
            elif not is_binary or ext == "svg":
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(file_path, "r", encoding="latin-1") as f:
                            text_content = f.read()
                    except Exception:
                        pass

        # If disk read didn't provide text, retrieve genuine pre-extracted text from Qdrant memory layer (<5ms)
        if not text_content and qdrant_manager and qdrant_manager.client:
            try:
                from qdrant_client import models
                scroll_res, _ = qdrant_manager.client.scroll(
                    collection_name=QDRANT_COLLECTION,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=file_id))]
                    ),
                    limit=50,
                    with_payload=True,
                )
                if not scroll_res:
                    scroll_res, _ = qdrant_manager.client.scroll(
                        collection_name=QDRANT_COLLECTION,
                        scroll_filter=models.Filter(
                            must=[models.FieldCondition(key="filename", match=models.MatchValue(value=filename))]
                        ),
                        limit=50,
                        with_payload=True,
                    )
                if scroll_res:
                    sorted_chunks = sorted(scroll_res, key=lambda p: (p.payload or {}).get("chunk_index", 0))
                    texts = [(p.payload or {}).get("chunk_text", "") for p in sorted_chunks if (p.payload or {}).get("chunk_text")]
                    if is_binary:
                        visual_metadata = "\n\n".join(texts)
                    else:
                        text_content = "\n\n".join(texts)
            except Exception as qe:
                logger.warning(f"Could not load chunks from Qdrant for preview: {qe}")

        result_payload = {
            "file_id": file_id,
            "filename": filename,
            "category": category,
            "extension": ext,
            "is_binary": is_binary,
            "content": text_content,
            "visual_metadata": visual_metadata or text_content,
            "preview_url": f"/preview/{file_id}",
            "size_bytes": file_path.stat().st_size if file_path and file_path.is_file() else file_meta.get("size_bytes", len(text_content.encode("utf-8"))),
            "topic_tags": file_meta.get("topic_tags", [])
        }

        # Cache valid payload
        if text_content or visual_metadata or is_binary:
            PREVIEW_CONTENT_CACHE[file_id] = result_payload

        return JSONResponse(result_payload)



    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FileContent] Error for file_id={file_id}: {e}")
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
        if file_id in SYSTEM_IGNORED_NAMES or file_id.startswith("."):
            raise HTTPException(status_code=400, detail="Cannot delete system database or reserved file")

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
    """List all 175 cataloged files using persistent metadata and disk synchronization"""
    try:
        metadata = load_metadata()
        folders = load_folders()
        uploaded_files = []
        seen_ids = set()

        # 1. Populate all actual cataloged files from metadata.json
        for file_id, info in metadata.items():
            if file_id in SYSTEM_IGNORED_NAMES or file_id.startswith("."):
                continue

            filename = info.get("filename", f"{file_id}.txt")
            ext = info.get("extension") or Path(filename).suffix.replace(".", "").lower() or "txt"
            cat = info.get("file_type_category") or get_file_category(filename)
            f_folder_id = info.get("folder_id")

            # Check if file has a physical disk target to get exact size/mtime if available
            f_target = None
            if info.get("file_path") and Path(info["file_path"]).is_file():
                f_target = Path(info["file_path"])
            elif info.get("file_path") and (UPLOAD_DIR / info["file_path"]).is_file():
                f_target = UPLOAD_DIR / info["file_path"]
            elif (UPLOAD_DIR / f"{file_id}.{ext}").is_file():
                f_target = UPLOAD_DIR / f"{file_id}.{ext}"

            size_bytes = info.get("size_bytes")
            if size_bytes is None and f_target:
                size_bytes = f_target.stat().st_size
            elif size_bytes is None:
                size_bytes = 1024

            modified_ts = info.get("upload_time")
            if modified_ts is None and f_target:
                modified_ts = f_target.stat().st_mtime
            elif modified_ts is None:
                modified_ts = time.time()

            uploaded_files.append({
                "file_id": file_id,
                "name": filename,
                "size_bytes": size_bytes,
                "modified": modified_ts,
                "extension": ext,
                "file_type_category": cat,
                "topic_tags": info.get("topic_tags", []),
                "folder_id": f_folder_id,
                "folder_path": compute_folder_path(f_folder_id, folders),
            })
            seen_ids.add(file_id)

        # 2. Also catch any physical files on disk in UPLOAD_DIR not yet in metadata
        for f in UPLOAD_DIR.glob("*"):
            if not f.is_file() or f.name in SYSTEM_IGNORED_NAMES or f.name.startswith("."):
                continue
            if f.stem not in seen_ids:
                ext = f.suffix.replace(".", "").lower()
                uploaded_files.append({
                    "file_id": f.stem,
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                    "extension": ext,
                    "file_type_category": get_file_category(f.name),
                    "topic_tags": [],
                    "folder_id": None,
                    "folder_path": "/",
                })

        return JSONResponse({
            "uploaded_files": sorted(uploaded_files, key=lambda x: x["modified"], reverse=True)
        })
    except Exception as e:
        logger.error(f"[Files] Error listing files: {e}")
        return JSONResponse({"uploaded_files": []})


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

# ============================================================================
# Phase 5: Privacy-Preserving Local Feedback (Objective 5)
# ============================================================================

@app.post("/feedback", tags=["Phase 5: Local Feedback"])
async def record_interaction_feedback(payload: Dict[str, Any] = Body(...)):
    """
    Record local user interaction signal (clicks, downloads, dwell times)
    completely offline in local storage without transmitting telemetry externally.
    """
    try:
        feedback_file = Path("data/interaction_feedback.json")
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        events = []
        if feedback_file.exists():
            try:
                with open(feedback_file, "r") as f:
                    events = json.load(f)
            except Exception:
                events = []
        payload["timestamp"] = time.time()
        events.append(payload)
        with open(feedback_file, "w") as f:
            json.dump(events[-500:], f, indent=2)
        return JSONResponse({"status": "recorded", "action": payload.get("action", "unknown")})
    except Exception as e:
        logger.error(f"Feedback recording error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

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
