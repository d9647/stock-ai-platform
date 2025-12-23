"""
Agent output schemas - what agents produce (OFFLINE ONLY).
These schemas ensure agent outputs are structured and auditable.

CRITICAL: Agents never run in API requests. These schemas represent
pre-computed, versioned results stored in the database.
"""
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from .base import TimestampedSchema, Signal, RiskLevel, PositionSize, Recommendation


class AgentOutput(TimestampedSchema):
    """
    Base schema for all agent outputs.
    Every agent decision is versioned and traceable.
    """

    output_id: str = Field(..., description="Unique output identifier (UUID)")
    agent_type: str = Field(..., description="Type of agent (technical, sentiment, risk, etc.)")
    ticker: str = Field(..., description="Stock ticker analyzed")
    as_of_date: date = Field(..., description="Analysis date")

    # Traceability
    feature_snapshot_id: str = Field(
        ...,
        description="Feature snapshot this analysis is based on"
    )
    model_version: str = Field(..., description="Agent model version")
    prompt_hash: str = Field(..., description="Hash of prompt used (for reproducibility)")

    model_config = ConfigDict(frozen=True)


class TechnicalAgentOutput(AgentOutput):
    """Output from Technical Analyst agent."""

    agent_type: str = Field(default="technical", frozen=True)

    signal: Signal = Field(..., description="Technical signal (BULLISH/NEUTRAL/BEARISH)")
    strength: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Signal strength/confidence"
    )

    reasoning: list[str] = Field(
        ...,
        description="List of technical reasons for this signal"
    )

    key_indicators: dict[str, Any] = Field(
        default_factory=dict,
        description="Key technical indicators that drove the decision"
    )

    model_config = ConfigDict(frozen=True)


class SentimentAgentOutput(AgentOutput):
    """Output from Sentiment Analyst agent."""

    agent_type: str = Field(default="sentiment", frozen=True)

    signal: Signal = Field(..., description="Sentiment signal")
    strength: float = Field(..., ge=0.0, le=1.0, description="Sentiment strength")

    reasoning: list[str] = Field(
        ...,
        description="Key sentiment drivers"
    )

    top_themes: list[str] = Field(
        default_factory=list,
        description="Most important themes from news"
    )

    article_count: int = Field(..., ge=0, description="Number of articles analyzed")

    model_config = ConfigDict(frozen=True)


class RiskAgentOutput(AgentOutput):
    """Output from Risk Manager agent."""

    agent_type: str = Field(default="risk", frozen=True)

    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quantitative risk score"
    )

    risk_factors: list[str] = Field(
        ...,
        description="Identified risk factors"
    )

    position_sizing: PositionSize = Field(
        ...,
        description="Recommended position size given risk"
    )

    model_config = ConfigDict(frozen=True)


class StockRecommendation(TimestampedSchema):
    """
    Final synthesized recommendation (from Portfolio Synthesizer agent).
    This is what the API serves to users.

    CRITICAL: This is pre-computed offline, never generated on-demand.
    """

    recommendation_id: str = Field(..., description="Unique recommendation ID (UUID)")
    ticker: str = Field(..., description="Stock ticker")
    as_of_date: date = Field(..., description="Recommendation date")

    # Recommendation
    recommendation: Recommendation = Field(
        ...,
        description="Final recommendation (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in recommendation"
    )

    # Supporting signals from individual agents
    technical_signal: Signal = Field(..., description="Technical agent signal")
    sentiment_signal: Signal = Field(..., description="Sentiment agent signal")
    risk_level: RiskLevel = Field(..., description="Risk assessment")

    # Explanation (for UI)
    rationale: dict[str, list[str]] = Field(
        ...,
        description="Structured explanation: {technical: [...], sentiment: [...], risk: [...]}"
    )

    # Position sizing
    position_size: PositionSize = Field(..., description="Recommended position size")
    time_horizon: str = Field(..., description="Suggested holding period")

    # Traceability
    agent_outputs: dict[str, str] = Field(
        ...,
        description="Map of agent_type -> output_id for full audit trail"
    )
    feature_snapshot_id: str = Field(
        ...,
        description="Feature snapshot all agents used"
    )
    model_version: str = Field(..., description="Synthesizer model version")

    model_config = ConfigDict(frozen=True)


class AgentExecutionLog(TimestampedSchema):
    """
    Log of agent execution for monitoring and debugging.
    Tracks when agents ran, how long they took, etc.
    """

    execution_id: str = Field(..., description="Execution run ID")
    agent_type: str = Field(..., description="Agent type")
    ticker: str = Field(..., description="Stock analyzed")
    as_of_date: date = Field(..., description="Analysis date")

    started_at: datetime = Field(..., description="Execution start time")
    completed_at: datetime = Field(..., description="Execution completion time")
    duration_seconds: float = Field(..., ge=0, description="Execution duration")

    status: str = Field(..., description="success, failed, timeout")
    error_message: Optional[str] = Field(None, description="Error if failed")

    tokens_used: Optional[int] = Field(None, description="LLM tokens consumed")
    cost_usd: Optional[float] = Field(None, description="Estimated cost")

    model_config = ConfigDict(frozen=True)
