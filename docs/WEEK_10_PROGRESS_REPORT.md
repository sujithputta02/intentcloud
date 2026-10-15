# B.Tech Final Year Capstone Project Phase 1 — Weekly Progress Report

**Dayananda Sagar University**  
**School of Engineering**  
Devarakaggalahalli, Harohalli Kanakapura Road, Bangalore South Dt., Karnataka 562112

**Department of Computer Science and Technology**

---

| Field | Details |
|---|---|
| **Project Semester** | 7 |
| **Duration** | Aug–Dec 2026 |
| **Week No** | 10 |
| **Date Range** | 05/10/2026 to 10/10/2026 |
| **Department** | Computer Science and Technology |
| **Team Number** | Team 3 |
| **Team Members (Names & USN)** | Putta Sujith — ENG23CT0058<br>K Vikas Aneesh Reddy — ENG23CT0052<br>Karnati Mokshith — ENG23CT0053 |
| **Guide** | Dr. Ramandeep Kaur |
| **Project Title** | IntentCloud — Intent-Aware Cognitive Cloud Memory System |

---

## Work Carried Out by the Team

- Generated and indexed a comprehensive empirical corpus of 150 mixed-format documents (50 PDF, 50 DOCX, 50 TXT) across 10 technical domains, embedding version lineage triplets per topic to evaluate document-memory retrieval and recency discrimination.
- Engineered pure-Python stream-level PDF text extraction and XML-based DOCX extractors without external C-extension dependencies, ensuring seamless document ingestion across ARM edge hardware and host systems.
- Designed and executed an automated 50-query evaluation suite across five operational categories (Exact Lexical, Semantic Paraphrase, Multi-Concept, Version Lineage, and Negative Controls) to systematically evaluate the sparse, dense, and proposed hybrid pipelines.
- Achieved 95.0% Top-1 Accuracy, 100.0% Top-3 Accuracy (surpassing the 85% requirement), and an MRR of 0.971 on the 150-document benchmark, demonstrating a 22.5 percentage-point gain over baseline models.
- Calibrated the confidence gating mechanism to achieve a 100% true-negative rejection rate across all out-of-domain queries with strict abstention, effectively preventing false-positive hallucinations.
- Deployed the physical OLED display driver and hardware communication bridge on edge microcontroller hardware and synchronized real-time retrieval pipeline telemetry with the web interface.

---

## Individual Contribution

### Putta Sujith (ENG23CT0058)
- Authored the comprehensive empirical benchmark evaluation suite and integrated dual-query scoring matching production cross-encoder specifications.
- Executed comparative evaluation runs across sparse, dense, and hybrid retrieval modes, validating the 22.5% Top-1 accuracy gain and 100% Top-3 retrieval guarantee.
- Calibrated the confidence gating decision boundary to achieve 100% true-negative rejection across all out-of-domain control queries.
- Updated the IEEE conference paper draft with empirical metrics, experimental evaluation sections, and ablation analysis.

### K Vikas Aneesh Reddy (ENG23CT0052)
- Structured the multi-domain document curriculum schema for the 150-file corpus, covering 10 technical domains with version lineage pairs.
- Developed fallback extraction routines for PDF and DOCX formats to eliminate external native dependencies on edge devices.
- Conducted latency profiling across retrieval stages, measuring sparse search, dense embedding, and reranking to verify sub-second execution.
- Managed synchronization and deployment of document extraction routines to the edge single-board computer over local network protocols.

### Karnati Mokshith (ENG23CT0053)
- Developed the hardware communication bridge daemon linking the backend retrieval pipeline to physical edge display hardware.
- Configured the edge OLED display driver to visualize multi-stage pipeline status transitions in real time.
- Built the interactive hardware monitoring component in the frontend to track edge device state transitions.
- Structured the automated logging and data serialization for empirical evaluation results verification in the project report.

---

## Work Planned for the Following Week (Week 11)

- Optimize and improve the search retrieval pipeline across all file types (PDF, DOCX, TXT, and source code) to ensure comprehensive document coverage, instant indexing, and sub-second query response times.
- Substantially revise and improve the IEEE conference paper draft: expanding theoretical formulations, integrating refined ablation study tables, updating high-resolution architecture diagrams, and formatting strictly to IEEE conference guidelines based on guide recommendations.
- Compile and structure the comprehensive Phase-1 Capstone Project Report incorporating system architecture, mathematical formulations, implementation workflow, and 150-corpus empirical results.
- Finalize the conference submission package and submit the refined paper to the targeted IEEE conference in consultation with the project guide.

---

## Percentage Work Completed

**81%**

*PRD Phase-1 Week 10 target is 78%–83% (Week 6: 54% → Week 7: 62% → Week 8: 67% → Week 9: 74% → Week 10: 81%). Completed this week (+7%): Generation and indexing of the 150-document multi-domain corpus, execution of the 50-query empirical evaluation suite, validation of 95.0% Top-1 / 100.0% Top-3 accuracy and 100% negative rejection, integration of the physical OLED hardware status pipeline, and updating of the IEEE conference paper draft with empirical evaluation data. Paces smoothly into Weeks 11–14 for comprehensive project report documentation, paper submission refinement, and committee review presentation.*

---

| | |
|---|---|
| **Signature of the Students** | _____________________________ |
| **Signature of the Guide(s)** | _____________________________ |
