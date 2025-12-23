# Fix: Students Auto-Advance When Teacher Advances Day

## Problem
When teachers advance the day in sync mode, students were not seeing the new day automatically. They had to manually refresh the page to see updates.

## Solution
Created a `SyncStateManager` component that polls room state every 2 seconds and automatically advances the student's game when it detects the teacher has advanced to a new day.

## Implementation

### 1. Created SyncStateManager Component
**File**: [web/components/game/sync-state-manager.tsx](web/components/game/sync-state-manager.tsx)

This component:
- Polls room state every 2 seconds
- Compares server's `current_day` with local player's `currentDay`
- If server is ahead, automatically calls `advanceDay()` to catch up
- Uses a ref to track the last known day to prevent infinite loops
- Doesn't render any UI (returns null)

```typescript
export function SyncStateManager({ roomCode }: SyncStateManagerProps) {
  const { player, advanceDay } = useGameStore();
  const lastDayRef = useRef<number>(player.currentDay);

  useEffect(() => {
    const pollState = async () => {
      const state = await getRoomState(roomCode);

      // If teacher has advanced the day and we're behind, catch up
      if (state.current_day > lastDayRef.current) {
        const daysToAdvance = state.current_day - lastDayRef.current;
        for (let i = 0; i < daysToAdvance; i++) {
          advanceDay();
        }
        lastDayRef.current = state.current_day;
      }
    };

    pollState(); // Initial fetch
    const interval = setInterval(pollState, 2000);
    return () => clearInterval(interval);
  }, [roomCode, player.currentDay, advanceDay]);

  return null;
}
```

### 2. Integrated into GameView
**File**: [web/components/game/game-view.tsx](web/components/game/game-view.tsx:47-50)

Added the component at the top of GameView, only for sync mode:

```tsx
{/* Sync State Manager - Auto-advances students when teacher advances day */}
{isMultiplayer && roomCode && room?.game_mode === 'sync' && (
  <SyncStateManager roomCode={roomCode} />
)}
```

## How It Works

### Teacher Flow
1. Teacher clicks "⏭️ Next Day" in TeacherDashboard
2. Backend increments `room.current_day`
3. Backend resets all players' `is_ready` status
4. API returns updated room state

### Student Flow (Automatic)
1. SyncStateManager polls `/api/v1/multiplayer/rooms/{code}/state` every 2 seconds
2. Detects `state.current_day > lastDayRef.current`
3. Calls `advanceDay()` the correct number of times to catch up
4. Student's game advances to new day
5. UI updates automatically (new prices, news, etc.)

## Edge Cases Handled

### Multiple Day Advances
If teacher advances multiple days before student polls (unlikely with 2s polling):
```typescript
const daysToAdvance = state.current_day - lastDayRef.current;
for (let i = 0; i < daysToAdvance; i++) {
  advanceDay();
}
```

### Race Conditions
Using a ref instead of state prevents re-render loops:
```typescript
const lastDayRef = useRef<number>(player.currentDay);
```

### Network Failures
Polling continues even if one request fails:
```typescript
catch (err) {
  console.error('Failed to poll room state:', err);
}
// Interval continues
```

## Benefits

✅ **Real-time sync** - Students see updates within 2 seconds
✅ **No manual refresh** - Automatic advancement
✅ **Kahoot-like experience** - Everyone moves together
✅ **Graceful degradation** - If polling fails, game still works
✅ **No WebSockets needed** - Simple HTTP polling

## Testing

To test this feature:

1. **Setup**: Create a sync mode room with 2+ players
2. **Teacher**: Click "Start Game" then "⏭️ Next Day"
3. **Student**: Should see day advance automatically within 2 seconds
4. **Verify**: Student's portfolio, chart, and news all update
5. **Repeat**: Advance multiple days, verify students keep up

## Remaining Issue

The teacher controls (TeacherDashboard with "⏭️ Next Day" button) are only visible in the **room lobby**, not in the game view itself.

**Possible Solutions:**
1. Keep teacher in lobby (can view game via separate tab/window)
2. Add mini teacher controls to game view
3. Create a split-screen view for teachers (lobby + game)

## Files Modified

### Created
- `web/components/game/sync-state-manager.tsx` - Auto-advance component

### Modified
- `web/components/game/game-view.tsx` - Integrated SyncStateManager

## Status
✅ **Students auto-advance when teacher advances day**
⚠️ **Teacher workflow needs clarification** - Should teachers stay in lobby or play the game?
