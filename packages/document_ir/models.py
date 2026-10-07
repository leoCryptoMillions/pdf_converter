"""
Document Intermediate Representation (IR) Models

Defines the canonical schema for document representation across all conversion engines.
This IR enables engine-agnostic extraction, validation, and export.

Schema Version: 1.0.0
Last Updated: 2026-10-07
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from pydantic import BaseModel, Field, validator


# ============================================================================
# Enums for Classification
# ============================================================================

class PageClassification(str, Enum):
    """Classification of page content type"""
    DIGITAL = "digital"      # Text extracted directly
    SCANNED = "scanned"      # OCR required
    MIXED = "mixed"          # Combination of digital and scanned


class ExtractionMethod(str, Enum):
    """How content was extracted"""
    DIRECT = "direct"        # Direct PDF text extraction
    OCR = "ocr"              # Optical Character Recognition
    HYBRID = "hybrid"        # Combined direct + OCR


class DataType(str, Enum):
    """Cell/value data type classification"""
    TEXT = "text"
    NUMBER = "number"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    IDENTIFIER = "identifier"  # RFC, CLABE, etc - preserve as text
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class ContentWarningLevel(str, Enum):
    """Severity levels for content warnings"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Coordinate and Geometry Models
# ============================================================================

class Point(BaseModel):
    """2D point in PDF coordinates"""
    x: float = Field(..., description="X coordinate (points)")
    y: float = Field(..., description="Y coordinate (points)")

    class Config:
        json_schema_extra = {
            "example": {"x": 100.5, "y": 200.25}
        }


class Rectangle(BaseModel):
    """Bounding box in PDF coordinates"""
    x0: float = Field(..., description="Left edge")
    y0: float = Field(..., description="Bottom edge")
    x1: float = Field(..., description="Right edge")
    y1: float = Field(..., description="Top edge")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    class Config:
        json_schema_extra = {
            "example": {"x0": 100, "y0": 200, "x1": 300, "y1": 400}
        }


# ============================================================================
# Content Block Models
# ============================================================================

class ContentWarning(BaseModel):
    """Warning about content extraction or quality"""
    level: ContentWarningLevel = Field(..., description="Warning severity")
    code: str = Field(..., description="Machine-readable code")
    message: str = Field(..., description="Human-readable message")
    page_number: int = Field(..., description="Page where issue occurred")
    location: Optional[Rectangle] = Field(None, description="Location on page")
    confidence: Optional[float] = Field(None, description="Confidence 0-1 if applicable")

    class Config:
        json_schema_extra = {
            "example": {
                "level": "warning",
                "code": "LOW_OCR_CONFIDENCE",
                "message": "OCR confidence below 0.85",
                "page_number": 3,
                "confidence": 0.72
            }
        }


class Cell(BaseModel):
    """Table cell with content and metadata"""
    content: str = Field(..., description="Cell text content")
    normalized_value: Optional[Any] = Field(None, description="Normalized/parsed value")
    data_type: DataType = Field(default=DataType.TEXT, description="Detected data type")

    row_index: int = Field(..., description="Row index in table")
    col_index: int = Field(..., description="Column index in table")
    row_span: int = Field(default=1, description="Rows spanned")
    col_span: int = Field(default=1, description="Columns spanned")

    extraction_method: ExtractionMethod = Field(..., description="How content was extracted")
    original_source: Optional[Rectangle] = Field(None, description="Location in PDF")

    confidence: Optional[float] = Field(None, description="Extraction confidence 0-1")
    warnings: List[ContentWarning] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "1,234.56",
                "normalized_value": Decimal("1234.56"),
                "data_type": "decimal",
                "row_index": 0,
                "col_index": 0,
                "extraction_method": "direct"
            }
        }


class Table(BaseModel):
    """Extracted table with structure and content"""
    id: str = Field(..., description="Unique table identifier")
    title: Optional[str] = Field(None, description="Table title if detected")
    page_number: int = Field(..., description="Page where table appears")
    location: Rectangle = Field(..., description="Table bounding box")

    rows: int = Field(..., description="Number of rows")
    columns: int = Field(..., description="Number of columns")
    cells: List[Cell] = Field(..., description="All cells in reading order")

    has_header: bool = Field(default=False, description="Has header row")
    header_rows: int = Field(default=0, description="Number of header rows")

    extraction_method: ExtractionMethod = Field(..., description="Primary extraction method")
    source_engine: str = Field(..., description="Engine that extracted table")

    multi_page: bool = Field(default=False, description="Table spans multiple pages")
    continuation_of: Optional[str] = Field(None, description="ID of previous table segment")

    confidence: Optional[float] = Field(None, description="Detection confidence 0-1")
    warnings: List[ContentWarning] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "table_1_p1",
                "title": "Financial Summary",
                "page_number": 1,
                "location": {"x0": 50, "y0": 100, "x1": 550, "y1": 400},
                "rows": 5,
                "columns": 3,
                "cells": [],
                "has_header": True,
                "extraction_method": "direct",
                "source_engine": "pdfplumber"
            }
        }


class Image(BaseModel):
    """Extracted image from PDF"""
    id: str = Field(..., description="Unique image identifier")
    page_number: int = Field(..., description="Source page")
    location: Rectangle = Field(..., description="Image location on page")

    format: str = Field(..., description="Image format (png, jpg, etc)")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    dpi: int = Field(default=300, description="Resolution in DPI")

    data_uri: Optional[str] = Field(None, description="Data URI for small images")
    external_ref: Optional[str] = Field(None, description="Reference to external storage")

    is_text_region: bool = Field(default=False, description="May contain text for OCR")
    extracted_text: Optional[str] = Field(None, description="OCR text if extracted")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "img_1_p1",
                "page_number": 1,
                "location": {"x0": 50, "y0": 500, "x1": 550, "y1": 650},
                "format": "jpeg",
                "width": 1200,
                "height": 400,
                "dpi": 300
            }
        }


class TextBlock(BaseModel):
    """Continuous text block (paragraph, heading, etc)"""
    id: str = Field(..., description="Unique block identifier")
    content: str = Field(..., description="Text content")
    page_number: int = Field(..., description="Source page")
    location: Rectangle = Field(..., description="Block bounding box")

    block_type: str = Field(default="paragraph", description="heading, paragraph, list, etc")
    reading_order: int = Field(..., description="Position in reading order")

    extraction_method: ExtractionMethod = Field(..., description="How extracted")
    is_vertical: bool = Field(default=False, description="Vertical text")
    rotation: int = Field(default=0, description="Text rotation 0/90/180/270")

    confidence: Optional[float] = Field(None, description="Extraction confidence")
    warnings: List[ContentWarning] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "block_1_p1",
                "content": "This is a paragraph of text.",
                "page_number": 1,
                "location": {"x0": 50, "y0": 600, "x1": 550, "y1": 650},
                "block_type": "paragraph",
                "reading_order": 1,
                "extraction_method": "direct"
            }
        }


# ============================================================================
# Page Model
# ============================================================================

class Page(BaseModel):
    """Single page from document"""
    page_number: int = Field(..., description="1-based page number")

    width: float = Field(..., description="Page width in points")
    height: float = Field(..., description="Page height in points")
    rotation: int = Field(default=0, description="Rotation 0/90/180/270")

    classification: PageClassification = Field(..., description="Page type")
    text_coverage: float = Field(..., description="Estimated text coverage 0-1")
    image_coverage: float = Field(..., description="Estimated image coverage 0-1")

    extracted_text: str = Field(default="", description="All text on page in order")
    blocks: List[TextBlock] = Field(default_factory=list, description="Text blocks")
    tables: List[Table] = Field(default_factory=list, description="Tables found")
    images: List[Image] = Field(default_factory=list, description="Images found")

    warnings: List[ContentWarning] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "page_number": 1,
                "width": 612,
                "height": 792,
                "classification": "digital",
                "text_coverage": 0.75,
                "image_coverage": 0.20,
                "extracted_text": "Page content here...",
                "blocks": [],
                "tables": [],
                "images": []
            }
        }


# ============================================================================
# Document Metadata
# ============================================================================

class DocumentMetadata(BaseModel):
    """Document metadata from PDF"""
    title: Optional[str] = Field(None)
    author: Optional[str] = Field(None)
    subject: Optional[str] = Field(None)
    keywords: Optional[str] = Field(None)
    creator: Optional[str] = Field(None)
    producer: Optional[str] = Field(None)
    creation_date: Optional[datetime] = Field(None)
    modification_date: Optional[datetime] = Field(None)
    encrypted: bool = Field(default=False)
    password_protected: bool = Field(default=False)
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class EngineConfig(BaseModel):
    """Configuration and version of extraction engine"""
    engine_name: str = Field(..., description="Engine name")
    engine_version: str = Field(..., description="Engine version")
    model_name: Optional[str] = Field(None, description="ML model if applicable")
    model_version: Optional[str] = Field(None)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Engine parameters")


# ============================================================================
# Main Document IR Model
# ============================================================================

class DocumentIR(BaseModel):
    """
    Intermediate Representation of a document.

    This schema is canonical across all conversion engines.
    It enables engine-agnostic extraction, validation, and export.
    """

    # Schema versioning
    schema_version: str = Field(default="1.0.0", description="IR schema version")

    # Document identification
    document_id: str = Field(..., description="Unique document identifier")
    source_filename: str = Field(..., description="Original filename")
    source_hash: str = Field(..., description="SHA256 of source PDF")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Document properties
    page_count: int = Field(..., description="Total pages")
    pages: List[Page] = Field(..., description="All pages")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    # Extraction configuration
    engines_used: List[EngineConfig] = Field(..., description="Engines that processed this")
    extraction_options: Dict[str, Any] = Field(default_factory=dict)

    # Overall quality metrics
    text_extraction_confidence: Optional[float] = Field(None, description="Average confidence 0-1")
    has_meaningful_content: bool = Field(default=True, description="Contains extractable data")

    # Processing information
    total_processing_time_seconds: Optional[float] = Field(None)
    ocr_enabled: bool = Field(default=False)
    ocr_languages: List[str] = Field(default_factory=list)

    # Warnings and issues
    warnings: List[ContentWarning] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Export tracking
    exported_formats: List[str] = Field(default_factory=list, description="Formats exported")
    export_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "title": "Document Intermediate Representation",
            "description": "Canonical document schema for all conversion engines"
        }

    @validator('schema_version')
    def validate_version(cls, v):
        """Validate schema version format"""
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Schema version must be semantic versioning (X.Y.Z)')
        return v

    def get_all_tables(self) -> List[Table]:
        """Get all tables from all pages"""
        tables = []
        for page in self.pages:
            tables.extend(page.tables)
        return tables

    def get_all_images(self) -> List[Image]:
        """Get all images from all pages"""
        images = []
        for page in self.pages:
            images.extend(page.images)
        return images

    def get_all_text(self) -> str:
        """Get all text in reading order"""
        texts = []
        for page in self.pages:
            texts.append(page.extracted_text)
        return '\n'.join(texts)

    def has_warnings(self) -> bool:
        """Check if document has any warnings"""
        if self.warnings:
            return True
        for page in self.pages:
            if page.warnings:
                return True
            for table in page.tables:
                if table.warnings:
                    return True
            for block in page.blocks:
                if block.warnings:
                    return True
        return False


# ============================================================================
# Export/Validation Models
# ============================================================================

class IRValidationResult(BaseModel):
    """Result of IR validation"""
    is_valid: bool = Field(..., description="Whether IR is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Document statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "stats": {
                    "page_count": 10,
                    "table_count": 5,
                    "image_count": 8,
                    "total_cells": 342
                }
            }
        }
