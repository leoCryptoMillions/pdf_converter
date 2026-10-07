"""
FastAPI Application Entry Point

Main application factory for the PDF Converter API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from apps.api.config import settings

# Create FastAPI app instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Convert PDFs to multiple formats (Excel, Word, CSV, etc.)",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS Configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )


# ============================================================================
# Health and Status Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/status", tags=["Health"])
async def status():
    """Detailed status endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


# ============================================================================
# API Routes (Placeholder - to be implemented)
# ============================================================================

@app.get("/v1/info", tags=["Info"])
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "active",
        "endpoints": {
            "files": "/v1/files",
            "conversions": "/v1/conversions",
            "health": "/health",
            "docs": "/docs",
        },
    }


# Routes to implement in F1:
# POST   /v1/files - Upload file
# POST   /v1/conversions - Create conversion job
# GET    /v1/conversions/{id} - Get job status
# GET    /v1/conversions/{id}/preview - Get preview
# PATCH  /v1/conversions/{id}/tables - Update table corrections
# POST   /v1/conversions/{id}/exports - Export with corrections
# POST   /v1/conversions/{id}/cancel - Cancel job
# GET    /v1/artifacts/{id}/download - Download result
# DELETE /v1/conversions/{id} - Delete job and data


# ============================================================================
# Custom OpenAPI Schema
# ============================================================================

def custom_openapi():
    """Customize OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom fields
    openapi_schema["info"]["x-api-id"] = "pdf-converter-api"
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "support@pdf-converter.local",
    }
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://api.pdf-converter.local", "description": "Production"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================================
# Application Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    # TODO: Initialize database connections
    # TODO: Connect to message broker
    # TODO: Perform health checks


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print(f"Shutting down {settings.APP_NAME}")
    # TODO: Close database connections
    # TODO: Disconnect from message broker
    # TODO: Cleanup resources


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS if not settings.API_RELOAD else 1,
    )
