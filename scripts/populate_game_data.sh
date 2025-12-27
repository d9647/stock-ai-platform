#!/bin/bash

# Stock AI Platform - Game Data Population Script
# This script populates the database with market data, news, features, and AI recommendations
# Required for the AI Stock Challenge Game to function

set -e  # Exit on error

echo "========================================="
echo "AI Stock Challenge - Data Population"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DAYS=${DAYS:-90}  # Default to 30 days, can override with: DAYS=60 ./scripts/populate_game_data.sh
TICKERS=${TICKERS:-"AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA"}  # Default tickers

echo -e "${BLUE}Configuration:${NC}"
echo "  Days: $DAYS"
echo "  Tickers: $TICKERS"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    exit 1
fi

# Check for required API keys
if ! grep -q "ALPHA_VANTAGE_API_KEY=" .env || ! grep -q "OPENAI_API_KEY=" .env; then
    echo -e "${RED}❌ Missing API keys in .env file!${NC}"
    echo "Please add ALPHA_VANTAGE_API_KEY and OPENAI_API_KEY to .env"
    exit 1
fi

echo -e "${GREEN}✓ Configuration OK${NC}"
echo ""

# Function to run a pipeline
run_pipeline() {
    local service_name=$1
    local service_path=$2
    local pipeline_command=$3
    local description=$4

    echo "========================================="
    echo -e "${YELLOW}Step $5/4: $description${NC}"
    echo "========================================="
    echo ""

    cd "$service_path"

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment for $service_name...${NC}"
        python3 -m venv venv
    fi

    # Activate and run
    source venv/bin/activate

    echo -e "${BLUE}Running: $pipeline_command${NC}"
    echo ""

    eval "$pipeline_command"

    echo ""
    echo -e "${GREEN}✓ $description complete${NC}"
    echo ""

    cd - > /dev/null
}

# Store the project root
PROJECT_ROOT=$(pwd)

# Pipeline 1: Market Data
run_pipeline \
    "market-data" \
    "$PROJECT_ROOT/services/market-data" \
    "python -m src.pipelines.daily_market_pipeline --days $DAYS" \
    "Market Data Pipeline (prices, volume, technical indicators)" \
    "1"

# Pipeline 2: News Sentiment
run_pipeline \
    "news-sentiment" \
    "$PROJECT_ROOT/services/news-sentiment" \
    "python -m src.pipelines.daily_news_pipeline --days $DAYS" \
    "News Sentiment Pipeline (articles, AI sentiment analysis)" \
    "2"

# Pipeline 3: Feature Store
run_pipeline \
    "feature-store" \
    "$PROJECT_ROOT/services/feature-store" \
    "python -m src.pipelines.daily_feature_pipeline --days $DAYS" \
    "Feature Store Pipeline (point-in-time feature snapshots)" \
    "3"

# Pipeline 4: AI Agent (MOST IMPORTANT)
echo "========================================="
echo -e "${YELLOW}Step 4/4: AI Agent Pipeline (CRITICAL FOR GAME)${NC}"
echo "========================================="
echo ""
echo -e "${RED}⚠️  This pipeline generates the AI recommendations that power the game.${NC}"
echo -e "${RED}⚠️  It may take 10-20 minutes and will use OpenAI API credits (~\$2-3 for 30 days).${NC}"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipping AI Agent pipeline. Game will not work without recommendations!"
    exit 1
fi

run_pipeline \
    "agent-orchestrator" \
    "$PROJECT_ROOT/services/agent-orchestrator" \
    "python -m src.pipelines.daily_agent_pipeline --tickers $TICKERS --days $DAYS" \
    "AI Agent Pipeline (BUY/HOLD/SELL recommendations)" \
    "4"

# Verification
echo "========================================="
echo -e "${YELLOW}Verifying Data...${NC}"
echo "========================================="
echo ""

cd "$PROJECT_ROOT/api"
source venv/bin/activate

echo "Checking database for recommendations..."
python -c "
from app.db import SessionLocal
from app.models.recommendations import AIRecommendation

db = SessionLocal()
try:
    count = db.query(AIRecommendation).count()
    print(f'✓ Found {count} AI recommendations in database')

    if count < 10:
        print('⚠️  Warning: Less than 10 recommendations. Game may not work properly.')
    else:
        print('✓ Sufficient data for game!')
except Exception as e:
    print(f'❌ Error checking database: {e}')
finally:
    db.close()
"

cd "$PROJECT_ROOT"

echo ""
echo "========================================="
echo -e "${GREEN}Data Population Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend API (if not already running):"
echo "   cd api && source venv/bin/activate && python -m app.main"
echo ""
echo "2. Start the frontend (if not already running):"
echo "   cd web && npm run dev"
echo ""
echo "3. Open the game:"
echo "   http://localhost:3000"
echo ""
echo "4. The game should now load with AI recommendations!"
echo ""
echo -e "${BLUE}Game Stats:${NC}"
echo "  - Days of data: $DAYS"
echo "  - Tickers: $TICKERS"
echo "  - Expected recommendations: ~$((DAYS * $(echo $TICKERS | tr ',' '\n' | wc -l)))"
echo ""
