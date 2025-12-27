'use client';

import { useEffect, useState } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { useGameData } from '@/lib/hooks/useGameData';
import { GameLobby } from '@/components/game/game-lobby';
import { GameView } from '@/components/game/game-view';
import { GameOver } from '@/components/game/game-over';

export default function GamePage() {
  const { status, loadGameData, isMultiplayer, gameData: storeGameData } = useGameStore();
  const [showLobby, setShowLobby] = useState(true);
  const [gameConfig, setGameConfig] = useState<{
    days: number;
    startDate?: string;
    tickers: string[];
  }>({
    days: 30,
    startDate: useGameStore.getState().config.startDate || undefined,
    tickers: ['AAPL','MSFT','GOOGL','NVDA','AMZN','TSLA','META','WMT','MU','AVGO','TSM','JPM','BRK.A','INTC','AMD','QCOM','TXN','LRCX','KLAC','ASML','LLY','ORCL','V','PYPL','MA','JNJ','PLTR'],
  });

  const computeEndDate = () => {
    if (!gameConfig.startDate) return undefined;
    const start = new Date(gameConfig.startDate);
    if (Number.isNaN(start.getTime())) return undefined;
    const end = new Date(start);
    end.setDate(start.getDate() + gameConfig.days - 1);
    return end.toISOString().slice(0, 10);
  };

  // Adjust lobby visibility based on mode/status
  useEffect(() => {
    if (isMultiplayer) {
      if (storeGameData && status === 'playing') setShowLobby(false);
      return;
    }

    // Solo: lobby only before play; keep GameOver visible when finished
    if (status === 'not_started') {
      setShowLobby(true);
    } else {
      setShowLobby(false);
    }
  }, [isMultiplayer, storeGameData, status]);

  // Only fetch game data for solo mode (not multiplayer)
  const shouldFetchData = !isMultiplayer;
  const { data: gameData, isLoading, error } = useGameData({
    days: gameConfig.days,
    tickers: gameConfig.tickers,
    startDate: gameConfig.startDate,
    endDate: computeEndDate(),
    enabled: shouldFetchData,
  });

  // Load game data into store when ready (solo mode only)
  useEffect(() => {
    if (!isMultiplayer && gameData && !isLoading ) {
      loadGameData(gameData);
    }
  }, [gameData, isLoading, loadGameData, isMultiplayer]);

  // Show appropriate view based on game status
  if (
    status !== 'playing' &&
    (status === 'not_started' || (showLobby && !isMultiplayer))
  ) {
    return (
      <GameLobby
        isLoading={isLoading}
        error={error}
        onStart={() => setShowLobby(false)}
        gameConfig={gameConfig}
        onConfigChange={setGameConfig}
      />
    );
  }

  if (status === 'finished') {
    return <GameOver />;
  }

  return <GameView />;
}
