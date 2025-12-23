"""
Calculate technical indicators from OHLCV data.
Deterministic and reproducible calculations.
"""
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.volatility import AverageTrueRange, BollingerBands
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator
from loguru import logger


class TechnicalIndicatorCalculator:
    """
    Calculates technical indicators from OHLCV data.
    All calculations are deterministic - same input always produces same output.
    """

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for a price dataframe.

        Args:
            df: DataFrame with columns: date, open, high, low, close, volume

        Returns:
            DataFrame with additional indicator columns
        """
        if df.empty or len(df) < 200:
            logger.warning("Insufficient data for technical indicators")
            return df

        df = df.copy()
        df = df.sort_values("date").reset_index(drop=True)

        try:
            # Moving Averages
            df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
            df["sma_50"] = SMAIndicator(close=df["close"], window=50).sma_indicator()
            df["sma_200"] = SMAIndicator(close=df["close"], window=200).sma_indicator()
            df["ema_12"] = EMAIndicator(close=df["close"], window=12).ema_indicator()
            df["ema_26"] = EMAIndicator(close=df["close"], window=26).ema_indicator()

            # MACD
            macd = MACD(close=df["close"])
            df["macd"] = macd.macd()
            df["macd_signal"] = macd.macd_signal()
            df["macd_histogram"] = macd.macd_diff()

            # RSI
            df["rsi_14"] = RSIIndicator(close=df["close"], window=14).rsi()

            # Bollinger Bands
            bollinger = BollingerBands(close=df["close"], window=20, window_dev=2)
            df["bollinger_upper"] = bollinger.bollinger_hband()
            df["bollinger_middle"] = bollinger.bollinger_mavg()
            df["bollinger_lower"] = bollinger.bollinger_lband()

            # ATR (Average True Range)
            df["atr_14"] = AverageTrueRange(
                high=df["high"],
                low=df["low"],
                close=df["close"],
                window=14
            ).average_true_range()

            # OBV (On-Balance Volume)
            df["obv"] = OnBalanceVolumeIndicator(
                close=df["close"],
                volume=df["volume"]
            ).on_balance_volume()

            # Historical Volatility (30-day)
            df["volatility_30d"] = TechnicalIndicatorCalculator._calculate_volatility(
                df["close"],
                window=30
            )

            logger.info(f"Calculated indicators for {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise

    @staticmethod
    def _calculate_volatility(prices: pd.Series, window: int = 30) -> pd.Series:
        """
        Calculate historical volatility (annualized).

        Args:
            prices: Series of closing prices
            window: Rolling window size

        Returns:
            Series of volatility values
        """
        # Calculate log returns
        log_returns = np.log(prices / prices.shift(1))

        # Rolling standard deviation of returns
        volatility = log_returns.rolling(window=window).std()

        # Annualize (assuming 252 trading days)
        annualized_volatility = volatility * np.sqrt(252)

        return annualized_volatility

    @staticmethod
    def extract_indicators_for_date(df: pd.DataFrame, date: pd.Timestamp) -> dict:
        """
        Extract all indicator values for a specific date.

        Args:
            df: DataFrame with calculated indicators
            date: Target date

        Returns:
            Dict of indicator values for that date
        """
        row = df[df["date"] == date]

        if row.empty:
            return {}

        row = row.iloc[0]

        indicators = {
            "sma_20": row.get("sma_20"),
            "sma_50": row.get("sma_50"),
            "sma_200": row.get("sma_200"),
            "ema_12": row.get("ema_12"),
            "ema_26": row.get("ema_26"),
            "rsi_14": row.get("rsi_14"),
            "macd": row.get("macd"),
            "macd_signal": row.get("macd_signal"),
            "macd_histogram": row.get("macd_histogram"),
            "bollinger_upper": row.get("bollinger_upper"),
            "bollinger_middle": row.get("bollinger_middle"),
            "bollinger_lower": row.get("bollinger_lower"),
            "atr_14": row.get("atr_14"),
            "obv": row.get("obv"),
            "volatility_30d": row.get("volatility_30d"),
        }

        # Remove None values
        indicators = {k: v for k, v in indicators.items() if pd.notna(v)}

        return indicators


if __name__ == "__main__":
    # Test with sample data
    from ..ingestion.fetch_prices import PolygonPriceFetcher
    from datetime import datetime, timedelta

    fetcher = PolygonPriceFetcher()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    df = fetcher.fetch_historical_prices("AAPL", start_date, end_date)
    df_with_indicators = TechnicalIndicatorCalculator.calculate_all_indicators(df)

    print(df_with_indicators.tail())
    print("\nIndicator columns:", [col for col in df_with_indicators.columns if col not in ["date", "open", "high", "low", "close", "volume", "ticker"]])
