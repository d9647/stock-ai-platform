'use client';

import { useMemo, useState } from 'react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Bar,
} from 'recharts';
import { useGameStore } from '@/lib/stores/gameStore';
import { formatCurrency } from '@/lib/utils/format';
import { BuyModal } from './buy-modal';
import { SellModal } from './sell-modal';

interface StockChartProps {
  ticker: string;
}

interface CandlestickData {
  day: number;
  date: string;
  displayDate: string; // Formatted for display (e.g., "Nov 17")
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  isGreen: boolean;
}

const COMPANY_NAMES: Record<string, string> = {
  AAPL: 'Apple Inc.',
  MSFT: 'Microsoft Corporation',
  GOOGL: 'Alphabet Inc.',
  NVDA: 'NVIDIA Corporation',
  AMZN: 'Amazon.com, Inc.',
  TSLA: 'Tesla, Inc.',
  META: 'Meta Platforms, Inc.',
  WMT: 'Walmart Inc.',
  MU: 'Micron Technology, Inc.',
  AVGO: 'Broadcom Inc.',
  TSM: 'Taiwan Semiconductor Manufacturing Co. Ltd.',
  JPM: 'JPMorgan Chase & Co.',
  'BRK.A': 'Berkshire Hathaway Inc. Class A',
  INTC: 'Intel Corporation',
  AMD: 'Advanced Micro Devices, Inc.',
  QCOM: 'Qualcomm Incorporated',
  TXN: 'Texas Instruments Incorporated',
  LRCX: 'Lam Research Corporation',
  KLAC: 'KLA Corporation',
  ASML: 'ASML Holding N.V.',
  LLY: 'Eli Lilly and Company',
  ORCL: 'Oracle Corporation',
  V: 'Visa Inc.',
  PYPL: 'PayPal Holdings, Inc.',
  MA: 'Mastercard Incorporated',
  JNJ: 'Johnson & Johnson',
  PLTR: 'Palantir Technologies Inc.',
};

export function StockChart({ ticker }: StockChartProps) {
  const { player, gameData } = useGameStore();
  const normalizedTicker = ticker?.toUpperCase();
  const companyName = normalizedTicker ? COMPANY_NAMES[normalizedTicker] : undefined;
  const [showBuy, setShowBuy] = useState(false);
  const [showSell, setShowSell] = useState(false);

const chartData = useMemo<CandlestickData[]>(() => {
  if (!gameData) return [];

  const currentDate = gameData.days[player.currentDay]?.date;
  if (!currentDate) return [];

  return gameData.days
    .filter((day) => {
      // Only plot trading days (skip weekends) and only if we have prices for this ticker
      const [year, month, dayNum] = day.date.split('-').map(Number);
      const dateObj = new Date(year, month - 1, dayNum);
      const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
      return !isWeekend && day.date <= currentDate && day.prices[ticker];
    })
    .map((day) => {
      const price = day.prices[ticker];
      const [year, month, dayNum] = day.date.split('-').map(Number);
      const dateObj = new Date(year, month - 1, dayNum);
      const displayDate = dateObj.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });


      if (!price) {
        return {
          day: day.day,
          date: day.date,
          displayDate,
          open: 0,
          high: 0,
          low: 0,
          close: 0,
          volume: 0,
          isGreen: false,
        };
      }

      return {
        day: day.day,
        date: day.date,
        displayDate,
        open: price.open,
        high: price.high,
        low: price.low,
        close: price.close,
        volume: price.volume,
        isGreen: price.close >= price.open,
      };
    });
}, [gameData, player.currentDay, ticker]);

 // ✅ INSERT DEBUG LOG HERE
  {/*if (gameData && chartData.length > 0) {
    console.log(
      'Decision date:',
      gameData.days[player.currentDay]?.date,
      'Last candle:',
      chartData[chartData.length - 1]?.date
    );
  }*/}

  const latestPrice = chartData[chartData.length - 1];

  if (chartData.length === 0) {
    return (
      <div className="bg-layer1 rounded-lg shadow-soft p-6 border border-borderDark-subtle">
        <h2 className="text-xl font-bold text-text-primary mb-4">{ticker} Chart</h2>
        <div className="text-center py-8">
          <p className="text-text-muted">No chart data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-layer1 rounded-lg shadow-soft p-6 border border-borderDark-subtle">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold font-mono text-text-primary">
            {ticker} · {companyName || 'Stock'}
          </h2>
          {latestPrice && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-text-primary">
                {formatCurrency(latestPrice.close)}
              </span>
              <span
                className={`text-sm font-semibold ${
                  latestPrice.isGreen ? 'text-success' : 'text-error'
                }`}
              >
                {latestPrice.isGreen ? '▲' : '▼'}
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBuy(true)}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-accent text-white hover:bg-accent/80 transition-colors"
          >
            Buy
          </button>
          {player.holdings[normalizedTicker || ticker]?.shares > 0 && (
            <button
              onClick={() => setShowSell(true)}
              className="px-3 py-1.5 text-sm font-medium rounded-lg bg-error text-white hover:bg-error/80 transition-colors"
            >
              Sell
            </button>
          )}
        </div>
      </div>

      {/* Price Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3ddc97" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#3ddc97" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorRed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff6b6b" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#ff6b6b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#3b4060" opacity={0.3} />
          <XAxis
            dataKey="displayDate"
            stroke="#6f748a"
            style={{ fontSize: '12px' }}
            hide
          />
          <YAxis
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
            stroke="#6f748a"
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Unified candlestick (wick + body) */}
          <Bar
            dataKey={(data: CandlestickData) => [data.low, data.high]}
            fill="transparent"
            shape={<CandlestickBar />}
          />

          {/* Close price line */}
          <Line
            type="monotone"
            dataKey="close"
            stroke="#7aa2ff"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume Chart */}
      <ResponsiveContainer width="100%" height={120}>
        <ComposedChart data={chartData} margin={{ top: 0, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3b4060" opacity={0.3} />
          <XAxis
            dataKey="displayDate"
            stroke="#6f748a"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            tickFormatter={(value) => {
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
              if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
              return value.toString();
            }}
            stroke="#6f748a"
            style={{ fontSize: '10px' }}
            width={60}
          />
          <Tooltip content={<VolumeTooltip />} />
          <Bar
            dataKey="volume"
            fill="#a8adbd"
            opacity={0.4}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {showBuy && (
        <BuyModal
          ticker={normalizedTicker || ticker}
          onClose={() => setShowBuy(false)}
        />
      )}
      {showSell && (
        <SellModal
          ticker={normalizedTicker || ticker}
          onClose={() => setShowSell(false)}
        />
      )}
    </div>
  );
}

// Unified candlestick bar component (draws both wick and body)
const CandlestickBar = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const { open, close, high, low, isGreen } = payload;
  const color = isGreen ? '#3ddc97' : '#ff6b6b';

  // This Bar uses dataKey [low, high], so:
  // - y is the pixel position of 'high' (top of wick)
  // - y + height is the pixel position of 'low' (bottom of wick)

  // Calculate center x-position for alignment
  const centerX = x + width / 2;
  const candleWidth = Math.min(width * 0.6, 8);

  // We need to calculate where open and close are in pixel space
  // Since we know high is at y and low is at (y + height),
  // we can interpolate to find open and close positions
  const priceRange = high - low;
  if (priceRange === 0) {
    // Doji candle - all prices are the same
    return (
      <g>
        <line
          x1={centerX}
          y1={y}
          x2={centerX}
          y2={y + height}
          stroke={color}
          strokeWidth={1.5}
        />
        <rect
          x={centerX - candleWidth / 2}
          y={y}
          width={candleWidth}
          height={1}
          fill={color}
          stroke={color}
        />
      </g>
    );
  }

  // Calculate pixel positions for open and close using linear interpolation
  // high is at y (top), low is at y+height (bottom)
  const openY = y + ((high - open) / priceRange) * height;
  const closeY = y + ((high - close) / priceRange) * height;

  // Body goes from min(open, close) to max(open, close)
  const bodyTop = Math.min(openY, closeY);
  const bodyHeight = Math.abs(openY - closeY) || 1; // Min 1px for very small bodies

  return (
    <g>
      {/* Wick: from high to low */}
      <line
        x1={centerX}
        y1={y}
        x2={centerX}
        y2={y + height}
        stroke={color}
        strokeWidth={1.5}
      />

      {/* Body: from open to close */}
      <rect
        x={centerX - candleWidth / 2}
        y={bodyTop}
        width={candleWidth}
        height={bodyHeight}
        fill={color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

// Custom tooltip component for price chart
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload[0]) return null;

  const data: CandlestickData = payload[0].payload;

  // Format volume with commas
  const formatVolume = (volume: number) => {
    return volume.toLocaleString('en-US');
  };

  return (
    <div className="bg-layer2 border border-borderDark-subtle rounded-lg shadow-medium p-3">
      <p className="text-sm font-semibold text-text-primary mb-2">{data.displayDate}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-text-muted">Open:</span>
          <span className="font-mono font-semibold text-text-primary">{formatCurrency(data.open)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-text-muted">High:</span>
          <span className="font-mono font-semibold text-success">{formatCurrency(data.high)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-text-muted">Low:</span>
          <span className="font-mono font-semibold text-error">{formatCurrency(data.low)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-text-muted">Close:</span>
          <span className={`font-mono font-semibold ${data.isGreen ? 'text-success' : 'text-error'}`}>
            {formatCurrency(data.close)}
          </span>
        </div>
        <div className="flex justify-between gap-4 pt-1 border-t border-borderDark-subtle">
          <span className="text-text-muted">Volume:</span>
          <span className="font-mono font-semibold text-text-primary">{formatVolume(data.volume)}</span>
        </div>
      </div>
    </div>
  );
};

// Custom tooltip component for volume chart
const VolumeTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload[0]) return null;

  const data: CandlestickData = payload[0].payload;

  return (
    <div className="bg-layer2 border border-borderDark-subtle rounded-lg shadow-medium p-2">
      <p className="text-xs font-semibold text-text-primary mb-1">{data.displayDate}</p>
      <div className="text-xs">
        <span className="text-text-muted">Volume: </span>
        <span className="font-mono font-semibold text-text-primary">
          {data.volume.toLocaleString('en-US')}
        </span>
      </div>
    </div>
  );
};
