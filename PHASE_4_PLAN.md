# Phase 4: Web Platform - Implementation Plan

> **Note**: This document describes the original plan for a Bloomberg-style financial dashboard. The actual implementation pivoted to a **game-first educational approach** with a turn-based stock trading game. See [PHASE_4_COMPLETE.md](PHASE_4_COMPLETE.md) and [GAME_IMPLEMENTATION.md](GAME_IMPLEMENTATION.md) for the actual implementation.

**Status**: 📋 Original Plan - Implementation Pivoted to Game-First Approach
**Estimated Timeline**: 4 weeks to MVP (original estimate)
**Tech Stack**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Query

---

## 📊 Executive Summary

Building a **production-grade Next.js web platform** that showcases AI stock recommendations with Bloomberg/Robinhood-level polish. The frontend will mirror the backend's architectural excellence: read-only data consumption, performance-first design, and professional implementation.

### Key Goals

1. **Showcase AI Recommendations** - Beautiful, explainable UI for stock analysis
2. **Portfolio Simulation** - Paper trading to test AI signals
3. **Performance Analytics** - Backtesting and accuracy tracking
4. **Mobile-First Design** - Responsive across all devices
5. **Production Quality** - Lighthouse 90+, WCAG AA compliant

---

## 🏗️ Technology Stack

### Core Framework
- **Next.js 14.2+** with App Router (Server Components)
- **TypeScript 5.3+** with strict mode
- **React 18+** with Server Components as default

### Styling & UI
- **Tailwind CSS 3.4+** with custom design system
- **shadcn/ui** for accessible, customizable components
- **Lucide React** for icons
- **Recharts** for financial charts

### Data & State
- **TanStack Query (React Query)** v5 for server state
- **Zustand** for client state (portfolio, UI preferences)
- **Native fetch** with Next.js caching strategies

### Type Safety
- **Zod** for runtime validation
- **TypeScript** codegen from OpenAPI spec

### Testing
- **Vitest** for unit tests
- **Playwright** for E2E tests
- **Testing Library** for component tests
- **MSW** for API mocking

---

## 📁 Project Structure

```
web/
├── src/
│   ├── app/                       # Next.js 14 App Router
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Homepage (dashboard)
│   │   ├── stocks/
│   │   │   ├── page.tsx          # Stock list
│   │   │   └── [ticker]/
│   │   │       └── page.tsx      # Stock detail
│   │   ├── portfolio/
│   │   │   └── page.tsx          # Portfolio simulation
│   │   └── analytics/
│   │       └── page.tsx          # Backtesting UI
│   │
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components
│   │   ├── layout/               # Header, Footer, Nav
│   │   ├── stocks/               # Stock-specific components
│   │   ├── portfolio/            # Portfolio components
│   │   └── analytics/            # Analytics components
│   │
│   ├── lib/
│   │   ├── api/                  # API client layer
│   │   ├── hooks/                # Custom React hooks
│   │   ├── stores/               # Zustand stores
│   │   ├── utils/                # Utility functions
│   │   └── constants/            # App configuration
│   │
│   └── types/                    # TypeScript types
│
├── .env.local                     # Environment variables
├── next.config.js                # Next.js configuration
├── tailwind.config.ts            # Tailwind configuration
└── README.md                      # Web-specific docs
```

---

## 🎨 Key Pages

### 1. Homepage/Dashboard (`/`)
**Purpose:** First impression, today's top picks, system status

**Features:**
- Hero section with value proposition
- Top 4 AI recommendations (BUY/HOLD/SELL)
- System metrics (stocks tracked, last update)
- Quick navigation to key sections

**Data Fetching:**
- SSR for SEO
- Fetch from `/api/v1/recommendations/today/top`
- 5-minute cache revalidation

---

### 2. Stock List (`/stocks`)
**Purpose:** Browse all recommendations, filter by signal

**Features:**
- Filter by recommendation type (BUY/HOLD/SELL)
- Sort by confidence, ticker
- Search by ticker
- Pagination or infinite scroll
- Skeleton loaders

**Data Fetching:**
- Client-side with React Query
- Fetch from `/api/v1/recommendations/`
- 5-minute stale time

---

### 3. Stock Detail (`/stocks/[ticker]`)
**Purpose:** Deep dive into single recommendation

**Features:**
- Full recommendation with confidence score
- Signal indicators (Technical/Sentiment/Risk)
- Expandable rationale sections
- Interactive charts
- Historical performance tracking
- Model metadata

**Layout:**
```
┌─────────────────────────────────────────────┐
│  AAPL • Apple Inc.               $175.43   │
│  ┌──────────────────────────────────────┐  │
│  │  BUY    65% Confidence   Medium Risk │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  [Technical] [Sentiment] [Risk] [History]  │
│  ┌──────────────────────────────────────┐  │
│  │  Technical Analysis                  │  │
│  │  • Trading above key moving averages │  │
│  │  • RSI at 57.58, room to move higher │  │
│  │  [Interactive Chart]                 │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

**Data Fetching:**
- SSR for initial load
- Fetch from `/api/v1/recommendations/{ticker}`
- Fetch from `/api/v1/recommendations/{ticker}/history`

---

### 4. Portfolio Simulation (`/portfolio`)
**Purpose:** Paper trading to test AI recommendations

**Features:**
- Current holdings with P&L
- Available cash
- Buy/Sell actions based on AI signals
- Performance chart vs benchmarks
- Trade history
- Reset functionality

**State Management:**
- Zustand store with localStorage persistence
- No authentication needed (local-only)
- Simulated trades with historical prices

---

### 5. Analytics/Backtesting (`/analytics`)
**Purpose:** Visualize AI performance over time

**Features:**
- Aggregate metrics (win rate, avg return, Sharpe)
- Accuracy breakdown by recommendation type
- Performance charts
- Best/worst calls
- Downloadable reports

---

## 🎨 Design System

### Color Palette
```typescript
// Financial semantic colors
bullish: { DEFAULT: '#10B981', light: '#D1FAE5' }    // Green
bearish: { DEFAULT: '#EF4444', light: '#FEE2E2' }    // Red
neutral: { DEFAULT: '#6B7280', light: '#F3F4F6' }    // Gray

// Recommendation badges
buy: { DEFAULT: '#059669', bg: '#D1FAE5' }
sell: { DEFAULT: '#DC2626', bg: '#FEE2E2' }
hold: { DEFAULT: '#F59E0B', bg: '#FEF3C7' }
```

### Typography
- **UI Text:** Inter (system font)
- **Numbers/Tickers:** JetBrains Mono (monospace)

### Spacing
- 8px grid system
- Generous whitespace

### Visual Style
- Subtle card shadows with hover effects
- Rounded corners (8px)
- Dark mode for charts, light mode for marketing

---

## 🔌 API Integration

### API Client (`lib/api/client.ts`)
```typescript
const API_BASE_URL = 'http://192.168.5.126:8000';

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) throw new APIError(response.status, response.statusText);
  return response.json();
}
```

### Query Hooks (`lib/hooks/useRecommendation.ts`)
```typescript
export function useRecommendation(ticker: string) {
  return useQuery({
    queryKey: ['recommendation', ticker],
    queryFn: () => getRecommendation(ticker),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!ticker,
  });
}
```

### API Functions (`lib/api/recommendations.ts`)
```typescript
export async function getRecommendation(ticker: string): Promise<RecommendationDetail>
export async function getRecommendations(params?): Promise<RecommendationList>
export async function getTopRecommendations(limit = 10): Promise<Recommendation[]>
export async function getRecommendationHistory(ticker, limit): Promise<HistoricalRecommendation[]>
```

---

## 💾 State Management

### Server State: TanStack Query
For all API data (recommendations, history):
- Automatic caching
- Background refetching
- Request deduplication
- 5-minute stale time

### Client State: Zustand
For local-only state (portfolio, UI preferences):
```typescript
interface PortfolioState {
  cash: number;
  holdings: Record<string, Holding>;
  trades: Trade[];
  buyStock: (ticker: string, shares: number, price: number) => void;
  sellStock: (ticker: string, shares: number, price: number) => void;
  getTotalValue: () => number;
  getReturns: () => number;
}

export const usePortfolioStore = create<PortfolioState>()(
  persist(
    (set, get) => ({ /* implementation */ }),
    { name: 'portfolio-storage' }
  )
);
```

---

## 📅 Implementation Timeline (4 Weeks)

### Week 1: Foundation & Core Pages
**Day 1-2: Project Setup**
- [ ] Initialize Next.js 14 with TypeScript
- [ ] Install dependencies (Tailwind, shadcn/ui, React Query)
- [ ] Configure TypeScript, ESLint, Prettier
- [ ] Set up folder structure
- [ ] Create `.env.local` with API URL

**Day 3-4: Layout & Navigation**
- [ ] Root layout with providers
- [ ] Header/Navbar component
- [ ] Footer component
- [ ] Configure fonts (Inter, JetBrains Mono)
- [ ] Global styles and Tailwind config

**Day 5-7: Homepage/Dashboard**
- [ ] Hero section
- [ ] "Top Picks" section with StockCard
- [ ] Fetch data from `/today/top` endpoint
- [ ] Loading skeletons
- [ ] Error handling UI

---

### Week 2: Stock Pages & Components
**Day 8-10: Stock List Page**
- [ ] Stock list/screener UI
- [ ] Filtering (BUY/HOLD/SELL)
- [ ] Sorting (confidence, ticker)
- [ ] Pagination
- [ ] Search functionality

**Day 11-14: Stock Detail Page**
- [ ] Stock header component
- [ ] Recommendation badge/card
- [ ] Signal indicators
- [ ] Rationale accordion
- [ ] Confidence gauge
- [ ] Historical performance chart

---

### Week 3: Portfolio Simulation
**Day 15-17: Portfolio State & UI**
- [ ] Zustand portfolio store
- [ ] Portfolio summary component
- [ ] Holdings list
- [ ] Buy/Sell actions
- [ ] Trade history table
- [ ] Performance chart

**Day 18-21: Integration & Polish**
- [ ] Connect to real stock prices
- [ ] Calculate returns accurately
- [ ] Transaction validation
- [ ] Export trade history (CSV)
- [ ] Portfolio reset
- [ ] Responsive design for mobile

---

### Week 4: Analytics & Testing
**Day 22-24: Backtesting/Analytics Page**
- [ ] Metrics grid (win rate, avg return)
- [ ] Accuracy breakdown by type
- [ ] Performance chart over time
- [ ] Best/worst calls table

**Day 25-28: Testing & Deployment**
- [ ] Unit tests for utility functions
- [ ] Component tests for key components
- [ ] E2E tests for critical flows
- [ ] Performance audit (Lighthouse 90+)
- [ ] Accessibility audit (WCAG AA)
- [ ] SEO optimization
- [ ] Deployment (Vercel/Netlify)

---

## 🧪 Testing Strategy

### Unit Tests (Vitest)
```typescript
// __tests__/lib/utils/format.test.ts
describe('formatCurrency', () => {
  it('formats positive values correctly', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });
});
```

### Component Tests (Testing Library)
```typescript
// __tests__/components/RecommendationCard.test.tsx
describe('RecommendationCard', () => {
  it('renders BUY recommendation correctly', () => {
    render(<RecommendationCard ticker="AAPL" recommendation="BUY" confidence={0.65} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('BUY')).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)
```typescript
// e2e/stock-detail.spec.ts
test('displays stock recommendation details', async ({ page }) => {
  await page.goto('/stocks/AAPL');
  await expect(page.locator('h1')).toContainText('AAPL');
  await expect(page.locator('[data-testid="recommendation-badge"]')).toContainText('BUY');
});
```

---

## 🚀 Deployment

### Environment Variables
```bash
# .env.local (development)
NEXT_PUBLIC_API_URL=http://192.168.5.126:8000

# .env (production)
NEXT_PUBLIC_API_URL=https://api.stockai.example.com
```

### Deployment Options

**Option 1: Vercel (Recommended)**
- Zero-config deployment
- Automatic HTTPS and CDN
- Preview deployments for PRs
- Free tier sufficient for MVP

**Option 2: Netlify**
- Similar to Vercel
- Great DX for static sites

**Option 3: Self-hosted (Docker)**
- Full control
- Can run alongside backend

---

## 📊 Performance Targets

### Lighthouse Scores (Target: 90+)
- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

### Core Web Vitals
- **LCP:** < 2.5s
- **FID:** < 100ms
- **CLS:** < 0.1

### Optimization Techniques
- Server Components for static content
- Dynamic imports for heavy components
- Route prefetching on hover
- API response caching (5-minute SWR)
- Image optimization (next/image)
- Font subsetting

---

## ✅ Success Criteria

- [ ] All 5 API end points integrated
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Lighthouse score 90+ across all metrics
- [ ] Zero accessibility violations (WCAG AA)
- [ ] Portfolio simulation working with local storage
- [ ] E2E tests covering critical user flows
- [ ] Production deployment (Vercel/Netlify)

---

## 🎯 Key Components to Build

### 1. RecommendationCard
Reusable card displaying ticker, recommendation, confidence, and signals.

### 2. ConfidenceGauge
Visual representation of confidence score (radial progress or gauge).

### 3. RationaleAccordion
Expandable sections for technical/sentiment/risk analysis.

### 4. SignalBadge
Color-coded badge for BULLISH/NEUTRAL/BEARISH signals.

### 5. PortfolioSummary
Overview of portfolio value, returns, holdings.

### 6. PerformanceChart
Line chart comparing portfolio vs benchmarks.

### 7. StockHeader
Stock detail page header with ticker, price, recommendation.

---

## 📚 Additional Resources

### Backend Integration points
- API: `http://192.168.5.126:8000/api/v1/`
- Docs: `http://192.168.5.126:8000/docs`
- Schema: `/api/app/schemas/recommendations.py`

### Design Inspiration
- Bloomberg Terminal (professional financial UI)
- Robinhood (clean, accessible design)
- TradingView (interactive charts)

### Documentation
- Next.js 14: https://nextjs.org/docs
- shadcn/ui: https://ui.shadcn.com
- React Query: https://tanstack.com/query
- Tailwind CSS: https://tailwindcss.com

---

## 🚀 Ready to Start?

**First Steps:**
1. Review this plan and provide feedback
2. Initialize Next.js project in `web/` directory
3. Set up shadcn/ui and Tailwind
4. Create API client with TypeScript types
5. Build homepage with top picks

**Questions to Clarify:**
- Do you want to start with Week 1 (Foundation)?
- Any specific design preferences or modifications?
- Should we deploy to Vercel or prefer self-hosted?
- Any additional features to prioritize?

Let me know if you'd like to proceed with implementation or need any modifications to the plan!
