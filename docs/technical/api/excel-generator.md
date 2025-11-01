# 📊 ExcelReportGenerator API Reference

**Модуль**: `src.excel_generator.generator`  
**Класс**: `ExcelReportGenerator`  
**Версия**: v3.0.2

---

## 📖 Обзор

`ExcelReportGenerator` — компонент для создания профессиональных Excel отчётов с автоматическим форматированием, стилизацией и группировкой данных.

### Ключевые возможности

- 📄 **Dual-sheet отчёты** (краткий + детальный)
- 🎨 **Автоматическая стилизация** (цвета, шрифты, границы)
- 📏 **Авто-ширина колонок** по содержимому
- 🦓 **Зебра-группировка** товаров
- ✅ **Валидация качества** данных

---

## ⚡ Быстрый старт

```python
from src.excel_generator.generator import ExcelReportGenerator

# Инициализация генератора
generator = ExcelReportGenerator()

# Создание comprehensive отчёта
result = generator.generate_comprehensive_report(
    brief_data=brief_invoices,
    detailed_data=detailed_products,
    output_path="reports/report_2024-01.xlsx",
    return_metrics=True,
    verbose=True
)

if result.success:
    print(f"Отчёт создан: {result.output_path}")
    print(f"Качество: {result.quality_metrics.total_issues} проблем")
```

---

## 🎯 Основные методы

### `generate_comprehensive_report(brief_data, detailed_data, output_path, ...)`

Создаёт комплексный отчёт с двумя листами (краткий + детальный).

**Параметры:**
- `brief_data` (`List[Dict]`) - данные для краткого листа
- `detailed_data` (`List[Dict]`) - данные для детального листа
- `output_path` (`str`) - путь сохранения
- `return_metrics` (`bool`) - возвращать метрики качества
- `verbose` (`bool`) - подробный вывод

**Возвращает**: `ReportResult` или `str` (путь к файлу)

**Пример:**

```python
result = generator.generate_comprehensive_report(
    brief_data=invoices,
    detailed_data=products,
    output_path="reports/january_2024.xlsx",
    return_metrics=True,
    verbose=True
)

print(f"Создано строк: {result.rows_created}")
print(f"Валидных записей: {result.quality_metrics.brief_valid}")
```

---

### `create_report(data, output_path)`

Создаёт простой отчёт с одним листом.

**Параметры:**
- `data` (`List[Dict]`) - данные для отчёта
- `output_path` (`str`) - путь сохранения

**Возвращает**: `str` - путь к созданному файлу

**Пример:**

```python
path = generator.create_report(
    data=invoices,
    output_path="reports/simple_report.xlsx"
)
```

---

## 📋 Структура отчётов

### Краткий лист

Колонки:
- Номер счёта
- Контрагент
- ИНН
- Сумма счёта
- Сумма НДС
- Ставка НДС
- Дата счёта
- Дата отгрузки
- Дата оплаты

### Детальный лист

Колонки:
- Номер счёта
- Контрагент
- ИНН
- Наименование товара
- Единица измерения
- Количество
- Цена за единицу
- Сумма без НДС
- Сумма НДС
- Сумма с НДС
- Ставка НДС

---

## 🎨 Стилизация

Автоматическая стилизация включает:
- **Заголовки**: жирный шрифт, цветной фон
- **Данные**: читаемые шрифты, выравнивание
- **Группы**: зебра-эффект (чередование цветов)
- **Границы**: профессиональное оформление
- **Форматы**: числа, даты, валюта

---

## 📚 См. также

- [DataProcessor API](data-processor.md) - подготовка данных
- [WorkflowOrchestrator API](workflow.md) - оркестрация процесса
- [Примеры](../../examples/) - практические примеры

---

**Обновлено**: 2025-11-01  
**Версия API**: v3.0.2
