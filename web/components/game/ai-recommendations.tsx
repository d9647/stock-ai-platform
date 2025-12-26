'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import {
  formatConfidence,
  getRecommendationColor,
  getSignalColor,
} from '@/lib/utils/format';
import { cn } from '@/lib/utils/cn';

export function AIRecommendations() {
  const { player, gameData } = useGameStore();
  const canBuy = useGameStore((state) => state.canBuy);

  const [showDetails, setShowDetails] = useState(false);

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  if (!currentDayData) return null;
  const recs = currentDayData.recommendations || [];
  const tickers = gameData?.tickers || [];
  const hasRecs = recs.length > 0;
  const isWeekend = (() => {
    const [year, month, dayNum] = currentDayData.date.split('-').map(Number);
    const d = new Date(year, month - 1, dayNum);
    return d.getDay() === 0 || d.getDay() === 6;
  })();

  /* ---------------- Weekend ---------------- */
  // Only treat as weekend if the calendar day is actually a weekend; otherwise
  // allow rendering even if the backend flagged non-trading due to missing data.
  if (isWeekend) {
    return (
      <div className="bg-layer2 border border-borderDark-subtle p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          AI Recommendations
        </h2>
        <div className="text-center py-8">
          <div className="text-4xl mb-3">🏖️</div>
          <p className="text-text-primary font-medium">
            Markets closed (weekend)
          </p>
          <p className="text-sm text-text-muted mt-1">
            Recommendations resume on the next trading day.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-layer2 border border-borderDark-subtle p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          AI Recommendations
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto pr-1">
          {(tickers.length ? tickers : recs.map((r) => r.ticker)).map((ticker) => {
            const rec = recs.find((r) => r.ticker === ticker);
            const validation = canBuy(ticker);
            const canBuyThis = true; // keep buy enabled

            return rec ? (
              <div
                key={ticker}
                className="bg-layer1 border border-borderDark-subtle p-4 flex flex-col gap-3"
              >
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-mono text-lg font-semibold text-text-primary">
                      {rec.ticker}
                    </div>
                    <span
                      className={cn(
                        'inline-block mt-1 px-2 py-0.5 text-xs font-semibold',
                        getRecommendationColor(rec.recommendation)
                      )}
                    >
                      {rec.recommendation.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-text-muted">Confidence</div>
                    <div className="text-sm font-semibold text-text-primary">
                      {formatConfidence(rec.confidence)}
                    </div>
                  </div>
                </div>

                {/* Signals */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <Signal label="Technical" value={rec.technical_signal} />
                  <Signal label="Sentiment" value={rec.sentiment_signal} />
                  <div>
                    <div className="text-text-muted">Risk</div>
                    <div className="font-semibold text-text-secondary">
                      {rec.risk_level.replace('_', ' ')}
                    </div>
                  </div>
                </div>

                {/* Rationale summary */}
                <div className="text-sm text-text-secondary">
                  {rec.rationale_summary || 'No rationale available.'}
                </div>

                {/* Toggle analysis */}
                {(rec.rationale_technical_view?.length ||
                  rec.rationale_sentiment_view?.length ||
                  rec.rationale_risk_view?.length) ? (
                  <button
                    onClick={() => setShowDetails((v) => !v)}
                    className="text-xs text-accent text-left"
                  >
                    {showDetails ? 'Hide analysis' : 'Show analysis'}
                  </button>
                ) : null}

                {/* Detailed analysis */}
                {showDetails && (
                  <div className="space-y-3 text-xs">
                    {rec.rationale_technical_view?.length > 0 && (
                      <Section title="Technical">
                        {rec.rationale_technical_view.map((f, i) => (
                          <ReasonItem key={i} text={f} />
                        ))}
                      </Section>
                    )}
                    {rec.rationale_sentiment_view?.length > 0 && (
                      <Section title="Sentiment">
                        {rec.rationale_sentiment_view.map((f, i) => (
                          <ReasonItem key={i} text={f} />
                        ))}
                      </Section>
                    )}
                    {rec.rationale_risk_view?.length > 0 && (
                      <Section title="Risk">
                        {rec.rationale_risk_view.map((f, i) => (
                          <ReasonItem key={i} text={f} />
                        ))}
                      </Section>
                    )}
                    <div className="text-text-muted">
                      As of {rec.as_of_date}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div
                key={ticker}
                className="bg-layer1 border border-borderDark-subtle p-4 flex flex-col gap-3"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-mono text-lg font-semibold text-text-primary">
                      {ticker}
                    </div>
                    <span className="inline-block mt-1 px-2 py-0.5 text-xs font-semibold bg-layer2 text-text-muted border border-borderDark-subtle">
                      No AI recommendation
                    </span>
                  </div>
                </div>
                <div className="text-sm text-text-secondary">
                  No AI analysis available for today. You can still trade using price charts.
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}

/* ---------------- Helpers ---------------- */

function Signal({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-text-muted">{label}</div>
      <div className={cn('font-semibold', getSignalColor(value))}>
        {value}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-text-muted font-semibold mb-1">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function ReasonItem({ text }: { text: string }) {
  return (
    <div className="bg-layer3 border border-borderDark-subtle px-2 py-1 text-text-secondary">
      {text}
    </div>
  );
}
