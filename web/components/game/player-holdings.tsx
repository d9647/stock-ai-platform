'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency, formatPercent } from '@/lib/utils/format';
import { SellModal } from './sell-modal';

export function PlayerHoldings() {
  const playerHoldings = useGameStore((state) => state.player.holdings);
  const gameData = useGameStore((state) => state.gameData);
  const currentDay = useGameStore((state) => state.player.currentDay);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  const holdings = useMemo(() => {
    if (!gameData) return [];

    const currentDayData = gameData.days[currentDay];
    if (!currentDayData) return [];

    return Object.values(playerHoldings).map((holding) => {
      const currentPrice = currentDayData.prices[holding.ticker]?.close || holding.avgCost;
      return {
        ...holding,
        currentValue: holding.shares * currentPrice,
        unrealizedPnL: holding.shares * currentPrice - holding.totalCost,
        unrealizedPnLPercent:
          ((holding.shares * currentPrice - holding.totalCost) / holding.totalCost) * 100,
      };
    });
  }, [playerHoldings, gameData, currentDay]);

  if (holdings.length === 0) {
    return (
      <div className="bg-layer1 rounded-lg shadow-soft p-6 border border-borderDark-subtle">
        <h2 className="text-xl font-bold text-text-primary mb-4">Your Holdings</h2>
        <p className="text-text-muted text-center py-8">
          You don't own any stocks yet. You may optionally refer to AI recommendations: BUY or STRONG_BUY.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-layer1 rounded-lg shadow-soft p-5 border border-borderDark-subtle">
        <h2 className="text-lg font-bold text-text-primary mb-3">Your Holdings</h2>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-borderDark-subtle text-left text-xs text-text-muted uppercase tracking-wide">
                <th className="pb-2 font-semibold">Stock</th>
                <th className="pb-2 font-semibold text-right">Shares</th>
                <th className="pb-2 font-semibold text-right">Avg Cost</th>
                <th className="pb-2 font-semibold text-right">Current Value</th>
                <th className="pb-2 font-semibold text-right">P&L</th>
                <th className="pb-2 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {holdings.map((holding) => (
                <tr key={holding.ticker} className="border-b border-borderDark-subtle/50">
                  <td className="py-3">
                    <div className="font-semibold font-mono text-text-primary text-sm">{holding.ticker}</div>
                  </td>
                  <td className="py-3 text-right font-mono text-sm text-text-primary">{holding.shares}</td>
                  <td className="py-3 text-right font-mono text-text-secondary text-sm">
                    {formatCurrency(holding.avgCost)}
                  </td>
                  <td className="py-3 text-right font-mono font-semibold text-sm text-text-primary">
                    {formatCurrency(holding.currentValue)}
                  </td>
                  <td className="py-3 text-right">
                    <div
                      className={`font-semibold text-sm ${
                        holding.unrealizedPnL >= 0 ? 'text-success' : 'text-error'
                      }`}
                    >
                      {holding.unrealizedPnL >= 0 ? '+' : ''}
                      {formatCurrency(holding.unrealizedPnL)}
                    </div>
                    <div
                      className={`text-xs ${
                        holding.unrealizedPnLPercent >= 0 ? 'text-success' : 'text-error'
                      }`}
                    >
                      {holding.unrealizedPnLPercent >= 0 ? '+' : ''}
                      {formatPercent(holding.unrealizedPnLPercent / 100)}
                    </div>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setSelectedTicker(holding.ticker)}
                      className="px-3 py-2 bg-error text-white rounded-lg hover:bg-error/80 font-semibold text-xs transition-colors"
                    >
                      Sell
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sell Modal */}
      {selectedTicker && (
        <SellModal ticker={selectedTicker} onClose={() => setSelectedTicker(null)} />
      )}
    </>
  );
}
