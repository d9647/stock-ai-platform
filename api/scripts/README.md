# API Scripts

Utility scripts for the Stock AI Platform API.

## seed_test_data.py

Seeds minimal test data for CI/testing environments.

### Purpose

Creates just enough data to pass API tests without running full data pipelines. This is used in CI workflows to provide sample data for testing API endpoints.

### What It Seeds

- **Recommendations**: 30 days × 4 tickers = 120 stock recommendations
- **News Articles**: 10 days × 4 tickers = 40 news articles
- **Sentiment Aggregates**: 10 days × 4 tickers = 40 sentiment records

### Usage

```bash
cd api
python scripts/seed_test_data.py
```

Or with custom database URL:

```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname python scripts/seed_test_data.py
```

### CI Integration

This script is automatically run in GitHub Actions workflows:

```yaml
- name: Seed test data
  env:
    DATABASE_URL: postgresql://postgres:postgres@localhost:5432/stockai_dev
  run: |
    cd api
    python scripts/seed_test_data.py
```

### Data Created

**Tickers**: AAPL, MSFT, GOOGL, AMZN

**Recommendations**:
- Weekdays: BUY recommendations with 65% confidence
- Weekends: HOLD recommendations (markets closed)
- Includes rationale, technical signals, sentiment signals, risk levels

**News Articles**:
- Sample headlines and content
- Sentiment scores around 0.5 (neutral)
- Test source URLs

**Sentiment Aggregates**:
- Average sentiment: 0.5
- Article counts: 5 per day
- Top themes: earnings, technology, market

### Exit Codes

- `0`: Success - data seeded correctly
- `1`: Failure - error occurred during seeding

### Notes

- Clears existing data before seeding (safe for test databases only!)
- Creates tables if they don't exist
- Minimal data for fast execution (~1 second)
- Designed for CI/testing, NOT for production use
