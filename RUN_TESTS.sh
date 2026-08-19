#!/bin/bash

# IntentCloud - Automated Testing Script
# Tests Phase 1-3 implementation across all components

set -e

echo "=========================================="
echo "IntentCloud - Automated Test Suite"
echo "Week 1-3 Implementation Testing"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run test
run_test() {
    local test_name=$1
    local command=$2
    
    echo -n "Testing: $test_name ... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
}

echo -e "${YELLOW}PHASE 1: DEPENDENCY VERIFICATION${NC}"
echo "======================================"

# Check Python packages
run_test "FastAPI installed" "python3 -c 'import fastapi'"
run_test "Uvicorn installed" "python3 -c 'import uvicorn'"
run_test "PyMuPDF installed" "python3 -c 'import fitz'"
run_test "Python-docx installed" "python3 -c 'import docx'"
run_test "Requests installed" "python3 -c 'import requests'"
run_test "Sentence-transformers installed" "python3 -c 'import sentence_transformers'"
run_test "Qdrant installed" "python3 -c 'import qdrant_client'"

echo ""
echo -e "${YELLOW}PHASE 2: FILE STRUCTURE VERIFICATION${NC}"
echo "======================================"

# Check backend files
run_test "Backend main.py exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/main.py"
run_test "Extraction service exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/extraction.py"
run_test "Embeddings service exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/embeddings.py"
run_test "Qdrant service exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/qdrant_client.py"
run_test "Intent parser exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/intent_parser.py"
run_test "Search service exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-api/services/search.py"

# Check frontend files
run_test "Frontend layout exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-web/app/layout.tsx"
run_test "Upload page exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-web/app/upload/page.tsx"
run_test "Search page exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-web/app/search/page.tsx"
run_test "Dashboard page exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-web/app/dashboard/page.tsx"
run_test "Navbar component exists" "test -f /Users/sujithputta/Projects/Intentcloud/intentcloud-web/components/Navbar.tsx"

echo ""
echo -e "${YELLOW}PHASE 3: BACKEND IMPORT VERIFICATION${NC}"
echo "======================================"

# Test service imports
run_test "All services importable" "cd /Users/sujithputta/Projects/Intentcloud/intentcloud-api && source venv/bin/activate && python3 -c '
from services.extraction import extract_text_from_upload
from services.embeddings import generate_embeddings
from services.qdrant_client import QdrantIndexManager
from services.intent_parser import parse_intent_with_phi3
from services.search import hybrid_search
print(\"OK\")
'"

echo ""
echo -e "${YELLOW}PHASE 4: TEST FILE CREATION${NC}"
echo "======================================"

# Create test directory
TEST_DIR="/tmp/intentcloud_tests"
mkdir -p "$TEST_DIR"

# Create test files
echo "This is a test document about machine learning and artificial intelligence." > "$TEST_DIR/test_ml.txt"
run_test "Test TXT file created" "test -f $TEST_DIR/test_ml.txt"

echo -e "${YELLOW}PHASE 5: UPLOAD ENDPOINT TEST${NC}"
echo "======================================"

# Test upload endpoint (assuming backend is running on localhost:8000)
echo ""
echo "NOTE: Requires backend running on http://localhost:8000"
echo "Start backend with: cd intentcloud-api && source venv/bin/activate && python main.py"
echo ""

# Try health check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
    
    # Test health endpoint
    run_test "Health endpoint responds" "curl -s http://localhost:8000/health | grep -q 'healthy'"
    
    # Test stats endpoint
    run_test "Stats endpoint responds" "curl -s http://localhost:8000/stats | grep -q 'total_files'"
    
    # Test upload (if backend supports it)
    echo ""
    echo "Testing upload endpoint..."
    UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@$TEST_DIR/test_ml.txt" http://localhost:8000/upload)
    
    if echo "$UPLOAD_RESPONSE" | grep -q "file_id"; then
        echo -e "${GREEN}✓ Upload endpoint accepts files${NC}"
        ((TESTS_PASSED++))
        
        # Extract file_id from response
        FILE_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"file_id":"[^"]*' | cut -d'"' -f4)
        echo "  Uploaded file ID: $FILE_ID"
        
        # Wait for processing
        echo "  Waiting 10 seconds for background processing..."
        sleep 10
        
        # Check stats
        STATS=$(curl -s http://localhost:8000/stats)
        if echo "$STATS" | grep -q "\"total_files\": 1"; then
            echo -e "${GREEN}✓ File appears in stats${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗ File not found in stats${NC}"
            ((TESTS_FAILED++))
        fi
    else
        echo -e "${RED}✗ Upload endpoint failed${NC}"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ Backend not running - skipping upload tests${NC}"
    echo "   To run upload tests, start: cd intentcloud-api && python main.py"
fi

echo ""
echo -e "${YELLOW}PHASE 6: FRONTEND VERIFICATION${NC}"
echo "======================================"

# Check Bun is installed
run_test "Bun is installed" "which bun"

# Check frontend dependencies
if [ -d "/Users/sujithputta/Projects/Intentcloud/intentcloud-web/node_modules" ]; then
    run_test "Frontend dependencies installed" "test -d /Users/sujithputta/Projects/Intentcloud/intentcloud-web/node_modules"
else
    echo -n "Testing: Frontend dependencies installed ... "
    echo -e "${YELLOW}⚠ NOT YET (run: cd intentcloud-web && bun install)${NC}"
fi

echo ""
echo "=========================================="
echo -e "TEST RESULTS"
echo "=========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start backend: cd intentcloud-api && source venv/bin/activate && python main.py"
    echo "2. Start frontend: cd intentcloud-web && bun run dev"
    echo "3. Open http://localhost:3000 in browser"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Issues to resolve:"
    echo "- Missing dependencies: run 'pip install -r requirements.txt' in intentcloud-api"
    echo "- Missing files: check file structure in intentcloud-web and intentcloud-api"
    echo "- Backend not running: start with 'cd intentcloud-api && python main.py'"
    exit 1
fi
