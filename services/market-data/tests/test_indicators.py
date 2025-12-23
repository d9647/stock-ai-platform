"""
Unit tests for technical indicators calculation.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from src.indicators.technical_indicators import TechnicalIndicatorCalculator


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')

    df = pd.DataFrame({
        'ticker': ['AAPL'] * 250,
        'date': dates,
        'open': np.random.uniform(150, 200, 250),
        'high': np.random.uniform(150, 200, 250),
        'low': np.random.uniform(150, 200, 250),
        'close': np.linspace(150, 200, 250),  # Upward trend
        'volume': np.random.randint(1000000, 10000000, 250)
    })

    # Ensure high >= close >= low
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)

    return df


class TestTechnicalIndicatorCalculator:
    """Test suite for TechnicalIndicatorCalculator."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = TechnicalIndicatorCalculator()
        assert calc is not None

    def test_calculate_sma(self, sample_ohlcv_data):
        """Test SMA calculation."""
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all_indicators(sample_ohlcv_data)

        # Check SMA columns exist
        assert 'sma_20' in result.columns
        assert 'sma_50' in result.columns
        assert 'sma_200' in result.columns

        # Check SMA values are reasonable
        assert result['sma_20'].notna().sum() >= 230  # Should have values after warmup
        assert result['sma_50'].notna().sum() >= 200
        assert result['sma_200'].notna().sum() >= 50

        # SMA should be within reasonable range of close prices
        valid_sma_20 = result['sma_20'].dropna()
        assert valid_sma_20.min() > 140
        assert valid_sma_20.max() < 210

    def test_calculate_rsi(self, sample_ohlcv_data):
        """Test RSI calculation."""
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all_indicators(sample_ohlcv_data)

        # Check RSI column exists
        assert 'rsi_14' in result.columns

        # Check RSI is in valid range [0, 100]
        valid_rsi = result['rsi_14'].dropna()
        assert valid_rsi.min() >= 0
        assert valid_rsi.max() <= 100

        # Should have RSI values after warmup period
        assert result['rsi_14'].notna().sum() >= 230

    def test_calculate_macd(self, sample_ohlcv_data):
        """Test MACD calculation."""
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all_indicators(sample_ohlcv_data)

        # Check MACD columns exist
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns

        # MACD histogram should equal MACD - signal
        valid_rows = result[['macd', 'macd_signal', 'macd_histogram']].dropna()
        if len(valid_rows) > 0:
            calculated_histogram = valid_rows['macd'] - valid_rows['macd_signal']
            np.testing.assert_array_almost_equal(
                valid_rows['macd_histogram'].values,
                calculated_histogram.values,
                decimal=5
            )

    def test_calculate_bollinger_bands(self, sample_ohlcv_data):
        """Test Bollinger Bands calculation."""
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all_indicators(sample_ohlcv_data)

        # Check Bollinger columns exist
        assert 'bollinger_upper' in result.columns
        assert 'bollinger_middle' in result.columns
        assert 'bollinger_lower' in result.columns

        # Upper > Middle > Lower
        valid_rows = result[['bollinger_upper', 'bollinger_middle', 'bollinger_lower']].dropna()
        if len(valid_rows) > 0:
            assert (valid_rows['bollinger_upper'] >= valid_rows['bollinger_middle']).all()
            assert (valid_rows['bollinger_middle'] >= valid_rows['bollinger_lower']).all()

    def test_calculate_volatility(self, sample_ohlcv_data):
        """Test volatility calculation."""
        calc = TechnicalIndicatorCalculator()
        result = calc.calculate_all_indicators(sample_ohlcv_data)

        # Check volatility column exists
        assert 'volatility_30d' in result.columns

        # Volatility should be positive and reasonable (< 200% annualized)
        valid_vol = result['volatility_30d'].dropna()
        if len(valid_vol) > 0:
            assert valid_vol.min() >= 0
            assert valid_vol.max() < 2.0  # 200% annualized volatility

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        calc = TechnicalIndicatorCalculator()
        empty_df = pd.DataFrame()
        result = calc.calculate_all_indicators(empty_df)

        assert result.empty

    def test_insufficient_data(self):
        """Test handling of insufficient data for indicators."""
        calc = TechnicalIndicatorCalculator()

        # Only 10 days of data (insufficient for 200-day minimum requirement)
        small_df = pd.DataFrame({
            'ticker': ['AAPL'] * 10,
            'date': pd.date_range('2024-01-01', periods=10),
            'close': [150, 151, 152, 151, 150, 149, 150, 151, 152, 153],
            'high': [151, 152, 153, 152, 151, 150, 151, 152, 153, 154],
            'low': [149, 150, 151, 150, 149, 148, 149, 150, 151, 152],
            'open': [150, 151, 152, 151, 150, 149, 150, 151, 152, 153],
            'volume': [1000000] * 10
        })

        result = calc.calculate_all_indicators(small_df)

        # When data is insufficient (< 200 rows), returns original DataFrame without indicators
        assert len(result) == 10
        # Should NOT have indicator columns added
        assert 'sma_20' not in result.columns
        # Should have original columns
        assert 'close' in result.columns
        assert 'volume' in result.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
