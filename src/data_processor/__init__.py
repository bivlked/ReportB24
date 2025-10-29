"""
Data Processor module для обработки данных отчёта.
Координирует работу специализированных процессоров: INN, Date, Currency.
"""

from .inn_processor import INNProcessor, INNValidationResult
from .date_processor import DateProcessor, DateProcessingResult
from .currency_processor import (
    CurrencyProcessor,
    CurrencyProcessingResult,
    VATCalculationResult,
)
from .data_processor import DataProcessor, InvoiceData, ProcessedInvoice

__all__ = [
    # Главный процессор
    "DataProcessor",
    "InvoiceData",
    "ProcessedInvoice",
    # INN процессор
    "INNProcessor",
    "INNValidationResult",
    # Date процессор
    "DateProcessor",
    "DateProcessingResult",
    # Currency процессор
    "CurrencyProcessor",
    "CurrencyProcessingResult",
    "VATCalculationResult",
]
