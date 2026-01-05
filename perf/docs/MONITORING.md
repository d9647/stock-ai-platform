# Performance Monitoring with Prometheus + Grafana

This document describes the monitoring stack for K6 performance testing.

## Architecture

```
K6 Load Generator → Prometheus Remote Write → Prometheus → Grafana
                                                    ↓
                                            Recording Rules
                                            (SLO Calculations)
```

### Design Principles

1. **Backend is single source of truth**: All metrics reflect actual backend response times, not client perception
2. **Endpoint-level visibility**: Each endpoint tracked separately to avoid averaging fast/slow endpoints
3. **SLO-driven dashboards**: Percentiles (p50, p95) matter more than averages
4. **Deterministic load tests**: Metrics are reproducible across runs
5. **Low operational overhead**: Minimal configuration, no custom exporters

## Components

### 1. K6 (Load Generator)
- Generates realistic user load
- Sends metrics directly to Prometheus via Remote Write protocol
- Custom metrics for each endpoint (join_room, get_state, etc.)

### 2. Prometheus (Time Series DB)
- Remote Write Receiver enabled (receives K6 metrics at `/api/v1/write`)
- Scrapes FastAPI backend metrics from `/metrics` endpoint
- Stores all performance metrics
- 30-day retention period
- Runs recording rules to pre-compute percentiles
- Runs on port 9090

### 3. FastAPI Backend (/metrics)
- Exposes Prometheus metrics via `prometheus-fastapi-instrumentator`
- Provides server-side observability (request counts, processing time, etc.)
- Complements K6 client-side metrics
- See [BACKEND_METRICS.md](BACKEND_METRICS.md) for details

### 4. Grafana (Dashboards & Alerting)
- Visualizes both K6 and backend metrics
- Pre-configured dashboard with endpoint-level visibility
- SLO compliance tracking
- Runs on port 3001 (to avoid conflict with frontend on 3000)

## Quick Start

### 1. Start Monitoring Stack

```bash
cd perf
docker-compose -f docker-compose.monitoring.yml up -d
```

This starts:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

**Note**: Prometheus will also automatically scrape backend metrics from your FastAPI app at `http://localhost:8000/metrics` (make sure your backend is running).

### 2. Run K6 Test with Prometheus Export

```bash
# Set Prometheus Remote Write URL
export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write

# Run test with Prometheus output
k6 run -o experimental-prometheus-rw perf/multiplayer-load.js

# Or with custom load
k6 run --vus 50 --duration 5m -o experimental-prometheus-rw perf/multiplayer-load.js
```

### 3. View Metrics in Grafana

1. Open http://localhost:3001
2. Login: admin/admin
3. Navigate to Dashboards → Performance Testing → Stock AI Platform - Multiplayer Performance

## Dashboard Overview

The Grafana dashboard provides:

### Top Row: Critical Endpoints
- **Join Room Latency**: p50 and p95 with 300ms SLO threshold
- **Get Room State Latency**: p50 and p95 with 200ms SLO threshold

### Second Row: Health Indicators
- **Join Room Success Rate**: Gauge showing success percentage (target: >95%)
- **SLO Compliance**: Real-time SLO pass/fail (1 = passing, 0 = failing)
- **Request Rate**: Total backend requests per second
- **HTTP Error Rate**: Percentage of 4xx/5xx responses

### Middle Section: Endpoint Performance
- **Endpoint Latency p95 by Endpoint**: Time series comparing all endpoints
  - Get News (SLO: <300ms)
  - Get Recommendations (SLO: <400ms)
  - Get Game Data (SLO: <500ms)
  - Update Player (SLO: <300ms)
  - Leaderboard (SLO: <400ms)

### Bottom Section: Load Distribution
- **Request Rate by Endpoint**: Shows which endpoints receive most traffic
- **Endpoint Performance Summary Table**: Sortable table with p50, p95, success rate per endpoint

## Metrics Reference

### Custom K6 Metrics

| Metric Name | Type | Description | SLO |
|-------------|------|-------------|-----|
| `join_room_latency` | Trend | Time to join multiplayer room | p95 < 300ms |
| `get_state_latency` | Trend | Time to fetch room state | p95 < 200ms |
| `leaderboard_latency` | Trend | Time to fetch leaderboard | p95 < 400ms |
| `get_news_latency` | Trend | Time to fetch news articles | p95 < 300ms |
| `get_recommendations_latency` | Trend | Time to fetch AI recommendations | p95 < 400ms |
| `get_game_data_latency` | Trend | Time to fetch game data | p95 < 500ms |
| `update_player_latency` | Trend | Time to update player state | p95 < 300ms |
| `join_room_success` | Rate | Success rate of join operations | > 95% |
| `api_errors` | Counter | Total API errors | < 1% |

### Standard HTTP Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_reqs` | Counter | Total HTTP requests |
| `http_req_duration` | Trend | HTTP request duration |
| `http_req_failed` | Rate | Percentage of failed requests |

### Recording Rules (Pre-computed)

Prometheus recording rules pre-compute percentiles every 30s:

```
join_room_latency:p50
join_room_latency:p95
get_state_latency:p50
get_state_latency:p95
... (etc for all endpoints)
```

And SLO compliance:
```
slo:join_room:p95_under_300ms
slo:get_state:p95_under_200ms
... (etc)
```

## Usage Examples

### Example 1: Basic Performance Test

```bash
# Start monitoring
docker-compose -f perf/docker-compose.monitoring.yml up -d

# Set K6 output
export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write

# Run test
k6 run -o experimental-prometheus-rw perf/multiplayer-load.js

# View in Grafana: http://localhost:3001
```

### Example 2: Progressive Load Test

```bash
export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write

k6 run \
  --stage 1m:10 \
  --stage 2m:50 \
  --stage 2m:100 \
  --stage 1m:50 \
  --stage 1m:0 \
  -o experimental-prometheus-rw \
  perf/multiplayer-load.js
```

Watch the dashboard to see:
- Latency increase as load ramps up
- Which endpoints become bottlenecks first
- When SLOs start failing

### Example 3: Full Game Session (30 students, 30 days)

```bash
export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write

k6 run \
  --vus 30 \
  --iterations 30 \
  -o experimental-prometheus-rw \
  perf/multiplayer-load.js
```

Monitor:
- Total game session duration
- Consistency of performance across days
- Leaderboard query performance as player count grows

### Example 4: Endurance Test

```bash
export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write

k6 run \
  --vus 50 \
  --duration 30m \
  -o experimental-prometheus-rw \
  perf/multiplayer-load.js
```

Check for:
- Memory leaks (degrading performance over time)
- Database connection pool exhaustion
- Cache effectiveness

## Interpreting Results

### ✅ Good Performance Indicators

- p95 latencies below SLO thresholds (green in dashboard)
- Success rate > 99%
- Error rate < 1%
- Consistent latency (no spikes)
- All SLO compliance metrics = 1

### ⚠️ Warning Signs

- p95 latencies approaching SLO thresholds (yellow)
- Success rate 95-99%
- Error rate 1-5%
- Occasional latency spikes
- Some SLO metrics = 0

### ❌ Performance Issues

- p95 latencies exceeding SLO thresholds (red)
- Success rate < 95%
- Error rate > 5%
- Sustained high latency
- Multiple SLO metrics = 0

### Endpoint-Level Analysis

The dashboard shows **per-endpoint metrics** so you can identify specific bottlenecks:

**Example**: If `get_game_data_latency` is high (500ms+) but other endpoints are fast:
- Problem is likely in game data query logic
- Not a general system overload
- Focus optimization on that specific endpoint

**Example**: If all endpoints show high latency:
- General system overload
- Database connection pool exhaustion
- Network issues
- Need to scale infrastructure

## Prometheus Queries

Useful PromQL queries for custom analysis:

### Get p95 for specific endpoint over last 5 minutes
```promql
histogram_quantile(0.95, sum(rate(join_room_latency_bucket[5m])) by (le))
```

### Error rate by endpoint
```promql
sum(rate(http_reqs{status=~"[45].."}[5m])) by (name)
/
sum(rate(http_reqs[5m])) by (name)
```

### Requests per second by endpoint
```promql
sum(rate(http_reqs[1m])) by (name)
```

### Compare current p95 to historical
```promql
join_room_latency:p95 offset 1h
```

## Alerting (Optional)

You can add Prometheus alerts for SLO violations:

```yaml
# prometheus/rules/alerts.yml
groups:
  - name: performance_alerts
    rules:
      - alert: JoinRoomSLOViolation
        expr: slo:join_room:p95_under_300ms == 0
        for: 5m
        annotations:
          summary: "Join Room p95 latency exceeds 300ms SLO"
          description: "p95: {{ $value }}ms"

      - alert: HighErrorRate
        expr: sum(rate(http_reqs{status=~"[45].."}[5m])) / sum(rate(http_reqs[5m])) > 0.05
        for: 2m
        annotations:
          summary: "Error rate above 5%"
```

## Maintenance

### View Prometheus Metrics
```bash
# Prometheus UI
open http://localhost:9090

# Query raw metrics
curl http://localhost:9090/api/v1/query?query=join_room_latency:p95
```

### Stop Monitoring Stack
```bash
docker-compose -f perf/docker-compose.monitoring.yml down
```

### Clear All Monitoring Data
```bash
docker-compose -f perf/docker-compose.monitoring.yml down -v
```

## Troubleshooting

### K6 metrics not appearing in Grafana

1. Verify K6_PROMETHEUS_RW_SERVER_URL is set:
   ```bash
   echo $K6_PROMETHEUS_RW_SERVER_URL
   # Should output: http://localhost:9090/api/v1/write
   ```

2. Check K6 output includes prometheus:
   ```bash
   k6 run -o experimental-prometheus-rw perf/multiplayer-load.js
   # Should see: output: Prometheus remote write
   ```

3. Verify Prometheus remote write receiver is enabled:
   ```bash
   docker logs stockai-prometheus | grep "remote-write-receiver"
   # Should see: "Remote write receiver enabled"
   ```

### Grafana dashboard shows "No Data"

1. Verify Prometheus is receiving metrics:
   - Open http://localhost:9090
   - Run query: `join_room_latency`
   - Should see data points

2. Verify datasource in Grafana:
   - Settings → Data Sources → Prometheus
   - Click "Test" - should be green

### Docker containers not starting

```bash
# Check logs
docker-compose -f perf/docker-compose.monitoring.yml logs

# Restart
docker-compose -f perf/docker-compose.monitoring.yml restart
```

## Cost and Resources

### Resource Usage

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| Prometheus | ~200m | ~500MB | ~1GB/day |
| Grafana | ~100m | ~200MB | ~100MB |

### Retention Policy

- Prometheus: 30 days (configurable in docker-compose.yml)
- Grafana: Infinite (dashboards are configuration, not data)

## Best Practices

1. **Always run with Prometheus output for serious testing**
   - Console output is good for quick checks
   - Prometheus provides historical analysis

2. **Use recording rules for common queries**
   - Pre-computed percentiles are faster
   - Reduces load on Prometheus

3. **Tag your test runs**
   - Use labels to distinguish different test scenarios
   - Add to docker-compose.yml external_labels

4. **Monitor during development**
   - Catch performance regressions early
   - Baseline metrics for new features

5. **Archive important test results**
   - Export dashboard as JSON
   - Save Prometheus snapshots for capacity planning

## References

- [K6 Documentation](https://k6.io/docs/)
- [K6 Prometheus Output](https://k6.io/docs/results-output/real-time/prometheus-remote-write/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
