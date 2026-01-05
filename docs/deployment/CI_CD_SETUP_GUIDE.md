# CI/CD Setup Guide - GitHub Actions + Postman/Newman

**Stock AI Platform - Automated Testing Pipeline**

This guide shows you how to set up automated API testing using GitHub Actions and Newman (Postman CLI).

---

## 🎯 What You Get

### Automated Testing on Every Push/PR

✅ **pytest tests** - 75 unit/integration tests
✅ **Newman/Postman tests** - 24 API endpoint tests
✅ **HTML test reports** - Downloadable artifacts
✅ **PR comments** - Automatic test results in pull requests
✅ **Test isolation** - Each run uses fresh database

---

## 📁 Files Created

### GitHub Actions Workflows

1. **[.github/workflows/api-tests.yml](.github/workflows/api-tests.yml)**
   - Combined pytest + Newman workflow
   - Runs on push to main/develop
   - Full test suite

2. **[.github/workflows/postman-tests.yml](.github/workflows/postman-tests.yml)**
   - Dedicated Postman/Newman workflow
   - Automatic PR comments with results
   - HTML report generation

---

## 🚀 Quick Setup

### Step 1: Ensure Workflows Are Committed

```bash
# Check workflows exist
ls -la .github/workflows/

# Should see:
# api-tests.yml
# postman-tests.yml

# Commit if needed
git add .github/workflows/
git commit -m "Add CI/CD workflows for API testing"
git push origin main
```

### Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. You should see workflows appear automatically

### Step 3: Trigger Your First Run

**Option A - Push to main/develop:**
```bash
git push origin main
```

**Option B - Create a pull request:**
```bash
git checkout -b test-api-changes
git push origin test-api-changes
# Create PR on GitHub
```

**Option C - Manual trigger:**
1. Go to **Actions** tab
2. Select **Postman API Tests**
3. Click **Run workflow**
4. Select branch and click **Run workflow**

---

## 📊 Workflow Overview

### Workflow 1: Combined API Tests (`api-tests.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**

```
1. pytest-tests (runs first)
   ├─ Set up Python 3.9
   ├─ Install dependencies
   ├─ Start PostgreSQL
   └─ Run 75 pytest tests

2. postman-tests (runs if pytest passes)
   ├─ Set up Python + Node.js
   ├─ Install Newman
   ├─ Start API server
   ├─ Run 24 Postman tests
   └─ Upload HTML report

3. test-summary
   └─ Show overall results
```

**Estimated Duration**: ~3-5 minutes

### Workflow 2: Postman-Only Tests (`postman-tests.yml`)

**Triggers:**
- Push to `main`/`develop` (only if API files changed)
- Pull requests
- Manual trigger (workflow_dispatch)

**Jobs:**

```
1. newman-tests
   ├─ Start PostgreSQL service
   ├─ Set up Python + Node.js
   ├─ Install Newman + reporters
   ├─ Start API server (wait for health check)
   ├─ Run Postman collection
   ├─ Generate HTML + JSON reports
   ├─ Comment on PR with results
   └─ Upload artifacts
```

**Estimated Duration**: ~2-3 minutes

---

## 📋 What Gets Tested

### pytest Tests (75 tests)
- ✅ Phase 0: Architecture verification (13 tests)
- ✅ Game engine invariants (16 tests)
- ✅ Trade rules validation (28 tests)
- ✅ API contract schemas (24 tests)

### Postman/Newman Tests (24 requests)
- ✅ Health & info endpoints (2)
- ✅ Game data endpoints (4)
- ✅ Room management (7)
- ✅ Player actions (4)
- ✅ Leaderboards (2)
- ✅ News & recommendations (2)
- ✅ Error handling (3)

---

## 🎨 Viewing Test Results

### 1. In GitHub Actions Tab

**See workflow runs:**
```
GitHub Repo → Actions → Select workflow run
```

**View logs:**
- Click on a workflow run
- Expand job steps to see detailed logs
- Green ✅ = passed, Red ❌ = failed

### 2. Download HTML Reports

**For Postman tests:**
1. Go to workflow run
2. Scroll to **Artifacts** section
3. Download `newman-report-html`
4. Open `newman-report.html` in browser

**Report includes:**
- ✅ Pass/fail status for each request
- 📊 Statistics (requests, assertions, duration)
- 🐛 Detailed failure messages
- 📈 Response time charts

### 3. PR Comments (Automatic)

When you create a pull request, the workflow automatically comments with:

```markdown
## 🧪 Postman API Test Results

**Run**: #42
**Status**: ✅ PASSED

### Statistics
- **Requests**: 24 (0 failed)
- **Assertions**: 58 (58 passed, 0 failed)
- **Pass Rate**: 100.0%
- **Duration**: 0.45s avg

[View Full Report](link)
```

---

## 🔧 Configuration

### Environment Variables

The workflows use these environment variables:

```yaml
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/stockai_dev
APP_NAME: Stock AI Platform
APP_VERSION: 1.0.0
ENVIRONMENT: test
API_PORT: 8000
```

### Customizing Test Triggers

**Run on specific paths only:**
```yaml
on:
  push:
    paths:
      - 'api/**'              # Only API changes
      - '**.postman_collection.json'  # Collection changes
```

**Run on schedule (nightly):**
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Every day at 2 AM UTC
```

**Skip CI for certain commits:**
```bash
git commit -m "Update docs [skip ci]"
```

### Newman Options

**Customize in workflow file:**

```yaml
newman run Stock_AI_Platform_API.postman_collection.json \
  --timeout-request 15000 \      # 15 second timeout
  --delay-request 500 \          # 500ms delay between requests
  --bail \                       # Stop on first failure
  --color on                     # Colored output
```

---

## 🐛 Troubleshooting

### Issue: Tests failing in CI but passing locally

**Common causes:**
1. **Database not ready** - Increase health check retries
2. **Server not started** - Increase wait timeout
3. **Environment differences** - Check environment variables

**Solution**:
```yaml
# Increase wait time in workflow
for i in {1..60}; do  # Was {1..30}
  if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    break
  fi
  sleep 1
done
```

### Issue: Newman reports "connection refused"

**Cause**: API server not started or crashed

**Debug**:
```yaml
# Add step to show server logs
- name: Show server logs
  if: failure()
  run: cat api/server.log
```

### Issue: PostgreSQL connection errors

**Cause**: Database service not healthy

**Solution**:
```yaml
# Increase health check intervals
services:
  postgres:
    options: >-
      --health-interval 10s  # Was 5s
      --health-timeout 5s
      --health-retries 10    # Was 5
```

### Issue: Tests timeout

**Cause**: Slow network or heavy load

**Solution**:
```yaml
# Increase timeouts
newman run ... \
  --timeout-request 20000 \  # 20 seconds
  --timeout-script 10000     # 10 seconds for scripts
```

---

## 📈 Advanced Usage

### Running Specific Tests Only

**Create custom workflow:**

```yaml
# .github/workflows/smoke-tests.yml
name: Smoke Tests

on:
  push:
    branches: [ main ]

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Run health check only
        run: |
          newman run Stock_AI_Platform_API.postman_collection.json \
            --folder "Health & Info" \  # Run specific folder
            --env-var "base_url=${{ secrets.PROD_API_URL }}"
```

### Testing Against Production

**Use GitHub Secrets:**

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secret: `PROD_API_URL` = `https://your-api.com`
3. Use in workflow:

```yaml
- name: Test production API
  run: |
    newman run Stock_AI_Platform_API.postman_collection.json \
      --env-var "base_url=${{ secrets.PROD_API_URL }}" \
      --folder "Health & Info"  # Only non-destructive tests
```

### Parallel Test Execution

**Run tests in parallel:**

```yaml
jobs:
  test-game-data:
    # ... setup ...
    run: newman run collection.json --folder "Game Data"

  test-multiplayer:
    # ... setup ...
    run: newman run collection.json --folder "Multiplayer"

  test-errors:
    # ... setup ...
    run: newman run collection.json --folder "Error Cases"
```

### Slack/Discord Notifications

**Add notification step:**

```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'API tests failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 📊 Metrics & Monitoring

### Track Test Performance Over Time

**Newman JSON reports contain:**
- Total requests/assertions
- Pass/fail counts
- Response times (min/max/avg)
- Test duration

**Store in GitHub:**
```yaml
- name: Store test metrics
  run: |
    echo "$(jq '.run.stats' reports/newman-report.json)" >> metrics.json
    git add metrics.json
    git commit -m "Update test metrics [skip ci]"
```

### Badge for README

**Add status badge to README.md:**

```markdown
![API Tests](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/postman-tests.yml/badge.svg)
```

Shows:
- ✅ Passing - Green badge
- ❌ Failing - Red badge

---

## 🔐 Security Best Practices

### 1. Use Secrets for Sensitive Data

**Never commit:**
- API keys
- Database passwords (except test passwords)
- Production URLs

**Use GitHub Secrets instead:**
```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  API_KEY: ${{ secrets.API_KEY }}
```

### 2. Limit Permissions

**Add to workflow:**
```yaml
permissions:
  contents: read       # Read repo code
  pull-requests: write # Comment on PRs
  actions: read        # Read workflow status
```

### 3. Don't Test Production Destructively

**Safe for production:**
- ✅ Health checks
- ✅ GET requests
- ✅ Read-only endpoints

**Unsafe for production:**
- ❌ POST/PUT/DELETE
- ❌ Data mutations
- ❌ Room creation

---

## 📝 Workflow YAML Reference

### Trigger Events

```yaml
on:
  push:                # On push to branch
  pull_request:        # On PR creation/update
  workflow_dispatch:   # Manual trigger
  schedule:            # Cron schedule
    - cron: '0 2 * * *'
```

### Job Dependencies

```yaml
jobs:
  test-backend:
    # ...

  test-api:
    needs: test-backend  # Wait for backend tests
    # ...
```

### Conditional Execution

```yaml
steps:
  - name: Only on main
    if: github.ref == 'refs/heads/main'
    run: echo "Main branch!"

  - name: Only on failure
    if: failure()
    run: cat logs.txt

  - name: Always run
    if: always()
    run: cleanup.sh
```

---

## 🚀 Next Steps

### After Setup

1. **Monitor first few runs** - Check for issues
2. **Adjust timeouts** - Based on your API performance
3. **Add more tests** - Expand Postman collection
4. **Set up notifications** - Slack/Discord/Email
5. **Create badges** - Show status in README

### Expanding Tests

**Add to Postman collection:**
- Performance tests (response time checks)
- Data validation tests
- Authentication tests (when implemented)
- Edge case scenarios

**Update workflows:**
- Add staging environment tests
- Add database migration tests
- Add load testing (with k6 or artillery)

---

## 📚 Resources

**GitHub Actions:**
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

**Newman:**
- [Newman CLI Docs](https://learning.postman.com/docs/running-collections/using-newman-cli/command-line-integration-with-newman/)
- [Newman Reporters](https://www.npmjs.com/package/newman-reporter-htmlextra)

**Related Docs:**
- [POSTMAN_TESTING_GUIDE.md](POSTMAN_TESTING_GUIDE.md)
- [TESTING_COMPLETE_GUIDE.md](TESTING_COMPLETE_GUIDE.md)

---

## ✅ Checklist

Setup complete when:

- [ ] Workflows committed to `.github/workflows/`
- [ ] First workflow run successful
- [ ] HTML reports downloadable
- [ ] PR comments working
- [ ] All tests passing
- [ ] Team notified of setup

---

**Last Updated**: 2025-12-29
**Workflow Version**: 1.0
**Status**: ✅ Ready for production use
