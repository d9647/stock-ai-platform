# Fix: News Fetching for Long Date Ranges (365+ days)

## Problem

When running `--days 365` for the news sentiment pipeline, only ~70 daily aggregates were being created instead of the expected 365. The root cause was **Finnhub's API limit of ~250 articles per request**.

### Previous Behavior

```python
# Single API call for entire date range
news = self.finnhub_client.company_news(ticker, _from="2024-01-01", to="2024-12-18")
# Returns only the most recent 250 articles (covering ~70 days)
```

For a 365-day request, Finnhub would return only the **most recent 250 articles**, which typically covered only 70-90 days depending on the ticker's news volume.

## Solution

**Implemented date chunking** - Split large date ranges into 10-day chunks and fetch each chunk separately.

### New Behavior

```python
# For 365 days, automatically splits into 37 chunks of 10 days each
# (10 days chosen because high-volume tickers like AAPL have ~250 articles per 10-14 days)
chunks = [
    (2024-01-01, 2024-01-11),  # Chunk 1
    (2024-01-11, 2024-01-21),  # Chunk 2
    ...
    (2024-12-08, 2024-12-18)   # Chunk 37
]

# Fetch each chunk separately with rate limiting
for chunk in chunks:
    news = self.finnhub_client.company_news(ticker, _from=chunk[0], to=chunk[1])
    time.sleep(1)  # Rate limiting
```

This ensures complete coverage for any date range, regardless of length.

## Files Changed

- [services/news-sentiment/src/ingestion/fetch_news.py](services/news-sentiment/src/ingestion/fetch_news.py) - Modified `_fetch_from_finnhub()` method

## Bug Fixes Included

In addition to the chunking fix, the following bugs were also addressed:

### 1. Invalid Datetime Handling
**Problem**: If Finnhub returns `"datetime": null` or `"datetime": 0`, calling `datetime.fromtimestamp(None)` would crash with "year 0 out of range".

**Fix**: Added validation and error handling:
```python
dt = item.get("datetime")
if dt is None or dt == 0:
    logger.warning(f"Skipping article with invalid datetime")
    continue

try:
    published_at = datetime.fromtimestamp(dt)
except (ValueError, OSError, OverflowError) as e:
    logger.warning(f"Invalid timestamp {dt}: {e}")
    continue
```

### 2. Overlapping Chunks
**Problem**: Chunks were potentially overlapping on boundary dates:
- Chunk 1: Jan 1 → Jan 11
- Chunk 2: Jan 11 → Jan 21 (Jan 11 appears in both)

**Fix**: Added +1 day offset when advancing to next chunk:
```python
current_start = current_end + timedelta(days=1)  # Avoid overlap
```

This ensures no duplicates. The existing deduplication logic (`drop_duplicates`) provides additional safety.

### 3. Infinite Loop Protection
**Problem**: If the chunking logic had a bug, it could create an infinite loop.

**Fix**: Added maximum chunk limit with error handling:
```python
max_chunks = 1000
chunk_count = 0

while current_start < end_date and chunk_count < max_chunks:
    # ... chunking logic ...
    chunk_count += 1

if chunk_count >= max_chunks:
    raise ValueError(f"Too many chunks generated")
```

## Implementation Details

### Key Changes

1. **Automatic Chunking**
   - Date ranges ≤ 10 days: Single API call (no change)
   - Date ranges > 10 days: Split into 10-day chunks

2. **Rate Limiting**
   - Maintains 1 second delay between API calls
   - Respects Finnhub's 60 calls/minute free tier limit

3. **Logging**
   - Shows number of chunks being processed
   - Logs total articles fetched across all chunks
   - Debug logs for each chunk's date range

### Why 10 Days?

Based on real data: **AAPL had 250 articles covering only 13 days** (12/5 to 12/18).

- **Safe for High-Volume Tickers**: Even AAPL (~20 articles/day) stays under 250 articles
- **Works for All Tickers**: Low-volume tickers benefit from fewer API calls when possible
- **Rate-Limit Friendly**: 365 days = 37 API calls ≈ 37 seconds (well within 60/minute limit)

## Testing

### Test Scripts

**Quick Chunking Test** - [services/news-sentiment/test_chunking.py](services/news-sentiment/test_chunking.py):
```bash
cd services/news-sentiment
source venv/bin/activate
python test_chunking.py
```

**Comprehensive Bug Fix Verification** - [services/news-sentiment/test_fixes.py](services/news-sentiment/test_fixes.py):
```bash
cd services/news-sentiment
source venv/bin/activate
python test_fixes.py
```

The comprehensive test verifies:
1. **Chunking logic**: No overlaps, correct gap between chunks
2. **Invalid datetime handling**: Skips None, 0, and out-of-range timestamps
3. **Infinite loop protection**: Stops at 1,000 chunk limit
4. **Real-world 365-day fetch**: Tests with actual AAPL data (37 API calls)

### Expected Results After Fix

| Command | Before Fix | After Fix |
|---------|-----------|-----------|
| `--days 30` | ~250 articles, 30 aggregates ✅ | ~250 articles, 30 aggregates ✅ |
| `--days 90` | ~250 articles, ~70 aggregates ❌ | ~750 articles, 90 aggregates ✅ |
| `--days 365` | ~250 articles, ~70 aggregates ❌ | ~3,250 articles, 365 aggregates ✅ |

## Impact on Pipeline Runtime

### Time Increase

- **10 days**: No change (~2 minutes)
- **30 days**: +2 seconds (3 chunks vs 1 call)
- **90 days**: +8 seconds (9 chunks vs 1 call)
- **365 days**: +36 seconds (37 chunks vs 1 call)

The additional time is minimal because:
1. Rate limiting was already 1 second per call
2. We're just doing more API calls (which we should have been doing)
3. OpenAI sentiment analysis is still the bottleneck (~5-10 minutes)

### API Quota Impact

Finnhub free tier allows **60 calls/minute** and **unlimited daily calls**.

- **365 days, 4 tickers**: 37 chunks × 4 tickers = **148 API calls** ≈ 2.5 minutes (well within limits)

## Usage

No changes needed! The fix is automatic and transparent:

```bash
# This now works correctly for any number of days
cd services/news-sentiment
source venv/bin/activate

# 365 days will automatically chunk into 30-day periods
python -m src.pipelines.daily_news_pipeline --days 365
```

## Verification

After running the fixed pipeline, verify in the database:

```sql
-- Check daily aggregates count (should match --days parameter)
SELECT ticker, COUNT(*) as days_of_data
FROM news.news_sentiment_aggregates
GROUP BY ticker;

-- Expected for --days 365:
-- ticker | days_of_data
-- -------+-------------
-- AAPL   | 365
-- MSFT   | 365
-- GOOGL  | 365
-- AMZN   | 365
```

## Migration Notes

### For Existing Data

If you've already run the pipeline with `--days 365` and only got 70 days of data:

1. **Option 1: Re-run the entire pipeline** (recommended)
   ```bash
   # This will fetch missing data and deduplicate automatically
   cd services/news-sentiment
   source venv/bin/activate
   python -m src.pipelines.daily_news_pipeline --days 365
   ```

2. **Option 2: Fetch only missing date ranges**
   ```bash
   # Manually run for specific date ranges
   # (Not implemented - would require custom script)
   ```

### Database Deduplication

The pipeline automatically handles duplicates:
- Articles are deduplicated by `(ticker, headline, published_at)`
- Daily aggregates are upserted (overwritten if they already exist)
- Safe to re-run without data corruption

## Future Improvements

Potential enhancements (not implemented):

1. **Adaptive Chunking**
   - Use 30 days for high-volume tickers (AAPL, TSLA)
   - Use 60 days for low-volume tickers (smaller companies)

2. **Parallel Fetching**
   - Fetch chunks concurrently to reduce total time
   - Requires careful rate limit management

3. **Resume Support**
   - Track which chunks have been fetched
   - Resume from last successful chunk on failure

4. **Configurable Chunk Size**
   - Add `--chunk-days` parameter for fine-tuning
   - Default remains 30 days

## Related Issues

- [POPULATE_DATABASE.md](POPULATE_DATABASE.md) - Updated to reflect accurate data expectations
- [PHASE_4_COMPLETE.md](PHASE_4_COMPLETE.md) - Game implementation documentation

## Conclusion

The fix ensures that **requesting N days of data actually returns N days of data**, regardless of how many articles are published per day. This is critical for:

1. **Game accuracy**: Players need consistent daily data
2. **Backtesting**: Historical analysis requires complete coverage
3. **AI recommendations**: Agents need full sentiment history

The implementation is automatic, transparent, and respects API rate limits while providing complete historical coverage.

---

**Fixed**: December 18, 2024
**Version**: v1.1.0
