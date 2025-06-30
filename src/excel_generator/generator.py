#!/usr/bin/env python3
"""
Генератор Excel отчетов для Bitrix24.

Создает финальные отчеты с правильным форматированием,
соответствующим скриншотам-эталонам.
"""

from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
import logging

from .styles import ExcelStyles, ColumnStyleConfig
from .layout import WorksheetBuilder, ReportLayout
from .formatter import ExcelDataFormatter, ExcelSummaryFormatter, DataValidator


class ExcelReportGenerator:
    """
    Финальный генератор Excel отчетов.
    
    Создает отчеты с полным соответствием скриншотам-эталонам:
    - Отступы сверху и слева
    - Заморозка заголовков при прокручивании 
    - Правильные цвета и границы
    - Выравнивание по типу данных
    - Числовое форматирование
    - Итоги как на скриншоте 04.png
    """
    
    def __init__(self):
        self.styles = ExcelStyles()
        self.layout = ReportLayout()
        self.worksheet_builder = WorksheetBuilder()
        self.data_formatter = ExcelDataFormatter()
        self.summary_formatter = ExcelSummaryFormatter()
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        # Настройки отступов (начинаем с B2 вместо A1)
        self.start_row = 2  # Отступ сверху
        self.start_col = 2  # Отступ слева (столбец B)
    
    def create_report(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """
        Создает финальный Excel отчет с полным форматированием.
        
        Args:
            data: Обработанные данные счетов
            output_path: Путь для сохранения файла
        """
        try:
            self.logger.info(f"📊 Создание финального Excel отчета: {len(data)} записей")
            
            # Создаем новую книгу
            wb = Workbook()  
            ws = wb.active
            ws.title = "Краткий"  # 7. Название листа "Краткий"
            
            # 1. Добавляем заголовки с форматированием
            self._add_headers(ws)
            
            # 2. Добавляем данные с правильным форматированием
            self._add_data_rows(ws, data)
            
            # 3. Применяем границы только вокруг данных (без итогов)
            self._apply_data_table_borders(ws, len(data))
            
            # 4. Добавляем итоги как на скриншоте 04.png (ВНЕ жирной рамки)
            self._add_summary_section_new_format(ws, data)
            
            # 5. Заморозка заголовков
            self._freeze_headers(ws)
            
            # 6. Настройка столбцов с автошириной
            self._adjust_column_widths_auto(ws, data)
            
            # Сохраняем файл
            wb.save(output_path)
            self.logger.info(f"✅ Excel отчет успешно создан: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания Excel отчета: {e}")
            raise
    
    def _add_headers(self, ws) -> None:
        """Добавляет строку заголовков с правильным форматированием."""
        headers = self.layout.get_column_headers()
        
        # Заголовки начинаются с позиции (start_row, start_col)
        for col_idx, header in enumerate(headers):
            cell = ws.cell(
                row=self.start_row, 
                column=self.start_col + col_idx, 
                value=header
            )
            
            # 6. Применяем новый цвет заголовков #FCE4D6 (Orange, Accent 2, Lighter 80%)
            cell.font = Font(bold=True, color="000000")  # Жирный черный текст
            cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")  # Новый оранжевый фон
            cell.alignment = Alignment(horizontal="center", vertical="center")  # По центру
            
            # Жирные границы для заголовков
            thick_border = Side(border_style="thick", color="000000")
            thin_border = Side(border_style="thin", color="000000")
            
            cell.border = Border(
                top=thick_border,
                left=thick_border if col_idx == 0 else thin_border,
                right=thick_border if col_idx == len(headers) - 1 else thin_border,
                bottom=thick_border  # Нижняя граница заголовков жирная
            )
    
    def _add_data_rows(self, ws, data: List[Dict[str, Any]]) -> None:
        """Добавляет строки данных с правильным форматированием."""
        
        for row_idx, record in enumerate(data):
            ws_row = self.start_row + 1 + row_idx  # +1 чтобы не перезаписать заголовки
            
            # Получаем данные строки в правильном порядке
            row_data = [
                record.get('account_number', ''),
                record.get('inn', ''),
                record.get('counterparty', ''),
                record.get('amount', ''),
                record.get('vat_amount', ''),
                record.get('invoice_date', ''),
                record.get('shipping_date', ''),
                record.get('payment_date', '')
            ]
            
            # Определяем цвет строки
            fill_color = self._get_row_color(record)
            
            for col_idx, value in enumerate(row_data):
                cell = ws.cell(
                    row=ws_row,
                    column=self.start_col + col_idx,
                    value=value
                )
                
                # 2. Преобразуем номер счета в число для правильного форматирования
                if col_idx == 0 and value:  # Столбец "Номер"
                    try:
                        # Извлекаем числовую часть из номера счета
                        if isinstance(value, str) and '-' in value:
                            number_part = value.split('-')[0]
                            cell.value = int(number_part)
                        elif isinstance(value, str) and value.isdigit():
                            cell.value = int(value)
                    except (ValueError, AttributeError):
                        pass  # Оставляем как есть, если не удается преобразовать
                
                # Цветовая заливка строки
                if fill_color:
                    cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                
                # Выравнивание по типу столбца
                cell.alignment = self._get_column_alignment(col_idx)
                
                # Числовое форматирование
                cell.number_format = self._get_column_number_format(col_idx)
                
                # Обычные границы для данных
                thin_border = Side(border_style="thin", color="000000")
                thick_border = Side(border_style="thick", color="000000")
                
                cell.border = Border(
                    top=thin_border,
                    left=thick_border if col_idx == 0 else thin_border,
                    right=thick_border if col_idx == len(row_data) - 1 else thin_border,
                    bottom=thin_border
                )
    
    def _apply_data_table_borders(self, ws, data_rows: int) -> None:
        """4. Применяет жирную рамку только вокруг таблицы с данными (БЕЗ итогов)."""
        
        thick_border = Side(border_style="thick", color="000000")
        
        # Рамка заканчивается ПОСЛЕ последней строки данных
        last_data_row = self.start_row + data_rows  # заголовки + данные
        last_col = self.start_col + 7  # 8 столбцов = индекс 7
        
        # Жирная граница только вокруг таблицы с данными
        for row in range(self.start_row, last_data_row + 1):
            for col in range(self.start_col, last_col + 1):
                cell = ws.cell(row=row, column=col)
                
                border_left = thick_border if col == self.start_col else cell.border.left
                border_right = thick_border if col == last_col else cell.border.right  
                border_top = thick_border if row == self.start_row else cell.border.top
                border_bottom = thick_border if row == last_data_row else cell.border.bottom
                
                cell.border = Border(
                    left=border_left,
                    right=border_right,
                    top=border_top,
                    bottom=border_bottom
                )
    
    def _add_summary_section_new_format(self, ws, data: List[Dict[str, Any]]) -> None:
        """5. Добавляет итоги в новом формате как на скриншоте 04.png."""
        
        if not data:
            return
        
        # Вычисляем итоги
        total_amount = sum(record.get('amount_numeric', 0) or 0 for record in data)
        total_vat = sum(record.get('vat_amount_numeric', 0) or 0 for record in data)
        
        # Вычисляем счета с НДС и без НДС
        no_vat_records = [r for r in data if r.get('is_no_vat', False)]
        with_vat_records = [r for r in data if not r.get('is_no_vat', False)]
        
        no_vat_amount = sum(record.get('amount_numeric', 0) or 0 for record in no_vat_records)
        with_vat_amount = sum(record.get('amount_numeric', 0) or 0 for record in with_vat_records)
        
        # Позиция для итогов (строка после данных + 2 пустые строки)
        summary_start_row = self.start_row + len(data) + 3
        
        # 5. Новый формат итогов как на скриншоте 04.png
        summaries = [
            ("Всего счетов на сумму:", total_amount),
            ("Счетов без НДС на сумму:", no_vat_amount), 
            ("Счетов с НДС на сумму:", with_vat_amount),
            ("Всего НДС в счетах:", total_vat)
        ]
        
        for idx, (label, amount) in enumerate(summaries):
            current_row = summary_start_row + idx
            
            # Подпись в столбце D (Контрагент)
            label_cell = ws.cell(row=current_row, column=self.start_col + 2, value=label)
            label_cell.font = Font(bold=True)
            label_cell.alignment = Alignment(horizontal="left")
            
            # Сумма в столбце E (Сумма)
            amount_cell = ws.cell(row=current_row, column=self.start_col + 3, value=amount)
            amount_cell.font = Font(bold=True)
            amount_cell.alignment = Alignment(horizontal="right")
            amount_cell.number_format = '#,##0.00'
            
            # Выделяем НДС красным цветом
            if "НДС" in label:
                amount_cell.font = Font(bold=True, color="FF0000")  # Красный цвет для НДС
        
        self.logger.info(f"📊 Новые итоги: {len(data)} счетов, всего: {total_amount:,.2f}, без НДС: {no_vat_amount:,.2f}, с НДС: {with_vat_amount:,.2f}, НДС: {total_vat:,.2f}")
    
    def _get_row_color(self, record: Dict[str, Any]) -> Optional[str]:
        """Определяет цвет строки по данным записи."""
        
        # Красный для неоплаченных
        if record.get('is_unpaid', False):
            return "FFC0CB"  # Красный для неоплаченных
            
        # Серый для записей без НДС
        if record.get('is_no_vat', False):
            return "D3D3D3"  # Серый для "Без НДС"
            
        return None  # Белый фон для обычных записей
    
    def _get_column_alignment(self, col_idx: int) -> Alignment:
        """Возвращает выравнивание для столбца по индексу."""
        
        # Столбцы для центрирования: Номер(0), ИНН(1), Дата счёта(5), Дата отгрузки(6), Дата оплаты(7)
        center_columns = [0, 1, 5, 6, 7]
        # Столбцы для правого выравнивания: Сумма(3), НДС(4)  
        right_columns = [3, 4]
         
        if col_idx in center_columns:
            return Alignment(horizontal="center", vertical="center")
        elif col_idx in right_columns:
            return Alignment(horizontal="right", vertical="center")
        else:
            return Alignment(horizontal="left", vertical="center")  # Контрагент слева
    
    def _get_column_number_format(self, col_idx: int) -> str:
        """Возвращает числовое форматирование для столбца."""
        
        # 2. Номер как число (столбец 0)
        if col_idx == 0:
            return '0'  # Целое число без разделителей
        
        # ИНН как число (столбец 1)
        elif col_idx == 1:
            return '0'  # Целое число без разделителей
            
        # Суммы как числа (столбцы 3, 4)
        elif col_idx in [3, 4]:
            return '#,##0.00'  # Число с разделителями тысяч и 2 знака после запятой
            
        else:
            return 'General'  # Обычный формат для остальных
    
    def _parse_amount(self, amount_str: str) -> float:
        """Парсит сумму из строки в число."""
        
        if not amount_str or amount_str == 'нет':
            return 0.0
            
        try:
            # Убираем все кроме цифр, точек и запятых
            clean_str = str(amount_str).replace(' ', '').replace(',', '.')
            return float(clean_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _freeze_headers(self, ws) -> None:
        """Заморозка заголовков при прокручивании."""
        
        # Заморозка на строке после заголовков
        freeze_cell = f"{get_column_letter(self.start_col)}{self.start_row + 1}"
        ws.freeze_panes = freeze_cell
        self.logger.info(f"🧊 Заголовки заморожены на позиции: {freeze_cell}")
    
    def _adjust_column_widths_auto(self, ws, data: List[Dict[str, Any]]) -> None:
        """1. Настройка ширины столбцов с автоподбором для "Контрагент", "Дата счёта", "Дата оплаты"."""
        
        # 3. Столбец A (пустой) делаем очень узким - примерно как высота строки
        ws.column_dimensions[get_column_letter(1)].width = 3  # Очень узкий столбец A
        
        # Базовые ширины столбцов
        column_widths = {
            self.start_col + 0: 12,  # Номер
            self.start_col + 1: 15,  # ИНН
            self.start_col + 2: 25,  # Контрагент (базовая ширина)
            self.start_col + 3: 15,  # Сумма
            self.start_col + 4: 12,  # НДС
            self.start_col + 5: 14,  # Дата счёта (базовая ширина)
            self.start_col + 6: 14,  # Дата отгрузки
            self.start_col + 7: 14,  # Дата оплаты (базовая ширина)
        }
        
        # 1. Автоподбор ширины для "Контрагент", "Дата счёта", "Дата оплаты"
        if data:
            # Анализируем длину контрагентов
            max_counterparty_len = max(len(str(record.get('counterparty', ''))) for record in data) if data else 0
            if max_counterparty_len > 25:
                column_widths[self.start_col + 2] = min(max_counterparty_len + 2, 50)  # Максимум 50
            
            # Анализируем даты (обычно одинаковые по длине, но проверим на всякий случай)
            max_invoice_date_len = max(len(str(record.get('invoice_date', ''))) for record in data) if data else 0
            max_payment_date_len = max(len(str(record.get('payment_date', ''))) for record in data) if data else 0
            
            if max_invoice_date_len > 14:
                column_widths[self.start_col + 5] = min(max_invoice_date_len + 2, 20)
            if max_payment_date_len > 14:
                column_widths[self.start_col + 7] = min(max_payment_date_len + 2, 20)
        
        # Применяем ширины
        for col_num, width in column_widths.items():
            ws.column_dimensions[get_column_letter(col_num)].width = width
            
        self.logger.info(f"📏 Настроены ширины столбцов: A={3}, Контрагент={column_widths[self.start_col + 2]}, Даты={column_widths[self.start_col + 5]}")


class ReportGenerationError(Exception):
    """Custom exception for report generation errors."""
    pass


class ExcelReportBuilder:
    """
    High-level builder interface for Excel reports.
    
    Provides a convenient API for creating reports with different configurations.
    """
    
    def __init__(self):
        self.generator = ExcelReportGenerator()
    
    def build_invoice_report(self, invoices: List[Dict[str, Any]], 
                           output_path: str,
                           report_title: str = "Отчёт по счетам") -> str:
        """
        Build an invoice report.
        
        Args:
            invoices: List of invoice data
            output_path: Where to save the report
            report_title: Title for the report sheet
            
        Returns:
            Path to the generated report
        """
        try:
            return self.generator.generate_report(
                data=invoices,
                output_path=output_path,
                sheet_name=report_title
            )
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate invoice report: {e}")
    
    def build_summary_report(self, invoices: List[Dict[str, Any]], 
                           output_path: str) -> Dict[str, Any]:
        """
        Build a summary report with statistics only.
        
        Args:
            invoices: List of invoice data
            output_path: Where to save the report
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            # Format data
            formatted_data = self.generator.data_formatter.format_invoice_data(invoices)
            
            # Generate summary
            summary = self.generator.summary_formatter.format_summary(formatted_data)
            
            # Generate Excel file
            self.generator.generate_report(
                data=invoices,
                output_path=output_path,
                sheet_name="Сводка"
            )
            
            return summary
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate summary report: {e}")
    
    def validate_data_for_report(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate data before report generation.
        
        Args:
            data: List of data to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'total_records': len(data),
            'valid_records': 0,
            'invalid_records': 0,
            'errors': []
        }
        
        for i, record in enumerate(data):
            try:
                # Validate record
                validated = self.generator.validator.validate_invoice_data(record)
                
                # Try formatting
                formatted = self.generator.data_formatter._format_single_invoice(validated, i + 1)
                
                results['valid_records'] += 1
                
            except Exception as e:
                results['invalid_records'] += 1
                results['errors'].append(f"Record {i + 1}: {str(e)}")
                results['is_valid'] = False
        
        return results 