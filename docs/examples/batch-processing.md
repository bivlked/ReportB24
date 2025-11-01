# ⚡ Batch Processing - Обработка больших объёмов

Оптимизированная обработка больших объёмов счетов (>100) с использованием Batch API Bitrix24 и кэширования.

---

## 🎯 Когда использовать

Batch Processing необходим, когда:

- ✅ **>100 счетов** за период
- ✅ Нужна **высокая скорость** обработки
- ✅ Ограничения **rate limiting** (2 req/sec) становятся узким местом
- ✅ Есть **повторяющиеся запросы** (кэширование)
- ✅ Требуется **минимизировать нагрузку** на Bitrix24 API

**Преимущества**:
- 🚀 **До 50x быстрее** по сравнению с последовательными запросами
- 💾 **Кэширование** данных компаний и товаров
- 🔄 **Автоматический retry** при ошибках
- 📊 **Прогресс-бар** с ETA

---

## 📊 Сравнение производительности

| Метод | 100 счетов | 500 счетов | 1000 счетов |
|-------|-----------|-----------|------------|
| **Последовательный** | ~50 сек | ~4.2 мин | ~8.3 мин |
| **Batch (v2.4.0+)** | ~3 сек | ~15 сек | ~30 сек |
| **Ускорение** | ~16x | ~17x | ~17x |

> 💡 **Примечание**: Batch API загружает до 50 счетов за один запрос.

---

## 💻 Использование Batch API

### Автоматическое использование (рекомендуется)

Система **автоматически** использует Batch API, если:
1. Версия >= v2.4.0
2. Количество счетов > 10

```python
from src.core.app import AppFactory

# Batch автоматически активируется при необходимости
with AppFactory.create_app() as app:
    result = app.generate_report(
        output_path="reports/large_report.xlsx",
        return_metrics=True
    )
    
    # Система сама выбирает оптимальный метод
    print(f"Обработано счетов: {result.quality_metrics.brief_valid}")
```

### Ручное управление Batch

Для продвинутых сценариев:

```python
from src.bitrix24_client.client import Bitrix24Client
from src.config.config_reader import ConfigReader

# Инициализация
config = ConfigReader("config.ini")
client = Bitrix24Client(config.get_webhook_url())

# Получаем список ID счетов
invoice_ids = [12345, 12346, 12347, ...]  # Ваши ID

# Batch загрузка товаров для нескольких счетов
batch_results = client.get_products_by_invoices_batch(invoice_ids)

# Обработка результатов
for invoice_id, result in batch_results.items():
    if not result["has_error"]:
        products = result["products"]
        print(f"Счёт {invoice_id}: {len(products)} товаров")
    else:
        print(f"Счёт {invoice_id}: ошибка - {result['error_message']}")
```

---

## 🔄 Оптимизации v2.4.0

### 1. Batch API для товаров

**До v2.4.0** (последовательно):
```python
# 100 счетов = 100 запросов = ~50 секунд
for invoice in invoices:
    products = client.get_products_by_invoice(invoice["id"])
```

**После v2.4.0** (batch):
```python
# 100 счетов = 2 запроса (50+50) = ~3 секунды
invoice_ids = [inv["id"] for inv in invoices]
batch_results = client.get_products_by_invoices_batch(invoice_ids)
```

### 2. Кэширование компаний

**Проблема**: Одна компания может иметь множество счетов.

**Решение**: Кэш на уровне номера счёта:

```python
# Первый запрос - загружается из API
company_info = client.get_company_info_by_invoice("СЧ-00123")

# Второй запрос с тем же счётом - из кэша (мгновенно)
company_info_cached = client.get_company_info_by_invoice("СЧ-00123")
```

### 3. Интеллектуальное чанкирование

Система автоматически разбивает запросы на оптимальные части:

```python
# 237 счетов автоматически разбиваются:
# Chunk 1: 50 счетов
# Chunk 2: 50 счетов
# Chunk 3: 50 счетов
# Chunk 4: 50 счетов
# Chunk 5: 37 счетов

batch_results = client.get_products_by_invoices_batch(invoice_ids)
# 5 запросов вместо 237!
```

---

## 📊 Мониторинг и метрики

### Отслеживание прогресса

```python
from src.excel_generator.console_ui import ConsoleUI, Spinner

# Spinner для длительных операций
spinner = Spinner("Загрузка счетов из Bitrix24")
spinner.start()

invoices = client.get_smart_invoices(
    filter_params={">=dateCreate": "2024-01-01"}
)

spinner.stop(f"Загружено счетов: {len(invoices)}", success=True)

# Прогресс-бар для обработки
for i, invoice in enumerate(invoices, 1):
    if i % 10 == 0 or i == len(invoices):
        ConsoleUI.print_progress(
            current=i,
            total=len(invoices),
            prefix="Обработка",
            suffix=f"(счёт {i}/{len(invoices)})"
        )
    # Обработка счёта
```

### Сбор статистики

```python
import time

start_time = time.time()

# Обработка
with AppFactory.create_app() as app:
    result = app.generate_report(
        output_path="reports/large.xlsx",
        return_metrics=True
    )

execution_time = time.time() - start_time

# Статистика
print(f"\n📊 Статистика обработки:")
print(f"  Счетов обработано: {result.quality_metrics.brief_valid}")
print(f"  Товаров загружено: {result.quality_metrics.detailed_valid}")
print(f"  Время выполнения: {execution_time:.1f} сек")
print(f"  Скорость: {result.quality_metrics.brief_valid / execution_time:.1f} счетов/сек")
```

---

## 🎛️ Настройка производительности

### Оптимизация config.ini

```ini
[bitrix24]
webhook_url = https://your-portal.bitrix24.ru/rest/1/token/

# Производительность
enable_cache = true              # Кэширование (по умолчанию: true)
cache_ttl = 3600                # TTL кэша в секундах (1 час)
batch_size = 50                 # Размер batch (не рекомендуется изменять)

[app]
log_level = WARNING             # INFO для отладки, WARNING для production
```

### Параллельная обработка (экспериментально)

```python
from concurrent.futures import ThreadPoolExecutor
import time

def process_invoice_batch(invoice_ids_chunk):
    """Обрабатывает чанк счетов."""
    with AppFactory.create_app() as app:
        client = app.bitrix_client
        return client.get_products_by_invoices_batch(invoice_ids_chunk)

# Разбиваем на чанки по 50
chunks = [invoice_ids[i:i+50] for i in range(0, len(invoice_ids), 50)]

# Параллельная обработка (осторожно с rate limiting!)
with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(process_invoice_batch, chunks))

# Объединяем результаты
all_results = {}
for chunk_result in results:
    all_results.update(chunk_result)

print(f"✅ Обработано {len(all_results)} счетов параллельно")
```

> ⚠️ **Внимание**: Параллельная обработка может нарушить rate limiting (2 req/sec). Используйте осторожно!

---

## 🔧 Оптимизация памяти

Для **очень больших** объёмов (>5000 счетов):

```python
def process_large_dataset_in_chunks(start_date, end_date, chunk_size=500):
    """Обрабатывает большой датасет по частям."""
    
    with AppFactory.create_app() as app:
        client = app.bitrix_client
        
        # Получаем все счета
        all_invoices = client.get_smart_invoices(
            filter_params={
                ">=dateCreate": start_date,
                "<=dateCreate": end_date
            }
        )
        
        print(f"Всего счетов: {len(all_invoices)}")
        
        # Обрабатываем чанками
        for i in range(0, len(all_invoices), chunk_size):
            chunk = all_invoices[i:i+chunk_size]
            chunk_num = i // chunk_size + 1
            total_chunks = (len(all_invoices) + chunk_size - 1) // chunk_size
            
            print(f"\nОбработка чанка {chunk_num}/{total_chunks}")
            
            # Генерируем отчёт для чанка
            output_path = f"reports/report_chunk_{chunk_num}.xlsx"
            
            # ... обработка chunk ...
            
            print(f"✅ Чанк {chunk_num} сохранён в {output_path}")
        
        print(f"\n✅ Все {total_chunks} чанков обработаны!")

# Использование
process_large_dataset_in_chunks("2024-01-01", "2024-12-31", chunk_size=1000)
```

---

## ⚠️ Ограничения и рекомендации

### Rate Limiting Bitrix24

**Ограничение**: 2 запроса в секунду.

**Как система справляется**:
```python
# Встроенный rate limiter в Bitrix24Client
class Bitrix24Client:
    def __init__(self, webhook_url):
        self._rate_limiter = {
            "max_requests_per_second": 2,
            "request_interval": 0.5  # 500ms между запросами
        }
```

**Рекомендации**:
- ✅ Используйте Batch API для групповых операций
- ✅ Включите кэширование
- ⚠️ Избегайте параллельных запросов без контроля
- ❌ Не отключайте rate limiting

### Batch Size

**Оптимальный размер**: 50 счетов на запрос.

**Почему не больше**:
- Ограничение Bitrix24 API: max 50 команд в batch
- Timeout риск при больших запросах
- Оптимальный баланс скорость/надёжность

---

## 📚 Дополнительные материалы

### Документация

- **[Bitrix24Client API](../technical/api/bitrix24-client.md)** - Batch методы
- **[WorkflowOrchestrator](../technical/api/workflow.md)** - v2.4.0 оптимизации
- **[Performance Guide](../technical/performance.md)** - Тюнинг производительности

### Примеры

- **[Basic Report](basic-report.md)** - Простая генерация
- **[Error Handling](error-handling.md)** - Обработка ошибок batch
- **[Integration](integration.md)** - Автоматизация batch обработки

---

[← Назад к примерам](index.md) | [Custom Formatting →](custom-formatting.md)
