"""
Read feature snapshots from database.
"""
from typing import Optional, Dict, Any
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Import models from API
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from api.app.models.features import FeatureSnapshot

from ..config import config


class FeatureSnapshotReader:
    """
    Read feature snapshots from database.
    Agents consume ONLY feature snapshots (never raw tables).
    """

    def __init__(self, database_url: str = None):
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

        logger.info("Initialized feature snapshot reader")

    def get_snapshot(
        self,
        ticker: str,
        as_of_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get feature snapshot for ticker and date.

        Returns:
            Snapshot dict or None if not found
        """
        try:
            snapshot = (
                self.session.query(FeatureSnapshot)
                .filter(
                    FeatureSnapshot.ticker == ticker,
                    FeatureSnapshot.as_of_date == as_of_date
                )
                .first()
            )

            if not snapshot:
                logger.warning(f"No snapshot found for {ticker} on {as_of_date}")
                return None

            # Unpack JSONB data
            snapshot_dict = {
                "snapshot_id": snapshot.snapshot_id,
                "ticker": snapshot.ticker,
                "as_of_date": snapshot.as_of_date,
                "feature_version": snapshot.feature_version,
                **snapshot.snapshot_data  # Unpack JSONB column
            }

            logger.info(f"Retrieved snapshot: {snapshot.snapshot_id}")
            return snapshot_dict

        except Exception as e:
            logger.error(f"Error retrieving snapshot: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()
