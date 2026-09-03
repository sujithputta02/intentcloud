# IntentCloud — Review-1 Presentation
**System Architecture & Design**

| | |
|---|---|
| **Date** | 29 August 2026 |
| **Review** | Review-1 — System Architecture & Design |
| **Project** | IntentCloud: Intent-Aware Cognitive Cloud Memory System |
| **Team** | Sujith Putta (ENG23CT0058) · K Vikas Aneesh Reddy (ENG23CT0052) · Mokshith Karnati (ENG23CT0053) |
| **Guide** | Dr. Ramandeep Kaur, Dept. of CST, Dayananda Sagar University |

> Convert each `## Slide N` section to one PowerPoint slide. Full diagrams are in `REVIEW_1_DIAGRAMS.md`.

---

## Slide 1 — Title

**IntentCloud: Intent-Aware Cognitive Cloud Memory System**

Review-1 — System Architecture & Design  
29 August 2026

Sujith Putta · K Vikas Aneesh Reddy · Mokshith Karnati  
Guide: Dr. Ramandeep Kaur  
Department of Computer Science & Technology, Dayananda Sagar University

---

## Slide 2 — Agenda

1. System architecture diagram  
2. Detailed description of modules / components  
3. Workflow / process diagrams  
4. Database design (schema & ER diagram)  
5. Technology stack  
6. Hardware and software requirements  
7. Algorithms, tools, libraries, and frameworks  
8. Implementation plan and proposed development approach  
9. Project timeline / milestones  
10. Task allocation and responsibilities among team members  

---

## Slide 3 — System Architecture Diagram

**Three-layer architecture: User → Cognitive → Memory**

```
┌──────────────────────────────────────────────────────────────┐
│                     USER LAYER (Next.js)                      │
│  Home · Upload · Search · Dashboard  →  localhost:3000       │
└────────────────────────────┬─────────────────────────────────┘
                             │ REST (HTTP)
┌────────────────────────────▼─────────────────────────────────┐
│              COGNITIVE LAYER (FastAPI — Laptop)               │
│  Phase 1: Upload + Extract (PyMuPDF, python-docx, Tesseract)│
│  Phase 2: Embed (MiniLM-L6-v2) + Index (Qdrant)             │
│  Phase 3: Intent parse (Ollama) + Dense search              │
│  Phase 4: Sparse/BM25 + RRF + cross-encoder rerank        │
│  Phase 5: Download / Delete / Tunnel serving                │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│           MEMORY LAYER (Raspberry Pi 4B + USB)              │
│  Qdrant embedded · uploads/ · metadata.json · cloudflared   │
└──────────────────────────────────────────────────────────────┘
                             │
                    Cloudflare Tunnel (HTTPS)
```

**Design principle:** Cognitive processing on laptop; persistent storage and always-on serving on Raspberry Pi.

---

## Slide 4 — Modules / Components (Frontend)

| Component | Path | Responsibility |
|---|---|---|
| **Home page** | `intentcloud-web/app/page.tsx` | Project overview and navigation |
| **Upload page** | `intentcloud-web/app/upload/page.tsx` | Drag-and-drop file upload (PDF, DOCX, TXT) |
| **Search page** | `intentcloud-web/app/search/page.tsx` | Natural language query input and ranked results |
| **Dashboard** | `intentcloud-web/app/dashboard/page.tsx` | File count, vector count, memory profile stats |
| **API client** | Frontend fetch calls | Communicates with FastAPI backend on port 8000 |

**Stack:** Next.js 16 (App Router), React 19, Tailwind CSS 4

---

## Slide 5 — Modules / Components (Backend)

| Module | File | Responsibility |
|---|---|---|
| **Upload & validation** | `main.py` | Accept files, assign UUID, queue background indexing |
| **Text extraction** | `services/extraction.py` | PyMuPDF / python-docx / TXT; Tesseract OCR if text < 100 chars |
| **Embeddings** | `services/embeddings.py` | Chunk text; generate 384-dim dense + sparse hash vectors |
| **Vector index** | `services/qdrant_client.py` | Qdrant upsert, duplicate check, dense / sparse / hybrid search |
| **Intent parser** | `services/intent_parser.py` | NL query → JSON (topic, keywords, intent_type, confidence) via Ollama |
| **Search orchestrator** | `services/search.py` | Intent parsing + retrieval + snippet / explanation enrichment |
| **Metadata store** | `uploads/metadata.json` | File tracking — filename, size, tags, chunk count, status |
| **Raw file store** | `uploads/{file_id}.{ext}` | Original uploaded documents on disk / USB |

**Stack:** FastAPI + Uvicorn, Python 3.11, service-module layout

---

## Slide 6 — Workflow: Upload & Indexing Process

```
User selects file (PDF / DOCX / TXT)
        ↓
POST /upload  →  save uploads/{uuid}.ext + metadata.json entry
        ↓
Background task (async)
        ├─ Extract text (PyMuPDF / python-docx / Tesseract OCR)
        ├─ Chunk + embed (all-MiniLM-L6-v2, 384-dim)
        ├─ Duplicate check (document cosine ≥ 0.95 → reject)
        ├─ Upsert chunks to Qdrant (dense + sparse vectors)
        └─ Update metadata (topic tags, chunk count)
        ↓
GET /stats  →  dashboard shows file & vector counts
```

---

## Slide 7 — Workflow: Search Process

```
User enters natural language query on /search
        ↓
POST /search?query=...&top_k=5
        ├─ Intent parsing (Ollama + llama3.2:1b → JSON)
        │     fallback: keyword extraction if Ollama unavailable
        ├─ Query embedding (same MiniLM model)
        ├─ Qdrant retrieval (dense now; hybrid + RRF in Week 5)
        └─ Enrich: rank, relevance %, matched snippet, explanation
        ↓
Frontend displays:
        • Understood Intent (topic, keywords, confidence)
        • Ranked result cards with excerpt + download link
```

**Target end-to-end flow (Phase 5–6):** Search → Top-3 reranked results → GET /download/{file_id} → original file returned via Cloudflare Tunnel HTTPS URL.

---

## Slide 8 — Database Design

IntentCloud uses a **vector-index + file + metadata** model (no relational SQL database).

### Qdrant collection: `intentcloud_docs`

| Field | Type | Purpose |
|---|---|---|
| Point ID | UUID | Primary key per text chunk |
| dense vector | 384 floats (cosine) | Semantic similarity search |
| sparse vector | hashed unigram/bigram | Keyword / hybrid search |
| Payload: `file_id` | string | Links chunk to source document |
| Payload: `filename`, `file_type` | string | Display and filtering |
| Payload: `chunk_index`, `chunk_text` | int, string | Snippet highlighting |
| Payload: `keywords[]`, `upload_time` | array, timestamp | Metadata enrichment |

### File metadata: `uploads/metadata.json`

```json
{
  "file_id": {
    "filename": "report.pdf",
    "size_bytes": 512000,
    "upload_time": 1787806144.3,
    "topic_tags": ["Kafka", "performance"],
    "chunk_count": 12,
    "status": "indexed"
  }
}
```

### ER diagram (logical relationships)

```
┌─────────────┐       1:N        ┌─────────────┐       1:1        ┌─────────────┐
│  Document   │─────────────────▶│    Chunk    │─────────────────▶│ Qdrant Point│
│  (file_id)  │                  │ (chunk_idx) │                  │  (UUID)     │
└─────────────┘                  └─────────────┘                  └─────────────┘
       │
       │ 1:1
       ▼
┌─────────────┐
│ metadata.json│
│   entry      │
└─────────────┘
       │
       │ 1:1
       ▼
┌─────────────┐
│ Raw file on │
│ disk / USB  │
└─────────────┘
```

---

## Slide 9 — Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4 | Web UI (upload, search, dashboard) |
| **Backend API** | FastAPI, Uvicorn | REST endpoints, background tasks |
| **Embeddings** | sentence-transformers `all-MiniLM-L6-v2` | 384-dim semantic vectors |
| **Intent LLM** | Ollama + `llama3.2:1b` | Local NL intent parsing (JSON output) |
| **Vector DB** | Qdrant embedded 1.19 | Persistent dense + sparse index |
| **Text extraction** | PyMuPDF, python-docx, Tesseract | PDF / DOCX / TXT + OCR fallback |
| **ML runtime** | PyTorch | MPS (Apple) / CUDA (NVIDIA) / CPU auto-detect |
| **Remote access** | Cloudflare Tunnel (cloudflared) | Public HTTPS without port forwarding |
| **Edge node OS** | Raspberry Pi OS 64-bit | Pi 4B memory layer |
| **Version control** | Git / GitHub | Team collaboration |

---

## Slide 10 — Hardware Requirements

| Item | Specification | Qty | Est. cost (₹) |
|---|---|---|---|
| Raspberry Pi 4 Model B | 8 GB RAM | 1 | 6,500 |
| microSD card | 64 GB A2/U3 | 1 | 700 |
| USB storage | 128 GB USB 3.0 | 1 | 1,000 |
| Power supply | 5.1V / 3A USB-C official | 1 | 700 |
| Cooling case | Active cooling | 1 | 600 |
| Ethernet cable | Cat6 (laptop ↔ Pi) | 1 | 200 |
| Contingency | Cables, card reader | — | 500 |
| **Total** | | | **~₹10,200** |

**Development laptops (all 3 members):** 8 GB+ RAM (16 GB preferred), Apple Silicon / NVIDIA GPU / CPU fallback supported.

**Procurement:** Raspberry Pi ordered by Week 5 (5 September 2026); interim development runs on laptops with identical directory layout for easy Pi migration.

---

## Slide 11 — Software Requirements

### Development environment (laptops)
- macOS (Apple Silicon) or Windows / Linux with NVIDIA GPU  
- Python 3.11+, Bun or Node.js 20 LTS  
- Ollama (local LLM server)  
- Tesseract OCR  
- Git  

### Raspberry Pi memory node
- Raspberry Pi OS 64-bit (Bookworm)  
- Python 3.11 virtual environment  
- Qdrant embedded, FastAPI, cloudflared  
- USB mount for persistent file storage  

### External services (free tier)
- Cloudflare Tunnel — public HTTPS access  
- GitHub — private repository  
- Hugging Face — one-time model download (cached locally)  

**Total software cost: ₹0** — fully open-source stack.

---

## Slide 12 — Algorithms, Tools, Libraries & Frameworks

| Stage | Algorithm / tool | Purpose |
|---|---|---|
| **Text extraction** | PyMuPDF, python-docx, Tesseract OCR | Offline ingest of PDF, DOCX, TXT, scanned PDFs |
| **Chunking** | Fixed-size text splitting | Prepare documents for embedding |
| **Dense embedding** | Transformer encoder MiniLM-L6-v2 | 384-dim semantic vectors |
| **Sparse embedding** | Hashed unigram / bigram vectors | Keyword-level retrieval |
| **Intent parsing** | Local LLM via Ollama (JSON mode) | Open-ended NL query understanding |
| **Dense retrieval** | Cosine similarity over Qdrant | Semantic nearest-neighbor search |
| **Sparse retrieval** | BM25-style sparse vector search | Exact keyword and filename matching |
| **Fusion** | Reciprocal Rank Fusion (k = 60) | Merge dense + sparse rankings: score(d) = Σ 1/(k + rank_i(d)) |
| **Reranking** | Cross-encoder `ms-marco-MiniLM-L-6-v2` | Improve top-3 precision |
| **Duplicate detection** | Document-level cosine ≥ 0.95 | Prevent duplicate indexing |
| **Explainability** | Highest-similarity chunk snippet | Show why each result matched |
| **No-match gate** | Confidence threshold on rerank score | Return "No confident match" for low-relevance queries |
| **Remote access** | Cloudflare Tunnel | Secure HTTPS without port forwarding |

---

## Slide 13 — Implementation Plan & Development Approach

### Six-phase implementation

| Phase | Scope | Target week |
|---|---|---|
| **Phase 1** | Upload, text extraction, OCR fallback | Week 2 |
| **Phase 2** | Embeddings, Qdrant indexing, duplicate detection, dashboard | Week 3 |
| **Phase 3** | Intent parsing + dense NL search | Week 4 (Review-1) |
| **Phase 4** | Hybrid sparse retrieval + RRF + cross-encoder rerank | Week 5 |
| **Phase 5** | Raspberry Pi deployment, USB storage, Cloudflare Tunnel, download/delete | Week 6 |
| **Phase 6** | Evaluation — 30–50 queries, baselines, latency measurement | Weeks 7–9 |

### Development approach
1. **Laptop-first:** Build and test on dev laptops using the same folder layout as the Pi.  
2. **Incremental retrieval:** dense baseline → hybrid → rerank (measurable improvement at each step).  
3. **Test-corpus driven:** 150–200 files across 8 topics with ground-truth query labels.  
4. **Automated regression:** end-to-end upload → index → search validation script.  
5. **Weekly reports:** progress documented every Saturday per department template.

---

## Slide 14 — Project Timeline & Milestones

| Week | Dates | Milestone | Progress |
|---|---|---|---|
| 1 | 3–7 Aug | Environment setup, Review-0 | ~10% |
| 2 | 10–14 Aug | Upload + extraction pipeline | ~15% |
| 3 | 17–21 Aug | Embeddings + Qdrant + dashboard | ~30% |
| 4 | 24–29 Aug | **Review-1** — intent search + architecture | **~40%** |
| 5 | 31 Aug–4 Sep | Hybrid + RRF + rerank; order Pi | ~50% |
| 6 | 7–11 Sep | Pi migration + Cloudflare Tunnel | ~60% |
| 7 | 14–18 Sep | Evaluation harness + baselines | ~70% |
| 8 | 21–25 Sep | UI polish, confidence gate, documentation | ~85% |
| 9 | 28 Sep–2 Oct | Final report + Review-3 prep | ~100% |

### Department review milestones

| Milestone | Date |
|---|---|
| Review-0 | 8 August 2026 ✅ |
| **Review-1** | **29 August 2026** |
| Review-2 (25% demo) | 12 September 2026 |
| Review-3 (50% demo) | 22 September 2026 |
| Phase-1 report | October 2026 |

---

## Slide 15 — Task Allocation & Responsibilities

### Primary roles

| Member | Primary ownership |
|---|---|
| **Sujith Putta** | Backend API, search pipeline, hybrid / RRF algorithms, Pi procurement & migration |
| **K Vikas Aneesh Reddy** | Qdrant indexing, duplicate detection, regression testing, cross-encoder integration |
| **Mokshith Karnati** | Next.js UI / UX, architecture diagrams, test corpus, weekly reports & presentations |

### Weekly task allocation

| Week | Sujith Putta | K Vikas Aneesh Reddy | Mokshith Karnati |
|---|---|---|---|
| **1** | FastAPI scaffold, /upload endpoint | Qdrant setup, extraction service | Next.js project setup, home page |
| **2** | Background tasks, OCR integration | Embedding pipeline, chunk indexing | Upload page UI |
| **3** | /stats endpoint, duplicate detection logic | Qdrant upsert, metadata.json | Dashboard UI |
| **4** | POST /search, Ollama intent parsing | Regression test corpus + script | Search page UI, Review-1 PPT |
| **5** | Sparse / BM25 + RRF implementation | Hybrid Qdrant query + cross-encoder rerank | Search UI — top-3 with explanations |
| **6** | Pi deployment, Cloudflare Tunnel setup | USB storage migration, Pi Qdrant config | UI polish, remote access testing |
| **7** | Evaluation query runner, latency measurement | Baseline comparison (keyword / dense / hybrid) | Results charts for Review-3 |
| **8** | Confidence threshold, download / delete endpoints | Expand corpus to 150+ files | Final UI, documentation |
| **9** | Phase-1 report — backend & algorithms section | Phase-1 report — evaluation section | Phase-1 report — UI & presentation |

---

*Review-1 presentation · 29 August 2026 · IntentCloud Team · Guide: Dr. Ramandeep Kaur*
