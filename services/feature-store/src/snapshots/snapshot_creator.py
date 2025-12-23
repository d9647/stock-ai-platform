"""
Create point-in-time feature snapshots.
Combines technical indicators and sentiment data for a specific date.
"""
from datetime import date, datetime
from typing import Dict, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from api.app.models.market_data import TechnicalIndicator
from api.app.models.news import DailySentimentAggregate

# Import config with proper path handling
try:
    from ..config import config
except ImportError:
    from config import config


class SnapshotCreator:
    """
    Creates point-in-time feature snapshots.
    Ensures no look-ahead bias by only using data available as of the snapshot date.
    """

    def __init__(self, database_url: str = None):
        """Initialize snapshot creator."""
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()
        self.feature_version = config.FEATURE_VERSION

        logger.info("Initialized snapshot creator")

    def create_snapshot(
        self,
        ticker: str,
        as_of_date: date,
        snapshot_id: str = None
    ) -> Optional[Dict]:
        """
        Create a feature snapshot for a ticker as of a specific date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for point-in-time snapshot
            snapshot_id: Optional custom snapshot ID (default: {ticker}_{date}_{version})

        Returns:
            Dict with snapshot data, or None if insufficient data
        """
        # Generate snapshot_id if not provided
        if snapshot_id is None:
            snapshot_id = f"{ticker}_{as_of_date.isoformat()}_{self.feature_version}"

        logger.info(f"Creating snapshot: {snapshot_id}")

        # Fetch technical features
        technical_features = self._fetch_technical_features(ticker, as_of_date)

        # Fetch sentiment features
        sentiment_features = self._fetch_sentiment_features(ticker, as_of_date)

        # Track data sources for lineage
        data_sources = {
            "technical": {
                "table": "market_data.technical_indicators",
                "date": as_of_date.isoformat(),
                "has_data": technical_features is not None
            },
            "sentiment": {
                "table": "news.daily_sentiment_aggregates",
                "date": as_of_date.isoformat(),
                "has_data": sentiment_features is not None
            }
        }

        # Determine if we have enough data for a valid snapshot
        # At minimum, we need technical data
        if technical_features is None:
            logger.warning(
                f"No technical data for {ticker} on {as_of_date}, "
                f"cannot create snapshot"
            )
            return None

        # Build the complete snapshot
        snapshot = {
            "snapshot_id": snapshot_id,
            "ticker": ticker,
            "as_of_date": as_of_date,
            "feature_version": self.feature_version,
            "technical_features": technical_features,
            "sentiment_features": sentiment_features or {},  # Empty dict if no sentiment data
            "data_sources": data_sources
        }

        logger.info(
            f"Created snapshot {snapshot_id}: "
            f"technical={technical_features is not None}, "
            f"sentiment={sentiment_features is not None}"
        )

        return snapshot

    def _fetch_technical_features(
        self,
        ticker: str,
        as_of_date: date
    ) -> Optional[Dict]:
        """
        Fetch technical indicator features for a specific date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for features

        Returns:
            Dict with technical features, or None if not found
        """
        try:
            indicator = (
                self.session.query(TechnicalIndicator)
                .filter(
                    TechnicalIndicator.ticker == ticker,
                    TechnicalIndicator.date == as_of_date
                )
                .first()
            )

            if indicator is None:
                logger.debug(f"No technical indicators for {ticker} on {as_of_date}")
                return None

            # Extract all indicator columns
            features = {
                "sma_20": float(indicator.sma_20) if indicator.sma_20 is not None else None,
                "sma_50": float(indicator.sma_50) if indicator.sma_50 is not None else None,
                "sma_200": float(indicator.sma_200) if indicator.sma_200 is not None else None,
                "ema_12": float(indicator.ema_12) if indicator.ema_12 is not None else None,
                "ema_26": float(indicator.ema_26) if indicator.ema_26 is not None else None,
                "rsi_14": float(indicator.rsi_14) if indicator.rsi_14 is not None else None,
                "macd": float(indicator.macd) if indicator.macd is not None else None,
                "macd_signal": float(indicator.macd_signal) if indicator.macd_signal is not None else None,
                "macd_histogram": float(indicator.macd_histogram) if indicator.macd_histogram is not None else None,
                "bollinger_upper": float(indicator.bollinger_upper) if indicator.bollinger_upper is not None else None,
                "bollinger_middle": float(indicator.bollinger_middle) if indicator.bollinger_middle is not None else None,
                "bollinger_lower": float(indicator.bollinger_lower) if indicator.bollinger_lower is not None else None,
                "atr_14": float(indicator.atr_14) if indicator.atr_14 is not None else None,
                "obv": float(indicator.obv) if indicator.obv is not None else None,
                "volatility_30d": float(indicator.volatility_30d) if indicator.volatility_30d is not None else None,
            }

            return features

        except Exception as e:
            logger.error(f"Error fetching technical features: {e}")
            return None

    def _fetch_sentiment_features(
        self,
        ticker: str,
        as_of_date: date
    ) -> Optional[Dict]:
        """
        Fetch sentiment features for a specific date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for features

        Returns:
            Dict with sentiment features, or None if not found
        """
        try:
            aggregate = (
                self.session.query(DailySentimentAggregate)
                .filter(
                    DailySentimentAggregate.ticker == ticker,
                    DailySentimentAggregate.date == as_of_date
                )
                .first()
            )

            if aggregate is None:
                logger.debug(f"No sentiment data for {ticker} on {as_of_date}")
                return None

            # Extract sentiment metrics
            features = {
                "avg_sentiment": float(aggregate.avg_sentiment),
                "weighted_sentiment": float(aggregate.weighted_sentiment),
                "article_count": int(aggregate.article_count),
                "positive_count": int(aggregate.positive_count),
                "neutral_count": int(aggregate.neutral_count),
                "negative_count": int(aggregate.negative_count),
                "top_themes": aggregate.top_themes or []
            }

            return features

        except Exception as e:
            logger.error(f"Error fetching sentiment features: {e}")
            return None

    def close(self):
        """Close database session."""
        self.session.close()
        logger.info("Closed database connection")


if __name__ == "__main__":
    # Test snapshot creator
    from datetime import date

    creator = SnapshotCreator()

    # Create snapshot for AAPL on a recent date
    test_date = date(2025, 12, 14)
    snapshot = creator.create_snapshot("AAPL", test_date)

    if snapshot:
        print(f"\nSnapshot ID: {snapshot['snapshot_id']}")
        print(f"Ticker: {snapshot['ticker']}")
        print(f"As of date: {snapshot['as_of_date']}")
        print(f"\nTechnical features: {snapshot['technical_features']}")
        print(f"\nSentiment features: {snapshot['sentiment_features']}")
        print(f"\nData sources: {snapshot['data_sources']}")
    else:
        print("Could not create snapshot (insufficient data)")

    creator.close()
