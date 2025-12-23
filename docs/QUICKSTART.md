## Quick Start Guide

Get the Stock AI Platform running locally in 10 minutes.

---

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Git

---

## Setup (Automated)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd stock-ai-platform

# 2. Run setup script
./scripts/setup.sh
```

The script will:
- ✅ Start PostgreSQL and Redis containers
- ✅ Create Python virtual environments
- ✅ Install all dependencies
- ✅ Run database migrations

---

## Manual Setup (if needed)

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **pgAdmin** on port 5050 (optional UI)

### 2. Setup API Backend

```bash
cd api
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 3. Setup Market Data Service

```bash
cd services/market-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Platform

### Step 1: Fetch Market Data (Offline Pipeline)

```bash
cd services/market-data
source venv/bin/activate

# Fetch data for default tickers (AAPL, MSFT, GOOGL, etc.)
python -m src.pipelines.daily_market_pipeline

# Or fetch for a specific ticker
python -m src.pipelines.daily_market_pipeline --ticker AAPL --days 365
```

**Expected output:**
```
[2024-03-15 10:00:00] INFO: Running pipeline for AAPL
[2024-03-15 10:00:05] INFO: Fetched 252 price records
[2024-03-15 10:00:10] INFO: Calculated technical indicators
[2024-03-15 10:00:12] INFO: Inserted 252 OHLCV records
[2024-03-15 10:00:14] INFO: Inserted 252 indicator records
[2024-03-15 10:00:15] INFO: Pipeline complete!
```

### Step 2: Start API Server

```bash
cd api
source venv/bin/activate

# Start server
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --port 8000
```

**Server available at:**
- API: http://192.168.5.126:8000
- Docs: http://192.168.5.126:8000/docs
- Health: http://192.168.5.126:8000/api/v1/health

### Step 3: Test API End points

```bash
# Health check
curl http://192.168.5.126:8000/api/v1/health

# Get recommendations (will be empty until Phase 3 - agents)
curl http://192.168.5.126:8000/api/v1/recommendations/

# Check database
curl http://192.168.5.126:8000/api/v1/health/db
```

---

## Verify Setup

### Check Database

Access pgAdmin at http://192.168.5.126:5050:
- **Email**: admin@stockai.local
- **Password**: admin

Add server:
- **Host**: postgres (or localhost if outside Docker)
- **Port**: 5432
- **Database**: stockai_dev
- **Username**: stockai
- **Password**: stockai

You should see tables in these schemas:
- `market_data.*` - OHLCV prices, technical indicators
- `news.*` - News articles, sentiment (Phase 2)
- `features.*` - Feature snapshots (Phase 2)
- `agents.*` - Recommendations (Phase 3)

### Query Market Data

```sql
-- Check OHLCV data
SELECT * FROM market_data.ohlcv_prices
WHERE ticker = 'AAPL'
ORDER BY date DESC
LIMIT 10;

-- Check technical indicators
SELECT
    ticker, date, rsi_14, macd, sma_50, sma_200
FROM market_data.technical_indicators
WHERE ticker = 'AAPL'
ORDER BY date DESC
LIMIT 10;
```

---

## Development Workflow

### Daily Development

1. **Start infrastructure** (if not running):
   ```bash
   docker-compose up -d
   ```

2. **Run API server**:
   ```bash
   cd api && source venv/bin/activate && python -m app.main
   ```

3. **Update market data** (optional):
   ```bash
   cd services/market-data && source venv/bin/activate
   python -m src.pipelines.daily_market_pipeline
   ```

### Stopping Services

```bash
# Stop Docker containers
docker-compose down

# Keep data volumes (recommended)
docker-compose down  # Just stops containers

# Remove everything including data (dangerous!)
docker-compose down -v  # Deletes all data
```

---

## Troubleshooting

### Database Connection Issues

**Error**: `could not connect to server`

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### API Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

```bash
# Make sure you're in the api directory
cd api

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Market Data Fetching Fails

**Error**: `POLYGON_API_KEY not found`

```bash
# Check .env file exists
cat .env | grep POLYGON_API_KEY

# If missing, add it
echo "POLYGON_API_KEY=your_key_here" >> .env
```

**Error**: `Rate limit exceeded`

Polygon.io free tier: 5 requests/minute

Solution: The pipeline has built-in rate limiting. Just wait for it to complete.

---

## Next Steps

✅ **Phase 1 Complete!** You now have:
- PostgreSQL + Redis infrastructure
- Market data ingestion pipeline
- FastAPI backend with read-only end points
- Technical indicators calculation

🚀 **Coming in Phase 2:**
- News sentiment service
- Feature store implementation
- Point-in-time feature snapshots

🤖 **Coming in Phase 3:**
- LangGraph agent orchestrator
- Multi-agent reasoning (technical, sentiment, risk)
- AI-powered recommendations

---

## Useful Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f postgres
docker-compose logs -f redis

# Access PostgreSQL CLI
docker exec -it stockai-postgres psql -U stockai -d stockai_dev

# Access Redis CLI
docker exec -it stockai-redis redis-cli

# Run tests
cd api && pytest
cd services/market-data && pytest

# Database migrations
cd api
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## Getting Help

- Check the [Architecture Overview](docs/architecture/overview.md)
- Review API docs at http://192.168.5.126:8000/docs
- Check Docker logs: `docker-compose logs -f`
- Database issues: Access pgAdmin at http://192.168.5.126:5050

---

Happy coding! 🚀
