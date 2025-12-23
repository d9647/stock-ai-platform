# AI Stock Challenge - Game Implementation

**Status**: ✅ Core Game Complete - Ready for Testing
**Implementation Date**: 2025-12-18
**Architecture**: Turn-based educational stock game with AI opponent

---

## 🎮 Game Design Overview

The AI Stock Challenge is a **turn-based educational stock market simulation** where students compete against an AI opponent to build the best portfolio. The game prioritizes learning, determinism, and engagement over financial complexity.

### Core Principles

1. **Turn-Based**: Time advances only when player clicks "Advance Day"
2. **Deterministic**: All data is preloaded, no randomness during gameplay
3. **Educational**: AI recommendations are explainable with technical/sentiment/risk breakdown
4. **Competitive**: Score system with grades (A-F) for motivation
5. **Safe**: Paper trading only, no real money involved

---

## 📊 Game Flow

```
Homepage
   ↓
Game Lobby (Configure & Load Data)
   ↓
Game View (Day Loop):
   1. View AI recommendations
   2. View portfolio & score
   3. Buy shares (if AI says BUY/STRONG_BUY)
   4. Sell shares (if you own them)
   5. Click "Advance Day"
   ↓
Game Over (Final Score & Grade)
```

---

## 🏗️ Architecture

### Data Flow

```
Backend API (FastAPI)
   ↓
GET /api/v1/game/data?days=30
   ↓
Returns all 30 days of:
   - AI recommendations
   - OHLC prices
   ↓
Frontend loads once at game start
   ↓
Zustand store manages game state locally
   ↓
No more API calls during gameplay
```

### State Management (Zustand)

**Location**: `web/lib/stores/gameStore.ts`

**Key State**:
- `config`: Game settings (initial cash, num days, tickers, difficulty)
- `gameData`: All 30 days preloaded
- `player`: Portfolio (cash, holdings, trades, score, grade)
- `ai`: AI opponent portfolio (runs in parallel)
- `status`: 'not_started' | 'playing' | 'finished'

**Key Actions**:
- `loadGameData()`: Load precomputed data from API
- `startGame()`: Initialize player and AI portfolios
- `buy(ticker, shares)`: Execute buy trade (at next day's open)
- `sell(ticker, shares)`: Execute sell trade (at next day's open)
- `advanceDay()`: Move to next day, execute trades, update score
- `resetGame()`: Clear state and restart

---

## 🎯 Trading Rules

### Buy Rules

- ✅ Can only buy when AI recommends **BUY** or **STRONG_BUY**
- ✅ Must have sufficient cash
- ✅ Trade executes at **next day's open price**

### Sell Rules

- ✅ Can only sell shares you own
- ✅ Trade executes at **next day's open price**
- ✅ Can sell partial or all shares

### Trade Execution

**IMPORTANT**: Trades never execute immediately. They execute at the **next day's opening price**.

Example:
- Day 5: User clicks "Buy 10 shares of AAPL"
- Trade is recorded but not executed
- User clicks "Advance Day"
- Day 6: Trade executes at Day 6's opening price
- Portfolio is updated

---

## 📈 Scoring System

### Score Components

| Component | points | Description |
|-----------|--------|-------------|
| Portfolio Return | 0-500 | Based on % return vs. initial cash |
| Risk Discipline | 50 per trade | Bonus for following AI signals |
| Beat AI Bonus | 0-200 | Bonus if you beat the AI |
| Drawdown Penalty | 0 to -200 | Penalty for large portfolio drops |

### Grade Thresholds (Medium Difficulty)

| Grade | Return Required |
|-------|-----------------|
| A | ≥ 10% |
| B | ≥ 5% |
| C | ≥ 0% |
| D | ≥ -5% |
| F | < -5% |

---

## 🗂️ File Structure

### Backend (FastAPI)

```
api/app/
├── routes/
│   └── game.py                  # Game data endpoint
├── schemas/
│   └── game.py                  # GameDataResponse, GameDayResponse
└── main.py                      # Registers game router
```

### Frontend (Next.js)

```
web/
├── app/
│   ├── page.tsx                 # Homepage (game landing)
│   └── game/
│       └── page.tsx             # Game controller (lobby → view → game over)
│
├── components/game/
│   ├── game-lobby.tsx           # Start screen with config
│   ├── game-view.tsx            # Main gameplay view
│   ├── game-over.tsx            # Results screen
│   ├── day-header.tsx           # Day number & score display
│   ├── portfolio-summary.tsx    # Cash, holdings, vs. AI
│   ├── ai-recommendations.tsx   # Today's AI picks
│   ├── player-holdings.tsx      # Stocks you own
│   ├── buy-modal.tsx            # Buy confirmation dialog
│   ├── sell-modal.tsx           # Sell confirmation dialog
│   └── advance-day-button.tsx   # Move to next day
│
├── lib/
│   ├── api/
│   │   └── game.ts              # API client for game data
│   ├── hooks/
│   │   └── useGameData.ts       # React Query hook
│   └── stores/
│       └── gameStore.ts         # Zustand game state (1,100 lines)
│
└── types/
    └── game.ts                  # TypeScript types for game
```

---

## 🔌 API End points

### GET /api/v1/game/data

**Purpose**: Fetch all game data for N days

**Query Parameters**:
- `days` (optional): Number of days (default: 30, max: 90)
- `tickers` (optional): Comma-separated tickers (default: AAPL,MSFT,GOOGL,AMZN)
- `end_date` (optional): End date YYYY-MM-DD (default: latest data)

**Response**: `GameDataResponse`
```json
{
  "days": [
    {
      "day": 0,
      "date": "2025-12-01",
      "recommendations": [
        {
          "ticker": "AAPL",
          "recommendation": "BUY",
          "confidence": 0.75,
          "technical_signal": "BULLISH",
          "sentiment_signal": "BULLISH",
          "risk_level": "MEDIUM_RISK",
          "rationale_summary": "Strong uptrend with positive sentiment"
        }
      ],
      "prices": {
        "AAPL": {
          "open": 150.0,
          "high": 152.0,
          "low": 149.0,
          "close": 151.5
        }
      }
    }
  ],
  "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
  "start_date": "2025-12-01",
  "end_date": "2025-12-30",
  "total_days": 30
}
```

---

## 🎨 UI Components

### Game Lobby

**Features**:
- Game explanation ("How to Play")
- Settings: Number of days (10-60), tickers
- Loading state while fetching data
- Error handling with helpful messages
- "Start Game" button

**Screenshot**:
```
┌─────────────────────────────────────────┐
│  📈 AI Stock Challenge                 │
│  Compete against our AI to build       │
│  the best portfolio!                    │
│                                         │
│  How to Play:                           │
│  1. Start with $10,000                  │
│  2. Review AI recommendations           │
│  3. Buy when AI says BUY                │
│  4. Sell when you think it's right      │
│  5. Click "Advance Day"                 │
│  6. Beat the AI to earn A grade!        │
│                                         │
│  [========== 30 days ==========]        │
│  Stocks: AAPL MSFT GOOGL AMZN           │
│                                         │
│  [Start Game 🚀]                        │
└─────────────────────────────────────────┘
```

### Game View

**Layout**:
```
┌─────────────────────────────────────────┐
│ Day 5 of 30          Score: 1,234 (A-) │ ← Fixed Header
├─────────────────────────────────────────┤
│ Your Portfolio                          │
│ Total: $10,500 (+5.0%)                  │
│ Cash: $2,500  Holdings: $8,000          │
│ 🎯 You're beating the AI!               │
├─────────────────────────────────────────┤
│ 🤖 Today's AI Recommendations           │
│ ┌─────────┐ ┌─────────┐                │
│ │ AAPL    │ │ MSFT    │                │
│ │ BUY 75% │ │ HOLD 60%│                │
│ │ [💰 Buy]│ │ [🚫]    │                │
│ └─────────┘ └─────────┘                │
├─────────────────────────────────────────┤
│ Your Holdings                           │
│ AAPL: 10 shares @ $150  [Sell]          │
│ P&L: +$200 (+13.3%)                     │
├─────────────────────────────────────────┤
│ [⏭️ Advance to Day 6]                   │
└─────────────────────────────────────────┘
```

### Game Over

**Features**:
- Final grade (A-F) in large display
- Your performance (final value, return %, trades)
- AI performance (value, return %)
- Score breakdown with explanation
- "Play Again" button

---

## 🧪 Testing the Game

### Prerequisites

1. **Backend API running** with data:
   ```bash
   cd api
   source venv/bin/activate
   python -m app.main
   ```

2. **Game data generated** (at least 10 days):
   ```bash
   # Generate market data
   cd services/market-data
   python -m src.pipelines.daily_market_pipeline --days 30

   # Generate news/sentiment
   cd services/news-sentiment
   python -m src.pipelines.daily_news_pipeline --days 30

   # Generate features
   cd services/feature-store
   python -m src.pipelines.daily_feature_pipeline --days 30

   # Generate recommendations
   cd services/agent-orchestrator
   python -m src.pipelines.daily_agent_pipeline --tickers AAPL MSFT GOOGL AMZN
   ```

3. **Web frontend running**:
   ```bash
   cd web
   pnpm install  # First time only
   pnpm dev
   ```

### Test Flow

1. **Open** http://192.168.5.126:3000
2. **Click** "Start Playing Now! 🚀"
3. **Configure** game (30 days, AAPL/MSFT/GOOGL/AMZN)
4. **Click** "Start Game"
5. **Day 1**: Review AI recommendations
6. **Buy** shares of a BUY recommendation
7. **Click** "Advance Day"
8. **Day 2**: See portfolio updated
9. **Sell** some shares
10. **Click** "Advance Day" multiple times
11. **Complete** all 30 days
12. **View** final score and grade

---

## 🐛 Common Issues

### Issue: "Error loading game data"

**Causes**:
1. Backend API not running
2. No recommendations in database
3. Insufficient data (need at least 10 days)

**Solution**:
```bash
# Check API health
curl http://192.168.5.126:8000/api/v1/health

# Check game endpoint
curl "http://192.168.5.126:8000/api/v1/game/data?days=30"

# If empty, run pipelines to generate data
```

### Issue: "Cannot buy" any stocks

**Cause**: AI is not recommending BUY/STRONG_BUY for any tickers

**Solution**: This is normal! The game enforces that you can only buy when AI says to buy. Wait for a day when AI recommends BUY, or restart with different date range.

### Issue: Trades not executing

**Cause**: Trades execute at **next day's open**, not immediately

**Solution**: This is intentional! Click "Advance Day" to see trades execute.

---

## 🚀 Next Steps (Phase 4 Completion)

### Week 2 Tasks (Remaining)

- [ ] Add trade history view
- [ ] Add portfolio performance chart (Recharts)
- [ ] Add AI vs. Player comparison chart
- [ ] Improve mobile responsiveness
- [ ] Add keyboard shortcuts (Space = Advance Day)

### Week 3: Multiplayer (Phase 4 Goal)

- [ ] Backend: Room creation API
- [ ] Backend: Room join API
- [ ] Backend: Leaderboard API
- [ ] Frontend: Create room flow (teacher)
- [ ] Frontend: Join room flow (student)
- [ ] Frontend: Live leaderboard

### Week 4: Polish & Testing

- [ ] Unit tests for game store logic
- [ ] E2E tests for complete game flow
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Deployment to Vercel

---

## 📝 Implementation Notes

### Why Zustand over Context/Redux?

- **Minimal boilerplate**: No providers, actions, reducers
- **localStorage persistence**: Built-in with `persist` middleware
- **Performance**: Components only re-render when specific state changes
- **DevTools**: Zustand DevTools available
- **Perfect for game state**: Complex state with many actions

### Why Preload All Data?

- **Deterministic gameplay**: No API failures mid-game
- **Instant gameplay**: No loading between days
- **Reproducible**: Same data = same game
- **Offline capable**: Could work without backend after initial load

### Why Turn-Based?

- **Educational focus**: Students learn without time pressure
- **Strategic thinking**: Time to analyze AI recommendations
- **Classroom friendly**: Teacher can pause and discuss
- **Mobile friendly**: No need for constant attention

---

## 📊 Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| Game Lobby | ✅ Complete | With config and loading states |
| Game View | ✅ Complete | All components implemented |
| AI Recommendations | ✅ Complete | With buy validation |
| Portfolio Management | ✅ Complete | Buy/sell with modals |
| Advance Day | ✅ Complete | With trade execution |
| Scoring System | ✅ Complete | All 4 components |
| Grade Calculation | ✅ Complete | A-F grades |
| Game Over Screen | ✅ Complete | With score breakdown |
| Backend API | ✅ Complete | /game/data endpoint |
| Type Safety | ✅ Complete | Full TypeScript coverage |

**Total Lines of Code**: ~2,500 lines for game implementation
**Total Components**: 11 React components
**Total Files Created**: 16 files

---

## 🎓 Educational Value

### Learning Outcomes

Students who play this game will learn:

1. **Stock Market Basics**:
   - What are stocks?
   - How do prices change?
   - What is a portfolio?

2. **Technical Analysis**:
   - Moving averages
   - RSI (overbought/oversold)
   - MACD signals
   - Volatility indicators

3. **Sentiment Analysis**:
   - How news affects stock prices
   - Positive vs. negative sentiment
   - Importance of themes

4. **Risk Management**:
   - Portfolio diversification
   - Position sizing
   - Volatility and risk levels
   - Drawdown management

5. **Strategic Thinking**:
   - When to buy vs. sell
   - Following vs. ignoring recommendations
   - Balancing risk and reward

6. **Performance Metrics**:
   - Return on investment (ROI)
   - Benchmark comparison
   - Win rate
   - Sharpe ratio (future)

---

**Last Updated**: 2025-12-18
**Next Review**: After initial testing
