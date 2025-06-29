"""Unit тесты для главного DataProcessor"""
import pytest
from decimal import Decimal
from datetime import datetime
from src.data_processor.data_processor import DataProcessor, InvoiceData


class TestDataProcessor:
    """Тесты главного DataProcessor - оркестратора"""
    
    @pytest.fixture
    def processor(self):
        return DataProcessor()
    
    def test_processor_initialization(self, processor):
        """Тест: инициализация процессора"""
        assert processor is not None
        assert processor.inn_processor is not None
        assert processor.date_processor is not None
        assert processor.currency_processor is not None
        assert processor.default_currency == 'RUB'
    
    def test_process_valid_invoice(self, processor):
        """Тест: обработка валидного счёта"""
        raw_data = {
            'ACCOUNT_NUMBER': 'С-12345',
            'UF_CRM_INN': '3321035160',  # Валидный ИНН со скриншотов
            'TITLE': 'ООО "ГЕНЕРИУМ-НЕКСТ"',
            'OPPORTUNITY': '120000',
            'DATE_BILL': '15.06.2024'
        }
        
        invoice = processor.process_invoice_data(raw_data)
        
        assert invoice.invoice_number == 'С-12345'
        assert invoice.inn == '3321035160'
        assert invoice.inn_valid is True
        assert invoice.counterparty == 'ООО "ГЕНЕРИУМ-НЕКСТ"'
        assert invoice.amount == Decimal('120000')
        assert invoice.amounts_valid is True
        assert invoice.dates_valid is True
        assert len(invoice.validation_errors) == 0
    
    def test_process_invoice_with_invalid_inn(self, processor):
        """Тест: обработка счёта с невалидным ИНН"""
        raw_data = {
            'ACCOUNT_NUMBER': 'С-12345',
            'UF_CRM_INN': '1234567890',  # Невалидный ИНН
            'TITLE': 'ООО "Тест"',
            'OPPORTUNITY': '100000',
            'DATE_BILL': '15.06.2024'
        }
        
        invoice = processor.process_invoice_data(raw_data)
        
        assert invoice.inn_valid is False
        assert any('Невалидный ИНН' in error for error in invoice.validation_errors)
    
    def test_process_invoice_missing_fields(self, processor):
        """Тест: обработка счёта с отсутствующими полями"""
        raw_data = {
            'ACCOUNT_NUMBER': 'С-12345',
            # Отсутствуют ИНН, сумма, дата
        }
        
        invoice = processor.process_invoice_data(raw_data)
        
        assert len(invoice.validation_errors) > 0
        assert any('ИНН не найден' in error for error in invoice.validation_errors)
        assert any('Сумма не найдена' in error for error in invoice.validation_errors)
    
    def test_vat_calculation(self, processor):
        """Тест: расчёт НДС"""
        raw_data = {
            'ACCOUNT_NUMBER': 'С-12345',
            'UF_CRM_INN': '3321035160',
            'TITLE': 'ООО "Тест"',
            'OPPORTUNITY': '120000',  # Сумма с НДС
            'DATE_BILL': '15.06.2024'
        }
        
        invoice = processor.process_invoice_data(raw_data)
        
        # Проверяем что НДС рассчитан корректно
        # 120000 с НДС 20% = 100000 без НДС + 20000 НДС
        assert invoice.vat_amount == Decimal('20000.00')
    
    def test_process_batch(self, processor):
        """Тест: пакетная обработка счетов"""
        raw_data_list = [
            {
                'ACCOUNT_NUMBER': 'С-1',
                'UF_CRM_INN': '3321035160',
                'TITLE': 'ООО "Компания 1"',
                'OPPORTUNITY': '100000',
                'DATE_BILL': '15.06.2024'
            },
            {
                'ACCOUNT_NUMBER': 'С-2',
                'UF_CRM_INN': '5403339998',
                'TITLE': 'ООО "Компания 2"',
                'OPPORTUNITY': '200000',
                'DATE_BILL': '16.06.2024'
            }
        ]
        
        invoices = processor.process_invoice_batch(raw_data_list)
        
        assert len(invoices) == 2
        assert all(invoice.inn_valid for invoice in invoices)
        assert all(invoice.amounts_valid for invoice in invoices)
        assert all(invoice.dates_valid for invoice in invoices)
    
    def test_field_extraction_methods(self, processor):
        """Тест: методы извлечения полей"""
        # Тест извлечения номера счёта
        raw_data_number = {'ACCOUNT_NUMBER': 'С-12345'}
        number = processor._extract_invoice_number(raw_data_number)
        assert number == 'С-12345'
        
        # Тест извлечения контрагента
        raw_data_title = {'TITLE': 'ООО "Тест"'}
        title = processor._extract_counterparty(raw_data_title)
        assert title == 'ООО "Тест"'
    
    def test_date_processing(self, processor):
        """Тест: обработка различных форматов дат"""
        test_cases = [
            {'DATE_BILL': '15.06.2024'},
            {'DATE_BILL': '2024-06-15'},
            {'created_time': '15/06/2024'},
        ]
        
        for raw_data in test_cases:
            raw_data.update({
                'ACCOUNT_NUMBER': 'С-12345',
                'UF_CRM_INN': '3321035160',
                'TITLE': 'ООО "Тест"',
                'OPPORTUNITY': '100000'
            })
            
            invoice = processor.process_invoice_data(raw_data)
            assert invoice.dates_valid is True
            assert invoice.invoice_date is not None
            assert invoice.formatted_invoice_date == '15.06.2024'
    
    def test_currency_formats(self, processor):
        """Тест: обработка различных форматов сумм"""
        test_cases = [
            ('100000', Decimal('100000')),
            ('100 000', Decimal('100000')),
            ('100000,50', Decimal('100000.50')),
            ('100 000,50 руб', Decimal('100000.50')),
        ]
        
        for amount_str, expected_amount in test_cases:
            raw_data = {
                'ACCOUNT_NUMBER': 'С-12345',
                'UF_CRM_INN': '3321035160',
                'TITLE': 'ООО "Тест"',
                'OPPORTUNITY': amount_str,
                'DATE_BILL': '15.06.2024'
            }
            
            invoice = processor.process_invoice_data(raw_data)
            assert invoice.amounts_valid is True
            assert invoice.amount == expected_amount
    
    def test_error_handling(self, processor):
        """Тест: обработка ошибок"""
        # Тест с некорректными данными
        raw_data = {
            'ACCOUNT_NUMBER': None,
            'UF_CRM_INN': '',
            'TITLE': '',
            'OPPORTUNITY': 'invalid_amount',
            'DATE_BILL': 'invalid_date'
        }
        
        invoice = processor.process_invoice_data(raw_data)
        
        # Должны быть ошибки валидации
        assert len(invoice.validation_errors) > 0
        assert not invoice.inn_valid
        assert not invoice.amounts_valid


class TestInvoiceData:
    """Тесты структуры InvoiceData"""
    
    def test_invoice_data_creation(self):
        """Тест: создание InvoiceData"""
        invoice = InvoiceData()
        
        assert invoice.invoice_number is None
        assert invoice.inn is None
        assert invoice.counterparty is None
        assert invoice.amount is None
        assert invoice.validation_errors == []
        assert invoice.inn_valid is False
        assert invoice.dates_valid is False
        assert invoice.amounts_valid is False
    
    def test_invoice_data_with_values(self):
        """Тест: InvoiceData с значениями"""
        invoice = InvoiceData(
            invoice_number='С-12345',
            inn='3321035160',
            counterparty='ООО "Тест"',
            amount=Decimal('100000'),
            inn_valid=True,
            amounts_valid=True
        )
        
        assert invoice.invoice_number == 'С-12345'
        assert invoice.inn == '3321035160'
        assert invoice.counterparty == 'ООО "Тест"'
        assert invoice.amount == Decimal('100000')
        assert invoice.inn_valid is True
        assert invoice.amounts_valid is True


@pytest.mark.unit
def test_data_processor_integration():
    """Интеграционный тест DataProcessor"""
    processor = DataProcessor()
    
    # Реальные данные как могут прийти из Bitrix24
    sample_data = [
        {
            'ACCOUNT_NUMBER': 'С-001/2024',
            'UF_CRM_INN': '3321035160',
            'TITLE': 'ООО "ГЕНЕРИУМ-НЕКСТ"',
            'OPPORTUNITY': '500000.00',
            'DATE_BILL': '2024-06-15T10:30:00'
        },
        {
            'ACCOUNT_NUMBER': 'С-002/2024', 
            'UF_CRM_INN': '5403339998',
            'TITLE': 'ООО "САНЗЭЙТРАНС"',
            'OPPORTUNITY': '1200000',
            'DATE_BILL': '15.06.2024'
        }
    ]
    
    # Пакетная обработка
    invoices = processor.process_invoice_batch(sample_data)
    
    # Проверяем результаты
    assert len(invoices) == 2
    
    for invoice in invoices:
        assert invoice.inn_valid is True
        assert invoice.amounts_valid is True
        assert invoice.dates_valid is True
        assert len(invoice.validation_errors) == 0
        assert invoice.amount > 0
        assert invoice.vat_amount is not None
        assert invoice.vat_amount > 0  # НДС рассчитан 