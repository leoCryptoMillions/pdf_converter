"""
Shared pytest fixtures and configuration for PDF Converter tests.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

import pytest
from unittest.mock import MagicMock, Mock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Environment and Configuration
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Get test data directory"""
    data_dir = PROJECT_ROOT / "tests" / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["DEBUG"] = "True"
    yield
    # Cleanup
    if os.path.exists("test.db"):
        os.remove("test.db")


# ============================================================================
# Document IR Fixtures
# ============================================================================

@pytest.fixture
def sample_rectangle():
    """Create sample rectangle for testing"""
    from packages.document_ir.models import Rectangle
    return Rectangle(x0=10, y0=20, x1=100, y1=200)


@pytest.fixture
def sample_cell(sample_rectangle):
    """Create sample table cell"""
    from packages.document_ir.models import Cell, DataType, ExtractionMethod
    return Cell(
        content="123.45",
        normalized_value=123.45,
        data_type=DataType.DECIMAL,
        row_index=0,
        col_index=0,
        extraction_method=ExtractionMethod.DIRECT,
        original_source=sample_rectangle,
        confidence=0.99,
    )


@pytest.fixture
def sample_table(sample_rectangle, sample_cell):
    """Create sample table with cells"""
    from packages.document_ir.models import Table, ExtractionMethod
    return Table(
        id="table_1",
        title="Sample Table",
        page_number=1,
        location=sample_rectangle,
        rows=5,
        columns=3,
        cells=[sample_cell],
        has_header=True,
        extraction_method=ExtractionMethod.DIRECT,
        source_engine="pdfplumber",
        confidence=0.95,
    )


@pytest.fixture
def sample_page(sample_rectangle, sample_table):
    """Create sample document page"""
    from packages.document_ir.models import (
        Page,
        PageClassification,
        ExtractionMethod,
    )
    return Page(
        page_number=1,
        width=612,
        height=792,
        classification=PageClassification.DIGITAL,
        text_coverage=0.75,
        image_coverage=0.20,
        extracted_text="Sample page text",
        tables=[sample_table],
        extraction_method=ExtractionMethod.DIRECT,
    )


@pytest.fixture
def sample_document_ir(sample_page):
    """Create sample document IR"""
    from packages.document_ir.models import DocumentIR, EngineConfig
    return DocumentIR(
        schema_version="1.0.0",
        document_id="doc_test_001",
        source_filename="sample.pdf",
        source_hash="abc123def456",
        page_count=1,
        pages=[sample_page],
        engines_used=[
            EngineConfig(
                engine_name="pdfplumber",
                engine_version="0.10.3",
            )
        ],
        has_meaningful_content=True,
        ocr_enabled=False,
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_pdf_parser():
    """Mock PDF parser"""
    parser = MagicMock()
    parser.extract_text = MagicMock(return_value="Mock PDF text")
    parser.extract_tables = MagicMock(return_value=[])
    parser.get_page_count = MagicMock(return_value=10)
    return parser


@pytest.fixture
def mock_ocr_engine():
    """Mock OCR engine"""
    engine = MagicMock()
    engine.extract_text = MagicMock(return_value="Extracted text via OCR")
    engine.get_confidence = MagicMock(return_value=0.92)
    return engine


@pytest.fixture
def mock_storage():
    """Mock file storage backend"""
    storage = MagicMock()
    storage.upload = MagicMock(return_value="s3://bucket/file_key")
    storage.download = MagicMock(return_value=b"file content")
    storage.delete = MagicMock(return_value=True)
    return storage


@pytest.fixture
def mock_database():
    """Mock database connection"""
    db = MagicMock()
    db.save = MagicMock(return_value=True)
    db.query = MagicMock()
    db.delete = MagicMock(return_value=True)
    return db


@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    task = MagicMock()
    task.delay = MagicMock(return_value=MagicMock(id="task_123"))
    task.apply_async = MagicMock(return_value=MagicMock(id="task_456"))
    return task


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Sample conversion job data"""
    return {
        "job_id": "job_001",
        "user_id": "user_123",
        "document_filename": "sample.pdf",
        "target_format": "xlsx",
        "status": "queued",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24),
    }


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data"""
    return {
        "user_id": "user_123",
        "email": "test@example.com",
        "organization_id": "org_001",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_organization_data() -> Dict[str, Any]:
    """Sample organization data"""
    return {
        "organization_id": "org_001",
        "name": "Test Organization",
        "max_file_size_mb": 25,
        "max_pages_per_job": 100,
        "retention_hours": 24,
    }


# ============================================================================
# Temporary File Fixtures
# ============================================================================

@pytest.fixture
def tmp_pdf_file(tmp_path):
    """Create temporary PDF file for testing"""
    pdf_file = tmp_path / "sample.pdf"
    # Create minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
214
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    return pdf_file


@pytest.fixture
def tmp_storage_dir(tmp_path):
    """Create temporary storage directory"""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    return storage_dir


# ============================================================================
# Parametrize Fixtures
# ============================================================================

@pytest.fixture(
    params=[
        ("digital", 0.85),
        ("scanned", 0.65),
        ("mixed", 0.75),
    ],
    ids=["digital", "scanned", "mixed"],
)
def page_types_and_coverage(request):
    """Parametrized fixture for different page types"""
    page_type, coverage = request.param
    return page_type, coverage


# ============================================================================
# Autouse Fixtures for Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """Cleanup temporary files after each test"""
    yield
    # Cleanup happens automatically with tmp_path


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests"""
    yield
    MagicMock().reset_mock()


# ============================================================================
# Helper Functions for Tests
# ============================================================================

def create_test_document_ir_with_pages(num_pages: int = 5):
    """Factory function to create DocumentIR with multiple pages"""
    from packages.document_ir.models import DocumentIR, Page, EngineConfig

    pages = []
    for i in range(1, num_pages + 1):
        page = Page(
            page_number=i,
            width=612,
            height=792,
            classification="digital",
            text_coverage=0.75,
            image_coverage=0.20,
            extracted_text=f"Text from page {i}",
        )
        pages.append(page)

    return DocumentIR(
        schema_version="1.0.0",
        document_id=f"doc_test_{num_pages}pages",
        source_filename="multi_page.pdf",
        source_hash="test_hash",
        page_count=num_pages,
        pages=pages,
        engines_used=[
            EngineConfig(
                engine_name="pdfplumber",
                engine_version="0.10.3",
            )
        ],
        has_meaningful_content=True,
    )


def create_test_table(
    rows: int = 5,
    cols: int = 3,
    with_header: bool = True,
):
    """Factory function to create test table"""
    from packages.document_ir.models import Table, Cell, Rectangle, DataType, ExtractionMethod

    cells = []
    for row in range(rows):
        for col in range(cols):
            cell = Cell(
                content=f"Cell_{row}_{col}",
                data_type=DataType.TEXT,
                row_index=row,
                col_index=col,
                extraction_method=ExtractionMethod.DIRECT,
                confidence=0.99,
            )
            cells.append(cell)

    return Table(
        id="test_table",
        page_number=1,
        location=Rectangle(x0=0, y0=0, x1=500, y1=500),
        rows=rows,
        columns=cols,
        cells=cells,
        has_header=with_header,
        extraction_method=ExtractionMethod.DIRECT,
        source_engine="pdfplumber",
    )


# ============================================================================
# Pytest Hooks for Reporting
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add markers based on test path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)


def pytest_configure(config):
    """Custom pytest configuration"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
