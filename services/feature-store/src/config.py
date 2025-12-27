"""
Configuration for feature store service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Feature store service configuration."""

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://stockai:stockai@localhost:5432/stockai_dev"
    )

    # Data settings
    DEFAULT_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA"
    ]

    # Feature versioning
    FEATURE_VERSION = "1.0.0"

    # Validation thresholds
    VALIDATION_RULES = {
        # Technical indicators
        "rsi_14": {"min": 0, "max": 100, "required": True},
        "macd": {"required": False},  # Can be negative or positive
        "sma_20": {"min": 0, "required": True},
        "sma_50": {"min": 0, "required": True},
        "sma_200": {"min": 0, "required": True},
        "volatility_30d": {"min": 0, "max": 2.0, "required": False},  # Usually < 100%

        # Sentiment
        "avg_sentiment": {"min": -1, "max": 1, "required": False},
        "weighted_sentiment": {"min": -1, "max": 1, "required": False},
        "article_count": {"min": 0, "required": False},
    }

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
