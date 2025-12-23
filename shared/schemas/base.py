"""
Base schemas and common types used across all services.
All timestamps are in UTC. All schemas are immutable after creation.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TimestampedSchema(BaseModel):
    """Base schema with creation timestamp (immutable)."""

    model_config = ConfigDict(frozen=True)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this record was created (immutable)"
    )


class StockSymbol(BaseModel):
    """Validated stock symbol."""

    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")

    model_config = ConfigDict(frozen=True)


class DateRange(BaseModel):
    """Date range for queries."""

    start_date: datetime
    end_date: datetime

    model_config = ConfigDict(frozen=True)


class Recommendation(str, Enum):
    """Stock recommendation types."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class Signal(str, Enum):
    """Agent signal types."""

    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class PositionSize(str, Enum):
    """Position sizing recommendations."""

    NONE = "NONE"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
