"""
Shared schemas for the Stock AI Platform.
All schemas are immutable (frozen=True) to ensure data integrity.
"""

from .base import (
    TimestampedSchema,
    StockSymbol,
    DateRange,
    Recommendation,
    Signal,
    RiskLevel,
    PositionSize,
)
from .market_data import (
    OHLCVData,
    TechnicalIndicators,
    StockInfo,
    MarketDataBatch,
)
from .news_sentiment import (
    NewsArticle,
    NewsSentiment,
    DailySentimentAggregate,
    NewsBatch,
)
from .feature_store import (
    FeatureSnapshot,
    FeatureSnapshotMetadata,
    FeatureValidation,
    FeatureQuery,
    FeatureBatch,
)
from .agents import (
    AgentOutput,
    TechnicalAgentOutput,
    SentimentAgentOutput,
    RiskAgentOutput,
    StockRecommendation,
    AgentExecutionLog,
)

__all__ = [
    # Base
    "TimestampedSchema",
    "StockSymbol",
    "DateRange",
    "Recommendation",
    "Signal",
    "RiskLevel",
    "PositionSize",
    # Market Data
    "OHLCVData",
    "TechnicalIndicators",
    "StockInfo",
    "MarketDataBatch",
    # News & Sentiment
    "NewsArticle",
    "NewsSentiment",
    "DailySentimentAggregate",
    "NewsBatch",
    # Feature Store
    "FeatureSnapshot",
    "FeatureSnapshotMetadata",
    "FeatureValidation",
    "FeatureQuery",
    "FeatureBatch",
    # Agents
    "AgentOutput",
    "TechnicalAgentOutput",
    "SentimentAgentOutput",
    "RiskAgentOutput",
    "StockRecommendation",
    "AgentExecutionLog",
]
