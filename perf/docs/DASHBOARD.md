# Grafana Dashboard Guide

Complete guide to using the performance monitoring dashboard.

## Quick Start (5 Minutes)

```bash
# 1. Start monitoring stack
cd perf
docker compose -f docker-compose.monitoring.yml up -d

# 2. Start backend
cd ../api && source venv/bin/activate
uvicorn app.main:app --reload

# 3. Run test
cd ../perf
k6 run --duration 30s --vus 5 \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js

# 4. Open Grafana
open http://localhost:3001
# Login: admin/admin
# Navigate: Dashboards → Performance Testing → Backend & K6 Performance
```

## Dashboard Overview

The dashboard shows **two perspectives**:

### Top Section: Backend Server Metrics
- **What it measures**: Server processing time only (excludes network)
- **Percentiles available**: p50, p95, p99 (full histogram data)
- **Updates**: Every 5 seconds automatically
- **Data source**: FastAPI prometheus-fastapi-instrumentator

**Panels**:
1. Join Room Latency (p50/p95/p99)
2. Get Room State Latency (p50/p95/p99)
3. Backend Request Rate
4. Concurrent Requests
5. Success Rate
6. HTTP Error Rate
7. p95 Latency by Endpoint
8. Request Rate by Endpoint

### Bottom Section: K6 Client Metrics
- **What it measures**: End-to-end latency (network + server)
- **Percentiles available**: p99 only (K6 Prometheus limitation)
- **Updates**: During and after K6 tests
- **Data source**: K6 remote write to Prometheus

**Panels**:
1. Join Room Latency (p99)
2. All Endpoints p99 Latency
3. Join Room Success Rate
4. HTTP Error Rate

## Why Two Perspectives?

```
┌─────────────────────────────────┐
│  K6 Client Metrics (p99 only)   │  ← What users experience
│  Latency = 150ms                │     (includes network: 30ms)
└─────────────┬───────────────────┘
              │
              ↓
┌─────────────────────────────────┐
│  Backend Server Metrics         │  ← What server is doing
│  Latency = 120ms (p95)          │     (processing only)
└─────────────────────────────────┘
```

**Use Backend Metrics** when:
- Debugging slow endpoints
- Monitoring production capacity
- Setting up alerts
- Need full p50/p95/p99

**Use K6 Metrics** when:
- Load testing
- Validating end-to-end SLOs
- Testing user experience
- Measuring network impact

## Common Scenarios

### Scenario 1: Capacity Testing

**Goal**: Find backend capacity limit

```bash
k6 run --vus 100 --duration 5m \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js
```

**Watch in dashboard**:
- Concurrent Requests panel (should stay < 100)
- Backend p95 Latency (should stay < 200ms)
- Success Rate (should stay > 99%)

When any metric degrades, you've found the capacity limit.

### Scenario 2: Debugging Slow Endpoint

**Goal**: Identify bottleneck location

```bash
k6 run --vus 20 --duration 2m \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js
```

**Compare metrics**:
- Backend p95 = 200ms → Server processing time
- K6 p99 = 250ms → End-to-end time
- Difference = 50ms → Network overhead

**If backend high**: Optimize server code/database
**If K6 high but backend low**: Network or serialization issue

### Scenario 3: SLO Validation

**Goal**: Ensure all endpoints meet targets

```bash
k6 run --vus 50 --duration 5m multiplayer-load.js
```

**Check console output** for full percentiles:
```
join_room_latency: p(95)=220ms ✅ < 300ms SLO
get_state_latency: p(95)=150ms ✅ < 200ms SLO
```

**Check dashboard** for visual confirmation and trends.

### Scenario 4: Production Monitoring

**Goal**: Continuous monitoring

**No action needed** - Backend metrics auto-update every 5s.

**Watch for**:
- Error rate spikes
- Latency increases
- High concurrent requests

## K6 Prometheus Limitation

### Why Only p99 from K6?

K6's `experimental-prometheus-rw` output has fundamental limitations:
- Only exports **pre-aggregated p99 values**
- No histogram buckets → can't compute p50/p95
- This is a K6 design choice, not a configuration issue

### Getting Full Percentiles from K6

**Option 1**: Check console output
```bash
k6 run multiplayer-load.js
# Shows: p(50)=110ms p(95)=220ms p(99)=280ms
```

**Option 2**: Use backend metrics
- Backend has full histogram data
- Shows server-side p50/p95/p99
- Good for production monitoring

**Option 3**: Use K6 JSON output
```bash
k6 run --out json=results.json multiplayer-load.js
# Analyze results.json for detailed percentiles
```

## Troubleshooting

### Dashboard Shows "No Data"

**Backend Section Empty**:

1. Check backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check Prometheus scraping:
   ```bash
   curl http://localhost:9090/targets
   # stockai-api should show "UP"
   ```

3. Verify metrics exist:
   ```bash
   curl http://localhost:8000/metrics | grep http_requests_total
   ```

**K6 Section Empty** (This is normal):

K6 metrics only appear during/after tests.

**Solution**: Run a test
```bash
k6 run --duration 30s --vus 5 \
  -o experimental-prometheus-rw=http://localhost:9090/api/v1/write \
  multiplayer-load.js
```

### Different Values: Backend vs K6

**This is expected!**

- Backend measures server processing only
- K6 measures end-to-end (server + network)
- Difference = network overhead

**Example**:
- Backend p95 = 120ms
- K6 p99 = 150ms
- Network = 30ms ✅ Normal

### Time Range Issues

1. Top right: Select "Last 15 minutes"
2. For K6 metrics, ensure test ran in this window
3. Adjust range as needed for analysis

## Advanced Queries

### Find Network Overhead

Compare backend and K6 metrics to calculate network latency:

```promql
# K6 end-to-end p99
k6_join_room_latency_p99

# Backend server processing p99
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{handler="/api/v1/multiplayer/rooms/join"}[5m])) by (le)
)

# Network overhead = difference
```

### Slowest Endpoint

```promql
topk(5,
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le)
  )
)
```

### Error Rate by Endpoint

```promql
sum(rate(http_requests_total{status=~"[45].."}[5m])) by (handler)
/
sum(rate(http_requests_total[5m])) by (handler)
```

### Peak Load Metrics

```promql
# Max concurrent requests in last hour
max_over_time(sum(http_requests_inprogress)[1h])

# Peak request rate
max_over_time(sum(rate(http_requests_total[1m]))[1h])
```

## Best Practices

### 1. Always Use Remote Write for Grafana

```bash
# ✅ Good - metrics go to Prometheus
k6 run -o experimental-prometheus-rw=http://localhost:9090/api/v1/write ...

# ❌ Bad - no Grafana data
k6 run ...
```

### 2. Check Console for Full Percentiles

Console output shows p50/p95/p99 that Prometheus can't provide.

### 3. Use Both Metrics Together

- Backend metrics → Production monitoring, debugging
- K6 metrics → Load testing, user experience validation

### 4. Set Realistic SLOs

```yaml
# Server-side (backend)
join_room: p95 < 200ms

# Client-side (K6)
join_room: p99 < 300ms  # includes network
```

### 5. Monitor Trends

Use Grafana's time range selector to analyze:
- Before/after optimizations
- SLO compliance over time
- Capacity trends

## Quick Links

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Backend Metrics**: http://localhost:8000/metrics
- **API Docs**: http://localhost:8000/docs

## Related Documentation

- [METRICS.md](METRICS.md) - Complete metrics reference
- [MONITORING.md](MONITORING.md) - Monitoring stack details
- [../README.md](../README.md) - Main performance testing guide
