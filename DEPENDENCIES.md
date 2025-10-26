# 📦 Управление зависимостями

## Структура файлов зависимостей

### `requirements.txt` - Production
Минимальные зависимости для работы приложения в production:
```bash
pip install -r requirements.txt
```

**Содержит:**
- `requests` - HTTP клиент для Bitrix24 API
- `openpyxl` - Excel генерация и форматирование

### `requirements-dev.txt` - Development
Все зависимости для разработки (включая тестирование, линтинг, форматирование):
```bash
pip install -r requirements-dev.txt
```

**Содержит:**
- Все production зависимости
- `pytest`, `pytest-cov`, `pytest-qt` - тестирование
- `black` - форматирование кода
- `flake8`, `mypy` - линтинг и проверка типов
- `radon`, `vulture` - анализ кода
- `pre-commit` - git hooks
- `pip-tools` - управление зависимостями
- `python-dotenv` - поддержка .env файлов

### `requirements-test.txt` - Testing (CI/CD)
Минимальные зависимости для запуска тестов в CI/CD окружении:
```bash
pip install -r requirements-test.txt
```

### `requirements-lock.txt` - Frozen versions
Полный список всех установленных пакетов с точными версиями для reproducibility:
```bash
pip install -r requirements-lock.txt
```

Генерируется командой: `pip freeze > requirements-lock.txt`

---

## Быстрый старт

### 1. Production окружение
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Development окружение
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt
```

### 3. Обновление зависимостей
```bash
# Обновить все зависимости до последних compatible версий
pip install --upgrade -r requirements-dev.txt

# Заморозить новые версии
pip freeze > requirements-lock.txt
```

---

## Встроенные модули Python 3.12+

Следующие модули **не требуют** установки:
- `datetime` - обработка дат и времени
- `configparser` - чтение конфигурационных файлов
- `logging` - логирование
- `pathlib` - работа с путями файловой системы
- `dataclasses` - структуры данных
- `decimal` - точная арифметика
- `typing` - аннотации типов

---

## Проверка актуальности зависимостей

### Context7 (рекомендуется)
Использовать MCP инструмент Context7 для проверки:
- Актуальных версий пакетов
- Breaking changes в новых релизах
- Совместимости с Python 3.12+

### pip-audit (безопасность)
```bash
pip install pip-audit
pip-audit
```

### pip list --outdated
```bash
pip list --outdated
```

---

## Версионирование

Проект использует **semantic versioning** для зависимостей:

- `==X.Y.Z` - точная версия (production)
- `>=X.Y.Z,<(X+1).0.0` - major version constraint (development)

**Примеры:**
- `requests==2.32.4` - только эта версия
- `pytest>=8.4.1,<9.0.0` - версия 8.x.x, но не 9.0.0

---

## Pre-commit hooks

Установка pre-commit hooks для автоматических проверок:

```bash
pip install pre-commit
pre-commit install
```

Проверки выполняются автоматически перед каждым коммитом:
- Форматирование с black
- Линтинг с flake8
- Проверка типов с mypy

---

## CI/CD интеграция

В CI/CD pipeline используйте:

```yaml
# .github/workflows/tests.yml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements-test.txt
```

---

**Последнее обновление:** 2025-10-26  
**Версия проекта:** v2.4.0
