#!/bin/bash
# Week 5 Evaluation & Benchmark Runner (Phase 4 Hybrid + RRF + Cross-Encoder Rerank)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT/intentcloud-api"

echo "================================================================="
echo "IntentCloud — Week 5 Benchmark Evaluation (Phase 4)"
echo "Dense + Sparse + Reciprocal Rank Fusion + Cross-Encoder Reranker"
echo "================================================================="
echo ""

if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "⚠️ Backend not reachable at http://localhost:8000"
  echo "   Starting backend temporarily in background..."
  cd "$API_DIR"
  if [ -d "venv" ]; then
    source venv/bin/activate
  fi
  python main.py &
  API_PID=$!
  trap 'kill $API_PID 2>/dev/null || true' EXIT
  sleep 5
fi

cd "$API_DIR"
if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

python scripts/week5_evaluation.py "$@"
