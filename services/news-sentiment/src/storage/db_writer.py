"""
Write news and sentiment data to PostgreSQL database.
Ensures immutability - only INSERT operations (APPEND-ONLY).
"""
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from loguru import logger
import pandas as pd

from api.app.models.news import NewsArticle, NewsSentimentScore, DailySentimentAggregate
from ..config import config


class NewsDataWriter:
    """
    Writes news and sentiment data to database with immutability guarantees.
    All writes are APPEND-ONLY using INSERT ... ON CONFLICT DO NOTHING.
    """

    def __init__(self, database_url: str = None):
        """Initialize database connection."""
        self.database_url = database_url or config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        SessionLocal = sessionmaker(bind=self.engine)
        self.session = SessionLocal()

        logger.info("Initialized news data writer")

    def write_articles_batch(self, df: pd.DataFrame) -> int:
        """
        Write news articles in batch (APPEND-ONLY).
        Uses INSERT ... ON CONFLICT DO NOTHING for idempotency.

        Args:
            df: DataFrame with columns: ticker, published_at, headline, content, source, url, author

        Returns:
            Number of records inserted
        """
        if df.empty:
            logger.warning("No articles to write")
            return 0

        try:
            records = []
            for _, row in df.iterrows():
                # Ensure published_at is timezone-aware (UTC)
                published_at = pd.to_datetime(row["published_at"])
                if published_at.tzinfo is None:
                    published_at = published_at.tz_localize('UTC')

                records.append({
                    "ticker": row["ticker"],
                    "published_at": published_at,
                    "headline": str(row["headline"]),
                    "content": str(row["content"]) if pd.notna(row.get("content")) else None,
                    "source": str(row["source"]),
                    "url": str(row["url"]) if pd.notna(row.get("url")) else None,
                    "author": str(row["author"]) if pd.notna(row.get("author")) else None,
                })

            logger.info(
                f"Prepared {len(records)} news articles "
                f"({records[0]['ticker']}, {records[0]['published_at'].date()} → "
                f"{records[-1]['published_at'].date()})"
            )

            # Use INSERT ... ON CONFLICT DO NOTHING for idempotency
            # Conflict on unique constraint uq_news_article (ticker, published_at, headline)
            stmt = insert(NewsArticle.__table__).values(records)
            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_news_article"
            )

            result = self.session.execute(stmt)
            self.session.commit()

            inserted = result.rowcount
            skipped = len(records) - inserted

            if inserted > 0:
                logger.info(f"Inserted {inserted} new news articles")
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing articles (already in database)")

            return inserted

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing news articles: {e}")
            raise

    def write_sentiment_scores_batch(self, df: pd.DataFrame) -> int:
        """
        Write sentiment scores in batch (APPEND-ONLY).

        Args:
            df: DataFrame with columns: ticker, published_at, article_id,
                sentiment_score, confidence, themes, model_name, model_version

        Returns:
            Number of records inserted
        """
        if df.empty:
            logger.warning("No sentiment scores to write")
            return 0

        try:
            records = []
            for _, row in df.iterrows():
                # Convert themes to list if it's not already
                themes = row.get("themes", [])
                if not isinstance(themes, list):
                    themes = []

                records.append({
                    "article_id": row["article_id"],
                    "ticker": row["ticker"],
                    "published_at": pd.to_datetime(row["published_at"]),
                    "sentiment_score": float(row["sentiment_score"]),
                    "confidence": float(row["confidence"]),
                    "themes": themes,
                    "model_name": str(row["model_name"]),
                    "model_version": str(row["model_version"]),
                })

            logger.info(
                f"Prepared {len(records)} sentiment scores "
                f"({records[0]['ticker']}, {records[0]['published_at'].date()})"
            )

            # Use INSERT ... ON CONFLICT DO NOTHING
            # Conflict on unique constraint uq_sentiment_article (article_id)
            stmt = insert(NewsSentimentScore.__table__).values(records)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_sentiment_article")

            result = self.session.execute(stmt)
            self.session.commit()

            inserted = result.rowcount
            skipped = len(records) - inserted

            if inserted > 0:
                logger.info(f"Inserted {inserted} new sentiment scores")
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing sentiment scores (already in database)")

            return inserted

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing sentiment scores: {e}")
            raise

    def write_daily_aggregates_batch(self, df: pd.DataFrame) -> int:
        """
        Write daily sentiment aggregates in batch (APPEND-ONLY).

        Args:
            df: DataFrame with columns: ticker, date, avg_sentiment, weighted_sentiment,
                article_count, positive_count, neutral_count, negative_count, top_themes

        Returns:
            Number of records inserted
        """
        if df.empty:
            logger.warning("No daily aggregates to write")
            return 0

        try:
            records = []
            for _, row in df.iterrows():
                # Convert top_themes to list if it's not already
                top_themes = row.get("top_themes", [])
                if not isinstance(top_themes, list):
                    top_themes = []

                records.append({
                    "ticker": row["ticker"],
                    "date": pd.to_datetime(row["date"]).date(),
                    "avg_sentiment": float(row["avg_sentiment"]),
                    "weighted_sentiment": float(row["weighted_sentiment"]),
                    "article_count": int(row["article_count"]),
                    "positive_count": int(row["positive_count"]),
                    "neutral_count": int(row["neutral_count"]),
                    "negative_count": int(row["negative_count"]),
                    "top_themes": top_themes,
                })

            logger.info(
                f"Prepared {len(records)} daily aggregates "
                f"({records[0]['ticker']}, {records[0]['date']} → "
                f"{records[-1]['date']})"
            )

            # Use INSERT ... ON CONFLICT DO NOTHING
            # Conflict on unique constraint uq_daily_sentiment (ticker, date)
            stmt = insert(DailySentimentAggregate.__table__).values(records)
            stmt = stmt.on_conflict_do_nothing(constraint="uq_daily_sentiment")

            result = self.session.execute(stmt)
            self.session.commit()

            inserted = result.rowcount
            skipped = len(records) - inserted

            if inserted > 0:
                logger.info(f"Inserted {inserted} new daily aggregates")
            if skipped > 0:
                logger.info(f"Skipped {skipped} existing daily aggregates (already in database)")

            return inserted

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error writing daily aggregates: {e}")
            raise

    def get_article_ids_for_ticker(
        self,
        ticker: str
    ) -> Dict[tuple, str]:
        """
        Retrieve all article IDs for a given ticker.
        Used to link sentiment scores to articles.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict mapping (ticker, published_at, headline) -> article_id
        """
        try:
            # Query all articles for this ticker (no date filter for robustness)
            articles = (
                self.session.query(
                    NewsArticle.ticker,
                    NewsArticle.published_at,
                    NewsArticle.headline,
                    NewsArticle.id
                )
                .filter(NewsArticle.ticker == ticker)
                .all()
            )

            # Create mapping using (ticker, published_at, headline) as key
            mapping = {}
            for article in articles:
                key = (article.ticker, article.published_at, article.headline)
                mapping[key] = str(article.id)

            logger.info(f"Retrieved {len(mapping)} article IDs for {ticker}")
            return mapping

        except Exception as e:
            logger.error(f"Error retrieving article IDs: {e}")
            raise

    def get_scored_article_keys_for_ticker(self, ticker: str) -> Dict[tuple, str]:
        """
        Retrieve article keys that already have sentiment scores.
        Returns mapping (ticker, published_at, headline) -> article_id.
        """
        try:
            rows = (
                self.session.query(
                    NewsArticle.ticker,
                    NewsArticle.published_at,
                    NewsArticle.headline,
                    NewsArticle.id,
                )
                .join(
                    NewsSentimentScore,
                    NewsSentimentScore.article_id == NewsArticle.id,
                )
                .filter(NewsArticle.ticker == ticker)
                .all()
            )

            mapping = {}
            for row in rows:
                key = (row.ticker, row.published_at, row.headline)
                mapping[key] = str(row.id)

            logger.info(f"Retrieved {len(mapping)} scored article keys for {ticker}")
            return mapping
        except Exception as e:
            logger.error(f"Error retrieving scored article keys: {e}")
            raise

    def get_article_date_bounds(self, ticker: str):
        """
        Return (earliest_date, latest_date) for articles of a ticker.
        Dates are timezone-naive (date only). Returns (None, None) if none exist.
        """
        try:
            row = (
                self.session.query(
                    func.min(NewsArticle.published_at),
                    func.max(NewsArticle.published_at)
                )
                .filter(NewsArticle.ticker == ticker)
                .one()
            )
            earliest, latest = row
            if earliest:
                earliest = earliest.date()
            if latest:
                latest = latest.date()
            logger.info(f"Date bounds for {ticker}: earliest={earliest}, latest={latest}")
            return earliest, latest
        except Exception as e:
            logger.error(f"Error retrieving date bounds: {e}")
            raise

    def close(self):
        """Close database session."""
        self.session.close()
        logger.info("Closed database connection")


if __name__ == "__main__":
    # Test the writer
    writer = NewsDataWriter()

    # Create sample article data
    sample_articles = pd.DataFrame([
        {
            "ticker": "AAPL",
            "published_at": pd.Timestamp("2024-12-16 10:00:00"),
            "headline": "Apple announces new product",
            "content": "Apple Inc. announced a new product today...",
            "source": "Reuters",
            "url": "https://example.com/article1",
            "author": "John Doe"
        }
    ])

    # Write articles
    count = writer.write_articles_batch(sample_articles)
    print(f"Wrote {count} articles")

    writer.close()
