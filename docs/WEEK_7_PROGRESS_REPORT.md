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
| **Week No** | 7 |
| **Date Range** | 14/09/2026 to 19/09/2026 |
| **Department** | Computer Science and Technology |
| **Team Number** | Team 3 |
| **Team Members (Names & USN)** | Putta Sujith — ENG23CT0058<br>K Vikas Aneesh Reddy — ENG23CT0052<br>Karnati Mokshith — ENG23CT0053 |
| **Guide** | Dr. Ramandeep Kaur |
| **Project Title** | IntentCloud — Intent-Aware Cognitive Cloud Memory System |

---

## Work Carried Out by the Team

- **High-Fidelity macOS Finder Interface Realization:**
  - Redesigned and overhauled `MacFinder.tsx` to match the exact neumorphic glassmorphism design specification from the target UI reference.
  - Implemented macOS window header controls with traffic lights (Close, Minimize, Zoom), navigation chevron, and quick action toolbar (`Share`, `Quick Look`, `Tags`, Spotlight `Search`).
  - Added the translucent left sidebar with crisp icons for *All My Files*, *iCloud Drive*, *Applications*, *Desktop*, *Documents* (active pill state), and *Downloads*.
  - Built the signature asymmetric visual preview cards:
    - `aerial-01`: Azure ocean video tile with play button badge and bold overlay title.
    - `index`: Dark syntax-highlighted code editor tile displaying `<html>` and `<meta>` tags.
    - `canyon`: Warm sandstone canyon photography preview.
    - `final soundtrack`: Frosted lilac audio card with interactive play/pause and dynamic multi-bar audio waveform.
    - `jellyfish`: Dark underwater tile with bioluminescent glow and Adobe Photoshop (`Ps`) badge.
    - `project files`: Tall composite stacked album card displaying multiple photo previews.
    - `project`: Emerald design card with diamond badge and mobile smartphone UI mockup.
  - Added toggleable integration between the curated showcase cards and real uploaded cloud documents with Quick Look modal and file download triggers.
- **Visual Intelligence & Structured Preview Integration:**
  - Integrated visual intelligence preview modal to inspect extracted entities, OCR content, and semantic embeddings directly from the Finder.
  - Fixed cross-encoder reranker inference and confidence score formatting for stable edge serving.
- **Hardware Staging for College Lab Deployment:**
  - Pre-packaged deployment scripts and system configuration ahead of hands-on college lab assembly (Raspberry Pi OS 64-bit flashing, headless SSH, and Qdrant index migration).

---

## Individual Contribution

| Name of the Student | Contribution |
|---|---|
| **Putta Sujith** (ENG23CT0058) | • Implemented the exact-spec macOS Finder interface overhaul in `MacFinder.tsx` — window chrome, traffic light actions, and responsive layout.<br>• Designed the visual card preview system (`aerial-01` ocean video, dark code card, and audio waveform player).<br>• Integrated Quick Look preview modal connections and verified Next.js 16 production build type-safety.<br>• Authored the Week 7 Progress Report and updated project tracking documentation. |
| **K Vikas Aneesh Reddy** (ENG23CT0052) | • Prepared the edge migration checklist and headless environment configs for Raspberry Pi 3B college lab assembly.<br>• Audited Qdrant snapshot serialization and storage paths for cross-platform migration between laptop and ARM edge node.<br>• Verified static file serving endpoints and original document download routes in FastAPI. |
| **Karnati Mokshith** (ENG23CT0053) | • Tested the dual-mode Finder switcher (Curated Showcase vs Real User Files) across dark and light modes.<br>• Verified Spotlight search filtering and interactive audio waveform toggles.<br>• Prepared the Week 7 expanded benchmark query set for multi-graded relevance testing ahead of Review-3. |

---

## Work Planned for the Following Week (Week 8)

- Complete Raspberry Pi 3B OS flashing and headless network configuration in the college department lab.
- Mount local storage and migrate `qdrant_storage/` snapshot onto the Pi.
- Install and configure `cloudflared` daemon on the Pi to expose the API and web UI over a public HTTPS Zero-Trust URL.
- Execute live search demo served directly from the Pi for the Review-3 gate ($\ge 50\%$ working threshold).

---

## Major Bottlenecks / Challenges Resolved

- **Exact UI Alignment:** Replaced generic file list view with an exact 1:1 neumorphic macOS Finder canvas featuring custom tile visualizers (video, syntax code, audio waveform, composite album) while maintaining full reactivity with live backend files.
- **Build & Type Safety:** Aligned modal payload interfaces (`PreviewableFile`) with Next.js Turbopack build checks to ensure production compilation with zero errors.

---

## Percentage Work Completed

**65%**

*PRD Week 7 target is **65%** (Week 6: 54% → Week 7: 65%). Completed this week: Exact macOS Finder UI redesign and implementation without outer container, live connection to backend folders and files, working folder creation modal, direct file uploads into directories, Quick Look modal linkage, and college lab deployment automation (`setup_pi.sh`). Ready for hands-on college lab edge hardware setup in Week 8.*

---

| | |
|---|---|
| **Signature of the Students** | _____________________________ |
| **Signature of the Guide(s)** | _____________________________ |
