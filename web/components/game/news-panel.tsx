'use client';

import { useMemo } from 'react';
import { useGameStore } from '@/lib/stores/gameStore';
import { NewsArticle } from '@/types/game';
import { Newspaper, ExternalLink } from 'lucide-react';

interface NewsPanelProps {
  selectedTicker?: string;
}

export function NewsPanel({ selectedTicker }: NewsPanelProps) {
  const { player, gameData } = useGameStore();

  const currentDayData = useMemo(() => {
    if (!gameData || player.currentDay >= gameData.total_days) {
      return null;
    }
    return gameData.days[player.currentDay];
  }, [gameData, player.currentDay]);

  /**
   * FIXED LOGIC:
   * - Always try current trading day first
   * - Walk backward in time if fewer than 10 articles
   * - Only include articles matching selected ticker
   * - Support multi-ticker articles (e.g. "AAPL,MSFT")
   * - Deterministic newest → oldest ordering
   */
  const newsArticles = useMemo(() => {
    if (!gameData || !currentDayData || !selectedTicker) {
      return [];
    }

    const targetTicker = selectedTicker.toUpperCase();
    const collected: NewsArticle[] = [];

    // Walk backward from the latest day
    for (let i = gameData.days.length - 1; i >= 0; i--) {
      const day = gameData.days[i];

      // Skip future simulated days
      if (day.date > currentDayData.date) continue;

      const dayArticles = (day.news || []).filter((article) => {
        if (!article.ticker) return false;

        // Support multi-ticker articles: "AAPL,MSFT"
        const tickers = article.ticker
          .toUpperCase()
          .split(',')
          .map(t => t.trim());

        return tickers.includes(targetTicker);
      });

      collected.push(...dayArticles);

      // Stop early once we have enough
      if (collected.length >= 10) break;
    }

    // Sort globally by published time (newest first)
    collected.sort(
      (a, b) =>
        new Date(b.published_at).getTime() -
        new Date(a.published_at).getTime()
    );

    // Hard cap to 10
    return collected.slice(0, 10);
  }, [gameData, currentDayData, selectedTicker]);

  if (!currentDayData) {
    return null;
  }

  return (
    <div className="bg-layer1 rounded-lg shadow-soft p-6 border border-borderDark-subtle">
      <div className="flex items-center gap-2 mb-4">
        <Newspaper className="w-5 h-5 text-accent" />
        <h2 className="text-xl font-bold text-text-primary">
          Recent Market News
        </h2>
      </div>

      {newsArticles.length === 0 ? (
        <div className="text-center py-8 text-text-muted">
          <Newspaper className="w-12 h-12 mx-auto mb-2 opacity-30" />
          <p>No news articles available</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-[600px] overflow-y-auto">
          <div className="text-xs text-text-muted">
            Showing latest {newsArticles.length} articles for {selectedTicker}.
          </div>
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
    if (score === null || score === undefined)
      return 'bg-layer3 text-text-muted';
    if (score > 0.3) return 'bg-success/20 text-success';
    if (score < -0.3) return 'bg-error/20 text-error';
    return 'bg-warning/20 text-warning';
  };

  const getSentimentLabel = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'Neutral';
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
    <div className="bg-layer2 border border-borderDark-subtle rounded-lg p-4 hover:bg-layer3 transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 bg-accent/20 text-accent text-xs font-semibold rounded">
              {article.ticker}
            </span>
            <span
              className={`px-2 py-0.5 text-xs font-semibold rounded ${getSentimentColor(
                article.sentiment_score
              )}`}
            >
              {getSentimentLabel(article.sentiment_score)}
            </span>
          </div>

          {article.url ? (
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="font-bold text-text-primary text-sm leading-snug hover:text-accent transition-colors inline-flex items-center gap-1 group"
            >
              {article.headline}
              <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
          ) : (
            <h3 className="font-bold text-text-primary text-sm leading-snug">
              {article.headline}
            </h3>
          )}
        </div>
      </div>

      {/* Content */}
      {article.content && (
        <p className="text-sm text-text-secondary mb-3 line-clamp-3">
          {article.content}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-text-muted">
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
