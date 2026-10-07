#!/usr/bin/env python3
"""
Clean and catalog the 138 real corpus files with their exact original names,
folders, and metadata, preserving existing files and cleaning any stray UUID copies.
"""
import os
import sys
import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone

# Locate uploads directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
UPLOADS_DIR = PROJECT_DIR / "uploads"
CORPUS_DIR = UPLOADS_DIR / "real_corpus_150"
META_FILE = UPLOADS_DIR / "metadata.json"
FOLDERS_FILE = UPLOADS_DIR / "folders.json"

if not CORPUS_DIR.exists():
    print(f"Error: {CORPUS_DIR} not found")
    sys.exit(1)

# 1. Setup Folders
cat_folder_specs = {
    "pdfs": ("arXiv Research Papers", "purple"),
    "images": ("Architecture & Diagrams", "amber"),
    "code": ("Backend Source Modules", "green"),
    "documents": ("RFC Protocols & Specifications", "blue")
}

folders = []
if FOLDERS_FILE.exists():
    try:
        with open(FOLDERS_FILE, "r") as f:
            folders = json.load(f)
    except Exception:
        folders = []

folder_by_name = {f.get("name"): f for f in folders if isinstance(f, dict)}
folder_ids = {}

for sub_dir, (folder_name, color) in cat_folder_specs.items():
    if folder_name not in folder_by_name:
        fid = str(uuid.uuid4())
        new_folder = {
            "id": fid,
            "name": folder_name,
            "parent_id": None,
            "color": color,
            "created_at": time.time()
        }
        folders.append(new_folder)
        folder_by_name[folder_name] = new_folder
        folder_ids[sub_dir] = fid
    else:
        folder_ids[sub_dir] = folder_by_name[folder_name]["id"]

with open(FOLDERS_FILE, "w") as f:
    json.dump(folders, f, indent=2)

# 2. Load existing metadata and keep only genuine files (exclude UUID-named duplicates)
metadata = {}
if META_FILE.exists():
    try:
        with open(META_FILE, "r") as f:
            raw_meta = json.load(f)
            for fid, info in raw_meta.items():
                fname = info.get("filename", "")
                # Preserve existing files that are not UUID-named stray artifacts
                if not (len(fname) >= 36 and fname.count("-") >= 4 and (fname.endswith(".pdf") or fname.endswith(".txt") or fname.endswith(".png") or fname.endswith(".py") or fname.endswith(".docx")) and fname[:8] == fid[:8]):
                    metadata[fid] = info
    except Exception:
        metadata = {}

print(f"Preserved {len(metadata)} existing baseline files.")

# 3. Catalog the 138 real corpus files
now_iso = datetime.now(timezone.utc).isoformat()
added = 0

for sub_dir in ["pdfs", "images", "code", "documents"]:
    sub_path = CORPUS_DIR / sub_dir
    if not sub_path.exists():
        continue
    
    fid_for_folder = folder_ids[sub_dir]
    folder_path_str = f"/{cat_folder_specs[sub_dir][0]}"

    for file_path in sorted(sub_path.glob("*")):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue
        
        orig_name = file_path.name
        ext = file_path.suffix.lower()
        clean_ext = ext.replace(".", "")
        
        # Check if already in metadata by filename
        existing_fid = None
        for fid, info in metadata.items():
            if info.get("filename") == orig_name:
                existing_fid = fid
                break
        
        file_id = existing_fid or str(uuid.uuid4())
        rel_path = f"uploads/real_corpus_150/{sub_dir}/{orig_name}"

        # Clean tags
        stem_clean = file_path.stem.replace("_", " ").replace("-", " ")
        tags = [w.capitalize() for w in stem_clean.split() if len(w) > 2]
        if sub_dir == "pdfs":
            tags.insert(0, "Research Paper")
            cat = "pdf"
        elif sub_dir == "images":
            tags.insert(0, "Architecture Diagram")
            cat = "photo"
        elif sub_dir == "code":
            tags.insert(0, "Source Code")
            cat = "code"
        else:
            tags.insert(0, "Specification")
            cat = "document"

        metadata[file_id] = {
            "file_id": file_id,
            "filename": orig_name,
            "size_bytes": file_path.stat().st_size,
            "upload_time": file_path.stat().st_mtime,
            "created_at": now_iso,
            "modified_at": now_iso,
            "version_number": 1,
            "is_latest": True,
            "parent_id": None,
            "extension": clean_ext,
            "file_path": rel_path,
            "file_type_category": cat,
            "topic_tags": tags[:8],
            "folder_id": fid_for_folder,
            "folder_path": folder_path_str,
            "chunk_count": 1
        }
        added += 1

with open(META_FILE, "w") as f:
    json.dump(metadata, f, indent=2)

print(f"✓ Total cataloged files in metadata: {len(metadata)} (added {added} real corpus files)")
