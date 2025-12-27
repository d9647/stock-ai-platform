"""
Configuration for news sentiment service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """News sentiment service configuration."""

    # API Keys
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

    # Historical data range (start small for development)
    HISTORICAL_DAYS = 30  # Start with 1 month to conserve free tier

    # API limits
    NEWSAPI_RATE_LIMIT = 100  # requests per day (free tier)
    FINNHUB_RATE_LIMIT = 60   # requests per minute (free tier)

    # Sentiment analysis
    SENTIMENT_MODEL = "gpt-4o-mini"  # Cost-effective for sentiment
    SENTIMENT_VERSION = "1.0.0"
    SENTIMENT_BATCH_SIZE = 10  # Process 10 articles per API call

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
