"""Кастомные исключения для Bitrix24 API Client"""


class Bitrix24APIError(Exception):
    """Базовое исключение для всех ошибок Bitrix24 API"""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def is_retryable(self) -> bool:
        """Определяет, можно ли повторить запрос"""
        return False

    def is_rate_limit_error(self) -> bool:
        """Проверяет, является ли ошибка превышением лимитов"""
        return False


class RateLimitError(Bitrix24APIError):
    """Ошибка превышения лимита запросов (429 Too Many Requests)"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)

    def is_retryable(self) -> bool:
        return True

    def is_rate_limit_error(self) -> bool:
        return True


class ServerError(Bitrix24APIError):
    """Ошибки сервера (5xx)"""

    def is_retryable(self) -> bool:
        return True


class AuthenticationError(Bitrix24APIError):
    """Ошибки аутентификации (401, 403)"""

    pass


class NetworkError(Bitrix24APIError):
    """Ошибки сети и соединения"""

    def is_retryable(self) -> bool:
        return True


class BadRequestError(Bitrix24APIError):
    """Ошибки в запросе (400)"""

    pass


class NotFoundError(Bitrix24APIError):
    """Ресурс не найден (404)"""

    pass


class TimeoutError(Bitrix24APIError):
    """Ошибка таймаута запроса"""

    def is_retryable(self) -> bool:
        return True
