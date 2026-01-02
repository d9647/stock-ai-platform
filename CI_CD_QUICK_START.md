# CI/CD Quick Start Guide

**Get automated API testing running in 5 minutes**

---

## 🚀 Option 1: GitHub Actions (Cloud)

### Setup (One-Time)

```bash
# 1. Ensure workflows are committed
git add .github/workflows/
git commit -m "Add CI/CD workflows"
git push origin main

# 2. Done! GitHub Actions runs automatically on push/PR
```

### View Results

1. Go to GitHub repository
2. Click **Actions** tab
3. See workflow runs and download reports

**That's it!** Tests run automatically on every push.

---

## 💻 Option 2: Local Testing with Newman

### Setup (One-Time)

```bash
# Install Newman
npm install -g newman
npm install -g newman-reporter-htmlextra
```

### Run Tests Locally

```bash
# 1. Start API server (Terminal 1)
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 2. Run Newman tests (Terminal 2)
./scripts/run-newman-tests.sh

# 3. View HTML report
open reports/newman-report-*.html
```

---

## 📊 What Gets Tested

**Automatically on every push:**
- ✅ 75 pytest tests (game logic, trade rules, API contracts)
- ✅ 24 Postman/Newman tests (API endpoints)
- ✅ HTML reports generated
- ✅ PR comments with results

---

## 🎯 Quick Commands

### Local Testing
```bash
# Run pytest only
cd api && pytest tests/ -v

# Run Newman only
./scripts/run-newman-tests.sh

# Run both
cd api && pytest tests/ -v && cd .. && ./scripts/run-newman-tests.sh
```

### Trigger CI/CD
```bash
# Push to main (runs full test suite)
git push origin main

# Create PR (runs tests + adds comment)
git checkout -b feature-branch
git push origin feature-branch
# Create PR on GitHub

# Manual trigger
# Go to GitHub → Actions → Run workflow
```

---

## �� Files Created

```
.github/workflows/
├── api-tests.yml          # Combined pytest + Newman
└── postman-tests.yml      # Postman/Newman only (with PR comments)

scripts/
└── run-newman-tests.sh    # Local Newman testing

docs/
└── CI_CD_SETUP_GUIDE.md   # Complete documentation
```

---

## ✅ Verify Setup

**Check 1: Workflows exist**
```bash
ls -la .github/workflows/
# Should see: api-tests.yml, postman-tests.yml
```

**Check 2: Newman installed**
```bash
newman --version
# Should show version number
```

**Check 3: GitHub Actions enabled**
- Go to GitHub repo → Actions tab
- Should see workflows listed

---

## 🐛 Troubleshooting

### "Newman not found"
```bash
npm install -g newman newman-reporter-htmlextra
```

### "API server not running"
```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### GitHub Actions failing
1. Check workflow logs in Actions tab
2. Ensure PostgreSQL service starts
3. Verify API server health check passes

---

## 📖 Full Documentation

- [CI/CD Setup Guide](docs/CI_CD_SETUP_GUIDE.md) - Complete workflow documentation
- [Postman Testing Guide](docs/POSTMAN_TESTING_GUIDE.md) - Postman collection usage
- [Testing Complete Guide](docs/TESTING_COMPLETE_GUIDE.md) - All testing info

---

## 🎉 You're Done!

Your API now has:
- ✅ Automated testing on every push
- ✅ Test reports on every PR
- ✅ Local testing capability
- ✅ 99 total tests covering all endpoints

**Next**: Create a PR and watch tests run automatically!
