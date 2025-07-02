# 🔒 Настройка безопасности ReportB24

## 🚀 Быстрая настройка

### 1. Установка pre-commit хуков

```bash
# Установка pre-commit
pip install pre-commit

# Установка хуков
pre-commit install

# Настройка Git хуков
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

### 2. Проверка системы безопасности

```bash
# Тест скрипта проверки
python scripts/security_check.py

# Тест pre-commit хуков
pre-commit run --all-files

# Тест Git хука
.githooks/pre-commit
```

### 3. Первоначальная очистка (при необходимости)

```bash
# Запуск скрипта очистки истории
bash git-history-cleanup.sh
```

## 📋 Checklist первоначальной настройки

### ✅ Обязательно:
- [ ] Создать новый webhook в Bitrix24
- [ ] Обновить config.ini с новым webhook
- [ ] Установить pre-commit хуки
- [ ] Запустить полную проверку безопасности
- [ ] Очистить Git историю (при необходимости)

### ✅ Рекомендуется:
- [ ] Настроить GitHub Actions
- [ ] Создать .secrets.baseline для detect-secrets
- [ ] Обучить команду новым процессам
- [ ] Запланировать регулярные аудиты

## 🔧 Конфигурация

### Pre-commit хуки

Файл `.pre-commit-config.yaml` содержит:
- Базовые проверки файлов
- Форматирование Python кода
- Обнаружение секретов
- Кастомные проверки безопасности

### GitHub Actions

Файл `.github/workflows/security-check.yml` обеспечивает:
- Автоматическую проверку при push/PR
- Еженедельные аудиты безопасности
- Проверку зависимостей на уязвимости
- Генерацию отчетов безопасности

### Git хуки

Файл `.githooks/pre-commit` выполняет:
- Проверку на утечки webhook
- Валидацию файлов Memory Bank
- Строгую проверку критичных паттернов

## 🚨 Реагирование на инциденты

### При обнаружении утечки:

1. **Немедленно**:
   ```bash
   # Проверить масштаб проблемы
   python scripts/security_check.py
   
   # Найти все вхождения
   grep -r "problem_pattern" .
   ```

2. **Исправить**:
   ```bash
   # Заменить на безопасные примеры
   sed -i 's/real_webhook/https:\/\/your-portal.bitrix24.ru\/rest\/***\/***\//g' file.md
   ```

3. **Зафиксировать**:
   ```bash
   git add .
   git commit -m "SECURITY: Устранение утечки секретов"
   ```

4. **Сменить секреты**:
   - Создать новый webhook в Bitrix24
   - Обновить все среды
   - Уведомить команду

## 📚 Правила безопасного кодирования

### ✅ Правильно:
```bash
https://your-portal.bitrix24.ru/rest/***/***/
https://portal.bitrix24.ru/rest/12/***/
BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/USER_ID/TOKEN/
```

### ❌ Неправильно:
```bash
https://realportal.bitrix24.ru/rest/12/realsecret123/
real_webhook_token_here
актуальные данные портала
```

## 🔄 Регулярное обслуживание

### Еженедельно:
- Запуск полной проверки безопасности
- Аудит новых файлов Memory Bank
- Проверка логов GitHub Actions

### Ежемесячно:
- Обновление зависимостей безопасности
- Ротация API токенов (при необходимости)
- Проверка настроек pre-commit

### Ежеквартально:
- Полный security audit репозитория
- Обновление процессов безопасности
- Обучение команды новым угрозам

---

*Документ обновлен: 2025-01-20*  
*Версия: 1.0*  
*Статус: АКТУАЛЕН*