'use client';

import { useMemo } from 'react';
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

export function StockChart({ ticker }: StockChartProps) {
  const { player, gameData } = useGameStore();

const chartData = useMemo<CandlestickData[]>(() => {
  if (!gameData) return [];

  const currentDate = gameData.days[player.currentDay]?.date;
  if (!currentDate) return [];

  return gameData.days
    .filter(
      (day) =>
        day.is_trading_day &&
        day.date <= currentDate
    )
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
  if (gameData && chartData.length > 0) {
    console.log(
      'Decision date:',
      gameData.days[player.currentDay]?.date,
      'Last candle:',
      chartData[chartData.length - 1]?.date
    );
  }

  const latestPrice = chartData[chartData.length - 1];

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">{ticker} Chart</h2>
        <div className="text-center py-8">
          <p className="text-gray-500">No chart data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold font-mono text-gray-900">{ticker}</h2>
          {latestPrice && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-gray-900">
                {formatCurrency(latestPrice.close)}
              </span>
              <span
                className={`text-sm font-semibold ${
                  latestPrice.isGreen ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {latestPrice.isGreen ? '▲' : '▼'}
              </span>
            </div>
          )}
        </div>
        <div className="text-sm text-gray-600">
          Day {player.currentDay + 1} of {gameData?.total_days || 0}
        </div>
      </div>

      {/* Price Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorRed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="displayDate"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            hide
          />
          <YAxis
            domain={['dataMin - 5', 'dataMax + 5']}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
            stroke="#6b7280"
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
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume Chart */}
      <ResponsiveContainer width="100%" height={120}>
        <ComposedChart data={chartData} margin={{ top: 0, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="displayDate"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            tickFormatter={(value) => {
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
              if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
              return value.toString();
            }}
            stroke="#9ca3af"
            style={{ fontSize: '10px' }}
            width={60}
          />
          <Tooltip content={<VolumeTooltip />} />
          <Bar
            dataKey="volume"
            fill="#9ca3af"
            opacity={0.5}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// Unified candlestick bar component (draws both wick and body)
const CandlestickBar = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const { open, close, high, low, isGreen } = payload;
  const color = isGreen ? '#10b981' : '#ef4444';

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
    <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-3">
      <p className="text-sm font-semibold text-gray-900 mb-2">{data.displayDate}</p>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Open:</span>
          <span className="font-mono font-semibold">{formatCurrency(data.open)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">High:</span>
          <span className="font-mono font-semibold text-green-600">{formatCurrency(data.high)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Low:</span>
          <span className="font-mono font-semibold text-red-600">{formatCurrency(data.low)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Close:</span>
          <span className={`font-mono font-semibold ${data.isGreen ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(data.close)}
          </span>
        </div>
        <div className="flex justify-between gap-4 pt-1 border-t border-gray-200">
          <span className="text-gray-600">Volume:</span>
          <span className="font-mono font-semibold text-gray-900">{formatVolume(data.volume)}</span>
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
    <div className="bg-white border border-gray-300 rounded-lg shadow-lg p-2">
      <p className="text-xs font-semibold text-gray-900 mb-1">{data.displayDate}</p>
      <div className="text-xs">
        <span className="text-gray-600">Volume: </span>
        <span className="font-mono font-semibold text-gray-900">
          {data.volume.toLocaleString('en-US')}
        </span>
      </div>
    </div>
  );
};
