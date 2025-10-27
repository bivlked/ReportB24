"""
Модуль оркестрации workflow.

Координирует весь процесс генерации отчётов от получения данных
из Bitrix24 до создания финального Excel файла с обработкой ошибок.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..config.config_reader import ConfigReader
from ..bitrix24_client.client import Bitrix24Client
from ..data_processor.data_processor import DataProcessor
from ..excel_generator.generator import ExcelReportGenerator
from .error_handler import handle_error


@dataclass
class WorkflowResult:
    """Результат выполнения workflow."""
    success: bool
    records_processed: int = 0
    excel_file_path: Optional[Path] = None
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    detailed_stats: Optional[Dict[str, Any]] = None
    
    @property
    def is_successful(self) -> bool:
        """Проверяет успешность выполнения."""
        return self.success and self.excel_file_path is not None


@dataclass
class WorkflowProgress:
    """Прогресс выполнения workflow."""
    current_stage: str
    stages_completed: int
    total_stages: int
    current_operation: str
    records_processed: int = 0
    
    @property
    def progress_percent(self) -> float:
        """Возвращает процент выполнения."""
        if self.total_stages == 0:
            return 0.0
        return (self.stages_completed / self.total_stages) * 100


class WorkflowStages:
    """Этапы выполнения workflow."""
    
    INITIALIZATION = "initialization"
    DATA_FETCHING = "data_fetching"
    DATA_PROCESSING = "data_processing"
    EXCEL_GENERATION = "excel_generation"
    FINALIZATION = "finalization"
    
    ALL_STAGES = [
        INITIALIZATION,
        DATA_FETCHING,
        DATA_PROCESSING,
        EXCEL_GENERATION,
        FINALIZATION
    ]


class WorkflowOrchestrator:
    """
    Оркестратор workflow процесса генерации отчётов.
    
    Координирует взаимодействие всех компонентов системы для выполнения
    полного цикла: получение данных → обработка → генерация Excel отчёта.
    """
    
    def __init__(self, 
                 bitrix_client: Bitrix24Client,
                 data_processor: DataProcessor,
                 excel_generator: ExcelReportGenerator,
                 config_reader: ConfigReader):
        """
        Инициализация оркестратора.
        
        Args:
            bitrix_client: Клиент для работы с Bitrix24 API
            data_processor: Обработчик данных
            excel_generator: Генератор Excel отчётов
            config_reader: Читатель конфигурации
        """
        self.bitrix_client = bitrix_client
        self.data_processor = data_processor
        self.excel_generator = excel_generator
        self.config_reader = config_reader
        
        # 🔧 ИСПРАВЛЕНИЕ БАГ-2: Передаём Bitrix24Client в DataProcessor
        self.data_processor.set_bitrix_client(bitrix_client)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_progress: Optional[WorkflowProgress] = None
        
        # Колбэки для отслеживания прогресса
        self.progress_callbacks: List[callable] = []
    
    def add_progress_callback(self, callback: callable) -> None:
        """
        Добавляет колбэк для отслеживания прогресса.
        
        Args:
            callback: Функция, которая будет вызываться при обновлении прогресса
        """
        self.progress_callbacks.append(callback)
    
    def _update_progress(self, stage: str, operation: str, records_processed: int = 0) -> None:
        """Обновляет прогресс выполнения."""
        if stage in WorkflowStages.ALL_STAGES:
            stages_completed = WorkflowStages.ALL_STAGES.index(stage)
        else:
            stages_completed = 0
        
        self.current_progress = WorkflowProgress(
            current_stage=stage,
            stages_completed=stages_completed,
            total_stages=len(WorkflowStages.ALL_STAGES),
            current_operation=operation,
            records_processed=records_processed
        )
        
        # Уведомление колбэков
        for callback in self.progress_callbacks:
            try:
                callback(self.current_progress)
            except Exception as e:
                self.logger.warning(f"Ошибка в progress callback: {e}")
    
    def execute_full_workflow(self, output_file_path: Path) -> WorkflowResult:
        """
        Выполняет полный workflow генерации отчёта (v2.4.0 - refactored).
        
        Args:
            output_file_path: Путь для сохранения Excel файла
            
        Returns:
            WorkflowResult: Результат выполнения workflow
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Начало выполнения workflow генерации отчёта")
            
            # Этап 1: Инициализация
            period_config = self._execute_initialization_stage()
            
            # Этап 2: Получение данных
            raw_invoices_data = self._execute_data_fetching_stage(period_config)
            if not raw_invoices_data:
                return self._create_error_result("Не найдено счетов для указанного периода", start_time)
            
            # Этап 3: Обработка данных
            processed_data = self._execute_data_processing_stage(raw_invoices_data)
            if not processed_data:
                return self._create_error_result("После обработки не осталось валидных записей", start_time)
            
            # Этап 4: Генерация Excel
            excel_path = self._execute_excel_generation_stage(processed_data, output_file_path)
            
            # Этап 5: Финализация
            result = self._execute_finalization_stage(excel_path, processed_data, start_time)
            
            self.logger.info(f"Workflow завершён успешно за {result.execution_time_seconds:.2f} сек")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = f"Ошибка workflow: {str(e)}"
            
            handle_error(e, "execute_full_workflow", "WorkflowOrchestrator")
            self.logger.error(error_message)
            
            return WorkflowResult(
                success=False,
                error_message=error_message,
                execution_time_seconds=execution_time
            )
    
    def _execute_initialization_stage(self):
        """Этап 1: Инициализация и получение конфигурации."""
        self._update_progress(WorkflowStages.INITIALIZATION, "Подготовка к выполнению")
        self.logger.info("Этап 1: Инициализация")
        
        period_config = self.config_reader.get_report_period_config()
        self.logger.info(f"Период отчёта: {period_config.start_date} - {period_config.end_date}")
        
        return period_config
    
    def _execute_data_fetching_stage(self, period_config) -> List[Dict[str, Any]]:
        """Этап 2: Получение данных из Bitrix24."""
        self._update_progress(WorkflowStages.DATA_FETCHING, "Получение данных из Bitrix24")
        self.logger.info("Этап 2: Получение данных из Bitrix24")
        
        raw_invoices_data = self._fetch_invoices_data(period_config.start_date, period_config.end_date)
        self.logger.info(f"Получено счетов: {len(raw_invoices_data)}")
        
        return raw_invoices_data
    
    def _execute_data_processing_stage(self, raw_invoices_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Этап 3: Обработка и валидация данных."""
        self._update_progress(WorkflowStages.DATA_PROCESSING, "Обработка и валидация данных")
        self.logger.info("Этап 3: Обработка данных")
        
        processed_data = self._process_invoices_data(raw_invoices_data)
        self.logger.info(f"Обработано записей: {len(processed_data)}")
        
        return processed_data
    
    def _execute_excel_generation_stage(self, processed_data: List[Dict[str, Any]], output_file_path: Path) -> Path:
        """Этап 4: Генерация Excel отчёта."""
        self._update_progress(WorkflowStages.EXCEL_GENERATION, "Создание Excel отчёта", len(processed_data))
        self.logger.info("Этап 4: Генерация Excel отчёта")
        
        excel_path = self._generate_excel_report(processed_data, output_file_path)
        self.logger.info(f"Excel отчёт создан: {excel_path}")
        
        return excel_path
    
    def _execute_finalization_stage(
        self, 
        excel_path: Path, 
        processed_data: List[Dict[str, Any]], 
        start_time: datetime
    ) -> WorkflowResult:
        """Этап 5: Финализация и формирование результата."""
        self._update_progress(WorkflowStages.FINALIZATION, "Завершение и проверка результата")
        self.logger.info("Этап 5: Финализация")
        
        # Проверка созданного файла
        if not excel_path.exists():
            return WorkflowResult(
                success=False,
                error_message=f"Excel файл не был создан: {excel_path}",
                execution_time_seconds=(datetime.now() - start_time).total_seconds()
            )
        
        # Статистика
        detailed_stats = self._calculate_detailed_stats(processed_data)
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return WorkflowResult(
            success=True,
            records_processed=len(processed_data),
            excel_file_path=excel_path,
            execution_time_seconds=execution_time,
            detailed_stats=detailed_stats
        )
    
    def _create_error_result(self, error_message: str, start_time: datetime) -> WorkflowResult:
        """Создает результат с ошибкой."""
        return WorkflowResult(
            success=False,
            error_message=error_message,
            execution_time_seconds=(datetime.now() - start_time).total_seconds()
        )
    
    def _fetch_invoices_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Получает данные счетов из Bitrix24 (v2.4.0 - refactored).
        
        Args:
            start_date: Дата начала периода (дд.мм.гггг)
            end_date: Дата окончания периода (дд.мм.гггг)
            
        Returns:
            List: Список данных счетов с реквизитами
        """
        try:
            # Конвертация дат
            start_date_obj, end_date_obj = self._convert_date_range(start_date, end_date)
            self.logger.info(f"Получение Smart Invoices за период: {start_date_obj} - {end_date_obj}")
            
            # Получение всех счетов
            all_invoices = self._fetch_all_invoices()
            self.logger.info(f"Получено {len(all_invoices)} счетов всего")
            
            # Фильтрация по дате отгрузки
            filtered_invoices = self._filter_invoices_by_date(all_invoices, start_date_obj, end_date_obj)
            self.logger.info(f"Отфильтровано {len(filtered_invoices)} счетов по дате отгрузки")
            
            # Обогащение реквизитами
            enriched_invoices = self._enrich_invoices_with_requisites(filtered_invoices)
            self.logger.info(f"Итого обработано {len(enriched_invoices)} счетов с реквизитами")
            
            return enriched_invoices
            
        except Exception as e:
            handle_error(e, "_fetch_invoices_data", "WorkflowOrchestrator")
            raise
    
    def _convert_date_range(self, start_date: str, end_date: str) -> Tuple[Any, Any]:
        """Конвертирует строковые даты в объекты date."""
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, "%d.%m.%Y").date()
        end_date_obj = datetime.strptime(end_date, "%d.%m.%Y").date()
        return start_date_obj, end_date_obj
    
    def _fetch_all_invoices(self) -> List[Dict[str, Any]]:
        """Получает все Smart Invoices из Bitrix24 (как в ShortReport.py)."""
        filter_params = {"!stageId": "DT31_1:D"}
        select_fields = [
            'id', 'accountNumber', 'statusId', 'dateBill', 'price',
            'UFCRM_SMART_INVOICE_1651168135187', 'UFCRM_626D6ABE98692',
            'begindate', 'opportunity', 'stageId', 'taxValue'
        ]
        return self.bitrix_client.get_smart_invoices(entity_type_id=31, filters=filter_params, select=select_fields)
    
    def _filter_invoices_by_date(self, invoices: List[Dict[str, Any]], start_date: Any, end_date: Any) -> List[Dict[str, Any]]:
        """Фильтрует счета по дате отгрузки."""
        from datetime import datetime
        filtered = []
        for inv in invoices:
            ship_date_str = inv.get('UFCRM_SMART_INVOICE_1651168135187')
            if ship_date_str:
                try:
                    d = datetime.fromisoformat(ship_date_str.replace('Z', '+00:00')).date()
                    if start_date <= d <= end_date:
                        filtered.append(inv)
                except ValueError as ex:
                    self.logger.warning(f"Ошибка преобразования даты отгрузки (ID={inv.get('id')}): {ex}")
        return filtered
    
    def _enrich_invoices_with_requisites(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обогащает счета данными реквизитов компаний (v2.4.0 - optimized).
        
        Оптимизация: Запрашивает реквизиты только для уникальных номеров счетов,
        сокращая количество API запросов с N до K (где K - уникальные счета).
        """
        if not invoices:
            return []
        
        # Собираем уникальные номера счетов
        unique_accounts = set(inv.get('accountNumber', '') for inv in invoices if inv.get('accountNumber'))
        
        # Кеш для реквизитов {account_number: (company_name, inn)}
        requisites_cache = {}
        
        # Запрашиваем реквизиты только для уникальных счетов
        for acc_num in unique_accounts:
            try:
                comp_name, inn = self.bitrix_client.get_company_info_by_invoice(acc_num)
                if not comp_name and not inn:
                    comp_name, inn = "Не найдено", "Не найдено"
                requisites_cache[acc_num] = (comp_name, inn)
            except Exception as exp:
                self.logger.error(f"Ошибка получения реквизитов для счета {acc_num}: {exp}")
                requisites_cache[acc_num] = ("Ошибка", "Ошибка")
        
        self.logger.debug(f"Запрошено реквизитов: {len(requisites_cache)} уникальных из {len(invoices)} счетов")
        
        # Обогащаем счета из кеша
        enriched = []
        for invoice in invoices:
            acc_num = invoice.get('accountNumber', '')
            
            # Получаем реквизиты из кеша
            if acc_num in requisites_cache:
                comp_name, inn = requisites_cache[acc_num]
            else:
                comp_name, inn = "Не найдено", "Не найдено"
            
            # Создаем обогащенную копию
            enriched_invoice = invoice.copy()
            enriched_invoice.update({'company_name': comp_name, 'company_inn': inn})
            enriched.append(enriched_invoice)
        
        return enriched
    
    # 🔧 v2.4.0: Методы _format_amount, _format_vat_amount, _format_date удалены
    # Форматирование теперь выполняется в DataProcessor и ExcelReportGenerator

    def _process_invoices_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обрабатывает сырые данные счетов используя DataProcessor (v2.4.0).
        
        Новая гибридная архитектура:
        - DataProcessor обрабатывает и валидирует данные
        - WorkflowOrchestrator координирует процесс
        - Excel генератор форматирует Decimal типы
        
        Args:
            raw_data: Сырые данные счетов из Bitrix24
            
        Returns:
            List[Dict]: Обработанные данные для Excel с ЧИСЛОВЫМИ типами
        """
        try:
            # Используем DataProcessor для batch обработки!
            processed_invoices = self.data_processor.process_invoice_batch(raw_data)
            
            # Конвертируем ProcessedInvoice в dict для Excel
            processed_records = [invoice.to_dict() for invoice in processed_invoices]
            
            # Фильтруем invalid записи
            valid_records = [r for r in processed_records if r.get('is_valid', True)]
            
            self.logger.info(f"Обработано {len(valid_records)} валидных записей из {len(raw_data)}")
            
            return valid_records
            
        except Exception as e:
            handle_error(e, "_process_invoices_data", "WorkflowOrchestrator")
            raise
    
    def _generate_excel_report(self, processed_data: List[Dict[str, Any]], output_path: Path) -> Path:
        """
        Генерирует Excel отчёт.
        
        Args:
            processed_data: Обработанные данные
            output_path: Путь для сохранения файла
            
        Returns:
            Path: Путь к созданному файлу
        """
        try:
            # Создание Excel отчёта
            self.excel_generator.create_report(processed_data, str(output_path))
            
            return output_path
            
        except Exception as e:
            handle_error(e, "_generate_excel_report", "WorkflowOrchestrator")
            raise
    
    def _calculate_detailed_stats(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Вычисляет детальную статистику по обработанным данным.
        
        Args:
            processed_data: Обработанные данные
            
        Returns:
            Dict: Статистика
        """
        if not processed_data:
            return {"total_records": 0}
        
        # Базовая статистика
        total_records = len(processed_data)
        total_amount = sum(float(record.get('amount_numeric', 0) or 0) for record in processed_data)
        total_vat = sum(float(record.get('vat_amount_numeric', 0) or 0) for record in processed_data)
        
        # Статистика по НДС
        vat_stats = {}
        for record in processed_data:
            vat_rate = record.get('vat_rate', 'Без НДС')
            if vat_rate not in vat_stats:
                vat_stats[vat_rate] = {"count": 0, "amount": 0}
            vat_stats[vat_rate]["count"] += 1
            vat_stats[vat_rate]["amount"] += float(record.get('amount_numeric', 0) or 0)
        
        # Статистика по контрагентам
        contractors = {}
        for record in processed_data:
            contractor = record.get('counterparty', 'Неизвестно')
            if contractor not in contractors:
                contractors[contractor] = {"count": 0, "amount": 0}
            contractors[contractor]["count"] += 1
            contractors[contractor]["amount"] += float(record.get('amount_numeric', 0) or 0)
        
        # Топ-5 контрагентов по сумме
        top_contractors = sorted(
            contractors.items(), 
            key=lambda x: x[1]["amount"], 
            reverse=True
        )[:5]
        
        return {
            "total_records": total_records,
            "total_amount": total_amount,
            "total_vat": total_vat,
            "vat_breakdown": vat_stats,
            "unique_contractors": len(contractors),
            "top_contractors": [
                {
                    "name": name,
                    "count": stats["count"],
                    "amount": stats["amount"]
                }
                for name, stats in top_contractors
            ]
        }
    
    def validate_workflow_readiness(self) -> Tuple[bool, List[str]]:
        """
        Проверяет готовность к выполнению workflow.
        
        Returns:
            Tuple: (готовность, список ошибок)
        """
        errors = []
        
        # Проверка компонентов
        if not self.bitrix_client:
            errors.append("Bitrix24 клиент не инициализирован")
        
        if not self.data_processor:
            errors.append("Обработчик данных не инициализирован")
        
        if not self.excel_generator:
            errors.append("Генератор Excel не инициализирован")
        
        if not self.config_reader:
            errors.append("Читатель конфигурации не инициализирован")
        
        # Проверка конфигурации
        try:
            period_config = self.config_reader.get_report_period_config()
            if not period_config.start_date or not period_config.end_date:
                errors.append("Не настроен период отчёта")
        except Exception as e:
            errors.append(f"Ошибка чтения конфигурации: {e}")
        
        # Проверка API подключения
        try:
            if self.bitrix_client:
                stats = self.bitrix_client.get_stats()
                if not stats:
                    errors.append("Не удалось получить статистику API")
        except Exception as e:
            errors.append(f"Ошибка проверки API: {e}")
        
        return len(errors) == 0, errors
    
    def get_current_progress(self) -> Optional[WorkflowProgress]:
        """
        Возвращает текущий прогресс выполнения.
        
        Returns:
            WorkflowProgress: Текущий прогресс или None
        """
        return self.current_progress
    
    def cleanup(self) -> None:
        """Очищает ресурсы оркестратора."""
        try:
            self.logger.info("Очистка ресурсов WorkflowOrchestrator")
            
            # Очистка колбэков
            self.progress_callbacks.clear()
            
            # Сброс прогресса
            self.current_progress = None
            
            self.logger.info("Очистка WorkflowOrchestrator завершена")
            
        except Exception as e:
            handle_error(e, "cleanup", "WorkflowOrchestrator") 