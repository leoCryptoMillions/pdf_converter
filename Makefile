.PHONY: help install install-dev run test test-coverage lint format type-check clean docker-up docker-down db-migrate db-seed

PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose

help:
	@echo "PDF Converter - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run              Run FastAPI development server"
	@echo "  make run-worker       Run Celery worker"
	@echo "  make run-beat         Run Celery beat scheduler"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-e2e         Run E2E tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (flake8, pylint)"
	@echo "  make format           Format code (black, isort)"
	@echo "  make type-check       Type checking with mypy"
	@echo "  make quality          Run all quality checks"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate       Run database migrations"
	@echo "  make db-seed          Seed database with test data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Start Docker containers"
	@echo "  make docker-down      Stop Docker containers"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove generated files and cache"
	@echo "  make clean-pyc        Remove Python cache files"
	@echo "  make clean-test       Remove test cache and coverage"
	@echo ""

## Setup
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

## Development
run:
	cd apps/api && $(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	cd apps/worker && celery -A tasks worker --loglevel=info --concurrency=2

run-beat:
	cd apps/worker && celery -A tasks beat --loglevel=info

run-all: docker-up
	@echo "All services started with Docker Compose"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "RabbitMQ Management: http://localhost:15672 (guest:guest)"

## Testing
test:
	pytest tests/ -v --tb=short

test-coverage:
	pytest tests/ --cov=apps --cov=packages --cov-report=html --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-watch:
	pytest-watch tests/ -v

## Code Quality
lint:
	flake8 apps/ packages/ tests/
	pylint apps/ packages/ --disable=all --enable=E,F

format:
	black apps/ packages/ tests/
	isort apps/ packages/ tests/

type-check:
	mypy apps/ packages/

quality: format lint type-check

## Database
db-migrate:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-migration:
	alembic revision --autogenerate -m "$(MESSAGE)"

db-seed:
	$(PYTHON) scripts/seed_database.py

## Docker
docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f

docker-logs-api:
	$(DOCKER_COMPOSE) logs -f api

docker-logs-worker:
	$(DOCKER_COMPOSE) logs -f worker

docker-rebuild:
	$(DOCKER_COMPOSE) build --no-cache

docker-clean:
	$(DOCKER_COMPOSE) down -v

## Cleanup
clean: clean-pyc clean-test clean-build

clean-pyc:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '.coverage' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true

clean-test:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

## Benchmark
benchmark:
	$(PYTHON) benchmarks/runner.py

benchmark-tables:
	$(PYTHON) benchmarks/tables_benchmark.py

benchmark-ocr:
	$(PYTHON) benchmarks/ocr_benchmark.py

## Documentation
docs-openapi:
	$(PYTHON) -c "from apps.api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json

docs-build:
	@echo "Building documentation..."
	@echo "OpenAPI schema generated to openapi.json"

## Development Environment
setup-dev: install-dev clean
	@echo "Development environment ready!"
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Update .env with your configuration"
	@echo "  3. Run: make docker-up (or individual make run, make run-worker)"
	@echo "  4. Run: make test to verify setup"
