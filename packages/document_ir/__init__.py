"""
Document Intermediate Representation (IR) Package

Canonical schema and utilities for document representation across conversion engines.
"""

from .models import (
    DocumentIR,
    Page,
    Table,
    Cell,
    Image,
    TextBlock,
    TextRun,
    PositionedText,
    ContentWarning,
    DocumentMetadata,
    EngineConfig,
    PageClassification,
    ExtractionMethod,
    DataType,
    ContentWarningLevel,
    Rectangle,
    Point,
    IRValidationResult,
)

__version__ = "1.1.0"
__all__ = [
    "DocumentIR",
    "Page",
    "Table",
    "Cell",
    "Image",
    "TextBlock",
    "TextRun",
    "PositionedText",
    "ContentWarning",
    "DocumentMetadata",
    "EngineConfig",
    "PageClassification",
    "ExtractionMethod",
    "DataType",
    "ContentWarningLevel",
    "Rectangle",
    "Point",
    "IRValidationResult",
]
