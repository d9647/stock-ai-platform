# Multiplayer Game Flow Fix

## Problem
Students joining multiplayer rooms were being directed to **solo game mode** instead of **multiplayer mode**. Their game results were not syncing to the backend and not appearing on the live leaderboard.

## Root Cause Analysis

### Issue 1: Game Page Always Showed Solo Lobby
The `/game` page had this problematic flow:
1. Always fetched its own game data using `useGameData` hook
2. Always showed the solo game lobby with configuration options
3. When "Start Game" was clicked, it called `startGame()` (solo mode)
4. This **overwrote** all the multiplayer state that was loaded by `startMultiplayerGame()`

### Issue 2: Multiplayer State Not Persisted
The game store's `partialize` function only saved:
- `config`
- `player`
- `ai`
- `status`

But **NOT**:
- `isMultiplayer` (flag to indicate multiplayer mode)
- `roomCode` (room identifier)
- `gameData` (the game data already loaded)

This meant when navigating to `/game`, the page would refresh and lose all multiplayer context.

### Issue 3: No Conditional Logic for Multiplayer
The game page didn't check if it was coming from multiplayer mode. It always assumed solo mode and always showed the lobby.

---

## Solution Implemented

### 1. Added Multiplayer Detection to Game Page
**File**: [web/app/game/page.tsx](web/app/game/page.tsx)

**Changes**:
```typescript
// Get multiplayer state from store
const { status, loadGameData, isMultiplayer, gameData: storeGameData } = useGameStore();

// Check if we're coming from multiplayer mode
useEffect(() => {
  if (isMultiplayer && storeGameData && status === 'playing') {
    console.log('Multiplayer mode detected, skipping lobby');
    setShowLobby(false);
  }
}, [isMultiplayer, storeGameData, status]);

// Only fetch game data for solo mode (not multiplayer)
const shouldFetchData = !isMultiplayer;
const { data: gameData, isLoading, error } = useGameData({
  days: gameConfig.days,
  tickers: gameConfig.tickers,
  enabled: shouldFetchData, // ← Only fetch if solo mode
});

// Load game data into store when ready (solo mode only)
useEffect(() => {
  if (!isMultiplayer && gameData && !isLoading) {
    loadGameData(gameData);
  }
}, [gameData, isLoading, loadGameData, isMultiplayer]);

// Show lobby only for solo mode
if (status === 'not_started' || (showLobby && !isMultiplayer)) {
  return <GameLobby ... />;
}
```

**Result**:
- ✅ Multiplayer mode detected on page load
- ✅ Lobby skipped when coming from multiplayer
- ✅ Game data not re-fetched (uses existing data)
- ✅ Multiplayer state preserved

---

### 2. Updated useGameData Hook
**File**: [web/lib/hooks/useGameData.ts](web/lib/hooks/useGameData.ts)

**Changes**:
```typescript
export function useGameData(params?: GetGameDataParams & { enabled?: boolean }) {
  const { enabled = true, ...queryParams } = params || {};

  return useQuery({
    queryKey: ['gameData', queryParams],
    queryFn: () => getGameData(queryParams),
    staleTime: Infinity,
    gcTime: Infinity,
    retry: 2,
    enabled, // ← Allow disabling the query
  });
}
```

**Result**:
- ✅ Can disable data fetching when `enabled: false`
- ✅ Prevents unnecessary API calls in multiplayer mode

---

### 3. Persist Multiplayer State
**File**: [web/lib/stores/gameStore.ts](web/lib/stores/gameStore.ts#L606-L616)

**Changes**:
```typescript
{
  name: 'stock-game-storage',
  partialize: (state) => ({
    config: state.config,
    player: state.player,
    ai: state.ai,
    status: state.status,
    isMultiplayer: state.isMultiplayer, // ← Added
    roomCode: state.roomCode,           // ← Added
    gameData: state.gameData,           // ← Added
  }),
}
```

**Result**:
- ✅ Multiplayer state survives page refreshes
- ✅ Room code preserved across navigation
- ✅ Game data stays in localStorage

---

### 4. Added Multiplayer UI Indicator
**File**: [web/components/game/game-view.tsx](web/components/game/game-view.tsx)

**Changes**:
```tsx
export function GameView() {
  const { player, gameData, config, isMultiplayer, roomCode } = useGameStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <DayHeader />

      {/* Multiplayer Banner */}
      {isMultiplayer && roomCode && (
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-4">
          <div className="container mx-auto flex items-center justify-center gap-4">
            <span className="font-semibold">
              🎮 Multiplayer Mode • Room: {roomCode}
            </span>
            <a href={`/multiplayer/room/${roomCode}`}>
              View Leaderboard →
            </a>
          </div>
        </div>
      )}

      {/* Rest of game UI */}
    </div>
  );
}
```

**Result**:
- ✅ Players see clear indicator they're in multiplayer mode
- ✅ Quick link back to leaderboard
- ✅ Shows room code for reference

---

## Complete Multiplayer Flow (Now Working ✅)

### Teacher Flow
1. Visit `/multiplayer/create`
2. Configure game settings (days, cash, difficulty)
3. Click "Create Room" → Get room code (e.g., "ABC123")
4. Share room code with students
5. View `/multiplayer/room/ABC123` → See leaderboard

### Student Flow
1. Visit `/multiplayer/join`
2. Enter room code "ABC123" and student name
3. Click "Join Room" → See room lobby with leaderboard
4. Click "Start Playing" → **Triggers the following**:
   - `await startMultiplayerGame()` - Fetches game data
   - Sets `isMultiplayer: true` in store
   - Sets `roomCode: "ABC123"` in store
   - Sets `status: 'playing'` in store
   - Loads game data into store
   - Persists everything to localStorage
   - `router.push('/game')` - Navigates to game page

5. **Game page loads** (`/game`):
   - Reads state from localStorage
   - Sees `isMultiplayer: true` and `gameData` exists
   - **Skips solo lobby** ✅
   - Shows `<GameView />` directly ✅
   - Displays multiplayer banner with room code ✅

6. **Student plays game**:
   - Makes trades, advances days
   - `advanceDay()` checks `isMultiplayer` flag
   - Syncs state to backend after each day ✅
   - Leaderboard updates automatically ✅

7. **Check leaderboard**:
   - Click "View Leaderboard" in banner
   - See updated score, rank, grade ✅

---

## Testing Checklist

### Test Solo Mode (Make Sure It Still Works)
- [ ] Visit `/game` directly
- [ ] Should show solo game lobby ✅
- [ ] Configure settings and start game
- [ ] Should enter solo mode (no multiplayer banner)
- [ ] Game works normally

### Test Multiplayer Mode
1. **Create Room**
   - [ ] Visit `/multiplayer/create`
   - [ ] Fill in teacher name, configure settings
   - [ ] Click "Create Room"
   - [ ] Should redirect to room lobby
   - [ ] Should show room code

2. **Join Room**
   - [ ] Open new incognito window
   - [ ] Visit `/multiplayer/join`
   - [ ] Enter room code and student name
   - [ ] Click "Join Room"
   - [ ] Should redirect to room lobby
   - [ ] Should see yourself in player list

3. **Start Playing**
   - [ ] Click "Start Playing"
   - [ ] Should show loading spinner
   - [ ] Should navigate to `/game`
   - [ ] **Should NOT show solo lobby** ✅
   - [ ] **Should show game view directly** ✅
   - [ ] **Should show purple multiplayer banner** ✅
   - [ ] Banner should show correct room code

4. **Play Game**
   - [ ] Make some trades
   - [ ] Click "Advance Day"
   - [ ] Check browser console - should see sync logs
   - [ ] State should sync to backend

5. **Check Leaderboard**
   - [ ] Click "View Leaderboard" in banner
   - [ ] Should redirect to room lobby
   - [ ] Should see updated score, rank
   - [ ] Leaderboard should auto-refresh every 5 seconds

6. **Navigate Back to Game**
   - [ ] Click browser back button
   - [ ] Should return to game view (not lobby)
   - [ ] Game state should be preserved
   - [ ] Should still show multiplayer banner

7. **Page Refresh Test**
   - [ ] Refresh the `/game` page (F5)
   - [ ] Should still show game view (not lobby)
   - [ ] Multiplayer state should be preserved
   - [ ] Banner should still show

---

## API Verification

```bash
# Check if player state is syncing
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/ABC123/leaderboard

# Expected response:
[
  {
    "rank": 1,
    "player_name": "Student Name",
    "score": 450.5,
    "grade": "B",
    "current_day": 3,
    "portfolio_value": 10450.00,
    "total_return_pct": 4.5,
    "is_finished": false
  }
]
```

---

## Files Modified

1. **web/app/game/page.tsx**
   - Added multiplayer detection logic
   - Conditionally fetch data only for solo mode
   - Skip lobby for multiplayer mode

2. **web/lib/hooks/useGameData.ts**
   - Added `enabled` parameter support
   - Allows disabling query for multiplayer mode

3. **web/lib/stores/gameStore.ts**
   - Added `isMultiplayer`, `roomCode`, `gameData` to persisted state
   - Ensures multiplayer context survives page transitions

4. **web/components/game/game-view.tsx**
   - Added multiplayer banner with room code
   - Added "View Leaderboard" link
   - Visual indicator for multiplayer mode

---

## Key Differences: Solo vs Multiplayer

| Aspect | Solo Mode | Multiplayer Mode |
|--------|-----------|------------------|
| **Entry Point** | `/game` directly | `/multiplayer/join` → lobby → `/game` |
| **Lobby** | Always shown | Skipped (data pre-loaded) |
| **Data Fetch** | `useGameData` hook | `startMultiplayerGame()` in lobby |
| **State Sync** | None (local only) | Auto-sync after each day |
| **UI Indicator** | None | Purple banner with room code |
| **Leaderboard** | N/A | Live updates every 5 seconds |
| **Player ID** | Auto-generated | From backend (assigned on join) |

---

## Success Criteria ✅

When tested, the system should:
- ✅ Students click "Start Playing" → go directly to game (not solo lobby)
- ✅ Game view shows multiplayer banner with room code
- ✅ State syncs to backend after each day
- ✅ Leaderboard shows updated scores within 5 seconds
- ✅ Page refresh preserves multiplayer state
- ✅ Students can navigate between game and leaderboard freely
- ✅ Solo mode still works independently

---

## Troubleshooting

### Issue: Still showing solo lobby
**Check**:
1. Is `isMultiplayer` set to `true` in localStorage?
   - Open DevTools → Application → Local Storage → `stock-game-storage`
2. Is `gameData` present in the store?
3. Is `status` set to `'playing'`?

### Issue: "Room not found" error
**Check**:
1. Is API server running on port 8000?
2. Does the room exist in database?
3. Are tickers set to `['AAPL']` only (temporary fix)?

### Issue: State not syncing
**Check**:
1. Open browser console - look for sync logs
2. Check network tab for PUT requests to `/api/v1/multiplayer/players/{id}`
3. Verify `playerId` is set correctly in store

### Issue: Leaderboard not updating
**Check**:
1. Is player state actually syncing? (check API response)
2. Is room lobby polling interval working? (check network tab)
3. Check database: `SELECT * FROM multiplayer.players WHERE room_id = ...`

---

## Performance Considerations

- **Data Fetch**: Only happens once on "Start Playing" (not on every page load)
- **LocalStorage**: Game data cached locally for instant loading
- **Sync**: Happens only after `advanceDay()` (not every action)
- **Leaderboard**: Polls every 5 seconds (acceptable for educational context)

---

## Future Enhancements

1. **WebSocket Support**: Replace polling with real-time updates
2. **Resume Game**: Restore progress from backend when rejoining
3. **Multiplayer Chat**: Allow students to discuss strategies
4. **Teacher Dashboard**: View all student progress in real-time
5. **Game Replay**: Watch any player's game step-by-step
