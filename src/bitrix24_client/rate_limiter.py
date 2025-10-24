"""
Адаптивный Rate Limiter для Bitrix24 API.
Гарантирует соблюдение лимита ≤2 запроса в секунду.
"""

import time
from typing import Optional, Dict, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Адаптивный контроллер лимитов запросов.

    Особенности:
    - Гарантированно ≤2 запроса в секунду
    - Адаптируется к ответам сервера
    - Учитывает заголовки X-RateLimit-*
    - Автоматическое восстановление после 429
    """

    def __init__(self, max_requests_per_second: float = 2.0):
        """
        Инициализация rate limiter.

        Args:
            max_requests_per_second: Максимальное количество запросов в секунду
        """
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second  # 0.5 секунды между запросами

        # Состояние лимитера
        self._last_request_time = 0.0
        self._request_count = 0
        self._lock = Lock()

        # Адаптивные настройки
        self._current_interval = self.min_interval
        self._retry_after = 0
        self._rate_limit_reset = 0

        logger.info(f"Rate limiter initialized: {max_requests_per_second} req/sec")

    def acquire(self) -> float:
        """
        Получить разрешение на запрос.

        Returns:
            float: Время ожидания до запроса в секундах
        """
        with self._lock:
            now = time.time()

            # Проверяем, нужно ли ждать после 429 ошибки
            if self._retry_after > 0:
                wait_time = max(0, self._retry_after - now)
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.2f}s due to rate limit")
                    time.sleep(wait_time)
                    now = time.time()
                self._retry_after = 0

            # Вычисляем время с последнего запроса
            time_since_last = now - self._last_request_time

            # Если прошло недостаточно времени, ждём
            if time_since_last < self._current_interval:
                wait_time = self._current_interval - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.3f}s")
                time.sleep(wait_time)
                now = time.time()

            # Обновляем состояние
            self._last_request_time = now
            self._request_count += 1

            return 0.0

    def update_from_response(
        self, response_headers: Dict[str, str], status_code: int = 200
    ):
        """
        Обновить состояние лимитера на основе ответа сервера.

        Args:
            response_headers: Заголовки ответа
            status_code: HTTP статус код
        """
        with self._lock:
            # Обрабатываем 429 ошибку
            if status_code == 429:
                retry_after = self._parse_retry_after(response_headers)
                if retry_after:
                    self._retry_after = time.time() + retry_after
                    logger.warning(f"Rate limit hit, retry after {retry_after}s")
                else:
                    # Если Retry-After не указан, используем экспоненциальную задержку
                    self._retry_after = time.time() + (self._current_interval * 2)
                    logger.warning("Rate limit hit, using exponential backoff")

                # Увеличиваем интервал между запросами
                self._current_interval = min(self._current_interval * 1.5, 2.0)
                return

            # Обрабатываем заголовки лимитов
            remaining = self._parse_rate_limit_remaining(response_headers)
            reset_time = self._parse_rate_limit_reset(response_headers)

            if remaining is not None and reset_time is not None:
                self._adapt_to_rate_limits(remaining, reset_time)

    def _parse_retry_after(self, headers: Dict[str, str]) -> Optional[int]:
        """Парсинг заголовка Retry-After"""
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None

    def _parse_rate_limit_remaining(self, headers: Dict[str, str]) -> Optional[int]:
        """Парсинг оставшихся запросов"""
        for header_name in ["X-RateLimit-Remaining", "x-ratelimit-remaining"]:
            if header_name in headers:
                try:
                    return int(headers[header_name])
                except ValueError:
                    pass
        return None

    def _parse_rate_limit_reset(self, headers: Dict[str, str]) -> Optional[int]:
        """Парсинг времени сброса лимитов"""
        for header_name in ["X-RateLimit-Reset", "x-ratelimit-reset"]:
            if header_name in headers:
                try:
                    return int(headers[header_name])
                except ValueError:
                    pass
        return None

    def _adapt_to_rate_limits(self, remaining: int, reset_time: int):
        """
        Адаптация интервала на основе оставшихся лимитов.

        Args:
            remaining: Оставшееся количество запросов
            reset_time: Время сброса лимитов (timestamp)
        """
        now = time.time()
        time_until_reset = reset_time - now

        if time_until_reset > 0 and remaining > 0:
            # Вычисляем оптимальный интервал
            optimal_interval = time_until_reset / remaining

            # Используем максимум из минимального интервала и оптимального
            self._current_interval = max(self.min_interval, optimal_interval)

            logger.debug(
                f"Adapted interval to {self._current_interval:.3f}s "
                f"(remaining: {remaining}, reset in: {time_until_reset:.1f}s)"
            )
        elif remaining == 0:
            # Если запросы исчерпаны, ждём до сброса
            self._retry_after = reset_time
            logger.info(f"Rate limit exhausted, waiting until {reset_time}")

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику работы лимитера"""
        with self._lock:
            return {
                "total_requests": self._request_count,
                "current_interval": self._current_interval,
                "max_requests_per_second": self.max_requests_per_second,
                "retry_after": (
                    max(0, self._retry_after - time.time())
                    if self._retry_after > 0
                    else 0
                ),
                "last_request_time": self._last_request_time,
            }

    def reset(self):
        """Сброс состояния лимитера"""
        with self._lock:
            self._last_request_time = 0.0
            self._request_count = 0
            self._current_interval = self.min_interval
            self._retry_after = 0
            self._rate_limit_reset = 0
            logger.info("Rate limiter reset")
