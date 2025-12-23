"""
Write feature snapshots and validation results to PostgreSQL.
Follows append-only, immutable pattern.
"""
from datetime import datetime
from typing import Dict, List
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from loguru import logger

from api.app.models.features import FeatureSnapshot, FeatureValidation

# Import config with proper path handling
try:
    from ..config import config
except ImportError:
    from config import config


class FeatureStoreWriter:
    """
    Write feature snapshots and validation results to PostgreSQL.
    All writes are append-only and idempotent.
    """

    def __init__(self, database_url: str = None):
        """Initialize database writer."""
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

        logger.info("Initialized feature store writer")

    def write_snapshot(self, snapshot: Dict) -> bool:
        """
        Write a feature snapshot to the database.

        Args:
            snapshot: Snapshot dict from SnapshotCreator

        Returns:
            True if written (or already exists), False on error
        """
        try:
            # Extract snapshot metadata
            snapshot_id = snapshot["snapshot_id"]
            ticker = snapshot["ticker"]
            as_of_date = snapshot["as_of_date"]
            feature_version = snapshot["feature_version"]

            # Build snapshot data for JSONB column
            snapshot_data = {
                "technical_features": snapshot.get("technical_features", {}),
                "sentiment_features": snapshot.get("sentiment_features", {}),
                "data_sources": snapshot.get("data_sources", {})
            }

            # Prepare record
            record = {
                "snapshot_id": snapshot_id,
                "ticker": ticker,
                "as_of_date": as_of_date,
                "feature_version": feature_version,
                "snapshot_data": snapshot_data,
                "created_at": datetime.utcnow()
            }

            # Insert with idempotency (ON CONFLICT DO NOTHING)
            stmt = insert(FeatureSnapshot.__table__).values(record)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_feature_snapshot"
            )

            result = self.session.execute(stmt)
            self.session.commit()

            # Check if row was inserted
            if result.rowcount > 0:
                logger.info(f"Wrote snapshot: {snapshot_id}")
                return True
            else:
                logger.debug(f"Snapshot already exists: {snapshot_id}")
                return True

        except Exception as e:
            logger.error(f"Error writing snapshot {snapshot.get('snapshot_id')}: {e}")
            self.session.rollback()
            return False

    def write_snapshots_batch(self, snapshots: List[Dict]) -> int:
        """
        Write multiple snapshots in batch.

        Args:
            snapshots: List of snapshot dicts

        Returns:
            Number of snapshots written (including duplicates skipped)
        """
        success_count = 0

        for snapshot in snapshots:
            if self.write_snapshot(snapshot):
                success_count += 1

        logger.info(f"Wrote {success_count}/{len(snapshots)} snapshots")
        return success_count

    def write_validation(
        self,
        snapshot_id: str,
        ticker: str,
        as_of_date,
        validation_result: Dict
    ) -> bool:
        """
        Write validation results to the database.

        Args:
            snapshot_id: Snapshot identifier
            ticker: Stock ticker symbol
            as_of_date: Date of snapshot
            validation_result: Validation dict from FeatureValidator

        Returns:
            True if written, False on error
        """
        try:
            # Extract validation results
            is_valid = validation_result["is_valid"]
            errors = validation_result.get("errors", [])
            warnings = validation_result.get("warnings", [])
            checks_passed = validation_result.get("checks_passed", 0)
            checks_failed = validation_result.get("checks_failed", 0)

            # Prepare record
            record = {
                "snapshot_id": snapshot_id,
                "ticker": ticker,
                "as_of_date": as_of_date,
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
                "validated_at": datetime.utcnow()
            }

            # Insert with idempotency
            stmt = insert(FeatureValidation.__table__).values(record)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_feature_validation"
            )

            result = self.session.execute(stmt)
            self.session.commit()

            if result.rowcount > 0:
                logger.info(
                    f"Wrote validation for {snapshot_id}: "
                    f"valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}"
                )
                return True
            else:
                logger.debug(f"Validation already exists: {snapshot_id}")
                return True

        except Exception as e:
            logger.error(f"Error writing validation for {snapshot_id}: {e}")
            self.session.rollback()
            return False

    def get_snapshot_count(self) -> int:
        """Get total number of snapshots in database."""
        try:
            count = self.session.query(FeatureSnapshot).count()
            logger.info(f"Total snapshots in database: {count}")
            return count
        except Exception as e:
            logger.error(f"Error counting snapshots: {e}")
            return 0

    def get_validation_summary(self) -> Dict:
        """
        Get summary of validation results.

        Returns:
            Dict with validation statistics
        """
        try:
            total = self.session.query(FeatureValidation).count()
            valid = (
                self.session.query(FeatureValidation)
                .filter(FeatureValidation.is_valid == True)
                .count()
            )
            invalid = total - valid

            summary = {
                "total_validations": total,
                "valid_count": valid,
                "invalid_count": invalid,
                "valid_percentage": (valid / total * 100) if total > 0 else 0
            }

            logger.info(
                f"Validation summary: {valid}/{total} valid "
                f"({summary['valid_percentage']:.1f}%)"
            )

            return summary

        except Exception as e:
            logger.error(f"Error getting validation summary: {e}")
            return {
                "total_validations": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "valid_percentage": 0
            }

    def close(self):
        """Close database session."""
        self.session.close()
        logger.info("Closed database connection")


if __name__ == "__main__":
    # Test database writer
    from datetime import date

    writer = FeatureStoreWriter()

    # Test snapshot write
    test_snapshot = {
        "snapshot_id": "TEST_2025-12-16_1.0.0",
        "ticker": "TEST",
        "as_of_date": date(2025, 12, 16),
        "feature_version": "1.0.0",
        "technical_features": {
            "sma_20": 250.0,
            "rsi_14": 55.0
        },
        "sentiment_features": {
            "avg_sentiment": 0.25,
            "article_count": 5
        },
        "data_sources": {
            "technical": {"has_data": True},
            "sentiment": {"has_data": True}
        }
    }

    success = writer.write_snapshot(test_snapshot)
    print(f"\nSnapshot write success: {success}")

    # Test validation write
    test_validation = {
        "is_valid": True,
        "errors": [],
        "warnings": ["Test warning"],
        "checks_passed": 10,
        "checks_failed": 0
    }

    success = writer.write_validation(
        "TEST_2025-12-16_1.0.0",
        "TEST",
        date(2025, 12, 16),
        test_validation
    )
    print(f"Validation write success: {success}")

    # Get counts
    snapshot_count = writer.get_snapshot_count()
    print(f"\nTotal snapshots: {snapshot_count}")

    validation_summary = writer.get_validation_summary()
    print(f"Validation summary: {validation_summary}")

    writer.close()
