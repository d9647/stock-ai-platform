import Link from 'next/link';
import type { RecommendationSummary } from '@/types/api';
import { formatConfidence, getRecommendationColor, getSignalColor } from '@/lib/utils/format';
import { cn } from '@/lib/utils/cn';

interface RecommendationCardProps {
  recommendation: RecommendationSummary;
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const {
    ticker,
    recommendation: rec,
    confidence,
    technical_signal,
    sentiment_signal,
    risk_level,
  } = recommendation;

  return (
    <Link
      href={`/stocks/${ticker}`}
      className="block bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6"
    >
      {/* Ticker */}
      <div className="mb-4">
        <h3 className="text-2xl font-bold font-mono text-gray-900">{ticker}</h3>
      </div>

      {/* Recommendation Badge */}
      <div className="mb-4">
        <div
          className={cn(
            'inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold',
            getRecommendationColor(rec)
          )}
        >
          {rec.replace('_', ' ')}
        </div>
        <div className="text-sm text-gray-600 mt-2">
          Confidence: <span className="font-semibold">{formatConfidence(confidence)}</span>
        </div>
      </div>

      {/* Signals */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Technical:</span>
          <span className={cn('font-semibold', getSignalColor(technical_signal))}>
            {technical_signal}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Sentiment:</span>
          <span className={cn('font-semibold', getSignalColor(sentiment_signal))}>
            {sentiment_signal}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Risk:</span>
          <span className="font-semibold text-gray-700">{risk_level.replace('_', ' ')}</span>
        </div>
      </div>

      {/* View Details */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <span className="text-blue-600 text-sm font-medium hover:underline">View Details →</span>
      </div>
    </Link>
  );
}
