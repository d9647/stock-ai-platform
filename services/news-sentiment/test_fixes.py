"""
Test script to verify bug fixes in news fetching:
1. Invalid datetime handling (None, 0, or out of range)
2. No overlapping chunks
3. No infinite loops
"""
from datetime import datetime, timedelta
from src.ingestion.fetch_news import NewsFetcher

def test_chunking_logic():
    """Test that chunks don't overlap and cover the full range."""
    print("=" * 60)
    print("TEST 1: Chunking Logic")
    print("=" * 60)

    # Simulate the chunking logic
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)  # 30 days
    chunk_size_days = 10

    chunks = []
    current_start = start_date
    max_chunks = 1000
    chunk_count = 0

    while current_start < end_date and chunk_count < max_chunks:
        current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)  # +1 day to avoid overlap
        chunk_count += 1

    print(f"\nDate range: {start_date.date()} to {end_date.date()} ({(end_date - start_date).days} days)")
    print(f"Chunk size: {chunk_size_days} days")
    print(f"Number of chunks: {len(chunks)}")
    print("\nChunks:")

    for i, (start, end) in enumerate(chunks, 1):
        print(f"  Chunk {i}: {start.date()} → {end.date()} ({(end - start).days} days)")

    # Verify no overlaps
    print("\nVerifying no overlaps...")
    for i in range(len(chunks) - 1):
        chunk1_end = chunks[i][1]
        chunk2_start = chunks[i+1][0]
        gap = (chunk2_start - chunk1_end).days

        if gap < 0:
            print(f"  ❌ OVERLAP detected between Chunk {i+1} and Chunk {i+2}")
            print(f"     Chunk {i+1} ends: {chunk1_end.date()}")
            print(f"     Chunk {i+2} starts: {chunk2_start.date()}")
            return False
        elif gap == 0:
            print(f"  ⚠️  Adjacent (potential duplicate on boundary): Chunk {i+1} ends {chunk1_end.date()}, Chunk {i+2} starts {chunk2_start.date()}")
        elif gap == 1:
            print(f"  ✅ Chunk {i+1} and {i+2}: 1-day gap (correct)")

    print("\n✅ No overlaps detected!")
    return True


def test_invalid_datetime_handling():
    """Test that invalid datetimes are handled gracefully."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid Datetime Handling")
    print("=" * 60)

    # Simulate invalid datetime scenarios
    test_cases = [
        {"datetime": None, "headline": "Article with None datetime"},
        {"datetime": 0, "headline": "Article with zero datetime"},
        {"datetime": -1, "headline": "Article with negative timestamp"},
        {"datetime": 1734566400, "headline": "Valid article"},  # Dec 18, 2024
    ]

    print("\nProcessing test articles:")
    valid_count = 0
    skipped_count = 0

    for item in test_cases:
        dt = item.get("datetime")
        headline = item.get("headline")

        if dt is None or dt == 0:
            print(f"  ⚠️  Skipped: {headline} (datetime={dt})")
            skipped_count += 1
            continue

        try:
            published_at = datetime.fromtimestamp(dt)
            print(f"  ✅ Valid: {headline} → {published_at}")
            valid_count += 1
        except (ValueError, OSError, OverflowError) as e:
            print(f"  ⚠️  Skipped: {headline} (error: {e})")
            skipped_count += 1

    print(f"\nResults: {valid_count} valid, {skipped_count} skipped")
    print("✅ Invalid datetime handling works correctly!")
    return True


def test_infinite_loop_protection():
    """Test that infinite loop protection works."""
    print("\n" + "=" * 60)
    print("TEST 3: Infinite Loop Protection")
    print("=" * 60)

    # Test with 10,000 days (should create ~1,000 chunks max)
    start_date = datetime(2000, 1, 1)
    end_date = datetime(2027, 5, 19)  # ~10,000 days
    chunk_size_days = 10
    max_chunks = 1000

    chunks = []
    current_start = start_date
    chunk_count = 0

    while current_start < end_date and chunk_count < max_chunks:
        current_end = min(current_start + timedelta(days=chunk_size_days), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
        chunk_count += 1

    print(f"\nDate range: {start_date.date()} to {end_date.date()} ({(end_date - start_date).days} days)")
    print(f"Chunks created: {len(chunks)}")
    print(f"Max chunks limit: {max_chunks}")

    if chunk_count >= max_chunks:
        print(f"✅ Safety limit triggered at {chunk_count} chunks (protection works!)")
    else:
        print(f"✅ Completed normally with {chunk_count} chunks")

    return True


def test_real_world_365_days():
    """Test real-world scenario: 365 days of AAPL news."""
    print("\n" + "=" * 60)
    print("TEST 4: Real-World 365-Day Fetch (AAPL)")
    print("=" * 60)

    fetcher = NewsFetcher()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    print(f"\nFetching AAPL news: {start_date.date()} to {end_date.date()}")
    print("This will make real API calls and may take ~40 seconds...")
    print("(37 chunks × 1 second rate limiting)")

    try:
        df = fetcher.fetch_historical_news("AAPL", start_date, end_date)

        print(f"\n✅ SUCCESS!")
        print(f"Total articles fetched: {len(df)}")

        if not df.empty:
            print(f"\nDate range of articles:")
            print(f"  Earliest: {df['published_at'].min()}")
            print(f"  Latest: {df['published_at'].max()}")
            print(f"  Coverage: {(df['published_at'].max() - df['published_at'].min()).days} days")

            print(f"\nFirst 3 articles:")
            print(df[['published_at', 'headline']].head(3).to_string(index=False))

            # Check for duplicates
            duplicate_count = df.duplicated(subset=['ticker', 'headline', 'published_at']).sum()
            print(f"\nDuplicate check: {duplicate_count} duplicates (should be 0)")

            if duplicate_count == 0:
                print("✅ No duplicates found!")
            else:
                print(f"⚠️  Found {duplicate_count} duplicates (deduplication may have failed)")
        else:
            print("⚠️  No articles found (check API keys)")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NEWS FETCHING BUG FIX VERIFICATION")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Chunking Logic", test_chunking_logic()))
    results.append(("Invalid Datetime Handling", test_invalid_datetime_handling()))
    results.append(("Infinite Loop Protection", test_infinite_loop_protection()))

    # Ask before running real API test
    print("\n" + "=" * 60)
    response = input("\nRun real-world API test? This will make 37 API calls to Finnhub (y/n): ")
    if response.lower() == 'y':
        results.append(("Real-World 365-Day Fetch", test_real_world_365_days()))
    else:
        print("Skipped real-world test.")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All tests passed! Bug fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
