"""
API Configuration

Loads and validates configuration from environment variables using Pydantic Settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application Settings"""

    # ========================================================================
    # Core Application
    # ========================================================================
    APP_NAME: str = "PDF Converter"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ========================================================================
    # API Configuration
    # ========================================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    API_TITLE: str = "PDF Converter API"
    API_DESCRIPTION: str = "Convert PDFs to multiple formats"

    # ========================================================================
    # CORS Configuration
    # ========================================================================
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ========================================================================
    # Database Configuration
    # ========================================================================
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/pdf_converter"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False

    # ========================================================================
    # Redis Configuration
    # ========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: int = 5

    # ========================================================================
    # Celery / RabbitMQ Configuration
    # ========================================================================
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540

    # ========================================================================
    # Storage Configuration
    # ========================================================================
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "/tmp/pdf-converter-storage"
    MAX_FILE_SIZE_MB: int = 25
    MAX_PAGES_PER_JOB: int = 100
    MAX_CONCURRENT_JOBS: int = 10

    # ========================================================================
    # Processing Configuration
    # ========================================================================
    MAX_PROCESSING_TIME_SECONDS: int = 600
    MAX_MEMORY_PER_PROCESS_MB: int = 2048
    OCR_ENGINE: str = "tesseract"
    OCR_LANGUAGES: str = "spa,eng"
    PDF_PARSER_ENGINE: str = "pdfplumber"

    # ========================================================================
    # Data Retention
    # ========================================================================
    RETENTION_HOURS: int = 24
    AUTO_DELETE_ENABLED: bool = True

    # ========================================================================
    # Security Settings
    # ========================================================================
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Session Security
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    CSRF_ENABLED: bool = True

    # ========================================================================
    # Logging Configuration
    # ========================================================================
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/tmp/pdf-converter.log"
    LOG_TO_CONSOLE: bool = True
    LOG_TO_FILE: bool = True

    # ========================================================================
    # Monitoring
    # ========================================================================
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090

    # ========================================================================
    # Feature Flags
    # ========================================================================
    FEATURE_OCR_ENABLED: bool = True
    FEATURE_BATCH_PROCESSING: bool = False
    FEATURE_TABLE_CORRECTION: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Load settings from environment
settings = Settings()
