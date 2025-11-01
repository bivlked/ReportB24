# 🏛️ Архитектура системы

Подробная многоуровневая архитектура ReportB24 с компонентами, слоями и взаимодействиями.

---

## 🏗️ Слоистая архитектура

```mermaid
graph TB
    subgraph "Presentation Layer"
        CLI["🖥️ CLI<br/>run_report.py"]
        API_REST["🌐 REST API<br/>(Flask)"]
    end
    
    subgraph "Application Layer"
        App["🎯 ReportGeneratorApp<br/>Application Facade"]
        Factory["🏭 AppFactory<br/>Component Factory"]
        Workflow["🔄 WorkflowOrchestrator<br/>Business Logic"]
    end
    
    subgraph "Service Layer"
        subgraph "Core Services"
            Client["📡 Bitrix24Client<br/>API Communication"]
            Processor["⚙️ DataProcessor<br/>Data Transformation"]
            Generator["📊 ExcelReportGenerator<br/>Report Generation"]
        end
        
        subgraph "Supporting Services"
            Config["⚙️ ConfigReader<br/>Configuration Management"]
            ErrorHandler["🛡️ ErrorHandler<br/>Error Management"]
            ConsoleUI["🖼️ ConsoleUI<br/>User Interface"]
        end
    end
    
    subgraph "Infrastructure Layer"
        subgraph "Cross-cutting Concerns"
            Logger["📝 Logger<br/>Logging"]
            Cache["💾 Cache<br/>LRU Cache"]
            RateLimiter["⏱️ RateLimiter<br/>API Throttling"]
            Validator["✅ Validator<br/>Data Validation"]
        end
        
        subgraph "External Adapters"
            HTTPAdapter["🔌 Requests<br/>HTTP Client"]
            ExcelAdapter["📗 openpyxl<br/>Excel Library"]
        end
    end
    
    subgraph "External Systems"
        Bitrix24["🌐 Bitrix24<br/>REST API"]
        FileSystem["💾 File System<br/>reports/, logs/"]
    end
    
    %% Relationships
    CLI --> App
    API_REST --> App
    
    App --> Factory
    App --> Workflow
    Factory --> Config
    
    Workflow --> Client
    Workflow --> Processor
    Workflow --> Generator
    
    Client --> Cache
    Client --> RateLimiter
    Client --> HTTPAdapter
    Client --> Logger
    
    Processor --> Validator
    Processor --> Logger
    
    Generator --> ExcelAdapter
    Generator --> Logger
    
    HTTPAdapter --> Bitrix24
    ExcelAdapter --> FileSystem
    Logger --> FileSystem
    
    App --> ErrorHandler
    App --> ConsoleUI
    
    %% Styling
    classDef presentation fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef application fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef service fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef external fill:#ffebee,stroke:#c62828,stroke-width:2px
    
    class CLI,API_REST presentation
    class App,Factory,Workflow application
    class Client,Processor,Generator,Config,ErrorHandler,ConsoleUI service
    class Logger,Cache,RateLimiter,Validator,HTTPAdapter,ExcelAdapter infra
    class Bitrix24,FileSystem external
```

---

## 🎯 Компоненты по слоям

### 1. Presentation Layer (Представление)

```mermaid
graph LR
    User["👤 User"] --> CLI["🖥️ CLI<br/>Command Line"]
    External["🔗 External System"] --> API["🌐 REST API<br/>HTTP Endpoints"]
    
    CLI --> AppFacade["🎯 App Facade"]
    API --> AppFacade
    
    style User fill:#4caf50,color:white
    style External fill:#2196f3,color:white
    style AppFacade fill:#ff9800,color:white
```

**Ответственность**:
- Взаимодействие с пользователем
- Парсинг команд и параметров
- Форматирование вывода

**Компоненты**:
- `run_report.py` - CLI точка входа
- Flask API routes - HTTP endpoints
- `ConsoleUI` - форматированный вывод

---

### 2. Application Layer (Приложение)

```mermaid
graph TB
    Facade["🎯 ReportGeneratorApp"] --> Init["Initialization"]
    Facade --> Validation["Configuration Validation"]
    Facade --> Generation["Report Generation"]
    
    Init --> Factory["🏭 AppFactory"]
    Factory --> Components["Create Components"]
    
    Generation --> Workflow["🔄 WorkflowOrchestrator"]
    Workflow --> Coordination["Coordinate Services"]
    
    style Facade fill:#7b1fa2,color:white
    style Workflow fill:#9c27b0,color:white
```

**Ответственность**:
- Координация бизнес-логики
- Управление жизненным циклом
- Транзакционные границы

**Компоненты**:
- `ReportGeneratorApp` - главный фасад
- `AppFactory` - фабрика компонентов
- `WorkflowOrchestrator` - оркестратор процесса

---

### 3. Service Layer (Сервисы)

#### Core Services

```mermaid
graph LR
    subgraph "Data Services"
        Client["📡 Bitrix24Client<br/>API Requests"]
        Processor["⚙️ DataProcessor<br/>Data Transform"]
        Generator["📊 ExcelGenerator<br/>Report Builder"]
    end
    
    Client -->|Raw Data| Processor
    Processor -->|Processed Data| Generator
    Generator -->|Excel File| Output["💾 Output"]
    
    style Client fill:#2196f3,color:white
    style Processor fill:#4caf50,color:white
    style Generator fill:#ff9800,color:white
    style Output fill:#f44336,color:white
```

**Ответственность**:
- Бизнес-логика предметной области
- Трансформация данных
- Генерация отчётов

---

#### Supporting Services

```mermaid
graph TB
    Config["⚙️ ConfigReader"] --> Priority["Priority System<br/>.env > config.ini"]
    Config --> Validation["Validation"]
    Config --> Security["Security<br/>Webhook Masking"]
    
    ErrorHandler["🛡️ ErrorHandler"] --> Capture["Error Capture"]
    ErrorHandler --> Format["Error Formatting"]
    ErrorHandler --> Recovery["Recovery Strategy"]
    
    style Config fill:#ff9800,color:white
    style ErrorHandler fill:#f44336,color:white
```

**Ответственность**:
- Конфигурация приложения
- Обработка ошибок
- UI взаимодействие

---

### 4. Infrastructure Layer (Инфраструктура)

```mermaid
graph TB
    subgraph "Cross-Cutting"
        Logger["📝 Logging<br/>TimedRotatingFileHandler"]
        Cache["💾 Caching<br/>LRU Strategy"]
        RateLimit["⏱️ Rate Limiting<br/>≤2 req/sec"]
        Validator["✅ Validation<br/>Data Quality"]
    end
    
    subgraph "Adapters"
        HTTP["🔌 HTTP Client<br/>requests + retry"]
        Excel["📗 Excel Library<br/>openpyxl"]
    end
    
    Logger --> FileSystem["💾 logs/"]
    Excel --> FileSystem2["💾 reports/"]
    
    style FileSystem fill:#4caf50,color:white
    style FileSystem2 fill:#4caf50,color:white
```

**Ответственность**:
- Логирование (с ротацией)
- Кэширование (LRU)
- Rate limiting (Bitrix24)
- Валидация данных
- Внешние адаптеры

---

## 🔄 Dependency Flow

```mermaid
graph TD
    Top["👤 User"] --> Layer1["Presentation"]
    Layer1 --> Layer2["Application"]
    Layer2 --> Layer3["Service"]
    Layer3 --> Layer4["Infrastructure"]
    Layer4 --> Bottom["🌐 External"]
    
    Bottom -.->|Dependency Inversion| Layer3
    Layer3 -.->|DI| Layer2
    Layer2 -.->|DI| Layer1
    
    style Top fill:#4caf50,color:white
    style Bottom fill:#f44336,color:white
    style Layer1 fill:#e3f2fd
    style Layer2 fill:#f3e5f5
    style Layer3 fill:#e8f5e9
    style Layer4 fill:#fff3e0
```

**Принцип**: Зависимости направлены **вниз** по слоям

---

## 📦 Module Structure

```mermaid
graph LR
    subgraph "src/"
        Core["core/"]
        B24["bitrix24_client/"]
        Data["data_processor/"]
        Excel["excel_generator/"]
        Cfg["config/"]
    end
    
    Core --> App["app.py"]
    Core --> Workflow["workflow.py"]
    Core --> Error["error_handler.py"]
    
    B24 --> Client["client.py"]
    B24 --> Cache["api_cache.py"]
    
    Data --> Processor["data_processor.py"]
    
    Excel --> Generator["generator.py"]
    Excel --> Validation["validation.py"]
    Excel --> UI["console_ui.py"]
    
    Cfg --> ConfigReader["config_reader.py"]
    Cfg --> Settings["settings.py"]
    
    style Core fill:#7b1fa2,color:white
    style B24 fill:#2196f3,color:white
    style Data fill:#4caf50,color:white
    style Excel fill:#ff9800,color:white
    style Cfg fill:#f57c00,color:white
```

---

## 🔗 Component Relationships

### High Coupling Components

```mermaid
graph LR
    App["App"] ---|Strong| Workflow
    Workflow ---|Strong| Client
    Workflow ---|Strong| Processor
    Workflow ---|Strong| Generator
    
    style App fill:#f44336,color:white
    style Workflow fill:#f44336,color:white
```

### Low Coupling Components

```mermaid
graph LR
    Client -.-|Weak| Cache
    Processor -.-|Weak| Validator
    Generator -.-|Weak| Logger
    
    style Client fill:#4caf50,color:white
    style Cache fill:#4caf50,color:white
```

---

## 🎨 Design Patterns

### 1. Factory Pattern

```mermaid
classDiagram
    class AppFactory {
        +create_app(config_path) ReportGeneratorApp
        +create_config_reader(path) ConfigReader
        +create_bitrix_client(url) Bitrix24Client
    }
    
    class ReportGeneratorApp {
        -config_reader
        -bitrix_client
        -data_processor
        -excel_generator
    }
    
    AppFactory ..> ReportGeneratorApp : creates
```

**Применение**: Создание и инициализация компонентов

---

### 2. Facade Pattern

```mermaid
classDiagram
    class ReportGeneratorApp {
        +initialize() bool
        +generate_report(path) Result
        +validate_configuration() bool
        +test_api_connection() bool
    }
    
    class WorkflowOrchestrator
    class Bitrix24Client
    class DataProcessor
    class ExcelGenerator
    
    ReportGeneratorApp --> WorkflowOrchestrator
    ReportGeneratorApp --> Bitrix24Client
    ReportGeneratorApp --> DataProcessor
    ReportGeneratorApp --> ExcelGenerator
```

**Применение**: Упрощённый интерфейс для сложной подсистемы

---

### 3. Strategy Pattern

```mermaid
classDiagram
    class Bitrix24Client {
        +get_products_by_invoice(id)
        +get_products_by_invoices_batch(ids)
    }
    
    class SequentialStrategy {
        +execute()
    }
    
    class BatchStrategy {
        +execute()
    }
    
    Bitrix24Client --> SequentialStrategy
    Bitrix24Client --> BatchStrategy
```

**Применение**: Выбор стратегии загрузки (sequential vs batch)

---

### 4. Context Manager Pattern

```python
# Правильное управление ресурсами
with AppFactory.create_app() as app:
    result = app.generate_report()
# Автоматическая очистка ресурсов
```

**Применение**: Управление жизненным циклом приложения

---

## 🔒 Security Architecture

```mermaid
graph TB
    Config["⚙️ Configuration"] --> Env[".env File<br/>Sensitive Data"]
    Config --> Ini["config.ini<br/>Non-sensitive"]
    
    Env --> Mask["🔐 Webhook Masking<br/>in Logs"]
    Env --> Encrypt["🔐 Encryption<br/>(future)"]
    
    Logs["📝 Logs"] --> NoWebhook["✅ No Webhooks<br/>in Logs"]
    
    style Env fill:#f44336,color:white
    style Mask fill:#4caf50,color:white
    style NoWebhook fill:#4caf50,color:white
```

**Security Measures**:
1. ✅ `.env` для sensitive данных
2. ✅ Маскирование webhook в логах
3. ✅ `.env` в `.gitignore`
4. ✅ Валидация входных данных
5. ⚠️ Шифрование (планируется)

---

## 📊 Performance Optimizations

```mermaid
graph LR
    subgraph "Optimization Strategies"
        Batch["⚡ Batch API<br/>50 requests → 1"]
        Cache["💾 LRU Cache<br/>Company data"]
        RateLimit["⏱️ Rate Limiting<br/>Avoid throttling"]
        Async["🔄 Async Ready<br/>Future enhancement"]
    end
    
    Batch --> Fast["16x Faster"]
    Cache --> Fast
    RateLimit --> Stable["Stable<br/>Performance"]
    
    style Fast fill:#4caf50,color:white
    style Stable fill:#2196f3,color:white
```

---

## 🔗 External Dependencies

| Layer | Dependencies | Purpose |
|-------|-------------|---------|
| **HTTP** | `requests` | API communication |
| **Excel** | `openpyxl` | Excel generation |
| **Config** | `python-dotenv` | .env loading |
| **CLI** | `sys`, `argparse` | Command line |
| **Logging** | `logging` | Application logs |

**Total**: 5 core dependencies (minimal footprint)

---

## 📈 Scalability Strategy

```mermaid
graph TB
    Current["Current<br/>Single Process"] --> Future1["Phase 1<br/>Multi-threading"]
    Future1 --> Future2["Phase 2<br/>Multi-processing"]
    Future2 --> Future3["Phase 3<br/>Distributed"]
    
    Future3 --> Queue["Message Queue<br/>(RabbitMQ)"]
    Future3 --> Workers["Worker Processes<br/>(Celery)"]
    Future3 --> DB["Shared Database<br/>(PostgreSQL)"]
    
    style Current fill:#ff9800,color:white
    style Future3 fill:#4caf50,color:white
```

---

## 🔗 Связанные диаграммы

- **[System Overview](system-overview.md)** - Общая схема
- **[Workflow](workflow.md)** - Процесс генерации
- **[Data Flow](data-flow.md)** - Поток данных

---

[← Назад к диаграммам](index.md) | [System Overview →](system-overview.md)
