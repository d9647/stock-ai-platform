# Stock AI Platform - Replit Configuration

## Overview

This is a production-grade educational stock trading simulator with AI-powered recommendations. Students compete against an AI opponent in a turn-based game to learn portfolio decision-making using real historical market data. The platform uses a microservices architecture with 4 backend services (market-data, news-sentiment, feature-store, agent-orchestrator), a FastAPI backend, and a Next.js frontend.

**Core Design Principle**: "If it can 'think', it cannot block a request. If it serves a request, it must not think." All AI processing happens offline, and the API serves only pre-computed recommendations.

## Replit Environment Setup

### Running the Application
- **Backend API**: FastAPI on port 5000 (exposed to web)
- **Database**: PostgreSQL via Replit's built-in database (DATABASE_URL)

### Workflows
1. **API Server** - `cd api && python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload` (webview)

### Database Schemas
The application uses 5 PostgreSQL schemas: `agents`, `features`, `market_data`, `multiplayer`, `news`

### Running Migrations
```bash
cd api && python -m alembic upgrade head
```

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Services

1. **FastAPI API** (`/api`) - Read-only REST API serving pre-computed recommendations
   - No LLM calls in request handlers
   - All responses are cacheable and deterministic
   - PostgreSQL database with SQLAlchemy ORM
   - Alembic for database migrations

2. **Market Data Service** (`/services/market-data`) - Fetches OHLCV prices from Polygon.io and calculates 15 technical indicators (RSI, MACD, Bollinger Bands, etc.)

3. **News Sentiment Service** (`/services/news-sentiment`) - Ingests financial news from Finnhub/NewsAPI and generates sentiment scores using OpenAI GPT-4o-mini

4. **Feature Store Service** (`/services/feature-store`) - Creates point-in-time feature snapshots combining technical and sentiment data (append-only, immutable)

5. **Agent Orchestrator** (`/services/agent-orchestrator`) - LangGraph-based multi-agent system with 4 agents (Technical, Sentiment, Risk, Portfolio Synthesizer) that generates stock recommendations offline

### Frontend

- **Next.js 14** with App Router (`/web`)
- **TypeScript** for type safety
- **Tailwind CSS** with custom dark theme (OpenAI-inspired)
- **TanStack Query** for data fetching
- **Zustand** for state management with localStorage persistence
- **Recharts** for stock charts

### Database Design

- **PostgreSQL** with 5 schemas: `market_data`, `news`, `features`, `agents`, `multiplayer`
- **13 tables** total (11 main + 2 multiplayer)
- **Append-only architecture** - No UPDATE or DELETE on historical records
- All data is immutable for point-in-time correctness and backtesting accuracy

### Key Architectural Decisions

1. **Offline AI Processing**: Agents never run during API requests. Recommendations are pre-computed and stored in the database.

2. **Feature Snapshots**: Agents only read from versioned feature snapshots, never raw tables. This prevents look-ahead bias and ensures reproducibility.

3. **Turn-Based Gameplay**: Students control time progression, advancing one market day at a time without time pressure.

4. **Multiplayer Support**: Teachers can create game rooms; students join with room codes and compete on the same dataset with live leaderboards.

## External Dependencies

### APIs & Services
- **Polygon.io** - Historical stock price data (OHLCV)
- **Finnhub** - Financial news (primary source, 60 calls/minute free tier)
- **NewsAPI** - Financial news (backup source, 100 calls/day free tier)
- **OpenAI API** - GPT-4o-mini for sentiment analysis and agent reasoning

### Database
- **PostgreSQL 16** - Primary database (use Replit's DATABASE_URL environment variable)
- **Redis 7** - Optional caching layer

### Key Python Packages
- FastAPI, SQLAlchemy, Alembic, Pydantic
- LangGraph, LangChain, OpenAI SDK
- Pandas, NumPy for data processing

### Key Node Packages
- Next.js 14, React 18
- TanStack Query, Zustand
- Tailwind CSS, Recharts