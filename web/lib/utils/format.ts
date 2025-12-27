/**
 * Format number as currency (USD)
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format number as percentage
 */
export function formatPercent(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format large numbers with K, M, B suffixes
 */
export function formatCompactNumber(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`;
  }
  return value.toFixed(2);
}

/**
 * Format confidence score as percentage string
 */
export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}%`;
}

/**
 * Get color class for recommendation type
 */
export function getRecommendationColor(recommendation: string): string {
  switch (recommendation) {
    case 'STRONG_BUY':
    case 'BUY':
      return 'text-buy bg-buy-bg';
    case 'STRONG_SELL':
    case 'SELL':
      return 'text-sell bg-sell-bg';
    case 'HOLD':
    default:
      return 'text-hold bg-hold-bg';
  }
}

/**
 * Get color class for signal type
 */
export function getSignalColor(signal: string): string {
  switch (signal) {
    case 'BULLISH':
      return 'text-bullish';
    case 'BEARISH':
      return 'text-bearish';
    case 'NEUTRAL':
    default:
      return 'text-neutral';
  }
}

/**
 * Format date to locale string (timezone-safe for YYYY-MM-DD)
 */
export function formatDate(date: string | Date): string {
  let d: Date;

  if (typeof date === 'string') {
    // Handle YYYY-MM-DD as a pure calendar date (avoid UTC shift)
    const [year, month, day] = date.split('-').map(Number);
    d = new Date(year, month - 1, day);
  } else {
    d = date;
  }

  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

