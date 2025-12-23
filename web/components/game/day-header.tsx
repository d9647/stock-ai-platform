'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatDate } from '@/lib/utils/format';

export function DayHeader() {
  const {
    player,
    config,
    gameData,
    advanceDay,
    isMultiplayer,
    role,
  } = useGameStore();

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  if (!currentDayData) return null;

  const dayNumber = player.currentDay + 1;

  // Allow advancing only in solo / async modes
  const canAdvance =
    !isMultiplayer;

  return (
    <div className="sticky top-0 z-10 bg-layer1 border-b border-borderDark-subtle">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
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

          {/* Right: Score */}
          <div className="text-right">
            <div className="text-xl font-semibold text-text-primary">
              {player.score.toFixed(0)} points
            </div>
            <div className="text-xs text-text-muted">
              Grade: {player.grade}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
