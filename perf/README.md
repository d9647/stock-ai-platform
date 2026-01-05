# Performance Testing with K6

Performance tests for the Stock AI Platform using [K6](https://k6.io/) with Prometheus and Grafana monitoring.

## 🚀 Quick Start

### Option 1: Basic Testing (Console Output)

```bash
# Run basic test - shows full p50/p95/p99 in console
k6 run perf/multiplayer-load.js
```

### Option 2: With Grafana Dashboard (Recommended)

```bash
# 1. Start monitoring stack
cd perf
docker compose -f docker-compose.monitoring.yml up -d

# 2. Start backend
cd ../api && source venv/bin/activate && uvicorn app.main:app --reload

# 3. Run test with metrics export
cd ../perf
k6 run --duration 30s --vus 5 \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js

# 4. View dashboard
open http://localhost:3001
# Login: admin/admin
# Navigate: Dashboards → Performance Testing → Backend & K6 Performance
```

## 📊 What You Get

### Two Perspectives

```
┌─────────────────────────────────┐
│  K6 Client (p99 only)           │  ← What users experience
│  End-to-end latency             │     (includes network)
└─────────────┬───────────────────┘
              │
              ↓
┌─────────────────────────────────┐
│  Backend Server (p50/p95/p99)   │  ← What server is doing
│  Processing time only           │     (excludes network)
└─────────────────────────────────┘
```

**Backend Metrics** (Grafana):
- Full p50/p95/p99 via histogram buckets
- Updates every 5 seconds automatically
- Request rate, concurrency, success rate
- Available 24/7

**K6 Metrics** (Grafana):
- p99 only (K6 Prometheus limitation)
- Available during/after tests
- End-to-end latency

**K6 Console** (Terminal):
- Full p50/p95/p99 for all metrics
- Most accurate for SLO validation
- Available during test run

## 🧪 Running Tests

### Basic Load Testing Patterns

```bash
cd perf

# Quick test (10 VUs, 2 minutes) - default
k6 run multiplayer-load.js

# Light load with gradual ramp (30 VUs peak)
k6 run \
  --stage 30s:5 --stage 1m:15 --stage 2m:30 \
  --stage 2m:30 --stage 1m:15 --stage 30s:0 \
  multiplayer-load.js

# Medium load with gradual ramp (60 VUs peak)
k6 run \
  --stage 1m:10 --stage 2m:30 --stage 2m:60 \
  --stage 3m:60 --stage 2m:30 --stage 1m:10 --stage 1m:0 \
  multiplayer-load.js

# Heavy load with gradual ramp (100 VUs peak)
k6 run \
  --stage 1m:10 --stage 2m:30 --stage 2m:60 --stage 2m:100 \
  --stage 4m:100 --stage 2m:60 --stage 2m:30 --stage 1m:10 --stage 1m:0 \
  multiplayer-load.js

# Stress test to find breaking point
k6 run \
  --stage 1m:50 --stage 2m:50 --stage 1m:200 --stage 2m:200 \
  --stage 1m:50 --stage 1m:50 --stage 1m:0 \
  multiplayer-load.js
```

### With Grafana Monitoring

**CRITICAL**: Always use the `-o experimental-prometheus-rw` flag to send metrics to Grafana!

```bash
# ✅ CORRECT - metrics sent to Grafana
k6 run --vus 60 --duration 5m \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js

# ❌ WRONG - no Grafana metrics (console only)
k6 run --vus 60 --duration 5m multiplayer-load.js
```

### Environment Variables

```bash
# Use existing room
k6 run -e ROOM_CODE=ABC123 multiplayer-load.js

# Custom API URL
k6 run -e BASE_URL=https://api.example.com multiplayer-load.js
```

## 📈 Load Test Patterns Explained

### Gradual Ramp-Up/Ramp-Down

Always use gradual ramping to avoid shocking the server:

**Light Load** (~7 min, peak 30 VUs):
```
5 → 15 → 30 → [sustain] → 30 → 15 → 5 → 0 users
```
- Good for CI/CD pipelines
- Validates basic capacity

**Medium Load** (~12 min, peak 60 VUs):
```
10 → 30 → 60 → [sustain] → 60 → 30 → 10 → 0 users
```
- Target production capacity
- Realistic load simulation

**Heavy Load** (~17 min, peak 100 VUs):
```
10 → 30 → 60 → 100 → [sustain] → 100 → 60 → 30 → 10 → 0 users
```
- Maximum expected capacity
- Pre-deployment validation

**Why Gradual?**
- ✅ Realistic user arrival pattern
- ✅ Server can adapt to load
- ✅ Won't crash production
- ✅ Find real capacity limits

## 📈 Understanding Results

### Console Output (Most Accurate)

```
✓ join room: status 201
✓ join room: has player_id

join_room_latency............: avg=120ms min=50ms med=110ms max=300ms p(90)=180ms p(95)=220ms p(99)=280ms
get_state_latency............: avg=80ms  min=30ms med=75ms  max=200ms p(90)=120ms p(95)=150ms p(99)=180ms
join_room_success_rate.......: 100.00%

http_reqs.....................: 1234   20.5/s
http_req_duration.............: avg=95ms min=30ms med=85ms max=400ms p(95)=180ms
```

**Use console for**: Accurate SLO validation (full percentiles)

### Grafana Dashboard

- **Backend section**: Shows p50/p95/p99 from server metrics
- **K6 section**: Shows p99 from load test metrics
- **Use dashboard for**: Visual trends, historical analysis, real-time monitoring

## 🎯 Performance Targets

### SLOs

- **Join room**: p95 < 300ms
- **Get state**: p95 < 200ms
- **Get news**: p95 < 300ms
- **Get recommendations**: p95 < 400ms
- **Update player**: p95 < 300ms
- **Success rate**: > 99%

### Recommended Load

- **Normal**: 50 concurrent users
- **Peak**: 100 concurrent users
- **Stress**: 200+ concurrent users

## ✅ Ensuring Metrics Appear in Grafana

### Quick Verification

Before running tests:

```bash
# Run verification script
./verify-monitoring.sh
```

**Expected output**:
- ✅ Prometheus running
- ✅ Grafana running
- ✅ Backend running
- ✅ Prometheus scraping backend

**If any ❌**:
1. Start monitoring: `./start-monitoring.sh`
2. Start backend: `cd ../api && uvicorn app.main:app --reload`
3. Wait 10 seconds and verify again

### The Monitoring Flag

**CRITICAL**: Always include `-o experimental-prometheus-rw` to send metrics to Grafana:

```bash
# This flag does two things:
# 1. Tells K6 to push metrics to Prometheus
# 2. Specifies the Prometheus remote write endpoint

k6 run --vus 50 --duration 5m \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js
```

**Without this flag**, K6 metrics will NOT appear in Grafana (only console output).

### Workflow

```bash
# 1. Start monitoring stack (do once)
cd perf
./start-monitoring.sh

# 2. Start backend (separate terminal)
cd api
source venv/bin/activate
uvicorn app.main:app --reload

# 3. Verify everything is ready
cd perf
./verify-monitoring.sh

# 4. Open Grafana BEFORE running test
open http://localhost:3001
# Navigate: Dashboards → Performance Testing → Backend & K6 Performance

# 5. Run test WITH monitoring
k6 run --vus 60 --duration 5m \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js

# 6. Watch Grafana update in real-time!
```

## 🛠️ Troubleshooting

### Grafana Shows "No Data"

**Backend section empty**:
```bash
# Check backend running
curl http://localhost:8000/health

# Check Prometheus scraping
open http://localhost:9090/targets
# stockai-api should show "UP"
```

**K6 section empty**:
```bash
# This is normal - K6 metrics only appear during/after tests
# Make sure you used -o experimental-prometheus-rw flag!

k6 run --duration 30s --vus 5 \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js
```

### Test Fails

```bash
# Ensure results directory exists
mkdir -p results

# Check backend is accessible
curl http://localhost:8000/health
```

### Metrics Not Persisting

```bash
# Check Prometheus is storing data
curl -s 'http://localhost:9090/api/v1/query?query=k6_join_room_latency_p99' | python3 -m json.tool

# Should return metrics from recent test
```

## 📚 Documentation

### In `docs/` Directory

- **[docs/DASHBOARD.md](docs/DASHBOARD.md)** - Complete Grafana dashboard guide
- **[docs/METRICS.md](docs/METRICS.md)** - All available metrics reference
- **[docs/MONITORING.md](docs/MONITORING.md)** - Monitoring stack architecture
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Design decisions

### What's in the Test

The `multiplayer-load.js` test simulates realistic gameplay where each VU (student):
1. Joins game room once
2. For each game day:
   - Gets news articles
   - Reviews AI recommendations
   - Checks game data
   - Views leaderboard
   - Makes trades (buy/sell stocks)
   - Updates player state
   - Advances to next day

## 🔗 Quick Links

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Backend Metrics**: http://localhost:8000/metrics
- **API Docs**: http://localhost:8000/docs

## 💡 Pro Tips

1. **Always use `-o experimental-prometheus-rw`** when you want Grafana metrics
2. **Check console output** for accurate p50/p95/p99 percentiles
3. **Backend metrics update automatically** - no test needed
4. **K6 metrics only appear during/after tests**
5. **Use both perspectives** - backend for debugging, K6 for user experience
6. **Gradual ramp-up/ramp-down** - prevents server shock, finds real limits

---

📖 For detailed guides, see **[docs/](docs/)** directory.
