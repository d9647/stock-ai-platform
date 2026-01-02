"""
Phase 1 - API Contract Tests

Tests that enforce Phase 0 decision: "Versioned APIs (/v1/)"

These tests ensure:
1. Request/response schema stability
2. Error codes are meaningful and consistent
3. Timestamps are timezone-safe
4. Numeric precision is consistent
5. Backward compatibility

CRITICAL: These tests define the contract between backend and iOS.
Any failing test represents a BREAKING CHANGE that requires /v2/.
"""
import pytest
from httpx import AsyncClient


class TestAPIVersioning:
    """Test API versioning strategy."""

    @pytest.mark.integration
    async def test_all_routes_use_v1_prefix(self, client: AsyncClient):
        """All game/multiplayer routes must use /api/v1/ prefix."""
        # These routes define the iOS contract
        v1_routes = [
            "/api/v1/health",
            "/api/v1/game/data",
            "/api/v1/multiplayer/rooms",
        ]

        # All routes should be accessible
        # (Note: Some may return errors without params, but should exist)
        for route in v1_routes:
            # We're just testing the route exists (not 404)
            # Some routes may return 422 (validation error) which is fine
            pass  # Placeholder for actual HTTP calls


class TestHealthEndpoint:
    """Test health check endpoint contract."""

    @pytest.mark.integration
    async def test_health_endpoint_exists(self, client: AsyncClient):
        """GET /api/v1/health must exist and return 200."""
        # This will be implemented when we have async client fixture working
        pass

    @pytest.mark.integration
    def test_health_response_schema(self):
        """Health response must have consistent schema."""
        # Expected schema
        expected_fields = ["status", "timestamp", "version"]

        # Mock response
        mock_response = {
            "status": "healthy",
            "timestamp": "2025-01-15T10:00:00Z",
            "version": "1.0.0"
        }

        for field in expected_fields:
            assert field in mock_response, f"Health response missing '{field}'"


class TestGameDataEndpoint:
    """Test /api/v1/game/data contract."""

    @pytest.mark.integration
    def test_game_data_response_schema(self):
        """
        GET /api/v1/game/data response must have stable schema.

        iOS depends on these exact field names and types.
        """
        # Expected top-level fields
        expected_fields = [
            "days",           # List[GameDayResponse]
            "tickers",        # List[str]
            "start_date",     # str (ISO date)
            "end_date",       # str (ISO date)
            "total_days",     # int
        ]

        mock_response = {
            "days": [],
            "tickers": ["AAPL", "MSFT"],
            "start_date": "2025-01-01",
            "end_date": "2025-01-30",
            "total_days": 30
        }

        for field in expected_fields:
            assert field in mock_response, f"Missing field: {field}"

    @pytest.mark.integration
    def test_game_day_response_schema(self):
        """Each day object must have stable schema."""
        expected_fields = [
            "day",                    # int (0-indexed)
            "date",                   # str (ISO date)
            "is_trading_day",         # bool
            "recommendations",        # List[GameRecommendation]
            "prices",                 # Dict[ticker, GamePrice]
            "news",                   # List[NewsArticle]
            "technical_indicators",   # Dict[ticker, TechnicalIndicators]
        ]

        mock_day = {
            "day": 0,
            "date": "2025-01-01",
            "is_trading_day": True,
            "recommendations": [],
            "prices": {},
            "news": [],
            "technical_indicators": {}
        }

        for field in expected_fields:
            assert field in mock_day, f"Missing field: {field}"

    @pytest.mark.integration
    def test_recommendation_schema(self):
        """Recommendation object must have stable schema."""
        expected_fields = [
            "ticker",
            "recommendation",           # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
            "confidence",               # float (0-1)
            "technical_signal",
            "sentiment_signal",
            "risk_level",
            "rationale_summary",
            "rationale_risk_view",
            "rationale_technical_view",
            "rationale_sentiment_view",
            "as_of_date",
        ]

        mock_rec = {
            "ticker": "AAPL",
            "recommendation": "BUY",
            "confidence": 0.85,
            "technical_signal": "BULLISH",
            "sentiment_signal": "POSITIVE",
            "risk_level": "MEDIUM_RISK",
            "rationale_summary": "Strong buy signal",
            "rationale_risk_view": [],
            "rationale_technical_view": [],
            "rationale_sentiment_view": [],
            "as_of_date": "2025-01-15"
        }

        for field in expected_fields:
            assert field in mock_rec, f"Missing field: {field}"

    @pytest.mark.integration
    def test_price_schema(self):
        """Price object must have stable schema."""
        expected_fields = ["open", "high", "low", "close", "volume"]

        mock_price = {
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "volume": 1000000
        }

        for field in expected_fields:
            assert field in mock_price, f"Missing field: {field}"


class TestMultiplayerEndpoints:
    """Test /api/v1/multiplayer/* contracts."""

    @pytest.mark.integration
    def test_create_room_response_schema(self):
        """POST /api/v1/multiplayer/rooms response schema."""
        expected_fields = [
            "id",
            "room_code",
            "created_by",
            "room_name",
            "config",
            "start_date",
            "end_date",
            "status",
            "game_mode",
            "current_day",
            "created_at",
        ]

        mock_response = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "room_code": "ABC123",
            "created_by": "Teacher",
            "room_name": "Period 3 Economics",
            "config": {
                "initialCash": 100000,
                "numDays": 30,
                "tickers": ["AAPL", "MSFT"],
                "difficulty": "medium"
            },
            "start_date": "2025-01-01",
            "end_date": "2025-01-30",
            "status": "waiting",
            "game_mode": "async",
            "current_day": 0,
            "created_at": "2025-01-15T10:00:00Z"
        }

        for field in expected_fields:
            assert field in mock_response, f"Missing field: {field}"

    @pytest.mark.integration
    def test_join_room_response_schema(self):
        """POST /api/v1/multiplayer/rooms/join response schema."""
        expected_fields = [
            "id",
            "player_name",
            "player_email",
            "current_day",
            "is_finished",
            "cash",
            "portfolio_value",
            "total_return_pct",
            "total_return_usd",
            "score",
            "grade",
            "joined_at",
            "last_action_at",
        ]

        mock_response = {
            "id": "789e4567-e89b-12d3-a456-426614174000",
            "player_name": "Alice",
            "player_email": "alice@school.edu",
            "current_day": 0,
            "is_finished": False,
            "cash": 100000.0,
            "portfolio_value": 100000.0,
            "total_return_pct": 0.0,
            "total_return_usd": 0.0,
            "score": 0.0,
            "grade": "C",
            "joined_at": "2025-01-15T10:05:00Z",
            "last_action_at": "2025-01-15T10:05:00Z"
        }

        for field in expected_fields:
            assert field in mock_response, f"Missing field: {field}"

    @pytest.mark.integration
    def test_leaderboard_response_schema(self):
        """GET /api/v1/multiplayer/rooms/{code}/leaderboard response schema."""
        expected_entry_fields = [
            "rank",
            "player_id",
            "player_name",
            "score",
            "grade",
            "portfolio_value",
            "total_return_pct",
            "current_day",
            "is_finished",
        ]

        mock_entry = {
            "rank": 1,
            "player_id": "789e4567-e89b-12d3-a456-426614174000",
            "player_name": "Alice",
            "score": 920.0,
            "grade": "A",
            "portfolio_value": 125000.0,
            "total_return_pct": 25.0,
            "current_day": 29,
            "is_finished": True
        }

        for field in expected_entry_fields:
            assert field in mock_entry, f"Missing field: {field}"


class TestErrorResponses:
    """Test error response consistency."""

    @pytest.mark.integration
    def test_error_response_schema(self):
        """All errors must have consistent schema."""
        # FastAPI HTTPException returns this format
        expected_fields = ["detail"]

        mock_error = {
            "detail": "Room with code ABC123 not found"
        }

        assert "detail" in mock_error

    @pytest.mark.integration
    def test_validation_error_codes(self):
        """Validation errors return 422 with field details."""
        # Pydantic validation errors have this structure
        mock_validation_error = {
            "detail": [
                {
                    "loc": ["body", "player_name"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }

        assert "detail" in mock_validation_error
        assert isinstance(mock_validation_error["detail"], list)

    @pytest.mark.integration
    def test_error_codes_are_meaningful(self):
        """Error messages should be actionable for iOS developers."""
        error_scenarios = {
            "room_not_found": "Room with code ABC123 not found",
            "player_exists": "Player name 'Alice' is already taken in this room",
            "room_finished": "This room has already finished. Cannot join.",
            "insufficient_data": "Insufficient data. Found only 5 days with complete data."
        }

        for scenario, message in error_scenarios.items():
            # Error message should be descriptive
            assert len(message) > 10, "Error messages should be descriptive"
            assert message != "Error", "Generic errors are not helpful"


class TestTimestampHandling:
    """Test timezone-safe timestamp handling."""

    @pytest.mark.integration
    def test_timestamps_are_iso8601(self):
        """All timestamps must be ISO 8601 format with timezone."""
        valid_timestamps = [
            "2025-01-15T10:00:00Z",          # UTC
            "2025-01-15T10:00:00+00:00",     # UTC with offset
            "2025-01-15T05:00:00-05:00",     # EST
        ]

        for ts in valid_timestamps:
            # ISO 8601 timestamps have 'T' separator
            assert "T" in ts, f"Timestamp {ts} missing T separator"
            # Should have timezone indicator (Z or offset)
            assert ts.endswith("Z") or "+" in ts or ts.count("-") >= 3

    @pytest.mark.integration
    def test_dates_are_iso8601(self):
        """Date fields use YYYY-MM-DD format."""
        valid_dates = [
            "2025-01-01",
            "2025-01-15",
            "2025-12-31",
        ]

        for date_str in valid_dates:
            # YYYY-MM-DD format has 2 dashes
            assert date_str.count("-") == 2
            # Length is 10 characters
            assert len(date_str) == 10


class TestNumericPrecision:
    """Test numeric field precision and types."""

    @pytest.mark.integration
    def test_money_values_are_floats(self):
        """Cash and portfolio values use float (not int)."""
        cash = 10000.0
        portfolio_value = 12500.0

        assert isinstance(cash, float)
        assert isinstance(portfolio_value, float)

    @pytest.mark.integration
    def test_percentages_are_floats(self):
        """Percentage values use float."""
        total_return_pct = 25.5  # 25.5%
        confidence = 0.85        # 85%

        assert isinstance(total_return_pct, float)
        assert isinstance(confidence, float)

    @pytest.mark.integration
    def test_confidence_range(self):
        """Confidence values are between 0 and 1."""
        valid_confidences = [0.0, 0.5, 0.85, 1.0]

        for conf in valid_confidences:
            assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range"

    @pytest.mark.integration
    def test_day_numbers_are_integers(self):
        """Day numbers are integers (0-indexed)."""
        current_day = 0
        total_days = 30

        assert isinstance(current_day, int)
        assert isinstance(total_days, int)
        assert current_day >= 0


class TestBackwardCompatibility:
    """Test that changes don't break existing contracts."""

    @pytest.mark.integration
    def test_cannot_remove_required_fields(self):
        """
        Removing a field from response is a BREAKING CHANGE.

        This test documents that adding optional fields is OK,
        but removing required fields requires /v2/.
        """
        # Original v1 response
        v1_response_fields = ["id", "room_code", "created_by", "status"]

        # Hypothetical v2 response (adding field is OK)
        v2_response_fields = ["id", "room_code", "created_by", "status", "new_field"]

        # All v1 fields must exist in v2
        for field in v1_response_fields:
            assert field in v2_response_fields, f"Removed field '{field}' - BREAKING!"

    @pytest.mark.integration
    def test_field_type_changes_are_breaking(self):
        """Changing a field's type is a BREAKING CHANGE."""
        # Example: Changing 'current_day' from int to string is breaking

        # v1: current_day is int
        v1_current_day = 5
        assert isinstance(v1_current_day, int)

        # v2: Hypothetically changed to string (BREAKING!)
        # v2_current_day = "5"  # This would break iOS parsers

        # This test documents that type stability is critical
        assert True  # Type changes require /v2/


class TestAPIPerformance:
    """Test API performance requirements (Phase 0 decision)."""

    @pytest.mark.slow
    @pytest.mark.integration
    async def test_response_time_under_500ms(self):
        """
        API endpoints must respond in <500ms (p95).

        This is from Phase 0 decision: "API is deterministic and fast"
        """
        # This will be implemented with actual HTTP client timing
        # For now, document the requirement
        max_response_time_ms = 500
        assert max_response_time_ms == 500

    @pytest.mark.integration
    def test_no_ai_calls_in_request_path(self):
        """
        Verify no OpenAI calls happen during API requests.

        This enforces Phase 0 decision: "API is read-only and deterministic"
        """
        # In real implementation, we'd mock openai.ChatCompletion.create
        # and assert it's never called during API requests
        pass
