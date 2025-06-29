"""
Основной клиент для работы с Bitrix24 REST API.
Включает адаптивное rate limiting и обработку ошибок.
"""
import requests
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin

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
        self.webhook_url = webhook_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Инициализируем компоненты
        self.rate_limiter = AdaptiveRateLimiter(max_requests_per_second=rate_limit)
        self.session = requests.Session()
        
        # Настраиваем сессию
        self.session.headers.update({
            'User-Agent': 'Bitrix24-Report-Generator/1.0',
            'Accept': 'application/json',
        })
        
        logger.info(f"Bitrix24 client initialized for {webhook_url}")
    
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
                
                if method.upper() == 'GET':
                    response = self.session.get(
                        url, params=params, timeout=self.timeout
                    )
                elif method.upper() == 'POST':
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
                
                logger.warning(f"Request failed, retry {retry_count}/{self.max_retries}: {error}")
        
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
        if 'error' in json_data:
            error_msg = json_data.get('error_description', json_data.get('error', 'Unknown error'))
            raise Bitrix24APIError(f"Bitrix24 API error: {error_msg}")
        
        # Извлекаем данные
        result_data = json_data.get('result', json_data)
        total = json_data.get('total')
        next_item = json_data.get('next')
        
        return APIResponse(
            data=result_data,
            headers=headers,
            status_code=response.status_code,
            success=True,
            total=total,
            next=next_item,
        )
    
    def _handle_request_exception(
        self, 
        exception: requests.exceptions.RequestException, 
        retry_count: int
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
            return NetworkError(f"Connection error (attempt {retry_count}): {exception}")
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
            'start': start,
            'limit': min(limit, 50),  # Bitrix24 ограничение
        }
        
        if filters:
            params.update(filters)
        
        return self._make_request('GET', 'crm.invoice.list', params=params)
    
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
            'filter': {
                'ENTITY_TYPE_ID': entity_type,
                'ENTITY_ID': entity_id,
            }
        }
        
        return self._make_request('GET', 'crm.requisite.list', params=params)
    
    def get_all_invoices(
        self, 
        filters: Optional[Dict[str, Any]] = None
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
        filters: Optional[Dict[str, Any]] = None
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
            params = {
                'entityTypeId': entity_type_id,
                'start': start,
                'limit': limit
            }
            
            if filters:
                params['filter'] = filters
            
            response = self._make_request('POST', 'crm.item.list', data=params)
            
            if not response.data or not response.data.get('items'):
                break
            
            items = response.data.get('items', [])
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
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы клиента"""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "session_adapters": len(self.session.adapters),
            "webhook_url": self.webhook_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close() 