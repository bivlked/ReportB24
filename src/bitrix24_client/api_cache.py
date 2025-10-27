#!/usr/bin/env python3
"""
API Data Cache для оптимизации запросов к Bitrix24
Phase 2.1 of detailed-report-enhancements-2025-07-25

Цель: Request Deduplication Cache для минимизации API запросов
- Кэширование продуктов по invoice_id
- Кэширование информации о компаниях
- Short-Term Memory Cache (сессионное кэширование)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Запись в кэше с метаданными"""

    data: Any
    created_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at


class APIDataCache:
    """
    Система кэширования данных API для минимизации запросов к Bitrix24

    Реализует:
    - Request Deduplication: предотвращение дублирующих запросов
    - Short-Term Memory Cache: кэширование на время сессии
    - Automatic Cleanup: очистка устаревших данных
    """

    def __init__(self, default_ttl_minutes: int = 15):
        """
        Инициализация кэша

        Args:
            default_ttl_minutes: Время жизни кэша по умолчанию в минутах
        """
        self.default_ttl = timedelta(minutes=default_ttl_minutes)

        # Основные кэши
        self._product_cache: Dict[str, CacheEntry] = {}
        self._company_cache: Dict[str, CacheEntry] = {}
        self._invoice_cache: Dict[str, CacheEntry] = {}
        # Общий кэш для произвольных запросов
        self._general_cache: Dict[str, CacheEntry] = {}

        # Статистика
        self._hits = 0
        self._misses = 0
        self._cache_created = datetime.now()

        # Thread safety
        self._lock = threading.RLock()

        logger.info(f"APIDataCache инициализирован, TTL: {default_ttl_minutes} мин")

    def get_products_cached(self, invoice_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Получение кэшированных товаров для счета

        Args:
            invoice_id: ID счета

        Returns:
            List[Dict]: Список товаров или None если нет в кэше
        """
        cache_key = f"products_{invoice_id}"

        with self._lock:
            entry = self._product_cache.get(cache_key)

            if entry and self._is_valid(entry):
                # Cache HIT
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._hits += 1

                logger.debug(
                    f"Cache HIT: продукты для счета {invoice_id} "
                    f"(обращений: {entry.access_count})"
                )
                return entry.data

            # Cache MISS
            self._misses += 1
            logger.debug(f"Cache MISS: продукты для счета {invoice_id}")
            return None

    def set_products_cached(
        self, invoice_id: str, products: List[Dict[str, Any]]
    ) -> None:
        """
        Сохранение товаров в кэш

        Args:
            invoice_id: ID счета
            products: Список товаров для кэширования
        
        Note:
            🔥 БАГ-3 FIX: Теперь кэширует ПУСТЫЕ списки товаров.
            Это КРИТИЧНО для предотвращения повторных API запросов для счетов без товаров.
        """
        cache_key = f"products_{invoice_id}"

        with self._lock:
            entry = CacheEntry(data=products, created_at=datetime.now())
            self._product_cache[cache_key] = entry

            if not products:
                logger.info(
                    f"✅ БАГ-3: Кэшировано 0 товаров для счета {invoice_id} (пустой список)"
                )
            else:
                logger.debug(f"Кэшировано {len(products)} товаров для счета {invoice_id}")

    def get_company_cached(self, invoice_number: str) -> Optional[Tuple[str, str]]:
        """
        Получение кэшированной информации о компании

        Args:
            invoice_number: Номер счета

        Returns:
            Tuple[str, str]: (company_name, inn) или None если нет в кэше
        """
        cache_key = f"company_{invoice_number}"

        with self._lock:
            entry = self._company_cache.get(cache_key)

            if entry and self._is_valid(entry):
                # Cache HIT
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._hits += 1

                logger.debug(f"Cache HIT: компания для счета {invoice_number}")
                return entry.data

            # Cache MISS
            self._misses += 1
            logger.debug(f"Cache MISS: компания для счета {invoice_number}")
            return None

    def set_company_cached(
        self, invoice_number: str, company_name: str, inn: str
    ) -> None:
        """
        Сохранение информации о компании в кэш

        Args:
            invoice_number: Номер счета
            company_name: Название компании
            inn: ИНН компании
        """
        cache_key = f"company_{invoice_number}"

        with self._lock:
            entry = CacheEntry(data=(company_name, inn), created_at=datetime.now())
            self._company_cache[cache_key] = entry

            logger.debug(
                f"Кэширована компания {company_name} для счета {invoice_number}"
            )

    def get_company_details_cached(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение кэшированных реквизитов компании

        🔥 НОВОЕ (v2.1.2): Кэширование полных данных компании по company_id
        для избежания повторных API запросов при обработке счетов

        Args:
            company_id: ID компании в Bitrix24

        Returns:
            Dict с полными данными компании или None если нет в кэше

        Thread-safe: Да
        """
        cache_key = f"company_details_{company_id}"

        with self._lock:
            entry = self._company_cache.get(cache_key)

            if entry and self._is_valid(entry):
                # Cache HIT
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._hits += 1

                logger.debug(
                    f"Cache HIT: реквизиты компании {company_id} "
                    f"(обращений: {entry.access_count})"
                )
                return entry.data

            # Cache MISS
            self._misses += 1
            logger.debug(f"Cache MISS: реквизиты компании {company_id}")
            return None

    def cache_company_details(
        self, company_id: str, company_data: Dict[str, Any]
    ) -> None:
        """
        Сохранение реквизитов компании в кэш

        🔥 НОВОЕ (v2.1.2): Кэширование полных данных компании для
        избежания повторных обращений к crm.company.get

        Args:
            company_id: ID компании
            company_data: Полные данные компании включая реквизиты

        Thread-safe: Да
        """
        cache_key = f"company_details_{company_id}"

        with self._lock:
            entry = CacheEntry(data=company_data, created_at=datetime.now())
            self._company_cache[cache_key] = entry

            logger.debug(
                f"Cache PUT: реквизиты компании {company_id} "
                f"сохранены (TTL: {self.default_ttl})"
            )

    def get_invoice_cached(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение кэшированной информации о счете

        Args:
            invoice_id: ID счета

        Returns:
            Dict: Данные счета или None если нет в кэше
        """
        cache_key = f"invoice_{invoice_id}"

        with self._lock:
            entry = self._invoice_cache.get(cache_key)

            if entry and self._is_valid(entry):
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._hits += 1

                logger.debug(f"Cache HIT: счет {invoice_id}")
                return entry.data

            self._misses += 1
            logger.debug(f"Cache MISS: счет {invoice_id}")
            return None

    def set_invoice_cached(self, invoice_id: str, invoice_data: Dict[str, Any]) -> None:
        """
        Сохранение данных счета в кэш

        Args:
            invoice_id: ID счета
            invoice_data: Данные счета
        """
        cache_key = f"invoice_{invoice_id}"

        with self._lock:
            entry = CacheEntry(data=invoice_data, created_at=datetime.now())
            self._invoice_cache[cache_key] = entry

            logger.debug(f"Кэширован счет {invoice_id}")

    def get(self, method: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Общий метод получения данных из кэша

        Args:
            method: Название метода API
            params: Параметры запроса

        Returns:
            Any: Кэшированные данные или None если нет в кэше
        """
        cache_key = self._generate_cache_key(method, params)

        with self._lock:
            entry = self._general_cache.get(cache_key)

            if entry and self._is_valid(entry):
                # Cache HIT
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self._hits += 1

                logger.debug(f"Cache HIT: {method} (ключ: {cache_key[:16]}...)")
                return entry.data

            # Cache MISS
            self._misses += 1
            logger.debug(f"Cache MISS: {method} (ключ: {cache_key[:16]}...)")
            return None

    def put(self, method: str, params: Dict[str, Any], data: Any) -> None:
        """
        Общий метод сохранения данных в кэш

        Args:
            method: Название метода API
            params: Параметры запроса
            data: Данные для кэширования
        """
        if data is None:
            logger.warning(f"Попытка кэширования None для метода {method}")
            return

        cache_key = self._generate_cache_key(method, params)

        with self._lock:
            entry = CacheEntry(data=data, created_at=datetime.now())
            self._general_cache[cache_key] = entry

            logger.debug(f"Кэшированы данные для {method} (ключ: {cache_key[:16]}...)")

    def _generate_cache_key(self, method: str, params: Dict[str, Any]) -> str:
        """
        Генерация ключа кэша на основе метода и параметров

        Args:
            method: Название метода
            params: Параметры

        Returns:
            str: Уникальный ключ кэша
        """
        # Сериализуем параметры в JSON с сортировкой ключей для консистентности
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        # Создаем хеш для компактности
        cache_data = f"{method}:{params_str}"
        return hashlib.md5(cache_data.encode("utf-8")).hexdigest()

    def _is_valid(self, entry: CacheEntry) -> bool:
        """
        Проверка валидности записи кэша

        Args:
            entry: Запись кэша

        Returns:
            bool: True если запись валидна
        """
        age = datetime.now() - entry.created_at
        return age <= self.default_ttl

    def cleanup_expired(self) -> int:
        """
        Очистка устаревших записей кэша

        Returns:
            int: Количество удаленных записей
        """
        removed_count = 0
        current_time = datetime.now()

        with self._lock:
            # Очистка кэша товаров
            expired_products = [
                key
                for key, entry in self._product_cache.items()
                if (current_time - entry.created_at) > self.default_ttl
            ]
            for key in expired_products:
                del self._product_cache[key]
                removed_count += 1

            # Очистка кэша компаний
            expired_companies = [
                key
                for key, entry in self._company_cache.items()
                if (current_time - entry.created_at) > self.default_ttl
            ]
            for key in expired_companies:
                del self._company_cache[key]
                removed_count += 1

            # Очистка кэша счетов
            expired_invoices = [
                key
                for key, entry in self._invoice_cache.items()
                if (current_time - entry.created_at) > self.default_ttl
            ]
            for key in expired_invoices:
                del self._invoice_cache[key]
                removed_count += 1

            # Очистка общего кэша
            expired_general = [
                key
                for key, entry in self._general_cache.items()
                if (current_time - entry.created_at) > self.default_ttl
            ]
            for key in expired_general:
                del self._general_cache[key]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Очищено {removed_count} устаревших записей кэша")

        return removed_count

    def clear_all(self) -> None:
        """Полная очистка всех кэшей"""
        with self._lock:
            total_entries = (
                len(self._product_cache)
                + len(self._company_cache)
                + len(self._invoice_cache)
                + len(self._general_cache)
            )

            self._product_cache.clear()
            self._company_cache.clear()
            self._invoice_cache.clear()
            self._general_cache.clear()

            logger.info(f"Кэш полностью очищен, удалено {total_entries} записей")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша

        🔧 ИСПРАВЛЕНИЕ (v2.1.2): Добавлен подсчет company_details записей

        Returns:
            Dict: Статистика использования кэша
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            uptime = datetime.now() - self._cache_created

            # Подсчет записей для каждого типа кэша
            company_details_count = sum(
                1
                for key in self._company_cache.keys()
                if key.startswith("company_details_")
            )
            companies_basic_count = sum(
                1
                for key in self._company_cache.keys()
                if key.startswith("company_") and not key.startswith("company_details_")
            )

            return {
                "hit_rate_percent": round(hit_rate, 2),
                "total_hits": self._hits,
                "total_misses": self._misses,
                "total_requests": total_requests,
                "uptime_minutes": round(uptime.total_seconds() / 60, 1),
                "cache_sizes": {
                    "products": len(self._product_cache),
                    "companies_basic": companies_basic_count,  # 🔥 НОВОЕ: раздельный подсчет
                    "companies_details": company_details_count,  # 🔥 НОВОЕ: полные реквизиты
                    "invoices": len(self._invoice_cache),
                    "general": len(self._general_cache),
                },
                "memory_efficiency": self._calculate_efficiency(),
            }

    def _calculate_efficiency(self) -> str:
        """
        Расчет эффективности кэша

        Returns:
            str: Оценка эффективности
        """
        # Вычисляем hit_rate напрямую, избегая рекурсии с get_cache_stats()
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        if hit_rate >= 80:
            return "Отличная"
        elif hit_rate >= 60:
            return "Хорошая"
        elif hit_rate >= 40:
            return "Удовлетворительная"
        else:
            return "Требует оптимизации"

    def print_cache_report(self) -> None:
        """Вывод детального отчета о состоянии кэша"""
        stats = self.get_cache_stats()

        print("\n" + "=" * 50)
        print("📊 ОТЧЕТ О СОСТОЯНИИ API CACHE")
        print("=" * 50)
        print(f"🎯 Hit Rate: {stats['hit_rate_percent']}%")
        print(f"✅ Попаданий: {stats['total_hits']}")
        print(f"❌ Промахов: {stats['total_misses']}")
        print(f"📈 Всего запросов: {stats['total_requests']}")
        print(f"⏱️ Время работы: {stats['uptime_minutes']} мин")
        print(f"🧠 Эффективность: {stats['memory_efficiency']}")

        print("\n📦 РАЗМЕРЫ КЭШЕЙ:")
        for cache_type, size in stats["cache_sizes"].items():
            print(f"  • {cache_type}: {size} записей")

        print("=" * 50)


# Глобальный экземпляр кэша для использования в приложении
_global_cache: Optional[APIDataCache] = None


def get_api_cache() -> APIDataCache:
    """
    Получение глобального экземпляра кэша

    Returns:
        APIDataCache: Глобальный кэш
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = APIDataCache()
    return _global_cache


def clear_global_cache() -> None:
    """Очистка глобального кэша"""
    global _global_cache
    if _global_cache:
        _global_cache.clear_all()
        _global_cache = None


# Alias для совместимости с существующим кодом
get_cache = get_api_cache
