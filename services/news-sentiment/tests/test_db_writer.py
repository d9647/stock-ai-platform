"""
Unit tests for news database writer.
"""
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

import sys
from pathlib import Path
# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.storage.db_writer import NewsDataWriter


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    with patch('src.storage.db_writer.create_engine'):
        with patch('src.storage.db_writer.sessionmaker') as mock_sessionmaker:
            mock_session = MagicMock()
            mock_sessionmaker.return_value.return_value = mock_session

            # Mock execute result
            mock_result = MagicMock()
            mock_result.rowcount = 5  # Default: 5 rows inserted
            mock_session.execute.return_value = mock_result

            yield mock_session


@pytest.fixture
def sample_articles():
    """Create sample articles DataFrame."""
    return pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 10, 0),
            "headline": "Apple reports record earnings",
            "content": "Strong iPhone sales drive growth",
            "source": "Reuters",
            "url": "https://example.com/article1",
            "author": "John Doe"
        },
        {
            "ticker": "TSLA",
            "published_at": datetime(2024, 12, 16, 11, 0),
            "headline": "Tesla production update",
            "content": "New factory coming online",
            "source": "Bloomberg",
            "url": "https://example.com/article2",
            "author": "Jane Smith"
        },
        {
            "ticker": "MSFT",
            "published_at": datetime(2024, 12, 16, 12, 0),
            "headline": "Microsoft AI announcement",
            "content": None,  # Test null content
            "source": "TechCrunch",
            "url": None,  # Test null URL
            "author": None  # Test null author
        }
    ])


@pytest.fixture
def sample_sentiment_scores():
    """Create sample sentiment scores DataFrame."""
    article_id1 = str(uuid4())
    article_id2 = str(uuid4())

    return pd.DataFrame([
        {
            "article_id": article_id1,
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 10, 0),
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "themes": ["earnings", "growth"],
            "model_name": "gpt-4o-mini",
            "model_version": "1.0.0"
        },
        {
            "article_id": article_id2,
            "ticker": "TSLA",
            "published_at": datetime(2024, 12, 16, 11, 0),
            "sentiment_score": -0.3,
            "confidence": 0.7,
            "themes": ["production", "delays"],
            "model_name": "gpt-4o-mini",
            "model_version": "1.0.0"
        }
    ])


@pytest.fixture
def sample_daily_aggregates():
    """Create sample daily aggregates DataFrame."""
    return pd.DataFrame([
        {
            "ticker": "AAPL",
            "date": date(2024, 12, 16),
            "avg_sentiment": 0.45,
            "weighted_sentiment": 0.52,
            "article_count": 10,
            "positive_count": 7,
            "neutral_count": 2,
            "negative_count": 1,
            "top_themes": ["earnings", "innovation", "growth"]
        },
        {
            "ticker": "TSLA",
            "date": date(2024, 12, 16),
            "avg_sentiment": -0.15,
            "weighted_sentiment": -0.10,
            "article_count": 8,
            "positive_count": 3,
            "neutral_count": 2,
            "negative_count": 3,
            "top_themes": ["production", "regulatory", "competition"]
        }
    ])


class TestNewsDataWriter:
    """Test suite for NewsDataWriter."""

    def test_initialization(self, mock_db_session):
        """Test writer initialization."""
        writer = NewsDataWriter()

        assert writer is not None
        assert writer.session is not None

    def test_write_articles_batch_empty_df(self, mock_db_session):
        """Test handling of empty DataFrame."""
        writer = NewsDataWriter()
        empty_df = pd.DataFrame()

        result = writer.write_articles_batch(empty_df)

        assert result == 0

    def test_write_articles_batch_success(self, mock_db_session, sample_articles):
        """Test successful article writing."""
        writer = NewsDataWriter()

        # Mock rowcount to return the number of articles
        mock_db_session.execute.return_value.rowcount = len(sample_articles)

        result = writer.write_articles_batch(sample_articles)

        # Should call execute once
        assert mock_db_session.execute.called
        # Should commit
        assert mock_db_session.commit.called
        # Should return number of inserted rows
        assert result == 3

    def test_write_articles_batch_handles_null_values(self, mock_db_session):
        """Test handling of null/None values in articles."""
        writer = NewsDataWriter()

        df_with_nulls = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "headline": "Test headline",
                "content": None,  # Null content
                "source": "Test Source",
                "url": None,  # Null URL
                "author": None  # Null author
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_articles_batch(df_with_nulls)

        assert result == 1
        assert mock_db_session.commit.called

    def test_write_articles_batch_timezone_handling(self, mock_db_session):
        """Test timezone-aware datetime handling."""
        writer = NewsDataWriter()

        # Create DataFrame with timezone-naive datetime
        df_naive = pd.DataFrame([
            {
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),  # No timezone
                "headline": "Test",
                "content": "Test",
                "source": "Test",
                "url": "https://test.com",
                "author": "Test"
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_articles_batch(df_naive)

        assert result == 1

    def test_write_articles_batch_database_error(self, mock_db_session, sample_articles):
        """Test handling of database errors."""
        writer = NewsDataWriter()

        # Make execute raise an exception
        mock_db_session.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            writer.write_articles_batch(sample_articles)

        assert "Database error" in str(exc_info.value)
        # Should rollback on error
        assert mock_db_session.rollback.called

    def test_write_sentiment_scores_batch_empty_df(self, mock_db_session):
        """Test handling of empty sentiment scores DataFrame."""
        writer = NewsDataWriter()
        empty_df = pd.DataFrame()

        result = writer.write_sentiment_scores_batch(empty_df)

        assert result == 0

    def test_write_sentiment_scores_batch_success(self, mock_db_session, sample_sentiment_scores):
        """Test successful sentiment scores writing."""
        writer = NewsDataWriter()

        mock_db_session.execute.return_value.rowcount = len(sample_sentiment_scores)
        result = writer.write_sentiment_scores_batch(sample_sentiment_scores)

        assert result == 2
        assert mock_db_session.execute.called
        assert mock_db_session.commit.called

    def test_write_sentiment_scores_batch_invalid_themes(self, mock_db_session):
        """Test handling of invalid themes format."""
        writer = NewsDataWriter()

        df_invalid_themes = pd.DataFrame([
            {
                "article_id": str(uuid4()),
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": 0.5,
                "confidence": 0.8,
                "themes": "not_a_list",  # Invalid format
                "model_name": "gpt-4o-mini",
                "model_version": "1.0.0"
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_sentiment_scores_batch(df_invalid_themes)

        # Should convert invalid themes to empty list and succeed
        assert result == 1

    def test_write_daily_aggregates_batch_empty_df(self, mock_db_session):
        """Test handling of empty daily aggregates DataFrame."""
        writer = NewsDataWriter()
        empty_df = pd.DataFrame()

        result = writer.write_daily_aggregates_batch(empty_df)

        assert result == 0

    def test_write_daily_aggregates_batch_success(self, mock_db_session, sample_daily_aggregates):
        """Test successful daily aggregates writing."""
        writer = NewsDataWriter()

        mock_db_session.execute.return_value.rowcount = len(sample_daily_aggregates)
        result = writer.write_daily_aggregates_batch(sample_daily_aggregates)

        assert result == 2
        assert mock_db_session.execute.called
        assert mock_db_session.commit.called

    def test_write_daily_aggregates_batch_invalid_top_themes(self, mock_db_session):
        """Test handling of invalid top_themes format."""
        writer = NewsDataWriter()

        df_invalid_themes = pd.DataFrame([
            {
                "ticker": "AAPL",
                "date": date(2024, 12, 16),
                "avg_sentiment": 0.5,
                "weighted_sentiment": 0.6,
                "article_count": 10,
                "positive_count": 7,
                "neutral_count": 2,
                "negative_count": 1,
                "top_themes": "not_a_list"  # Invalid format
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_daily_aggregates_batch(df_invalid_themes)

        # Should convert invalid themes to empty list and succeed
        assert result == 1

    def test_get_article_ids_for_ticker(self, mock_db_session):
        """Test retrieving article IDs for a ticker."""
        writer = NewsDataWriter()

        # Mock query result
        mock_article_1 = MagicMock()
        mock_article_1.ticker = "AAPL"
        mock_article_1.published_at = datetime(2024, 12, 16, 10, 0)
        mock_article_1.headline = "Test headline 1"
        mock_article_1.id = uuid4()

        mock_article_2 = MagicMock()
        mock_article_2.ticker = "AAPL"
        mock_article_2.published_at = datetime(2024, 12, 16, 11, 0)
        mock_article_2.headline = "Test headline 2"
        mock_article_2.id = uuid4()

        mock_query = mock_db_session.query.return_value
        mock_query.filter.return_value.all.return_value = [mock_article_1, mock_article_2]

        result = writer.get_article_ids_for_ticker("AAPL")

        assert len(result) == 2
        assert ("AAPL", mock_article_1.published_at, "Test headline 1") in result
        assert ("AAPL", mock_article_2.published_at, "Test headline 2") in result

    def test_get_article_ids_for_ticker_database_error(self, mock_db_session):
        """Test handling of database errors when retrieving article IDs."""
        writer = NewsDataWriter()

        # Make query raise an exception
        mock_db_session.query.side_effect = Exception("Query error")

        with pytest.raises(Exception) as exc_info:
            writer.get_article_ids_for_ticker("AAPL")

        assert "Query error" in str(exc_info.value)

    def test_close(self, mock_db_session):
        """Test closing database session."""
        writer = NewsDataWriter()
        writer.close()

        assert mock_db_session.close.called

    def test_idempotency_duplicate_insert(self, mock_db_session, sample_articles):
        """Test that duplicate inserts are handled gracefully."""
        writer = NewsDataWriter()

        # First insert: 3 rows inserted
        mock_db_session.execute.return_value.rowcount = 3
        result1 = writer.write_articles_batch(sample_articles)
        assert result1 == 3

        # Second insert: 0 rows inserted (all duplicates)
        mock_db_session.execute.return_value.rowcount = 0
        result2 = writer.write_articles_batch(sample_articles)
        assert result2 == 0

    def test_type_conversions_in_sentiment_scores(self, mock_db_session):
        """Test proper type conversions for sentiment scores."""
        writer = NewsDataWriter()

        df_with_strings = pd.DataFrame([
            {
                "article_id": str(uuid4()),
                "ticker": "AAPL",
                "published_at": datetime(2024, 12, 16, 10, 0),
                "sentiment_score": "0.8",  # String instead of float
                "confidence": "0.9",  # String instead of float
                "themes": ["test"],
                "model_name": "gpt-4o-mini",
                "model_version": "1.0.0"
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_sentiment_scores_batch(df_with_strings)

        # Should convert strings to floats and succeed
        assert result == 1

    def test_type_conversions_in_daily_aggregates(self, mock_db_session):
        """Test proper type conversions for daily aggregates."""
        writer = NewsDataWriter()

        df_with_strings = pd.DataFrame([
            {
                "ticker": "AAPL",
                "date": date(2024, 12, 16),
                "avg_sentiment": "0.5",  # String
                "weighted_sentiment": "0.6",  # String
                "article_count": "10",  # String
                "positive_count": "7",  # String
                "neutral_count": "2",  # String
                "negative_count": "1",  # String
                "top_themes": ["test"]
            }
        ])

        mock_db_session.execute.return_value.rowcount = 1
        result = writer.write_daily_aggregates_batch(df_with_strings)

        # Should convert strings to appropriate types and succeed
        assert result == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
