# 🚀 ReportGeneratorApp API Reference

**Модуль**: `src.core.app`  
**Класс**: `ReportGeneratorApp`  
**Фабрика**: `AppFactory`  
**Версия**: v3.0.2

---

## 📖 Обзор

`ReportGeneratorApp` — главное приложение для генерации отчётов Bitrix24. Предоставляет высокоуровневый интерфейс и координирует работу всех компонентов системы.

### Ключевые возможности

- 🎯 **Простой интерфейс** - один метод для генерации отчёта
- 🔧 **Автоматическая инициализация** всех компонентов
- ✅ **Валидация конфигурации** перед запуском
- 🔌 **Тестирование API** подключения
- 📊 **Отчёты об ошибках** для диагностики

---

## ⚡ Быстрый старт

```python
from src.core.app import AppFactory

# Создание приложения (рекомендуемый способ)
with AppFactory.create_app('config.ini') as app:
    # Генерация отчёта
    success = app.generate_report()
    
    if success:
        print("Отчёт успешно создан!")
    else:
        # Получение детального отчёта об ошибках
        error_report = app.get_error_report()
        print(error_report)
```

---

## 🏭 AppFactory

### `create_app(config_path)`

Фабричный метод для создания настроенного приложения.

**Параметры:**
- `config_path` (`str`) - путь к config.ini

**Возвращает**: `ReportGeneratorApp` - настроенное приложение

**Пример:**

```python
# С context manager (рекомендуется)
with AppFactory.create_app('config.ini') as app:
    success = app.generate_report()

# Без context manager
app = AppFactory.create_app('config.ini')
try:
    success = app.generate_report()
finally:
    app.shutdown()
```

---

## 🎯 Основные методы

### `initialize()`

Инициализирует все компоненты приложения.

**Возвращает**: `bool` - успех инициализации

**Пример:**

```python
app = AppFactory.create_app('config.ini')
if app.initialize():
    print("Приложение инициализировано")
```

---

### `generate_report(custom_filename=None)`

Генерирует комплексный отчёт (краткий + детальный листы).

**Параметры:**
- `custom_filename` (`str`, optional) - пользовательское имя файла

**Возвращает**: `bool` - успех операции

**Пример:**

```python
# С автоматическим именем
success = app.generate_report()

# С пользовательским именем
success = app.generate_report(custom_filename="january_2024.xlsx")
```

---

### `validate_configuration()`

Проверяет корректность конфигурации.

**Возвращает**: `bool` - валидность конфигурации

**Пример:**

```python
if app.validate_configuration():
    print("Конфигурация корректна")
    app.generate_report()
else:
    errors = app.get_error_report()
    print(f"Ошибки конфигурации:\n{errors}")
```

---

### `test_api_connection()`

Тестирует подключение к Bitrix24 API.

**Возвращает**: `bool` - успешность подключения

**Пример:**

```python
if app.test_api_connection():
    print("API доступен")
else:
    print("Не удалось подключиться к API")
```

---

### `get_error_report()`

Возвращает детальный отчёт об ошибках.

**Возвращает**: `str` - форматированный отчёт

**Пример:**

```python
if not app.generate_report():
    error_report = app.get_error_report()
    print(error_report)
```

---

### `get_app_info()`

Возвращает информацию о приложении.

**Возвращает**: `Dict[str, Any]` - информация

**Пример:**

```python
info = app.get_app_info()
print(f"Версия: {info['version']}")
print(f"Период: {info['report_period']}")
```

---

## 🔄 Жизненный цикл

```python
# 1. Создание
app = AppFactory.create_app('config.ini')

# 2. Инициализация
app.initialize()

# 3. Валидация
if not app.validate_configuration():
    print("Ошибка конфигурации")
    exit(1)

# 4. Тестирование API
if not app.test_api_connection():
    print("API недоступен")
    exit(1)

# 5. Генерация отчёта
success = app.generate_report()

# 6. Завершение
app.shutdown()
```

---

## 🛡️ Обработка ошибок

```python
from src.core.app import AppFactory

try:
    with AppFactory.create_app('config.ini') as app:
        # Валидация
        if not app.validate_configuration():
            print(app.get_error_report())
            exit(1)
        
        # Тест API
        if not app.test_api_connection():
            print("Ошибка подключения к Bitrix24")
            exit(1)
        
        # Генерация
        if not app.generate_report():
            print(app.get_error_report())
            exit(1)
        
        print("Отчёт создан успешно!")

except Exception as e:
    print(f"Критическая ошибка: {e}")
    exit(1)
```

---

## 📚 См. также

- [WorkflowOrchestrator API](workflow.md) - внутренний процесс
- [ConfigReader API](config-reader.md) - конфигурация
- [Quick Start Guide](../../user/quick-start.md) - руководство

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
