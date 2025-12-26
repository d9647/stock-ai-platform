"""
Unit tests for pipeline orchestration.
"""
import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock

import sys
from pathlib import Path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.pipelines.daily_agent_pipeline import DailyAgentPipeline


@pytest.fixture
def mock_dependencies():
    """Mock all pipeline dependencies."""
    with patch('src.pipelines.daily_agent_pipeline.build_agent_graph') as mock_graph, \
         patch('src.pipelines.daily_agent_pipeline.FeatureSnapshotReader') as mock_reader, \
         patch('src.pipelines.daily_agent_pipeline.AgentOutputWriter') as mock_writer:
        
        # Mock graph
        mock_graph_instance = MagicMock()
        mock_graph.return_value = mock_graph_instance
        
        # Mock successful graph execution
        mock_graph_instance.invoke.return_value = {
            "ticker": "AAPL",
            "as_of_date": date(2024, 12, 16),
            "feature_snapshot": {},
            "technical_output": {"signal": "BULLISH"},
            "sentiment_output": {"signal": "BULLISH"},
            "risk_output": {"signal": "MEDIUM_RISK"},
            "recommendation": {"recommendation": "BUY"},
            "errors": [],
            "execution_start": 1000.0
        }
        
        # Mock reader
        mock_reader_instance = MagicMock()
        mock_reader.return_value = mock_reader_instance
        mock_reader_instance.get_snapshot.return_value = {
            "snapshot_id": "AAPL_2024-12-16_snap_123",
            "ticker": "AAPL",
            "technical_features": {},
            "sentiment_features": {}
        }
        
        # Mock writer
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance
        mock_writer_instance.write_agent_outputs.return_value = {
            "outputs_written": 4,
            "recommendation_written": True
        }
        mock_writer_instance.recommendation_exists.return_value = False
        
        yield {
            "graph": mock_graph_instance,
            "reader": mock_reader_instance,
            "writer": mock_writer_instance
        }


class TestDailyAgentPipeline:
    """Test suite for DailyAgentPipeline."""

    def test_initialization(self, mock_dependencies):
        """Test pipeline initialization."""
        pipeline = DailyAgentPipeline()
        
        assert pipeline is not None
        assert pipeline.agent_graph is not None
        assert pipeline.reader is not None
        assert pipeline.writer is not None

    def test_run_for_ticker_and_date_success(self, mock_dependencies):
        """Test successful pipeline execution for single ticker."""
        pipeline = DailyAgentPipeline()
        
        result = pipeline.run_for_ticker_and_date("AAPL", date(2024, 12, 16))
        
        assert result["status"] == "success"
        assert result["ticker"] == "AAPL"
        assert result["recommendation"] == "BUY"
        assert len(result["errors"]) == 0
        
        # Verify reader was called
        assert mock_dependencies["reader"].get_snapshot.called
        
        # Verify graph was invoked
        assert mock_dependencies["graph"].invoke.called
        
        # Verify writer was called
        assert mock_dependencies["writer"].write_agent_outputs.called

    def test_run_for_ticker_and_date_no_snapshot(self, mock_dependencies):
        """Test handling when no feature snapshot exists."""
        # Mock reader to return None
        mock_dependencies["reader"].get_snapshot.return_value = None
        
        pipeline = DailyAgentPipeline()
        result = pipeline.run_for_ticker_and_date("AAPL", date(2024, 12, 16))
        
        assert result["status"] == "failed"
        assert "No feature snapshot available" in result["errors"]

    def test_run_for_ticker_and_date_graph_error(self, mock_dependencies):
        """Test handling of graph execution error."""
        # Mock graph to raise exception
        mock_dependencies["graph"].invoke.side_effect = Exception("Graph execution failed")
        
        pipeline = DailyAgentPipeline()
        result = pipeline.run_for_ticker_and_date("AAPL", date(2024, 12, 16))
        
        assert result["status"] == "failed"
        assert len(result["errors"]) > 0

    def test_run_for_multiple_tickers(self, mock_dependencies):
        """Test pipeline execution for multiple tickers."""
        pipeline = DailyAgentPipeline()
        
        tickers = ["AAPL", "MSFT", "GOOGL"]
        summary = pipeline.run_for_multiple_tickers(tickers, date(2024, 12, 16))
        
        assert summary["total_tickers"] == 3
        assert summary["successful"] == 3
        assert summary["failed"] == 0
        assert summary["skipped"] == 0
        assert "recommendations" in summary
        assert summary["recommendations"]["BUY"] == 3

    def test_run_for_multiple_tickers_mixed_results(self, mock_dependencies):
        """Test pipeline with mixed success/failure results."""
        # Mock reader to fail for second ticker
        def get_snapshot_side_effect(ticker, as_of_date):
            if ticker == "MSFT":
                return None
            return {"snapshot_id": f"{ticker}_snap", "ticker": ticker}
        
        mock_dependencies["reader"].get_snapshot.side_effect = get_snapshot_side_effect
        
        pipeline = DailyAgentPipeline()
        tickers = ["AAPL", "MSFT", "GOOGL"]
        summary = pipeline.run_for_multiple_tickers(tickers, date(2024, 12, 16))
        
        assert summary["total_tickers"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1

    def test_close(self, mock_dependencies):
        """Test pipeline cleanup."""
        pipeline = DailyAgentPipeline()
        pipeline.close()
        
        assert mock_dependencies["reader"].close.called
        assert mock_dependencies["writer"].close.called


class TestPipelineStateManagement:
    """Test pipeline state management."""

    def test_initial_state_creation(self, mock_dependencies):
        """Test creation of initial state for graph."""
        pipeline = DailyAgentPipeline()
        
        # Run pipeline and capture graph invocation
        pipeline.run_for_ticker_and_date("AAPL", date(2024, 12, 16))
        
        # Get the state passed to graph
        call_args = mock_dependencies["graph"].invoke.call_args
        initial_state = call_args[0][0]
        
        assert initial_state["ticker"] == "AAPL"
        assert initial_state["as_of_date"] == date(2024, 12, 16)
        assert "feature_snapshot" in initial_state
        assert initial_state["technical_output"] is None
        assert initial_state["sentiment_output"] is None
        assert initial_state["risk_output"] is None
        assert initial_state["recommendation"] is None
        assert initial_state["errors"] == []
        assert "execution_start" in initial_state


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
