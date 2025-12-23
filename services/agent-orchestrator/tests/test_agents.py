"""
Unit tests for agent implementations.
"""
import pytest
import json
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

import sys
from pathlib import Path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.agents.technical_agent import TechnicalAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.risk_agent import RiskAgent
from src.agents.portfolio_synthesizer import PortfolioSynthesizer


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    with patch('src.agents.base_agent.ChatOpenAI') as mock_openai:
        mock_llm_instance = MagicMock()
        mock_openai.return_value = mock_llm_instance
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "signal": "BULLISH",
            "strength": 0.8,
            "reasoning": ["Strong momentum", "Positive trend"],
            "key_indicators": {
                "trend": "uptrend",
                "momentum": "strong",
                "volatility": "normal"
            }
        })
        mock_llm_instance.invoke.return_value = mock_response
        
        yield mock_llm_instance


@pytest.fixture
def sample_feature_snapshot():
    """Create sample feature snapshot for testing."""
    return {
        "snapshot_id": "AAPL_2024-12-16_snap_123abc",
        "ticker": "AAPL",
        "as_of_date": date(2024, 12, 16),
        "feature_version": "1.0.0",
        "technical_features": {
            "close": 195.50,
            "sma_20": 190.00,
            "sma_50": 185.00,
            "sma_200": 180.00,
            "rsi_14": 65.5,
            "macd": 1.5,
            "macd_signal": 1.2,
            "volatility_30d": 0.25,
            "atr_14": 3.5,
            "bollinger_upper": 200.00,
            "bollinger_middle": 195.00,
            "bollinger_lower": 190.00
        },
        "sentiment_features": {
            "avg_sentiment": 0.6,
            "weighted_sentiment": 0.65,
            "article_count": 25,
            "positive_count": 18,
            "neutral_count": 5,
            "negative_count": 2,
            "top_themes": ["earnings", "growth", "innovation"]
        }
    }


class TestTechnicalAgent:
    """Test suite for TechnicalAgent."""

    def test_initialization(self, mock_llm):
        """Test agent initialization."""
        agent = TechnicalAgent()
        
        assert agent is not None
        assert agent.agent_type == "technical"
        assert agent.model_version == "1.0.0"

    def test_analyze_success(self, mock_llm, sample_feature_snapshot):
        """Test successful technical analysis."""
        agent = TechnicalAgent()
        
        result = agent.analyze(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=sample_feature_snapshot
        )
        
        # Check output structure
        assert "output_id" in result
        assert result["agent_type"] == "technical"
        assert result["ticker"] == "AAPL"
        assert result["signal"] == "BULLISH"
        assert result["strength"] == 0.8
        assert len(result["reasoning"]) == 2
        assert "feature_snapshot_id" in result
        assert "prompt_hash" in result
        
        # Check LLM was called
        assert mock_llm.invoke.called

    def test_analyze_no_technical_data(self, mock_llm):
        """Test handling of missing technical data."""
        agent = TechnicalAgent()
        
        snapshot = {
            "snapshot_id": "AAPL_2024-12-16_snap_123",
            "ticker": "AAPL",
            "technical_features": {}
        }
        
        result = agent.analyze(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=snapshot
        )
        
        assert result["signal"] == "NEUTRAL"
        assert result["strength"] == 0.0
        assert "No technical data available" in result["reasoning"]

    def test_format_features(self, mock_llm, sample_feature_snapshot):
        """Test feature formatting for prompt."""
        agent = TechnicalAgent()
        
        formatted = agent._format_features(
            sample_feature_snapshot["technical_features"]
        )
        
        assert "SMA_20" in formatted
        assert "RSI(14)" in formatted
        assert "MACD" in formatted
        assert "30-day Volatility" in formatted


class TestSentimentAgent:
    """Test suite for SentimentAgent."""

    def test_initialization(self, mock_llm):
        """Test agent initialization."""
        agent = SentimentAgent()
        
        assert agent is not None
        assert agent.agent_type == "sentiment"

    def test_analyze_success(self, mock_llm, sample_feature_snapshot):
        """Test successful sentiment analysis."""
        agent = SentimentAgent()
        
        # Update mock for sentiment response
        mock_llm.invoke.return_value.content = json.dumps({
            "signal": "BULLISH",
            "strength": 0.7,
            "reasoning": ["Positive news coverage", "Strong themes"],
            "key_themes": {
                "primary_themes": ["earnings", "growth"],
                "sentiment_trend": "improving",
                "article_quality": "high"
            }
        })
        
        result = agent.analyze(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=sample_feature_snapshot
        )
        
        assert result["signal"] == "BULLISH"
        assert result["strength"] == 0.7
        assert "agent_metadata" in result

    def test_analyze_no_sentiment_data(self, mock_llm):
        """Test handling of missing sentiment data."""
        agent = SentimentAgent()
        
        snapshot = {
            "snapshot_id": "AAPL_2024-12-16_snap_123",
            "ticker": "AAPL",
            "sentiment_features": {"article_count": 0}
        }
        
        result = agent.analyze(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=snapshot
        )
        
        assert result["signal"] == "NEUTRAL"
        assert result["strength"] == 0.0


class TestRiskAgent:
    """Test suite for RiskAgent."""

    def test_initialization(self, mock_llm):
        """Test agent initialization."""
        agent = RiskAgent()
        
        assert agent is not None
        assert agent.agent_type == "risk"

    def test_analyze_success(self, mock_llm, sample_feature_snapshot):
        """Test successful risk analysis."""
        agent = RiskAgent()
        
        # Update mock for risk response
        mock_llm.invoke.return_value.content = json.dumps({
            "signal": "MEDIUM_RISK",
            "strength": 0.6,
            "reasoning": ["Moderate volatility", "Stable trend"],
            "risk_breakdown": {
                "volatility_level": "moderate",
                "trend_stability": "stable",
                "position_sizing": "moderate"
            }
        })
        
        result = agent.analyze(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=sample_feature_snapshot
        )
        
        assert result["signal"] == "MEDIUM_RISK"
        assert result["strength"] == 0.6
        assert "risk_breakdown" in result["agent_metadata"]


class TestPortfolioSynthesizer:
    """Test suite for PortfolioSynthesizer."""

    def test_initialization(self, mock_llm):
        """Test synthesizer initialization."""
        synthesizer = PortfolioSynthesizer()
        
        assert synthesizer is not None
        assert synthesizer.agent_type == "synthesizer"

    def test_synthesize_success(self, mock_llm, sample_feature_snapshot):
        """Test successful synthesis."""
        synthesizer = PortfolioSynthesizer()
        
        # Update mock for synthesis response
        mock_llm.invoke.return_value.content = json.dumps({
            "recommendation": "BUY",
            "confidence": 0.75,
            "rationale": {
                "summary": "Strong technical and sentiment signals",
                "technical_view": "Bullish trend",
                "sentiment_view": "Positive coverage",
                "risk_view": "Moderate risk acceptable",
                "key_factors": ["Uptrend", "Positive news", "Manageable risk"]
            },
            "position_size": "medium",
            "time_horizon": "medium_term"
        })
        
        technical_output = {
            "output_id": "tech_123",
            "signal": "BULLISH",
            "strength": 0.8,
            "reasoning": ["Strong trend"]
        }
        
        sentiment_output = {
            "output_id": "sent_123",
            "signal": "BULLISH",
            "strength": 0.7,
            "reasoning": ["Positive news"]
        }
        
        risk_output = {
            "output_id": "risk_123",
            "signal": "MEDIUM_RISK",
            "strength": 0.6,
            "reasoning": ["Moderate volatility"]
        }
        
        result = synthesizer.synthesize(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=sample_feature_snapshot,
            technical_output=technical_output,
            sentiment_output=sentiment_output,
            risk_output=risk_output
        )
        
        assert result["recommendation"] == "BUY"
        assert result["confidence"] == 0.75
        assert result["technical_signal"] == "BULLISH"
        assert result["sentiment_signal"] == "BULLISH"
        assert result["risk_assessment"] == "MEDIUM_RISK"
        assert result["position_size"] == "medium"

    def test_synthesize_incomplete_outputs(self, mock_llm, sample_feature_snapshot):
        """Test handling of incomplete agent outputs."""
        synthesizer = PortfolioSynthesizer()
        
        result = synthesizer.synthesize(
            ticker="AAPL",
            as_of_date=date(2024, 12, 16),
            feature_snapshot=sample_feature_snapshot,
            technical_output=None,
            sentiment_output=None,
            risk_output=None
        )
        
        assert result["recommendation"] == "HOLD"
        assert result["confidence"] == 0.0
        assert "Incomplete agent outputs" in result["rationale"]["summary"]


class TestBaseAgentFunctionality:
    """Test base agent functionality."""

    def test_prompt_hashing(self, mock_llm):
        """Test prompt hash generation."""
        agent = TechnicalAgent()
        
        prompt = "Test prompt"
        hash1 = agent._create_prompt_hash(prompt)
        hash2 = agent._create_prompt_hash(prompt)
        
        # Same prompt should produce same hash
        assert hash1 == hash2
        
        # Different prompt should produce different hash
        hash3 = agent._create_prompt_hash("Different prompt")
        assert hash1 != hash3

    def test_json_response_parsing(self, mock_llm):
        """Test JSON response parsing."""
        agent = TechnicalAgent()
        
        # Test plain JSON
        response = '{"signal": "BULLISH", "strength": 0.8}'
        parsed = agent._parse_json_response(response)
        assert parsed["signal"] == "BULLISH"
        
        # Test JSON in markdown code block
        response = '```json\n{"signal": "BEARISH", "strength": 0.3}\n```'
        parsed = agent._parse_json_response(response)
        assert parsed["signal"] == "BEARISH"

    def test_json_parsing_error(self, mock_llm):
        """Test handling of invalid JSON."""
        agent = TechnicalAgent()
        
        with pytest.raises(Exception):
            agent._parse_json_response("invalid json")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
