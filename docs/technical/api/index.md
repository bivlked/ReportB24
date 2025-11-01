# 📚 API Reference - ReportB24

**Версия**: v3.0.2  
**Обновлено**: 2025-11-01

---

## 🎯 Обзор

Полная документация публичного API ReportB24 для генерации профессиональных Excel отчётов из Bitrix24.

### Архитектура системы

```
┌─────────────────────────────────────────┐
│      ReportGeneratorApp                 │  ← Главное приложение
│         (High-level API)                │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼─────┐    ┌──────▼──────┐
│ Bitrix24  │    │   Workflow  │
│  Client   │◄───┤ Orchestrator│
└─────┬─────┘    └──────┬──────┘
      │                 │
      │          ┌──────▼──────┐
      │          │    Data     │
      └─────────►│  Processor  │
                 └──────┬──────┘
                        │
                 ┌──────▼──────┐
                 │    Excel    │
                 │  Generator  │
                 └─────────────┘
```

---

## 📖 Модули API

### 🚀 Главное приложение

#### [ReportGeneratorApp](app.md)
Высокоуровневый интерфейс приложения. Используйте этот модуль для простой генерации отчётов.

**Основные методы:**
- `generate_report()` - создание отчёта
- `validate_configuration()` - проверка настроек
- `test_api_connection()` - тест API

**Пример:**
```python
with AppFactory.create_app('config.ini') as app:
    app.generate_report()
```

---

### 🔌 Интеграция с Bitrix24

#### [Bitrix24Client](bitrix24-client.md)
Клиент для работы с Bitrix24 REST API. Полная документация с 13+ методами.

**Основные методы:**
- `get_smart_invoices()` - получение счетов
- `get_products_by_invoice()` - получение товаров
- `get_company_info_by_invoice()` - информация о компании
- `call()` - базовый метод API

**Возможности:**
- ⚡ Автоматический rate limiting
- 🔄 Retry механизм
- 💾 Кэширование
- 📊 Статистика использования

---

### 🔄 Обработка данных

#### [DataProcessor](data-processor.md)
Процессор для валидации и обогащения данных счетов.

**Основные методы:**
- `process_invoice_record()` - обработка счёта
- `process_invoice_batch()` - пакетная обработка
- `format_detailed_products_for_excel()` - форматирование товаров

**Возможности:**
- ✅ Валидация (ИНН, даты, суммы)
- 🔄 Обогащение данными компаний
- 💰 Расчёты НДС

---

### 📊 Генерация Excel

#### [ExcelReportGenerator](excel-generator.md)
Генератор профессиональных Excel отчётов с автоматической стилизацией.

**Основные методы:**
- `generate_comprehensive_report()` - комплексный отчёт (dual-sheet)
- `create_report()` - простой отчёт

**Возможности:**
- 📄 Dual-sheet отчёты
- 🎨 Автоматическая стилизация
- 🦓 Зебра-группировка
- ✅ Валидация качества

---

### 🎼 Оркестрация

#### [WorkflowOrchestrator](workflow.md)
Координатор процесса генерации отчётов.

**Основной метод:**
- `generate_report()` - полный цикл генерации

**Процесс:**
1. Получение счетов из Bitrix24
2. Обогащение данными компаний
3. Получение товаров (batch)
4. Обработка и валидация
5. Генерация Excel

**Оптимизации v2.4.0:**
- ⚡ Batch обработка
- 💾 Кэширование
- 🚀 До 5-10x ускорение

---

### ⚙️ Конфигурация

#### [ConfigReader](config-reader.md)
Безопасное управление конфигурацией приложения.

**Основные методы:**
- `get_webhook_url()` - webhook URL (с приоритетами)
- `get_report_period_config()` - период отчёта
- `get_app_config()` - настройки приложения
- `validate()` - валидация конфигурации

**Возможности:**
- 🔐 Гибридная система (.env + config.ini)
- 🎯 Приоритеты конфигурации
- 🔒 Маскировка секретов

---

## 🚀 Quick Start

### Базовое использование

```python
from src.core.app import AppFactory

# Самый простой способ
with AppFactory.create_app('config.ini') as app:
    success = app.generate_report()
    
    if success:
        print("Отчёт создан!")
```

### Продвинутое использование

```python
from src.bitrix24_client.client import Bitrix24Client
from src.data_processor.data_processor import DataProcessor
from src.excel_generator.generator import ExcelReportGenerator

# Прямое использование компонентов
client = Bitrix24Client(webhook_url="...")
processor = DataProcessor()
generator = ExcelReportGenerator()

# Получение данных
invoices = client.get_smart_invoices("2024-01-01", "2024-01-31")

# Обработка
processor.set_bitrix_client(client)
processed = processor.process_invoice_batch(invoices, "2024-01-01", "2024-01-31")

# Генерация
generator.generate_comprehensive_report(
    brief_data=processed,
    detailed_data=detailed_products,
    output_path="report.xlsx"
)
```

---

## 📊 Использование по уровням

### 🟢 Уровень 1: Простое использование
**Целевая аудитория**: Конечные пользователи

- [ReportGeneratorApp](app.md) - всё что нужно

### 🟡 Уровень 2: Настройка компонентов
**Целевая аудитория**: Продвинутые пользователи

- [ReportGeneratorApp](app.md) + настройка конфигурации
- [ConfigReader](config-reader.md) для управления настройками

### 🔴 Уровень 3: Глубокая интеграция
**Целевая аудитория**: Разработчики

- Прямое использование всех компонентов
- [Bitrix24Client](bitrix24-client.md) для кастомных запросов
- [DataProcessor](data-processor.md) для особой обработки
- [ExcelReportGenerator](excel-generator.md) для специальных отчётов

---

## 🔍 Поиск по функционалу

### Работа со счетами
- [Получение счетов](bitrix24-client.md#get_smart_invoices)
- [Детальная информация о счёте](bitrix24-client.md#get_detailed_invoice_data)
- [Обработка счёта](data-processor.md#process_invoice_record)

### Работа с товарами
- [Получение товаров](bitrix24-client.md#get_products_by_invoice)
- [Пакетное получение](bitrix24-client.md#get_products_by_invoices_batch)
- [Форматирование для Excel](data-processor.md#format_detailed_products_for_excel)

### Работа с компаниями
- [Информация о компании](bitrix24-client.md#get_company_info_by_invoice)
- [Обогащение данными](data-processor.md#process_invoice_batch)

### Генерация отчётов
- [Комплексный отчёт](excel-generator.md#generate_comprehensive_report)
- [Простой отчёт](excel-generator.md#create_report)
- [Полный процесс](workflow.md#generate_report)

---

## 📚 Дополнительные ресурсы

### Руководства
- [Quick Start Guide](../../user/quick-start.md) - начало работы
- [Configuration Guide](../../user/configuration.md) - настройка
- [User Guide](../../user/usage-guide.md) - полное руководство

### Примеры
- [Базовые примеры](../../examples/) - простые сценарии
- [Продвинутые примеры](../../examples/) - сложные случаи

### Техническая документация
- [Architecture](../architecture.md) - архитектура системы
- [Development](../development.md) - разработка
- [Testing](../testing.md) - тестирование

---

## 🤝 Поддержка

**Нужна помощь?**

1. 📖 [FAQ](../../user/faq.md) - частые вопросы
2. 🔧 [Troubleshooting](../../user/troubleshooting.md) - решение проблем
3. 💬 [Discussions](https://github.com/bivlked/ReportB24/discussions) - обсуждения
4. 🐛 [Issues](https://github.com/bivlked/ReportB24/issues) - сообщить об ошибке

---

**Версия**: v3.0.2  
**Последнее обновление**: 2025-11-01
