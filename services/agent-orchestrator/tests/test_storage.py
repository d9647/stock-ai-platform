"""
Unit tests for storage layer (feature reader and agent writer).
"""
import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.storage.feature_reader import FeatureSnapshotReader
from src.storage.agent_writer import AgentOutputWriter


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    with patch('src.storage.feature_reader.create_engine') as mock_engine_fr, \
         patch('src.storage.feature_reader.sessionmaker') as mock_sessionmaker_fr, \
         patch('src.storage.agent_writer.create_engine') as mock_engine_aw, \
         patch('src.storage.agent_writer.sessionmaker') as mock_sessionmaker_aw:
        
        # Mock session for feature reader
        mock_session_fr = MagicMock()
        mock_sessionmaker_fr.return_value.return_value = mock_session_fr
        
        # Mock session for agent writer
        mock_session_aw = MagicMock()
        mock_sessionmaker_aw.return_value.return_value = mock_session_aw
        
        yield {
            "feature_reader_session": mock_session_fr,
            "agent_writer_session": mock_session_aw
        }


class TestFeatureSnapshotReader:
    """Test suite for FeatureSnapshotReader."""

    def test_initialization(self, mock_db_session):
        """Test reader initialization."""
        reader = FeatureSnapshotReader()
        
        assert reader is not None
        assert reader.session is not None

    def test_get_snapshot_success(self, mock_db_session):
        """Test successful snapshot retrieval."""
        reader = FeatureSnapshotReader()
        
        # Mock snapshot from database
        mock_snapshot = MagicMock()
        mock_snapshot.snapshot_id = "AAPL_2024-12-16_snap_123"
        mock_snapshot.ticker = "AAPL"
        mock_snapshot.as_of_date = date(2024, 12, 16)
        mock_snapshot.feature_version = "1.0.0"
        mock_snapshot.snapshot_data = {
            "technical_features": {"close": 195.50},
            "sentiment_features": {"avg_sentiment": 0.6}
        }
        
        # Configure mock query
        mock_query = mock_db_session["feature_reader_session"].query.return_value
        mock_query.filter.return_value.first.return_value = mock_snapshot
        
        result = reader.get_snapshot("AAPL", date(2024, 12, 16))
        
        assert result is not None
        assert result["snapshot_id"] == "AAPL_2024-12-16_snap_123"
        assert result["ticker"] == "AAPL"
        assert "technical_features" in result
        assert "sentiment_features" in result

    def test_get_snapshot_not_found(self, mock_db_session):
        """Test handling when snapshot doesn't exist."""
        reader = FeatureSnapshotReader()
        
        # Mock query returning None
        mock_query = mock_db_session["feature_reader_session"].query.return_value
        mock_query.filter.return_value.first.return_value = None
        
        result = reader.get_snapshot("AAPL", date(2024, 12, 16))
        
        assert result is None

    def test_get_snapshot_database_error(self, mock_db_session):
        """Test handling of database errors."""
        reader = FeatureSnapshotReader()
        
        # Mock query raising exception
        mock_db_session["feature_reader_session"].query.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            reader.get_snapshot("AAPL", date(2024, 12, 16))
        
        assert "Database error" in str(exc_info.value)

    def test_close(self, mock_db_session):
        """Test closing database session."""
        reader = FeatureSnapshotReader()
        reader.close()
        
        assert mock_db_session["feature_reader_session"].close.called


class TestAgentOutputWriter:
    """Test suite for AgentOutputWriter."""

    def test_initialization(self, mock_db_session):
        """Test writer initialization."""
        writer = AgentOutputWriter()
        
        assert writer is not None
        assert writer.session is not None

    def test_write_agent_outputs_success(self, mock_db_session):
        """Test successful writing of agent outputs."""
        writer = AgentOutputWriter()
        
        final_state = {
            "ticker": "AAPL",
            "as_of_date": date(2024, 12, 16),
            "technical_output": {
                "output_id": "tech_123",
                "agent_type": "technical",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "signal": "BULLISH",
                "strength": 0.8,
                "reasoning": ["Strong trend"],
                "agent_metadata": {},
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0",
                "prompt_hash": "abc123"
            },
            "sentiment_output": {
                "output_id": "sent_123",
                "agent_type": "sentiment",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "signal": "BULLISH",
                "strength": 0.7,
                "reasoning": ["Positive news"],
                "agent_metadata": {},
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0",
                "prompt_hash": "def456"
            },
            "risk_output": {
                "output_id": "risk_123",
                "agent_type": "risk",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "signal": "MEDIUM_RISK",
                "strength": 0.6,
                "reasoning": ["Moderate volatility"],
                "agent_metadata": {},
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0",
                "prompt_hash": "ghi789"
            },
            "recommendation": {
                "recommendation_id": "rec_123",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "recommendation": "BUY",
                "confidence": 0.75,
                "rationale": {},
                "technical_signal": "BULLISH",
                "sentiment_signal": "BULLISH",
                "risk_assessment": "MEDIUM_RISK",
                "position_size": "medium",
                "time_horizon": "medium_term",
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0"
            },
            "errors": [],
            "execution_start": 1000.0
        }
        
        result = writer.write_agent_outputs(final_state)
        
        assert result["outputs_written"] == 4
        assert result["recommendation_written"] is True
        assert mock_db_session["agent_writer_session"].commit.called

    def test_write_agent_outputs_partial(self, mock_db_session):
        """Test writing with some missing outputs."""
        writer = AgentOutputWriter()
        
        final_state = {
            "ticker": "AAPL",
            "as_of_date": date(2024, 12, 16),
            "technical_output": {
                "output_id": "tech_123",
                "agent_type": "technical",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "signal": "BULLISH",
                "strength": 0.8,
                "reasoning": [],
                "agent_metadata": {},
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0",
                "prompt_hash": "abc123"
            },
            "sentiment_output": None,
            "risk_output": None,
            "recommendation": None,
            "errors": [],
            "execution_start": 1000.0
        }
        
        result = writer.write_agent_outputs(final_state)
        
        assert result["outputs_written"] == 1
        assert result["recommendation_written"] is False

    def test_write_agent_outputs_database_error(self, mock_db_session):
        """Test handling of database errors."""
        writer = AgentOutputWriter()
        
        # Mock execute to raise exception
        mock_db_session["agent_writer_session"].execute.side_effect = Exception("Write error")
        
        final_state = {
            "ticker": "AAPL",
            "as_of_date": date(2024, 12, 16),
            "technical_output": {
                "output_id": "tech_123",
                "agent_type": "technical",
                "ticker": "AAPL",
                "as_of_date": date(2024, 12, 16),
                "signal": "BULLISH",
                "strength": 0.8,
                "reasoning": [],
                "agent_metadata": {},
                "feature_snapshot_id": "snap_123",
                "model_version": "1.0.0",
                "prompt_hash": "abc123"
            },
            "errors": [],
            "execution_start": 1000.0
        }
        
        with pytest.raises(Exception) as exc_info:
            writer.write_agent_outputs(final_state)
        
        assert "Write error" in str(exc_info.value)
        assert mock_db_session["agent_writer_session"].rollback.called

    def test_close(self, mock_db_session):
        """Test closing database session."""
        writer = AgentOutputWriter()
        writer.close()
        
        assert mock_db_session["agent_writer_session"].close.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
