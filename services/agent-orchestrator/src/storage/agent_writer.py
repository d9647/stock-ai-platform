"""
Write agent outputs and recommendations to database.
"""
from typing import Dict, Any, List
from datetime import datetime
import json
import sys
from pathlib import Path

# Add API models to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

from api.app.models.agents import AgentOutput, StockRecommendation, AgentExecutionLog
from ..config import config


class AgentOutputWriter:
    """
    Write agent outputs to database.
    Writes to 3 tables:
    1. agents.agent_outputs - Individual agent decisions
    2. agents.stock_recommendations - Final recommendations
    3. agents.agent_execution_logs - Execution tracking
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

        logger.info("Initialized agent output writer")

    def write_agent_outputs(self, final_state: Dict[str, Any]) -> Dict[str, int]:
        """
        Write all agent outputs from final state to database.

        Args:
            final_state: Final state from LangGraph execution

        Returns:
            Dict with counts of written records
        """
        try:
            outputs_written = 0
            recommendation_written = False

            # Write individual agent outputs
            for agent_type in ["technical_output", "sentiment_output", "risk_output"]:
                output = final_state.get(agent_type)
                if output:
                    self._write_agent_output(output)
                    outputs_written += 1

            # Write final recommendation
            recommendation = final_state.get("recommendation")
            if recommendation:
                self._write_recommendation(recommendation)
                recommendation_written = True
                outputs_written += 1

            # Write execution log
            self._write_execution_log(final_state)

            self.session.commit()
            logger.info(f"Wrote {outputs_written} outputs to database")

            return {
                "outputs_written": outputs_written,
                "recommendation_written": recommendation_written
            }

        except Exception as e:
            logger.error(f"Error writing outputs: {e}")
            self.session.rollback()
            raise

    def _write_agent_output(self, output: Dict[str, Any]):
        """Write single agent output to agents.agent_outputs table."""
        # Check if already exists
        existing = self.session.query(AgentOutput).filter_by(
            output_id=output["output_id"]
        ).first()

        if existing:
            logger.debug(f"Output {output['output_id']} already exists, skipping")
            return

        # Create new AgentOutput using ORM
        agent_output = AgentOutput(
            output_id=output["output_id"],
            agent_type=output["agent_type"],
            ticker=output["ticker"],
            as_of_date=output["as_of_date"],
            signal=output["signal"],
            strength=output["strength"],
            reasoning=output.get("reasoning", []),
            agent_metadata=output.get("agent_metadata", {}),
            feature_snapshot_id=output.get("feature_snapshot_id"),
            model_version=output["model_version"],
            prompt_hash=output.get("prompt_hash", "")
        )

        self.session.add(agent_output)

    def _write_recommendation(self, recommendation: Dict[str, Any]):
        """Write final recommendation to agents.stock_recommendations table."""
        # Check if already exists
        existing = self.session.query(StockRecommendation).filter_by(
            recommendation_id=recommendation["recommendation_id"]
        ).first()

        if existing:
            logger.debug(f"Recommendation {recommendation['recommendation_id']} already exists, skipping")
            return

        # Create new StockRecommendation using ORM
        stock_rec = StockRecommendation(
            recommendation_id=recommendation["recommendation_id"],
            ticker=recommendation["ticker"],
            as_of_date=recommendation["as_of_date"],
            recommendation=recommendation["recommendation"],
            confidence=recommendation["confidence"],
            rationale=recommendation.get("rationale", {}),
            technical_signal=recommendation.get("technical_signal"),
            sentiment_signal=recommendation.get("sentiment_signal"),
            risk_level=recommendation.get("risk_level"),  # Changed from risk_assessment
            position_size=recommendation.get("position_size"),
            time_horizon=recommendation.get("time_horizon"),
            agent_outputs=recommendation.get("agent_outputs", {}),  # Added agent_outputs
            feature_snapshot_id=recommendation.get("feature_snapshot_id"),
            model_version=recommendation["model_version"]
        )

        self.session.add(stock_rec)

    def _write_execution_log(self, final_state: Dict[str, Any]):
        """Write execution log to agents.agent_execution_logs table."""
        try:
            start_ts = final_state.get("execution_start")
            started_at = (
                datetime.fromtimestamp(start_ts)
                if isinstance(start_ts, (int, float))
                else datetime.utcnow()
            )
            completed_at = datetime.utcnow()
            duration_seconds = (completed_at - started_at).total_seconds()

            execution_id = final_state.get("execution_id") or f"{final_state.get('ticker')}_{final_state.get('as_of_date')}"
            status = "success" if not final_state.get("errors") else "failed"
            error_message = "; ".join(final_state.get("errors", [])) or None

            # Avoid duplicate logs for the same execution_id/agent_type/date
            existing = (
                self.session.query(AgentExecutionLog)
                .filter_by(
                    execution_id=execution_id,
                    agent_type="pipeline",
                    as_of_date=final_state.get("as_of_date"),
                )
                .first()
            )
            if existing:
                logger.debug(f"Execution log {execution_id} already exists, skipping")
                return

            log_entry = AgentExecutionLog(
                execution_id=execution_id,
                agent_type="pipeline",
                ticker=final_state.get("ticker"),
                as_of_date=final_state.get("as_of_date"),
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                status=status,
                error_message=error_message,
                tokens_used=final_state.get("tokens_used"),
                cost_usd=final_state.get("cost_usd"),
            )

            self.session.add(log_entry)
            logger.debug(f"Wrote execution log {execution_id}")

        except Exception as e:
            logger.error(f"Error writing execution log: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()

    # Convenience helpers
    def recommendation_exists(self, ticker: str, as_of_date) -> bool:
        """Return True if a recommendation already exists for ticker/date."""
        return (
            self.session.query(StockRecommendation)
            .filter_by(ticker=ticker, as_of_date=as_of_date)
            .first()
            is not None
        )
