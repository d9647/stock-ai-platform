"""
API response schemas for recommendations.
These are read-only schemas - API never creates recommendations.
"""
from datetime import date as DateType
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    """
    Public-facing recommendation response.
    Simplified version of StockRecommendation model.
    """

    ticker: str = Field(..., description="Stock ticker symbol")
    date: DateType = Field(..., description="Recommendation date")
    recommendation: str = Field(..., description="BUY, HOLD, SELL, etc.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    position_size: str = Field(..., description="Position sizing recommendation")
    time_horizon: str = Field(..., description="Suggested holding period")

    class Config:
        from_attributes = True


class RecommendationDetailResponse(BaseModel):
    """
    Detailed recommendation with full explanation.
    """

    ticker: str
    date: DateType
    recommendation: str
    confidence: float

    # Signals from individual agents
    technical_signal: str
    sentiment_signal: str
    risk_level: str

    # Structured explanation
    rationale: Dict[str, List[str]] = Field(
        ...,
        description="Explanation broken down by: technical, sentiment, risk"
    )

    # Position sizing
    position_size: str
    time_horizon: str

    # Metadata
    model_version: str = Field(..., description="AI model version used")
    created_at: str = Field(..., description="When this recommendation was created")

    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Paginated list of recommendations."""

    total: int
    page: int
    page_size: int
    recommendations: List[RecommendationResponse]


class HistoricalRecommendation(BaseModel):
    """Historical recommendation with performance data."""

    ticker: str
    date: DateType
    recommendation: str
    confidence: float

    # Performance (if available)
    price_at_recommendation: Optional[float] = None
    current_price: Optional[float] = None
    return_pct: Optional[float] = None

    class Config:
        from_attributes = True
