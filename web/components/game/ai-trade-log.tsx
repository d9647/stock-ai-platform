'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';

export function AITradeLog() {
  const { ai } = useGameStore();

  const recentTrades = useMemo(
    () => [...(ai.trades || [])].slice(-10).reverse(), // show last 10, latest first
    [ai.trades]
  );

  if (recentTrades.length === 0) {
    return (
      <div className="bg-layer2 border border-borderDark-subtle rounded-md p-4 text-sm text-text-muted">
        AI has not traded yet.
      </div>
    );
  }

  return (
    <div className="bg-layer2 border border-borderDark-subtle rounded-md p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">AI Trade Log</h3>
        <span className="text-xs text-text-muted">Latest 10</span>
      </div>
      <div className="divide-y divide-borderDark-subtle text-sm">
        {recentTrades.map((trade) => (
          <div key={trade.id} className="py-2 flex justify-between items-center">
            <div>
              <div className="text-text-primary font-medium">
                {trade.ticker} • {trade.type}
              </div>
              <div className="text-xs text-text-muted">
                Day {trade.day + 1} · {trade.shares} @ ${trade.price.toFixed(2)}
              </div>
            </div>
            <div className="text-right">
              <div className="text-text-primary font-mono">
                ${trade.total.toFixed(2)}
              </div>
              {trade.portfolioValue > 0 && (
                <div className="text-xs text-text-muted">
                  Portfolio: ${trade.portfolioValue.toFixed(0)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
