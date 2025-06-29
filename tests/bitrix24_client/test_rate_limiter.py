"""
Unit тесты для адаптивного Rate Limiter.
Проверяют соблюдение лимитов и адаптивное поведение.
"""
import pytest
import time
from unittest.mock import patch
from src.bitrix24_client.rate_limiter import AdaptiveRateLimiter


class TestAdaptiveRateLimiter:
    """Тесты основного функционала rate limiter"""
    
    def test_initialization(self):
        """Тест: инициализация с корректными параметрами"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=2.0)
        assert limiter.max_requests_per_second == 2.0
        assert limiter.min_interval == 0.5  # 1/2 = 0.5 секунды
        
        stats = limiter.get_stats()
        assert stats["total_requests"] == 0
        assert stats["current_interval"] == 0.5
    
    def test_basic_rate_limiting(self):
        """Тест: базовое ограничение скорости"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=4.0)  # 0.25с между запросами
        
        # Первый запрос должен пройти сразу
        start_time = time.time()
        limiter.acquire()
        first_request_time = time.time() - start_time
        assert first_request_time < 0.1  # Должно быть быстро
        
        # Второй запрос должен ждать
        start_time = time.time()
        limiter.acquire()
        second_request_time = time.time() - start_time
        assert second_request_time >= 0.2  # Должно быть около 0.25с
    
    def test_rate_limit_response_handling(self):
        """Тест: обработка 429 ответа"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=2.0)
        
        # Эмулируем 429 ответ с Retry-After
        headers = {"Retry-After": "2"}
        limiter.update_from_response(headers, status_code=429)
        
        stats = limiter.get_stats()
        assert stats["retry_after"] > 1.5  # Должно быть около 2 секунд
        assert stats["current_interval"] > 0.5  # Интервал должен увеличиться
    
    def test_rate_limit_headers_parsing(self):
        """Тест: парсинг заголовков лимитов"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=2.0)
        
        # Эмулируем заголовки с оставшимися лимитами
        future_time = int(time.time()) + 60  # Через минуту
        headers = {
            "X-RateLimit-Remaining": "10",
            "X-RateLimit-Reset": str(future_time)
        }
        
        initial_interval = limiter._current_interval
        limiter.update_from_response(headers, status_code=200)
        
        # Интервал должен адаптироваться
        # При 10 запросах на 60 секунд = 6 секунд на запрос
        assert limiter._current_interval >= initial_interval
    
    def test_stats_collection(self):
        """Тест: сбор статистики"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=3.0)
        
        # Делаем несколько запросов
        limiter.acquire()
        limiter.acquire()
        
        stats = limiter.get_stats()
        assert stats["total_requests"] == 2
        assert stats["max_requests_per_second"] == 3.0
        assert "current_interval" in stats
        assert "last_request_time" in stats
    
    def test_reset_functionality(self):
        """Тест: сброс состояния лимитера"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=2.0)
        
        # Используем лимитер
        limiter.acquire()
        limiter.acquire()
        
        # Эмулируем rate limit
        headers = {"Retry-After": "5"}
        limiter.update_from_response(headers, status_code=429)
        
        stats_before = limiter.get_stats()
        assert stats_before["total_requests"] > 0
        
        # Сбрасываем
        limiter.reset()
        
        stats_after = limiter.get_stats()
        assert stats_after["total_requests"] == 0
        assert stats_after["retry_after"] == 0
        assert stats_after["current_interval"] == 0.5  # Восстановлен минимальный


class TestRateLimiterEdgeCases:
    """Тесты граничных случаев"""
    
    def test_zero_remaining_requests(self):
        """Тест: когда остается 0 запросов"""
        limiter = AdaptiveRateLimiter()
        
        future_time = int(time.time()) + 30
        headers = {
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(future_time)
        }
        
        limiter.update_from_response(headers, status_code=200)
        
        stats = limiter.get_stats()
        assert stats["retry_after"] > 25  # Должно ждать почти 30 секунд
    
    def test_malformed_headers(self):
        """Тест: некорректные заголовки"""
        limiter = AdaptiveRateLimiter()
        
        # Некорректные заголовки не должны ломать лимитер
        headers = {
            "X-RateLimit-Remaining": "invalid",
            "X-RateLimit-Reset": "not_a_number",
            "Retry-After": "also_invalid"
        }
        
        limiter.update_from_response(headers, status_code=429)
        
        # Лимитер должен продолжать работать
        stats = limiter.get_stats()
        assert isinstance(stats["total_requests"], int)
    
    def test_very_high_rate_limit(self):
        """Тест: очень высокий лимит запросов"""
        limiter = AdaptiveRateLimiter(max_requests_per_second=100.0)
        
        # Минимальный интервал должен быть разумным
        assert limiter.min_interval == 0.01  # 1/100
        
        # Быстрые запросы должны проходить без задержек
        start_time = time.time()
        for _ in range(5):
            limiter.acquire()
        total_time = time.time() - start_time
        
        # При высоком лимите общее время должно быть небольшим
        assert total_time < 0.5


@pytest.mark.unit
def test_concurrent_access():
    """Тест: потокобезопасность (имитация)"""
    import threading
    
    limiter = AdaptiveRateLimiter(max_requests_per_second=5.0)
    results = []
    
    def make_requests():
        for _ in range(3):
            start = time.time()
            limiter.acquire()
            results.append(time.time() - start)
    
    # Запускаем 2 потока одновременно
    threads = [threading.Thread(target=make_requests) for _ in range(2)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Проверяем, что все запросы обработались
    assert len(results) == 6
    assert limiter.get_stats()["total_requests"] == 6


@pytest.mark.unit
def test_retry_after_wait_logic():
    """Тест: логика ожидания после retry_after"""
    with patch('time.sleep') as mock_sleep, patch('time.time') as mock_time:
        # Настраиваем mock времени
        mock_time.side_effect = [100.0, 100.0, 102.0, 102.0, 102.0]
        
        limiter = AdaptiveRateLimiter()
        
        # Устанавливаем retry_after в будущее
        limiter._retry_after = 102.0
        
        # Вызываем acquire
        limiter.acquire()
        
        # Проверяем что sleep был вызван с правильным временем
        mock_sleep.assert_called()


@pytest.mark.unit
def test_header_parsing_value_errors():
    """Тест: ValueError при парсинге заголовков"""
    limiter = AdaptiveRateLimiter()
    
    # Тестируем ValueError в _parse_rate_limit_remaining
    headers_remaining = {"x-ratelimit-remaining": "invalid_number"}
    result = limiter._parse_rate_limit_remaining(headers_remaining)
    assert result is None
    
    # Тестируем ValueError в _parse_rate_limit_reset  
    headers_reset = {"x-ratelimit-reset": "not_a_timestamp"}
    result = limiter._parse_rate_limit_reset(headers_reset)
    assert result is None 