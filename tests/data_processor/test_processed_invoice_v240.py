"""
Тесты для ProcessedInvoice и нового batch обработчика (v2.4.0).

Проверяет исправления БАГ-A1 и БАГ-A5:
- Decimal типы вместо строк
- process_invoice_batch() возвращает List[ProcessedInvoice]
"""

import pytest
from decimal import Decimal
from datetime import datetime
from src.data_processor.data_processor import DataProcessor, ProcessedInvoice


class TestProcessedInvoiceBatchV240:
    """Тесты для нового метода process_invoice_batch() (БАГ-A1, БАГ-A5)"""
    
    @pytest.fixture
    def processor(self):
        """Фикстура DataProcessor"""
        return DataProcessor()
    
    def test_process_invoice_batch_returns_processed_invoices(self, processor):
        """Тест: process_invoice_batch возвращает List[ProcessedInvoice]"""
        raw_data = [
            {
                'accountNumber': 'С-001/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "ГЕНЕРИУМ-НЕКСТ"',
                'opportunity': '500000.00',
                'taxValue': '100000.00',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        
        # Проверяем что возвращается список ProcessedInvoice
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ProcessedInvoice)
    
    def test_processed_invoice_uses_decimal_types(self, processor):
        """Тест: ProcessedInvoice использует Decimal для сумм (БАГ-A1)"""
        raw_data = [
            {
                'accountNumber': 'С-002/2024',
                'ufCrmInn': '5403339998',
                'title': 'ООО "САНЗЭЙТРАНС"',
                'opportunity': '1200000.50',  # С копейками!
                'taxValue': '240000.10',      # Явно указываем НДС
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice = result[0]
        
        # Проверяем что суммы - это Decimal, а не строки
        assert isinstance(invoice.amount, Decimal)
        assert invoice.amount == Decimal('1200000.50')
        
        # НДС тоже должен быть Decimal когда указан явно
        assert isinstance(invoice.vat_amount, Decimal)
        assert invoice.vat_amount == Decimal('240000.10')
    
    def test_processed_invoice_handles_no_vat(self, processor):
        """Тест: ProcessedInvoice корректно обрабатывает "нет" НДС"""
        raw_data = [
            {
                'accountNumber': 'С-003/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Без НДС"',
                'opportunity': '300000',
                'taxValue': '0',  # НДС = 0
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice = result[0]
        
        # Проверяем что vat_amount="нет" когда taxValue=0
        assert invoice.vat_amount == "нет"
    
    def test_processed_invoice_to_dict_conversion(self, processor):
        """Тест: ProcessedInvoice.to_dict() сохраняет числовые типы для Excel"""
        raw_data = [
            {
                'accountNumber': 'С-004/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Тест Excel"',
                'opportunity': '750000.99',
                'taxValue': '150000.20',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice_dict = result[0].to_dict()
        
        # Проверяем что в dict суммы остаются Decimal (не строки!)
        assert isinstance(invoice_dict['amount'], Decimal)
        assert isinstance(invoice_dict['vat_amount'], (Decimal, str))
        
        # Проверяем наличие полей для обратной совместимости
        assert 'amount_numeric' in invoice_dict
        assert 'vat_amount_numeric' in invoice_dict
        assert isinstance(invoice_dict['amount_numeric'], float)
    
    def test_processed_invoice_batch_with_multiple_invoices(self, processor):
        """Тест: Batch обработка нескольких счетов с разными типами НДС"""
        raw_data = [
            {
                'accountNumber': 'С-100/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "С НДС"',
                'opportunity': '100000',
                'taxValue': '20000',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            },
            {
                'accountNumber': 'С-101/2024',
                'ufCrmInn': '5403339998',
                'title': 'ООО "Без НДС"',
                'opportunity': '200000',
                'taxValue': '0',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        
        assert len(result) == 2
        
        # Первый счёт с НДС
        invoice1 = result[0]
        assert isinstance(invoice1.amount, Decimal)
        assert isinstance(invoice1.vat_amount, Decimal)
        
        # Второй счёт без НДС
        invoice2 = result[1]
        assert isinstance(invoice2.amount, Decimal)
        assert invoice2.vat_amount == "нет"
    
    def test_processed_invoice_validation_errors(self, processor):
        """Тест: ProcessedInvoice сохраняет ошибки валидации"""
        raw_data = [
            {
                'accountNumber': '',  # Пустой номер счёта
                'ufCrmInn': '1234567890',  # Невалидный ИНН
                'title': '',
                'opportunity': '0',  # Нулевая сумма
                'taxValue': '0',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice = result[0]
        
        # Проверяем что есть ошибки валидации
        assert invoice.is_valid is False or len(invoice.validation_errors) > 0


class TestDecimalPrecisionV240:
    """Тесты точности Decimal для предотвращения БАГ-A1"""
    
    @pytest.fixture
    def processor(self):
        return DataProcessor()
    
    def test_decimal_precision_with_kopecks(self, processor):
        """Тест: Decimal сохраняет точность копеек"""
        raw_data = [
            {
                'accountNumber': 'С-005/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Копейки"',
                'opportunity': '123456.78',  # С копейками
                'taxValue': '24691.36',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice = result[0]
        
        # Decimal не теряет точность
        assert invoice.amount == Decimal('123456.78')
        assert str(invoice.amount) == '123456.78'
    
    def test_decimal_no_string_conversion(self, processor):
        """Тест: Decimal не конвертируется в строку (БАГ-A1)"""
        raw_data = [
            {
                'accountNumber': 'С-006/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Арифметика"',
                'opportunity': '1000.01',
                'taxValue': '200.00',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        result = processor.process_invoice_batch(raw_data)
        invoice = result[0]
        
        # Проверяем что суммы НЕ строки
        assert not isinstance(invoice.amount, str)
        assert not isinstance(invoice.vat_amount, str)
        assert isinstance(invoice.amount, Decimal)
        assert isinstance(invoice.vat_amount, Decimal)


class TestWorkflowIntegrationV240:
    """Тесты интеграции с WorkflowOrchestrator (БАГ-A5)"""
    
    @pytest.fixture
    def processor(self):
        return DataProcessor()
    
    def test_workflow_uses_process_invoice_batch(self, processor):
        """Тест: Workflow использует process_invoice_batch() (БАГ-A5)"""
        # Это проверяется в интеграционных тестах workflow
        # Здесь просто проверяем что метод существует и работает
        raw_data = [
            {
                'accountNumber': 'С-007/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Workflow Test"',
                'opportunity': '50000',
                'taxValue': '10000',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        # Метод должен работать без ошибок
        result = processor.process_invoice_batch(raw_data)
        
        assert len(result) == 1
        assert isinstance(result[0], ProcessedInvoice)
        assert result[0].is_valid is True
