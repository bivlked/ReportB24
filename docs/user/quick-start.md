# 🚀 Quick Start Guide

**Цель**: Создать первый Excel отчет за 5 минут

**Требования**: Python 3.8+, Bitrix24 webhook URL

---

## Шаг 1: Установка (2 минуты)

```bash
# Клонирование
git clone https://github.com/bivlked/ReportB24.git
cd ReportB24

# Виртуальное окружение
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/Mac)
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

**Результат**: ✅ Зависимости установлены

---

## Шаг 2: Настройка (2 минуты)

### 2.1 Создание конфигурации

```bash
# Windows
copy .env-example .env
copy config.ini.example config.ini

# Linux/Mac
cp .env-example .env
cp config.ini.example config.ini
```

### 2.2 Получение Webhook URL

1. Войдите в ваш Bitrix24
2. Перейдите в **Приложения** → **Вебхуки**
3. Создайте **входящий вебхук** с правами:
   - ✅ `crm` - доступ к CRM
   - ✅ `smart_invoice` - доступ к умным счетам
4. Скопируйте URL (формат: `https://ваш-портал.bitrix24.ru/rest/USER_ID/WEBHOOK_CODE/`)

### 2.3 Настройка .env

Отредактируйте `.env`:

```env
# .env
BITRIX24_WEBHOOKURL=https://ваш-портал.bitrix24.ru/rest/12/abc123def456/
```

⚠️ **Важно**: Замените URL на ваш реальный webhook

**Примечание**: Поддерживаются разные форматы имени переменной:
- `BITRIX24_WEBHOOKURL` (рекомендуется)
- `BITRIXAPI_WEBHOOKURL`
- `WEBHOOKURL`

### 2.4 Настройка периода (опционально)

Отредактируйте `config.ini`:

```ini
[ReportPeriod]
startdate = 01.01.2024
enddate = 31.03.2024
```

**Результат**: ✅ Конфигурация готова

---

## Шаг 3: Первый отчет (1 минута)

### Базовый отчет

```bash
python scripts/run_report.py
```

**Результат**: 
- ✅ Excel файл создан в `reports/`
- 📊 Один лист с кратким отчетом

### Детальный отчет с товарами

```bash
python scripts/run_detailed_report.py
```

**Результат**:
- ✅ Excel файл создан в `reports/`
- 📊 Два листа: "Краткий" + "Полный" с детализацией товаров

---

## 🎉 Готово!

Ваш первый отчет создан! Откройте `reports/` для просмотра.

---

## 🔧 Устранение проблем

### Ошибка: "ModuleNotFoundError"

```bash
# Проверьте активацию venv
pip list

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Ошибка: "Bitrix24 API Error"

1. Проверьте webhook URL в `.env`
2. Убедитесь, что webhook активен в Bitrix24
3. Проверьте права доступа webhook (crm, smart_invoice)

### Ошибка: "FileNotFoundError: config.ini"

```bash
# Убедитесь, что config.ini существует
ls config.ini

# Создайте из примера
copy config.ini.example config.ini  # Windows
cp config.ini.example config.ini    # Linux/Mac
```

---

## 📚 Следующие шаги

- 📖 [Полное руководство](usage-guide.md) - Подробное использование
- ⚙️ [Настройка](configuration.md) - Все параметры конфигурации
- ❓ [FAQ](faq.md) - Частые вопросы
- 🔧 [Troubleshooting](troubleshooting.md) - Решение проблем

---

<div align="center">

[← Назад к README](../../README.md) • [Installation Guide →](installation.md)

**Нужна помощь?** [Создайте Issue](https://github.com/bivlked/ReportB24/issues)

</div>
