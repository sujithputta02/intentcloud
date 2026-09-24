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

- Placed order for Raspberry Pi aluminum heatsink and active cooling case to ensure thermal stability under neural search workloads.
- Flashed 64-bit Raspberry Pi OS Lite onto 64GB MicroSD card, configured headless SSH networking over Ethernet (`192.168.2.2`), and configured Mac Internet Sharing.
- Created and activated a 2GB swapfile (expanding total available memory to 2.9GB) to prevent kernel OOM during edge operations.
- Synced the IntentCloud backend codebase, document uploads, and Qdrant vector index from laptop to Raspberry Pi over SSH.
- Installed ARM64 build tools, system dependencies, and installed the `cloudflared` binary for Zero-Trust tunneling.
- Implemented and integrated the macOS Finder web interface with live backend folder creation, file uploads, and preview cards.
- Restricted document upload and embedding runs to lightweight test batches to prevent board overheating while awaiting the cooling kit.
- Refined and proofread IEEE Research Paper 1 (`docs/paper/ieee_paper_1.tex`) based on guide review feedback.
- Began automated Python environment installation (`requirements.txt`) and systemd service configuration on the edge device.

---

## Individual Contribution

| Name of the Student | Contribution |
|---|---|
| **Putta Sujith** (ENG23CT0058) | • Outlined the core technical deliverables for Review-3 and refined IEEE Paper 1 mathematical formulation sections.<br>• Overhauled the frontend into a macOS Finder interface with folder navigation and direct file uploads.<br>• Configured headless SSH keys and Ethernet network bridging between Mac and the Raspberry Pi.<br>• Created the edge systemd service configuration (`intentcloud.service`) and automated deployment script. |
| **K Vikas Aneesh Reddy** (ENG23CT0052) | • Prepared edge hardware benchmark criteria for Review-3 and verified IEEE Paper 1 architecture diagrams and citations.<br>• Ordered the aluminum heatsink and cooling fan case for the Raspberry Pi 3B board.<br>• Configured memory swap expansion (2.9GB total) and synced the Qdrant storage snapshot to the Pi filesystem.<br>• Installed and verified the ARM64 `cloudflared` package on the Raspberry Pi for public endpoint access. |
| **Karnati Mokshith** (ENG23CT0053) | • Tested lightweight sample document uploads and folder creation flows against the API to prevent board heating while awaiting cooling accessories.<br>• Verified Quick Look file preview modal integration and visual preview card rendering in the web interface.<br>• Monitored network transfer rates and package dependency extraction during Pi provisioning.<br>• Validated API error handling and file download endpoint stability on local and LAN connections. |

---

## Work Planned for the Following Week (Week 8)

- Assemble the aluminum heatsink and active cooling fan case on the Raspberry Pi 3B upon delivery.
- Complete Python virtual environment setup and start the background `intentcloud.service` systemd daemon on the Pi.
- Launch `cloudflared` tunnel to expose the edge API and Finder interface through a public Zero-Trust HTTPS URL (`https://*.trycloudflare.com`).
- Expand the document corpus to 100+ files across technical domains and run full ingestion under active cooling.
- Incorporate secondary guide review feedback into IEEE Paper 1 ahead of final submission.
- Execute live retrieval query demonstrations from laptop and mobile over LAN and Cloudflare Tunnel to fulfill all Review-3 evaluation deliverables ($\ge 50\%$ gate).

---

## Percentage Work Completed

**62%**

*PRD V1.0/V2.0 Week 7 target is **65%** (range: 60% → 70%; Week 6: 54% → Week 7: 62%). Completed this week (+8%): Aluminum heatsink and active cooling case ordered, 64-bit Raspberry Pi OS flashed and networked via headless SSH (`192.168.2.2`), swap expanded to 2.9GB, backend codebase and Qdrant index synced, `cloudflared` ARM64 binary installed, macOS Finder interface implemented, and IEEE Paper 1 refined based on guide feedback. Pending (~3 points): Cooling kit arrival & assembly, full document embedding without thermal throttling, and active tunnel daemon launch — carried into Week 8. Fully satisfies the upcoming Review-3 $\ge 50\%$ university threshold.*

---

| | |
|---|---|
| **Signature of the Students** | _____________________________ |
| **Signature of the Guide(s)** | _____________________________ |
