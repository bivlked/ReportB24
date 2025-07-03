"""
Excel layout module for Bitrix24 report generation.

Defines the report structure, headers, and column configuration
that exactly matches the provided screenshots.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet


@dataclass
class ColumnDefinition:
    """Definition for a single report column."""
    
    header: str           # Column header text
    width: float         # Column width in Excel units
    alignment: str       # Text alignment: 'left', 'center', 'right'
    data_key: str        # Key in data dict for this column


class ReportLayout:
    """
    Report layout configuration matching the screenshot requirements.
    
    Defines column structure, headers, and layout parameters
    for the Bitrix24 invoice report.
    """
    
    # Column definitions matching the screenshot
    COLUMNS = [
        ColumnDefinition(
            header="Номер",
            width=15.0,
            alignment="center",
            data_key="invoice_number"
        ),
        ColumnDefinition(
            header="ИНН",
            width=15.0,
            alignment="center",
            data_key="inn"
        ),
        ColumnDefinition(
            header="Контрагент",
            width=30.0,
            alignment="left",
            data_key="contractor_name"
        ),
        ColumnDefinition(
            header="Сумма",
            width=18.0,
            alignment="right",
            data_key="total_amount"
        ),
        ColumnDefinition(
            header="НДС",
            width=18.0,
            alignment="center",
            data_key="vat_amount"
        ),
        ColumnDefinition(
            header="Дата счёта",
            width=15.0,
            alignment="right",
            data_key="invoice_date"
        ),
        ColumnDefinition(
            header="Дата отгрузки",
            width=15.0,
            alignment="right",
            data_key="shipment_date"
        ),
        ColumnDefinition(
            header="Дата оплаты",
            width=15.0,
            alignment="right",
            data_key="payment_date"
        ),
    ]
    
    # Layout constants
    HEADER_ROW = 2          # Row for headers (1-based, skip empty row)
    DATA_START_ROW = 3      # First data row (1-based)
    START_COLUMN = 2        # Starting column (1-based, skip empty column)
    
    def __init__(self):
        self.total_columns = len(self.COLUMNS)
    
    def setup_worksheet(self, ws: Worksheet) -> None:
        """
        Set up worksheet with proper structure and column widths.
        
        Args:
            ws: OpenPyXL worksheet object
        """
        # Set column widths
        for i, col_def in enumerate(self.COLUMNS, start=self.START_COLUMN):
            col_letter = ws.cell(row=1, column=i).column_letter
            ws.column_dimensions[col_letter].width = col_def.width
        
        # Set row heights
        ws.row_dimensions[self.HEADER_ROW].height = 20  # Header row height
        
        # Freeze panes (freeze first row and first column)
        # This allows headers to stay visible when scrolling
        freeze_cell = ws.cell(row=self.DATA_START_ROW, column=self.START_COLUMN)
        ws.freeze_panes = freeze_cell
    
    def write_headers(self, ws: Worksheet) -> None:
        """
        Write column headers to the worksheet.
        
        Args:
            ws: OpenPyXL worksheet object
        """
        for i, col_def in enumerate(self.COLUMNS, start=self.START_COLUMN):
            cell = ws.cell(row=self.HEADER_ROW, column=i)
            cell.value = col_def.header
    
    def get_data_cell_position(self, row_index: int, column_index: int) -> Tuple[int, int]:
        """
        Get Excel cell position for data.
        
        Args:
            row_index: 0-based data row index
            column_index: 0-based column index
            
        Returns:
            Tuple of (row, column) in 1-based Excel coordinates
        """
        excel_row = self.DATA_START_ROW + row_index
        excel_col = self.START_COLUMN + column_index
        return excel_row, excel_col
    
    def get_column_key(self, column_index: int) -> str:
        """
        Get data key for a column.
        
        Args:
            column_index: 0-based column index
            
        Returns:
            Data key string for this column
        """
        if 0 <= column_index < len(self.COLUMNS):
            return self.COLUMNS[column_index].data_key
        return ""
    
    def get_column_alignment(self, column_index: int) -> str:
        """
        Get alignment for a column.
        
        Args:
            column_index: 0-based column index
            
        Returns:
            Alignment type: 'left', 'center', or 'right'
        """
        if 0 <= column_index < len(self.COLUMNS):
            return self.COLUMNS[column_index].alignment
        return "left"
    
    def get_column_headers(self) -> List[str]:
        """
        Get list of column headers.
        
        Returns:
            List of column header strings
        """
        return [col_def.header for col_def in self.COLUMNS]


class SummaryLayout:
    """
    Layout for summary/totals section at the bottom of the report.
    
    Provides structure for totals and statistics that appear
    below the main data table.
    """
    
    def __init__(self, layout: ReportLayout):
        self.layout = layout
    
    def add_summary_section(self, ws: Worksheet, data_row_count: int, 
                          totals: Dict[str, Any]) -> None:
        """
        Add summary section with totals below the data.
        
        Args:
            ws: OpenPyXL worksheet object
            data_row_count: Number of data rows written
            totals: Dictionary with total amounts
        """
        # Calculate summary start row (2 rows below last data)
        summary_start_row = self.layout.DATA_START_ROW + data_row_count + 2
        
        # Total count
        count_row = summary_start_row
        ws.cell(row=count_row, column=self.layout.START_COLUMN).value = "Всего записей:"
        ws.cell(row=count_row, column=self.layout.START_COLUMN + 1).value = data_row_count
        
        # Total amounts
        if 'amount_without_vat' in totals:
            amount_row = summary_start_row + 1
            ws.cell(row=amount_row, column=self.layout.START_COLUMN).value = "Общая сумма без НДС:"
            ws.cell(row=amount_row, column=self.layout.START_COLUMN + 4).value = totals['amount_without_vat']
        
        if 'amount_with_vat' in totals:
            total_row = summary_start_row + 2
            ws.cell(row=total_row, column=self.layout.START_COLUMN).value = "Общая сумма с НДС:"
            ws.cell(row=total_row, column=self.layout.START_COLUMN + 6).value = totals['amount_with_vat']


class WorksheetBuilder:
    """
    Builder class for creating and configuring Excel worksheets.
    
    Combines layout configuration with styling to create
    properly formatted worksheets.
    """
    
    def __init__(self):
        self.layout = ReportLayout()
        self.summary = SummaryLayout(self.layout)
    
    def create_worksheet(self, workbook: Workbook, sheet_name: str = "Отчёт") -> Worksheet:
        """
        Create and configure a new worksheet.
        
        Args:
            workbook: OpenPyXL workbook object
            sheet_name: Name for the worksheet
            
        Returns:
            Configured worksheet object
        """
        # Create or get worksheet
        if workbook.worksheets:
            ws = workbook.active
            ws.title = sheet_name
        else:
            ws = workbook.create_sheet(sheet_name)
        
        # Apply layout configuration
        self.layout.setup_worksheet(ws)
        self.layout.write_headers(ws)
        
        return ws
    
    def calculate_totals(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate totals for the summary section.
        
        Args:
            data: List of data rows
            
        Returns:
            Dictionary with calculated totals
        """
        totals = {
            'count': len(data),
            'amount_without_vat': 0.0,
            'amount_with_vat': 0.0
        }
        
        for row in data:
            # Add amounts (handle both string and numeric values)
            if 'amount_without_vat' in row:
                amount = row['amount_without_vat']
                if isinstance(amount, (int, float)):
                    totals['amount_without_vat'] += amount
            
            if 'amount_with_vat' in row:
                amount = row['amount_with_vat']
                if isinstance(amount, (int, float)):
                    totals['amount_with_vat'] += amount
        
        return totals


# ============================================================================
# ДЕТАЛЬНЫЙ ОТЧЕТ LAYOUT - ФАЗА 4: EXCEL ГЕНЕРАЦИЯ
# ============================================================================

class DetailedReportLayout:
    """
    Layout configuration for detailed report with product breakdown.
    
    Создает макет для листа "Полный" с детальной информацией о товарах.
    Интегрируется с DataProcessor из Фазы 3 для обработки данных товаров.
    """
    
    # Column definitions for detailed report (8 columns)
    COLUMNS = [
        ColumnDefinition(
            header="Номер счёта",
            width=18.0,
            alignment="center",
            data_key="invoice_number"
        ),
        ColumnDefinition(
            header="Контрагент", 
            width=25.0,
            alignment="left",
            data_key="company_name"
        ),
        ColumnDefinition(
            header="ИНН",
            width=15.0,
            alignment="center",
            data_key="inn"
        ),
        ColumnDefinition(
            header="Наименование товара",
            width=35.0,
            alignment="left",
            data_key="product_name"
        ),
        ColumnDefinition(
            header="Кол-во",
            width=12.0,
            alignment="right",
            data_key="quantity"
        ),
        ColumnDefinition(
            header="Ед. изм.",
            width=10.0,
            alignment="center",
            data_key="unit_measure"
        ),
        ColumnDefinition(
            header="Цена",
            width=15.0,
            alignment="right",
            data_key="price"
        ),
        ColumnDefinition(
            header="Сумма",
            width=18.0,
            alignment="right",
            data_key="total_amount"
        ),
    ]
    
    # Layout constants (same as brief report for consistency)
    HEADER_ROW = 2
    DATA_START_ROW = 3
    START_COLUMN = 2
    
    # Green header color from Hello World Excel Test
    HEADER_FILL_COLOR = "C6E0B4"  # Green color for headers
    
    def __init__(self):
        self.total_columns = len(self.COLUMNS)
    
    def setup_worksheet(self, ws: Worksheet) -> None:
        """
        Set up detailed worksheet with proper structure and styling.
        
        Применяет зеленые заголовки, заморозку панелей и границы
        как в Hello World Excel Test из Фазы 0.
        
        Args:
            ws: OpenPyXL worksheet object
        """
        from openpyxl.styles import PatternFill, Border, Side, Alignment
        
        # Set column widths
        for i, col_def in enumerate(self.COLUMNS, start=self.START_COLUMN):
            col_letter = ws.cell(row=1, column=i).column_letter
            ws.column_dimensions[col_letter].width = col_def.width
        
        # Set row heights
        ws.row_dimensions[self.HEADER_ROW].height = 22  # Slightly taller for detailed headers
        
        # Freeze panes at first data row
        freeze_cell = ws.cell(row=self.DATA_START_ROW, column=self.START_COLUMN)
        ws.freeze_panes = freeze_cell
        
        # Apply header styling (green background)
        header_fill = PatternFill(start_color=self.HEADER_FILL_COLOR, 
                                end_color=self.HEADER_FILL_COLOR, 
                                fill_type="solid")
        
        # Border style for professional look
        border_style = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Apply styling to header row
        for i in range(self.START_COLUMN, self.START_COLUMN + self.total_columns):
            header_cell = ws.cell(row=self.HEADER_ROW, column=i)
            header_cell.fill = header_fill
            header_cell.border = border_style
            header_cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def write_headers(self, ws: Worksheet) -> None:
        """
        Write column headers for detailed report.
        
        Args:
            ws: OpenPyXL worksheet object
        """
        for i, col_def in enumerate(self.COLUMNS, start=self.START_COLUMN):
            cell = ws.cell(row=self.HEADER_ROW, column=i)
            cell.value = col_def.header
    
    def apply_zebra_effect(self, ws: Worksheet, data_rows: List[Dict[str, Any]]) -> None:
        """
        Применение зебра-эффекта для группировки по счетам.
        
        Чередует цвет строк для каждого нового счета, чтобы
        визуально разделить товары разных счетов.
        
        Args:
            ws: OpenPyXL worksheet object  
            data_rows: Список строк данных с метаданными группировки
        """
        from openpyxl.styles import PatternFill
        
        # Colors for zebra effect (light gray for alternating invoices)
        zebra_color = "F2F2F2"  # Light gray
        zebra_fill = PatternFill(start_color=zebra_color, 
                               end_color=zebra_color, 
                               fill_type="solid")
        
        current_invoice_id = None
        use_zebra = False
        
        for row_idx, row_data in enumerate(data_rows):
            invoice_id = row_data.get('invoice_id')
            
            # Check if we're starting a new invoice group
            if invoice_id != current_invoice_id:
                current_invoice_id = invoice_id
                use_zebra = not use_zebra  # Toggle zebra effect
            
            # Apply zebra fill to this row if needed
            if use_zebra:
                excel_row = self.DATA_START_ROW + row_idx
                for col_idx in range(self.START_COLUMN, self.START_COLUMN + self.total_columns):
                    cell = ws.cell(row=excel_row, column=col_idx)
                    cell.fill = zebra_fill
    
    def get_data_cell_position(self, row_index: int, column_index: int) -> Tuple[int, int]:
        """
        Get Excel cell position for detailed data.
        
        Args:
            row_index: 0-based data row index
            column_index: 0-based column index
            
        Returns:
            Tuple of (row, column) in 1-based Excel coordinates
        """
        excel_row = self.DATA_START_ROW + row_index
        excel_col = self.START_COLUMN + column_index
        return excel_row, excel_col
    
    def get_column_key(self, column_index: int) -> str:
        """Get data key for a column in detailed report."""
        if 0 <= column_index < len(self.COLUMNS):
            return self.COLUMNS[column_index].data_key
        return ""
    
    def get_column_alignment(self, column_index: int) -> str:
        """Get alignment for a column in detailed report."""
        if 0 <= column_index < len(self.COLUMNS):
            return self.COLUMNS[column_index].alignment
        return "left"
    
    def get_column_headers(self) -> List[str]:
        """Get list of column headers for detailed report."""
        return [col_def.header for col_def in self.COLUMNS]


class DetailedWorksheetBuilder:
    """
    Builder for creating detailed report worksheets.
    
    Создает и настраивает листы для детального отчета с товарами.
    Интегрируется с DataProcessor для обработки данных.
    """
    
    def __init__(self):
        self.layout = DetailedReportLayout()
    
    def create_detailed_worksheet(
        self, 
        workbook: Workbook, 
        sheet_name: str = "Полный"
    ) -> Worksheet:
        """
        Create and configure detailed worksheet.
        
        Args:
            workbook: OpenPyXL workbook object
            sheet_name: Name for the detailed worksheet
            
        Returns:
            Configured detailed worksheet object
        """
        # Create new worksheet (don't replace existing ones)
        ws = workbook.create_sheet(sheet_name)
        
        # Apply detailed layout configuration
        self.layout.setup_worksheet(ws)
        self.layout.write_headers(ws)
        
        return ws
    
    def write_detailed_data(
        self, 
        ws: Worksheet, 
        data_rows: List[Dict[str, Any]]
    ) -> None:
        """
        Write detailed product data to worksheet.
        
        Записывает данные товаров с применением зебра-эффекта
        для группировки по счетам.
        
        Args:
            ws: OpenPyXL worksheet object
            data_rows: List of formatted product data from DataProcessor
        """
        from openpyxl.styles import Alignment, Border, Side
        
        # Border for data cells
        border_style = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Write data rows
        for row_idx, row_data in enumerate(data_rows):
            for col_idx, col_def in enumerate(self.layout.COLUMNS):
                excel_row, excel_col = self.layout.get_data_cell_position(row_idx, col_idx)
                
                cell = ws.cell(row=excel_row, column=excel_col)
                cell.value = row_data.get(col_def.data_key, "")
                
                # Apply alignment
                cell.alignment = Alignment(horizontal=col_def.alignment, vertical="center")
                
                # Apply border
                cell.border = border_style
        
        # Apply zebra effect after writing all data
        self.layout.apply_zebra_effect(ws, data_rows)
    
    def add_detailed_summary(
        self, 
        ws: Worksheet, 
        data_row_count: int,
        summary_stats: Dict[str, Any]
    ) -> None:
        """
        Add summary section for detailed report.
        
        Args:
            ws: OpenPyXL worksheet object
            data_row_count: Number of product rows written
            summary_stats: Summary statistics (total products, invoices, etc.)
        """
        # Calculate summary start row
        summary_start_row = self.layout.DATA_START_ROW + data_row_count + 2
        
        # Products count
        ws.cell(row=summary_start_row, column=self.layout.START_COLUMN).value = "Всего товаров:"
        ws.cell(row=summary_start_row, column=self.layout.START_COLUMN + 1).value = data_row_count
        
        # Invoices count
        if 'total_invoices' in summary_stats:
            invoices_row = summary_start_row + 1
            ws.cell(row=invoices_row, column=self.layout.START_COLUMN).value = "Всего счетов:"
            ws.cell(row=invoices_row, column=self.layout.START_COLUMN + 1).value = summary_stats['total_invoices']


class MultiSheetBuilder:
    """
    Builder for creating multi-sheet reports (Brief + Detailed).
    
    Создает Excel файл с двумя листами: "Краткий" и "Полный".
    Координирует работу обычного и детального макетов.
    """
    
    def __init__(self):
        self.brief_builder = WorksheetBuilder()
        self.detailed_builder = DetailedWorksheetBuilder()
    
    def create_multi_sheet_workbook(self) -> Workbook:
        """
        Create workbook with both brief and detailed sheets.
        
        Returns:
            Workbook with "Краткий" and "Полный" sheets
        """
        workbook = Workbook()
        
        # Remove default sheet if exists
        if workbook.worksheets:
            workbook.remove(workbook.active)
        
        # Create brief sheet first
        brief_ws = self.brief_builder.create_worksheet(workbook, "Краткий")
        
        # Create detailed sheet
        detailed_ws = self.detailed_builder.create_detailed_worksheet(workbook, "Полный")
        
        return workbook
    
    def get_brief_worksheet(self, workbook: Workbook) -> Worksheet:
        """Get brief worksheet from multi-sheet workbook."""
        return workbook["Краткий"]
    
    def get_detailed_worksheet(self, workbook: Workbook) -> Worksheet:
        """Get detailed worksheet from multi-sheet workbook."""
        return workbook["Полный"] 