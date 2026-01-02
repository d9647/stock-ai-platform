"""
Seed minimal test data for CI/testing environments.
Creates just enough data to pass API tests without running full pipelines.
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base
from app.models.agents import StockRecommendation
from app.models.news import NewsArticle, DailySentimentAggregate


def seed_test_data():
    """Seed minimal test data for API endpoints."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/stockai_dev")

    print(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create schemas first (if they don't exist)
        print("Creating schemas...")
        schemas = ['market_data', 'news', 'agents', 'features', 'multiplayer']
        for schema in schemas:
            db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        db.commit()
        print("✓ Schemas created/verified")

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created/verified")

        # Define test data parameters
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        days = 30
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)

        print(f"\nSeeding data for {len(tickers)} tickers, {days} days")
        print(f"Date range: {start_date} to {end_date}")

        # Clear existing test data
        print("\nClearing existing data...")
        db.query(StockRecommendation).delete()
        db.query(DailySentimentAggregate).delete()
        db.query(NewsArticle).delete()
        db.commit()
        print("✓ Cleared existing data")

        # Seed recommendations
        print("\nSeeding recommendations...")
        recommendations_count = 0
        current_date = start_date

        for day in range(days):
            for ticker in tickers:
                # Determine if it's a weekend (simplified - just use day number)
                is_weekend = current_date.weekday() >= 5

                recommendation = StockRecommendation(
                    ticker=ticker,
                    as_of_date=current_date,
                    action="HOLD" if is_weekend else "BUY",
                    confidence=0.65 if not is_weekend else 1.0,
                    technical_signal="NEUTRAL" if is_weekend else "BULLISH",
                    sentiment_signal="NEUTRAL" if is_weekend else "BULLISH",
                    risk_level="LOW_RISK" if is_weekend else "MEDIUM_RISK",
                    rationale_summary="Markets are closed. No trading available." if is_weekend else f"Sample recommendation for {ticker}",
                    rationale_technical_view=[] if is_weekend else [f"Technical indicator for {ticker}"],
                    rationale_sentiment_view=[] if is_weekend else [f"Sentiment indicator for {ticker}"],
                    rationale_risk_view=[] if is_weekend else [f"Risk indicator for {ticker}"],
                    target_price=150.0 + (day * 0.5),
                    stop_loss=140.0,
                    version="1.0.0-test"
                )
                db.add(recommendation)
                recommendations_count += 1

            current_date += timedelta(days=1)

        db.commit()
        print(f"✓ Seeded {recommendations_count} recommendations")

        # Seed news articles
        print("\nSeeding news articles...")
        news_count = 0
        current_date = start_date

        for day in range(min(days, 10)):  # Only seed 10 days of news to keep it light
            for ticker in tickers:
                article = NewsArticle(
                    ticker=ticker,
                    headline=f"Test news article for {ticker} on {current_date}",
                    content=f"Sample content for {ticker}. This is a test article.",
                    source="TestSource",
                    published_at=datetime.combine(current_date, datetime.min.time()),
                    sentiment_score=0.5,
                    url=f"https://example.com/{ticker}/{current_date}"
                )
                db.add(article)
                news_count += 1

            current_date += timedelta(days=1)

        db.commit()
        print(f"✓ Seeded {news_count} news articles")

        # Seed daily sentiment aggregates
        print("\nSeeding sentiment aggregates...")
        sentiment_count = 0
        current_date = start_date

        for day in range(min(days, 10)):  # Only seed 10 days of sentiment
            for ticker in tickers:
                sentiment = DailySentimentAggregate(
                    ticker=ticker,
                    date=current_date,
                    avg_sentiment=0.5,
                    weighted_sentiment=0.5,
                    article_count=5,
                    positive_count=3,
                    negative_count=1,
                    neutral_count=1,
                    top_themes=["earnings", "technology", "market"],
                    sentiment_trend="stable"
                )
                db.add(sentiment)
                sentiment_count += 1

            current_date += timedelta(days=1)

        db.commit()
        print(f"✓ Seeded {sentiment_count} sentiment aggregates")

        # Verify data
        print("\n" + "="*50)
        print("VERIFICATION")
        print("="*50)

        total_recommendations = db.query(StockRecommendation).count()
        total_news = db.query(NewsArticle).count()
        total_sentiment = db.query(DailySentimentAggregate).count()

        print(f"Total recommendations: {total_recommendations}")
        print(f"Total news articles: {total_news}")
        print(f"Total sentiment aggregates: {total_sentiment}")

        if total_recommendations > 0:
            print("\n✅ Seed data created successfully!")
            print(f"\nAPI endpoints should now work:")
            print(f"  - GET /api/v1/game/data?days=30")
            print(f"  - GET /api/v1/recommendations/")
            print(f"  - GET /api/v1/news/AAPL")
            return 0
        else:
            print("\n❌ Failed to create seed data")
            return 1

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit_code = seed_test_data()
    sys.exit(exit_code)
