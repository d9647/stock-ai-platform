'use client';

import { useState, useEffect } from 'react';
import {
  RoomResponse,
  startGame,
  advanceDay,
  endGame,
  getRoomState,
  RoomStateResponse,
  setTimer,
} from '@/lib/api/multiplayer';

interface TeacherDashboardProps {
  room: RoomResponse;
  teacherName: string;
  onRoomUpdate: () => void;
}

export function TeacherDashboard({
  room,
  teacherName,
  onRoomUpdate,
}: TeacherDashboardProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roomState, setRoomState] = useState<RoomStateResponse | null>(null);
  const [timerInput, setTimerInput] = useState<number>(30);

  const status = roomState?.status ?? room.status;
  const isAuto = room.game_mode === 'sync_auto';

  /* ---------- Poll room state ---------- */
  useEffect(() => {
    if (room.game_mode === 'async') return;

    const poll = async () => {
      try {
        const state = await getRoomState(room.room_code);
        setRoomState(state);
      } catch {}
    };

    poll();
    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, [room.room_code, room.game_mode]);

  /* ---------- Sync finished ---------- */
  useEffect(() => {
    if (roomState?.status === 'finished' && room.status !== 'finished') {
      onRoomUpdate();
    }
  }, [roomState?.status, room.status, onRoomUpdate]);

  /* ---------- Actions ---------- */
  const handleStartGame = async () => {
    setLoading(true);
    setError(null);
    try {
      await startGame(room.room_code, teacherName);
      onRoomUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceDay = async () => {
    setLoading(true);
    setError(null);
    try {
      await advanceDay(room.room_code, teacherName, timerInput);
      setRoomState((prev) =>
        prev ? { ...prev, ready_count: 0, waiting_for_teacher: true } : prev
      );
      onRoomUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to advance day');
    } finally {
      setLoading(false);
    }
  };

  const handleSetTimer = async () => {
    setLoading(true);
    setError(null);
    try {
      await setTimer(room.room_code, timerInput);
      onRoomUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set timer');
    } finally {
      setLoading(false);
    }
  };

  const handleEndGame = async () => {
    if (!confirm('End the game for all players?')) return;
    setLoading(true);
    setError(null);
    try {
      await endGame(room.room_code, teacherName);
      onRoomUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end game');
    } finally {
      setLoading(false);
    }
  };

  /* ---------- Hide for async ---------- */
  if (room.game_mode === 'async') return null;

  return (
    <div className="bg-layer2 border border-borderDark-subtle rounded-md p-6 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            Teacher Controls
          </h2>
          <p className="text-xs text-text-muted">
            Synchronous room mode
          </p>
        </div>

        <div className="flex items-center gap-6">
          {roomState && room.game_mode === 'sync' && (
            <div className="text-right">
              <div className="text-xs text-text-muted">Ready</div>
              <div className="text-lg font-semibold text-text-primary">
                {roomState.ready_count} / {roomState.total_players}
              </div>
            </div>
          )}

          <a
            href={`/multiplayer/leaderboard/${room.room_code}`}
            className="text-xs text-accent hover:underline whitespace-nowrap"
          >
            View leaderboard
          </a>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-layer1 border border-borderDark-subtle rounded-md px-4 py-3 mb-4 text-sm text-text-primary">
          {error}
        </div>
      )}

      {/* Waiting */}
      {status === 'waiting' && (
        <div className="space-y-4">
          <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 text-sm">
            <p className="text-text-secondary">
              <span className="text-text-primary font-semibold">
                {room.player_count}
              </span>{' '}
              player{room.player_count !== 1 && 's'} in lobby
            </p>
            <p className="text-text-muted mt-1">
              Game length: {room.config.numDays} days
            </p>
          </div>

          <button
            onClick={handleStartGame}
            disabled={loading || room.player_count === 0}
            className="w-full btn-primary rounded-md py-3 font-medium"
          >
            {loading ? 'Starting…' : 'Start Game'}
          </button>
        </div>
      )}

      {/* In Progress */}
      {status === 'in_progress' && (
        <div className="space-y-4">
          <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 text-sm">
            <div className="flex justify-between mb-2">
              <span className="text-text-muted">Current Day</span>
              <span className="text-text-primary font-semibold">
                Day {room.current_day + 1}
              </span>
            </div>

            {roomState?.time_remaining !== undefined && (
              <div className="flex justify-between">
                <span className="text-text-muted">Time Remaining</span>
                <span className="text-text-primary font-mono">
                  {Math.floor(roomState.time_remaining / 60)}:
                  {String(roomState.time_remaining % 60).padStart(2, '0')}
                </span>
              </div>
            )}
          </div>

          {/* Timer */}
          <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 text-sm">
            <label className="block text-text-secondary mb-1">
              Timer for next day (seconds)
            </label>
            <input
              type="number"
              min={0}
              max={600}
              value={timerInput}
              onChange={(e) => setTimerInput(Number(e.target.value))}
              className="w-full px-3 py-2 bg-layer2 border border-borderDark-subtle rounded-md text-text-primary"
            />
            <p className="text-xs text-text-muted mt-1">
              Set to 0 to disable timer
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={isAuto ? handleSetTimer : handleAdvanceDay}
              disabled={loading}
              className="btn-primary rounded-md py-3 font-medium"
            >
              {isAuto ? 'Set Timer' : 'Next Day'}
            </button>

            <button
              onClick={handleEndGame}
              disabled={loading}
              className="bg-layer1 border border-borderDark-subtle text-text-primary rounded-md py-3 font-medium hover:bg-layer3"
            >
              End Game
            </button>
          </div>
        </div>
      )}

      {/* Finished */}
      {status === 'finished' && (
        <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 text-center text-sm">
          <p className="text-text-primary mb-3">
            Game completed. View final results.
          </p>
          <a
            href={`/multiplayer/leaderboard/${room.room_code}`}
            className="text-accent font-medium"
          >
            View Leaderboard →
          </a>
        </div>
      )}
    </div>
  );
}
