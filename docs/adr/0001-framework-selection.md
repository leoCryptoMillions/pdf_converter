# ADR 0001: Framework Selection - FastAPI + Python

**Date:** 2026-10-07  
**Status:** Accepted  
**Deciders:** Architecture Review Team

## Context

The PDF conversion application requires a backend framework that can:
1. Directly access Python PDF/OCR libraries (pdfplumber, Tesseract, Docling)
2. Provide type safety and API documentation
3. Handle async task processing
4. Support modular document conversion pipelines
5. Integrate with message queues (RabbitMQ) and worker processes

## Decision

**Adopt FastAPI for backend API development.**

FastAPI was selected as the primary framework for the following reasons:

### Advantages (Selected Solution)
- **Typed API Documentation**: Built-in OpenAPI/Swagger generation from Pydantic models
- **Direct Library Access**: Python enables direct use of PDF engines without additional layers
- **Async/Await**: Native async support for I/O-bound operations
- **Dependency Injection**: Clean service layer implementation
- **Ecosystem**: Excellent match for background task processing via Celery
- **Developer Experience**: Clear, explicit code; excellent documentation
- **Performance**: Comparable to Node.js alternatives while maintaining Python ecosystem

### Rationale
Converting PDFs to multiple formats requires:
- Complex document parsing (pdfplumber, Docling, Camelot)
- OCR processing (Tesseract, OCRmyPDF)
- Format-specific export logic (openpyxl, python-docx)

These libraries are primarily Python-based. Using FastAPI+Python avoids:
- Duplicating logic in multiple languages
- Python-to-Node.js RPC complexity
- Maintenance burden of cross-language services

## Alternatives Considered

| Framework | Advantages | Disadvantages | Verdict |
|-----------|-----------|---------------|---------|
| **Django + DRF** | Batteries included (ORM, admin, auth) | Heavier for API-focused app; more boilerplate | Rejected |
| **NestJS + Node** | TypeScript throughout; async | Requires Python bridge; new toolchain; higher complexity | Rejected |
| **ASP.NET Core** | Good if existing .NET infrastructure | PDF libraries less mature; still needs Python bridge | Rejected |
| **FastAPI** | ✓ Typed; async; Python; minimal overhead | Fewer batteries included (auth, admin) | **Selected** |

## Consequences

### Positive
- Python ecosystem fully leveraged for PDF/OCR
- Clear contract between frontend and API via OpenAPI schema
- Type safety reduces bugs in data transformation pipelines
- Async support enables efficient resource utilization

### Negative
- Requires explicit implementation of common features (user auth, admin panel)
- Python deployment/scaling requires different skills than Node/Go
- Celery/RabbitMQ complexity introduced earlier than pure sync framework

### Implementation Requirements
- Use Pydantic for all request/response schemas
- Document OpenAPI contract early
- Establish clear separation between API layer and domain logic
- Use SQLAlchemy with type hints for data access

## Related Decisions

- **ADR 0002**: Database Strategy (PostgreSQL + SQLAlchemy)
- **ADR 0003**: Background Processing (Celery + RabbitMQ)
- **ADR 0004**: Document IR Versioning

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- Python PDF Ecosystem: https://github.com/jsvine/pdfplumber
- Celery Background Tasks: https://docs.celeryq.dev/
