# Multiplayer Testing Guide

## Prerequisites

### Backend Server
```bash
# Terminal 1 - Start API server
cd api
./venv/bin/python -m app.main

# Should show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend Server
```bash
# Terminal 2 - Start Next.js dev server
cd web
npm run dev

# Should show:
# ▲ Next.js 14.x.x
# - Local:        http://192.168.5.126:3000
```

### Verify API is Running
```bash
curl http://192.168.5.126:8000/health
# Expected: {"status":"healthy"}
```

---

## Test 1: Solo Mode (Baseline Test)

**Purpose**: Ensure solo mode still works after multiplayer changes

### Steps
1. Open browser: `http://192.168.5.126:3000`
2. Click **"Play Solo 🎮"**
3. **EXPECT**: Should show game lobby with configuration options ✅
4. Click **"Start Game 🚀"**
5. **EXPECT**: Should show game view (charts, recommendations, etc.) ✅
6. **EXPECT**: Should NOT show purple multiplayer banner ✅
7. Make a trade, click "Advance Day"
8. **EXPECT**: Game should advance normally ✅

### Success Criteria
- ✅ Lobby appears
- ✅ Game starts normally
- ✅ No multiplayer banner
- ✅ No console errors

---

## Test 2: Create Multiplayer Room

**Purpose**: Verify teacher can create a room

### Steps
1. Open browser: `http://192.168.5.126:3000`
2. Click **"👨‍🏫 Create Classroom"**
3. Fill in form:
   - Teacher Name: `"Test Teacher"`
   - Room Name: `"Period 3 Economics"` (optional)
   - Game Duration: `30 days`
   - Starting Cash: `$10,000`
   - Difficulty: `Medium`
4. Click **"Create Room"**

### Expected Results
- ✅ Loading spinner appears briefly
- ✅ Redirects to `/multiplayer/room/XXXXXX` (6-char code)
- ✅ Room lobby page shows:
  - Room code in header
  - Game settings displayed
  - Empty leaderboard (or just teacher if they auto-joined)
  - "Copy Room Code" button
  - "Start Playing" button

### Verify in Console
```javascript
// Open browser DevTools → Console
// Should see no errors

// Check localStorage
const state = JSON.parse(localStorage.getItem('multiplayer_room_code'));
console.log('Room Code:', state); // Should show the 6-char code
```

### Verify in API
```bash
# Replace XXXXXX with actual room code
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/XXXXXX

# Expected response:
{
  "id": "...",
  "room_code": "XXXXXX",
  "created_by": "Test Teacher",
  "room_name": "Period 3 Economics",
  "status": "waiting",
  "config": {
    "numDays": 30,
    "initialCash": 10000,
    "tickers": ["AAPL"],
    "difficulty": "medium"
  },
  "players": [],
  ...
}
```

---

## Test 3: Join Multiplayer Room as Student

**Purpose**: Verify student can join with room code

### Steps
1. Open **NEW INCOGNITO WINDOW**: `http://192.168.5.126:3000`
   - (This simulates a different student)
2. Click **"👨‍🎓 Join Classroom"**
3. Fill in form:
   - Room Code: `XXXXXX` (from Test 2)
   - Student Name: `"Alice"`
   - Email: (leave blank or fill in)
4. Click **"Join Room"**

### Expected Results
- ✅ Loading spinner appears
- ✅ Redirects to `/multiplayer/room/XXXXXX`
- ✅ Room lobby shows:
  - Student's name in leaderboard
  - Rank: 1 (or 2 if teacher joined)
  - Score: 0 points
  - Grade: C
  - Progress: 0/21 days
  - "Start Playing" button

### Verify in API
```bash
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/XXXXXX/leaderboard

# Expected response:
[
  {
    "rank": 1,
    "player_id": "...",
    "player_name": "Alice",
    "score": 0,
    "grade": "C",
    "current_day": 0,
    "portfolio_value": 10000,
    "total_return_pct": 0,
    "total_return_usd": 0,
    "is_finished": false
  }
]
```

---

## Test 4: Start Playing (CRITICAL TEST)

**Purpose**: Verify student enters multiplayer mode correctly

### Steps
1. In student's incognito window (from Test 3)
2. On room lobby page, click **"Start Playing"**

### Expected Results - Phase 1: Loading
- ✅ Button changes to "Starting game..."
- ✅ Loading spinner appears
- ✅ Button is disabled during load

### Expected Results - Phase 2: Navigation
- ✅ After ~1-2 seconds, redirects to `/game`
- ✅ **SHOULD NOT SHOW SOLO LOBBY** ❌ (This was the bug!)
- ✅ **SHOULD SHOW GAME VIEW DIRECTLY** ✅

### Expected Results - Phase 3: Game View
- ✅ Shows blue day header: "Day 1 of 21"
- ✅ Shows **purple multiplayer banner**:
  ```
  🎮 Multiplayer Mode • Room: XXXXXX
      [View Leaderboard →]
  ```
- ✅ Shows game interface (charts, recommendations, holdings)
- ✅ Shows "Advance to Next Day" button

### Browser Console Verification
```javascript
// Open DevTools → Console
// Should see:
"Multiplayer mode detected, skipping lobby"
"Fetching game data from: http://192.168.5.126:8000/api/v1/game/data?..."
"Game data loaded successfully: 21 days"

// Check localStorage
const state = JSON.parse(localStorage.getItem('stock-game-storage')).state;
console.log('Is Multiplayer?', state.isMultiplayer);  // ✅ true
console.log('Room Code:', state.roomCode);            // ✅ "XXXXXX"
console.log('Player ID:', state.player.playerId);     // ✅ UUID
console.log('Status:', state.status);                 // ✅ "playing"
console.log('Has Game Data?', !!state.gameData);      // ✅ true
console.log('Game Days:', state.gameData?.total_days); // ✅ 21 (or similar)
```

### Network Tab Verification
1. Open DevTools → Network tab
2. Should see:
   - `GET /api/v1/game/data?days=30&end_date=...&tickers=AAPL` - Status 200 ✅
   - Response contains ~21 days of trading data ✅

---

## Test 5: Make Trades and Advance Day

**Purpose**: Verify game works in multiplayer mode and syncs to backend

### Steps
1. In game view (from Test 4)
2. Find a stock with "BUY" recommendation (likely AAPL)
3. Click **"Buy Shares"** on a recommendation
4. Enter quantity: `10`
5. Click **"Confirm"**
6. Click **"Advance to Next Day"**

### Expected Results - Trade Execution
- ✅ Trade dialog appears
- ✅ Shows price calculation
- ✅ Trade executes successfully
- ✅ Holdings panel updates
- ✅ Cash decreases
- ✅ Portfolio value updates

### Expected Results - Day Advance
- ✅ Day counter increments: "Day 2 of 21"
- ✅ Chart updates with new data
- ✅ New recommendations load
- ✅ Score updates
- ✅ Grade may change

### Browser Console Verification
```javascript
// Should see sync log:
"🔄 Syncing to backend..." {
  playerId: "...",
  currentDay: 1,
  score: 50
}
```

### Network Tab Verification
1. Open DevTools → Network tab
2. Filter: "multiplayer"
3. Should see:
   - `PUT /api/v1/multiplayer/players/{player-id}` - Status 200 ✅
   - Request payload includes:
     ```json
     {
       "current_day": 1,
       "cash": 9720.50,
       "holdings": { "AAPL": { ... } },
       "score": 50,
       "grade": "C",
       "portfolio_value": 10045.30,
       "total_return_pct": 0.45,
       ...
     }
     ```

---

## Test 6: Leaderboard Updates

**Purpose**: Verify leaderboard shows updated scores

### Steps
1. After advancing day (from Test 5)
2. Click **"View Leaderboard →"** in purple banner
3. Or navigate to: `http://192.168.5.126:3000/multiplayer/room/XXXXXX`

### Expected Results
- ✅ Redirects to room lobby
- ✅ Leaderboard shows updated data:
  ```
  Rank | Name  | Score | Grade | Day  | Value      | Return
  1    | Alice | 50    | C     | 1/21 | $10,045.30 | +0.45%
  ```
- ✅ Personal stats card shows:
  - Your Rank: 1
  - Score: 50 points
  - Grade: C
  - Return: +0.45%
  - Progress: 1/21 days
- ✅ "Continue Game" button appears
- ✅ Leaderboard auto-refreshes every 5 seconds

### API Verification
```bash
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/XXXXXX/leaderboard

# Expected:
[
  {
    "rank": 1,
    "player_name": "Alice",
    "score": 50,  # ✅ Updated!
    "grade": "C",
    "current_day": 1,  # ✅ Updated!
    "portfolio_value": 10045.30,  # ✅ Updated!
    "total_return_pct": 0.45,  # ✅ Updated!
    "is_finished": false
  }
]
```

---

## Test 7: Continue Playing

**Purpose**: Verify student can return to game from leaderboard

### Steps
1. On room lobby (from Test 6)
2. Click **"Continue Game"** or **"Start Playing"**

### Expected Results
- ✅ Redirects to `/game`
- ✅ **SHOULD NOT SHOW LOBBY** ✅
- ✅ Shows game view directly with current state
- ✅ Shows purple multiplayer banner
- ✅ Day counter shows current day: "Day 2 of 21"
- ✅ Holdings are preserved
- ✅ Cash amount is correct
- ✅ Can continue playing

---

## Test 8: Page Refresh Persistence

**Purpose**: Verify state survives page reload

### Steps
1. While in game view (on Day 2)
2. Press **F5** (refresh page)

### Expected Results
- ✅ Page reloads
- ✅ **DOES NOT SHOW LOBBY** ✅
- ✅ Shows game view directly
- ✅ Purple multiplayer banner still visible
- ✅ Day counter preserved: "Day 2 of 21"
- ✅ Holdings preserved
- ✅ Cash amount preserved
- ✅ Score preserved
- ✅ Can continue playing

### Browser Console Verification
```javascript
// After page refresh
const state = JSON.parse(localStorage.getItem('stock-game-storage')).state;
console.log('Is Multiplayer?', state.isMultiplayer);  // ✅ Still true
console.log('Current Day:', state.player.currentDay); // ✅ Still 1
console.log('Cash:', state.player.cash);              // ✅ Preserved
```

---

## Test 9: Multiple Students (Optional)

**Purpose**: Verify multiple students can compete

### Steps
1. Open **ANOTHER INCOGNITO WINDOW**
2. Join same room as "Bob"
3. Start playing
4. Make different trades
5. Advance day
6. Check leaderboard in original window (Alice)

### Expected Results
- ✅ Leaderboard shows both students:
  ```
  Rank | Name  | Score | Grade | Day
  1    | Alice | 120   | B     | 3/21
  2    | Bob   | 85    | C     | 1/21
  ```
- ✅ Rankings update based on score
- ✅ "You" badge appears next to own name
- ✅ Auto-refresh shows Bob's progress

---

## Test 10: Game Completion

**Purpose**: Verify game finishes correctly

### Steps
1. In game view, keep clicking "Advance Day"
2. Advance through all 21 days
3. On day 21, click "Advance Day"

### Expected Results
- ✅ Game over screen appears
- ✅ Shows final score
- ✅ Shows final grade
- ✅ Shows total return
- ✅ "View Leaderboard" button

### Network Tab Verification
- ✅ Final sync includes `is_finished: true`

### API Verification
```bash
curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/XXXXXX/leaderboard

# Expected:
[
  {
    "rank": 1,
    "player_name": "Alice",
    "score": 650,
    "grade": "A",
    "current_day": 21,
    "is_finished": true,  # ✅ Marked as finished
    ...
  }
]
```

---

## Common Issues and Solutions

### Issue: Still shows solo lobby after "Start Playing"

**Diagnosis**:
```javascript
// Check localStorage
const state = JSON.parse(localStorage.getItem('stock-game-storage')).state;
console.log('Is Multiplayer?', state.isMultiplayer);
console.log('Has Game Data?', !!state.gameData);
console.log('Status:', state.status);
```

**Solutions**:
- If `isMultiplayer` is `false`: State not saved correctly
- If `gameData` is `null`: API call failed
- If `status` is `'not_started'`: startMultiplayerGame didn't complete
- Clear localStorage and try again: `localStorage.clear()`

### Issue: "Room not found" error

**Solutions**:
1. Check API server is running: `curl http://192.168.5.126:8000/health`
2. Verify room code is correct (case-sensitive)
3. Check database:
   ```bash
   psql -d stock_trading -c "SELECT room_code FROM multiplayer.game_rooms;"
   ```

### Issue: State not syncing to backend

**Diagnosis**:
```javascript
// Check network tab for PUT requests
// Should see: PUT /api/v1/multiplayer/players/{id}

// Check console for errors
// Should NOT see CORS errors or 404s
```

**Solutions**:
1. Verify `playerId` is set: `state.player.playerId`
2. Check backend logs for errors
3. Verify endpoint is working:
   ```bash
   curl -X PUT http://192.168.5.126:8000/api/v1/multiplayer/players/{id} \
     -H "Content-Type: application/json" \
     -d '{"current_day": 1, "cash": 10000, ...}'
   ```

### Issue: Leaderboard not updating

**Solutions**:
1. Check if sync is working (see above)
2. Verify polling is active (Network tab should show requests every 5s)
3. Hard refresh the leaderboard page (Ctrl+Shift+R)

---

## Success Checklist

- [ ] Solo mode still works
- [ ] Teacher can create room
- [ ] Student can join room
- [ ] Student clicks "Start Playing"
- [ ] **Student goes directly to game (no solo lobby)** ✅
- [ ] **Purple multiplayer banner shows** ✅
- [ ] Student can make trades
- [ ] **State syncs to backend after each day** ✅
- [ ] **Leaderboard updates automatically** ✅
- [ ] Student can navigate between game and leaderboard
- [ ] State survives page refresh
- [ ] Multiple students can compete
- [ ] Game completes successfully

---

## Performance Benchmarks

- Room creation: < 500ms
- Join room: < 500ms
- Start playing (data load): 1-2 seconds
- Day advance: < 100ms (+ network latency for sync)
- Leaderboard refresh: < 300ms

---

## Next Steps After Testing

1. If all tests pass → Feature is complete! ✅
2. Populate more ticker data (MSFT, GOOGL, AMZN) to enable multi-stock games
3. Consider adding WebSocket support for real-time leaderboard updates
4. Add game resume functionality
5. Build teacher dashboard
