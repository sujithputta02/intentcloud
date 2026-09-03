#!/bin/bash
# Week 4 regression test runner (upload → extract → embed → search)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
API_DIR="$ROOT/intentcloud-api"

echo "IntentCloud — Week 4 Regression Test"
echo "====================================="
echo ""
echo "Ensure the API is running:"
echo "  cd intentcloud-api && python main.py"
echo ""

if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo "❌ Backend not reachable at http://localhost:8000"
  echo "   Start it first, then re-run this script."
  exit 1
fi

cd "$API_DIR"

if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

python scripts/week4_regression_test.py "$@"
