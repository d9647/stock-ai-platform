"""
Daily agent pipeline orchestrator.
Runs agents for specified tickers and dates.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict
import time

from loguru import logger

from ..graphs.agent_graph import build_agent_graph
from ..storage.feature_reader import FeatureSnapshotReader
from ..storage.agent_writer import AgentOutputWriter
from ..config import config


class DailyAgentPipeline:
    """
    Orchestrates daily agent execution.

    Flow:
    1. Read feature snapshot for (ticker, date)
    2. Run LangGraph agent orchestration
    3. Write outputs to database
    """

    def __init__(self, database_url: str = None, skip_existing: bool = True):
        self.database_url = database_url or config.DATABASE_URL
        self.agent_graph = build_agent_graph()
        self.reader = FeatureSnapshotReader(database_url)
        self.writer = AgentOutputWriter(database_url)
        self.skip_existing = skip_existing

        logger.info("Initialized daily agent pipeline")

    def run_for_ticker_and_date(
        self,
        ticker: str,
        as_of_date: date
    ) -> Dict:
        """
        Run agents for single ticker and date.

        Returns:
            {
                "ticker": str,
                "date": date,
                "status": "success" | "failed",
                "recommendation": str,
                "errors": [str]
            }
        """
        logger.info(f"Processing {ticker} for {as_of_date}")

        result = {
            "ticker": ticker,
            "date": as_of_date,
            "status": "failed",
            "recommendation": None,
            "errors": []
        }

        try:
            # Skip if already processed (existing recommendation)
            if self.skip_existing and self.writer.recommendation_exists(ticker, as_of_date):
                logger.info(f"Skipping {ticker} {as_of_date}: recommendation already exists")
                result["status"] = "skipped"
                return result

            # Step 1: Fetch feature snapshot
            snapshot = self.reader.get_snapshot(ticker, as_of_date)

            if not snapshot:
                result["errors"].append("No feature snapshot available")
                return result

            # Step 2: Run LangGraph agent orchestration
            initial_state = {
                "ticker": ticker,
                "as_of_date": as_of_date,
                "feature_snapshot": snapshot,
                "technical_output": None,
                "sentiment_output": None,
                "risk_output": None,
                "recommendation": None,
                "errors": [],
                "execution_start": time.time()
            }

            final_state = self.agent_graph.invoke(initial_state)

            # Step 3: Write outputs to database
            write_result = self.writer.write_agent_outputs(final_state)

            result["status"] = "success"
            result["recommendation"] = (
                final_state.get("recommendation", {}).get("recommendation")
            )
            result["errors"] = final_state.get("errors", [])

            logger.info(
                f"✅ {ticker} {as_of_date}: "
                f"{result['recommendation']} "
                f"(wrote {write_result['outputs_written']} outputs)"
            )

        except Exception as e:
            logger.error(f"Agent pipeline failed for {ticker}: {e}")
            result["errors"].append(str(e))

        return result

    def run_for_multiple_tickers(
        self,
        tickers: List[str],
        as_of_date: date
    ) -> Dict:
        """
        Run agents for multiple tickers on a single date.

        Returns:
            Summary statistics
        """
        logger.info(
            f"Running agent pipeline for {len(tickers)} tickers on {as_of_date}"
        )

        results = []

        for i, ticker in enumerate(tickers):
            result = self.run_for_ticker_and_date(ticker, as_of_date)
            results.append(result)

            # Rate limiting (avoid overwhelming OpenAI API)
            if (i + 1) < len(tickers):
                time.sleep(2)  # 2 seconds between tickers

        # Calculate summary
        summary = {
            "date": as_of_date,
            "total_tickers": len(tickers),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "recommendations": {
                rec: sum(1 for r in results if r.get("recommendation") == rec)
                for rec in ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
            },
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "results": results
        }

        logger.info(
            f"\n{'='*60}\n"
            f"AGENT PIPELINE COMPLETE\n"
            f"{'='*60}\n"
            f"Date: {as_of_date}\n"
            f"Tickers: {summary['successful']}/{summary['total_tickers']} successful "
            f"({summary['skipped']} skipped)\n"
            f"Recommendations: {summary['recommendations']}\n"
            f"{'='*60}"
        )

        return summary

    def close(self):
        """Close all database connections."""
        self.reader.close()
        self.writer.close()
        logger.info("Closed all database connections")


if __name__ == "__main__":
    import argparse
    import sys
    from sqlalchemy import create_engine, text

    parser = argparse.ArgumentParser(
        description="Run agent pipeline for tickers and date(s)"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=config.DEFAULT_TICKERS,
        help="Ticker symbols to process"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=False,
        help="Single date (YYYY-MM-DD). Default: yesterday"
    )
    parser.add_argument(
        "--days",
        type=int,
        required=False,
        help="Number of days to process (gets last N trading days from feature snapshots)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.date and args.days:
        logger.error("Cannot specify both --date and --days")
        sys.exit(1)

    # Run pipeline
    pipeline = DailyAgentPipeline()

    try:
        if args.days:
            # Multi-day mode: fetch last N trading days from feature snapshots
            logger.info(f"Fetching last {args.days} trading days from database...")

            engine = create_engine(config.DATABASE_URL)
            with engine.connect() as conn:
                query = text("""
                    SELECT DISTINCT as_of_date
                    FROM features.feature_snapshots
                    WHERE ticker = :ticker
                    ORDER BY as_of_date DESC
                    LIMIT :days
                """)
                result = conn.execute(query, {"ticker": args.tickers[0], "days": args.days})
                dates = [row[0] for row in result]

            if not dates:
                logger.error("No feature snapshots found in database")
                sys.exit(1)

            logger.info(f"Found {len(dates)} trading days to process")
            logger.info(f"Date range: {dates[-1]} to {dates[0]}")

            # Process each date
            all_summaries = []
            success_count = 0
            fail_count = 0

            for i, analysis_date in enumerate(dates, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing date {i}/{len(dates)}: {analysis_date}")
                logger.info(f"{'='*60}")

                try:
                    summary = pipeline.run_for_multiple_tickers(args.tickers, analysis_date)
                    all_summaries.append(summary)

                    if summary['successful'] > 0:
                        success_count += 1
                    if summary['failed'] > 0:
                        fail_count += 1

                except Exception as e:
                    logger.error(f"Failed to process {analysis_date}: {e}")
                    fail_count += 1

            # Overall summary
            print("\n" + "="*60)
            print("MULTI-DAY AGENT PIPELINE COMPLETE")
            print("="*60)
            print(f"Processed: {len(dates)} trading days")
            print(f"Successful days: {success_count}")
            print(f"Failed days: {fail_count}")
            print(f"Total recommendations generated: {sum(s['successful'] for s in all_summaries)}")
            print("="*60)

        else:
            # Single date mode (original behavior)
            if args.date:
                analysis_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            else:
                analysis_date = date.today() - timedelta(days=1)

            logger.info(f"Starting agent pipeline for {len(args.tickers)} tickers")
            logger.info(f"Analysis date: {analysis_date}")

            summary = pipeline.run_for_multiple_tickers(args.tickers, analysis_date)

            print("\n" + "="*60)
            print("AGENT PIPELINE RESULTS")
            print("="*60)
            print(f"Date: {summary['date']}")
            print(f"Successful: {summary['successful']}/{summary['total_tickers']} (skipped {summary['skipped']})")
            print(f"\nRecommendations:")
            for rec, count in summary['recommendations'].items():
                if count > 0:
                    print(f"  {rec}: {count}")
            print("="*60)

    finally:
        pipeline.close()
