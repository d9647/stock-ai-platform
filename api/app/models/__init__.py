"""
SQLAlchemy models for Stock AI Platform.

IMMUTABILITY RULES:
- Market data, news, features, and agent outputs are APPEND-ONLY
- No UPDATE or DELETE operations on historical records
- Point-in-time correctness guaranteed
"""

from .stocks import Stock
from .market_data import OHLCVPrice, TechnicalIndicator
from .news import NewsArticle, NewsSentimentScore, DailySentimentAggregate
from .features import FeatureSnapshot, FeatureValidation
from .agents import AgentOutput, StockRecommendation, AgentExecutionLog
from .multiplayer import GameRoom, Player

__all__ = [
    "Stock",
    "OHLCVPrice",
    "TechnicalIndicator",
    "NewsArticle",
    "NewsSentimentScore",
    "DailySentimentAggregate",
    "FeatureSnapshot",
    "FeatureValidation",
    "AgentOutput",
    "StockRecommendation",
    "AgentExecutionLog",
    "GameRoom",
    "Player",
]
