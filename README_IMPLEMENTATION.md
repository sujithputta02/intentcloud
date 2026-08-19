# IntentCloud - First 3 Weeks Implementation

## 🎯 Project Overview

**IntentCloud** is an intent-aware cognitive cloud memory system that allows users to upload documents and search them using natural language queries. It combines:

- **Frontend**: Next.js 16 with React 19, Tailwind CSS, built with Bun
- **Backend**: FastAPI with Python 3.11+
- **AI/ML**: 
  - Embeddings: `sentence-transformers` (all-MiniLM-L6-v2, 384-dim vectors)
  - Intent Parsing: Phi-3 Mini via Ollama (local LLM)
  - Vector Store: Qdrant (embedded mode, no server needed)
- **Architecture**: Laptop (cognitive layer) + Raspberry Pi 4B (memory layer, Phase 2+)

---

## 📦 What Has Been Built (Week 1-3 Scaffolding)

### Frontend (Next.js + Bun)
✅ **Complete Structure**
- App Router with TypeScript
- Tailwind CSS with custom design tokens
- Light/Dark/System theme switching
- 4 main pages:
  - `page.tsx` - Home page
  - `upload/page.tsx` - Upload drag-and-drop
  - `search/page.tsx` - Natural language search
  - `dashboard/page.tsx` - Statistics and memory profile
- Components:
  - `Navbar.tsx` - Navigation with theme toggle
  - `ThemeProvider.tsx` - Theme management
- Design system (`globals.css`):
  - Light theme tokens
  - Dark theme tokens
  - Responsive breakpoints (360px to 1920px+)
  - Accessibility (WCAG AA contrast, 44px touch targets)
  - Typography (Fraunces + Inter fonts)

### Backend (FastAPI)
✅ **Complete Structure**
- Main app (`main.py`) with:
  - CORS middleware for localhost:3000
  - Health check endpoint
  - Upload endpoint (POST /upload)
  - Search endpoint (POST /search)
  - Stats endpoint (GET /stats)
  - Download endpoint (GET /download/{file_id})
- Service modules:
  - `services/extraction.py` - PDF/DOCX/TXT extraction, OCR fallback
  - `services/embeddings.py` - Sentence-transformers integration
  - `services/qdrant_client.py` - Qdrant vector store management
  - `services/intent_parser.py` - Phi-3 Mini intent parsing via Ollama
  - `services/search.py` - Dense + sparse hybrid search (Phase 4)
- Configuration:
  - `.env` - Environment variables
  - `requirements.txt` - All dependencies listed

### Documentation
✅ **Complete**
- `QUICK_START.md` - Installation and startup guide
- `IMPLEMENTATION_PLAN.md` - Week-by-week breakdown
- `TEST_SYSTEM.md` - Testing procedures
- `design.md` - Frontend design system (from user)

---

## 🔧 Installation Status

### ✅ Completed
- Next.js project scaffolded with Bun
- FastAPI project structure created
- All service module files created with full implementations
- All frontend page files created
- All configuration files created

### ⏳ In Progress
- Backend dependencies installing:
  - `sentence-transformers` (with `torch`)
  - `qdrant-client`
  - Estimated time: 5-10 minutes

### ⏳ Pending
- Run `bun install` for frontend (will be quick, ~2 minutes)
- Test full system end-to-end

---

## 🚀 Quick Start (Once Dependencies Installed)

### Terminal 1: Backend
```bash
cd /Users/sujithputta/Projects/Intentcloud/intentcloud-api
source venv/bin/activate
python main.py
```
→ Runs on `http://localhost:8000`

### Terminal 2: Frontend
```bash
cd /Users/sujithputta/Projects/Intentcloud/intentcloud-web
bun install  # If not already done
bun run dev
```
→ Runs on `http://localhost:3000`

### Terminal 3: Optional - Ollama (for Phase 3 intent parsing)
```bash
ollama serve
```
→ Runs on `http://localhost:11434`

---

## 📋 Implementation Breakdown by Week

### ✅ Week 1 (03-08 Aug 2026) - Scaffolding & Verification
**Status: 100% COMPLETE**

Tasks:
- [x] Project directory structure created
- [x] Next.js app initialized (App Router, TypeScript, Tailwind, Bun)
- [x] FastAPI app scaffolded with health check
- [x] Design system implemented (light/dark themes, tokens)
- [x] 4 frontend pages built (home, upload, search, dashboard)
- [x] Navbar with theme toggle created
- [x] 5 service modules created with full code
- [x] Environment configuration files created
- [x] Documentation created (QUICK_START, IMPLEMENTATION_PLAN, TEST_SYSTEM)

Deliverable: ✅ All scaffolding complete, ready for implementation

### 🔄 Week 2 (10-14 Aug 2026) - Phase 1: Data Ingestion & Upload
**Status: CODE COMPLETE, AWAITING TESTING**

Implemented:
- [x] POST `/upload` endpoint (file handling, multipart form data)
- [x] Background task pipeline for processing
- [x] Text extraction from PDF/DOCX/TXT
- [x] OCR fallback for scanned PDFs (Tesseract integration)
- [x] File storage in `./uploads` directory
- [x] Qdrant collection schema (id, vector, metadata)
- [x] Duplicate detection via cosine similarity
- [x] Frontend upload UI with drag-and-drop

Remaining:
- [ ] **Test** upload endpoint with real files
- [ ] **Verify** text extraction working
- [ ] **Check** Qdrant collection creation

### 🔄 Week 3 (17-22 Aug 2026) - Phase 2 & 3: Embeddings & Intent Parsing
**Status: CODE COMPLETE, AWAITING TESTING**

Phase 2 (Embeddings):
- [x] sentence-transformers integration (all-MiniLM-L6-v2)
- [x] Sentence splitting and embedding generation
- [x] Embedding storage in Qdrant
- [x] GET `/stats` endpoint for dashboard stats
- [x] Dashboard page showing file count and stats

Phase 3 (Intent Parsing):
- [x] Phi-3 Mini integration via Ollama
- [x] Natural language query parsing
- [x] Intent extraction (topic, keywords, confidence)
- [x] POST `/search` endpoint with dense search
- [x] Search page with results display
- [x] Relevance scoring and explanations

Remaining:
- [ ] **Test** embeddings generation
- [ ] **Verify** Qdrant storage working
- [ ] **Test** intent parsing with Phi-3
- [ ] **Verify** search returning results

---

## 📁 File Structure

```
/Users/sujithputta/Projects/Intentcloud/
├── intentcloud-api/                    # Backend (FastAPI)
│   ├── main.py                         # Main app
│   ├── services/
│   │   ├── __init__.py
│   │   ├── extraction.py              # Text extraction
│   │   ├── embeddings.py              # Embeddings generation
│   │   ├── qdrant_client.py           # Vector store
│   │   ├── intent_parser.py           # Intent parsing
│   │   └── search.py                  # Search logic
│   ├── uploads/                        # Uploaded files (auto-created)
│   ├── qdrant_storage/                # Qdrant DB (auto-created)
│   ├── venv/                          # Virtual environment
│   ├── .env                           # Configuration
│   ├── requirements.txt               # Dependencies
│   └── .gitignore
│
├── intentcloud-web/                    # Frontend (Next.js + Bun)
│   ├── app/
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Home page
│   │   ├── globals.css                # Design tokens
│   │   ├── upload/page.tsx            # Upload page
│   │   ├── search/page.tsx            # Search page
│   │   └── dashboard/page.tsx         # Dashboard page
│   ├── components/
│   │   ├── Navbar.tsx                 # Navigation
│   │   └── ThemeProvider.tsx          # Theme management
│   ├── public/
│   ├── package.json                   # Dependencies (Bun)
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.local                     # Environment variables
│   ├── .gitignore
│   └── bun.lockb                      # Lock file
│
├── design.md                           # Design system (from user)
├── QUICK_START.md                      # Quick start guide
├── IMPLEMENTATION_PLAN.md              # Detailed schedule
├── TEST_SYSTEM.md                      # Testing guide
└── README_IMPLEMENTATION.md            # This file
```

---

## 🔌 API Endpoints

### Phase 1: Upload
```
POST /upload
Content-Type: multipart/form-data
Body: file (PDF/DOCX/TXT)

Response:
{
  "status": "received",
  "file_id": "uuid",
  "filename": "document.pdf",
  "size_bytes": 12345
}
```

### Phase 2: Dashboard
```
GET /stats

Response:
{
  "total_vectors": 500,
  "total_files": 5,
  "collection": "intentcloud_docs",
  "vector_dim": 384,
  "status": "ready"
}
```

### Phase 3: Search
```
POST /search?query=your+query&top_k=3

Response:
{
  "query": "your query",
  "parsed_intent": {
    "topic": "...",
    "keywords": [...],
    "confidence": 0.9
  },
  "results": [
    {
      "file_id": "uuid",
      "filename": "document.pdf",
      "sentence_text": "...",
      "relevance_score": 0.92,
      "explanation": "..."
    }
  ]
}
```

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "service": "IntentCloud API",
  "components": {
    "api": "running",
    "qdrant": "healthy",
    "uploads_dir": "./uploads"
  }
}
```

---

## 🌐 Frontend Pages

### Home (`/`)
- Hero section with gradient background
- Feature cards (Upload, Understand Intent, Find Instantly)
- Tech stack information
- Quick start CTA

### Upload (`/upload`)
- Drag-and-drop zone
- File validation (PDF/DOCX/TXT only)
- Progress indication
- Uploaded files list

### Search (`/search`)
- Large search input with example queries
- Result cards with relevance scores
- Match explanations
- Intent parsing display

### Dashboard (`/dashboard`)
- Greeting based on time of day
- Stats cards (Total Files, Indexed Sentences, Embedding Dimension)
- Memory profile section
- Quick action links

---

## 🎨 Design System (Per design.md)

### Light Theme Colors
- `--bg-base`: #FAF9F6 (warm off-white)
- `--text-primary`: #1C1917 (dark)
- `--accent`: #B45F3C (muted terracotta)
- `--success`: #3F7D58 (green)

### Dark Theme Colors
- `--bg-base`: #15130F (dark)
- `--text-primary`: #F2EFE9 (light)
- `--accent`: #E08556 (lighter terracotta)
- `--success`: #5FAE7A (lighter green)

### Responsive Breakpoints
- Mobile: 360-639px
- Tablet: 640-1023px
- Desktop: 1024-1279px
- Ultrawide: 1280px+

### Typography
- Headings: Fraunces (serif)
- Body: Inter (sans-serif)
- Never mix third typeface

---

## 🧪 Testing Checklist

### ✅ Phase 1: Upload
- [ ] Health endpoint returns "healthy"
- [ ] POST /upload accepts PDF/DOCX/TXT
- [ ] Files stored in ./uploads/
- [ ] Text extraction works
- [ ] Errors on invalid file types
- [ ] Upload progress shown in UI

### ✅ Phase 2: Embeddings
- [ ] Embeddings generated (384-dim)
- [ ] Sentences extracted and embedded
- [ ] Vectors stored in Qdrant
- [ ] GET /stats returns file count > 0
- [ ] Dashboard shows updated stats
- [ ] Duplicate detection prevents duplicates

### ✅ Phase 3: Intent & Search
- [ ] Phi-3 Mini intent parsing works
- [ ] POST /search returns results
- [ ] Results have relevance scores
- [ ] Search page displays results
- [ ] Dark/light theme switching works
- [ ] All pages responsive (360px-1920px)

---

## 📊 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Next.js Frontend | ✅ Ready | Bun ready, dependencies pending |
| FastAPI Backend | ✅ Ready | Structure complete, dependencies installing |
| Service Modules | ✅ Code Complete | extraction, embeddings, qdrant, intent, search |
| Design System | ✅ Complete | Light/dark themes, responsive, WCAG AA |
| Endpoints | ✅ Structured | /health, /upload, /search, /stats, /download |
| Documentation | ✅ Complete | QUICK_START, PLAN, TESTING guides |
| **Dependencies** | ⏳ Installing | sentence-transformers, qdrant-client (~5-10 min) |
| **Testing** | ⏹️ Pending | Ready to start once deps installed |

---

## 🎯 Next Steps

### Immediate (Once dependencies installed, ~10 minutes)
1. Run backend: `python main.py` → verify /health endpoint
2. Run frontend: `bun run dev` → verify home page loads
3. Test upload: drag a test file → verify in /uploads
4. Check stats: GET /stats → verify file count increases
5. Test search: enter query → verify results displayed

### Week 2 Focus (if needed)
- Fix any extraction issues
- Optimize embedding generation
- Test with real documents

### Week 3 Focus (if needed)
- Fine-tune intent parsing
- Improve search ranking
- Polish UI based on feedback

### Weeks 4-9 (Per PRD)
- Phase 4: Hybrid retrieval + RRF + reranking
- Review presentations
- Raspberry Pi hardware setup
- Evaluation and benchmarking

---

## 📚 Documentation Files

1. **QUICK_START.md** - Installation and first run
2. **IMPLEMENTATION_PLAN.md** - Week-by-week detailed schedule
3. **TEST_SYSTEM.md** - Testing procedures and verification
4. **design.md** - Frontend design specifications (from user)
5. **README_IMPLEMENTATION.md** - This file

---

## ✅ Completion Summary

**Week 1 Scaffolding: 100% ✓**
- All directories created
- All files with full implementations
- All configurations in place
- Ready for execution

**Week 2 Implementation Code: 100% ✓**
- Upload endpoint implemented
- Extraction service implemented
- Qdrant integration implemented
- All dependencies specified

**Week 3 Implementation Code: 100% ✓**
- Embeddings service implemented
- Intent parsing service implemented
- Search service implemented
- Dashboard/stats endpoints implemented

**Testing & Verification: ⏳ Awaiting Dependency Installation**

---

## 🚀 Ready to Launch!

Once `pip install` completes (~5-10 minutes more), the system is ready to test end-to-end.

**All code is in place. All configurations are set. All documentation is complete.**

Next: Install dependencies → Run tests → Iterate based on results.
