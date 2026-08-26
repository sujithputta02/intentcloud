# Test Corpus Plan
**Week 4 Deliverable (Due: 29 August 2026)**  
**Owner:** Mokshith Karnati  
**Target Corpus Size:** 150-200 files  
**Coverage:** 8 semantic topic categories

---

## 1. Corpus Overview

The test corpus is designed to:
- **Stress-test** the Phase 1-3 pipeline (extract → embed → index → search)
- **Validate** OCR fallback on scanned PDFs
- **Evaluate** duplicate detection (0.95 similarity threshold)
- **Enable** ground-truth evaluation of search quality
- **Provide** diverse document types and topics for realistic testing

**Total Target:** 150-200 files across 8 topics

---

## 2. Topic Categories & Distribution

| Topic Category | File Count | Examples | Rationale |
|---|---|---|---|
| **Kafka & Streaming** | 25 files | Performance guides, architecture docs, tutorials | Core use case from PRD |
| **Microservices** | 25 files | Design patterns, deployment, monitoring | Paired with Kafka |
| **Thesis & Research** | 25 files | Academic papers, research notes, drafts | Knowledge work |
| **Machine Learning** | 25 files | ML papers, model docs, implementation guides | Technical depth |
| **Information Retrieval** | 25 files | Search papers, ranking, vector DB docs | Domain-specific |
| **Business Reports** | 20 files | Executive summaries, quarterly reports, analyses | Corporate documents |
| **Project Documentation** | 20 files | API specs, architecture, requirements | Development context |
| **Cloud & DevOps** | 15 files | AWS/Azure guides, CI/CD, infrastructure | Cloud operations |
| **TOTAL** | **180 files** | Mix of PDF, DOCX, TXT | Balanced coverage |

---

## 3. Document Format Distribution

```
PDF (60% of corpus)
├─ Native digital PDFs (85% of PDFs)
│  └─ Easy text extraction, normal pipeline
└─ Scanned/image-only PDFs (15% of PDFs)
   └─ Requires OCR fallback (3-4 scanned PDFs per topic × 8 topics ≈ 24-32)

DOCX (25% of corpus)
├─ Standard Microsoft Word documents
└─ Text extraction via python-docx

TXT (15% of corpus)
├─ Plain text files
└─ Minimal extraction needed
```

**Exact distribution for 180 files:**
- PDF: ~108 files (65 native + ~15-20 scanned)
- DOCX: ~45 files
- TXT: ~27 files

---

## 4. Scanned PDF & OCR Testing

**Target:** 3-4 scanned/image-only PDFs per topic (24-32 total)

**Scanned PDFs include:**
- Single-column academic papers (PDF scans)
- Multi-page business reports (image extraction)
- Historical documents (black & white scans)
- Mixed quality (clear + degraded)

**OCR Fallback Testing:**
- PyMuPDF extraction yields <100 characters → triggers Tesseract
- Tesseract processes rendered pages at 2x zoom
- Output verified: text extracted correctly despite scan quality

---

## 5. Duplicate & Near-Duplicate Testing

**Target:** 2 near-duplicate pairs (4 files total)

**Near-duplicate scenarios:**
1. **Report v1 vs v2:** Same content, minor edits (cosine_similarity ≈ 0.96-0.98)
   - Should trigger duplicate detection (≥0.95 threshold)

2. **Paper draft vs final:** Similar sections, different conclusion (cosine_similarity ≈ 0.93-0.96)
   - May or may not trigger (boundary testing)

**Expected behavior:**
- First file: uploaded successfully, indexed
- Second file: duplicate detection flags it, logged as warning, NOT indexed
- User sees: "File flagged as duplicate. Skipping indexing."

---

## 6. Ground Truth Evaluation Queries

**File:** `docs/EVAL_QUERY_GROUND_TRUTH.json`

40 diverse natural language queries with verified expected results:

```json
{
  "eval_queries": [
    {
      "id": "query_001",
      "query": "Find documents about Kafka performance optimization",
      "expected_files": ["kafka_perf_tuning.pdf", "streaming_benchmarks.docx"],
      "intent_type": "find",
      "keywords": ["Kafka", "performance", "optimization"]
    },
    {
      "id": "query_002",
      "query": "Where is the thesis draft about neural networks?",
      "expected_files": ["thesis_neural_networks_v2.pdf"],
      "intent_type": "locate",
      "keywords": ["thesis", "neural networks"]
    },
    {
      "id": "query_003",
      "query": "Show me documents comparing microservices patterns",
      "expected_files": ["microservices_patterns_comparison.docx", "service_mesh_guide.pdf"],
      "intent_type": "compare",
      "keywords": ["microservices", "patterns", "comparison"]
    },
    {
      "id": "query_004",
      "query": "Find research on embedding models and similarity search",
      "expected_files": ["embeddings_survey.pdf", "semantic_search_paper.pdf"],
      "intent_type": "find",
      "keywords": ["embeddings", "similarity search", "models"]
    },
    {
      "id": "query_005",
      "query": "AWS deployment best practices and security",
      "expected_files": ["aws_deployment_guide.pdf", "cloud_security_handbook.docx"],
      "intent_type": "find_guide",
      "keywords": ["AWS", "deployment", "security"]
    },
    {
      "id": "query_006",
      "query": "Q3 business performance and revenue metrics",
      "expected_files": ["q3_2026_report.pdf", "quarterly_summary.xlsx"],
      "intent_type": "find",
      "keywords": ["Q3", "revenue", "performance"]
    },
    {
      "id": "query_007",
      "query": "CI/CD pipeline configuration and best practices",
      "expected_files": ["cicd_setup_guide.docx", "pipeline_automation.md"],
      "intent_type": "guide",
      "keywords": ["CI/CD", "pipeline", "automation"]
    },
    {
      "id": "query_008",
      "query": "Machine learning model evaluation metrics",
      "expected_files": ["ml_evaluation_guide.pdf", "model_metrics_paper.txt"],
      "intent_type": "reference",
      "keywords": ["machine learning", "evaluation", "metrics"]
    }
    // ... 32 more queries (total 40)
  ]
}
```

**Query Distribution:**
- Topic-specific: 20 queries (5 per major topic)
- Cross-topic: 10 queries (multiple file results)
- Edge cases: 10 queries (ambiguous, time-constrained, etc.)

---

## 7. Corpus Storage Layout

```
intentcloud-api/test_corpus/
├── kafka/
│   ├── kafka_101_basics.pdf
│   ├── kafka_performance_tuning.pdf
│   ├── kafka_stream_processing.docx
│   ├── kafka_scanned_paper_1.pdf
│   └── ... (25 files total)
│
├── microservices/
│   ├── microservices_patterns.pdf
│   ├── docker_kubernetes_guide.docx
│   ├── service_mesh_istio.pdf
│   └── ... (25 files total)
│
├── thesis_research/
│   ├── thesis_draft_v1.pdf
│   ├── thesis_draft_v2.pdf  [near-duplicate of v1]
│   ├── neural_networks_survey.pdf
│   └── ... (25 files total)
│
├── machine_learning/
│   ├── ml_fundamentals.pdf
│   ├── deep_learning_handbook.docx
│   ├── transformer_paper.pdf
│   └── ... (25 files total)
│
├── information_retrieval/
│   ├── retrieval_models_survey.pdf
│   ├── ranking_algorithms.docx
│   ├── vector_db_comparison.txt
│   └── ... (25 files total)
│
├── business_reports/
│   ├── q3_2026_summary.pdf
│   ├── annual_revenue_report.docx
│   ├── market_analysis.pdf
│   └── ... (20 files total)
│
├── project_documentation/
│   ├── api_specification.pdf
│   ├── architecture_design.docx
│   ├── requirements.txt
│   └── ... (20 files total)
│
└── cloud_devops/
    ├── aws_deployment_guide.pdf
    ├── kubernetes_setup.docx
    ├── ci_cd_pipeline.txt
    └── ... (15 files total)
```

---

## 8. Corpus Assembly Process

### Timeline (Week 4)

| Date | Task | Owner | Status |
|---|---|---|---|
| Aug 26-27 | Source documents from team/public repos | Mokshith | ⏳ |
| Aug 27-28 | Organize by topic & format (PDF/DOCX/TXT) | Mokshith | ⏳ |
| Aug 28 | Generate ground truth queries & expected results | Mokshith + Sujith | ⏳ |
| Aug 29 | Final validation: 150-200 files ready for indexing | Mokshith | ⏳ |

### Document Sources

- **Academic papers:** arXiv, Google Scholar (open access)
- **Technical docs:** GitHub wikis, official documentation, tutorials
- **Business reports:** Public company filings, sample reports
- **Project docs:** Internal design docs, API specs
- **Scanned PDFs:** Historical papers, archival documents

---

## 9. Corpus Validation Checklist

- [ ] Total file count: 150-200 ✓
- [ ] Topic distribution: ~25 files per major category
- [ ] Format mix: ~60% PDF, ~25% DOCX, ~15% TXT
- [ ] Scanned PDFs: 3-4 per topic (20-30 total)
- [ ] Near-duplicates: 2 pairs (4 files) for testing
- [ ] Ground truth: 40 queries with verified expected results
- [ ] File naming: Descriptive, topic-prefixed (e.g., `kafka_perf_tuning.pdf`)
- [ ] Metadata: README per topic with file descriptions
- [ ] Storage: All files in `intentcloud-api/test_corpus/` on local disk
- [ ] Ready for upload: Validated file integrity (checksums if needed)

---

## 10. Week 4 Testing Plan

### Phase 1-3 Pipeline Validation

1. **Bulk upload test:** Upload all 180 files via `/upload` endpoint
   - Verify: All files saved, background processing triggered
   - Check: metadata.json updated with all file_ids

2. **Extraction validation:** Verify text extracted from all formats
   - PDF: PyMuPDF extraction + OCR fallback for scanned
   - DOCX: python-docx extraction
   - TXT: Direct read
   - Check: Extract logs show successful extraction for 180 files

3. **Duplicate detection:** Verify near-duplicates flagged
   - Upload thesis v1 → indexed successfully
   - Upload thesis v2 → duplicate detection flags (cosine_similarity ≥ 0.95)
   - Check: Warning logged, v2 NOT indexed (only v1 in Qdrant)

4. **Embedding & indexing:** Verify all vectors in Qdrant
   - Expected vectors: ~180 files × avg sentences per file ≈ 3000-5000 vectors
   - Check: `/stats` endpoint shows correct counts

5. **Ground truth evaluation:** Run 40 queries, verify results
   - For each query: Run `/search`, check top-5 results
   - Validate: Expected files appear in results (rank may vary)
   - Measure: Precision@5 for each query

### Expected Outcomes

- **Week 4 end:** All 180 files indexed (minus 1 duplicate flagged)
- **Qdrant collection:** ~3000-5000 vectors ready for Phase 4 hybrid search
- **Ground truth:** 40 queries validated, baseline established for Phase 4 hybrid improvements
- **Review-1 gate:** "Phase 1-3 pipeline proven on diverse, realistic corpus"

---

## 11. Phase 4 Handoff (Week 5)

**Corpus becomes test set for Phase 4 hybrid search implementation:**
- **Baseline:** Dense-only search quality (current/Phase 3)
- **Phase 4 target:** Hybrid search (dense + sparse + RRF) should improve precision@5
- **Evaluation:** Re-run 40 ground truth queries, compare Phase 3 vs Phase 4 results

---

**Document Status:** Ready for corpus assembly (Week 4, due 29 Aug)  
**Total Files:** Target 150-200 (plan for 180)  
**Topics:** 8 categories with balanced distribution  
**Ground Truth:** 40 diverse queries for evaluation  
**Next Step:** Assemble corpus by Aug 29, validate pipeline, prepare for Review-1
