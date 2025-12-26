"""
Fetch news articles from Finnhub and NewsAPI.
Priority: Finnhub for better financial coverage.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Set, Tuple
import time

import pandas as pd
import finnhub
from newsapi import NewsApiClient
from loguru import logger

from ..config import config


class NewsFetcher:
    """
    Fetches news articles from Finnhub (primary) and NewsAPI (backup).
    Returns deterministic, reproducible results.
    """

    def __init__(self):
        """Initialize API clients."""
        # Finnhub (primary)
        self.finnhub_client = finnhub.Client(api_key=config.FINNHUB_API_KEY)

        # NewsAPI (backup)
        self.newsapi_client = NewsApiClient(api_key=config.NEWSAPI_KEY) if config.NEWSAPI_KEY else None

        logger.info("Initialized news fetcher (Finnhub priority)")

    def fetch_historical_news(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        existing_urls: "set[tuple[str, str]] | None" = None,  # (ticker, url)
        existing_keys: "set[tuple[str, str, datetime]] | None" = None,  # (ticker, headline, dt)
    ) -> pd.DataFrame:
        """
        Fetch historical news for a ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with columns: [ticker, published_at, headline, content, source, url, author]
        """
        logger.info(f"Fetching news for {ticker} from {start_date.date()} to {end_date.date()}")

        # Try Finnhub first
        try:
            articles = self._fetch_from_finnhub(
                ticker, start_date, end_date, existing_urls, existing_keys
            )
            if articles:
                logger.info(f"Fetched {len(articles)} articles from Finnhub for {ticker}")
                return self._articles_to_dataframe(articles, ticker)
        except Exception as e:
            logger.warning(f"Finnhub fetch failed for {ticker}: {e}")

        # Fallback to NewsAPI if Finnhub fails
        if self.newsapi_client:
            try:
                articles = self._fetch_from_newsapi(
                    ticker, start_date, end_date, existing_urls, existing_keys
                )
                if articles:
                    logger.info(f"Fetched {len(articles)} articles from NewsAPI for {ticker}")
                    return self._articles_to_dataframe(articles, ticker)
            except Exception as e:
                logger.warning(f"NewsAPI fetch failed for {ticker}: {e}")

        logger.warning(f"No articles found for {ticker}")
        return pd.DataFrame()

    def _fetch_from_finnhub(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        existing_urls: "set[str] | None" = None,
        existing_keys: "set[tuple[str, datetime]] | None" = None,
    ) -> List[dict]:
        """
        Fetch from Finnhub API.

        Finnhub has a limit of ~250 articles per API call, so we chunk
        the date range into 10-day periods to ensure we get all articles
        for longer historical periods (e.g., 365 days).

        Based on real data: AAPL has ~250 articles per 13 days, so 10-day
        chunks ensure we stay safely under the limit for all tickers.

        Finnhub API docs: https://finnhub.io/docs/api/company-news
        """
        articles = []

        # Calculate number of days in the range
        total_days = (end_date - start_date).days

        # Finnhub returns max 250 articles per call
        # For high-volume tickers (AAPL, TSLA, etc), 250 articles ≈ 10-14 days
        # To be safe, we chunk at 10 days to ensure we never hit the limit
        chunk_size_days = 10

        if total_days <= chunk_size_days:
            # Single request for small ranges
            chunks = [(start_date, end_date)]
        else:
            # Split into 10-day chunks for large ranges
            # This ensures even high-volume tickers stay under 250 articles/call
            chunks = []
            current_start = start_date

            # Safety limit to prevent infinite loops
            max_chunks = 1000
            chunk_count = 0

            while current_start < end_date and chunk_count < max_chunks:
                current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
                chunks.append((current_start, current_end))
                # Move to next day to avoid overlap (Finnhub date range is inclusive on both ends)
                current_start = current_end + timedelta(days=1)
                chunk_count += 1

            if chunk_count >= max_chunks:
                logger.error(f"Hit maximum chunk limit ({max_chunks}). Check date range logic.")
                raise ValueError(f"Too many chunks generated for date range {start_date} to {end_date}")

        logger.info(f"Fetching Finnhub data for {ticker} in {len(chunks)} chunk(s)")

        try:
            for chunk_num, (chunk_start, chunk_end) in enumerate(chunks, 1):
                # Convert dates to YYYY-MM-DD format
                from_date = chunk_start.strftime("%Y-%m-%d")
                to_date = chunk_end.strftime("%Y-%m-%d")

                logger.debug(
                    f"  Chunk {chunk_num}/{len(chunks)}: "
                    f"{from_date} to {to_date}"
                )

                # Finnhub company news endpoint
                news = self.finnhub_client.company_news(ticker, _from=from_date, to=to_date)

                for item in news:
                    # Skip articles with invalid/missing datetime
                    dt = item.get("datetime")
                    if dt is None or dt == 0:
                        logger.warning(f"Skipping article with invalid datetime: {item.get('headline', 'Unknown')}")
                        continue

                    try:
                        published_at = datetime.fromtimestamp(dt)
                    except (ValueError, OSError, OverflowError) as e:
                        logger.warning(f"Invalid timestamp {dt} for article: {item.get('headline', 'Unknown')} - {e}")
                        continue

                    headline = item.get("headline", "")
                    url = item.get("url", "")

                    # Skip if already seen for this ticker
                    norm_ts = (
                        published_at
                        if published_at.tzinfo
                        else published_at.replace(tzinfo=timezone.utc)
                    )
                    if existing_urls and url and (ticker, url) in existing_urls:
                        continue
                    if existing_keys and (ticker, headline, norm_ts) in existing_keys:
                        continue

                    articles.append({
                        "published_at": published_at,
                        "headline": headline,
                        "content": item.get("summary", ""),  # Finnhub provides summary
                        "source": item.get("source", "Finnhub"),
                        "url": url,
                        "author": item.get("author", "")
                    })

                # Rate limiting (60 calls/minute for free tier)
                # 1 second between calls = 60 calls/minute
                time.sleep(1)

            logger.info(f"Fetched total of {len(articles)} articles for {ticker} across all chunks")

        except Exception as e:
            logger.error(f"Error fetching from Finnhub: {e}")
            raise

        return articles

    def _fetch_from_newsapi(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        existing_urls: "set[tuple[str, str]] | None" = None,
        existing_keys: "set[tuple[str, str, datetime]] | None" = None,
    ) -> List[dict]:
        """
        Fetch from NewsAPI (backup).

        NewsAPI docs: https://newsapi.org/docs/end points/everything
        Note: Free tier only allows 1 month of historical data
        """
        articles = []

        # NewsAPI free tier limit: only last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        if start_date < thirty_days_ago:
            logger.warning(f"NewsAPI free tier: adjusting start_date to last 30 days")
            start_date = thirty_days_ago

        try:
            # Search query: ticker symbol and related terms
            query = f"{ticker} OR {self._get_company_name(ticker)}"

            response = self.newsapi_client.get_everything(
                q=query,
                from_param=start_date.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d"),
                language="en",
                sort_by="publishedAt",
                page_size=100  # Max 100 articles per request
            )

            if response.get("status") == "ok":
                for item in response.get("articles", []):
                    published_at = datetime.strptime(
                        item.get("publishedAt", ""),
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
                    headline = item.get("title", "")
                    url = item.get("url", "")

                    norm_ts = (
                        published_at
                        if published_at.tzinfo
                        else published_at.replace(tzinfo=timezone.utc)
                    )

                    if existing_urls and url and (ticker, url) in existing_urls:
                        continue
                    if existing_keys and (ticker, headline, norm_ts) in existing_keys:
                        continue

                    articles.append({
                        "published_at": published_at,
                        "headline": headline,
                        "content": item.get("description", "") or item.get("content", ""),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "url": url,
                        "author": item.get("author", "")
                    })

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            raise

        return articles

    def _articles_to_dataframe(self, articles: List[dict], ticker: str) -> pd.DataFrame:
        """
        Convert articles list to DataFrame with required schema.

        Args:
            articles: List of article dictionaries
            ticker: Stock ticker symbol

        Returns:
            DataFrame with columns: [ticker, published_at, headline, content, source, url, author]
        """
        if not articles:
            return pd.DataFrame()

        # Add ticker to each article
        for article in articles:
            article["ticker"] = ticker

        # Create DataFrame
        df = pd.DataFrame(articles)

        # Ensure required columns
        required_columns = ["ticker", "published_at", "headline", "content", "source", "url", "author"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Sort by published_at (deterministic)
        df = df.sort_values("published_at").reset_index(drop=True)

        # Remove duplicates (same headline + published_at)
        df = df.drop_duplicates(subset=["ticker", "headline", "published_at"])

        logger.info(f"Prepared {len(df)} articles for {ticker}")

        return df[required_columns]

    def _get_company_name(self, ticker: str) -> str:
        """
        Get company name from ticker for better news search.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company name
        """
        # Simple mapping for common tickers
        ticker_to_company = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google Alphabet",
            "AMZN": "Amazon",
            "NVDA": "NVIDIA",
            "META": "Meta Facebook",
            "TSLA": "Tesla"
        }

        return ticker_to_company.get(ticker, ticker)


if __name__ == "__main__":
    # Test fetcher
    fetcher = NewsFetcher()

    # Fetch last 7 days for AAPL
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    df = fetcher.fetch_historical_news("AAPL", start_date, end_date)

    print(f"\\nFetched {len(df)} articles for AAPL")
    print(df.head())
