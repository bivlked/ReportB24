"""
Unit tests for main Excel generator module.

Tests complete Excel report generation workflow
combining all components.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from openpyxl import Workbook, load_workbook

from src.excel_generator.generator import (
    ExcelReportGenerator,
    ExcelReportBuilder,
    ReportGenerationError
)


class TestExcelReportGenerator:
    """Test main Excel report generator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ExcelReportGenerator()
    
    def test_generator_initialization(self):
        """Test ExcelReportGenerator initialization."""
        assert hasattr(self.generator, 'styles')
        assert hasattr(self.generator, 'layout')
        assert hasattr(self.generator, 'worksheet_builder')
        assert hasattr(self.generator, 'data_formatter')
        assert hasattr(self.generator, 'summary_formatter')
        assert hasattr(self.generator, 'validator')
    
    def test_generate_report_basic(self):
        """Test basic report generation."""
        test_data = [
            {
                'contractor_name': 'ООО "Тест"',
                'inn': '1234567890',
                'shipment_date': '15.06.2025',
                'invoice_number': 'ТСТ-001',
                'amount': 100000,
                'vat_rate': '20%'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'test_report.xlsx')
            
            result_path = self.generator.generate_report(test_data, output_path)
            
            # Test that file was created
            assert os.path.exists(result_path)
            assert result_path.endswith('.xlsx')
            
            # Test that file can be opened
            wb = load_workbook(result_path)
            assert len(wb.worksheets) == 1
            ws = wb.active
            assert ws.title == "Отчёт"
    
    def test_generate_report_custom_sheet_name(self):
        """Test report generation with custom sheet name."""
        test_data = [{'contractor_name': 'Test', 'amount': 1000}]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'custom_report.xlsx')
            
            result_path = self.generator.generate_report(
                test_data, output_path, sheet_name="Кастомный отчёт"
            )
            
            wb = load_workbook(result_path)
            ws = wb.active
            assert ws.title == "Кастомный отчёт"
    
    def test_ensure_xlsx_extension(self):
        """Test ensuring .xlsx extension."""
        # Test without extension
        result = self.generator._ensure_xlsx_extension('file')
        assert result.endswith('file.xlsx')
        
        # Test with .xlsx extension
        result = self.generator._ensure_xlsx_extension('file.xlsx')
        assert result.endswith('file.xlsx')
        
        # Test with other extension
        result = self.generator._ensure_xlsx_extension('file.xls')
        assert result.endswith('file.xlsx')
    
    def test_ensure_output_directory(self):
        """Test ensuring output directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, 'nested', 'folder', 'file.xlsx')
            
            # Directory should not exist initially
            assert not os.path.exists(os.path.dirname(nested_path))
            
            # Call ensure_output_directory
            self.generator._ensure_output_directory(nested_path)
            
            # Directory should now exist
            assert os.path.exists(os.path.dirname(nested_path))
    
    def test_write_data_to_worksheet(self):
        """Test writing data to worksheet."""
        wb = Workbook()
        ws = wb.active
        
        test_data = [
            {
                'row_number': 1,
                'contractor_name': 'ООО "Тест"',
                'inn': '1234567890',
                'shipment_date': '15.06.2025',
                'invoice_number': 'ТСТ-001',
                'amount_without_vat': '100 000,00',
                'vat_rate': '20%',
                'amount_with_vat': '120 000,00'
            }
        ]
        
        self.generator._write_data_to_worksheet(ws, test_data)
        
        # Test that data was written to correct positions
        # First data row starts at row 3, column 2 (B3)
        assert ws.cell(row=3, column=2).value == 1  # row_number
        assert ws.cell(row=3, column=3).value == 'ООО "Тест"'  # contractor_name
        assert ws.cell(row=3, column=4).value == '1234567890'  # inn
    
    def test_apply_styling(self):
        """Test applying styling to worksheet."""
        wb = Workbook()
        ws = wb.active
        
        # Set up worksheet with headers
        self.generator.layout.write_headers(ws)
        
        test_data = [
            {'is_no_vat': False},
            {'is_no_vat': True}
        ]
        
        # Write some test data
        for row_index, row_data in enumerate(test_data):
            for col_index in range(len(self.generator.layout.COLUMNS)):
                excel_row, excel_col = self.generator.layout.get_data_cell_position(row_index, col_index)
                ws.cell(row=excel_row, column=excel_col).value = f'Test {row_index}-{col_index}'
        
        # Apply styling
        self.generator._apply_styling(ws, test_data)
        
        # Test that styling was applied (basic checks)
        # Header styling
        header_cell = ws.cell(row=self.generator.layout.HEADER_ROW, column=self.generator.layout.START_COLUMN)
        assert header_cell.font.bold is True
        
        # Data styling should be applied (exact checks depend on styles implementation)
        data_cell = ws.cell(row=self.generator.layout.DATA_START_ROW, column=self.generator.layout.START_COLUMN)
        assert data_cell.font is not None
    
    def test_add_summary_section(self):
        """Test adding summary section to worksheet."""
        wb = Workbook()
        ws = wb.active
        
        test_summary = {
            'record_count': 5,
            'total_without_vat': '500 000,00',
            'total_with_vat': '600 000,00'
        }
        
        self.generator._add_summary_section(ws, 5, test_summary)
        
        # Test that summary was added
        summary_start_row = self.generator.layout.DATA_START_ROW + 5 + 2  # 10
        
        count_cell = ws.cell(row=summary_start_row, column=self.generator.layout.START_COLUMN)
        assert count_cell.value == "Всего записей:"
        
        count_value_cell = ws.cell(row=summary_start_row, column=self.generator.layout.START_COLUMN + 1)
        assert count_value_cell.value == 5


class TestExcelReportBuilder:
    """Test high-level Excel report builder."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.builder = ExcelReportBuilder()
    
    def test_builder_initialization(self):
        """Test ExcelReportBuilder initialization."""
        assert hasattr(self.builder, 'generator')
    
    def test_build_invoice_report(self):
        """Test building invoice report."""
        test_invoices = [
            {
                'contractor_name': 'ООО "Строитель"',
                'inn': '1234567890',
                'amount': 250000,
                'vat_rate': '20%'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'invoice_report.xlsx')
            
            result_path = self.builder.build_invoice_report(
                test_invoices, output_path, "Отчёт по счетам"
            )
            
            assert os.path.exists(result_path)
            
            wb = load_workbook(result_path)
            ws = wb.active
            assert ws.title == "Отчёт по счетам"
    
    def test_build_invoice_report_error_handling(self):
        """Test error handling in invoice report building."""
        with patch.object(self.builder.generator, 'generate_report', side_effect=Exception("Test error")):
            with pytest.raises(ReportGenerationError):
                self.builder.build_invoice_report([], 'test.xlsx')
    
    def test_build_summary_report(self):
        """Test building summary report."""
        test_invoices = [
            {'amount': 100000, 'vat_rate': '20%'},
            {'amount': 200000, 'vat_rate': '20%'}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'summary_report.xlsx')
            
            summary = self.builder.build_summary_report(test_invoices, output_path)
            
            assert isinstance(summary, dict)
            assert 'record_count' in summary
            assert 'total_without_vat' in summary
            assert 'total_with_vat' in summary
            
            # Test that Excel file was also created
            assert os.path.exists(output_path)
    
    def test_build_summary_report_error_handling(self):
        """Test error handling in summary report building."""
        with patch.object(self.builder.generator.data_formatter, 'format_invoice_data', side_effect=Exception("Test error")):
            with pytest.raises(ReportGenerationError):
                self.builder.build_summary_report([], 'test.xlsx')
    
    def test_validate_data_for_report_valid(self):
        """Test data validation for valid data."""
        valid_data = [
            {
                'contractor_name': 'ООО "Валидный"',
                'inn': '1234567890',
                'amount': 100000,
                'vat_rate': '20%'
            }
        ]
        
        results = self.builder.validate_data_for_report(valid_data)
        
        assert results['is_valid'] is True
        assert results['total_records'] == 1
        assert results['valid_records'] == 1
        assert results['invalid_records'] == 0
        assert len(results['errors']) == 0
    
    def test_validate_data_for_report_invalid(self):
        """Test data validation for invalid data."""
        invalid_data = [
            {'contractor_name': 'Valid'},
            {}  # This might cause errors in formatting
        ]
        
        # Mock formatting to raise an error for the second record
        with patch.object(self.builder.generator.data_formatter, '_format_single_invoice') as mock_format:
            mock_format.side_effect = [
                {'row_number': 1, 'contractor_name': 'Valid'},  # First succeeds
                Exception("Formatting error")  # Second fails
            ]
            
            results = self.builder.validate_data_for_report(invalid_data)
            
            assert results['is_valid'] is False
            assert results['total_records'] == 2
            assert results['valid_records'] == 1
            assert results['invalid_records'] == 1
            assert len(results['errors']) == 1
    
    def test_validate_data_for_report_empty(self):
        """Test data validation for empty data."""
        results = self.builder.validate_data_for_report([])
        
        assert results['is_valid'] is True
        assert results['total_records'] == 0
        assert results['valid_records'] == 0
        assert results['invalid_records'] == 0
        assert len(results['errors']) == 0


class TestGeneratorIntegration:
    """Integration tests for the entire generator module."""
    
    def test_complete_report_generation_workflow(self):
        """Test complete report generation from start to finish."""
        generator = ExcelReportGenerator()
        
        # Comprehensive test data
        test_data = [
            {
                'contractor_name': 'ООО "Первая компания"',
                'inn': '1234567890',
                'shipment_date': '15.06.2025',
                'invoice_number': 'ПК-001',
                'amount': 100000,
                'vat_rate': '20%'
            },
            {
                'contractor_name': 'ИП Иванов И.И.',
                'inn': '123456789012',
                'shipment_date': '16.06.2025',
                'invoice_number': 'ИИ-002',
                'amount': 50000,
                'vat_rate': 'Без НДС'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'integration_test.xlsx')
            
            # Generate report
            result_path = generator.generate_report(test_data, output_path)
            
            # Verify file creation
            assert os.path.exists(result_path)
            
            # Load and verify content
            wb = load_workbook(result_path)
            ws = wb.active
            
            # Test headers are present
            for i, col_def in enumerate(generator.layout.COLUMNS, start=generator.layout.START_COLUMN):
                header_cell = ws.cell(row=generator.layout.HEADER_ROW, column=i)
                assert header_cell.value == col_def.header
            
            # Test data is present
            # First row data should be in row 3 (DATA_START_ROW)
            first_data_row = generator.layout.DATA_START_ROW
            assert ws.cell(row=first_data_row, column=generator.layout.START_COLUMN).value == 1  # row_number
            
            # Second row data should be in row 4
            second_data_row = first_data_row + 1
            assert ws.cell(row=second_data_row, column=generator.layout.START_COLUMN).value == 2  # row_number
    
    def test_error_handling_workflow(self):
        """Test error handling throughout the generation workflow."""
        generator = ExcelReportGenerator()
        
        # Test with completely invalid output path that will definitely fail
        invalid_path = '/invalid/path/that/definitely/does/not/exist/and/cannot/be/created/file.xlsx'
        
        # On Windows, also test with invalid characters
        if os.name == 'nt':
            invalid_path = 'C:\\invalid\\<>|*?"path\\file.xlsx'
        
        with pytest.raises((PermissionError, OSError, FileNotFoundError)):
            generator.generate_report([], invalid_path)
    
    def test_different_file_extensions(self):
        """Test handling of different file extensions."""
        generator = ExcelReportGenerator()
        test_data = [{'contractor_name': 'Test', 'amount': 1000}]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test various extensions
            for ext in ['.xls', '.xlsx', '', '.txt']:
                filename = f'test{ext}'
                output_path = os.path.join(temp_dir, filename)
                
                result_path = generator.generate_report(test_data, output_path)
                
                # Should always end with .xlsx
                assert result_path.endswith('.xlsx')
                assert os.path.exists(result_path)
    
    def test_large_dataset_handling(self):
        """Test handling of larger datasets."""
        generator = ExcelReportGenerator()
        
        # Create larger test dataset
        large_data = []
        for i in range(100):
            large_data.append({
                'contractor_name': f'ООО "Компания {i}"',
                'inn': f'{1234567890 + i}',
                'shipment_date': '15.06.2025',
                'invoice_number': f'КМП-{i:03d}',
                'amount': 10000 * (i + 1),
                'vat_rate': '20%' if i % 2 == 0 else 'Без НДС'
            })
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, 'large_dataset.xlsx')
            
            result_path = generator.generate_report(large_data, output_path)
            
            assert os.path.exists(result_path)
            
            # Verify data count in summary
            wb = load_workbook(result_path)
            ws = wb.active
            
            # Summary should show 100 records
            summary_start_row = generator.layout.DATA_START_ROW + len(large_data) + 2
            count_value_cell = ws.cell(row=summary_start_row, column=generator.layout.START_COLUMN + 1)
            assert count_value_cell.value == 100 