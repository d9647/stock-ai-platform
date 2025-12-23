"""
Daily feature pipeline orchestrator.
Creates feature snapshots for specified tickers and dates.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).resolve().parents[4]
src_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from loguru import logger

from snapshots.snapshot_creator import SnapshotCreator
from validators.feature_validation import FeatureValidator
from storage.db_writer import FeatureStoreWriter
from config import config


class DailyFeaturePipeline:
    """
    Orchestrates the complete feature snapshot pipeline.

    Flow:
    1. Create point-in-time snapshot (combine technical + sentiment)
    2. Validate snapshot for data quality
    3. Write snapshot to database (if valid)
    4. Write validation results to database
    """

    def __init__(self, database_url: str = None):
        """Initialize pipeline components."""
        self.database_url = database_url or config.DATABASE_URL

        # Initialize components
        self.creator = SnapshotCreator(self.database_url)
        self.validator = FeatureValidator()
        self.writer = FeatureStoreWriter(self.database_url)

        logger.info("Initialized daily feature pipeline")

    def run_for_ticker_and_date(
        self,
        ticker: str,
        as_of_date: date
    ) -> Dict:
        """
        Create and store feature snapshot for a single ticker and date.

        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for snapshot

        Returns:
            Dict with processing results
        """
        logger.info(f"Processing {ticker} for {as_of_date}")

        result = {
            "ticker": ticker,
            "date": as_of_date,
            "snapshot_created": False,
            "snapshot_valid": False,
            "snapshot_written": False,
            "validation_written": False,
            "errors": []
        }

        try:
            # Step 1: Create snapshot
            snapshot = self.creator.create_snapshot(ticker, as_of_date)

            if snapshot is None:
                logger.warning(
                    f"No snapshot created for {ticker} on {as_of_date} "
                    f"(missing technical data)"
                )
                result["errors"].append("No technical data available")
                return result

            result["snapshot_created"] = True
            result["snapshot_id"] = snapshot["snapshot_id"]

            # Step 2: Validate snapshot
            validation_result = self.validator.validate_snapshot(snapshot)
            result["snapshot_valid"] = validation_result["is_valid"]
            result["validation_errors"] = validation_result.get("errors", [])
            result["validation_warnings"] = validation_result.get("warnings", [])
            result["checks_passed"] = validation_result.get("checks_passed", 0)
            result["checks_failed"] = validation_result.get("checks_failed", 0)

            # Step 3: Write snapshot (even if invalid, for debugging)
            snapshot_written = self.writer.write_snapshot(snapshot)
            result["snapshot_written"] = snapshot_written

            # Step 4: Write validation results
            validation_written = self.writer.write_validation(
                snapshot["snapshot_id"],
                ticker,
                as_of_date,
                validation_result
            )
            result["validation_written"] = validation_written

            # Log summary
            if validation_result["is_valid"]:
                logger.info(
                    f"✅ {ticker} {as_of_date}: Valid snapshot created "
                    f"({result['checks_passed']} checks passed)"
                )
            else:
                logger.warning(
                    f"⚠️ {ticker} {as_of_date}: Invalid snapshot "
                    f"(errors: {len(result['validation_errors'])})"
                )

        except Exception as e:
            logger.error(f"Error processing {ticker} on {as_of_date}: {e}")
            result["errors"].append(str(e))

        return result

    def run_for_ticker(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Create snapshots for a ticker across a date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict with summary statistics
        """
        logger.info(
            f"Running feature pipeline for {ticker} "
            f"from {start_date} to {end_date}"
        )

        results = []
        current_date = start_date

        while current_date <= end_date:
            result = self.run_for_ticker_and_date(ticker, current_date)
            results.append(result)
            current_date += timedelta(days=1)

        # Calculate summary statistics
        summary = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "total_dates": len(results),
            "snapshots_created": sum(1 for r in results if r["snapshot_created"]),
            "snapshots_valid": sum(1 for r in results if r["snapshot_valid"]),
            "snapshots_invalid": sum(
                1 for r in results if r["snapshot_created"] and not r["snapshot_valid"]
            ),
            "snapshots_missing": sum(1 for r in results if not r["snapshot_created"]),
            "results": results
        }

        logger.info(
            f"Summary for {ticker}: {summary['snapshots_created']} snapshots created, "
            f"{summary['snapshots_valid']} valid, {summary['snapshots_invalid']} invalid, "
            f"{summary['snapshots_missing']} missing"
        )

        return summary

    def run_for_multiple_tickers(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Create snapshots for multiple tickers across a date range.

        Args:
            tickers: List of ticker symbols
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict with summary for all tickers
        """
        logger.info(
            f"Running feature pipeline for {len(tickers)} tickers "
            f"from {start_date} to {end_date}"
        )

        ticker_summaries = []

        for ticker in tickers:
            summary = self.run_for_ticker(ticker, start_date, end_date)
            ticker_summaries.append(summary)

        # Overall summary
        overall_summary = {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            "total_tickers": len(tickers),
            "total_snapshots_created": sum(
                s["snapshots_created"] for s in ticker_summaries
            ),
            "total_snapshots_valid": sum(
                s["snapshots_valid"] for s in ticker_summaries
            ),
            "total_snapshots_invalid": sum(
                s["snapshots_invalid"] for s in ticker_summaries
            ),
            "total_snapshots_missing": sum(
                s["snapshots_missing"] for s in ticker_summaries
            ),
            "ticker_summaries": ticker_summaries
        }

        logger.info(
            f"\n{'='*60}\n"
            f"FEATURE PIPELINE COMPLETE\n"
            f"{'='*60}\n"
            f"Tickers processed: {overall_summary['total_tickers']}\n"
            f"Snapshots created: {overall_summary['total_snapshots_created']}\n"
            f"Valid: {overall_summary['total_snapshots_valid']}\n"
            f"Invalid: {overall_summary['total_snapshots_invalid']}\n"
            f"Missing: {overall_summary['total_snapshots_missing']}\n"
            f"{'='*60}"
        )

        return overall_summary

    def close(self):
        """Close all database connections."""
        self.creator.close()
        self.writer.close()
        logger.info("Closed all database connections")


if __name__ == "__main__":
    import argparse

    # CLI interface
    parser = argparse.ArgumentParser(
        description="Run feature snapshot pipeline for tickers and dates"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=config.DEFAULT_TICKERS,
        help="Ticker symbols to process (default: all configured tickers)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=False,
        help="Start date (YYYY-MM-DD). If not provided, uses yesterday."
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=False,
        help="End date (YYYY-MM-DD). If not provided, uses yesterday."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days back from today (alternative to start-date/end-date)"
    )

    args = parser.parse_args()

    # Parse dates
    if args.days:
        # Use last N days
        end_date = date.today() - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=args.days - 1)
    elif args.start_date and args.end_date:
        # Use specified range
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        # Default: yesterday only
        start_date = date.today() - timedelta(days=1)
        end_date = start_date

    logger.info(
        f"Starting feature pipeline for {len(args.tickers)} tickers: {args.tickers}"
    )
    logger.info(f"Date range: {start_date} to {end_date}")

    # Run pipeline
    pipeline = DailyFeaturePipeline()

    try:
        summary = pipeline.run_for_multiple_tickers(
            args.tickers,
            start_date,
            end_date
        )

        # Print detailed results
        print("\n" + "="*60)
        print("FEATURE PIPELINE RESULTS")
        print("="*60)
        print(f"Tickers: {summary['tickers']}")
        print(f"Date range: {summary['start_date']} to {summary['end_date']}")
        print(f"\nSnapshots created: {summary['total_snapshots_created']}")
        print(f"Valid: {summary['total_snapshots_valid']}")
        print(f"Invalid: {summary['total_snapshots_invalid']}")
        print(f"Missing: {summary['total_snapshots_missing']}")

        # Per-ticker breakdown
        print("\nPer-ticker breakdown:")
        for ticker_summary in summary['ticker_summaries']:
            ticker = ticker_summary['ticker']
            created = ticker_summary['snapshots_created']
            valid = ticker_summary['snapshots_valid']
            invalid = ticker_summary['snapshots_invalid']
            missing = ticker_summary['snapshots_missing']

            print(
                f"  {ticker}: {created} created, {valid} valid, "
                f"{invalid} invalid, {missing} missing"
            )

        print("="*60)

    finally:
        pipeline.close()
