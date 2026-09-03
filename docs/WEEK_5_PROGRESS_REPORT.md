# B.Tech Final Year Capstone Project Phase 1 — Weekly Progress Report

## Header Information

- **Academic Year / Semester:** 2026–2027 / 7th Semester (Aug–Dec 2026)
- **Project Title:** IntentCloud: Intent-Aware Cognitive Cloud Memory System
- **Guide:** Dr. Ramandeep Kaur, Department of Computer Science & Technology, School of Engineering, Dayananda Sagar University
- **Week Number:** Week 5
- **Reporting Window:** 31 August 2026 – 04 September 2026
- **Team Members:**
  1. **Sujith Putta** (USN: `ENG23CT0058`) — *Cognitive Layer & Hybrid Reranking*
  2. **K Vikas Aneesh Reddy** (USN: `ENG23CT0052`) — *Memory Layer, Qdrant & Hardware Setup*
  3. **Mokshith Karnati** (USN: `ENG23CT0053`) — *Frontend UI, Tunnel Deployment & Benchmarking*

---

## 1. Work Carried Out by the Team During the Week

- Designed and implemented **Phase 4 (Hybrid Retrieval & Cross-Encoder Reranking)** on local development environments with zero cloud API dependencies.
- Integrated dual-stream candidate retrieval in Qdrant: dense semantic vectors (`all-MiniLM-L6-v2`, 384-d) and universal deterministic feature-hashed sparse keyword representations (1,000,003-d).
- Implemented **Reciprocal Rank Fusion (RRF)** with smoothing parameter $k=60$ ($score_{RRF}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + rank_m(d)}$) to merge dense and sparse candidate rankings ahead of reranking (PRD §5.4).
- Integrated local cross-encoder model `cross-encoder/ms-marco-MiniLM-L-6-v2` with hardware acceleration auto-detection (Apple Silicon MPS / NVIDIA CUDA / CPU fallback) to perform final high-precision top-3 reordering.
- Implemented explainable **Matched-Snippet Highlighting**: computing sentence-level relevance to extract and quote the exact passage within each document triggering the retrieval.
- Implemented **Confidence Threshold Fallback**: returns `"No confident match found"` when top score falls below the 0.35 normalized threshold, preventing false-positive hallucinated answers on out-of-domain queries.
- Updated Next.js `/search` UI to display top-3 ranked cards, search mode toggles (Hybrid, Dense, Sparse, RRF), golden citation quote blocks, and direct file download actions.
- Formulated an expanded 35-query ground-truth benchmark evaluation set and developed automated evaluation scripts (`scripts/week5_evaluation.py`, `RUN_WEEK5_EVALUATION.sh`).
- Finalized the Raspberry Pi 4B (8GB RAM) procurement order details per PRD §10.3 ahead of Week 6 hardware unboxing and memory-layer migration.

---

## 2. Individual Contributions from Students

### Sujith Putta (`ENG23CT0058`)
- Implemented the sparse/BM25 feature-hashing token representation and the **Reciprocal Rank Fusion (RRF)** scoring algorithm in `services/search.py`.
- Developed the sentence-level matched-snippet extraction and explanation generator in `services/reranker.py` providing human-interpretable "Why this matched" rationales.
- Tuned the confidence thresholding logic (0.35 threshold) to gracefully reject negative/out-of-domain queries.
- Authored the Week 5 implementation documentation and technical specifications for the Phase-1 methodology section.

### K Vikas Aneesh Reddy (`ENG23CT0052`)
- Wired Qdrant's vector store queries to support dual dense and sparse candidate streams for candidate pooling ($N=20$).
- Built the `RerankerManager` singleton with auto-detection for Apple Silicon Metal (MPS), CUDA, and CPU fallback.
- Added `/health` and `/stats` endpoint enhancements exposing sparse dimensions, reranker device status, and RRF parameters.
- Finalized the Raspberry Pi 4B (8GB) hardware order and USB storage procurement plan (PRD §10.3) for delivery by Week 6.

### Mokshith Karnati (`ENG23CT0053`)
- Upgraded the Next.js `/search` page (`app/search/page.tsx`) with search mode selection pills, top-3 ranked card displays, matched citation quotes, and download links.
- Updated the Dashboard (`app/dashboard/page.tsx`) to display Phase 4 hybrid vector metrics and architecture status.
- Designed and authored the 35-query evaluation ground-truth dataset (`test_corpus/ground_truth.json`) with positive and negative test cases.
- Co-developed the automated benchmark harness (`scripts/week5_evaluation.py`) measuring Top-1/Top-3 accuracy and latency.

---

## 3. Work Planned for the Following Week (Week 6: 07–12 Sep 2026)

- **Review-2 Demo Preparation**: Deliver the Review-2 presentation demonstrating $\ge 25\%$ working implementation (Phase 1–4 running live on hybrid retrieval).
- **Research Paper Submission**: Finalize and submit the IEEE conference/journal contribution (due 12 September 2026).
- **Raspberry Pi 4B Setup**: Flash Raspberry Pi OS (64-bit Bookworm), complete headless SSH configuration, and setup static hostname.
- **Memory Layer Migration**: Install Python, FastAPI, and Qdrant on the Pi and migrate vector index and file storage from laptop to the Pi over the local network (LAN).
- **UI Verification on Edge Node**: Verify statically exported Next.js UI served from the Pi.

---

## 4. Major Bottlenecks / Challenges Resolved

- *Cross-Encoder Candidate Latency*: Scoring large candidate sets through Cross-Encoder on CPU can introduce latency; resolved by capping candidate pooling to top-20 fused items and leveraging Apple Silicon MPS / CUDA acceleration, achieving sub-second query latency (~400–600ms).
- *False-Positive Top-3 Matches*: Traditional dense vector search always returns the top-3 closest vectors even for completely unrelated queries; resolved by implementing a calibrated confidence threshold (0.35) returning `"No confident match found"`.

---

## 5. Percentage Work Completed

- **Current Cumulative Progress:** **48%**
- **Stage Alignment:** Stage-2 (Methodology & Partial Implementation) active — satisfies Review-2 $\ge 25\%$ requirement with substantial margin.
