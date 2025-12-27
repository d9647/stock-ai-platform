# Deployment Checklist

Quick reference checklist for deploying Stock AI Platform.

---

## 🎯 Pre-Deployment

### Local Setup
- [ ] All code committed to GitHub
- [ ] `.env` files NOT committed (check `.gitignore`)
- [ ] Database migrations up to date locally
- [ ] Local tests passing
- [ ] All API endpoints working locally

### External Services
- [ ] OpenAI API key obtained
- [ ] Polygon.io API key obtained
- [ ] Finnhub API key obtained
- [ ] NewsAPI key obtained
- [ ] Production database provisioned (Neon/Supabase)

---

## 🚀 Replit Backend Deployment

### 1. Import Project
- [ ] Create Replit account
- [ ] Import from GitHub
- [ ] Verify files loaded correctly

### 2. Configure Secrets (🔒 in sidebar)
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `OPENAI_API_KEY` - OpenAI API key
- [ ] `POLYGON_API_KEY` - Polygon.io key
- [ ] `FINNHUB_API_KEY` - Finnhub key
- [ ] `NEWSAPI_KEY` - NewsAPI key
- [ ] `FRONTEND_URL` - Vercel URL (add after frontend deployment)
- [ ] `SECRET_KEY` - Generated secret (optional)
- [ ] `JWT_SECRET` - Generated JWT secret (optional)

### 3. Database Setup
- [ ] Run migrations: `cd api && python -m alembic upgrade head`
- [ ] Verify tables created: `psql $DATABASE_URL -c "\dt"`
- [ ] Import local data (if needed): `psql $DATABASE_URL < backup.sql`

### 4. Test Backend
- [ ] Click ▶️ Run button
- [ ] Visit: `https://your-repl.replit.dev/docs`
- [ ] Test health endpoint: `/api/v1/health`
- [ ] Test game endpoint: `/api/v1/game/data?days=10&tickers=AAPL`

### 5. Deploy (Optional - for always-on)
- [ ] Click "Deploy" button
- [ ] Choose: Reserved VM ($7/month) or Autoscale ($20/month)
- [ ] Verify deployment URL works

### 6. Keep Awake (If using free tier)
- [ ] Sign up at [uptimerobot.com](https://uptimerobot.com)
- [ ] Add monitor for `/api/v1/health` endpoint
- [ ] Set interval to 5 minutes

---

## 🌐 Vercel Frontend Deployment

### 1. Prepare Repository
- [ ] Code pushed to GitHub
- [ ] `web` folder contains Next.js app
- [ ] `package.json` has correct scripts

### 2. Import to Vercel
- [ ] Create Vercel account
- [ ] Click "New Project"
- [ ] Import from GitHub
- [ ] Select repository

### 3. Configure Project
- [ ] Framework: Next.js (auto-detected)
- [ ] Root Directory: `web`
- [ ] Build Command: `npm run build` (default)
- [ ] Output Directory: `.next` (default)

### 4. Add Environment Variable
- [ ] Add `NEXT_PUBLIC_API_URL`:
  ```
  https://your-repl-name.your-username.replit.dev
  ```
  (Use your actual Replit URL)

### 5. Deploy
- [ ] Click "Deploy"
- [ ] Wait ~2 minutes for build
- [ ] Verify deployment successful

### 6. Update Backend CORS
- [ ] Copy Vercel URL (e.g., `https://your-app.vercel.app`)
- [ ] Add to Replit Secrets: `FRONTEND_URL=https://your-app.vercel.app`
- [ ] Restart Replit backend (click Run again)

### 7. Test Frontend
- [ ] Visit Vercel URL
- [ ] Click "Start Playing Now"
- [ ] Verify game data loads
- [ ] Test full game flow
- [ ] Test multiplayer mode

---

## 🔐 Security Hardening

### Secrets Management
- [ ] All API keys stored in Replit Secrets (not in code)
- [ ] `.env` files in `.gitignore`
- [ ] No secrets committed to GitHub
- [ ] Different keys for dev/prod

### CORS Configuration
- [ ] Frontend URL added to Replit Secrets
- [ ] CORS settings in `api/app/core/config.py` updated
- [ ] Wildcard `*` removed from CORS (if present)
- [ ] Only specific domains whitelisted

### Database Security
- [ ] Database password is strong
- [ ] Connection uses SSL (check Neon/Supabase settings)
- [ ] No public database access
- [ ] Regular backups enabled

---

## 📊 Data Migration

### Export from Local
- [ ] Run: `pg_dump -U postgres stock_ai | gzip > backup.sql.gz`
- [ ] Verify backup file created
- [ ] Check file size (should be < 500MB for free tier)

### Import to Production
- [ ] Upload backup to Replit (drag & drop)
- [ ] Run: `gunzip -c backup.sql.gz | psql $DATABASE_URL`
- [ ] Verify data imported: check row counts
- [ ] Test API returns correct data

---

## ✅ Post-Deployment Verification

### Backend Tests
- [ ] Health check: `https://backend-url/api/v1/health` returns OK
- [ ] API docs: `https://backend-url/docs` loads
- [ ] Game data: `https://backend-url/api/v1/game/data?days=10&tickers=AAPL` returns data
- [ ] Recommendations: `https://backend-url/api/v1/recommendations/` returns data
- [ ] Multiplayer endpoints working

### Frontend Tests
- [ ] Homepage loads correctly
- [ ] Can start new game
- [ ] Game lobby works
- [ ] Can advance through days
- [ ] Trading (buy/sell) works
- [ ] Scoring system works
- [ ] Game over screen shows
- [ ] Multiplayer room creation works
- [ ] Multiplayer room joining works
- [ ] Leaderboard updates

### Integration Tests
- [ ] Frontend can call backend APIs
- [ ] No CORS errors in browser console
- [ ] Data loads within 3 seconds
- [ ] No errors in Replit console
- [ ] Mobile view works (responsive design)

---

## 📈 Monitoring Setup

### UptimeRobot (Free)
- [ ] Account created
- [ ] Monitor added for backend health endpoint
- [ ] Email alerts configured
- [ ] Monitor interval: 5 minutes

### Vercel Analytics (Optional)
- [ ] Enable Vercel Analytics
- [ ] Monitor page load times
- [ ] Track user visits

### Error Tracking (Optional)
- [ ] Sentry account created (free tier)
- [ ] Sentry integrated in frontend
- [ ] Test error reporting

---

## 💰 Cost Tracking

### Current Costs
- [ ] Replit: $___/month (Free, $7 Reserved, or $20 Autoscale)
- [ ] Vercel: $0/month (Free tier)
- [ ] Database: $0/month (Free tier) or $___/month
- [ ] OpenAI API: ~$___/month (pay-as-you-go)
- [ ] **Total**: ~$___/month

### Usage Monitoring
- [ ] OpenAI usage dashboard checked weekly
- [ ] Database storage monitored
- [ ] Replit resource usage reviewed

---

## 📝 Documentation

### Update URLs
- [ ] README.md updated with live URLs
- [ ] MILESTONE_1_COMPLETE.md updated
- [ ] Deployment docs include actual URLs

### Share with Team
- [ ] Replit URL shared: `https://your-repl.replit.dev`
- [ ] Vercel URL shared: `https://your-app.vercel.app`
- [ ] Admin credentials shared (if any)
- [ ] API documentation shared: `https://your-repl.replit.dev/docs`

---

## 🎓 Classroom Setup (If applicable)

### Teacher Access
- [ ] Demo game completed successfully
- [ ] Multiplayer room creation tested
- [ ] Room codes working
- [ ] Leaderboard visible

### Student Instructions
- [ ] Create student guide with URLs
- [ ] Explain how to join room with code
- [ ] Provide trading rules
- [ ] Share scoring criteria

---

## 🔄 Maintenance Plan

### Regular Tasks
- [ ] Weekly: Check OpenAI API costs
- [ ] Weekly: Review error logs
- [ ] Monthly: Update dependencies
- [ ] Monthly: Database backup
- [ ] Quarterly: Rotate API keys

### Scaling Plan
- [ ] If >50 concurrent users: Upgrade Replit to Autoscale
- [ ] If database >500MB: Upgrade Neon to Pro
- [ ] If >100 students: Consider dedicated hosting

---

## 🎉 Go-Live Checklist

### Final Verification (Do this right before announcing)
- [ ] All deployment steps completed above
- [ ] Backend is responding
- [ ] Frontend is loading
- [ ] Can complete full game from start to finish
- [ ] Multiplayer mode works
- [ ] No errors in console
- [ ] URLs bookmarked

### Communication
- [ ] Live URLs ready to share
- [ ] User guide prepared
- [ ] Support email/channel set up
- [ ] Feedback mechanism in place

### Launch! 🚀
- [ ] Announce to users
- [ ] Monitor for first hour
- [ ] Respond to feedback
- [ ] Celebrate! 🎉

---

**Deployment Status**: ⬜ Not Started | 🔄 In Progress | ✅ Complete

**Last Updated**: ________________

**Deployed By**: ________________

**Live URLs**:
- Backend: ________________________________
- Frontend: ________________________________
- API Docs: ________________________________
