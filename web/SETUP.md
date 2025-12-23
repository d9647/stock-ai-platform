# Web Frontend Setup Guide

## Prerequisites Check

Before you begin, verify you have the following installed:

### 1. Node.js (v18 or higher)

```bash
node --version
```

If not installed:
- **macOS**: `brew install node`
- **Windows**: Download from https://nodejs.org/
- **Linux**: `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs`

### 2. Package Manager

We recommend **pnpm** for faster installs:

```bash
npm install -g pnpm
pnpm --version
```

Alternatively, use npm (comes with Node.js):
```bash
npm --version
```

### 3. Backend API

The web frontend requires the backend API to be running:

```bash
# Terminal 1: Start the API
cd api
source venv/bin/activate
python -m app.main

# Verify API is running
curl http://192.168.5.126:8000/api/v1/health
```

You should see: `{"status":"healthy","timestamp":"..."}`

---

## Installation Steps

### Step 1: Install Dependencies

```bash
cd web
pnpm install
```

This will install:
- Next.js 14.2+
- React 18+
- TypeScript 5.3+
- Tailwind CSS 3.4+
- TanStack Query (React Query) v5
- Zustand v5
- And all other dependencies

**Expected time**: 1-2 minutes

### Step 2: Verify Environment

Check that `.env.local` exists and contains:

```env
NEXT_PUBLIC_API_URL=http://192.168.5.126:8000
```

This file is already created - no action needed unless you want to change the API URL.

### Step 3: Start Development Server

```bash
pnpm dev
```

You should see:
```
  ▲ Next.js 14.2.18
  - Local:        http://192.168.5.126:3000
  - Ready in 2.5s
```

### Step 4: Open in Browser

Navigate to: [http://192.168.5.126:3000](http://192.168.5.126:3000)

You should see:
- Hero section with "AI-Powered Stock Recommendations"
- "Today's Top Picks" section with recommendation cards

---

## Troubleshooting

### Issue: `command not found: node`

**Solution**: Install Node.js (see Prerequisites above)

### Issue: `command not found: pnpm`

**Solution**: Either install pnpm (`npm install -g pnpm`) or use npm instead:
```bash
npm install
npm run dev
```

### Issue: "Error loading recommendations"

**Cause**: Backend API is not running or not accessible

**Solutions**:

1. **Start the API**:
   ```bash
   cd api
   source venv/bin/activate
   python -m app.main
   ```

2. **Verify API is running**:
   ```bash
   curl http://192.168.5.126:8000/api/v1/health
   ```

3. **Check for recommendations**:
   ```bash
   curl http://192.168.5.126:8000/api/v1/recommendations/
   ```

   If this returns `{"recommendations": [], "total": 0}`, you need to generate recommendations:
   ```bash
   cd services/agent-orchestrator
   source venv/bin/activate
   python -m src.pipelines.daily_agent_pipeline --tickers AAPL MSFT
   ```

### Issue: Port 3000 already in use

**Solution**: Use a different port:
```bash
pnpm dev -p 3001
```

Or kill the process using port 3000:
```bash
lsof -ti:3000 | xargs kill
```

### Issue: TypeScript errors

**Solution**: Run type checking:
```bash
pnpm type-check
```

Fix any errors reported before running `pnpm dev` again.

### Issue: Build fails

**Solution**: Clear Next.js cache and rebuild:
```bash
rm -rf .next
pnpm install
pnpm build
```

---

## Verification Checklist

After setup, verify everything works:

- [ ] Homepage loads at http://192.168.5.126:3000
- [ ] Hero section displays correctly
- [ ] "Today's Top Picks" section shows recommendation cards (if API has data)
- [ ] No console errors in browser DevTools
- [ ] No TypeScript errors: `pnpm type-check`
- [ ] Clicking a recommendation card navigates to stock detail page (will show 404 for now - not implemented yet)

---

## Next Steps

Now that the foundation is set up, you can:

1. **Explore the codebase**:
   - `app/page.tsx` - Homepage
   - `components/stocks/` - Recommendation components
   - `lib/api/` - API client
   - `lib/hooks/` - React Query hooks

2. **Continue Phase 4 implementation**:
   - Week 2: Stock List and Detail pages
   - Week 3: Portfolio simulation
   - Week 4: Analytics and testing

3. **Customize the design**:
   - Edit `tailwind.config.ts` for colors
   - Modify `app/globals.css` for global styles
   - Update `components/layout/hero.tsx` for homepage content

---

## Useful Commands

```bash
# Development
pnpm dev              # Start dev server
pnpm lint             # Run ESLint
pnpm type-check       # Check TypeScript types

# Production
pnpm build            # Build for production
pnpm start            # Start production server

# Maintenance
pnpm install          # Install dependencies
rm -rf .next          # Clear build cache
rm -rf node_modules && pnpm install  # Fresh install
```

---

## Need Help?

- **Documentation**: See [README.md](./README.md)
- **Phase 4 Plan**: See [PHASE_4_PLAN.md](../PHASE_4_PLAN.md)
- **API Docs**: http://192.168.5.126:8000/docs (when API is running)
- **Next.js Docs**: https://nextjs.org/docs
- **React Query Docs**: https://tanstack.com/query/latest

---

**You're ready to build!** 🚀
