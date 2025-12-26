"""
Daily news sentiment pipeline.
Fetches news, analyzes sentiment, aggregates daily scores, and stores to database.

This script is designed to run OFFLINE (scheduled, not in API requests).
"""
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from loguru import logger
import pandas as pd

from ..ingestion.fetch_news import NewsFetcher
from ..processing.sentiment_scoring import SentimentScorer
from ..processing.aggregation import SentimentAggregator
from ..storage.db_writer import NewsDataWriter
from ..config import config
from ..ingestion.news_cache import NewsSeenCache


class DailyNewsSentimentPipeline:
    """
    End-to-end pipeline for news sentiment analysis.
    Runs offline, populates database for API consumption.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.fetcher = NewsFetcher()
        self.scorer = SentimentScorer()
        self.aggregator = SentimentAggregator()
        self.writer = NewsDataWriter()
        # Use src/ingestion/data/news_cache relative to this file
        cache_dir = Path(__file__).resolve().parents[1] / "ingestion" / "data" / "news_cache"
        self.cache_dir = cache_dir
        # Cache will be initialized per-ticker inside run_for_ticker
        self.cache = None
        self.existing_urls = set()
        self.existing_keys = set()

        logger.info("Initialized daily news sentiment pipeline")

    def run_for_ticker(
        self,
        ticker: str,
        start_date: datetime = None,
        end_date: datetime = None,
        skip_sentiment: bool = False,
        forward_only: bool = False,
    ) -> dict:
        """
        Run complete pipeline for a single ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (default: HISTORICAL_DAYS ago)
            end_date: End date (default: today)

        Returns:
            Dict with pipeline statistics
        """
        # Default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=config.HISTORICAL_DAYS)

        logger.info(f"Running pipeline for {ticker} from {start_date.date()} to {end_date.date()}")

        try:
            # Initialize ticker-specific cache
            self.cache = NewsSeenCache(self.cache_dir, ticker)
            self.existing_urls, self.existing_keys = self.cache.load()

            # Load existing article keys from DB to avoid reprocessing
            logger.info(f"[{ticker}] Loading existing article keys from DB...")
            existing_article_mapping = self.writer.get_article_ids_for_ticker(ticker)
            scored_article_mapping = self.writer.get_scored_article_keys_for_ticker(ticker)
            def _norm_db_ts(ts):
                ts = pd.to_datetime(ts)
                if ts.tzinfo is None:
                    ts = ts.tz_localize('UTC')
                else:
                    ts = ts.tz_convert('UTC')
                return ts

            existing_article_keys_db = {
                (ticker_db, headline, _norm_db_ts(published_at))
                for (ticker_db, published_at, headline) in existing_article_mapping.keys()
            }
            scored_article_keys_db = {
                (ticker_db, headline, _norm_db_ts(published_at))
                for (ticker_db, published_at, headline) in scored_article_mapping.keys()
            }

            # For fetch: skip cache + already scored keys to reduce downloads
            combined_existing_keys_for_fetch = set(self.existing_keys) | scored_article_keys_db
            # For insert: skip cache + anything already in DB
            combined_existing_keys_for_insert = set(self.existing_keys) | existing_article_keys_db

            # Determine fetch ranges, avoiding already-covered dates in DB
            earliest_date_db, latest_date_db = self.writer.get_article_date_bounds(ticker)
            fetch_ranges = []
            if earliest_date_db is None or latest_date_db is None:
                fetch_ranges.append((start_date, end_date))
            else:
                if forward_only and latest_date_db:
                    # Only fetch forward from the latest known date
                    forward_start = max(start_date, datetime.combine(latest_date_db, datetime.min.time()) + timedelta(days=1))
                    if forward_start <= end_date:
                        fetch_ranges.append((forward_start, end_date))
                else:
                    # Older gap (before earliest in DB)
                    if start_date.date() < earliest_date_db:
                        fetch_ranges.append(
                            (start_date, min(end_date, datetime.combine(earliest_date_db, datetime.min.time()) - timedelta(days=1)))
                        )
                    # Newer gap (after latest in DB)
                    if end_date.date() > latest_date_db:
                        fetch_ranges.append(
                            (max(start_date, datetime.combine(latest_date_db, datetime.min.time()) + timedelta(days=1)), end_date)
                        )

            all_articles = []
            for fetch_start, fetch_end in fetch_ranges:
                logger.info(f"[{ticker}] Step 1: Fetching news articles ({fetch_start.date()} to {fetch_end.date()})...")
                articles_df = self.fetcher.fetch_historical_news(
                    ticker,
                    fetch_start,
                    fetch_end,
                    existing_urls=self.existing_urls,
                    existing_keys=combined_existing_keys_for_fetch,
                )
                if not articles_df.empty:
                    all_articles.append(articles_df)

            if all_articles:
                articles_df = pd.concat(all_articles, ignore_index=True)
            else:
                logger.warning(f"[{ticker}] No news articles found in requested gaps")
                return {
                    "ticker": ticker,
                    "status": "no_data",
                    "articles": 0,
                    "sentiments": 0,
                    "aggregates": 0
                }


            # Filter to brand-new articles (defensive: in case cache missed some)
            def _normalize_ts(ts):
                ts = pd.to_datetime(ts)
                if ts.tzinfo is None:
                    ts = ts.tz_localize('UTC')
                else:
                    ts = ts.tz_convert('UTC')
                return ts

            def _is_new(row):
                url = str(row.get("url") or "")
                headline = str(row.get("headline") or "")
                ts = _normalize_ts(row.get("published_at"))
                if url and (ticker, url) in self.existing_urls:
                    return False
                if headline and (ticker, headline, ts) in combined_existing_keys_for_insert:
                    return False
                return True

            new_mask = articles_df.apply(_is_new, axis=1)
            new_articles_df = articles_df[new_mask].copy()

            # Step 2: Write raw articles to database
            logger.info(f"[{ticker}] Step 2: Writing articles to database...")
            article_count = self.writer.write_articles_batch(new_articles_df)
            if article_count > 0:
                # Update in-memory cache and append new entries to disk
                new_articles = []
                for _, row in new_articles_df.iterrows():
                    published_at = _normalize_ts(row["published_at"])
                    new_articles.append(
                        {
                            "ticker": ticker,
                            "url": row.get("url"),
                            "headline": row.get("headline"),
                            "published_at": published_at,
                        }
                    )
                    if row.get("url"):
                        self.existing_urls.add((ticker, str(row.get("url"))))
                    if row.get("headline") and published_at:
                        self.existing_keys.add((ticker, row.get("headline"), published_at))

                self.cache.append(new_articles)

            # Optionally skip sentiment/aggregation
            if skip_sentiment:
                logger.info(f"[{ticker}] Skipping sentiment/aggregation per flag.")
                return {
                    "ticker": ticker,
                    "status": "success_no_sentiment",
                    "articles": article_count,
                    "sentiments": 0,
                    "aggregates": 0,
                    "date_range": f"{start_date.date()} to {end_date.date()}",
                }

            # Step 3: Analyze sentiment (OpenAI)
            logger.info(f"[{ticker}] Step 3: Analyzing sentiment with OpenAI...")
            # Sentiment input: fetched articles that are not already scored
            def _needs_sentiment(row):
                headline = str(row.get("headline") or "")
                ts = _normalize_ts(row.get("published_at"))
                return (ticker, headline, ts) not in scored_article_keys_db

            sentiment_input_df = articles_df[articles_df.apply(_needs_sentiment, axis=1)].copy()

            if sentiment_input_df.empty:
                logger.info(f"[{ticker}] All fetched articles already scored; skipping sentiment.")
                return {
                    "ticker": ticker,
                    "status": "no_new_sentiment",
                    "articles": article_count,
                    "sentiments": 0,
                    "aggregates": 0,
                }

            sentiment_df = self.scorer.analyze_sentiment_batch(sentiment_input_df)

            # Ensure published_at is timezone-aware for matching
            if sentiment_df["published_at"].dt.tz is None:
                sentiment_df["published_at"] = sentiment_df["published_at"].dt.tz_localize('UTC')

            # Step 4: Retrieve article IDs for sentiment linking (refresh after inserts)
            logger.info(f"[{ticker}] Step 4: Linking sentiment to articles...")
            article_id_mapping = self.writer.get_article_ids_for_ticker(ticker)

            # Add article_id to sentiment_df by matching (ticker, published_at, headline)
            def get_article_id(row):
                key = (row["ticker"], row["published_at"], row["headline"])
                article_id = article_id_mapping.get(key)
                if article_id is None and len(article_id_mapping) > 0:
                    # Debug: Show first key from mapping and first key we're trying
                    sample_db_key = list(article_id_mapping.keys())[0]
                    logger.debug(f"No match found. Sample DB key: {sample_db_key}")
                    logger.debug(f"  DB published_at type: {type(sample_db_key[1])}")
                    logger.debug(f"Searching for key: {key}")
                    logger.debug(f"  Sentiment published_at type: {type(key[1])}")
                return article_id

            sentiment_df["article_id"] = sentiment_df.apply(get_article_id, axis=1)

            # Filter out any rows without article_id (shouldn't happen, but be defensive)
            before_filter = len(sentiment_df)
            sentiment_df = sentiment_df[sentiment_df["article_id"].notna()]
            after_filter = len(sentiment_df)

            if before_filter != after_filter:
                logger.warning(
                    f"[{ticker}] Could not link {before_filter - after_filter}/{before_filter} "
                    f"sentiment scores to articles"
                )

            if sentiment_df.empty:
                logger.error(f"[{ticker}] No sentiment scores could be linked to articles!")
                return {
                    "ticker": ticker,
                    "status": "partial_failure",
                    "articles": article_count,
                    "sentiments": 0,
                    "aggregates": 0,
                    "error": "Could not link sentiment to articles"
                }

            # Step 5: Write sentiment scores
            logger.info(f"[{ticker}] Step 5: Writing sentiment scores...")
            sentiment_count = self.writer.write_sentiment_scores_batch(sentiment_df)

            # Step 6: Aggregate by date
            logger.info(f"[{ticker}] Step 6: Aggregating sentiment by date...")
            aggregates_df = self.aggregator.aggregate_daily_sentiment(sentiment_df)

            # Step 7: Write daily aggregates
            logger.info(f"[{ticker}] Step 7: Writing daily aggregates...")
            aggregate_count = self.writer.write_daily_aggregates_batch(aggregates_df)

            logger.info(f"[{ticker}] Pipeline complete!")

            return {
                "ticker": ticker,
                "status": "success",
                "articles": article_count,
                "sentiments": sentiment_count,
                "aggregates": aggregate_count,
                "date_range": f"{start_date.date()} to {end_date.date()}"
            }

        except Exception as e:
            logger.error(f"[{ticker}] Pipeline failed: {e}")
            return {
                "ticker": ticker,
                "status": "failed",
                "error": str(e)
            }

    def run_for_multiple_tickers(
        self,
        tickers: list = None,
        start_date: datetime = None,
        end_date: datetime = None,
        skip_sentiment: bool = False,
        forward_only: bool = False
    ) -> list:
        """
        Run pipeline for multiple tickers.

        Args:
            tickers: List of ticker symbols (default: config.DEFAULT_TICKERS)
            start_date: Start date
            end_date: End date

        Returns:
            List of result dicts
        """
        if tickers is None:
            tickers = config.DEFAULT_TICKERS

        logger.info(f"Running pipeline for {len(tickers)} tickers")

        results = []
        for i, ticker in enumerate(tickers):
            result = self.run_for_ticker(
                ticker,
                start_date,
                end_date,
                skip_sentiment=skip_sentiment,
                forward_only=forward_only,
            )
            results.append(result)

            # Rate limiting for NewsAPI and Finnhub
            # Finnhub free tier: 60 calls/minute
            # NewsAPI free tier: 100 calls/day
            # We're conservative: wait 5 seconds between tickers
            if (i + 1) < len(tickers):
                logger.info(
                    f"Processed {i + 1}/{len(tickers)} tickers. "
                    f"Waiting 5 seconds to respect rate limits..."
                )
                time.sleep(5)

        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        total_articles = sum(r.get("articles", 0) for r in results)
        total_sentiments = sum(r.get("sentiments", 0) for r in results)
        total_aggregates = sum(r.get("aggregates", 0) for r in results)

        logger.info(
            f"Pipeline complete: {success_count}/{len(tickers)} successful | "
            f"Articles: {total_articles} | Sentiments: {total_sentiments} | "
            f"Aggregates: {total_aggregates}"
        )

        return results

    def close(self):
        """Cleanup resources."""
        self.writer.close()


def main():
    """Main entry point for pipeline execution."""
    import argparse

    parser = argparse.ArgumentParser(description="News Sentiment Pipeline")
    parser.add_argument(
        "--ticker",
        type=str,
        help="Single ticker to process (or omit for all default tickers)"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        help="Multiple tickers to process (space separated)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=config.HISTORICAL_DAYS,
        help="Number of days of historical data to fetch"
    )
    parser.add_argument(
        "--skip-sentiment",
        action="store_true",
        help="Fetch and store news only (skip sentiment scoring and aggregation)"
    )
    parser.add_argument(
        "--forward-only",
        action="store_true",
        help="Only fetch dates after the latest article in DB (skip older gaps)"
    )

    args = parser.parse_args()

    # Setup dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    # Run pipeline
    pipeline = DailyNewsSentimentPipeline()

    try:
        tickers = args.tickers or ([args.ticker] if args.ticker else None)

        if tickers:
            results = pipeline.run_for_multiple_tickers(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                skip_sentiment=args.skip_sentiment,
                forward_only=args.forward_only
            )
            print(f"\nResults:")
            for r in results:
                print(f"  {r}")
        else:
            results = pipeline.run_for_multiple_tickers(
                start_date=start_date,
                end_date=end_date,
                skip_sentiment=args.skip_sentiment,
                forward_only=args.forward_only
            )
            print(f"\nResults:")
            for r in results:
                print(f"  {r}")

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
