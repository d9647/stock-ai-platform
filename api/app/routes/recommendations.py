"""
Recommendation API end points - READ-ONLY.

CRITICAL RULES:
- NO LLM calls in these end points
- NO agent execution in request path
- Only read pre-computed recommendations from database
- All responses must be cacheable
"""
from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db import get_db
from ..models import StockRecommendation, OHLCVPrice
from ..schemas import (
    RecommendationResponse,
    RecommendationDetailResponse,
    RecommendationListResponse,
    HistoricalRecommendation,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=RecommendationListResponse)
def get_recommendations(
    as_of_date: Optional[date] = Query(None, description="Filter by recommendation date"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get list of stock recommendations (READ-ONLY).

    Returns pre-computed recommendations from database.
    No AI computation happens during this request.
    """
    query = db.query(StockRecommendation)

    # Filters
    if as_of_date:
        query = query.filter(StockRecommendation.as_of_date == as_of_date)
    if ticker:
        query = query.filter(StockRecommendation.ticker == ticker.upper())

    # Get total count
    total = query.count()

    # Pagination
    offset = (page - 1) * page_size
    recommendations = query.order_by(
        desc(StockRecommendation.as_of_date)
    ).offset(offset).limit(page_size).all()

    return RecommendationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        recommendations=[
            RecommendationResponse(
                ticker=rec.ticker,
                date=rec.as_of_date,
                recommendation=rec.recommendation,
                confidence=rec.confidence,
                position_size=rec.position_size,
                time_horizon=rec.time_horizon,
            )
            for rec in recommendations
        ]
    )


@router.get("/{ticker}", response_model=RecommendationDetailResponse)
def get_recommendation_detail(
    ticker: str,
    as_of_date: Optional[date] = Query(None, description="Specific date (default: latest)"),
    db: Session = Depends(get_db),
):
    """
    Get detailed recommendation for a specific ticker (READ-ONLY).

    Includes full explanation and supporting data.
    No AI computation - reads from pre-computed results.
    """
    query = db.query(StockRecommendation).filter(
        StockRecommendation.ticker == ticker.upper()
    )

    if as_of_date:
        query = query.filter(StockRecommendation.as_of_date == as_of_date)
    else:
        # Get most recent
        query = query.order_by(desc(StockRecommendation.as_of_date))

    recommendation = query.first()

    if not recommendation:
        raise HTTPException(
            status_code=404,
            detail=f"No recommendation found for {ticker}"
        )

    return RecommendationDetailResponse(
        ticker=recommendation.ticker,
        date=recommendation.as_of_date,
        recommendation=recommendation.recommendation,
        confidence=recommendation.confidence,
        technical_signal=recommendation.technical_signal,
        sentiment_signal=recommendation.sentiment_signal,
        risk_level=recommendation.risk_level,
        rationale=recommendation.rationale,
        position_size=recommendation.position_size,
        time_horizon=recommendation.time_horizon,
        model_version=recommendation.model_version,
        created_at=recommendation.created_at.isoformat(),
    )


@router.get("/{ticker}/history", response_model=List[HistoricalRecommendation])
def get_recommendation_history(
    ticker: str,
    limit: int = Query(30, ge=1, le=365, description="Number of historical records"),
    db: Session = Depends(get_db),
):
    """
    Get historical recommendations for a ticker (READ-ONLY).

    Useful for:
    - Backtesting simulation
    - Performance tracking
    - Trust building

    No AI computation - pure database read.
    """
    recommendations = db.query(StockRecommendation).filter(
        StockRecommendation.ticker == ticker.upper()
    ).order_by(
        desc(StockRecommendation.as_of_date)
    ).limit(limit).all()

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=f"No historical recommendations found for {ticker}"
        )

    # Fetch historical prices for performance calculation
    results = []
    for rec in recommendations:
        # Get price at recommendation date
        price_at_rec = db.query(OHLCVPrice).filter(
            OHLCVPrice.ticker == ticker.upper(),
            OHLCVPrice.date == rec.as_of_date
        ).first()

        # Get latest price
        latest_price = db.query(OHLCVPrice).filter(
            OHLCVPrice.ticker == ticker.upper()
        ).order_by(desc(OHLCVPrice.date)).first()

        # Calculate return
        return_pct = None
        if price_at_rec and latest_price:
            return_pct = (
                (latest_price.close - price_at_rec.close) / price_at_rec.close * 100
            )

        results.append(
            HistoricalRecommendation(
                ticker=rec.ticker,
                date=rec.as_of_date,
                recommendation=rec.recommendation,
                confidence=rec.confidence,
                price_at_recommendation=price_at_rec.close if price_at_rec else None,
                current_price=latest_price.close if latest_price else None,
                return_pct=return_pct,
            )
        )

    return results


@router.get("/today/top", response_model=List[RecommendationResponse])
def get_top_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of top recommendations"),
    as_of_date: Optional[date] = Query(None, description="Date (default: latest available)"),
    db: Session = Depends(get_db),
):
    """
    Get top recommendations for today/specified date (READ-ONLY).

    Sorted by confidence score.
    Useful for homepage "Today's Top Picks" feature.
    """
    query = db.query(StockRecommendation)

    if as_of_date:
        query = query.filter(StockRecommendation.as_of_date == as_of_date)
    else:
        # Get latest date available
        latest_date = db.query(StockRecommendation.as_of_date).order_by(
            desc(StockRecommendation.as_of_date)
        ).first()

        if latest_date:
            query = query.filter(StockRecommendation.as_of_date == latest_date[0])

    # Filter for BUY/STRONG_BUY and sort by confidence
    recommendations = query.filter(
        StockRecommendation.recommendation.in_(["BUY", "STRONG_BUY"])
    ).order_by(
        desc(StockRecommendation.confidence)
    ).limit(limit).all()

    return [
        RecommendationResponse(
            ticker=rec.ticker,
            date=rec.as_of_date,
            recommendation=rec.recommendation,
            confidence=rec.confidence,
            position_size=rec.position_size,
            time_horizon=rec.time_horizon,
        )
        for rec in recommendations
    ]
