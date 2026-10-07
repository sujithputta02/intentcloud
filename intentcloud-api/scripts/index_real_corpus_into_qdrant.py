#!/usr/bin/env python3
"""
IntentCloud - Batch Ingestion of Real Multi-Modal Corpus into Qdrant Memory Layer.
Extracts document structure, generates dense (MiniLM-L6) and sparse (feature hash)
embeddings, and writes vectors into Qdrant collection `intentcloud_docs`.
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from services.extraction import extract_document_tree
from services.embeddings import generate_embeddings
from services.qdrant_client import QdrantIndexManager, COLLECTION_NAME, QDRANT_PATH

def main():
    print("=" * 65)
    print("IntentCloud Cognitive Memory Ingestion: Real Multi-Modal Corpus")
    print("=" * 65)
    
    meta_path = PROJECT_DIR / "uploads" / "metadata.json"
    if not meta_path.exists():
        print(f"Error: {meta_path} does not exist!")
        sys.exit(1)
        
    with open(meta_path) as f:
        metadata = json.load(f)
        
    print(f"Loaded {len(metadata)} documents from metadata.json")
    
    # Initialize QdrantIndexManager locally
    qm = QdrantIndexManager()
    stats = qm.get_collection_stats()
    print(f"Initial Qdrant Status: total_vectors={stats.get('total_vectors')}, files={stats.get('total_files')}")
    
    t0 = time.time()
    success_count = 0
    skipped_count = 0
    error_count = 0
    total_chunks_added = 0
    
    # Process each document
    for idx, (file_id, info) in enumerate(metadata.items(), 1):
        filename = info.get("filename", "")
        file_path_rel = info.get("file_path", "")
        file_path = PROJECT_DIR / file_path_rel
        
        # Fallback search if relative path doesn't exist
        if not file_path.exists():
            candidates = list((PROJECT_DIR / "test_corpus" / "real_corpus_150").rglob(filename))
            if candidates:
                file_path = candidates[0]
            else:
                candidates2 = list((PROJECT_DIR / "uploads").rglob(filename))
                if candidates2:
                    file_path = candidates2[0]
                else:
                    candidates3 = list((PROJECT_DIR / "uploads").glob(f"{file_id}.*"))
                    if candidates3:
                        file_path = candidates3[0]
                        
        if not file_path.exists() or not file_path.is_file():
            print(f"[{idx}/{len(metadata)}] Skipping missing file: {filename}")
            skipped_count += 1
            continue
            
        file_ext = file_path.suffix.lower().replace(".", "")
        folder_id = info.get("folder_id")
        folder_path = info.get("folder_path", "/")
        
        try:
            print(f"[{idx}/{len(metadata)}] Extracting & Embedding: {filename} ({file_ext})...", end="", flush=True)
            
            # Step 1: Extract Document Tree
            doc_tree = extract_document_tree(str(file_path), original_filename=filename)
            full_text = doc_tree.get("full_text", "")
            
            if not full_text or len(full_text.strip()) < 10:
                # Provide standard fallback header
                full_text = f"[{filename}]\nTechnical document for {filename}."
                doc_tree["full_text"] = full_text
                doc_tree["sections"] = [{
                    "section_id": "sec_0",
                    "title": filename,
                    "section_path": [filename],
                    "text": full_text,
                    "page": 1
                }]
                
            # Step 2: Generate Universal Dense + Sparse Embeddings
            representation = generate_embeddings(
                doc_tree,
                doc_title=filename,
                doc_category=file_ext,
            )
            chunk_count = representation.get("chunk_count", 1)
            
            # Step 3: Upsert into Qdrant
            res = qm.upsert_document(
                file_id=file_id,
                filename=filename,
                text_content=doc_tree,
                file_type=file_ext,
                metadata={
                    "folder_id": folder_id,
                    "folder_path": folder_path,
                }
            )
            
            if res.get("success"):
                success_count += 1
                total_chunks_added += chunk_count
                metadata[file_id]["chunk_count"] = chunk_count
                print(f" ✓ ({chunk_count} chunks)")
            else:
                print(f" (duplicate/skipped)")
                skipped_count += 1
                
        except Exception as exc:
            print(f" ✗ Error: {exc}")
            error_count += 1
            
    # Save updated chunk counts in metadata
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    duration = time.time() - t0
    stats_after = qm.get_collection_stats()
    print("\n" + "=" * 65)
    print(f"INGESTION COMPLETE in {duration:.2f}s")
    print(f"Success: {success_count} docs | Errors: {error_count} | Skipped: {skipped_count}")
    print(f"Total Chunks Added: {total_chunks_added}")
    print(f"Updated Qdrant Total Vectors: {stats_after.get('total_vectors')}")
    print("=" * 65)

if __name__ == "__main__":
    main()
