"""
Main Excel generator module for Bitrix24 report generation.

Combines styles, layout, and formatting to create complete Excel reports
that exactly match the provided visual requirements.
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from .styles import ExcelStyles, ColumnStyleConfig
from .layout import WorksheetBuilder, ReportLayout
from .formatter import ExcelDataFormatter, ExcelSummaryFormatter, DataValidator


class ExcelReportGenerator:
    """
    Main Excel report generator.
    
    Creates complete Excel reports with proper formatting, styling,
    and layout that matches the visual requirements.
    """
    
    def __init__(self):
        self.styles = ExcelStyles()
        self.layout = ReportLayout()
        self.worksheet_builder = WorksheetBuilder()
        self.data_formatter = ExcelDataFormatter()
        self.summary_formatter = ExcelSummaryFormatter()
        self.validator = DataValidator()
    
    def generate_report(self, data: List[Dict[str, Any]], 
                       output_path: str, 
                       sheet_name: str = "Отчёт") -> str:
        """
        Generate complete Excel report.
        
        Args:
            data: List of invoice data dictionaries
            output_path: Path where to save the Excel file
            sheet_name: Name for the Excel sheet
            
        Returns:
            Path to the generated Excel file
        """
        # Validate input data
        validated_data = []
        for invoice in data:
            validated_invoice = self.validator.validate_invoice_data(invoice)
            validated_data.append(validated_invoice)
        
        # Format data for Excel
        formatted_data = self.data_formatter.format_invoice_data(validated_data)
        
        # Validate formatted data
        if not self.validator.validate_formatted_data(formatted_data):
            raise ValueError("Formatted data failed validation")
        
        # Create workbook and worksheet
        workbook = Workbook()
        worksheet = self.worksheet_builder.create_worksheet(workbook, sheet_name)
        
        # Write data to worksheet
        self._write_data_to_worksheet(worksheet, formatted_data)
        
        # Apply styling
        self._apply_styling(worksheet, formatted_data)
        
        # Add summary section
        summary_data = self.summary_formatter.format_summary(formatted_data)
        self._add_summary_section(worksheet, len(formatted_data), summary_data)
        
        # Save workbook
        output_path = self._ensure_xlsx_extension(output_path)
        self._ensure_output_directory(output_path)
        workbook.save(output_path)
        
        return output_path
    
    def _write_data_to_worksheet(self, worksheet: Worksheet, 
                                data: List[Dict[str, Any]]) -> None:
        """
        Write formatted data to the worksheet.
        
        Args:
            worksheet: OpenPyXL worksheet object
            data: List of formatted data dictionaries
        """
        for row_index, row_data in enumerate(data):
            for col_index, column in enumerate(self.layout.COLUMNS):
                excel_row, excel_col = self.layout.get_data_cell_position(row_index, col_index)
                
                # Get cell and set value
                cell = worksheet.cell(row=excel_row, column=excel_col)
                cell_value = row_data.get(column.data_key, '')
                cell.value = cell_value
    
    def _apply_styling(self, worksheet: Worksheet, 
                      data: List[Dict[str, Any]]) -> None:
        """
        Apply visual styling to the worksheet.
        
        Args:
            worksheet: OpenPyXL worksheet object
            data: List of formatted data dictionaries for styling decisions
        """
        # Style headers
        self._style_headers(worksheet)
        
        # Style data rows
        self._style_data_rows(worksheet, data)
    
    def _style_headers(self, worksheet: Worksheet) -> None:
        """
        Apply header styling.
        
        Args:
            worksheet: OpenPyXL worksheet object
        """
        header_style = self.styles.get_header_style()
        
        for col_index, column in enumerate(self.layout.COLUMNS):
            header_col = self.layout.START_COLUMN + col_index
            header_cell = worksheet.cell(row=self.layout.HEADER_ROW, column=header_col)
            self.styles.apply_style_to_cell(header_cell, header_style)
    
    def _style_data_rows(self, worksheet: Worksheet, 
                        data: List[Dict[str, Any]]) -> None:
        """
        Apply data row styling.
        
        Args:
            worksheet: OpenPyXL worksheet object
            data: List of formatted data dictionaries
        """
        for row_index, row_data in enumerate(data):
            is_no_vat = row_data.get('is_no_vat', False)
            
            for col_index, column in enumerate(self.layout.COLUMNS):
                excel_row, excel_col = self.layout.get_data_cell_position(row_index, col_index)
                cell = worksheet.cell(row=excel_row, column=excel_col)
                
                # Get appropriate styling
                alignment = column.alignment
                data_style = self.styles.get_data_style(
                    is_no_vat=is_no_vat,
                    alignment_type=alignment
                )
                
                # Apply style to cell
                self.styles.apply_style_to_cell(cell, data_style)
    
    def _add_summary_section(self, worksheet: Worksheet, 
                            data_row_count: int,
                            summary_data: Dict[str, Any]) -> None:
        """
        Add summary section to the worksheet.
        
        Args:
            worksheet: OpenPyXL worksheet object
            data_row_count: Number of data rows
            summary_data: Summary statistics
        """
        # Calculate summary start row
        summary_start_row = self.layout.DATA_START_ROW + data_row_count + 2
        
        # Add record count
        count_cell = worksheet.cell(row=summary_start_row, column=self.layout.START_COLUMN)
        count_cell.value = "Всего записей:"
        count_value_cell = worksheet.cell(row=summary_start_row, column=self.layout.START_COLUMN + 1)
        count_value_cell.value = summary_data['record_count']
        
        # Add total without VAT
        if 'total_without_vat' in summary_data:
            without_vat_row = summary_start_row + 1
            without_vat_cell = worksheet.cell(row=without_vat_row, column=self.layout.START_COLUMN)
            without_vat_cell.value = "Общая сумма без НДС:"
            without_vat_value_cell = worksheet.cell(
                row=without_vat_row, 
                column=self.layout.START_COLUMN + 4
            )
            without_vat_value_cell.value = summary_data['total_without_vat']
        
        # Add total with VAT
        if 'total_with_vat' in summary_data:
            with_vat_row = summary_start_row + 2
            with_vat_cell = worksheet.cell(row=with_vat_row, column=self.layout.START_COLUMN)
            with_vat_cell.value = "Общая сумма с НДС:"
            with_vat_value_cell = worksheet.cell(
                row=with_vat_row, 
                column=self.layout.START_COLUMN + 6
            )
            with_vat_value_cell.value = summary_data['total_with_vat']
        
        # Apply basic styling to summary section
        summary_style = self.styles.get_data_style(is_no_vat=False, alignment_type='left')
        for row in range(summary_start_row, summary_start_row + 3):
            for col in range(self.layout.START_COLUMN, self.layout.START_COLUMN + 7):
                cell = worksheet.cell(row=row, column=col)
                if cell.value:  # Only style cells with content
                    self.styles.apply_style_to_cell(cell, summary_style)
    
    def _ensure_xlsx_extension(self, file_path: str) -> str:
        """
        Ensure the file path has .xlsx extension.
        
        Args:
            file_path: Original file path
            
        Returns:
            File path with .xlsx extension
        """
        path = Path(file_path)
        if path.suffix.lower() != '.xlsx':
            return str(path.with_suffix('.xlsx'))
        return file_path
    
    def _ensure_output_directory(self, file_path: str) -> None:
        """
        Ensure the output directory exists.
        
        Args:
            file_path: Path to the output file
        """
        output_dir = Path(file_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)


class ReportGenerationError(Exception):
    """Custom exception for report generation errors."""
    pass


class ExcelReportBuilder:
    """
    High-level builder interface for Excel reports.
    
    Provides a convenient API for creating reports with different configurations.
    """
    
    def __init__(self):
        self.generator = ExcelReportGenerator()
    
    def build_invoice_report(self, invoices: List[Dict[str, Any]], 
                           output_path: str,
                           report_title: str = "Отчёт по счетам") -> str:
        """
        Build an invoice report.
        
        Args:
            invoices: List of invoice data
            output_path: Where to save the report
            report_title: Title for the report sheet
            
        Returns:
            Path to the generated report
        """
        try:
            return self.generator.generate_report(
                data=invoices,
                output_path=output_path,
                sheet_name=report_title
            )
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate invoice report: {e}")
    
    def build_summary_report(self, invoices: List[Dict[str, Any]], 
                           output_path: str) -> Dict[str, Any]:
        """
        Build a summary report with statistics only.
        
        Args:
            invoices: List of invoice data
            output_path: Where to save the report
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            # Format data
            formatted_data = self.generator.data_formatter.format_invoice_data(invoices)
            
            # Generate summary
            summary = self.generator.summary_formatter.format_summary(formatted_data)
            
            # Generate Excel file
            self.generator.generate_report(
                data=invoices,
                output_path=output_path,
                sheet_name="Сводка"
            )
            
            return summary
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate summary report: {e}")
    
    def validate_data_for_report(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate data before report generation.
        
        Args:
            data: List of data to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'total_records': len(data),
            'valid_records': 0,
            'invalid_records': 0,
            'errors': []
        }
        
        for i, record in enumerate(data):
            try:
                # Validate record
                validated = self.generator.validator.validate_invoice_data(record)
                
                # Try formatting
                formatted = self.generator.data_formatter._format_single_invoice(validated, i + 1)
                
                results['valid_records'] += 1
                
            except Exception as e:
                results['invalid_records'] += 1
                results['errors'].append(f"Record {i + 1}: {str(e)}")
                results['is_valid'] = False
        
        return results 