"""
Market data schemas (OHLCV, technical indicators).
These schemas represent deterministic, immutable market data.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from .base import TimestampedSchema


class OHLCVData(TimestampedSchema):
    """
    Daily OHLCV (Open, High, Low, Close, Volume) data.
    Immutable once recorded.
    """

    ticker: str = Field(..., description="Stock ticker symbol")
    date: date = Field(..., description="Trading date")
    open: float = Field(..., gt=0, description="Opening price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")
    adjusted_close: Optional[float] = Field(None, description="Adjusted closing price")

    model_config = ConfigDict(frozen=True)


class TechnicalIndicators(TimestampedSchema):
    """
    Technical indicators computed from OHLCV data.
    Deterministic and reproducible.
    """

    ticker: str = Field(..., description="Stock ticker symbol")
    date: date = Field(..., description="Calculation date")

    # Moving Averages
    sma_20: Optional[float] = Field(None, description="20-day Simple Moving Average")
    sma_50: Optional[float] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[float] = Field(None, description="200-day Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-day Exponential Moving Average")
    ema_26: Optional[float] = Field(None, description="26-day Exponential Moving Average")

    # Momentum Indicators
    rsi_14: Optional[float] = Field(None, ge=0, le=100, description="14-day Relative Strength Index")
    macd: Optional[float] = Field(None, description="MACD (12, 26, 9)")
    macd_signal: Optional[float] = Field(None, description="MACD Signal Line")
    macd_histogram: Optional[float] = Field(None, description="MACD Histogram")

    # Volatility
    bollinger_upper: Optional[float] = Field(None, description="Bollinger Band Upper")
    bollinger_middle: Optional[float] = Field(None, description="Bollinger Band Middle")
    bollinger_lower: Optional[float] = Field(None, description="Bollinger Band Lower")
    atr_14: Optional[float] = Field(None, ge=0, description="14-day Average True Range")

    # Volume Indicators
    obv: Optional[float] = Field(None, description="On-Balance Volume")

    # Volatility Metrics
    volatility_30d: Optional[float] = Field(None, ge=0, le=1, description="30-day historical volatility")

    model_config = ConfigDict(frozen=True)


class StockInfo(BaseModel):
    """Stock company information (mostly static)."""

    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Industry sector")
    industry: Optional[str] = Field(None, description="Industry")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    description: Optional[str] = Field(None, description="Company description")

    model_config = ConfigDict(frozen=False)  # Can be updated


class MarketDataBatch(BaseModel):
    """Batch of market data for efficient processing."""

    ticker: str
    ohlcv_records: list[OHLCVData]
    technical_indicators: list[TechnicalIndicators]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
