#!/usr/bin/env python3
"""
Generate complete, clean metadata.json with all 27 baseline files
plus 138 real corpus files with genuine filenames and correct folder mapping.
"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
CORPUS_DIR = BASE_DIR / "test_corpus" / "real_corpus_150"
META_FILE = UPLOADS_DIR / "metadata.json"
FOLDERS_FILE = UPLOADS_DIR / "folders.json"

# 1. Load folders
with open(FOLDERS_FILE) as f:
    folders = json.load(f)

folder_by_name = {f.get("name"): f.get("id") for f in folders if isinstance(f, dict)}
cat_specs = {
    "pdfs": ("arXiv Research Papers", folder_by_name.get("arXiv Research Papers")),
    "images": ("Architecture & Diagrams", folder_by_name.get("Architecture & Diagrams")),
    "code": ("Backend Source Modules", folder_by_name.get("Backend Source Modules")),
    "documents": ("RFC Protocols & Specifications", folder_by_name.get("RFC Protocols & Specifications"))
}

# 2. Extract baseline 27 original files from current local metadata
with open(META_FILE) as f:
    curr_meta = json.load(f)

complete_meta = {}
# The 27 baseline files
for fid, info in curr_meta.items():
    fname = info.get("filename", "")
    # Baseline files have natural filenames or are the original 27
    if not (len(fname) >= 36 and fname.count("-") >= 4 and (fname.endswith(".pdf") or fname.endswith(".txt") or fname.endswith(".png") or fname.endswith(".py") or fname.endswith(".docx")) and fname[:8] == fid[:8]):
        # Also exclude if it's already a real_corpus_150 file (we will add freshly)
        if "real_corpus_150" not in info.get("file_path", ""):
            complete_meta[fid] = info

print(f"Loaded {len(complete_meta)} baseline original files.")

# 3. Add all 138 real corpus files
now_iso = datetime.now(timezone.utc).isoformat()
added = 0

for sub_dir, (folder_name, folder_id) in cat_specs.items():
    sub_path = CORPUS_DIR / sub_dir
    if not sub_path.exists():
        continue
    
    folder_path_str = f"/{folder_name}"

    for file_path in sorted(sub_path.glob("*")):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue
        
        orig_name = file_path.name
        ext = file_path.suffix.lower()
        clean_ext = ext.replace(".", "")
        
        # Deterministic UUID
        file_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, orig_name))
        rel_path = f"uploads/real_corpus_150/{sub_dir}/{orig_name}"

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

        complete_meta[file_id] = {
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
            "folder_id": folder_id,
            "folder_path": folder_path_str,
            "chunk_count": 1
        }
        added += 1

with open(META_FILE, "w") as f:
    json.dump(complete_meta, f, indent=2)

print(f"✓ Generated complete metadata.json with {len(complete_meta)} total files (27 baseline + {added} real corpus).")
