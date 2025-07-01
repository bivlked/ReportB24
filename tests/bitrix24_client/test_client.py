"""
Unit тесты для основного Bitrix24 API клиента.
Используем mock для изоляции от внешних зависимостей.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.bitrix24_client.client import Bitrix24Client, APIResponse
from src.bitrix24_client.exceptions import (
    RateLimitError,
    ServerError,
    AuthenticationError,
    NetworkError,
    BadRequestError,
    NotFoundError,
    Bitrix24APIError,
)


@pytest.fixture
def mock_response():
    """Фикстура для создания mock HTTP ответа"""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {'Content-Type': 'application/json'}
    response.json.return_value = {
        'result': [{'ID': '1', 'ACCOUNT_NUMBER': 'INV-001'}],
        'total': 1,
        'next': None
    }
    return response


@pytest.fixture
def client():
    """Фикстура для создания тестового клиента"""
    return Bitrix24Client(
        webhook_url="https://test.bitrix24.ru/rest/1/test_token",
        timeout=10,
        max_retries=1,
        rate_limit=10.0  # Быстрее для тестов
    )


class TestBitrix24Client:
    """Тесты основного функционала клиента"""
    
    def test_client_initialization(self, client):
        """Тест: инициализация клиента"""
        assert client.webhook_url == "https://test.bitrix24.ru/rest/1/test_token"
        assert client.timeout == 10
        assert client.max_retries == 1
        assert client.rate_limiter is not None
        assert client.session is not None
    
    def test_webhook_url_normalization(self):
        """Тест: нормализация URL webhook"""
        client = Bitrix24Client("https://test.bitrix24.ru/rest/1/test_token/")
        assert client.webhook_url == "https://test.bitrix24.ru/rest/1/test_token"
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_successful_get_request(self, mock_get, client, mock_response):
        """Тест: успешный GET запрос"""
        mock_get.return_value = mock_response
        
        response = client._make_request('GET', 'crm.invoice.list')
        
        assert isinstance(response, APIResponse)
        assert response.success is True
        assert response.status_code == 200
        assert response.data == [{'ID': '1', 'ACCOUNT_NUMBER': 'INV-001'}]
        mock_get.assert_called_once()
    
    @patch('src.bitrix24_client.client.requests.Session.post')
    def test_successful_post_request(self, mock_post, client, mock_response):
        """Тест: успешный POST запрос"""
        mock_post.return_value = mock_response
        
        test_data = {'field': 'value'}
        response = client._make_request('POST', 'crm.invoice.add', data=test_data)
        
        assert isinstance(response, APIResponse)
        assert response.success is True
        mock_post.assert_called_once()
        
        # Проверяем что данные переданы как JSON
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs['json'] == test_data
    
    def test_unsupported_http_method(self, client):
        """Тест: неподдерживаемый HTTP метод"""
        with pytest.raises(BadRequestError) as exc_info:
            client._make_request('DELETE', 'test.endpoint')
        
        assert "Unsupported HTTP method: DELETE" in str(exc_info.value)
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_rate_limit_error_handling(self, mock_get, client):
        """Тест: обработка 429 ошибки"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '5'}
        mock_get.return_value = mock_response
        
        with pytest.raises(RateLimitError):
            client._make_request('GET', 'test.endpoint')
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_authentication_error_handling(self, mock_get, client):
        """Тест: обработка ошибок аутентификации"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            client._make_request('GET', 'test.endpoint')
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_server_error_handling(self, mock_get, client):
        """Тест: обработка серверных ошибок"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        with pytest.raises(ServerError):
            client._make_request('GET', 'test.endpoint')
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_not_found_error_handling(self, mock_get, client):
        """Тест: обработка 404 ошибки"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_get.return_value = mock_response
        
        with pytest.raises(NotFoundError):
            client._make_request('GET', 'test.endpoint')
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_invalid_json_response(self, mock_get, client):
        """Тест: некорректный JSON в ответе"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        with pytest.raises(Bitrix24APIError) as exc_info:
            client._make_request('GET', 'test.endpoint')
        
        assert "Invalid JSON response" in str(exc_info.value)
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_bitrix24_api_error_response(self, mock_get, client):
        """Тест: Bitrix24 API ошибка в ответе"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            'error': 'INVALID_REQUEST',
            'error_description': 'Invalid request parameters'
        }
        mock_get.return_value = mock_response
        
        with pytest.raises(Bitrix24APIError) as exc_info:
            client._make_request('GET', 'test.endpoint')
        
        assert "Invalid request parameters" in str(exc_info.value)
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_request_timeout_handling(self, mock_get, client):
        """Тест: обработка таймаута запроса"""
        from src.bitrix24_client.exceptions import TimeoutError as APITimeoutError
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with pytest.raises(APITimeoutError):
            client._make_request('GET', 'test.endpoint')
    
    @patch('src.bitrix24_client.client.requests.Session.get')
    def test_connection_error_handling(self, mock_get, client):
        """Тест: обработка ошибки соединения"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(NetworkError):
            client._make_request('GET', 'test.endpoint')


class TestBitrix24ClientHighLevel:
    """Тесты высокоуровневых методов клиента"""
    
    @patch.object(Bitrix24Client, '_make_request')
    def test_get_invoices(self, mock_request, client):
        """Тест: получение счетов"""
        mock_response = APIResponse(
            data=[{'ID': '1', 'ACCOUNT_NUMBER': 'INV-001'}],
            headers={},
            status_code=200,
            success=True
        )
        mock_request.return_value = mock_response
        
        result = client.get_invoices(start=0, limit=25)
        
        assert result == mock_response
        mock_request.assert_called_once_with(
            'GET', 
            'crm.invoice.list', 
            params={'start': 0, 'limit': 25}
        )
    
    @patch.object(Bitrix24Client, '_make_request')
    def test_get_invoices_with_filters(self, mock_request, client):
        """Тест: получение счетов с фильтрами"""
        mock_response = APIResponse(
            data=[],
            headers={},
            status_code=200,
            success=True
        )
        mock_request.return_value = mock_response
        
        filters = {'filter': {'STATUS_ID': 'PAID'}}
        result = client.get_invoices(filters=filters)
        
        expected_params = {
            'start': 0,
            'limit': 50,
            'filter': {'STATUS_ID': 'PAID'}
        }
        mock_request.assert_called_once_with(
            'GET', 
            'crm.invoice.list', 
            params=expected_params
        )
    
    @patch.object(Bitrix24Client, '_make_request')
    def test_get_requisites(self, mock_request, client):
        """Тест: получение реквизитов"""
        mock_response = APIResponse(
            data=[{'ID': '1', 'RQ_INN': '1234567890'}],
            headers={},
            status_code=200,
            success=True
        )
        mock_request.return_value = mock_response
        
        result = client.get_requisites('COMPANY', 123)
        
        expected_params = {
            'filter': {
                'ENTITY_TYPE_ID': 'COMPANY',
                'ENTITY_ID': 123
            }
        }
        mock_request.assert_called_once_with(
            'GET', 
            'crm.requisite.list', 
            params=expected_params
        )
    
    @patch.object(Bitrix24Client, 'get_invoices')
    def test_get_all_invoices_single_page(self, mock_get_invoices, client):
        """Тест: получение всех счетов (одна страница)"""
        mock_response = APIResponse(
            data=[{'ID': '1'}, {'ID': '2'}],
            headers={},
            status_code=200,
            success=True,
            next=None
        )
        mock_get_invoices.return_value = mock_response
        
        result = client.get_all_invoices()
        
        assert len(result) == 2
        assert result[0]['ID'] == '1'
        assert result[1]['ID'] == '2'
        mock_get_invoices.assert_called_once()
    
    @patch.object(Bitrix24Client, 'get_invoices')
    def test_get_all_invoices_multiple_pages(self, mock_get_invoices, client):
        """Тест: получение всех счетов (несколько страниц)"""
        # Первая страница - полная (50 элементов = лимит)
        first_page_data = [{'ID': str(i)} for i in range(1, 51)]  # 50 элементов
        first_response = APIResponse(
            data=first_page_data,
            headers={},
            status_code=200,
            success=True,
            next=50
        )
        
        # Вторая страница (последняя) - неполная
        second_response = APIResponse(
            data=[{'ID': '51'}, {'ID': '52'}],
            headers={},
            status_code=200,
            success=True,
            next=None
        )
        
        mock_get_invoices.side_effect = [first_response, second_response]
        
        result = client.get_all_invoices()
        
        assert len(result) == 52  # 50 + 2
        assert mock_get_invoices.call_count == 2
    
    def test_context_manager(self, client):
        """Тест: использование как context manager"""
        with patch.object(client, 'close') as mock_close:
            with client as c:
                assert c is client
            mock_close.assert_called_once()
    
    def test_get_stats(self, client):
        """Тест: получение статистики с маскированным webhook URL"""
        stats = client.get_stats()
        
        assert 'rate_limiter' in stats
        assert 'webhook_url' in stats
        assert 'timeout' in stats
        assert 'max_retries' in stats
        # webhook_url теперь возвращается в маскированном виде для безопасности
        assert stats['webhook_url'] == client._mask_webhook_url(client.webhook_url) 