# Postman Collection - Quick Start

**Stock AI Platform API Testing**

---

## 🚀 Setup (2 minutes)

### 1. Import Collection

**File**: `Stock_AI_Platform_API.postman_collection.json`

1. Open Postman
2. Click **Import**
3. Drag/drop the JSON file
4. Done! ✅

### 2. Start API Server

```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 3. Test It Works

In Postman:
- Open: **Health & Info** → **Health Check**
- Click: **Send**
- Should get: `200 OK`

---

## 📋 Common Test Flows

### Solo Game Test

```
1. Health Check              → 200 OK
2. Get Game Data - Default   → Returns 30 days of data
```

### Multiplayer Test

```
1. Create Room - Async       → Returns room_code (e.g., ABC123)
2. Join Room                 → Player 1 joins (auto-saves player_id)
3. Join Room - Player 2      → Player 2 joins
4. Get Leaderboard           → Shows both players
```

### Sync Mode Test

```
1. Create Room - Sync Manual → Returns room_code
2. Join Room (2x)            → Add 2 players
3. Start Game                → Status: in_progress
4. Advance Day               → All move to day 1
5. Get Leaderboard           → View standings
6. End Game                  → Status: finished
```

---

## 🔑 Key Variables

Variables auto-save between requests:

| Variable | Set By | Use |
|----------|--------|-----|
| `room_code` | Create Room | Join, Get Room, Leaderboard |
| `player_id` | Join Room | Update Player State |

**View/Edit**: Collection → **Variables** tab

---

## 📍 Main Endpoints

### Game Data
```
GET /api/v1/game/data?days=30&tickers=AAPL,MSFT
```

### Create Room
```
POST /api/v1/multiplayer/rooms
Body: { created_by, room_name, game_mode, config }
```

### Join Room
```
POST /api/v1/multiplayer/rooms/join
Body: { room_code, player_name, player_email }
```

### Leaderboard
```
GET /api/v1/multiplayer/rooms/{room_code}/leaderboard
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Start API server: `uvicorn app.main:app --reload` |
| Room not found | Run "Create Room" first |
| Variables not saving | Create & select Postman environment |
| 422 Validation error | Check request body matches schema |

---

## 📦 Collection Contents

**24 Requests:**
- 2 Health checks
- 4 Game data queries
- 7 Room management
- 4 Player actions
- 2 Leaderboards
- 2 News/recommendations
- 3 Error cases

---

## 📖 Full Documentation

See [POSTMAN_TESTING_GUIDE.md](docs/POSTMAN_TESTING_GUIDE.md) for:
- Detailed workflows
- Request/response examples
- Advanced usage (Newman CLI)
- iOS integration checklist

---

**Ready to test!** 🎉

Start with: **Health Check** → **Create Room** → **Join Room**
