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
from ..config.settings import BitrixAPISettings
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
        Выполняет полный workflow генерации отчёта.
        
        Args:
            output_file_path: Путь для сохранения Excel файла
            
        Returns:
            WorkflowResult: Результат выполнения workflow
        """
        start_time = datetime.now()
        
        try:
            self.logger.info("Начало выполнения workflow генерации отчёта")
            
            # Этап 1: Инициализация
            self._update_progress(WorkflowStages.INITIALIZATION, "Подготовка к выполнению")
            self.logger.info("Этап 1: Инициализация")
            
            # Получение конфигурации периода
            period_config = self.config_reader.get_report_period_config()
            self.logger.info(f"Период отчёта: {period_config.start_date} - {period_config.end_date}")
            
            # Этап 2: Получение данных из Bitrix24
            self._update_progress(WorkflowStages.DATA_FETCHING, "Получение данных из Bitrix24")
            self.logger.info("Этап 2: Получение данных из Bitrix24")
            
            raw_invoices_data = self._fetch_invoices_data(period_config.start_date, period_config.end_date)
            self.logger.info(f"Получено счетов: {len(raw_invoices_data)}")
            
            if not raw_invoices_data:
                return WorkflowResult(
                    success=False,
                    error_message="Не найдено счетов для указанного периода",
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Этап 3: Обработка данных
            self._update_progress(WorkflowStages.DATA_PROCESSING, "Обработка и валидация данных")
            self.logger.info("Этап 3: Обработка данных")
            
            processed_data = self._process_invoices_data(raw_invoices_data)
            self.logger.info(f"Обработано записей: {len(processed_data)}")
            
            if not processed_data:
                return WorkflowResult(
                    success=False,
                    error_message="После обработки не осталось валидных записей",
                    execution_time_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Этап 4: Генерация Excel отчёта
            self._update_progress(WorkflowStages.EXCEL_GENERATION, "Создание Excel отчёта", len(processed_data))
            self.logger.info("Этап 4: Генерация Excel отчёта")
            
            excel_path = self._generate_excel_report(processed_data, output_file_path)
            self.logger.info(f"Excel отчёт создан: {excel_path}")
            
            # Этап 5: Финализация
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
            
            self.logger.info(f"Workflow завершён успешно за {execution_time:.2f} сек")
            
            return WorkflowResult(
                success=True,
                records_processed=len(processed_data),
                excel_file_path=excel_path,
                execution_time_seconds=execution_time,
                detailed_stats=detailed_stats
            )
            
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
    
    def _fetch_invoices_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Получает данные счетов из Bitrix24.
        
        Args:
            start_date: Дата начала периода (дд.мм.гггг)
            end_date: Дата окончания периода (дд.мм.гггг)
            
        Returns:
            List: Список данных счетов
        """
        try:
            # Параметры фильтрации
            filter_params = {
                ">=UF_CRM_SHIPPING_DATE": start_date,
                "<=UF_CRM_SHIPPING_DATE": end_date
            }
            
            # Поля для выборки
            select_fields = [
                "ID",
                "ACCOUNT_NUMBER",
                "OPPORTUNITY", 
                "CURRENCY_ID",
                "UF_CRM_SHIPPING_DATE",
                "UF_CRM_INN",
                "UF_CRM_COMPANY_NAME",
                "UF_CRM_VAT_RATE",
                "UF_CRM_VAT_AMOUNT"
            ]
            
            self.logger.info(f"Запрос счетов с {start_date} по {end_date}")
            
            # Получение Smart Invoices 
            invoices = self.bitrix_client.get_smart_invoices(
                entity_type_id=31,
                filters=filter_params
            )
            
            # Обогащение данными реквизитов
            enriched_invoices = self._enrich_with_requisites(invoices)
            
            return enriched_invoices
            
        except Exception as e:
            handle_error(e, "_fetch_invoices_data", "WorkflowOrchestrator")
            raise
    
    def _enrich_with_requisites(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обогащает данные счетов информацией из реквизитов.
        
        Args:
            invoices: Список счетов
            
        Returns:
            List: Обогащённый список счетов
        """
        enriched = []
        
        for invoice in invoices:
            try:
                # Копируем базовые данные
                enriched_invoice = invoice.copy()
                
                # Получаем связи с реквизитами
                if 'ID' in invoice:
                    requisite_links = self.bitrix_client.get_requisite_links(
                        entity_type_id=BitrixAPISettings.SMART_INVOICE_ENTITY_TYPE_ID,
                        entity_id=invoice['ID']
                    )
                    
                    # Получаем детали первого реквизита
                    if requisite_links:
                        first_link = requisite_links[0]
                        if 'REQUISITE_ID' in first_link:
                            requisite_details = self.bitrix_client.get_requisite_details(
                                first_link['REQUISITE_ID']
                            )
                            
                            # Добавляем данные реквизитов
                            if requisite_details:
                                enriched_invoice.update({
                                    'REQUISITE_NAME': requisite_details.get('NAME', ''),
                                    'REQUISITE_INN': requisite_details.get('RQ_INN', ''),
                                    'REQUISITE_KPP': requisite_details.get('RQ_KPP', ''),
                                    'REQUISITE_ACTIVE': requisite_details.get('ACTIVE', 'N')
                                })
                
                enriched.append(enriched_invoice)
                
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку других счетов
                self.logger.warning(f"Ошибка обогащения счёта {invoice.get('ID', 'unknown')}: {e}")
                enriched.append(invoice)  # Добавляем без обогащения
        
        return enriched
    
    def _process_invoices_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Обрабатывает сырые данные счетов.
        
        Args:
            raw_data: Сырые данные из Bitrix24
            
        Returns:
            List: Обработанные данные
        """
        try:
            processed_records = []
            
            for record in raw_data:
                try:
                    # Обработка через DataProcessor
                    processed_record = self.data_processor.process_invoice_record(record)
                    
                    if processed_record:
                        processed_records.append(processed_record)
                    else:
                        self.logger.warning(f"Запись {record.get('ID', 'unknown')} не прошла валидацию")
                        
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки записи {record.get('ID', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Успешно обработано {len(processed_records)} из {len(raw_data)} записей")
            
            return processed_records
            
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
        total_amount = sum(float(record.get('amount', 0) or 0) for record in processed_data)
        total_vat = sum(float(record.get('vat_amount', 0) or 0) for record in processed_data)
        
        # Статистика по НДС
        vat_stats = {}
        for record in processed_data:
            vat_rate = record.get('vat_rate', 'Без НДС')
            if vat_rate not in vat_stats:
                vat_stats[vat_rate] = {"count": 0, "amount": 0}
            vat_stats[vat_rate]["count"] += 1
            vat_stats[vat_rate]["amount"] += float(record.get('amount', 0) or 0)
        
        # Статистика по контрагентам
        contractors = {}
        for record in processed_data:
            contractor = record.get('contractor', 'Неизвестно')
            if contractor not in contractors:
                contractors[contractor] = {"count": 0, "amount": 0}
            contractors[contractor]["count"] += 1
            contractors[contractor]["amount"] += float(record.get('amount', 0) or 0)
        
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


class ProgressTracker:
    """Трекер прогресса для workflow."""
    
    def __init__(self):
        self.progress_history: List[WorkflowProgress] = []
    
    def track_progress(self, progress: WorkflowProgress) -> None:
        """Отслеживает изменения прогресса."""
        self.progress_history.append(progress)
        print(f"🔄 {progress.current_stage}: {progress.current_operation} "
              f"({progress.progress_percent:.1f}%)")
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по прогрессу."""
        if not self.progress_history:
            return {"stages_completed": 0, "total_time": 0}
        
        return {
            "stages_completed": len(set(p.current_stage for p in self.progress_history)),
            "total_operations": len(self.progress_history),
            "last_stage": self.progress_history[-1].current_stage,
            "last_operation": self.progress_history[-1].current_operation,
            "records_processed": self.progress_history[-1].records_processed
        } 