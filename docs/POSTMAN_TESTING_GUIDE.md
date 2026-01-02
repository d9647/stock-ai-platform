# Postman API Testing Guide

**Stock AI Platform - Complete API Test Collection**

This guide shows you how to test all API endpoints using Postman.

---

## Quick Start

### 1. Import Collection into Postman

**File Location**: [Stock_AI_Platform_API.postman_collection.json](../Stock_AI_Platform_API.postman_collection.json)

**Import Steps:**
1. Open Postman Desktop or Web
2. Click **Import** (top left)
3. Drag and drop the JSON file or click **Upload Files**
4. Select `Stock_AI_Platform_API.postman_collection.json`
5. Click **Import**

### 2. Start Your API Server

```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Verify server is running:**
- Open browser: http://localhost:8000
- Should see API info response

### 3. Run Your First Test

In Postman:
1. Open the collection: **Stock AI Platform API**
2. Navigate to: **Health & Info** → **Health Check**
3. Click **Send**
4. Should get: `200 OK` with health status

---

## Collection Structure

```
Stock AI Platform API/
├── Health & Info (2 requests)
│   ├── Root - Get API Info
│   └── Health Check
│
├── Game Data (4 requests)
│   ├── Get Game Data - Default (30 days)
│   ├── Get Game Data - Custom Tickers
│   ├── Get Game Data - Date Range
│   └── Get Game Data - Latest Available
│
├── Multiplayer - Room Management (7 requests)
│   ├── Create Room - Async Mode
│   ├── Create Room - Sync Manual
│   ├── Create Room - Sync Auto
│   ├── Get Room Details
│   ├── Start Game (Sync Mode)
│   ├── Advance Day (Sync Manual)
│   └── End Game (Sync Mode)
│
├── Multiplayer - Player Actions (4 requests)
│   ├── Join Room
│   ├── Join Room - Player 2
│   ├── Update Player State
│   └── Mark Player Ready (Sync Mode)
│
├── Multiplayer - Leaderboards (2 requests)
│   ├── Get Leaderboard
│   └── Get Room State (Polling)
│
├── News & Recommendations (2 requests)
│   ├── Get Recommendations by Date
│   └── Get News by Date
│
└── Error Cases (3 requests)
    ├── Invalid Room Code
    ├── Join Room - Duplicate Name
    └── Invalid Date Range
```

**Total**: 24 API requests covering all endpoints

---

## Environment Variables

The collection uses variables to chain requests together:

| Variable | Auto-Set By | Used By |
|----------|-------------|---------|
| `base_url` | Manual (default: `http://localhost:8000`) | All requests |
| `room_code` | Create Room requests | Join Room, Get Room, etc. |
| `room_id` | Create Room requests | Update/Delete operations |
| `player_id` | Join Room request | Update Player State |
| `player2_id` | Join Room - Player 2 | Multi-player tests |
| `sync_room_code` | Create Room - Sync Manual | Sync mode tests |

### How Auto-Setting Works

Some requests include **Test Scripts** that automatically save values:

```javascript
// Example: Create Room saves room_code
if (pm.response.code === 200) {
    const jsonData = pm.response.json();
    pm.environment.set("room_code", jsonData.room_code);
    console.log("Room created with code: " + jsonData.room_code);
}
```

**View Variables**: Click the collection → **Variables** tab

---

## Testing Workflows

### Workflow 1: Test Game Data Endpoint

**Purpose**: Verify solo game data is available

**Steps:**
1. **Health Check** - Ensure API is running
2. **Get Game Data - Default** - Get 30 days of data
3. Verify response has:
   - `days` array with 30+ items
   - `tickers` array
   - Each day has `recommendations`, `prices`, `news`

**Expected Result**: 200 OK with complete game data

### Workflow 2: Create and Join Multiplayer Room

**Purpose**: Test multiplayer room creation and joining

**Steps:**
1. **Create Room - Async Mode**
   - Creates room, auto-saves `room_code`
   - Note the room code in response (e.g., "ABC123")

2. **Join Room**
   - Uses saved `{{room_code}}`
   - Auto-saves `player_id`
   - Player "Alice Johnson" joins

3. **Join Room - Player 2**
   - Same room code
   - Auto-saves `player2_id`
   - Player "Bob Smith" joins

4. **Get Room Details**
   - Uses `{{room_code}}`
   - Should show 2 players

5. **Get Leaderboard**
   - Shows both players ranked by score

**Expected Result**: All requests succeed, room has 2 players

### Workflow 3: Sync Mode Game Flow

**Purpose**: Test teacher-controlled sync gameplay

**Steps:**
1. **Create Room - Sync Manual**
   - Auto-saves `sync_room_code`
   - Room status: "waiting"

2. **Join Room** (use `{{sync_room_code}}`)
   - Add 1-2 players

3. **Start Game**
   - Teacher starts game
   - Room status changes to "in_progress"
   - All players start at day 0

4. **Get Room State**
   - Verify `current_day` = 0
   - Status = "in_progress"

5. **Advance Day**
   - Teacher advances day
   - All players move to day 1

6. **Get Leaderboard**
   - View current standings

7. **End Game**
   - Teacher ends game early
   - Status changes to "finished"

**Expected Result**: Synchronized day progression works

### Workflow 4: Player State Updates

**Purpose**: Test player progress tracking

**Steps:**
1. **Create Room** and **Join Room** (get `player_id`)

2. **Update Player State**
   - Submit after-day-1 portfolio:
     - Cash: $95,000
     - Holdings: 10 AAPL, 15 MSFT
     - Trades: 2 trades on day 0
     - Portfolio value: $102,000
     - Score: 250

3. **Get Leaderboard**
   - Verify player appears with score 250

4. **Update Player State** again
   - Submit after-day-2 portfolio
   - Higher score: 350

5. **Get Leaderboard**
   - Verify score updated to 350

**Expected Result**: Player state persists correctly

### Workflow 5: Error Handling Tests

**Purpose**: Verify API error responses

**Test Cases:**

1. **Invalid Room Code**
   - Request: GET `/rooms/INVALID`
   - Expected: `404 Not Found`
   - Error: "Room with code INVALID not found"

2. **Duplicate Player Name**
   - Join room with same name twice
   - Expected: `400 Bad Request`
   - Error: "Player name 'Alice Johnson' is already taken"

3. **Invalid Date Range**
   - Request data before 2025-01-01
   - Expected: `400 Bad Request`
   - Error: "start_date must be on or after 2025-01-01"

**Expected Result**: Meaningful error messages returned

---

## API Endpoints Reference

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Get API version and info |
| `/api/v1/health` | GET | Health check with DB status |

### Game Data

| Endpoint | Method | Query Params | Description |
|----------|--------|--------------|-------------|
| `/api/v1/game/data` | GET | `days`, `tickers`, `start_date`, `end_date` | Get complete game data |

**Query Parameters:**
- `days`: Number of calendar days (1-90), default: 30
- `tickers`: Comma-separated symbols (default: AAPL,MSFT,GOOGL,AMZN)
- `start_date`: YYYY-MM-DD format
- `end_date`: YYYY-MM-DD format

### Multiplayer - Rooms

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/multiplayer/rooms` | POST | Create new room |
| `/api/v1/multiplayer/rooms/{code}` | GET | Get room details |
| `/api/v1/multiplayer/rooms/{code}/start` | POST | Start game (sync mode) |
| `/api/v1/multiplayer/rooms/{code}/advance-day` | POST | Advance day (sync manual) |
| `/api/v1/multiplayer/rooms/{code}/end` | POST | End game early |
| `/api/v1/multiplayer/rooms/{code}/leaderboard` | GET | Get leaderboard |
| `/api/v1/multiplayer/rooms/{code}/state` | GET | Get current room state |

### Multiplayer - Players

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/multiplayer/rooms/join` | POST | Join room as player |
| `/api/v1/multiplayer/players/{id}` | PUT | Update player state |
| `/api/v1/multiplayer/players/{id}/ready` | POST | Mark player ready |

### News & Recommendations

| Endpoint | Method | Query Params | Description |
|----------|--------|--------------|-------------|
| `/api/v1/recommendations` | GET | `date` | Get recommendations by date |
| `/api/v1/news` | GET | `date` | Get news articles by date |

---

## Request Examples

### Create Room - Full Example

**Request:**
```http
POST http://localhost:8000/api/v1/multiplayer/rooms
Content-Type: application/json

{
  "created_by": "Mr. Smith",
  "room_name": "Economics 101",
  "game_mode": "async",
  "config": {
    "initial_cash": 100000,
    "num_days": 30,
    "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "difficulty": "medium"
  }
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "room_code": "ABC123",
  "created_by": "Mr. Smith",
  "room_name": "Economics 101",
  "config": {
    "initialCash": 100000,
    "numDays": 30,
    "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "difficulty": "medium"
  },
  "start_date": "2025-01-01",
  "end_date": "2025-01-30",
  "status": "waiting",
  "game_mode": "async",
  "current_day": 0,
  "created_at": "2025-12-29T10:00:00Z",
  "players": []
}
```

### Join Room - Full Example

**Request:**
```http
POST http://localhost:8000/api/v1/multiplayer/rooms/join
Content-Type: application/json

{
  "room_code": "ABC123",
  "player_name": "Alice Johnson",
  "player_email": "alice@school.edu"
}
```

**Response:**
```json
{
  "id": "789e4567-e89b-12d3-a456-426614174001",
  "player_name": "Alice Johnson",
  "player_email": "alice@school.edu",
  "current_day": 0,
  "is_finished": false,
  "cash": 100000.0,
  "portfolio_value": 100000.0,
  "total_return_pct": 0.0,
  "total_return_usd": 0.0,
  "score": 0.0,
  "grade": "C",
  "joined_at": "2025-12-29T10:05:00Z",
  "last_action_at": "2025-12-29T10:05:00Z"
}
```

### Update Player State - Full Example

**Request:**
```http
PUT http://localhost:8000/api/v1/multiplayer/players/789e4567-e89b-12d3-a456-426614174001
Content-Type: application/json

{
  "current_day": 1,
  "cash": 95000,
  "holdings": {
    "AAPL": {"shares": 10, "avgCost": 150.00},
    "MSFT": {"shares": 15, "avgCost": 300.00}
  },
  "trades": [
    {
      "day": 0,
      "ticker": "AAPL",
      "action": "BUY",
      "shares": 10,
      "price": 150.00,
      "total": 1500.00
    }
  ],
  "portfolio_value": 102000,
  "total_return_pct": 2.0,
  "total_return_usd": 2000,
  "score": 250,
  "grade": "B",
  "score_breakdown": {
    "return_points": 100,
    "discipline_points": 100,
    "ai_bonus": 50
  },
  "portfolio_history": [
    {"day": 0, "value": 100000, "return_pct": 0},
    {"day": 1, "value": 102000, "return_pct": 2.0}
  ]
}
```

---

## Common Issues & Solutions

### Issue: "Connection refused"

**Cause**: API server not running

**Solution**:
```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Issue: "Room with code XXX not found"

**Cause**: Using invalid or expired room code

**Solution**:
1. Run **Create Room** request first
2. Check **Variables** tab for saved `room_code`
3. Manually set `room_code` variable if needed

### Issue: Variables not auto-saving

**Cause**: No Postman environment selected

**Solution**:
1. Create new environment: **Environments** → **Create Environment**
2. Name it: "Stock AI Local"
3. Select it from dropdown (top right)
4. Re-run requests

### Issue: "Player name already taken"

**Cause**: Trying to join same room with duplicate name

**Solution**: Change `player_name` in request body to unique value

### Issue: 422 Validation Error

**Cause**: Missing required fields or invalid data types

**Solution**: Check request body matches schema in documentation

---

## Advanced Usage

### Running All Tests Automatically

**Using Collection Runner:**

1. Click collection → **Run** (right-click menu)
2. Select requests to run
3. Click **Run Stock AI Platform API**
4. View results

**Recommended Order:**
1. Health Check
2. Create Room
3. Join Room (x2)
4. Update Player State
5. Get Leaderboard

### Exporting Test Results

After running collection:
1. Click **Export Results**
2. Choose format (JSON/HTML)
3. Share with team

### Using with Newman (CLI)

**Install Newman:**
```bash
npm install -g newman
```

**Run collection from command line:**
```bash
newman run Stock_AI_Platform_API.postman_collection.json
```

**Run with environment:**
```bash
newman run Stock_AI_Platform_API.postman_collection.json \
  --env-var "base_url=http://localhost:8000"
```

---

## Testing for iOS Development

### Key Endpoints for iOS

**Must-Test Before iOS Development:**

1. **Game Data**
   - `/api/v1/game/data` - Solo mode depends on this
   - Verify all fields exist (days, tickers, recommendations, prices)

2. **Room Management**
   - Create room, join room, get leaderboard
   - Test all 3 game modes (async, sync_manual, sync_auto)

3. **Player State**
   - Update player state after each day
   - Verify state persists correctly

4. **Error Handling**
   - Test all error scenarios
   - iOS needs to handle these gracefully

### iOS Integration Checklist

- [ ] Game data response parses correctly
- [ ] Room creation returns valid room_code
- [ ] Join room returns player_id
- [ ] Leaderboard shows all players
- [ ] Player state updates persist
- [ ] Errors return meaningful messages
- [ ] Timestamps are ISO 8601 format
- [ ] All numeric fields are correct type (float/int)

---

## API Response Schemas

### Game Data Response

```json
{
  "days": [
    {
      "day": 0,
      "date": "2025-01-01",
      "is_trading_day": true,
      "recommendations": [...],
      "prices": {...},
      "news": [...],
      "technical_indicators": {...}
    }
  ],
  "tickers": ["AAPL", "MSFT"],
  "start_date": "2025-01-01",
  "end_date": "2025-01-30",
  "total_days": 30
}
```

### Leaderboard Response

```json
[
  {
    "rank": 1,
    "player_id": "uuid",
    "player_name": "Alice Johnson",
    "score": 920.0,
    "grade": "A",
    "portfolio_value": 125000.0,
    "total_return_pct": 25.0,
    "current_day": 29,
    "is_finished": true
  }
]
```

---

## Support

**Issues with Postman collection?**
- Check API server is running
- Verify base_url is correct
- Check Postman console for errors
- Review API logs for backend errors

**Need more examples?**
- See [TESTING_COMPLETE_GUIDE.md](TESTING_COMPLETE_GUIDE.md)
- Review [API documentation](http://localhost:8000/docs) (Swagger)

---

**File**: [Stock_AI_Platform_API.postman_collection.json](../Stock_AI_Platform_API.postman_collection.json)
**Last Updated**: 2025-12-29
**Version**: 1.0
**Total Requests**: 24
