#!/bin/bash
# Quick script to start the monitoring stack
# Usage: ./perf/start-monitoring.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Stock AI Performance Monitoring Stack...${NC}"
echo ""

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}Error: Docker is not running${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

# Start monitoring stack
echo -e "${BLUE}Starting Prometheus, Grafana, and K6 Adapter...${NC}"
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 5

# Check if services are running
if docker ps | grep -q stockai-prometheus && \
   docker ps | grep -q stockai-grafana; then
    echo ""
    echo -e "${GREEN}✓ Monitoring stack is running!${NC}"
    echo ""
    echo "Access the monitoring tools:"
    echo -e "  ${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "  ${GREEN}Grafana:${NC}    http://localhost:3001 (admin/admin)"
    echo ""
    echo "Set environment variable for K6:"
    echo -e "  ${YELLOW}export K6_PROMETHEUS_RW_SERVER_URL=http://localhost:9090/api/v1/write${NC}"
    echo ""
    echo "Run K6 test with monitoring:"
    echo -e "  ${YELLOW}k6 run -o experimental-prometheus-rw multiplayer-load.js${NC}"
    echo ""
    echo "View logs:"
    echo -e "  ${YELLOW}docker-compose -f docker-compose.monitoring.yml logs -f${NC}"
    echo ""
    echo "Stop monitoring:"
    echo -e "  ${YELLOW}docker-compose -f docker-compose.monitoring.yml down${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Some services may not have started correctly${NC}"
    echo "Check logs with:"
    echo "  docker-compose -f docker-compose.monitoring.yml logs"
    exit 1
fi
