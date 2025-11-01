# ⚙️ ConfigReader API Reference

**Модуль**: `src.config.config_reader`  
**Классы**: `ConfigReader`, `SecureConfigReader`  
**Версия**: v3.0.2

---

## 📖 Обзор

`ConfigReader` и `SecureConfigReader` — компоненты для безопасного управления конфигурацией приложения. Поддерживают гибридную систему: `.env` для секретов + `config.ini` для настроек.

### Ключевые возможности

- 🔐 **Безопасность** - секреты в `.env`, настройки в `config.ini`
- 🎯 **Приоритеты** - переменные окружения → .env → config.ini
- ✅ **Валидация** конфигурации
- 🔒 **Маскировка** webhook URL в логах
- 📁 **Автосоздание** директорий

---

## ⚡ Быстрый старт

```python
from src.config.config_reader import SecureConfigReader

# Инициализация (автоматически загружает .env)
config = SecureConfigReader(config_path="config.ini")

# Получение webhook URL (из .env приоритетно)
webhook_url = config.get_webhook_url()

# Получение конфигурации периода отчёта
period = config.get_report_period_config()
print(f"Период: {period.start_date} - {period.end_date}")

# Получение конфигурации приложения
app_config = config.get_app_config()
print(f"Сохранять в: {app_config.default_save_folder}")
```

---

## 🎯 Основные методы

### SecureConfigReader

#### `get_webhook_url()`

Возвращает webhook URL с учётом приоритетов.

**Приоритет:**
1. `os.environ['BITRIX24_WEBHOOK_URL']`
2. `.env` файл
3. `config.ini`

**Возвращает**: `str` - webhook URL

---

#### `get_report_period_config()`

Возвращает конфигурацию периода отчёта.

**Возвращает**: `ReportPeriodConfig`

```python
period = config.get_report_period_config()
print(period.start_date)  # "2024-01-01"
print(period.end_date)    # "2024-01-31"
```

---

#### `get_app_config()`

Возвращает конфигурацию приложения.

**Возвращает**: `AppConfig`

```python
app = config.get_app_config()
print(app.default_save_folder)    # "reports"
print(app.default_filename)        # "report_2024-01.xlsx"
print(app.create_folder_if_missing)  # True
```

---

#### `validate()`

Проверяет корректность конфигурации.

**Возвращает**: `bool` - валидность конфигурации

**Пример:**

```python
if config.validate():
    print("Конфигурация валидна")
else:
    errors = config.get_validation_errors()
    print(f"Ошибки: {errors}")
```

---

## 🔐 Безопасность

### Гибридная система

```
Приоритет (от высокого к низкому):
1. os.environ - переменные окружения
2. .env - секреты (webhook URL)
3. config.ini - настройки приложения
```

### Маскировка webhook

```python
# Webhook URL автоматически маскируется в логах
# Было: https://portal.bitrix24.ru/rest/12/abc123def456/
# Стало: https://portal.bitrix24.ru/rest/12/***/
```

### Файл .env

```bash
# .env (не коммитится в git)
BITRIX24_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/12/your-key/
```

---

## 📁 Структура config.ini

```ini
[Bitrix24]
webhook_url = https://portal.bitrix24.ru/rest/12/key/

[ReportPeriod]
start_date = 2024-01-01
end_date = 2024-01-31

[App]
default_save_folder = reports
default_filename = report_{date}.xlsx
create_folder_if_missing = true
```

---

## 📚 См. также

- [ReportGeneratorApp API](app.md) - использование конфигурации
- [Security Guide](../security-deep-dive.md) - безопасность
- [Configuration Guide](../../user/configuration.md) - настройка

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
