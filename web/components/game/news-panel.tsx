'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { NewsArticle } from '@/types/game';
import { Newspaper, ExternalLink } from 'lucide-react';

export function NewsPanel() {
  const { player, gameData } = useGameStore();

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  const newsArticles = currentDayData?.news || [];

  if (!currentDayData) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center gap-2 mb-4">
        <Newspaper className="w-5 h-5 text-blue-600" />
        <h2 className="text-xl font-bold text-gray-900">Today's Market News</h2>
      </div>

      {newsArticles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Newspaper className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>No news articles for today</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[600px] overflow-y-auto">
          {newsArticles.map((article, index) => (
            <NewsCard key={index} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}

interface NewsCardProps {
  article: NewsArticle;
}

function NewsCard({ article }: NewsCardProps) {
  const getSentimentColor = (score: number | null | undefined) => {
    if (!score) return 'bg-gray-100 text-gray-700';
    if (score > 0.3) return 'bg-green-100 text-green-700';
    if (score < -0.3) return 'bg-red-100 text-red-700';
    return 'bg-yellow-100 text-yellow-700';
  };

  const getSentimentLabel = (score: number | null | undefined) => {
    if (!score) return 'Neutral';
    if (score > 0.5) return 'Very Positive';
    if (score > 0.3) return 'Positive';
    if (score < -0.5) return 'Very Negative';
    if (score < -0.3) return 'Negative';
    return 'Neutral';
  };

  const publishedDate = new Date(article.published_at);
  const dateString = publishedDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const timeString = publishedDate.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
              {article.ticker}
            </span>
            {article.sentiment_score !== null && article.sentiment_score !== undefined && (
              <span
                className={`px-2 py-0.5 text-xs font-semibold rounded ${getSentimentColor(article.sentiment_score)}`}
              >
                {getSentimentLabel(article.sentiment_score)}
              </span>
            )}
          </div>
          {article.url ? (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold text-gray-900 text-sm leading-snug hover:text-blue-600 transition-colors inline-flex items-center gap-1 group"
            >
              {article.headline}
              <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
          ) : (
            <h3 className="font-bold text-gray-900 text-sm leading-snug">{article.headline}</h3>
          )}
        </div>
      </div>

      {/* Content */}
      {article.content && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-3">{article.content}</p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="font-medium">{article.source}</span>
        <div className="flex items-center gap-1">
          <span>{dateString}</span>
          <span>•</span>
          <span>{timeString}</span>
        </div>
      </div>
    </div>
  );
}
