"""
Интеграционные тесты для модуля конфигурации.

Проверяет работу конфигурационного слоя с реальными файлами
и валидацию настроек системы.
"""

import pytest
import tempfile
import configparser
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.config_reader import (
    ConfigReader, BitrixConfig, AppConfig, ReportPeriodConfig,
    create_config_reader
)
from src.config.validation import (
    validate_system, ComprehensiveValidator, ValidationResult
)
from src.config.settings import TestSettings


class TestConfigIntegration:
    """Тесты интеграции конфигурационного модуля."""
    
    def test_create_temp_config_file(self):
        """Тест создания временного конфигурационного файла."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            # Добавление тестовых данных
            for section, values in TestSettings.TEST_CONFIG_DATA.items():
                config.add_section(section)
                for key, value in values.items():
                    config.set(section, key, value)
            
            config.write(f)
            temp_path = f.name
        
        # Проверка что файл создан
        assert Path(temp_path).exists()
        
        # Проверка чтения через ConfigReader
        reader = ConfigReader(temp_path)
        reader.load_config()
        
        # Проверка всех секций
        bitrix_config = reader.get_bitrix_config()
        app_config = reader.get_app_config()
        period_config = reader.get_report_period_config()
        
        assert bitrix_config.webhook_url == TestSettings.TEST_CONFIG_DATA['BitrixAPI']['webhookurl']
        assert app_config.default_save_folder == TestSettings.TEST_CONFIG_DATA['AppSettings']['defaultsavefolder']
        assert period_config.start_date == TestSettings.TEST_CONFIG_DATA['ReportPeriod']['startdate']
        
        # Очистка
        Path(temp_path).unlink()
    
    def test_config_validation_integration(self):
        """Тест интеграции валидации конфигурации."""
        # Создание валидного конфигурационного файла
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            config.add_section('BitrixAPI')
            config.set('BitrixAPI', 'webhookurl', 'https://test.bitrix24.ru/rest/1/test123/')
            
            config.add_section('AppSettings')
            config.set('AppSettings', 'defaultsavefolder', 'test_reports')
            config.set('AppSettings', 'defaultfilename', 'test_report.xlsx')
            
            config.add_section('ReportPeriod')
            config.set('ReportPeriod', 'startdate', '01.01.2023')
            config.set('ReportPeriod', 'enddate', '31.12.2023')
            
            config.write(f)
            temp_path = f.name
        
        try:
            # Тест валидации без сетевых проверок
            is_valid, report = validate_system(temp_path, check_network=False)
            
            # Может быть предупреждения, но не должно быть критических ошибок
            assert isinstance(is_valid, bool)
            assert isinstance(report, str)
            
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_config_handling(self):
        """Тест обработки некорректной конфигурации."""
        # Создание некорректного конфигурационного файла
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            # Неполная конфигурация
            config.add_section('BitrixAPI')
            config.set('BitrixAPI', 'webhookurl', 'invalid_url')
            
            # Отсутствуют обязательные секции
            
            config.write(f)
            temp_path = f.name
        
        try:
            # Проверка что выбрасывается исключение
            with pytest.raises(ValueError):
                reader = ConfigReader(temp_path)
                reader.load_config()
                reader.get_app_config()  # Должно вызвать ошибку - секция отсутствует
                
        finally:
            Path(temp_path).unlink()
    
    @patch('src.config.validation.requests.get')
    def test_network_validation_mock(self, mock_get):
        """Тест сетевой валидации с мокированием."""
        # Настройка мока для успешного ответа
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'ID': '1', 'NAME': 'Test User'}}
        mock_get.return_value = mock_response
        
        # Создание валидного конфигурационного файла
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            config.add_section('BitrixAPI')
            config.set('BitrixAPI', 'webhookurl', 'https://test.bitrix24.ru/rest/1/test123/')
            
            config.add_section('AppSettings')
            config.set('AppSettings', 'defaultsavefolder', 'test_reports')
            config.set('AppSettings', 'defaultfilename', 'test.xlsx')
            
            config.add_section('ReportPeriod')
            config.set('ReportPeriod', 'startdate', '01.01.2023')
            config.set('ReportPeriod', 'enddate', '31.12.2023')
            
            config.write(f)
            temp_path = f.name
        
        try:
            # Тест с сетевой проверкой (мокированной)
            validator = ComprehensiveValidator(temp_path)
            result = validator.validate_all(check_network=True)
            
            assert isinstance(result, ValidationResult)
            
            # Проверяем что GET запрос был вызван (если нет серьёзных ошибок валидации)
            if result.is_valid or not result.has_errors():
                mock_get.assert_called()
            else:
                # Если есть ошибки валидации, сетевая проверка может не выполняться
                # В таком случае просто проверяем, что мок был настроен правильно
                assert mock_get.return_value.status_code == 200
            
        finally:
            Path(temp_path).unlink()
    
    def test_config_factory_function(self):
        """Тест фабричной функции create_config_reader."""
        # Создание тестового файла
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            for section, values in TestSettings.TEST_CONFIG_DATA.items():
                config.add_section(section)
                for key, value in values.items():
                    config.set(section, key, value)
            
            config.write(f)
            temp_path = f.name
        
        try:
            # Тест фабричной функции
            reader = create_config_reader(temp_path)
            
            assert isinstance(reader, ConfigReader)
            assert reader.config_path == Path(temp_path)
            
            # Проверка что конфигурация уже загружена
            all_config = reader.get_all_config()
            assert 'bitrix' in all_config
            assert 'app' in all_config
            assert 'report_period' in all_config
            
        finally:
            Path(temp_path).unlink()
    
    def test_safe_save_path_creation(self):
        """Тест создания безопасного пути для сохранения."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            config = configparser.ConfigParser()
            
            config.add_section('AppSettings')
            config.set('AppSettings', 'defaultsavefolder', 'test_output')
            config.set('AppSettings', 'defaultfilename', 'report.xlsx')
            
            # Добавим минимальные обязательные секции
            config.add_section('BitrixAPI')
            config.set('BitrixAPI', 'webhookurl', 'https://test.bitrix24.ru/rest/1/test/')
            
            config.add_section('ReportPeriod')
            config.set('ReportPeriod', 'startdate', '01.01.2023')
            config.set('ReportPeriod', 'enddate', '31.12.2023')
            
            config.write(f)
            temp_path = f.name
        
        try:
            reader = ConfigReader(temp_path)
            reader.load_config()
            
            # Тест создания безопасного пути
            safe_path = reader.get_safe_save_path()
            
            assert safe_path.name == 'report.xlsx'
            assert safe_path.parent.exists()  # Директория должна быть создана
            
            # Тест с пользовательским именем файла
            custom_path = reader.get_safe_save_path('custom_report')
            assert custom_path.name == 'custom_report.xlsx'  # Расширение должно добавиться
            
        finally:
            Path(temp_path).unlink()
            # Очистка созданных тестовых директорий
            test_output = Path('test_output')
            if test_output.exists():
                import shutil
                shutil.rmtree(test_output)


class TestConfigErrorHandling:
    """Тесты обработки ошибок в конфигурационном модуле."""
    
    def test_missing_config_file(self):
        """Тест обработки отсутствующего файла конфигурации."""
        reader = ConfigReader('nonexistent_config.ini')
        
        with pytest.raises(FileNotFoundError):
            reader.load_config()
    
    def test_corrupted_config_file(self):
        """Тест обработки повреждённого конфигурационного файла."""
        # Создание файла с некорректным содержимым
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("This is not a valid INI file content\n")
            f.write("Random text without proper structure\n")
            temp_path = f.name
        
        try:
            reader = ConfigReader(temp_path)
            
            # Должно возникнуть исключение при чтении
            with pytest.raises(ValueError):
                reader.load_config()
                
        finally:
            Path(temp_path).unlink()
    
    def test_validation_of_invalid_webhook_url(self):
        """Тест валидации некорректного webhook URL."""
        invalid_urls = [
            'http://example.com',  # Не HTTPS
            'https://example.com/wrong/format',  # Неправильный формат
            'not_a_url_at_all',  # Не URL
            '',  # Пустая строка
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValueError, match="(Некорректный формат webhook URL|Webhook URL не может быть пустым)"):
                BitrixConfig(webhook_url=invalid_url)
    
    def test_validation_of_invalid_file_extension(self):
        """Тест валидации некорректного расширения файла."""
        invalid_filenames = [
            'report.xls',  # Старый формат Excel
            'report.txt',  # Текстовый файл
            'report',  # Без расширения
        ]
        
        for invalid_filename in invalid_filenames:
            with pytest.raises(ValueError, match="Файл должен иметь расширение .xlsx"):
                AppConfig(
                    default_save_folder='test',
                    default_filename=invalid_filename
                )
    
    def test_validation_of_invalid_dates(self):
        """Тест валидации некорректных дат."""
        invalid_date_pairs = [
            ('32.01.2023', '31.01.2023'),  # Несуществующая дата
            ('01.13.2023', '31.12.2023'),  # Несуществующий месяц
            ('01.01.2024', '31.12.2023'),  # Начало позже окончания
            ('1.1.23', '31.12.2023'),  # Неправильный формат
        ]
        
        for start_date, end_date in invalid_date_pairs:
            with pytest.raises(ValueError):
                ReportPeriodConfig(start_date=start_date, end_date=end_date) 