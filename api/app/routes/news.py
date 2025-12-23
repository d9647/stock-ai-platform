"""
News API end points for fetching news articles and sentiment data.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends

from ..db import get_db
from ..models.news import NewsArticle as NewsArticleModel, NewsSentimentScore
from ..schemas.game import NewsArticle

router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("/", response_model=List[NewsArticle])
async def get_news(
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of articles to return"),
    db: Session = Depends(get_db),
):
    """
    Get news articles with optional filters.

    Returns news articles with sentiment scores if available.
    """
    # Build query
    query = (
        db.query(NewsArticleModel, NewsSentimentScore)
        .join(
            NewsSentimentScore,
            NewsArticleModel.id == NewsSentimentScore.article_id,
            isouter=True
        )
    )

    # Apply filters
    if ticker:
        query = query.filter(NewsArticleModel.ticker == ticker.upper())

    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(func.date(NewsArticleModel.published_at) == filter_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(NewsArticleModel.published_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(NewsArticleModel.published_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )

    # Order by most recent first and apply limit
    query = query.order_by(NewsArticleModel.published_at.desc()).limit(limit)

    # Execute query
    results = query.all()

    # Build response
    news_list = []
    for article, sentiment in results:
        news_list.append(NewsArticle(
            ticker=article.ticker,
            headline=article.headline,
            content=article.content,
            source=article.source,
            published_at=article.published_at.isoformat(),
            sentiment_score=sentiment.sentiment_score if sentiment else None,
            url=article.url
        ))

    return news_list


@router.get("/tickers/{ticker}", response_model=List[NewsArticle])
async def get_news_by_ticker(
    ticker: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of articles to return"),
    db: Session = Depends(get_db),
):
    """
    Get latest news articles for a specific ticker.
    """
    query = (
        db.query(NewsArticleModel, NewsSentimentScore)
        .join(
            NewsSentimentScore,
            NewsArticleModel.id == NewsSentimentScore.article_id,
            isouter=True
        )
        .filter(NewsArticleModel.ticker == ticker.upper())
        .order_by(NewsArticleModel.published_at.desc())
        .limit(limit)
    )

    results = query.all()

    news_list = []
    for article, sentiment in results:
        news_list.append(NewsArticle(
            ticker=article.ticker,
            headline=article.headline,
            content=article.content,
            source=article.source,
            published_at=article.published_at.isoformat(),
            sentiment_score=sentiment.sentiment_score if sentiment else None,
            url=article.url
        ))

    return news_list


@router.get("/date/{date}", response_model=List[NewsArticle])
async def get_news_by_date(
    date: str,
    tickers: Optional[str] = Query(None, description="Comma-separated ticker symbols"),
    db: Session = Depends(get_db),
):
    """
    Get all news articles for a specific date.

    Optionally filter by tickers.
    """
    # Parse date
    try:
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )

    # Build query
    query = (
        db.query(NewsArticleModel, NewsSentimentScore)
        .join(
            NewsSentimentScore,
            NewsArticleModel.id == NewsSentimentScore.article_id,
            isouter=True
        )
        .filter(func.date(NewsArticleModel.published_at) == filter_date)
    )

    # Filter by tickers if provided
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        query = query.filter(NewsArticleModel.ticker.in_(ticker_list))

    # Order by most recent first
    query = query.order_by(NewsArticleModel.published_at.desc())

    results = query.all()

    news_list = []
    for article, sentiment in results:
        news_list.append(NewsArticle(
            ticker=article.ticker,
            headline=article.headline,
            content=article.content,
            source=article.source,
            published_at=article.published_at.isoformat(),
            sentiment_score=sentiment.sentiment_score if sentiment else None,
            url=article.url
        ))

    return news_list
