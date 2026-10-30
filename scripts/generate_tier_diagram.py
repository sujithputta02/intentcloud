#!/usr/bin/env python3
"""
Generate a publication-grade Three-Tier Architecture diagram for IntentCloud.
Outputs both PNG (300 DPI) and PDF vector formats.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def generate_three_tier_diagram():
    fig, ax = plt.subplots(figsize=(11.0, 7.8), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(100, 0)  # Inverted Y: 0 is top, 100 is bottom

    # Palette
    c_tier1_bg = "#F0F9FF"
    c_tier1_border = "#0284C7"
    c_tier1_hdr = "#0369A1"

    c_tier2_bg = "#F0FDF4"
    c_tier2_border = "#16A34A"
    c_tier2_hdr = "#15803D"

    c_tier3_bg = "#FFFBEB"
    c_tier3_border = "#D97706"
    c_tier3_hdr = "#B45309"

    c_card_bg = "#FFFFFF"
    c_card_border = "#CBD5E1"
    c_text_dark = "#0F172A"
    c_text_muted = "#334155"

    # ==========================================
    # 1. TOP HEADER BANNER
    # ==========================================
    hdr_box = patches.FancyBboxPatch((3, 2), 94, 7, boxstyle="round,pad=0.5", facecolor="#0F172A", edgecolor="#1E293B", lw=1.2)
    ax.add_patch(hdr_box)
    ax.text(50, 4.5, "IntentCloud: Three-Tier System Architecture & Communication Dataflow", ha="center", va="center", fontsize=11, fontweight="bold", color="#FFFFFF")
    ax.text(50, 7.2, "On-Device Neural Document Search · Local Hybrid Embeddings · Calibrated Gate · Zero-Trust Transport", ha="center", va="center", fontsize=7.8, color="#94A3B8")

    # ==========================================
    # 2. TIER 1: PRESENTATION & USER INTERACTION
    # ==========================================
    t1_box = patches.FancyBboxPatch((3, 11), 94, 23, boxstyle="round,pad=0.8", facecolor=c_tier1_bg, edgecolor=c_tier1_border, lw=1.5)
    ax.add_patch(t1_box)

    # Tier 1 Banner
    t1_hdr = patches.FancyBboxPatch((4, 11.8), 92, 4.2, boxstyle="round,pad=0.4", facecolor=c_tier1_hdr, edgecolor=c_tier1_border, lw=1.0)
    ax.add_patch(t1_hdr)
    ax.text(50, 13.9, "TIER 1: PRESENTATION & USER INTERACTION TIER  [Next.js 14 · React 19 · TypeScript · Tailwind CSS]",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#FFFFFF")

    # 4 Components in Tier 1
    t1_cards = [
        ("Natural Language Query UI",
         ["• Real-time debounced search bar",
          "• Dynamic category filter pills",
          "• Client query caching & history",
          "• Low-latency reactive state"],
         5, 21.5),
        ("Drag-and-Drop Ingestion",
         ["• Multi-format drop zone (PDF/DOCX/TXT)",
          "• Client-side format & size guard",
          "• Asynchronous batch upload tracker",
          "• Live indexing progress telemetry"],
         28.5, 21.5),
        ("Attribution & Citations",
         ["• Confidence score visual badges",
          "• Matched sentence verbatim excerpts",
          "• Multi-document comparative view",
          "• Low-confidence warning alerts"],
         52, 21.5),
        ("Zero-Trust File Delivery",
         ["• Authentic byte-stream download",
          "• In-browser instant PDF preview",
          "• Remote access via TLS reverse proxy",
          "• Cryptographic SHA integrity check"],
         75.5, 21.5)
    ]

    for title, bullets, x, w in t1_cards:
        card = patches.FancyBboxPatch((x, 17.2), w, 15.5, boxstyle="round,pad=0.5", facecolor=c_card_bg, edgecolor=c_card_border, lw=1.0)
        ax.add_patch(card)
        ax.text(x + w/2, 19.3, title, ha="center", va="center", fontsize=7.8, fontweight="bold", color=c_tier1_hdr)
        ax.plot([x + 1.5, x + w - 1.5], [20.8, 20.8], color="#E2E8F0", lw=0.8)
        b_y = 22.8
        for bullet in bullets:
            ax.text(x + 1.2, b_y, bullet, ha="left", va="center", fontsize=6.3, color=c_text_muted)
            b_y += 2.5

    # ==========================================
    # INTER-TIER PROTOCOL 1 (Tier 1 <-> Tier 2)
    # ==========================================
    p1_box = patches.FancyBboxPatch((18, 35.2), 64, 4.4, boxstyle="round,pad=0.4", facecolor="#FEF3C7", edgecolor="#F59E0B", lw=1.2)
    ax.add_patch(p1_box)
    ax.text(50, 37.4, "◄──  REST API / JSON Payloads & Byte Streams (HTTP/2 localhost:8000 / Cloudflare Zero-Trust Tunnel)  ──►",
            ha="center", va="center", fontsize=7.4, fontweight="bold", color="#92400E")

    # Down/Up Arrows
    for arrow_x in [10, 50, 90]:
        ax.annotate("", xy=(arrow_x, 40.5), xytext=(arrow_x, 34.2),
                    arrowprops=dict(arrowstyle="<->", color="#0284C7", lw=1.5))

    # ==========================================
    # 3. TIER 2: COGNITIVE PROCESSING & ORCHESTRATION
    # ==========================================
    t2_box = patches.FancyBboxPatch((3, 41), 94, 32, boxstyle="round,pad=0.8", facecolor=c_tier2_bg, edgecolor=c_tier2_border, lw=1.5)
    ax.add_patch(t2_box)

    t2_hdr = patches.FancyBboxPatch((4, 41.8), 92, 4.2, boxstyle="round,pad=0.4", facecolor=c_tier2_hdr, edgecolor=c_tier2_border, lw=1.0)
    ax.add_patch(t2_hdr)
    ax.text(50, 43.9, "TIER 2: COGNITIVE PROCESSING & SERVICE ORCHESTRATION TIER  [FastAPI · Asynchronous ASGI · PyTorch ML Runtime]",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#FFFFFF")

    # 3 Cards in Tier 2
    t2_cards = [
        ("Ingestion & Dual Vector Encoding",
         ["• PyMuPDF & python-docx native stream parsing",
          "• Tesseract OCR automatic fallback (<100 chars)",
          "• Sliding-window chunker (C=1200, O=200 chars)",
          "• Dense: all-MiniLM-L6-v2 (384-dim embeddings)",
          "• Sparse: MurmurHash3 feature hashing (D=10^6)",
          "• SHA-256 fingerprinting & cosine deduplication"],
         5, 28.5),
        ("Intent Analysis & Hybrid Search",
         ["• Local Ollama runtime (llama3.2:1b, 4-bit quant)",
          "• Query intent classification & synonym expansion",
          "• Parallel dense semantic search (Cosine top-N=20)",
          "• Parallel sparse lexical search (Dot product top-N=20)",
          "• Reciprocal Rank Fusion (RRF, constant k=60)",
          "• Candidate deduplication & pool pruning (N <= 25)"],
         35.75, 28.5),
        ("Cross-Attention Reranking & Gating",
         ["• Cross-Encoder: ms-marco-MiniLM-L-6-v2",
          "• Full token-level cross-attention score s(q, c)",
          "• Calibrated Confidence Gate threshold (tau = 0.40)",
          "• Out-of-Distribution (OOD) active abstention",
          "• Sentence-level provenance & attribution span",
          "• Performance telemetry (P95 latency tracking)"],
         66.5, 28.5)
    ]

    for title, bullets, x, w in t2_cards:
        card = patches.FancyBboxPatch((x, 47.2), w, 24.5, boxstyle="round,pad=0.5", facecolor=c_card_bg, edgecolor=c_card_border, lw=1.0)
        ax.add_patch(card)
        ax.text(x + w/2, 49.3, title, ha="center", va="center", fontsize=8.0, fontweight="bold", color=c_tier2_hdr)
        ax.plot([x + 1.5, x + w - 1.5], [50.8, 50.8], color="#E2E8F0", lw=0.8)
        b_y = 53.0
        for bullet in bullets:
            ax.text(x + 1.2, b_y, bullet, ha="left", va="center", fontsize=6.6, color=c_text_muted)
            b_y += 3.0

    # Intra-tier Pipeline Arrows between cards
    ax.annotate("", xy=(35.2, 59.5), xytext=(33.8, 59.5),
                arrowprops=dict(arrowstyle="->", color="#15803D", lw=1.6))
    ax.annotate("", xy=(66.0, 59.5), xytext=(64.5, 59.5),
                arrowprops=dict(arrowstyle="->", color="#15803D", lw=1.6))

    # ==========================================
    # INTER-TIER PROTOCOL 2 (Tier 2 <-> Tier 3)
    # ==========================================
    p2_box = patches.FancyBboxPatch((20, 74.2), 60, 4.4, boxstyle="round,pad=0.4", facecolor="#EDE9FE", edgecolor="#8B5CF6", lw=1.2)
    ax.add_patch(p2_box)
    ax.text(50, 76.4, "◄──  In-Memory C ABI / Direct NVMe File I/O Streams (Air-Gapped, Zero Network Latency)  ──►",
            ha="center", va="center", fontsize=7.4, fontweight="bold", color="#5B21B6")

    # Down/Up Arrows
    for arrow_x in [10, 50, 90]:
        ax.annotate("", xy=(arrow_x, 79.5), xytext=(arrow_x, 73.2),
                    arrowprops=dict(arrowstyle="<->", color="#16A34A", lw=1.5))

    # ==========================================
    # 4. TIER 3: EMBEDDED MEMORY & STORAGE
    # ==========================================
    t3_box = patches.FancyBboxPatch((3, 80), 94, 18, boxstyle="round,pad=0.8", facecolor=c_tier3_bg, edgecolor=c_tier3_border, lw=1.5)
    ax.add_patch(t3_box)

    t3_hdr = patches.FancyBboxPatch((4, 80.8), 92, 4.2, boxstyle="round,pad=0.4", facecolor=c_tier3_hdr, edgecolor=c_tier3_border, lw=1.0)
    ax.add_patch(t3_hdr)
    ax.text(50, 82.9, "TIER 3: EMBEDDED MEMORY & LOCAL STORAGE TIER  [Local NVMe Storage · Complete Air-Gap Sovereignty]",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#FFFFFF")

    # 3 Cards in Tier 3
    t3_cards = [
        ("Embedded Vector Database",
         ["• Embedded Qdrant instance (path: ./qdrant_storage/)",
          "• SQLite transactional store with Write-Ahead Logging (WAL)",
          "• HNSW index for dense vectors + sparse inverted index",
          "• Zero external daemon required; runs entirely in-process"],
         5, 28.5),
        ("Local Document Vault",
         ["• Air-gapped file repository (path: ./uploads/)",
          "• Preserves exact byte structure of source documents",
          "• Cryptographic SHA-256 integrity validation",
          "• Tamper-proof local on-premise storage"],
         35.75, 28.5),
        ("Document Registry & Metadata",
         ["• Lightweight document catalog (path: metadata.json)",
          "• Track original filenames, mime-types, and timestamps",
          "• Document versioning & update lineage history",
          "• Rapid cold-start index restoration on daemon boot"],
         66.5, 28.5)
    ]

    for title, bullets, x, w in t3_cards:
        card = patches.FancyBboxPatch((x, 86.0), w, 11.2, boxstyle="round,pad=0.5", facecolor=c_card_bg, edgecolor=c_card_border, lw=1.0)
        ax.add_patch(card)
        ax.text(x + w/2, 87.8, title, ha="center", va="center", fontsize=8.0, fontweight="bold", color=c_tier3_hdr)
        ax.plot([x + 1.5, x + w - 1.5], [89.1, 89.1], color="#E2E8F0", lw=0.8)
        b_y = 90.8
        for bullet in bullets:
            ax.text(x + 1.2, b_y, bullet, ha="left", va="center", fontsize=6.4, color=c_text_muted)
            b_y += 2.2

    plt.tight_layout()

    out_png = Path("/Users/sujithputta/Projects/Intentcloud/fig_three_tier_architecture.png")
    out_pdf = Path("/Users/sujithputta/Projects/Intentcloud/fig_three_tier_architecture.pdf")

    plt.savefig(out_png, format="png", bbox_inches="tight", dpi=300)
    plt.savefig(out_pdf, format="pdf", bbox_inches="tight")
    plt.close()
    print(f"Generated {out_png} and {out_pdf} successfully.")

if __name__ == "__main__":
    generate_three_tier_diagram()
