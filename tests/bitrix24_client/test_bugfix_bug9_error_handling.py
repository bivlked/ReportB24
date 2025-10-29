"""
Тесты для БАГ-9: Улучшенная обработка ошибок в get_products_by_invoice

Проблема:
- Метод проглатывал все исключения (401/403, 404, сетевые ошибки)
- Возвращал пустой список [] во всех случаях
- Невозможно отличить "пустой результат" от "произошла ошибка"

Решение:
- Возвращаем Dict с полями: products, has_error, error_message
- Различаем ожидаемые пустые результаты и реальные ошибки
- Логируем критические ошибки отдельно
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.bitrix24_client.client import Bitrix24Client
from src.bitrix24_client.exceptions import (
    AuthenticationError,
    ServerError,
    NetworkError,
    TimeoutError as APITimeoutError,
    NotFoundError,
)


@pytest.fixture
def client():
    """Фикстура для Bitrix24Client"""
    return Bitrix24Client("https://test.bitrix24.ru/rest/123/abc/")


@pytest.fixture(autouse=True)
def clear_cache():
    """Очистка кэша перед каждым тестом"""
    from src.bitrix24_client.api_cache import get_cache
    cache = get_cache()
    cache._product_cache.clear()
    cache._company_cache.clear()
    cache._invoice_cache.clear()
    cache._general_cache.clear()
    yield
    cache._product_cache.clear()
    cache._company_cache.clear()
    cache._invoice_cache.clear()
    cache._general_cache.clear()


class TestBug9ErrorHandling:
    """Тесты для БАГ-9: обработка ошибок в get_products_by_invoice"""

    def test_successful_products_retrieval(self, client):
        """
        БАГ-9: Успешное получение товаров возвращает корректную структуру.
        """
        # Arrange
        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {"productRows": [{"id": 1, "name": "Product 1"}]}

        with patch.object(client, "_make_request", return_value=mock_response):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict), "Результат должен быть Dict"
            assert "products" in result
            assert "has_error" in result
            assert result["has_error"] is False
            assert len(result["products"]) == 1
            assert result["products"][0]["name"] == "Product 1"
            assert "error_message" not in result

    def test_empty_products_without_error(self, client):
        """
        БАГ-9: Пустой список товаров (ожидаемый случай) не должен помечаться как ошибка.
        """
        # Arrange
        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {"productRows": []}

        with patch.object(client, "_make_request", return_value=mock_response):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is False, "Пустой результат НЕ должен быть ошибкой"
            assert "error_message" not in result

    def test_authentication_error_returns_error_flag(self, client):
        """
        БАГ-9: AuthenticationError (401/403) должна возвращать has_error=True.
        """
        # Arrange
        with patch.object(
            client,
            "_make_request",
            side_effect=AuthenticationError("Unauthorized", status_code=401),
        ):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is True, "AuthenticationError должна помечаться как ошибка"
            assert "error_message" in result
            assert "AuthenticationError" in result["error_message"]

    def test_server_error_returns_error_flag(self, client):
        """
        БАГ-9: ServerError (5xx) должна возвращать has_error=True.
        """
        # Arrange
        with patch.object(
            client,
            "_make_request",
            side_effect=ServerError("Internal Server Error", status_code=500),
        ):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is True
            assert "error_message" in result
            assert "ServerError" in result["error_message"]

    def test_network_error_returns_error_flag(self, client):
        """
        БАГ-9: NetworkError должна возвращать has_error=True.
        """
        # Arrange
        with patch.object(
            client, "_make_request", side_effect=NetworkError("Connection refused")
        ):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is True
            assert "error_message" in result
            assert "NetworkError" in result["error_message"]

    def test_timeout_error_returns_error_flag(self, client):
        """
        БАГ-9: TimeoutError должна возвращать has_error=True.
        """
        # Arrange
        with patch.object(
            client, "_make_request", side_effect=APITimeoutError("Request timeout")
        ):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is True
            assert "error_message" in result
            assert "TimeoutError" in result["error_message"]

    def test_unexpected_error_returns_error_flag(self, client):
        """
        БАГ-9: Неожиданные исключения должны возвращать has_error=True.
        """
        # Arrange
        with patch.object(
            client, "_make_request", side_effect=ValueError("Unexpected error")
        ):
            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == []
            assert result["has_error"] is True
            assert "error_message" in result
            assert "Unexpected error" in result["error_message"]

    def test_cache_hit_returns_correct_structure(self, client):
        """
        БАГ-9: Кэшированный результат (List) должен оборачиваться в Dict.
        """
        # Arrange
        cached_products = [{"id": 1, "name": "Cached Product"}]

        with patch("src.bitrix24_client.client.get_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get.return_value = cached_products
            mock_get_cache.return_value = mock_cache

            # Act
            result = client.get_products_by_invoice(123)

            # Assert
            assert isinstance(result, dict)
            assert result["products"] == cached_products
            assert result["has_error"] is False

    def test_batch_method_handles_new_response_format(self, client):
        """
        БАГ-9: get_products_by_invoices_batch должен корректно обрабатывать новый формат.
        """
        # Arrange
        mock_response_success = {
            "products": [{"id": 1, "name": "Product 1"}],
            "has_error": False,
        }
        mock_response_error = {
            "products": [],
            "has_error": True,
            "error_message": "AuthenticationError: Unauthorized",
        }

        with patch.object(
            client,
            "get_products_by_invoice",
            side_effect=[mock_response_success, mock_response_error],
        ):
            # Act
            result = client.get_products_by_invoices_batch([123, 456])

            # Assert
            assert 123 in result
            assert 456 in result
            assert len(result[123]) == 1  # Успешно получены товары
            assert len(result[456]) == 0  # Ошибка, пустой список

    def test_empty_response_without_success_flag(self, client):
        """
        БАГ-9: Пустой ответ (response.success=False) должен кэшироваться и возвращать has_error=False.
        """
        # Arrange
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "No data"

        with patch.object(client, "_make_request", return_value=mock_response):
            with patch("src.bitrix24_client.client.get_cache") as mock_get_cache:
                mock_cache = Mock()
                mock_cache.get.return_value = None
                mock_get_cache.return_value = mock_cache

                # Act
                result = client.get_products_by_invoice(123)

                # Assert
                assert isinstance(result, dict)
                assert result["products"] == []
                assert result["has_error"] is False, "Пустой ответ НЕ должен быть ошибкой"
                # Проверяем что пустой список закэширован
                mock_cache.put.assert_called_once()
