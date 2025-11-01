# 🎨 Кастомное форматирование Excel

Продвинутая кастомизация Excel отчётов для специфических требований бизнеса.

---

## 🎯 Что можно настроить

- ✅ **Цвета и стили** ячеек, заголовков, групп
- ✅ **Шрифты** (размер, жирность, цвет)
- ✅ **Границы** (стиль, толщина, цвет)
- ✅ **Форматы чисел** (валюта, проценты, даты)
- ✅ **Ширина колонок** (фиксированная или авто)
- ✅ **Условное форматирование** (по значениям)
- ✅ **Диаграммы** (графики, charts)

---

## 💻 Базовая кастомизация

### Изменение цветов заголовка

```python
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Кастомные цвета для заголовка
header_fill = PatternFill(
    start_color="1F4E78",  # Тёмно-синий
    end_color="1F4E78",
    fill_type="solid"
)

header_font = Font(
    name="Arial",
    size=12,
    bold=True,
    color="FFFFFF"  # Белый текст
)

# Применяем к первой строке (заголовок)
for cell in sheet[1]:
    cell.fill = header_fill
    cell.font = header_font

wb.save("reports/report_custom_header.xlsx")
print("✅ Заголовок кастомизирован")
```

### Изменение зебра-группировки

```python
from openpyxl.styles import PatternFill

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Полный"]

# Корпоративные цвета
COLOR_LIGHT = "E8F4F8"  # Светло-голубой
COLOR_DARK = "D4E9F2"   # Средне-голубой

current_account = None
color_index = 0

for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
    account_value = row[0].value
    
    # Меняем цвет при смене счёта
    if account_value != current_account:
        current_account = account_value
        color_index = 1 - color_index
    
    # Применяем цвет
    fill_color = COLOR_LIGHT if color_index == 0 else COLOR_DARK
    for cell in row:
        cell.fill = PatternFill(start_color=fill_color, fill_type="solid")

wb.save("reports/report_corporate_colors.xlsx")
print("✅ Корпоративные цвета применены")
```

---

## 🎨 Продвинутые техники

### Условное форматирование по сумме

```python
from openpyxl.formatting.rule import ColorScaleRule

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Находим колонку "Сумма" (обычно колонка D)
sum_column = "D"

# Применяем цветовую шкалу (зелёный-жёлтый-красный)
rule = ColorScaleRule(
    start_type="min",
    start_color="63BE7B",  # Зелёный (минимум)
    mid_type="percentile",
    mid_value=50,
    mid_color="FFEB84",    # Жёлтый (средний)
    end_type="max",
    end_color="F8696B"     # Красный (максимум)
)

# Применяем к диапазону (со 2-й строки до конца)
sheet.conditional_formatting.add(
    f"{sum_column}2:{sum_column}{sheet.max_row}",
    rule
)

wb.save("reports/report_conditional.xlsx")
print("✅ Условное форматирование применено")
```

### Добавление границ

```python
from openpyxl.styles import Border, Side

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Определяем стиль границ
thin_border = Border(
    left=Side(style="thin", color="000000"),
    right=Side(style="thin", color="000000"),
    top=Side(style="thin", color="000000"),
    bottom=Side(style="thin", color="000000")
)

# Применяем ко всем ячейкам с данными
for row in sheet.iter_rows(
    min_row=1,
    max_row=sheet.max_row,
    min_col=1,
    max_col=sheet.max_column
):
    for cell in row:
        cell.border = thin_border

wb.save("reports/report_bordered.xlsx")
print("✅ Границы добавлены")
```

---

## 📊 Добавление диаграмм

### Гистограмма топ-компаний

```python
from openpyxl.chart import BarChart, Reference

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Создаём график
chart = BarChart()
chart.type = "col"
chart.style = 10
chart.title = "Топ-10 компаний по выручке"
chart.y_axis.title = "Сумма (₽)"
chart.x_axis.title = "Компания"

# Данные для графика (предполагаем отсортированные)
# Компании в колонке B, суммы в колонке D
data = Reference(sheet, min_col=4, min_row=1, max_row=11)  # Топ-10 + заголовок
categories = Reference(sheet, min_col=2, min_row=2, max_row=11)

chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)

# Размещаем график
sheet.add_chart(chart, "F2")

wb.save("reports/report_with_chart.xlsx")
print("✅ График добавлен")
```

### Круговая диаграмма долей

```python
from openpyxl.chart import PieChart, Reference

# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Создаём круговую диаграмму
pie = PieChart()
pie.title = "Распределение выручки по компаниям"

# Данные для диаграммы
labels = Reference(sheet, min_col=2, min_row=2, max_row=6)  # Топ-5 компаний
data = Reference(sheet, min_col=4, min_row=1, max_row=6)

pie.add_data(data, titles_from_data=True)
pie.set_categories(labels)

# Размещаем
sheet.add_chart(pie, "F15")

wb.save("reports/report_with_pie.xlsx")
print("✅ Круговая диаграмма добавлена")
```

---

## 🎛️ Автоматизация кастомизации

### Создание кастомного генератора

```python
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
from typing import Dict

class CustomReportFormatter:
    """Кастомный форматтер для отчётов."""
    
    def __init__(self, corporate_colors: Dict[str, str]):
        """
        Args:
            corporate_colors: Словарь с корпоративными цветами
                {"primary": "1F4E78", "secondary": "E8F4F8", ...}
        """
        self.colors = corporate_colors
    
    def format_header(self, sheet, row_num=1):
        """Форматирует заголовок."""
        header_fill = PatternFill(
            start_color=self.colors.get("primary", "1F4E78"),
            fill_type="solid"
        )
        header_font = Font(
            size=12,
            bold=True,
            color="FFFFFF",
            name="Arial"
        )
        
        for cell in sheet[row_num]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def apply_zebra_grouping(self, sheet, group_column=1, start_row=2):
        """Применяет зебра-группировку."""
        color_1 = self.colors.get("light", "FFFFFF")
        color_2 = self.colors.get("secondary", "E8F4F8")
        
        current_value = None
        color_index = 0
        
        for row in sheet.iter_rows(min_row=start_row, max_row=sheet.max_row):
            cell_value = row[group_column - 1].value
            
            if cell_value != current_value:
                current_value = cell_value
                color_index = 1 - color_index
            
            fill_color = color_1 if color_index == 0 else color_2
            for cell in row:
                cell.fill = PatternFill(start_color=fill_color, fill_type="solid")
    
    def apply_borders(self, sheet):
        """Добавляет границы."""
        thin_border = Border(
            left=Side(style="thin", color="000000"),
            right=Side(style="thin", color="000000"),
            top=Side(style="thin", color="000000"),
            bottom=Side(style="thin", color="000000")
        )
        
        for row in sheet.iter_rows(
            min_row=1,
            max_row=sheet.max_row,
            min_col=1,
            max_col=sheet.max_column
        ):
            for cell in row:
                cell.border = thin_border
    
    def format_report(self, input_path: str, output_path: str):
        """Применяет все форматирования."""
        wb = load_workbook(input_path)
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            
            # Применяем форматирования
            self.format_header(sheet)
            self.apply_zebra_grouping(sheet)
            self.apply_borders(sheet)
        
        wb.save(output_path)
        print(f"✅ Отчёт отформатирован: {output_path}")

# Использование
corporate_colors = {
    "primary": "1F4E78",    # Тёмно-синий
    "secondary": "E8F4F8",  # Светло-голубой
    "light": "FFFFFF"       # Белый
}

formatter = CustomReportFormatter(corporate_colors)
formatter.format_report(
    input_path="reports/report.xlsx",
    output_path="reports/report_corporate.xlsx"
)
```

---

## 🔧 Интеграция в workflow

### Автоматическое применение форматирования

```python
from src.core.app import AppFactory
from pathlib import Path

def generate_custom_report(config_path="config.ini", corporate_colors=None):
    """Генерирует отчёт с кастомным форматированием."""
    
    # 1. Генерируем стандартный отчёт
    with AppFactory.create_app(config_path) as app:
        result = app.generate_report(
            output_path="reports/temp_report.xlsx",
            return_metrics=True
        )
    
    if not result.success:
        print(f"❌ Ошибка генерации: {result.error}")
        return False
    
    # 2. Применяем кастомное форматирование
    colors = corporate_colors or {
        "primary": "1F4E78",
        "secondary": "E8F4F8",
        "light": "FFFFFF"
    }
    
    formatter = CustomReportFormatter(colors)
    formatter.format_report(
        input_path="reports/temp_report.xlsx",
        output_path="reports/final_report.xlsx"
    )
    
    # 3. Удаляем временный файл
    Path("reports/temp_report.xlsx").unlink()
    
    print("✅ Кастомный отчёт готов!")
    return True

# Использование
generate_custom_report()
```

---

## 📐 Настройка ширины колонок

### Фиксированная ширина

```python
# Загружаем отчёт
wb = load_workbook("reports/report.xlsx")
sheet = wb["Краткий"]

# Устанавливаем ширину колонок
column_widths = {
    "A": 15,  # Счёт
    "B": 40,  # Компания
    "C": 12,  # ИНН
    "D": 15,  # Сумма
    "E": 12   # Дата
}

for column, width in column_widths.items():
    sheet.column_dimensions[column].width = width

wb.save("reports/report_fixed_width.xlsx")
print("✅ Ширина колонок установлена")
```

### Авто-ширина (оптимизированная)

```python
def adjust_column_width(sheet, min_width=10, max_width=50):
    """Автоматически подбирает ширину колонок."""
    for column_cells in sheet.columns:
        length = max(len(str(cell.value or "")) for cell in column_cells)
        adjusted_width = min(max(length + 2, min_width), max_width)
        sheet.column_dimensions[column_cells[0].column_letter].width = adjusted_width

# Использование
wb = load_workbook("reports/report.xlsx")
for sheet_name in wb.sheetnames:
    adjust_column_width(wb[sheet_name])

wb.save("reports/report_auto_width.xlsx")
print("✅ Ширина колонок подобрана автоматически")
```

---

## 🎨 Готовые темы

### Тема "Минимализм"

```python
minimal_theme = {
    "header_fill": "F0F0F0",      # Светло-серый
    "header_font_color": "000000", # Чёрный
    "zebra_color_1": "FFFFFF",     # Белый
    "zebra_color_2": "FAFAFA",     # Очень светло-серый
    "border_color": "E0E0E0"       # Серый
}
```

### Тема "Контрастная"

```python
contrast_theme = {
    "header_fill": "000000",       # Чёрный
    "header_font_color": "FFFFFF", # Белый
    "zebra_color_1": "FFFFFF",     # Белый
    "zebra_color_2": "F5F5F5",     # Светло-серый
    "border_color": "000000"       # Чёрный
}
```

### Тема "Корпоративная синяя"

```python
blue_theme = {
    "header_fill": "1F4E78",       # Тёмно-синий
    "header_font_color": "FFFFFF", # Белый
    "zebra_color_1": "E8F4F8",     # Светло-голубой
    "zebra_color_2": "D4E9F2",     # Средне-голубой
    "border_color": "1F4E78"       # Тёмно-синий
}
```

---

## 📚 Дополнительные материалы

### Документация

- **[openpyxl Documentation](https://openpyxl.readthedocs.io/)** - Официальная документация
- **[Excel Generator API](../technical/api/excel-generator.md)** - API генератора
- **[Style Guide](https://openpyxl.readthedocs.io/en/stable/styles.html)** - Руководство по стилям

### Примеры

- **[Basic Report](basic-report.md)** - Базовая генерация
- **[Detailed Report](detailed-report.md)** - Работа с детальными данными
- **[Integration](integration.md)** - Автоматизация форматирования

---

[← Назад к примерам](index.md) | [Error Handling →](error-handling.md)
