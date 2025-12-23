.PHONY: help setup start stop clean test fetch-data api logs db-migrate

help:
	@echo "Stock AI Platform - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Initial setup (run once)"
	@echo "  make install-api    - Install API dependencies"
	@echo "  make install-market - Install market data service dependencies"
	@echo ""
	@echo "Running Services:"
	@echo "  make start          - Start all infrastructure (Docker)"
	@echo "  make api            - Run API server"
	@echo "  make fetch-data     - Fetch market data for default tickers"
	@echo ""
	@echo "Development:"
	@echo "  make logs           - View Docker logs"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make redis-shell    - Open Redis shell"
	@echo "  make db-migrate     - Run database migrations"
	@echo ""
	@echo "Maintenance:"
	@echo "  make stop           - Stop all services"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make test           - Run all tests"

setup:
	@echo "Running setup script..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

start:
	@echo "Starting infrastructure..."
	docker-compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 10
	@echo "✓ Infrastructure started"
	@echo ""
	@echo "Services running:"
	@echo "  PostgreSQL: 192.168.5.126:5432"
	@echo "  Redis: 192.168.5.126:6379"
	@echo "  pgAdmin: http://192.168.5.126:5050"

stop:
	@echo "Stopping services..."
	docker-compose down
	@echo "✓ Services stopped"

clean:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf api/venv services/*/venv; \
		echo "✓ Cleaned up"; \
	fi

install-api:
	@echo "Installing API dependencies..."
	cd api && python3 -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt
	@echo "✓ API dependencies installed"

install-market:
	@echo "Installing market data service dependencies..."
	cd services/market-data && python3 -m venv venv && \
	. venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt
	@echo "✓ Market data dependencies installed"

api:
	@echo "Starting API server..."
	@echo "API will be available at http://192.168.5.126:8000"
	@echo "Docs available at http://192.168.5.126:8000/docs"
	@echo ""
	cd api && . venv/bin/activate && python -m app.main

fetch-data:
	@echo "Fetching market data..."
	cd services/market-data && \
	. venv/bin/activate && \
	python -m src.pipelines.daily_market_pipeline

fetch-ticker:
	@read -p "Enter ticker symbol: " ticker; \
	read -p "Enter days (default 365): " days; \
	days=$${days:-365}; \
	echo "Fetching $$ticker for $$days days..."; \
	cd services/market-data && \
	. venv/bin/activate && \
	python -m src.pipelines.daily_market_pipeline --ticker $$ticker --days $$days

logs:
	docker-compose logs -f

logs-postgres:
	docker-compose logs -f postgres

logs-redis:
	docker-compose logs -f redis

db-shell:
	docker exec -it stockai-postgres psql -U stockai -d stockai_dev

redis-shell:
	docker exec -it stockai-redis redis-cli

db-migrate:
	@echo "Running database migrations..."
	cd api && . venv/bin/activate && alembic upgrade head
	@echo "✓ Migrations complete"

db-migrate-create:
	@read -p "Enter migration description: " desc; \
	cd api && . venv/bin/activate && \
	alembic revision --autogenerate -m "$$desc"

test:
	@echo "Running tests..."
	cd api && . venv/bin/activate && pytest
	cd services/market-data && . venv/bin/activate && pytest

test-api:
	cd api && . venv/bin/activate && pytest -v

test-coverage:
	cd api && . venv/bin/activate && pytest --cov=app --cov-report=html
	@echo "Coverage report: api/htmlcov/index.html"

format:
	@echo "Formatting code..."
	cd api && . venv/bin/activate && black app/
	cd services/market-data && . venv/bin/activate && black src/

lint:
	@echo "Linting code..."
	cd api && . venv/bin/activate && ruff app/
	cd services/market-data && . venv/bin/activate && ruff src/

status:
	@echo "=== Docker Services ==="
	@docker-compose ps
	@echo ""
	@echo "=== Database Status ==="
	@docker exec stockai-postgres pg_isready -U stockai -d stockai_dev || echo "PostgreSQL not ready"
	@echo ""
	@echo "=== Redis Status ==="
	@docker exec stockai-redis redis-cli ping || echo "Redis not ready"

dev:
	@echo "Starting development environment..."
	@make start
	@echo ""
	@echo "Run these in separate terminals:"
	@echo "  Terminal 1: make api"
	@echo "  Terminal 2: make logs"
	@echo ""
	@echo "Useful commands:"
	@echo "  make fetch-data     - Fetch market data"
	@echo "  make db-shell       - Access database"
	@echo "  make test          - Run tests"
