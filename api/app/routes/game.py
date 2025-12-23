"""
Game API end points for educational stock challenge.
Returns precomputed data for N days to enable deterministic gameplay.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends

from ..db import get_db
from ..models.agents import StockRecommendation
from ..models.market_data import OHLCVPrice
from ..models.news import NewsArticle as NewsArticleModel, NewsSentimentScore
from ..schemas.game import GameDataResponse, GameDayResponse, GameRecommendation, GamePrice, NewsArticle

router = APIRouter(prefix="/api/v1/game", tags=["game"])


def is_trading_day(check_date: date) -> bool:
    """
    Check if a date is a trading day (Monday-Friday).
    Does not account for market holidays.
    """
    return check_date.weekday() < 5  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday


def get_last_trading_day_prices(
    current_date: date,
    db: Session,
    ticker_list: List[str]
) -> Optional[Dict[str, GamePrice]]:
    """
    Find the most recent trading day before current_date that has complete price data.
    Returns prices dict for carryover to weekends.
    """
    search_date = current_date - timedelta(days=1)
    max_lookback = 7  # Don't look back more than a week

    for _ in range(max_lookback):
        if search_date.weekday() < 5:  # Is a weekday
            # Check if we have complete data for this date
            prices = db.query(OHLCVPrice).filter(
                OHLCVPrice.ticker.in_(ticker_list),
                OHLCVPrice.date == search_date
            ).all()

            if len(prices) == len(ticker_list):
                # Build prices dict
                price_dict = {}
                for price in prices:
                    # For weekends, carry forward Friday's close as all OHLC values
                    price_dict[price.ticker] = GamePrice(
                        open=float(price.close),   # Weekend open = Friday close
                        high=float(price.close),   # Weekend high = Friday close
                        low=float(price.close),    # Weekend low = Friday close
                        close=float(price.close),  # Weekend close = Friday close
                        volume=0                   # No volume on weekends
                    )
                return price_dict

        search_date -= timedelta(days=1)

    return None


@router.get("/data", response_model=GameDataResponse)
async def get_game_data(
    days: int = Query(30, ge=1, le=90, description="Number of calendar days"),
    tickers: Optional[str] = Query(
        None,
        description="Comma-separated ticker symbols (default: AAPL,MSFT,GOOGL,AMZN)"
    ),
    start_date: Optional[str] = Query(
        None,
        description="Start date (YYYY-MM-DD), takes precedence over days parameter if provided"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date (YYYY-MM-DD), defaults to latest available data"
    ),
):
    """
    Get complete game data for N calendar days (including weekends).

    Weekend days will:
    - Carry forward Friday's closing prices
    - Include weekend news articles (if available)
    - Set is_trading_day=False
    """
    # Parse tickers
    ticker_list = tickers.split(",") if tickers else ["AAPL", "MSFT", "GOOGL", "AMZN"]
    ticker_list = [t.strip().upper() for t in ticker_list]

    # Parse start date if provided
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    else:
        start_dt = None

    # Parse end date or use latest
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    else:
        # Find latest date with data (must be a weekday)
        db = next(get_db())
        latest_rec = db.query(StockRecommendation).order_by(
            StockRecommendation.as_of_date.desc()
        ).first()
        if not latest_rec:
            raise HTTPException(
                status_code=404,
                detail="No recommendation data available"
            )
        end_dt = latest_rec.as_of_date

    # Calculate start date and days
    # If start_date is provided, use it and calculate days from start to end
    # Otherwise, calculate start from end_date - days
    if start_dt:
        days = (end_dt - start_dt).days + 1  # +1 to include both start and end dates
        if days < 1 or days > 90:
            raise HTTPException(
                status_code=400,
                detail=f"Date range must be between 1 and 90 days (got {days} days)"
            )
    else:
        # Calculate start date (N calendar days, not trading days)
        start_dt = end_dt - timedelta(days=days - 1)

    # Fetch all data from database
    db = next(get_db())

    game_days: List[GameDayResponse] = []
    last_valid_prices: Optional[Dict[str, GamePrice]] = None  # Track for weekend carryover

    for day_offset in range(days):
        current_date = start_dt + timedelta(days=day_offset)
        is_trading = is_trading_day(current_date)

        # Always fetch news for this day (even weekends may have news)
        news_articles = (
            db.query(NewsArticleModel, NewsSentimentScore)
            .join(
                NewsSentimentScore,
                NewsArticleModel.id == NewsSentimentScore.article_id,
                isouter=True
            )
            .filter(
                NewsArticleModel.ticker.in_(ticker_list),
                func.date(NewsArticleModel.published_at) == current_date
            )
            .order_by(NewsArticleModel.published_at.desc())
            .limit(10)
            .all()
        )

        if is_trading:
            # TRADING DAY: Get real recommendations and prices
            recommendations = (
                db.query(StockRecommendation)
                .filter(
                    StockRecommendation.ticker.in_(ticker_list),
                    StockRecommendation.as_of_date == current_date
                )
                .all()
            )

            prices = (
                db.query(OHLCVPrice)
                .filter(
                    OHLCVPrice.ticker.in_(ticker_list),
                    OHLCVPrice.date == current_date
                )
                .all()
            )

            # Skip if incomplete data on a trading day
            if len(recommendations) < len(ticker_list) or len(prices) < len(ticker_list):
                # fallback to HOLD with last known prices
                is_trading = False

            # Build recommendations list
            recs = []
            for rec in recommendations:
                recs.append(GameRecommendation(
                    ticker=rec.ticker,
                    recommendation=rec.recommendation,
                    confidence=rec.confidence,
                    technical_signal=rec.technical_signal,
                    sentiment_signal=rec.sentiment_signal,
                    risk_level=rec.risk_level,
                    rationale_summary=rec.rationale.get("summary", [""])[0] if rec.rationale else "",
                    rationale_risk_view=rec.rationale.get("risk_view", [""]) if rec.rationale else "",
                    rationale_technical_view=rec.rationale.get("sentiment_view", [""]) if rec.rationale else "",
                    rationale_sentiment_view=rec.rationale.get("technical_view", [""]) if rec.rationale else "",
                    as_of_date=rec.as_of_date.isoformat()
                ))

            # Build prices dict
            price_dict = {}
            for price in prices:
                price_dict[price.ticker] = GamePrice(
                    open=float(price.open),
                    high=float(price.high),
                    low=float(price.low),
                    close=float(price.close),
                    volume=price.volume
                )

            # Cache prices for weekend carryover
            last_valid_prices = price_dict

        else:
            # WEEKEND/NON-TRADING DAY: Carry forward prices and create HOLD recommendations
            if last_valid_prices is None:
                # If we haven't seen a trading day yet, try to find previous prices
                last_valid_prices = get_last_trading_day_prices(current_date, db, ticker_list)
                if last_valid_prices is None:
                    continue  # Skip this weekend day if no previous data

            # Create HOLD recommendations for all tickers
            recs = []
            for ticker in ticker_list:
                recs.append(GameRecommendation(
                    ticker=ticker,
                    recommendation="HOLD",
                    confidence=1.0,
                    technical_signal="NEUTRAL",
                    sentiment_signal="NEUTRAL",
                    risk_level="LOW_RISK",
                    rationale_summary="Markets are closed. No trading available.",
                    rationale_risk_view=[],
                    rationale_technical_view=[],
                    rationale_sentiment_view=[],
                    as_of_date=current_date.isoformat()  # Use current weekend date
                ))

            # Use carried-forward prices
            price_dict = last_valid_prices

        # Build news articles list (same for both trading and non-trading days)
        news_list = []
        for article, sentiment in news_articles:
            news_list.append(NewsArticle(
                ticker=article.ticker,
                headline=article.headline,
                content=article.content,
                source=article.source,
                published_at=article.published_at.isoformat(),
                sentiment_score=sentiment.sentiment_score if sentiment else None,
                url=article.url
            ))

        game_days.append(GameDayResponse(
            day=len(game_days),  # 0-indexed
            date=current_date.isoformat(),
            is_trading_day=is_trading,
            recommendations=recs,
            prices=price_dict,
            news=news_list
        ))

    if len(game_days) < 10:  # Need at least 10 days for a meaningful game
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient data. Found only {len(game_days)} days with complete data. Need at least 10 days."
        )

    return GameDataResponse(
        days=game_days,
        tickers=ticker_list,
        start_date=game_days[0].date,
        end_date=game_days[-1].date,
        total_days=len(game_days)
    )
