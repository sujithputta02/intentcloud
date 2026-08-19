# IntentCloud - System Testing Guide

## Test the Full 3-Week Implementation

### Prerequisites
- Bun installed ✓
- FastAPI dependencies installing
- Backend structure ready
- Frontend structure ready

### Test 1: Verify Bun Installation
```bash
bun --version
```

Should show version number (e.g., 1.3.14)

### Test 2: Verify Backend Structure
```bash
ls -la /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/
```

Should show:
- extraction.py ✓
- embeddings.py ✓
- qdrant_client.py ✓
- intent_parser.py ✓
- search.py ✓

### Test 3: Start Backend (once dependencies installed)
```bash
cd /Users/sujithputta/Projects/Intentcloud/intentcloud-api
source venv/bin/activate
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
[Pipeline] Startup complete
✓ Qdrant manager initialized
```

### Test 4: Health Check
```bash
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

### Test 5: Install Frontend Dependencies (with Bun)
```bash
cd /Users/sujithputta/Projects/Intentcloud/intentcloud-web
bun install
```

### Test 6: Start Frontend
```bash
bun run dev
```

Expected output:
```
  ▲ Next.js 16.3.1
  ✓ Ready in 3.2s
  ○ Listening on http://localhost:3000
```

### Test 7: Test Upload (once everything running)
```bash
# Create a test file
echo "This is a test document about machine learning and neural networks." > /tmp/test.txt

# Upload it
curl -X POST -F "file=@/tmp/test.txt" http://localhost:8000/upload
```

Expected response:
```json
{
  "status": "received",
  "file_id": "uuid-here",
  "filename": "test.txt",
  "size_bytes": 67,
  "message": "File received. Processing in background..."
}
```

### Test 8: Wait for Processing
Watch backend logs for:
```
[Pipeline] Starting for file_id=...
[Step 1] Extracting text...
[Step 1] Extracted 67 chars
[Step 2] Generating embeddings...
[Step 2] Generated 1 embeddings
[Step 3] Storing in Qdrant...
[Pipeline] Complete for file_id=...
```

### Test 9: Check Stats
```bash
curl http://localhost:8000/stats
```

Expected response:
```json
{
  "total_vectors": 1,
  "total_files": 1,
  "collection": "intentcloud_docs",
  "vector_dim": 384,
  "status": "ready"
}
```

### Test 10: Test Search
```bash
curl "http://localhost:8000/search?query=machine%20learning&top_k=3"
```

Expected response:
```json
{
  "query": "machine learning",
  "parsed_intent": {
    "topic": "machine learning",
    "keywords": ["machine", "learning"],
    "confidence": 0.8
  },
  "results": [
    {
      "file_id": "uuid",
      "filename": "test.txt",
      "sentence_text": "This is a test document about machine learning...",
      "relevance_score": 0.87,
      "rank": 1,
      "explanation": "Strong semantic match for 'machine learning'"
    }
  ],
  "count": 1
}
```

### Test 11: Frontend Navigation
1. Open http://localhost:3000
2. Should see home page with "Your Cognitive Memory for Documents"
3. Click "Upload Files" → should go to /upload page
4. Click "Start Searching" → should go to /search page
5. Click "Dashboard" in navbar → should go to /dashboard

### Test 12: Theme Switching
1. Click "Light" button in top-right → page becomes light
2. Click "Dark" button → page becomes dark
3. Click "System" button → follows OS preference
4. Refresh page → theme persists (from localStorage)

### Test 13: Upload via UI
1. Go to http://localhost:3000/upload
2. Drag a test file or click "Browse Files"
3. File should upload and show in the list
4. Should see success message

### Test 14: Dashboard Stats
1. Go to http://localhost:3000/dashboard
2. Should see "Good [morning/afternoon/evening]"
3. Should show file count and indexed sentences
4. Stats should update if new files uploaded

### Test 15: Search via UI
1. Go to http://localhost:3000/search
2. Enter query (e.g., "Find documents about machine learning")
3. Should show results with relevance scores
4. Each result should have explanation text

---

## Status by Week

### ✅ Week 1: Scaffolding Complete
- [x] Project structure
- [x] Next.js setup (Bun)
- [x] FastAPI setup
- [x] Design system
- [x] All pages (home, upload, search, dashboard)
- [x] Service modules (extraction, embeddings, qdrant, intent, search)

### 🔄 Week 2: Phase 1 - Upload Pipeline
- [x] Endpoint structure
- [x] File handling code
- [x] Text extraction code
- [ ] **TO TEST**: Full upload flow
- [ ] **TO TEST**: Extraction working
- [ ] **TO TEST**: File storage working

### 🔄 Week 3: Phase 2 & 3 - Embeddings & Intent
- [x] Embeddings module code
- [x] Intent parsing module code
- [x] Search module code
- [ ] **TO TEST**: Embeddings generating
- [ ] **TO TEST**: Qdrant storage working
- [ ] **TO TEST**: Intent parsing working
- [ ] **TO TEST**: Search returning results

---

## Dependency Installation Status

### Backend (in progress)
```
✓ fastapi
✓ uvicorn
✓ python-multipart
✓ pymupdf
✓ python-docx
✓ requests
⏳ sentence-transformers (installing...)
⏳ qdrant-client (installing...)
⏳ torch (installing with sentence-transformers)
```

### Frontend
```
⏳ Next.js dependencies (will install with bun install)
```

---

## Once Everything is Running

To test the **complete 3-week pipeline**:

```bash
# Terminal 1: Backend
cd intentcloud-api
source venv/bin/activate
python main.py

# Terminal 2: Frontend
cd intentcloud-web
bun run dev

# Terminal 3: Test upload
curl -X POST -F "file=@testfile.txt" http://localhost:8000/upload

# Then visit http://localhost:3000/dashboard to see stats
# And http://localhost:3000/search to search for your content
```

---

## Common Issues During Testing

### Backend won't start
- Check if dependencies installed: `pip list | grep fastapi`
- Check Qdrant storage exists: `ls -la qdrant_storage/`

### Frontend won't build
- Check Bun is in PATH: `which bun`
- Clear cache: `rm -rf node_modules .next && bun install`

### Search returns no results
- Check files uploaded: `curl http://localhost:8000/stats`
- Check backend logs for extraction errors
- Ensure Ollama/Phi-3 running (if intent parsing needed)

### Uploads fail with 400
- Check file type: only PDF, DOCX, TXT allowed
- Check file size: max 50 MB
- Check CORS enabled: backend should list localhost:3000

---

## Next: Testing Steps

After both installations complete, run these tests in order to verify Week 1-3 implementation.
