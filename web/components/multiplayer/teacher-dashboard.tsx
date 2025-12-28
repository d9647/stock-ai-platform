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
    <div className="bg-layer2 border border-borderDark-subtle rounded-md mb-6">
      {/* Error */}
      {error && (
        <div className="bg-error/10 border-error/30 rounded-md px-4 py-3 m-4 text-sm text-error">
          {error}
        </div>
      )}

      {/* Waiting */}
      {status === 'waiting' && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-text-secondary">
                <span className="text-text-primary font-semibold text-lg">
                  {room.player_count}
                </span>{' '}
                <span className="text-text-muted">player{room.player_count !== 1 && 's'} waiting</span>
              </p>
            </div>
            <button
              onClick={handleStartGame}
              disabled={loading || room.player_count === 0}
              className="px-6 py-2 btn-primary rounded-full font-medium disabled:opacity-50"
            >
              {loading ? 'Starting…' : 'Start Game'}
            </button>
          </div>
        </div>
      )}

      {/* In Progress */}
      {status === 'in_progress' && (
        <div className="p-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Day Counter */}
            <div className="flex flex-col">
              <span className="text-lg font-semibold text-text-primary">
                Day {room.current_day + 1}
              </span>
              <span className="text-xs text-text-muted">
                of {room.config.numDays}
              </span>
            </div>

            {/* Timer Countdown */}
            {roomState?.time_remaining !== undefined && roomState.time_remaining > 0 && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-layer1 rounded-full border border-borderDark-subtle">
                <span className="text-xs text-text-muted">Time Remaining:</span>
                <span className="text-sm font-mono font-semibold text-text-primary">
                  {Math.floor(roomState.time_remaining / 60)}:
                  {String(roomState.time_remaining % 60).padStart(2, '0')}
                </span>
              </div>
            )}

            {/* Timer Duration Setting */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-layer1 rounded-full border border-borderDark-subtle">
              <span className="text-xs text-text-muted whitespace-nowrap">Duration:</span>
              <input
                type="number"
                min={0}
                max={600}
                value={timerInput}
                onChange={(e) => setTimerInput(Number(e.target.value))}
                className="w-14 px-2 py-0.5 text-sm bg-base border border-borderDark-subtle rounded text-text-primary text-center"
              />
              <span className="text-xs text-text-muted">s</span>
              {isAuto && (
                <button
                  onClick={handleSetTimer}
                  disabled={loading}
                  className="px-2 py-0.5 text-xs btn-primary rounded transition-colors disabled:opacity-50"
                >
                  Set
                </button>
              )}
            </div>

            {/* Next Day Button */}
            {!isAuto && (
              <button
                onClick={handleAdvanceDay}
                disabled={loading}
                className="px-4 py-2 btn-primary text-sm font-medium rounded-full transition-colors disabled:opacity-50"
              >
                {loading ? 'Advancing…' : 'Next Day'}
              </button>
            )}

            {/* End Game Button */}
            <button
              onClick={handleEndGame}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-text-muted border border-borderDark-subtle rounded-full transition-colors hover:text-text-primary hover:bg-layer2"
            >
              Quit
            </button>
          </div>
        </div>
      )}

      {/* Finished */}
      {status === 'finished' && (
        <div className="p-6 text-center">
          <p className="text-sm text-text-muted">
            Game completed
          </p>
        </div>
      )}
    </div>
  );
}
