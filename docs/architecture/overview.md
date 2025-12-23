# Stock AI Platform - Architecture Overview

## Core Design Principles

### 1. The Golden Rule

> **If it can "think", it cannot block a request.**
>
> **If it serves a request, it must not think.**

This principle ensures:
- ✅ Low latency API responses (<100ms)
- ✅ Predictable costs
- ✅ Reproducible results
- ✅ Regulatory compliance

### 2. Append-Only, Immutable Data

All historical data is **APPEND-ONLY**:
- Market data (OHLCV, technical indicators)
- News and sentiment scores
- Feature snapshots
- Agent outputs
- Recommendations

**No UPDATE or DELETE operations on historical records.**

This ensures:
- Point-in-time correctness
- Auditability
- Backtesting accuracy
- No look-ahead bias

### 3. Agent Isolation

Agents **ONLY** read from feature snapshots, never raw tables:
- Prevents accidental look-ahead bias
- Enforces point-in-time correctness
- Makes backtesting identical to production

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
│  (Web App, iOS App - reads pre-computed recommendations)        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (READ-ONLY)                      │
│  FastAPI - No LLM calls, no agents, deterministic               │
│  Serves: Recommendations, Historical Data, Backtests            │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE (PostgreSQL)                       │
│  ┌───────────────┬───────────────┬──────────────────────────┐  │
│  │ Market Data   │ News/Sentiment│ Feature Store (Append-Only)│
│  ├───────────────┼───────────────┼──────────────────────────┤  │
│  │ Agent Outputs │ Recommendations│ Execution Logs          │  │
│  └───────────────┴───────────────┴──────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▲
┌─────────────────┴───────────────────────────────────────────────┐
│                    OFFLINE PIPELINES (Scheduled)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Market Data Service  → Fetch prices, calc indicators  │  │
│  │  2. News Sentiment Service → Fetch news, analyze sentiment│  │
│  │  3. Feature Store Service → Create point-in-time snapshots│  │
│  │  4. Agent Orchestrator → LangGraph agents reason offline  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Daily Pipeline (Runs Offline)

```
08:00 AM → Market Data Service fetches OHLCV from Polygon.io
        → Calculate technical indicators (RSI, MACD, etc.)
        → Write to market_data schema (APPEND-ONLY)

09:00 AM → News Sentiment Service fetches news from NewsAPI/Finnhub
        → Analyze sentiment with OpenAI
        → Write to news schema (APPEND-ONLY)

10:00 AM → Feature Store Service reads market data + news
        → Create immutable feature snapshots
        → Write to features schema (APPEND-ONLY)

11:00 AM → Agent Orchestrator (LangGraph) launches 4 agents:
        │
        ├─ Technical Agent → Reads feature snapshot
        │                  → Analyzes chart patterns, indicators
        │                  → Outputs: BULLISH/NEUTRAL/BEARISH signal
        │
        ├─ Sentiment Agent → Reads feature snapshot
        │                  → Analyzes news themes
        │                  → Outputs: POSITIVE/NEUTRAL/NEGATIVE signal
        │
        ├─ Risk Agent → Reads feature snapshot
        │              → Evaluates volatility, drawdown risk
        │              → Outputs: LOW/MEDIUM/HIGH risk level
        │
        └─ Synthesizer Agent → Combines all agent outputs
                             → Generates final recommendation
                             → Write to agents.stock_recommendations

12:00 PM → Pipeline complete
        → Recommendations available for API consumption
```

### User Request (Real-time, < 100ms)

```
User → API → PostgreSQL → Return pre-computed recommendation
(NO AI/LLM involved in request path)
```

---

## Service Responsibilities

### Market Data Service
- **Input**: Polygon.io API
- **Processing**: OHLCV fetching, technical indicator calculation
- **Output**: Deterministic, reproducible market data
- **Key Rule**: Pure math, no AI

### News Sentiment Service
- **Input**: NewsAPI, Finnhub
- **Processing**: News fetching, sentiment analysis (OpenAI)
- **Output**: Sentiment scores + themes
- **Key Rule**: Store raw headlines for explainability

### Feature Store Service
- **Input**: Market data + news sentiment
- **Processing**: Point-in-time snapshot creation
- **Output**: Immutable feature snapshots
- **Key Rule**: Append-only, never updated

### Agent Orchestrator (LangGraph)
- **Input**: Feature snapshots
- **Processing**: Multi-agent reasoning (technical, sentiment, risk)
- **Output**: Structured recommendations
- **Key Rule**: Runs offline only, never in API requests

### FastAPI Backend
- **Input**: User HTTP requests
- **Processing**: Database queries only
- **Output**: Pre-computed recommendations
- **Key Rule**: Read-only, deterministic, cacheable

---

## Database Schema Principles

### Schema Separation

```
market_data.*     → OHLCV prices, technical indicators
news.*            → News articles, sentiment scores
features.*        → Feature snapshots (append-only)
agents.*          → Agent outputs, recommendations
users.*           → User accounts, portfolios, trades
```

### Immutability Enforcement

Every table has:
- `created_at` timestamp (when record was created)
- **NO** `updated_at` (because records are never updated)
- Unique indexes on (ticker, date) to prevent duplicates

### Point-in-Time Correctness

```sql
-- Feature snapshot example
SELECT * FROM features.feature_snapshots
WHERE ticker = 'AAPL'
  AND as_of_date = '2024-03-15';
-- Returns EXACTLY what was known on 2024-03-15
-- No look-ahead bias possible
```

---

## Why This Architecture Works

### ✅ Low Latency
- API only reads database (no LLM calls)
- Responses < 100ms
- Highly cacheable

### ✅ Cost Efficient
- AI processing once per day per stock
- No wasted API calls on duplicate requests
- Predictable monthly costs

### ✅ Explainable
- Every recommendation traces to:
  - Feature snapshot ID
  - Agent outputs
  - Source news articles
  - Model version
  - Prompt hash

### ✅ Backtestable
- Same pipeline runs on historical dates
- Point-in-time snapshots guarantee accuracy
- No look-ahead bias

### ✅ Scalable
- Offline processing scales independently
- API scales independently
- Can process 1,000s of stocks without impacting users

### ✅ Auditable
- Immutable records
- Full lineage tracking
- Regulatory compliance ready

---

## Technology Stack

**Backend**
- FastAPI (Python) - High performance async API
- PostgreSQL - Transactional consistency
- Redis - Response caching
- SQLAlchemy - ORM with type safety

**Data Processing**
- Polygon.io - Market data
- NewsAPI/Finnhub - News sources
- Pandas/Polars - Data manipulation
- TA-Lib - Technical indicators

**AI/Agents**
- OpenAI GPT-4 - Reasoning engine
- LangGraph - Agent orchestration
- Pydantic - Structured outputs

**Infrastructure**
- Docker - Local development
- Alembic - Database migrations
- Pytest - Testing

---

## Key Files Reference

- `/api/app/models/features.py` - Append-only feature store model
- `/api/app/models/agents.py` - Agent output models
- `/api/app/routes/recommendations.py` - Read-only API end points
- `/services/market-data/` - Deterministic data pipeline
- `/services/agent-orchestrator/` - LangGraph agent logic (Phase 3)

---

## Next Steps (Phase 2+)

1. **News Sentiment Service** (Week 3-4)
2. **Feature Store Implementation** (Week 4)
3. **Agent Orchestrator with LangGraph** (Week 5-6)
4. **Web Frontend** (Week 7-8)
5. **Production Deployment** (Week 9+)
