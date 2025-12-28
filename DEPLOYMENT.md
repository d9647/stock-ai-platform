# Production Deployment Guide

Complete guide to deploy the Stock AI Platform to production.

## Deployment Overview

This platform consists of two parts:
- **Backend API** (FastAPI) → Deploy to Replit
- **Frontend** (Next.js) → Deploy to Vercel

Both deployments are FREE (with optional paid tiers for scale).

## Prerequisites

Before deploying, ensure you have:

- [ ] GitHub account with your repository
- [ ] Replit account (free or paid)
- [ ] Vercel account (free)
- [ ] Production database (Neon or Supabase - free tier available)
- [ ] API keys:
  - OpenAI API key
  - Polygon.io API key
  - Finnhub API key
  - NewsAPI key

## Database Setup

Choose ONE database option:

### Option A: Neon PostgreSQL (Recommended)

**Free Tier**: 0.5GB storage, 100 hours compute/month

1. Sign up at [neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string (format: `postgresql://username:password@ep-xxx.us-east-2.aws.neon.tech/neondb`)
4. Save for later use

### Option B: Supabase PostgreSQL

**Free Tier**: 500MB storage, 2GB bandwidth

1. Sign up at [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings → Database → Connection String
4. Copy "URI" connection string
5. Save for later use

## Backend Deployment (Replit)

### Step 1: Import Project to Replit

1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Select "Import from GitHub"
4. Enter your repository URL
5. Replit will auto-detect Python project
6. Click "Import from GitHub"

### Step 2: Configure Environment Variables

Click the **🔒 Secrets** (lock icon) in the Replit sidebar and add:

**Required Secrets**:
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

# Frontend URL (add after deploying frontend)
FRONTEND_URL=https://your-app.vercel.app
```

**Optional Secrets**:
```env
# Redis (optional - for caching)
REDIS_URL=redis://username:password@host:port

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-random-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

**Generate secure keys**:
```bash
# In Replit Shell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 3: Run Database Migrations

In Replit Shell:
```bash
cd api
python -m alembic upgrade head
```

This creates all database tables.

### Step 4: Migrate Local Data (Optional)

If you have local data to migrate:

**Method 1: Full database dump**
```bash
# On your local machine
pg_dump -U postgres -h localhost stockai_dev | gzip > stock_ai_backup.sql.gz

# Upload to Replit (drag & drop to Files panel)

# In Replit Shell, restore:
gunzip -c stock_ai_backup.sql.gz | psql $DATABASE_URL
```

**Method 2: Essential tables only**
```bash
# Export specific tables
pg_dump -U postgres -h localhost \
  -t market_data.ohlcv_prices \
  -t market_data.technical_indicators \
  -t news.news_articles \
  -t agents.stock_recommendations \
  -t multiplayer.game_rooms \
  -t multiplayer.players \
  stockai_dev > essential_data.sql

# Upload and restore in Replit
psql $DATABASE_URL < essential_data.sql
```

### Step 5: Run the API

Click the **▶️ Run** button in Replit!

Your API will be live at: `https://your-repl-name.your-username.replit.dev`

### Step 6: Test Backend

Visit these URLs to verify:

- **Health check**: `https://your-repl.replit.dev/api/v1/health`
  - Should return: `{"status": "healthy", ...}`

- **API Docs**: `https://your-repl.replit.dev/docs`
  - Interactive API documentation

- **Game Data**: `https://your-repl.replit.dev/api/v1/game/data?days=10&tickers=AAPL`
  - Should return game data JSON

### Step 7: Keep Backend Awake (Free Tier)

**If using Replit free tier**, the backend sleeps after 1 hour of inactivity. Keep it awake:

1. Sign up at [uptimerobot.com](https://uptimerobot.com) (free)
2. Add monitor:
   - Type: HTTP(s)
   - URL: `https://your-repl.replit.dev/api/v1/health`
   - Interval: 5 minutes
3. Your backend stays awake 24/7!

**Alternative**: Upgrade to Replit Reserved VM ($7/month) or Autoscale ($20/month) for always-on hosting.

## Frontend Deployment (Vercel)

### Step 1: Push Code to GitHub

Ensure your latest code is pushed:
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### Step 2: Import to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import from GitHub
4. Select your repository
5. Configure project:
   - **Framework**: Next.js (auto-detected)
   - **Root Directory**: `web`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

### Step 3: Add Environment Variable

In Vercel project settings, add:

```env
NEXT_PUBLIC_API_URL=https://your-repl-name.your-username.replit.dev
```

Use your actual Replit URL from step 5 of backend deployment.

### Step 4: Deploy

1. Click "Deploy"
2. Wait ~2-3 minutes for build
3. Vercel will show your live URL: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

Now that you have your Vercel URL, update the backend:

1. Go back to Replit
2. Add to Secrets:
   ```env
   FRONTEND_URL=https://your-app.vercel.app
   ```
3. Restart the Replit backend (click Run button again)

### Step 6: Test Frontend

Visit your Vercel URL and test:

- [ ] Homepage loads
- [ ] Click "Start Playing Now"
- [ ] Game data loads from backend
- [ ] Can play through a few days
- [ ] Trading (buy/sell) works
- [ ] Click "Create Classroom" (multiplayer)
- [ ] Create room and get room code
- [ ] Open incognito window and join room
- [ ] Both see leaderboard

## Post-Deployment Checklist

### Security

- [ ] All API keys stored in Replit Secrets (not in code)
- [ ] `.env` files in `.gitignore`
- [ ] No secrets committed to GitHub
- [ ] CORS limited to your Vercel domain only
- [ ] Database connection uses SSL
- [ ] Strong SECRET_KEY and JWT_SECRET generated

### Verification

**Backend**:
- [ ] `/api/v1/health` returns healthy status
- [ ] `/docs` shows API documentation
- [ ] `/api/v1/game/data` returns data
- [ ] `/api/v1/multiplayer/rooms` works
- [ ] No errors in Replit Console

**Frontend**:
- [ ] Homepage loads correctly
- [ ] Can start and complete a game
- [ ] Trading functionality works
- [ ] Multiplayer room creation works
- [ ] Leaderboard updates
- [ ] No CORS errors in browser console
- [ ] Mobile view works (responsive)

### Monitoring

- [ ] UptimeRobot monitor active (if using free tier)
- [ ] Email alerts configured
- [ ] Vercel Analytics enabled (optional)
- [ ] Bookmark live URLs for easy access

## Deployment Architecture

```
┌─────────────────────────────────────────────┐
│                                             │
│  Users (Students/Teachers)                  │
│                                             │
└──────────────────┬──────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │  Vercel (Frontend)   │
        │  Next.js App         │
        │  FREE                │
        └──────────┬───────────┘
                   │
                   │ HTTPS API Calls
                   ↓
        ┌──────────────────────┐
        │  Replit (Backend)    │
        │  FastAPI Server      │
        │  FREE or $7-$20/mo   │
        └──────────┬───────────┘
                   │
                   │ PostgreSQL Connection
                   ↓
        ┌──────────────────────┐
        │  Neon/Supabase DB    │
        │  PostgreSQL          │
        │  FREE (0.5-500MB)    │
        └──────────────────────┘
```

## Cost Breakdown

### Minimal Setup (FREE)
- Replit Free Tier: $0
- Vercel Free Tier: $0
- Neon Database Free: $0
- UptimeRobot: $0
- **Total Fixed**: $0/month
- **Variable**: OpenAI API usage (~$20-84/month depending on usage)

### Production Setup
- Replit Reserved VM: $7/month
- Vercel Free Tier: $0
- Neon Database Free: $0
- **Total Fixed**: $7/month
- **Variable**: OpenAI API usage

### High-Scale Setup
- Replit Autoscale: $20/month
- Vercel Pro (optional): $20/month
- Neon Pro (optional): $19/month
- **Total Fixed**: $20-59/month
- **Variable**: OpenAI API usage

## Troubleshooting

### "Module not found" errors

**Solution**: Install dependencies manually in Replit Shell
```bash
cd api
pip install -r requirements.txt
```

### "Database connection failed"

**Solution**: Check DATABASE_URL secret
```bash
# In Replit Shell
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### "CORS errors" in frontend

**Solution**: Verify FRONTEND_URL is set in Replit Secrets and backend was restarted

### "API returns 404"

**Solution**: Check that Replit is running and the URL is correct. API should be at `/api/v1/...` not `/v1/...`

### Backend sleeps (free tier)

**Solution**: Set up UptimeRobot or upgrade to Reserved VM ($7/month)

### "Data not loading" in frontend

**Solution**: Check browser console for errors. Verify:
- NEXT_PUBLIC_API_URL is correct in Vercel
- Backend is responding at that URL
- CORS is configured correctly

## Maintenance

### Regular Tasks

**Weekly**:
- Check OpenAI API usage/costs
- Review error logs in Replit Console
- Verify UptimeRobot is pinging successfully

**Monthly**:
- Update dependencies (if needed)
- Database backup (export from Neon/Supabase)
- Review Vercel analytics

**Quarterly**:
- Rotate API keys for security
- Review and optimize database size
- Update documentation

### Scaling Triggers

- **>50 concurrent users**: Upgrade Replit to Autoscale ($20/month)
- **Database >500MB**: Upgrade Neon to Pro ($19/month)
- **>100 students**: Consider dedicated hosting or contact Replit support

## Classroom Launch Checklist

Before announcing to students:

### Teacher Preparation
- [ ] Demo game completed successfully
- [ ] Created test multiplayer room
- [ ] Verified room codes work
- [ ] Leaderboard displays correctly
- [ ] Understand scoring system
- [ ] Prepared student instructions

### Student Instructions Document
Create a simple guide with:
- [ ] Live URL: `https://your-app.vercel.app`
- [ ] How to join a room with code
- [ ] Trading rules (can only buy when AI says BUY/STRONG_BUY)
- [ ] Scoring criteria (portfolio return, risk discipline, beat AI, drawdown)
- [ ] Grade thresholds (A: 700+, B: 550-699, C: 400-549, D: 250-399, F: <250)

### Launch Day
- [ ] URLs ready to share
- [ ] Support channel set up (email/Slack/etc.)
- [ ] Monitor for first hour
- [ ] Be ready to help students join rooms
- [ ] Collect feedback

## Support

If you encounter issues:

1. Check Replit Console for backend errors
2. Check browser console for frontend errors
3. Verify all Secrets/Environment Variables are set
4. Test database connection in Replit Shell
5. Check API docs: `https://your-repl.replit.dev/docs`

## You're Live! 🎉

Once deployed, you have:

✅ Backend API: `https://your-repl.replit.dev`
✅ Frontend: `https://your-app.vercel.app`
✅ API Docs: `https://your-repl.replit.dev/docs`

Share the frontend URL with your students and start teaching!

---

**Deployment Status**: ⬜ Not Started | 🔄 In Progress | ✅ Complete

**Last Updated**: 2025-12-28

**Deployed By**: ________________

**Live URLs**:
- Backend: ________________________________
- Frontend: ________________________________
- API Docs: ________________________________
