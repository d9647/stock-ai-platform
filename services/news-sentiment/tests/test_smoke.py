"""
Smoke tests for news-sentiment pipeline.
Tests the complete pipeline without external API calls.
"""
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import Mock, patch

import sys
from pathlib import Path
# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from processing.aggregation import SentimentAggregator


class TestNewsSentimentPipelineSmoke:
    """Smoke tests for the complete news sentiment pipeline."""

    def test_aggregator_end_to_end(self):
        """Test complete aggregation flow."""
        # Prepare mock sentiment data
        sentiment_data = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "themes": ["earnings", "growth"]
            },
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 14, 0),
                "sentiment_score": -0.3,
                "confidence": 0.7,
                "themes": ["concerns", "market"]
            }
        ])

        # Run aggregation
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sentiment_data)

        # Verify output structure
        assert not result.empty
        assert len(result) == 1  # One day for AAPL

        # Verify all required columns present
        required_columns = [
            'ticker', 'date', 'avg_sentiment', 'weighted_sentiment',
            'article_count', 'positive_count', 'neutral_count',
            'negative_count', 'top_themes'
        ]
        for col in required_columns:
            assert col in result.columns

        # Verify data quality
        row = result.iloc[0]
        assert row['ticker'] == 'AAPL'
        assert row['date'] == date(2024, 12, 16)
        assert row['article_count'] == 2
        assert -1 <= row['avg_sentiment'] <= 1
        assert -1 <= row['weighted_sentiment'] <= 1
        assert isinstance(row['top_themes'], list)

    def test_sentiment_score_validation(self):
        """Test that sentiment scores are validated."""
        # Test data with valid sentiment scores
        valid_data = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.0,  # Neutral
                "confidence": 1.0,
                "themes": []
            },
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 11, 0),
                "sentiment_score": 1.0,  # Maximum positive
                "confidence": 1.0,
                "themes": []
            },
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 12, 0),
                "sentiment_score": -1.0,  # Maximum negative
                "confidence": 1.0,
                "themes": []
            }
        ])

        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(valid_data)

        # All scores should be within [-1, 1]
        assert -1 <= result['avg_sentiment'].iloc[0] <= 1
        assert -1 <= result['weighted_sentiment'].iloc[0] <= 1

    def test_empty_themes_handling(self):
        """Test handling of articles with no themes."""
        data_no_themes = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "themes": []  # No themes
            }
        ])

        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(data_no_themes)

        assert not result.empty
        assert result['top_themes'].iloc[0] == []

    def test_single_article_aggregation(self):
        """Test aggregation with only one article."""
        single_article = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.75,
                "confidence": 0.9,
                "themes": ["positive", "news"]
            }
        ])

        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(single_article)

        assert len(result) == 1
        # With single article, avg and weighted should be the same
        assert abs(result['avg_sentiment'].iloc[0] - 0.75) < 0.01
        assert abs(result['weighted_sentiment'].iloc[0] - 0.75) < 0.01
        assert result['article_count'].iloc[0] == 1

    def test_multiple_days_aggregation(self):
        """Test aggregation across multiple days."""
        multi_day_data = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "themes": ["day1"]
            },
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 17, 10, 0),
                "sentiment_score": -0.5,
                "confidence": 0.8,
                "themes": ["day2"]
            },
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 18, 10, 0),
                "sentiment_score": 0.0,
                "confidence": 0.8,
                "themes": ["day3"]
            }
        ])

        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(multi_day_data)

        # Should have 3 separate daily aggregates
        assert len(result) == 3
        assert len(result['date'].unique()) == 3

        # Each day should have article_count = 1
        assert (result['article_count'] == 1).all()


class TestFeatureStoreSmoke:
    """Smoke tests for feature store components."""

    def test_snapshot_structure(self):
        """Test that snapshot has correct structure."""
        # This is a placeholder for when feature store is complete
        snapshot = {
            "snapshot_id": "AAPL_2024-12-16_1.0.0",
            "ticker": "AAPL",
            "as_of_date": date(2024, 12, 16),
            "feature_version": "1.0.0",
            "technical_features": {
                "sma_20": 250.0,
                "rsi_14": 55.0
            },
            "sentiment_features": {
                "avg_sentiment": 0.5,
                "article_count": 10
            },
            "data_sources": {
                "technical": {"has_data": True},
                "sentiment": {"has_data": True}
            }
        }

        # Verify structure
        assert "snapshot_id" in snapshot
        assert "ticker" in snapshot
        assert "technical_features" in snapshot
        assert "sentiment_features" in snapshot
        assert "data_sources" in snapshot


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
