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
| **Week No** | 6 |
| **Date Range** | 07/09/2026 to 12/09/2026 |
| **Department** | Computer Science and Technology |
| **Team Number** | Team 3 |
| **Team Members (Names & USN)** | Putta Sujith — ENG23CT0058<br>K Vikas Aneesh Reddy — ENG23CT0052<br>Karnati Mokshith — ENG23CT0053 |
| **Guide** | Dr. Ramandeep Kaur |
| **Project Title** | IntentCloud — Intent-Aware Cognitive Cloud Memory System |

---

## Work Carried Out by the Team

- Prepared the Review-2 presentation and live demonstration script for the full V1.0 pipeline on local laptop hardware.
- Validated all four demo phases: document upload, hybrid search, cross-encoder reranking, and out-of-domain abstention.
- Finalized IEEE Research Paper 1 in IEEEtran LaTeX and plain-text submission formats.
- Re-ran the 35-query benchmark and achieved 90.6% Top-1 accuracy, 0.953 MRR, and 100% negative-query rejection.
- Calibrated the confidence threshold (τ = 0.40) for the no-match fallback across the search pipeline.
- Procured and verified Raspberry Pi 3B board, power supply, microSD card, and all other required components; only heatsink and cooling kit remain to be ordered in Week 7.

---

## Individual Contribution

| Name of the Student | Contribution |
|---|---|
| **Putta Sujith** (ENG23CT0058) | • Prepared and structured the Review-2 presentation slides — architecture overview, four-phase pipeline, benchmark table, and live demo script.<br>• Authored the Methodology and Mathematical Formulation sections of the IEEE research paper (RRF formulation, k=60, logistic sigmoid confidence scoring).<br>• Formatted the IEEE LaTeX manuscript and finalized the plain-text submission package for guide review.<br>• Calibrated the confidence threshold (τ = 0.40) and validated cross-platform inference acceleration (Apple Silicon MPS / CUDA / CPU fallback). |
| **K Vikas Aneesh Reddy** (ENG23CT0052) | • Prepared the Raspberry Pi 3B hardware showcase for the Review-2 panel — unboxed board, power supply, microSD card, and other procured accessories.<br>• Co-authored the System Architecture, Database Design, and Embedded Qdrant sections of the IEEE research paper.<br>• Validated the empirical benchmark comparison table, author affiliations, and IEEE bibliography entries in the paper.<br>• Audited backend service health, Qdrant collections, and file storage integrity ahead of the demo. |
| **Karnati Mokshith** (ENG23CT0053) | • Polished the Next.js search and upload pages — search mode switcher, top-3 result cards, matched citation highlights, and no-match banner.<br>• Re-ran the 35-query benchmark evaluation and recorded Top-1 accuracy, MRR, and latency numbers for the presentation.<br>• Fixed the home page search bar layout and API proxy integration for a stable live demo.<br>• Tested the full upload-to-search demo flow end-to-end before Review-2. |

---

## Work Planned for the Following Week

- Place order for Raspberry Pi heatsink and active cooling fan; flash Raspberry Pi OS with headless SSH once the cooling kit arrives.
- Install Python 3.11, FastAPI, and Qdrant on the Pi; migrate the Qdrant index and uploaded files from laptop via scp.
- Confirm hybrid search runs end-to-end on the Pi and is reachable from the laptop over LAN.
- Serve the statically-exported Next.js UI from the Pi alongside the FastAPI backend.
- Install `cloudflared` on the Pi and expose the UI and API via a public HTTPS Cloudflare Tunnel URL.
- Implement the file download endpoint so result cards serve the original file from Pi/USB storage.
- Run a full upload → search → download smoke test through the public tunnel and begin the Review-3 slide deck.

---

## Major Bottlenecks / Challenges Resolved

- **Hardware Bring-Up Staging:** Raspberry Pi 3B and all other components were procured; only heatsink and cooling kit are pending order. OS setup and edge migration were deferred to Week 7. Review-2 demo ran on laptop with procured Pi hardware shown to the panel.
- **IEEE Template Compliance:** Ensured strict IEEEtran formatting (two-column layout, formal author blocks, mathematical notation, IEEE-style numbered bibliography) to meet submission standards.

---

## Percentage Work Completed

**54%**

*PRD Week 6 target is **58%** (Week 5: 48% → Week 6: 58%). Completed this week: Review-2 presentation and demo, IEEE paper, benchmark re-validation, and Raspberry Pi 3B hardware procurement (board, power supply, microSD, and accessories). Pending (~4 points): heatsink and cooling kit order, Pi OS flash, Qdrant/FastAPI migration, and LAN end-to-end demo — carried to Week 7. Still exceeds the Review-2 ≥25% requirement.*

---

| | |
|---|---|
| **Signature of the Students** | _____________________________ |
| **Signature of the Guide(s)** | _____________________________ |
