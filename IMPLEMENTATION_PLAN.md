# IntentCloud - First 3 Weeks Implementation Plan

## Project Structure

```
intentcloud/
├── intentcloud-api/              # FastAPI Backend
│   ├── main.py                   # Main app with endpoints
│   ├── services/
│   │   ├── extraction.py        # Phase 1: Text extraction
│   │   ├── embeddings.py        # Phase 2: Embeddings
│   │   ├── qdrant_client.py     # Qdrant vector store
│   │   ├── intent_parser.py     # Phase 3: Intent parsing
│   │   └── search.py            # Phase 3: Hybrid search
│   ├── uploads/                  # Uploaded files storage
│   ├── qdrant_storage/           # Qdrant DB storage
│   ├── requirements.txt          # Python dependencies
│   └── venv/                     # Virtual environment
│
├── intentcloud-web/              # Next.js Frontend (Bun)
│   ├── app/
│   │   ├── layout.tsx           # App layout with theme provider
│   │   ├── page.tsx             # Home page
│   │   ├── globals.css          # Design system tokens
│   │   ├── upload/              # Phase 1: Upload page
│   │   ├── search/              # Phase 3: Search page
│   │   └── dashboard/           # Phase 2: Dashboard page
│   ├── components/
│   │   ├── Navbar.tsx           # Navigation + theme toggle
│   │   ├── ThemeProvider.tsx    # Theme management
│   │   └── [more components]
│   ├── lib/
│   │   └── api.ts               # API client utilities
│   ├── package.json             # Frontend dependencies (Bun)
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── README.md                      # Project documentation
```

## Week 1 (03-08 Aug 2026) - Scaffolding & Verification

### Completed ✓
- [x] Project structure created (Next.js + FastAPI)
- [x] FastAPI main app with health endpoint
- [x] Next.js app with App Router, TypeScript, Tailwind
- [x] Design system (CSS tokens, light/dark theme)
- [x] Navbar component with theme switching
- [x] Upload page UI (drag-and-drop)

### Deliverables for Week 1
- [x] Next.js frontend bootstrapped with Bun
- [x] FastAPI backend with CORS and health check
- [ ] Verify Next.js dev server runs: `bun run dev`
- [ ] Verify FastAPI backend runs: `python main.py`
- [ ] Verify Ollama + Phi-3 Mini installed
- [ ] Verify Qdrant embedded client initializes
- [ ] Health check endpoint responds with all components healthy

### Status: ~15% Complete (Scaffolding phase)

---

## Week 2 (10-14 Aug 2026) - Phase 1: Data Ingestion & Upload Pipeline

### Tasks

#### Sujith Putta
- [ ] Implement POST /upload endpoint (file handling)
- [ ] Integrate PyMuPDF for PDF text extraction
- [ ] Add Tesseract OCR fallback for scanned PDFs
- [ ] Write integration tests for extraction pipeline

#### K Vikas Aneesh Reddy
- [ ] Setup Qdrant embedded instance locally
- [ ] Create collection schema (id, vector, filename, topic_tags, upload_time)
- [ ] Implement duplicate detection (cosine similarity check)
- [ ] Test vector insertion and similarity queries

#### Mokshith Karnati
- [ ] Build Next.js /upload page (drag-and-drop UI)
- [ ] Implement POST to API endpoint
- [ ] Add error handling and file validation
- [ ] Show upload progress and success/failure feedback

### Deliverables for Week 2
- [ ] Upload endpoint accepts PDF/DOCX/TXT files
- [ ] Text extraction working end-to-end
- [ ] Files stored in ./uploads directory
- [ ] Qdrant collection created and functional
- [ ] Upload UI works and communicates with backend
- [ ] Error handling for invalid files

### Status: ~30% Complete (Phase 1 halfway)

---

## Week 3 (17-22 Aug 2026) - Phase 2 & 3: Embeddings & Intent Parsing

### Tasks

#### Sujith Putta
- [ ] Implement sentence-transformers embedding generation
- [ ] Integrate with Ollama Phi-3 Mini for intent parsing
- [ ] Build intent parsing prompt and response handler
- [ ] Add confidence scoring to parsed intents

#### K Vikas Aneesh Reddy
- [ ] Upsert embeddings into Qdrant after upload
- [ ] Implement duplicate detection check before upsert
- [ ] Add metadata storage (filename, upload_time, topic_tags)
- [ ] Create GET /stats endpoint for dashboard

#### Mokshith Karnati
- [ ] Build Next.js /search page with search bar
- [ ] Build Next.js /dashboard page with stats
- [ ] Display uploaded file count and topics
- [ ] Add GET /stats integration

### Deliverables for Week 3
- [ ] Embeddings generated for uploaded documents
- [ ] Dense semantic search working in Qdrant
- [ ] Intent parsing working with Phi-3 via Ollama
- [ ] /search endpoint returns results with relevance scores
- [ ] Dashboard shows file count and statistics
- [ ] Full pipeline: Upload → Extract → Embed → Store → Search

### Status: ~40% Complete (Phases 1-3 baseline)

---

## Backend API Endpoints Summary

### Health Check
- `GET /health` - System status, all components

### Phase 1: Upload
- `POST /upload` - Upload file, triggers extraction pipeline
- `GET /files` - List uploaded files (debug)

### Phase 2: Dashboard
- `GET /stats` - Collection statistics, file count

### Phase 3: Search
- `POST /search?query=...&top_k=3` - Natural language search
  - Input: query string
  - Output: top-3 results with relevance scores and explanations

### Phase 5: Download (partial prep)
- `GET /download/{file_id}` - Download stored file

---

## Frontend Pages Summary

### Navigation
- **Navbar** - Logo, nav links, theme toggle (Light/Dark/System)

### Pages
1. **Homepage** - Welcome, quick start links
2. **Upload** (`/upload`) - Drag-and-drop file upload
3. **Search** (`/search`) - Search bar, results display
4. **Dashboard** (`/dashboard`) - File stats, memory profile

---

## Frontend Components Needed

- [ ] Button component
- [ ] Card component  
- [ ] Input component
- [ ] Badge component (file types, relevance scores)
- [ ] SearchResults component
- [ ] FileGrid component
- [ ] TopicTag component
- [ ] RelevanceScore component

---

## Environment Variables

### Backend (.env)
```
OLLAMA_BASE_URL=http://localhost:11434
QDRANT_PATH=./qdrant_storage
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=pdf,docx,txt
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Testing Checklist

### Backend Tests
- [ ] Health endpoint returns all components healthy
- [ ] File upload stores file correctly
- [ ] Text extraction works for PDF/DOCX/TXT
- [ ] Embeddings generated and stored in Qdrant
- [ ] Duplicate detection prevents similar files
- [ ] Intent parsing returns structured JSON
- [ ] Search returns results ordered by relevance

### Frontend Tests
- [ ] Navbar renders and theme toggle works
- [ ] Upload drag-and-drop works
- [ ] File validation prevents invalid types
- [ ] Search bar accepts queries
- [ ] Dashboard displays stats
- [ ] Results show relevance scores
- [ ] Dark/light/system theme switching persists

### Integration Tests
- [ ] Upload → Extract → Embed → Store → Search full pipeline
- [ ] Query parsing via Ollama returns valid intent
- [ ] Search results match query intent

---

## Key Configuration Files

### Bun Runtime (Next.js)
- package.json - Already configured
- Uses `bun run dev` and `bun run build`

### Python Runtime (FastAPI)
- requirements.txt - All dependencies listed
- venv/ - Virtual environment

### Models
- `all-MiniLM-L6-v2` - sentence-transformers for embeddings (384-dim)
- `phi:3` - Ollama quantized Phi-3 Mini for intent parsing
- `ms-marco-MiniLM` - Cross-encoder for reranking (Phase 4, Week 5)

---

## Next Steps (After Week 3)

### Week 4 (24-29 Aug) - Review-1 Preparation
- Finalize literature survey
- Complete review presentation
- Fix any bugs from Week 1-3

### Week 5 (31 Aug - 04 Sep) - Phase 4: Hybrid Retrieval & Reranking
- Implement sparse/BM25 search
- Add Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Place Raspberry Pi hardware order

### Weeks 6-9 - Hardware migration, demos, evaluation

---

## Quick Start Commands

### Backend Setup
```bash
cd intentcloud-api
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd intentcloud-web
bun install
bun run dev
```

### Dependencies Start-Up
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: FastAPI Backend
cd intentcloud-api && source venv/bin/activate && python main.py

# Terminal 3: Next.js Frontend
cd intentcloud-web && bun run dev

# Access
Frontend: http://localhost:3000
Backend: http://localhost:8000
Ollama: http://localhost:11434
```

---

## Notes

- All code includes logging for debugging
- Design system fully responsive (360px to 1920px+)
- Light/dark theme switching with system preference fallback
- Phase 4-5 placeholder functions already in code for easy Week 5 implementation
- Document created: 19 Aug 2026
- Schedule aligns exactly with PRD weekly milestones
