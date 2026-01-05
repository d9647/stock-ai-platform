# Performance Monitoring Architecture

## Overview

This document describes the complete performance monitoring architecture for the Stock AI Platform.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Performance Testing Stack                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  K6 Test     │  Generates load simulating student gameplay
│  (Load Gen)  │  - Join room
└──────┬───────┘  - Get news, recommendations, game data
       │          - Update player state (trading)
       │          - Check leaderboard
       │
       │ HTTP Requests
       ↓
┌──────────────────────────────────────┐
│  FastAPI Backend                      │
│  (Single Source of Truth)            │
│                                       │
│  Endpoints:                          │
│  - POST /multiplayer/rooms/join      │
│  - GET  /multiplayer/rooms/{id}/state│
│  - GET  /multiplayer/rooms/{id}/leaderboard
│  - GET  /news/                       │
│  - GET  /recommendations             │
│  - GET  /game/data                   │
│  - PUT  /multiplayer/players/{id}    │
└──────────────────────────────────────┘
       ↑
       │ Response Times (Backend Metrics)
       │
┌──────┴───────┐
│  K6 Metrics  │  Custom Trends for each endpoint:
│  Collection  │  - join_room_latency
└──────┬───────┘  - get_state_latency
       │          - leaderboard_latency
       │          - get_news_latency
       │          - get_recommendations_latency
       │          - get_game_data_latency
       │          - update_player_latency
       │
       │ Prometheus Remote Write Protocol
       │ (K6 → http://localhost:9090/api/v1/write)
       ↓
┌──────────────────────────────────────────┐
│  Prometheus                               │  Port 9090
│  (Time Series Database)                   │
│                                           │
│  - Remote Write Receiver enabled         │
│  - Stores metrics (30-day retention)     │
│  - Runs recording rules every 30s:       │
│    * join_room_latency:p50               │
│    * join_room_latency:p95               │
│    * slo:join_room:p95_under_300ms       │
│    * ... (for all endpoints)             │
│                                           │
│  - PromQL query engine                   │
└──────┬───────────────────────────────────┘
       │
       │ PromQL Queries
       ↓
┌──────────────────────────────────────────┐
│  Grafana                                  │  Port 3001
│  (Visualization & Alerting)              │
│                                           │
│  Dashboard Panels:                       │
│  ┌────────────────────────────────────┐ │
│  │ Endpoint Latency (Time Series)     │ │
│  │ - p50, p95 by endpoint             │ │
│  │ - SLO threshold lines              │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ SLO Compliance (Stat)              │ │
│  │ - Real-time pass/fail              │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Request Rate by Endpoint (Graph)   │ │
│  │ - Backend load distribution        │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Performance Table                  │ │
│  │ - p50, p95, success rate           │ │
│  │ - Sortable, color-coded            │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
       │
       │ Visual Analysis
       ↓
┌──────────────────────┐
│  Performance         │  - Identify bottlenecks
│  Engineer            │  - Validate SLOs
└──────────────────────┘  - Plan capacity
```

## Design Principles

### 1. Backend is Single Source of Truth

**Principle**: Metrics reflect actual backend behavior, not client perception.

**Implementation**:
- K6 measures HTTP response times from backend
- No client-side rendering delays
- No network latency simulation
- Pure backend performance metrics

**Why**:
- Reproducible across environments
- Isolates backend performance
- Eliminates client-side variability

### 2. Endpoint-Level Visibility

**Principle**: High-latency endpoints must not be averaged with fast ones.

**Implementation**:
- Separate Trend metric for each endpoint
- Individual p50/p95 calculations per endpoint
- Dashboard shows all endpoints side-by-side

**Why**:
- Identify specific bottlenecks
- Avoid masking problems
- Target optimizations effectively

**Example**:
```
Without endpoint separation:
  Average latency: 200ms ❌ Looks good, but misleading!

With endpoint separation:
  join_room: 50ms ✅
  get_state: 30ms ✅
  get_game_data: 800ms ❌ Found the problem!
```

### 3. SLO-Driven Dashboards

**Principle**: Percentiles matter more than averages.

**Implementation**:
- Track p50 (median) and p95 (95th percentile)
- No p99 (not enough data for reliable p99)
- SLO thresholds visible on graphs
- Pre-computed recording rules for performance

**Why**:
- Averages hide outliers
- p95 represents user experience
- SLOs drive product decisions

**SLO Definitions**:
```yaml
join_room_latency: p95 < 300ms
get_state_latency: p95 < 200ms
leaderboard_latency: p95 < 400ms
get_news_latency: p95 < 300ms
get_recommendations_latency: p95 < 400ms
get_game_data_latency: p95 < 500ms
update_player_latency: p95 < 300ms
```

### 4. Deterministic Load Tests

**Principle**: Metrics must be reproducible across runs.

**Implementation**:
- Fixed VU counts or predictable stages
- Consistent test scenarios
- Same data fixtures
- No randomized delays in critical paths

**Why**:
- Compare runs over time
- Detect regressions
- Validate optimizations

**Example**:
```bash
# Run 1
k6 run --vus 50 --duration 5m perf/multiplayer-load.js
# Result: join_room p95 = 145ms

# Run 2 (after optimization)
k6 run --vus 50 --duration 5m perf/multiplayer-load.js
# Result: join_room p95 = 85ms ✅ Measurable improvement!
```

### 5. Low Operational Overhead

**Principle**: Minimal configuration, no custom exporters.

**Implementation**:
- Docker Compose for one-command setup
- K6 built-in Prometheus remote write
- Pre-configured Grafana datasource
- Auto-provisioned dashboards
- Recording rules for expensive queries

**Why**:
- Easy to run locally
- Easy to maintain
- Easy to onboard new team members

## Data Flow

### 1. Metric Collection (K6)

```javascript
// K6 test creates custom Trend metrics
const joinRoomLatency = new Trend('join_room_latency');

function joinRoom() {
  const startTime = Date.now();
  const res = http.post(`${BASE_URL}/api/v1/multiplayer/rooms/join`, ...);
  const duration = Date.now() - startTime;

  joinRoomLatency.add(duration);  // Record backend response time
}
```

### 2. Metric Export (Prometheus Remote Write)

```bash
# K6 sends metrics directly to Prometheus via remote write
K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write \
  k6 run -o experimental-prometheus-rw perf/multiplayer-load.js
```

### 3. Metric Storage (Prometheus)

Prometheus receives metrics via its built-in remote write receiver (enabled with `--web.enable-remote-write-receiver` flag):

```yaml
# No scraping needed - K6 pushes directly via remote write
# Prometheus receives metrics at /api/v1/write endpoint
```

### 4. Metric Pre-computation (Recording Rules)

```yaml
# Every 30s, Prometheus pre-computes percentiles
- record: join_room_latency:p95
  expr: histogram_quantile(0.95, sum(rate(join_room_latency_bucket[5m])) by (le))
```

### 5. Metric Visualization (Grafana)

```json
// Dashboard panel queries pre-computed metrics
{
  "expr": "join_room_latency:p95",
  "legendFormat": "p95 (SLO: <300ms)"
}
```

## Metrics Reference

### Custom Metrics (Endpoint-Specific)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `join_room_latency` | Trend | - | Join room response time |
| `get_state_latency` | Trend | - | Get state response time |
| `leaderboard_latency` | Trend | - | Leaderboard query time |
| `get_news_latency` | Trend | - | News fetch time |
| `get_recommendations_latency` | Trend | - | Recommendations fetch time |
| `get_game_data_latency` | Trend | - | Game data fetch time |
| `update_player_latency` | Trend | - | Player update time |
| `join_room_success` | Rate | - | Join success rate |
| `api_errors` | Counter | - | Total API errors |

### Standard HTTP Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_reqs` | Counter | `name`, `status`, `method` | Total requests |
| `http_req_duration` | Trend | `name`, `status`, `method` | Request duration |
| `http_req_failed` | Rate | `name` | Request failure rate |

### Recording Rules (Pre-computed)

```promql
# Percentiles by endpoint
join_room_latency:p50
join_room_latency:p95
get_state_latency:p50
get_state_latency:p95
... (for all endpoints)

# Request rates by endpoint
http_req_rate:by_endpoint

# Success rates by endpoint
http_success_rate:by_endpoint

# Error rates by endpoint
http_error_rate:by_endpoint

# SLO compliance
slo:join_room:p95_under_300ms
slo:get_state:p95_under_200ms
... (for all endpoints)
```

## Query Examples

### Get current p95 for endpoint

```promql
join_room_latency:p95
```

### Compare current vs 1 hour ago

```promql
join_room_latency:p95
vs
join_room_latency:p95 offset 1h
```

### Find slowest endpoint

```promql
topk(1,
  max by (endpoint) (
    join_room_latency:p95 or
    get_state_latency:p95 or
    leaderboard_latency:p95 or
    get_news_latency:p95 or
    get_recommendations_latency:p95 or
    get_game_data_latency:p95 or
    update_player_latency:p95
  )
)
```

### Check if any SLO is failing

```promql
sum(
  slo:join_room:p95_under_300ms +
  slo:get_state:p95_under_200ms +
  slo:leaderboard:p95_under_400ms +
  slo:get_news:p95_under_300ms +
  slo:recommendations:p95_under_400ms +
  slo:game_data:p95_under_500ms +
  slo:update_player:p95_under_300ms
) < 7  # If less than 7, at least one SLO is failing
```

## Performance Analysis Workflow

### 1. Run Baseline Test

```bash
# Start monitoring
./perf/start-monitoring.sh

# Run baseline
./perf/run-tests.sh multiplayer --with-monitoring
```

### 2. Analyze Results in Grafana

1. Open http://localhost:3001
2. Check SLO compliance panel
3. Identify slow endpoints in performance table
4. Review latency trends over time

### 3. Identify Bottlenecks

**If all endpoints are slow**:
- General system overload
- Database connection pool exhausted
- CPU/Memory saturation
- Network issues

**If specific endpoint is slow**:
- Query optimization needed
- Missing database index
- N+1 query problem
- External API dependency

### 4. Optimize Code

Make targeted improvements to slow endpoints.

### 5. Re-test and Compare

```bash
# Run same test after optimization
./perf/run-tests.sh multiplayer --with-monitoring

# Compare metrics in Grafana
# Use time range selector to compare before/after
```

### 6. Validate SLO Compliance

- Check SLO compliance panel
- Verify all metrics are green (value = 1)
- Review p95 latencies are below thresholds

## Alerting (Optional)

You can configure Prometheus alerts for SLO violations:

```yaml
# prometheus/rules/alerts.yml
groups:
  - name: performance_alerts
    rules:
      - alert: EndpointSLOViolation
        expr: |
          slo:join_room:p95_under_300ms == 0 or
          slo:get_state:p95_under_200ms == 0 or
          slo:leaderboard:p95_under_400ms == 0 or
          slo:get_news:p95_under_300ms == 0 or
          slo:recommendations:p95_under_400ms == 0 or
          slo:game_data:p95_under_500ms == 0 or
          slo:update_player:p95_under_300ms == 0
        for: 5m
        annotations:
          summary: "At least one endpoint is violating SLO"

      - alert: HighErrorRate
        expr: sum(rate(http_reqs{status=~"[45].."}[5m])) / sum(rate(http_reqs[5m])) > 0.05
        for: 2m
        annotations:
          summary: "HTTP error rate above 5%"
```

## Scaling Considerations

### When to Scale Up

Indicators you need more backend capacity:

1. **All endpoints** showing high latency
2. Error rate > 5%
3. CPU/Memory near 100%
4. Database connection pool exhausted

### When to Optimize Code

Indicators you need code optimization:

1. **Specific endpoint** showing high latency
2. Latency grows with data size
3. N+1 queries detected
4. Missing database indexes

## Best Practices

1. **Always run with monitoring for serious tests**
   - Console output for quick checks
   - Prometheus for historical analysis

2. **Establish baselines early**
   - Run tests before making changes
   - Document baseline metrics
   - Compare all future runs to baseline

3. **Use realistic scenarios**
   - Match production user patterns
   - Use production-like data volumes
   - Simulate concurrent users accurately

4. **Monitor during development**
   - Catch regressions early
   - Validate optimizations immediately
   - Build performance culture

5. **Archive important results**
   - Export Grafana dashboards as JSON
   - Save Prometheus snapshots
   - Document before/after comparisons

## Resources

- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [K6 Performance Testing Guide](https://k6.io/docs/testing-guides/)
- [SLO Engineering](https://sre.google/workbook/implementing-slos/)
