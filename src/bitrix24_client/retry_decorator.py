"""
Декоратор для автоматического retry API запросов с exponential backoff

🔥 НОВОЕ (v2.1.2): Устойчивость к временным сбоям API
- Exponential backoff: 1s, 2s, 4s, 8s...
- Настраиваемые HTTP коды для retry (429, 500, 502, 503, 504)
- Логирование попыток
- Thread-safe
"""

import time
import functools
from typing import Callable, Any, Tuple, Type
from requests.exceptions import RequestException, HTTPError
import logging

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Исключение когда все retry попытки исчерпаны"""

    pass


def retry_on_api_error(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retryable_codes: Tuple[int, ...] = (429, 500, 502, 503, 504),
    exceptions: Tuple[Type[Exception], ...] = (RequestException, ConnectionError),
    log_attempts: bool = True,
):
    """
    Декоратор для retry с exponential backoff

    Args:
        max_retries: Максимальное количество попыток (по умолчанию 3)
        backoff_factor: Базовый фактор задержки в секундах (по умолчанию 1.0)
        retryable_codes: Tuple HTTP кодов, для которых применяется retry
        exceptions: Tuple типов исключений, для которых применяется retry
        log_attempts: Логировать попытки (по умолчанию True)

    Returns:
        Декорированная функция с retry логикой

    Example:
        @retry_on_api_error(max_retries=5, backoff_factor=2.0)
        def api_call():
            return requests.get('https://api.example.com')
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    # Пытаемся выполнить функцию
                    result = func(*args, **kwargs)

                    # Успешное выполнение
                    if log_attempts and attempt > 1:
                        logger.info(
                            f"✅ {func.__name__} успешно выполнен "
                            f"после {attempt} попыток"
                        )

                    return result

                except HTTPError as e:
                    # Проверяем HTTP код
                    if hasattr(e, "response") and e.response is not None:
                        status_code = e.response.status_code

                        if status_code not in retryable_codes:
                            # Не retry для неподходящих кодов
                            if log_attempts:
                                logger.error(
                                    f"❌ HTTP {status_code} для {func.__name__}, "
                                    f"retry не применяется"
                                )
                            raise

                    last_exception = e

                except exceptions as e:
                    # Сохраняем исключение для повтора
                    last_exception = e

                # Если это не последняя попытка, ждем и повторяем
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s, 8s...
                    delay = backoff_factor * (2 ** (attempt - 1))

                    if log_attempts:
                        logger.warning(
                            f"⚠️ {func.__name__} попытка {attempt}/{max_retries} не удалась: "
                            f"{type(last_exception).__name__}: {last_exception}. "
                            f"Повтор через {delay:.1f}с..."
                        )

                    time.sleep(delay)
                else:
                    # Последняя попытка исчерпана
                    if log_attempts:
                        logger.error(
                            f"❌ Все {max_retries} попытки исчерпаны для {func.__name__}"
                        )

            # Если все попытки исчерпаны, бросаем последнее исключение
            if last_exception is not None:
                raise last_exception

            # Теоретически недостижимо, но для безопасности
            raise RetryExhaustedError(
                f"Retry исчерпаны для {func.__name__} без записи исключения"
            )

        return wrapper

    return decorator
