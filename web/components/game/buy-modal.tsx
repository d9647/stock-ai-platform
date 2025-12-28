'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency } from '@/lib/utils/format';

interface BuyModalProps {
  ticker: string;
  onClose: () => void;
}

export function BuyModal({ ticker, onClose }: BuyModalProps) {
  const { player, buy, gameData } = useGameStore();

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) return null;
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  const [shares, setShares] = useState<number | ''>(1);

  if (!currentDayData || !gameData) return null;

  const nextDayData = gameData.days[player.currentDay + 1];
  const executionPrice = nextDayData?.prices[ticker]?.open || 0;
  const shareCount = shares === '' ? 0 : shares;
  const totalCost = shareCount * executionPrice;
  const canAfford = totalCost <= player.cash && shareCount > 0;

  const maxShares =
    executionPrice > 0 ? Math.floor(player.cash / executionPrice) : 0;

  const handleBuy = () => {
    if (!canAfford || shares === '') return;
    buy(ticker, shares);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-layer2 border border-borderDark-subtle rounded-md max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Buy {ticker}
        </h2>

        {/* Execution Price Card */}
        <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 mb-4">
          <div className="text-xs text-text-muted mb-1">
            Execution price (tomorrow’s open)
          </div>
          <div className="text-xl font-mono font-semibold text-text-primary">
            {formatCurrency(executionPrice)}
          </div>
          <div className="text-xs text-text-muted mt-1">
            Executes at start of Day {player.currentDay + 2}
          </div>
        </div>

        {/* Shares Input */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-text-muted mb-2">
            Shares to buy
          </label>
          <input
            type="number"
            min={1}
            max={maxShares}
            value={shares}
            onChange={(e) => {
              const value = e.target.value;
              if (value === '') {
                setShares('');
              } else {
                const num = parseInt(value);
                if (!isNaN(num)) {
                  setShares(Math.max(1, Math.min(num, maxShares)));
                }
              }
            }}
            onBlur={() => {
              if (shares === '' || shares < 1) {
                setShares(1);
              }
            }}
            className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary font-mono focus:outline-none focus:border-green-600"
          />
          <div className="text-xs text-text-muted mt-1">
            Max affordable: {maxShares} shares
          </div>
        </div>

        {/* Cost Summary Card */}
        <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 mb-6 text-sm">
          <div className="flex justify-between mb-2">
            <span className="text-text-muted">Total cost</span>
            <span className="font-mono font-medium text-text-primary">
              {formatCurrency(totalCost)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Cash after trade</span>
            <span className="font-mono text-text-primary">
              {formatCurrency(player.cash - totalCost)}
            </span>
          </div>
        </div>

        {/* Error */}
        {!canAfford && shares !== '' && shareCount > 0 && (
          <div className="mb-4 p-3 border border-red-500/30 bg-red-500/10 text-red-400 text-sm rounded-md">
            Insufficient cash. You have {formatCurrency(player.cash)} available.
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-borderDark-subtle text-text-primary hover:bg-layer1 text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleBuy}
            disabled={!canAfford}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm buy
          </button>
        </div>
      </div>
    </div>
  );
}
