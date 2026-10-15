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
| **Week No** | 9 |
| **Date Range** | 28/09/2026 to 03/10/2026 |
| **Department** | Computer Science and Technology |
| **Team Number** | Team 3 |
| **Team Members (Names & USN)** | Putta Sujith — ENG23CT0058<br>K Vikas Aneesh Reddy — ENG23CT0052<br>Karnati Mokshith — ENG23CT0053 |
| **Guide** | Dr. Ramandeep Kaur |
| **Project Title** | IntentCloud — Intent-Aware Cognitive Cloud Memory System |

---

## Work Carried Out by the Team

- Physically assembled the single-board edge computer with the aluminum heatsink enclosure and active 5V cooling fan, validating continuous thermal regulation under active processing loads.
- Configured and validated the background system service (`intentcloud.service`) on the edge device (`192.168.2.2`), establishing persistent auto-restart capabilities and health check telemetry.
- Enhanced the multi-format ingestion pipeline with embedded visual figure and diagram extraction for technical documents, associating figure captions and spatial metadata for multimodal evidence attribution.
- Conducted test ingestion runs of the multi-format document corpus on the edge vector database, validating schema persistence, chunk graph pointers, and version lineage metadata indexing.
- Established and optimized the local network API proxy bridge between the Next.js cognitive web client and the edge memory layer, eliminating cross-origin latency and handling service connectivity gracefully.
- Prototyped the hardware telemetry communication protocol for physical device status indication, preparing the pipeline event hooks to stream retrieval stages to external hardware.

---

## Individual Contribution

### Putta Sujith (ENG23CT0058)
- Engineered the edge service auto-recovery configuration and tested FastAPI background workers under sustained local network traffic.
- Implemented the visual diagram and embedded figure extraction logic within the PDF processing pipeline, binding detected figure captions to vector chunk payloads.
- Optimized the search orchestrator's multimodal query expansion and recency filtering to ensure sub-second candidate retrieval across the edge memory layer.
- Authored the Week 9 milestone report and coordinated technical progress verification against the Phase-1 Review-3 evaluation rubric.

### K Vikas Aneesh Reddy (ENG23CT0052)
- Completed physical hardware assembly of the single-board computer, securing the aluminum heatsinks and wiring the 5V active cooling fan to GPIO pins.
- Conducted thermal profiling benchmarks on the edge hardware, recording baseline idle temperatures (41°C) and active ingestion peak thermals (under 58°C) without throttling.
- Tested batch corpus ingestion across technical document formats (PDF, DOCX, TXT) to verify chunk sequence graph indexing and memory utilization in Qdrant.
- Validated fallback text extraction routines on ARM64 Linux, ensuring seamless document ingestion without external binary dependency failures.

### Karnati Mokshith (ENG23CT0053)
- Designed the telemetry serialization schema and event hooks to broadcast retrieval states (IDLE, SEARCHING, RERANKING, PUSHED) from the backend pipeline.
- Configured and tested local network routing and proxy endpoints between the Next.js web interface and the edge device IP (`192.168.2.2:8000`).
- Developed the prototype hardware bridge communication script for edge display device integration.
- Conducted end-to-end integration tests on document upload, indexing status, and search response rendering to verify web client stability.

---

## Work Planned for the Following Week (Week 10)

- Generate and index a comprehensive empirical corpus of 150 mixed-format documents (50 PDF, 50 DOCX, 50 TXT) across 10 technical domains, embedding version lineage triplets per topic to evaluate document-memory retrieval and recency discrimination.
- Engineer pure-Python stream-level PDF text extraction and XML-based DOCX extractors without external C-extension dependencies, ensuring seamless document ingestion across ARM edge hardware and host systems.
- Design and execute an automated 50-query evaluation suite across five operational categories (Exact Lexical, Semantic Paraphrase, Multi-Concept, Version Lineage, and Negative Controls) to systematically evaluate the sparse, dense, and proposed hybrid pipelines.
- Benchmark hybrid retrieval against baseline models, targeting 95.0% Top-1 Accuracy, 100.0% Top-3 Accuracy (surpassing the 85% requirement), and an MRR of 0.971 on the 150-document benchmark corpus.
- Calibrate the confidence gating decision boundary to achieve a 100% true-negative rejection rate across all out-of-domain queries with strict abstention, effectively preventing false-positive hallucinations.
- Deploy the physical OLED display driver and hardware communication bridge on edge microcontroller hardware and synchronize real-time retrieval pipeline telemetry with the web interface.

---

## Percentage Work Completed

**74%**

*PRD Phase-1 Week 9 target is 70%–75% (Week 6: 54% → Week 7: 62% → Week 8: 67% → Week 9: 74% → Week 10: 81%). Completed this week (+7%): Physical board assembly with active cooling, baseline thermal validation under continuous operation, edge background daemon configuration on Raspberry Pi (`192.168.2.2`), visual figure and diagram extraction pipeline enhancements, vector database lineage test ingestion, and hardware telemetry communication protocol prototyping. Seamlessly bridges Week 8 preparation into Week 10 empirical evaluation and Review-3 presentation.*

---

| | |
|---|---|
| **Signature of the Students** | _____________________________ |
| **Signature of the Guide(s)** | _____________________________ |
