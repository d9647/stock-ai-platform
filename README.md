# Stock AI Platform

A production-grade stock trading simulator with AI-powered recommendations based on historical technical data and news sentiment analysis.

## 🏗️ Architecture Principles

### Critical Design Rules

1. **Feature Store is Append-Only and Point-in-Time**
   - Immutable snapshots for reproducibility
   - No data is ever updated or deleted
   - Historical replay guaranteed accurate

2. **Agents Read Only Feature Snapshots**
   - Agents never access raw tables
   - All inputs are versioned snapshots
   - Prevents look-ahead bias

3. **Agents Run Offline Only**
   - Agent reasoning is async/scheduled
   - Never in API request path
   - Results are pre-computed

4. **API is Read-Only and Deterministic**
   - No LLM calls in request handlers
   - Cacheable responses
   - Sub-100ms latency

### Golden Rule

> **If it can "think", it cannot block a request.**
> **If it serves a request, it must not think.**

---

## 📦 Project Structure

```
stock-ai-platform/
├── services/
│   ├── market-data/           # Deterministic price + technical indicators
│   ├── news-sentiment/         # Historical news + sentiment extraction
│   ├── feature-store/          # Append-only, point-in-time feature snapshots
│   └── agent-orchestrator/     # LangGraph agents (offline only)
├── api/                        # FastAPI backend (read-only end points)
├── web/                        # Next.js frontend
├── backtesting/                # Historical replay & strategy testing
├── shared/                     # Shared schemas, types, utilities
├── infra/                      # Docker, CI/CD, infrastructure
├── docs/                       # Architecture docs, ADRs
└── scripts/                    # Setup, migration, utility scripts
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (must be running!)
- Python 3.11+
- Git

### 1. Start Docker Desktop

**IMPORTANT**: Make sure Docker Desktop is running before proceeding!

- Open Docker Desktop application
- Wait for it to fully start (whale icon in menu bar should be steady)
- Verify: `docker info` should show system information (not an error)

### 2. Clone and Setup

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

```bash
# Start infrastructure
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- pgAdmin (port 5050)

### 3. Initialize Database

```bash
cd api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
alembic upgrade head
```

### 4. Run Data Pipelines

**Market Data Pipeline** (Technical Indicators):
```bash
cd services/market-data
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_market_pipeline --ticker AAPL --days 30
```

**News Sentiment Pipeline**:
```bash
cd services/news-sentiment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_news_pipeline --ticker AAPL --days 30
```

**Feature Store Pipeline**:
```bash
cd services/feature-store
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_feature_pipeline --tickers AAPL MSFT --days 30
```

**Agent Orchestrator Pipeline** (AI Recommendations):
```bash
cd services/agent-orchestrator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.pipelines.daily_agent_pipeline --tickers AAPL MSFT --date 2024-12-15
```

### 5. Start API Server

```bash
cd api
uvicorn app.main:app --reload --port 8000
```

API available at http://192.168.5.126:8000
Docs at http://192.168.5.126:8000/docs

### 6. Start Web Frontend

```bash
cd web
pnpm install
pnpm dev
```

Frontend available at http://192.168.5.126:3000

---

## 🎮 Playing the AI Stock Challenge Game

The Stock AI Platform features a **turn-based educational stock trading game** where you compete against an AI opponent to learn trading strategies.

### Game Overview

- **Educational Focus**: Learn to follow AI recommendations and manage risk
- **Turn-Based Gameplay**: You control time by clicking "Advance Day"
- **No Real Money**: Practice with a simulated $10,000 portfolio
- **Compete vs AI**: The AI follows its own recommendations perfectly
- **Earn Grades**: Get scored A-F based on performance

### First Time Setup

**Before playing, you need to populate the database with AI recommendations:**

```bash
cd /Users/wdng/Projects/stock-ai-platform
./scripts/populate_game_data.sh
```

This takes ~20-30 minutes and generates 30 days of AI trading recommendations. See [POPULATE_DATABASE.md](POPULATE_DATABASE.md) for details.

### How to Play

1. **Start Game**: Visit http://192.168.5.126:3000 and click "Start Playing Now"
2. **Configure**: Choose game length (10-60 days) and select stocks to trade
3. **Review Daily**: Each day, review AI recommendations with explanations
4. **Trade**: Buy stocks when AI says BUY/STRONG_BUY, sell anytime
5. **Advance**: Click "Advance to Next Day" to execute trades and move forward
6. **Complete**: After all days, view your grade and compare with AI

### Trading Rules

- **Can only BUY** when AI recommends BUY or STRONG_BUY
- **Can SELL anytime** (no restrictions)
- **Trades execute** at next day's open price (not immediately)
- Starting cash: $10,000
- Track portfolio value, P&L, and performance vs AI

### Scoring System

Your final grade (A-F) is based on:

1. **Portfolio Return** (0-500 points) - How much you earned
2. **Risk Discipline** (50 pointsper trade) - Following AI recommendations
3. **Beat AI Bonus** (0-200 points) - Outperforming the AI opponent
4. **Drawdown Penalty** (0 to -200 points) - Avoiding large losses

**Grade Scale**:
- A: 700+ points (outstanding)
- B: 550-699 points (good)
- C: 400-549 points (satisfactory)
- D: 250-399 points (needs improvement)
- F: <250 points (poor)

### Educational Value

- Learn to trust expert recommendations
- Practice risk management
- Understand portfolio diversification
- Experience buy low, sell high mechanics
- Compare your strategy against AI

See [GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md) for complete game design and mechanics.

---

## 🔑 API Keys Required

Add these to `.env`:

```
# Market Data
POLYGON_API_KEY=your_polygon_key

# News Sources
NEWSAPI_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_key

# AI Agents
OPENAI_API_KEY=your_openai_key

# Database
DATABASE_URL=postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev
REDIS_URL=redis://192.168.5.126:6379/0
```

---

## 📊 Data Flow

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
                                      Frontend/Mobile
```

---

## 🧪 Running Tests

```bash
# Market data tests
cd services/market-data
pytest tests/ -v

# News sentiment tests
cd services/news-sentiment
pytest tests/ -v

# Feature store tests
cd services/feature-store
pytest tests/ --cov=src --cov-report=html

# Agent orchestrator tests
cd services/agent-orchestrator
pytest tests/ --cov=src --cov-report=html

# API tests
cd api && pytest
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

---

## 📖 Documentation

### Quick Start
- [START_HERE.md](START_HERE.md) - Quick start guide for new developers

### Milestone Documentation
- **[MILESTONE_1_COMPLETE.md](MILESTONE_1_COMPLETE.md)** - Complete milestone 1 summary with all phases
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical architecture overview

### Phase Documentation
- [PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md) - Foundation: Infrastructure, market data, technical indicators
- [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md) - News sentiment & feature store
- [PHASE_3_COMPLETE.md](PHASE_3_COMPLETE.md) - AI agents with LangGraph (82.69% test coverage)
- [PHASE_4_COMPLETE.md](PHASE_4_COMPLETE.md) - Educational game platform with multiplayer

### Implementation Guides
- [GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md) - Complete game design documentation (450+ lines)
- [IMPLEMENTATION_CHANGELOG.md](IMPLEMENTATION_CHANGELOG.md) - All bug fixes and enhancements
- [TESTING.md](TESTING.md) - Testing guide
- [POPULATE_DATABASE.md](POPULATE_DATABASE.md) - Database population guide
- [MULTIPLAYER_IMPLEMENTATION.md](MULTIPLAYER_IMPLEMENTATION.md) - Multiplayer classroom mode

### Frontend Documentation
- [web/README.md](web/README.md) - Frontend architecture and setup
- [web/SETUP.md](web/SETUP.md) - Web installation instructions

---

## 🛣️ Roadmap

### Phase 1: Foundation ✅ COMPLETE
- [x] Project structure
- [x] Database schema (10 tables across 5 schemas)
- [x] Market data ingestion (Polygon API)
- [x] Technical indicators (15 indicators: SMA, EMA, RSI, MACD, Bollinger, ATR, OBV, Volatility)
- [x] Basic API end points
- [x] Frontend shell

### Phase 2: News Sentiment & Feature Store ✅ COMPLETE
- [x] News ingestion (Finnhub + NewsAPI)
- [x] Sentiment analysis (OpenAI GPT-4o-mini)
- [x] Daily sentiment aggregation
- [x] Feature store implementation (point-in-time snapshots)
- [x] Feature validation framework
- [x] Complete test suite (15+ tests)

### Phase 3: AI Agents ✅ COMPLETE
- [x] Technical analyst agent (LangGraph)
- [x] Sentiment analyst agent
- [x] Risk manager agent
- [x] Portfolio synthesizer agent
- [x] Agent orchestration pipeline
- [x] Parallel agent execution (LangGraph StateGraph)
- [x] Versioned prompts with SHA-256 hashing
- [x] Complete test suite (33 tests, 82.69% coverage)

### Phase 4: Educational Game Platform ✅ COMPLETE
- [x] Turn-based stock trading game
- [x] Game lobby with configuration (10-60 days, stock selection)
- [x] AI opponent that follows recommendations
- [x] Buy/sell trading with validation rules
- [x] Scoring system with A-F grades (4 components)
- [x] Portfolio tracking with P&L visualization
- [x] Game state persistence (Zustand + localStorage)
- [x] Complete game loop (lobby → play → game over)
- [x] 11 game UI components
- [x] Game data API endpoint
- [x] Dark theme with technical signals panel
- [x] Multiplayer rooms (teacher/student)
- [x] Live leaderboards for classroom competition
- [x] Comprehensive documentation ([GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md))
- [ ] Trade history visualization
- [ ] Portfolio performance charts

### Phase 5: Production Ready
- [ ] Performance optimization
- [ ] Caching strategy
- [ ] Mobile-responsive design
- [ ] iOS app preparation

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## ⚠️ Disclaimer

This platform is for **educational and simulation purposes only**. Not financial advice. Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions.
