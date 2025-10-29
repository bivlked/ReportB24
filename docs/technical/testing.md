# 🧪 Testing Guide

Комплексное тестирование ReportB24 - стратегия, практики и примеры.

---

## 📊 Test Coverage

**Текущее состояние**:
```
✅ 530/530 тестов пройдено (100% success rate)
📊 77% покрытие кода (3816/4957 строк)
⚡ Performance: ~7 минут для полного набора
🔒 Security tests включены
```

---

## 🎯 Testing Strategy

### Test Pyramid

```
        /\
       /  \
      / E2E \      ← End-to-End (5%)
     /------\
    /  Integ  \    ← Integration (20%)
   /----------\
  /    Unit    \   ← Unit Tests (75%)
 /--------------\
```

**Распределение**:
- **Unit Tests (75%)**: Тестирование отдельных компонентов
- **Integration Tests (20%)**: Тестирование взаимодействия
- **E2E Tests (5%)**: Тестирование полного workflow

---

## 🔧 Running Tests

### Basic Commands

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src --cov-report=html --cov-report=term

# Конкретный модуль
pytest tests/data_processor/

# Конкретный файл
pytest tests/test_integration_workflow.py

# Конкретный тест
pytest tests/test_integration.py::test_full_report_generation

# Verbose
pytest -v

# С подробными логами
pytest -s

# Остановка на первой ошибке
pytest -x

# Параллельный запуск
pytest -n auto
```

---

## 📝 Writing Tests

### Unit Test Example

```python
# tests/data_processor/test_inn_processor.py
import pytest
from src.data_processor.inn_processor import INNProcessor

class TestINNProcessor:
    """Tests for INN validation"""
    
    @pytest.fixture
    def processor(self):
        return INNProcessor()
    
    def test_validate_inn_10_digits_valid(self, processor):
        """Test valid 10-digit INN"""
        assert processor.validate_inn("7707083893") is True
    
    def test_validate_inn_12_digits_valid(self, processor):
        """Test valid 12-digit INN"""
        assert processor.validate_inn("500100732259") is True
    
    def test_validate_inn_invalid_checksum(self, processor):
        """Test INN with invalid checksum"""
        assert processor.validate_inn("7707083894") is False
    
    @pytest.mark.parametrize("invalid_inn", [
        "",  # Empty
        "123",  # Too short
        "12345678901234",  # Too long
        "abcdefghij",  # Non-numeric
    ])
    def test_validate_inn_invalid_format(self, processor, invalid_inn):
        """Test various invalid INN formats"""
        assert processor.validate_inn(invalid_inn) is False
```

---

### Integration Test Example

```python
# tests/test_integration_workflow.py
import pytest
from src.core.app import create_app
from src.bitrix24_client.client import Bitrix24Client

@pytest.fixture
def app():
    """Create application instance"""
    return create_app('config.ini')

def test_full_report_generation(app, tmp_path):
    """Test complete report generation workflow"""
    # Arrange
    app.initialize()
    output_file = tmp_path / "test_report.xlsx"
    
    # Act
    success = app.generate_report(str(output_file))
    
    # Assert
    assert success is True
    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_report_with_products(app, tmp_path):
    """Test detailed report with products"""
    # Arrange
    app.initialize()
    output_file = tmp_path / "detailed_report.xlsx"
    
    # Act
    from src.excel_generator.generator import ExcelReportGenerator
    generator = ExcelReportGenerator()
    
    invoices = app.bitrix_client.get_invoices_by_period('01.01.2024', '31.01.2024')
    workbook = generator.create_multi_sheet_report(
        invoices, 
        app.bitrix_client, 
        app.data_processor
    )
    workbook.save(str(output_file))
    
    # Assert
    assert output_file.exists()
    # Verify sheets exist
    from openpyxl import load_workbook
    wb = load_workbook(output_file)
    assert "Краткий" in wb.sheetnames
    assert "Полный" in wb.sheetnames
```

---

### Mocking External Dependencies

```python
# tests/bitrix24_client/test_client.py
import pytest
from unittest.mock import Mock, patch
from src.bitrix24_client.client import Bitrix24Client

@pytest.fixture
def mock_requests():
    """Mock requests library"""
    with patch('src.bitrix24_client.client.requests') as mock:
        yield mock

def test_call_api_success(mock_requests):
    """Test successful API call"""
    # Arrange
    client = Bitrix24Client("https://test.bitrix24.ru/rest/12/abc/")
    mock_response = Mock()
    mock_response.json.return_value = {'result': {'id': '123'}}
    mock_response.raise_for_status = Mock()
    mock_requests.post.return_value = mock_response
    
    # Act
    result = client.call('crm.item.list')
    
    # Assert
    assert result == {'result': {'id': '123'}}
    mock_requests.post.assert_called_once()

def test_call_api_rate_limiting(mock_requests):
    """Test that rate limiting is applied"""
    # Arrange
    client = Bitrix24Client("https://test.bitrix24.ru/rest/12/abc/")
    mock_response = Mock()
    mock_response.json.return_value = {'result': []}
    mock_requests.post.return_value = mock_response
    
    # Act
    import time
    start = time.time()
    client.call('method1')
    client.call('method2')
    elapsed = time.time() - start
    
    # Assert: должна быть задержка между вызовами (rate limiting)
    assert elapsed >= 0.5  # ≥0.5 сек для 2 запросов (max 2 req/sec)
```

---

## 🎨 Test Fixtures

### Common Fixtures

```python
# tests/conftest.py
import pytest
from decimal import Decimal
from src.config.config_reader import SecureConfigReader
from src.data_processor.data_processor import DataProcessor

@pytest.fixture
def config():
    """Provide test configuration"""
    return SecureConfigReader('config.ini')

@pytest.fixture
def processor():
    """Provide DataProcessor instance"""
    return DataProcessor()

@pytest.fixture
def sample_invoice():
    """Provide sample invoice data"""
    return {
        'id': '123',
        'title': 'Test Invoice',
        'opportunity': '10000.00',
        'taxValue': '2000.00',
        'company': {
            'id': '456',
            'title': 'Test Company',
            'inn': '7707083893'
        },
        'begindate': '2024-01-15T00:00:00+03:00',
        'closedate': '2024-01-31T00:00:00+03:00'
    }

@pytest.fixture
def sample_products():
    """Provide sample product data"""
    return [
        {
            'id': '1',
            'productName': 'Product 1',
            'price': '1000.00',
            'quantity': '5',
            'measureName': 'шт'
        },
        {
            'id': '2',
            'productName': 'Product 2',
            'price': '2000.00',
            'quantity': '3',
            'measureName': 'шт'
        }
    ]
```

---

## ✅ Test Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_calculate_vat():
    # Arrange: Setup
    processor = DataProcessor()
    amount = Decimal('10000')
    
    # Act: Execute
    vat = processor.calculate_vat(amount, '20%')
    
    # Assert: Verify
    assert vat == Decimal('2000')
```

### 2. Descriptive Test Names

```python
# ❌ Bad: Неясно что тестируется
def test_processor():
    ...

# ✅ Good: Понятная цель теста
def test_process_invoice_with_valid_inn_returns_processed_data():
    ...
```

### 3. One Concept Per Test

```python
# ❌ Bad: Тестирует несколько вещей
def test_processor():
    assert processor.validate_inn('123') is False
    assert processor.calculate_vat(100, '20%') == 20
    assert processor.format_date('2024-01-01') == '01.01.2024'

# ✅ Good: Один концепт
def test_validate_inn_with_invalid_format_returns_false():
    assert processor.validate_inn('123') is False

def test_calculate_vat_20_percent():
    assert processor.calculate_vat(100, '20%') == 20

def test_format_date_iso_to_russian():
    assert processor.format_date('2024-01-01') == '01.01.2024'
```

### 4. Use Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("inn,expected", [
    ("7707083893", True),   # Valid 10-digit
    ("500100732259", True), # Valid 12-digit
    ("7707083894", False),  # Invalid checksum
    ("123", False),         # Too short
    ("", False),            # Empty
])
def test_validate_inn_various_cases(inn, expected):
    processor = INNProcessor()
    assert processor.validate_inn(inn) == expected
```

---

## 🔒 Security Tests

### Test Webhook URL Masking

```python
def test_webhook_url_masked_in_logs(caplog):
    """Test that webhook URLs are masked in logs"""
    import logging
    caplog.set_level(logging.INFO)
    
    client = Bitrix24Client("https://portal.bitrix24.ru/rest/12/secret123/")
    client.call('profile')
    
    # Assert: Logs should contain masked URL
    assert "secret123" not in caplog.text
    assert "***" in caplog.text
```

### Test Configuration Security

```python
def test_env_file_not_committed():
    """Test that .env file is in .gitignore"""
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    assert '.env' in gitignore_content
```

---

## ⚡ Performance Tests

### Test Report Generation Performance

```python
import time
import pytest

@pytest.mark.performance
def test_report_generation_performance():
    """Test that report generation completes within acceptable time"""
    from src.core.app import create_app
    
    app = create_app('config.ini')
    app.initialize()
    
    # Measure time
    start = time.time()
    app.generate_report('performance_test.xlsx')
    elapsed = time.time() - start
    
    # Assert: Should complete within 5 minutes for 100 invoices
    assert elapsed < 300  # 5 minutes

@pytest.mark.performance
def test_product_processing_performance():
    """Test product processing speed"""
    from src.data_processor.data_processor import DataProcessor
    
    processor = DataProcessor()
    
    # Generate 1000 test products
    products = [
        {'id': str(i), 'productName': f'Product {i}', 
         'price': '1000', 'quantity': '1', 'measureName': 'шт'}
        for i in range(1000)
    ]
    
    # Measure time
    start = time.time()
    processed = processor.process_product_data(products)
    elapsed = time.time() - start
    
    # Assert: Should process 1000 products in < 1 second
    assert elapsed < 1.0
    assert len(processed) == 1000
```

---

## 📈 Coverage Analysis

### Generate Coverage Report

```bash
# HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Module

```bash
pytest --cov=src --cov-report=term-missing
```

**Example Output**:
```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/__init__.py                             0      0   100%
src/bitrix24_client/__init__.py             0      0   100%
src/bitrix24_client/client.py             156     15    90%   45-48, 123-126
src/data_processor/data_processor.py      234     12    95%   189-192, 345-348
src/excel_generator/generator.py         198      8    96%   234-237
---------------------------------------------------------------------
TOTAL                                    4957    958    81%
```

---

## 🏃 Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

<div align="center">

[← Development](development.md) • [Performance →](performance.md)

**Questions about testing?** [Create Discussion](https://github.com/bivlked/ReportB24/discussions)

</div>
