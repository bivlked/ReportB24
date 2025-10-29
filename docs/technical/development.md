# 💻 Development Guide

Руководство по разработке и контрибьюции в ReportB24.

---

## 🚀 Development Setup

### Prerequisites

```bash
# Required
- Python 3.8+
- Git
- pip

# Recommended
- Python 3.11+
- VS Code / PyCharm
- Black formatter
- pytest
```

### Initial Setup

```bash
# 1. Fork и клонирование
git clone https://github.com/YOUR_USERNAME/ReportB24.git
cd ReportB24

# 2. Создание feature branch
git checkout -b feature/amazing-feature

# 3. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate  # Windows

# 4. Установка зависимостей
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools
pip install -r requirements-test.txt  # Testing tools

# 5. Настройка pre-commit hooks
pre-commit install
```

### Configuration

```bash
# Create config files
cp .env-example .env
cp config.ini.example config.ini

# Edit .env with your test webhook
BITRIX_WEBHOOK_URL=https://test-portal.bitrix24.ru/rest/12/test123/
```

---

## 🔄 Development Workflow

### Standard Workflow

```bash
# 1. Обновление main
git checkout main
git pull origin main

# 2. Создание feature branch
git checkout -b feature/new-feature

# 3. Разработка
# ... your code changes ...

# 4. Форматирование кода
black src/ tests/

# 5. Запуск тестов
pytest

# 6. Commit
git add .
git commit -m "feat: add new feature"

# 7. Push
git push origin feature/new-feature

# 8. Create Pull Request на GitHub
```

### Commit Message Convention

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: Новая feature
- `fix`: Bug fix
- `docs`: Изменения в документации
- `style`: Форматирование (без изменения логики)
- `refactor`: Рефакторинг кода
- `test`: Добавление/изменение тестов
- `chore`: Maintenance задачи

**Examples**:
```bash
feat(excel): add zebra-effect grouping
fix(api): handle empty product lists
docs(readme): update installation instructions
refactor(processor): simplify data validation
test(client): add rate limiter tests
```

---

## 📁 Project Structure

```
ReportB24/
├── src/                      # Source code
│   ├── bitrix24_client/      # API клиент
│   ├── config/               # Конфигурация
│   ├── core/                 # Ядро приложения
│   ├── data_processor/       # Обработка данных
│   └── excel_generator/      # Генерация Excel
│
├── tests/                    # Тесты
│   ├── bitrix24_client/
│   ├── data_processor/
│   └── test_*.py
│
├── docs/                     # Документация
│   ├── user/                 # Пользовательская
│   └── technical/            # Техническая
│
├── scripts/                  # Утилиты и скрипты
├── reports/                  # Generated reports
└── logs/                     # Log files
```

---

## 🎨 Code Style

### Python Style Guide

**Основа**: [PEP 8](https://pep8.org/) + [Black](https://black.readthedocs.io/)

```bash
# Auto-formatting
black src/ tests/

# Checking
black --check src/ tests/
```

**Key Points**:
- ✅ Line length: 100 characters
- ✅ Imports: `isort` compatible
- ✅ Docstrings: Google style
- ✅ Type hints: Encouraged

**Example**:
```python
from typing import List, Optional
from decimal import Decimal

def process_invoices(
    invoices: List[dict], 
    validate: bool = True
) -> List[dict]:
    """
    Process invoice records.
    
    Args:
        invoices: List of raw invoice dictionaries
        validate: Whether to validate INN (default: True)
    
    Returns:
        List of processed invoice dictionaries
    
    Raises:
        ValueError: If invoice data is invalid
    """
    processed = []
    for invoice in invoices:
        if validate:
            _validate_invoice(invoice)
        processed.append(_process_single(invoice))
    return processed
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/data_processor/

# Specific test
pytest tests/test_integration.py::test_full_workflow

# With coverage
pytest --cov=src --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

### Writing Tests

**Structure**:
```python
# tests/data_processor/test_processor.py
import pytest
from src.data_processor.data_processor import DataProcessor

class TestDataProcessor:
    """Tests for DataProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create processor instance"""
        return DataProcessor()
    
    def test_process_invoice_record_success(self, processor):
        """Test successful invoice processing"""
        # Arrange
        raw_data = {
            'id': '123',
            'title': 'Test Invoice',
            'opportunity': '10000.00'
        }
        
        # Act
        result = processor.process_invoice_record(raw_data)
        
        # Assert
        assert result['id'] == '123'
        assert result['total_amount'] == Decimal('10000.00')
    
    def test_process_invoice_record_invalid_inn(self, processor):
        """Test processing with invalid INN"""
        # Arrange
        raw_data = {'id': '123', 'company': {'inn': 'invalid'}}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid INN"):
            processor.process_invoice_record(raw_data)
```

**Best Practices**:
- ✅ One assertion concept per test
- ✅ Descriptive test names
- ✅ Use fixtures for setup
- ✅ Test edge cases
- ✅ Mock external dependencies

---

## 🔍 Debugging

### Using Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or (Python 3.7+)
breakpoint()
```

### Debugging Tests

```bash
# Run with debugger
pytest --pdb

# Drop to debugger on failure
pytest --pdb -x
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Detailed information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error occurred")
```

**Enable DEBUG logging**:
```ini
# config.ini
[AppSettings]
loglevel = DEBUG
```

---

## 📦 Adding Dependencies

### Process

1. **Add to requirements files**:
```bash
# Runtime dependency
echo "new-package==1.2.3" >> requirements.txt

# Development tool
echo "new-dev-tool==4.5.6" >> requirements-dev.txt

# Testing tool
echo "new-test-lib==7.8.9" >> requirements-test.txt
```

2. **Update lock file**:
```bash
pip freeze > requirements-lock.txt
```

3. **Document why** in commit message

4. **Test** that it works

---

## 🚢 Release Process

### Creating a Release

```bash
# 1. Update version in relevant files
# - src/__init__.py
# - README.md badges

# 2. Update CHANGELOG.md
# Add new version section with changes

# 3. Commit version bump
git add .
git commit -m "chore: bump version to 2.5.0"

# 4. Create tag
git tag -a v2.5.0 -m "Release v2.5.0"

# 5. Push
git push origin main --tags

# 6. Create GitHub Release
# Go to GitHub → Releases → New Release
# - Tag: v2.5.0
# - Title: v2.5.0 - Feature Name
# - Description: Copy from CHANGELOG.md
```

---

## 💡 Development Tips

### Performance Profiling

```python
import cProfile
import pstats

# Profile function
cProfile.run('generate_report()', 'profile_stats')

# Analyze
p = pstats.Stats('profile_stats')
p.sort_stats('cumulative')
p.print_stats(20)  # Top 20
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Run with profiling
python -m memory_profiler scripts/run_report.py
```

### Using IPython

```bash
# Install
pip install ipython

# Interactive shell with better introspection
ipython

# In IPython
from src.core.app import create_app
app = create_app('config.ini')
app.initialize()

# Tab completion, ? for help
app.generate_report?
```

---

## 🐛 Common Issues

### Issue: Import errors

```python
# ❌ Wrong
from data_processor import DataProcessor

# ✅ Correct
from src.data_processor.data_processor import DataProcessor
```

**Solution**: Always use full paths from project root

### Issue: Tests not found

```bash
# Ensure __init__.py exists
touch tests/__init__.py
touch tests/data_processor/__init__.py

# Run from project root
pytest
```

### Issue: Black conflicts with editor

**Solution**: Configure editor to use Black:

**VS Code** (`.vscode/settings.json`):
```json
{
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "editor.formatOnSave": true
}
```

**PyCharm**: Settings → Tools → Black → Enable

---

## 📚 Resources

### Documentation
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)

### Tools
- [Black](https://github.com/psf/black) - Code formatter
- [pytest](https://pytest.org/) - Testing framework
- [mypy](http://mypy-lang.org/) - Static type checker
- [flake8](https://flake8.pycqa.org/) - Linter

---

## 🤝 Getting Help

**Questions?**
1. Check [Architecture](architecture.md)
2. Read [API Reference](api-reference.md)
3. Search [GitHub Issues](https://github.com/bivlked/ReportB24/issues)
4. Ask in [Discussions](https://github.com/bivlked/ReportB24/discussions)

---

<div align="center">

[← Architecture](architecture.md) • [Testing Guide →](testing.md)

**Ready to contribute?** [CONTRIBUTING.md](../../CONTRIBUTING.md)

</div>
