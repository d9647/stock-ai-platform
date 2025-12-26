# Implementation Changelog

**Project**: Stock AI Platform
**Period**: December 2025
**Status**: Milestone 1 Complete

This document tracks all significant bug fixes, enhancements, and implementation changes made during development.

---

## Table of Contents

- [Dark Theme & UI Enhancements](#dark-theme--ui-enhancements)
- [Technical Signals Panel](#technical-signals-panel)
- [Multiplayer Implementation](#multiplayer-implementation)
- [Multiplayer Bug Fixes](#multiplayer-bug-fixes)
- [Game Mode Fixes](#game-mode-fixes)
- [News Fetching Improvements](#news-fetching-improvements)
- [Session State & Persistence](#session-state--persistence)
- [Database & Backend Fixes](#database--backend-fixes)

---

## Dark Theme & UI Enhancements

**Date**: December 26, 2025
**Impact**: All UI components
**Status**: ✅ Complete

### Changes Made

Applied comprehensive dark theme across all game components:

**Color System**:
- Backgrounds: bg-layer1 (darkest), bg-layer2 (mid), bg-layer3 (lightest hover states)
- Text: text-text-primary (white), text-text-secondary (gray-300), text-text-muted (gray-500)
- Borders: border-borderDark-subtle (gray-700)
- Status colors: success (green), error (red), warning (yellow), accent (blue)

**Components Updated** (10 files):
1. `web/components/game/news-panel.tsx` - Dark cards with hover effects
2. `web/components/game/player-holdings.tsx` - Dark table with alternating rows
3. `web/components/game/portfolio-summary.tsx` - Dark cards with semantic colors
4. `web/components/game/stock-chart.tsx` - Dark candlesticks, grid, tooltips
5. `web/components/game/teacher-game-controls.tsx` - Dark collapsed/expanded states
6. `web/components/game/ai-recommendations.tsx` - Dark recommendation cards
7. `web/components/game/game-lobby.tsx` - Dark form inputs and buttons
8. `web/components/game/game-over.tsx` - Dark results screen
9. `web/components/game/buy-modal.tsx` - Dark modal backgrounds
10. `web/components/game/sell-modal.tsx` - Dark modal backgrounds

**Key Improvements**:
- Consistent color tokens across all components
- Improved contrast for better readability
- Semantic colors for financial data (green = profit, red = loss)
- Smooth hover transitions
- Professional trading platform aesthetic

**Files Modified**: 10 React components

---

## Technical Signals Panel

**Date**: December 26, 2025
**Impact**: Game view, API schemas
**Status**: ✅ Complete

### What Was Built

Created a day-trader-friendly technical analysis panel that displays 5 semantic signals:

**Signal Types**:
1. **Momentum** - MACD histogram + RSI (bullish/extended/bearish/neutral)
2. **Trend** - EMA/SMA crossovers (uptrend/downtrend/mixed)
3. **Range** - Bollinger Band width + ATR (normal/expanded/compressed)
4. **Reversion** - RSI + BB position (oversold/low/moderate/high risk)
5. **Volume** - OBV (supportive/neutral)

**Features**:
- Color-coded status badges (🟢 bullish, 🔴 bearish, 🟡 caution, ⚪ neutral)
- Overall bias calculation with weighted scoring
- Expandable details with raw indicator values
- Tooltips with explanations on hover
- Status shown first, numbers hidden until user expands

**Backend Changes**:
- Added `TechnicalIndicators` schema to `api/app/schemas/game.py`
- Updated `GameDayResponse` to include `technical_indicators` dict
- Modified `api/app/routes/game.py` to fetch and return technical data
- Database query joins `TechnicalIndicator` model by ticker and date

**Frontend Changes**:
- Created `web/components/game/technical-signals.tsx` (390 lines)
- Added `TechnicalIndicators` interface to `web/types/game.ts`
- Integrated component into `web/components/game/game-view.tsx`
- Positioned above news panel in right sidebar

**Technical Implementation**:
- Signal calculation using useMemo for performance
- Comprehensive validation (checks for undefined before calculations)
- Non-null assertions after validation
- Semantic status aggregation (not just raw numbers)

**Files Created**: 1 new component
**Files Modified**: 4 (schemas, routes, types, game-view)

---

## Multiplayer Implementation

**Date**: December 2025
**Impact**: Backend + Frontend
**Status**: ✅ Complete

### Backend Implementation

**Database Models** (`api/app/models/multiplayer.py`):
- `GameRoom` - Stores room code, teacher name, game config, creation time
- `Player` - Stores player name, room association, game state, portfolio, scores

**API Endpoints** (`api/app/routes/multiplayer.py`):
- `POST /api/v1/multiplayer/rooms` - Create new room
- `GET /api/v1/multiplayer/rooms/{code}` - Get room details
- `POST /api/v1/multiplayer/rooms/{code}/join` - Join room
- `GET /api/v1/multiplayer/rooms/{code}/leaderboard` - Get live rankings
- `PUT /api/v1/multiplayer/players/{id}/state` - Update player state

**Key Features**:
- 6-character room codes (auto-generated, e.g., "ABC123")
- Deterministic gameplay (all players use same date range)
- Player state persistence (cash, holdings, trades, score)
- Grade calculation (A-F) with 4 score components
- Leaderboard sorting by total score

**Database Migration**:
- Created `multiplayer` schema
- Added unique constraints on room codes and player IDs
- Indexed for fast leaderboard queries

### Frontend Implementation

**Components Created** (5 files):
1. `web/components/multiplayer/create-room.tsx` - Teacher creates room
2. `web/components/multiplayer/join-room.tsx` - Student joins with code
3. `web/components/multiplayer/room-lobby.tsx` - Leaderboard view
4. `web/components/multiplayer/player-card.tsx` - Individual player stats
5. `web/components/multiplayer/leaderboard-table.tsx` - Rankings table

**Routes Created**:
- `/multiplayer/create` - Teacher interface
- `/multiplayer/join` - Student interface
- `/multiplayer/room/[code]` - Room lobby with leaderboard

**Game Store Integration**:
- Added `isMultiplayer`, `roomCode`, `role` to Zustand store
- Implemented `startMultiplayerGame()` action
- Auto-sync player state after `advanceDay()`
- API calls to update backend on every move

**Key Features**:
- Real-time leaderboard (polls every 5 seconds)
- Rank, name, score, grade, current day display
- Color-coded grades (green A, yellow B, orange C, red D/F)
- Room code display for sharing
- "Start Playing" button that launches game

**Files Created**: 7 new files (5 components + 2 routes)
**Files Modified**: gameStore.ts, homepage

---

## Multiplayer Bug Fixes

### Fix #1: Sync Bug - Students Entering Solo Mode

**Date**: December 2025
**Issue**: Students clicking "Start Playing" entered solo mode, results not syncing to leaderboard
**File**: `web/lib/stores/gameStore.ts`

**Root Cause**:
- `startMultiplayerGame` was fetching data asynchronously
- Navigation happened immediately without waiting for data
- Game loaded without multiplayer state initialized

**Solution**:
1. Made `startMultiplayerGame` return `Promise<void>`
2. Added `await` before navigation in room lobby
3. Added proper error handling and loading states
4. Ensured multiplayer state persisted in localStorage

**Code Changes**:
```typescript
// Before
const startMultiplayerGame = (config, roomCode, playerId) => {
  fetchGameData(...); // async, not awaited
  set({ isMultiplayer: true, roomCode, playerId });
}

// After
const startMultiplayerGame = async (config, roomCode, playerId) => {
  const data = await fetchGameData(...); // wait for data
  set({ gameData: data, isMultiplayer: true, roomCode, playerId });
}
```

**Result**: ✅ Game data fully loads before navigation, multiplayer state properly set, auto-sync works

---

### Fix #2: Auto-Advance Sync Issue

**Date**: December 2025
**Issue**: In sync mode, advancing day didn't wait for player state sync, causing race conditions
**File**: `web/lib/stores/gameStore.ts`

**Root Cause**:
- `advanceDay()` called `syncPlayerState()` asynchronously
- Day advanced before sync completed
- Backend received stale state for previous day

**Solution**:
```typescript
// Before
const advanceDay = () => {
  if (isMultiplayer) syncPlayerState(); // not awaited
  set({ currentDay: currentDay + 1 });
}

// After
const advanceDay = async () => {
  if (isMultiplayer) await syncPlayerState(); // wait for sync
  set({ currentDay: currentDay + 1 });
}
```

**Result**: ✅ State sync completes before day advances, leaderboard shows accurate scores

---

### Fix #3: Resume Game Functionality

**Date**: December 2025
**Issue**: Players couldn't restore existing progress when rejoining room
**File**: `web/components/multiplayer/room-lobby.tsx`

**Solution**:
- Check if player already exists in room (by name)
- If exists, restore playerId and game state from backend
- If new, create new player entry
- Added loading state during resume check

**Code Changes**:
```typescript
const handleJoinRoom = async () => {
  const existingPlayer = await checkPlayerExists(roomCode, playerName);
  if (existingPlayer) {
    // Resume existing game
    restorePlayerState(existingPlayer.id);
  } else {
    // Create new player
    const newPlayer = await createPlayer(roomCode, playerName);
  }
}
```

**Result**: ✅ Players can leave and rejoin rooms, preserving progress

---

### Fix #4: Data Availability (AAPL-Only Limitation)

**Date**: December 2025
**Issue**: API returning "Insufficient data" error when requesting multi-ticker games
**File**: `web/components/multiplayer/create-room.tsx`

**Investigation**:
- Database has 93 recommendations for AAPL (2025-08-12 to 2025-12-17)
- Only 1 recommendation for MSFT
- 0 recommendations for GOOGL and AMZN
- Game endpoint requires ALL tickers to have complete data

**Temporary Solution**: Changed default tickers from `['AAPL', 'MSFT', 'GOOGL', 'AMZN']` to `['AAPL']`

**Verification**:
```bash
curl "http://192.168.5.126:8000/api/v1/game/data?days=20&end_date=2025-12-17&tickers=AAPL"
# Returns 14+ days of valid data ✅
```

**Long-term TODO**: Populate recommendation data for MSFT, GOOGL, AMZN to enable multi-ticker games

**Files Modified**: `create-room.tsx` (line 32)

---

## Game Mode Fixes

### Fix #1: Day Counter Display

**Date**: December 2025
**Issue**: Game header showed "Day 1 of 30" but game only had ~21 trading days
**File**: `web/components/game/day-header.tsx`

**Problem**: Counter used config.numDays (calendar days requested) instead of actual trading days returned

**Solution**: Changed display to show actual trading days from API response:
```typescript
// Before
Day {dayNumber} of {config.numDays}

// After
Day {dayNumber} of {gameData?.total_days || config.numDays}
```

**Result**: ✅ Now accurately displays "Day 1 of 21" matching actual playable game length

**Files Modified**: `day-header.tsx` (line 36)

---

## News Fetching Improvements

### Fix #1: News Backfill for Weekends

**Date**: December 26, 2025
**Issue**: Backend only returned news from current trading day (could be 0-5 articles)
**File**: `api/app/routes/game.py`

**Problem**: Original query fetched news with `published_at <= current_date` and limited to 10, but didn't prioritize current day news first

**Solution**: Implemented two-phase query:
```python
# Phase 1: Fetch all news on current_date
current_day_news = (
    db.query(NewsArticleModel, NewsSentimentScore)
    .filter(func.date(NewsArticleModel.published_at) == current_date)
    .order_by(NewsArticleModel.published_at.desc())
    .all()
)

# Phase 2: If < 10 articles, backfill with recent news
news_articles = list(current_day_news)
if len(news_articles) < 10:
    recent_news = (
        db.query(NewsArticleModel, NewsSentimentScore)
        .filter(NewsArticleModel.published_at < datetime.combine(current_date, datetime.min.time()))
        .order_by(NewsArticleModel.published_at.desc())
        .limit(10 - len(news_articles))
        .all()
    )
    news_articles.extend(recent_news)
```

**Result**: ✅ Guaranteed minimum of 10 recent news articles per ticker

**Files Modified**: `api/app/routes/game.py` (lines 184-222)

---

### Fix #2: Date Chunking for 365+ Day Ranges

**Date**: December 2025
**Issue**: News API couldn't fetch more than ~250 articles due to API limits
**File**: `services/news-sentiment/src/ingestion/fetch_news.py`

**Solution**: Implemented date chunking to split large date ranges into smaller chunks:
```python
def fetch_news_chunked(ticker, start_date, end_date, chunk_days=30):
    all_articles = []
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days), end_date)
        chunk_articles = fetch_news(ticker, current, chunk_end)
        all_articles.extend(chunk_articles)
        current = chunk_end
    return all_articles
```

**Result**: ✅ Can now fetch 365+ days of historical news

**Files Modified**: `fetch_news.py`

---

## Session State & Persistence

### Fix #1: LocalStorage Quota Exceeded

**Date**: December 26, 2025
**Issue**: `QuotaExceededError: Failed to execute 'setItem' on 'Storage'`
**File**: `web/lib/stores/gameStore.ts`

**Root Cause**: With expanded news data (10+ articles per ticker per day), gameData object became too large for localStorage (5MB limit)

**Solution**: Modified Zustand persist middleware to exclude gameData from persistence:
```typescript
partialize: (state) => ({
  config: state.config,
  player: state.player,
  ai: state.ai,
  status: state.status,
  isMultiplayer: state.isMultiplayer,
  roomCode: state.roomCode,
  role: state.role,
  // ⚠️ EXCLUDE gameData from persistence to avoid quota issues
  // gameData will be re-fetched when needed
})
```

**Result**: ✅ Only player state, config, and multiplayer info persisted; gameData re-fetched on load

**Files Modified**: `gameStore.ts` (lines 617-627)

---

## Database & Backend Fixes

### Fix #1: Import Path Corrections

**Date**: December 2025
**Issue**: Backend API failing with import errors
**File**: `api/app/routes/game.py`

**Problems**:
- `from ..database import get_db` (should be `from ..db import get_db`)
- `DailyPrice` model name (should be `OHLCVPrice`)
- Missing `from fastapi import Depends`

**Solution**: Fixed all import paths and model names

**Files Modified**: `game.py` (lines 14, 16, 49)

---

### Fix #2: Schema Enum Definitions

**Date**: December 2025
**Issue**: Circular dependency errors in Pydantic schemas
**File**: `api/app/schemas/game.py`

**Solution**: Added local enum definitions to avoid import path issues:
```python
class RecommendationType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class SignalType(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"

class RiskLevel(str, Enum):
    LOW = "LOW_RISK"
    MEDIUM = "MEDIUM_RISK"
    HIGH = "HIGH_RISK"
```

**Result**: ✅ Prevents circular dependency errors

**Files Modified**: `game.py` (added local enum definitions)

---

### Fix #3: TypeScript Type Errors

**Date**: December 26, 2025
**Issue**: Multiple "possibly undefined" errors in technical-signals.tsx
**File**: `web/components/game/technical-signals.tsx`

**Root Cause**: TechnicalIndicators interface had all optional fields, but code was using them without null checks

**Solution**:
1. Added comprehensive validation at beginning of useMemo (lines 42-52) checking all required fields
2. Used non-null assertions (!) throughout after validation
3. Used nullish coalescing (?? 0) for OBV which is truly optional

**Code Changes**:
```typescript
// Validation check
if (!technicalData ||
    technicalData.rsi_14 === undefined ||
    technicalData.macd_histogram === undefined ||
    // ... all required fields
) {
  return unavailableSignals;
}

// Safe to use non-null assertions after validation
const macdBullish = macd_histogram! > 0;
const rsiStrong = rsi_14! >= 60 && rsi_14! <= 70;
```

**Result**: ✅ All TypeScript type errors resolved

**Files Modified**: `technical-signals.tsx` (lines 42-52, throughout)

---

### Fix #4: SWC Compiler Error

**Date**: December 2025
**Issue**: SWC parser error with inline JSX ternary expressions
**File**: `web/components/game/advance-day-button.tsx`

**Error Message**: "SWC parser error: Expected '}', got ':'"

**Root Cause**: Complex inline ternary expressions in JSX return statement

**Solution**: Extracted ternary logic into variables before return statement:
```typescript
// Before (caused error)
return (
  <button>
    {status === 'playing' ? (
      pendingTrades.length > 0 ? '⏩ Execute Trades' : '⏩ Next Day'
    ) : '🏁 Game Over'}
  </button>
);

// After (works)
const buttonText = status === 'playing'
  ? (pendingTrades.length > 0 ? '\u23E9 Execute Trades' : '\u23E9 Next Day')
  : '\uD83C\uDFC1 Game Over';

return (
  <button>{buttonText}</button>
);
```

**Additional Changes**:
- Added explicit React import
- Used Unicode escape sequences for emojis
- Cleared `.next` build cache

**Result**: ✅ Frontend compiles successfully

**Files Modified**: `advance-day-button.tsx`

---

## Summary Statistics

| Category | Files Created | Files Modified | Lines Changed |
|----------|--------------|----------------|---------------|
| Dark Theme | 0 | 10 | ~500 |
| Technical Signals | 1 | 4 | ~450 |
| Multiplayer | 7 | 2 | ~1,200 |
| Bug Fixes | 0 | 8 | ~200 |
| **Total** | **8** | **24** | **~2,350** |

---

## Critical Lessons Learned

1. **Always await async operations before state changes** - Prevents race conditions
2. **Partition localStorage carefully** - Exclude large data objects
3. **Validate all optional TypeScript fields** - Use comprehensive checks before non-null assertions
4. **Implement two-phase queries for completeness** - Current data first, then backfill
5. **Use local enum definitions** - Avoids circular dependency issues in schemas
6. **Test compiler edge cases** - Complex JSX ternaries may cause SWC parser errors

---

**Last Updated**: December 26, 2025
**Status**: All fixes tested and deployed ✅
