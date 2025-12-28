# Populate Database for Game

This guide will help you populate the database with AI recommendations so the game works.

## Why You Need This

The game needs **AI-generated stock recommendations** and **historical price data** in the database. Right now it's empty, which is why you see:
> "Error loading game data: Insufficient data. Found only 0 days with complete data."

## Quick Start (Automated) ⭐ RECOMMENDED

Run this single command to populate everything automatically:

```bash
cd /Users/wdng/Projects/stock-ai-platform
./scripts/populate_game_data.sh
```

**What it does**:
- ✅ Runs all 4 pipelines in the correct order
- ✅ Shows progress for each step
- ✅ Verifies data at the end
- ✅ Takes ~20-30 minutes total
- ✅ Prompts before running expensive AI pipeline

**Optional**: Customize days or tickers:
```bash
# Custom configuration
DAYS=60 TICKERS="AAPL,TSLA,NVDA" ./scripts/populate_game_data.sh
```

## Manual Setup (Recommended - See Progress)

Open **4 separate terminal windows** and run these commands in sequence:

### Terminal 1: Market Data Pipeline
```bash
cd /Users/wdng/Projects/stock-ai-platform/services/market-data
source venv/bin/activate
python -m src.pipelines.daily_market_pipeline --days 60
```

**What it does**: Fetches OHLCV prices and calculates 15 technical indicators
**Time**: ~2 minutes
**Wait for**: "Pipeline complete" message

---

### Terminal 2: News Sentiment Pipeline
```bash
cd /Users/wdng/Projects/stock-ai-platform/services/news-sentiment
source venv/bin/activate
python -m src.pipelines.daily_news_pipeline --days 60
```

**What it does**: Fetches news articles and analyzes sentiment with OpenAI
**Time**: ~5-10 minutes
**Wait for**: "Pipeline complete" message

---

### Terminal 3: Feature Store Pipeline
```bash
cd /Users/wdng/Projects/stock-ai-platform/services/feature-store
source venv/bin/activate
python -m src.pipelines.daily_feature_pipeline --tickers AAPL,MSFT,GOOGL,AMZN --days 60
```

**What it does**: Creates point-in-time feature snapshots
**Time**: ~1 minute
**Wait for**: "Pipeline complete" message

---

### Terminal 4: AI Agent Pipeline ⚠️ CRITICAL
```bash
cd /Users/wdng/Projects/stock-ai-platform/services/agent-orchestrator
source venv/bin/activate
python -m src.pipelines.daily_agent_pipeline --tickers AAPL,MSFT,GOOGL,AMZN --days 30
```

**What it does**: Runs 4 AI agents to generate BUY/HOLD/SELL recommendations
**Time**: ~10-15 minutes (calls OpenAI GPT-4 for each ticker/day)
**Wait for**: "Pipeline complete" message

**This is the most important pipeline!** The game needs recommendations to work.

---

## Order Matters!

Run them in this exact order:
1. Market Data (Terminal 1)
2. News Sentiment (Terminal 2)
3. Feature Store (Terminal 3)
4. AI Agents (Terminal 4) ← **MUST complete for game to work**

Each pipeline depends on the previous one's data.

---

## Check if Data is Ready

After running all 4 pipelines, check the database:

```bash
# Connect to database
psql postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev

# Check recommendations (MUST have rows for game to work)
SELECT COUNT(*) FROM agents.stock_recommendations;

# Should see: count > 0 (ideally 100+ rows for 30 days × 4 tickers)
# If count = 0, the AI agent pipeline hasn't run yet!

# See sample recommendations
SELECT ticker, as_of_date, recommendation, confidence
FROM agents.stock_recommendations
ORDER BY as_of_date DESC
LIMIT 10;

# Exit psql
\q
```

---

## Expected Output

After all pipelines complete, you should have:

| Table | Rows | Pipeline |
|-------|------|----------|
| `market_data.ohlcv_prices` | ~240 | Market Data ✓ |
| `market_data.technical_indicators` | ~240 | Market Data ✓ |
| `news.news_articles` | ~100+ | News Sentiment ✓ |
| `features.feature_snapshots` | ~240 | Feature Store ✓ |
| **`agents.stock_recommendations`** | **~120** | **AI Agents ✓** |

---

## Verify Game Works

Once pipelines complete:

1. Refresh your browser at http://192.168.5.126:3000
2. Click "Start Playing Now"
3. Configure game settings
4. Click "Start Game"

You should now see:
- ✅ Game loads successfully
- ✅ AI recommendations displayed
- ✅ Stocks have prices
- ✅ Ready to play!

---

## Troubleshooting

### Issue: "Insufficient data. Found only 0 days"

**Cause**: AI Agent pipeline hasn't completed successfully
**Fix**: Run Terminal 4 (AI Agent pipeline) again

### Issue: Pipeline fails with API key error

**Cause**: Missing API keys in `.env`
**Fix**:
```bash
# Check if keys are set
grep -E "POLYGON_API_KEY|OPENAI_API_KEY" /Users/wdng/Projects/stock-ai-platform/.env

# If missing, add them to .env file
```

### Issue: Database connection error

**Cause**: PostgreSQL not running
**Fix**:
```bash
docker-compose up -d
# Wait 10 seconds for database to start
```

### Issue: Pipeline takes forever

**Cause**: OpenAI API rate limits or slow network
**Solution**: This is normal. AI Agent pipeline can take 10-15 minutes because it:
- Calls OpenAI GPT-4 for each ticker/day combination
- Runs 4 agents per ticker/day (Technical, Sentiment, Risk, Synthesizer)
- For 30 days × 4 tickers = 120 API calls

---

## Quick Test (Just 10 Days)

If you want to test faster with less data:

```bash
# Terminal 1
cd /Users/wdng/Projects/stock-ai-platform/services/market-data
source venv/bin/activate
python -m src.pipelines.daily_market_pipeline --ticker AAPL --days 15

# Terminal 2
cd ../news-sentiment
source venv/bin/activate
python -m src.pipelines.daily_news_pipeline --ticker AAPL --days 15

# Terminal 3
cd ../feature-store
source venv/bin/activate
python -m src.pipelines.daily_feature_pipeline --tickers AAPL --days 15

# Terminal 4 (CRITICAL)
cd ../agent-orchestrator
source venv/bin/activate
python -m src.pipelines.daily_agent_pipeline --tickers AAPL --days 10
```

This will create 10 days of game data for just AAPL (takes ~3-5 minutes total).

---

## Cost Estimate

Running pipelines with OpenAI:
- **30 days, 4 tickers**: ~$2-3 in OpenAI API costs
- **10 days, 1 ticker**: ~$0.20 in OpenAI API costs

All other APIs (Polygon, Finnhub, NewsAPI) are free tier.

---

## After Data is Loaded

The game will work with any amount of data:
- **Minimum**: 10 days for 1 ticker
- **Recommended**: 30 days for 4 tickers (AAPL, MSFT, GOOGL, AMZN)
- **Maximum**: 60 days for all tickers

You can always run pipelines again to add more data later!

---

## Need Help?

If pipelines fail or take too long:
1. Check the terminal output for error messages
2. Verify API keys in `.env`
3. Ensure Docker is running (`docker ps` should show PostgreSQL)
4. Check database connection works (`psql postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev`)

---

**Once all 4 pipelines complete, refresh the game and enjoy!** 🎮
