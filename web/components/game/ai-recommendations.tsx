'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import {
  formatConfidence,
  getRecommendationColor,
  getSignalColor,
} from '@/lib/utils/format';
import { cn } from '@/lib/utils/cn';
import { BuyModal } from './buy-modal';

export function AIRecommendations() {
  const { player, gameData } = useGameStore();
  const canBuy = useGameStore((state) => state.canBuy);

  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  if (!currentDayData) return null;

  /* ---------------- Weekend ---------------- */
  if (!currentDayData.is_trading_day) {
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentDayData.recommendations.map((rec) => {
            const validation = canBuy(rec.ticker);
            //const canBuyThis = validation.allowed;
            // hardcode to allow to buy for all stocks 
            const canBuyThis = true;
            return (
              <div
                key={rec.ticker}
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

                {/* Buy button */}
                <button
                  onClick={() => setSelectedTicker(rec.ticker)}
                  //disabled={!canBuyThis}
                  className={cn(
                    'mt-2 inline-flex items-center justify-center whitespace-nowrap px-3 py-1.5 text-sm font-medium border rounded-full leading-none transition-colors',
                    canBuyThis
                      ? 'btn-primary border-borderDark-subtle'
                      : 'bg-layer1 text-text-muted border-borderDark-subtle cursor-not-allowed'
                  )}
                  title={canBuyThis ? 'Buy shares' : validation.reason}
                >
                  {canBuyThis ? 'Buy shares' : 'Unavailable'}
                </button>
                {!canBuyThis && (
                  <div className="text-xs text-text-muted text-center">
                    {validation.reason}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {selectedTicker && (
        <BuyModal
          ticker={selectedTicker}
          onClose={() => setSelectedTicker(null)}
        />
      )}
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
