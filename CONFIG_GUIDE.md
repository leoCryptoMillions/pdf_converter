# Configuration Guide

Complete reference for all configuration options in the PDF Converter application.

**Last Updated**: 2026-10-07

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [FastAPI Configuration](#fastapi-configuration)
3. [Celery Configuration](#celery-configuration)
4. [Database Configuration](#database-configuration)
5. [Storage Configuration](#storage-configuration)
6. [Security Configuration](#security-configuration)
7. [Logging Configuration](#logging-configuration)
8. [Feature Flags](#feature-flags)

## Environment Variables

All environment variables should be defined in `.env` file. Use `.env.example` as template.

### Database Configuration

```bash
# PostgreSQL connection string
DATABASE_URL=postgresql://postgres:password@localhost:5432/pdf_converter

# SQLAlchemy settings
SQLALCHEMY_ECHO=false  # Set to true for SQL query logging
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=40
SQLALCHEMY_POOL_PRE_PING=true
SQLALCHEMY_POOL_RECYCLE=3600
```

### Redis Configuration

```bash
# Redis connection for caching and sessions
REDIS_URL=redis://localhost:6379/0

# Redis settings
REDIS_POOL_SIZE=10
REDIS_DECODE_RESPONSES=true
```

### RabbitMQ / Celery Configuration

```bash
# RabbitMQ message broker
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//

# Redis backend for task results
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Celery settings
CELERY_TASK_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_RESULT_SERIALIZER=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_TASK_TRACK_STARTED=true
CELERY_TASK_TIME_LIMIT=600  # 10 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT=540  # 9 minutes soft limit
CELERY_WORKER_MAX_TASKS_PER_CHILD=100
```

### FastAPI Server Configuration

```bash
# Server settings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development  # or 'production'
DEBUG=true  # Set to false in production
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# API version
API_VERSION=v1
```

### File Upload Configuration

```bash
# Maximum file size (bytes, default 25MB)
MAX_FILE_SIZE=26214400

# Maximum pages per PDF (default 100)
MAX_PDF_PAGES=100

# Maximum total pages per user per day
MAX_DAILY_PAGES=10000

# Allowed file types (MIME types)
ALLOWED_MIME_TYPES=application/pdf

# Temporary storage directory
UPLOAD_DIR=/tmp/pdf-converter-storage

# Quarantine directory for suspicious files
QUARANTINE_DIR=/tmp/pdf-converter-quarantine
```

### PDF Processing Configuration

```bash
# PDF parsing engines
PDF_ENGINE_PRIMARY=pdfplumber  # pdfplumber, docling, camelot

# OCR Settings
ENABLE_OCR=true
OCR_ENGINE=tesseract  # tesseract, paddleocr
OCR_LANGUAGE=spa+eng  # Spanish + English

# Tesseract path (if not in system PATH)
TESSERACT_PATH=/usr/bin/tesseract

# OCR Quality threshold (0.0-1.0)
OCR_MIN_CONFIDENCE=0.7

# Preprocessing
ENABLE_OCR_PREPROCESS=true
OCR_PREPROCESS_ENGINE=ocrmypdf
```

### Export Configuration

```bash
# Excel export
EXCEL_MAX_ROWS=1048576  # Maximum rows in XLSX
EXCEL_MAX_COLUMNS=16384  # Maximum columns in XLSX
EXCEL_LOCALE=es_MX  # Locale for formatting

# Word export
DOCX_PAGE_SIZE=letter  # letter, a4, a5
DOCX_MARGIN_TOP_MM=20
DOCX_MARGIN_BOTTOM_MM=20
DOCX_MARGIN_LEFT_MM=20
DOCX_MARGIN_RIGHT_MM=20

# CSV export
CSV_ENCODING=utf-8
CSV_DELIMITER=,
CSV_QUOTE_CHAR="

# Image export
IMAGE_DPI=150  # DPI for PNG/JPEG export
IMAGE_FORMAT=png  # png, jpeg
IMAGE_QUALITY=85  # JPEG quality (0-100)
IMAGE_MAX_PIXELS=104857600  # Max pixel count
```

### Authentication Configuration

```bash
# JWT configuration
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OIDC Provider (optional)
OIDC_ENABLED=false
OIDC_PROVIDER_URL=https://your-oidc-provider.com
OIDC_CLIENT_ID=your-client-id
OIDC_CLIENT_SECRET=your-client-secret

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

### Security Configuration

```bash
# HTTPS/TLS
FORCE_HTTPS=false  # Set to true in production
HTTPS_ONLY_COOKIES=false  # Set to true in production

# Password hashing
PASSWORD_ALGORITHM=bcrypt
PASSWORD_BCRYPT_ROUNDS=12

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60  # seconds

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# CSP headers
ENABLE_CSP=false
CSP_POLICY="default-src 'self'"

# Security headers
ENABLE_SECURITY_HEADERS=true
```

### Storage Configuration

```bash
# Storage type: local, s3, minio
STORAGE_TYPE=local

# Local storage
LOCAL_STORAGE_PATH=/tmp/pdf-converter-storage

# S3 Configuration
S3_BUCKET=pdf-converter-dev
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_ENDPOINT_URL=https://s3.amazonaws.com

# MinIO Configuration (compatible with S3)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=pdf-converter

# Retention policy
STORAGE_RETENTION_DAYS=1
STORAGE_AUTO_CLEANUP_ENABLED=true
STORAGE_CLEANUP_CRON=0 2 * * *  # 2 AM daily
```

### Logging Configuration

```bash
# Log level
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Structured logging
LOG_FORMAT=json  # json, text
LOG_OUTPUT=console  # console, file, both

# File logging
LOG_FILE_PATH=/var/log/pdf-converter.log
LOG_FILE_SIZE_MB=100
LOG_FILE_BACKUP_COUNT=10

# Logging sensitive data (be careful!)
LOG_INCLUDE_CONTENT=false  # Never log PDF content
LOG_INCLUDE_ERRORS=true
LOG_ERROR_DETAIL=production  # development, production

# Observability
SENTRY_DSN=https://...@sentry.io/...  # Error tracking
DATADOG_API_KEY=...  # Datadog monitoring (optional)
```

### Feature Flags

```bash
# Enable/disable features
FEATURE_XLSX_EXPORT=true
FEATURE_DOCX_EXPORT=true
FEATURE_CSV_EXPORT=true
FEATURE_TXT_EXPORT=true
FEATURE_MARKDOWN_EXPORT=true
FEATURE_JSON_EXPORT=true
FEATURE_IMAGE_EXPORT=true
FEATURE_BATCH_CONVERSION=true
FEATURE_OCR=true
FEATURE_USER_REGISTRATION=false  # Closed beta

# Experimental features
FEATURE_DOCLING_ENGINE=false
FEATURE_CAMELOT_ENGINE=false
FEATURE_ADVANCED_OCR=false
FEATURE_FORMULA_DETECTION=true
FEATURE_TABLE_CORRECTION_UI=true
```

### Monitoring Configuration

```bash
# Prometheus metrics
ENABLE_METRICS=true
METRICS_PORT=9090

# Health check
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30  # seconds

# Tracing (OpenTelemetry)
ENABLE_TRACING=false
TRACING_SAMPLE_RATE=0.1
```

## FastAPI Configuration

### Location: `apps/api/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API info
    API_TITLE: str = "PDF Converter"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "Convert PDFs to multiple formats"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    SQLALCHEMY_POOL_SIZE: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

## Celery Configuration

### Location: `apps/worker/config.py`

```python
from celery import Celery

app = Celery('pdf_converter')

# Broker and result backend
app.conf.broker_url = os.getenv('CELERY_BROKER_URL')
app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND')

# Task settings
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'

# Task routing
app.conf.task_routes = {
    'apps.worker.tasks.extract_pdf': {'queue': 'extraction'},
    'apps.worker.tasks.export_xlsx': {'queue': 'export'},
    'apps.worker.tasks.export_docx': {'queue': 'export'},
}

# Task retry configuration
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
```

## Database Configuration

### Connection Pooling

```bash
# apps/api/config.py
SQLALCHEMY_POOL_SIZE=20  # Min connections in pool
SQLALCHEMY_MAX_OVERFLOW=40  # Additional connections allowed
SQLALCHEMY_POOL_RECYCLE=3600  # Recycle connections after 1 hour
SQLALCHEMY_POOL_PRE_PING=true  # Verify connection before using
```

### Migration Configuration

```bash
# Alembic configuration (alembic.ini)
sqlalchemy.url = driver://user:password@localhost/dbname
script_location = alembic
```

## Storage Configuration

### Local Storage

```bash
STORAGE_TYPE=local
UPLOAD_DIR=/tmp/pdf-converter-storage
# Files stored at: /tmp/pdf-converter-storage/{uuid}/{filename}
```

### S3 Configuration

```bash
STORAGE_TYPE=s3
S3_BUCKET=pdf-converter-prod
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=***
S3_SECRET_ACCESS_KEY=***
# Files stored at: s3://pdf-converter-prod/{conversion_id}/{filename}
```

## Security Configuration

### HTTPS

```bash
# In production, set to true
FORCE_HTTPS=true
HTTPS_ONLY_COOKIES=true

# In docker-compose.yml or nginx
# Generate certificate:
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```

### CORS

Update `CORS_ORIGINS` in `.env`:

```bash
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Rate Limiting

```bash
# Global rate limit
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Per-user limits (in code)
MAX_CONVERSIONS_PER_HOUR=50
MAX_DAILY_PAGES=10000
```

## Logging Configuration

### Log Levels

- `DEBUG`: Verbose, for development
- `INFO`: General application flow
- `WARNING`: Unexpected but handled situations
- `ERROR`: Error conditions requiring attention
- `CRITICAL`: Failure conditions requiring immediate attention

### Structured Logging

```python
import structlog

log = structlog.get_logger()

# Example usage
log.info("conversion_started", 
    job_id="123", 
    format="xlsx",
    duration_ms=1500
)
```

## Feature Flags

Enable/disable features without code changes:

```bash
# Enable DOCX export
FEATURE_DOCX_EXPORT=true

# Enable beta OCR features
FEATURE_ADVANCED_OCR=true

# Disable user registration (closed beta)
FEATURE_USER_REGISTRATION=false
```

Query in code:

```python
from apps.api.config import settings

if settings.FEATURE_TABLE_CORRECTION_UI:
    # Show table editor UI
    pass
```

## Configuration Precedence

1. Environment variables (`.env` file or system env)
2. Pydantic Settings defaults
3. Application hardcoded defaults

Example:

```bash
# .env file
DEBUG=false

# But if system environment has:
# export DEBUG=true
# System env wins, DEBUG=true
```

## Validation

Configuration is validated at startup:

```bash
# If invalid config:
# pydantic.ValidationError: DATABASE_URL must be valid PostgreSQL URL

# Fix:
# 1. Correct .env
# 2. Restart application
```

## Common Configuration Scenarios

### Development

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:password@localhost:5432/pdf_converter_dev
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
FORCE_HTTPS=false
STORAGE_TYPE=local
UPLOAD_DIR=/tmp/pdf-converter-storage
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@postgres.staging.internal:5432/pdf_converter
REDIS_URL=redis://redis.staging.internal:6379/0
CELERY_BROKER_URL=amqp://user:pass@rabbitmq.staging.internal:5672/
CORS_ORIGINS=https://staging.yourdomain.com
FORCE_HTTPS=true
STORAGE_TYPE=s3
S3_BUCKET=pdf-converter-staging
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:secure_pass@postgres-prod.internal:5432/pdf_converter
REDIS_URL=redis://redis-prod.internal:6379/0
CELERY_BROKER_URL=amqp://user:secure_pass@rabbitmq-prod.internal:5672/
JWT_SECRET_KEY=use-secure-random-key-here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FORCE_HTTPS=true
HTTPS_ONLY_COOKIES=true
STORAGE_TYPE=s3
S3_BUCKET=pdf-converter-prod
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_PERIOD=60
```

## References

- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Celery Configuration](https://docs.celeryproject.org/en/stable/userguide/configuration.html)
- [SQLAlchemy Engine](https://docs.sqlalchemy.org/en/20/core/engines.html)

**Last Updated**: 2026-10-07  
**Next Review**: 2026-12-07
