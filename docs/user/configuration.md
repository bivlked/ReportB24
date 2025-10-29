# 🔧 Configuration Guide

Полное руководство по настройке ReportB24.

---

## 📁 Файлы конфигурации

ReportB24 использует **гибридную систему конфигурации**:

| Файл | Назначение | Версионирование |
|------|-----------|-----------------|
| `.env` | **Секретные данные** (webhook URL) | ❌ Не коммитить (в .gitignore) |
| `config.ini` | **Публичные настройки** (периоды, папки) | ✅ Можно коммитить |

### Приоритет загрузки

```
1. Переменные окружения (os.environ)  ← Наивысший приоритет
2. .env файл
3. config.ini файл                     ← Наименьший приоритет
```

---

## 🔒 .env - Секретные данные

**Создание**:
```bash
copy .env-example .env  # Windows
cp .env-example .env    # Linux/Mac
```

**Содержимое**:

```env
# Bitrix24 Webhook URL (ОБЯЗАТЕЛЬНО)
BITRIX_WEBHOOK_URL=https://ваш-портал.bitrix24.ru/rest/12/abc123def456/

# Опционально: Дополнительные секреты
# DB_PASSWORD=your_database_password
# API_SECRET_KEY=your_api_secret
```

### Получение Webhook URL

1. **Bitrix24** → **Приложения** → **Вебхуки**
2. Создайте **входящий вебхук**
3. Выберите права:
   - ✅ `crm` - Доступ к CRM
   - ✅ `smart_invoice` - Доступ к умным счетам
4. Скопируйте URL

**Формат URL**:
```
https://{portal}.bitrix24.ru/rest/{user_id}/{webhook_code}/
```

⚠️ **Безопасность**:
- **Никогда** не коммитьте `.env` в Git
- Храните backup в безопасном месте
- Периодически обновляйте webhook

---

## ⚙️ config.ini - Публичные настройки

**Создание**:
```bash
copy config.ini.example config.ini  # Windows
cp config.ini.example config.ini    # Linux/Mac
```

### Секция [AppSettings]

**Базовые настройки приложения**:

```ini
[AppSettings]
# Папка для сохранения отчетов
defaultsavefolder = reports

# Имя файла по умолчанию
defaultfilename = bitrix24_report.xlsx

# Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
loglevel = INFO

# Файл логов
logfile = logs/app.log

# Максимальный размер файла логов (МБ)
maxlogsize = 10

# Количество backup файлов логов
backupcount = 5
```

**Параметры**:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `defaultsavefolder` | string | `reports` | Директория для отчетов |
| `defaultfilename` | string | `bitrix24_report.xlsx` | Имя файла отчета |
| `loglevel` | enum | `INFO` | Уровень детализации логов |
| `logfile` | string | `logs/app.log` | Путь к файлу логов |
| `maxlogsize` | int | `10` | Макс. размер лог-файла (МБ) |
| `backupcount` | int | `5` | Кол-во backup логов |

### Секция [ReportPeriod]

**Период для отчета**:

```ini
[ReportPeriod]
# Начальная дата (формат: дд.мм.гггг)
startdate = 01.01.2024

# Конечная дата (формат: дд.мм.гггг)
enddate = 31.03.2024
```

**Примеры**:

```ini
# Квартальный отчет Q1 2024
startdate = 01.01.2024
enddate = 31.03.2024

# Месячный отчет (март)
startdate = 01.03.2024
enddate = 31.03.2024

# Годовой отчет
startdate = 01.01.2024
enddate = 31.12.2024
```

### Секция [Performance] (опционально)

**Настройки производительности**:

```ini
[Performance]
# Размер пакета для batch запросов
batch_size = 50

# Максимум одновременных запросов к API
max_concurrent_requests = 2

# Размер кэша данных компаний
company_cache_size = 1000

# Использовать multiprocessing
use_multiprocessing = false

# Количество worker процессов
max_workers = 4

# Timeout для API запросов (секунды)
api_timeout = 30
```

### Секция [Excel] (опционально)

**Настройки генерации Excel**:

```ini
[Excel]
# Цвет заголовка краткого листа (hex)
summary_header_color = #FCE4D6

# Цвет заголовка детального листа (hex)
detailed_header_color = #C6E0B4

# Цвета зебра-эффекта
zebra_color_1 = #F2F2F2
zebra_color_2 = #FFFFFF

# Закрепление заголовков
freeze_panes = true

# Автоширина колонок
auto_width = true

# Показывать линии сетки
show_gridlines = true
```

---

## 🔄 Переменные окружения

Альтернатива файлам конфигурации (наивысший приоритет).

### Windows

**PowerShell**:
```powershell
$env:BITRIX_WEBHOOK_URL = "https://portal.bitrix24.ru/rest/12/abc123/"
$env:DEFAULT_SAVE_FOLDER = "reports"
```

**CMD**:
```cmd
set BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/abc123/
set DEFAULT_SAVE_FOLDER=reports
```

### Linux/Mac

**Bash/Zsh**:
```bash
export BITRIX_WEBHOOK_URL="https://portal.bitrix24.ru/rest/12/abc123/"
export DEFAULT_SAVE_FOLDER="reports"
```

**Постоянная установка** (добавьте в `~/.bashrc` или `~/.zshrc`):
```bash
echo 'export BITRIX_WEBHOOK_URL="your_url"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🎯 Примеры конфигураций

### Минимальная конфигурация

**Только .env**:
```env
BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/abc123/
```

ReportB24 использует значения по умолчанию для остальных параметров.

### Продакшн конфигурация

**.env**:
```env
BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/abc123/
```

**config.ini**:
```ini
[AppSettings]
defaultsavefolder = /var/reports
defaultfilename = production_report.xlsx
loglevel = WARNING
logfile = /var/log/reportb24/app.log
maxlogsize = 50
backupcount = 10

[ReportPeriod]
startdate = 01.01.2024
enddate = 31.12.2024

[Performance]
batch_size = 50
max_concurrent_requests = 3
company_cache_size = 2000
use_multiprocessing = true
max_workers = 8
api_timeout = 60
```

### Разработка (debug)

**.env**:
```env
BITRIX_WEBHOOK_URL=https://test-portal.bitrix24.ru/rest/12/test123/
```

**config.ini**:
```ini
[AppSettings]
defaultsavefolder = test_reports
defaultfilename = test_report.xlsx
loglevel = DEBUG
logfile = logs/debug.log
maxlogsize = 5
backupcount = 3

[ReportPeriod]
startdate = 01.01.2024
enddate = 31.01.2024

[Performance]
batch_size = 10
max_concurrent_requests = 1
company_cache_size = 100
use_multiprocessing = false
```

---

## 🔍 Валидация конфигурации

**Проверка конфигурации**:

```python
# validate_config.py
from src.config.config_reader import SecureConfigReader
from src.config.validation import validate_config

config = SecureConfigReader('config.ini')

try:
    validate_config(config)
    print("✅ Конфигурация валидна")
except ValueError as e:
    print(f"❌ Ошибка конфигурации: {e}")
```

**Запуск**:
```bash
python validate_config.py
```

---

## 🔧 Устранение проблем

### Ошибка: "Webhook URL not found"

**Причина**: Отсутствует `BITRIX_WEBHOOK_URL` в `.env`

**Решение**:
1. Убедитесь, что `.env` существует
2. Проверьте формат URL
3. Перезапустите приложение

### Ошибка: "Invalid config.ini format"

**Причина**: Синтаксическая ошибка в `config.ini`

**Решение**:
```bash
# Пересоздайте из примера
copy config.ini.example config.ini
```

### Ошибка: "Permission denied"

**Причина**: Нет прав на запись в `defaultsavefolder`

**Решение**:
```bash
# Создайте директорию с правами
mkdir reports
chmod 755 reports  # Linux/Mac
```

---

## 📚 Дополнительно

- 🚀 [Quick Start](quick-start.md) - Быстрый старт
- 📖 [User Guide](usage-guide.md) - Руководство пользователя
- 🔒 [Security Deep Dive](../technical/security-deep-dive.md) - Безопасность

---

<div align="center">

[← Installation](installation.md) • [User Guide →](usage-guide.md)

**Вопросы по конфигурации?** [FAQ](faq.md) • [Troubleshooting](troubleshooting.md)

</div>
