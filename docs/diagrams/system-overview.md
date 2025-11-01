# 🏗️ Общая схема системы

Высокоуровневая архитектура ReportB24 - интеграция с Bitrix24 для генерации Excel отчётов.

---

## 📊 Общая схема

```mermaid
graph TB
    subgraph "Внешние системы"
        Bitrix24[("🌐 Bitrix24<br/>REST API")]
        User["👤 Пользователь"]
    end
    
    subgraph "ReportB24 Application"
        CLI["🖥️ CLI Interface<br/>run_report.py"]
        API["🌐 REST API<br/>(опционально)"]
        
        subgraph "Ядро приложения"
            App["🎯 ReportGeneratorApp<br/>Точка входа"]
            Config["⚙️ ConfigReader<br/>Конфигурация"]
            Workflow["🔄 WorkflowOrchestrator<br/>Координация"]
        end
        
        subgraph "Бизнес-логика"
            Client["📡 Bitrix24Client<br/>API клиент"]
            Processor["⚙️ DataProcessor<br/>Обработка данных"]
            Generator["📊 ExcelGenerator<br/>Генерация отчётов"]
        end
        
        subgraph "Инфраструктура"
            Cache["💾 Cache<br/>Кэширование"]
            Logger["📝 Logger<br/>Логирование"]
            Validator["✅ Validator<br/>Валидация"]
        end
    end
    
    subgraph "Хранилище"
        Excel[("📄 Excel файлы<br/>reports/")]
        Logs[("📋 Логи<br/>logs/")]
    end
    
    %% Взаимодействие
    User -->|Запуск| CLI
    User -->|HTTP| API
    
    CLI --> App
    API --> App
    
    App --> Config
    App --> Workflow
    
    Workflow --> Client
    Workflow --> Processor
    Workflow --> Generator
    
    Client <-->|REST API| Bitrix24
    Client --> Cache
    
    Processor --> Validator
    Generator --> Excel
    
    App --> Logger
    Logger --> Logs
    
    %% Стили
    classDef external fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef core fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef business fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef infra fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class Bitrix24,User external
    class App,Config,Workflow core
    class Client,Processor,Generator business
    class Cache,Logger,Validator infra
    class Excel,Logs storage
```

---

## 🔑 Ключевые компоненты

### 1. **Точки входа**

| Компонент | Назначение | Использование |
|-----------|-----------|---------------|
| **CLI** | Командная строка | Ручной запуск, скрипты |
| **REST API** | HTTP интерфейс | Интеграция, автоматизация |

### 2. **Ядро приложения**

| Компонент | Назначение | Ответственность |
|-----------|-----------|-----------------|
| **ReportGeneratorApp** | Главный класс | Инициализация, координация |
| **ConfigReader** | Конфигурация | Чтение settings из config.ini и .env |
| **WorkflowOrchestrator** | Оркестратор | Координация процесса генерации |

### 3. **Бизнес-логика**

| Компонент | Назначение | Функции |
|-----------|-----------|---------|
| **Bitrix24Client** | API клиент | Получение данных из Bitrix24 |
| **DataProcessor** | Обработчик | Валидация, обогащение, форматирование |
| **ExcelGenerator** | Генератор | Создание Excel с форматированием |

### 4. **Инфраструктура**

| Компонент | Назначение | Роль |
|-----------|-----------|------|
| **Cache** | Кэш | Ускорение повторных запросов |
| **Logger** | Логирование | Отладка, аудит |
| **Validator** | Валидация | Проверка качества данных |

---

## 🔄 Основной поток данных

```mermaid
sequenceDiagram
    participant User
    participant App
    participant Client
    participant Bitrix24
    participant Processor
    participant Generator
    participant Excel

    User->>App: Запуск генерации
    App->>Client: get_smart_invoices()
    Client->>Bitrix24: REST API запрос
    Bitrix24-->>Client: JSON data
    Client-->>App: Счета
    
    loop Для каждого счёта
        App->>Client: get_products_by_invoice()
        Client->>Bitrix24: REST API запрос
        Bitrix24-->>Client: Товары
        Client-->>App: Товары
        
        App->>Processor: Обработка данных
        Processor-->>App: Форматированные данные
    end
    
    App->>Generator: generate_comprehensive_report()
    Generator->>Excel: Создание файла
    Excel-->>Generator: Success
    Generator-->>App: Result
    App-->>User: ✅ Отчёт готов
```

---

## 📈 Метрики производительности

| Операция | Среднее время | Оптимизация |
|----------|--------------|-------------|
| Загрузка 100 счетов | ~3 сек | Batch API |
| Обработка данных | ~1 сек | Валидация |
| Генерация Excel | ~2 сек | openpyxl |
| **Итого** | **~6 сек** | v2.4.0+ |

---

## 🎯 Основные особенности

### ⚡ Производительность
- **Batch API** для загрузки товаров (до 50x быстрее)
- **Кэширование** компаний и продуктов
- **Параллельная обработка** (опционально)

### 🛡️ Надёжность
- **Автоматический retry** при временных ошибках
- **Rate limiting** (≤2 req/sec) для Bitrix24 API
- **Graceful degradation** при частичных ошибках

### ✅ Качество
- **Валидация данных** на всех этапах
- **Подробное логирование** для отладки
- **Метрики качества** в результате

---

## 🔗 Связанные диаграммы

- **[Workflow](workflow.md)** - Детальный процесс генерации
- **[Data Flow](data-flow.md)** - Поток данных через систему
- **[Architecture](architecture.md)** - Подробная архитектура

---

[← Назад к диаграммам](index.md) | [Workflow →](workflow.md)
