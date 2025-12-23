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

from api.app.models.agents import AgentOutput, StockRecommendation
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
        # TODO: Implement proper execution logging matching the schema
        # For now, skip execution logs to get the pipeline working
        logger.debug("Skipping execution log write (not yet implemented)")

    def close(self):
        """Close database session."""
        self.session.close()
