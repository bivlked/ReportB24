# ⚙️ Installation Guide

Подробное руководство по установке ReportB24 на разных платформах.

---

## 📋 Системные требования

### Минимальные требования
- **ОС**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8 или выше
- **RAM**: 512 МБ
- **Диск**: 100 МБ для установки

### Рекомендуемые требования
- **Python**: 3.11+
- **RAM**: 1 ГБ
- **Диск**: 200 МБ (включая место для отчетов)
- **Интернет**: Стабильное соединение для API запросов

---

## 🪟 Windows

### Шаг 1: Установка Python

1. Скачайте Python с [python.org](https://www.python.org/downloads/)
2. Запустите установщик
3. ✅ **Важно**: Отметьте "Add Python to PATH"
4. Выберите "Install Now"

**Проверка установки**:
```cmd
python --version
# Должно показать: Python 3.8.x или выше
```

### Шаг 2: Клонирование репозитория

```cmd
# Создайте директорию проекта
mkdir C:\Projects
cd C:\Projects

# Клонируйте репозиторий
git clone https://github.com/bivlked/ReportB24.git
cd ReportB24
```

**Без Git?**
1. Скачайте [ZIP архив](https://github.com/bivlked/ReportB24/archive/refs/heads/main.zip)
2. Распакуйте в `C:\Projects\ReportB24`

### Шаг 3: Виртуальное окружение

```cmd
# Создание venv
python -m venv .venv

# Активация
.venv\Scripts\activate

# Проверка активации (должен показать путь к .venv)
where python
```

### Шаг 4: Установка зависимостей

```cmd
# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
pip list
```

---

## 🍎 macOS

### Шаг 1: Установка Python

**С Homebrew** (рекомендуется):
```bash
# Установка Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python
brew install python@3.11
```

**Проверка установки**:
```bash
python3 --version
# Должно показать: Python 3.8.x или выше
```

### Шаг 2: Клонирование репозитория

```bash
# Создайте директорию проекта
mkdir -p ~/Projects
cd ~/Projects

# Клонируйте репозиторий
git clone https://github.com/bivlked/ReportB24.git
cd ReportB24
```

### Шаг 3: Виртуальное окружение

```bash
# Создание venv
python3 -m venv .venv

# Активация
source .venv/bin/activate

# Проверка активации
which python
```

### Шаг 4: Установка зависимостей

```bash
# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
pip list
```

---

## 🐧 Linux (Ubuntu/Debian)

### Шаг 1: Установка Python

```bash
# Обновление пакетов
sudo apt update

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv

# Проверка установки
python3 --version
```

### Шаг 2: Клонирование репозитория

```bash
# Создайте директорию проекта
mkdir -p ~/Projects
cd ~/Projects

# Клонируйте репозиторий
git clone https://github.com/bivlked/ReportB24.git
cd ReportB24
```

### Шаг 3: Виртуальное окружение

```bash
# Создание venv
python3 -m venv .venv

# Активация
source .venv/bin/activate

# Проверка активации
which python
```

### Шаг 4: Установка зависимостей

```bash
# Обновление pip
python -m pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Проверка установки
pip list
```

---

## 🐳 Docker (опционально)

**Dockerfile** (создайте в корне проекта):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "scripts/run_report.py"]
```

**Использование**:

```bash
# Сборка образа
docker build -t reportb24 .

# Запуск контейнера
docker run -v $(pwd)/reports:/app/reports reportb24
```

---

## ✅ Проверка установки

### Тест конфигурации

```python
# test_installation.py
from src.config.config_reader import SecureConfigReader

try:
    config = SecureConfigReader('config.ini')
    print("✅ Конфигурация загружена успешно")
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

Запуск:
```bash
python test_installation.py
```

### Запуск тестов

```bash
# Все тесты
pytest

# Быстрые тесты
pytest tests/ -k "not slow"

# С покрытием
pytest --cov=src --cov-report=html
```

---

## 🔧 Устранение проблем

### Windows: "python не является внутренней или внешней командой"

**Решение**: Добавьте Python в PATH:
1. Найдите установочную директорию Python (обычно `C:\Python311\`)
2. Откройте "Система" → "Дополнительные параметры системы"
3. Нажмите "Переменные среды"
4. В "Системные переменные" найдите `Path` и нажмите "Изменить"
5. Добавьте `C:\Python311\` и `C:\Python311\Scripts\`

### macOS: "command not found: python"

**Решение**: Используйте `python3` вместо `python`:
```bash
# Создайте alias (добавьте в ~/.zshrc или ~/.bash_profile)
alias python=python3
alias pip=pip3
```

### Linux: "ModuleNotFoundError: No module named 'pip'"

**Решение**:
```bash
sudo apt install python3-pip
```

### Все платформы: "Permission denied"

**Решение**:
```bash
# Linux/Mac
chmod +x scripts/run_report.py

# Windows: Запустите PowerShell/CMD от администратора
```

---

## 🔄 Обновление

### Обновление из Git

```bash
# Получите последние изменения
git pull origin main

# Обновите зависимости
pip install -r requirements.txt --upgrade
```

### Обновление без Git

1. Скачайте [последнюю версию](https://github.com/bivlked/ReportB24/archive/refs/heads/main.zip)
2. Распакуйте в новую директорию
3. Скопируйте `.env` и `config.ini` из старой версии
4. Установите зависимости: `pip install -r requirements.txt`

---

## 🗑️ Удаление

```bash
# Деактивируйте venv
deactivate

# Удалите директорию проекта
# Windows
rmdir /s ReportB24

# Linux/Mac
rm -rf ReportB24
```

---

## 📚 Следующие шаги

- ⚙️ [Настройка конфигурации](configuration.md)
- 🚀 [Quick Start](quick-start.md)
- 📖 [Руководство пользователя](usage-guide.md)

---

<div align="center">

[← Quick Start](quick-start.md) • [Configuration →](configuration.md)

**Проблемы с установкой?** [Troubleshooting](troubleshooting.md) • [FAQ](faq.md)

</div>
