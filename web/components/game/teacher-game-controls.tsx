'use client';

import { useState, useEffect } from 'react';
import { advanceDay, endGame, getRoomState, type RoomStateResponse } from '@/lib/api/multiplayer';

interface TeacherGameControlsProps {
  roomCode: string;
  teacherName: string;
  currentDay: number;
}

/**
 * Compact teacher controls for the game view.
 * Shows in a fixed position so teacher can control the game while playing.
 */
export function TeacherGameControls({ roomCode, teacherName, currentDay }: TeacherGameControlsProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roomState, setRoomState] = useState<RoomStateResponse | null>(null);
  const [expanded, setExpanded] = useState(false);

  // Poll room state every 2 seconds
  useEffect(() => {
    const pollState = async () => {
      try {
        const state = await getRoomState(roomCode);
        setRoomState(state);
      } catch (err) {
        console.error('Failed to poll room state:', err);
      }
    };

    pollState();
    const interval = setInterval(pollState, 2000);
    return () => clearInterval(interval);
  }, [roomCode]);

  const handleAdvanceDay = async () => {
    setLoading(true);
    setError(null);
    try {
      await advanceDay(roomCode, teacherName, 0); // No timer for now
      setExpanded(false); // Collapse after advancing
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to advance day');
    } finally {
      setLoading(false);
    }
  };

  const handleEndGame = async () => {
    if (!confirm('Are you sure you want to end the game for all players?')) return;

    setLoading(true);
    setError(null);
    try {
      await endGame(roomCode, teacherName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end game');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Collapsed State - Floating Action Button */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="bg-accent hover:bg-accent/80 text-white rounded-full p-4 shadow-2xl transition-all flex items-center gap-2"
        >
          <span className="text-2xl">👨‍🏫</span>
          {roomState && (
            <div className="flex items-center gap-2 pr-2">
              <span className="text-sm font-semibold">Day {currentDay}</span>
              <span className="text-xs bg-white/20 px-2 py-1 rounded-full">
                {roomState.ready_count}/{roomState.total_players} ready
              </span>
            </div>
          )}
        </button>
      )}

      {/* Expanded State - Control Panel */}
      {expanded && (
        <div className="bg-layer1 rounded-lg shadow-2xl p-4 w-80 border-2 border-accent/50">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-xl">👨‍🏫</span>
              <h3 className="font-bold text-text-primary">Teacher Controls</h3>
            </div>
            <button
              onClick={() => setExpanded(false)}
              className="text-text-muted hover:text-text-secondary text-xl"
            >
              ×
            </button>
          </div>

          {error && (
            <div className="bg-error/20 border border-error/50 text-error px-3 py-2 rounded text-sm mb-3">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {roomState && (
              <div className="bg-accent/10 rounded p-3 text-sm border border-accent/20">
                <div className="flex justify-between mb-1">
                  <span className="text-text-muted">Current Day:</span>
                  <span className="font-bold text-accent">Day {currentDay}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Ready Players:</span>
                  <span className="font-bold text-accent">
                    {roomState.ready_count} / {roomState.total_players}
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={handleAdvanceDay}
              disabled={loading}
              className="w-full bg-accent hover:bg-accent/80 disabled:bg-layer3 disabled:text-text-muted text-white font-bold py-3 px-4 rounded-lg transition-colors"
            >
              {loading ? 'Advancing...' : '⏭️ Advance All to Next Day'}
            </button>

            <button
              onClick={handleEndGame}
              disabled={loading}
              className="w-full bg-error hover:bg-error/80 disabled:bg-layer3 disabled:text-text-muted text-white font-bold py-2 px-4 rounded-lg transition-colors text-sm"
            >
              {loading ? 'Ending...' : '🏁 End Game'}
            </button>

            <a
              href={`/multiplayer/room/${roomCode}`}
              className="block text-center text-sm text-accent hover:text-accent/80 font-medium"
            >
              View Full Dashboard →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
