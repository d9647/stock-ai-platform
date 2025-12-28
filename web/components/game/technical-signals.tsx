'use client';

import { useMemo, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, ChevronDown, ChevronUp } from 'lucide-react';

interface TechnicalSignalsProps {
  ticker: string;
  technicalData?: {
    sma_20?: number;
    sma_50?: number;
    sma_200?: number;
    ema_12?: number;
    ema_26?: number;
    rsi_14?: number;
    macd?: number;
    macd_signal?: number;
    macd_histogram?: number;
    bollinger_upper?: number;
    bollinger_middle?: number;
    bollinger_lower?: number;
    atr_14?: number;
    obv?: number;
    volatility_30d?: number;
  };
  currentPrice: number;
}

type SignalStatus = 'bullish' | 'bearish' | 'neutral' | 'caution' | 'unavailable';

interface Signal {
  label: string;
  status: SignalStatus;
  shortText: string;
  details: string;
  tooltip: string;
}

export function TechnicalSignals({ ticker, technicalData, currentPrice }: TechnicalSignalsProps) {
  const [expanded, setExpanded] = useState(false);

  const signals = useMemo<Signal[]>(() => {
    if (!technicalData ||
        technicalData.rsi_14 === undefined ||
        technicalData.macd_histogram === undefined ||
        technicalData.ema_12 === undefined ||
        technicalData.ema_26 === undefined ||
        technicalData.sma_20 === undefined ||
        technicalData.sma_50 === undefined ||
        technicalData.bollinger_upper === undefined ||
        technicalData.bollinger_lower === undefined ||
        technicalData.bollinger_middle === undefined ||
        technicalData.atr_14 === undefined) {
      return [
        {
          label: 'Momentum',
          status: 'unavailable',
          shortText: 'N/A',
          details: 'No data',
          tooltip: 'Technical indicators not available',
        },
        {
          label: 'Trend',
          status: 'unavailable',
          shortText: 'N/A',
          details: 'No data',
          tooltip: 'Trend indicators not available',
        },
        {
          label: 'Range',
          status: 'unavailable',
          shortText: 'N/A',
          details: 'No data',
          tooltip: 'Volatility indicators not available',
        },
        {
          label: 'Reversion',
          status: 'unavailable',
          shortText: 'N/A',
          details: 'No data',
          tooltip: 'Mean reversion indicators not available',
        },
      ];
    }

    const {
      rsi_14,
      macd_histogram,
      ema_12,
      ema_26,
      sma_20,
      sma_50,
      bollinger_upper,
      bollinger_lower,
      bollinger_middle,
      atr_14,
      obv,
    } = technicalData;

    // A. Momentum Signal
    const momentumSignal: Signal = (() => {
      const macdBullish = macd_histogram! > 0;
      const rsiStrong = rsi_14! >= 60 && rsi_14! <= 70;
      const rsiOverbought = rsi_14! > 70;

      if (macdBullish && rsiStrong) {
        return {
          label: 'Momentum',
          status: 'bullish',
          shortText: 'Bullish',
          details: `RSI ${rsi_14!.toFixed(1)} | MACD +${macd_histogram!.toFixed(2)}`,
          tooltip: 'Momentum is positive and accelerating. RSI is elevated but not extreme.',
        };
      } else if (macdBullish && rsiOverbought) {
        return {
          label: 'Momentum',
          status: 'caution',
          shortText: 'Extended',
          details: `RSI ${rsi_14!.toFixed(1)} | MACD +${macd_histogram!.toFixed(2)}`,
          tooltip: 'Strong momentum but RSI indicates overbought conditions. Watch for pullback.',
        };
      } else if (!macdBullish && rsi_14! < 40) {
        return {
          label: 'Momentum',
          status: 'bearish',
          shortText: 'Bearish',
          details: `RSI ${rsi_14!.toFixed(1)} | MACD ${macd_histogram!.toFixed(2)}`,
          tooltip: 'Negative momentum with weak RSI. Downside pressure present.',
        };
      } else {
        return {
          label: 'Momentum',
          status: 'neutral',
          shortText: 'Neutral',
          details: `RSI ${rsi_14!.toFixed(1)} | MACD ${macd_histogram!.toFixed(2)}`,
          tooltip: 'Mixed momentum signals. No clear directional bias.',
        };
      }
    })();

    // B. Trend Signal
    const trendSignal: Signal = (() => {
      const shortTermUp = ema_12! > ema_26!;
      const intermediateUp = sma_20! > sma_50!;

      if (shortTermUp && intermediateUp) {
        return {
          label: 'Trend',
          status: 'bullish',
          shortText: 'Uptrend',
          details: `EMA12 > EMA26 | SMA20 > SMA50`,
          tooltip: 'Short-term and intermediate trends are aligned upward.',
        };
      } else if (!shortTermUp && !intermediateUp) {
        return {
          label: 'Trend',
          status: 'bearish',
          shortText: 'Downtrend',
          details: `EMA12 < EMA26 | SMA20 < SMA50`,
          tooltip: 'Both short and intermediate trends are pointing down.',
        };
      } else {
        return {
          label: 'Trend',
          status: 'neutral',
          shortText: 'Mixed',
          details: shortTermUp ? 'EMA12 > EMA26 | SMA20 < SMA50' : 'EMA12 < EMA26 | SMA20 > SMA50',
          tooltip: 'Trend signals are conflicting. Wait for confirmation.',
        };
      }
    })();

    // C. Range/Volatility Signal
    const rangeSignal: Signal = (() => {
      const bbWidth = bollinger_upper! - bollinger_lower!;
      const bbWidthPercent = (bbWidth / bollinger_middle!) * 100;

      let status: SignalStatus = 'neutral';
      let shortText = 'Normal';
      let tooltip = 'Volatility is within normal ranges.';

      if (bbWidthPercent > 10) {
        status = 'caution';
        shortText = 'Expanded';
        tooltip = 'Daily movement is large. Use tighter risk controls.';
      } else if (bbWidthPercent < 5) {
        status = 'caution';
        shortText = 'Compressed';
        tooltip = 'Range is tight. Expecting volatility expansion soon.';
      }

      return {
        label: 'Range',
        status,
        shortText,
        details: `ATR ${atr_14!.toFixed(2)} | BB Range ${bbWidthPercent.toFixed(1)}%`,
        tooltip,
      };
    })();

    // D. Mean Reversion Risk Signal
    const reversionSignal: Signal = (() => {
      const bbWidth = bollinger_upper! - bollinger_lower!;
      const pricePosition = (currentPrice - bollinger_lower!) / bbWidth;

      if (rsi_14! > 70 || pricePosition > 0.9) {
        return {
          label: 'Reversion',
          status: 'caution',
          shortText: 'High Risk',
          details: `RSI ${rsi_14!.toFixed(1)} | Near BB Upper`,
          tooltip: 'Price is extended. High probability of pullback or consolidation.',
        };
      } else if (rsi_14! < 30 || pricePosition < 0.1) {
        return {
          label: 'Reversion',
          status: 'bullish',
          shortText: 'Oversold',
          details: `RSI ${rsi_14!.toFixed(1)} | Near BB Lower`,
          tooltip: 'Price is oversold. Potential bounce setup.',
        };
      } else if (rsi_14! > 65) {
        return {
          label: 'Reversion',
          status: 'caution',
          shortText: 'Moderate',
          details: `RSI ${rsi_14!.toFixed(1)}`,
          tooltip: 'Momentum is strong, but upside continuation may require consolidation.',
        };
      } else {
        return {
          label: 'Reversion',
          status: 'neutral',
          shortText: 'Low Risk',
          details: `RSI ${rsi_14!.toFixed(1)}`,
          tooltip: 'Price is within normal range. Low mean reversion risk.',
        };
      }
    })();

    // E. Volume Signal (simplified since we only have OBV absolute value)
    const volumeSignal: Signal = {
      label: 'Volume',
      status: (obv ?? 0) > 0 ? 'bullish' : 'neutral',
      shortText: (obv ?? 0) > 0 ? 'Supportive' : 'Neutral',
      details: `OBV ${((obv ?? 0) / 1000000).toFixed(1)}M`,
      tooltip:
        (obv ?? 0) > 0
          ? 'On-balance volume is positive, suggesting accumulation.'
          : 'Volume data available but no clear directional signal.',
    };

    return [momentumSignal, trendSignal, rangeSignal, reversionSignal, volumeSignal];
  }, [technicalData, currentPrice]);

  // Calculate overall bias
  const overallBias = useMemo(() => {
    if (!technicalData) return { status: 'unavailable' as SignalStatus, text: 'N/A' };

    const weights = {
      Momentum: 0.3,
      Trend: 0.3,
      Range: 0.2,
      Reversion: 0.2,
    };

    let bullishScore = 0;
    let bearishScore = 0;

    signals.forEach((signal) => {
      const weight = weights[signal.label as keyof typeof weights] || 0;
      if (signal.status === 'bullish') bullishScore += weight;
      else if (signal.status === 'bearish') bearishScore += weight;
      else if (signal.status === 'caution' && signal.label === 'Reversion') bearishScore += weight * 0.5;
    });

    if (bullishScore > bearishScore + 0.2) {
      return { status: 'bullish' as SignalStatus, text: 'Bullish' };
    } else if (bearishScore > bullishScore + 0.2) {
      return { status: 'bearish' as SignalStatus, text: 'Bearish' };
    } else {
      return { status: 'neutral' as SignalStatus, text: 'Neutral' };
    }
  }, [signals, technicalData]);

  const getStatusColor = (status: SignalStatus) => {
    switch (status) {
      case 'bullish':
        return 'bg-success/20 text-success border-success/30';
      case 'bearish':
        return 'bg-error/20 text-error border-error/30';
      case 'caution':
        return 'bg-warning/20 text-warning border-warning/30';
      case 'neutral':
        return 'bg-layer3 text-text-secondary border-borderDark-subtle';
      case 'unavailable':
        return 'bg-layer3 text-text-muted border-borderDark-subtle';
    }
  };

  const getStatusIcon = (status: SignalStatus) => {
    switch (status) {
      case 'bullish':
        return <TrendingUp className="w-3 h-3" />;
      case 'bearish':
        return <TrendingDown className="w-3 h-3" />;
      default:
        return <Minus className="w-3 h-3" />;
    }
  };

  return (
    <div className="bg-layer1 rounded-lg shadow-soft p-4 border border-borderDark-subtle">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-bold text-text-primary">Technical Signals</h3>
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-semibold ${getStatusColor(overallBias.status)}`}>
            {getStatusIcon(overallBias.status)}
            <span>Overall: {overallBias.text}</span>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-text-muted hover:text-text-primary transition-colors"
          aria-label={expanded ? 'Collapse details' : 'Expand details'}
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Signal Strip */}
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {signals.map((signal) => (
          <div
            key={signal.label}
            className={`group relative flex items-center gap-1 px-2 py-1.5 rounded border text-xs font-medium transition-all cursor-help flex-shrink-0 ${getStatusColor(signal.status)}`}
            title={signal.tooltip}
          >
            {getStatusIcon(signal.status)}
            <div className="flex flex-col">
              <span className="font-semibold text-[10px] sm:text-xs">{signal.label}</span>
              <span className="text-[9px] sm:text-[10px] opacity-90">{signal.shortText}</span>
            </div>

            {/* Tooltip on hover */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10 w-64">
              <div className="bg-layer2 border border-borderDark-subtle rounded-lg shadow-medium p-3 text-xs">
                <div className="font-semibold text-text-primary mb-1">
                  {signal.label}: {signal.shortText}
                </div>
                <div className="text-text-secondary mb-2">{signal.details}</div>
                <div className="text-text-muted text-[10px]">{signal.tooltip}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Expanded Details */}
      {expanded && technicalData && (
        <div className="mt-4 pt-4 border-t border-borderDark-subtle">
          <div className="grid grid-cols-2 gap-3 text-xs">
            {signals.map((signal) => (
              <div key={signal.label} className="bg-layer2 rounded p-2 border border-borderDark-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-text-primary">{signal.label}</span>
                  <span className={`text-xs font-medium ${signal.status === 'bullish' ? 'text-success' : signal.status === 'bearish' ? 'text-error' : signal.status === 'caution' ? 'text-warning' : 'text-text-muted'}`}>
                    {signal.shortText}
                  </span>
                </div>
                <div className="text-text-secondary text-[10px] mb-1">{signal.details}</div>
                <div className="text-text-muted text-[10px]">{signal.tooltip}</div>
              </div>
            ))}
          </div>

          {/* Raw Values (Optional) */}
          <div className="mt-3 pt-3 border-t border-borderDark-subtle">
            <button
              onClick={() => setExpanded(false)}
              className="text-xs text-accent hover:text-accent/80 transition-colors"
            >
              Show less ↑
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
