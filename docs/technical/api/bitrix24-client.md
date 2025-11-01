# 🔌 Bitrix24Client API Reference

**Модуль**: `src.bitrix24_client.client`  
**Класс**: `Bitrix24Client`  
**Версия**: v3.0.2

---

## 📋 Содержание

- [Обзор](#обзор)
- [Быстрый старт](#быстрый-старт)
- [Инициализация](#инициализация)
- [Основные методы](#основные-методы)
- [Работа со счетами](#работа-со-счетами)
- [Работа с товарами](#работа-с-товарами)
- [Работа с компаниями](#работа-с-компаниями)
- [Служебные методы](#служебные-методы)
- [Обработка ошибок](#обработка-ошибок)
- [Best Practices](#best-practices)

---

## 📖 Обзор

`Bitrix24Client` — основной клиент для взаимодействия с Bitrix24 REST API. Предоставляет высокоуровневый интерфейс для работы с умными счетами (Smart Invoices), товарами, компаниями и реквизитами.

### Ключевые возможности

- ⚡ **Автоматический rate limiting** (≤2 req/sec)
- 🔄 **Retry механизм** для временных ошибок
- 💾 **Кэширование** результатов запросов
- 🛡️ **Обработка ошибок** с детальной информацией
- 📊 **Статистика** использования API
- 🔐 **Безопасность** с маскировкой webhook URL

---

## ⚡ Быстрый старт

```python
from src.bitrix24_client.client import Bitrix24Client

# Инициализация клиента
client = Bitrix24Client(
    webhook_url="https://your-portal.bitrix24.ru/rest/12/your-key/",
    timeout=30,
    max_retries=3,
    rate_limit=2.0
)

# Получение умных счетов за период
invoices = client.get_smart_invoices(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Получено счетов: {len(invoices)}")

# Закрытие соединения
client.close()
```

> 💡 **Рекомендация**: Используйте context manager для автоматического закрытия соединения

---

## 🔧 Инициализация

### `__init__(webhook_url, timeout, max_retries, rate_limit)`

Создаёт экземпляр клиента Bitrix24.

**Параметры:**

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `webhook_url` | `str` | *обязательный* | URL webhook для доступа к API |
| `timeout` | `int` | `30` | Таймаут запроса в секундах |
| `max_retries` | `int` | `3` | Максимальное количество повторов |
| `rate_limit` | `float` | `2.0` | Лимит запросов в секунду |

**Возвращает**: `Bitrix24Client`

**Пример:**

```python
# Базовая инициализация
client = Bitrix24Client(
    webhook_url="https://portal.bitrix24.ru/rest/12/abc123/"
)

# С настройкой параметров
client = Bitrix24Client(
    webhook_url="https://portal.bitrix24.ru/rest/12/abc123/",
    timeout=60,        # Увеличенный таймаут
    max_retries=5,     # Больше попыток
    rate_limit=1.5     # Меньше запросов/сек
)
```

**Важно:**
- ⚠️ Webhook URL должен содержать trailing slash `/`
- 🔒 URL автоматически маскируется в логах для безопасности
- 📊 Инициализируется AdaptiveRateLimiter для контроля частоты запросов

---

## 🎯 Основные методы

### `get_smart_invoices(start_date, end_date, filter_params=None)`

Получает умные счета (Smart Invoices) за указанный период. Основной метод для работы со счетами.

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `start_date` | `str` | Дата начала периода (YYYY-MM-DD) |
| `end_date` | `str` | Дата окончания периода (YYYY-MM-DD) |
| `filter_params` | `dict`, optional | Дополнительные фильтры |

**Возвращает**: `List[Dict[str, Any]]` - список счетов

**Пример:**

```python
# Получение счетов за месяц
invoices = client.get_smart_invoices(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

for invoice in invoices:
    print(f"Счёт {invoice['accountNumber']}: {invoice['opportunity']} руб.")

# С дополнительными фильтрами
invoices = client.get_smart_invoices(
    start_date="2024-01-01",
    end_date="2024-01-31",
    filter_params={">=OPPORTUNITY": 10000}  # Только счета ≥ 10000 руб
)
```

**Возвращаемая структура:**

```python
{
    "id": "12345",
    "accountNumber": "С-00123",
    "opportunity": "50000.00",
    "ufCrm_..._TITLE": "Название счёта",
    "begindate": "2024-01-15T00:00:00+03:00",
    # ... другие поля
}
```

**Особенности:**
- ✅ Автоматическая пагинация (обрабатывает все страницы)
- ⚡ Использует batch API для оптимизации
- 💾 Результаты кэшируются
- 🔄 Автоматические retry при временных ошибках

---

### `call(method, params=None)`

Базовый метод для вызова любого метода Bitrix24 API.

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `method` | `str` | Название метода API (например, "crm.deal.list") |
| `params` | `dict`, optional | Параметры запроса |

**Возвращает**: `Dict[str, Any]` - ответ от API

**Пример:**

```python
# Прямой вызов API метода
response = client.call(
    method="crm.deal.list",
    params={
        "filter": {"STAGE_ID": "WON"},
        "select": ["ID", "TITLE", "OPPORTUNITY"]
    }
)

deals = response.get("result", [])
print(f"Найдено сделок: {len(deals)}")

# Получение информации о пользователе
user_info = client.call("user.current")
print(f"Текущий пользователь: {user_info['result']['NAME']}")
```

**Обработка ошибок:**

```python
from src.bitrix24_client.exceptions import Bitrix24APIError

try:
    result = client.call("crm.deal.get", {"ID": "999999"})
except Bitrix24APIError as e:
    print(f"Ошибка API: {e}")
```

---

## 📄 Работа со счетами

### `get_detailed_invoice_data(invoice_id)`

Получает детальную информацию о счёте, включая все связанные данные.

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `invoice_id` | `int` | ID счёта |

**Возвращает**: `Optional[Dict[str, Any]]` - детальные данные счёта или `None`

**Пример:**

```python
invoice_data = client.get_detailed_invoice_data(invoice_id=12345)

if invoice_data:
    print(f"Номер: {invoice_data['accountNumber']}")
    print(f"Сумма: {invoice_data['opportunity']}")
    print(f"Товаров: {len(invoice_data.get('products', []))}")
else:
    print("Счёт не найден")
```

---

### `get_all_invoices(start_date, end_date)`

Получает все счета за период (альтернативный метод, использует старый API).

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `start_date` | `str` | Дата начала (YYYY-MM-DD) |
| `end_date` | `str` | Дата окончания (YYYY-MM-DD) |

**Возвращает**: `List[Dict[str, Any]]`

**Пример:**

```python
# Получение всех счетов (legacy API)
invoices = client.get_all_invoices(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

> ⚠️ **Deprecated**: Рекомендуется использовать `get_smart_invoices()` для работы с новым API

---

## 📦 Работа с товарами

### `get_products_by_invoice(invoice_id)`

Получает список товаров по ID счёта с обработкой ошибок.

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `invoice_id` | `int` | ID счёта |

**Возвращает**: `Dict[str, Any]` - словарь с ключами `products`, `has_error`, `error_message`

**Пример:**

```python
result = client.get_products_by_invoice(invoice_id=12345)

if result["has_error"]:
    print(f"Ошибка: {result['error_message']}")
else:
    products = result["products"]
    print(f"Товаров: {len(products)}")
    
    for product in products:
        print(f"- {product['PRODUCT_NAME']}: {product['PRICE']} x {product['QUANTITY']}")
```

**Структура ответа:**

```python
{
    "products": [
        {
            "PRODUCT_ID": "123",
            "PRODUCT_NAME": "Товар 1",
            "PRICE": "1000.00",
            "QUANTITY": "2",
            "TAX_RATE": "20",
            # ... другие поля
        }
    ],
    "has_error": False,
    "error_message": None
}
```

---

### `get_products_by_invoices_batch(invoice_ids)`

Пакетное получение товаров для множества счетов (оптимизировано).

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `invoice_ids` | `List[int]` | Список ID счетов |

**Возвращает**: `Dict[int, List[Dict]]` - словарь {invoice_id: [products]}

**Пример:**

```python
# Получение товаров для нескольких счетов одновременно
invoice_ids = [12345, 12346, 12347, 12348, 12349]
products_by_invoice = client.get_products_by_invoices_batch(invoice_ids)

for invoice_id, products in products_by_invoice.items():
    print(f"Счёт {invoice_id}: {len(products)} товаров")
```

**Преимущества:**
- ⚡ До 50x быстрее, чем отдельные запросы
- 🔄 Использует batch API
- 💾 Автоматическое кэширование
- 🎯 Оптимизация для больших объёмов

---

## 🏢 Работа с компаниями

### `get_company_info_by_invoice(invoice_number)`

Получает информацию о компании (название и ИНН) по номеру счёта.

**Параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `invoice_number` | `str` | Номер счёта (например, "С-00123") |

**Возвращает**: `Tuple[str, str]` - (название компании, ИНН)

**Пример:**

```python
company_name, inn = client.get_company_info_by_invoice("С-00123")

if company_name != "Не указано":
    print(f"Компания: {company_name}")
    print(f"ИНН: {inn}")
else:
    print("Информация о компании не найдена")
```

**Возвращаемые значения:**
- `("Название компании", "1234567890")` - успешно
- `("Не указано", "Не указано")` - не найдено
- `("Ошибка", "Ошибка")` - ошибка запроса

---

## 🛠️ Служебные методы

### `get_stats()`

Возвращает статистику использования API клиента.

**Возвращает**: `Dict[str, Any]` - статистика

**Пример:**

```python
stats = client.get_stats()

print(f"Всего запросов: {stats['total_requests']}")
print(f"Успешных: {stats['successful_requests']}")
print(f"Ошибок: {stats['failed_requests']}")
print(f"Попаданий в кэш: {stats['cache_hits']}")
print(f"Время работы: {stats['uptime_seconds']}с")
```

---

### `close()`

Закрывает сессию и освобождает ресурсы.

**Пример:**

```python
client = Bitrix24Client(webhook_url="...")
try:
    invoices = client.get_smart_invoices("2024-01-01", "2024-01-31")
    # ... работа с данными
finally:
    client.close()
```

> 💡 **Best Practice**: Используйте context manager вместо явного вызова `close()`

---

## ⚠️ Обработка ошибок

### Типы исключений

```python
from src.bitrix24_client.exceptions import (
    Bitrix24APIError,      # Базовая ошибка API
    RateLimitError,        # Превышен лимит запросов
    ServerError,           # Ошибка сервера (5xx)
    AuthenticationError,   # Ошибка авторизации
    NetworkError,          # Сетевая ошибка
    BadRequestError,       # Неверный запрос (4xx)
    NotFoundError,         # Ресурс не найден
    TimeoutError           # Таймаут запроса
)
```

### Обработка ошибок

```python
try:
    invoices = client.get_smart_invoices("2024-01-01", "2024-01-31")
    
except RateLimitError as e:
    print(f"Превышен лимит запросов: {e}")
    # Подождите и повторите попытку
    
except AuthenticationError as e:
    print(f"Ошибка авторизации: {e}")
    # Проверьте webhook URL
    
except NetworkError as e:
    print(f"Сетевая ошибка: {e}")
    # Проверьте соединение
    
except Bitrix24APIError as e:
    print(f"Общая ошибка API: {e}")
    # Обработка других ошибок
```

---

## 🎯 Best Practices

### 1. Используйте Context Manager

```python
# ✅ Правильно
with Bitrix24Client(webhook_url="...") as client:
    invoices = client.get_smart_invoices("2024-01-01", "2024-01-31")
    # Автоматическое закрытие

# ❌ Неправильно
client = Bitrix24Client(webhook_url="...")
invoices = client.get_smart_invoices("2024-01-01", "2024-01-31")
# Забыли вызвать close()
```

### 2. Используйте Batch API для больших объёмов

```python
# ✅ Эффективно - один batch запрос
products = client.get_products_by_invoices_batch([1, 2, 3, 4, 5])

# ❌ Неэффективно - 5 отдельных запросов
for invoice_id in [1, 2, 3, 4, 5]:
    products = client.get_products_by_invoice(invoice_id)
```

### 3. Обрабатывайте ошибки продуктов

```python
result = client.get_products_by_invoice(invoice_id)

if result["has_error"]:
    logger.warning(f"Не удалось получить товары для счёта {invoice_id}")
    # Продолжайте обработку других счетов
else:
    products = result["products"]
    # Обрабатывайте товары
```

### 4. Мониторьте статистику

```python
# Периодически проверяйте статистику
stats = client.get_stats()
if stats['failed_requests'] / stats['total_requests'] > 0.1:
    logger.warning("Высокий процент ошибок API!")
```

### 5. Настройте rate limiting

```python
# Для высоконагруженных систем уменьшите rate
client = Bitrix24Client(
    webhook_url="...",
    rate_limit=1.5  # 1.5 запроса в секунду
)

# Для тестирования можно увеличить
client = Bitrix24Client(
    webhook_url="...",
    rate_limit=3.0  # Осторожно! Может превысить лимиты Bitrix24
)
```

---

## 📚 См. также

- [DataProcessor API](data-processor.md) - обработка данных счетов
- [WorkflowOrchestrator API](workflow.md) - оркестрация процессов
- [Примеры использования](../../examples/) - практические примеры

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
