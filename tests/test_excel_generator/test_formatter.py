"""
Unit tests for Excel formatter module.

Tests data formatting for Excel output with integration
to existing data processor modules.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from src.excel_generator.formatter import (
    ExcelDataFormatter,
    ExcelSummaryFormatter,
    DataValidator
)


class TestExcelDataFormatter:
    """Test Excel data formatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ExcelDataFormatter()
    
    def test_formatter_initialization(self):
        """Test ExcelDataFormatter initialization."""
        assert hasattr(self.formatter, 'currency_processor')
        assert hasattr(self.formatter, 'date_processor')
        assert hasattr(self.formatter, 'inn_processor')
    
    def test_format_invoice_data(self):
        """Test formatting invoice data for Excel."""
        test_invoices = [
            {
                'contractor_name': 'ООО "Тест"',
                'inn': '1234567890',
                'shipment_date': '15.06.2025',
                'invoice_number': 'ТСТ-001',
                'amount': 100000,
                'vat_rate': '20%'
            },
            {
                'contractor_name': 'ИП Иванов',
                'inn': '123456789012',
                'shipment_date': '16.06.2025',
                'invoice_number': 'ИВ-002',
                'amount': 50000,
                'vat_rate': 'Без НДС'
            }
        ]
        
        formatted_data = self.formatter.format_invoice_data(test_invoices)
        
        assert len(formatted_data) == 2
        
        # Test first invoice
        first_row = formatted_data[0]
        assert 'ООО "Тест"' in first_row['contractor_name']
        assert first_row['inn'] == '1234567890'
        assert 'ТСТ-001' in first_row['invoice_number']
        assert first_row['is_no_vat'] is False
        
        # Test second invoice (no VAT)
        second_row = formatted_data[1]
        assert 'ИП Иванов' in second_row['contractor_name']
        assert second_row['inn'] == '123456789012'
        assert 'ИВ-002' in second_row['invoice_number']
        assert second_row['is_no_vat'] is True
    
    def test_format_single_invoice(self):
        """Test formatting a single invoice."""
        test_invoice = {
            'contractor_name': 'ООО "Рога и Копыта"',
            'inn': '7707083893',
            'shipment_date': '01.06.2025',
            'invoice_number': 'РК-123',
            'amount': 250000,
            'vat_rate': '20%'
        }
        
        formatted = self.formatter._format_single_invoice(test_invoice, 5)
        
        assert 'ООО "Рога и Копыта"' in formatted['contractor_name']
        assert 'РК-123' in formatted['invoice_number']
        assert 'amount_without_vat_numeric' in formatted
        assert 'amount_with_vat_numeric' in formatted
        assert 'total_amount' in formatted
        assert 'vat_amount' in formatted
    
    def test_format_inn_valid(self):
        """Test INN formatting with valid INN."""
        # Create mock result object
        from src.data_processor.inn_processor import INNValidationResult
        mock_result = INNValidationResult(is_valid=True, formatted_inn='12 34 56 78 90')
        
        with patch.object(self.formatter.inn_processor, 'validate_inn', return_value=mock_result):
            result = self.formatter._format_inn('1234567890')
            assert result == '12 34 56 78 90'
    
    def test_format_inn_invalid(self):
        """Test INN formatting with invalid INN."""
        from src.data_processor.inn_processor import INNValidationResult
        mock_result = INNValidationResult(is_valid=False, error_message='Invalid INN')
        
        with patch.object(self.formatter.inn_processor, 'validate_inn', return_value=mock_result):
            result = self.formatter._format_inn('invalid_inn')
            assert result == 'invalid_inn'
    
    def test_format_inn_empty(self):
        """Test INN formatting with empty value."""
        result = self.formatter._format_inn('')
        assert result == ''
        
        result = self.formatter._format_inn(None)
        assert result == ''
    
    def test_format_date_valid(self):
        """Test date formatting with valid date."""
        from src.data_processor.date_processor import DateProcessingResult
        from datetime import datetime
        
        test_date = datetime(2025, 6, 15)
        mock_result = DateProcessingResult(
            is_valid=True, 
            parsed_date=test_date, 
            formatted_date='15.06.2025'
        )
        
        with patch.object(self.formatter.date_processor, 'parse_date', return_value=mock_result):
            result = self.formatter._format_date('15.06.2025')
            assert result == '15.06.2025'
    
    def test_format_date_invalid(self):
        """Test date formatting with invalid date."""
        from src.data_processor.date_processor import DateProcessingResult
        
        mock_result = DateProcessingResult(is_valid=False, error_message='Invalid date')
        
        with patch.object(self.formatter.date_processor, 'parse_date', return_value=mock_result):
            result = self.formatter._format_date('invalid_date')
            assert result == 'invalid_date'
    
    def test_format_amounts_with_vat(self):
        """Test amount formatting with VAT."""
        from src.data_processor.currency_processor import CurrencyProcessingResult, VATCalculationResult
        from decimal import Decimal
        
        # Mock parse_amount result
        mock_parse_result = CurrencyProcessingResult(
            is_valid=True, 
            amount=Decimal('100000'), 
            formatted_amount='100 000,00'
        )
        
        # Mock calculate_vat result
        mock_vat_result = VATCalculationResult(
            is_valid=True,
            base_amount=Decimal('100000'),
            total_amount=Decimal('120000'),
            formatted_base='100 000,00',
            formatted_total='120 000,00'
        )
        
        with patch.object(self.formatter.currency_processor, 'parse_amount', return_value=mock_parse_result), \
             patch.object(self.formatter.currency_processor, 'calculate_vat', return_value=mock_vat_result), \
             patch.object(self.formatter.currency_processor, 'format_amount', side_effect=['100 000,00', '120 000,00']):
            
            result = self.formatter._format_amounts(100000, '20%')
            
            assert 'without_vat_display' in result
            assert 'with_vat_display' in result
            assert 'vat_display' in result
            assert 'without_vat_numeric' in result
            assert 'with_vat_numeric' in result
    
    def test_is_no_vat_row(self):
        """Test determining if row is no-VAT."""
        # Test with no VAT
        assert self.formatter._is_no_vat_row('Без НДС') is True
        assert self.formatter._is_no_vat_row('0%') is True
        
        # Test with VAT
        assert self.formatter._is_no_vat_row('20%') is False
        assert self.formatter._is_no_vat_row('10%') is False
        
        # Test edge cases
        assert self.formatter._is_no_vat_row('') is False
        assert self.formatter._is_no_vat_row(None) is False
    
    def test_clean_text(self):
        """Test text cleaning for Excel."""
        # Test normal text
        assert self.formatter._clean_text('Normal text') == 'Normal text'
        
        # Test text with extra whitespace
        assert self.formatter._clean_text('  Extra   spaces  ') == 'Extra spaces'
        
        # Test text with newlines
        assert self.formatter._clean_text('Text\nwith\nnewlines') == 'Text with newlines'
        
        # Test empty/None values
        assert self.formatter._clean_text('') == ''
        assert self.formatter._clean_text(None) == ''
        
        # Test non-string values
        assert self.formatter._clean_text(123) == '123'


class TestExcelSummaryFormatter:
    """Test Excel summary formatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ExcelSummaryFormatter()
    
    def test_formatter_initialization(self):
        """Test ExcelSummaryFormatter initialization."""
        assert hasattr(self.formatter, 'currency_processor')
    
    def test_format_summary(self):
        """Test formatting summary data."""
        test_data = [
            {
                'amount_without_vat_numeric': 100000.0,
                'amount_with_vat_numeric': 120000.0
            },
            {
                'amount_without_vat_numeric': 50000.0,
                'amount_with_vat_numeric': 60000.0
            }
        ]
        
        with patch.object(self.formatter.currency_processor, 'format_amount') as mock_format:
            mock_format.side_effect = ['150 000,00', '180 000,00']
            
            summary = self.formatter.format_summary(test_data)
            
            assert summary['record_count'] == 2
            assert 'total_without_vat' in summary
            assert 'total_with_vat' in summary
            assert summary['total_without_vat_numeric'] == 150000.0
            assert summary['total_with_vat_numeric'] == 180000.0
    
    def test_format_summary_empty_data(self):
        """Test formatting summary with empty data."""
        summary = self.formatter.format_summary([])
        
        assert summary['record_count'] == 0
        assert summary['total_without_vat_numeric'] == 0.0
        assert summary['total_with_vat_numeric'] == 0.0


class TestDataValidator:
    """Test data validator."""
    
    def test_validate_invoice_data(self):
        """Test invoice data validation."""
        test_invoice = {
            'contractor_name': 'ООО "Тест"',
            'amount': 100000
        }
        
        validated = DataValidator.validate_invoice_data(test_invoice)
        
        # Test that all required fields are present
        required_fields = ['contractor_name', 'inn', 'shipment_date', 'invoice_number', 'amount', 'vat_rate']
        for field in required_fields:
            assert field in validated
        
        # Test that original values are preserved
        assert validated['contractor_name'] == 'ООО "Тест"'
        assert validated['amount'] == 100000
        
        # Test that default values are added
        assert validated['inn'] == ''
        assert validated['vat_rate'] == '20%'
    
    def test_validate_invoice_data_complete(self):
        """Test validation with complete invoice data."""
        complete_invoice = {
            'contractor_name': 'ООО "Полный"',
            'inn': '1234567890',
            'shipment_date': '15.06.2025',
            'invoice_number': 'ПОЛ-001',
            'amount': 200000,
            'vat_rate': '20%'
        }
        
        validated = DataValidator.validate_invoice_data(complete_invoice)
        
        # All original values should be preserved
        for key, value in complete_invoice.items():
            assert validated[key] == value
    
    def test_validate_formatted_data_valid(self):
        """Test validation of properly formatted data."""
        valid_data = [
            {
                'invoice_number': 'ТСТ-001',
                'inn': '1234567890',
                'contractor_name': 'ООО "Тест"',
                'total_amount': '120 000,00',
                'vat_amount': '20 000,00',
                'invoice_date': '15.06.2025',
                'shipment_date': '15.06.2025',
                'payment_date': '16.06.2025'
            }
        ]
        
        assert DataValidator.validate_formatted_data(valid_data) is True
    
    def test_validate_formatted_data_invalid(self):
        """Test validation of improperly formatted data."""
        # Test with non-list
        assert DataValidator.validate_formatted_data("not a list") is False
        
        # Test with non-dict items
        assert DataValidator.validate_formatted_data(["not a dict"]) is False
        
        # Test with missing required keys
        invalid_data = [{'row_number': 1}]  # Missing other required keys
        assert DataValidator.validate_formatted_data(invalid_data) is False
    
    def test_validate_formatted_data_empty(self):
        """Test validation of empty data."""
        assert DataValidator.validate_formatted_data([]) is True


class TestFormatterIntegration:
    """Integration tests for formatter module."""
    
    def test_complete_formatting_workflow(self):
        """Test complete formatting workflow."""
        formatter = ExcelDataFormatter()
        
        test_invoices = [
            {
                'contractor_name': 'ООО "Интеграция"',
                'inn': '1234567890',
                'shipment_date': '20.06.2025',
                'invoice_number': 'ИНТ-100',
                'amount': 500000,
                'vat_rate': '20%'
            }
        ]
        
        # Format data
        formatted_data = formatter.format_invoice_data(test_invoices)
        
        # Validate formatted data
        assert DataValidator.validate_formatted_data(formatted_data) is True
        
        # Create summary
        summary_formatter = ExcelSummaryFormatter()
        summary = summary_formatter.format_summary(formatted_data)
        
        assert summary['record_count'] == 1
        assert 'total_without_vat' in summary
        assert 'total_with_vat' in summary 