"""
Тесты для БАГ-6: Проверка правильности структуры ответа get_requisite_details

БАГ-6: response.data содержит вложенный ключ "requisite", но код обращается к RQ_INN напрямую

Проверяем, что:
1. get_requisite_details возвращает правильную структуру
2. get_company_info_by_invoice корректно извлекает RQ_INN и RQ_COMPANY_NAME
3. Обработка случаев с отсутствующими полями
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.bitrix24_client.client import Bitrix24Client, APIResponse


class TestBug6RequisiteStructure:
    """Тесты для проверки правильности извлечения реквизитов"""

    @pytest.fixture
    def mock_bitrix_client(self):
        """Создаёт мок Bitrix24Client"""
        return Bitrix24Client("https://test.bitrix24.ru/rest/123/abc/")

    def test_get_requisite_details_returns_correct_structure(self, mock_bitrix_client):
        """
        Тест: get_requisite_details возвращает структуру без вложенного ключа 'requisite'
        
        Согласно документации Bitrix24, crm.requisite.get возвращает:
        {
            "result": {
                "ID": "27",
                "RQ_INN": "7717586110",
                "RQ_COMPANY_NAME": "ООО ...",
                ...
            }
        }
        
        _handle_response извлекает "result", поэтому response.data уже содержит
        прямой объект реквизита.
        """
        # Arrange
        requisite_data = {
            "ID": "27",
            "RQ_INN": "7717586110",
            "RQ_COMPANY_NAME": "ООО \"ТЕСТОВАЯ\"",
            "RQ_NAME": "Иванов Иван Иванович",
            "ACTIVE": "Y"
        }
        
        mock_response = APIResponse(
            data=requisite_data,  # response.data уже содержит "result"
            headers={},
            status_code=200,
            success=True
        )
        
        with patch.object(mock_bitrix_client, '_make_request', return_value=mock_response):
            # Act
            result = mock_bitrix_client.get_requisite_details(27)
        
        # Assert
        assert result is not None
        assert result.get("RQ_INN") == "7717586110"
        assert result.get("RQ_COMPANY_NAME") == "ООО \"ТЕСТОВАЯ\""
        assert result.get("ID") == "27"

    def test_get_company_info_by_invoice_extracts_fields_correctly(self, mock_bitrix_client):
        """
        БАГ-6 CHECK: Проверяем, что get_company_info_by_invoice корректно извлекает
        RQ_INN и RQ_COMPANY_NAME из результата get_requisite_details
        """
        # Arrange - мок для поиска счёта
        invoice_response = APIResponse(
            data={"items": [{"id": "100"}]},
            headers={},
            status_code=200,
            success=True
        )
        
        # Мок для получения связей реквизитов
        requisite_links = [{"REQUISITE_ID": "27"}]
        
        # Мок для получения реквизитов (БАГ-6: структура без вложенного "requisite")
        requisite_data = {
            "ID": "27",
            "RQ_INN": "7717586110",
            "RQ_COMPANY_NAME": "ООО \"1С-БИТРИКС\"",
            "RQ_NAME": None
        }
        
        with patch.object(mock_bitrix_client, '_make_request', return_value=invoice_response):
            with patch.object(mock_bitrix_client, 'get_requisite_links', return_value=requisite_links):
                with patch.object(mock_bitrix_client, 'get_requisite_details', return_value=requisite_data):
                    # Act
                    company_name, inn = mock_bitrix_client.get_company_info_by_invoice("INV-001")
        
        # Assert
        assert inn == "7717586110"
        assert company_name == "ООО \"1С-БИТРИКС\""

    def test_get_company_info_handles_missing_requisite_fields(self, mock_bitrix_client):
        """
        Тест: Обработка случаев, когда RQ_INN или RQ_COMPANY_NAME отсутствуют
        """
        # Arrange
        invoice_response = APIResponse(
            data={"items": [{"id": "100"}]},
            headers={},
            status_code=200,
            success=True
        )
        
        requisite_links = [{"REQUISITE_ID": "27"}]
        
        # Реквизит без полей (все None или пустые)
        requisite_data = {
            "ID": "27",
            "RQ_INN": "",
            "RQ_COMPANY_NAME": "",
            "RQ_NAME": ""
        }
        
        with patch.object(mock_bitrix_client, '_make_request', return_value=invoice_response):
            with patch.object(mock_bitrix_client, 'get_requisite_links', return_value=requisite_links):
                with patch.object(mock_bitrix_client, 'get_requisite_details', return_value=requisite_data):
                    # Act
                    company_name, inn = mock_bitrix_client.get_company_info_by_invoice("INV-001")
        
        # Assert - должны быть возвращены пустые строки или fallback значения
        # Код использует RQ_NAME как fallback для ИП
        assert isinstance(company_name, (str, type(None)))
        assert isinstance(inn, (str, type(None)))

    def test_get_requisite_details_with_none_response(self, mock_bitrix_client):
        """
        Тест: Обработка случая, когда API возвращает None (реквизит не найден)
        """
        # Arrange
        mock_response = APIResponse(
            data=None,
            headers={},
            status_code=200,
            success=True
        )
        
        with patch.object(mock_bitrix_client, '_make_request', return_value=mock_response):
            # Act
            result = mock_bitrix_client.get_requisite_details(999)
        
        # Assert
        assert result is None

    def test_get_company_info_handles_no_requisite_links(self, mock_bitrix_client):
        """
        Тест: Обработка случая, когда у счёта нет связанных реквизитов
        """
        # Arrange
        invoice_response = APIResponse(
            data={"items": [{"id": "100"}]},
            headers={},
            status_code=200,
            success=True
        )
        
        with patch.object(mock_bitrix_client, '_make_request', return_value=invoice_response):
            with patch.object(mock_bitrix_client, 'get_requisite_links', return_value=[]):
                # Act
                company_name, inn = mock_bitrix_client.get_company_info_by_invoice("INV-001")
        
        # Assert
        assert company_name == "Нет реквизитов"
        assert inn == "Нет реквизитов"
