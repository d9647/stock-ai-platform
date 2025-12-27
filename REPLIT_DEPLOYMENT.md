# Replit Deployment Guide

Complete guide to deploy the Stock AI Platform backend API to Replit.

---

## 📋 Prerequisites

- GitHub account with your repository
- Replit account (free or paid)
- Production database (Neon, Supabase, or Replit DB)
- API keys for external services (OpenAI, Polygon.io, Finnhub, NewsAPI)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Import to Replit

1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Select **"Import from GitHub"**
4. Enter your repository URL: `https://github.com/your-username/stock-ai-platform`
5. Replit will auto-detect Python project
6. Click **"Import from GitHub"**

### Step 2: Configure Environment Variables

In Replit, click the **🔒 Secrets** (lock icon) in the sidebar and add:

#### Required Secrets

```env
# Database (required)
DATABASE_URL=postgresql://user:password@host.neon.tech:5432/database

# OpenAI (required for AI agents)
OPENAI_API_KEY=sk-...

# Market Data API (required)
POLYGON_API_KEY=...

# News APIs (required)
FINNHUB_API_KEY=...
NEWSAPI_KEY=...

# Frontend URL (for CORS)
FRONTEND_URL=https://your-app.vercel.app

# Optional - Security
SECRET_KEY=your-random-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

#### Optional Secrets

```env
# Redis (optional - for caching)
REDIS_URL=redis://username:password@host:port

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 3: Install Dependencies

Replit will automatically install dependencies from `api/requirements.txt` when you run.

If needed, manually install in Replit Shell:

```bash
cd api
pip install -r requirements.txt
```

### Step 4: Run Database Migrations

In Replit Shell:

```bash
cd api
python -m alembic upgrade head
```

This creates all database tables.

### Step 5: Run the API

Click the **▶️ Run** button in Replit!

Your API will start at: `https://your-repl-name.your-username.replit.dev`

---

## 🗄️ Database Setup Options

### Option A: Neon PostgreSQL (Recommended)

**Free Tier**: 0.5GB storage, 100 hours compute/month

1. Sign up at [neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string
4. Add to Replit Secrets as `DATABASE_URL`

**Connection string format**:
```
postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb
```

### Option B: Supabase PostgreSQL

**Free Tier**: 500MB storage, 2GB bandwidth

1. Sign up at [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → Database → Connection String
4. Copy "URI" connection string
5. Add to Replit Secrets as `DATABASE_URL`

### Option C: Replit Database (Built-in)

**Limitations**: Basic features, smaller storage

1. In Replit, click **"Database"** icon in sidebar
2. Replit provisions PostgreSQL automatically
3. Connection string available in Secrets as `DATABASE_URL`

---

## 📊 Migrate Your Local Database

If you have local data, migrate it to production:

### Method 1: pg_dump (Recommended)

```bash
# On your local machine:

# 1. Export your local database
pg_dump -U postgres -h localhost stock_ai | gzip > stock_ai_backup.sql.gz

# 2. Upload to Replit (drag & drop to Files panel)

# 3. In Replit Shell, restore:
gunzip -c stock_ai_backup.sql.gz | psql $DATABASE_URL
```

### Method 2: Table by Table

```bash
# Export specific tables only
pg_dump -U postgres -h localhost \
  -t market_data.ohlcv_prices \
  -t market_data.technical_indicators \
  -t news.news_articles \
  -t agents.stock_recommendations \
  stock_ai > essential_data.sql

# Upload to Replit and restore
psql $DATABASE_URL < essential_data.sql
```

---

## 🔧 Replit Deployment Types

### Free Tier (Always-On Development)

- **Cost**: FREE
- **Features**:
  - Repl stays awake while you're coding
  - Sleeps after 1 hour of inactivity
  - Wakes up when accessed (~5-10 seconds)
- **Best for**: Development, testing

**Keep Awake with UptimeRobot**:
1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-repl.replit.dev/api/v1/health`
   - Interval: 5 minutes
3. Repl stays awake 24/7!

### Reserved VM ($7/month)

- **Cost**: $7/month
- **Features**:
  - Always-on (never sleeps)
  - 1 vCPU, 1GB RAM
  - Dedicated resources
  - Faster performance
- **Best for**: Classroom use, small production

**How to Deploy**:
1. Click **"Deploy"** button in Replit
2. Select **"Reserved VM"**
3. Configure settings
4. Click **"Deploy"**

### Autoscale ($20/month)

- **Cost**: $20/month
- **Features**:
  - Auto-scales based on traffic
  - Up to 2GB RAM
  - High availability
  - Best performance
- **Best for**: Production, many users

---

## ✅ Post-Deployment Checklist

### 1. Verify API Health

Visit in browser:
```
https://your-repl.replit.dev/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-26T12:00:00Z"
}
```

### 2. Test API Endpoints

```bash
# List recommendations
curl https://your-repl.replit.dev/api/v1/recommendations/

# Get game data
curl "https://your-repl.replit.dev/api/v1/game/data?days=10&tickers=AAPL"
```

### 3. Check Database Connection

In Replit Shell:
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM agents.stock_recommendations;"
```

### 4. Update Frontend Environment Variable

In Vercel dashboard:
1. Go to your project settings
2. Click **"Environment Variables"**
3. Update `NEXT_PUBLIC_API_URL`:
   ```
   https://your-repl.replit.dev
   ```
4. Redeploy frontend

### 5. Test End-to-End

1. Visit your Vercel frontend
2. Start a new game
3. Verify data loads from Replit backend
4. Test multiplayer mode

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Install dependencies manually
```bash
cd api
pip install -r requirements.txt
```

### Issue: "Database connection failed"

**Solution**: Check DATABASE_URL secret
```bash
# In Replit Shell
echo $DATABASE_URL
# Should show your connection string

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Issue: "CORS errors" in frontend

**Solution**: Add frontend URL to secrets
```env
FRONTEND_URL=https://your-app.vercel.app
```

Then verify CORS in `api/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: "Port 8000 not accessible"

**Solution**: Check .replit configuration
- Ensure `run` command uses port 8000
- Check [[ports]] section maps correctly

### Issue: Repl sleeps on free tier

**Solution**: Use UptimeRobot (free) or upgrade to Reserved VM ($7/month)

---

## 📈 Monitoring & Logs

### View Logs in Replit

Click **Console** tab to see real-time logs:
- API requests
- Database queries
- Errors and warnings

### Add Structured Logging

Already configured in `api/app/core/config.py`:
```python
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

Set in Secrets:
```env
LOG_LEVEL=DEBUG  # For development
LOG_LEVEL=INFO   # For production
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets

Ensure `.env` is in `.gitignore`:
```bash
# Check
cat .gitignore | grep .env
```

### 2. Use Strong Secret Keys

Generate secure keys:
```bash
# In Replit Shell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use output for `SECRET_KEY` and `JWT_SECRET`

### 3. Limit CORS Origins

Update `api/app/core/config.py` with specific domains (already done):
```python
CORS_ORIGINS = [
    "https://your-app.vercel.app",  # Your specific domain
]
```

### 4. Enable HTTPS Only

Replit provides HTTPS automatically - all requests are encrypted.

---

## 💰 Cost Optimization

### Minimize OpenAI Costs

Reduce AI agent runs:
```python
# In services/agent-orchestrator/src/pipelines/daily_agent_pipeline.py

# Run for fewer tickers
TICKERS = ["AAPL"]  # Instead of ["AAPL", "MSFT", "GOOGL", ...]

# Or run less frequently (every 2 days instead of daily)
```

### Use Free Database Tier

- Neon: 0.5GB free
- Supabase: 500MB free
- Keep data minimal for classroom use

### Start with Free Repl + UptimeRobot

Total cost: $0/month (+ OpenAI usage ~$20-84/month)

Upgrade to Reserved VM only when needed.

---

## 📞 Support

If you encounter issues:

1. Check Replit Console for errors
2. Verify all Secrets are set correctly
3. Test database connection in Shell
4. Check API docs: https://your-repl.replit.dev/docs

---

## 🎉 You're Live!

Once deployed:

✅ Backend API: `https://your-repl.replit.dev`
✅ API Docs: `https://your-repl.replit.dev/docs`
✅ Health Check: `https://your-repl.replit.dev/api/v1/health`

Next: Deploy frontend to Vercel and connect them!

---

**Last Updated**: December 26, 2025
