# 🎙️ IntentCloud — Capstone Phase-1 Demo Speech Script

**Project Title:** IntentCloud: Intent-Aware Cognitive Cloud Memory System  
**Team Members:** 
- Putta Sujith (`ENG23CT0058`)
- K Vikas Aneesh Reddy (`ENG23CT0052`)
- Mokshith Karnati (`ENG23CT0053`)  
**Project Guide:** Dr. Ramandeep Kaur  
**Institution:** Department of Computer Science & Technology, Dayananda Sagar University  
**Milestone:** Capstone Phase-1 Review (7th Semester)  

---

## ⏱️ Quick Presentation Roadmap (~5 Minutes)

| Time | Stage | Action / Visual | Key Talking Point |
|---|---|---|---|
| **0:00 – 1:00** | **Section 1: The Core Problem** | Show Title Slide | Traditional search fails on intent; cloud AI violates privacy and hallucinates. |
| **1:00 – 2:15** | **Section 2: Objectives & Phase-1 Scope** | Show Objectives Slide | 50–50 academic split; Phase-1 completed Objectives 1, 2, and 3 (97.5% accuracy). |
| **2:15 – 4:00** | **Section 3: Live System Demo** | Screen share browser (`localhost:3010`) | Query: `"i need a colour palette file"` → Rank #1 in 798ms, full 6-swatch palette, OLED telemetry. |
| **4:00 – 4:45** | **Section 4: IEEE Research Paper** | Open IEEE Paper PDF / LaTeX | Empirical benchmark on 175 documents, RRF formula, mathematical proof. |
| **4:45 – 5:15** | **Section 5: Phase-2 Scope & Q&A** | Show Roadmap Slide | Phase-2 (DAG lineage, gating, edge INT8 quantization). Open for questions. |

---

## 🎤 Full Verbatim Speaking Script

---

### 1. Introduction & Problem Statement (1:00 min)

> **"Respected evaluators and guides, Good morning / afternoon.**  
>
> Today, our team is presenting our capstone project: **IntentCloud — an Intent-Aware Cognitive Cloud Memory System**.  
>
> #### The Problem We Are Solving:
> In everyday work, traditional desktop search tools like Windows Search or macOS Spotlight only do basic keyword matching. If you forget the exact filename and search by conceptual intent—for instance, *“i need a colour palette file”* or *“deployment architecture diagram”*—they return zero results.  
>
> Meanwhile, modern cloud AI search engines upload all your private, proprietary personal documents to external third-party servers like OpenAI. Worse, they return generated text summaries instead of delivering the **authentic original file** you actually need to edit or present.  
>
> #### Our Solution:
> **IntentCloud** solves this by providing a **100% local-first, privacy-preserving cognitive cloud**. It understands natural language intent, indexes multi-modal document evidence (including OCR and extracted visual color palettes), and delivers the **authentic original document** in sub-second response time with zero external API calls."

---

### 2. Project Objectives & Phase-1 Accomplishments (1:15 min)

> "Our capstone project is structured across a clear **50–50 academic milestone split**:  
>
> - **Phase-1 (7th Semester):** Focuses on **Objectives 1, 2, and 3** — the core functional foundation, hybrid dual-stream retrieval, local multi-format document and vision processing, self-hosted web service, and empirical benchmark validation. **All 3 objectives are 100% completed.**  
> - **Phase-2 (8th Semester):** Focuses on **Objectives 4, 5, and 6** — research optimizations: document version lineage DAGs, adaptive intent gating, and INT8 ONNX quantization on edge hardware.  
>
> #### What We Finished in Phase-1:
>
> 1. **Objective 1 — Hybrid Retrieval with Reciprocal Rank Fusion:**  
>    We designed and implemented a dual-stream search pipeline combining:  
>    - **Sparse Token Feature Hashing** (1,000,003 dimensions) for exact codes, acronyms, and technical terms.  
>    - **Dense Semantic Embeddings** (`all-MiniLM-L6-v2`, 384 dimensions) for conceptual understanding.  
>    - **Reciprocal Rank Fusion (RRF, $k=60$)** to balance both rankings without score distortion.  
>    - **Cross-Encoder Reranking** (`ms-marco-MiniLM-L-6-v2`) for sentence-level citation verification.  
>    - *Empirical Result:* On our 175-document benchmark across 10 domains, our hybrid engine achieved **97.5% Top-1 Accuracy** and **0.983 MRR**, outperforming dense and keyword baselines by **25 percentage points**.
>
> 2. **Objective 2 — 100% Local Multi-Modal Document & Vision Processing:**  
>    Running completely offline on consumer hardware with zero cloud subscriptions:  
>    - Native multi-format parser for **PDF, DOCX, PPTX presentations, and images**.  
>    - **Apple Vision Neural Engine OCR** executing in ~20 milliseconds.  
>    - **Local Vision-Language Model** (Ollama Moondream) for scene layout analysis.  
>    - **Dominant Pixel Color Quantization & Swatch Extraction** to automatically detect brand palettes and hex codes.
>
> 3. **Objective 3 — Self-Hosted Service, Hardware Sync & Original File Delivery:**  
>    A production-grade FastAPI and Next.js platform that serves the **authentic original files** with in-browser previews and one-click downloads in under 1 second, while streaming live search telemetry to an **I2C OLED display on a Raspberry Pi**."

---

### 3. Live Demonstration Walkthrough (1:45 min)

*(Switch screen to your browser at `http://localhost:3010`)*

> **`[STEP 1: Show the Document Workspace]`**  
> *"Here is our IntentCloud interface. You can see our local archive of multi-format documents: PDFs, DOCX files, PowerPoint decks, and high-resolution images, indexed with cognitive topic clusters."*  
>
> **`[STEP 2: Type Natural Language Intent in Search Bar]`**  
> *"Now, let's run a test where traditional keyword search completely fails. I will search using conceptual intent:*  
> **`i need a colour palette file`**  
> *(Notice that I am using British spelling 'colour', and I have not specified the filename or extension.)*  
>
> **`[PRESS ENTER & POINT TO LATENCY]`**  
> *"In just **798 milliseconds**, IntentCloud delivers **Rank #1 with 90% confidence**: `WhatsApp Image 2026-09-03 at 20.25.38.jpeg`, which is the brand visual identity slide from our presentation deck.*  
>
> **`[STEP 3: Highlight Visual Intelligence & Color Swatches]`**  
> *Look at the Visual Intelligence panel:*  
> 1. **Scene Description:** It accurately identifies the slide layout: *'Presentation slide displaying a 6-color palette grid titled Minimal Structure. Maximum Personality.'*  
> 2. **Detected Color Palette Swatches:** It extracted all 6 brand colors with their exact hex codes:  
>    - **Cherry Red (`#590F1E`)**  
>    - **Dark Teal (`#0C4238`)**  
>    - **Light Teal (`#17846F`)**  
>    - **Beige (`#D58842`)**  
>    - **Pitch Black (`#000000`)**  
>    - **Pure White (`#FFFFFF`)**  
>    *Each swatch is fully interactive—clicking any swatch copies the hex code directly to the clipboard.*  
>
> **`[STEP 4: Point to the Edge OLED Display]`**  
> *Simultaneously, our edge OLED display on the Raspberry Pi updated in real-time, showing `PUSHED | Pi 3B | 90% Match` alongside the retrieved filename.*  
>
> **`[STEP 5: Show Authentic File Delivery]`**  
> *Unlike an LLM that summarizes text and hallucinates, clicking **Inspect** opens the high-resolution original image with OCR labels, and clicking **Download** delivers the exact authentic file immediately."*

---

### 4. IEEE Research Paper Presentation (0:45 min)

*(Open the compiled paper or LaTeX file `docs/paper/ieee_paper_1.tex`)*

> **"To formally validate our architecture and empirical results, we have authored an IEEE conference paper:**  
>  
> - **Title:** *'Intent-Aware Hybrid Document Retrieval with Reciprocal Rank Fusion and Cross-Encoder Reranking'*  
> - **Authors:** Putta Sujith, K Vikas Aneesh Reddy, Mokshith Karnati, guided by Dr. Ramandeep Kaur, Dayananda Sagar University.  
>  
> **Key Contributions in the Paper:**  
> 1. The mathematical formulation of the dual-stream Dense-Sparse Reciprocal Rank Fusion pipeline ($k=60$).  
> 2. Empirical benchmark on 175 documents across 10 domains proving **97.5% Top-1 accuracy** and **0.983 MRR**, outperforming dense and keyword baselines by 25 percentage points.  
> 3. An empirical confidence threshold mechanism achieving **100% true-negative rejection** on out-of-domain queries to eliminate hallucinations.  
> 4. Full IEEE-standard citation provenance and edge hardware profiling."

---

### 5. Conclusion & Phase-2 Roadmap (0:30 min)

> **"In conclusion:**  
> For Phase-1, we have successfully completed 100% of our planned objectives: delivering a fully working, privacy-preserving hybrid retrieval system with multi-modal visual extraction and authentic file delivery.  
>
> In Phase-2 (8th Semester), we will focus on our research objectives:  
> - **Objective 4:** Document Version History DAGs for automatic revision tracking.  
> - **Objective 5:** Adaptive intent gating and confidence-based abstention.  
> - **Objective 6:** INT8 ONNX neural quantization and edge profiling on the Raspberry Pi 4B.  
>
> Thank you, and we look forward to your questions!"

---

## 🎯 Evaluator Q&A Cheat Sheet (Instant Answers)

1. **Q: Why not just use a standard RAG chatbot like LangChain or ChatGPT?**  
   > *"Chatbots generate text summaries that can hallucinate details, and they require uploading private files to third-party cloud servers. IntentCloud is 100% local, privacy-first, zero-subscription, and delivers the **authentic original file** with sentence-level verifiable citations."*

2. **Q: Why combine Dense and Sparse search instead of pure Vector Search?**  
   > *"Vector embeddings understand broad conceptual synonyms, but fail on exact technical codes, serial numbers, and filenames. Sparse hashing captures exact tokens. Reciprocal Rank Fusion (RRF) combines both strengths, boosting our Top-1 accuracy from 72.5% to 97.5%."*

3. **Q: How does visual intelligence run locally without cloud vision APIs?**  
   > *"We use Apple Vision Neural Engine OCR on macOS running in ~20 milliseconds, local Ollama Moondream VLM for semantic scene layouts, and Pillow pixel quantization to extract dominant hex swatches. Everything runs 100% offline on consumer hardware."*

4. **Q: What is the hardware connection to the Raspberry Pi OLED?**  
   > *"The FastAPI backend streams search event payloads over an asynchronous bridge to the Raspberry Pi, which renders match percentage, device status, and filename to a 0.96-inch SSD1306 I2C OLED display."*
