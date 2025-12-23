#!/bin/bash

# Stock AI Platform - Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "========================================="
echo "Stock AI Platform - Development Setup"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+ first."
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Start Docker services
echo -e "${YELLOW}Starting Docker services (PostgreSQL, Redis)...${NC}"
docker-compose up -d

echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Setup API
echo -e "${YELLOW}Setting up API backend...${NC}"
cd api

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ API dependencies installed${NC}"

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
alembic upgrade head

echo -e "${GREEN}✓ Database migrations complete${NC}"

cd ..
echo ""

# Setup market data service
echo -e "${YELLOW}Setting up market data service...${NC}"
cd services/market-data

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo -e "${GREEN}✓ Market data service ready${NC}"

cd ../..
echo ""

# Final instructions
echo "========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the API server:"
echo "   cd api && source venv/bin/activate && python -m app.main"
echo ""
echo "2. Fetch initial market data:"
echo "   cd services/market-data && source venv/bin/activate && python -m src.pipelines.daily_market_pipeline"
echo ""
echo "3. Access the API:"
echo "   http://192.168.5.126:8000/docs"
echo ""
echo "4. Access pgAdmin (database UI):"
echo "   http://192.168.5.126:5050"
echo "   Email: admin@stockai.local"
echo "   Password: admin"
echo ""
