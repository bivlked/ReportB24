"""
Excel generator module for Bitrix24 report generation.

This module provides comprehensive Excel report generation capabilities
with visual formatting that exactly matches the provided screenshots.

Main classes:
- ExcelReportGenerator: Core report generation engine
- ExcelReportBuilder: High-level builder interface
- ExcelStyles: Visual styling and formatting
- ReportLayout: Report structure and layout
- ExcelDataFormatter: Data formatting for Excel output
"""

# Main generator classes
from .generator import ExcelReportGenerator, ExcelReportBuilder, ReportGenerationError

# Styling components
from .styles import ExcelStyles, ColorScheme, ColumnStyleConfig

# Layout components
from .layout import ReportLayout, SummaryLayout, WorksheetBuilder, ColumnDefinition

# Formatting components
from .formatter import ExcelDataFormatter, ExcelSummaryFormatter, DataValidator

# Validation components (v2.5.0)
from .validation import (
    DataQualityValidator,
    ValidationIssue,
    ValidationResult,
    QualityMetrics,
    ComprehensiveReportResult,
)

# Console UI components (v2.5.0)
from .console_ui import ConsoleUI, Colors, Spinner, format_number, format_duration

# Export all public classes
__all__ = [
    # Main generator classes
    "ExcelReportGenerator",
    "ExcelReportBuilder",
    "ReportGenerationError",
    # Styling classes
    "ExcelStyles",
    "ColorScheme",
    "ColumnStyleConfig",
    # Layout classes
    "ReportLayout",
    "SummaryLayout",
    "WorksheetBuilder",
    "ColumnDefinition",
    # Formatting classes
    "ExcelDataFormatter",
    "ExcelSummaryFormatter",
    "DataValidator",
    # Validation classes (v2.5.0)
    "DataQualityValidator",
    "ValidationIssue",
    "ValidationResult",
    "QualityMetrics",
    "ComprehensiveReportResult",
    # Console UI (v2.5.0)
    "ConsoleUI",
    "Colors",
    "Spinner",
    "format_number",
    "format_duration",
]

# Version information
__version__ = (
    "2.5.0"  # 🆕 Added validation, quality metrics, and colored console output
)
__author__ = "Bitrix24 Report Generator"
__description__ = "Excel report generator with visual formatting for Bitrix24 data"
