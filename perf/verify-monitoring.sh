#!/bin/bash
# Quick monitoring verification script

echo "🔍 Monitoring Stack Verification"
echo "=================================="
echo ""

# Check Docker containers
echo "Docker Containers:"
echo -n "  Prometheus: "
docker ps | grep -q stockai-prometheus && echo "✅ Running" || echo "❌ Not running"

echo -n "  Grafana:    "
docker ps | grep -q stockai-grafana && echo "✅ Running" || echo "❌ Not running"

echo ""

# Check services
echo "Service Health:"
echo -n "  Prometheus: "
curl -s http://localhost:9090/-/healthy > /dev/null 2>&1 && echo "✅ http://localhost:9090" || echo "❌ Not accessible"

echo -n "  Grafana:    "
curl -s http://localhost:3001/api/health > /dev/null 2>&1 && echo "✅ http://localhost:3001" || echo "❌ Not accessible"

echo -n "  Backend:    "
curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1 && echo "✅ http://localhost:8000" || echo "❌ Not running"

echo ""

# Check Prometheus targets
echo "Prometheus Configuration:"
echo -n "  Backend scraping: "
TARGETS=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null)
if echo "$TARGETS" | grep -q '"health":"up"'; then
    echo "✅ Backend is being scraped"
else
    echo "❌ Backend not being scraped (check targets)"
fi

echo ""

# Check metrics exist
echo "Metrics Availability:"
echo -n "  Backend metrics: "
BACKEND_METRICS=$(curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' 2>/dev/null)
if echo "$BACKEND_METRICS" | grep -q '"result":\[{'; then
    COUNT=$(echo "$BACKEND_METRICS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['data']['result']))" 2>/dev/null || echo "0")
    echo "✅ $COUNT metric series found"
else
    echo "⚠️  No data (backend may need traffic)"
fi

echo -n "  K6 metrics:      "
K6_METRICS=$(curl -s 'http://localhost:9090/api/v1/query?query=k6_join_room_latency_p99' 2>/dev/null)
if echo "$K6_METRICS" | grep -q '"result":\[{'; then
    VALUE=$(echo "$K6_METRICS" | python3 -c "import sys, json; r = json.load(sys.stdin)['data']['result']; print(r[0]['value'][1] if r else 'N/A')" 2>/dev/null || echo "N/A")
    echo "✅ Latest: ${VALUE}ms (from previous test)"
else
    echo "⚠️  No data (run test with --with-monitoring)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary
ALL_OK=true

if ! docker ps | grep -q stockai-prometheus; then
    echo "❌ ISSUE: Prometheus not running"
    echo "   Fix: ./start-monitoring.sh"
    ALL_OK=false
fi

if ! docker ps | grep -q stockai-grafana; then
    echo "❌ ISSUE: Grafana not running"
    echo "   Fix: ./start-monitoring.sh"
    ALL_OK=false
fi

if ! curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "❌ ISSUE: Backend not running"
    echo "   Fix: cd api && source venv/bin/activate && uvicorn app.main:app --reload"
    ALL_OK=false
fi

if ! echo "$TARGETS" | grep -q '"health":"up"'; then
    echo "⚠️  WARNING: Prometheus not scraping backend"
    echo "   Check: http://localhost:9090/targets"
    ALL_OK=false
fi

if $ALL_OK; then
    echo "✅ All systems ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Open Grafana: http://localhost:3001 (admin/admin)"
    echo "  2. Navigate: Dashboards → Performance Testing → Backend & K6 Performance"
    echo "  3. Run test: ./run-tests.sh load-medium --with-monitoring"
    echo ""
else
    echo ""
    echo "⚠️  Fix issues above before running tests"
    echo ""
fi

echo "Quick Links:"
echo "  Grafana Dashboard: http://localhost:3001"
echo "  Prometheus:        http://localhost:9090"
echo "  Prometheus Targets: http://localhost:9090/targets"
echo "  Backend Health:    http://localhost:8000/api/v1/health"
