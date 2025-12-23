# Stock AI Platform - Web Frontend

Production-grade Next.js 14 web platform for AI-powered stock recommendations.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.3+
- **Styling**: Tailwind CSS 3.4+ with custom design system
- **UI Components**: shadcn/ui (when installed)
- **Data Fetching**: TanStack Query (React Query) v5
- **State Management**: Zustand with localStorage persistence
- **Icons**: Lucide React
- **Charts**: Recharts
- **Fonts**: Inter (UI), JetBrains Mono (numbers/tickers)

## Documentation

- [GAME_IMPLEMENTATION.md](../GAME_IMPLEMENTATION.md) - Complete game design and mechanics (450+ lines)
- [PHASE_4_COMPLETE.md](../PHASE_4_COMPLETE.md) - Phase 4 implementation summary
- [SETUP.md](SETUP.md) - Detailed setup and troubleshooting guide
- [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) - Overall project status

## What Is This?

This web frontend is an **educational turn-based stock trading game** where students compete against an AI opponent. Key features:

- Turn-based gameplay (you control time)
- AI recommendations with explanations
- Buy/sell trading with validation
- Scoring system with A-F grades
- Portfolio simulation ($10,000 starting cash)
- localStorage persistence (resume games)

See [GAME_IMPLEMENTATION.md](../GAME_IMPLEMENTATION.md) for complete game documentation.

## Prerequisites

Before running the web frontend, ensure you have:

1. **Node.js 18+** installed
   ```bash
   # macOS
   brew install node

   # Or download from https://nodejs.org/
   ```

2. **pnpm** (recommended) or npm
   ```bash
   npm install -g pnpm
   ```

3. **Backend API running** at http://192.168.5.126:8000
   ```bash
   # From project root
   cd api
   source venv/bin/activate
   python -m app.main
   ```

## Getting Started

### 1. Install Dependencies

```bash
cd web
pnpm install
# or: npm install
```

### 2. Environment Setup

The `.env.local` file is already configured:

```env
NEXT_PUBLIC_API_URL=http://192.168.5.126:8000
```

For production, update this to your deployed API URL.

### 3. Run Development Server

```bash
pnpm dev
# or: npm run dev
```

Open [http://192.168.5.126:3000](http://192.168.5.126:3000) to view the app.

### 4. Build for Production

```bash
pnpm build
pnpm start
```

## Project Structure

```
web/
├── app/                        # Next.js 14 App Router
│   ├── layout.tsx             # Root layout with providers
│   ├── page.tsx               # Homepage (dashboard)
│   ├── globals.css            # Global styles and CSS variables
│   ├── providers.tsx          # React Query provider
│   ├── stocks/
│   │   ├── page.tsx           # Stock list (TODO)
│   │   └── [ticker]/
│   │       └── page.tsx       # Stock detail (TODO)
│   ├── portfolio/
│   │   └── page.tsx           # Portfolio simulation (TODO)
│   └── analytics/
│       └── page.tsx           # Backtesting UI (TODO)
│
├── components/
│   ├── ui/                    # shadcn/ui components (TODO)
│   ├── layout/                # Header, Footer, Hero
│   │   └── hero.tsx
│   ├── stocks/                # Stock-specific components
│   │   ├── top-picks.tsx
│   │   └── recommendation-card.tsx
│   ├── portfolio/             # Portfolio components (TODO)
│   └── analytics/             # Analytics components (TODO)
│
├── lib/
│   ├── api/                   # API client layer
│   │   ├── client.ts          # Base API client
│   │   └── recommendations.ts # Recommendations end points
│   ├── hooks/                 # Custom React hooks
│   │   └── useRecommendations.ts
│   ├── stores/                # Zustand stores (TODO)
│   ├── utils/                 # Utility functions
│   │   ├── cn.ts              # Tailwind merge utility
│   │   └── format.ts          # Formatting utilities
│   └── constants/             # App configuration (TODO)
│
├── types/
│   └── api.ts                 # TypeScript types matching API
│
├── public/                    # Static assets
│
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript configuration
├── tailwind.config.ts         # Tailwind configuration
├── next.config.js             # Next.js configuration
├── .eslintrc.json             # ESLint rules
├── .prettierrc                # Prettier configuration
└── .env.local                 # Environment variables
```

## Available Scripts

```bash
pnpm dev          # Start development server (http://192.168.5.126:3000)
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
pnpm type-check   # Run TypeScript compiler check
```

## Features Implemented

### Week 1 (Current)

- ✅ Next.js 14 project initialization
- ✅ TypeScript, ESLint, Prettier configuration
- ✅ Tailwind CSS with custom design system
- ✅ React Query (TanStack Query) setup
- ✅ API client with error handling
- ✅ Homepage with Hero section
- ✅ Top Picks component showing AI recommendations
- ✅ Recommendation Card component
- ✅ Type-safe API integration
- ✅ Loading and error states

### Coming Next

- [ ] Stock List page with filtering/sorting
- [ ] Stock Detail page with full recommendation rationale
- [ ] Portfolio simulation (Zustand store)
- [ ] Analytics/Backtesting page
- [ ] shadcn/ui component installation
- [ ] Responsive mobile design
- [ ] Testing (Vitest, Playwright)
- [ ] Deployment (Vercel)

## Design System

### Colors

Financial semantic colors for stock recommendations:

```typescript
bullish: { DEFAULT: '#10B981', light: '#D1FAE5' }    // Green
bearish: { DEFAULT: '#EF4444', light: '#FEE2E2' }    // Red
neutral: { DEFAULT: '#6B7280', light: '#F3F4F6' }    // Gray

// Recommendation badges
buy: { DEFAULT: '#059669', bg: '#D1FAE5' }
sell: { DEFAULT: '#DC2626', bg: '#FEE2E2' }
hold: { DEFAULT: '#F59E0B', bg: '#FEF3C7' }
```

### Typography

- **UI Text**: Inter (Google Font)
- **Numbers/Tickers**: JetBrains Mono (Google Font, monospace)

### Spacing

- 8px grid system
- Container max-width: 1400px

## API Integration

### End points Used

```
GET /api/v1/recommendations/           # List recommendations
GET /api/v1/recommendations/{ticker}   # Single recommendation
```

### Data Fetching Strategy

- **Server State**: TanStack Query for API data
  - 5-minute stale time
  - Automatic background refetching
  - Request deduplication

- **Client State**: Zustand for portfolio simulation (coming soon)
  - localStorage persistence
  - No authentication needed (local-only)

## Deployment

### Option 1: Vercel (Recommended)

```bash
# Install Vercel CLI
pnpm add -g vercel

# Deploy
vercel
```

### Option 2: Docker

```bash
# Build Docker image
docker build -t stock-ai-web .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://your-api.com stock-ai-web
```

### Option 3: Static Export

```bash
# Build static site
pnpm build

# Output in: ./out
# Deploy to any static host (Netlify, CloudFlare Pages, etc.)
```

## Environment Variables

```env
# Development (.env.local)
NEXT_PUBLIC_API_URL=http://192.168.5.126:8000

# Production (.env.production)
NEXT_PUBLIC_API_URL=https://api.yourproduction.com
```

## Performance Targets

- **Lighthouse Score**: 90+ across all metrics
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

## Troubleshooting

### API Connection Issues

1. Ensure backend API is running:
   ```bash
   curl http://192.168.5.126:8000/api/v1/health
   ```

2. Check NEXT_PUBLIC_API_URL in `.env.local`

3. Verify CORS is configured in FastAPI backend

### Build Errors

1. Clear Next.js cache:
   ```bash
   rm -rf .next
   pnpm build
   ```

2. Check TypeScript errors:
   ```bash
   pnpm type-check
   ```

## Contributing

See main project [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

MIT License - See [LICENSE](../LICENSE)
