# 🔧 Troubleshooting Guide

Руководство по решению типичных проблем ReportB24.

---

## 🎯 Диагностика проблем

### Быстрая диагностика

```bash
# 1. Проверка Python
python --version  # Должно быть 3.8+

# 2. Проверка venv
pip list | grep openpyxl  # Должен быть установлен

# 3. Проверка файлов
ls .env config.ini  # Должны существовать

# 4. Тест конфигурации
python -c "from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           print('✅ Config OK')"

# 5. Тест Bitrix24 подключения
python -c "from src.bitrix24_client.client import Bitrix24Client; \
           from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           client = Bitrix24Client(config.get_webhook_url()); \
           print('✅ Bitrix24 OK' if client.call('profile') else '❌ Error')"
```

---

## 🐍 Проблемы с Python и зависимостями

### ❌ "python: command not found"

**Симптомы**:
```bash
$ python --version
bash: python: command not found
```

**Причина**: Python не установлен или не в PATH

**Решение**:

**Windows**:
1. Скачайте [Python](https://www.python.org/downloads/)
2. Установите с флагом "Add to PATH"
3. Перезапустите терминал

**macOS**:
```bash
# Используйте python3
python3 --version

# Или создайте alias
echo 'alias python=python3' >> ~/.zshrc
source ~/.zshrc
```

**Linux**:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

### ❌ "ModuleNotFoundError: No module named 'openpyxl'"

**Симптомы**:
```python
ModuleNotFoundError: No module named 'openpyxl'
ModuleNotFoundError: No module named 'requests'
```

**Причина**: Зависимости не установлены или venv не активирован

**Решение**:

```bash
# 1. Убедитесь что venv активирован
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# 2. Проверьте активацию (должен быть путь к .venv)
which python  # Linux/Mac
where python  # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Проверьте установку
pip list
```

**Если не помогло**:

```bash
# Пересоздайте venv
deactivate
rm -rf .venv  # Linux/Mac
rmdir /s .venv  # Windows

python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt --force-reinstall
```

---

### ❌ "pip: command not found"

**Симптомы**:
```bash
$ pip install requirements.txt
bash: pip: command not found
```

**Решение**:

**Linux**:
```bash
sudo apt install python3-pip
```

**macOS**:
```bash
python3 -m ensurepip --upgrade
```

**Windows**: Переустановите Python с pip

---

## 🔒 Проблемы с конфигурацией

### ❌ "Webhook URL not found"

**Симптомы**:
```
ValueError: Webhook URL not found in configuration
KeyError: 'BITRIX_WEBHOOK_URL'
```

**Причина**: Отсутствует webhook URL в `.env`

**Решение**:

```bash
# 1. Проверьте .env файл
cat .env  # Linux/Mac
type .env  # Windows

# 2. Создайте .env если отсутствует
copy .env-example .env  # Windows
cp .env-example .env    # Linux/Mac

# 3. Добавьте webhook URL
# Отредактируйте .env:
BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/12/abc123/

# 4. Проверьте формат
# ✅ Правильно:
BITRIX_WEBHOOK_URL=https://portal.bitrix24.ru/rest/12/abc123/

# ❌ Неправильно:
BITRIX_WEBHOOK_URL=portal.bitrix24.ru  # Нет https://
BITRIX_WEBHOOK_URL="https://..."  # Лишние кавычки
```

---

### ❌ "FileNotFoundError: config.ini"

**Симптомы**:
```python
FileNotFoundError: [Errno 2] No such file or directory: 'config.ini'
```

**Решение**:

```bash
# Создайте config.ini из примера
copy config.ini.example config.ini  # Windows
cp config.ini.example config.ini    # Linux/Mac

# Проверьте создание
ls config.ini  # Linux/Mac
dir config.ini  # Windows
```

---

### ❌ "Invalid config.ini format"

**Симптомы**:
```python
configparser.ParsingError: File contains parsing errors
```

**Причина**: Синтаксическая ошибка в config.ini

**Решение**:

```bash
# 1. Проверьте синтаксис
cat config.ini

# 2. Типичные ошибки:
# ❌ Неправильно:
[AppSettings
defaultsavefolder = reports

# ✅ Правильно:
[AppSettings]
defaultsavefolder = reports

# 3. Пересоздайте из примера
copy config.ini.example config.ini  # Windows
cp config.ini.example config.ini    # Linux/Mac
```

---

## 🌐 Проблемы с Bitrix24 API

### ❌ "Bitrix24 API Error: 401 Unauthorized"

**Симптомы**:
```
requests.exceptions.HTTPError: 401 Client Error: Unauthorized
Bitrix24APIError: Authentication failed
```

**Причина**: Неверный или просроченный webhook

**Решение**:

```bash
# 1. Тест webhook вручную
curl "https://your-portal.bitrix24.ru/rest/12/abc123/profile"

# 2. Если ошибка - пересоздайте webhook:
# - Bitrix24 → Приложения → Вебхуки
# - Удалите старый webhook
# - Создайте новый с правами: crm, smart_invoice
# - Обновите .env

# 3. Проверьте формат URL
# ✅ Правильно:
https://portal.bitrix24.ru/rest/12/abc123def456/

# ❌ Неправильно:
https://portal.bitrix24.ru/rest/12/abc123def456  # Нет слэша в конце
portal.bitrix24.ru/rest/12/abc123/  # Нет https://
```

---

### ❌ "Bitrix24 API Error: 403 Forbidden"

**Симптомы**:
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden
Bitrix24APIError: Access denied
```

**Причина**: Недостаточно прав у webhook

**Решение**:

1. **Bitrix24** → **Приложения** → **Вебхуки**
2. Откройте ваш webhook
3. Убедитесь, что выбраны права:
   - ✅ `crm` - Доступ к CRM
   - ✅ `smart_invoice` - Доступ к умным счетам
4. Сохраните изменения

---

### ❌ "Bitrix24 API Error: 429 Too Many Requests"

**Симптомы**:
```
requests.exceptions.HTTPError: 429 Client Error: Too Many Requests
Bitrix24APIError: Rate limit exceeded
```

**Причина**: Превышен лимит запросов API (обычно 2 req/sec)

**Решение**:

```ini
# config.ini
[Performance]
# Уменьшите количество одновременных запросов
max_concurrent_requests = 1

# Увеличьте задержку между запросами
request_delay = 0.6  # 0.5 сек = 2 req/sec max
```

**Или подождите 1 минуту** и повторите

---

### ❌ "Connection timeout" / "Network error"

**Симптомы**:
```
requests.exceptions.Timeout: HTTPSConnectionPool(...): Read timed out
requests.exceptions.ConnectionError: Connection aborted
```

**Причина**: Проблемы с интернет-соединением или Bitrix24 недоступен

**Решение**:

```bash
# 1. Проверьте интернет
ping google.com

# 2. Проверьте доступность Bitrix24
ping your-portal.bitrix24.ru

# 3. Увеличьте timeout в config.ini
```

```ini
[Performance]
api_timeout = 60  # Увеличьте до 60 секунд
```

```bash
# 4. Проверьте firewall/антивирус
# Разрешите Python доступ к сети
```

---

## 📊 Проблемы с отчетами

### ❌ "No invoices found for period"

**Симптомы**:
```
INFO: No invoices found for period 01.01.2024 - 31.03.2024
WARNING: Report will be empty
```

**Причина**: Нет счетов за указанный период в Bitrix24

**Решение**:

```bash
# 1. Проверьте период в config.ini
[ReportPeriod]
startdate = 01.01.2024  # Проверьте даты
enddate = 31.03.2024

# 2. Проверьте в Bitrix24
# CRM → Умные счета → Фильтр по дате

# 3. Тест API напрямую
python -c "from src.bitrix24_client.client import Bitrix24Client; \
           from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           client = Bitrix24Client(config.get_webhook_url()); \
           invoices = client.get_invoices_by_period('01.01.2024', '31.03.2024'); \
           print(f'Found {len(invoices)} invoices')"
```

---

### ❌ Отчет создается, но пустой/поврежден

**Симптомы**:
- Excel файл создан, но не открывается
- Файл пустой (0 байт)
- "Файл поврежден" при открытии

**Причина**: Ошибка при генерации Excel или недостаточно прав

**Решение**:

```bash
# 1. Проверьте логи
cat logs/app.log  # Linux/Mac
type logs\app.log  # Windows

# 2. Проверьте права на запись
# Linux/Mac
ls -la reports/
chmod 755 reports  # Исправьте права

# Windows: Запустите от администратора или проверьте права папки

# 3. Проверьте антивирус
# Добавьте ReportB24 в исключения

# 4. Тест генерации
python -c "from openpyxl import Workbook; \
           wb = Workbook(); \
           wb.save('test.xlsx'); \
           print('✅ Excel generation OK')"
```

---

### ❌ В детальном отчете нет товаров

**Симптомы**:
- Лист "Полный" создан, но пустой
- Только заголовки, нет данных

**Причина**: Нет товаров у счетов или недостаточно прав API

**Решение**:

```bash
# 1. Проверьте права webhook
# Bitrix24 → Вебхуки → Убедитесь что есть: smart_invoice

# 2. Тест получения товаров
python -c "from src.bitrix24_client.client import Bitrix24Client; \
           from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           client = Bitrix24Client(config.get_webhook_url()); \
           products = client.get_products_by_invoice('INVOICE_ID'); \
           print(f'Found {len(products)} products')"

# 3. Проверьте в Bitrix24
# Откройте счет → Убедитесь, что есть товары
```

---

## ⚡ Проблемы с производительностью

### ❌ Отчет генерируется очень медленно

**Симптомы**:
- Генерация > 30 минут для 100 счетов
- Зависание при "Processing invoices..."

**Решение**:

```ini
# 1. Оптимизируйте config.ini
[Performance]
batch_size = 50  # Увеличьте batch
max_concurrent_requests = 3  # Больше параллельных запросов
company_cache_size = 2000  # Увеличьте кэш
use_multiprocessing = true  # Включите multiprocessing
max_workers = 4  # CPU cores
```

```bash
# 2. Разбейте на меньшие периоды
# Вместо целого года - по кварталам

# 3. Проверьте интернет-соединение
speedtest-cli  # Установите: pip install speedtest-cli

# 4. Проверьте нагрузку системы
# Windows: Task Manager → Performance
# Linux/Mac: top или htop
```

---

### ❌ "MemoryError" при генерации

**Симптомы**:
```python
MemoryError: Unable to allocate array
```

**Причина**: Недостаточно RAM для большого отчета

**Решение**:

```bash
# 1. Закройте другие приложения

# 2. Разбейте отчет на части
# Генерируйте помесячно вместо годового

# 3. Уменьшите batch size
```

```ini
[Performance]
batch_size = 25  # Уменьшите
max_concurrent_requests = 1
```

```bash
# 4. Увеличьте swap (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🪟 Windows-специфичные проблемы

### ❌ "Access is denied" при активации venv

**Решение**:

```powershell
# Запустите PowerShell от администратора
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Затем активируйте venv
.venv\Scripts\activate
```

---

### ❌ Кириллица в путях вызывает ошибки

**Симптомы**:
```
UnicodeDecodeError: 'charmap' codec can't decode byte
```

**Решение**:

```bash
# Используйте пути без кириллицы
# ❌ Неправильно:
C:\Пользователи\Иван\Проекты\ReportB24

# ✅ Правильно:
C:\Projects\ReportB24

# Или переместите проект:
move C:\Пользователи\Иван\Проекты\ReportB24 C:\Projects\ReportB24
```

---

## 🐧 Linux/Mac-специфичные проблемы

### ❌ "Permission denied" при выполнении скриптов

**Решение**:

```bash
# Дайте права на выполнение
chmod +x scripts/run_report.py
chmod +x scripts/run_report.py

# Или запускайте через python
python scripts/run_report.py
```

---

### ❌ "SSL: CERTIFICATE_VERIFY_FAILED"

**Симптомы**:
```python
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Решение**:

```bash
# macOS
/Applications/Python\ 3.11/Install\ Certificates.command

# Linux
sudo apt install ca-certificates
sudo update-ca-certificates
```

---

## 🔍 Дополнительная диагностика

### Включение DEBUG логов

```ini
# config.ini
[AppSettings]
loglevel = DEBUG  # Максимальная детализация
```

```bash
# Запустите и проверьте логи
python scripts/run_report.py
cat logs/app.log | tail -50
```

---

### Сбор информации для Issue

Если проблема не решена, соберите информацию для [создания Issue](https://github.com/bivlked/ReportB24/issues/new):

```bash
# Версия Python
python --version

# ОС
uname -a  # Linux/Mac
systeminfo | findstr /B /C:"OS"  # Windows

# Версия ReportB24
git describe --tags  # Если установлен через Git

# Установленные пакеты
pip list

# Логи (УДАЛИТЕ СЕКРЕТЫ!)
cat logs/app.log | tail -100

# Config (УДАЛИТЕ WEBHOOK URL!)
cat config.ini
```

---

## 📚 Дополнительная помощь

**Не нашли решение?**

1. 📖 [FAQ](faq.md) - Частые вопросы
2. 💬 [GitHub Discussions](https://github.com/bivlked/ReportB24/discussions)
3. 🐛 [Create Issue](https://github.com/bivlked/ReportB24/issues/new)

---

<div align="center">

[← FAQ](faq.md) • [User Guide](usage-guide.md)

**Помог этот гид?** ⭐ [Star проект](https://github.com/bivlked/ReportB24) на GitHub!

</div>
