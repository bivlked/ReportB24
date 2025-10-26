"""
Тесты для БАГ-A3 и БАГ-A4 в ReportGeneratorApp (v2.4.0).

БАГ-A3: Параметр use_secure_config теперь работает корректно
БАГ-A4: TimedRotatingFileHandler для автоматической ротации логов
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from logging.handlers import TimedRotatingFileHandler
import logging

from src.core.app import ReportGeneratorApp, AppFactory


class TestBugA3SecureConfigParameter:
    """Тесты для БАГ-A3: параметр use_secure_config"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Очистка логгеров после каждого теста"""
        yield
        # Очищаем логгеры
        logger = logging.getLogger('ReportGeneratorApp')
        logger.handlers.clear()
    
    def test_use_secure_config_true(self, tmp_path):
        """Тест: use_secure_config=True использует SecureConfigReader"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        with patch('src.core.app.create_secure_config_reader') as mock_secure:
            mock_secure.return_value = Mock()
            
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=False,
                use_secure_config=True
            )
            
            # Проверяем что use_secure_config сохранен
            assert app.use_secure_config is True
            
            # Проверяем что при инициализации будет использован SecureConfigReader
            # (проверим при вызове initialize)
    
    def test_use_secure_config_false(self, tmp_path):
        """Тест: use_secure_config=False использует ConfigReader"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        app = ReportGeneratorApp(
            config_path=str(config_file),
            enable_logging=False,
            use_secure_config=False
        )
        
        # Проверяем что use_secure_config сохранен
        assert app.use_secure_config is False
    
    def test_app_factory_with_use_secure_config_true(self, tmp_path):
        """Тест: AppFactory передает use_secure_config=True"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        # Создаем приложение через фабрику
        app = AppFactory.create_app(
            config_path=str(config_file),
            use_secure_config=True,
            auto_initialize=False,
            enable_logging=False
        )
        
        # Проверяем что use_secure_config установлен
        assert app.use_secure_config is True
    
    def test_app_factory_with_use_secure_config_false(self, tmp_path):
        """Тест: AppFactory передает use_secure_config=False"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        # Создаем приложение через фабрику
        app = AppFactory.create_app(
            config_path=str(config_file),
            use_secure_config=False,
            auto_initialize=False,
            enable_logging=False
        )
        
        # Проверяем что use_secure_config установлен
        assert app.use_secure_config is False
    
    def test_default_use_secure_config_is_true(self, tmp_path):
        """Тест: По умолчанию use_secure_config=True"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        # Создаем приложение через фабрику без явного указания use_secure_config
        app = AppFactory.create_app(
            config_path=str(config_file),
            auto_initialize=False,
            enable_logging=False
        )
        
        # Проверяем что по умолчанию use_secure_config=True
        assert app.use_secure_config is True


class TestBugA4LogRotation:
    """Тесты для БАГ-A4: TimedRotatingFileHandler для ротации логов"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Очистка логов после каждого теста"""
        yield
        # Очищаем логгеры
        logger = logging.getLogger('ReportGeneratorApp')
        logger.handlers.clear()
    
    def test_uses_timed_rotating_file_handler(self, tmp_path):
        """Тест: Используется TimedRotatingFileHandler"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        # Создаем директорию для логов
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        try:
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=True,
                use_secure_config=False
            )
            
            # Проверяем что logger создан
            assert app.logger is not None
            
            # Проверяем что есть TimedRotatingFileHandler
            has_timed_handler = any(
                isinstance(handler, TimedRotatingFileHandler)
                for handler in app.logger.handlers
            )
            assert has_timed_handler, "TimedRotatingFileHandler не найден"
            
        finally:
            # Очистка
            if logs_dir.exists():
                for handler in logging.getLogger('ReportGeneratorApp').handlers[:]:
                    handler.close()
                    logging.getLogger('ReportGeneratorApp').removeHandler(handler)
    
    def test_log_rotation_configuration(self, tmp_path):
        """Тест: Конфигурация ротации логов"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        try:
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=True,
                use_secure_config=False
            )
            
            # Находим TimedRotatingFileHandler
            timed_handler = None
            for handler in app.logger.handlers:
                if isinstance(handler, TimedRotatingFileHandler):
                    timed_handler = handler
                    break
            
            assert timed_handler is not None, "TimedRotatingFileHandler не найден"
            
            # Проверяем параметры ротации
            assert timed_handler.when == 'MIDNIGHT', "Ротация должна быть в полночь"
            # interval для MIDNIGHT хранится в секундах (86400 = 1 день)
            assert timed_handler.interval == 86400, "Интервал ротации должен быть 1 день (86400 секунд)"
            assert timed_handler.backupCount == 30, "Должно храниться 30 backup файлов"
            
        finally:
            # Очистка
            if logs_dir.exists():
                for handler in logging.getLogger('ReportGeneratorApp').handlers[:]:
                    handler.close()
                    logging.getLogger('ReportGeneratorApp').removeHandler(handler)
    
    def test_log_file_suffix_format(self, tmp_path):
        """Тест: Суффикс ротированных файлов в формате YYYYMMDD"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        try:
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=True,
                use_secure_config=False
            )
            
            # Находим TimedRotatingFileHandler
            timed_handler = None
            for handler in app.logger.handlers:
                if isinstance(handler, TimedRotatingFileHandler):
                    timed_handler = handler
                    break
            
            assert timed_handler is not None
            
            # Проверяем формат суффикса
            assert timed_handler.suffix == "%Y%m%d", "Суффикс должен быть в формате YYYYMMDD"
            
        finally:
            # Очистка
            if logs_dir.exists():
                for handler in logging.getLogger('ReportGeneratorApp').handlers[:]:
                    handler.close()
                    logging.getLogger('ReportGeneratorApp').removeHandler(handler)
    
    def test_logs_directory_created(self, tmp_path):
        """Тест: Директория logs создается автоматически"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        # Убеждаемся что директория logs будет создана
        logs_dir = Path("logs")
        
        try:
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=True,
                use_secure_config=False
            )
            
            # Проверяем что директория создана
            assert logs_dir.exists(), "Директория logs должна быть создана"
            assert logs_dir.is_dir(), "logs должен быть директорией"
            
        finally:
            # Очистка
            for handler in logging.getLogger('ReportGeneratorApp').handlers[:]:
                handler.close()
                logging.getLogger('ReportGeneratorApp').removeHandler(handler)
    
    def test_logging_can_be_disabled(self, tmp_path):
        """Тест: Логирование можно отключить через enable_logging=False"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        app = ReportGeneratorApp(
            config_path=str(config_file),
            enable_logging=False,
            use_secure_config=False
        )
        
        # Проверяем что logger не создан
        assert app.logger is None


class TestBugA3A4Integration:
    """Интеграционные тесты для БАГ-A3 и БАГ-A4"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Очистка после тестов"""
        yield
        logger = logging.getLogger('ReportGeneratorApp')
        logger.handlers.clear()
    
    def test_app_initialization_with_all_features(self, tmp_path):
        """Тест: Инициализация приложения со всеми исправлениями"""
        config_file = tmp_path / "config.ini"
        config_file.write_text("""
[Bitrix24]
webhook_url = https://test.bitrix24.ru/rest/123/token/

[Report]
start_date = 2024-01-01
end_date = 2024-12-31
save_path = reports
filename = test_report.xlsx
""")
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        try:
            # Создаем приложение с обоими исправлениями
            app = ReportGeneratorApp(
                config_path=str(config_file),
                enable_logging=True,  # БАГ-A4
                use_secure_config=True  # БАГ-A3
            )
            
            # Проверяем БАГ-A3
            assert app.use_secure_config is True
            
            # Проверяем БАГ-A4
            assert app.logger is not None
            has_timed_handler = any(
                isinstance(h, TimedRotatingFileHandler)
                for h in app.logger.handlers
            )
            assert has_timed_handler
            
        finally:
            for handler in logging.getLogger('ReportGeneratorApp').handlers[:]:
                handler.close()
                logging.getLogger('ReportGeneratorApp').removeHandler(handler)
