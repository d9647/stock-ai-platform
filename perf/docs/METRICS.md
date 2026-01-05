# Metrics Reference

Complete reference for all available metrics in the performance monitoring stack.

## Overview

We collect metrics from two sources:
1. **Backend (FastAPI)** - Server-side metrics with full histograms
2. **K6 (Load Tests)** - Client-side metrics with p99 only

## Backend Metrics (FastAPI)

Source: `prometheus-fastapi-instrumentator`
Endpoint: http://localhost:8000/metrics
Scrape interval: 5 seconds

### HTTP Request Duration

**Metric**: `http_request_duration_seconds`
**Type**: Histogram
**Labels**: `handler`, `method`, `status`

Server processing time in seconds (excludes network latency).

**Example queries**:
```promql
# p95 latency for join room endpoint
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{handler="/api/v1/multiplayer/rooms/join"}[5m])) by (le)
)

# p50/p95/p99 for all endpoints
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))
```

### HTTP Request Count

**Metric**: `http_requests_total`
**Type**: Counter
**Labels**: `handler`, `method`, `status`

Total number of HTTP requests.

**Example queries**:
```promql
# Requests per second
rate(http_requests_total[1m])

# Success rate
sum(rate(http_requests_total{status=~"2.."}[5m]))
/
sum(rate(http_requests_total[5m]))

# Request count by endpoint
sum(rate(http_requests_total[1m])) by (handler)
```

### Requests in Progress

**Metric**: `http_requests_inprogress`
**Type**: Gauge
**Labels**: `handler`, `method`

Currently processing HTTP requests (concurrency).

**Example queries**:
```promql
# Active requests by endpoint
sum(http_requests_inprogress) by (handler)

# Total active requests
sum(http_requests_inprogress)

# Alert if too many concurrent requests
http_requests_inprogress > 100
```

### Request/Response Size

**Metrics**:
- `http_request_size_bytes` (Histogram)
- `http_response_size_bytes` (Histogram)

**Example queries**:
```promql
# p95 request size
histogram_quantile(0.95, sum(rate(http_request_size_bytes_bucket[5m])) by (le))

# p95 response size by endpoint
histogram_quantile(0.95,
  sum(rate(http_response_size_bytes_bucket[5m])) by (handler, le)
)
```

## K6 Metrics (Load Tests)

Source: K6 Prometheus remote write
Endpoint: Pushes to Prometheus `/api/v1/write`
Available: During and after tests

### Custom Endpoint Latency (p99 only)

**Metrics**:
- `k6_join_room_latency_p99`
- `k6_get_state_latency_p99`
- `k6_get_news_latency_p99`
- `k6_get_recommendations_latency_p99`
- `k6_get_game_data_latency_p99`
- `k6_update_player_latency_p99`
- `k6_leaderboard_latency_p99`

**Type**: Gauge (pre-aggregated p99 value)
**Unit**: Milliseconds

End-to-end latency including network + server processing.

**Example queries**:
```promql
# Join room p99
k6_join_room_latency_p99

# All endpoints compared
k6_join_room_latency_p99
k6_get_state_latency_p99
k6_get_news_latency_p99
```

**Note**: K6 Prometheus output only provides p99. For p50/p95, check K6 console output.

### Success/Error Rates

**Metrics**:
- `k6_join_room_success_rate` - Join room success percentage
- `k6_http_req_failed_rate` - HTTP error percentage
- `k6_checks_rate` - Overall check pass rate

**Type**: Gauge
**Unit**: Percentage (0-1)

**Example queries**:
```promql
# Join room success rate
k6_join_room_success_rate

# Alert if success rate drops
k6_join_room_success_rate < 0.99
```

### HTTP Timing Breakdown

**Metrics** (all p99):
- `k6_http_req_duration_p99` - Total HTTP request time
- `k6_http_req_blocked_p99` - Time spent blocked
- `k6_http_req_connecting_p99` - TCP connection time
- `k6_http_req_tls_handshaking_p99` - TLS handshake time
- `k6_http_req_sending_p99` - Sending request time
- `k6_http_req_waiting_p99` - Waiting for response time
- `k6_http_req_receiving_p99` - Receiving response time

**Type**: Gauge
**Unit**: Seconds

Useful for diagnosing where time is spent in HTTP requests.

### Counters

**Metrics**:
- `k6_http_reqs_total` - Total HTTP requests made
- `k6_iterations_total` - Total test iterations completed
- `k6_api_errors_total` - Total API errors encountered
- `k6_data_sent_total` - Total bytes sent
- `k6_data_received_total` - Total bytes received

**Type**: Counter

**Example queries**:
```promql
# Requests per second during test
rate(k6_http_reqs_total[1m])

# Total data transferred
k6_data_sent_total + k6_data_received_total
```

### Load Metrics

**Metrics**:
- `k6_vus` - Current virtual users
- `k6_vus_max` - Maximum virtual users
- `k6_iteration_duration_p99` - Iteration duration p99

**Type**: Gauge

## Comparing Backend vs K6 Metrics

### Example: Join Room Endpoint

**Backend Metric**:
```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{handler="/api/v1/multiplayer/rooms/join"}[5m])) by (le)
)
# Result: 0.120 (120ms)
```
→ Server processing time only

**K6 Metric**:
```promql
k6_join_room_latency_p99
# Result: 150 (150ms)
```
→ End-to-end time (network + server)

**Network Overhead**: 150ms - 120ms = 30ms

### When to Use Which

| Scenario | Use Backend Metrics | Use K6 Metrics |
|----------|-------------------|----------------|
| **Production monitoring** | ✅ Always available | ❌ Only during tests |
| **Debugging slow endpoints** | ✅ Full p50/p95/p99 | ⚠️ p99 only |
| **Load testing** | ⚠️ Server-side only | ✅ User experience |
| **SLO validation** | ✅ Server SLOs | ✅ End-to-end SLOs |
| **Historical trends** | ✅ Continuous data | ⚠️ Test-time only |
| **Network impact** | ❌ No network data | ✅ Includes network |

## Common Queries

### Find Slowest Endpoint

```promql
topk(5,
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le)
  )
)
```

### Error Rate by Status Code

```promql
sum(rate(http_requests_total[1m])) by (status)
```

### Capacity Planning

```promql
# Max concurrent requests in last 24h
max_over_time(sum(http_requests_inprogress)[24h])

# Peak request rate
max_over_time(sum(rate(http_requests_total[1m]))[24h])

# 99th percentile latency trend
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[24h])) by (handler, le)
)
```

### Network Overhead Calculation

```promql
# K6 end-to-end
k6_join_room_latency_p99

# Backend processing
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{handler="/api/v1/multiplayer/rooms/join"}[5m])) by (le)
) * 1000  # Convert to ms

# Difference = network overhead
```

## Validation

All metrics confirmed working:

### Backend Metrics
✅ `http_requests_total` - Working
✅ `http_request_duration_seconds_bucket` - Full histogram
✅ `http_requests_inprogress` - Real-time concurrency
✅ `http_request_size_bytes_bucket` - Request sizes
✅ `http_response_size_bytes_bucket` - Response sizes

### K6 Metrics (25 total)
✅ 7 custom endpoint latency metrics (p99)
✅ 3 success/error rate metrics
✅ 7 HTTP timing breakdown metrics (p99)
✅ 5 counter metrics
✅ 3 load/iteration metrics

See [../VALIDATION_RESULTS.md](archive/VALIDATION_RESULTS.md) for test results.

## Troubleshooting

### Metrics Not Appearing in Prometheus

**Backend Metrics**:
1. Check `/metrics` endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus scraping:
   ```bash
   curl http://localhost:9090/targets
   # stockai-api should be "UP"
   ```

3. Check Prometheus logs:
   ```bash
   docker logs stockai-prometheus | grep "stockai-api"
   ```

**K6 Metrics**:
1. K6 metrics only appear during/after tests
2. Ensure using `-o experimental-prometheus-rw` flag
3. Query Prometheus:
   ```bash
   curl -s 'http://localhost:9090/api/v1/query?query=k6_join_room_latency_p99' | python3 -m json.tool
   ```

### Different Values: Backend vs K6

**This is expected!**

Backend measures processing only, K6 measures end-to-end.

**Example**:
- Backend: 120ms (server processing)
- K6: 150ms (server + network)
- Difference: 30ms network overhead ✅ Normal

## Quick Reference

### Backend Histogram Percentiles

```promql
# p50 (median)
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))

# p95
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))

# p99
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (handler, le))
```

### K6 Endpoint Metrics

All endpoint metrics are p99 only:
- `k6_join_room_latency_p99`
- `k6_get_state_latency_p99`
- `k6_get_news_latency_p99`
- `k6_get_recommendations_latency_p99`
- `k6_get_game_data_latency_p99`
- `k6_update_player_latency_p99`
- `k6_leaderboard_latency_p99`

## Related Documentation

- [DASHBOARD.md](DASHBOARD.md) - Using Grafana dashboard
- [MONITORING.md](MONITORING.md) - Monitoring stack details
- [../README.md](../README.md) - Main performance testing guide
