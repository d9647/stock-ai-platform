'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency } from '@/lib/utils/format';

interface SellModalProps {
  ticker: string;
  onClose: () => void;
}

export function SellModal({ ticker, onClose }: SellModalProps) {
  const { player, sell, gameData } = useGameStore();

  const holdings = useMemo(() => {
    if (!gameData) return [];

    const day = gameData.days[player.currentDay];
    if (!day) return [];

    return Object.values(player.holdings).map((holding) => {
      const price = day.prices[holding.ticker]?.close || holding.avgCost;
      return {
        ...holding,
        currentValue: holding.shares * price,
      };
    });
  }, [player.holdings, player.currentDay, gameData]);

  const holding = holdings.find((h) => h.ticker === ticker);
  const [shares, setShares] = useState<number | ''>(holding?.shares || 1);

  if (!holding || !gameData) return null;

  const nextDayData = gameData.days[player.currentDay + 1];
  const executionPrice = nextDayData?.prices[ticker]?.open || 0;

  const shareCount = shares === '' ? 0 : shares;
  const totalProceeds = shareCount * executionPrice;
  const costBasis = shareCount * holding.avgCost;
  const profit = totalProceeds - costBasis;

  const handleSell = () => {
    if (shares === '' || shares < 1) return;
    sell(ticker, shares);
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
          Sell {ticker}
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

        {/* Holding Summary Card */}
        <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 mb-4 text-sm">
          <div className="flex justify-between mb-2">
            <span className="text-text-muted">Shares owned</span>
            <span className="font-mono font-medium text-text-primary">
              {holding.shares}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Average cost</span>
            <span className="font-mono text-text-primary">
              {formatCurrency(holding.avgCost)}
            </span>
          </div>
        </div>

        {/* Shares Input */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-text-muted mb-2">
            Shares to sell
          </label>
          <input
            type="number"
            min={1}
            max={holding.shares}
            value={shares}
            onChange={(e) => {
              const value = e.target.value;
              if (value === '') {
                setShares('');
              } else {
                const num = parseInt(value);
                if (!isNaN(num)) {
                  setShares(Math.min(holding.shares, Math.max(1, num)));
                }
              }
            }}
            onBlur={() => {
              if (shares === '' || shares < 1) {
                setShares(1);
              }
            }}
            className="w-full px-3 py-2 bg-layer1 border border-borderDark-subtle text-text-primary font-mono focus:outline-none focus:border-red-600"
          />

          <div className="flex gap-2 mt-2">
            <button
              onClick={() => setShares(Math.floor(holding.shares / 2))}
              className="px-2 py-1 text-xs border border-borderDark-subtle text-text-muted hover:bg-layer1"
            >
              Half
            </button>
            <button
              onClick={() => setShares(holding.shares)}
              className="px-2 py-1 text-xs border border-borderDark-subtle text-text-muted hover:bg-layer1"
            >
              All
            </button>
          </div>
        </div>

        {/* Proceeds Card */}
        <div className="bg-layer1 border border-borderDark-subtle rounded-md p-4 mb-6 text-sm">
          <div className="flex justify-between mb-2">
            <span className="text-text-muted">Total proceeds</span>
            <span className="font-mono font-medium text-text-primary">
              {formatCurrency(totalProceeds)}
            </span>
          </div>
          <div className="flex justify-between mb-2">
            <span className="text-text-muted">Cost basis</span>
            <span className="font-mono text-text-primary">
              {formatCurrency(costBasis)}
            </span>
          </div>
          <div className="flex justify-between pt-2 border-t border-borderDark-subtle">
            <span className="font-medium text-text-muted">Profit / Loss</span>
            <span
              className={`font-mono font-semibold ${
                profit >= 0 ? 'text-success' : 'text-red-500'
              }`}
            >
              {profit >= 0 ? '+' : ''}
              {formatCurrency(profit)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-borderDark-subtle text-text-primary hover:bg-layer1 text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSell}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium"
          >
            Confirm sell
          </button>
        </div>
      </div>
    </div>
  );
}
