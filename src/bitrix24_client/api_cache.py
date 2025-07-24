"""
API Data Cache - Request Deduplication System
Реализует кэширование API запросов для минимизации дублирующихся вызовов.
Основан на решении Creative Phase: Request Deduplication with Short-Term Memory Cache.
"""
import hashlib
import time
import threading
import json
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше с данными и временной меткой"""
    data: Any
    timestamp: float
    ttl: float = 300.0  # Time to live в секундах (5 минут)
    
    def is_expired(self) -> bool:
        """Проверяет, истекла ли запись"""
        return time.time() - self.timestamp > self.ttl
    
    def age_seconds(self) -> float:
        """Возвращает возраст записи в секундах"""
        return time.time() - self.timestamp


class APIDataCache:
    """
    Система кэширования API данных с дедупликацией запросов.
    
    Основные принципы:
    - Кэшируем результаты API запросов на 5 минут
    - Используем SHA256 хэш параметров запроса для уникальности
    - Thread-safe операции
    - Автоматическая очистка устаревших записей
    """
    
    def __init__(self, default_ttl: float = 300.0):
        """
        Инициализация кэша
        
        Args:
            default_ttl: Время жизни записей по умолчанию (секунды)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl
        self._stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'evicted': 0
        }
        
        logger.info(f"APIDataCache инициализирован с TTL={default_ttl}s")
    
    def _generate_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """
        Генерирует уникальный ключ кэша на основе метода и параметров
        
        Args:
            method: Название API метода
            params: Параметры запроса
            
        Returns:
            SHA256 хэш как ключ кэша
        """
        # Создаем стабильный JSON для хэширования
        cache_data = {
            'method': method,
            'params': params
        }
        
        # Сортируем ключи для стабильности хэша
        json_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        
        # Генерируем SHA256 хэш
        hash_object = hashlib.sha256(json_str.encode('utf-8'))
        return hash_object.hexdigest()
    
    def get(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Получить данные из кэша
        
        Args:
            method: Название API метода
            params: Параметры запроса
            
        Returns:
            Кэшированные данные или None если не найдено/истекло
        """
        cache_key = self._generate_cache_key(method, params)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats['misses'] += 1
                logger.debug(f"Cache MISS: {method} - {cache_key[:8]}...")
                return None
            
            if entry.is_expired():
                # Удаляем истекшую запись
                del self._cache[cache_key]
                self._stats['expired'] += 1
                logger.debug(f"Cache EXPIRED: {method} - {cache_key[:8]}... (age: {entry.age_seconds():.1f}s)")
                return None
            
            self._stats['hits'] += 1
            logger.debug(f"Cache HIT: {method} - {cache_key[:8]}... (age: {entry.age_seconds():.1f}s)")
            return entry.data
    
    def put(self, method: str, params: Dict[str, Any], data: Any, ttl: Optional[float] = None) -> None:
        """
        Сохранить данные в кэш
        
        Args:
            method: Название API метода
            params: Параметры запроса
            data: Данные для кэширования
            ttl: Время жизни записи (по умолчанию используется default_ttl)
        """
        cache_key = self._generate_cache_key(method, params)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=effective_ttl
            )
            
            self._cache[cache_key] = entry
            logger.debug(f"Cache PUT: {method} - {cache_key[:8]}... (TTL: {effective_ttl}s)")
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {cleared_count} entries removed")
    
    def cleanup_expired(self) -> int:
        """
        Удалить все истекшие записи
        
        Returns:
            Количество удаленных записей
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._stats['evicted'] += len(expired_keys)
                logger.debug(f"Cache cleanup: {len(expired_keys)} expired entries removed")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику кэша
        
        Returns:
            Словарь со статистикой
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'cache_size': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'expired': self._stats['expired'],
                'evicted': self._stats['evicted'],
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests
            }
    
    def __len__(self) -> int:
        """Количество записей в кэше"""
        return len(self._cache)
    
    def __contains__(self, cache_key: str) -> bool:
        """Проверка наличия ключа в кэше"""
        with self._lock:
            entry = self._cache.get(cache_key)
            return entry is not None and not entry.is_expired()


# Глобальный экземпляр кэша для использования в клиенте
_global_cache = APIDataCache()


def get_cache() -> APIDataCache:
    """Получить глобальный экземпляр кэша"""
    return _global_cache


def set_cache_ttl(ttl: float) -> None:
    """Установить новое время жизни по умолчанию для кэша"""
    _global_cache.default_ttl = ttl
    logger.info(f"Cache TTL updated to {ttl}s") 