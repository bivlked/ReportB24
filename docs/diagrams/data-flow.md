# 📊 Data Flow - Поток данных

Визуализация потока данных от Bitrix24 API через систему до финального Excel отчёта.

---

## 🌊 Полный поток данных

```mermaid
graph LR
    subgraph "Bitrix24 Cloud"
        B24_SI[("Smart Invoices<br/>crm.item.list")]
        B24_PR[("Products<br/>crm.product.list")]
        B24_CO[("Companies<br/>crm.company.get")]
    end
    
    subgraph "Bitrix24Client"
        API["REST API Client"]
        Cache[("💾 Cache<br/>LRU")]
        RateLimit["⏱️ Rate Limiter<br/>2 req/sec"]
    end
    
    subgraph "Raw Data"
        RawInvoices["📑 Raw Invoices<br/>JSON"]
        RawProducts["🛍️ Raw Products<br/>JSON"]
        RawCompanies["🏢 Raw Companies<br/>JSON"]
    end
    
    subgraph "DataProcessor"
        Validator["✅ Validator"]
        Enricher["➕ Enricher"]
        Formatter["🎨 Formatter"]
    end
    
    subgraph "Processed Data"
        BriefData["📋 Brief Data<br/>List[Dict]"]
        DetailedData["📊 Detailed Data<br/>List[Dict]"]
    end
    
    subgraph "ExcelGenerator"
        BriefSheet["📄 Краткий лист"]
        DetailedSheet["📄 Детальный лист"]
        Styler["🎨 Styler"]
    end
    
    subgraph "Output"
        Excel[("📗 Excel Report<br/>.xlsx")]
    end
    
    %% Data Flow
    B24_SI -->|JSON| API
    B24_PR -->|JSON| API
    B24_CO -->|JSON| API
    
    API --> RateLimit
    RateLimit --> Cache
    
    Cache --> RawInvoices
    Cache --> RawProducts
    Cache --> RawCompanies
    
    RawInvoices --> Validator
    RawProducts --> Validator
    RawCompanies --> Validator
    
    Validator --> Enricher
    Enricher --> Formatter
    
    Formatter --> BriefData
    Formatter --> DetailedData
    
    BriefData --> BriefSheet
    DetailedData --> DetailedSheet
    
    BriefSheet --> Styler
    DetailedSheet --> Styler
    
    Styler --> Excel
    
    %% Styling
    classDef source fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef client fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef raw fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef process fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef data fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef output fill:#4caf50,stroke:#2e7d32,stroke-width:3px
    
    class B24_SI,B24_PR,B24_CO source
    class API,Cache,RateLimit client
    class RawInvoices,RawProducts,RawCompanies raw
    class Validator,Enricher,Formatter process
    class BriefData,DetailedData data
    class Excel output
```

---

## 📋 Детальное преобразование данных

### 1. Raw Invoice → Brief Data

```mermaid
graph LR
    subgraph "Bitrix24 JSON"
        A1["id: 12345"]
        A2["accountNumber: 'СЧ-123'"]
        A3["opportunity: '125000.50'"]
        A4["dateCreate: '2024-01-15T10:30:00'"]
        A5["companyId: 789"]
    end
    
    subgraph "Validation & Enrichment"
        V["✅ Валидация"]
        E["➕ Обогащение<br/>(компания, ИНН)"]
        F["🎨 Форматирование"]
    end
    
    subgraph "Brief Data"
        B1["account_number: 'СЧ-123'"]
        B2["company_name: 'ООО Ромашка'"]
        B3["inn: '7707123456'"]
        B4["total_amount: 125000.50"]
        B5["date_create: '15.01.2024'"]
    end
    
    A1 & A2 & A3 & A4 & A5 --> V
    V --> E
    E --> F
    F --> B1 & B2 & B3 & B4 & B5
    
    style V fill:#9c27b0,color:white
    style E fill:#2196f3,color:white
    style F fill:#ff9800,color:white
```

---

### 2. Raw Products → Detailed Data

```mermaid
graph TB
    subgraph "Bitrix24 Product JSON"
        P1["id: 456"]
        P2["PRODUCT_NAME: 'Консультация'"]
        P3["QUANTITY: '5'"]
        P4["PRICE: '1500.00'"]
        P5["MEASURE_NAME: 'час'"]
    end
    
    subgraph "Processing Pipeline"
        V2["✅ Валидация<br/>типов"]
        C["🔄 Конвертация<br/>в float"]
        F2["🎨 Форматирование<br/>с разделителями"]
        M["📊 Добавление<br/>мета-данных"]
    end
    
    subgraph "Detailed Data"
        D1["product_name: 'Консультация'"]
        D2["unit: 'час'"]
        D3["quantity_raw: 5.0"]
        D4["price_raw: 1500.0"]
        D5["formatted_quantity: '5.00'"]
        D6["formatted_price: '1 500.00'"]
        D7["formatted_total: '7 500.00'"]
        D8["account_number: 'СЧ-123'"]
        D9["company_name: '...'"]
        D10["inn: '...'"]
    end
    
    P1 & P2 & P3 & P4 & P5 --> V2
    V2 --> C
    C --> F2
    F2 --> M
    M --> D1 & D2 & D3 & D4 & D5 & D6 & D7 & D8 & D9 & D10
```

---

## 🔄 Трансформации данных

### Валидация

```mermaid
graph LR
    Input["Raw Data"] --> Check1{"Поля<br/>есть?"}
    Check1 -->|No| Error1["❌ Missing Field"]
    Check1 -->|Yes| Check2{"Тип<br/>верен?"}
    Check2 -->|No| Error2["❌ Type Error"]
    Check2 -->|Yes| Check3{"Значение<br/>валидно?"}
    Check3 -->|No| Warn["⚠️ Warning"]
    Check3 -->|Yes| OK["✅ Valid"]
    
    style Error1 fill:#f44336,color:white
    style Error2 fill:#f44336,color:white
    style Warn fill:#ff9800,color:white
    style OK fill:#4caf50,color:white
```

**Проверки**:
- Обязательные поля
- Типы данных (str, int, float)
- Бизнес-правила (сумма > 0)
- Форматы (даты, ИНН)

---

### Обогащение (Enrichment)

```mermaid
graph TB
    Invoice["📄 Счёт"] --> NeedCompany{"Нужна<br/>компания?"}
    NeedCompany -->|Yes| GetCompany["🏢 get_company_info_by_invoice()"]
    NeedCompany -->|No| Skip
    
    GetCompany --> Cache{"В кэше?"}
    Cache -->|Yes| FromCache["💾 Из кэша"]
    Cache -->|No| FromAPI["🌐 Из Bitrix24"]
    
    FromAPI --> SaveCache["💾 Сохранить в кэш"]
    
    FromCache & SaveCache --> AddData["➕ Добавить к счёту"]
    Skip --> AddData
    
    AddData --> Enriched["✨ Обогащённый счёт"]
    
    style Enriched fill:#4caf50,color:white
```

**Добавляется**:
- Название компании
- ИНН компании
- Дополнительные поля

---

### Форматирование

```mermaid
graph LR
    Raw["Raw Value"] --> Type{"Тип?"}
    
    Type -->|Number| Num["🔢 Число"]
    Type -->|Date| Date["📅 Дата"]
    Type -->|String| Str["📝 Строка"]
    
    Num --> NumFormat["Разделители тысяч<br/>2 знака после запятой<br/>125,000.50"]
    Date --> DateFormat["Русский формат<br/>ДД.ММ.ГГГГ<br/>15.01.2024"]
    Str --> StrFormat["Обрезка<br/>Capitalize<br/>UTF-8"]
    
    NumFormat & DateFormat & StrFormat --> Formatted["✨ Formatted"]
    
    style Formatted fill:#4caf50,color:white
```

---

## 📊 Структуры данных

### Brief Data Structure

```python
{
    "account_number": str,        # "СЧ-00123"
    "company_name": str,          # "ООО Ромашка"
    "inn": str,                   # "7707123456"
    "total_amount": float,        # 125000.50
    "date_create": str,           # "15.01.2024"
    "date_create_raw": datetime,  # datetime(2024, 1, 15)
    "invoice_id": int,            # 12345
    "currency": str               # "RUB"
}
```

### Detailed Data Structure

```python
{
    "account_number": str,        # "СЧ-00123"
    "company_name": str,          # "ООО Ромашка"
    "inn": str,                   # "7707123456"
    "product_name": str,          # "Консультация юриста"
    "unit": str,                  # "час"
    "quantity_raw": float,        # 5.0
    "price_raw": float,           # 1500.0
    "formatted_quantity": str,    # "5.00"
    "formatted_price": str,       # "1 500.00"
    "formatted_total": str,       # "7 500.00"
    "invoice_id": int             # 12345
}
```

---

## 🎨 Excel Styling Pipeline

```mermaid
graph TB
    Data["📊 Data"] --> Sheet["📄 Sheet Creation"]
    
    Sheet --> Headers["🎨 Headers Styling"]
    Sheet --> Body["📝 Body Styling"]
    
    Headers --> HFont["✍️ Font: Bold, 11pt"]
    Headers --> HFill["🎨 Fill: Gray"]
    Headers --> HAlign["📐 Align: Center"]
    
    Body --> BFont["✍️ Font: Regular, 10pt"]
    Body --> BFill["🎨 Fill: Zebra Groups"]
    Body --> BAlign["📐 Align: Left/Right"]
    Body --> BNumber["🔢 Number Format"]
    
    HFont & HFill & HAlign & BFont & BFill & BAlign & BNumber --> Width["📏 Auto Width"]
    Width --> Borders["🔲 Borders"]
    Borders --> Final["✅ Styled Sheet"]
    
    style Final fill:#4caf50,color:white
```

---

## 🔗 Data Validation Flow

```mermaid
sequenceDiagram
    participant Raw as Raw Data
    participant Val as Validator
    participant Metrics as Metrics
    participant Log as Logger
    participant Output as Output
    
    Raw->>Val: validate_brief_data()
    
    loop Для каждой записи
        Val->>Val: Проверка полей
        Val->>Val: Проверка типов
        Val->>Val: Бизнес-правила
        
        alt Ошибка
            Val->>Metrics: Error++
            Val->>Log: log.error()
        else Предупреждение
            Val->>Metrics: Warning++
            Val->>Log: log.warning()
        else OK
            Val->>Metrics: Valid++
        end
    end
    
    Val->>Metrics: Формирование метрик
    Metrics-->>Output: ValidationMetrics
```

---

## 📈 Data Volume Analysis

| Этап | Input | Output | Коэффициент |
|------|-------|--------|-------------|
| Raw Invoices | 100 записей | 100 записей | 1:1 |
| With Products | 100 счетов | ~500 товаров | 1:5 |
| After Validation | 500 товаров | 495 валидных | 0.99:1 |
| Excel Rows | 495 товаров | 495 строк + headers | 1:1 |

**Средний коэффициент**: 1 счёт = 5 товаров

---

## 🔗 Связанные диаграммы

- **[System Overview](system-overview.md)** - Общая архитектура
- **[Workflow](workflow.md)** - Процесс генерации
- **[Architecture](architecture.md)** - Детальная архитектура

---

[← Назад к диаграммам](index.md) | [Architecture →](architecture.md)
