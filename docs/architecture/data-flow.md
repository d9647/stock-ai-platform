# Data Flow Architecture

## Overview

This document explains how data flows through the Stock AI Platform, emphasizing the **separation between offline processing and online serving**.

---

## The Golden Rule

```
╔═══════════════════════════════════════════════════════════╗
║  If it can "think", it cannot block a request.            ║
║  If it serves a request, it must not think.               ║
╚═══════════════════════════════════════════════════════════╝
```

---

## System Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  (Web App, Mobile App - Phase 4)                                │
│  - Reads pre-computed data only                                 │
│  - No AI processing here                                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP GET
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (READ-ONLY)                      │
│  FastAPI Backend - Phase 1 ✅                                   │
│  - NO LLM calls                                                 │
│  - NO agent execution                                           │
│  - Deterministic database queries only                          │
│  - Response time: <100ms                                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SQL SELECT
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA LAYER (PostgreSQL)                       │
│  ┌──────────────┬──────────────┬───────────────┬─────────────┐ │
│  │ Market Data  │ News/Sentiment│ Feature Store │ Recommendations│
│  │  (Phase 1)   │   (Phase 2)   │   (Phase 2)   │   (Phase 3)  │ │
│  └──────────────┴──────────────┴───────────────┴─────────────┘ │
│  All tables are APPEND-ONLY (immutable)                         │
└──────────────────────────────┬──────────────────────────────────┘
                               ▲ SQL INSERT (only)
                               │
┌──────────────────────────────┴──────────────────────────────────┐
│              PROCESSING LAYER (Offline, Scheduled)              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Pipeline 1: Market Data (Phase 1 ✅)                       │ │
│  │ Pipeline 2: News Sentiment (Phase 2)                       │ │
│  │ Pipeline 3: Feature Store (Phase 2)                        │ │
│  │ Pipeline 4: Agent Orchestrator (Phase 3)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│  - Runs on schedule (daily, hourly)                             │
│  - This is where AI/LLM calls happen                            │
│  - Never in user request path                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Data Flow

### Phase 1: Market Data (Complete ✅)

```
┌─────────────┐
│ Polygon.io  │ External API
└──────┬──────┘
       │ HTTPS GET
       ▼
┌───────────────────────────────────────────────┐
│  Market Data Service                          │
│  ┌─────────────────────────────────────────┐ │
│  │ 1. fetch_prices.py                      │ │
│  │    - Fetch OHLCV data                   │ │
│  │    - Handle rate limiting (5 req/min)   │ │
│  └─────────────────┬───────────────────────┘ │
│                    │ DataFrame                │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 2. technical_indicators.py              │ │
│  │    - RSI (14-day)                       │ │
│  │    - MACD (12, 26, 9)                   │ │
│  │    - Bollinger Bands (20-day)           │ │
│  │    - SMA (20, 50, 200)                  │ │
│  │    - Volatility (30-day)                │ │
│  └─────────────────┬───────────────────────┘ │
│                    │ DataFrame + Indicators   │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 3. db_writer.py                         │ │
│  │    - Write OHLCV (APPEND-ONLY)          │ │
│  │    - Write indicators (APPEND-ONLY)     │ │
│  │    - ON CONFLICT DO NOTHING             │ │
│  └─────────────────┬───────────────────────┘ │
└────────────────────┼───────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL (market_data schema)            │
│  ┌─────────────────────────────────────────┐│
│  │ ohlcv_prices                            ││
│  │ ├─ ticker, date, open, high, low, close││
│  │ └─ created_at (NO updated_at!)          ││
│  └─────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────┐│
│  │ technical_indicators                    ││
│  │ ├─ ticker, date, rsi_14, macd, sma_50  ││
│  │ └─ created_at (NO updated_at!)          ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### Phase 2: News & Sentiment (Coming Next)

```
┌─────────────┐  ┌─────────────┐
│  NewsAPI    │  │  Finnhub    │ External APIs
└──────┬──────┘  └──────┬──────┘
       │                │
       └────────┬───────┘ HTTPS GET
                ▼
┌───────────────────────────────────────────────┐
│  News Sentiment Service                       │
│  ┌─────────────────────────────────────────┐ │
│  │ 1. fetch_news.py                        │ │
│  │    - Fetch articles by ticker + date    │ │
│  │    - Deduplicate                        │ │
│  └─────────────────┬───────────────────────┘ │
│                    │ Raw articles             │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 2. sentiment_scoring.py                 │ │
│  │    - OpenAI GPT-4 sentiment analysis    │ │
│  │    - Score: -1 (negative) to +1 (pos)   │ │
│  │    - Extract themes                     │ │
│  └─────────────────┬───────────────────────┘ │
│                    │ Sentiment scores         │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 3. daily_aggregator.py                  │ │
│  │    - Aggregate by ticker + date         │ │
│  │    - Weighted by confidence             │ │
│  └─────────────────┬───────────────────────┘ │
└────────────────────┼───────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL (news schema)                   │
│  ┌─────────────────────────────────────────┐│
│  │ news_articles                           ││
│  │ ├─ ticker, headline, content, source    ││
│  │ └─ published_at, created_at             ││
│  └─────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────┐│
│  │ news_sentiment_scores                   ││
│  │ ├─ article_id, sentiment_score          ││
│  │ └─ confidence, themes, model_version    ││
│  └─────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────┐│
│  │ daily_sentiment_aggregates              ││
│  │ ├─ ticker, date, avg_sentiment          ││
│  │ └─ top_themes, article_count            ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### Phase 2: Feature Store (Critical!)

```
┌─────────────┐  ┌─────────────┐
│ Market Data │  │ News/Sentiment│ From PostgreSQL
└──────┬──────┘  └──────┬──────┘
       │                │
       └────────┬───────┘ SQL SELECT
                ▼
┌───────────────────────────────────────────────┐
│  Feature Store Service                        │
│  ┌─────────────────────────────────────────┐ │
│  │ 1. snapshot_creator.py                  │ │
│  │    - Read market data for ticker + date │ │
│  │    - Read news sentiment for date       │ │
│  │    - Create point-in-time snapshot      │ │
│  └─────────────────┬───────────────────────┘ │
│                    │                          │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 2. feature_validator.py                 │ │
│  │    - Check for missing values           │ │
│  │    - Validate ranges                    │ │
│  │    - Flag quality issues                │ │
│  └─────────────────┬───────────────────────┘ │
│                    │                          │
│  ┌─────────────────▼───────────────────────┐ │
│  │ 3. snapshot_writer.py                   │ │
│  │    - Generate snapshot_id (UUID)        │ │
│  │    - Store as JSONB                     │ │
│  │    - APPEND-ONLY (never updated!)       │ │
│  └─────────────────┬───────────────────────┘ │
└────────────────────┼───────────────────────────┘
                     ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL (features schema)               │
│  ┌─────────────────────────────────────────┐│
│  │ feature_snapshots                       ││
│  │ ├─ snapshot_id (UUID, unique)           ││
│  │ ├─ ticker, as_of_date                   ││
│  │ ├─ technical_features (JSONB)           ││
│  │ ├─ sentiment_features (JSONB)           ││
│  │ ├─ feature_version                      ││
│  │ └─ created_at (IMMUTABLE!)              ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘

Example snapshot:
{
  "snapshot_id": "abc-123-def-456",
  "ticker": "AAPL",
  "as_of_date": "2024-03-15",
  "technical_features": {
    "rsi_14": 62.4,
    "macd": 1.32,
    "sma_50": 187.2,
    "sma_200": 175.6
  },
  "sentiment_features": {
    "avg_sentiment": 0.42,
    "themes": ["earnings", "supply chain"],
    "article_count": 15
  },
  "feature_version": "1.0.0",
  "created_at": "2024-03-16T08:00:00Z"
}
```

### Phase 3: Agent Orchestrator (LangGraph)

```
┌─────────────────────────────┐
│  Feature Snapshots          │ From PostgreSQL
│  (features.feature_snapshots)│
└──────────────┬──────────────┘
               │ SQL SELECT (read-only)
               ▼
┌─────────────────────────────────────────────────────┐
│  Agent Orchestrator (LangGraph)                     │
│  ┌────────────────────────────────────────────────┐ │
│  │  Input: Feature Snapshot (AAPL, 2024-03-15)   │ │
│  └────────────────┬───────────────────────────────┘ │
│                   │                                  │
│     ┌─────────────┼─────────────┐                   │
│     │             │             │                   │
│     ▼             ▼             ▼                   │
│  ┌──────┐    ┌──────┐      ┌──────┐                │
│  │Tech  │    │Senti-│      │Risk  │ Parallel        │
│  │Agent │    │ment  │      │Agent │ Execution       │
│  │      │    │Agent │      │      │                 │
│  └───┬──┘    └───┬──┘      └───┬──┘                │
│      │           │             │                    │
│      │ BULLISH   │ POSITIVE    │ MEDIUM             │
│      │ 0.68      │ 0.55        │ RISK               │
│      │           │             │                    │
│      └───────────┼─────────────┘                    │
│                  ▼                                   │
│  ┌────────────────────────────────────────────────┐ │
│  │  Synthesizer Agent                             │ │
│  │  - Combines all agent outputs                  │ │
│  │  - Generates final recommendation              │ │
│  │  - Structured output (Pydantic)                │ │
│  └────────────────┬───────────────────────────────┘ │
└───────────────────┼─────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL (agents schema)                 │
│  ┌─────────────────────────────────────────┐│
│  │ stock_recommendations                   ││
│  │ ├─ recommendation_id (UUID)             ││
│  │ ├─ ticker, as_of_date                   ││
│  │ ├─ recommendation (BUY/HOLD/SELL)       ││
│  │ ├─ confidence (0.0 - 1.0)               ││
│  │ ├─ rationale (JSONB)                    ││
│  │ ├─ feature_snapshot_id (traceability)   ││
│  │ ├─ model_version                        ││
│  │ └─ created_at (IMMUTABLE!)              ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

---

## API Request Flow (Real-time, <100ms)

```
┌─────────────┐
│  User       │ Web/Mobile App
└──────┬──────┘
       │ HTTP GET /api/v1/recommendations/AAPL
       ▼
┌─────────────────────────────────────────────┐
│  FastAPI Backend                            │
│  ┌─────────────────────────────────────────┐│
│  │ recommendations.py                      ││
│  │                                         ││
│  │ @router.get("/{ticker}")                ││
│  │ def get_recommendation(ticker):         ││
│  │     # NO LLM calls!                     ││
│  │     # NO agent execution!               ││
│  │     # Just read from database           ││
│  │     rec = db.query(                     ││
│  │         StockRecommendation             ││
│  │     ).filter(                           ││
│  │         ticker == ticker                ││
│  │     ).first()                           ││
│  │     return rec                          ││
│  └─────────────────┬───────────────────────┘│
└────────────────────┼─────────────────────────┘
                     │ SQL SELECT
                     ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL                                 │
│  SELECT * FROM agents.stock_recommendations │
│  WHERE ticker = 'AAPL'                      │
│  ORDER BY as_of_date DESC                   │
│  LIMIT 1;                                   │
└─────────────────────┬───────────────────────┘
                     │ Pre-computed result
                     ▼
┌─────────────────────────────────────────────┐
│  Response (JSON)                            │
│  {                                          │
│    "ticker": "AAPL",                        │
│    "recommendation": "BUY",                 │
│    "confidence": 0.67,                      │
│    "rationale": {                           │
│      "technical": ["Golden cross"],         │
│      "sentiment": ["Positive earnings"],    │
│      "risk": ["Acceptable volatility"]      │
│    }                                        │
│  }                                          │
└─────────────────────┬───────────────────────┘
                     │
                     ▼
┌─────────────┐
│  User       │ Receives response in <100ms
└─────────────┘
```

**Key points:**
- ✅ No AI processing during request
- ✅ Deterministic database query
- ✅ Cacheable response
- ✅ Sub-100ms latency
- ✅ Predictable costs

---

## Scheduling (Offline Pipelines)

```
Daily Schedule (Example):

06:00 AM UTC
  └─> Market Data Pipeline
      - Fetch yesterday's OHLCV
      - Calculate indicators
      - Write to database
      Duration: ~10 minutes

07:00 AM UTC
  └─> News Sentiment Pipeline
      - Fetch yesterday's news
      - Analyze sentiment
      - Aggregate by ticker
      Duration: ~20 minutes

08:00 AM UTC
  └─> Feature Store Pipeline
      - Create point-in-time snapshots
      - Validate quality
      - Write to database
      Duration: ~5 minutes

09:00 AM UTC
  └─> Agent Orchestrator Pipeline
      - Load feature snapshots
      - Run LangGraph agents (4 agents × 100 stocks)
      - Generate recommendations
      - Write to database
      Duration: ~30 minutes

10:00 AM UTC
  └─> All pipelines complete!
      Recommendations available for API consumption
```

---

## Data Lineage & Traceability

Every recommendation can be fully traced:

```
stock_recommendations.recommendation_id
  │
  ├─> feature_snapshot_id
  │     └─> technical_features (from market_data)
  │     └─> sentiment_features (from news)
  │
  ├─> agent_outputs
  │     ├─> technical_agent.output_id
  │     ├─> sentiment_agent.output_id
  │     └─> risk_agent.output_id
  │
  ├─> model_version
  │
  └─> prompt_hash (SHA-256)
```

**Benefits:**
- ✅ Full audit trail
- ✅ Reproducible results
- ✅ Debugging capabilities
- ✅ Regulatory compliance

---

## Summary

### Data Flows IN (Offline)
1. **External APIs** → Services → **PostgreSQL** (APPEND-ONLY)
2. **LLM/Agents** → Services → **PostgreSQL** (APPEND-ONLY)

### Data Flows OUT (Online)
1. **User** → API → **PostgreSQL** (SELECT only) → **User**

### The Wall Between Them
```
       OFFLINE              │              ONLINE
    (Can "think")           │        (Cannot "think")
                            │
  ┌─────────────────┐      │      ┌─────────────────┐
  │ Agent Orchestrator│      │      │   FastAPI       │
  │ (LangGraph)      │      │      │   (Read-only)   │
  │                 │      │      │                 │
  │ - LLM calls OK  │      │      │ - NO LLM calls  │
  │ - Long latency OK│      │      │ - <100ms only   │
  │ - High cost OK  │      │      │ - Low cost      │
  └─────────────────┘      │      └─────────────────┘
                            │
                    PostgreSQL
                (Append-only writes │ Read-only queries)
```

**This separation is CRITICAL for production ML systems.**
