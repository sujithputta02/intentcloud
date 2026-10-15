# 🎙️ IntentCloud: Final Demo & Presentation Speech Script
**Project Title:** IntentCloud — Intent-Aware Cognitive Cloud Memory System  
**Team Members:** Putta Sujith (`ENG23CT0058`), K Vikas Aneesh Reddy (`ENG23CT0052`), Mokshith Karnati (`ENG23CT0053`)  
**Project Guide:** Dr. Ramandeep Kaur  
**Department:** Department of Computer Science & Technology, Dayananda Sagar University  
**Milestone:** Capstone Phase-1 (7th Semester Final Evaluation & Review)  

---

## ⏱️ Presentation Outline & Timing (Total ~5–6 Minutes)

| Section | Topic | Allocated Time |
|---|---|---|
| **Section 1** | Introduction & The Core Problem | 1.0 min |
| **Section 2** | Project Objectives & Phase-1 Scope (50–50 Split) | 1.5 min |
| **Section 3** | Live System Demonstration (Workspace, Intent Search, Visual Swatches) | 2.0 min |
| **Section 4** | IEEE Research Paper Presentation | 1.0 min |
| **Section 5** | Conclusion & Roadmap to Phase-2 | 0.5 min |

---

## 🎤 Speaker Script

---

### Section 1: Introduction & The Core Problem (1 minute)

> **"Respected evaluators and guides, Good morning / afternoon.**  
>
> Today, we are presenting our capstone project: **IntentCloud — an Intent-Aware Cognitive Cloud Memory System**.  
>
> #### The Problem:
> When we look for files on our personal computers or cloud storage, traditional search tools like Windows Search or macOS Spotlight fail whenever we don’t remember the exact filename. If you search by meaning or conceptual intent—for example, *“i need a colour palette file”* or *“deployment architecture diagram”*—traditional keyword search returns zero results.  
>
> On the other hand, commercial AI search engines upload all your private personal and enterprise documents to third-party cloud APIs (like OpenAI), exposing sensitive data, and often return AI-generated text summaries rather than the authentic original document you actually need to edit, read, or share.  
>
> #### Our Solution:
> **IntentCloud** solves this by providing a **100% local-first, privacy-preserving personal cloud** that understands natural language intent, retrieves both text and visual evidence (diagrams, color palettes, and presentation slides), and delivers the **authentic original file** in sub-second response time with zero external API calls."

---

### Section 2: Overall Project Objectives & Phase-1 Scope (1.5 minutes)

> "Our capstone project follows a structured **50–50 academic partition**:  
> - **Phase-1 (7th Semester):** Focuses on **Objectives 1, 2, and 3** — building the complete functional foundation: hybrid retrieval, local multi-format document/vision processing, self-hosted web service with original file delivery, and empirical benchmark validation. **All 3 objectives are 100% completed.**  
> - **Phase-2 (8th Semester):** Focuses on **Objectives 4, 5, and 6** — research optimizations: document version lineage DAGs, adaptive intent gating, and INT8 ONNX quantization on the edge Raspberry Pi.  
>
> #### Phase-1 Completed Objectives:
>
> 1. **Objective 1 — Hybrid Retrieval Pipeline with Rank Fusion:**  
>    We engineered a dual-stream search engine combining:  
>    - **Sparse Keyword Search** (1,000,003-dimensional token feature hashing) for exact terms and technical IDs.  
>    - **Dense Semantic Embeddings** (384-dimensional `all-MiniLM-L6-v2`) for conceptual understanding.  
>    - **Reciprocal Rank Fusion (RRF, $k=60$)** to combine both result sets fairly without score distortion.  
>    - **Cross-Encoder Reranking** (`ms-marco-MiniLM-L-6-v2`) for sentence-level citation verification.  
>    - *Empirical Result:* Our hybrid pipeline achieved **97.5% Top-1 Accuracy** and **0.983 Mean Reciprocal Rank (MRR)** on a 175-document benchmark, outperforming keyword and dense baselines by **25 percentage points**.
>
> 2. **Objective 2 — 100% Local & Multi-Modal Vision Processing:**  
>    Everything runs on consumer-grade hardware with zero third-party APIs. We implemented native multi-format extraction for **PDF, DOCX, PPTX presentations, and Images**, including:  
>    - **Native Apple Vision Neural Engine OCR** running in ~20 milliseconds.  
>    - **Local Vision-Language Model (VLM)** using Ollama Moondream for visual scene understanding.  
>    - **Dominant Pixel Color Quantization & Swatch Extraction** to automatically identify design palettes and hex codes.
>
> 3. **Objective 3 — Self-Hosted Service, Hardware Sync & Original File Delivery:**  
>    Unlike LLM chatbots that hallucinate text, IntentCloud is a production-grade FastAPI & Next.js service that returns the **authentic original file** with instant in-browser previews and one-click download in **under 1 second**, with real-time hardware telemetry pushed to an attached **I2C OLED display on a Raspberry Pi**."

---

### Section 3: Live Demonstration Walkthrough (2 minutes)

*(Switch screen to the browser: `http://localhost:3010`)*

> **`[DEMO ACTION 1: Show the Workspace]`**  
> *"Here is the IntentCloud Document Workspace. You can see our local archive of multi-format documents: PDFs, Word documents, PowerPoint decks, and image assets organized with cognitive topic tags."*
>
> **`[DEMO ACTION 2: Type Query in Search Bar]`**  
> *"Now, let's test a natural language intent query where traditional search completely fails. I will search:*  
> **`i need a colour palette file`**  
> *(Notice I'm using British spelling 'colour', and not mentioning the filename at all.)*  
>
> **`[HIT ENTER & SHOW RESULTS]`**  
> *"In just **798 milliseconds**, IntentCloud delivers **Rank #1 with 90% confidence**: `WhatsApp Image 2026-09-03 at 20.25.38.jpeg`—which is the brand visual system slide from our PowerPoint deck.*  
>
> **`[POINT TO THE VISUAL INTELLIGENCE CARD]`**  
> *Look at what our multi-modal vision engine extracted in real-time:*  
> 1. **Visual Scene Understanding:** It describes the slide layout: *'Presentation slide displaying a 6-color palette grid titled Minimal Structure. Maximum Personality.'*  
> 2. **Detected Color Palette Swatches:** It successfully identified all 6 brand swatches with their exact hex codes:  
>    - **Cherry Red (`#590F1E`)**  
>    - **Dark Teal (`#0C4238`)**  
>    - **Light Teal (`#17846F`)**  
>    - **Beige (`#D58842`)**  
>    - **Pitch Black (`#000000`)**  
>    - **Pure White (`#FFFFFF`)**  
>    *And each swatch chip is interactive—you can click any chip to copy the hex code directly to your clipboard.*  
>
> **`[POINT TO OLED HARDWARE SCREEN / CAMERA]`**  
> *Simultaneously, our edge OLED display on the Raspberry Pi updated in live time showing `PUSHED | Pi 3B | 90% Match` and the filename.*  
>
> **`[CLICK 'PREVIEW' / 'DOWNLOAD']`**  
> *Finally, clicking **Inspect** opens our full Visual Intelligence modal showing the high-resolution image, full OCR labels, and one-click download of the authentic original file."*

---

### Section 4: The IEEE Research Paper (1 minute)

*(Open the PDF or LaTeX document of your paper: `docs/paper/ieee_paper_1.tex`)*

> **"To formally validate our work, we have authored an IEEE conference research paper:**  
>  
> - **Paper Title:** *'Intent-Aware Hybrid Document Retrieval with Reciprocal Rank Fusion and Cross-Encoder Reranking'*  
> - **Authors:** Putta Sujith, K Vikas Aneesh Reddy, Mokshith Karnati, under the guidance of Dr. Ramandeep Kaur, Department of Computer Science & Technology, Dayananda Sagar University.  
>  
> **Key Contributions Documented in the Paper:**  
> 1. The mathematical formulation of the dual-stream Dense-Sparse Reciprocal Rank Fusion architecture ($k=60$).  
> 2. The empirical benchmark on 175 documents across 10 domains demonstrating **97.5% Top-1 accuracy** and **0.983 MRR**, outperforming dense and keyword baselines by 25 percentage points.  
> 3. Zero-hallucination empirical confidence thresholding achieving **100% true-negative rejection** on out-of-domain queries.  
> 4. Full IEEE-standard figure citation provenance and local hardware edge latency evaluation."

---

### Section 5: Conclusion & Roadmap to Phase-2 (30 seconds)

> **"In conclusion:**  
> For Phase-1, we have successfully met 100% of our objectives: building a working, validated, privacy-preserving hybrid retrieval engine with multimodal visual intelligence and original document delivery.  
>
> In Phase-2 (8th Semester), we will extend this with:  
> - **Objective 4:** Document Version History DAGs for tracing draft vs. final revisions.  
> - **Objective 5:** Adaptive intent gating and confidence-based abstention.  
> - **Objective 6:** INT8 ONNX neural quantization and edge profiling on the Raspberry Pi 4B.  
>
> Thank you, and we are now open to any questions!"

---

## 📌 Q&A Cheat Sheet (Potential Evaluator Questions)

1. **Q: Why not use a standard RAG chatbot like LangChain or ChatGPT?**  
   **A:** Chatbots generate text summaries that can hallucinate details, and they require sending private documents to third-party cloud APIs. IntentCloud is local-first, zero-subscription, privacy-preserving, and delivers the **authentic original file** with sentence-level verifiable citations.

2. **Q: Why combine Dense and Sparse search instead of just Vector Search?**  
   **A:** Dense vectors are great for conceptual synonyms, but fail on exact technical codes, IDs, and filenames (out-of-vocabulary). Sparse search captures exact tokens. Reciprocal Rank Fusion (RRF) gives the best of both worlds, boosting Top-1 accuracy from 72.5% to 97.5%.

3. **Q: How does the visual extraction work on edge hardware?**  
   **A:** We use Apple Vision Neural Engine OCR on macOS (taking ~20ms) combined with local Ollama VLM (Moondream) for semantic scene descriptions and Pillow color quantization for pixel palette extraction. No cloud vision APIs are used.

4. **Q: How does the OLED display communicate?**  
   **A:** The backend streams live telemetry over an asynchronous lightweight WebSocket / HTTP bridge to the Raspberry Pi running an SSD1306 OLED script over I2C bus.
