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

## 🏫 Multiplayer Classroom Mode

### Overview

Multiplayer mode enables teachers to create game rooms where students compete on identical game scenarios with a live leaderboard. This creates an engaging classroom environment where students learn trading strategies while competing for the best portfolio performance.

### Key Features

**✅ Deterministic Gameplay**
- All players in a room play the exact same game
- Same start/end dates, tickers, and AI recommendations
- Ensures fair competition

**✅ Real-Time Leaderboard**
- Automatically updates every 5 seconds
- Ranks by score (same algorithm as solo mode)
- Shows progress, grade, and returns

**✅ Persistent State**
- Player credentials stored in localStorage
- Game state synced to backend after each day
- Can close browser and resume later

**✅ Three Game Modes**
1. **Async Mode**: Students play at their own pace
2. **Sync Manual**: Teacher manually advances each day for the entire class
3. **Sync Auto**: Timer automatically advances days for synchronized play

### Architecture

**Backend Components**:
- `multiplayer` schema in PostgreSQL
- `game_rooms` table with auto-generated 6-character room codes
- `players` table with complete game state storage
- RESTful API endpoints for room management

**Frontend Components**:
- Create Room (teachers)
- Join Room (students)
- Room Lobby with live leaderboard
- Sync Banner for real-time coordination
- Teacher Dashboard for room control

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/multiplayer/rooms` | POST | Create new room (teacher) |
| `/api/v1/multiplayer/rooms/join` | POST | Join existing room (student) |
| `/api/v1/multiplayer/rooms/{code}` | GET | Get room details and players |
| `/api/v1/multiplayer/rooms/{code}/leaderboard` | GET | Get ranked leaderboard |
| `/api/v1/multiplayer/players/{id}` | PUT | Update player state after each day |
| `/api/v1/multiplayer/rooms/{code}/start` | POST | Start game (teacher control) |
| `/api/v1/multiplayer/rooms/{code}/advance-day` | POST | Advance all players (sync mode) |
| `/api/v1/multiplayer/rooms/{code}/end-game` | POST | End game for all players |
| `/api/v1/multiplayer/rooms/{code}/set-timer` | POST | Set day timer (sync auto mode) |
| `/api/v1/multiplayer/players/{id}/ready` | POST | Mark player ready for next day |

### User Flows

**Teacher Flow**:
1. Click "Create Classroom" on home page
2. Enter name, optional room name, configure game settings
3. Select game mode (async, sync manual, or sync auto)
4. Click "Create Room" → generates room code (e.g., "ABC123")
5. Share room code with students
6. View leaderboard and monitor student progress
7. (Sync modes) Control game progression via dashboard
8. Students' scores update automatically as they play

**Student Flow**:
1. Click "Join Classroom" on home page
2. Enter room code from teacher
3. Enter name (and optional email)
4. Click "Join Room" → enters room lobby
5. View current rank and leaderboard
6. Click "Start Playing" or "Continue Game"
7. Play game normally - state syncs automatically
8. (Sync modes) Wait for teacher to advance days
9. Check leaderboard to see ranking vs classmates

### Game Modes Explained

**Async Mode**:
- Students progress independently at their own pace
- No teacher control over day advancement
- Perfect for homework assignments or flexible classroom activities
- Students can work ahead or catch up as needed
- Leaderboard updates as students complete days

**Sync Manual Mode**:
- Teacher manually advances all players to next day
- Entire class experiences each trading day together
- Great for guided instruction and group discussions
- Teacher controls pacing based on classroom needs
- "Ready" system shows which students finished trading

**Sync Auto Mode**:
- Timer automatically advances to next day
- Teacher sets duration (e.g., 5 minutes per trading day)
- Creates time pressure and excitement
- Countdown timer visible to all students
- Automatic advancement when timer expires

### Leaderboard Features

**Display Information**:
- Rank (with medals for top 3: 🥇🥈🥉)
- Player name with "You" badge for current player
- Portfolio value
- Total return percentage
- Score and grade
- Current day / total days
- "Finished" badge for completed players
- AI Agent benchmark for comparison

**Sorting Options**:
- By score (default)
- By portfolio value
- By return percentage
- By progress (current day)

**Real-Time Updates**:
- Polls server every 5 seconds
- Instant rank changes when players advance
- Color-coded performance (green for gains, red for losses)

### Teacher Dashboard

**Game Control**:
- View all players in room
- See who's finished vs still playing
- Monitor day-by-day progress
- (Sync modes) Control day advancement
- Set timers for auto-advance
- End game for all players

**Analytics**:
- Room status (waiting, in_progress, finished)
- Player count and participation
- Average score and grade distribution
- AI benchmark comparison
- Ready player counter (sync manual mode)

### Database Schema

**game_rooms Table**:
```sql
- id (UUID, primary key)
- room_code (6-char string, unique)
- created_by (teacher name)
- room_name (optional)
- config (JSON: initial_cash, num_days, tickers, difficulty)
- start_date, end_date (game date range)
- status (waiting, in_progress, finished)
- game_mode (async, sync, sync_auto)
- current_day (sync modes only)
- day_time_limit (seconds, sync auto mode)
- created_at, started_at, finished_at
```

**players Table**:
```sql
- id (UUID, primary key)
- room_id (foreign key to game_rooms)
- player_name
- player_email (optional)
- current_day
- cash, holdings (JSON)
- portfolio_value
- total_return_pct, total_return_usd
- score, grade
- is_ready (sync modes)
- is_finished
- portfolio_history (JSON array)
- joined_at, last_action_at
```

### State Synchronization

After each day advancement:
1. Frontend calculates new portfolio state
2. Calculates updated score and grade
3. PUTs complete state to backend
4. Backend updates player record
5. Leaderboard recalculates rankings
6. Other students see updated leaderboard on next poll

### Files Created/Modified

**Backend Files**:
- `api/app/models/multiplayer.py` - SQLAlchemy models
- `api/app/routes/multiplayer.py` - API endpoints
- `api/app/schemas/multiplayer.py` - Pydantic schemas
- `api/migrations/versions/*_add_multiplayer_schema.py` - Database migration

**Frontend Files**:
- `web/lib/api/multiplayer.ts` - API client
- `web/components/multiplayer/create-room.tsx` - Teacher setup
- `web/components/multiplayer/join-room.tsx` - Student join
- `web/components/multiplayer/room-lobby.tsx` - Lobby with leaderboard
- `web/components/multiplayer/leaderboard.tsx` - Full leaderboard page
- `web/components/multiplayer/teacher-dashboard.tsx` - Teacher controls
- `web/components/game/sync-banner.tsx` - Sync mode coordination
- `web/app/multiplayer/create/page.tsx` - Create room page
- `web/app/multiplayer/join/page.tsx` - Join room page
- `web/app/multiplayer/room/[code]/page.tsx` - Room lobby page
- `web/app/multiplayer/leaderboard/[code]/page.tsx` - Full leaderboard

**Store Updates**:
- `web/lib/stores/gameStore.ts` - Added multiplayer state and actions

### Testing Multiplayer

**Backend Testing**:
```bash
# Create room
curl -X POST http://localhost:8000/api/v1/multiplayer/rooms \
  -H "Content-Type: application/json" \
  -d '{"created_by":"Test Teacher","room_name":"Demo Room"}'

# Join room
curl -X POST http://localhost:8000/api/v1/multiplayer/rooms/join \
  -H "Content-Type: application/json" \
  -d '{"room_code":"ABC123","player_name":"Student 1"}'

# Get leaderboard
curl http://localhost:8000/api/v1/multiplayer/rooms/ABC123/leaderboard
```

**Frontend Testing**:
1. Open browser at http://localhost:3000
2. Click "Create Classroom"
3. Create room with specific settings
4. Copy room code
5. Open incognito window
6. Click "Join Classroom"
7. Enter room code as different student
8. Both windows should see leaderboard
9. Students play and advance
10. Leaderboard updates automatically

### Educational Benefits

**Motivation Through Competition**:
- Students naturally motivated to improve their rank
- Peer comparison encourages strategic thinking
- Friendly competition makes learning engaging

**Collaborative Learning**:
- Students can discuss strategies between days (async mode)
- Teacher can pause and facilitate group discussions (sync modes)
- Students learn from observing different approaches

**Accountability**:
- Visible progress tracking encourages completion
- Teacher can monitor who needs help
- "Ready" system shows engagement level

**Fair Assessment**:
- Identical game data ensures fairness
- AI benchmark provides objective standard
- Score breakdown reveals strategic decisions

### Privacy and Security

**Minimal Data Collection**:
- No authentication required
- Optional email (for notifications only)
- No sensitive personal information stored

**Room Code Security**:
- 6-character codes provide 2.2 billion combinations
- Rooms expire after completion
- No public room listing (must know code to join)

**Data Lifecycle**:
- Room data persists for grading purposes
- Teacher can export results
- Optional data retention policies

### Scalability

**Database Design**:
- Indexed room codes for fast lookups
- Player state updates are atomic
- Leaderboard queries optimized with SQL ranking

**API Performance**:
- Stateless endpoints for horizontal scaling
- Efficient JSON payloads
- Caching opportunities for room data

**Frontend Efficiency**:
- 5-second polling interval balances freshness and load
- Only fetches diff data where possible
- localStorage caching for player credentials

### Future Enhancements

**Planned Features**:
- WebSocket support for instant updates
- Room analytics dashboard for teachers
- Custom ticker selection per room
- Time limits and deadlines
- Achievement badges
- CSV export for gradebook integration
- In-room chat/discussions
- Replay mode to watch any player's game

**Integration Possibilities**:
- LMS integration (Canvas, Blackboard, Moodle)
- Single sign-on (SSO)
- Grade passback
- Attendance tracking

---

**Last Updated**: 2025-12-28
**Next Review**: After multiplayer testing in classroom environment
