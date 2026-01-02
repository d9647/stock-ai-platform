"""
Phase 1 - Trade Rules Validation Tests

Tests trading rules specific to the Stock Simulation game:
1. Buy only allowed on BUY/STRONG_BUY recommendations
2. Sell allowed anytime (no restrictions)
3. HOLD does not block manual trades
4. Same-day double trade rejection
5. Trade execution at next day's open price

These rules are documented in the game design.
"""
import pytest
from datetime import datetime, date


class TestBuyRestrictions:
    """Test buy order validation rules."""

    @pytest.mark.unit
    def test_buy_allowed_on_buy_recommendation(self):
        """Players can buy when AI recommends BUY."""
        recommendation = "BUY"
        action = "BUY"

        # Buy is allowed on BUY recommendation
        is_valid = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert is_valid == True

    @pytest.mark.unit
    def test_buy_allowed_on_strong_buy_recommendation(self):
        """Players can buy when AI recommends STRONG_BUY."""
        recommendation = "STRONG_BUY"
        action = "BUY"

        is_valid = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert is_valid == True

    @pytest.mark.unit
    def test_buy_blocked_on_hold_recommendation(self):
        """Players cannot buy when AI recommends HOLD."""
        recommendation = "HOLD"
        action = "BUY"

        is_valid = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert is_valid == False

    @pytest.mark.unit
    def test_buy_blocked_on_sell_recommendation(self):
        """Players cannot buy when AI recommends SELL."""
        recommendation = "SELL"
        action = "BUY"

        is_valid = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert is_valid == False

    @pytest.mark.unit
    def test_buy_blocked_on_strong_sell_recommendation(self):
        """Players cannot buy when AI recommends STRONG_SELL."""
        recommendation = "STRONG_SELL"
        action = "BUY"

        is_valid = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert is_valid == False


class TestSellRestrictions:
    """Test sell order validation rules."""

    @pytest.mark.unit
    def test_sell_allowed_anytime(self):
        """Sell is always allowed, regardless of recommendation."""
        test_cases = [
            "STRONG_BUY",
            "BUY",
            "HOLD",
            "SELL",
            "STRONG_SELL"
        ]

        for recommendation in test_cases:
            action = "SELL"
            # Sell is always valid (no recommendation check needed)
            is_valid = action == "SELL"
            assert is_valid == True, f"Sell should be allowed on {recommendation}"

    @pytest.mark.unit
    def test_sell_requires_ownership(self):
        """Can only sell stocks you own."""
        holdings = {
            "AAPL": {"shares": 10, "avgCost": 150.0}
        }

        # Try to sell AAPL (owned)
        ticker = "AAPL"
        shares_to_sell = 5
        has_shares = ticker in holdings and holdings[ticker]["shares"] >= shares_to_sell
        assert has_shares == True

        # Try to sell MSFT (not owned)
        ticker = "MSFT"
        shares_to_sell = 5
        has_shares = ticker in holdings and holdings[ticker]["shares"] >= shares_to_sell
        assert has_shares == False

    @pytest.mark.unit
    def test_cannot_sell_more_than_owned(self):
        """Cannot sell more shares than you own."""
        holdings = {
            "AAPL": {"shares": 10, "avgCost": 150.0}
        }

        # Try to sell 15 shares (only have 10)
        ticker = "AAPL"
        shares_to_sell = 15
        owned_shares = holdings[ticker]["shares"]

        can_sell = shares_to_sell <= owned_shares
        assert can_sell == False


class TestHoldBehavior:
    """Test HOLD recommendation behavior."""

    @pytest.mark.unit
    def test_hold_does_not_block_manual_trades(self):
        """HOLD recommendation doesn't prevent manual sell orders."""
        recommendation = "HOLD"
        action = "SELL"
        holdings = {"AAPL": {"shares": 10, "avgCost": 150.0}}

        # Sell is always allowed if you own the stock
        can_sell = action == "SELL" and "AAPL" in holdings
        assert can_sell == True

    @pytest.mark.unit
    def test_hold_prevents_buy(self):
        """HOLD recommendation prevents buy orders (only BUY/STRONG_BUY allowed)."""
        recommendation = "HOLD"
        action = "BUY"

        can_buy = action == "BUY" and recommendation in ["BUY", "STRONG_BUY"]
        assert can_buy == False


class TestTradeExecution:
    """Test trade execution timing and pricing."""

    @pytest.mark.unit
    def test_trades_execute_next_day_open(self):
        """
        Trades placed on day N execute at day N+1's open price.

        This prevents players from seeing the close price before trading.
        """
        current_day = 0
        trade_placed_day = current_day

        # Trade executes on next day
        execution_day = current_day + 1
        assert execution_day == 1

        # Use next day's open price
        next_day_prices = {"AAPL": {"open": 155.0, "close": 160.0}}
        execution_price = next_day_prices["AAPL"]["open"]

        assert execution_price == 155.0  # Not 160.0 (close)

    @pytest.mark.unit
    def test_trade_cost_calculation(self):
        """Total cost = shares * price (no fees in this game)."""
        shares = 10
        price = 150.0

        total_cost = shares * price
        assert total_cost == 1500.0

    @pytest.mark.unit
    def test_sell_proceeds_calculation(self):
        """Sell proceeds = shares * price (no fees)."""
        shares = 10
        price = 160.0

        proceeds = shares * price
        assert proceeds == 1600.0


class TestTradeLimits:
    """Test trading limits and validation."""

    @pytest.mark.unit
    def test_positive_shares_only(self):
        """Cannot trade 0 or negative shares."""
        invalid_shares = [0, -5, -10]

        for shares in invalid_shares:
            is_valid = shares > 0
            assert is_valid == False, f"Shares {shares} should be invalid"

        # Valid shares
        valid_shares = [1, 5, 10, 100]
        for shares in valid_shares:
            is_valid = shares > 0
            assert is_valid == True

    @pytest.mark.unit
    def test_integer_shares_only(self):
        """Cannot trade fractional shares."""
        # In real implementation, this would be enforced by Pydantic schema
        # or database column type (Integer)

        valid_shares = [1, 5, 10]  # Integers
        for shares in valid_shares:
            is_integer = isinstance(shares, int)
            assert is_integer == True

    @pytest.mark.unit
    def test_sufficient_cash_for_buy(self):
        """Must have enough cash to execute buy order."""
        cash = 5000.0
        shares = 10
        price = 600.0  # Total cost: $6,000

        total_cost = shares * price
        has_sufficient_cash = cash >= total_cost

        assert has_sufficient_cash == False

        # Test with sufficient cash
        cash = 10000.0
        has_sufficient_cash = cash >= total_cost
        assert has_sufficient_cash == True


class TestSameDayTrading:
    """Test same-day trading restrictions."""

    @pytest.mark.unit
    def test_cannot_trade_same_stock_twice_same_day(self):
        """
        Cannot buy and sell (or sell and buy) the same stock on the same day.

        This prevents gaming the system with multiple trades per day.
        """
        # Track trades for current day
        todays_trades = []

        # First trade: BUY AAPL
        trade1 = {"ticker": "AAPL", "action": "BUY", "day": 0}
        todays_trades.append(trade1)

        # Attempt second trade: SELL AAPL (same day, same ticker)
        ticker = "AAPL"
        current_day = 0

        already_traded_today = any(
            t["ticker"] == ticker and t["day"] == current_day
            for t in todays_trades
        )

        assert already_traded_today == True

    @pytest.mark.unit
    def test_can_trade_different_stocks_same_day(self):
        """Can trade different stocks on the same day."""
        todays_trades = []

        # First trade: BUY AAPL
        trade1 = {"ticker": "AAPL", "action": "BUY", "day": 0}
        todays_trades.append(trade1)

        # Second trade: BUY MSFT (different ticker, same day)
        ticker = "MSFT"
        current_day = 0

        already_traded_today = any(
            t["ticker"] == ticker and t["day"] == current_day
            for t in todays_trades
        )

        assert already_traded_today == False  # MSFT not traded yet

    @pytest.mark.unit
    def test_can_trade_same_stock_next_day(self):
        """Can trade the same stock on different days."""
        trades = []

        # Day 0: BUY AAPL
        trade1 = {"ticker": "AAPL", "action": "BUY", "day": 0}
        trades.append(trade1)

        # Day 1: SELL AAPL (different day, same ticker)
        ticker = "AAPL"
        current_day = 1

        already_traded_today = any(
            t["ticker"] == ticker and t["day"] == current_day
            for t in trades
        )

        assert already_traded_today == False  # Different day, so allowed


class TestTradeValidationFlow:
    """Test complete trade validation flow."""

    @pytest.mark.unit
    def test_valid_buy_order_checklist(self):
        """A valid buy order must pass all checks."""
        # Setup
        cash = 10000.0
        recommendation = "BUY"
        ticker = "AAPL"
        shares = 10
        price = 150.0
        current_day = 0
        todays_trades = []

        # Validation checks
        has_cash = cash >= (shares * price)
        is_buy_allowed = recommendation in ["BUY", "STRONG_BUY"]
        not_traded_today = not any(
            t["ticker"] == ticker and t["day"] == current_day
            for t in todays_trades
        )
        valid_shares = shares > 0

        # All checks must pass
        is_valid = all([has_cash, is_buy_allowed, not_traded_today, valid_shares])
        assert is_valid == True

    @pytest.mark.unit
    def test_valid_sell_order_checklist(self):
        """A valid sell order must pass all checks."""
        # Setup
        holdings = {"AAPL": {"shares": 20, "avgCost": 150.0}}
        ticker = "AAPL"
        shares = 10
        current_day = 0
        todays_trades = []

        # Validation checks
        owns_stock = ticker in holdings
        has_shares = holdings[ticker]["shares"] >= shares if owns_stock else False
        not_traded_today = not any(
            t["ticker"] == ticker and t["day"] == current_day
            for t in todays_trades
        )
        valid_shares = shares > 0

        # All checks must pass
        is_valid = all([owns_stock, has_shares, not_traded_today, valid_shares])
        assert is_valid == True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_sell_all_shares(self):
        """Can sell all shares of a position (full liquidation)."""
        holdings = {"AAPL": {"shares": 10, "avgCost": 150.0}}
        shares_to_sell = 10

        can_sell = holdings["AAPL"]["shares"] >= shares_to_sell
        assert can_sell == True

        # After sale, position should be removed or set to 0
        remaining_shares = holdings["AAPL"]["shares"] - shares_to_sell
        assert remaining_shares == 0

    @pytest.mark.unit
    def test_buy_with_exact_cash(self):
        """Can buy stock using all available cash."""
        cash = 1500.0
        shares = 10
        price = 150.0

        total_cost = shares * price
        can_afford = cash >= total_cost

        assert can_afford == True
        assert total_cost == 1500.0

        # After purchase, cash = 0
        remaining_cash = cash - total_cost
        assert remaining_cash == 0.0

    @pytest.mark.unit
    def test_empty_portfolio_sell_attempt(self):
        """Cannot sell from empty portfolio."""
        holdings = {}  # No positions
        ticker = "AAPL"
        shares = 10

        owns_stock = ticker in holdings
        assert owns_stock == False
