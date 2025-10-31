"""
Bitrix24 API Client Module
Модуль для работы с Bitrix24 REST API

Компоненты:
- client.py: основной API клиент
- rate_limiter.py: контроль лимитов запросов
- exceptions.py: кастомные исключения
- retry_decorator.py: декоратор для retry с exponential backoff (v2.1.2)
- api_cache.py: кэширование API запросов
"""

from .client import Bitrix24Client
from .rate_limiter import AdaptiveRateLimiter
from .exceptions import (
    Bitrix24APIError,
    RateLimitError,
    ServerError,
    AuthenticationError,
    NetworkError,
    BadRequestError,
    NotFoundError,
    TimeoutError,
)
from .api_cache import APIDataCache, get_api_cache, get_cache

__all__ = [
    # Client
    "Bitrix24Client",
    # Rate limiting
    "AdaptiveRateLimiter",
    # Exceptions
    "Bitrix24APIError",
    "RateLimitError",
    "ServerError",
    "AuthenticationError",
    "NetworkError",
    "BadRequestError",
    "NotFoundError",
    "TimeoutError",
    # Cache
    "APIDataCache",
    "get_api_cache",
    "get_cache",
]
