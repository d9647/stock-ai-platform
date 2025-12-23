"""
Market data models (OHLCV, technical indicators).
IMMUTABLE - records are never updated, only inserted.
"""
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..db.base import Base


class OHLCVPrice(Base):
    """
    Daily OHLCV price data (IMMUTABLE).
    One record per ticker per date.
    """
    __tablename__ = "ohlcv_prices"
    __table_args__ = (
        Index("idx_ohlcv_ticker_date", "ticker", "date"),
        Index("idx_ohlcv_date", "date"),
        CheckConstraint("open > 0", name="check_open_positive"),
        CheckConstraint("high > 0", name="check_high_positive"),
        CheckConstraint("low > 0", name="check_low_positive"),
        CheckConstraint("close > 0", name="check_close_positive"),
        CheckConstraint("volume >= 0", name="check_volume_non_negative"),
        {"schema": "market_data"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(Float)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<OHLCVPrice(ticker={self.ticker}, date={self.date}, close={self.close})>"


class TechnicalIndicator(Base):
    """
    Technical indicators computed from OHLCV data (IMMUTABLE).
    One record per ticker per date.
    """
    __tablename__ = "technical_indicators"
    __table_args__ = (
        Index("idx_technical_ticker_date", "ticker", "date"),
        Index("idx_technical_date", "date"),
        CheckConstraint("rsi_14 >= 0 AND rsi_14 <= 100", name="check_rsi_range"),
        CheckConstraint("atr_14 >= 0", name="check_atr_positive"),
        CheckConstraint("volatility_30d >= 0 AND volatility_30d <= 3.0", name="check_volatility_range"),
        {"schema": "market_data"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Moving Averages
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)

    # Momentum Indicators
    rsi_14 = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)

    # Volatility
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    atr_14 = Column(Float)

    # Volume Indicators
    obv = Column(Float)

    # Volatility Metrics
    volatility_30d = Column(Float)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<TechnicalIndicator(ticker={self.ticker}, date={self.date})>"
