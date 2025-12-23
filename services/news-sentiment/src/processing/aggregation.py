"""
Daily sentiment aggregation.
Aggregates sentiment scores by ticker and date for feature store consumption.
"""
from collections import Counter
from typing import List

import pandas as pd
import numpy as np
from loguru import logger


class SentimentAggregator:
    """
    Aggregates sentiment scores by ticker and date.
    Creates daily snapshots for the feature store.
    """

    def __init__(self):
        """Initialize aggregator."""
        logger.info("Initialized sentiment aggregator")

    def aggregate_daily_sentiment(self, sentiment_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate sentiment scores by ticker and date.

        Args:
            sentiment_df: DataFrame with sentiment analysis results
                          Must have columns: [ticker, published_at, sentiment_score, confidence, themes]

        Returns:
            DataFrame with daily aggregates:
            [ticker, date, avg_sentiment, weighted_sentiment, article_count,
             positive_count, neutral_count, negative_count, top_themes]
        """
        if sentiment_df.empty:
            logger.warning("No sentiment data to aggregate")
            return pd.DataFrame()

        logger.info(f"Aggregating sentiment for {len(sentiment_df)} articles")

        # Extract date from published_at
        sentiment_df["date"] = pd.to_datetime(sentiment_df["published_at"]).dt.date

        # Group by ticker and date
        aggregates = []

        for (ticker, date), group in sentiment_df.groupby(["ticker", "date"]):
            aggregate = self._aggregate_group(ticker, date, group)
            aggregates.append(aggregate)

        result_df = pd.DataFrame(aggregates)

        # Sort by ticker and date (deterministic)
        result_df = result_df.sort_values(["ticker", "date"]).reset_index(drop=True)

        logger.info(f"Created {len(result_df)} daily aggregates")

        return result_df

    def _aggregate_group(
        self,
        ticker: str,
        date,
        group: pd.DataFrame
    ) -> dict:
        """
        Aggregate a single group (ticker, date).

        Args:
            ticker: Stock ticker symbol
            date: Date
            group: DataFrame with articles for this ticker and date

        Returns:
            Dict with aggregated metrics
        """
        article_count = len(group)

        # Average sentiment (simple average)
        avg_sentiment = group["sentiment_score"].mean()

        # Weighted sentiment (weighted by confidence)
        if group["confidence"].sum() > 0:
            weighted_sentiment = (
                (group["sentiment_score"] * group["confidence"]).sum()
                / group["confidence"].sum()
            )
        else:
            weighted_sentiment = avg_sentiment

        # Sentiment distribution
        positive_count = int((group["sentiment_score"] > 0.1).sum())
        neutral_count = int((group["sentiment_score"].abs() <= 0.1).sum())
        negative_count = int((group["sentiment_score"] < -0.1).sum())

        # Top themes (most common)
        top_themes = self._extract_top_themes(group["themes"])

        return {
            "ticker": ticker,
            "date": date,
            "avg_sentiment": float(avg_sentiment),
            "weighted_sentiment": float(weighted_sentiment),
            "article_count": article_count,
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "top_themes": top_themes
        }

    def _extract_top_themes(self, themes_series: pd.Series, top_n: int = 5) -> List[str]:
        """
        Extract top N most common themes from a series of theme lists.

        Args:
            themes_series: Series where each element is a list of themes
            top_n: Number of top themes to return

        Returns:
            List of top N themes
        """
        # Flatten all themes
        all_themes = []
        for themes in themes_series:
            if isinstance(themes, list):
                all_themes.extend(themes)

        if not all_themes:
            return []

        # Count occurrences
        theme_counts = Counter(all_themes)

        # Get top N
        top_themes = [theme for theme, count in theme_counts.most_common(top_n)]

        return top_themes


if __name__ == "__main__":
    # Test aggregator
    aggregator = SentimentAggregator()

    # Create sample sentiment data
    sample_sentiment = pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": pd.Timestamp("2024-12-16 10:00:00"),
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "themes": ["earnings", "growth"]
        },
        {
            "ticker": "AAPL",
            "published_at": pd.Timestamp("2024-12-16 14:00:00"),
            "sentiment_score": 0.6,
            "confidence": 0.8,
            "themes": ["product_launch", "innovation"]
        },
        {
            "ticker": "AAPL",
            "published_at": pd.Timestamp("2024-12-17 09:00:00"),
            "sentiment_score": -0.3,
            "confidence": 0.7,
            "themes": ["supply_chain", "delays"]
        },
        {
            "ticker": "TSLA",
            "published_at": pd.Timestamp("2024-12-16 11:00:00"),
            "sentiment_score": -0.5,
            "confidence": 0.8,
            "themes": ["production", "delays"]
        }
    ])

    # Aggregate
    aggregates = aggregator.aggregate_daily_sentiment(sample_sentiment)

    print("\\nDaily Sentiment Aggregates:")
    print(aggregates)
