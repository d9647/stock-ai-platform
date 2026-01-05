# Testing Guide

This document explains how to run tests for the Stock AI Platform.

## Overview

The project includes comprehensive unit tests and smoke tests for all implemented phases:

- **Phase 1 (Market Data)**: Technical indicator calculations
- **Phase 2 (News Sentiment)**: Sentiment aggregation and pipeline validation
- **Integration Tests**: End-to-end pipeline validation

## Test Structure

```
services/
├── market-data/
│   └── tests/
│       ├── __init__.py
│       └── test_indicators.py      # Technical indicator tests
│
└── news-sentiment/
    └── tests/
        ├── __init__.py
        ├── test_aggregation.py      # Sentiment aggregation tests
        └── test_smoke.py            # End-to-end smoke tests
```

## Running Tests

### Prerequisites

Install test dependencies:

```bash
# For market-data service
cd services/market-data
pip install pytest pytest-cov

# For news-sentiment service
cd services/news-sentiment
./venv/bin/pip install pytest pytest-cov
```

### Run All Tests

**Market Data Service:**
```bash
cd services/market-data
pytest tests/ -v
```

**News Sentiment Service:**
```bash
cd services/news-sentiment
./venv/bin/pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test only technical indicators
pytest tests/test_indicators.py -v

# Test only sentiment aggregation
pytest tests/test_aggregation.py -v

# Run smoke tests only
pytest tests/test_smoke.py -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Tests

```bash
# Run a specific test class
pytest tests/test_aggregation.py::TestSentimentAggregator -v

# Run a specific test method
pytest tests/test_aggregation.py::TestSentimentAggregator::test_average_sentiment_calculation -v
```

## Test Categories

### Unit Tests

Test individual components in isolation:

- `test_indicators.py`: Technical indicator calculations
  - SMA, EMA calculations
  - RSI calculation
  - MACD calculation
  - Bollinger Bands
  - Volatility

- `test_aggregation.py`: Sentiment aggregation logic
  - Average sentiment calculation
  - Weighted sentiment calculation
  - Sentiment distribution
  - Theme extraction

### Smoke Tests

Test complete workflows without external dependencies:

- `test_smoke.py`: End-to-end pipeline validation
  - Full aggregation pipeline
  - Data validation
  - Empty data handling
  - Multi-day aggregation

## Test Data

Tests use fixture data to avoid external API calls:

```python
@pytest.fixture
def sample_sentiment_data():
    """Create sample sentiment data for testing."""
    return pd.DataFrame([...])
```

This ensures:
- Tests run quickly
- No API costs
- Deterministic results
- No network dependencies

## Expected Test Results

All tests should pass:

```
========================= test session starts =========================
collected 15 items

tests/test_aggregation.py::TestSentimentAggregator::test_initialization PASSED
tests/test_aggregation.py::TestSentimentAggregator::test_aggregate_daily_sentiment PASSED
tests/test_aggregation.py::TestSentimentAggregator::test_average_sentiment_calculation PASSED
...

========================= 15 passed in 2.34s =========================
```

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd services/news-sentiment
    ./venv/bin/pytest tests/ --cov=src
```

## Adding New Tests

When adding new features:

1. **Create test file**: `tests/test_<feature>.py`
2. **Add fixtures**: Use `@pytest.fixture` for test data
3. **Write test cases**:
   - Test happy path
   - Test edge cases
   - Test error handling
4. **Run tests**: Ensure all pass before committing

### Test Template

```python
import pytest

class TestNewFeature:
    """Test suite for new feature."""

    def test_basic_functionality(self):
        """Test basic feature works."""
        # Arrange
        input_data = ...

        # Act
        result = process(input_data)

        # Assert
        assert result is not None
        assert result.status == "success"

    def test_edge_case(self):
        """Test edge case handling."""
        # ...
```

## Troubleshooting

### Import Errors

If you see import errors:
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH=/Users/wdng/Projects/stock-ai-platform:$PYTHONPATH
```

### Database Tests

Database integration tests require:
- PostgreSQL running (`docker-compose up -d`)
- Migrations applied (`alembic upgrade head`)

Skip database tests during development:
```bash
pytest tests/ -m "not integration"
```

## Test Coverage Goals

- **Unit Tests**: >80% code coverage
- **Integration Tests**: All critical paths
- **Smoke Tests**: End-to-end validation

Check current coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Best Practices

1. ✅ **Keep tests isolated**: No shared state between tests
2. ✅ **Use fixtures**: Reusable test data
3. ✅ **Test edge cases**: Empty data, invalid input, etc.
4. ✅ **Mock external services**: No real API calls
5. ✅ **Descriptive names**: `test_average_sentiment_calculation` not `test1`
6. ✅ **Fast tests**: Aim for <5s total runtime
7. ✅ **Deterministic**: Same input → same output

---

**Questions?** See the test files for examples or refer to [pytest documentation](https://docs.pytest.org/).
