"""
Excel formatter module for Bitrix24 report generation.

Converts processed data from data_processor modules into Excel-ready format
with proper Russian formatting for dates, currencies, and VAT rates.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import re
from datetime import datetime

from ..data_processor.currency_processor import CurrencyProcessor
from ..data_processor.date_processor import DateProcessor
from ..data_processor.inn_processor import INNProcessor


class ExcelDataFormatter:
    """
    Formats processed data for Excel output.
    
    Integrates with existing data processors to ensure consistent
    formatting throughout the application.
    """
    
    def __init__(self):
        self.currency_processor = CurrencyProcessor()
        self.date_processor = DateProcessor()
        self.inn_processor = INNProcessor()
    
    def format_invoice_data(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format invoice data for Excel output.
        
        Args:
            invoices: List of processed invoice dictionaries
            
        Returns:
            List of Excel-ready data dictionaries
        """
        formatted_data = []
        
        for i, invoice in enumerate(invoices, 1):
            formatted_row = self._format_single_invoice(invoice, i)
            formatted_data.append(formatted_row)
        
        return formatted_data
    
    def _format_single_invoice(self, invoice: Dict[str, Any], row_number: int) -> Dict[str, Any]:
        """
        Format a single invoice for Excel output.
        
        Args:
            invoice: Invoice data dictionary
            row_number: Row number for display
            
        Returns:
            Formatted data dictionary matching Excel layout
        """
        # Extract basic fields with fallbacks
        contractor_name = invoice.get('contractor_name', '')
        inn = invoice.get('inn', '')
        shipment_date = invoice.get('shipment_date', '')
        invoice_number = invoice.get('invoice_number', '')
        amount = invoice.get('amount', 0)
        vat_rate = invoice.get('vat_rate', '20%')
        
        # Format INN
        formatted_inn = self._format_inn(inn)
        
        # Format date
        formatted_date = self._format_date(shipment_date)
        
        # Format amounts and VAT
        formatted_amounts = self._format_amounts(amount, vat_rate)
        
        # Determine if this is a no-VAT row (for styling)
        is_no_vat = self._is_no_vat_row(vat_rate)
        
        return {
            'row_number': row_number,
            'contractor_name': self._clean_text(contractor_name),
            'inn': formatted_inn,
            'shipment_date': formatted_date,
            'invoice_number': self._clean_text(invoice_number),
            'amount_without_vat': formatted_amounts['without_vat_display'],
            'vat_rate': formatted_amounts['vat_display'],
            'amount_with_vat': formatted_amounts['with_vat_display'],
            'amount_without_vat_numeric': formatted_amounts['without_vat_numeric'],
            'amount_with_vat_numeric': formatted_amounts['with_vat_numeric'],
            'is_no_vat': is_no_vat
        }
    
    def _format_inn(self, inn: str) -> str:
        """Format INN using the INN processor."""
        if not inn:
            return ""
        
        # Use existing validate_inn method which returns INNValidationResult
        result = self.inn_processor.validate_inn(inn)
        if result.is_valid and result.formatted_inn:
            return result.formatted_inn
        else:
            # Return as-is if validation fails
            return str(inn)
    
    def _format_date(self, date_value: Any) -> str:
        """Format date using the date processor."""
        if not date_value:
            return ""
        
        try:
            # Use existing parse_date method
            result = self.date_processor.parse_date(date_value)
            if result.is_valid and result.formatted_date:
                return result.formatted_date
            else:
                # If parsing fails, return original value as string
                return str(date_value)
        except Exception:
            return str(date_value) if date_value else ""
    
    def _format_amounts(self, amount: Any, vat_rate: str) -> Dict[str, Any]:
        """
        Format currency amounts using the currency processor.
        
        Args:
            amount: Base amount value
            vat_rate: VAT rate string (e.g., "20%", "Без НДС")
            
        Returns:
            Dictionary with formatted amounts
        """
        try:
            # Parse amount using currency processor
            parse_result = self.currency_processor.parse_amount(amount)
            if not parse_result.is_valid:
                # Fallback to zero if parsing fails
                base_amount = Decimal('0')
            else:
                base_amount = parse_result.amount
            
            # Determine VAT calculation logic
            is_no_vat = 'без ндс' in str(vat_rate).lower() or vat_rate == '0%'
            
            if is_no_vat:
                # No VAT calculation
                without_vat = base_amount
                with_vat = base_amount
                vat_display = "Без НДС"
            else:
                # Calculate VAT using existing method
                vat_result = self.currency_processor.calculate_vat(
                    base_amount, vat_rate, amount_includes_vat=False
                )
                
                if vat_result.is_valid:
                    without_vat = vat_result.base_amount
                    with_vat = vat_result.total_amount
                    vat_display = str(vat_rate)
                else:
                    # Fallback calculation
                    without_vat = base_amount
                    with_vat = base_amount
                    vat_display = str(vat_rate)
            
            # Format for display using existing method
            without_vat_display = self.currency_processor.format_amount(
                without_vat, include_currency_symbol=False
            )
            with_vat_display = self.currency_processor.format_amount(
                with_vat, include_currency_symbol=False
            )
            
            return {
                'without_vat_display': without_vat_display,
                'with_vat_display': with_vat_display,
                'vat_display': vat_display,
                'without_vat_numeric': float(without_vat),
                'with_vat_numeric': float(with_vat)
            }
            
        except Exception as e:
            # Fallback formatting
            fallback_amount = str(amount) if amount else "0,00"
            return {
                'without_vat_display': fallback_amount,
                'with_vat_display': fallback_amount,
                'vat_display': str(vat_rate),
                'without_vat_numeric': 0.0,
                'with_vat_numeric': 0.0
            }
    
    def _is_no_vat_row(self, vat_rate: str) -> bool:
        """
        Determine if this is a no-VAT row (for gray styling).
        
        Args:
            vat_rate: VAT rate string
            
        Returns:
            True if this row should have gray styling
        """
        if not vat_rate:
            return False
        
        vat_lower = str(vat_rate).lower()
        return 'без ндс' in vat_lower or vat_rate == '0%'
    
    def _clean_text(self, text: Any) -> str:
        """
        Clean text for Excel display.
        
        Args:
            text: Text value to clean
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        text_str = str(text)
        
        # Remove extra whitespace
        text_str = ' '.join(text_str.split())
        
        # Remove any problematic characters for Excel
        text_str = text_str.replace('\n', ' ').replace('\r', ' ')
        
        return text_str


class ExcelSummaryFormatter:
    """
    Formats summary data for Excel output.
    
    Creates totals and statistics for the bottom section of the report.
    """
    
    def __init__(self):
        self.currency_processor = CurrencyProcessor()
    
    def format_summary(self, formatted_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format summary totals for Excel output.
        
        Args:
            formatted_data: List of formatted invoice data
            
        Returns:
            Dictionary with formatted summary data
        """
        total_without_vat = Decimal('0')
        total_with_vat = Decimal('0')
        record_count = len(formatted_data)
        
        # Calculate totals
        for row in formatted_data:
            total_without_vat += Decimal(str(row.get('amount_without_vat_numeric', 0)))
            total_with_vat += Decimal(str(row.get('amount_with_vat_numeric', 0)))
        
        return {
            'record_count': record_count,
            'total_without_vat': self.currency_processor.format_amount(
                total_without_vat, include_currency_symbol=False
            ),
            'total_with_vat': self.currency_processor.format_amount(
                total_with_vat, include_currency_symbol=False
            ),
            'total_without_vat_numeric': float(total_without_vat),
            'total_with_vat_numeric': float(total_with_vat)
        }


class DataValidator:
    """
    Validates data before Excel formatting.
    
    Ensures data integrity and handles edge cases.
    """
    
    @staticmethod
    def validate_invoice_data(invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean invoice data.
        
        Args:
            invoice: Raw invoice data
            
        Returns:
            Validated invoice data with required fields
        """
        required_fields = {
            'contractor_name': '',
            'inn': '',
            'shipment_date': '',
            'invoice_number': '',
            'amount': 0,
            'vat_rate': '20%'
        }
        
        # Ensure all required fields exist
        validated = required_fields.copy()
        validated.update(invoice)
        
        return validated
    
    @staticmethod
    def validate_formatted_data(data: List[Dict[str, Any]]) -> bool:
        """
        Validate formatted data structure.
        
        Args:
            data: List of formatted data dictionaries
            
        Returns:
            True if data is valid for Excel output
        """
        if not isinstance(data, list):
            return False
        
        required_keys = {
            'row_number', 'contractor_name', 'inn', 'shipment_date',
            'invoice_number', 'amount_without_vat', 'vat_rate', 'amount_with_vat'
        }
        
        for row in data:
            if not isinstance(row, dict):
                return False
            if not required_keys.issubset(row.keys()):
                return False
        
        return True 