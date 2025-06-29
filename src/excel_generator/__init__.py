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

# Export all public classes
__all__ = [
    # Main generator classes
    'ExcelReportGenerator',
    'ExcelReportBuilder', 
    'ReportGenerationError',
    
    # Styling classes
    'ExcelStyles',
    'ColorScheme',
    'ColumnStyleConfig',
    
    # Layout classes
    'ReportLayout',
    'SummaryLayout',
    'WorksheetBuilder',
    'ColumnDefinition',
    
    # Formatting classes
    'ExcelDataFormatter',
    'ExcelSummaryFormatter',
    'DataValidator'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Bitrix24 Report Generator'
__description__ = 'Excel report generator with visual formatting for Bitrix24 data' 