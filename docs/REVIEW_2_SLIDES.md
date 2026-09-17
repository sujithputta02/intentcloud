# IntentCloud — Review-2 Slide Content (5 Slides)
**Continue from Review-0 & Review-1 deck · No title slide · Date: 12 September 2026**

---

## Slide 1 — Methodology: Problem Approach & Design
*Rubric: Problem approach clearly defined, aligned with objectives*

- IntentCloud helps users find personal documents using **natural language intent**, not exact filenames or folder paths.
- Core problem: keyword search fails on paraphrased queries; cloud RAG tools raise **privacy and cost** concerns.
- **Four-phase local pipeline:** Ingestion → Dual Embedding → Intent Parsing → Hybrid Retrieval & Reranking.
- **Two-node architecture:** Laptop runs AI processing; **Raspberry Pi 3B** stores files and vector index (edge node).
- Design goals: privacy-preserving, self-hosted, returns the **original file** (not a generated summary).

**[ADD DIAGRAM: Reuse System Architecture diagram from Review-0/1 (Figure 1). Update label from Pi 4B to Pi 3B if shown on slide.]**

---

## Slide 2 — Methodology: Implementation Workflow
*Rubric: Complete workflow with proper sequence, tools, and techniques*

- **Phase 1 — Upload:** User uploads PDF / DOCX / TXT → text extracted (PyMuPDF, python-docx) → Tesseract OCR if scanned → duplicate check (cosine ≥ 0.95).
- **Phase 2 — Index:** Text chunked → **384-d dense** embeddings + **sparse feature-hash** vectors → stored in **Qdrant**.
- **Phase 3 — Query:** Natural-language query parsed by **Ollama (Phi-3 Mini)** into topic + keywords → query expanded for retrieval.
- **Phase 4 — Retrieve:** Dense + sparse search in parallel → **Reciprocal Rank Fusion (k = 60)** → **cross-encoder rerank** → top-3 results with matched sentence highlight.
- **Safety:** If top cross-encoder score < τ = 0.40, system sets **“No confident match found”** and returns **zero result cards** (strict abstention — no false-positive files shown).

**[ADD DIAGRAM: Reuse Workflow diagram from Review-0/1 (Figure 2), or add updated flow: Upload → Embed → Search → RRF → Rerank → Result.]**

---

## Slide 3 — Methodology: Technical Justification & Feasibility
*Rubric: Tools and techniques well justified; approach is practically feasible*

- **Qdrant (not FAISS):** stores dense + sparse vectors with metadata; supports hybrid search; runs embedded on Pi.
- **RRF (k = 60):** merges dense and sparse rankings without mixing incompatible score scales.
- **Cross-encoder (ms-marco-MiniLM-L-6-v2):** improves ranking precision after candidate fusion.
- **Why local AI:** Phi-3 Mini + sentence-transformers run offline — zero third-party API calls.
- **Feasibility:** Pipeline tested on team laptops (MPS / CUDA / CPU); **Pi 3B board, power supply, and microSD procured**; heatsink and cooling fan to be ordered in Week 7.

---

## Slide 4 — Progress Status & Partial Implementation
*University requirement: ≥ 25% implementation · Rubric: consistent progress demonstrated*

- **Review-2 requirement:** minimum **25%** working implementation.
- **Current cumulative progress: 54%** (PRD Week 6 target: 58%; Pi migration planned Week 7).
- **Implementation status:**
  - Phase 1 — Ingestion & OCR: **Complete**
  - Phase 2 — Embeddings & Qdrant indexing: **Complete**
  - Phase 3 — Intent parsing & search API: **Complete**
  - Phase 4 — Hybrid + RRF + cross-encoder rerank: **Complete**
  - Phase 5 — Pi deployment & Cloudflare Tunnel: **In progress**
- **Benchmark (42 queries, Week 6 re-run):** Hybrid **87.5% Top-1** · **100% Top-3** · **0.932 MRR** (PRD target ≥85% Top-1: **passed**).
- **Out-of-domain controls (10 queries):** all 10 correctly rejected — `is_confident_match=false` **and** empty results at τ = 0.40 (100% rejection rate).
- **Week 6 fixes completed:** expanded negative test set from 3 → 10; strict abstention now suppresses result cards (not just a warning banner).
- **Live demo today:** upload → hybrid search → citation snippet → negative-query abstention demo (no false-positive cards).
- **Guide meetings:** weekly reports submitted (Weeks 1–6); guide feedback applied on hybrid retrieval and paper drafting.

---

## Slide 5 — Research Paper Draft (IEEE Format)
*Rubric: Well-structured draft with required sections in prescribed/IEEE format*

- **Paper title:** *Intent-Aware Hybrid Document Retrieval with Reciprocal Rank Fusion and Cross-Encoder Reranking*
- **Format:** IEEE conference template (IEEEtran LaTeX + plain-text version).
- **Sections included:**
  - Title · Abstract · Introduction · **Literature Review** · **Methodology** · Experimental Setup · **Results** · Conclusion · References
- **Literature gap addressed:** cloud-dependent RAG, dense-only vocabulary mismatch, false positives on irrelevant queries.
- **Reported results:** 87.5% Top-1 · 0.932 MRR · +21.9 pts over dense-only · 10/10 negative controls rejected with empty results.
- **Evaluation scope:** 42-query benchmark (32 positive + 10 out-of-domain negatives); corpus expansion and Pi deployment planned Week 7+.
- **Status:** draft finalized and submitted to guide for Review-2 feedback.
