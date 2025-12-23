'use client';

import { useEffect, useRef } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { getRoomState } from '@/lib/api/multiplayer';

interface SyncStateManagerProps {
  roomCode: string;
}

/**
 * Manages sync mode state for students.
 * Polls room state and auto-advances the game when teacher advances the day.
 */
export function SyncStateManager({ roomCode }: SyncStateManagerProps) {
  const { player, advanceDay } = useGameStore();
  const lastDayRef = useRef<number>(player.currentDay);

  useEffect(() => {
    const pollState = async () => {
      try {
        const state = await getRoomState(roomCode);

        // If teacher has advanced the day and we're behind, catch up
        if (state.current_day > lastDayRef.current) {
          console.log(`Teacher advanced to day ${state.current_day}, catching up from day ${lastDayRef.current}`);

          // Advance our game to match the teacher's current day
          const daysToAdvance = state.current_day - lastDayRef.current;
          for (let i = 0; i < daysToAdvance; i++) {
            advanceDay();
          }

          lastDayRef.current = state.current_day;
        }

        // Update ref when player advances manually (shouldn't happen in sync mode, but just in case)
        if (player.currentDay > lastDayRef.current) {
          lastDayRef.current = player.currentDay;
        }
      } catch (err) {
        console.error('Failed to poll room state:', err);
      }
    };

    // Poll every 2 seconds
    pollState(); // Initial fetch
    const interval = setInterval(pollState, 2000);
    return () => clearInterval(interval);
  }, [roomCode, player.currentDay, advanceDay]);

  // This component doesn't render anything
  return null;
}
