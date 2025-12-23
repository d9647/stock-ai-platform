"""
Agent output models - what agents produce (OFFLINE ONLY).
ALL records are IMMUTABLE and pre-computed.

CRITICAL: These tables are NEVER written to during API requests.
They are only populated by offline agent orchestration pipelines.
"""
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, Text, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class AgentOutput(Base):
    """
    Individual agent output (IMMUTABLE).
    Records what each specialized agent decided.
    """
    __tablename__ = "agent_outputs"
    __table_args__ = (
        Index("idx_agent_output_id", "output_id", unique=True),
        Index("idx_agent_ticker_date", "ticker", "as_of_date"),
        Index("idx_agent_type_date", "agent_type", "as_of_date"),
        Index("idx_agent_feature_snapshot", "feature_snapshot_id"),
        {"schema": "agents"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    output_id = Column(String(100), nullable=False, unique=True, index=True)

    # What agent and when
    agent_type = Column(String(50), nullable=False, index=True)  # technical, sentiment, risk, etc.
    ticker = Column(String(10), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)

    # Agent decision (stored as JSONB for flexibility)
    signal = Column(String(20))  # BULLISH, NEUTRAL, BEARISH
    strength = Column(Float)  # 0.0 to 1.0
    reasoning = Column(JSONB, default=[])  # List of reasoning points
    agent_metadata = Column(JSONB, default={})  # Additional agent-specific data

    # Traceability
    feature_snapshot_id = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    prompt_hash = Column(String(64), nullable=False)  # SHA-256 hash

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AgentOutput(agent={self.agent_type}, ticker={self.ticker}, signal={self.signal})>"


class StockRecommendation(Base):
    """
    Final synthesized recommendation (IMMUTABLE).
    This is what the API serves to users.

    CRITICAL: Pre-computed offline, NEVER generated during API requests.
    """
    __tablename__ = "stock_recommendations"
    __table_args__ = (
        Index("idx_recommendation_id", "recommendation_id", unique=True),
        Index("idx_recommendation_ticker_date", "ticker", "as_of_date"),
        Index("idx_recommendation_date", "as_of_date"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
        {"schema": "agents"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(String(100), nullable=False, unique=True, index=True)

    # What and when
    ticker = Column(String(10), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)

    # Recommendation
    recommendation = Column(String(20), nullable=False)  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0

    # Supporting signals
    technical_signal = Column(String(20))
    sentiment_signal = Column(String(20))
    risk_level = Column(String(20))

    # Explanation (structured for UI)
    rationale = Column(JSONB, nullable=False, default={})

    # Position sizing
    position_size = Column(String(20))  # NONE, SMALL, MEDIUM, LARGE
    time_horizon = Column(String(50))  # e.g., "1-3 months"

    # Traceability - links to agent outputs
    agent_outputs = Column(JSONB, nullable=False, default={})  # Map of agent_type -> output_id
    feature_snapshot_id = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<StockRecommendation(ticker={self.ticker}, date={self.as_of_date}, rec={self.recommendation})>"


class AgentExecutionLog(Base):
    """
    Log of agent execution for monitoring (IMMUTABLE).
    Tracks performance, costs, and errors.
    """
    __tablename__ = "agent_execution_logs"
    __table_args__ = (
        Index("idx_execution_id", "execution_id"),
        Index("idx_execution_agent_date", "agent_type", "as_of_date"),
        Index("idx_execution_status", "status"),
        {"schema": "agents"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(String(100), nullable=False, index=True)

    agent_type = Column(String(50), nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    as_of_date = Column(Date, nullable=False)

    # Execution tracking
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Float, nullable=False)

    status = Column(String(20), nullable=False)  # success, failed, timeout
    error_message = Column(Text)

    # Cost tracking
    tokens_used = Column(Integer)
    cost_usd = Column(Float)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AgentExecutionLog(agent={self.agent_type}, status={self.status})>"
