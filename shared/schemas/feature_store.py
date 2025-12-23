"""
Feature Store schemas - CRITICAL for point-in-time correctness.
All feature snapshots are APPEND-ONLY and IMMUTABLE.
"""
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from .base import TimestampedSchema


class FeatureSnapshot(TimestampedSchema):
    """
    APPEND-ONLY feature snapshot for a specific ticker and date.

    CRITICAL PROPERTIES:
    - Immutable once created
    - Point-in-time correct (no look-ahead bias)
    - Agents can ONLY read from these snapshots
    - Never updated, only new versions appended
    """

    snapshot_id: str = Field(..., description="Unique snapshot identifier (UUID)")
    ticker: str = Field(..., description="Stock ticker")
    as_of_date: date = Field(..., description="Date this snapshot represents")

    # Technical features (from market data)
    technical_features: dict[str, Any] = Field(
        default_factory=dict,
        description="All technical indicators as of this date"
    )

    # Sentiment features (from news)
    sentiment_features: dict[str, Any] = Field(
        default_factory=dict,
        description="All sentiment metrics as of this date"
    )

    # Metadata for reproducibility
    feature_version: str = Field(..., description="Feature schema version")
    data_sources: dict[str, str] = Field(
        default_factory=dict,
        description="Source identifiers for traceability"
    )

    model_config = ConfigDict(frozen=True)


class FeatureSnapshotMetadata(BaseModel):
    """Metadata about available feature snapshots."""

    ticker: str
    as_of_date: date
    snapshot_id: str
    feature_version: str
    created_at: datetime
    has_technical: bool = Field(..., description="Technical features available")
    has_sentiment: bool = Field(..., description="Sentiment features available")

    model_config = ConfigDict(frozen=True)


class FeatureValidation(BaseModel):
    """
    Validation result for feature quality.
    Used to flag incomplete or suspicious data.
    """

    snapshot_id: str
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)


class FeatureQuery(BaseModel):
    """Query parameters for retrieving feature snapshots."""

    ticker: str
    as_of_date: date
    feature_version: Optional[str] = Field(
        None,
        description="Specific version, or latest if not specified"
    )

    model_config = ConfigDict(frozen=True)


class FeatureBatch(BaseModel):
    """
    Batch of feature snapshots for agent consumption.
    Used when agents need to reason over multiple stocks/dates.
    """

    snapshots: list[FeatureSnapshot]
    batch_id: str = Field(..., description="Batch identifier for tracking")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
