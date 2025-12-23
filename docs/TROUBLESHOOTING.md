# Troubleshooting Guide

Common issues and how to fix them.

---

## Docker Issues

### Error: "Cannot connect to the Docker daemon"

**Symptom:**
```
Cannot connect to the Docker daemon at unix:///Users/wdng/.docker/run/docker.sock.
Is the docker daemon running?
```

**Solution:**

1. **Start Docker Desktop:**
   - Open Docker Desktop application
   - Wait for it to fully start (whale icon in menu bar should be steady)
   - You should see "Docker Desktop is running" in the menu

2. **Verify Docker is running:**
   ```bash
   docker info
   ```

   Should show Docker version and system info (not an error).

3. **Test Docker:**
   ```bash
   docker run hello-world
   ```

   Should download and run a test container.

4. **Once Docker is running, try again:**
   ```bash
   make start
   ```

---

### Warning: "the attribute `version` is obsolete"

**Symptom:**
```
WARN[0000] docker-compose.yml: the attribute `version` is obsolete
```

**This is just a warning, not an error.** Docker Compose v2 no longer requires the `version` field. The file will work fine.

**To remove the warning (optional):**
Remove line 1 from `docker-compose.yml`:
```yaml
version: '3.8'  # <-- Delete this line
```

---

## Setup Issues

### Error: "No module named 'app'"

**Symptom:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**

1. **Make sure you're in the correct directory:**
   ```bash
   cd api  # Must be in the api directory
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

### Error: "POLYGON_API_KEY not found"

**Symptom:**
```
ValueError: POLYGON_API_KEY not found in environment
```

**Solution:**

1. **Check .env file exists:**
   ```bash
   cat .env | grep POLYGON_API_KEY
   ```

2. **If missing, add it:**
   ```bash
   echo "POLYGON_API_KEY=hFtktwGorb84kHjbtYOiq8ckR9Dei6at" >> .env
   ```

3. **Verify the key is set:**
   ```bash
   source .env
   echo $POLYGON_API_KEY
   ```

---

## Database Issues

### Error: "could not connect to server"

**Symptom:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution:**

1. **Check if PostgreSQL container is running:**
   ```bash
   docker-compose ps
   ```

   Should show `stockai-postgres` as "Up"

2. **If not running, start it:**
   ```bash
   docker-compose up -d postgres
   ```

3. **Check PostgreSQL logs:**
   ```bash
   docker-compose logs postgres
   ```

4. **Wait for PostgreSQL to be ready:**
   ```bash
   # PostgreSQL takes ~10 seconds to fully start
   sleep 10
   ```

5. **Test connection:**
   ```bash
   docker exec -it stockai-postgres pg_isready -U stockai
   ```

   Should output: `accepting connections`

---

### Error: "relation does not exist"

**Symptom:**
```
sqlalchemy.exc.ProgrammingError: relation "market_data.ohlcv_prices" does not exist
```

**Solution:**

1. **Run database migrations:**
   ```bash
   cd api
   source venv/bin/activate
   alembic upgrade head
   ```

2. **If migrations fail, create initial migration:**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

3. **Verify tables exist:**
   ```bash
   docker exec -it stockai-postgres psql -U stockai -d stockai_dev

   \dt market_data.*
   \dt news.*
   \dt features.*
   \dt agents.*
   ```

---

## API Issues

### Error: "Address already in use"

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**

1. **Find what's using port 8000:**
   ```bash
   lsof -i :8000
   ```

2. **Kill the process:**
   ```bash
   kill -9 <PID>
   ```

3. **Or use a different port:**
   ```bash
   uvicorn app.main:app --port 8001
   ```

---

### API responds with 404

**Symptom:**
```
GET /recommendations/ → 404 Not Found
```

**Solution:**

Use the correct API prefix:
```bash
# ❌ Wrong
curl http://192.168.5.126:8000/recommendations/

# ✅ Correct
curl http://192.168.5.126:8000/api/v1/recommendations/
```

---

## Market Data Issues

### Error: "Rate limit exceeded"

**Symptom:**
```
polygon.exceptions.RateLimitError: Rate limit exceeded
```

**Solution:**

**Polygon.io free tier: 5 requests/minute**

1. **The pipeline has built-in rate limiting.** Just wait for it to complete.

2. **For faster fetching, use premium tier:**
   - Upgrade at polygon.io
   - Update `POLYGON_API_KEY` in `.env`

3. **Reduce number of tickers:**
   ```python
   # In services/market-data/src/config.py
   DEFAULT_TICKERS = ["AAPL", "MSFT"]  # Fewer tickers
   ```

---

### No data returned for ticker

**Symptom:**
```
WARNING: No data found for TICKER
```

**Possible causes:**

1. **Ticker doesn't exist or is delisted**
   - Verify ticker is valid on Yahoo Finance

2. **Weekend/holiday (no trading data)**
   - Markets are closed, no new data available

3. **Date range too narrow**
   ```bash
   # Try wider date range
   python -m src.pipelines.daily_market_pipeline --ticker AAPL --days 365
   ```

---

## Python Environment Issues

### Multiple Python versions

**Symptom:**
```
python command not found
# or
Using wrong Python version
```

**Solution:**

1. **Use python3 explicitly:**
   ```bash
   python3 -m venv venv
   python3 -m pip install -r requirements.txt
   ```

2. **Check Python version:**
   ```bash
   python3 --version  # Should be 3.11+
   ```

3. **If Python 3.11+ not installed:**
   - macOS: `brew install python@3.11`
   - Ubuntu: `sudo apt install python3.11`
   - Windows: Download from python.org

---

## Permission Issues

### Error: "Permission denied"

**Symptom:**
```bash
./scripts/setup.sh
# bash: ./scripts/setup.sh: Permission denied
```

**Solution:**

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

### Docker permission denied

**Symptom:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution (macOS):**
Docker Desktop should handle this automatically.

**Solution (Linux):**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Clean Slate (Nuclear Option)

If everything is broken, start fresh:

```bash
# 1. Stop and remove all containers
docker-compose down -v

# 2. Remove Python virtual environments
rm -rf api/venv services/*/venv

# 3. Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# 4. Run setup again
./scripts/setup.sh

# 5. Fetch data
make fetch-data

# 6. Start API
make api
```

---

## Getting Help

### Check System Status

```bash
make status
```

Shows:
- Docker container status
- PostgreSQL connection
- Redis connection

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis

# API logs
cd api && python -m app.main  # Logs appear in console
```

### Database Debugging

```bash
# PostgreSQL shell
make db-shell

# Common queries
\dt                          # List tables
\d market_data.ohlcv_prices  # Describe table
SELECT COUNT(*) FROM market_data.ohlcv_prices;
```

### Redis Debugging

```bash
# Redis shell
make redis-shell

# Common commands
PING        # Test connection
KEYS *      # List all keys
FLUSHALL    # Clear all data (careful!)
```

---

## Common Workflow Issues

### "I changed code but nothing happened"

**API Changes:**
```bash
# Restart API (with --reload it should auto-reload)
# If not working, manually restart:
cd api
python -m app.main
```

**Database Model Changes:**
```bash
# Create and run migration
cd api
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Schema Changes:**
```bash
# Reinstall shared package
cd api
pip install -e ../shared/
```

---

### "Database has old data"

**Option 1: Clear specific table**
```sql
-- Connect to database
docker exec -it stockai-postgres psql -U stockai -d stockai_dev

-- Clear table (careful!)
TRUNCATE market_data.ohlcv_prices CASCADE;
```

**Option 2: Full database reset**
```bash
# WARNING: Deletes ALL data
docker-compose down -v
docker-compose up -d
cd api && alembic upgrade head
```

---

## Performance Issues

### API is slow

**Check:**
1. Database indexes exist (should be created by migrations)
2. No N+1 queries (use SQLAlchemy `.joinedload()`)
3. Redis is running (for caching)
4. PostgreSQL has enough memory

**Optimize:**
```python
# Use pagination
GET /api/v1/recommendations/?page=1&page_size=20

# Cache responses
# (Redis caching will be added in later phases)
```

---

### Pipeline is slow

**Polygon.io free tier limitations:**
- 5 requests/minute
- For 10 tickers × 2 years = ~20 requests = 4 minutes minimum

**Solutions:**
1. Upgrade to Polygon.io premium ($199/month)
2. Fetch fewer tickers
3. Fetch shorter date ranges
4. Run overnight (doesn't matter if it's slow)

---

## Still Stuck?

1. **Check logs**: `docker-compose logs -f`
2. **Check database**: `make db-shell`
3. **Check status**: `make status`
4. **Read docs**:
   - [QUICKSTART.md](QUICKSTART.md)
   - [Architecture Overview](architecture/overview.md)
   - [Data Flow](architecture/data-flow.md)

5. **Verify environment**:
   ```bash
   # Docker
   docker --version
   docker-compose --version

   # Python
   python3 --version

   # Database
   docker exec stockai-postgres pg_isready

   # API keys
   cat .env | grep API_KEY
   ```

---

## Quick Reference: Make Commands

```bash
make help           # Show all commands
make start          # Start Docker services
make stop           # Stop Docker services
make status         # Show system status
make api            # Run API server
make fetch-data     # Fetch market data
make db-shell       # PostgreSQL shell
make redis-shell    # Redis shell
make logs           # View all logs
make clean          # Nuclear option (deletes data!)
```