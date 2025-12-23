'use client';

import { useGameStore } from '@/lib/stores/gameStore';

interface GameLobbyProps {
  isLoading: boolean;
  error: Error | null;
  onStart: () => void;
  gameConfig: {
    days: number;
    tickers: string[];
  };
  onConfigChange: (config: { days: number; tickers: string[] }) => void;
}

export function GameLobby({
  isLoading,
  error,
  onStart,
  gameConfig,
  onConfigChange,
}: GameLobbyProps) {
  const { startGame } = useGameStore();

  const handleStartGame = () => {
    startGame({
      initialCash: 10000,
      numDays: gameConfig.days,
      tickers: gameConfig.tickers,
      difficulty: 'medium',
    });
    onStart();
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="bg-layer2 border border-borderDark-subtle max-w-2xl w-full p-8">
        {/* Title */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold text-text-primary mb-2">
            AI Stock Challenge
          </h1>
          <p className="text-sm text-text-secondary">
            Learn portfolio decision-making by comparing your results with an AI benchmark
          </p>
        </div>

        {/* How to Play */}
        <div className="bg-layer1 border border-borderDark-subtle p-6 mb-8">
          <h2 className="text-sm font-medium text-text-primary mb-4">
            How this simulation works
          </h2>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li>• You start with <strong className="text-text-primary">$10,000</strong> in virtual cash</li>
            <li>• Each day, the AI provides market analysis and recommendations</li>
            <li>• You may buy only when the AI signals BUY or STRONG BUY</li>
            <li>• You choose when to sell based on your own judgment</li>
            <li>• Trades execute at the next market open</li>
            <li>
              • At the end, your performance is evaluated against the AI as a reference point
            </li>
          </ul>
        </div>

        {/* Game Settings */}
        <div className="mb-8">
          <h2 className="text-sm font-medium text-text-primary mb-4">
            Game settings
          </h2>

          <div className="space-y-6">
            {/* Days */}
            <div>
              <label className="block text-xs text-text-muted mb-2">
                Duration: <span className="text-text-primary font-medium">{gameConfig.days} days</span>
              </label>
              <input
                type="range"
                min="10"
                max="60"
                step="10"
                value={gameConfig.days}
                onChange={(e) =>
                  onConfigChange({
                    ...gameConfig,
                    days: parseInt(e.target.value),
                  })
                }
                className="w-full accent-neutral-400"
              />
              <div className="flex justify-between text-xs text-text-muted mt-1">
                <span>10</span>
                <span>30</span>
                <span>60</span>
              </div>
            </div>

            {/* Tickers */}
            <div>
              <label className="block text-xs text-text-muted mb-2">
                Stocks included
              </label>
              <div className="flex gap-2 flex-wrap">
                {gameConfig.tickers.map((ticker) => (
                  <span
                    key={ticker}
                    className="px-3 py-1 border border-borderDark-subtle text-text-primary text-xs font-mono"
                  >
                    {ticker}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 border border-red-500/40 bg-layer1 text-sm text-red-400">
            <div className="font-medium mb-1">
              Unable to load game data
            </div>
            <div className="text-xs opacity-80">
              {error.message}
            </div>
          </div>
        )}

        {/* Start Button */}
        <button
          onClick={handleStartGame}
          disabled={isLoading || !!error}
          className="w-full btn-primary py-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed rounded-full"
        >
          {isLoading ? 'Preparing simulation…' : 'Start simulation'}
        </button>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-text-muted">
          Educational simulation only · No real money involved
        </div>
      </div>
    </div>
  );
}
