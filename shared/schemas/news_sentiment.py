"""
News and sentiment analysis schemas.
Sentiment scores are probabilistic but stored immutably.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from .base import TimestampedSchema


class NewsArticle(TimestampedSchema):
    """
    Raw news article (immutable historical record).
    """

    ticker: str = Field(..., description="Related stock ticker")
    published_at: datetime = Field(..., description="Article publication timestamp")
    headline: str = Field(..., min_length=1, description="Article headline")
    content: Optional[str] = Field(None, description="Full article content")
    source: str = Field(..., description="News source")
    url: Optional[str] = Field(None, description="Article URL")
    author: Optional[str] = Field(None, description="Article author")

    model_config = ConfigDict(frozen=True)


class NewsSentiment(TimestampedSchema):
    """
    Sentiment analysis result for a news article.
    Immutable once computed.
    """

    article_id: str = Field(..., description="Reference to news article")
    ticker: str = Field(..., description="Stock ticker")
    published_at: datetime = Field(..., description="Article publication time")

    # Sentiment scores
    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment score: -1 (very negative) to +1 (very positive)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in sentiment score"
    )

    # Extracted themes
    themes: list[str] = Field(
        default_factory=list,
        description="Key themes/topics extracted from article"
    )

    # Model metadata
    model_name: str = Field(..., description="Model used for sentiment analysis")
    model_version: str = Field(..., description="Version of sentiment model")

    model_config = ConfigDict(frozen=True)


class DailySentimentAggregate(TimestampedSchema):
    """
    Aggregated sentiment for a ticker on a specific date.
    Point-in-time snapshot.
    """

    ticker: str = Field(..., description="Stock ticker")
    date: date = Field(..., description="Aggregation date")

    # Aggregated metrics
    avg_sentiment: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Average sentiment score for the day"
    )
    weighted_sentiment: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment weighted by article prominence/confidence"
    )
    article_count: int = Field(..., ge=0, description="Number of articles analyzed")

    # Top themes
    top_themes: list[str] = Field(
        default_factory=list,
        description="Most frequent themes for the day"
    )

    # Sentiment distribution
    positive_count: int = Field(..., ge=0, description="Count of positive articles")
    neutral_count: int = Field(..., ge=0, description="Count of neutral articles")
    negative_count: int = Field(..., ge=0, description="Count of negative articles")

    model_config = ConfigDict(frozen=True)


class NewsBatch(BaseModel):
    """Batch of news articles for processing."""

    ticker: str
    articles: list[NewsArticle]
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
