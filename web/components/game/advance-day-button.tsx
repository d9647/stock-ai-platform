'use client';

import { useGameStore } from '@/lib/stores/gameStore';
import { markPlayerReady, getRoom } from '@/lib/api/multiplayer';
import { useState, useEffect } from 'react';

export function AdvanceDayButton() {
  const store = useGameStore();
  const { player, config, advanceDay, isMultiplayer, roomCode } = store;

  const [isReady, setIsReady] = useState(false);
  const [marking, setMarking] = useState(false);
  const [isSyncMode, setIsSyncMode] = useState(false);

  /* --------------------------------------------------
     Detect sync mode
  -------------------------------------------------- */
  useEffect(() => {
    if (isMultiplayer && roomCode) {
      getRoom(roomCode)
        .then((room) => setIsSyncMode(room.game_mode === 'sync'))
        .catch((err) => console.error('Failed to check game mode:', err));
    }
  }, [isMultiplayer, roomCode]);

  const handleMarkReady = async () => {
    setMarking(true);
    try {
      await markPlayerReady(player.playerId);
      setIsReady(true);
    } catch (err) {
      console.error('Failed to mark ready:', err);
    } finally {
      setMarking(false);
    }
  };

  /* --------------------------------------------------
     SYNC MODE (student → Ready)
  -------------------------------------------------- */
  if (isMultiplayer && isSyncMode) {
    return (
      <div className="bg-layer2 border border-borderDark-subtle p-5">
        <div className="text-center space-y-3">
          <p className="text-sm text-text-secondary">
            {isReady
              ? 'You are marked ready. Waiting for the teacher to advance.'
              : 'Finished trading for today? Mark yourself ready.'}
          </p>

          <button
            onClick={handleMarkReady}
            disabled={isReady || marking}
            className={
              isReady
                ? 'w-full py-2 text-sm font-medium bg-layer3 text-text-muted cursor-not-allowed'
                : 'w-full py-2 text-sm font-medium btn-primary'
            }
          >
            {isReady
              ? 'Ready'
              : marking
              ? 'Marking ready…'
              : 'Mark Ready'}
          </button>
        </div>
      </div>
    );
  }

  /* --------------------------------------------------
     ASYNC / SOLO MODE (Advance Day)
  -------------------------------------------------- */
  const isLastDay = player.currentDay >= config.numDays - 1;

  const message = isLastDay
    ? 'This is the final trading day.'
    : 'Trades will execute at the next market open.';

  const buttonText = isLastDay ? 'Finish Game' : 'Advance Day';

  return (
    <div className="bg-layer2 border border-borderDark-subtle p-5">
      <div className="text-center space-y-3">
        <p className="text-sm text-text-secondary">{message}</p>
      </div>
    </div>
  );
}


/* ---------
  copied from above, but commented out for reference
        <button
          onClick={advanceDay}
          className="w-full py-2 text-sm font-medium btn-primary"
        >
          {buttonText}
        </button>
 ---------*/
