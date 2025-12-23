"""
Pydantic schemas for game API end points.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date
from enum import Enum


# Define enums locally to avoid import issues
class RecommendationType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class SignalType(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"


class RiskLevel(str, Enum):
    LOW = "LOW_RISK"
    MEDIUM = "MEDIUM_RISK"
    HIGH = "HIGH_RISK"


class GamePrice(BaseModel):
    """OHLCV prices for a single ticker on a single day."""
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")


class GameRecommendation(BaseModel):
    """Simplified recommendation for game UI."""
    ticker: str = Field(..., description="Stock ticker symbol")
    recommendation: RecommendationType = Field(..., description="AI recommendation")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    technical_signal: SignalType = Field(..., description="Technical analysis signal")
    sentiment_signal: SignalType = Field(..., description="Sentiment analysis signal")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    rationale_summary: str = Field(..., description="Short explanation for students")
    rationale_risk_view: List[str] = Field(default_factory=list, description="Risk-related reasoning (bullet points)")
    rationale_technical_view: List[str] = Field(default_factory=list, description="Technical analysis reasoning (bullet points)")
    rationale_sentiment_view: List[str] = Field(default_factory=list, description="Sentiment analysis reasoning (bullet points)")
    as_of_date: str = Field(..., description="ISO date the AI used for analysis")


class NewsArticle(BaseModel):
    """News article for a ticker on a specific day."""
    ticker: str = Field(..., description="Stock ticker symbol")
    headline: str = Field(..., description="News headline")
    content: Optional[str] = Field(None, description="Article content/summary")
    source: str = Field(..., description="News source")
    published_at: str = Field(..., description="Publication timestamp")
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Sentiment score (-1 to +1)")
    url: Optional[str] = Field(None, description="Article URL")


class GameDayResponse(BaseModel):
    """Complete data for a single game day."""
    day: int = Field(..., description="Day number (0-indexed)")
    date: str = Field(..., description="ISO date string")
    is_trading_day: bool = Field(..., description="Whether markets are open (weekdays)")
    recommendations: List[GameRecommendation] = Field(..., description="AI recommendations for all tickers")
    prices: Dict[str, GamePrice] = Field(..., description="OHLC prices for all tickers")
    news: List[NewsArticle] = Field(default_factory=list, description="News articles for this day")


class GameDataResponse(BaseModel):
    """Complete game data for N days."""
    days: List[GameDayResponse] = Field(..., description="All game days")
    tickers: List[str] = Field(..., description="List of ticker symbols")
    start_date: str = Field(..., description="Game start date (ISO)")
    end_date: str = Field(..., description="Game end date (ISO)")
    total_days: int = Field(..., description="Total number of days")
