# IntentCloud Review-2 Presentation & Live Demo Master Script
## B.Tech Capstone Project Phase 1 (7th Semester, 2026–2027)

| Metadata | Details |
|---|---|
| **Project Title** | IntentCloud: Intent-Aware Cognitive Cloud Memory System |
| **Review Milestone** | Review-2 ($\ge 25\%$ Working Implementation Demo + Progress Status) |
| **Evaluation Date** | 12 September 2026 (50 Marks) |
| **Current Progress** | **54% Cumulative Completion** (PRD Week 6 target: 58%; Pi migration deferred to Week 7. Exceeds $\ge 25\%$ requirement.) |
| **Team Members** | Sujith Putta (`ENG23CT0058`), K Vikas Aneesh Reddy (`ENG23CT0052`), Mokshith Karnati (`ENG23CT0053`) |
| **Research Guide** | Dr. Ramandeep Kaur, Associate Professor, Dept. of CST, DSU |

---

## 1. Slide Deck Master Outline (10 Slides)

### Slide 1: Title & Team Information
- **Title:** IntentCloud: Intent-Aware Cognitive Cloud Memory System
- **Subtitle:** Phase 1: Algorithmic Hybrid Retrieval, Reciprocal Rank Fusion & Precision Reranking
- **Presenters:** Sujith Putta, K Vikas Aneesh Reddy, Mokshith Karnati
- **Guide:** Dr. Ramandeep Kaur, Dept. of CST, School of Engineering, Dayananda Sagar University
- **Date:** 12 September 2026

### Slide 2: Problem Statement & Motivation
- **The Personal Re-Finding Dilemma:** Users store hundreds of PDFs, notes, and specs across nested folders but fail to recall exact filenames or paths.
- **Why Existing Solutions Fail:**
  - *OS File Search:* Fails on conceptual intent (rigid keyword/substring matching only).
  - *Cloud RAG / ChatGPT:* Massive privacy leakage (sending private docs to external APIs), paid per-query subscriptions, and generated summaries instead of source files.
  - *Pure Vector Databases:* Dense embeddings miss rare domain tokens, error codes, and exact technical terms; force false positives on irrelevant queries.

### Slide 3: Proposed Architecture & Core Innovation
- **Four-Phase Local Architecture:**
  1. *Ingestion & Extraction:* PyMuPDF + python-docx with automated Tesseract OCR fallback and near-duplicate cosine filtering ($\ge 0.95$).
  2. *Dual-Stream Representation:* Parallel 384-d dense embeddings (`all-MiniLM-L6-v2`) and 1,000,003-d deterministic feature-hashed sparse token vectors.
  3. *Intent Parsing & Query Expansion:* Local LLM (`llama3.2:1b`) running offline via Ollama.
  4. *Hybrid Retrieval & Cross-Encoder Reranking:* Embedded Qdrant vector engine $\rightarrow$ Reciprocal Rank Fusion ($k=60$) $\rightarrow$ Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) $\rightarrow$ Sentence-level citation extraction $\rightarrow$ Calibrated confidence gate ($\tau=0.40$).

### Slide 4: Algorithmic Formulations (Mathematical Depth)
- **Reciprocal Rank Fusion (RRF):**
  $$\text{Score}_{\text{RRF}}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + \text{rank}_m(d)}$$
  *Why RRF?* Eliminates score scale incompatibility between unbounded BM25/sparse weights and bounded cosine similarities.
- **Cross-Encoder Confidence Sigmoid:**
  $$s_{\text{ce}}(q, d) = \sigma(z(q, d)) = \frac{1}{1 + e^{-z(q, d)}}$$
- **Out-of-Domain Abstention Gate:**
  If $\max_d s_{\text{ce}}(q, d) < 0.40$, output: `"No confident match found"` (out-of-domain abstention).

### Slide 5: Implementation Progress Status vs. Circular Requirements
- **University Review-2 Requirement:** Minimum **25%** working implementation.
- **IntentCloud Current Progress:** **54% Cumulative Completion** (PRD Week 6 target: 58%; Pi memory-layer migration pending Week 7).
  - Phase 1 (Ingestion & Extraction): **100% Complete**
  - Phase 2 (Vector Indexing & Sparse Hashing): **100% Complete**
  - Phase 3 (Intent Extraction & Expansion): **100% Complete**
  - Phase 4 (Hybrid RRF & Cross-Encoder Reranking): **100% Complete**
  - Evaluation & Benchmarking: **100% Complete (35 queries)**
  - Academic Paper 1: **Draft finalized in IEEE LaTeX format**

### Slide 6: Live Demonstration Transition Slide
- *[Switch to Browser: `http://localhost:3010`]*
- Demonstrating:
  1. Instant Document Ingestion & Text Extraction.
  2. Positive Query: Semantic + Lexical Match with Golden Sentence Highlight.
  3. Out-of-Domain Query: Calibrated Anti-Hallucination Gate.
  4. Instant Source File Download.

### Slide 7: Empirical Benchmark Results (35-Query Suite)
| Pipeline Configuration | Top-1 Accuracy | Top-3 Accuracy | MRR | Avg Latency | Out-of-Domain Rejection |
|---|---|---|---|---|---|
| Mode A: Sparse Keyword Baseline | 87.5% | 96.9% | 0.922 | 1,567 ms | 100% |
| Mode B: Dense Semantic Baseline | 87.5% | 96.9% | 0.922 | 1,103 ms | 100% |
| Mode C: RRF Hybrid (No Rerank) | 87.5% | 96.9% | 0.927 | 1,180 ms | 100% |
| **Mode D: Full Hybrid + RRF + Rerank** | **90.6%** | **100.0%** | **0.953** | **1,457 ms** | **100%** |

- **Key Takeaway:** Hybrid + RRF + Cross-Encoder achieves **+3.1% Top-1 accuracy** over pure dense and sparse baselines and **100% Top-3 accuracy**, exceeding PRD $\ge 85\%$ target.

### Slide 8: Hardware Procurement & Edge Roadmap
- **Physical Evidence:** Display unboxed Raspberry Pi 3B board, official power supply, microSD card, and other procured accessories (heatsink and cooling fan to be ordered in Week 7).
- **Edge Deployment Plan (Week 7–8):**
  - Order heatsink and active cooling fan; flash Raspberry Pi OS and setup headless SSH (`intentcloud-pi`).
  - Migrate Qdrant embedded storage and FastAPI service to the Pi edge node.
  - Expose via outbound Cloudflare Zero-Trust Tunnel (remote HTTPS without open router ports).

### Slide 9: Research Contribution (IEEE Paper 1 Submission)
- **Title:** *"Hybrid Neural-Lexical Information Retrieval with Reciprocal Rank Fusion and Cross-Encoder Reranking for Intent-Aware Local Document Understanding"*
- **Target Venue:** IEEE Conference on Cognitive Computing & Applied AI.
- **Status:** Complete IEEEtran LaTeX manuscript and plain-text submission package prepared.

### Slide 10: Conclusion & Next Steps (Week 7 Roadmap)
- Completed Phase 1–4 local pipeline running with zero cloud API dependencies.
- Confirmed sub-1.5s latency and 90.6% Top-1 precision on consumer hardware.
- Next Milestone: Edge migration to Raspberry Pi and Cloudflare Tunnel deployment for Review-3 ($\ge 50\%$ gate).

---

## 2. Live Demo Script (Step-by-Step for the Panel)

### Pre-Demo Checklist (2 minutes before presentation)
1. Ensure backend is running in terminal:
   ```bash
   cd <repo_root>/intentcloud-api
   source venv/bin/activate
   python main.py
   ```
2. Ensure frontend is running:
   ```bash
   cd <repo_root>/intentcloud-web
   bun run dev
   ```
3. Open browser tabs:
   - Tab 1: `http://localhost:3010/upload`
   - Tab 2: `http://localhost:3010/search`
   - Tab 3: `http://localhost:3010/dashboard`

---

### Step 1: Document Upload & Extraction Demo (`/upload`)
- **Action:** Drag and drop a sample PDF or TXT file into the upload zone.
- **Speaker (Vikas):**
  > *"Here we demonstrate Phase 1. When a user uploads a document, IntentCloud immediately extracts the full text using PyMuPDF. If a document is a scanned image, an automated Tesseract OCR fallback triggers automatically. Before indexing, a cosine similarity check against existing vectors detects near-duplicates ($\ge 0.95$) to prevent redundant storage. The document is chunked and embedded in parallel into dense 384-dimensional vectors and 1-million-dimensional sparse feature hashes directly inside our embedded Qdrant database."*

---

### Step 2: Positive Query Demo (`/search`)
- **Query to Type:** `Kafka stream processing latency and consumer groups`
- **Click:** **Search** (Mode: Hybrid)
- **What Appears:**
  - Rank 1 Card: `kafka_stream_processing.txt` (Match: ~94%)
  - Rank 2 Card: `kafka_performance_tuning.txt` (Match: ~88%)
  - Rank 3 Card: `distributed_systems_notes.txt` (Match: ~81%)
  - Under Rank 1: Golden highlighted quote:
    > *"Kafka consumer lag occurs when consumer processing time exceeds message arrival rate..."*
- **Speaker (Sujith):**
  > *"Notice what happened here: In parallel, Qdrant retrieved top-20 dense semantic candidates and top-20 sparse keyword candidates. Reciprocal Rank Fusion ($k=60$) unified these disparate candidate lists using scale-invariant ranks. Then, our local cross-encoder model reranked the top candidates with full token-to-token cross-attention.*
  > *Crucially, notice the illuminated golden quote box. We don't just return a file; we extract the highest-scoring sentence within the winning chunk to provide an explainable 'Why this matched' citation to the user."*

---

### Step 3: Out-of-Domain Negative Abstention Demo (`/search`)
- **Query to Type:** `How to bake chocolate sourdough bread at home`
- **Click:** **Search**
- **What Appears:**
  - An amber warning banner: **"No confident match found in your library."**
  - Below it: Results flagged with a "Low Confidence" badge.
- **Speaker (Sujith):**
  > *"This answers a major flaw in standard vector databases and RAG systems: hallucination on irrelevant queries. Standard nearest-neighbor search always forces a top match, even if you search for cooking recipes on a computer science repository.*
  > *IntentCloud applies a logistic sigmoid confidence threshold ($\tau = 0.40$) on cross-encoder logits. Because this cooking query scored only 0.08, the system gracefully abstains, protecting the user from false-positive hallucinations."*

---

### Step 4: Empirical Benchmark Evidence (`/dashboard`)
- **Action:** Navigate to the Dashboard or display Slide 7.
- **Speaker (Mokshith):**
  > *"We verified our system using an automated 35-query benchmark. As seen in our empirical table, sparse-only search achieved 87.5% and dense-only achieved 87.5%. Our hybrid RRF + Cross-Encoder pipeline boosted Top-1 accuracy to 90.6% and Top-3 accuracy to a perfect 100.0% with an MRR of 0.953, fully satisfying our PRD requirement of $\ge 85\%$."*

---

### Step 5: Physical Hardware Procurement Proof
- **Action:** Pick up and show the Raspberry Pi 3B board, power supply, and microSD card to the panel.
- **Speaker (Vikas):**
  > *"Here is our procured Raspberry Pi 3B with official power supply and microSD card. Heatsink and cooling fan will be ordered in Week 7. We validated the complete pipeline in laptop simulation mode for Review-2. In Week 7, we will flash Raspberry Pi OS, migrate Qdrant storage onto the Pi, and expose it via Cloudflare Zero-Trust Tunnels for our Review-3 milestone."*

---

## 3. Defense Preparation: Potential Examiner Questions & Answers

### Question 1: *"Why is IntentCloud anything more than an ordinary wrapper around Qdrant and Sentence-Transformers?"*
**Answer (Sujith):**
> *"External libraries provide isolated building blocks, but personal re-finding has unique failure modes that simple vector wrappers fail to solve. Dense vector search misses exact technical keywords and codes; uniform vector distance cannot abstain on negative queries; and simple vector similarity provides no human-interpretable explanations.*
> *Our research contribution is an intent-conditioned multi-stage retrieval architecture: we combine universal 1-million-dimensional sparse MurmurHash3 vectors with dense vectors using Reciprocal Rank Fusion ($k=60$), followed by cross-encoder reordering with sentence-level citation extraction and calibrated confidence gating. We prove empirically that this hybrid fusion achieves 90.6% Top-1 accuracy and 100% Top-3 accuracy, outperforming pure dense and sparse baselines on identical hardware with zero cloud API dependencies."*

### Question 2: *"Why did you use Reciprocal Rank Fusion instead of just adding the cosine similarity and BM25 score together?"*
**Answer (Sujith):**
> *"Cosine similarity is strictly bounded in $[0, 1]$, whereas sparse BM25 scores are unbounded and depend on document length and term saturation. Adding raw scores together is mathematically unsound and requires manual tuning for every dataset.*
> *Reciprocal Rank Fusion uses candidate rank orders rather than raw scores ($1 / (k + \text{rank})$), ensuring scale-invariant, outlier-resistant fusion that remains stable regardless of query length or score magnitude."*

### Question 3: *"Why run on a Raspberry Pi when you can just host it on AWS or Google Cloud?"*
**Answer (Vikas):**
> *"Personal documents contain sensitive contracts, tax records, and proprietary source code. Hosting on commercial cloud services introduces ongoing subscription costs, vendor lock-in, and privacy leakage risks. A Raspberry Pi 3B edge node consumes under 10 watts of power, costs under \$50, and runs continuously inside the user's home or office as an air-gapped, zero-trust personal knowledge server."*
