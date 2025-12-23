# Bug Fix: Game Mode Not Persisting (Sync Mode Showing as Async)

## Issue
When teachers created a room with "Synchronous (Kahoot-style)" mode selected, the room was being saved with `game_mode: "sync"` in the database, but API responses were returning `game_mode: "async"`.

## Root Cause
The API end points were manually constructing `RoomResponse` objects instead of using the helper function `_build_room_response()`, which meant they were missing the `game_mode` field and other sync mode fields from the response.

## Files Modified

### 1. [api/app/routes/multiplayer.py](api/app/routes/multiplayer.py)

#### Fixed `create_room` endpoint (line 79)
**Before:**
```python
return RoomResponse(
    id=str(room.id),
    room_code=room.room_code,
    created_by=room.created_by,
    room_name=room.room_name,
    config=room.config,
    start_date=room.start_date,
    end_date=room.end_date,
    status=room.status,
    created_at=room.created_at.isoformat(),
    started_at=room.started_at.isoformat() if room.started_at else None,
    finished_at=room.finished_at.isoformat() if room.finished_at else None,
    player_count=0,
    players=[],
)
```

**After:**
```python
return _build_room_response(room)
```

#### Fixed `get_room` endpoint (line 177)
**Before:**
```python
players = [
    PlayerResponse(
        id=str(p.id),
        player_name=p.player_name,
        # ... manually building player response, missing is_ready, last_sync_day
    )
    for p in room.players
]

return RoomResponse(
    id=str(room.id),
    room_code=room.room_code,
    # ... manually building room response, missing game_mode and sync fields
    player_count=len(players),
    players=players,
)
```

**After:**
```python
return _build_room_response(room)
```

#### Fixed `list_rooms` endpoint (line 296)
**Before:**
```python
return [
    RoomSummary(
        id=str(r.id),
        room_code=r.room_code,
        created_by=r.created_by,
        room_name=r.room_name,
        status=r.status,
        player_count=len(r.players),
        created_at=r.created_at.isoformat(),
        config=r.config,
    )
    for r in rooms
]
```

**After:**
```python
return [
    RoomSummary(
        id=str(r.id),
        room_code=r.room_code,
        created_by=r.created_by,
        room_name=r.room_name,
        status=r.status,
        game_mode=r.game_mode,  # Added
        player_count=len(r.players),
        created_at=r.created_at.isoformat(),
        config=r.config,
    )
    for r in rooms
]
```

### 2. [api/app/schemas/multiplayer.py](api/app/schemas/multiplayer.py:102)

#### Updated RoomSummary schema
**Before:**
```python
class RoomSummary(BaseModel):
    """Brief room information for listings."""
    id: str
    room_code: str
    created_by: str
    room_name: Optional[str]
    status: str
    player_count: int
    created_at: str
    config: Dict[str, Any]
```

**After:**
```python
class RoomSummary(BaseModel):
    """Brief room information for listings."""
    id: str
    room_code: str
    created_by: str
    room_name: Optional[str]
    status: str
    game_mode: str = "async"  # 'async' or 'sync' - ADDED
    player_count: int
    created_at: str
    config: Dict[str, Any]
```

## Testing

### Before Fix
```bash
$ curl -X POST http://192.168.5.126:8000/api/v1/multiplayer/rooms \
  -H "Content-Type: application/json" \
  -d '{"created_by":"Test","game_mode":"sync","config":{...}}'

# Response had game_mode: "async" (wrong!)
{"room_code":"Z0KZZV",...,"game_mode":"async",...}

$ curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/Z0KZZV
# Also returned game_mode: "async" (wrong!)
```

### After Fix
```bash
$ curl -X POST http://192.168.5.126:8000/api/v1/multiplayer/rooms \
  -H "Content-Type: application/json" \
  -d '{"created_by":"Test","game_mode":"sync","config":{...}}'

# Response has game_mode: "sync" (correct!)
{"room_code":"RXGROL",...,"game_mode":"sync",...}

$ curl http://192.168.5.126:8000/api/v1/multiplayer/rooms/RXGROL
# Also returns game_mode: "sync" (correct!)
{"room_code":"RXGROL",...,"game_mode":"sync",...}
```

## Impact

### What Works Now
✅ Teachers can create sync mode rooms
✅ `game_mode` is correctly saved to database
✅ `game_mode` is correctly returned in API responses
✅ GET /rooms/{code} returns correct game mode
✅ POST /rooms returns correct game mode
✅ GET /rooms (list) includes game mode
✅ Frontend will correctly detect sync vs async mode
✅ Teacher dashboard will appear for sync rooms
✅ Student sync UI will appear for sync rooms

### Side Effects Fixed
✅ All sync mode fields now included in responses:
- `game_mode`
- `current_day`
- `day_time_limit`
- `day_started_at`
- `game_started_at`
- `game_ended_at`

✅ All player sync fields now included:
- `is_ready`
- `last_sync_day`

## Lessons Learned

1. **Use Helper Functions**: The `_build_room_response()` helper was created in Phase 1 specifically to avoid this issue, but wasn't used consistently across all end points.

2. **DRY Principle**: Don't Repeat Yourself - manually building responses in multiple places leads to inconsistencies.

3. **Schema Validation**: Pydantic schemas should be leveraged through helper functions to ensure all fields are included.

4. **Testing**: Should have tested the full create → get flow immediately after Phase 1 backend implementation.

## Status
✅ **Fixed and Tested**

All end points now correctly handle `game_mode` and sync mode fields.
