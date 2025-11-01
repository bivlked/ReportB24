# 🔄 DataProcessor API Reference

**Модуль**: `src.data_processor.data_processor`  
**Класс**: `DataProcessor`  
**Версия**: v3.0.2

---

## 📖 Обзор

`DataProcessor` — центральный компонент для обработки и валидации данных счетов Bitrix24. Координирует работу специализированных процессоров (INN, Date, Currency) и обеспечивает консистентность данных.

### Ключевые возможности

- ✅ **Валидация данных** (ИНН, даты, суммы)
- 🔄 **Обогащение данных** через Bitrix24Client
- 📊 **Группировка товаров** по счетам
- 💰 **Расчёты НДС** и сумм
- 📝 **Форматирование** для Excel

---

## ⚡ Быстрый старт

```python
from src.data_processor.data_processor import DataProcessor

# Инициализация
processor = DataProcessor()

# Установка клиента Bitrix24 для обогащения данных
processor.set_bitrix_client(bitrix_client)

# Обработка счёта
invoice_data = processor.process_invoice_record({
    "accountNumber": "С-00123",
    "opportunity": "50000",
    "begindate": "2024-01-15T10:00:00+03:00",
    # ... другие поля
})

print(f"Обработан счёт: {invoice_data['account_number']}")
```

---

## 🎯 Основные методы

### `set_bitrix_client(bitrix_client)`

Устанавливает клиент Bitrix24 для обогащения данных компаниями.

**Параметры:**
- `bitrix_client` (`Bitrix24Client`) - клиент Bitrix24

---

### `process_invoice_record(raw_data)`

Обрабатывает один счёт с валидацией и обогащением.

**Параметры:**
- `raw_data` (`Dict[str, Any]`) - сырые данные счёта из API

**Возвращает**: `Dict[str, Any]` - обработанный счёт

**Пример:**

```python
processed = processor.process_invoice_record(raw_invoice)
print(f"ИНН: {processed['inn']}")
print(f"Контрагент: {processed['counterparty']}")
print(f"Сумма: {processed['amount']}")
```

---

### `process_invoice_batch(invoices, start_date, end_date)`

Пакетная обработка счетов с обогащением данными компаний.

**Параметры:**
- `invoices` (`List[Dict]`) - список счетов
- `start_date` (`str`) - начало периода
- `end_date` (`str`) - конец периода

**Возвращает**: `List[Dict[str, Any]]` - обработанные счета

**Пример:**

```python
# Пакетная обработка с обогащением
processed_invoices = processor.process_invoice_batch(
    invoices=raw_invoices,
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

---

### `format_detailed_products_for_excel(products, invoice_info)`

Форматирует товары для детального листа Excel с группировкой.

**Параметры:**
- `products` (`List[Dict]`) - список товаров
- `invoice_info` (`Dict`) - информация о счёте

**Возвращает**: `List[Dict]` - отформатированные товары

**Пример:**

```python
formatted_products = processor.format_detailed_products_for_excel(
    products=products,
    invoice_info={
        "account_number": "С-00123",
        "company_name": "ООО Компания",
        "inn": "1234567890",
        "invoice_id": 12345
    }
)
```

---

## 📦 Структура данных

### ProcessedInvoice

```python
{
    "account_number": "С-00123",
    "inn": "1234567890",
    "counterparty": "ООО Компания",
    "amount": Decimal("50000.00"),
    "vat_amount": Decimal("10000.00"),
    "invoice_date": datetime(2024, 1, 15),
    "is_valid": True,
    "validation_errors": []
}
```

---

## 📚 См. также

- [Bitrix24Client API](bitrix24-client.md) - получение данных
- [ExcelReportGenerator API](excel-generator.md) - генерация отчётов
- [Примеры](../../examples/) - практические примеры

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
