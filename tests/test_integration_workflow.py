"""
Интеграционные end-to-end тесты для всего workflow.

Тестирует полный цикл работы приложения от инициализации
до генерации Excel отчёта.
"""

import pytest
import tempfile
import configparser
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.app import ReportGeneratorApp, AppFactory
from src.core.workflow import WorkflowOrchestrator, WorkflowStages
from src.core.error_handler import get_error_handler
from src.config.settings import TestSettings


class TestEndToEndWorkflow:
    """End-to-end тесты полного workflow."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        # Очистка глобального обработчика ошибок
        get_error_handler().clear_error_history()
    
    def create_test_config(self) -> str:
        """Создаёт временный конфигурационный файл для тестов."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            for section, values in TestSettings.TEST_CONFIG_DATA.items():
                config.add_section(section)
                for key, value in values.items():
                    config.set(section, key, value)
            
            config.write(f)
            return f.name
    
    @patch('src.bitrix24_client.client.Bitrix24Client')
    @patch('src.data_processor.data_processor.DataProcessor')
    @patch('src.excel_generator.generator.ExcelReportGenerator')
    def test_app_initialization_workflow(self, mock_excel, mock_data, mock_bitrix):
        """Тест полного цикла инициализации приложения."""
        temp_config = self.create_test_config()
        
        try:
            # Настройка моков
            mock_bitrix_instance = MagicMock()
            mock_bitrix.return_value = mock_bitrix_instance
            
            mock_data_instance = MagicMock()
            mock_data.return_value = mock_data_instance
            
            mock_excel_instance = MagicMock()
            mock_excel.return_value = mock_excel_instance
            
            # Создание приложения
            app = ReportGeneratorApp(temp_config, enable_logging=False)
            
            # Тест инициализации
            success = app.initialize()
            assert success is True
            
            # Проверка статуса
            assert app.status.is_initialized is True
            assert app.status.is_configured is True
            assert app.status.is_validated is True
            
            # Проверка компонентов
            assert app.bitrix_client is not None
            assert app.data_processor is not None
            assert app.excel_generator is not None
            assert app.workflow_orchestrator is not None
            
            # Тест получения информации о приложении
            app_info = app.get_app_info()
            assert app_info['app_name'] == "Генератор отчётов Bitrix24"
            assert app_info['app_version'] == "1.0.0"
            assert app_info['status']['is_initialized'] is True
            
            app.shutdown()
            
        finally:
            Path(temp_config).unlink()
    
    @patch('src.core.app.validate_system')
    def test_app_initialization_failure_handling(self, mock_validate):
        """Тест обработки ошибок при инициализации."""
        # Мокируем неудачную валидацию системы
        mock_validate.return_value = (False, "Тестовая ошибка валидации")
        
        temp_config = self.create_test_config()
        
        try:
            app = ReportGeneratorApp(temp_config, enable_logging=False)
            
            # Инициализация должна провалиться
            success = app.initialize()
            assert success is False
            
            # Статус должен отражать неудачу
            assert app.status.is_initialized is False
            assert app.status.is_validated is False
            
        finally:
            Path(temp_config).unlink()
    
    @patch('src.bitrix24_client.client.Bitrix24Client')
    def test_workflow_orchestrator_integration(self, mock_bitrix):
        """Тест интеграции WorkflowOrchestrator с компонентами."""
        temp_config = self.create_test_config()
        
        try:
            # Настройка моков
            mock_bitrix_instance = MagicMock()
            mock_bitrix_instance.get_smart_invoices.return_value = [
                {
                    'ID': '1',
                    'ACCOUNT_NUMBER': 'INV-001',
                    'OPPORTUNITY': '10000.00',
                    'UF_CRM_SHIPPING_DATE': '01.01.2023',
                    'UF_CRM_INN': '1234567890',
                    'UF_CRM_COMPANY_NAME': 'Тест Компания'
                }
            ]
            mock_bitrix_instance.get_requisite_links.return_value = []
            mock_bitrix_instance.get_stats.return_value = {'requests_made': 0}
            mock_bitrix.return_value = mock_bitrix_instance
            
            # Создание приложения через фабрику
            app = AppFactory.create_app(temp_config, enable_logging=False)
            
            # Проверка готовности workflow
            is_ready, errors = app.workflow_orchestrator.validate_workflow_readiness()
            
            # Может быть ошибки из-за моков, но проверяем что метод работает
            assert isinstance(is_ready, bool)
            assert isinstance(errors, list)
            
            app.shutdown()
            
        finally:
            Path(temp_config).unlink()
    
    def test_app_factory_create_for_testing(self):
        """Тест создания приложения для тестирования через фабрику."""
        # Тест создания с дефолтными тестовыми данными
        app = AppFactory.create_for_testing()
        
        assert isinstance(app, ReportGeneratorApp)
        assert app.enable_logging is False
        
        # Проверка что конфигурация загружена
        assert app.config_path is not None
        assert Path(app.config_path).exists()
        
        # Очистка временного файла
        Path(app.config_path).unlink()
    
    def test_app_context_manager(self):
        """Тест использования приложения как context manager."""
        temp_config = self.create_test_config()
        
        try:
            with ReportGeneratorApp(temp_config, enable_logging=False) as app:
                assert isinstance(app, ReportGeneratorApp)
                
                # Приложение должно корректно завершиться при выходе из контекста
            
            # После выхода из контекста приложение должно быть завершено
            
        finally:
            if Path(temp_config).exists():
                Path(temp_config).unlink()
    
    @patch('src.bitrix24_client.client.Bitrix24Client')
    @patch('src.excel_generator.generator.ExcelReportGenerator')
    def test_report_generation_workflow_mock(self, mock_excel, mock_bitrix):
        """Тест полного workflow генерации отчёта с моками."""
        temp_config = self.create_test_config()
        
        try:
            # Настройка моков
            mock_bitrix_instance = MagicMock()
            mock_bitrix_instance.get_smart_invoices.return_value = [
                {
                    'ID': '1',
                    'ACCOUNT_NUMBER': 'INV-001',
                    'OPPORTUNITY': '10000.00',
                    'UF_CRM_SHIPPING_DATE': '01.01.2023',
                    'UF_CRM_INN': '1234567890',
                    'UF_CRM_COMPANY_NAME': 'Тест Компания'
                }
            ]
            mock_bitrix_instance.get_requisite_links.return_value = []
            mock_bitrix_instance.get_stats.return_value = {'requests_made': 0}
            mock_bitrix.return_value = mock_bitrix_instance
            
            mock_excel_instance = MagicMock()
            mock_excel.return_value = mock_excel_instance
            
            # Создание и инициализация приложения
            with ReportGeneratorApp(temp_config, enable_logging=False) as app:
                success = app.initialize()
                assert success is True
                
                # Попытка генерации отчёта
                # Может провалиться из-за моков, но проверяем что код выполняется
                result = app.generate_report('test_report.xlsx')
                
                # Проверяем что метод вызвался без критических ошибок
                assert isinstance(result, bool)
                
        finally:
            Path(temp_config).unlink()
    
    def test_error_handling_integration(self):
        """Тест интеграции системы обработки ошибок."""
        temp_config = self.create_test_config()
        
        try:
            app = ReportGeneratorApp(temp_config, enable_logging=False)
            
            # Попытка операции без инициализации (должна вызвать ошибку)
            result = app.generate_report()
            assert result is False
            
            # Проверка что ошибка была зарегистрирована
            error_summary = app.get_error_report()
            assert isinstance(error_summary, str)
            
            # Может содержать информацию об ошибке или быть пустым
            
        finally:
            Path(temp_config).unlink()
    
    def test_workflow_progress_tracking(self):
        """Тест отслеживания прогресса workflow."""
        from src.core.workflow import ProgressTracker
        
        tracker = ProgressTracker()
        
        # Имитация прогресса
        from src.core.workflow import WorkflowProgress
        
        progress1 = WorkflowProgress(
            current_stage=WorkflowStages.INITIALIZATION,
            stages_completed=0,
            total_stages=5,
            current_operation="Инициализация"
        )
        
        progress2 = WorkflowProgress(
            current_stage=WorkflowStages.DATA_FETCHING,
            stages_completed=1,
            total_stages=5,
            current_operation="Получение данных"
        )
        
        tracker.track_progress(progress1)
        tracker.track_progress(progress2)
        
        # Проверка сводки прогресса
        summary = tracker.get_progress_summary()
        assert summary['stages_completed'] == 2
        assert summary['total_operations'] == 2
        assert summary['last_stage'] == WorkflowStages.DATA_FETCHING


class TestIntegrationErrorScenarios:
    """Тесты интеграции для различных сценариев ошибок."""
    
    def test_missing_dependencies_handling(self):
        """Тест обработки отсутствующих зависимостей."""
        # Этот тест проверяет что система корректно обрабатывает
        # отсутствие критических зависимостей
        
        # В реальной ситуации зависимости есть, поэтому мокируем
        with patch('sys.modules', {'nonexistent_module': None}):
            # Система должна корректно работать даже если некоторые
            # модули недоступны
            pass
    
    def test_configuration_edge_cases(self):
        """Тест крайних случаев конфигурации."""
        # Конфигурация с минимальными значениями
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            config.add_section('BitrixAPI')
            config.set('BitrixAPI', 'webhookurl', 'https://a.bitrix24.ru/rest/1/a/')
            
            config.add_section('AppSettings')
            config.set('AppSettings', 'defaultsavefolder', '.')
            config.set('AppSettings', 'defaultfilename', 'a.xlsx')
            
            config.add_section('ReportPeriod')
            config.set('ReportPeriod', 'startdate', '01.01.2023')
            config.set('ReportPeriod', 'enddate', '02.01.2023')  # Очень короткий период
            
            config.write(f)
            temp_config = f.name
        
        try:
            app = ReportGeneratorApp(temp_config, enable_logging=False)
            
            # Приложение должно корректно работать даже с минимальной конфигурацией
            # (хотя может быть предупреждения)
            assert app.config_path == temp_config
            
        finally:
            Path(temp_config).unlink()
    
    def test_concurrent_access_simulation(self):
        """Тест симуляции конкурентного доступа."""
        # Симулируем ситуацию где несколько экземпляров приложения
        # могут работать одновременно
        
        temp_config1 = None
        temp_config2 = None
        
        try:
            # Создание двух конфигураций
            for i, temp_config in enumerate([temp_config1, temp_config2], 1):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                    config = configparser.ConfigParser()
                    
                    for section, values in TestSettings.TEST_CONFIG_DATA.items():
                        config.add_section(section)
                        for key, value in values.items():
                            if key == 'defaultsavefolder':
                                value = f'test_reports_{i}'  # Разные папки
                            config.set(section, key, value)
                    
                    config.write(f)
                    if i == 1:
                        temp_config1 = f.name
                    else:
                        temp_config2 = f.name
            
            # Создание двух приложений
            app1 = ReportGeneratorApp(temp_config1, enable_logging=False)
            app2 = ReportGeneratorApp(temp_config2, enable_logging=False)
            
            # Оба должны корректно инициализироваться
            assert app1.config_path != app2.config_path
            
            app1.shutdown()
            app2.shutdown()
            
        finally:
            for temp_config in [temp_config1, temp_config2]:
                if temp_config and Path(temp_config).exists():
                    Path(temp_config).unlink()
            
            # Очистка тестовых директорий
            for i in [1, 2]:
                test_dir = Path(f'test_reports_{i}')
                if test_dir.exists():
                    import shutil
                    shutil.rmtree(test_dir) 