#!/bin/bash

#
# Run Newman API Tests Locally
#
# This script runs the Postman collection using Newman CLI
# Useful for local testing before pushing to GitHub
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Stock AI Platform - Newman API Tests${NC}"
echo ""

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo -e "${RED}❌ Newman not found${NC}"
    echo ""
    echo "Install Newman:"
    echo "  npm install -g newman"
    echo "  npm install -g newman-reporter-htmlextra"
    echo ""
    exit 1
fi

echo "✅ Newman installed: $(newman --version)"

# Check if API server is running
echo ""
echo "🔍 Checking if API server is running..."
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server is running${NC}"
else
    echo -e "${RED}❌ API server not running${NC}"
    echo ""
    echo "Start the API server first:"
    echo "  cd api"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --port 8000"
    echo ""
    exit 1
fi

# Create reports directory
mkdir -p reports

# Run Newman tests
echo ""
echo "🚀 Running Newman tests..."
echo ""

newman run Stock_AI_Platform_API.postman_collection.json \
    --env-var "base_url=http://localhost:8000" \
    --reporters cli,htmlextra,json \
    --reporter-htmlextra-export reports/newman-report-$(date +%Y%m%d-%H%M%S).html \
    --reporter-htmlextra-title "Stock AI Platform API Tests - Local Run" \
    --reporter-htmlextra-browserTitle "API Test Report" \
    --reporter-json-export reports/newman-report-latest.json \
    --timeout-request 10000 \
    --delay-request 200 \
    --color on

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "📊 View HTML report:"
    echo "  open reports/newman-report-*.html"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "📊 View HTML report for details:"
    echo "  open reports/newman-report-*.html"
    echo ""
    exit 1
fi
