"""
Test script to verify date chunking works correctly for long date ranges.
"""
from datetime import datetime, timedelta
from src.ingestion.fetch_news import NewsFetcher

# Create fetcher
fetcher = NewsFetcher()

# Test with 365 days (1 year)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"Testing fetch for 365 days: {start_date.date()} to {end_date.date()}")
print(f"Expected chunks: {365 // 10 + 1} chunks of ~10 days each")
print(f"Why 10 days? AAPL has ~250 articles per 13 days, so 10 days is safe")
print("-" * 60)

# This should now split into multiple 10-day chunks automatically
df = fetcher.fetch_historical_news("AAPL", start_date, end_date)

print(f"\n✅ SUCCESS!")
print(f"Total articles fetched: {len(df)}")
print(f"\nDate range of articles:")
if not df.empty:
    print(f"  Earliest: {df['published_at'].min()}")
    print(f"  Latest: {df['published_at'].max()}")
    print(f"  Coverage: {(df['published_at'].max() - df['published_at'].min()).days} days")
else:
    print("  No articles found")

print("\nFirst 5 articles:")
print(df.head())
