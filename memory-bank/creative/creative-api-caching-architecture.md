# CREATIVE PHASE: API CACHING ARCHITECTURE

📌 CREATIVE PHASE START: API Caching Architecture  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1️⃣ PROBLEM

**Description**: Дизайн системы кэширования для минимизации дублирующихся API запросов при генерации двухлистового отчета.

**Requirements**:
- Уменьшить количество API запросов к Bitrix24 минимум на 30%
- Сохранить актуальность данных для отчетов
- Обеспечить стабильность при сбоях API
- Интегрироваться с существующей архитектурой DataProcessor

**Constraints**:
- Не использовать BATCH API (исключен из проекта)
- Память ограничена для кэша (разумные пределы)
- Время жизни кэша должно быть настраиваемым
- Совместимость с одностраничным отчетом (не изменять)

**Current Problem**: При генерации двухлистового отчета мы вызываем одинаковые API методы для обоих листов:
- `crm.item.productrow.list` - для каждого счета дважды
- `crm.requisite.link.list` и `crm.requisite.get` - для ИНН компаний дважды

## 2️⃣ OPTIONS

**Option A**: In-Memory Cache with TTL - Простое кэширование в памяти с временем жизни  
**Option B**: Persistent Cache with SQLite - Постоянное кэширование в локальной БД  
**Option C**: Layered Cache (Memory + Disk) - Двухуровневое кэширование  
**Option D**: Request Deduplication - Дедупликация запросов без постоянного хранения

## 3️⃣ ANALYSIS

| Criterion | Memory+TTL | SQLite Cache | Layered Cache | Deduplication |
|-----------|------------|--------------|---------------|---------------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Complexity | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Memory Usage | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Persistence | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Data Freshness | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Integration | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Key Insights**:
- Memory+TTL самый быстрый, но теряет данные при перезапуске
- SQLite Cache сложен в реализации и может вызвать проблемы с concurrent access
- Layered Cache максимальная сложность при минимальной выгоде для наших объемов
- Deduplication дает лучший баланс производительности и простоты

## 4️⃣ DECISION

**Selected**: Option D: Request Deduplication with Short-Term Memory Cache

**Rationale**: 
- Максимальная производительность при минимальной сложности
- Отличная интеграция с существующим кодом
- Не требует управления состоянием между сессиями
- Идеально подходит для случая двухлистового отчета (данные нужны только в рамках одной генерации)

## 5️⃣ IMPLEMENTATION NOTES

### Архитектурная схема:
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Report         │    │  APIDataCache    │    │  Bitrix24       │
│  Generator      │───▶│  Deduplicator    │───▶│  API            │
│                 │    │                  │    │                 │
│  - Brief Sheet  │    │  - Request Hash  │    │  - productrow   │
│  - Detail Sheet │    │  - Memory Store  │    │  - requisite    │
└─────────────────┘    │  - TTL=300s      │    └─────────────────┘
                       └──────────────────┘
```

### Ключевые компоненты:
1. **APIDataCache класс**: Центральный кэш-менеджер
2. **Request Hashing**: SHA256 хэш параметров запроса для уникальности  
3. **TTL Management**: Автоматическое истечение кэша через 5 минут
4. **Integration Points**: Внедрение в DataProcessor и Bitrix24Client

### Детали реализации:
- Использовать `threading.Lock()` для thread-safety
- Кэшировать ответы API как JSON с временными метками
- Автоматическая очистка устаревших записей
- Логирование cache hit/miss для мониторинга эффективности

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  
📌 CREATIVE PHASE END - API CACHING ARCHITECTURE 