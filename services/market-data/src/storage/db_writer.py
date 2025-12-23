"""
Write market data to PostgreSQL database.
Ensures immutability - only INSERT operations.
"""
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from loguru import logger
import pandas as pd

from api.app.models import OHLCVPrice, TechnicalIndicator, Stock
from ..config import config


class MarketDataWriter:
    """
    Writes market data to database with immutability guarantees.
    """

    def __init__(self, database_url: str = None):
        """Initialize database connection."""
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

        logger.info("Initialized market data writer")

    def write_stock_info(self, ticker: str, company_name: str, **kwargs) -> None:
        """
        Write or update stock company information.

        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            **kwargs: Additional fields (sector, industry, etc.)
        """
        try:
            # Check if stock exists
            existing = self.session.query(Stock).filter(Stock.ticker == ticker).first()

            if existing:
                # Update existing
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.company_name = company_name
                existing.updated_at = datetime.utcnow()
            else:
                # Insert new
                stock = Stock(
                    ticker=ticker,
                    company_name=company_name,
                    **kwargs
                )
                self.session.add(stock)

            self.session.commit()
            logger.info(f"Saved stock info for {ticker}")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving stock info for {ticker}: {e}")
            raise

    def write_ohlcv_batch(self, df: pd.DataFrame) -> int:
        """
        Write OHLCV data in batch (APPEND-ONLY).
        Uses INSERT ... ON CONFLICT DO NOTHING for idempotency.

        Args:
            df: DataFrame with columns: ticker, date, open, high, low, close, volume

        Returns:
            Number of records inserted
        """
        if df.empty:
            return 0

        try:
            records = []
            for _, row in df.iterrows():
                records.append({
                    "ticker": row["ticker"],
                    #"date": row["date"],
                    "date": pd.to_datetime(row["date"]).date(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": int(row["volume"]),
                    "adjusted_close": float(row.get("adjusted_close")) if pd.notna(row.get("adjusted_close")) else None,
                })
            logger.info(
                f"Prepared {len(records)} OHLCV rows "
                f"({records[0]['ticker']} {records[0]['date']} → "
                f"{records[-1]['date']})"
            )
            # Use INSERT ... ON CONFLICT DO NOTHING for idempotency
            stmt = insert(OHLCVPrice.__table__).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=["ticker", "date"])

            result = self.session.execute(stmt)
            self.session.commit()

            inserted = result.rowcount
            skipped = len(records) - inserted

            if inserted > 0:
                logger.info(f"Inserted {inserted} new OHLCV records")
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing OHLCV records (already in database)")

            return inserted

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing OHLCV data: {e}")
            raise

    def write_technical_indicators_batch(self, df: pd.DataFrame) -> int:
        """
        Write technical indicators in batch (APPEND-ONLY).

        Args:
            df: DataFrame with indicator columns

        Returns:
            Number of records inserted
        """
        if df.empty:
            return 0

        try:
            indicator_columns = [
                "sma_20", "sma_50", "sma_200", "ema_12", "ema_26",
                "rsi_14", "macd", "macd_signal", "macd_histogram",
                "bollinger_upper", "bollinger_middle", "bollinger_lower",
                "atr_14", "obv", "volatility_30d"
            ]

            records = []
            for idx, row in df.iterrows():
                record = {
                    "ticker": row["ticker"],
                    #"date": row["date"],
                    "date": pd.to_datetime(row["date"]).date(),
                }

                # Add ALL indicator columns (set to None if missing/NaN)
                # This ensures SQLAlchemy includes all columns in the INSERT
                for col in indicator_columns:
                    if col in row and pd.notna(row[col]):
                        record[col] = float(row[col])
                    else:
                        record[col] = None  # Explicitly set to None

                records.append(record)
            logger.info(
                f"Prepared {len(records)} OHLCV rows "
                f"({records[0]['ticker']} {records[0]['date']} → "
                f"{records[-1]['date']})"
            )
            # Use INSERT ... ON CONFLICT DO NOTHING
            stmt = insert(TechnicalIndicator.__table__).values(records)
            stmt = stmt.on_conflict_do_nothing(index_elements=["ticker", "date"])

            result = self.session.execute(stmt)
            self.session.commit()

            inserted = result.rowcount
            skipped = len(records) - inserted

            if inserted > 0:
                logger.info(f"Inserted {inserted} new technical indicator records")
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing technical indicator records (already in database)")

            return inserted

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing technical indicators: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()
        logger.info("Closed database connection")


if __name__ == "__main__":
    # Test the writer
    writer = MarketDataWriter()

    # Test stock info
    writer.write_stock_info(
        ticker="AAPL",
        company_name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics"
    )

    print("Stock info written successfully")
    writer.close()
