# IntentCloud Test Corpus (Week 4 Starter Set)

Starter regression corpus for Phase 1–3 pipeline validation. Expand toward 150–200 files per `docs/week4_deliverables/TEST_CORPUS_PLAN.md`.

## Layout

```
test_corpus/
├── ground_truth.json          # Evaluation queries + duplicate test pairs
├── kafka/                     # Kafka & streaming
├── microservices/
├── thesis_research/           # Includes near-duplicate pair (v1 vs v2)
├── machine_learning/
├── information_retrieval/
├── business_reports/
├── project_documentation/
└── cloud_devops/
```

## Run regression tests

1. Start the API: `cd intentcloud-api && python main.py`
2. Run: `./RUN_WEEK4_REGRESSION.sh` from the repo root

The script uploads every corpus file, waits for indexing, verifies duplicate detection, and runs ground-truth search queries.
