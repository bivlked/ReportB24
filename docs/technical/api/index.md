# 📋 API Documentation - Детальная документация

Детальная API документация для всех основных компонентов ReportB24.

---

## 🗺️ Обзор компонентов

### 🔗 Интеграция с Bitrix24

**[Bitrix24Client](bitrix24-client.md)** - REST API клиент для Bitrix24
- Получение Smart Invoices
- Получение товаров и компаний
- Rate limiting и пагинация
- Batch-оптимизация запросов

### 📊 Обработка данных

**[DataProcessor](data-processor.md)** - Обработка и валидация данных
- Обработка счетов и товаров
- Валидация российских ИНН
- Форматирование дат и сумм
- Группировка данных (zebra-effect)

### 📈 Генерация отчетов

**[ExcelGenerator](excel-generator.md)** - Генерация Excel отчетов
- Создание двухлистовых отчетов
- Форматирование и стилизация
- Автоширина колонок
- Сводные таблицы

### ⚙️ Конфигурация

**[ConfigReader](config-reader.md)** - Безопасное управление конфигурацией
- Hybrid `.env` + `config.ini` система
- Валидация параметров
- Маскировка секретов в логах

### 🔄 Оркестрация

**[Workflow](workflow.md)** - Управление workflow
- Координация компонентов
- Обработка ошибок
- Логирование операций

---

## 📖 Формат документации

Каждая страница API включает:

✅ **Overview** - Обзор компонента  
✅ **Imports** - Импорты и зависимости  
✅ **Initialization** - Инициализация  
✅ **Methods** - Методы с параметрами и примерами  
✅ **Examples** - Практические сценарии использования  
✅ **Best Practices** - Рекомендации  
✅ **See Also** - Связанные компоненты  

---

## 🚀 Быстрый доступ

| Компонент | Основные методы | Документация |
|-----------|----------------|--------------|
| **Bitrix24Client** | `get_smart_invoices()`, `get_products_by_invoices_batch()` | [→ Детали](bitrix24-client.md) |
| **DataProcessor** | `process_invoices()`, `validate_inn()` | [→ Детали](data-processor.md) |
| **ExcelGenerator** | `generate()`, `create_summary_sheet()` | [→ Детали](excel-generator.md) |
| **ConfigReader** | `get_webhook_url()`, `validate_config()` | [→ Детали](config-reader.md) |
| **Workflow** | `run()`, `handle_error()` | [→ Детали](workflow.md) |

---

## 🎯 Рекомендации по использованию

### Для интеграции:
1. Начните с **[Bitrix24Client](bitrix24-client.md)** - подключение к API
2. Изучите **[DataProcessor](data-processor.md)** - обработка данных
3. Проверьте **[ExcelGenerator](excel-generator.md)** - генерация отчетов

### Для оптимизации:
1. **[Bitrix24Client](bitrix24-client.md)** - batch-оптимизация
2. **[DataProcessor](data-processor.md)** - эффективная обработка
3. **[Workflow](workflow.md)** - управление потоками

### Для безопасности:
1. **[ConfigReader](config-reader.md)** - безопасная конфигурация
2. **[Bitrix24Client](bitrix24-client.md)** - маскировка URL
3. **[Workflow](workflow.md)** - обработка ошибок

---

## 📚 Дополнительные ресурсы

- **[API Reference](../api-reference.md)** - Обзор API
- **[Architecture](../architecture.md)** - Архитектура системы
- **[Examples](../../examples/)** - Практические примеры
- **[Data Structures](../data-structures.md)** - Форматы данных

---

[← Назад к Technical](../index.md) • [Bitrix24Client →](bitrix24-client.md)
