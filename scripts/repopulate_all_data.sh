#!/bin/bash
#
# Repopulate All Data - Full 290-Day Market + 365-Day News + 90-Day Analysis
#
# This script:
# 1. Clears existing data for 7 tickers
# 2. Fetches 290 days of market data (200 lookback + 90 analysis)
# 3. Fetches 365 days of news sentiment
# 4. Creates 90 days of feature snapshots
# 5. Generates 90 days of AI recommendations
#

# Error handling - show errors but don't exit silently
set -o pipefail  # Catch errors in pipes

# Trap errors and show what went wrong
trap 'echo -e "\n${RED}❌ Error on line $LINENO. Command: $BASH_COMMAND${NC}\n"; exit 1' ERR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TICKERS="AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA"
NEWS_DAYS=365        # News sentiment (full year for comprehensive coverage)
MARKET_DAYS=290      # Market data (200 lookback + 90 analysis for SMA_200, EMA_200, etc.)
ANALYSIS_DAYS=90     # Features and AI recommendations

PROJECT_ROOT="/Users/wdng/Projects/stock-ai-platform"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stock AI Platform - Full Data Repopulation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Tickers: ${TICKERS}"
echo -e "  Market data: ${MARKET_DAYS} days (200 lookback + 90 analysis)"
echo -e "  News sentiment: ${NEWS_DAYS} days"
echo -e "  Analysis period: ${ANALYSIS_DAYS} days (features + AI)"
echo ""
echo -e "${YELLOW}This will:${NC}"
echo -e "  1. DELETE existing data for these 7 tickers"
echo -e "  2. Fetch 290 days of market data (~4 min)"
echo -e "  3. Fetch 365 days of news sentiment (~15 min)"
echo -e "  4. Create 90 days of features (~2 min)"
echo -e "  5. Generate 90 days of AI recommendations (~20 min)"
echo ""
echo -e "${RED}Total estimated time: ~45 minutes${NC}"
echo ""

# Prompt for confirmation
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 0: Clearing Existing Data${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Clear data for all 7 tickers
echo -e "${YELLOW}Clearing data for: ${TICKERS}${NC}"

TICKER_ARRAY=(AAPL MSFT GOOGL AMZN NVDA META TSLA)

for ticker in "${TICKER_ARRAY[@]}"; do
    echo -e "${YELLOW}  Clearing ${ticker}...${NC}"
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM market_data.ohlcv_prices WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM market_data.technical_indicators WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM news.news_articles WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM news.news_sentiment_aggregates WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM features.feature_snapshots WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
    psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "DELETE FROM agent.recommendations WHERE ticker = '${ticker}';" 2>&1 | grep -v "DELETE" || true
done

echo -e "${GREEN}✓ Data cleared${NC}"
echo ""

# Pipeline 1: Market Data (290 days)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 1: Market Data Pipeline (290 days)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "${PROJECT_ROOT}/services/market-data"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${YELLOW}Fetching prices and technical indicators for ${TICKERS}...${NC}"
echo -e "${YELLOW}Note: 290 days = 200 lookback + 90 analysis (for SMA_200, EMA_200, etc.)${NC}"
echo ""

if python -m src.pipelines.daily_market_pipeline --days ${MARKET_DAYS}; then
    echo ""
    echo -e "${GREEN}✓ Market data complete${NC}"
else
    echo ""
    echo -e "${RED}❌ Market data pipeline failed!${NC}"
    echo -e "${YELLOW}Check the output above for errors${NC}"
    exit 1
fi

echo ""

# Pipeline 2: News Sentiment (365 days)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 2: News Sentiment Pipeline (365 days)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "${PROJECT_ROOT}/services/news-sentiment"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${YELLOW}Fetching news articles and calculating sentiment...${NC}"
echo -e "${YELLOW}Note: Full year of news for comprehensive sentiment analysis${NC}"
echo -e "${RED}Note: This uses OpenAI API and will cost ~\$0.50${NC}"
echo ""

read -p "Proceed with news sentiment analysis? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Skipping news sentiment pipeline${NC}"
else
    echo ""
    if python -m src.pipelines.daily_news_pipeline --days ${NEWS_DAYS}; then
        echo ""
        echo -e "${GREEN}✓ News sentiment complete${NC}"
    else
        echo ""
        echo -e "${RED}❌ News sentiment pipeline failed!${NC}"
        echo -e "${YELLOW}Check the output above for errors${NC}"
        exit 1
    fi
fi

echo ""

# Pipeline 3: Feature Store (90 days)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 3: Feature Store Pipeline (90 days)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "${PROJECT_ROOT}/services/feature-store"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${YELLOW}Creating feature snapshots for ${TICKERS}...${NC}"
echo ""

if python -m src.pipelines.daily_feature_pipeline --days ${ANALYSIS_DAYS}; then
    echo ""
    echo -e "${GREEN}✓ Feature store complete${NC}"
else
    echo ""
    echo -e "${RED}❌ Feature store pipeline failed!${NC}"
    echo -e "${YELLOW}Check the output above for errors${NC}"
    exit 1
fi

echo ""

# Pipeline 4: AI Agent Recommendations (90 days)
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: AI Agent Pipeline (90 days)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "${PROJECT_ROOT}/services/agent-orchestrator"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate

echo -e "${YELLOW}Generating AI recommendations...${NC}"
echo -e "${RED}Note: This uses OpenAI API (GPT-4o) and will cost ~\$2.00${NC}"
echo ""

read -p "Proceed with AI recommendation generation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Skipping AI recommendation pipeline${NC}"
else
    echo ""
    if python -m src.pipelines.daily_agent_pipeline --days ${ANALYSIS_DAYS}; then
        echo ""
        echo -e "${GREEN}✓ AI recommendations complete${NC}"
    else
        echo ""
        echo -e "${RED}❌ AI recommendation pipeline failed!${NC}"
        echo -e "${YELLOW}Check the output above for errors${NC}"
        exit 1
    fi
fi

echo ""

# Verification
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Data Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Checking database contents...${NC}"
echo ""

echo "Market Data (OHLCV):"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as days
    FROM market_data.ohlcv_prices
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo "Technical Indicators:"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as days
    FROM market_data.technical_indicators
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo "News Articles:"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as articles
    FROM news.news_articles
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo "News Sentiment Aggregates:"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as days
    FROM news.news_sentiment_aggregates
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo "Feature Snapshots:"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as snapshots
    FROM features.feature_snapshots
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo "AI Recommendations:"
psql postgresql://stockai:stockai@localhost:5432/stockai_dev -c "
    SELECT ticker, COUNT(*) as recommendations
    FROM agent.recommendations
    WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA')
    GROUP BY ticker
    ORDER BY ticker;
"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Data Repopulation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Refresh the game in your browser"
echo -e "  2. You should now have 90 days of playable game data"
echo -e "  3. Each ticker should have ~90 trading days worth of recommendations"
echo ""
echo -e "${BLUE}Game should now work! 🎮${NC}"
