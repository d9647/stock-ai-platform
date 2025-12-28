'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency, formatPercent } from '@/lib/utils/format';

export function PortfolioSummary() {
  const { player, config, ai, gameData } = useGameStore();

  const portfolioValue = useMemo(() => {
    if (!gameData) return player.cash;
    const currentDay = gameData.days[player.currentDay];
    if (!currentDay) return player.cash;

    let holdingsValue = 0;
    for (const ticker in player.holdings) {
      const holding = player.holdings[ticker];
      const currentPrice = currentDay.prices[ticker]?.close || holding.avgCost;
      holdingsValue += holding.shares * currentPrice;
    }
    return player.cash + holdingsValue;
  }, [player.cash, player.holdings, player.currentDay, gameData]);

  const aiPortfolioValue = useMemo(() => {
    if (!gameData) return ai.cash;
    const currentDay = gameData.days[player.currentDay];
    if (!currentDay) return ai.cash;

    let holdingsValue = 0;
    for (const ticker in ai.holdings) {
      const holding = ai.holdings[ticker];
      const currentPrice = currentDay.prices[ticker]?.close || holding.avgCost;
      holdingsValue += holding.shares * currentPrice;
    }
    return ai.cash + holdingsValue;
  }, [ai.cash, ai.holdings, player.currentDay, gameData]);

  const playerReturn = ((portfolioValue - config.initialCash) / config.initialCash) * 100;
  const aiReturn = ((aiPortfolioValue - config.initialCash) / config.initialCash) * 100;
  const beatAI = playerReturn > aiReturn;

  const holdingsValue = portfolioValue - player.cash;

  return (
    <div className="bg-layer1 rounded-lg shadow-soft p-5 border border-borderDark-subtle">
      <h2 className="text-lg font-bold text-text-primary mb-3">Your Portfolio</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        {/* Total Value */}
        <div>
          <div className="text-sm text-text-muted">Total Value</div>
          <div className="text-xl font-bold text-text-primary">{formatCurrency(portfolioValue)}</div>
          <div
            className={`text-xs font-semibold ${
              playerReturn >= 0 ? 'text-success' : 'text-error'
            }`}
          >
            {playerReturn >= 0 ? '+' : ''}
            {formatPercent(playerReturn / 100)}
          </div>
        </div>

        {/* Cash */}
        <div>
          <div className="text-sm text-text-muted">Cash</div>
          <div className="text-xl font-bold text-text-primary">{formatCurrency(player.cash)}</div>
          <div className="text-xs text-text-secondary">{formatPercent(player.cash / portfolioValue)}</div>
        </div>

        {/* Holdings */}
        <div>
          <div className="text-sm text-text-muted">Holdings Value</div>
          <div className="text-xl font-bold text-text-primary">{formatCurrency(holdingsValue)}</div>
          <div className="text-xs text-text-secondary">
            {formatPercent(holdingsValue / portfolioValue)}
          </div>
        </div>
      </div>

      {/* vs. AI */}
      <div className="mt-5 pt-5 border-t border-borderDark-subtle text-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-text-muted">AI Portfolio</div>
            <div className="text-base font-semibold text-text-secondary">
              {formatCurrency(aiPortfolioValue)}
            </div>
          </div>
          <div className="text-right">
            {beatAI ? (
              <div className="text-success font-bold text-base">
                You're winning!
              </div>
            ) : (
              <div className="text-warning font-bold text-base">AI is ahead</div>
            )}
            <div className="text-xs text-text-muted">
              AI Return: {formatPercent(aiReturn / 100)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
