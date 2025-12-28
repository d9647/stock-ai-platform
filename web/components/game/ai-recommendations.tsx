'use client';

import { useState, useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import {
  formatConfidence,
  getRecommendationColor,
  getSignalColor,
} from '@/lib/utils/format';
import { cn } from '@/lib/utils/cn';
import { ChevronDown, ChevronUp } from 'lucide-react';

// Ticker to company name mapping
const COMPANY_NAMES: Record<string, string> = {
  'AAPL': 'Apple Inc.',
  'MSFT': 'Microsoft Corp.',
  'GOOGL': 'Alphabet Inc.',
  'NVDA': 'NVIDIA Corp.',
  'AMZN': 'Amazon.com Inc.',
  'TSLA': 'Tesla Inc.',
  'META': 'Meta Platforms Inc.',
  'WMT': 'Walmart Inc.',
  'MU': 'Micron Technology Inc.',
  'AVGO': 'Broadcom Inc.',
  'TSM': 'Taiwan Semiconductor',
  'JPM': 'JPMorgan Chase & Co.',
  'BRK.A': 'Berkshire Hathaway Inc.',
  'INTC': 'Intel Corp.',
  'AMD': 'Advanced Micro Devices Inc.',
  'QCOM': 'Qualcomm Inc.',
  'TXN': 'Texas Instruments Inc.',
  'LRCX': 'Lam Research Corp.',
  'KLAC': 'KLA Corp.',
  'ASML': 'ASML Holding N.V.',
  'LLY': 'Eli Lilly and Co.',
  'ORCL': 'Oracle Corp.',
  'V': 'Visa Inc.',
  'PYPL': 'PayPal Holdings Inc.',
  'MA': 'Mastercard Inc.',
  'JNJ': 'Johnson & Johnson',
  'PLTR': 'Palantir Technologies Inc.',
};

// Format recommendation text (convert STRONG_BUY to "Strong Buy")
function formatRecommendation(rec: string): string {
  return rec
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function AIRecommendations() {
  const { player, gameData } = useGameStore();
  const canBuy = useGameStore((state) => state.canBuy);

  const [expandedTickers, setExpandedTickers] = useState<Set<string>>(new Set());

  const toggleDetails = (ticker: string) => {
    setExpandedTickers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ticker)) {
        newSet.delete(ticker);
      } else {
        newSet.add(ticker);
      }
      return newSet;
    });
  };

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
          AI Insights
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
      <div className="bg-layer2 border border-borderDark-subtle p-6 rounded-lg">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          AI Recommendations
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[600px] overflow-y-auto pr-1">
          {(tickers.length ? tickers : recs.map((r) => r.ticker)).map((ticker) => {
            const rec = recs.find((r) => r.ticker === ticker);
            const validation = canBuy(ticker);
            const canBuyThis = true; // keep buy enabled
            const isExpanded = expandedTickers.has(ticker);

            return rec ? (
              <div
                key={ticker}
                className="bg-layer1 rounded-lg shadow-soft p-4 border border-borderDark-subtle"
              >
                {/* Header - Match Technical Signals */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3 flex-wrap">
                    <div>
                      <h3 className="text-sm font-bold text-text-primary font-mono">
                        {rec.ticker}
                      </h3>
                      <p className="text-xs text-text-muted">
                        {COMPANY_NAMES[rec.ticker] || rec.ticker}
                      </p>
                    </div>
                    <div
                      className={cn(
                        'flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-semibold',
                        rec.recommendation === 'STRONG_BUY' || rec.recommendation === 'BUY'
                          ? 'bg-success/20 text-success border-success/30'
                          : rec.recommendation === 'STRONG_SELL' || rec.recommendation === 'SELL'
                          ? 'bg-error/20 text-error border-error/30'
                          : 'bg-layer3 text-text-secondary border-borderDark-subtle'
                      )}
                    >
                      {formatRecommendation(rec.recommendation)}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleDetails(ticker)}
                    className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0"
                    aria-label={isExpanded ? 'Hide details' : 'Show details'}
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>

                {/* Quick Signals - Match style */}
                <div className="flex gap-2 text-xs flex-wrap">
                  <div className="px-2 py-1 rounded border font-medium bg-layer3 text-text-secondary border-borderDark-subtle">
                    Tech: {formatRecommendation(rec.technical_signal)}
                  </div>
                  <div className="px-2 py-1 rounded border font-medium bg-layer3 text-text-secondary border-borderDark-subtle">
                    Sent: {formatRecommendation(rec.sentiment_signal)}
                  </div>
                  <div className="px-2 py-1 rounded border font-medium bg-layer3 text-text-secondary border-borderDark-subtle">
                    Risk: {formatRecommendation(rec.risk_level)}
                  </div>
                  <div className="px-2 py-1 rounded border font-medium bg-layer3 text-text-secondary border-borderDark-subtle">
                    Confidence: {formatConfidence(rec.confidence)}
                  </div>
                </div>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div className="space-y-2 text-xs pt-3 mt-3 border-t border-borderDark-subtle">
                    {/* Rationale summary */}
                    {rec.rationale_summary && (
                      <div className="text-sm text-text-secondary">
                        {rec.rationale_summary}
                      </div>
                    )}

                    {/* Detailed analysis */}
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
                    <div className="text-text-muted text-[10px] pt-1">
                      As of {rec.as_of_date}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              // Omit stocks with no recommendations
              null
            );
          }).filter(Boolean)}
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
    <div className="bg-layer3 border border-borderDark-subtle px-2 py-1 text-text-secondary rounded">
      {text}
    </div>
  );
}
