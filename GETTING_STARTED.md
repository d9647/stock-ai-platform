# Getting Started with Stock AI Platform

A production-grade educational stock trading simulator with AI-powered recommendations and multiplayer classroom mode.

## Prerequisites

Before you start, ensure you have:

- **Docker Desktop** (must be running!)
  - Download: https://www.docker.com/products/docker-desktop
  - Verify: `docker info` should show system information
- **Python 3.11+**
  - Check: `python3 --version`
- **Node.js 18+** and **pnpm**
  - Check: `node --version` and `pnpm --version`
- **Git** installed

## Quick Start

### 1. Start Docker Desktop

**IMPORTANT**: Open Docker Desktop and wait for it to fully start before proceeding.

```bash
# Verify Docker is running
docker info
```

If you see "Cannot connect to the Docker daemon", Docker Desktop is not running.

### 2. Clone Repository

```bash
git clone <repo-url>
cd stock-ai-platform
```

### 3. Automated Setup (Recommended)

```bash
./scripts/setup.sh
```

This will:
- Start PostgreSQL and Redis containers
- Create Python virtual environments
- Install all dependencies
- Run database migrations

### 4. Manual Setup (Alternative)

If the automated setup doesn't work, follow these steps:

**Start Infrastructure**:
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- pgAdmin (port 5050)

**Setup API Backend**:
```bash
cd api
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
```

**Setup Services**:
```bash
# Market data service
cd services/market-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# News sentiment service
cd ../news-sentiment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Feature store service
cd ../feature-store
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Agent orchestrator service
cd ../agent-orchestrator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## API Keys Configuration

Create a `.env` file in the project root with these keys:

```env
# Market Data
POLYGON_API_KEY=your_polygon_key

# News Sources
NEWSAPI_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_key

# AI Agents
OPENAI_API_KEY=your_openai_key

# Database (already configured for local development)
DATABASE_URL=postgresql://stockai:stockai@localhost:5432/stockai_dev
REDIS_URL=redis://localhost:6379/0
```

## Populate Game Data

Before playing the game, you need to populate the database with AI recommendations:

```bash
./scripts/populate_game_data.sh
```

This takes ~20-30 minutes and generates:
- 30 days of historical market data
- News sentiment analysis
- Feature snapshots
- AI trading recommendations

The script will:
1. Fetch market data for default tickers (AAPL, MSFT, GOOGL, AMZN, TSLA, etc.)
2. Analyze news sentiment for each ticker
3. Create point-in-time feature snapshots
4. Generate AI agent recommendations

## Running the Platform

### Start API Server

```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API available at:
- http://localhost:8000
- http://localhost:8000/docs (Interactive API documentation)

### Start Web Frontend

```bash
cd web
pnpm install
pnpm dev
```

Frontend available at http://localhost:3000

## Playing the Game

### Solo Mode

1. Visit http://localhost:3000
2. Click "Start Playing Now"
3. Configure game settings:
   - Game length: 10-60 days
   - Select stocks to trade
   - Choose difficulty (easy/medium/hard)
4. Review daily AI recommendations
5. Make buy/sell decisions
6. Click "Advance Day" to progress
7. Complete all days to see your final grade (A-F)

### Multiplayer Classroom Mode

**Teacher Setup**:
1. Visit http://localhost:3000
2. Click "Create Room"
3. Configure game settings and mode:
   - **Async Mode**: Students play at their own pace
   - **Sync Manual**: Teacher manually advances each day
   - **Sync Auto**: Timer automatically advances days
4. Share room code with students

**Student Join**:
1. Visit http://localhost:3000
2. Click "Join Room"
3. Enter room code and your name
4. Wait for teacher to start the game
5. Trade and compete on the leaderboard!

## Game Rules

- **Trading Restrictions**: Can only BUY when AI recommends BUY or STRONG_BUY
- **Selling**: Can sell anytime (no restrictions)
- **Trade Execution**: Trades execute at next day's open price
- **Starting Cash**: $10,000 (configurable)
- **AI Opponent**: Follows recommendations perfectly for comparison

## Scoring System

Your final grade (A-F) is based on four components:

1. **Portfolio Return** (0-500 points) - Total return percentage
2. **Risk Discipline** (50 points per valid trade) - Following AI recommendations
3. **Beat AI Bonus** (0-200 points) - Outperforming the AI benchmark
4. **Drawdown Penalty** (0 to -200 points) - Avoiding large losses

**Grade Scale**:
- A: 700+ points (outstanding)
- B: 550-699 points (good)
- C: 400-549 points (satisfactory)
- D: 250-399 points (needs improvement)
- F: <250 points (poor)

## Architecture Overview

### Golden Rule

> **If it can "think", it cannot block a request.**
> **If it serves a request, it must not think.**

This ensures:
- Fast API responses (<100ms)
- Predictable costs (AI runs offline)
- Scalable architecture

### Data Flow

```
Historical Data → Market Data Service → Feature Store (append-only)
                                            ↓
Historical News → News Sentiment Service → Feature Store (append-only)
                                            ↓
                                    Agent Orchestrator (offline)
                                            ↓
                                  Recommendation Store (versioned)
                                            ↓
                                    FastAPI Backend (read-only)
                                            ↓
                                      Next.js Frontend
```

### Key Principles

1. **Feature Store is Append-Only and Point-in-Time**
   - Immutable snapshots for reproducibility
   - No data updates or deletes
   - Perfect for backtesting

2. **Agents Read Only Feature Snapshots**
   - Agents never access raw tables
   - All inputs are versioned
   - Prevents look-ahead bias

3. **Agents Run Offline Only**
   - Agent reasoning is async/scheduled
   - Never in API request path
   - Results are pre-computed

4. **API is Read-Only and Deterministic**
   - No LLM calls in request handlers
   - Cacheable responses
   - Fast response times

## Project Structure

```
stock-ai-platform/
├── api/                        # FastAPI backend (read-only endpoints)
├── web/                        # Next.js frontend
├── services/
│   ├── market-data/           # Price data & technical indicators
│   ├── news-sentiment/        # News analysis & sentiment
│   ├── feature-store/         # Point-in-time feature snapshots
│   └── agent-orchestrator/    # LangGraph AI agents (offline)
├── scripts/                   # Setup & utility scripts
└── docs/                      # Documentation
```

## Common Commands

### Docker

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres

# Check status
docker-compose ps
```

### Database

```bash
# PostgreSQL shell
docker exec -it stockai-postgres psql -U stockai -d stockai_dev

# Redis shell
docker exec -it stockai-redis redis-cli

# Access pgAdmin
open http://localhost:5050
# Email: admin@stockai.local
# Password: admin
```

### Running Tests

```bash
# API tests
cd api && pytest

# Market data tests
cd services/market-data && pytest tests/ -v

# News sentiment tests
cd services/news-sentiment && pytest tests/ -v

# Feature store tests
cd services/feature-store && pytest tests/ --cov=src

# Agent orchestrator tests
cd services/agent-orchestrator && pytest tests/ --cov=src
```

## Troubleshooting

### Docker Not Running

```
Error: Cannot connect to the Docker daemon
```

**Solution**: Start Docker Desktop first!

### Port Already in Use

```
Error: Address already in use
```

**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Database Connection Failed

```
Error: could not connect to server
```

**Solution**:
```bash
# Wait for PostgreSQL to start
sleep 10

# Check if running
docker-compose ps

# Restart if needed
docker-compose restart postgres
```

### Game Shows "Loading..."

If the game gets stuck on "Loading game...":
- Ensure you've run `./scripts/populate_game_data.sh`
- Check API is running at http://localhost:8000
- Verify database has data: Check pgAdmin at http://localhost:5050

## Next Steps

### Explore the Database

Use pgAdmin (http://localhost:5050) to explore:

```sql
-- See AAPL prices
SELECT * FROM market_data.ohlcv_prices
WHERE ticker = 'AAPL'
ORDER BY date DESC LIMIT 10;

-- See technical indicators
SELECT ticker, date, rsi_14, macd, sma_50
FROM market_data.technical_indicators
WHERE ticker = 'AAPL'
ORDER BY date DESC LIMIT 10;

-- See AI recommendations
SELECT ticker, recommendation_date, action, confidence, reasoning
FROM agents.recommendations
WHERE ticker = 'AAPL'
ORDER BY recommendation_date DESC LIMIT 10;
```

### Fetch More Data

```bash
# Market data for additional tickers
cd services/market-data
source venv/bin/activate
python -m src.pipelines.daily_market_pipeline --tickers NVDA AMD --days 90

# News sentiment for additional tickers
cd ../news-sentiment
source venv/bin/activate
python -m src.pipelines.daily_news_pipeline --tickers NVDA AMD --days 30

# Feature snapshots
cd ../feature-store
source venv/bin/activate
python -m src.pipelines.daily_feature_pipeline --tickers NVDA AMD --days 30

# AI recommendations
cd ../agent-orchestrator
source venv/bin/activate
python -m src.pipelines.daily_agent_pipeline --tickers NVDA AMD --date 2024-12-15
```

## Documentation

- [README.md](README.md) - Project overview
- [GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md) - Complete game design
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical architecture
- [TESTING.md](TESTING.md) - Testing guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment

## Educational Value

This platform teaches:
- Following expert (AI) recommendations
- Risk management and discipline
- Portfolio diversification
- Technical analysis basics
- Market timing and trade execution
- Performance benchmarking

## Disclaimer

This platform is for **educational and simulation purposes only**. Not financial advice. Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions.
