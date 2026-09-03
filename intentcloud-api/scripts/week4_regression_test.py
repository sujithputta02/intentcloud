#!/usr/bin/env python3
"""
Week 4 regression test: upload → extract → embed → store → dense search.

Requires the API running at http://localhost:8000 (default).

Usage:
    cd intentcloud-api
    python scripts/week4_regression_test.py

Options:
    --api-url URL       API base URL (default: http://localhost:8000)
    --corpus-dir PATH   Corpus root (default: ./test_corpus)
    --skip-upload       Only run search queries (corpus already indexed)
    --processing-wait   Seconds to wait after uploads (default: 30)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}
DEFAULT_API = "http://localhost:8000"


def log_ok(message: str) -> None:
    print(f"  ✓ {message}")


def log_fail(message: str) -> None:
    print(f"  ✗ {message}")


def check_health(api_url: str) -> bool:
    print("\n[1/4] Health check")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "healthy":
            log_fail(f"API unhealthy: {data}")
            return False
        log_ok("API healthy")
        return True
    except requests.RequestException as exc:
        log_fail(f"Cannot reach API at {api_url}: {exc}")
        return False


def load_ground_truth(corpus_dir: Path) -> dict:
    path = corpus_dir / "ground_truth.json"
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def collect_corpus_files(corpus_dir: Path) -> list[Path]:
    files = []
    for path in sorted(corpus_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in ALLOWED_SUFFIXES:
            if path.name == "ground_truth.json":
                continue
            files.append(path)
    return files


def upload_corpus(api_url: str, corpus_files: list[Path], corpus_dir: Path) -> dict[str, str]:
    print(f"\n[2/4] Uploading {len(corpus_files)} corpus files")
    uploaded: dict[str, str] = {}

    for file_path in corpus_files:
        rel_name = file_path.relative_to(corpus_dir).name
        with open(file_path, "rb") as handle:
            response = requests.post(
                f"{api_url}/upload",
                files={"file": (rel_name, handle)},
                timeout=60,
            )

        if response.status_code != 200:
            log_fail(f"Upload failed for {rel_name}: {response.text}")
            continue

        payload = response.json()
        file_id = payload.get("file_id", "")
        uploaded[rel_name] = file_id
        log_ok(f"Uploaded {rel_name} → {file_id[:8]}...")

    return uploaded


def wait_for_processing(
    api_url: str,
    min_vectors: int = 1,
    timeout_seconds: int = 120,
    poll_interval: int = 5,
) -> bool:
    print(
        f"\n[3/4] Waiting up to {timeout_seconds}s for indexing "
        f"(poll every {poll_interval}s)..."
    )

    deadline = time.time() + timeout_seconds
    last_vectors = 0

    while time.time() < deadline:
        try:
            stats = requests.get(f"{api_url}/stats", timeout=10).json()
            vectors = stats.get("total_vectors", 0)
            last_vectors = vectors

            if vectors >= min_vectors:
                log_ok(f"Qdrant vectors indexed: {vectors}")
                return True

            print(f"  ... {vectors} vectors so far, waiting...")
        except requests.RequestException as exc:
            log_fail(f"Stats check failed: {exc}")
            return False

        time.sleep(poll_interval)

    log_fail(
        f"No vectors indexed after {timeout_seconds}s "
        f"(last count: {last_vectors})"
    )
    return False


def verify_duplicate_detection(
    metadata_path: Path,
    ground_truth: dict,
    uploaded: dict[str, str],
) -> tuple[int, int]:
    print("\n[3b/4] Duplicate detection verification")
    passed = 0
    failed = 0

    if not metadata_path.exists():
        log_fail(f"Metadata not found at {metadata_path}")
        return 0, len(ground_truth.get("duplicate_pairs", []))

    with open(metadata_path, encoding="utf-8") as handle:
        metadata = json.load(handle)

    for pair in ground_truth.get("duplicate_pairs", []):
        dup_name = Path(pair["near_duplicate"]).name
        orig_name = Path(pair["original"]).name

        dup_id = uploaded.get(dup_name)
        if not dup_id:
            log_fail(f"Near-duplicate file not uploaded: {dup_name}")
            failed += 1
            continue

        entry = metadata.get(dup_id, {})
        if entry.get("status") == "duplicate":
            log_ok(f"{dup_name} flagged as duplicate of {orig_name}")
            passed += 1
        else:
            log_fail(
                f"{dup_name} was not flagged duplicate "
                f"(status={entry.get('status', 'indexed')})"
            )
            failed += 1

    return passed, failed


def run_search_queries(api_url: str, ground_truth: dict, top_k: int = 5) -> tuple[int, int]:
    print(f"\n[4/4] Running {len(ground_truth['eval_queries'])} ground-truth search queries")
    passed = 0
    failed = 0

    for item in ground_truth["eval_queries"]:
        query = item["query"]
        expected = set(item["expected_files"])

        response = requests.post(
            f"{api_url}/search",
            params={"query": query, "top_k": top_k},
            timeout=60,
        )

        if response.status_code != 200:
            log_fail(f"{item['id']}: HTTP {response.status_code}")
            failed += 1
            continue

        data = response.json()
        result_names = {r.get("filename") for r in data.get("results", [])}
        hits = expected & result_names

        if hits:
            log_ok(f"{item['id']}: found {sorted(hits)} for \"{query[:50]}...\"")
            passed += 1
        else:
            log_fail(
                f"{item['id']}: expected {sorted(expected)}, "
                f"got {sorted(result_names)[:3]}"
            )
            failed += 1

        mode = data.get("search_mode", "dense")
        intent = data.get("parsed_intent", {})
        if intent.get("topic"):
            print(f"       intent topic: {intent['topic'][:60]}")

    return passed, failed


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 4 regression test suite")
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument(
        "--corpus-dir",
        default=str(Path(__file__).resolve().parent.parent / "test_corpus"),
    )
    parser.add_argument("--skip-upload", action="store_true")
    parser.add_argument("--processing-wait", type=int, default=120)
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_dir)
    api_url = args.api_url.rstrip("/")
    metadata_path = Path(__file__).resolve().parent.parent / "uploads" / "metadata.json"

    print("=" * 60)
    print("IntentCloud Week 4 Regression Test")
    print("=" * 60)

    if not check_health(api_url):
        print("\nStart the API first: cd intentcloud-api && python main.py")
        return 1

    ground_truth = load_ground_truth(corpus_dir)
    total_passed = 0
    total_failed = 0

    if not args.skip_upload:
        corpus_files = collect_corpus_files(corpus_dir)
        if not corpus_files:
            log_fail(f"No corpus files found in {corpus_dir}")
            return 1

        uploaded = upload_corpus(api_url, corpus_files, corpus_dir)
        if not wait_for_processing(
            api_url,
            min_vectors=1,
            timeout_seconds=args.processing_wait,
        ):
            total_failed += 1

        dup_pass, dup_fail = verify_duplicate_detection(
            metadata_path, ground_truth, uploaded
        )
        total_passed += dup_pass
        total_failed += dup_fail
    else:
        uploaded = {}

    search_pass, search_fail = run_search_queries(api_url, ground_truth)
    total_passed += search_pass
    total_failed += search_fail

    print("\n" + "=" * 60)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    print("=" * 60)

    if total_failed == 0:
        print("✅ Week 4 regression test PASSED")
        return 0

    print("❌ Week 4 regression test FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
