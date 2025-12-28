'use client';

import { useState, useRef } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';

interface GameLobbyProps {
  isLoading: boolean;
  error: Error | null;
  onStart: () => void;
  gameConfig: {
    days: number;
    startDate?: string;
    tickers: string[];
  };
  onConfigChange: (config: { days: number; startDate?: string; tickers: string[] }) => void;
}

// All available stocks
const ALL_AVAILABLE_TICKERS = [
  'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMZN', 'TSLA', 'META', 'WMT',
  'MU', 'AVGO', 'TSM', 'JPM', 'BRK.A', 'INTC', 'AMD', 'QCOM',
  'TXN', 'LRCX', 'KLAC', 'ASML', 'LLY', 'ORCL', 'V', 'PYPL',
  'MA', 'JNJ', 'PLTR'
];

export function GameLobby({
  isLoading,
  error,
  onStart,
  gameConfig,
  onConfigChange,
}: GameLobbyProps) {
  const { startGame } = useGameStore();
  const [showAllTickers, setShowAllTickers] = useState(false);
  const [showStockPicker, setShowStockPicker] = useState(false);
  const dateInputRef = useRef<HTMLInputElement>(null);

  const handleStartGame = () => {
    startGame({
      initialCash: 100000,
      numDays: gameConfig.days,
      tickers: gameConfig.tickers,
      difficulty: 'medium',
      startDate: gameConfig.startDate,
    });
    onStart();
  };

  const toggleTicker = (ticker: string) => {
    const newTickers = gameConfig.tickers.includes(ticker)
      ? gameConfig.tickers.filter(t => t !== ticker)
      : [...gameConfig.tickers, ticker];

    onConfigChange({
      ...gameConfig,
      tickers: newTickers,
    });
  };

  const handleDateDoubleClick = () => {
    if (dateInputRef.current) {
      dateInputRef.current.showPicker();
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="bg-layer2 border border-borderDark-subtle max-w-2xl w-full p-8 rounded-md">
        {/* Title */}
        <div className="mb-8 text-center rounded-full">
          <h1 className="text-3xl font-semibold text-text-primary mb-2">
            How do you like to play?
          </h1>
          <p className="text-sm text-text-secondary">
            Choose a start date and game length, begin with $100,000, pick your stocks, and trade using daily market data and AI insights.
          </p>
        </div>

        {/* How to Play */}
        {/*<div className="bg-layer1 border border-borderDark-subtle p-6 mb-8 rounded-full">
          <h2 className="text-sm font-medium text-text-primary mb-4">
            How this simulation works
          </h2>
          <p className="text-sm text-text-secondary">
            Choose a start date and game length, begin with $100,000, pick your stocks, and trade using daily market data and AI insights.
          </p>
        </div>*/}

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
                max="90"
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
                <span>90</span>
              </div>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-xs text-text-muted mb-2">
                Start Date (earliest 2025-01-01)
              </label>
              <div className="max-w-[200px]">
                <input
                  ref={dateInputRef}
                  type="date"
                  min="2025-01-01"
                  value={gameConfig.startDate || '2025-01-01'}
                  onChange={(e) => {
                    const selectedDate = e.target.value;
                    // Prevent dates earlier than 2025-01-01
                    if (selectedDate >= '2025-01-01') {
                      onConfigChange({
                        ...gameConfig,
                        startDate: selectedDate,
                      });
                    }
                  }}
                  onClick={() => dateInputRef.current?.showPicker()}
                  className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary cursor-pointer rounded-md"
                />
              </div>
              <p className="text-xs text-text-muted mt-1">
                Latest start depends on available data; choose any date on or after 2025-01-01.
              </p>
            </div>

            {/* Tickers */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-xs text-text-muted">
                  Stocks included ({gameConfig.tickers.length} selected)
                </label>
                <button
                  onClick={() => setShowStockPicker(!showStockPicker)}
                  className="text-xs text-text-muted hover:text-text-primary underline"
                >
                  {showStockPicker ? 'Done' : 'Select stocks'}
                </button>
              </div>

              {/* Stock Picker */}
              {showStockPicker ? (
                <div className="bg-layer1 border border-borderDark-subtle p-4 rounded max-h-64 overflow-y-auto">
                  <div className="grid grid-cols-4 gap-2">
                    {ALL_AVAILABLE_TICKERS.map((ticker) => {
                      const isSelected = gameConfig.tickers.includes(ticker);
                      return (
                        <button
                          key={ticker}
                          onClick={() => toggleTicker(ticker)}
                          className={`px-3 py-2 text-xs font-mono border transition-colors ${
                            isSelected
                              ? 'bg-neutral-600 border-neutral-500 text-white'
                              : 'border-borderDark-subtle text-text-muted hover:bg-layer2 hover:text-text-primary'
                          }`}
                        >
                          {ticker}
                        </button>
                      );
                    })}
                  </div>
                  <div className="mt-3 pt-3 border-t border-borderDark-subtle flex gap-2">
                    <button
                      onClick={() => onConfigChange({ ...gameConfig, tickers: ALL_AVAILABLE_TICKERS })}
                      className="text-xs text-text-muted hover:text-text-primary underline"
                    >
                      Select all
                    </button>
                    <button
                      onClick={() => onConfigChange({ ...gameConfig, tickers: [] })}
                      className="text-xs text-text-muted hover:text-text-primary underline"
                    >
                      Clear all
                    </button>
                  </div>
                </div>
              ) : (
                /* Selected Stocks Display */
                <div className="flex gap-2 flex-wrap items-center">
                  {gameConfig.tickers.length === 0 ? (
                    <span className="text-xs text-text-muted italic">No stocks selected</span>
                  ) : (
                    <>
                      {(showAllTickers ? gameConfig.tickers : gameConfig.tickers.slice(0, 5)).map((ticker) => (
                        <span
                          key={ticker}
                          className="px-3 py-1 border border-borderDark-subtle text-text-primary text-xs font-mono"
                        >
                          {ticker}
                        </span>
                      ))}
                      {gameConfig.tickers.length > 5 && (
                        <button
                          onClick={() => setShowAllTickers(!showAllTickers)}
                          className="px-3 py-1 border border-borderDark-subtle text-text-muted hover:text-text-primary hover:bg-layer1 text-xs transition-colors"
                        >
                          {showAllTickers ? '− Show less' : `+ ${gameConfig.tickers.length - 5} more`}
                        </button>
                      )}
                    </>
                  )}
                </div>
              )}
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

        {/* Start and Cancel Buttons */}
        <div className="flex gap-3 justify-end">
          <button
            type="button"
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 text-sm font-medium text-text-muted border border-borderDark-subtle rounded-full transition-colors hover:text-text-primary hover:bg-layer1"
          >
            Cancel
          </button>
          <button
            onClick={handleStartGame}
            disabled={isLoading || !!error}
            className="px-6 py-2 btn-primary text-sm font-medium border border-borderDark-subtle rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Preparing…' : 'Let\'s play!'}
          </button>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-xs text-text-muted">
          Educational simulation only · No real money involved
        </div>
      </div>
    </div>
  );
}
