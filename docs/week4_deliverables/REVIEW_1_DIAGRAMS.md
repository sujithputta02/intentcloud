# Review-1: Architecture & Design Diagrams
**IntentCloud Phase 1-3 Architecture Review**  
**Date:** 29 August 2026  
**Status:** Ready for Review Gate

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        INTENTCLOUD SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │         USER LAYER (Laptop - Phase 1-3)                    │  │
│  │  Next.js Frontend on http://localhost:3000                 │  │
│  │  ├─ Home Page (marketing)                                  │  │
│  │  ├─ Upload Page (drag-drop interface)                      │  │
│  │  ├─ Search Page (natural language queries)                 │  │
│  │  └─ Dashboard (stats & memory profile)                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │      COGNITIVE LAYER (FastAPI Backend)                     │  │
│  │      http://localhost:8000                                 │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Phase 1: Data Ingestion                              │  │  │
│  │  │ ├─ POST /upload (file validation + storage)          │  │  │
│  │  │ └─ services/extraction.py (PDF/DOCX/TXT + OCR)       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                        ▼                                    │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Phase 2: Semantic Representation                     │  │  │
│  │  │ ├─ services/embeddings.py (sentence-transformers)    │  │  │
│  │  │ ├─ services/qdrant_client.py (vector indexing)       │  │  │
│  │  │ └─ GET /stats (dashboard stats)                      │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                        ▼                                    │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Phase 3: Intent-Aware Query Understanding            │  │  │
│  │  │ ├─ services/intent_parser.py (Phi-3 via Ollama)      │  │  │
│  │  │ ├─ services/search.py (dense semantic search)        │  │  │
│  │  │ └─ POST /search (intent parsing + ranking)           │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │      MEMORY LAYER (Persistent Storage)                     │  │
│  │  ├─ uploads/ (raw files: PDF, DOCX, TXT)                  │  │
│  │  ├─ qdrant_storage/ (embedded vector DB)                  │  │
│  │  └─ metadata.json (file tracking)                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │      EXTERNAL SERVICES (Required)                           │  │
│  │  ├─ Ollama (localhost:11434) → Phi-3 Mini intent parsing   │  │
│  │  └─ Tesseract (system) → OCR fallback for scanned PDFs     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [Future: Week 5+ will add Pi layer, Tunnel, Hybrid search]     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Request Flow

### Upload Flow (Phase 1: Data Ingestion)

```
User uploads PDF/DOCX/TXT
        ↓
[Frontend] POST /upload
        ↓
[Backend] Validate file type & size
        ↓
Save to disk (uploads/{file_id}.{ext})
        ↓
Background task triggers:
        ├─ Extract text (PyMuPDF → fallback to Tesseract OCR)
        ├─ Generate embeddings (sentence-transformers all-MiniLM-L6-v2, 384-dim)
        ├─ Detect duplicates (cosine similarity ≥ 0.95 → flag & skip)
        ├─ Store in Qdrant (vectors + metadata)
        └─ Update metadata.json (filename, size, timestamp, topic_tags)
        ↓
Return to user: file_id + "Processing in background..."
        ↓
[Dashboard] User sees file in /stats endpoint
```

### Search Flow (Phase 3: Intent-Aware Query Understanding)

```
User enters natural language query
        ↓
[Frontend] POST /search?query="{query}"&top_k=5
        ↓
[Backend] Parse intent with Phi-3:
        ├─ Query → Ollama API (localhost:11434)
        ├─ Phi-3 Mini outputs JSON:
        │  {
        │    "topic": "what user is looking for",
        │    "keywords": ["kw1", "kw2"],
        │    "intent_type": "find|compare|summarize",
        │    "has_time_constraint": true|false,
        │    "confidence": 0.0-1.0
        │  }
        └─ Fallback to keyword extraction if Ollama unavailable
        ↓
Dense semantic search:
        ├─ Generate query embedding (same model as document embeddings)
        ├─ Qdrant cosine similarity search (top_k=5)
        └─ Return [{file_id, filename, sentence, score, ...}]
        ↓
Enrich results with explanations:
        ├─ For each result, generate "why this matched"
        └─ Score-based explanation: "Strong match for '{topic}'" etc.
        ↓
Return to frontend:
        {
          "query": "{query}",
          "parsed_intent": {...},
          "results": [{rank, filename, relevance_score, explanation, ...}],
          "count": 5
        }
        ↓
[Frontend] Display:
        ├─ Parsed intent box (topic + keywords + confidence)
        ├─ Result cards (filename, relevance %, excerpt, explanation)
        └─ Color-coded relevance (green ≥70%, yellow ≥40%, red <40%)
```

---

## 3. Data Schema & Database Design

### Phase 1-3 Qdrant Vector Storage Schema

```json
{
  "collection_name": "intentcloud_docs",
  "vectors_config": {
    "size": 384,
    "distance": "Cosine"
  },
  "points": [
    {
      "id": "<hash(file_id, sentence_index)>",
      "vector": [0.123, -0.456, ...],  // 384-dim embedding
      "payload": {
        "file_id": "uuid-of-document",
        "filename": "report_2024.pdf",
        "topic_tags": ["Kafka", "Microservices", "Performance"],
        "sentence_index": 0,
        "sentence_text": "Kafka provides low-latency message streaming...",
        "upload_time": "2026-08-26T10:30:00Z",
        "text_preview": "Kafka provides low-latency message..."
      }
    },
    {
      "id": "<hash(file_id, sentence_index)>",
      "vector": [...],
      "payload": {...}
    }
  ]
}
```

### File Metadata Storage (metadata.json)

```json
{
  "uuid-1": {
    "file_id": "uuid-1",
    "filename": "thesis_draft.pdf",
    "size_bytes": 2097152,
    "upload_time": 1724166600.0,
    "extension": "pdf",
    "file_path": "./uploads/uuid-1.pdf",
    "topic_tags": ["Neural Networks", "Deep Learning"]
  },
  "uuid-2": {
    "file_id": "uuid-2",
    "filename": "meeting_notes.docx",
    "size_bytes": 51200,
    "upload_time": 1724170000.0,
    "extension": "docx",
    "file_path": "./uploads/uuid-2.docx",
    "topic_tags": ["Project Planning", "Team Sync"]
  }
}
```

### Duplicate Detection

```
When uploading new document:
  ├─ Extract text → generate embeddings
  ├─ Compare first embedding with existing vectors in Qdrant
  ├─ If any match with cosine_similarity ≥ 0.95:
  │  └─ Flag as duplicate, log warning, skip upsert
  └─ Otherwise: upsert all vectors
```

---

## 4. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Frontend** | Next.js | 16.3.1 | React SSR, App Router |
| | React | 19.2.8 | UI components |
| | TypeScript | 5.9 | Type safety |
| | Tailwind CSS | 4.3 | Styling + design tokens |
| | Bun | 1.3.14 | Package manager & runtime |
| **Backend** | FastAPI | 0.141.1 | Web framework |
| | Uvicorn | 0.52.4 | ASGI server |
| | Python | 3.9+ | Runtime |
| **ML/AI** | sentence-transformers | 6.0.0 | Embeddings (all-MiniLM-L6-v2, 384-dim) |
| | PyTorch | 2.13.0 | ML inference backend |
| | Phi-3 Mini | via Ollama | Intent parsing LLM |
| **Vector DB** | Qdrant | 1.19.0 | Embedded vector storage, cosine similarity |
| **Document Processing** | PyMuPDF | 1.28.2 | PDF text extraction |
| | python-docx | 1.2.0 | DOCX text extraction |
| | pytesseract | 0.3.10 | OCR fallback for scanned PDFs |
| **External** | Ollama | (localhost:11434) | Local LLM inference server |

---

## 5. API Endpoints (Phase 1-3)

### Health & Status

```
GET /health
→ Returns: {status, version, components:{api, qdrant, uploads_dir, phase}}
```

### Phase 1: Upload & Storage

```
POST /upload
Content-Type: multipart/form-data
Body: {file}
→ Returns: {status, file_id, filename, size_bytes, message}
  Background: extract → embed → deduplicate → index in Qdrant

GET /files
→ Returns: {uploaded_files: [{file_id, name, size_bytes, modified, extension}]}

GET /download/{file_id}
→ Returns: File binary (original filename preserved)

DELETE /files/{file_id}
→ Returns: {status, message, file_id}
  Cleans up: disk file + metadata + Qdrant vectors
```

### Phase 2: Dashboard & Statistics

```
GET /stats
→ Returns: {
    total_vectors: <count>,
    total_files: <count>,
    collection: "intentcloud_docs",
    vector_dim: 384,
    topic_counts: {topic: count, ...},
    status: "ready"
  }
```

### Phase 3: Intent-Aware Search

```
POST /search
Query params: query (string, required), top_k (int, default 5)
→ Returns: {
    query: "<original query>",
    parsed_intent: {
      topic: "what user is looking for",
      keywords: ["kw1", "kw2"],
      intent_type: "find|compare|...",
      has_time_constraint: bool,
      confidence: 0.0-1.0
    },
    results: [
      {
        rank: 1,
        file_id: "uuid",
        filename: "document.pdf",
        sentence_text: "...",
        relevance_score: 0.92,
        relevance_percentage: 92,
        explanation: "Strong semantic match for...",
        upload_time: "2026-08-26T..."
      },
      ...
    ],
    count: 5
  }
```

---

## 6. Module Architecture

```
intentcloud-api/
├── main.py
│   ├─ FastAPI app setup
│   ├─ CORS middleware
│   ├─ Lifespan (startup/shutdown)
│   ├─ Endpoints: /health, /upload, /search, /stats, /download, /files
│   └─ Background pipeline orchestration
│
└── services/
    ├── extraction.py
    │   ├─ extract_pdf() → PyMuPDF + Tesseract OCR fallback
    │   ├─ extract_docx() → python-docx
    │   └─ extract_txt() → read file
    │
    ├── embeddings.py
    │   ├─ EmbeddingsManager class
    │   ├─ generate_embeddings() → sentence-transformers all-MiniLM-L6-v2
    │   ├─ classify_topic_tags() → derive topics from text
    │   └─ Models cached in ~/.cache/huggingface
    │
    ├── qdrant_client.py
    │   ├─ QdrantIndexManager class
    │   ├─ _ensure_collection_exists() → create if missing
    │   ├─ upsert_document() → insert vectors + metadata
    │   ├─ _check_duplicate() → cosine similarity ≥ 0.95 check
    │   ├─ search() → dense semantic search
    │   └─ get_collection_stats() → dashboard stats
    │
    ├── intent_parser.py
    │   ├─ parse_intent_with_phi3() → query → Ollama → JSON
    │   ├─ build_intent_prompt() → structured prompt
    │   ├─ call_ollama_phi3() → HTTP POST to localhost:11434
    │   ├─ parse_ollama_response() → JSON extraction & validation
    │   └─ get_fallback_intent() → keyword extraction fallback
    │
    └── search.py
        ├─ hybrid_search() → dense search only (Phase 3)
        ├─ generate_query_embedding() → query → embedding
        ├─ enrich_results_with_explanation() → add "why matched"
        └─ Phase 4 placeholders: sparse_keyword_search, RRF, cross_encoder_rerank
```

---

## 7. Deployment Topology (Week 4 Status)

```
LAPTOP (Phase 1-3 Complete)
├─ Browser (http://localhost:3000)
│  └─ Next.js Frontend (Bun dev server)
│
├─ Terminal 1 (http://localhost:8000)
│  └─ FastAPI Backend (Uvicorn)
│
├─ Terminal 2 (http://localhost:11434)
│  └─ Ollama Server + Phi-3 Mini Model
│
└─ Persistent Storage
   ├─ ./uploads/ (PDF/DOCX/TXT files)
   ├─ ./qdrant_storage/ (embedded Qdrant)
   └─ ./metadata.json (file tracking)

RASPBERRY PI (Week 5+ Target)
[Placeholder - not yet deployed in Phase 1-3]
├─ Qdrant Server (remote)
├─ Persistent storage (SSD/USB)
└─ Cloudflare Tunnel for secure access
```

---

## 8. Testing & Validation Checklist (Week 4)

- ✅ Phase 1: Upload → Extract → Embed → Store pipeline
- ✅ Phase 2: Dashboard stats endpoint (total files, vectors, topics)
- ✅ Phase 3: Search endpoint with intent parsing
- ✅ Duplicate detection (cosine similarity 0.95 threshold)
- ✅ OCR fallback for scanned PDFs
- ✅ Theme switching (light/dark/system) persistent
- ✅ Responsive design (360px, 768px, 1280px)
- ✅ Error handling & fallbacks (Ollama offline, etc.)
- ✅ WCAG AA color contrast (both themes)
- ✅ All endpoints compile & run without crashes

---

## 9. Phase Roadmap

```
Week 1-3: Phase 1-3 (COMPLETE)
├─ Week 1-2: Phase 1 (upload, extraction)
├─ Week 2-3: Phase 2 (embeddings, indexing)
└─ Week 3-4: Phase 3 (intent parsing, search)

Week 4: Review-1 Gate (THIS WEEK)
├─ Validation: All Phase 1-3 pipelines working
├─ Documentation: Architecture, diagrams, tech stack
└─ Readiness: Prepared for Phase 4 handoff

Week 5: Phase 4 (Hybrid Search - NOT YET IMPLEMENTED)
├─ Sparse/BM25 keyword search
├─ Reciprocal Rank Fusion merging
├─ Cross-encoder reranking (top-3)
└─ Updated /search endpoint

Week 6-7: Phase 5 (Remote & Hardware)
├─ Raspberry Pi deployment
├─ Cloudflare Tunnel setup
├─ Remote Qdrant server
└─ USB/SSD persistent storage

Week 8-9: Phase 6+ (Evaluation, Optimization)
├─ User studies & feedback
├─ Performance optimization
├─ Edge case handling
└─ Production hardening
```

---

## 10. Known Limitations & Future Work

### Phase 1-3 Scope (Current)

- ✅ Dense semantic search only (no BM25/sparse yet)
- ✅ Single-user system (no authentication)
- ✅ Laptop-only (no Pi/remote storage yet)
- ✅ Local Ollama inference (no cloud API)
- ✅ Cosine similarity only (no reranking yet)

### Phase 4+ (Week 5+)

- [ ] Hybrid search (dense + sparse + RRF)
- [ ] Cross-encoder reranking
- [ ] User authentication & per-user storage
- [ ] Raspberry Pi deployment
- [ ] Cloudflare Tunnel for remote access
- [ ] Performance evaluation & optimization

---

**Document Status:** Ready for Review-1 approval (29 August 2026)  
**Architecture:** Validated and tested  
**Tech Stack:** All dependencies installed and working  
**Next Gate:** Proceed to Phase 4 (Week 5) if approved
