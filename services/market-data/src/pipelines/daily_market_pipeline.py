"""
Daily market data pipeline.
Fetches prices, calculates indicators, and stores to database.

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

from ..ingestion.fetch_prices import PolygonPriceFetcher
from ..indicators.technical_indicators import TechnicalIndicatorCalculator
from ..storage.db_writer import MarketDataWriter
from ..config import config


class DailyMarketDataPipeline:
    """
    End-to-end pipeline for market data ingestion.
    Runs offline, populates database for API consumption.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.fetcher = PolygonPriceFetcher()
        self.calculator = TechnicalIndicatorCalculator()
        self.writer = MarketDataWriter()

        logger.info("Initialized daily market data pipeline")

    def run_for_ticker(
        self,
        ticker: str,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> dict:
        """
        Run complete pipeline for a single ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (default: 2 years ago)
            end_date: End date (default: today)

        Returns:
            Dict with pipeline statistics
        """
        # Default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365 * config.HISTORICAL_YEARS)

        logger.info(f"Running pipeline for {ticker} from {start_date} to {end_date}")

        try:
            # Step 1: Fetch prices
            logger.info(f"[{ticker}] Step 1: Fetching prices...")
            df = self.fetcher.fetch_historical_prices(ticker, start_date, end_date)

            if df.empty:
                logger.warning(f"[{ticker}] No data found")
                return {"ticker": ticker, "status": "no_data", "records": 0}

            # Step 2: Write raw OHLCV data
            logger.info(f"[{ticker}] Step 2: Writing OHLCV data...")
            ohlcv_count = self.writer.write_ohlcv_batch(df)

            # Step 3: Calculate technical indicators
            logger.info(f"[{ticker}] Step 3: Calculating indicators...")
            df_with_indicators = self.calculator.calculate_all_indicators(df)

            # Step 4: Write technical indicators
            logger.info(f"[{ticker}] Step 4: Writing indicators...")
            indicator_count = self.writer.write_technical_indicators_batch(df_with_indicators)

            logger.info(f"[{ticker}] Pipeline complete!")

            return {
                "ticker": ticker,
                "status": "success",
                "ohlcv_records": ohlcv_count,
                "indicator_records": indicator_count,
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
        end_date: datetime = None
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
            result = self.run_for_ticker(ticker, start_date, end_date)
            results.append(result)

            # Rate limiting: Polygon free tier allows 5 requests per minute
            # After every 5 tickers, wait 60 seconds (unless it's the last ticker)
            if (i + 1) % config.POLYGON_RATE_LIMIT == 0 and (i + 1) < len(tickers):
                logger.info(
                    f"Processed {i + 1}/{len(tickers)} tickers. "
                    f"Rate limit reached, waiting 60 seconds..."
                )
                time.sleep(60)

        # Summary
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Pipeline complete: {success_count}/{len(tickers)} successful")

        return results

    def close(self):
        """Cleanup resources."""
        self.writer.close()


def main():
    """Main entry point for pipeline execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Market Data Pipeline")
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
        default=365 * config.HISTORICAL_YEARS,
        help="Number of days of historical data to fetch"
    )

    args = parser.parse_args()

    # Setup dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    # Run pipeline
    pipeline = DailyMarketDataPipeline()

    try:
        tickers = args.tickers or ([args.ticker] if args.ticker else None)
        if tickers:
            results = pipeline.run_for_multiple_tickers(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date
            )
            print(f"\nResults:")
            for r in results:
                print(f"  {r}")
        else:
            results = pipeline.run_for_multiple_tickers(
                start_date=start_date,
                end_date=end_date
            )
            print(f"\nResults:")
            for r in results:
                print(f"  {r}")

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
