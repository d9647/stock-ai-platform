'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  getRoomState,
  markPlayerReady,
  type RoomStateResponse,
} from '@/lib/api/multiplayer';

interface SyncBannerProps {
  roomCode: string;
  playerId: string;
  currentDay: number;
  gameMode?: 'async' | 'sync' | 'sync_auto';
  playerCount?: number;
}

export function SyncBanner({
  roomCode,
  playerId,
  currentDay,
  gameMode,
  playerCount,
}: SyncBannerProps) {
  const router = useRouter();
  const [roomState, setRoomState] = useState<RoomStateResponse | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [markingReady, setMarkingReady] = useState(false);
  const lastDayRef = useRef<number | null>(null);

  const isAsyncMode = gameMode === 'async';

  /* --------------------------------------------------
     Poll room state (skip for async mode)
  -------------------------------------------------- */
  useEffect(() => {
    if (isAsyncMode) return;

    const pollState = async () => {
      try {
        const state = await getRoomState(roomCode);
        setRoomState(state);
      } catch (err) {
        console.error('Failed to poll room state:', err);
      }
    };

    pollState();
    const interval = setInterval(pollState, 1000);
    return () => clearInterval(interval);
  }, [roomCode, isAsyncMode]);

  /* --------------------------------------------------
     Reset ready when day advances or server resets
  -------------------------------------------------- */
  useEffect(() => {
    if (!roomState) return;

    const dayChanged = lastDayRef.current !== roomState.current_day;
    const serverResetReady = roomState.ready_count === 0 && isReady;

    if (dayChanged || serverResetReady || roomState.status === 'finished') {
      setIsReady(false);
    }

    lastDayRef.current = roomState.current_day;
  }, [roomState, isReady]);

  const handleMarkReady = async () => {
    setMarkingReady(true);
    try {
      await markPlayerReady(playerId);
      setIsReady(true);
    } catch (err) {
      console.error('Failed to mark ready:', err);
    } finally {
      setMarkingReady(false);
    }
  };

  // For async mode, show a simpler banner
  if (isAsyncMode) {
    return (
      <div className="bg-layer1 border-b border-borderDark-subtle">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            {/* Left: Mode + Status */}
            <div className="space-y-0.5">
              <div className="text-sm font-medium text-text-primary">
                Asynchronous Mode · Room {roomCode}
              </div>
              <div className="text-xs text-text-muted">
                Play at your own pace. Your progress is automatically saved.
              </div>
            </div>

            {/* Right: Players */}
            {playerCount !== undefined && (
              <div className="text-right">
                <div className="text-xs text-text-muted">Players</div>
                <div className="text-sm font-medium text-text-primary">
                  {playerCount}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!roomState) return null;

  const isFinished = roomState.status === 'finished';

  /* --------------------------------------------------
     Status message
  -------------------------------------------------- */
  const statusText =
    roomState.status === 'waiting'
      ? 'Waiting for the teacher to start the game.'
      : roomState.status === 'in_progress' && roomState.waiting_for_teacher
      ? 'Waiting for the teacher to advance.'
      : roomState.status === 'in_progress'
      ? 'Teacher controls the game pace.'
      : 'Game has ended.';

  return (
    <div className="bg-layer1 border-b border-borderDark-subtle">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          {/* Left: Mode + Status */}
          <div className="space-y-0.5">
            <div className="text-sm font-medium text-text-primary">
              Synchronous Mode · Room {roomCode}
            </div>
            <div className="text-xs text-text-muted">{statusText}</div>
          </div>

          {/* Right: Timer / Players / Actions */}
          <div className="flex items-center gap-6">
            {!isFinished &&
              roomState.time_remaining !== undefined &&
              roomState.time_remaining > 0 && (
                <div className="text-right">
                  <div className="text-xs text-text-muted">Time remaining</div>
                  <div
                    className={`font-mono text-sm ${
                      roomState.time_remaining < 30
                        ? 'text-accent'
                        : 'text-text-primary'
                    }`}
                  >
                    {Math.floor(roomState.time_remaining / 60)}:
                    {String(roomState.time_remaining % 60).padStart(2, '0')}
                  </div>
                </div>
              )}

            {!isFinished && (
              <div className="text-right">
                <div className="text-xs text-text-muted">Players</div>
                <div className="text-sm font-medium text-text-primary">
                  {roomState.total_players}
                </div>
              </div>
            )}

            {roomState.status === 'in_progress' &&
              gameMode !== 'sync_auto' && (
                <button
                  onClick={handleMarkReady}
                  disabled={isReady || markingReady}
                  className={
                    isReady
                      ? 'px-4 py-1.5 text-xs bg-layer3 text-text-muted cursor-not-allowed'
                      : 'px-4 py-1.5 text-xs btn-primary'
                  }
                >
                  {isReady
                    ? 'Ready'
                    : markingReady
                    ? 'Marking…'
                    : 'Mark ready'}
                </button>
              )}

            {isFinished && (
              <button
                onClick={() => router.push(`/multiplayer/leaderboard/${roomCode}`)}
                className="px-4 py-1.5 text-xs btn-primary"
              >
                View leaderboard →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
