"""
Configuration for market data service.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Market data service configuration."""

    # API Keys
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://stockai:stockai@192.168.5.126:5432/stockai_dev"
    )

    # Data settings
    DEFAULT_TICKERS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA"
        #"WMT", "YELP"
    ]

    # Historical data range (how far back to fetch)
    HISTORICAL_YEARS = 2  # Fetch 2 years of historical data

    # Polygon API limits
    POLYGON_RATE_LIMIT = 5  # requests per minute (free tier)
    POLYGON_BATCH_SIZE = 100  # max tickers per batch

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
