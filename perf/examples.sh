#!/bin/bash
# Examples of running K6 performance tests with different configurations

# ============================================================================
# BASIC EXAMPLES
# ============================================================================

# 1. Run smoke test
k6 run perf/smoke.js

# 2. Run multiplayer test with default settings (10 VUs, 2 minutes)
k6 run perf/multiplayer-load.js

# ============================================================================
# CUSTOM VUS AND DURATION
# ============================================================================

# 3. Run with 50 concurrent users for 5 minutes
k6 run --vus 50 --duration 5m perf/multiplayer-load.js

# 4. Run with 100 concurrent users for 10 minutes
k6 run --vus 100 --duration 10m perf/multiplayer-load.js

# ============================================================================
# PROGRESSIVE LOAD (STAGES)
# ============================================================================

# 5. Ramp up from 0 to 50 users over 1 minute, then maintain for 2 minutes
k6 run --stage 1m:50 --stage 2m:50 perf/multiplayer-load.js

# 6. Progressive load: 10 → 50 → 100 → 0 users
k6 run \
  --stage 30s:10 \
  --stage 1m:50 \
  --stage 1m:100 \
  --stage 2m:100 \
  --stage 1m:0 \
  perf/multiplayer-load.js

# 7. Spike test: normal → spike → recovery
k6 run \
  --stage 1m:50 \
  --stage 2m:50 \
  --stage 30s:200 \
  --stage 1m:200 \
  --stage 1m:50 \
  --stage 1m:0 \
  perf/multiplayer-load.js

# ============================================================================
# USING ENVIRONMENT VARIABLES
# ============================================================================

# 8. Use existing room (don't create new one)
k6 run -e ROOM_CODE=ABC123 perf/multiplayer-load.js

# 9. Test against different API URL
k6 run -e BASE_URL=https://api.staging.example.com perf/multiplayer-load.js

# 10. Combine environment variables
k6 run \
  -e BASE_URL=http://localhost:8000 \
  -e ROOM_CODE=XYZ789 \
  --vus 30 \
  --duration 3m \
  perf/multiplayer-load.js

# ============================================================================
# OUTPUT AND REPORTING
# ============================================================================

# 11. Save results to JSON file
k6 run --out json=perf/results/test-results.json perf/multiplayer-load.js

# 12. Save with timestamp
k6 run --out json=perf/results/test-$(date +%Y%m%d-%H%M%S).json perf/multiplayer-load.js

# 13. Run with verbose output
k6 run --verbose perf/multiplayer-load.js

# 14. Quiet mode (only show summary)
k6 run --quiet perf/multiplayer-load.js

# ============================================================================
# SPECIFIC TEST SCENARIOS
# ============================================================================

# 15. Single classroom (30 students)
k6 run --vus 30 --duration 5m perf/multiplayer-load.js

# 16. Peak hour (100 students, progressive join)
k6 run --stage 2m:100 --stage 5m:100 --stage 1m:0 perf/multiplayer-load.js

# 17. Endurance test (30 users for 15 minutes)
k6 run --vus 30 --duration 15m perf/multiplayer-load.js

# 18. Quick stress test
k6 run --vus 200 --duration 2m perf/multiplayer-load.js

# ============================================================================
# ADVANCED CONFIGURATIONS
# ============================================================================

# 19. Set specific number of iterations per VU
k6 run --vus 10 --iterations 100 perf/multiplayer-load.js

# 20. Disable thresholds (useful for exploration)
k6 run --no-thresholds perf/multiplayer-load.js

# 21. Override specific threshold
k6 run \
  --threshold "http_req_duration=p(95)<1000" \
  perf/multiplayer-load.js

# ============================================================================
# REAL-WORLD SCENARIOS
# ============================================================================

# 22. Teacher creates room, 30 students join over 2 minutes, play for 5 minutes
k6 run --stage 2m:30 --stage 5m:30 --stage 1m:0 perf/multiplayer-load.js

# 23. Find breaking point (progressive load until failure)
k6 run \
  --stage 1m:50 \
  --stage 1m:100 \
  --stage 1m:150 \
  --stage 1m:200 \
  --stage 1m:250 \
  --stage 1m:300 \
  perf/multiplayer-load.js

# 24. Sustained load test (simulate full school day)
k6 run --vus 50 --duration 30m perf/multiplayer-load.js

# ============================================================================
# CI/CD EXAMPLES
# ============================================================================

# 25. Quick CI test (fast, minimal load)
k6 run --vus 5 --duration 30s perf/multiplayer-load.js

# 26. Nightly full test
k6 run \
  --stage 2m:50 \
  --stage 10m:50 \
  --stage 2m:0 \
  --out json=perf/results/nightly-$(date +%Y%m%d).json \
  perf/multiplayer-load.js

# ============================================================================
# DEBUGGING
# ============================================================================

# 27. Run with single VU to debug
k6 run --vus 1 --iterations 1 perf/multiplayer-load.js

# 28. Run with HTTP debug output
k6 run --http-debug perf/multiplayer-load.js

# 29. Run with full debug output
k6 run --http-debug=full perf/multiplayer-load.js
