"""
Fetch historical price data from Polygon.io.
Deterministic and reproducible.
"""
from datetime import datetime, timedelta
from typing import List, Optional
import time

from polygon import RESTClient
from loguru import logger
import pandas as pd

from ..config import config


class PolygonPriceFetcher:
    """
    Fetches OHLCV data from Polygon.io.
    Handles rate limiting and retries.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Polygon client."""
        self.api_key = api_key or config.POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment")

        self.client = RESTClient(self.api_key)
        logger.info("Initialized Polygon price fetcher")

    def fetch_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        timespan: str = "day"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            timespan: Timespan for aggregation (day, hour, minute)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        logger.info(f"Fetching prices for {ticker} from {start_date} to {end_date}")

        try:
            # Convert dates to strings (Polygon expects YYYY-MM-DD)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Fetch aggregates from Polygon
            aggs = []
            for agg in self.client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan=timespan,
                from_=start_str,
                to=end_str,
                limit=50000  # Max limit
            ):
                aggs.append({
                    "date": datetime.utcfromtimestamp(agg.timestamp / 1000).date(),
                    "open": agg.open,
                    "high": agg.high,
                    "low": agg.low,
                    "close": agg.close,
                    "volume": agg.volume,
                })

            if not aggs:
                logger.warning(f"No data found for {ticker}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(aggs)
            df["ticker"] = ticker
            df = df.sort_values("date").reset_index(drop=True)

            logger.info(f"Fetched {len(df)} price records for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Error fetching prices for {ticker}: {e}")
            raise

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Fetch prices for multiple tickers (with rate limiting).

        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date

        Returns:
            Combined DataFrame for all tickers
        """
        all_data = []

        for i, ticker in enumerate(tickers):
            try:
                df = self.fetch_historical_prices(ticker, start_date, end_date)
                if not df.empty:
                    all_data.append(df)

                # Rate limiting (free tier: 5 requests/minute)
                if (i + 1) % config.POLYGON_RATE_LIMIT == 0:
                    logger.info("Rate limit reached, sleeping for 60 seconds...")
                    time.sleep(60)

            except Exception as e:
                logger.error(f"Failed to fetch {ticker}: {e}")
                continue

        if not all_data:
            return pd.DataFrame()

        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.info(f"Fetched total {len(combined_df)} records for {len(tickers)} tickers")

        return combined_df

    def fetch_latest_price(self, ticker: str) -> Optional[dict]:
        """
        Fetch the most recent price for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with latest price data or None
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Last week

            df = self.fetch_historical_prices(ticker, start_date, end_date)
            if df.empty:
                return None

            latest = df.iloc[-1].to_dict()
            return latest

        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {e}")
            return None


if __name__ == "__main__":
    # Test the fetcher
    fetcher = PolygonPriceFetcher()

    # Fetch last 30 days for AAPL
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    df = fetcher.fetch_historical_prices("AAPL", start_date, end_date)
    print(df.head())
    print(f"\nFetched {len(df)} records")
