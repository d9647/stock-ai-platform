# Kahoot-Style Synchronous Multiplayer Mode - Implementation Plan

## Overview
Convert multiplayer mode from asynchronous (each student plays at own pace) to synchronous (teacher-led, all students play together like Kahoot).

## Current State vs Desired State

### Current (Asynchronous)
```
Teacher creates room → Students join → Each student plays independently
- Student A: Day 15, making trades
- Student B: Day 3, just started
- Student C: Day 21, finished
- Everyone at different pace ❌
```

### Desired (Synchronous - Kahoot Style)
```
Teacher creates room → Students join → Teacher starts game → Everyone plays together
- Teacher: "Day 1 begins! You have 2 minutes to make trades"
- All students: Day 1, making trades simultaneously
- Timer expires → Teacher clicks "Next Day"
- All students: Advance to Day 2 together ✅
```

## Architecture Changes

### 1. Database Schema Updates

#### Update `game_rooms` table
```sql
ALTER TABLE multiplayer.game_rooms ADD COLUMN:
  - game_mode VARCHAR(20) DEFAULT 'async' -- 'async' or 'sync'
  - current_day INTEGER DEFAULT 0         -- Current day for sync mode
  - day_time_limit INTEGER                -- Seconds per day (optional)
  - day_started_at TIMESTAMP              -- When current day started
  - game_started_at TIMESTAMP             -- When teacher started game
  - game_ended_at TIMESTAMP               -- When teacher ended game
  - current_date DATE
```

#### Update `players` table
```sql
ALTER TABLE multiplayer.players ADD COLUMN:
  - is_ready BOOLEAN DEFAULT false        -- Ready for next day
  - last_sync_day INTEGER DEFAULT 0       -- Last day they synced to
```

### 2. New API End points

#### Teacher Control End points
```typescript
// Start the game (move from 'waiting' to 'in_progress')
POST /api/v1/multiplayer/rooms/{code}/start
Request: { started_by: teacher_id }
Response: { room, current_day: 0, started_at }

// Advance all players to next day
POST /api/v1/multiplayer/rooms/{code}/advance-day
Request: { initiated_by: teacher_id }
Response: { room, current_day: 1, all_players_advanced: true }

// End the game for everyone
POST /api/v1/multiplayer/rooms/{code}/end-game
Request: { ended_by: teacher_id }
Response: { room, status: 'finished', final_leaderboard }

// Set timer for current day (optional)
POST /api/v1/multiplayer/rooms/{code}/set-timer
Request: { duration_seconds: 120 }
Response: { room, day_started_at, expires_at }
```

#### Student Sync End points
```typescript
// Get current room state (for polling)
GET /api/v1/multiplayer/rooms/{code}/state
Response: {
  current_day: 1,
  status: 'in_progress',
  day_started_at: '2025-01-15T10:00:00Z',
  time_remaining: 45, // seconds
  waiting_for_teacher: true/false
}

// Mark student as ready for next day
POST /api/v1/multiplayer/players/{id}/ready
Response: { player, is_ready: true }
```

### 3. Frontend Changes

#### A. Teacher Dashboard Component
**New File**: `web/components/multiplayer/teacher-dashboard.tsx`

```tsx
interface TeacherDashboardProps {
  room: RoomResponse;
  isTeacher: boolean;
}

export function TeacherDashboard({ room, isTeacher }: TeacherDashboardProps) {
  if (!isTeacher) return null;

  return (
    <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Teacher Controls</h2>

      {room.status === 'waiting' && (
        <button onClick={handleStartGame}>
          🚀 Start Game for All Students
        </button>
      )}

      {room.status === 'in_progress' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span>Current Day: {room.current_day + 1}</span>
            <span>Players Ready: {readyCount} / {totalPlayers}</span>
          </div>

          <button onClick={handleAdvanceDay}>
            ⏭️ Advance to Day {room.current_day + 2}
          </button>

          <button onClick={handleEndGame}>
            🏁 End Game Now
          </button>

          {/* Timer Controls */}
          <div>
            <label>Day Timer (optional):</label>
            <select onChange={handleSetTimer}>
              <option value={0}>No Timer</option>
              <option value={60}>1 minute</option>
              <option value={120}>2 minutes</option>
              <option value={300}>5 minutes</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### B. Student Game View Updates
**File**: `web/components/game/game-view.tsx`

Changes needed:
1. **Remove "Advance Day" button** - Students can't control day progression
2. **Add "Ready" button** - Students mark themselves ready for next day
3. **Add sync status banner** - Show current day, timer, waiting status
4. **Add real-time polling** - Poll room state every 2 seconds

```tsx
export function GameView() {
  const { isMultiplayer, roomCode } = useGameStore();
  const [roomState, setRoomState] = useState<RoomState | null>(null);

  // Poll room state every 2 seconds
  useEffect(() => {
    if (!isMultiplayer || !roomCode) return;

    const poll = async () => {
      const state = await fetch(`/api/v1/multiplayer/rooms/${roomCode}/state`);
      const data = await state.json();
      setRoomState(data);

      // If room advanced to next day, sync local state
      if (data.current_day > player.currentDay) {
        syncToDay(data.current_day);
      }
    };

    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [isMultiplayer, roomCode]);

  return (
    <div className="min-h-screen bg-gray-50">
      <DayHeader />

      {/* Sync Mode Banner */}
      {isMultiplayer && roomState && (
        <SyncModeBanner roomState={roomState} />
      )}

      {/* Game Interface */}
      {/* ... existing game UI ... */}

      {/* Replace Advance Day button with Ready button */}
      {isMultiplayer ? (
        <ReadyButton roomState={roomState} />
      ) : (
        <AdvanceDayButton />
      )}
    </div>
  );
}
```

#### C. Sync Status Banner
**New Component**: `web/components/multiplayer/sync-banner.tsx`

```tsx
interface SyncBannerProps {
  roomState: RoomState;
}

export function SyncBanner({ roomState }: SyncBannerProps) {
  const timeRemaining = calculateTimeRemaining(roomState.day_started_at, roomState.day_time_limit);

  return (
    <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white py-4 px-6">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-2xl">⏱️</span>
          <div>
            <div className="font-bold text-lg">
              Day {roomState.current_day + 1}
            </div>
            <div className="text-sm">
              {roomState.waiting_for_teacher
                ? "Waiting for teacher to advance..."
                : `${timeRemaining}s remaining`}
            </div>
          </div>
        </div>

        {roomState.day_time_limit && (
          <div className="w-48 bg-white/20 rounded-full h-3">
            <div
              className="bg-white h-3 rounded-full transition-all"
              style={{ width: `${(timeRemaining / roomState.day_time_limit) * 100}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
```

#### D. Ready Button Component
**New Component**: `web/components/multiplayer/ready-button.tsx`

```tsx
interface ReadyButtonProps {
  roomState: RoomState;
  playerId: string;
}

export function ReadyButton({ roomState, playerId }: ReadyButtonProps) {
  const [isReady, setIsReady] = useState(false);

  const handleReady = async () => {
    await fetch(`/api/v1/multiplayer/players/${playerId}/ready`, {
      method: 'POST',
    });
    setIsReady(true);
  };

  if (isReady) {
    return (
      <div className="bg-green-100 text-green-800 font-semibold py-4 px-6 rounded-lg text-center">
        ✅ You're ready! Waiting for others...
      </div>
    );
  }

  return (
    <button
      onClick={handleReady}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg"
    >
      ✅ I'm Ready for Next Day
    </button>
  );
}
```

### 4. Game Flow

#### Teacher Flow
```
1. Create room (choose sync mode)
   ↓
2. Share room code with students
   ↓
3. Students join lobby
   ↓
4. Teacher sees player count, clicks "Start Game"
   ↓
   [API: POST /rooms/{code}/start]
   ↓
5. All students' screens advance to Day 1
   ↓
6. Students make trades, click "Ready"
   ↓
7. Teacher sees "5/10 students ready"
   ↓
8. Teacher clicks "Advance to Day 2"
   ↓
   [API: POST /rooms/{code}/advance-day]
   ↓
9. All students' screens advance to Day 2
   ↓
10. Repeat until end
    ↓
11. Teacher clicks "End Game"
    ↓
    [API: POST /rooms/{code}/end-game]
    ↓
12. All students see "Game Over" screen
```

#### Student Flow
```
1. Join room with code
   ↓
2. Wait in lobby
   ↓
3. Teacher starts game
   ↓
   [Poll detects game started]
   ↓
4. Screen auto-navigates to game at Day 1
   ↓
5. Make trades (buy/sell based on AI recommendations)
   ↓
6. Click "I'm Ready"
   ↓
   [API: POST /players/{id}/ready]
   ↓
7. See "Waiting for others..." message
   ↓
8. Teacher advances day
   ↓
   [Poll detects current_day changed]
   ↓
9. Screen auto-advances to Day 2
   ↓
   [Repeat steps 5-9]
   ↓
10. Teacher ends game
    ↓
    [Poll detects status: 'finished']
    ↓
11. Screen shows "Game Over" with final leaderboard
```

### 5. Real-Time Updates

#### Option A: Polling (Simpler)
```typescript
// Poll every 2 seconds
setInterval(async () => {
  const state = await getRoomState(roomCode);

  if (state.current_day > localDay) {
    // Teacher advanced, sync to new day
    advanceToDay(state.current_day);
  }

  if (state.status === 'finished') {
    // Game ended, show results
    showGameOver();
  }
}, 2000);
```

**Pros**:
- Simple to implement
- Works with existing HTTP infrastructure
- No WebSocket complexity

**Cons**:
- 2-second delay (acceptable for educational context)
- More API calls

#### Option B: WebSockets (More Responsive)
```typescript
// Connect to room WebSocket
const ws = new WebSocket(`ws://192.168.5.126:8000/ws/rooms/${roomCode}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'GAME_STARTED':
      navigateToGame();
      break;
    case 'DAY_ADVANCED':
      advanceToDay(message.current_day);
      break;
    case 'GAME_ENDED':
      showGameOver();
      break;
    case 'PLAYER_READY':
      updateReadyCount(message.ready_count);
      break;
  }
};
```

**Pros**:
- Instant updates (no delay)
- More interactive experience
- Less bandwidth (after initial connection)

**Cons**:
- More complex backend setup
- Need to handle reconnections
- Deployment complexity (need WebSocket support)

**Recommendation**: Start with **Polling (Option A)** for MVP, upgrade to WebSockets later if needed.

### 6. Timer System

#### Backend Timer Logic
```python
# When teacher sets timer
def set_day_timer(room_id: str, duration: int):
    room = get_room(room_id)
    room.day_time_limit = duration
    room.day_started_at = datetime.utcnow()
    db.commit()

    # Schedule auto-advance when timer expires
    schedule_auto_advance(room_id, duration)

# Auto-advance function
def auto_advance_day(room_id: str):
    room = get_room(room_id)
    if room.status != 'in_progress':
        return

    # Advance all players
    advance_room_day(room_id)

    # Broadcast to all connected students
    broadcast_day_advanced(room_id, room.current_day)
```

#### Frontend Timer Display
```tsx
function Timer({ startTime, duration }: TimerProps) {
  const [remaining, setRemaining] = useState(duration);

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      const left = Math.max(0, duration - elapsed);
      setRemaining(left);

      if (left === 0) {
        // Timer expired, wait for server to advance
      }
    }, 100);

    return () => clearInterval(interval);
  }, [startTime, duration]);

  return (
    <div className="text-2xl font-mono font-bold">
      {Math.floor(remaining / 60)}:{(remaining % 60).toFixed(0).padStart(2, '0')}
    </div>
  );
}
```

### 7. Broadcast Messages

#### Toast Notifications
```tsx
// When teacher starts game
toast.success('🚀 Game has started! Make your trades for Day 1');

// When day advances
toast.info(`⏭️ Moving to Day ${newDay}. Review your results!`);

// When timer warning
toast.warning('⏰ 30 seconds remaining!');

// When game ends
toast.success('🏁 Game finished! View the final leaderboard');
```

### 8. Database Migration

**File**: `api/migrations/versions/add_sync_mode_fields.py`

```python
def upgrade():
    # Add fields to game_rooms
    op.add_column('game_rooms',
        sa.Column('game_mode', sa.String(20), server_default='async'),
        schema='multiplayer'
    )
    op.add_column('game_rooms',
        sa.Column('current_day', sa.Integer, server_default='0'),
        schema='multiplayer'
    )
    op.add_column('game_rooms',
        sa.Column('day_time_limit', sa.Integer, nullable=True),
        schema='multiplayer'
    )
    op.add_column('game_rooms',
        sa.Column('day_started_at', sa.DateTime, nullable=True),
        schema='multiplayer'
    )
    op.add_column('game_rooms',
        sa.Column('game_started_at', sa.DateTime, nullable=True),
        schema='multiplayer'
    )
    op.add_column('game_rooms',
        sa.Column('game_ended_at', sa.DateTime, nullable=True),
        schema='multiplayer'
    )

    # Add fields to players
    op.add_column('players',
        sa.Column('is_ready', sa.Boolean, server_default='false'),
        schema='multiplayer'
    )
    op.add_column('players',
        sa.Column('last_sync_day', sa.Integer, server_default='0'),
        schema='multiplayer'
    )
```

## Implementation Phases

### Phase 1: Database & API (Backend)
**Time**: 2-3 days

1. Create database migration
2. Update models (GameRoom, Player)
3. Implement teacher control end points
4. Implement sync state end points
5. Add timer logic
6. Test with Postman/curl

### Phase 2: Teacher Dashboard (Frontend)
**Time**: 2 days

1. Create TeacherDashboard component
2. Add "Start Game" flow
3. Add "Advance Day" flow
4. Add "End Game" flow
5. Add timer controls
6. Show ready count

### Phase 3: Student Sync Mode (Frontend)
**Time**: 2-3 days

1. Add room state polling
2. Create SyncBanner component
3. Replace AdvanceDay with Ready button
4. Add auto-advance logic
5. Add broadcast notifications
6. Handle game end detection

### Phase 4: Testing & Polish
**Time**: 1-2 days

1. End-to-end testing with multiple students
2. Edge case handling (disconnects, late joiners)
3. UI polish
4. Performance optimization

**Total Estimated Time**: 7-10 days

## Migration Strategy

### Support Both Modes
```typescript
interface GameConfig {
  // ... existing fields ...
  gameMode: 'async' | 'sync';  // NEW
}

// In create-room form
<select name="gameMode">
  <option value="async">Asynchronous (students play at own pace)</option>
  <option value="sync">Synchronous (Kahoot-style, teacher-led)</option>
</select>
```

### Backward Compatibility
- Existing rooms default to 'async' mode
- Async mode works as before (current implementation)
- Sync mode uses new teacher controls

## Open Questions

1. **Late Joiners**: What happens if student joins after game started?
   - Option A: Reject join
   - Option B: Allow join, start at current day with default portfolio

2. **Timer Auto-Advance**: Should timer auto-advance or just warn?
   - Recommended: Auto-advance to keep everyone synced

3. **Teacher Offline**: What if teacher disconnects during game?
   - Could allow students to vote to advance
   - Or pause game until teacher returns

4. **Multiple Teachers**: Should multiple teachers control same room?
   - Probably not - one "host" teacher only

## Success Metrics

When implemented, the system should:
- ✅ Teacher can start game for all students simultaneously
- ✅ All students advance to same day together
- ✅ Students see live leaderboard during game
- ✅ Timer shows remaining time per day
- ✅ Teacher sees how many students are ready
- ✅ All students see game over at same time
- ✅ Experience feels like Kahoot (synchronized, interactive)

## Next Steps

Would you like me to:
1. **Start with Phase 1** (Backend API and database)?
2. **Create a prototype** of the teacher dashboard?
3. **Implement polling** for real-time sync?
4. **Design the UI** for sync mode?

Let me know which part you'd like to tackle first!
