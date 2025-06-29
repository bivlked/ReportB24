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
            ws.title = "Отчет"
            
            # 1. Добавляем заголовки с форматированием
            self._add_headers(ws)
            
            # 2. Добавляем данные с правильным форматированием
            self._add_data_rows(ws, data)
            
            # 3. Добавляем итоги как на скриншоте 04.png
            self._add_summary_section(ws, data)
            
            # 4. Применяем финальное форматирование
            self._apply_final_formatting(ws, len(data))
            
            # 5. Заморозка заголовков
            self._freeze_headers(ws)
            
            # 6. Настройка столбцов
            self._adjust_column_widths(ws)
            
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
            
            # Применяем стиль заголовка
            cell.font = Font(bold=True, color="000000")  # Жирный черный текст
            cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")  # Оранжевый фон
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
    
    def _add_summary_section(self, ws, data: List[Dict[str, Any]]) -> None:
        """Добавляет итоги как на скриншоте 04.png."""
        
        if not data:
            return
            
        # Вычисляем итоги
        total_amount = sum(record.get('amount_numeric', 0) or 0 for record in data)
        total_vat = sum(record.get('vat_amount_numeric', 0) or 0 for record in data)
        total_records = len(data)
        
        # Позиция для итогов (строка после данных + 1 пустая строка)
        summary_row = self.start_row + len(data) + 2
        
        # Строка "ИТОГО:"
        summary_cell = ws.cell(row=summary_row, column=self.start_col + 2, value="ИТОГО:")  # В столбце "Контрагент"
        summary_cell.font = Font(bold=True)
        summary_cell.alignment = Alignment(horizontal="right")
        
        # Сумма итого
        amount_cell = ws.cell(row=summary_row, column=self.start_col + 3, value=total_amount)  # Столбец "Сумма"
        amount_cell.font = Font(bold=True)
        amount_cell.alignment = Alignment(horizontal="right")
        amount_cell.number_format = '#,##0.00'
        
        # НДС итого  
        vat_cell = ws.cell(row=summary_row, column=self.start_col + 4, value=total_vat)  # Столбец "НДС"
        vat_cell.font = Font(bold=True)
        vat_cell.alignment = Alignment(horizontal="right")
        vat_cell.number_format = '#,##0.00'
        
        # Жирные границы для итогов
        thick_border = Side(border_style="thick", color="000000")
        
        for col_offset in range(8):  # Все столбцы таблицы
            cell = ws.cell(row=summary_row, column=self.start_col + col_offset)
            cell.border = Border(bottom=thick_border)
        
        self.logger.info(f"📊 Итоги: {total_records} записей, сумма: {total_amount:,.2f}, НДС: {total_vat:,.2f}")
    
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
        
        # ИНН как число (столбец 1)
        if col_idx == 1:
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
    
    def _apply_final_formatting(self, ws, data_rows: int) -> None:
        """Применяет финальное форматирование к таблице."""
        
        # Границы вокруг всей таблицы
        thick_border = Side(border_style="thick", color="000000")
        
        total_rows = self.start_row + data_rows + 2  # заголовки + данные + итоги
        total_cols = self.start_col + 7  # 8 столбцов = индекс 7
        
        # Жирная граница вокруг всей таблицы
        for row in range(self.start_row, total_rows + 1):
            for col in range(self.start_col, total_cols + 1):
                cell = ws.cell(row=row, column=col)
                
                border_left = thick_border if col == self.start_col else cell.border.left
                border_right = thick_border if col == total_cols else cell.border.right  
                border_top = thick_border if row == self.start_row else cell.border.top
                border_bottom = thick_border if row == total_rows else cell.border.bottom
                
                cell.border = Border(
                    left=border_left,
                    right=border_right,
                    top=border_top,
                    bottom=border_bottom
                )
    
    def _freeze_headers(self, ws) -> None:
        """Заморозка заголовков при прокручивании."""
        
        # Заморозка на строке после заголовков
        freeze_cell = f"{get_column_letter(self.start_col)}{self.start_row + 1}"
        ws.freeze_panes = freeze_cell
        self.logger.info(f"🧊 Заголовки заморожены на позиции: {freeze_cell}")
    
    def _adjust_column_widths(self, ws) -> None:
        """Настройка ширины столбцов для оптимального отображения."""
        
        column_widths = {
            self.start_col + 0: 12,  # Номер
            self.start_col + 1: 15,  # ИНН
            self.start_col + 2: 30,  # Контрагент  
            self.start_col + 3: 15,  # Сумма
            self.start_col + 4: 12,  # НДС
            self.start_col + 5: 12,  # Дата счёта
            self.start_col + 6: 12,  # Дата отгрузки
            self.start_col + 7: 12,  # Дата оплаты
        }
        
        for col_num, width in column_widths.items():
            ws.column_dimensions[get_column_letter(col_num)].width = width


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