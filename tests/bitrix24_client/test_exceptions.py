"""
Unit тесты для исключений Bitrix24 API Client.
Покрывают всю логику обработки ошибок.
"""
import pytest
from src.bitrix24_client.exceptions import (
    Bitrix24APIError,
    RateLimitError,
    ServerError,
    AuthenticationError,
    NetworkError,
    BadRequestError,
    NotFoundError,
    TimeoutError,
)


class TestBitrix24APIError:
    """Тесты базового исключения"""
    
    def test_basic_exception_creation(self):
        """Тест: создание базового исключения"""
        error = Bitrix24APIError("Test error", status_code=400)
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code == 400
    
    def test_default_retryable_behavior(self):
        """Тест: по умолчанию ошибки не повторяемые"""
        error = Bitrix24APIError("Test error")
        assert not error.is_retryable()
        assert not error.is_rate_limit_error()


class TestRateLimitError:
    """Тесты ошибки превышения лимитов"""
    
    def test_rate_limit_error_creation(self):
        """Тест: создание ошибки rate limit"""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.status_code == 429
    
    def test_rate_limit_error_retryable(self):
        """Тест: ошибка rate limit повторяемая"""
        error = RateLimitError()
        assert error.is_retryable()
        assert error.is_rate_limit_error()
    
    def test_default_message(self):
        """Тест: сообщение по умолчанию"""
        error = RateLimitError()
        assert "Rate limit exceeded" in str(error)


class TestServerError:
    """Тесты серверных ошибок"""
    
    def test_server_error_retryable(self):
        """Тест: серверные ошибки повторяемые"""
        error = ServerError("Internal server error", status_code=500)
        assert error.is_retryable()
        assert not error.is_rate_limit_error()
    
    def test_inheritance(self):
        """Тест: наследование от базового исключения"""
        error = ServerError("Server error")
        assert isinstance(error, Bitrix24APIError)


class TestAuthenticationError:
    """Тесты ошибок аутентификации"""
    
    def test_authentication_error_not_retryable(self):
        """Тест: ошибки аутентификации не повторяемые"""
        error = AuthenticationError("Invalid token")
        assert not error.is_retryable()
        assert not error.is_rate_limit_error()


class TestNetworkError:
    """Тесты сетевых ошибок"""
    
    def test_network_error_retryable(self):
        """Тест: сетевые ошибки повторяемые"""
        error = NetworkError("Connection failed")
        assert error.is_retryable()
        assert not error.is_rate_limit_error()


class TestAdditionalExceptions:
    """Тесты дополнительных исключений"""
    
    def test_bad_request_error(self):
        """Тест: ошибка bad request"""
        error = BadRequestError("Invalid parameters")
        assert str(error) == "Invalid parameters"
        assert not error.is_retryable()
        assert isinstance(error, Bitrix24APIError)
    
    def test_not_found_error(self):
        """Тест: ошибка not found"""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert not error.is_retryable()
        assert isinstance(error, Bitrix24APIError)
    
    def test_timeout_error(self):
        """Тест: ошибка timeout"""
        error = TimeoutError("Request timeout")
        assert str(error) == "Request timeout"
        assert error.is_retryable()  # Timeout ошибки повторяемые
        assert isinstance(error, Bitrix24APIError)


@pytest.mark.unit
def test_all_exceptions_inherit_from_base():
    """Тест: все исключения наследуются от базового"""
    from src.bitrix24_client.exceptions import BadRequestError, NotFoundError, TimeoutError
    
    exceptions = [
        RateLimitError("test"),
        ServerError("test"),
        AuthenticationError("test"),
        NetworkError("test"),
        BadRequestError("test"),
        NotFoundError("test"),
        TimeoutError("test"),
    ]
    
    for exception in exceptions:
        assert isinstance(exception, Bitrix24APIError)
        assert isinstance(exception, Exception) 