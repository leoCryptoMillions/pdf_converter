# Developer Setup Guide

Complete instructions for setting up the PDF Converter development environment.

**Time to complete**: ~30 minutes  
**Difficulty**: Intermediate  
**Prerequisites**: Python 3.11+, Docker Desktop, Git

## Step 1: Clone and Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/pdf-converter.git
cd pdf-converter

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat

# Verify Python version
python --version
# Expected: Python 3.11.x or higher
```

## Step 2: Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks (optional but recommended)
pre-commit install

# Verify installation
pip list | grep fastapi
# Expected: fastapi==0.104.1
```

## Step 3: Environment Configuration

```bash
# Copy example configuration
cp .env.example .env

# Edit for local development (optional - defaults work for docker-compose)
# nano .env  # or your favorite editor
```

**Key environment variables** (defaults in .env.example are suitable for development):
- `DATABASE_URL`: PostgreSQL connection string
- `CELERY_BROKER_URL`: RabbitMQ broker URL
- `ENVIRONMENT`: Set to 'development'
- `DEBUG`: Set to 'true'
- `LOG_LEVEL`: Set to 'DEBUG' for verbose logging

## Step 4: Start Docker Services

```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, etc.)
docker-compose up -d

# Verify services are running
docker-compose ps
# Expected: All services showing "Up"

# Check health
docker-compose exec postgres pg_isready
# Expected: "accepting connections"

docker-compose exec redis redis-cli ping
# Expected: "PONG"
```

## Step 5: Initialize Database

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Verify schema
docker-compose exec postgres psql -U postgres -d pdf_converter -c "\dt"
# Expected: List of tables (conversions, users, artifacts, etc.)

# (Optional) Seed with test data
docker-compose exec api python scripts/seed_database.py
```

## Step 6: Verify Setup

### Option A: Using Docker Compose (Recommended for development)

```bash
# Start API, Worker, and Beat in Docker
docker-compose up -d api worker beat

# Verify API is running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "0.1.0", ...}

# Access API documentation
open http://localhost:8000/docs
# You should see Swagger UI with all endpoints

# Check worker is processing
docker-compose logs -f worker | grep "ready to accept"
# Expected: "ready to accept tasks"
```

### Option B: Running API/Worker Locally

```bash
# Terminal 1: API server
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
cd apps/worker
celery -A tasks worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
cd apps/worker
celery -A tasks beat --loglevel=info

# Terminal 4: Run tests
cd ../..
pytest tests/ -v
```

## Step 7: Run Tests

```bash
# Run all tests
make test
# or
pytest tests/ -v

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with coverage
make test-coverage
# Coverage report: htmlcov/index.html

# Run specific test
pytest tests/unit/test_models.py::test_table_model_validation -v

# Run with keyword filter
pytest -k "xlsx" -v  # Run all tests with "xlsx" in name
```

## Step 8: Code Quality Checks

```bash
# Format code (auto-fix)
make format
# Equivalent to:
# black apps/ packages/ tests/
# isort apps/ packages/ tests/

# Run linters
make lint
# Equivalent to:
# flake8 apps/ packages/ tests/
# pylint apps/ packages/

# Type checking
make type-check
# mypy apps/ packages/

# All checks together
make quality

# Run pre-commit hooks manually
pre-commit run --all-files
```

## Step 9: Common Development Tasks

### View API Logs in Real-Time
```bash
docker-compose logs -f api
# or just the latest 50 lines:
docker-compose logs --tail=50 api
```

### Access Database
```bash
# Connect to PostgreSQL CLI
docker-compose exec postgres psql -U postgres -d pdf_converter

# Some useful commands:
# \dt - List all tables
# \d conversions - Describe conversions table
# SELECT * FROM conversions ORDER BY created_at DESC LIMIT 10;
# \q - Quit
```

### View Queue Status
```bash
# Active tasks
docker-compose exec worker celery -A apps.worker.tasks inspect active

# Pending tasks
docker-compose exec worker celery -A apps.worker.tasks inspect reserved

# Worker statistics
docker-compose exec worker celery -A apps.worker.tasks inspect stats

# RabbitMQ web UI
open http://localhost:15672
# Username: guest, Password: guest
```

### Run Database Migrations

```bash
# Check current migration
docker-compose exec api alembic current

# Create new migration (after modifying models)
docker-compose exec api alembic revision --autogenerate -m "Add new column"

# Apply migrations
docker-compose exec api alembic upgrade head

# Revert last migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

### Create a Test PDF for Development

```bash
# Create a simple test PDF (requires reportlab or similar)
python scripts/generate_test_pdf.py --output test.pdf --pages 5

# Upload and test conversion
curl -F "file=@test.pdf" http://localhost:8000/v1/files
```

## Step 10: IDE/Editor Setup

### VS Code

Install extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- Pytest Explorer

Configure `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

### PyCharm

1. Open project
2. Set Python interpreter: Settings → Project → Python Interpreter → Add Interpreter → Existing Environment
3. Select: `venv/bin/python`
4. Enable code inspections: Settings → Editor → Inspections
5. Configure pytest: Settings → Tools → Python Integrated Tools → pytest

## Step 11: Troubleshooting

### Issue: "Connection refused" when accessing API

```bash
# Check if API container is running
docker-compose ps api

# If not running, check logs
docker-compose logs api

# Restart API
docker-compose restart api

# If running locally, check port 8000
lsof -i :8000
# Kill if needed: kill -9 <PID>
```

### Issue: Database migration errors

```bash
# Check current state
docker-compose exec api alembic current

# Downgrade to previous version
docker-compose exec api alembic downgrade -1

# Re-apply
docker-compose exec api alembic upgrade head
```

### Issue: Worker not processing tasks

```bash
# Check if worker is running
docker-compose ps worker

# Check logs
docker-compose logs worker

# Verify RabbitMQ connection
docker-compose logs worker | grep -i "connected\|connection"

# Restart worker
docker-compose restart worker
```

### Issue: "out of memory" errors

```bash
# Increase Docker memory limit
# In Docker Desktop: Preferences → Resources → Memory → Set to 4GB+

# Or edit docker-compose.yml worker service:
# services:
#   worker:
#     mem_limit: 4gb

# Restart
docker-compose down && docker-compose up -d
```

### Issue: Port already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process (macOS/Linux)
kill -9 <PID>

# Or change port in docker-compose.yml:
# ports:
#   - "8001:8000"
```

## Step 12: Next Steps

After setup is complete:

1. **Read the documentation**:
   - [README.md](./README.md) - Project overview
   - [PLAN_APP_CONVERSION_PDF_v1.0.md](./PLAN_APP_CONVERSION_PDF_v1.0.md) - Full project plan
   - [docs/ARQUITECTURA.md](./docs/ARQUITECTURA.md) - Architecture details
   - [CLAUDE.md](./CLAUDE.md) - Development guidance

2. **Run a simple test**:
   ```bash
   make test-unit
   ```

3. **Create your first feature**:
   - Create a branch: `git checkout -b feature/my-feature`
   - Make changes
   - Run tests: `make test`
   - Format code: `make format`
   - Commit: `git add . && git commit -m "feat: description"`

4. **Join the team**:
   - Get added to Slack workspace
   - Review team processes in [CONTRIBUIR.md](./CONTRIBUIR.md)
   - Ask questions!

## Development Workflow Quick Reference

```bash
# Start of day
docker-compose up -d
source venv/bin/activate

# Make changes
# ... edit code ...

# Test locally
pytest tests/unit/test_mychanges.py -v

# Format and lint
make format
make quality

# Commit and push
git add .
git commit -m "feat: description"
git push origin feature/my-feature

# End of day
docker-compose down
deactivate
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Project Plan](./PLAN_APP_CONVERSION_PDF_v1.0.md)

## Getting Help

- Check existing documentation in `/docs`
- Review [AVANCE.md](./docs/AVANCE.md) for current blockers
- Ask in team Slack channel
- Create an issue on GitHub for bugs

**Last Updated**: 2026-10-07
