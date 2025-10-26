"""
Тесты для БАГ-A2: Корректная проверка Bitrix24Client (v2.4.0).

Проверяет что методы _extract_smart_invoice_inn и _extract_smart_invoice_counterparty
используют 'is not None' вместо hasattr, что предотвращает AttributeError.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.data_processor.data_processor import DataProcessor


class TestBugA2ClientCheckFix:
    """Тесты для БАГ-A2: проверка клиента через 'is not None'"""
    
    @pytest.fixture
    def processor_with_client(self):
        """DataProcessor с мок-клиентом"""
        processor = DataProcessor()
        mock_client = Mock()
        mock_client.get_company_info_by_invoice = Mock(
            return_value=("ООО Тест", "1234567890")
        )
        processor.set_bitrix_client(mock_client)
        return processor
    
    @pytest.fixture
    def processor_without_client(self):
        """DataProcessor без клиента (None)"""
        processor = DataProcessor()
        processor.set_bitrix_client(None)
        return processor
    
    def test_extract_inn_with_none_client_no_error(self, processor_without_client):
        """
        Тест: _extract_smart_invoice_inn с клиентом None не вызывает AttributeError.
        
        БАГ-A2: hasattr всегда возвращал True (атрибут существует но None),
        что приводило к AttributeError при попытке вызова метода.
        Исправление: проверка 'is not None'.
        """
        raw_data = {
            'accountNumber': 'С-001/2024',
            'title': 'ООО Тест'
        }
        
        # Не должно быть AttributeError
        result = processor_without_client._extract_smart_invoice_inn(raw_data)
        
        # Должна вернуться пустая строка
        assert result == ""
    
    def test_extract_counterparty_with_none_client_no_error(self, processor_without_client):
        """
        Тест: _extract_smart_invoice_counterparty с клиентом None не вызывает AttributeError.
        
        БАГ-A2: Аналогично с методом извлечения контрагента.
        """
        raw_data = {
            'accountNumber': 'С-001/2024',
            'title': 'ООО Тест'
        }
        
        # Не должно быть AttributeError
        result = processor_without_client._extract_smart_invoice_counterparty(raw_data)
        
        # Должна вернуться пустая строка
        assert result == ""
    
    def test_extract_inn_with_client_calls_api(self, processor_with_client):
        """Тест: _extract_smart_invoice_inn с клиентом вызывает API"""
        raw_data = {
            'accountNumber': 'С-002/2024',
            'title': 'ООО Тест'
        }
        
        result = processor_with_client._extract_smart_invoice_inn(raw_data)
        
        # Проверяем что API был вызван
        processor_with_client._bitrix_client.get_company_info_by_invoice.assert_called_once_with('С-002/2024')
        
        # Проверяем результат
        assert result == "1234567890"
    
    def test_extract_counterparty_with_client_calls_api(self, processor_with_client):
        """Тест: _extract_smart_invoice_counterparty с клиентом вызывает API"""
        raw_data = {
            'accountNumber': 'С-003/2024',
            'title': 'ООО Тест'
        }
        
        result = processor_with_client._extract_smart_invoice_counterparty(raw_data)
        
        # Проверяем что API был вызван
        processor_with_client._bitrix_client.get_company_info_by_invoice.assert_called_once_with('С-003/2024')
        
        # Проверяем результат
        assert result == "ООО Тест"
    
    def test_extract_inn_without_account_number(self, processor_with_client):
        """Тест: без номера счета API не вызывается"""
        raw_data = {
            'accountNumber': '',
            'title': 'ООО Тест'
        }
        
        result = processor_with_client._extract_smart_invoice_inn(raw_data)
        
        # API не должен вызываться
        processor_with_client._bitrix_client.get_company_info_by_invoice.assert_not_called()
        assert result == ""
    
    def test_extract_inn_filters_error_values(self, processor_with_client):
        """Тест: фильтрация ошибочных значений ИНН"""
        processor_with_client._bitrix_client.get_company_info_by_invoice.return_value = (
            "ООО Тест", "Не найдено"
        )
        
        raw_data = {'accountNumber': 'С-004/2024'}
        result = processor_with_client._extract_smart_invoice_inn(raw_data)
        
        # "Не найдено" должно быть заменено на пустую строку
        assert result == ""
    
    def test_extract_counterparty_filters_error_values(self, processor_with_client):
        """Тест: фильтрация ошибочных значений контрагента"""
        processor_with_client._bitrix_client.get_company_info_by_invoice.return_value = (
            "Ошибка", "1234567890"
        )
        
        raw_data = {'accountNumber': 'С-005/2024'}
        result = processor_with_client._extract_smart_invoice_counterparty(raw_data)
        
        # "Ошибка" должна быть заменена на пустую строку
        assert result == ""
    
    def test_extract_inn_handles_api_exception(self, processor_with_client):
        """Тест: обработка исключений от API"""
        processor_with_client._bitrix_client.get_company_info_by_invoice.side_effect = Exception("API Error")
        
        raw_data = {'accountNumber': 'С-006/2024'}
        
        # Не должно быть необработанного исключения
        result = processor_with_client._extract_smart_invoice_inn(raw_data)
        
        # Должна вернуться пустая строка
        assert result == ""
    
    def test_extract_counterparty_handles_api_exception(self, processor_with_client):
        """Тест: обработка исключений от API для контрагента"""
        processor_with_client._bitrix_client.get_company_info_by_invoice.side_effect = Exception("API Error")
        
        raw_data = {'accountNumber': 'С-007/2024'}
        
        # Не должно быть необработанного исключения
        result = processor_with_client._extract_smart_invoice_counterparty(raw_data)
        
        # Должна вернуться пустая строка
        assert result == ""


class TestBugA2Integration:
    """Интеграционные тесты для БАГ-A2"""
    
    def test_no_attribute_error_in_batch_processing(self):
        """Тест: batch обработка без клиента не вызывает AttributeError"""
        processor = DataProcessor()
        processor.set_bitrix_client(None)
        
        raw_data = [
            {
                'accountNumber': 'С-100/2024',
                'ufCrmInn': '3321035160',
                'title': 'ООО "Тест"',
                'opportunity': '100000',
                'taxValue': '20000',
                'begindate': '2024-06-15T00:00:00',
                'closedate': '2024-06-20T00:00:00',
                'stageId': 'DT31_20:WON'
            }
        ]
        
        # Не должно быть AttributeError
        result = processor.process_invoice_batch(raw_data)
        
        assert len(result) == 1
        # ИНН будет извлечен из ufCrmInn (fallback), контрагент из title
        assert result[0].inn == '3321035160'  # Из ufCrmInn fallback
        assert result[0].counterparty == 'ООО "Тест"'  # Из title
        assert result[0].is_valid is True  # Данные валидны
