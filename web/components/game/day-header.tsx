'use client';

import { useEffect, useMemo, useState } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatDate } from '@/lib/utils/format';
import { getRoom } from '@/lib/api/multiplayer';

export function DayHeader() {
  const {
    player,
    config,
    gameData,
    advanceDay,
    isMultiplayer,
    roomCode,
  } = useGameStore();
  const [isSyncMode, setIsSyncMode] = useState(false);
  const [roomMode, setRoomMode] = useState<string | null>(null);

  // Check multiplayer room mode (to gate the advance button)
  useEffect(() => {
    if (isMultiplayer && roomCode) {
      getRoom(roomCode)
        .then((room) => {
          setRoomMode(room.game_mode);
          setIsSyncMode(room.game_mode === 'sync' || room.game_mode === 'sync_auto');
        })
        .catch((err) => {
          console.error('Failed to fetch room info for mode check:', err);
          setIsSyncMode(false);
          setRoomMode(null);
        });
    } else {
      setIsSyncMode(false);
      setRoomMode(null);
    }
  }, [isMultiplayer, roomCode]);

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  if (!currentDayData) return null;

  const dayNumber = player.currentDay + 1;

  // Allow advancing only in solo / async modes (sync uses teacher controls)
  const canAdvance = !isMultiplayer || (isMultiplayer && !isSyncMode);

  return (
    <div className="sticky top-0 z-10 bg-layer1 border-b border-borderDark-subtle">
      <div className="container mx-auto px-4 py-3">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between md:gap-4">
          {/* Left: Day Info + Action */}
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-lg font-semibold text-text-primary">
                Day {dayNumber} of {gameData?.total_days || config.numDays}
              </h1>
              <p className="text-xs text-text-muted">
                {formatDate(currentDayData.date)}
              </p>
            </div>

            {canAdvance && (
              <button
                onClick={advanceDay}
                className="btn-primary inline-flex items-center gap-1.5 px-3.5 py-1.5 text-sm font-medium border border-borderDark-subtle rounded-full"
              >
                Next market day →
              </button>
            )}
          </div>

          {/* Right: Score + Room */}
          <div className="text-right space-y-1">
            <div className="text-xl font-semibold text-text-primary">
              {player.score.toFixed(0)} points
            </div>
            <div className="text-xs text-text-muted">
              Grade: {player.grade}
            </div>
            {isMultiplayer && roomCode && (
              <div className="text-xs text-text-muted flex items-center justify-end gap-2">
                <span className="font-mono text-text-primary">{roomCode}</span>
                {roomMode && (
                  <span className="px-2 py-0.5 border border-borderDark-subtle text-text-primary rounded-full">
                    {roomMode}
                  </span>
                )}
                <a
                  href={`/multiplayer/leaderboard/${roomCode}`}
                  className="text-accent hover:underline"
                >
                  View leaderboard
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
