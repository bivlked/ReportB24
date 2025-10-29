"""
Тесты для БАГ-7: Кэширование отсутствующих данных (None)

БАГ-7: Кэш отказывается сохранять None, повторные запросы к API

Проверяем, что:
1. None значения кэшируются используя sentinel
2. Sentinel преобразуется обратно в None при извлечении
3. Cache HIT работает для sentinel значений
4. Метрики кэша корректны для sentinel
"""

import pytest
from datetime import datetime
from src.bitrix24_client.api_cache import APIDataCache, CACHE_SENTINEL_NONE


class TestBug7CacheNone:
    """Тесты для проверки кэширования None значений"""

    @pytest.fixture
    def cache(self):
        """Создаёт новый экземпляр кэша"""
        return APIDataCache()

    def test_put_none_creates_sentinel(self, cache):
        """
        БАГ-7 FIX: Тест проверяет, что None преобразуется в sentinel при кэшировании
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "999"}
        
        # Act
        cache.put(method, params, None)
        
        # Assert - проверяем что в кэше sentinel, а не None
        cache_key = cache._generate_cache_key(method, params)
        entry = cache._general_cache.get(cache_key)
        
        assert entry is not None
        assert entry.data == CACHE_SENTINEL_NONE
        assert entry.data != None

    def test_get_sentinel_returns_none(self, cache):
        """
        БАГ-7 FIX: Тест проверяет, что sentinel преобразуется обратно в None
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "999"}
        cache.put(method, params, None)  # Кэшируем None
        
        # Act
        result = cache.get(method, params)
        
        # Assert
        assert result is None  # Должен вернуть None, а не sentinel

    def test_cache_hit_for_none_values(self, cache):
        """
        БАГ-7 FIX: Проверяем, что повторный запрос после кэширования None
        возвращает cache HIT (а не cache MISS)
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "999"}
        
        # Act - первый запрос кэширует None
        cache.put(method, params, None)
        
        # Сбрасываем счётчики
        initial_hits = cache._hits
        initial_misses = cache._misses
        
        # Второй запрос должен быть cache HIT
        result = cache.get(method, params)
        
        # Assert
        assert result is None
        assert cache._hits == initial_hits + 1  # +1 hit
        assert cache._misses == initial_misses  # misses не изменились

    def test_cache_miss_for_non_cached_none(self, cache):
        """
        Тест: Запрос несуществующих данных возвращает cache MISS
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "888"}
        
        initial_hits = cache._hits
        initial_misses = cache._misses
        
        # Act
        result = cache.get(method, params)
        
        # Assert
        assert result is None
        assert cache._hits == initial_hits  # hits не изменились
        assert cache._misses == initial_misses + 1  # +1 miss

    def test_none_vs_empty_dict_caching(self, cache):
        """
        Тест: Различие между None и пустым dict {}
        """
        # Arrange
        method1 = "crm.requisite.get"
        params1 = {"id": "1"}
        
        method2 = "crm.requisite.get"
        params2 = {"id": "2"}
        
        # Act
        cache.put(method1, params1, None)  # Кэшируем None
        cache.put(method2, params2, {})    # Кэшируем пустой dict
        
        # Assert
        result1 = cache.get(method1, params1)
        result2 = cache.get(method2, params2)
        
        assert result1 is None
        assert result2 == {}
        assert result1 != result2

    def test_none_caching_prevents_duplicate_api_calls(self, cache):
        """
        БАГ-7 SCENARIO: Проверяем основной сценарий бага
        
        Без фикса: cache.put(method, params, None) не кэширует → повторные API запросы
        С фиксом: cache.put(method, params, None) кэширует sentinel → cache HIT
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "nonexistent"}
        
        # Симулируем сценарий:
        # 1. Первый API запрос возвращает None (реквизит не найден)
        cache.put(method, params, None)
        
        # 2. Второй запрос с теми же параметрами
        initial_misses = cache._misses
        result = cache.get(method, params)
        
        # Assert - должен быть cache HIT, а не повторный API запрос
        assert result is None
        assert cache._misses == initial_misses  # НЕТ нового miss
        # Это означает, что повторного API запроса НЕ будет!

    def test_sentinel_ttl_expiration(self, cache):
        """
        Тест: Проверяем, что sentinel также подчиняется TTL
        """
        # Arrange
        method = "crm.requisite.get"
        params = {"id": "999"}
        cache.put(method, params, None)
        
        # Получаем entry и искусственно делаем его устаревшим
        cache_key = cache._generate_cache_key(method, params)
        entry = cache._general_cache[cache_key]
        
        # Устанавливаем created_at в прошлое (больше TTL)
        from datetime import timedelta
        entry.created_at = datetime.now() - timedelta(hours=25)  # TTL = 24 часа
        
        # Act
        result = cache.get(method, params)
        
        # Assert - должен вернуть None из-за cache MISS (expired)
        assert result is None
        # Проверяем что был miss (expired entry не считается валидным)
        initial_misses = cache._misses
        cache.get(method, params)
        assert cache._misses == initial_misses + 1

    def test_cache_stats_with_sentinel(self, cache):
        """
        Тест: Статистика кэша корректна с sentinel значениями
        """
        # Arrange & Act
        cache.put("method1", {"id": "1"}, {"data": "value"})  # Обычные данные
        cache.put("method2", {"id": "2"}, None)              # Sentinel
        cache.put("method3", {"id": "3"}, [])                # Пустой список
        
        # Получаем данные
        cache.get("method1", {"id": "1"})  # Hit
        cache.get("method2", {"id": "2"})  # Hit (sentinel)
        cache.get("method3", {"id": "3"})  # Hit
        cache.get("method4", {"id": "4"})  # Miss
        
        # Assert
        stats = cache.get_cache_stats()
        assert stats["total_hits"] == 3
        assert stats["total_misses"] == 1
        assert stats["hit_rate_percent"] in ["75.00", 75.0]  # Может быть float или string
