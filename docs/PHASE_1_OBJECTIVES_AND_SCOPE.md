# IntentCloud: Phase-1 Scope, Objectives & Implementation Boundaries

| Attribute | Details |
|---|---|
| **Academic Phase** | Capstone Phase-1 (7th Semester, Aug–Dec 2026) |
| **Current Stage** | Week 8 (21/09/2026 to 26/09/2026) |
| **Review-3 Date** | Rescheduled to October 10, 2026 (post-mid exams) |
| **Phase-1 Completion Target** | 50% to 65% (Satisfies Review-3 & Phase-1 Final without over-building Phase-2) |

---

## 1. Why Phase-1 Must NOT Complete the Entire Project

In the B.Tech final-year capstone structure:
- **Phase-1 (7th Sem):** Evaluates problem formulation, literature survey, core system architecture, initial implementation ($\ge 50\%$), paper submission, and preliminary hardware staging.
- **Phase-2 (8th Sem):** Requires substantial additional technical complexity: advanced machine learning models, statistical significance testing, deep edge profiling (energy/thermals), final thesis report, and external examiner viva.

If all 6 objectives were 100% completed in Phase-1, you would have zero novelty and zero technical milestones remaining for your 8th-semester reviews. Therefore, each of the guide's 6 modified objectives is partitioned into a **Phase-1 Slice** and a **Phase-2 Slice**.

---

## 2. Objective-by-Objective Scope Partition (Phase 1 vs. Phase 2)

### Objective 1: Hybrid Retrieval Pipeline vs. Baselines
> *To design and implement a privacy-preserving hybrid document retrieval pipeline that combines local query/intent processing, dense semantic embeddings, and sparse keyword retrieval using Reciprocal Rank Fusion (RRF) and cross-encoder reranking, and to evaluate its retrieval performance against keyword-only and dense-only baselines on a corpus of at least 150 mixed-format PDF, DOCX, and TXT documents.*

- **Phase-1 Implementation (Done / 67% Milestone):**
  - Dual-stream embedding (384-d dense `all-MiniLM-L6-v2` + 1M-d feature-hashed sparse token hashes).
  - Reciprocal Rank Fusion ($k=60$) in embedded Qdrant.
  - Cross-encoder precision reranker (`ms-marco-MiniLM-L-6-v2`) with sentence-level citation snippet extraction.
  - Benchmark evaluation on 42-query suite showing Mode C (87.5% Top-1, 0.932 MRR) outperforming Mode A (38.7%) and Mode B (65.6%).
  - Corpus generator script (`scripts/expand_corpus_150.py`) prepared to populate 150+ mixed files across 10 domains.
- **Phase-2 Extension (8th Sem):**
  - Run full 150-document evaluation benchmark with graded relevance annotations (0/1/2) and Wilcoxon signed-rank / paired t-test statistical significance testing.

---

### Objective 2: Fully Local, Portable Document Architecture
> *To develop a fully local document processing and retrieval architecture that performs document ingestion, text extraction, embedding generation, query processing, retrieval, and reranking on consumer-grade hardware without relying on third-party LLM APIs, while supporting portable execution across commonly available CPU and GPU environments.*

- **Phase-1 Implementation (Done / 100% of Phase 1):**
  - Multi-format text extraction (PDF via PyMuPDF, DOCX via python-docx, TXT directly) with local Tesseract OCR fallback.
  - Ingestion, embedding, search, and reranking operate 100% on local hardware with zero external API calls.
  - Auto-detection runtime support for Apple Silicon MPS, NVIDIA CUDA, and multi-threaded CPU fallback.
- **Phase-2 Extension (8th Sem):**
  - Containerization via Docker ARM64 and reproducible Nix/Oci packages for portable edge deployment.

---

### Objective 3: Query-Aware Retrieval & Document Version Lineage
> *To implement a query-aware retrieval mechanism that considers query characteristics and document metadata, including document recency and version information, to improve retrieval of relevant, original, historical, and latest document versions, and to evaluate its effectiveness using predefined retrieval-quality and response-latency metrics.*

- **Phase-1 Implementation (Done in Week 8):**
  - Document metadata ingestion now extracts and stores `version_number` (auto-parsed from filename), `is_latest` boolean, `parent_id` linkage, and timestamps (`created_at`, `modified_at`).
  - Search orchestrator (`services/search.py`) applies query-aware metadata conditioning: boosts `is_latest` candidates on recency queries ("recent", "latest") and earlier versions on historical queries ("original", "draft", "v1").
- **Phase-2 Extension (8th Sem):**
  - Full temporal graph database modeling with parent-child version tree traversal and continuous exponential decay parameter tuning.

---

### Objective 4: Self-Hosted Service & Original Document Delivery
> *To develop and evaluate a self-hosted document retrieval service that supports document upload, indexing, retrieval, and secure file delivery, with the objective of returning the original retrieved document within a predefined response-time target under realistic user workloads.*

- **Phase-1 Implementation (Done):**
  - Self-hosted FastAPI backend + Next.js macOS Finder web interface.
  - Authoritative original file delivery via `/download/{file_id}` and Quick Look file previews.
  - Cloudflare Zero-Trust Tunnel configuration (`intentcloud-api/scripts/setup_pi.sh`) for secure HTTPS file delivery without open router ports.
  - Sub-3-second average latency on workstation hardware (<15s target).
- **Phase-2 Extension (8th Sem):**
  - Multi-user concurrency stress testing and client-side bandwidth throttling measurements on edge hardware.

---

### Objective 5: Adaptive Reranking & Privacy-Preserving Abstention
> *To investigate adaptive reranking and confidence-based abstention using locally captured interaction signals, and experimentally determine whether these mechanisms improve retrieval relevance and reduce unnecessary reranking computation without transmitting user or document data to external services.*

- **Phase-1 Implementation (Done in Week 8):**
  - Calibrated sigmoid confidence gating ($\tau = 0.40$) on cross-encoder logits achieving 100% true-negative rejection on out-of-domain queries (zero hallucination).
  - Adaptive fast-path routing in `services/search.py`: selectively bypasses cross-encoder when RRF candidate separation is decisive ($\Delta \ge 0.008$), saving ~1300 ms of compute.
  - Offline local feedback endpoint (`POST /feedback`) capturing clicks, downloads, and dwell times without external network telemetry.
- **Phase-2 Extension (8th Sem):**
  - Train an embedded Learning-to-Rank (LTR) model (e.g. LightGBM / RankNet) using the collected interaction feedback to dynamically predict gating weights.

---

### Objective 6: Edge Optimization & Characterization on Raspberry Pi
> *To optimize and experimentally characterize the complete IntentCloud pipeline for resource-constrained edge deployment by evaluating model optimization and quantization strategies on Raspberry Pi-class hardware and measuring retrieval quality, latency, memory consumption, thermal behaviour, throughput, and energy consumption to establish the quality–latency–energy trade-off of local document retrieval.*

- **Phase-1 Implementation (Week 8 & Review-3 / 50% Hardware Requirement):**
  - 64-bit Raspberry Pi OS Lite flashed onto 64GB MicroSD.
  - Headless SSH networking (`192.168.2.2`) and 2.9GB RAM swap configured.
  - Active cooling kit (aluminum heatsink + 5V fan) received; physical assembly scheduled post-mid exams.
  - Serving the IntentCloud API and embedded Qdrant index live from the Pi over Cloudflare Tunnel for Review-3.
- **Phase-2 Extension (8th Sem - Major Research Milestone):**
  - Full thermal profiling under sustained load, INT8 ONNX quantization vs. FP32 benchmark comparison, and physical power logging (Joules per query via USB multimeter) to establish the empirical quality-latency-energy Pareto frontier.
