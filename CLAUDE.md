# CLAUDE.md

Comprehensive guidance for Claude Code and development teams working with the PDF Converter project.

## Project Overview

**PDF Converter** is a web application that converts PDF documents (digital, scanned, and mixed) into editable and reusable formats: Excel (.xlsx), Word (.docx), CSV, TXT, Markdown, JSON, and PNG/JPEG. The project emphasizes security, data integrity, and transparent handling of OCR uncertainty.

Core Design Principle: Preserve original content and conversion provenance. Never hide errors, fabricate confidence scores, or sacrifice editability for false fidelity.

**Plan Reference:** [PLAN_APP_CONVERSION_PDF_v1.0.md](./PLAN_APP_CONVERSION_PDF_v1.0.md)  
**Progress Tracking:** [docs/AVANCE.md](./docs/AVANCE.md)  
**Current Phase:** F0 - Viability Assessment  
**Last Updated:** 2026-10-07

---

## Technology Stack (Pinned Versions)

### Core Backend
- **Language**: Python 3.11+ (type hints required)
- **Web Framework**: FastAPI 0.104.1 with async/await
- **Server**: Uvicorn with uvicorn[standard] for production performance
- **ORM**: SQLAlchemy 2.0+ (Core + ORM) with Alembic 1.12 for migrations
- **Database**: PostgreSQL 15+ (jsonb, arrays, full text search)
- **Validation**: Pydantic v2 (strict mode for type safety)
- **Serialization**: pydantic-settings for config management

### Task Queue & Durability
- **Queue Broker**: RabbitMQ 3.12+ (AMQP protocol, durable queues)
- **Task Worker**: Celery 5.3+ with Redis result backend (for state only, not primary storage)
- **Scheduler**: Celery Beat for TTL cleanup tasks, failed job reconciliation
- **Pattern**: Outbox table in PostgreSQL for event-driven architecture
  - All job state transitions via atomic DB transaction + outbox event
  - Separate publisher process polls and publishes pending events
  - RabbitMQ dead-letter queue for poison messages
- **Idempotence**: Implement via (user_id, file_id, options_hash, attempt_id) tuple
- **Retries**: Exponential backoff for transient errors; circuit breaker for persistent failures

### PDF Processing Engines
**Primary (MVP):**
- **pdfplumber** 0.10+ — Extract text, geometry, tables from digital PDFs
  - No OCR capability; use only for text-native PDFs
  - Lightweight, no system dependencies

**Secondary (If F0 gate passed):**
- **Docling** 1.1+ — Document structure, reading order, complex tables
  - Candidate for advanced extraction; requires custom exporters to Office
  - Large model (200+ MB); preinstall in worker image
- **Camelot** 0.11+ — Alternative table extraction
  - Test only flavors supported by this version; ML/OCR extras are version-dependent
  - Not a fallback for OCR-heavy scans

**OCR Pipeline (Conditional):**
- **pytesseract** 0.3+ with Tesseract 5.x system library (Spanish + English)
- **pdf2image** 1.16+ for page rasterization → Tesseract
- **OCRmyPDF** 15.1+ for preprocessing/caching OCR results
  - Verify Ghostscript optional status in your version; Ghostscript 10+ if used
  - Add deskew + orientation correction before Tesseract
- **Language Data**: Pre-download `spa.traineddata`, `eng.traineddata` to worker image
  - Never download at runtime; connection failure = task failure

**Rendering & Validation:**
- **pypdfium2** 4.24+ for page rasterization, bounding boxes
  - Audit binary distribution; disclose LGPL implications
  - Use only for internal validation, not user output by default

### Office Format Export
- **Excel**: openpyxl 3.11+ with styles
  - No formulas from user content; convert formulas to text values
  - Use Decimal type for currency; explicit text type for RFC/CLABE/codes
  - Per-table sheet naming; Origin + Warnings sheets
- **Word**: python-docx 0.8.11+
  - Reconstructs structure only (Heading, Normal, Table styles)
  - Text preservation over visual fidelity
  - No embedded scripts, macros, or external links
  - Images as referenced resources only; sanitize before embedding
- **PowerPoint**: python-pptx 0.6.23 (foundation only; not primary MVP path)

### Frontend
- **Framework**: React 18+ with TypeScript 5.x
- **Build Tool**: Vite 5.x for dev speed and production optimization
- **Bundler**: Built-in Vite; no Webpack configuration needed
- **PDF Preview**: PDF.js 4.x (Mozilla; update quarterly for security)
- **State Management**: TBD (Redux, Zustand, or Context API per team)
- **Form Handling**: React Hook Form with Zod validation schema alignment
- **Accessibility**: WCAG 2.1 AA compliance (keyboard nav, screen reader, focus management)

### Infrastructure & Deployment
- **Containerization**: Docker 24+, Docker Compose 2.20+
- **Storage**: Local filesystem (dev) or S3-compatible object store (minio/AWS S3)
  - TLS for object store communication; separate credentials per environment
- **Caching/Sessions**: Redis 7+ (session tokens only; no persistent application state)
- **Logging**: structlog 24+ with python-json-logger for structured JSON output
  - No user content, file paths, or credentials in logs
- **Monitoring**: Prometheus client 0.19+ for metrics export
  - Metrics: phase timing, error rates, queue depth, memory usage, TTL cleanup success rate
- **Secret Management**: Environment variables (development) or external vault (production)

### Development & Quality Tools
- **Testing Framework**: pytest 7.4+, pytest-asyncio, pytest-cov
- **Mocking**: pytest-mock, responses (HTTP mocking)
- **Performance**: pytest-benchmark for reproducible measurements
- **Linting & Formatting**: 
  - ruff (replaces flake8, pylint, isort)
  - black 24+ for code formatting
- **Type Checking**: mypy 1.7+ with strict mode enabled
- **Pre-commit**: pre-commit 3.5+ framework
- **CI/CD**: GitHub Actions (or GitLab CI, depending on hosting)

---

## Quick Start

### Initial Setup

```bash
# 1. Clone and create virtual environment
git clone <repo>
cd pdf_converter
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Setup environment configuration
cp .env.example .env
# Edit .env with your secrets (PostgreSQL, S3, etc.)

# 4. Start services via Docker Compose
docker-compose -f docker-compose.yml up -d

# 5. Run database migrations
docker-compose exec api python -m alembic upgrade head

# 6. Verify setup
make test
# Navigate to http://localhost:8000/docs for OpenAPI

# 7. Watch worker logs (in another terminal)
docker-compose logs -f worker
```

### Common Development Commands

```bash
# API development server (auto-reload on file changes)
make run

# Start Celery worker in foreground (see task logs)
make run-worker

# Run full test suite
make test

# Run specific test file with verbose output
pytest tests/unit/test_converters.py -v

# Generate coverage report
make test-coverage

# Code quality checks (ruff, black, mypy)
make quality

# Autoformat code
make format

# Database operations
make db-migrate                 # Generate new migration
make db-migration              # Show migration status
docker-compose exec api python -m alembic upgrade head

# View Celery queue state
celery -A apps.worker inspect active

# Inspect Postgres schema
docker-compose exec db psql -U postgres -d pdf_converter -c "\d"

# Stop all services
docker-compose down

# Full reset (danger: deletes data)
docker-compose down -v && docker-compose up -d
```

---

## Architecture Patterns

### 1. Request/Response Design with Pydantic

**Rule**: All API contracts use Pydantic models for validation and OpenAPI schema generation.

```python
# apps/api/schemas/conversions.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum

class OutputFormat(str, Enum):
    XLSX = "xlsx"
    DOCX = "docx"
    CSV = "csv"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    PNG = "png"

class ConversionRequest(BaseModel):
    file_id: str = Field(..., description="Uploaded file UUID")
    format: OutputFormat
    pages: list[int] | None = Field(default=None, description="1-indexed page range")
    options: dict = Field(default_factory=dict)

    @field_validator('pages')
    @classmethod
    def validate_pages(cls, v):
        if v and (min(v) < 1 or max(v) > 100):  # Enforce F0 gate limit
            raise ValueError("Pages must be 1-100")
        return v

class ConversionResponse(BaseModel):
    job_id: str
    status: str  # queued, validating, extracting, exporting, succeeded, needs_review, failed, cancelled, expired
    created_at: datetime
    estimated_seconds: int | None = None
```

**Pattern**: Use `.model_dump(by_alias=True, exclude_none=True)` for API responses; Pydantic v2 replaces `.dict()`.

### 2. FastAPI Dependency Injection for Auth & Permissions

```python
# apps/api/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

async def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT token; return authenticated User."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    token = authorization.split(" ")[1]
    user = verify_jwt_and_get_user(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user

async def check_conversion_ownership(
    conversion_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Conversion:
    """Verify user owns the conversion; raise 403 if not."""
    conversion = db.query(Conversion).filter(
        Conversion.id == conversion_id,
        Conversion.user_id == current_user.id
    ).first()
    if not conversion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return conversion

# Usage in route:
@app.get("/v1/conversions/{conversion_id}", response_model=ConversionResponse)
async def get_conversion(
    conversion: Conversion = Depends(check_conversion_ownership)
) -> ConversionResponse:
    return ConversionResponse.from_orm(conversion)
```

### 3. PDF Processing Pipeline (Conversion Workflow)

**Core Flow:**
```
Streaming Upload → Quarantine → Validate → Classify → Extract → Export → Publish
```

**Validation Phase (API process):**
1. Receive file in streaming mode (avoid loading entire file into memory)
2. Write to quarantine directory (separate from user-facing storage)
3. Validate PDF structure (magic bytes, CRC, page count)
4. Detect encryption, corruption, or suspicious content
5. Classify pages: digital (>80% text coverage) vs. scanned vs. mixed
6. Respond with file_id + classification for user UX

**Extraction Phase (Worker process, fully isolated):**
1. Receive file_id and job config
2. Load PDF from quarantine (never from user-provided path)
3. Run engine (pdfplumber → Docling fallback)
4. Extract to DocumentIR (intermediate representation)
5. Calculate coverage metrics and uncertainty flags
6. Validate structure (table detection, OCR quality if used)
7. Publish DocumentIR to artifact storage (temporary)

**Export Phase (Worker process):**
1. Load DocumentIR from storage
2. Run format-specific exporter (xlsx_export, docx_export, etc.)
3. Validate result (file opens, content present, no injection)
4. Sign/version the result
5. Publish to final artifact store (permanent until TTL)
6. Update job state to "succeeded" or "needs_review"

**Critical Rules:**
- Never load entire PDF into memory for large files (stream with pypdfium2 page by page)
- Process PDFs in isolated worker; never in API process (security + responsiveness)
- Assume PDF content is adversarial (malformed, cycles, infinite loops, bombs)
- Always return `needs_review` if uncertainty detected; never hide warnings

### 4. DocumentIR (Intermediate Representation) Contract

**Location:** `packages/document_ir/models.py`

**Root Structure:**
```python
class DocumentIR(BaseModel):
    schema_version: str = "1.0"
    source_hash: str  # SHA-256 of original PDF
    
    # Provenance
    engines_used: dict[str, str]  # {"pdfplumber": "0.10", "tesseract": "5.2"}
    models_used: dict[str, str]   # {"docling": "v1.1-2026-10-07"}
    extraction_options: dict
    
    # Metadata
    page_count: int
    rotation_degrees: int
    page_size_pt: tuple[float, float]  # Width, height in PDF points
    
    # Content
    pages: list[Page]
    
    # Quality indicators
    text_coverage: float  # 0.0-1.0 of recoverable text
    warnings: list[ContentWarning]
```

**Page, TextBlock, Table Models:**
```python
class Page(BaseModel):
    page_num: int
    height_pt: float
    width_pt: float
    is_scanned: bool  # False: digital, True: requires OCR
    text_coverage: float
    blocks: list[TextBlock | Table | Image]
    transformation_matrix: list[float] | None  # For rotated content

class Table(BaseModel):
    table_id: str
    bbox_pt: tuple[float, float, float, float]  # x0, y0, x1, y1 in points
    rows: int
    cols: int
    cells: list[Cell]
    extraction_method: str  # "pdfplumber", "docling", "tesseract"
    confidence: float | None  # Only if engine provides it; not heuristic
    warnings: list[ContentWarning]

class Cell(BaseModel):
    row: int
    col: int
    text_original: str  # Verbatim from PDF/OCR
    text_normalized: str | None  # After cleanup (locale-aware)
    value_type: str  # "text", "numeric", "date", "currency"
    bbox_pt: tuple[float, float, float, float]
    spans: list[Span]  # Sub-cell regions if needed
    source: str  # "digital_text", "ocr", "table_structure"
```

**Key Rule**: Never fabricate confidence scores. Use only observed metrics:
- `text_coverage` = extracted characters / expected characters
- `ocr_cer` = character error rate (Levenshtein / length)
- Store as-is; let exporters decide thresholds for warnings

### 5. Excel Export (XLSX) Detailed Strategy

**Design Goals**: Preserve data integrity, signpost uncertainty, support correction.

```python
# packages/exporters/xlsx_exporter.py
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter
from decimal import Decimal

class XLSXExporter:
    def export(self, doc_ir: DocumentIR, options: dict) -> bytes:
        """
        Export DocumentIR to XLSX with data types, warnings, and origin tracking.
        """
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Extract tables and create sheets
        table_count = 0
        for page in doc_ir.pages:
            for table in [b for b in page.blocks if isinstance(b, Table)]:
                table_count += 1
                sheet = self._create_table_sheet(wb, table, table_count)
        
        if table_count == 0:
            # No tables found; create single text sheet
            self._create_text_sheet(wb, doc_ir)
        
        # Add metadata sheets
        self._add_origin_sheet(wb, doc_ir)
        if any(w for w in doc_ir.warnings if w.severity in ["high", "critical"]):
            self._add_warnings_sheet(wb, doc_ir)
        
        # Serialize
        output = BytesIO()
        wb.save(output)
        return output.getvalue()
    
    def _create_table_sheet(self, wb: Workbook, table: Table, seq: int) -> Worksheet:
        """Create sheet for one table with proper type handling."""
        sheet_name = f"Table_{seq}"[:31]  # Excel 31-char limit
        ws = wb.create_sheet(sheet_name)
        
        # Build cell matrix
        for cell in table.cells:
            excel_col = get_column_letter(cell.col + 1)
            excel_row = cell.row + 1
            
            # Determine value and type
            if cell.value_type == "numeric":
                ws[f"{excel_col}{excel_row}"] = Decimal(cell.text_normalized)
            elif cell.value_type == "date":
                ws[f"{excel_col}{excel_row}"] = parse_date(cell.text_normalized)
            elif cell.value_type in ["rfc", "clabe", "code"]:
                # Always text to preserve leading zeros
                ws[f"{excel_col}{excel_row}"] = cell.text_original
                ws[f"{excel_col}{excel_row}"].number_format = '@'
            else:
                # Default: string
                ws[f"{excel_col}{excel_row}"] = cell.text_original
        
        # Format header row
        for col_num, cell in enumerate(table.cells[:table.cols], 1):
            if cell.row == 0:
                cell_ref = get_column_letter(col_num) + "1"
                ws[cell_ref].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
                ws[cell_ref].font = Font(bold=True)
        
        # Highlight cells requiring review
        warning_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        for cell in table.cells:
            if cell.warnings:
                ws[f"{get_column_letter(cell.col + 1)}{cell.row + 1}"].fill = warning_fill
        
        # Set column widths
        for col in range(1, table.cols + 1):
            ws.column_dimensions[get_column_letter(col)].width = 20
        
        return ws
    
    def _add_origin_sheet(self, wb: Workbook, doc_ir: DocumentIR):
        """Add metadata: source pages, extraction engines, and confidence."""
        ws = wb.create_sheet("_Origin", 0)  # First sheet
        ws.append(["Source File Hash", doc_ir.source_hash])
        ws.append(["Schema Version", doc_ir.schema_version])
        ws.append(["Extraction Engines", ", ".join(doc_ir.engines_used.keys())])
        ws.append(["Total Pages", doc_ir.page_count])
        ws.append(["Text Coverage", f"{doc_ir.text_coverage:.1%}"])
        # Add per-table origin rows if needed
```

**Data Type Handling:**
- **RFC, CLABE, codes**: Always text (`@` format) to preserve leading zeros
- **Currency/amounts**: Use Decimal type with locale-aware format
- **Dates**: Parse with region awareness; document ambiguous formats as warnings
- **Identifiers**: Text if they exceed Excel's float precision (>15 digits)

**Warnings Sheet** (if any high/critical warnings):
- List issues by table, cell, and recommended action
- Never remove rows because they "look duplicated" without source evidence

**Important**: Do NOT export formulas from user content. Convert detected formulas to text values.

### 6. Word Export (DOCX) Detailed Strategy

**Design Goals**: Editable content + approximate structure + clear degradation messages.

```python
# packages/exporters/docx_exporter.py
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class DOCXExporter:
    def export(self, doc_ir: DocumentIR, options: dict) -> bytes:
        """
        Export DocumentIR to DOCX with structure, images, and warnings.
        Two objectives: (1) editable text, (2) approximate visual fidelity.
        May conflict; prioritize editability.
        """
        doc = Document()
        
        # Add header
        doc.add_heading("Converted from PDF", level=0)
        doc.add_paragraph(f"Source: {doc_ir.source_hash[:8]}")
        
        # Process pages and blocks
        for page in doc_ir.pages:
            if page.page_num > 1:
                doc.add_page_break()
            
            for block in page.blocks:
                if isinstance(block, TextBlock):
                    # Reconstruct paragraph with styles
                    para = doc.add_paragraph(block.text)
                    if block.style == "heading":
                        para.style = "Heading 1"
                    elif block.style == "bold":
                        for run in para.runs:
                            run.bold = True
                
                elif isinstance(block, Table):
                    # Reconstruct table
                    self._add_table_to_docx(doc, block)
                
                elif isinstance(block, Image):
                    # Embed image (sanitized)
                    self._add_image_to_docx(doc, block)
        
        # Add warnings as appendix if needed
        if any(w for w in doc_ir.warnings if w.severity == "high"):
            doc.add_page_break()
            doc.add_heading("Conversion Warnings", level=1)
            for warning in doc_ir.warnings:
                if warning.severity == "high":
                    doc.add_paragraph(f"• {warning.message}", style="List Bullet")
        
        # Serialize
        output = BytesIO()
        doc.save(output)
        return output.getvalue()
    
    def _add_table_to_docx(self, doc: Document, table_ir: Table):
        """Reconstruct table with rows, columns, and cell content."""
        rows, cols = table_ir.rows, table_ir.cols
        docx_table = doc.add_table(rows=rows, cols=cols)
        docx_table.style = "Light Grid Accent 1"
        
        for cell_ir in table_ir.cells:
            cell_docx = docx_table.rows[cell_ir.row].cells[cell_ir.col]
            para = cell_docx.paragraphs[0]
            para.text = cell_ir.text_original
            
            if cell_ir.warnings:
                para.text = f"[!] {cell_ir.text_original}"
                para.runs[0].font.color.rgb = RGBColor(255, 0, 0)

    def _add_image_to_docx(self, doc: Document, image_ir: Image):
        """Embed image with size limits; sanitize if necessary."""
        if image_ir.size_bytes > 5_000_000:  # 5 MB limit
            doc.add_paragraph(f"[Image too large to embed: {image_ir.size_bytes / 1e6:.1f} MB]")
            return
        
        try:
            doc.add_picture(image_ir.data_path, width=Inches(5))
        except Exception as e:
            doc.add_paragraph(f"[Image failed to embed: {str(e)[:100]}]")
```

**Structure Rules:**
- Map PDF logical structure (headings, body, lists) to DOCX styles
- Order of reading must match PDF; validate with screenreader
- Never embed text as images; always preserve text content
- Table cell content is editable text, not image

**Degradation**:
- Complex multi-column layouts → single column + warnings
- Absolutely positioned text → sequential + warnings
- Rotated text → as-is with orientation warning
- Complex fills → simplified or omitted
- Embedded fonts → system fallback + note

### 7. Worker Task Design & Idempotence

**Pattern**: All Celery tasks must be idempotent and track attempts atomically.

```python
# apps/worker/tasks.py
from celery import shared_task, Task
from apps.api.models import Conversion, ConversionAttempt
from packages.converters import get_converter
from packages.exporters import get_exporter
import tempfile
import os

class ConversionTask(Task):
    """Base task with cleanup and error handling."""
    autoretry_for = (TemporaryError,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called if task fails after retries."""
        conversion_id = kwargs.get('conversion_id')
        log.error("task_failed", task_id=task_id, conversion_id=conversion_id, error=str(exc))

@shared_task(base=ConversionTask, bind=True)
def convert_pdf_to_format(
    self,
    conversion_id: str,
    file_id: str,
    output_format: str,
    options: dict
) -> dict:
    """
    Atomically convert PDF with idempotence and cleanup.
    
    Idempotency Key: (user_id, file_id, options_hash) prevents duplicate work.
    Attempt Tracking: Each retry increments attempt_id.
    Cleanup: Always run cleanup even on error.
    """
    db = SessionLocal()
    temp_dir = None
    attempt = None
    
    try:
        # Load conversion record and user
        conversion = db.query(Conversion).filter_by(id=conversion_id).first()
        if not conversion:
            raise ValueError(f"Conversion {conversion_id} not found")
        
        # Create attempt record (idempotency check)
        attempt = ConversionAttempt(
            conversion_id=conversion_id,
            attempt_num=self.request.retries + 1,
            status="processing"
        )
        db.add(attempt)
        db.commit()
        
        # Create ephemeral directory for this job only
        temp_dir = tempfile.mkdtemp(prefix=f"conv_{conversion_id}_")
        
        log.info("conversion_started", conversion_id=conversion_id, 
                format=output_format, temp_dir=temp_dir)
        
        # Load original PDF from quarantine
        pdf_path = get_quarantine_path(file_id)
        if not os.path.exists(pdf_path):
            raise ValueError(f"Source PDF {file_id} not found in quarantine")
        
        # Step 1: Extract to DocumentIR
        log.info("phase_started", phase="extraction")
        converter = get_converter("pdfplumber")  # or Docling fallback
        doc_ir = converter.extract(pdf_path, options=options)
        log.info("phase_complete", phase="extraction", 
                tables_found=len([b for p in doc_ir.pages for b in p.blocks if isinstance(b, Table)]))
        
        # Step 2: Validate extraction
        if not doc_ir.pages or doc_ir.text_coverage < 0.1:
            conversion.status = "needs_review"
            conversion.needs_review_reason = "Low text coverage or no content detected"
            db.add(conversion)
            db.commit()
            attempt.status = "succeeded_needs_review"
            db.add(attempt)
            db.commit()
            return {"status": "needs_review", "reason": "no_content"}
        
        # Step 3: Export to target format
        log.info("phase_started", phase="export")
        exporter = get_exporter(output_format)
        artifact_bytes = exporter.export(doc_ir, options=options)
        log.info("phase_complete", phase="export", size_bytes=len(artifact_bytes))
        
        # Step 4: Publish result atomically
        log.info("phase_started", phase="publish")
        artifact_id = publish_artifact(
            conversion_id=conversion_id,
            format=output_format,
            data=artifact_bytes,
            doc_ir=doc_ir,
            attempt_id=attempt.id
        )
        
        # Step 5: Update state (DB only; events via outbox)
        conversion.status = "succeeded"
        conversion.artifact_id = artifact_id
        conversion.completed_at = datetime.utcnow()
        db.add(conversion)
        
        attempt.status = "succeeded"
        attempt.artifact_id = artifact_id
        db.add(attempt)
        
        db.commit()
        
        log.info("conversion_completed", conversion_id=conversion_id, artifact_id=artifact_id)
        return {"status": "succeeded", "artifact_id": artifact_id}
    
    except TemporaryError as e:
        # Network, DB, broker — retry
        log.warning("temporary_error", error=str(e), retries=self.request.retries)
        if attempt:
            attempt.status = "transient_error"
            attempt.error = str(e)[:500]
            db.add(attempt)
            db.commit()
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    
    except PermanentError as e:
        # Bad PDF, unsupported content — don't retry
        log.error("permanent_error", conversion_id=conversion_id, error=str(e))
        conversion.status = "failed"
        conversion.error = str(e)[:500]
        db.add(conversion)
        
        if attempt:
            attempt.status = "permanent_error"
            attempt.error = str(e)[:500]
            db.add(attempt)
        
        db.commit()
        return {"status": "failed", "error": str(e)[:100]}
    
    finally:
        # Always cleanup ephemeral directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                log.debug("temp_cleanup_success", temp_dir=temp_dir)
            except Exception as e:
                log.error("temp_cleanup_failed", temp_dir=temp_dir, error=str(e))
        
        db.close()
```

**Idempotence Guarantees:**
- Idempotency key: hash(user_id + file_id + options) prevents duplicate conversions
- Attempt tracking: Each retry increments attempt_num and is independently recorded
- Atomicity: Job state + attempt record + outbox event in single transaction
- Exactly-once delivery: Publisher deduplicates by (conversion_id, artifact_id)

### 8. Logging & Observability (No Content, Ever)

**Rule**: Never log user content, file paths, raw SQL, credentials, or OCR text.

```python
# Structured logging with context
import structlog

log = structlog.get_logger()

# Good: Observable but not sensitive
log.info("conversion_started",
    conversion_id="abc-123",  # UUID OK
    format="xlsx",
    phase="extraction")

log.warning("extraction_quality_low",
    page_num=5,
    text_coverage_ratio=0.25,  # Metrics OK
    recommendation="manual_review")  # Actionable guidance

# Bad: Do not do this
log.info("content:", text_content)  # Breach
log.error("file at /home/user/secret.pdf")  # Path leak
log.debug("password attempt", pwd=user_input)  # Credential leak

# Errors: Sanitize before logging
try:
    load_pdf(path)
except Exception as e:
    # Good: Generic, not the actual traceback
    log.error("pdf_load_failed", file_id=file_id, error_type=type(e).__name__)
    
    # Bad: Do not do this
    # log.error("pdf_load_failed", traceback=traceback.format_exc())
```

**Metrics to Export** (Prometheus):
- `conversion_phase_duration_seconds` (histogram by phase: extraction, export)
- `conversions_total` (counter by status: succeeded, failed, needs_review)
- `queue_depth` (gauge: pending tasks in RabbitMQ)
- `worker_memory_usage_bytes` (gauge per worker)
- `artifact_cleanup_success_total` (counter: TTL-based deletions completed)
- `artifact_orphaned_count` (gauge: unpublished temporary files)

---

## Security & OWASP Compliance

### PDF Parsing Hardening

**Threat Model**: PDFs are untrusted input. Attackers may embed exploits, infinite loops, or resource bombs.

**Mitigations:**
1. **Isolation**: Parse only in worker process (separate from API)
   - No root user; restricted `/tmp` and `/home`
   - seccomp or AppArmor profile limiting system calls
   - Resource limits: CPU time, memory, file descriptors, pixel count

2. **Validation**:
   - Check magic bytes (PDF file header)
   - Validate CRC/xref sections
   - Detect encryption; never auto-decrypt
   - Scan for embedded JavaScript or launch actions (log + reject or sandbox)

3. **Dependencies**:
   - pdfplumber: Pure Python, no native binaries
   - Tesseract: System package; audit version and disable extra features
   - pypdfium2: Audit binary distribution; verify LGPL compliance
   - Always use pinned versions; never use `latest` in production

4. **Timeouts**:
   - Page parsing: 60 seconds per page max
   - OCR: 180 seconds per page max
   - Export: 60 seconds per 10 pages max
   - Kill task if exceeded; mark as `failed` or `timeout`

### File Upload & Storage (OWASP File Upload Cheat Sheet)

```python
# apps/api/routes/files.py
from fastapi import UploadFile, File
from apps.api.dependencies import get_current_user
from apps.api.models import UploadedFile
import uuid
import hashlib

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB per plan

@app.post("/v1/files")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    Receive PDF in streaming mode, validate, quarantine, and return file_id.
    
    Validations:
    1. Content-Type must be application/pdf (check magic bytes, not header)
    2. Size must be <= 25 MB
    3. No traversal in original filename (ignored; use server-generated name)
    4. Virus/malware scan (optional; external service)
    """
    
    # Check size in streaming (don't load entire file)
    size_bytes = 0
    file_hash = hashlib.sha256()
    quarantine_id = str(uuid.uuid4())
    quarantine_path = get_quarantine_path(quarantine_id)
    
    try:
        with open(quarantine_path, 'wb') as f:
            while True:
                chunk = await file.read(64 * 1024)  # 64 KB chunks
                if not chunk:
                    break
                size_bytes += len(chunk)
                file_hash.update(chunk)
                f.write(chunk)
                
                if size_bytes > MAX_FILE_SIZE:
                    os.remove(quarantine_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {MAX_FILE_SIZE / 1e6:.0f} MB limit"
                    )
    except Exception as e:
        try:
            os.remove(quarantine_path)
        except:
            pass
        raise
    
    # Validate PDF magic bytes
    with open(quarantine_path, 'rb') as f:
        magic = f.read(4)
    if not magic.startswith(b'%PDF'):
        os.remove(quarantine_path)
        raise HTTPException(status_code=400, detail="Not a valid PDF file")
    
    # Record in DB
    uploaded_file = UploadedFile(
        id=quarantine_id,
        user_id=current_user.id,
        original_filename=file.filename[:255],  # Truncate; for UX only
        size_bytes=size_bytes,
        content_hash=file_hash.hexdigest(),
        status="quarantined",
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_file)
    db.commit()
    
    # Schedule background validation job
    # (async task: validate structure, classify pages, update status)
    
    return FileResponse(
        file_id=quarantine_id,
        filename=file.filename,
        size_bytes=size_bytes
    )
```

**Key Rules**:
- Server generates names for all files (e.g., `conv_<uuid>_<seq>.xlsx`)
- Original filename is for user display only; never use in file I/O
- No symbolic links, traversal (`../`), or user control over paths
- Quarantine directory must be on separate filesystem from production if possible

### Data Retention & Cleanup (GDPR/Privacy)

**Lifecycle**:
1. **Upload → Quarantine**: Ephemeral (24 hours or job completion, whichever first)
2. **Artifact Temporary**: During processing (TTL ~1 hour after export)
3. **Artifact Downloadable**: 24 hours (configurable per org)
4. **Archived/Audit Logs**: Minimal (no content; only metadata)
5. **User Deletion**: Cascade delete all artifacts and conversions; 30-day retention for audit

```python
# Celery Beat task: cleanup expired artifacts
@periodic_task(run_every=crontab(minute=0))  # Every hour
def cleanup_expired_artifacts():
    """Delete artifacts past retention TTL and update DB."""
    db = SessionLocal()
    now = datetime.utcnow()
    
    # Find expired conversions
    expired = db.query(Conversion).filter(
        Conversion.status == "succeeded",
        Conversion.completed_at < now - timedelta(hours=24)
    ).all()
    
    for conversion in expired:
        if conversion.artifact_id:
            # Delete from object store
            try:
                delete_from_storage(conversion.artifact_id)
                log.info("artifact_deleted", artifact_id=conversion.artifact_id)
            except Exception as e:
                log.error("artifact_delete_failed", artifact_id=conversion.artifact_id, error=str(e))
                continue
        
        # Soft-delete from DB (keep audit record)
        conversion.status = "expired"
        conversion.deleted_at = now
    
    db.commit()
```

### Injection Prevention

**CSV/XLSX Injection** (OWASP):
- Never export formulas from user content
- Prefix cells starting with `=`, `+`, `@`, `-` with `'` (text prefix)
- Test with formula payloads in security test suite

```python
def sanitize_cell_value(value: str) -> str:
    """Prevent formula injection in CSV/XLSX export."""
    if isinstance(value, str) and len(value) > 0:
        if value[0] in ('=', '+', '@', '-'):
            return f"'{value}"  # Prefix with quote to force text
    return value
```

**Path Traversal**:
- Use `pathlib.Path` with `.resolve()` and `is_relative_to()` checks
- Never construct paths via string concatenation

```python
from pathlib import Path

base = Path("/srv/artifacts").resolve()
requested = (base / user_input_filename).resolve()
if not requested.is_relative_to(base):
    raise ValueError("Path traversal detected")
```

**SQL Injection**:
- Always use parameterized queries (SQLAlchemy ORM prevents this)
- Never construct SQL strings from user input

---

## Testing Strategy

### Test Organization & Execution

```
tests/
├── unit/
│   ├── test_converters.py        # pdfplumber, Docling, Camelot
│   ├── test_exporters.py         # XLSX, DOCX, CSV, JSON
│   ├── test_models.py            # DocumentIR, Pydantic schemas
│   └── test_validators.py        # Region/locale-aware parsing
├── integration/
│   ├── test_database.py          # ORM, migrations, outbox
│   ├── test_worker.py            # Celery tasks, idempotence, retries
│   ├── test_storage.py           # S3 mock, object lifecycle
│   └── test_api_full.py          # Endpoint integration
├── e2e/
│   ├── test_pdf_to_xlsx.py       # Upload → Convert → Download
│   ├── test_pdf_to_docx.py       # Editability validation
│   └── test_error_paths.py       # Corrupted PDFs, cancellation
├── security/
│   ├── test_access_control.py    # User isolation
│   ├── test_injection.py         # Formula, traversal, command injection
│   ├── test_resource_limits.py   # Timeouts, memory bombs
│   └── test_sensitive_leaks.py   # No content in logs/errors
└── conftest.py                   # Fixtures, DB setup
```

### Pytest Configuration & Markers

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Fast, isolated tests (no I/O)
    integration: Database, broker, storage
    e2e: Full workflow tests
    security: Penetration and validation
    slow: Long-running (e.g., OCR benchmarks)
    benchmark: Performance regression tests
```

### Key Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_db():
    """In-memory SQLite for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(test_db):
    """Transactional session; rollback after each test."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_pdf_digital():
    """5-page digital PDF with text and one table."""
    return load_fixture("samples/digital_simple.pdf")

@pytest.fixture
def sample_pdf_scanned():
    """10-page scanned PDF (clean, English)."""
    return load_fixture("samples/scanned_clean.pdf")

@pytest.fixture
def api_client(db_session):
    """FastAPI TestClient with auth headers."""
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    
    # Create test user
    user = User(id="test-user", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Attach auth header
    client.headers.update({
        "Authorization": f"Bearer {create_test_token('test-user')}"
    })
    
    yield client
    
    app.dependency_overrides.clear()
```

### Unit Test Examples

```python
# tests/unit/test_exporters.py
import pytest
from packages.exporters import XLSXExporter
from packages.document_ir.models import DocumentIR, Table, Cell

@pytest.mark.unit
def test_xlsx_export_preserves_data_types():
    """Numeric types, dates, and text RFC codes."""
    # Arrange
    cell_text = Cell(row=0, col=0, text_original="12345-ABC", value_type="rfc")
    cell_amount = Cell(row=0, col=1, text_original="1,234.56", value_type="currency")
    
    table = Table(rows=1, cols=2, cells=[cell_text, cell_amount])
    doc_ir = DocumentIR(pages=[Page(blocks=[table])])
    
    # Act
    exporter = XLSXExporter()
    result_bytes = exporter.export(doc_ir, {})
    
    # Assert (load and inspect)
    from openpyxl import load_workbook
    from io import BytesIO
    wb = load_workbook(BytesIO(result_bytes))
    ws = wb.active
    
    assert ws['A1'].value == "12345-ABC"
    assert ws['A1'].number_format == "@"  # Text type
    
    # Currency should be Decimal
    assert isinstance(ws['B1'].value, Decimal)

@pytest.mark.unit
def test_xlsx_export_prevents_formula_injection():
    """Leading =, +, @ must be escaped."""
    cell_formula = Cell(row=0, col=0, text_original="=1+1", value_type="text")
    table = Table(rows=1, cols=1, cells=[cell_formula])
    doc_ir = DocumentIR(pages=[Page(blocks=[table])])
    
    exporter = XLSXExporter()
    result_bytes = exporter.export(doc_ir, {})
    
    from openpyxl import load_workbook
    from io import BytesIO
    wb = load_workbook(BytesIO(result_bytes))
    ws = wb.active
    
    # Must have escaped prefix
    assert ws['A1'].value == "'=1+1"

@pytest.mark.unit
def test_docx_export_preserves_editability():
    """Text is editable, not embedded as images."""
    text_block = TextBlock(text="Hello World", style="normal")
    doc_ir = DocumentIR(pages=[Page(blocks=[text_block])])
    
    exporter = DOCXExporter()
    result_bytes = exporter.export(doc_ir, {})
    
    from docx import Document
    from io import BytesIO
    doc = Document(BytesIO(result_bytes))
    
    # Must have editable text, not image
    assert doc.paragraphs[0].text == "Hello World"
```

### Integration Test Examples

```python
# tests/integration/test_worker.py
@pytest.mark.integration
async def test_conversion_task_is_idempotent(db_session, sample_pdf_digital):
    """Running task twice with same inputs yields same artifact."""
    from apps.worker.tasks import convert_pdf_to_format
    
    # Arrange
    conversion = Conversion(user_id="user1", file_id="file1", format="xlsx")
    db_session.add(conversion)
    db_session.commit()
    
    # Act: Run task twice
    result1 = await convert_pdf_to_format(
        conversion_id=conversion.id,
        file_id="file1",
        output_format="xlsx",
        options={}
    )
    
    result2 = await convert_pdf_to_format(
        conversion_id=conversion.id,
        file_id="file1",
        output_format="xlsx",
        options={}
    )
    
    # Assert: Same artifact
    assert result1["artifact_id"] == result2["artifact_id"]
    
    # Only one attempt published
    attempts = db_session.query(ConversionAttempt).filter_by(
        conversion_id=conversion.id
    ).all()
    assert len(attempts) == 1
```

### E2E Test Examples

```python
# tests/e2e/test_pdf_to_xlsx.py
@pytest.mark.e2e
async def test_full_workflow_upload_to_download(api_client, sample_pdf_digital):
    """User uploads PDF, converts, reviews, and downloads XLSX."""
    # Step 1: Upload
    response = api_client.post(
        "/v1/files",
        files={"file": ("test.pdf", sample_pdf_digital, "application/pdf")}
    )
    assert response.status_code == 200
    file_id = response.json()["file_id"]
    
    # Step 2: Request conversion
    response = api_client.post("/v1/conversions", json={
        "file_id": file_id,
        "format": "xlsx"
    })
    assert response.status_code == 202
    conversion_id = response.json()["job_id"]
    
    # Step 3: Poll status (with timeout)
    import time
    timeout = time.time() + 60
    while time.time() < timeout:
        response = api_client.get(f"/v1/conversions/{conversion_id}")
        status = response.json()["status"]
        if status in ["succeeded", "needs_review", "failed"]:
            break
        time.sleep(1)
    
    assert status != "failed"
    
    # Step 4: Download artifact
    response = api_client.get(f"/v1/conversions/{conversion_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Step 5: Validate XLSX
    from openpyxl import load_workbook
    from io import BytesIO
    wb = load_workbook(BytesIO(response.content))
    assert len(wb.sheetnames) > 0  # At least one sheet
```

### Security Test Examples

```python
# tests/security/test_access_control.py
@pytest.mark.security
def test_user_cannot_read_other_users_conversions(api_client, db_session):
    """User B cannot GET User A's conversions."""
    # Create User A's conversion
    user_a = User(id="user-a")
    db_session.add(user_a)
    db_session.commit()
    
    conversion_a = Conversion(user_id="user-a", file_id="file1", format="xlsx")
    db_session.add(conversion_a)
    db_session.commit()
    
    # Try to access as User B
    # (api_client is logged in as test-user)
    response = api_client.get(f"/v1/conversions/{conversion_a.id}")
    
    assert response.status_code == 403
    assert "Forbidden" in response.text

# tests/security/test_injection.py
@pytest.mark.security
def test_csv_formula_injection_prevention(api_client, db_session):
    """Formulas in PDF are escaped to text in CSV output."""
    # Create a PDF with cell text "=cmd|'/c calc'!A1"
    # Export to CSV
    # Verify it's prefixed with ' (text marker)
    pass

# tests/security/test_resource_limits.py
@pytest.mark.security
def test_task_timeout_on_slow_pdf(db_session):
    """PDF that takes >60 seconds per page is killed."""
    # Create a specially crafted PDF that causes infinite loop
    # Ensure task is marked as failed/timeout, not hung
    pass
```

---

## File Organization & Project Structure

```
pdf_converter/
├── README.md                           # Quick start, feature overview
├── CLAUDE.md                           # THIS FILE
├── PLAN_APP_CONVERSION_PDF_v1.0.md     # Complete project plan
├── Makefile                            # Common commands (run, test, format, etc.)
├── pyproject.toml                      # Package metadata, tool config
├── requirements.txt                    # Production dependencies
├── requirements-dev.txt                # Testing, linting, debugging tools
├── pytest.ini                          # Pytest configuration
├── .env.example                        # Environment template (no secrets)
│
├── apps/
│   ├── api/                            # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app, middleware, exception handlers
│   │   ├── config.py                   # Pydantic Settings (environment validation)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py             # SQLAlchemy Base, all ORM models
│   │   │   ├── user.py                 # User, Organization models
│   │   │   ├── conversion.py           # Conversion, ConversionAttempt, Artifact
│   │   │   ├── storage.py              # UploadedFile, StorageMetadata
│   │   │   └── events.py               # OutboxEvent for durable publishing
│   │   ├── schemas/                    # Pydantic models for request/response
│   │   │   ├── __init__.py
│   │   │   ├── conversion.py           # ConversionRequest, ConversionResponse
│   │   │   ├── file.py                 # FileUploadResponse, FileInfoResponse
│   │   │   ├── export.py               # ExportOptions, ExportFormats
│   │   │   └── errors.py               # ErrorDetail, ValidationError
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── files.py                # POST /v1/files, file upload logic
│   │   │   ├── conversions.py          # POST/GET /v1/conversions, status
│   │   │   ├── artifacts.py            # GET /v1/artifacts/{id}/download
│   │   │   └── health.py               # GET /health, readiness checks
│   │   ├── dependencies.py             # Shared dependencies (get_current_user, etc.)
│   │   ├── middleware.py               # CORS, security headers, request logging
│   │   └── exceptions.py               # Custom exception classes
│   │
│   └── worker/                         # Celery tasks and orchestration
│       ├── __init__.py
│       ├── celery_app.py               # Celery app instance and config
│       ├── tasks.py                    # @shared_task definitions (convert_pdf_to_format, etc.)
│       ├── config.py                   # Celery configuration, queue routing
│       ├── monitoring.py               # Task event listeners, health checks
│       └── cleanup.py                  # TTL cleanup, orphan detection
│
├── packages/
│   ├── document_ir/                    # Intermediate representation (shared across API/worker)
│   │   ├── __init__.py
│   │   ├── models.py                   # DocumentIR, Page, TextBlock, Table, Cell, Image, ContentWarning
│   │   ├── validators.py               # Custom Pydantic validators, region-aware parsing
│   │   └── serializers.py              # JSON/pickle serialization for storage
│   │
│   ├── converters/                     # PDF extraction engines (adapters)
│   │   ├── __init__.py
│   │   ├── base.py                     # PdfExtractor abstract base class
│   │   ├── pdfplumber_extractor.py     # Implementation for pdfplumber
│   │   ├── docling_extractor.py        # Implementation for Docling (if F0 passed)
│   │   ├── camelot_extractor.py        # Implementation for Camelot (if F0 passed)
│   │   ├── table_detection.py          # Shared table detection heuristics
│   │   ├── ocr/
│   │   │   ├── tesseract_ocr.py        # Tesseract OCR wrapper
│   │   │   ├── ocrmypdf_preprocessor.py  # OCRmyPDF pipeline
│   │   │   └── image_prep.py           # Deskew, orient, denoise utilities
│   │   └── router.py                   # Engine selection logic (pdfplumber default, Docling fallback)
│   │
│   ├── exporters/                      # Format-specific exporters (implementations)
│   │   ├── __init__.py
│   │   ├── base.py                     # FormatExporter abstract base class
│   │   ├── xlsx_exporter.py            # Excel (.xlsx) export with openpyxl
│   │   ├── docx_exporter.py            # Word (.docx) export with python-docx
│   │   ├── csv_exporter.py             # CSV export (per-table, UTF-8, injection prevention)
│   │   ├── txt_exporter.py             # Plain text export (reading order)
│   │   ├── md_exporter.py              # Markdown export (tables, headers, images)
│   │   ├── json_exporter.py            # Structured JSON (DocumentIR serialization)
│   │   └── image_exporter.py           # PNG/JPEG per page (with DPI limits)
│   │
│   └── common/                         # Shared utilities
│       ├── __init__.py
│       ├── enums.py                    # ConversionStatus, OutputFormat, PageClass
│       ├── exceptions.py               # TemporaryError, PermanentError, ValidationError
│       ├── types.py                    # Type aliases (FileId, ConversionId, UserId)
│       ├── storage.py                  # S3Client wrapper, file I/O
│       └── telemetry.py                # Prometheus metrics, structured logging helpers
│
├── tests/
│   ├── conftest.py                     # Pytest fixtures, DB setup, mocks
│   ├── fixtures/
│   │   ├── samples/
│   │   │   ├── digital_simple.pdf      # 5 pages, tables, text (for F0)
│   │   │   ├── scanned_clean.pdf       # 10 pages, OCR-ready (for F0)
│   │   │   ├── mixed.pdf               # Digital + scanned pages
│   │   │   └── adversarial/
│   │   │       ├── corrupted.pdf
│   │   │       ├── encrypted.pdf
│   │   │       ├── huge.pdf            # 1000+ pages or >25 MB
│   │   │       └── formula_injection.pdf  # Contains =1+1 in cells
│   │   └── expected_outputs/           # Ground truth (xlsx, docx, etc.)
│   │
│   ├── unit/
│   │   ├── test_converters.py          # pdfplumber, table detection, OCR
│   │   ├── test_exporters.py           # XLSX types, DOCX structure, CSV injection
│   │   ├── test_models.py              # Pydantic models, DocumentIR validation
│   │   ├── test_validators.py          # Region-aware date/number parsing
│   │   └── test_common.py              # Enums, exceptions, utilities
│   │
│   ├── integration/
│   │   ├── test_database.py            # SQLAlchemy ORM, migrations, transactions
│   │   ├── test_worker.py              # Celery task execution, retries, idempotence
│   │   ├── test_storage.py             # S3 mock, artifact lifecycle
│   │   ├── test_api_routes.py          # Endpoint integration, auth, validation
│   │   └── test_outbox.py              # Event publishing, reconciliation
│   │
│   ├── e2e/
│   │   ├── test_pdf_to_xlsx.py         # Upload → Convert → Download XLSX
│   │   ├── test_pdf_to_docx.py         # Upload → Convert → Download DOCX (editability check)
│   │   ├── test_error_paths.py         # Corrupted PDFs, unsupported formats, quota exceeded
│   │   └── test_cancellation.py        # Cancel mid-conversion, verify cleanup
│   │
│   └── security/
│       ├── test_access_control.py      # User/org isolation, forbidden conversions
│       ├── test_injection.py           # CSV/XLSX formula injection, traversal
│       ├── test_resource_limits.py     # Timeouts, memory bombs, pixel limits
│       └── test_sensitive_leaks.py     # No content in logs/errors, no passwords stored
│
├── benchmarks/
│   ├── conftest.py
│   ├── benchmark_extraction.py         # pdfplumber, Docling, Camelot speed on corpus
│   └── benchmark_export.py             # XLSX, DOCX, CSV generation speed
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api              # FastAPI server
│   │   ├── Dockerfile.worker           # Celery worker (with OCR, models pre-installed)
│   │   └── Dockerfile.base             # Common base (Python 3.11, system deps)
│   │
│   ├── compose/
│   │   └── docker-compose.yml          # Local dev stack (API, worker, DB, broker, storage)
│   │
│   ├── kubernetes/                     # K8s manifests (future; not MVP)
│   │   ├── deployment.yml
│   │   ├── service.yml
│   │   └── configmap.yml
│   │
│   └── scripts/
│       ├── migrate.sh                  # Run alembic upgrade
│       ├── seed.sh                     # Populate test data
│       ├── health_check.sh             # Readiness probe
│       └── backup.sh                   # Object store export (operational)
│
├── docs/
│   ├── README.md                       # Documentation index
│   ├── ARQUITECTURA.md                 # System design, diagrams, data flow
│   ├── ALCANCE.md                      # Features, formats, limitations, F0 gate criteria
│   ├── SEGURIDAD.md                    # Security model, OWASP compliance, threat analysis
│   ├── CALIDAD.md                      # Quality gates, metrics, testing strategy
│   ├── LICENCIAS.md                    # SBOM (dependencies, versions, licenses), legal analysis
│   ├── RUNBOOK.md                      # Operational procedures (deploy, rollback, incident response)
│   ├── AVANCE.md                       # Progress tracking (phases, blockers, decisions)
│   │
│   └── adr/                            # Architecture Decision Records
│       ├── 0001-fastapi-framework-choice.md
│       ├── 0002-celery-over-asyncio.md
│       ├── 0003-documentir-schema.md
│       ├── 0004-pdfplumber-primary-extractor.md
│       └── 0005-outbox-pattern-for-events.md
│
├── docker-compose.yml                  # Development stack orchestration
├── Makefile                            # Common commands
├── README.md                           # Project overview, quick start
└── .gitignore
```

---

## Phased Development (Reference)

Each phase has a specific gate that must pass before proceeding. Do not skip gates.

| Phase | Duration | Focus | Gate Criteria |
|-------|----------|-------|---------------|
| **F0** | 1-2 weeks | Corpus, motor comparison, viability | Measurable F1 quality (F1 >=0.95), viable cost model |
| **F1** | 1 week | API, database, auth, TXT end-to-end | Carga a descarga com permissões, recuperação básica |
| **F2** | 2 weeks | XLSX/CSV extraction, table correction UI | Validação de tipos, testes de injeção, interface |
| **F3** | 2 weeks | DOCX structure, images, editability | Abertura, edição, e re-save sem corrupção |
| **F4** | 1-2 weeks | OCR (Tesseract), scanned PDFs, rotation | CER <= 2%, dados críticos 100% digitais, sem duplicação |
| **F5** | 1 week | MD, JSON, PNG/JPEG, limited batches | Limites, procedência, compactação segura |
| **F6** | 2-3 weeks | Hardening, observability, pilot | Ensaios de carga, falha e recuperação, runbook atualizado |

---

## Security Essentials

### OWASP Top 10 Mapping

| OWASP | Mitigation | Location |
|-------|-----------|----------|
| A01: Injection | Parameterized SQL, formula escaping in CSV/XLSX | `apps/exporters/`, `tests/security/` |
| A02: Broken Auth | JWT tokens, CSRF/SameSite, HttpOnly cookies | `apps/api/dependencies.py` |
| A03: Broken Access | Per-tenant DB queries, ownership checks | `check_conversion_ownership()` |
| A04: Insecure Design | Isolation in worker, resource limits, TLS | `docker-compose.yml`, `infra/docker/` |
| A05: Security Misc. | Secure headers (CSP, X-Frame-Options), versioned dependencies | `apps/api/middleware.py` |
| A06: Vulnerable Components | Pinned versions, pre-commit hookss, periodic audits | `requirements.txt`, CI/CD |
| A07: Auth Bypass | Token rotation, rate limiting per user | `apps/api/middleware.py` |
| A08: Data Integrity | Atomic transaction + outbox, version tokens | `apps/api/routes/`, `apps/worker/` |
| A09: Logging/Monitoring | Structured logs, no content, request tracing | `apps/api/middleware.py`, `packages/common/telemetry.py` |
| A10: SSRF | No URL upload in MVP, internal service list | `PLAN_APP_CONVERSION_PDF_v1.0.md` §14 |

### Critical Checklist

- [ ] No user content in logs (file text, cell data, OCR output)
- [ ] Passwords never logged or persisted
- [ ] PDF parsing happens in isolated worker process only
- [ ] Resource limits enforced (CPU, memory, disk, pixels, timeout)
- [ ] File I/O uses server-generated names (UUIDs), never user input
- [ ] Formula injection prevented in CSV/XLSX (leading = escaped)
- [ ] Database queries parameterized (SQLAlchemy ORM)
- [ ] CORS explicit; not `*`
- [ ] CSRF protection on state-changing endpoints
- [ ] TLS for all network communication (AMQP, S3, DB connections)
- [ ] Sensitive data (passwords, API keys) in env vars or external vault, never hardcoded
- [ ] Artifact cleanup verified (no orphans, TTL enforced)
- [ ] User isolation tested (A cannot read B's data)
- [ ] Access logs record user_id, resource, timestamp, result (not content)

---

## When Stuck: Debugging & Troubleshooting

### 1. Enable Verbose Logging

```bash
# Set in .env
LOG_LEVEL=DEBUG
SQLALCHEMY_ECHO=true
CELERY_LOG_LEVEL=DEBUG

# Restart services
docker-compose restart api worker
docker-compose logs -f
```

### 2. Inspect Active Tasks

```bash
# List running Celery tasks
celery -A apps.worker inspect active

# Show task history
celery -A apps.worker inspect registered
```

### 3. Database Inspection

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d pdf_converter

# Common queries
SELECT * FROM conversions WHERE status = 'failed';
SELECT * FROM conversion_attempts WHERE status != 'succeeded';
SELECT * FROM outbox_events WHERE published_at IS NULL;
```

### 4. Worker Logs

```bash
# Real-time worker log
docker-compose logs -f worker

# Specific task error
celery -A apps.worker inspect reserved  # Stuck tasks
```

### 5. PDF Inspection

```bash
# System utilities (if available)
pdfinfo <file>
pdftotext <file>  # Extract text
pdfimages <file>  # Extract images
```

### 6. Memory Profiling

```bash
# In test or task
from memory_profiler import profile

@profile
def convert_pdf_to_format(...):
    ...

# Run with memory_profiler
mprof run pytest tests/unit/test_converters.py
mprof plot  # Generate graph
```

### 7. Performance Bottleneck

```bash
# Benchmark a single conversion
pytest benchmarks/benchmark_extraction.py -v

# Profile a specific function
python -m cProfile -s cumulative -m pytest tests/unit/test_converters.py
```

---

## Key References

| Document | Purpose |
|----------|---------|
| [PLAN_APP_CONVERSION_PDF_v1.0.md](./PLAN_APP_CONVERSION_PDF_v1.0.md) | Complete project requirements, constraints, risk analysis |
| [docs/AVANCE.md](./docs/AVANCE.md) | Progress tracking, current blockers, team notes |
| [docs/ARQUITECTURA.md](./docs/ARQUITECTURA.md) | System diagrams, data models, API contracts |
| [docs/SEGURIDAD.md](./docs/SEGURIDAD.md) | Security model, OWASP compliance, threat model |
| [docs/CALIDAD.md](./docs/CALIDAD.md) | Quality gates, metrics, test coverage targets |
| [docs/adr/](./docs/adr/) | Architecture decisions (motor choice, outbox pattern, etc.) |

---

## Questions? Start Here

1. **High-level design**: Read [PLAN_APP_CONVERSION_PDF_v1.0.md](./PLAN_APP_CONVERSION_PDF_v1.0.md) §1-8 (Objective, assumptions, frameworks, scope)
2. **API contracts**: Check [docs/ARQUITECTURA.md](./docs/ARQUITECTURA.md) and OpenAPI schema (`/docs` endpoint)
3. **Testing**: Review [Testing Strategy](#testing-strategy) section above and examples
4. **Security concerns**: See [Security & OWASP Compliance](#security--owasp-compliance) and [docs/SEGURIDAD.md](./docs/SEGURIDAD.md)
5. **Progress**: Check [docs/AVANCE.md](./docs/AVANCE.md) for current phase and blockers
6. **Past decisions**: Browse [docs/adr/](./docs/adr/) for context

---

## Notes for AI Development

- **Read before coding**: Plan (§1-15), current phase gate criteria, ADRs, and progress (AVANCE.md)
- **Inspect before assuming**: Always run `make test` and `docker-compose logs` to verify current state
- **Update progress**: At end of session, commit to git and update [docs/AVANCE.md](./docs/AVANCE.md) with verified next steps
- **Preserve constraints**: No LLM in base flow; no automatic corrections; always flag uncertainty and preserve original
- **Security first**: Isolation, timeouts, type checking, tested error paths before features
- **Document decisions**: Create ADR for significant choices; link from code comments

---

**Last updated**: 2026-10-07  
**Version**: 1.0  
**Audience**: Development team, AI agents, technical reviewers
