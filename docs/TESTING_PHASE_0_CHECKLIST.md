# Phase 0 - Testing Architecture Checklist

**Status**: 🟡 In Progress
**Target Completion**: Before Phase 1 begins

---

## Prerequisites

- [ ] Team has reviewed [TESTING_PHASE_0.md](TESTING_PHASE_0.md)
- [ ] All engineers agree on architectural decisions
- [ ] Testing dependencies installed

---

## Setup Tasks

### 1. Install Testing Dependencies

```bash
cd api
source venv/bin/activate
pip install pytest pytest-asyncio freezegun httpx
```

**Verification:**
```bash
pytest --version
# Should show: pytest 9.0.2 or higher
```

- [ ] pytest installed
- [ ] pytest-asyncio installed
- [ ] freezegun installed
- [ ] httpx installed

### 2. Verify Test Infrastructure

```bash
cd api
pytest tests/test_phase0_setup.py -v
```

**Expected Output:**
```
tests/test_phase0_setup.py::TestPhase0Setup::test_pytest_working PASSED
tests/test_phase0_setup.py::TestPhase0Setup::test_markers_registered PASSED
tests/test_phase0_setup.py::TestPhase0Decisions::test_backend_is_source_of_truth PASSED
...
tests/test_phase0_setup.py::test_phase0_complete PASSED

============ 10 passed in 0.12s ============
```

- [ ] All Phase 0 setup tests pass
- [ ] Test markers work (`-m unit`, `-m integration`)
- [ ] Async tests work

### 3. Document Code Architecture

Add comments to critical files documenting Phase 0 decisions:

**api/app/main.py** (already has good comments ✅)
```python
"""
CRITICAL DESIGN PRINCIPLES:
1. This API is READ-ONLY and deterministic
2. NO AI/LLM calls in request handlers
...
"""
```

**api/app/routes/game.py**
- [ ] Add comment: "All game state mutations happen here, backend is source of truth"

**api/app/routes/multiplayer.py**
- [ ] Add comment: "Deterministic game clock - server controls time progression"

### 4. Create Test Database

```bash
# Create test database (separate from dev database)
createdb stock_ai_test

# Or via Docker:
docker exec -it postgres psql -U postgres -c "CREATE DATABASE stock_ai_test;"
```

- [ ] Test database created
- [ ] Test database URL configured in `.env`:
  ```
  TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/stock_ai_test
  ```

### 5. Update Documentation

- [x] Create TESTING_PHASE_0.md
- [x] Create test directory structure
- [x] Create pytest.ini configuration
- [ ] Update main README.md with testing section
- [ ] Add Phase 0 to TESTING.md

---

## Architectural Decisions - Sign-off

Each team member confirms understanding:

| Decision | Engineer 1 | Engineer 2 | Engineer 3 |
|----------|------------|------------|------------|
| Backend is source of truth | [ ] | [ ] | [ ] |
| No client-side game logic | [ ] | [ ] | [ ] |
| Versioned APIs (/v1/) | [ ] | [ ] | [ ] |
| Deterministic game clock | [ ] | [ ] | [ ] |
| AI behind feature flag | [ ] | [ ] | [ ] |
| API is read-only/deterministic | [ ] | [ ] | [ ] |

---

## Exit Criteria

Phase 0 is **COMPLETE** when all boxes are checked:

### Required
- [ ] All testing dependencies installed
- [ ] `pytest tests/test_phase0_setup.py` passes
- [ ] Test directory structure created (unit/, integration/, e2e/)
- [ ] pytest.ini configured with markers
- [ ] Test database created and accessible
- [ ] All team members have signed off on decisions

### Optional (Nice to Have)
- [ ] CI/CD pipeline skeleton created (GitHub Actions)
- [ ] Test coverage reporting configured
- [ ] Pre-commit hooks for running tests

---

## Next Steps

Once Phase 0 is complete:

1. **Move to Phase 1**: Backend Contract & Logic Tests
   - Write game engine invariant tests
   - Write trade rule validation tests
   - Write scoring calculation tests

2. **Create Phase 1 Test Files**:
   ```bash
   api/tests/unit/test_game_engine.py
   api/tests/unit/test_trade_rules.py
   api/tests/unit/test_scoring.py
   ```

3. **Run Phase 1 Tests**:
   ```bash
   pytest tests/unit/ -v
   ```

---

## Quick Commands Reference

```bash
# Run all tests
pytest

# Run only Phase 0 setup tests
pytest tests/test_phase0_setup.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m unit

# Run only fast tests (skip slow tests)
pytest -m "not slow"

# Run specific test file
pytest tests/unit/test_game_engine.py -v

# Run specific test function
pytest tests/unit/test_game_engine.py::test_cash_never_negative -v
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-29
