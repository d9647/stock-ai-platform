"""
Unit tests for sentiment aggregation.
"""
import pytest
import pandas as pd
from datetime import datetime, date

import sys
from pathlib import Path
# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from processing.aggregation import SentimentAggregator


@pytest.fixture
def sample_sentiment_data():
    """Create sample sentiment data for testing."""
    return pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 10, 0),
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "themes": ["earnings", "growth"]
        },
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 14, 0),
            "sentiment_score": 0.6,
            "confidence": 0.8,
            "themes": ["product_launch", "innovation"]
        },
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 18, 0),
            "sentiment_score": -0.2,
            "confidence": 0.7,
            "themes": ["supply_chain", "delays"]
        },
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 17, 9, 0),
            "sentiment_score": -0.5,
            "confidence": 0.8,
            "themes": ["production", "delays"]
        },
        {
            "ticker": "TSLA",
            "published_at": datetime(2024, 12, 16, 11, 0),
            "sentiment_score": -0.3,
            "confidence": 0.85,
            "themes": ["production", "quality"]
        }
    ])


class TestSentimentAggregator:
    """Test suite for SentimentAggregator."""

    def test_initialization(self):
        """Test aggregator initialization."""
        aggregator = SentimentAggregator()
        assert aggregator is not None

    def test_aggregate_daily_sentiment(self, sample_sentiment_data):
        """Test daily sentiment aggregation."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        # Should have 2 aggregates (AAPL has 2 dates, TSLA has 1)
        assert len(result) == 3

        # Check columns exist
        assert 'ticker' in result.columns
        assert 'date' in result.columns
        assert 'avg_sentiment' in result.columns
        assert 'weighted_sentiment' in result.columns
        assert 'article_count' in result.columns
        assert 'positive_count' in result.columns
        assert 'neutral_count' in result.columns
        assert 'negative_count' in result.columns
        assert 'top_themes' in result.columns

    def test_average_sentiment_calculation(self, sample_sentiment_data):
        """Test average sentiment is calculated correctly."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        # Get AAPL Dec 16 aggregate
        aapl_dec16 = result[(result['ticker'] == 'AAPL') & (result['date'] == date(2024, 12, 16))]
        assert len(aapl_dec16) == 1

        # Average of [0.8, 0.6, -0.2] = 0.4
        expected_avg = (0.8 + 0.6 + (-0.2)) / 3
        assert abs(aapl_dec16['avg_sentiment'].iloc[0] - expected_avg) < 0.01

    def test_weighted_sentiment_calculation(self, sample_sentiment_data):
        """Test weighted sentiment is calculated correctly."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        aapl_dec16 = result[(result['ticker'] == 'AAPL') & (result['date'] == date(2024, 12, 16))]

        # Weighted: (0.8*0.9 + 0.6*0.8 + (-0.2)*0.7) / (0.9 + 0.8 + 0.7)
        expected_weighted = (0.8 * 0.9 + 0.6 * 0.8 + (-0.2) * 0.7) / (0.9 + 0.8 + 0.7)
        assert abs(aapl_dec16['weighted_sentiment'].iloc[0] - expected_weighted) < 0.01

    def test_sentiment_distribution(self, sample_sentiment_data):
        """Test sentiment distribution counts."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        aapl_dec16 = result[(result['ticker'] == 'AAPL') & (result['date'] == date(2024, 12, 16))]

        # Scores: 0.8, 0.6, -0.2
        # Positive (>0.1): 2, Neutral (abs<=0.1): 0, Negative (<-0.1): 1
        assert aapl_dec16['positive_count'].iloc[0] == 2
        assert aapl_dec16['neutral_count'].iloc[0] == 0
        assert aapl_dec16['negative_count'].iloc[0] == 1
        assert aapl_dec16['article_count'].iloc[0] == 3

    def test_top_themes_extraction(self, sample_sentiment_data):
        """Test top themes are extracted correctly."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        aapl_dec16 = result[(result['ticker'] == 'AAPL') & (result['date'] == date(2024, 12, 16))]

        top_themes = aapl_dec16['top_themes'].iloc[0]

        # All themes appear once, so order might vary
        # But should include themes from the 3 articles
        expected_themes = {"earnings", "growth", "product_launch", "innovation", "supply_chain", "delays"}
        assert set(top_themes).issubset(expected_themes)

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        aggregator = SentimentAggregator()
        empty_df = pd.DataFrame()
        result = aggregator.aggregate_daily_sentiment(empty_df)

        assert result.empty

    def test_multiple_tickers(self, sample_sentiment_data):
        """Test aggregation works for multiple tickers."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        # Should have rows for both AAPL and TSLA
        tickers = result['ticker'].unique()
        assert 'AAPL' in tickers
        assert 'TSLA' in tickers

    def test_deterministic_ordering(self, sample_sentiment_data):
        """Test that results are sorted deterministically."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate_daily_sentiment(sample_sentiment_data)

        # Should be sorted by ticker, then date
        assert result['ticker'].tolist() == sorted(result['ticker'].tolist())

        # Within each ticker, dates should be sorted
        for ticker in result['ticker'].unique():
            ticker_dates = result[result['ticker'] == ticker]['date'].tolist()
            assert ticker_dates == sorted(ticker_dates)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
