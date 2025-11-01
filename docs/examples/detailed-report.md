# 📋 Детальный отчёт с товарами

Углублённое руководство по работе с детальным листом отчёта, который содержит полную разбивку по товарам каждого счёта.

---

## 🎯 Когда использовать

Детальный лист полезен, когда нужно:

- ✅ Анализировать **продажи конкретных товаров**
- ✅ Отслеживать **количество и цены** товаров
- ✅ Сравнивать **структуру счетов** разных компаний
- ✅ Проводить **инвентаризацию** и контроль остатков
- ✅ Готовить данные для **бухгалтерского учёта**

---

## 📊 Структура детального листа

### Колонки отчёта

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| **Счёт** | `str` | Номер счёта | СЧ-00123 |
| **Компания** | `str` | Название компании | ООО "Ромашка" |
| **ИНН** | `str` | ИНН компании | 7707123456 |
| **Товар/Услуга** | `str` | Название товара | Консультация юриста |
| **Единица** | `str` | Единица измерения | шт, кг, час |
| **Количество** | `float` | Количество | 5.00 |
| **Цена** | `float` | Цена за единицу (₽) | 1 500.00 |
| **Сумма** | `float` | Итого (₽) | 7 500.00 |

### Форматирование данных

**Числовые значения**:
- Разделители тысяч: `125 000.50`
- Два знака после запятой
- Выравнивание по правому краю

**Текстовые значения**:
- Автоматическая ширина колонок
- Обрезка длинных названий (if needed)
- UTF-8 кодировка (кириллица поддерживается)

**Группировка**:
- 🎨 **Зебра-группировка** по счетам
- Чередующиеся цвета фона (белый/светло-серый)
- Визуальное разделение счетов

---

## 💻 Примеры использования

### Пример 1: Стандартная генерация

```python
from src.core.app import AppFactory

# Генерируем отчёт с детальными данными
with AppFactory.create_app() as app:
    result = app.generate_report(
        output_path="reports/detailed.xlsx",
        return_metrics=True
    )
    
    # Анализируем детальный лист
    print(f"Товарных позиций: {result.quality_metrics.detailed_valid}")
    print(f"Проблем: {result.quality_metrics.total_issues}")
```

### Пример 2: Анализ данных детального листа

```python
import openpyxl
from pathlib import Path

# Читаем созданный отчёт
wb = openpyxl.load_workbook("reports/detailed.xlsx")
sheet = wb["Полный"]

# Анализируем товары
products_analysis = {}
for row in sheet.iter_rows(min_row=2, values_only=True):
    account, company, inn, product, unit, quantity, price, total = row
    
    if product not in products_analysis:
        products_analysis[product] = {
            "total_quantity": 0,
            "total_amount": 0,
            "count": 0
        }
    
    products_analysis[product]["total_quantity"] += quantity
    products_analysis[product]["total_amount"] += total
    products_analysis[product]["count"] += 1

# Топ-5 товаров по выручке
top_products = sorted(
    products_analysis.items(),
    key=lambda x: x[1]["total_amount"],
    reverse=True
)[:5]

print("\n🏆 ТОП-5 товаров по выручке:")
for product, data in top_products:
    print(f"  {product}: {data['total_amount']:,.2f} ₽")
```

### Пример 3: Экспорт в DataFrame

```python
import pandas as pd

# Загружаем детальный лист в pandas
df = pd.read_excel(
    "reports/detailed.xlsx",
    sheet_name="Полный",
    engine="openpyxl"
)

# Анализ по компаниям
company_stats = df.groupby("Компания").agg({
    "Сумма": "sum",
    "Товар/Услуга": "count"
}).rename(columns={"Товар/Услуга": "Позиций"})

print("\n📊 Статистика по компаниям:")
print(company_stats.sort_values("Сумма", ascending=False))

# Анализ по товарам
product_stats = df.groupby("Товар/Услуга").agg({
    "Количество": "sum",
    "Сумма": "sum"
})

print("\n📦 Статистика по товарам:")
print(product_stats.sort_values("Сумма", ascending=False).head(10))
```

---

## 🔍 Работа с DataProcessor

### Форматирование товаров для Excel

```python
from src.data_processor.data_processor import DataProcessor
from src.bitrix24_client.client import Bitrix24Client
from src.config.config_reader import ConfigReader

# Инициализация
config = ConfigReader("config.ini")
client = Bitrix24Client(config.get_webhook_url())
processor = DataProcessor()
processor.set_bitrix_client(client)

# Получаем товары для счёта
invoice_id = 12345
products_result = client.get_products_by_invoice(invoice_id)

if not products_result["has_error"]:
    products = products_result["products"]
    
    # Информация о счёте
    invoice_info = {
        "account_number": "СЧ-00123",
        "company_name": "ООО \"Ромашка\"",
        "inn": "7707123456",
        "invoice_id": invoice_id
    }
    
    # Форматируем для Excel
    formatted_products = processor.format_detailed_products_for_excel(
        products, invoice_info
    )
    
    print(f"Отформатировано {len(formatted_products)} товаров")
    
    # Пример первого товара
    if formatted_products:
        first = formatted_products[0]
        print(f"\nПример товара:")
        print(f"  Название: {first['product_name']}")
        print(f"  Количество: {first['formatted_quantity']}")
        print(f"  Цена: {first['formatted_price']}")
        print(f"  Сумма: {first['formatted_total']}")
```

---

## 🎨 Кастомизация форматирования

### Изменение стиля зебра-группировки

Если хотите изменить цвета зебра-группировки:

```python
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# Загружаем отчёт
wb = load_workbook("reports/detailed.xlsx")
sheet = wb["Полный"]

# Определяем свои цвета
CUSTOM_COLOR_1 = "E3F2FD"  # Светло-голубой
CUSTOM_COLOR_2 = "FFFFFF"  # Белый

# Применяем свои цвета
current_account = None
color_index = 0

for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
    account_cell = row[0]
    
    # Меняем цвет при смене счёта
    if account_cell.value != current_account:
        current_account = account_cell.value
        color_index = 1 - color_index  # Переключаем 0/1
    
    # Применяем цвет ко всем ячейкам строки
    fill_color = CUSTOM_COLOR_1 if color_index == 0 else CUSTOM_COLOR_2
    for cell in row:
        cell.fill = PatternFill(start_color=fill_color, fill_type="solid")

# Сохраняем
wb.save("reports/detailed_custom.xlsx")
print("✅ Кастомные цвета применены")
```

---

## 📈 Валидация данных

### Проверка качества детальных данных

```python
from src.excel_generator.validation import validate_detailed_data

# Ваши данные
detailed_data = [
    {
        "account_number": "СЧ-00123",
        "company_name": "ООО \"Ромашка\"",
        "inn": "7707123456",
        "product_name": "Консультация",
        "unit": "час",
        "quantity_raw": 5.0,
        "price_raw": 1500.0,
        "formatted_quantity": "5.00",
        "formatted_price": "1 500.00",
        "formatted_total": "7 500.00"
    },
    # ... больше данных
]

# Валидация
metrics = validate_detailed_data(detailed_data)

print(f"✅ Валидных записей: {metrics.valid_count}")
print(f"⚠️ Записей с предупреждениями: {metrics.warning_count}")
print(f"❌ Записей с ошибками: {metrics.error_count}")

# Детали проблем
if metrics.issues:
    print("\n🔍 Обнаруженные проблемы:")
    for issue in metrics.issues[:5]:  # Первые 5
        print(f"  {issue.severity}: {issue.message}")
        print(f"    Контекст: {issue.context}")
```

---

## ⚠️ Частые проблемы

### 1. Некоторые товары отсутствуют

**Причина**: Ошибка загрузки товаров из Bitrix24.

**Решение**:
```python
# Проверяйте has_error при загрузке
products_result = client.get_products_by_invoice(invoice_id)

if products_result["has_error"]:
    print(f"❌ Ошибка: {products_result['error_message']}")
    # Логируйте или обрабатывайте ошибку
else:
    products = products_result["products"]
    # Обрабатывайте товары
```

### 2. Неправильное форматирование чисел

**Причина**: Товары содержат строковые значения вместо чисел.

**Решение**: Используйте `DataProcessor` для корректного форматирования:
```python
# Процессор автоматически конвертирует и форматирует
formatted = processor.format_detailed_products_for_excel(products, invoice_info)

# Все числа будут правильно отформатированы
```

### 3. Зебра-группировка нарушена

**Причина**: Счета не отсортированы.

**Решение**: Система автоматически группирует, но можно отсортировать вручную:
```python
# Сортировка данных перед генерацией
detailed_data_sorted = sorted(
    detailed_data,
    key=lambda x: x["account_number"]
)

# Теперь зебра-группировка будет корректной
```

---

## 📚 Дополнительные материалы

### Документация

- **[DataProcessor API](../technical/api/data-processor.md)** - Обработка данных
- **[ExcelGenerator API](../technical/api/excel-generator.md)** - Генерация Excel
- **[Validation Guide](../technical/api/excel-generator.md#validation)** - Валидация данных

### Примеры

- **[Basic Report](basic-report.md)** - Быстрый старт
- **[Batch Processing](batch-processing.md)** - Большие объёмы данных
- **[Custom Formatting](custom-formatting.md)** - Продвинутая кастомизация

---

[← Назад к примерам](index.md) | [Batch Processing →](batch-processing.md)
