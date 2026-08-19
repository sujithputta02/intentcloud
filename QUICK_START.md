# IntentCloud - Quick Start Guide

## 📋 Prerequisites

- **Python 3.11+** (for backend)
- **Bun 1.3+** (for frontend with Next.js)
- **Ollama** (for local LLM inference)
- **Git**

## 🚀 Installation & Startup

### Step 1: Install Ollama & Download Phi-3 Mini

```bash
# Install Ollama from https://ollama.ai
# Then download Phi-3 Mini model

ollama pull phi3:mini

# Start Ollama server (runs on localhost:11434)
ollama serve
```

**Terminal 1: Leave Ollama running**

---

### Step 2: Start FastAPI Backend

```bash
cd intentcloud-api

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies (this may take 2-3 minutes)
pip install -r requirements.txt

# Start the backend server
python main.py
```

**Terminal 2: Backend running on http://localhost:8000**

Check health: http://localhost:8000/health

---

### Step 3: Start Next.js Frontend with Bun

```bash
cd intentcloud-web

# Install dependencies with Bun
bun install

# Start development server
bun run dev
```

**Terminal 3: Frontend running on http://localhost:3000**

---

## ✅ Verification Checklist

### 1. Health Check
```bash
# Should return 200 with all components healthy
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "IntentCloud API",
  "components": {
    "api": "running",
    "qdrant": "healthy",
    "uploads_dir": "./uploads",
    "phase": "1-3 (Data Ingestion, Embeddings, Intent Parsing)"
  }
}
```

### 2. Frontend Accessibility
Open http://localhost:3000 in your browser

You should see:
- IntentCloud logo and navigation
- Hero section "Your Cognitive Memory for Documents"
- Links to Upload, Search, and Dashboard

### 3. Theme Toggle
Click the Light/Dark/System buttons in the top-right corner
- Light/Dark modes should switch immediately
- System mode should follow OS preference

### 4. Navigate to Upload Page
- Go to http://localhost:3000/upload
- Should see drag-and-drop upload zone
- Try uploading a test PDF/DOCX/TXT file (< 50 MB)

### 5. Monitor Backend Logs
In Terminal 2, you should see:
```
[Pipeline] Starting for file_id=..., filename=test.pdf
[Step 1] Extracting text...
[Step 1] Extracted 1234 chars
[Step 2] Generating embeddings...
[Qdrant] Upserting file_id=...
[Pipeline] Complete for file_id=...
```

### 6. Test Dashboard
- Go to http://localhost:3000/dashboard
- Should see stats: Total Files, Indexed Sentences, Embedding Dimension
- After uploading a file, stats should update

### 7. Test Search
- Go to http://localhost:3000/search
- Enter a natural language query, e.g., "Find documents about Kafka"
- See results with relevance scores and explanations

---

## 📁 Project Structure

```
intentcloud/
├── intentcloud-api/           # FastAPI Backend
│   ├── main.py               # Main application
│   ├── services/             # Service modules
│   │   ├── extraction.py     # Text extraction
│   │   ├── embeddings.py     # Embeddings generation
│   │   ├── qdrant_client.py  # Vector store
│   │   ├── intent_parser.py  # Intent parsing
│   │   └── search.py         # Search logic
│   ├── uploads/              # Uploaded files (created automatically)
│   ├── qdrant_storage/       # Qdrant DB (created automatically)
│   ├── requirements.txt      # Python dependencies
│   ├── .env                  # Configuration
│   └── venv/                 # Virtual environment
│
├── intentcloud-web/          # Next.js Frontend (Bun)
│   ├── app/
│   │   ├── page.tsx          # Home page
│   │   ├── layout.tsx        # Root layout
│   │   ├── globals.css       # Design tokens
│   │   ├── upload/           # Upload page
│   │   ├── search/           # Search page
│   │   └── dashboard/        # Dashboard page
│   ├── components/
│   │   ├── Navbar.tsx        # Navigation
│   │   └── ThemeProvider.tsx # Theme management
│   ├── package.json          # Dependencies (Bun)
│   ├── tsconfig.json
│   └── .env.local            # Environment variables
│
├── QUICK_START.md            # This file
├── IMPLEMENTATION_PLAN.md    # Detailed implementation schedule
└── README.md                 # Project overview
```

---

## 🛠️ Troubleshooting

### Backend won't start
```
Error: Ollama not available
```
**Solution:** Make sure Ollama server is running. Start with `ollama serve` in another terminal.

```
Error: ModuleNotFoundError: No module named 'qdrant_client'
```
**Solution:** Activate venv and reinstall: `pip install -r requirements.txt`

### Frontend won't start
```
Error: Unknown scheme "http"
```
**Solution:** Backend must be running. Start FastAPI in another terminal.

```
Error: Cannot find module
```
**Solution:** Run `bun install` in the intentcloud-web directory.

### Upload fails
```
Upload failed: 413 Payload Too Large
```
**Solution:** File is too large. Maximum is 50 MB. See MAX_FILE_SIZE_MB in .env

```
Upload failed: 400 Invalid file type
```
**Solution:** Only PDF, DOCX, and TXT files are allowed.

### Search returns no results
```
No results found. Try refining your query.
```
**Likely causes:**
1. No files have been uploaded yet
2. Ollama/Phi-3 is not responding
3. Query is too specific or different from file content

Try uploading a test file first, then searching with a general query.

### Theme toggle not working
**Solution:** Refresh the page. Theme preference is stored in localStorage.

---

## 📊 API Endpoints

### Health Check
```
GET /health
```
Returns system status.

### Upload File
```
POST /upload
Content-Type: multipart/form-data
- file: (binary)

Response:
{
  "status": "received",
  "file_id": "uuid",
  "filename": "document.pdf",
  "size_bytes": 12345
}
```

### Search Documents
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
  ],
  "count": 1
}
```

### Get Statistics
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

### Download File
```
GET /download/{file_id}

Returns: File binary content
```

---

## 🧪 Testing the Full Pipeline

### Test Scenario: Upload & Search

1. **Upload a test document**
   ```bash
   curl -X POST -F "file=@test.pdf" http://localhost:8000/upload
   ```

2. **Wait for processing** (watch backend logs)
   - Extraction: 2-5 seconds
   - Embeddings: 5-10 seconds
   - Total: ~15 seconds per file

3. **Check stats**
   ```bash
   curl http://localhost:8000/stats
   ```
   Should show: `"total_files": 1`

4. **Search**
   ```bash
   curl "http://localhost:8000/search?query=your+search+query&top_k=3"
   ```

5. **Verify results**
   - relevance_score should be > 0.3
   - explanation should match query intent

---

## 🎯 Week 1-3 Milestones (as per PRD)

### ✅ Week 1 (03-08 Aug 2026) - Scaffolding
- [x] Next.js + Tailwind setup
- [x] FastAPI with CORS
- [x] Design system (light/dark theme)
- [x] Navbar with theme toggle
- [ ] Verify all components running

### 🔄 Week 2 (10-14 Aug 2026) - Phase 1: Upload
- [ ] File upload endpoint
- [ ] Text extraction (PDF/DOCX/TXT)
- [ ] Qdrant collection setup
- [ ] Upload UI functional
- [ ] End-to-end upload working

### 🔄 Week 3 (17-22 Aug 2026) - Phase 2 & 3: Embeddings & Intent
- [ ] Embeddings generation
- [ ] Intent parsing with Phi-3
- [ ] Dense search in Qdrant
- [ ] Search page functional
- [ ] Dashboard showing stats
- [ ] Full pipeline: Upload → Extract → Embed → Store → Search

---

## 📚 Documentation

- **PRD**: See `IntentCloud_Final_PRD_v3 (1).pdf`
- **Design System**: See `design.md`
- **Implementation Plan**: See `IMPLEMENTATION_PLAN.md`
- **This File**: Quick start and troubleshooting

---

## 🤝 Team Roles (per PRD)

| Member | Focus | Week 1 | Week 2 | Week 3 |
|--------|-------|--------|--------|--------|
| **Sujith Putta** | Backend: Intent parsing, embeddings, retrieval | Setup Ollama | POST /upload, extraction | Phi-3 intent parsing |
| **K Vikas** | Backend: Qdrant, Pi setup, memory layer | Setup Qdrant | Duplicate detection | Stats endpoint |
| **Mokshith** | Frontend: UI, dashboard, deployment | Next.js setup | Upload page | Search & Dashboard pages |

---

## 🔮 Next Steps (After Week 3)

### Week 4: Review-1 Preparation
- Final literature survey
- Review presentation deck
- Bug fixes and polish

### Week 5: Phase 4 - Hybrid Retrieval & Reranking
- Sparse/BM25 keyword search
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Place Raspberry Pi hardware order

### Weeks 6-9: Hardware Migration & Evaluation
- Flash and setup Raspberry Pi
- Migrate system to Pi
- Cloudflare Tunnel setup
- Evaluation and testing
- Final report

---

## ❓ Questions?

1. **Can't start Ollama?** → Download from https://ollama.ai
2. **Embeddings too slow?** → First run downloads model (~200 MB). Subsequent runs are faster.
3. **Qdrant storage taking space?** → Embedded Qdrant stores vectors locally. Delete `qdrant_storage/` to reset.
4. **Files not uploading?** → Check backend logs and ensure API is running.

---

**Good luck! 🚀**

Created: 19 August 2026 | Status: Week 1 Scaffolding Complete
