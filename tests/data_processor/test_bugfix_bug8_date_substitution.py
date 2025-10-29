"""
Тесты для БАГ-8: Подмена отсутствующих дат на datetime.now()

БАГ-8: Отсутствующие даты счёта подменяются на datetime.now(), искажая данные

Проверяем, что:
1. Отсутствующие даты остаются None (не подменяются)
2. invoice_date и shipping_date теперь Optional[datetime]
3. Отсутствующие даты помечаются как validation_errors
4. is_valid=False для счетов с отсутствующими датами
"""

import pytest
from datetime import datetime
from decimal import Decimal
from src.data_processor.data_processor import DataProcessor, ProcessedInvoice


class TestBug8DateSubstitution:
    """Тесты для проверки обработки отсутствующих дат"""

    @pytest.fixture
    def data_processor(self):
        """Создаёт DataProcessor без client"""
        return DataProcessor(bitrix_client=None)

    def test_missing_invoice_date_stays_none(self, data_processor):
        """
        БАГ-8 FIX: Отсутствующая дата счёта должна остаться None
        """
        # Arrange
        raw_data = {
            "accountNumber": "INV-001",
            "company_inn": "1234567890",
            "company_name": "ООО Тест",
            "opportunity": "10000",
            "taxValue": "20",
            # begindate отсутствует → invoice_date должен быть None
            "UFCRM_SMART_INVOICE_1651168135187": "2025-01-15T10:00:00+03:00",
            "UFCRM_626D6ABE98692": None
        }
        
        # Act
        result = data_processor._process_single_invoice(raw_data)
        
        # Assert
        assert result.invoice_date is None  # БАГ-8 FIX: None, а НЕ datetime.now()
        assert not result.is_valid  # Счёт невалиден
        assert 'Отсутствует дата счета' in result.validation_errors

    def test_missing_shipping_date_stays_none(self, data_processor):
        """
        БАГ-8 FIX: Отсутствующая дата отгрузки должна остаться None
        """
        # Arrange
        raw_data = {
            "accountNumber": "INV-002",
            "company_inn": "1234567890",
            "company_name": "ООО Тест",
            "opportunity": "10000",
            "taxValue": "20",
            "begindate": "2025-01-10T10:00:00+03:00",
            # UFCRM_SMART_INVOICE_1651168135187 отсутствует → shipping_date должен быть None
            "UFCRM_626D6ABE98692": None
        }
        
        # Act
        result = data_processor._process_single_invoice(raw_data)
        
        # Assert
        assert result.shipping_date is None  # БАГ-8 FIX: None, а НЕ datetime.now()
        assert not result.is_valid  # Счёт невалиден
        assert 'Отсутствует дата отгрузки' in result.validation_errors

    def test_both_dates_missing_marked_invalid(self, data_processor):
        """
        БАГ-8 FIX: Счёт с обеими отсутствующими датами должен быть невалидным
        """
        # Arrange
        raw_data = {
            "accountNumber": "INV-003",
            "company_inn": "1234567890",
            "company_name": "ООО Тест",
            "opportunity": "10000",
            "taxValue": "20",
            # begindate и UFCRM_SMART_INVOICE_1651168135187 отсутствуют
            "UFCRM_626D6ABE98692": None
        }
        
        # Act
        result = data_processor._process_single_invoice(raw_data)
        
        # Assert
        assert result.invoice_date is None
        assert result.shipping_date is None
        assert not result.is_valid
        assert 'Отсутствует дата счета' in result.validation_errors
        assert 'Отсутствует дата отгрузки' in result.validation_errors

    def test_valid_invoice_date_parsing_attempt(self, data_processor):
        """
        Тест: Проверяем, что при наличии дат в сырых данных они парсятся
        (или остаются None если парсинг не удался, но НЕ подменяются на datetime.now())
        """
        # Arrange
        raw_data = {
            "accountNumber": "INV-004",
            "company_inn": "1234567890",
            "company_name": "ООО Тест",
            "opportunity": "10000",
            "taxValue": "20",
            "begindate": "2025-01-10T10:00:00+03:00",
            "UFCRM_SMART_INVOICE_1651168135187": "2025-01-15T10:00:00+03:00",
            "UFCRM_626D6ABE98692": "2025-01-20T10:00:00+03:00"
        }
        
        # Act
        now_before = datetime.now()
        result = data_processor._process_single_invoice(raw_data)
        now_after = datetime.now()
        
        # Assert - КРИТИЧНО: даты НЕ должны быть текущим временем
        # Если дата None - это нормально (парсинг не удался)
        # Если дата не None - она НЕ должна быть между now_before и now_after (т.е. НЕ datetime.now())
        if result.invoice_date is not None:
            is_current_time = now_before <= result.invoice_date <= now_after
            assert not is_current_time, "БАГ-8: invoice_date подменена на datetime.now()!"
        
        if result.shipping_date is not None:
            is_current_time = now_before <= result.shipping_date <= now_after
            assert not is_current_time, "БАГ-8: shipping_date подменена на datetime.now()!"

    def test_error_invoice_has_none_dates(self, data_processor):
        """
        БАГ-8 FIX: При ошибке обработки даты должны быть None
        """
        # Arrange - намеренно создаём некорректные данные
        raw_data = {
            "accountNumber": "INV-005",
            # Отсутствуют критичные поля → вызовет исключение
            "opportunity": "invalid_amount",
        }
        
        # Act
        processed = data_processor.process_invoice_batch([raw_data])
        
        # Assert
        assert len(processed) == 1
        result = processed[0]
        
        # БАГ-8 FIX: Даты должны быть None, а НЕ datetime.now()
        assert result.invoice_date is None
        assert result.shipping_date is None
        assert not result.is_valid
        # ИНН может быть либо 'ERROR', либо 'Не найдено' - главное что даты None
        assert result.inn in ['ERROR', 'Не найдено']

    def test_dates_not_substituted_with_current_time(self, data_processor):
        """
        БАГ-8 CRITICAL: Проверяем, что отсутствующие даты НЕ подменяются на текущее время
        """
        # Arrange
        now_before = datetime.now()
        
        raw_data = {
            "accountNumber": "INV-006",
            "company_inn": "1234567890",
            "company_name": "ООО Тест",
            "opportunity": "10000",
            "taxValue": "20",
            # begindate, UFCRM_SMART_INVOICE_1651168135187 отсутствуют
        }
        
        # Act
        result = data_processor._process_single_invoice(raw_data)
        
        now_after = datetime.now()
        
        # Assert - КРИТИЧЕСКАЯ ПРОВЕРКА
        # Если бы даты подменялись на datetime.now(), они были бы между now_before и now_after
        if result.invoice_date is not None:
            # Если дата НЕ None, проверяем что она НЕ между now_before и now_after
            # (т.е. не была подменена на текущее время)
            is_substituted = now_before <= result.invoice_date <= now_after
            assert not is_substituted, "БАГ-8: invoice_date была подменена на datetime.now()!"
        else:
            # БАГ-8 FIX: Дата должна быть None
            assert result.invoice_date is None

    def test_processed_invoice_type_hints(self):
        """
        БАГ-8 FIX: Проверяем, что типы в ProcessedInvoice корректны
        """
        # Arrange & Act
        from typing import get_type_hints
        hints = get_type_hints(ProcessedInvoice)
        
        # Assert - проверяем что типы дат Optional
        import typing
        
        # Извлекаем тип invoice_date
        invoice_date_type = hints['invoice_date']
        shipping_date_type = hints['shipping_date']
        payment_date_type = hints['payment_date']
        
        # Проверяем что все три Optional
        # В Python 3.10+ Optional[X] == Union[X, None]
        assert 'Optional' in str(invoice_date_type) or 'None' in str(invoice_date_type)
        assert 'Optional' in str(shipping_date_type) or 'None' in str(shipping_date_type)
        assert 'Optional' in str(payment_date_type) or 'None' in str(payment_date_type)
