"""
Unit tests for sentiment scoring.
"""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

import sys
from pathlib import Path
# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.processing.sentiment_scoring import SentimentScorer


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch('src.processing.sentiment_scoring.OpenAI') as mock_openai:
        # Create mock client instance
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Create mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "sentiment_score": 0.8,
            "confidence": 0.9,
            "themes": ["earnings", "growth"]
        })

        mock_client.chat.completions.create.return_value = mock_response

        yield mock_client


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    return pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": datetime(2024, 12, 16, 10, 0),
            "headline": "Apple reports record quarterly earnings",
            "content": "Apple Inc. exceeded analyst expectations with strong iPhone sales.",
            "source": "Reuters",
            "url": "https://example.com/article1",
            "author": "John Doe"
        },
        {
            "ticker": "TSLA",
            "published_at": datetime(2024, 12, 16, 11, 0),
            "headline": "Tesla faces production delays",
            "content": "Tesla announced delays in Cybertruck production.",
            "source": "Bloomberg",
            "url": "https://example.com/article2",
            "author": "Jane Smith"
        },
        {
            "ticker": "MSFT",
            "published_at": datetime(2024, 12, 16, 12, 0),
            "headline": "Microsoft announces AI partnership",
            "content": "",  # Empty content
            "source": "TechCrunch",
            "url": "https://example.com/article3",
            "author": ""
        }
    ])


class TestSentimentScorer:
    """Test suite for SentimentScorer."""

    def test_initialization(self, mock_openai_client):
        """Test scorer initialization."""
        scorer = SentimentScorer()

        assert scorer is not None
        assert scorer.model == "gpt-4o-mini"
        assert scorer.version == "1.0.0"
        assert scorer.client is not None

    def test_analyze_sentiment_batch_empty_df(self, mock_openai_client):
        """Test handling of empty DataFrame."""
        scorer = SentimentScorer()
        empty_df = pd.DataFrame()

        result = scorer.analyze_sentiment_batch(empty_df)

        assert result.empty

    def test_analyze_sentiment_batch_success(self, mock_openai_client, sample_articles):
        """Test successful sentiment analysis."""
        scorer = SentimentScorer()

        result = scorer.analyze_sentiment_batch(sample_articles)

        # Check DataFrame structure
        assert len(result) == 3
        assert "sentiment_score" in result.columns
        assert "confidence" in result.columns
        assert "themes" in result.columns
        assert "model_name" in result.columns
        assert "model_version" in result.columns

        # Check all original columns are preserved
        assert "ticker" in result.columns
        assert "headline" in result.columns
        assert "published_at" in result.columns

        # Check values are in valid ranges
        assert all(result["sentiment_score"].between(-1.0, 1.0))
        assert all(result["confidence"].between(0.0, 1.0))
        assert all(result["model_name"] == "gpt-4o-mini")
        assert all(result["model_version"] == "1.0.0")

    def test_analyze_sentiment_batch_with_api_error(self, mock_openai_client, sample_articles):
        """Test handling of API errors."""
        scorer = SentimentScorer()

        # Make the API call raise an exception
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")

        result = scorer.analyze_sentiment_batch(sample_articles)

        # Should still return results with default values
        assert len(result) == 3
        assert all(result["sentiment_score"] == 0.0)
        assert all(result["confidence"] == 0.0)
        assert all(result["themes"].apply(lambda x: len(x) == 0))

    def test_analyze_single_article_positive_sentiment(self, mock_openai_client):
        """Test analyzing a positive article."""
        scorer = SentimentScorer()

        result = scorer._analyze_single_article(
            ticker="AAPL",
            headline="Apple reports record earnings",
            content="Strong sales growth across all product lines."
        )

        assert "sentiment_score" in result
        assert "confidence" in result
        assert "themes" in result
        assert result["sentiment_score"] == 0.8
        assert result["confidence"] == 0.9
        assert result["themes"] == ["earnings", "growth"]

    def test_analyze_single_article_negative_sentiment(self, mock_openai_client):
        """Test analyzing a negative article."""
        scorer = SentimentScorer()

        # Update mock to return negative sentiment
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": -0.7,
            "confidence": 0.85,
            "themes": ["lawsuit", "regulatory"]
        })

        result = scorer._analyze_single_article(
            ticker="TSLA",
            headline="Tesla faces lawsuit",
            content="Company sued over safety concerns."
        )

        assert result["sentiment_score"] == -0.7
        assert result["confidence"] == 0.85
        assert "lawsuit" in result["themes"]

    def test_analyze_single_article_neutral_sentiment(self, mock_openai_client):
        """Test analyzing a neutral article."""
        scorer = SentimentScorer()

        # Update mock to return neutral sentiment
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": 0.0,
            "confidence": 0.6,
            "themes": ["announcement"]
        })

        result = scorer._analyze_single_article(
            ticker="MSFT",
            headline="Microsoft announces new product",
            content="Company reveals new product line."
        )

        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.6

    def test_sentiment_score_clamping(self, mock_openai_client):
        """Test that sentiment scores are clamped to [-1, 1]."""
        scorer = SentimentScorer()

        # Test score > 1.0
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": 1.5,
            "confidence": 0.9,
            "themes": ["positive"]
        })

        result = scorer._analyze_single_article("AAPL", "Test headline", "Test content")
        assert result["sentiment_score"] == 1.0

        # Test score < -1.0
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": -1.5,
            "confidence": 0.9,
            "themes": ["negative"]
        })

        result = scorer._analyze_single_article("AAPL", "Test headline", "Test content")
        assert result["sentiment_score"] == -1.0

    def test_confidence_clamping(self, mock_openai_client):
        """Test that confidence scores are clamped to [0, 1]."""
        scorer = SentimentScorer()

        # Test confidence > 1.0
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": 0.5,
            "confidence": 1.5,
            "themes": []
        })

        result = scorer._analyze_single_article("AAPL", "Test", "Test")
        assert result["confidence"] == 1.0

        # Test confidence < 0.0
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": 0.5,
            "confidence": -0.5,
            "themes": []
        })

        result = scorer._analyze_single_article("AAPL", "Test", "Test")
        assert result["confidence"] == 0.0

    def test_invalid_themes_handling(self, mock_openai_client):
        """Test handling of invalid themes format."""
        scorer = SentimentScorer()

        # Test themes as string instead of list
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "sentiment_score": 0.5,
            "confidence": 0.8,
            "themes": "invalid_format"
        })

        result = scorer._analyze_single_article("AAPL", "Test", "Test")
        assert result["themes"] == []

    def test_create_prompt_with_content(self, mock_openai_client):
        """Test prompt creation with content."""
        scorer = SentimentScorer()

        prompt = scorer._create_prompt(
            ticker="AAPL",
            headline="Apple announces new iPhone",
            content="The company revealed the iPhone 15 with improved features and performance."
        )

        assert "AAPL" in prompt
        assert "Apple announces new iPhone" in prompt
        assert "The company revealed" in prompt
        assert "sentiment_score" in prompt
        assert "confidence" in prompt
        assert "themes" in prompt

    def test_create_prompt_without_content(self, mock_openai_client):
        """Test prompt creation without content."""
        scorer = SentimentScorer()

        prompt = scorer._create_prompt(
            ticker="TSLA",
            headline="Tesla stock rises",
            content=""
        )

        assert "TSLA" in prompt
        assert "Tesla stock rises" in prompt
        assert "Headline:" in prompt
        # Should not include content section for empty content
        assert "Content:" not in prompt

    def test_create_prompt_truncates_long_content(self, mock_openai_client):
        """Test that very long content is truncated."""
        scorer = SentimentScorer()

        long_content = "A" * 2000  # 2000 characters
        prompt = scorer._create_prompt(
            ticker="AAPL",
            headline="Test",
            content=long_content
        )

        # Content should be truncated to 1000 chars
        assert long_content[:1000] in prompt
        # Check that the full content is not in the prompt
        assert len(prompt) < len(long_content) + 500  # Should be much shorter than full content

    def test_analyze_sentiment_preserves_article_metadata(self, mock_openai_client, sample_articles):
        """Test that article metadata is preserved in results."""
        scorer = SentimentScorer()

        result = scorer.analyze_sentiment_batch(sample_articles)

        # Check all metadata columns are preserved
        for col in ["ticker", "published_at", "headline", "content", "source", "url", "author"]:
            assert col in result.columns

        # Verify specific values are preserved
        assert result.loc[0, "ticker"] == "AAPL"
        assert result.loc[0, "source"] == "Reuters"
        assert result.loc[1, "ticker"] == "TSLA"
        assert result.loc[1, "author"] == "Jane Smith"

    def test_missing_api_key_handling(self):
        """Test handling when OpenAI API key is missing."""
        with patch('src.processing.sentiment_scoring.config') as mock_config:
            mock_config.OPENAI_API_KEY = None
            mock_config.SENTIMENT_MODEL = "gpt-4o-mini"
            mock_config.SENTIMENT_VERSION = "1.0.0"

            # Should not raise an error during initialization
            # (OpenAI client will handle missing key on first API call)
            with patch('src.processing.sentiment_scoring.OpenAI'):
                scorer = SentimentScorer()
                assert scorer is not None

    def test_json_parsing_error_handling(self, mock_openai_client):
        """Test handling of invalid JSON response from API."""
        scorer = SentimentScorer()

        # Return invalid JSON
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "invalid json"

        result = scorer._analyze_single_article("AAPL", "Test", "Test")

        # Should return default values on parse error
        assert result["sentiment_score"] == 0.0
        assert result["confidence"] == 0.0
        assert result["themes"] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
