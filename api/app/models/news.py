"""
News and sentiment models (IMMUTABLE).
Historical news records are never modified.
"""
from sqlalchemy import (
    Column, String, Float, Integer, Date, DateTime, Text, ForeignKey, Index, CheckConstraint, ARRAY, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..db.base import Base


class NewsArticle(Base):
    """
    Historical news article (IMMUTABLE).
    Source of truth for all news data.
    """
    __tablename__ = "news_articles"
    __table_args__ = (
        Index("idx_news_ticker_published", "ticker", "published_at"),
        Index("idx_news_published", "published_at"),
        UniqueConstraint("ticker", "published_at", "headline", name="uq_news_article"),
        {"schema": "news"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)

    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    headline = Column(Text, nullable=False)
    content = Column(Text)
    source = Column(String(100), nullable=False)
    url = Column(Text)
    author = Column(String(255))

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<NewsArticle(ticker={self.ticker}, headline={self.headline[:50]}...)>"


class NewsSentimentScore(Base):
    """
    Sentiment analysis result for a news article (IMMUTABLE).
    One record per article.
    """
    __tablename__ = "news_sentiment_scores"
    __table_args__ = (
        Index("idx_sentiment_article", "article_id"),
        Index("idx_sentiment_ticker_published", "ticker", "published_at"),
        UniqueConstraint("article_id", name="uq_sentiment_article"),
        CheckConstraint("sentiment_score >= -1 AND sentiment_score <= 1", name="check_sentiment_range"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="check_confidence_range"),
        {"schema": "news"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("news.news_articles.id"), nullable=False)
    ticker = Column(String(10), nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=False)

    # Sentiment scores
    sentiment_score = Column(Float, nullable=False)  # -1 to +1
    confidence = Column(Float, nullable=False)  # 0 to 1

    # Extracted themes
    themes = Column(ARRAY(String), default=[])

    # Model metadata for reproducibility
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<NewsSentimentScore(ticker={self.ticker}, score={self.sentiment_score})>"


class DailySentimentAggregate(Base):
    """
    Aggregated daily sentiment for a ticker (IMMUTABLE).
    Point-in-time snapshot of sentiment on a specific date.
    """
    __tablename__ = "daily_sentiment_aggregates"
    __table_args__ = (
        Index("idx_daily_sentiment_ticker_date", "ticker", "date"),
        UniqueConstraint("ticker", "date", name="uq_daily_sentiment"),
        CheckConstraint("avg_sentiment >= -1 AND avg_sentiment <= 1", name="check_avg_sentiment_range"),
        CheckConstraint("weighted_sentiment >= -1 AND weighted_sentiment <= 1", name="check_weighted_sentiment_range"),
        CheckConstraint("article_count >= 0", name="check_article_count"),
        {"schema": "news"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Aggregated metrics
    avg_sentiment = Column(Float, nullable=False)
    weighted_sentiment = Column(Float, nullable=False)
    article_count = Column(Integer, nullable=False)

    # Top themes
    top_themes = Column(ARRAY(String), default=[])

    # Sentiment distribution
    positive_count = Column(Integer, nullable=False, default=0)
    neutral_count = Column(Integer, nullable=False, default=0)
    negative_count = Column(Integer, nullable=False, default=0)

    # Immutability tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<DailySentimentAggregate(ticker={self.ticker}, date={self.date}, sentiment={self.avg_sentiment})>"
