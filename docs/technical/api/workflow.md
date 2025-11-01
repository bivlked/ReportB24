# 🎼 WorkflowOrchestrator API Reference

**Модуль**: `src.core.workflow`  
**Класс**: `WorkflowOrchestrator`  
**Версия**: v3.0.2

---

## 📖 Обзор

`WorkflowOrchestrator` — координатор процесса генерации отчётов. Управляет последовательностью операций от получения данных из Bitrix24 до создания Excel файла.

### Ключевые возможности

- 🎯 **Координация процесса** генерации отчёта
- 📊 **Оркестрация компонентов** (Client → Processor → Generator)
- ⚡ **Оптимизация v2.4.0** (batch обработка, кэширование)
- 🛡️ **Обработка ошибок** на всех этапах
- 📈 **Мониторинг прогресса** выполнения

---

## ⚡ Быстрый старт

```python
from src.core.workflow import WorkflowOrchestrator

# Инициализация с компонентами
orchestrator = WorkflowOrchestrator(
    bitrix_client=client,
    data_processor=processor,
    excel_generator=generator
)

# Генерация отчёта
success = orchestrator.generate_report(
    start_date="2024-01-01",
    end_date="2024-01-31",
    output_path="reports/january_2024.xlsx"
)

if success:
    print("Отчёт успешно создан!")
```

---

## 🎯 Основные методы

### `__init__(bitrix_client, data_processor, excel_generator)`

Инициализирует оркестратор с необходимыми компонентами.

**Параметры:**
- `bitrix_client` (`Bitrix24Client`) - клиент Bitrix24
- `data_processor` (`DataProcessor`) - процессор данных
- `excel_generator` (`ExcelReportGenerator`) - генератор Excel

---

### `generate_report(start_date, end_date, output_path)`

Координирует полный процесс генерации отчёта.

**Параметры:**
- `start_date` (`str`) - начало периода (YYYY-MM-DD)
- `end_date` (`str`) - конец периода (YYYY-MM-DD)
- `output_path` (`str`) - путь сохранения отчёта

**Возвращает**: `bool` - успех операции

**Процесс:**
1. Получение счетов из Bitrix24
2. Обогащение данными компаний (batch)
3. Получение товаров (batch, оптимизировано)
4. Обработка и валидация данных
5. Группировка товаров по счетам
6. Генерация Excel отчёта

**Пример:**

```python
success = orchestrator.generate_report(
    start_date="2024-01-01",
    end_date="2024-01-31",
    output_path="reports/report_january.xlsx"
)
```

---

## ⚡ Оптимизации v2.4.0

### Batch обработка
- Пакетное получение компаний
- Пакетное получение товаров
- Оптимизация API запросов

### Кэширование
- Кэш компаний по ИНН
- Кэш товаров по счетам
- Снижение нагрузки на API

### Производительность
- До 5-10x ускорение для множества счетов
- Эффективное использование rate limiting
- Параллельная обработка где возможно

---

## 📚 См. также

- [Bitrix24Client API](bitrix24-client.md) - получение данных
- [DataProcessor API](data-processor.md) - обработка данных
- [ExcelReportGenerator API](excel-generator.md) - создание отчётов

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
