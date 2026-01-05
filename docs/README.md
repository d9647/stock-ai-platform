# Documentation Index

Welcome to the Stock AI Platform documentation.

## 🚀 Quick Start

**New to the project?** Start here:
1. [QUICKSTART.md](QUICKSTART.md) - Get up and running in 10 minutes
2. [guides/GETTING_STARTED.md](guides/GETTING_STARTED.md) - Detailed setup guide
3. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview

## 📚 Documentation Structure

```
docs/
├── README.md                          # This file
├── QUICKSTART.md                      # 10-minute quick start
├── PROJECT_SUMMARY.md                 # Project overview
├── TESTING_COMPLETE_GUIDE.md          # Complete testing guide
├── TROUBLESHOOTING.md                 # Common issues & solutions
│
├── guides/                            # User guides
│   ├── GETTING_STARTED.md             # Detailed setup
│   ├── GAME_IMPLEMENTATION.md         # Game mechanics
│   └── TESTING.md                     # Testing guide
│
├── api-testing/                       # API testing resources
│   ├── POSTMAN_QUICK_START.md         # Quick Postman setup
│   ├── POSTMAN_TESTING_GUIDE.md       # Complete Postman guide
│   └── Stock_AI_Platform_API.postman_collection.json  # Postman collection
│
├── deployment/                        # Deployment guides
│   ├── CI_CD_QUICK_START.md           # CI/CD quick setup
│   ├── CI_CD_SETUP_GUIDE.md           # Complete CI/CD guide
│   └── DEPLOYMENT.md                  # Deployment guide
│
├── architecture/                      # Architecture docs
│   ├── overview.md                    # System architecture
│   └── data-flow.md                   # Data flow diagrams
│
└── archive/                           # Old/deprecated docs
    └── testing-phases/                # Historical testing docs
```

## 📖 Documentation by Topic

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup (10 min)
- **[guides/GETTING_STARTED.md](guides/GETTING_STARTED.md)** - Complete setup guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - What this project does

### Testing
- **[TESTING_COMPLETE_GUIDE.md](TESTING_COMPLETE_GUIDE.md)** - Complete testing guide
- **[guides/TESTING.md](guides/TESTING.md)** - Testing overview
- **[api-testing/POSTMAN_QUICK_START.md](api-testing/POSTMAN_QUICK_START.md)** - Postman quick start
- **[api-testing/POSTMAN_TESTING_GUIDE.md](api-testing/POSTMAN_TESTING_GUIDE.md)** - Complete Postman guide
- **[api-testing/Stock_AI_Platform_API.postman_collection.json](api-testing/Stock_AI_Platform_API.postman_collection.json)** - Import into Postman

### Performance Testing
- **[../perf/README.md](../perf/README.md)** - Performance testing with K6
- **[../perf/docs/DASHBOARD.md](../perf/docs/DASHBOARD.md)** - Grafana dashboard guide
- **[../perf/docs/METRICS.md](../perf/docs/METRICS.md)** - Metrics reference

### Deployment & CI/CD
- **[deployment/CI_CD_QUICK_START.md](deployment/CI_CD_QUICK_START.md)** - CI/CD quick setup
- **[deployment/CI_CD_SETUP_GUIDE.md](deployment/CI_CD_SETUP_GUIDE.md)** - Complete CI/CD guide
- **[deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)** - Deployment instructions

### Architecture
- **[architecture/overview.md](architecture/overview.md)** - System architecture
- **[architecture/data-flow.md](architecture/data-flow.md)** - Data flow diagrams

### Game Implementation
- **[guides/GAME_IMPLEMENTATION.md](guides/GAME_IMPLEMENTATION.md)** - Game mechanics & multiplayer

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues & solutions

## 🎯 By Use Case

### I want to...

#### ...get started quickly
→ [QUICKSTART.md](QUICKSTART.md) (10 min)

#### ...test the API with Postman
→ [api-testing/POSTMAN_QUICK_START.md](api-testing/POSTMAN_QUICK_START.md)

#### ...run performance tests
→ [../perf/README.md](../perf/README.md)

#### ...deploy to production
→ [deployment/DEPLOYMENT.md](deployment/DEPLOYMENT.md)

#### ...set up CI/CD
→ [deployment/CI_CD_QUICK_START.md](deployment/CI_CD_QUICK_START.md)

#### ...understand the architecture
→ [architecture/overview.md](architecture/overview.md)

#### ...fix an issue
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

#### ...understand the game mechanics
→ [guides/GAME_IMPLEMENTATION.md](guides/GAME_IMPLEMENTATION.md)

## 📦 API Testing with Postman

### Import Collection

1. Open Postman
2. Click **Import**
3. Select **[api-testing/Stock_AI_Platform_API.postman_collection.json](api-testing/Stock_AI_Platform_API.postman_collection.json)**
4. See **[api-testing/POSTMAN_QUICK_START.md](api-testing/POSTMAN_QUICK_START.md)** for setup

### Collection Contents

The Postman collection includes:
- Health checks
- News API endpoints
- Recommendations API endpoints
- Game data endpoints
- Multiplayer endpoints (rooms, players, state)
- Complete authentication flows

## 🔧 Project Structure

```
stock-ai-platform/
├── README.md                          # Main project README
├── docs/                              # This directory
│   ├── guides/                        # User guides
│   ├── api-testing/                   # Postman collection & guides
│   ├── deployment/                    # Deployment guides
│   ├── architecture/                  # Architecture docs
│   └── archive/                       # Old docs
│
├── api/                               # FastAPI backend
│   ├── app/                           # Application code
│   ├── tests/                         # Backend tests
│   └── requirements.txt               # Python dependencies
│
├── perf/                              # Performance testing
│   ├── README.md                      # K6 testing guide
│   └── docs/                          # Performance docs
│
├── backtesting/                       # AI backtesting
│   └── notebooks/                     # Jupyter notebooks
│
└── infra/                             # Infrastructure
    ├── docker/                        # Docker configs
    └── scripts/                       # Utility scripts
```

## 🆘 Need Help?

1. Check **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for common issues
2. See **[QUICKSTART.md](QUICKSTART.md)** for setup help
3. Review relevant guide in **[guides/](guides/)** directory

## 📝 Contributing to Docs

When adding new documentation:
- **Quick starts** → Root `docs/` directory
- **Complete guides** → `docs/guides/`
- **API testing** → `docs/api-testing/`
- **Deployment** → `docs/deployment/`
- **Architecture** → `docs/architecture/`
- **Old/deprecated** → `docs/archive/`

Keep the main project README.md minimal and point to detailed docs here.
