# Phase 0 — Testing Architecture Decisions

**Status**: 🟢 Active
**Owner**: Engineering Team
**Date**: 2025-12-29
**Purpose**: Lock down testing principles before iOS development begins

---

## Why Phase 0 Exists

Before writing a single test, we must agree on **how the system works** so that tests validate the right behavior. This document is the **single source of truth** for testing strategy.

**Rule**: Once these decisions are locked, all tests must enforce them.

---

## 1. Single Source of Truth: Backend Game Engine

### Decision
**The backend owns all game state. Clients (web, iOS) are view-only.**

### What This Means
- Game state lives in PostgreSQL (via FastAPI backend)
- Trade execution, score calculation, day advancement happen **server-side only**
- Clients send commands (buy/sell/advance), backend validates and executes
- Clients poll/subscribe for state updates

### Testing Requirements
```python
# ✅ REQUIRED: Backend tests must verify
- Cash balance never goes negative
- Holdings always reconcile (shares * price = value)
- Day can advance exactly once
- Game end state is immutable
- All calculations are deterministic

# ❌ FORBIDDEN: Client-side tests must NOT
- Calculate scores locally
- Validate trades without server
- Advance game day independently
```

### API Contract
```
POST /api/v1/games/{game_id}/trade
POST /api/v1/games/{game_id}/advance-day
GET  /api/v1/games/{game_id}/state

# All mutations return full updated game state
# Clients replace local state, never merge
```

---

## 2. No Client-Side Game Logic

### Decision
**Clients render UI and display data. Period.**

### What This Means
- iOS app is a **thin client** (like web app)
- No business logic in Swift/React
- No local score calculation, no trade validation
- UI reflects backend state exactly

### Testing Requirements
```swift
// ❌ iOS MUST NOT have tests like:
func testCalculatePortfolioValue() { ... }
func testValidateTrade() { ... }
func testAdvanceDay() { ... }

// ✅ iOS SHOULD have tests like:
func testDisplayGameState() { ... }
func testHandleTradeError() { ... }
func testSyncWithBackend() { ... }
```

### Why This Matters
- Backend changes don't require iOS updates
- Bugs are reproducible on server
- App Store review delays don't block fixes

---

## 3. Versioned APIs (/v1/)

### Decision
**All API routes start with `/api/v1/`**

### What This Means
- Breaking changes require new version (`/api/v2/`)
- `/v1/` endpoints remain stable indefinitely
- iOS apps can't force-update, so API must be backward-compatible

### Testing Requirements
```python
# ✅ REQUIRED: Contract tests
def test_v1_response_schema_stable():
    """Ensure /v1/games/{id}/state returns same fields"""
    response = client.get("/api/v1/games/123/state")
    assert "current_day" in response.json()
    assert "cash" in response.json()
    # ... all expected fields

def test_v1_error_codes_stable():
    """Error codes must not change"""
    response = client.post("/api/v1/games/123/trade", json=invalid_trade)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_TRADE"
```

### Deprecation Policy
- `/v1/` supported for **minimum 12 months** after `/v2/` ships
- Deprecation warnings returned in headers:
  ```
  X-API-Deprecation: /v1/ will be deprecated on 2026-12-29
  X-API-Upgrade: Use /v2/games/{id}/state instead
  ```

---

## 4. Deterministic Game Clock

### Decision
**Game time is controlled by server, not real-world time.**

### What This Means
- Day advances only when teacher clicks "Advance Day" (sync mode) or timer expires (async)
- No drift between clients
- Game can be paused indefinitely
- All clients see same "current_day" value

### Testing Requirements
```python
# ✅ REQUIRED: Time synchronization tests
@freeze_time("2025-01-15 14:00:00")
async def test_day_advance_deterministic():
    """All clients see same day after advance"""
    game = await create_game(mode="sync_manual")
    await advance_day(game.id)

    state1 = await get_game_state(game.id, user_id="student1")
    state2 = await get_game_state(game.id, user_id="student2")

    assert state1["current_day"] == state2["current_day"]
    assert state1["current_day"] == 2

# ✅ REQUIRED: No double-advance
async def test_cannot_advance_day_twice():
    """Day 1 → Day 2 is possible, Day 2 → Day 2 is not"""
    await advance_day(game.id)  # Day 1 → Day 2

    with pytest.raises(GameError, match="Day already advanced"):
        await advance_day(game.id)  # Should fail
```

### Clock Behavior by Mode

| Mode | Clock Behavior | Test Focus |
|------|----------------|------------|
| Solo | Player-controlled | Test button idempotency |
| Async | Auto-advance timer | Test timer doesn't skip days |
| Sync Manual | Teacher-controlled | Test only teacher can advance |
| Sync Auto | Auto-advance + teacher override | Test override stops timer |

---

## 5. AI Behind Feature Flag

### Decision
**Game functions identically with AI disabled.**

### What This Means
- AI recommendations are **advisory only**
- Trading works without AI
- Scoring works without AI (just no bonus points)
- AI is feature-flagged per game

### Testing Requirements
```python
# ✅ REQUIRED: AI-off tests
async def test_game_without_ai():
    """Full game playthrough with AI disabled"""
    game = await create_game(enable_ai=False)

    # Should complete normally
    for day in range(1, 31):
        await execute_trade(game.id, action="BUY", symbol="AAPL")
        await advance_day(game.id)

    final_state = await get_game_state(game.id)
    assert final_state["status"] == "completed"
    assert final_state["score"] >= 0  # Score still calculated

# ✅ REQUIRED: AI failure handling
async def test_ai_timeout_graceful():
    """When OpenAI times out, game continues"""
    with mock_openai_timeout():
        recommendations = await get_recommendations(game.id, day=5)

    # Should return fallback (no recommendations)
    assert recommendations == []
```

### AI Feature Flag
```python
# Environment variable controls AI globally
ENABLE_AI=false  # Disable for all games

# Per-game override in database
games.enable_ai = True/False
```

---

## 6. API is Read-Only and Deterministic

### Decision
**No LLM calls in API request handlers. Ever.**

### What This Means
- All AI recommendations are **pre-computed offline**
- API serves cached/stored results only
- Response times < 500ms (p95)
- Responses are cacheable

### Testing Requirements
```python
# ✅ REQUIRED: Performance tests
async def test_api_response_time():
    """API endpoints must respond in <500ms"""
    start = time.time()
    response = await client.get("/api/v1/games/123/state")
    duration = time.time() - start

    assert duration < 0.5  # 500ms

# ✅ REQUIRED: No AI in request path
async def test_no_llm_calls_during_request():
    """Mock OpenAI to ensure it's never called"""
    with mock.patch("openai.ChatCompletion.create") as mock_ai:
        mock_ai.side_effect = Exception("AI should not be called!")

        # These should all work without triggering AI
        await client.get("/api/v1/games/123/recommendations")
        await client.post("/api/v1/games/123/trade", json=trade_data)

        mock_ai.assert_not_called()
```

### Pre-computation Strategy
- Recommendations generated by **offline scheduler** (every 6 hours)
- Stored in `game_recommendations` table
- API reads from database, never calls OpenAI

---

## Testing Principles Summary

### Golden Rules
1. **Backend is source of truth** → Test server logic exhaustively
2. **Clients are thin** → Test rendering, not business logic
3. **APIs are versioned** → Test backward compatibility
4. **Time is deterministic** → Use `freezegun` in tests
5. **AI is optional** → Test game without AI first
6. **APIs are fast** → No blocking operations in handlers

### What Gets Tested Where

| Component | Test Type | Purpose |
|-----------|-----------|---------|
| **Backend** | Unit + Integration | Game rules, trade logic, scoring |
| **API** | Contract + Performance | Schema stability, response times |
| **Multiplayer** | Integration | Time sync, concurrency, race conditions |
| **Web** | E2E (Playwright) | Core flows work end-to-end |
| **iOS** | UI + Integration | Display, API calls, error handling |

### Test Pyramid

```
        /\
       /  \     E2E (10%)    - Critical user flows only
      /----\
     /      \   Integration (30%) - Multiplayer, time sync
    /--------\
   /          \ Unit (60%)   - Game engine, trade rules
  /____________\
```

---

## Exit Criteria

**Phase 0 is complete when:**

- [ ] All team members have reviewed this document
- [ ] Decisions are documented in code via comments
- [ ] Test directory structure created (Phase 1 setup)
- [ ] `pytest.ini` configured with markers for test types

**Next Phase**: Phase 1 - Backend Contract & Logic Tests

---

## Appendix: Technology Stack

### Backend Testing
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `freezegun` - Time mocking
- `httpx.AsyncClient` - API testing
- `testcontainers-python` - Isolated Postgres

### Frontend Testing (Future)
- `Playwright` - E2E testing (web + mobile)
- `pytest-playwright` - Python integration

### iOS Testing (Future)
- `XCTest` - Unit tests (UI rendering only)
- `XCUITest` - UI integration tests

---

**Document Version**: 1.0
**Last Updated**: 2025-12-29
**Approved By**: [Pending Team Review]
