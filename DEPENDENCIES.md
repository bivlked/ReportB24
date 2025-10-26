# 📦 Управление зависимостями ReportB24

## 📋 Содержание
- [Структура файлов зависимостей](#структура-файлов-зависимостей)
- [Быстрый старт](#быстрый-старт)
- [Встроенные модули Python](#встроенные-модули-python)
- [Стратегия версионирования](#стратегия-версионирования)
- [Проверка актуальности](#проверка-актуальности)
- [Обновление зависимостей](#обновление-зависимостей)
- [Pre-commit hooks](#pre-commit-hooks)
- [CI/CD интеграция](#cicd-интеграция)

---

## Структура файлов зависимостей

### 📄 requirements.txt
**Назначение:** Production зависимости - минимальный набор для работы приложения

```
requests  - HTTP клиент для Bitrix24 API
openpyxl  - Генерация Excel отчетов
```

**Установка:**
```bash
pip install -r requirements.txt
```

### 🛠️ requirements-dev.txt
**Назначение:** Development tools - инструменты разработки и контроля качества

```
black       - Автоматическое форматирование кода
flake8      - PEP 8 проверка и поиск ошибок
mypy        - Статическая проверка типов
pip-tools   - Управление зависимостями
pre-commit  - Git hooks для автоматических проверок
```

**Установка:**
```bash
pip install -r requirements-dev.txt
```

### 🧪 requirements-test.txt
**Назначение:** Testing tools - фреймворки для тестирования

```
pytest          - Основной фреймворк тестирования
pytest-cov      - Измерение покрытия кода
pytest-qt       - Тестирование Qt приложений
pytest-xdist    - Параллельное выполнение тестов
responses       - Мокирование HTTP запросов
freezegun       - Мокирование времени
```

**Установка:**
```bash
pip install -r requirements-test.txt
```

---

## Быстрый старт

### Для пользователей (production)
```bash
# 1. Создать виртуальное окружение
python -m venv venv

# 2. Активировать (Windows)
venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt
```

### Для разработчиков
```bash
# 1. Создать виртуальное окружение
python -m venv venv

# 2. Активировать (Windows)
venv\Scripts\activate

# 3. Установить все зависимости для разработки
pip install -r requirements-dev.txt -r requirements-test.txt

# 4. Установить pre-commit hooks
pre-commit install
```

---

## Встроенные модули Python

Следующие модули встроены в Python 3.12+ и **НЕ требуют установки**:

| Модуль | Назначение |
|--------|-----------|
| `datetime` | Обработка дат и времени |
| `configparser` | Чтение .ini конфигурации |
| `logging` | Логирование |
| `logging.handlers` | Ротация логов (TimedRotatingFileHandler) |
| `pathlib` | Работа с путями файловой системы |
| `dataclasses` | Структуры данных (@dataclass) |
| `decimal` | Точная арифметика для финансовых расчетов |
| `typing` | Аннотации типов (Type Hints) |
| `json` | Работа с JSON |
| `re` | Регулярные выражения |
| `enum` | Перечисления (Enum) |
| `abc` | Абстрактные базовые классы |
| `collections` | Расширенные коллекции |

---

## Стратегия версионирования

### Production зависимости (requirements.txt)
**Стратегия:** Фиксированные версии с минорной гибкостью

```
requests==2.32.4    # Точная версия (критично для production)
openpyxl==3.1.5     # Точная версия (стабильная работа Excel)
```

**Обоснование:**
- ✅ Предсказуемость - одинаковая среда везде
- ✅ Безопасность - контроль над обновлениями
- ✅ Стабильность - проверенные версии

### Development зависимости (requirements-dev.txt)
**Стратегия:** Минимальная версия с гибкостью вверх

```
black>=25.0.0       # Последние фичи форматирования
flake8>=7.1.0       # Актуальные правила PEP 8
mypy>=1.13.0        # Новые возможности проверки типов
```

**Обоснование:**
- ✅ Актуальность - последние инструменты
- ✅ Совместимость - semantic versioning
- ✅ Прогресс - доступ к новым фичам

### Testing зависимости (requirements-test.txt)
**Стратегия:** Минимальная версия с гибкостью вверх

```
pytest>=8.4.1       # Последние возможности тестирования
pytest-cov>=6.0.0   # Актуальные метрики покрытия
```

---

## Проверка актуальности

### 1. Через Context7 (рекомендуется)
**Для проверки breaking changes и актуальности API:**

```python
# Используя MCP Context7 в Cursor
# 1. Resolve library ID
context7_resolve_library_id("requests python")
context7_resolve_library_id("openpyxl python")

# 2. Get documentation для последней версии
context7_get_library_docs("/psf/requests", "latest version breaking changes")
context7_get_library_docs("/websites/openpyxl_readthedocs_io-en-stable", "latest version")
```

### 2. Через pip (базовая проверка)
```bash
# Показать устаревшие пакеты
pip list --outdated

# Показать информацию о пакете
pip show requests
pip show openpyxl

# Показать доступные версии
pip index versions requests
```

### 3. Через pip-tools
```bash
# Проверить зависимости на конфликты
pip-compile --dry-run requirements.txt

# Проверить security vulnerabilities
pip-audit
```

---

## Обновление зависимостей

### ⚠️ Процесс обновления (важно!)

#### Шаг 1: Backup
```bash
# Создать backup текущих зависимостей
pip freeze > requirements-backup.txt
git add requirements-backup.txt
git commit -m "chore: backup dependencies before update"
```

#### Шаг 2: Проверка через Context7
```
1. Найти library ID через resolve_library_id
2. Получить документацию через get_library_docs
3. Прочитать CHANGELOG и breaking changes
4. Проверить совместимость с текущим кодом
```

#### Шаг 3: Тестовое обновление
```bash
# Создать отдельную ветку
git checkout -b update-dependencies

# Обновить версии в requirements.txt
# Например: requests==2.32.5 (если вышла новая версия)

# Установить обновленные зависимости
pip install -r requirements.txt --upgrade

# Запустить все тесты
pytest --cov

# Проверить работу приложения
python scripts/run_report.py
```

#### Шаг 4: Миграция кода (если нужно)
```python
# Пример: Если API изменилось
# БЫЛО:
response = requests.get(url, params=params)

# СТАЛО:
response = requests.get(url, params=params, timeout=30)  # Новый обязательный параметр
```

#### Шаг 5: Документирование
```bash
# Обновить CHANGELOG.md
# Указать что изменилось и зачем

# Обновить DEPENDENCIES.md
# Указать новые версии и причины обновления

# Коммит
git add requirements.txt CHANGELOG.md DEPENDENCIES.md
git commit -m "chore(deps): update requests to 2.32.5

BREAKING CHANGES:
- None

FEATURES:
- Improved performance for large responses
- Better error messages

MIGRATION:
- No code changes required
"
```

#### Шаг 6: CI/CD проверка
```bash
# Запустить GitHub Actions локально (если есть act)
act

# Или запушить и проверить на GitHub
git push origin update-dependencies
```

### 📊 Проверки перед обновлением

✅ **Checklist:**
- [ ] Прочитан CHANGELOG пакета
- [ ] Проверены breaking changes через Context7
- [ ] Все тесты проходят
- [ ] Приложение работает корректно
- [ ] Обновлена документация
- [ ] Создан Pull Request
- [ ] CI/CD проверки прошли успешно

---

## Pre-commit hooks

### Установка
```bash
pre-commit install
```

### Конфигурация (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 25.0.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/PyCQA/flake8
    rev: 7.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Запуск вручную
```bash
# Проверить все файлы
pre-commit run --all-files

# Проверить конкретный файл
pre-commit run --files src/core/app.py
```

---

## CI/CD интеграция

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.12
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
```

---

## 🔄 Версии зависимостей (текущие)

**Дата проверки:** 2025-10-26  
**Python версия:** 3.12+

### Production
| Пакет | Текущая версия | Последняя стабильная | Статус |
|-------|---------------|---------------------|--------|
| requests | 2.32.4 | 2.32.4 | ✅ Актуально |
| openpyxl | 3.1.5 | 3.1.5 | ✅ Актуально |

### Development
| Пакет | Минимальная версия | Статус |
|-------|-------------------|--------|
| black | 25.0.0 | ✅ Актуально |
| flake8 | 7.1.0 | ✅ Актуально |
| mypy | 1.13.0 | ✅ Актуально |
| pre-commit | 4.0.0 | ✅ Актуально |

### Testing
| Пакет | Минимальная версия | Статус |
|-------|-------------------|--------|
| pytest | 8.4.1 | ✅ Актуально |
| pytest-cov | 6.0.0 | ✅ Актуально |
| pytest-qt | 4.4.0 | ✅ Актуально |

---

## 🚨 Частые проблемы и решения

### Проблема: Конфликт версий
```bash
# Решение: Проверить дерево зависимостей
pip-compile --dry-run requirements.txt

# Решение 2: Пересоздать окружение
deactivate
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Проблема: Сломанные тесты после обновления
```bash
# Решение: Откатиться к backup
pip install -r requirements-backup.txt
pytest

# Затем изучить breaking changes через Context7
```

### Проблема: Медленная установка
```bash
# Решение: Использовать pip cache
pip install -r requirements.txt --cache-dir=.pip-cache

# Решение 2: Использовать --no-deps если уверены
pip install --no-deps -r requirements.txt
```

---

## 📚 Дополнительные ресурсы

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [pip-tools Documentation](https://pip-tools.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Dependency Management](https://python-poetry.org/docs/dependency-specification/)

---

**Версия документа:** v2.4.0  
**Дата последнего обновления:** 2025-10-26  
**Автор:** ReportB24 Development Team
