# Stock AI Platform

A production-grade educational stock trading simulator with AI-powered recommendations and multiplayer classroom mode.

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
├── api/                        # FastAPI backend (read-only endpoints)
├── web/                        # Next.js frontend
├── services/
│   ├── market-data/           # Price data & technical indicators
│   ├── news-sentiment/        # News analysis & sentiment
│   ├── feature-store/         # Point-in-time feature snapshots
│   └── agent-orchestrator/    # LangGraph AI agents (offline)
├── scripts/                   # Setup & utility scripts
├── docs/                      # Documentation
│   └── archive/              # Historical documentation
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (must be running!)
- Python 3.11+
- Node.js 18+ and pnpm
- Git

### Automated Setup

```bash
# Clone repository
git clone <repo-url>
cd stock-ai-platform

# Run setup script
./scripts/setup.sh
```

This will start Docker containers, create virtual environments, install dependencies, and run database migrations.

### Populate Game Data

Before playing, generate AI recommendations:

```bash
./scripts/populate_game_data.sh
```

This takes ~20-30 minutes and generates 30 days of market data, sentiment analysis, and AI recommendations.

### Start the Platform

**Backend API**:
```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend**:
```bash
cd web
pnpm install
pnpm dev
```

Visit http://localhost:3000 to play!

**For detailed setup instructions**, see [GETTING_STARTED.md](GETTING_STARTED.md)

---

## 🎮 Game Modes

### Solo Mode

1. Visit http://localhost:3000
2. Click "Start Playing Now"
3. Configure game settings (10-60 days, select stocks)
4. Review daily AI recommendations
5. Make buy/sell decisions
6. Click "Advance Day" to progress
7. Complete all days to see your grade (A-F)

### Multiplayer Classroom Mode

**Teacher**:
1. Click "Create Classroom"
2. Configure game and select mode (async/sync manual/sync auto)
3. Share room code with students
4. Monitor leaderboard and control progression

**Student**:
1. Click "Join Classroom"
2. Enter room code
3. Compete on leaderboard with classmates

**For complete game documentation**, see [GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md)

---

## Trading Rules

- **Buy**: Only allowed when AI recommends BUY or STRONG_BUY
- **Sell**: Allowed anytime (no restrictions)
- **Execution**: Trades execute at next day's open price
- **Starting Cash**: $10,000 (configurable)
- **AI Opponent**: Follows recommendations perfectly for comparison

## Scoring System

Your grade (A-F) is based on:

1. **Portfolio Return** (0-500 points) - Total return percentage
2. **Risk Discipline** (50 points per valid trade) - Following AI recommendations
3. **Beat AI Bonus** (0-200 points) - Outperforming the AI benchmark
4. **Drawdown Penalty** (0 to -200 points) - Avoiding large losses

**Grade Scale**:
- **A**: 700+ points (outstanding)
- **B**: 550-699 points (good)
- **C**: 400-549 points (satisfactory)
- **D**: 250-399 points (needs improvement)
- **F**: <250 points (poor)

---

## Technology Stack

**Backend**:
- FastAPI (Python)
- PostgreSQL (Neon/Supabase)
- Redis (optional caching)
- SQLAlchemy ORM
- Alembic migrations

**Frontend**:
- Next.js 14 (App Router)
- React 18.3+
- TypeScript 5.3+
- Zustand (state management)
- TanStack Query (server state)
- Tailwind CSS

**AI Services**:
- OpenAI GPT-4 (sentiment analysis, recommendations)
- LangGraph (multi-agent orchestration)
- Polygon.io (market data)
- Finnhub & NewsAPI (news data)

## Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Detailed setup and getting started guide
- **[GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md)** - Complete game design and multiplayer mode
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment to Replit & Vercel
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical architecture overview
- **[TESTING.md](TESTING.md)** - Testing guide and best practices

## Development Status

| Feature | Status |
|---------|--------|
| Market Data Pipeline | ✅ Complete |
| News Sentiment Pipeline | ✅ Complete |
| Feature Store | ✅ Complete |
| AI Agent Orchestrator | ✅ Complete |
| Game Lobby & Flow | ✅ Complete |
| Trading System | ✅ Complete |
| Scoring System | ✅ Complete |
| Solo Mode | ✅ Complete |
| Multiplayer Async Mode | ✅ Complete |
| Multiplayer Sync Modes | ✅ Complete |
| Leaderboards | ✅ Complete |
| Teacher Dashboard | ✅ Complete |

## Deployment

### Production (Recommended)

- **Backend**: Replit (FREE or $7-20/month)
- **Frontend**: Vercel (FREE)
- **Database**: Neon or Supabase (FREE tier available)
- **Total Cost**: $0-20/month + OpenAI usage

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

## Educational Value

This platform teaches:

- **Stock Market Basics**: Understanding stocks, prices, and portfolios
- **Technical Analysis**: Moving averages, RSI, MACD, volatility indicators
- **Sentiment Analysis**: How news affects stock prices
- **Risk Management**: Portfolio diversification, position sizing, drawdown management
- **Strategic Thinking**: When to buy vs. sell, following vs. ignoring recommendations
- **Performance Metrics**: ROI, benchmarking, win rate

## License

MIT License - See [LICENSE](LICENSE)

## Disclaimer

This platform is for **educational and simulation purposes only**. Not financial advice. Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

For issues, questions, or feedback:
- Check [GETTING_STARTED.md](GETTING_STARTED.md) for setup help
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Open an issue on GitHub

---

**Built with ❤️ for education**
