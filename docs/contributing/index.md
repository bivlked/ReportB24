# 🤝 Руководство для контрибьюторов

Информация для тех, кто хочет внести вклад в развитие ReportB24.

---

## 📖 Содержание

### 🚀 Начало работы

**[Getting Started](getting-started.md)** - Как начать контрибьютить  
Первые шаги: форк, setup окружения, создание первого Pull Request.

---

### 📝 Стандарты и процессы

**[Coding Standards](coding-standards.md)** - Стандарты кода  
Правила оформления кода, docstrings, type hints, структура модулей.

**[PR Process](pr-process.md)** - Процесс Pull Request  
Как правильно создавать PR, code review, требования к коммитам.

**[Release Process](release-process.md)** - Процесс релизов  
Как создаются релизы, версионирование, changelog, deployment.

---

## 🎯 Типы вклада

### 💻 Код
- Новые функции
- Исправление багов
- Оптимизация производительности
- Рефакторинг

### 📚 Документация
- Улучшение существующей документации
- Добавление примеров
- Переводы
- Туториалы

### 🧪 Тестирование
- Unit тесты
- Integration тесты
- E2E тесты
- Отчеты об ошибках

### 🎨 Дизайн
- UX улучшения
- Визуальные диаграммы
- Документация паттернов

---

## 📋 Требования к контрибьюторам

### Обязательно:
✅ Следовать [Coding Standards](coding-standards.md)  
✅ Писать тесты для нового кода  
✅ Обновлять документацию  
✅ Использовать conventional commits  
✅ Проходить pre-commit hooks  

### Рекомендуется:
⭐ Обсудить большие изменения в Issues  
⭐ Следовать существующим паттернам  
⭐ Добавлять примеры использования  
⭐ Оптимизировать производительность  

---

## 🚀 Быстрый старт для контрибьюторов

### 1. Подготовка
```bash
# Fork репозитория на GitHub
# Клонирование форка
git clone https://github.com/YOUR-USERNAME/ReportB24.git
cd ReportB24

# Создание виртуального окружения
python -m venv .venv
.venv\Scripts\activate  # Windows

# Установка зависимостей для разработки
pip install -r requirements-dev.txt
pip install -r requirements-test.txt

# Установка pre-commit hooks
pre-commit install
```

### 2. Разработка
```bash
# Создание feature branch
git checkout -b feature/your-feature-name

# Разработка + тестирование
# ... coding ...

# Запуск тестов
pytest tests/

# Запуск pre-commit checks
pre-commit run --all-files
```

### 3. Pull Request
```bash
# Commit изменений
git add .
git commit -m "feat: add amazing feature"

# Push в fork
git push origin feature/your-feature-name

# Создание PR на GitHub
```

---

## 📚 Полезные ресурсы

- **[Technical Documentation](../technical/)** - Техническая документация
- **[Architecture](../technical/architecture.md)** - Архитектура системы
- **[API Reference](../technical/api-reference.md)** - API документация
- **[Testing Guide](../technical/testing.md)** - Руководство по тестированию
- **[Examples](../examples/)** - Примеры кода

---

## 💬 Коммуникация

- **[GitHub Issues](https://github.com/bivlked/ReportB24/issues)** - Баги и feature requests
- **[GitHub Discussions](https://github.com/bivlked/ReportB24/discussions)** - Обсуждения
- **[Pull Requests](https://github.com/bivlked/ReportB24/pulls)** - Code review

---

## 🏆 Благодарности

Все контрибьюторы указываются в [CONTRIBUTORS.md](../../CONTRIBUTORS.md).

Спасибо за ваш вклад в развитие ReportB24! 🙏

---

[← Назад к документации](../index.md) • [Getting Started →](getting-started.md)
