"""
Главный класс приложения.

Точка входа для всей системы генерации отчётов Bitrix24.
Обеспечивает инициализацию, координацию всех компонентов
и предоставляет высокоуровневый интерфейс.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..config.config_reader import ConfigReader, create_secure_config_reader
from ..config.settings import APP_NAME, APP_VERSION, get_runtime_info
from ..config.validation import validate_system
from ..bitrix24_client.client import Bitrix24Client
from ..data_processor.data_processor import DataProcessor
from ..excel_generator.generator import ExcelReportGenerator
from .error_handler import get_error_handler, handle_error, generate_error_report
from .workflow import WorkflowOrchestrator


@dataclass
class AppStatus:
    """Статус приложения."""

    is_initialized: bool = False
    is_configured: bool = False
    is_validated: bool = False
    last_operation: Optional[str] = None
    last_operation_time: Optional[datetime] = None
    errors_count: int = 0

    def update_operation(self, operation: str) -> None:
        """Обновляет информацию о последней операции."""
        self.last_operation = operation
        self.last_operation_time = datetime.now()


class ReportGeneratorApp:
    """
    Главный класс приложения для генерации отчётов Bitrix24.

    Обеспечивает полный жизненный цикл приложения от инициализации
    до генерации отчётов с централизованной обработкой ошибок.
    """

    def __init__(
        self,
        config_path: str = "config.ini",
        enable_logging: bool = True,
        use_secure_config: bool = True,
    ):
        """
        Инициализация приложения.

        Args:
            config_path: Путь к файлу конфигурации
            enable_logging: Включить логирование
            use_secure_config: Использовать SecureConfigReader (True) или ConfigReader (False)
        """
        self.config_path = config_path
        self.enable_logging = enable_logging
        self.use_secure_config = use_secure_config
        self.status = AppStatus()

        # Компоненты системы (ConfigReader или SecureConfigReader)
        self.config_reader = None
        self.bitrix_client: Optional[Bitrix24Client] = None
        self.data_processor: Optional[DataProcessor] = None
        self.excel_generator: Optional[ExcelReportGenerator] = None
        self.workflow_orchestrator: Optional[WorkflowOrchestrator] = None

        # Обработчик ошибок
        self.error_handler = get_error_handler()

        # Логгер
        self.logger = self._setup_logging() if enable_logging else None

        self._log_info(f"Инициализирован {APP_NAME} v{APP_VERSION}")

    def _setup_logging(self) -> logging.Logger:
        """
        Настраивает систему логирования с автоматической ротацией (v2.4.0).

        Использует TimedRotatingFileHandler для автоматической ротации
        логов в полночь. Старые логи сохраняются с суффиксом даты.
        Автоматически удаляет логи старше 30 дней.

        Returns:
            logging.Logger: Настроенный логгер
        """
        # Создание директории для логов
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Настройка логгера
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        # Обработчики добавляются только один раз
        if not logger.handlers:
            # TimedRotatingFileHandler для автоматической ротации
            log_file = log_dir / "app.log"
            file_handler = TimedRotatingFileHandler(
                filename=str(log_file),
                when="midnight",  # Ротация в полночь
                interval=1,  # Каждый день
                backupCount=30,  # Хранить 30 дней
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)

            # Суффикс для ротированных файлов: app.log.20251024
            file_handler.suffix = "%Y%m%d"

            # Обработчик для консоли
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)

            # Единый форматтер
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Добавление обработчиков
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def _log_info(self, message: str) -> None:
        """Логирует информационное сообщение."""
        if self.logger:
            self.logger.info(message)

    def _log_error(self, message: str) -> None:
        """Логирует ошибку."""
        if self.logger:
            self.logger.error(message)

    def initialize(self) -> bool:
        """
        Инициализирует все компоненты приложения.

        Returns:
            bool: True если инициализация прошла успешно
        """
        try:
            self.status.update_operation("Инициализация приложения")
            self._log_info("Начало инициализации приложения...")

            # 1. Валидация системы
            self._log_info("Проверка системных требований...")
            is_valid, validation_report = validate_system(
                self.config_path, check_network=False
            )

            if not is_valid:
                self._log_error(
                    f"Системные требования не выполнены:\n{validation_report}"
                )
                return False

            self.status.is_validated = True
            self._log_info("Системные требования проверены ✓")

            # 2. Загрузка конфигурации (🔧 БАГ-A3: условный выбор ConfigReader)
            if self.use_secure_config:
                self._log_info("Загрузка конфигурации с SecureConfigReader...")
                self.config_reader = create_secure_config_reader(self.config_path)
                self._log_info("Конфигурация загружена с поддержкой .env ✓")
            else:
                self._log_info("Загрузка конфигурации с ConfigReader...")
                self.config_reader = ConfigReader(self.config_path)
                self.config_reader.load_config()  # 🔥 БАГ-1 FIX: явная загрузка конфигурации
                self._log_info("Конфигурация загружена ✓")

            self.status.is_configured = True

            # 3. Инициализация компонентов
            self._log_info("Инициализация компонентов...")

            # Bitrix24 клиент
            bitrix_config = self.config_reader.get_bitrix_config()
            self.bitrix_client = Bitrix24Client(bitrix_config.webhook_url)
            self._log_info("Bitrix24 клиент инициализирован ✓")

            # Обработчик данных
            self.data_processor = DataProcessor()
            self._log_info("Обработчик данных инициализирован ✓")

            # Генератор Excel
            self.excel_generator = ExcelReportGenerator()
            self._log_info("Генератор Excel инициализирован ✓")

            # Оркестратор workflow
            self.workflow_orchestrator = WorkflowOrchestrator(
                bitrix_client=self.bitrix_client,
                data_processor=self.data_processor,
                excel_generator=self.excel_generator,
                config_reader=self.config_reader,
            )
            self._log_info("Оркестратор workflow инициализирован ✓")

            self.status.is_initialized = True
            self._log_info("Инициализация завершена успешно!")

            return True

        except Exception as e:
            handle_error(e, "initialize", "ReportGeneratorApp")
            self._log_error(f"Ошибка инициализации: {e}")
            return False

    def generate_report(self, custom_filename: Optional[str] = None) -> bool:
        """
        Генерирует отчёт по настройкам из конфигурации.

        Args:
            custom_filename: Пользовательское имя файла (опционально)

        Returns:
            bool: True если отчёт сгенерирован успешно
        """
        try:
            if not self.status.is_initialized:
                raise ValueError(
                    "Приложение не инициализировано. Вызовите initialize() сначала."
                )

            self.status.update_operation("Генерация отчёта")
            self._log_info("Начало генерации отчёта...")

            # Получение пути для сохранения
            save_path = self.config_reader.get_safe_save_path(custom_filename)
            self._log_info(f"Файл будет сохранён: {save_path}")

            # Запуск workflow
            result = self.workflow_orchestrator.execute_full_workflow(save_path)

            if result.success:
                self._log_info(f"Отчёт успешно сгенерирован: {save_path}")
                self._log_info(f"Обработано записей: {result.records_processed}")
                return True
            else:
                self._log_error(f"Ошибка генерации отчёта: {result.error_message}")
                return False

        except Exception as e:
            handle_error(e, "generate_report", "ReportGeneratorApp")
            self._log_error(f"Ошибка генерации отчёта: {e}")
            return False

    def validate_configuration(self) -> bool:
        """
        Проводит полную валидацию конфигурации включая сетевые проверки.

        Returns:
            bool: True если конфигурация валидна
        """
        try:
            self.status.update_operation("Валидация конфигурации")
            self._log_info("Начало валидации конфигурации...")

            is_valid, validation_report = validate_system(
                self.config_path, check_network=True
            )

            if is_valid:
                self._log_info("Конфигурация валидна ✓")
                self._log_info(validation_report)
            else:
                self._log_error("Ошибки в конфигурации:")
                self._log_error(validation_report)

            return is_valid

        except Exception as e:
            handle_error(e, "validate_configuration", "ReportGeneratorApp")
            self._log_error(f"Ошибка валидации: {e}")
            return False

    def test_api_connection(self) -> bool:
        """
        Тестирует подключение к Bitrix24 API.

        Returns:
            bool: True если подключение успешно
        """
        try:
            if not self.bitrix_client:
                raise ValueError("Bitrix24 клиент не инициализирован")

            self.status.update_operation("Тестирование API подключения")
            self._log_info("Тестирование подключения к Bitrix24...")

            # Попытка получения информации о пользователе
            stats = self.bitrix_client.get_stats()

            self._log_info("Подключение к Bitrix24 успешно ✓")
            self._log_info(f"Статистика API: {stats}")

            return True

        except Exception as e:
            handle_error(e, "test_api_connection", "ReportGeneratorApp")
            self._log_error(f"Ошибка подключения к API: {e}")
            return False

    def get_app_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о приложении и его состоянии.

        Returns:
            Dict: Информация о приложении
        """
        runtime_info = get_runtime_info()
        error_summary = self.error_handler.get_error_summary()

        return {
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "status": {
                "is_initialized": self.status.is_initialized,
                "is_configured": self.status.is_configured,
                "is_validated": self.status.is_validated,
                "last_operation": self.status.last_operation,
                "last_operation_time": (
                    self.status.last_operation_time.isoformat()
                    if self.status.last_operation_time
                    else None
                ),
                "errors_count": error_summary.get("total_errors", 0),
            },
            "configuration": {
                "config_path": self.config_path,
                "logging_enabled": self.enable_logging,
            },
            "runtime": runtime_info,
            "components": {
                "config_reader": self.config_reader is not None,
                "bitrix_client": self.bitrix_client is not None,
                "data_processor": self.data_processor is not None,
                "excel_generator": self.excel_generator is not None,
                "workflow_orchestrator": self.workflow_orchestrator is not None,
            },
        }

    def get_error_report(self) -> str:
        """
        Возвращает отчёт об ошибках.

        Returns:
            str: Текстовый отчёт об ошибках
        """
        return generate_error_report()

    def shutdown(self) -> None:
        """Корректно завершает работу приложения."""
        try:
            self.status.update_operation("Завершение работы")
            self._log_info("Завершение работы приложения...")

            # Закрытие соединений
            if self.bitrix_client:
                self.bitrix_client.close()
                self._log_info("Bitrix24 клиент закрыт ✓")

            # Очистка ресурсов
            if self.workflow_orchestrator:
                self.workflow_orchestrator.cleanup()
                self._log_info("Workflow оркестратор очищен ✓")

            self._log_info("Приложение завершено корректно")

        except Exception as e:
            handle_error(e, "shutdown", "ReportGeneratorApp")
            self._log_error(f"Ошибка при завершении: {e}")

    def __enter__(self):
        """Поддержка context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Корректное завершение при выходе из context manager."""
        self.shutdown()

        # Обработка исключения если было
        if exc_type:
            handle_error(exc_val, "__exit__", "ReportGeneratorApp")
            return False  # Не подавляем исключение


class AppFactory:
    """Фабрика для создания экземпляров приложения."""

    @staticmethod
    def create_app(
        config_path: str = "config.ini",
        enable_logging: bool = True,
        auto_initialize: bool = True,
        use_secure_config: bool = True,
    ) -> ReportGeneratorApp:
        """
        Создаёт и опционально инициализирует экземпляр приложения.

        Args:
            config_path: Путь к файлу конфигурации
            enable_logging: Включить логирование
            auto_initialize: Автоматически инициализировать компоненты
            use_secure_config: Использовать SecureConfigReader с поддержкой .env (по умолчанию True)

        Returns:
            ReportGeneratorApp: Настроенный экземпляр приложения
        """
        # 🔧 БАГ-A3: Передача use_secure_config в ReportGeneratorApp
        app = ReportGeneratorApp(config_path, enable_logging, use_secure_config)

        if auto_initialize:
            success = app.initialize()
            if not success:
                raise RuntimeError("Не удалось инициализировать приложение")

        return app

    @staticmethod
    def create_for_testing(
        config_data: Optional[Dict[str, Any]] = None,
    ) -> ReportGeneratorApp:
        """
        Создаёт экземпляр приложения для тестирования.

        Args:
            config_data: Тестовые данные конфигурации

        Returns:
            ReportGeneratorApp: Экземпляр для тестирования
        """
        # Создание временного файла конфигурации для тестов
        import tempfile
        import configparser

        if config_data is None:
            from ..config.settings import TestSettings

            config_data = TestSettings.TEST_CONFIG_DATA

        # Создание временного config файла
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            config = configparser.ConfigParser()

            for section, values in config_data.items():
                config.add_section(section)
                for key, value in values.items():
                    config.set(section, key, value)

            config.write(f)
            temp_config_path = f.name

        # Создание приложения с тестовой конфигурацией
        app = ReportGeneratorApp(temp_config_path, enable_logging=False)

        return app


def main() -> None:
    """
    Главная функция для запуска приложения из командной строки.
    """
    try:
        print(f"🚀 Запуск {APP_NAME} v{APP_VERSION}")
        print("=" * 50)

        # Создание и инициализация приложения
        with AppFactory.create_app() as app:

            # Вывод информации о приложении
            app_info = app.get_app_info()
            print(f"✅ Приложение инициализировано")
            print(f"📁 Конфигурация: {app_info['configuration']['config_path']}")
            print(f"🐍 Python: {app_info['runtime']['python_version']}")
            print("")

            # Валидация конфигурации
            if not app.validate_configuration():
                print("❌ Ошибки в конфигурации. Проверьте настройки.")
                sys.exit(1)

            # Тестирование API
            if not app.test_api_connection():
                print("❌ Не удалось подключиться к Bitrix24 API.")
                sys.exit(1)

            # Генерация отчёта
            print("📊 Генерация отчёта...")
            if app.generate_report():
                print("✅ Отчёт успешно сгенерирован!")
            else:
                print("❌ Ошибка генерации отчёта.")
                error_report = app.get_error_report()
                print("\n" + error_report)
                sys.exit(1)

        print("\n🎉 Работа завершена успешно!")

    except KeyboardInterrupt:
        print("\n⏹️  Работа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        handle_error(e, "main", "main_function")
        sys.exit(1)


if __name__ == "__main__":
    main()
