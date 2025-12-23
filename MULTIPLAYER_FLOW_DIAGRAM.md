# Multiplayer Flow: Before vs After

## ❌ BEFORE (Broken Flow)

```
Student joins room → Room Lobby → Click "Start Playing"
                          ↓
                    startMultiplayerGame() fires (async)
                          ↓
                    Sets: isMultiplayer = true
                          roomCode = "ABC123"
                          gameData = {...}
                          ↓
                    router.push('/game') ← Navigate IMMEDIATELY (doesn't wait!)
                          ↓
                    ┌─────────────────────────────────┐
                    │    /game page loads             │
                    ├─────────────────────────────────┤
                    │ - Reads from localStorage       │
                    │ - isMultiplayer NOT persisted ❌ │
                    │ - gameData NOT persisted ❌      │
                    │ - Assumes SOLO mode             │
                    │ - useGameData() fetches new data│
                    │ - Shows SOLO LOBBY ❌            │
                    └─────────────────────────────────┘
                          ↓
                    Student clicks "Start Game"
                          ↓
                    startGame() called (SOLO MODE)
                          ↓
                    Sets: isMultiplayer = false ❌
                          ↓
                    ┌─────────────────────────────────┐
                    │    Playing in SOLO mode         │
                    ├─────────────────────────────────┤
                    │ - No sync to backend ❌          │
                    │ - Leaderboard not updated ❌     │
                    │ - Results lost ❌                 │
                    └─────────────────────────────────┘
```

---

## ✅ AFTER (Fixed Flow)

```
Student joins room → Room Lobby → Click "Start Playing"
                          ↓
                    setLoading(true)
                          ↓
                    AWAIT startMultiplayerGame() ← Wait for completion!
                          ↓
                    Fetches game data from API
                          ↓
                    Sets: isMultiplayer = true ✅
                          roomCode = "ABC123" ✅
                          gameData = {...} ✅
                          status = 'playing' ✅
                          ↓
                    Persists to localStorage ✅
                          ↓
                    router.push('/game') ← Navigate AFTER data loaded
                          ↓
                    ┌─────────────────────────────────┐
                    │    /game page loads             │
                    ├─────────────────────────────────┤
                    │ useEffect checks:               │
                    │   - isMultiplayer? ✅ true       │
                    │   - gameData? ✅ exists          │
                    │   - status? ✅ 'playing'         │
                    │                                 │
                    │ → setShowLobby(false) ✅         │
                    │ → Skip solo lobby ✅             │
                    │ → useGameData(enabled: false) ✅ │
                    └─────────────────────────────────┘
                          ↓
                    ┌─────────────────────────────────┐
                    │    <GameView /> rendered        │
                    ├─────────────────────────────────┤
                    │ [Purple Banner]                 │
                    │ 🎮 Multiplayer • Room: ABC123   │
                    │    [View Leaderboard →]         │
                    │                                 │
                    │ [Game Interface]                │
                    │ - Charts, recommendations       │
                    │ - Portfolio, holdings           │
                    │ - Advance Day button            │
                    └─────────────────────────────────┘
                          ↓
                    Student makes trades
                          ↓
                    Student clicks "Advance Day"
                          ↓
                    advanceDay() checks: isMultiplayer? ✅
                          ↓
                    Syncs state to backend ✅
                    PUT /api/v1/multiplayer/players/{id}
                          ↓
                    ┌─────────────────────────────────┐
                    │    Backend updates              │
                    ├─────────────────────────────────┤
                    │ - current_day                   │
                    │ - cash, holdings                │
                    │ - portfolio_value               │
                    │ - score, grade                  │
                    │ - total_return_pct              │
                    └─────────────────────────────────┘
                          ↓
                    ┌─────────────────────────────────┐
                    │    Leaderboard updates          │
                    ├─────────────────────────────────┤
                    │ Rank | Name     | Score | Day   │
                    │   1  | Alice    | 520   | 5/21  │
                    │   2  | Student  | 450 ✅ | 3/21  │
                    │   3  | Bob      | 380   | 4/21  │
                    └─────────────────────────────────┘
```

---

## Key Fixes Applied

### 1. **Async/Await Pattern**
```typescript
// BEFORE
const handleStartGame = () => {
  startMultiplayerGame(...);  // Fire and forget ❌
  router.push('/game');       // Navigate immediately ❌
}

// AFTER
const handleStartGame = async () => {
  await startMultiplayerGame(...);  // Wait for completion ✅
  router.push('/game');             // Navigate after data loaded ✅
}
```

### 2. **State Persistence**
```typescript
// BEFORE
partialize: (state) => ({
  config: state.config,
  player: state.player,
  ai: state.ai,
  status: state.status,
  // Missing: isMultiplayer, roomCode, gameData ❌
})

// AFTER
partialize: (state) => ({
  config: state.config,
  player: state.player,
  ai: state.ai,
  status: state.status,
  isMultiplayer: state.isMultiplayer,  // ✅
  roomCode: state.roomCode,            // ✅
  gameData: state.gameData,            // ✅
})
```

### 3. **Conditional Rendering**
```typescript
// BEFORE
if (status === 'not_started' || showLobby) {
  return <GameLobby />;  // Always shows lobby ❌
}

// AFTER
if (status === 'not_started' || (showLobby && !isMultiplayer)) {
  return <GameLobby />;  // Skip lobby for multiplayer ✅
}
```

### 4. **Conditional Data Fetching**
```typescript
// BEFORE
const { data, isLoading, error } = useGameData({
  days: gameConfig.days,
  tickers: gameConfig.tickers,
  // Always fetches ❌
});

// AFTER
const shouldFetch = !isMultiplayer;
const { data, isLoading, error } = useGameData({
  days: gameConfig.days,
  tickers: gameConfig.tickers,
  enabled: shouldFetch,  // Only fetch for solo mode ✅
});
```

---

## State Transitions

### Solo Mode
```
not_started → (user clicks Start) → playing → finished
     ↓              ↓                   ↓
  [Lobby]      [startGame()]       [GameView]
```

### Multiplayer Mode
```
not_started → (join room + click Start Playing) → playing → finished
     ↓                      ↓                          ↓
  [Lobby]        [startMultiplayerGame()]         [GameView]
                  ↓                                    ↓
              [Skip game lobby]                  [Auto-sync]
```

---

## Data Flow

### Solo Mode
```
Component → useGameData → API → loadGameData → Store → UI
```

### Multiplayer Mode
```
Room Lobby → startMultiplayerGame → API → Store → persist → /game page
                                                        ↓
                                                   [reads from store]
                                                        ↓
                                                    GameView
                                                        ↓
                                                   advanceDay
                                                        ↓
                                                   Sync to API
```

---

## Debugging Tips

### Check if Multiplayer Mode is Active
```javascript
// In browser console
const state = JSON.parse(localStorage.getItem('stock-game-storage'));
console.log('Is Multiplayer?', state.state.isMultiplayer);
console.log('Room Code:', state.state.roomCode);
console.log('Status:', state.state.status);
console.log('Has Game Data?', !!state.state.gameData);
```

### Check if Sync is Working
```javascript
// In gameStore.ts advanceDay()
if (state.isMultiplayer && player.playerId) {
  console.log('🔄 Syncing to backend...', {
    playerId: player.playerId,
    currentDay: newPlayerState.currentDay,
    score: newPlayerState.score,
  });
}
```

### Verify Backend Received Update
```bash
# Check leaderboard API
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/ABC123/leaderboard | jq

# Check specific player
curl http://192.168.5.126:8000/api/v1/multiplayer/players/{player-id} | jq
```

---

## Visual Indicators

### Solo Mode
```
┌────────────────────────────────┐
│  Day 1 of 21         350 points  │  ← Blue header
├────────────────────────────────┤
│                                │
│  [Game Interface]              │
│                                │
└────────────────────────────────┘
```

### Multiplayer Mode
```
┌────────────────────────────────┐
│  Day 1 of 21         350 points  │  ← Blue header
├────────────────────────────────┤
│ 🎮 Multiplayer • Room: ABC123  │  ← Purple banner ✅
│     [View Leaderboard →]       │
├────────────────────────────────┤
│                                │
│  [Game Interface]              │
│                                │
└────────────────────────────────┘
```

---

## Expected User Experience

### Teacher
1. Creates room in 10 seconds
2. Gets 6-character code (e.g., "ABC123")
3. Shares with class
4. Views live leaderboard
5. Sees students' progress update in real-time

### Student
1. Enters room code and name
2. Sees lobby with current leaderboard
3. Clicks "Start Playing"
4. **Goes directly to game** (no second lobby ✅)
5. Sees purple banner confirming multiplayer mode ✅
6. Makes trades and advances days
7. Results automatically sync ✅
8. Can check leaderboard anytime via banner link ✅
