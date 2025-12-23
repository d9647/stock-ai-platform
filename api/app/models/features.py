"""
Feature Store models - CRITICAL for point-in-time correctness.
ALL records are APPEND-ONLY and IMMUTABLE.
Agents can ONLY read from feature snapshots, never raw tables.
"""
from sqlalchemy import (
    Column, String, Date, DateTime, Boolean, Integer, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from ..db.base import Base


class FeatureSnapshot(Base):
    """
    APPEND-ONLY feature snapshot for a specific ticker and date.

    CRITICAL INVARIANTS:
    1. NEVER updated - only INSERT operations allowed
    2. Provides point-in-time correctness (no look-ahead bias)
    3. Agents can ONLY read from these snapshots
    4. Each snapshot is versioned for reproducibility

    This is the SINGLE SOURCE OF TRUTH for agent inputs.
    """
    __tablename__ = "feature_snapshots"
    __table_args__ = (
        Index("idx_features_snapshot_id", "snapshot_id"),
        Index("idx_features_ticker_date", "ticker", "as_of_date"),
        Index("idx_features_date", "as_of_date"),
        Index("idx_features_version", "feature_version"),
        UniqueConstraint("snapshot_id", name="uq_feature_snapshot"),
        {"schema": "features"},
    )

    # Primary key (UUID for immutability)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String(100), nullable=False, index=True)

    # What and when
    ticker = Column(String(10), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)

    # Feature data (JSONB for flexibility)
    snapshot_data = Column(JSONB, nullable=False, default={})

    # Versioning for reproducibility
    feature_version = Column(String(50), nullable=False, index=True)

    # Immutability tracking (no updated_at - because it's never updated!)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<FeatureSnapshot(snapshot_id={self.snapshot_id}, ticker={self.ticker}, date={self.as_of_date})>"


class FeatureValidation(Base):
    """
    Validation results for feature snapshots (IMMUTABLE).
    Tracks data quality issues.
    """
    __tablename__ = "feature_validations"
    __table_args__ = (
        Index("idx_validation_snapshot", "snapshot_id"),
        Index("idx_validation_ticker_date", "ticker", "as_of_date"),
        UniqueConstraint("snapshot_id", name="uq_feature_validation"),
        {"schema": "features"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(String(100), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)

    is_valid = Column(Boolean, nullable=False)
    errors = Column(ARRAY(String), default=[])
    warnings = Column(ARRAY(String), default=[])
    checks_passed = Column(Integer, default=0)
    checks_failed = Column(Integer, default=0)

    validated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<FeatureValidation(snapshot_id={self.snapshot_id}, valid={self.is_valid})>"
