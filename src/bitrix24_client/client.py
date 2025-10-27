"""
Основной клиент для работы с Bitrix24 REST API.
Включает адаптивное rate limiting, кэширование и обработку ошибок.
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .rate_limiter import AdaptiveRateLimiter
from .exceptions import (
    Bitrix24APIError,
    RateLimitError,
    ServerError,
    AuthenticationError,
    NetworkError,
    BadRequestError,
    NotFoundError,
    TimeoutError as APITimeoutError,
)
from .api_cache import get_cache
from .retry_decorator import retry_on_api_error  # 🔥 НОВОЕ (v2.1.2)

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Структурированный ответ от Bitrix24 API"""

    data: Any
    headers: Dict[str, str]
    status_code: int
    success: bool
    error: Optional[str] = None
    total: Optional[int] = None
    next: Optional[int] = None


class Bitrix24Client:
    """
    Основной клиент для Bitrix24 REST API.

    Особенности:
    - Автоматическое rate limiting (≤2 req/sec)
    - Retry логика для временных ошибок
    - Пагинация результатов
    - Структурированная обработка ошибок
    """

    def __init__(
        self,
        webhook_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: float = 2.0,
    ):
        """
        Инициализация клиента.

        Args:
            webhook_url: URL webhook для доступа к API
            timeout: Таймаут запросов в секундах
            max_retries: Максимальное количество повторов
            rate_limit: Лимит запросов в секунду
        """
        self.webhook_url = webhook_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Инициализируем компоненты
        self.rate_limiter = AdaptiveRateLimiter(max_requests_per_second=rate_limit)
        self.session = requests.Session()

        # Настраиваем сессию
        self.session.headers.update(
            {
                "User-Agent": "Bitrix24-Report-Generator/1.0",
                "Accept": "application/json",
            }
        )

        # Маскируем webhook URL для безопасного логирования
        masked_url = self._mask_webhook_url(webhook_url)
        logger.info(f"Bitrix24 client initialized for {masked_url}")

    def _mask_webhook_url(self, webhook_url: str) -> str:
        """
        Маскирует webhook URL для безопасного логирования.

        Args:
            webhook_url: Полный webhook URL

        Returns:
            str: Маскированный URL вида https://portal.bitrix24.ru/rest/12/***/
        """
        import re

        if not webhook_url or "https://" not in webhook_url:
            return webhook_url

        # Маскируем токен в URL: https://portal.bitrix24.ru/rest/12345/abc123def456/ -> https://portal.bitrix24.ru/rest/12345/***/
        # Удаляем trailing slash перед маскировкой, чтобы избежать двойного слэша
        masked = re.sub(r"(/rest/\d+/)[a-zA-Z0-9_]+/?$", r"\1***/", webhook_url)
        return masked

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """
        Выполнение HTTP запроса с retry логикой.

        Args:
            method: HTTP метод (GET, POST)
            endpoint: API endpoint (например, 'crm.invoice.list')
            data: Данные для POST запроса
            params: URL параметры

        Returns:
            APIResponse: Структурированный ответ

        Raises:
            Bitrix24APIError: При ошибках API
        """
        url = f"{self.webhook_url}/{endpoint}"
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # Применяем rate limiting
                self.rate_limiter.acquire()

                # Выполняем запрос
                logger.debug(f"Making {method} request to {endpoint}")

                if method.upper() == "GET":
                    response = self.session.get(
                        url, params=params, timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = self.session.post(
                        url, json=data, params=params, timeout=self.timeout
                    )
                else:
                    raise BadRequestError(f"Unsupported HTTP method: {method}")

                # Обновляем rate limiter на основе ответа
                self.rate_limiter.update_from_response(
                    dict(response.headers), response.status_code
                )

                # Обрабатываем ответ
                return self._handle_response(response)

            except requests.exceptions.RequestException as e:
                retry_count += 1
                error = self._handle_request_exception(e, retry_count)

                if not error.is_retryable() or retry_count > self.max_retries:
                    raise error

                logger.warning(
                    f"Request failed, retry {retry_count}/{self.max_retries}: {error}"
                )

        raise NetworkError("Max retries exceeded")

    def _handle_response(self, response: requests.Response) -> APIResponse:
        """
        Обработка HTTP ответа от Bitrix24.

        Args:
            response: HTTP ответ

        Returns:
            APIResponse: Структурированный ответ

        Raises:
            Bitrix24APIError: При ошибках API
        """
        headers = dict(response.headers)

        # Проверяем HTTP статус
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code in (401, 403):
            raise AuthenticationError("Authentication failed")
        elif response.status_code == 404:
            raise NotFoundError("API endpoint not found")
        elif response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")
        elif response.status_code >= 400:
            raise BadRequestError(f"Bad request: {response.status_code}")

        try:
            json_data = response.json()
        except ValueError:
            raise Bitrix24APIError("Invalid JSON response")

        # Проверяем Bitrix24 specific ошибки
        if "error" in json_data:
            error_msg = json_data.get(
                "error_description", json_data.get("error", "Unknown error")
            )
            raise Bitrix24APIError(f"Bitrix24 API error: {error_msg}")

        # Извлекаем данные
        result_data = json_data.get("result", json_data)
        total = json_data.get("total")
        next_item = json_data.get("next")

        return APIResponse(
            data=result_data,
            headers=headers,
            status_code=response.status_code,
            success=True,
            total=total,
            next=next_item,
        )

    def _handle_request_exception(
        self, exception: requests.exceptions.RequestException, retry_count: int
    ) -> Bitrix24APIError:
        """
        Обработка исключений requests.

        Args:
            exception: Исключение requests
            retry_count: Номер попытки

        Returns:
            Bitrix24APIError: Соответствующее API исключение
        """
        if isinstance(exception, requests.exceptions.Timeout):
            return APITimeoutError(f"Request timeout (attempt {retry_count})")
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return NetworkError(
                f"Connection error (attempt {retry_count}): {exception}"
            )
        else:
            return NetworkError(f"Request error (attempt {retry_count}): {exception}")

    def get_invoices(
        self,
        start: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """
        Получение списка счетов.

        Args:
            start: Номер первого элемента
            limit: Количество элементов (макс. 50)
            filters: Фильтры для поиска

        Returns:
            APIResponse: Список счетов
        """
        params = {
            "start": start,
            "limit": min(limit, 50),  # Bitrix24 ограничение
        }

        if filters:
            params.update(filters)

        return self._make_request("GET", "crm.invoice.list", params=params)

    def get_requisites(
        self,
        entity_type: str,
        entity_id: int,
    ) -> APIResponse:
        """
        Получение реквизитов организации.

        Args:
            entity_type: Тип сущности (COMPANY, CONTACT)
            entity_id: ID сущности

        Returns:
            APIResponse: Реквизиты
        """
        params = {
            "filter": {
                "ENTITY_TYPE_ID": entity_type,
                "ENTITY_ID": entity_id,
            }
        }

        return self._make_request("GET", "crm.requisite.list", params=params)

    def get_all_invoices(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Получение всех счетов с автоматической пагинацией.

        Args:
            filters: Фильтры для поиска

        Returns:
            List[Dict]: Полный список счетов
        """
        all_invoices = []
        start = 0
        limit = 50

        while True:
            response = self.get_invoices(start=start, limit=limit, filters=filters)

            if not response.data:
                break

            if isinstance(response.data, list):
                all_invoices.extend(response.data)
            else:
                all_invoices.append(response.data)

            # Проверяем есть ли еще данные
            if response.next is None or len(response.data) < limit:
                break

            start = response.next

            logger.debug(f"Loaded {len(all_invoices)} invoices so far")

        logger.info(f"Total invoices loaded: {len(all_invoices)}")
        return all_invoices

    def get_smart_invoices(
        self,
        entity_type_id: int = 31,
        filters: Optional[Dict[str, Any]] = None,
        select: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Получение всех Smart Invoices с автоматической пагинацией.

        Args:
            entity_type_id: ID типа сущности (31 для Smart Invoices)
            filters: Фильтры для поиска

        Returns:
            List[Dict]: Полный список Smart Invoices
        """
        all_invoices = []
        start = 0
        limit = 50

        while True:
            params = {"entityTypeId": entity_type_id, "start": start, "limit": limit}

            if filters:
                params["filter"] = filters

            if select:
                params["select"] = select

            response = self._make_request("POST", "crm.item.list", data=params)

            if not response.data or not response.data.get("items"):
                break

            items = response.data.get("items", [])
            all_invoices.extend(items)

            # Проверяем есть ли еще данные
            if response.next is None or len(items) < limit:
                break

            start = response.next

            logger.debug(f"Loaded {len(all_invoices)} smart invoices so far")

        logger.info(f"Total smart invoices loaded: {len(all_invoices)}")
        return all_invoices

    def close(self):
        """Закрытие клиента и освобождение ресурсов"""
        if self.session:
            self.session.close()
            logger.info("Bitrix24 client closed")

    def get_requisite_links(
        self, entity_type_id: int, entity_id: int
    ) -> List[Dict[str, Any]]:
        """
        Получение связей реквизитов для сущности с кэшированием (как в ShortReport.py)

        Args:
            entity_type_id: Тип сущности (31 для Smart Invoices)
            entity_id: ID сущности

        Returns:
            List[Dict]: Список связей реквизитов
        """
        method = "crm.requisite.link.list"
        params = {
            "filter[ENTITY_TYPE_ID]": entity_type_id,
            "filter[ENTITY_ID]": entity_id,
        }

        # Проверяем кэш
        cache = get_cache()
        cached_result = cache.get(method, params)
        if cached_result is not None:
            logger.debug(f"Cache hit for requisite links of entity {entity_id}")
            return cached_result

        response = self._make_request("GET", method, params=params)
        result = response.data if response.data else []

        # Сохраняем в кэш
        cache.put(method, params, result)

        return result

    def get_requisite_details(self, requisite_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение деталей реквизита с кэшированием (как в ShortReport.py)

        Args:
            requisite_id: ID реквизита

        Returns:
            Dict: Детали реквизита или None
        """
        method = "crm.requisite.get"
        data = {"id": str(requisite_id)}

        # Проверяем кэш
        cache = get_cache()
        cached_result = cache.get(method, data)
        if cached_result is not None:
            logger.debug(f"Cache hit for requisite details {requisite_id}")
            return cached_result

        response = self._make_request("POST", method, data=data)
        result = response.data if response.data else None

        # Сохраняем в кэш
        cache.put(method, data, result)

        return result

    def get_company_info_by_invoice(self, invoice_number: str) -> tuple:
        """
        Получение информации о компании по номеру счета (точная копия из ShortReport.py)

        Args:
            invoice_number: Номер счета

        Returns:
            tuple: (название_компании, ИНН)
        """
        try:
            # 1. Ищем счёт по номеру (accountNumber)
            params = {"filter[accountNumber]": invoice_number, "entityTypeId": 31}

            response = self._make_request("GET", "crm.item.list", params=params)

            if not response.data or not response.data.get("items"):
                return None, None

            items = response.data.get("items", [])
            inv_id = items[0].get("id")
            if not inv_id:
                return None, None

            # 2. Ищем привязку в crm.requisite.link
            requisite_links = self.get_requisite_links(31, inv_id)
            if not requisite_links:
                return "Нет реквизитов", "Нет реквизитов"

            req_id = requisite_links[0].get("REQUISITE_ID")
            if not req_id or int(req_id) <= 0:
                return "Некорректный реквизит", "Некорректный реквизит"

            # 3. Получаем реквизит
            requisite_details = self.get_requisite_details(int(req_id))
            if not requisite_details:
                return "Ошибка реквизита", "Ошибка реквизита"

            rq_inn = requisite_details.get("RQ_INN", "")
            rq_company = requisite_details.get("RQ_COMPANY_NAME", "")
            rq_name = requisite_details.get("RQ_NAME", "")

            # 4. Логика определения типа по ИНН (как в ShortReport.py)
            if rq_inn.isdigit():
                if len(rq_inn) == 10:
                    return rq_company, rq_inn  # ООО/ЗАО
                elif len(rq_inn) == 12:
                    return (
                        f"ИП {rq_name}" if rq_name else "ИП (нет имени)",
                        rq_inn,
                    )  # ИП
                else:
                    return rq_company, rq_inn
            else:
                return rq_company, rq_inn

        except Exception as e:
            logger.error(f"Ошибка получения реквизитов для {invoice_number}: {e}")
            return "Ошибка", "Ошибка"

    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы клиента"""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "session_adapters": len(self.session.adapters),
            "webhook_url": self._mask_webhook_url(self.webhook_url),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    @retry_on_api_error(
        max_retries=3, backoff_factor=1.0, retryable_codes=(429, 500, 502, 503, 504)
    )
    def call(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Универсальный метод вызова Bitrix24 API с автоматическим retry

        🔥 НОВОЕ (v2.1.2): Упрощенный API wrapper с retry логикой для
        прямых вызовов методов Bitrix24 (например, crm.company.get)

        Args:
            method: Имя метода API (например, 'crm.company.get')
            params: Параметры запроса

        Returns:
            Dict с ответом API

        Raises:
            HTTPError: При неудачных HTTP запросах после всех retry
            RequestException: При проблемах с сетью после всех retry
        """
        if params is None:
            params = {}

        response = self._make_request("POST", method, data=params)

        if not response.success:
            raise Bitrix24APIError(
                f"API call failed: {response.error}", status_code=response.status_code
            )

        return response.data

    def get_products_by_invoice(self, invoice_id: int) -> List[Dict[str, Any]]:
        """
        Получение товаров по ID счета через crm.item.productrow.list с кэшированием

        На основе успешного Proof of Concept с правильными параметрами:
        - =ownerType: SI (Smart Invoice)
        - =ownerId: ID счета

        Использует APIDataCache для минимизации дублирующихся запросов.

        Args:
            invoice_id: ID Smart Invoice счета

        Returns:
            List[Dict]: Список товаров счета
        """
        try:
            method = "crm.item.productrow.list"
            params = {
                "filter": {
                    "=ownerType": "SI",  # Smart Invoice (проверено в PoC)
                    "=ownerId": invoice_id,
                }
            }

            # Проверяем кэш
            cache = get_cache()
            cached_result = cache.get(method, params)
            if cached_result is not None:
                logger.debug(f"Cache hit for products of invoice {invoice_id}")
                return cached_result

            logger.debug(f"Getting products for invoice {invoice_id} (cache miss)")
            response = self._make_request("POST", method, data=params)

            if response and response.success:
                # Структура ответа проверена в PoC: result.productRows
                products = (
                    response.data.get("productRows", [])
                    if isinstance(response.data, dict)
                    else []
                )

                # Сохраняем в кэш
                cache.put(method, params, products)

                logger.info(
                    f"Retrieved {len(products)} products for invoice {invoice_id}"
                )
                return products
            else:
                logger.warning(
                    f"No products found for invoice {invoice_id}: {response.error if response else 'Unknown error'}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting products for invoice {invoice_id}: {e}")
            return []

    def get_products_by_invoices_batch(
        self, invoice_ids: List[int], chunk_size: int = 50
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Batch получение товаров для списка счетов через crm.item.productrow.list

        Реализует Hybrid Caching Architecture из creative phase:
        - Группированная обработка по chunk_size
        - Batch API optimization для производительности
        - Возврат структурированных данных по счетам

        Args:
            invoice_ids: Список ID Smart Invoice счетов
            chunk_size: Размер batch (макс. 50 для Bitrix24)

        Returns:
            Dict[invoice_id, products_list]: Товары сгруппированные по счетам
        """
        if not invoice_ids:
            return {}

        all_products = {}

        # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Метод crm.item.productrow.list НЕ ПОДДЕРЖИВАЕТСЯ в batch API
        # Согласно тестированию, этот метод возвращает пустые результаты в batch запросах
        # Используем ТОЛЬКО индивидуальные запросы для надежности

        logger.info(
            f"Using individual requests for {len(invoice_ids)} invoices (batch API not supported for productrow.list)"
        )

        # Обрабатываем каждый счет индивидуально
        for invoice_id in invoice_ids:
            try:
                products = self.get_products_by_invoice(invoice_id)
                all_products[invoice_id] = products
                if products:
                    logger.debug(f"Invoice {invoice_id}: {len(products)} products")
            except Exception as e:
                logger.error(f"Error getting products for invoice {invoice_id}: {e}")
                all_products[invoice_id] = []

        total_products = sum(len(products) for products in all_products.values())
        logger.info(
            f"Individual processing complete: {len(all_products)} invoices, {total_products} total products"
        )

        return all_products

    def get_detailed_invoice_data(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации по счету включая товары и реквизиты

        Комбинирует данные счета, товаров и реквизитов для детального отчета.
        Использует существующие методы для получения полной картины.

        Args:
            invoice_id: ID Smart Invoice счета

        Returns:
            Dict: Детальная информация о счете или None при ошибке
        """
        try:
            # 1. Получаем базовую информацию о счете
            params = {
                "entityTypeId": 31,  # Smart Invoices
                "filter": {"id": invoice_id},
                "select": ["id", "title", "opportunity", "accountNumber", "stageId"],
            }

            invoice_response = self._make_request("POST", "crm.item.list", data=params)

            if not (
                invoice_response
                and invoice_response.success
                and invoice_response.data
                and invoice_response.data.get("items")
            ):
                logger.warning(f"Invoice {invoice_id} not found or inaccessible")
                return None

            invoice_info = invoice_response.data["items"][0]

            # 2. Получаем товары по счету
            products = self.get_products_by_invoice(invoice_id)

            # 3. Получаем реквизиты (если есть accountNumber)
            account_number = invoice_info.get("accountNumber")
            company_name = "Не найдено"
            inn = "Не найдено"

            if account_number:
                company_name, inn = self.get_company_info_by_invoice(account_number)

            # 4. Формируем детальную структуру
            detailed_data = {
                "invoice": invoice_info,
                "products": products,
                "company_name": company_name,
                "inn": inn,
                "total_products": len(products),
                "account_number": account_number,
            }

            logger.info(
                f"Retrieved detailed data for invoice {invoice_id}: {len(products)} products"
            )
            return detailed_data

        except Exception as e:
            logger.error(f"Error getting detailed invoice data for {invoice_id}: {e}")
            return None
