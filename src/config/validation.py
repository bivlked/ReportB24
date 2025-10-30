"""
Модуль валидации конфигурации и системных требований.

Обеспечивает комплексную проверку корректности настроек,
доступности ресурсов и готовности системы к работе.
"""

import os
import sys
import re
import requests
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass
import logging

from .config_reader import (
    SecureConfigReader,
    BitrixConfig,
    AppConfig,
    ReportPeriodConfig,
)
from .settings import ValidationSettings


@dataclass
class ValidationResult:
    """Результат валидации."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def add_error(self, error: str) -> None:
        """Добавляет ошибку."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Добавляет предупреждение."""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Проверяет наличие ошибок."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Проверяет наличие предупреждений."""
        return len(self.warnings) > 0


class SystemValidator:
    """Валидатор системных требований."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_python_version(self) -> ValidationResult:
        """
        Проверяет версию Python.

        Returns:
            ValidationResult: Результат проверки версии Python
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Минимальные требования
        min_version = (3, 12)
        current_version = sys.version_info[:2]

        if current_version < min_version:
            result.add_error(
                f"Требуется Python {min_version[0]}.{min_version[1]}+, "
                f"текущая версия: {current_version[0]}.{current_version[1]}"
            )

        # Проверка виртуального окружения
        if not hasattr(sys, "real_prefix") and not (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        ):
            result.add_warning(
                "Рекомендуется использовать виртуальное окружение Python"
            )

        return result

    def validate_dependencies(self) -> ValidationResult:
        """
        Проверяет установленные зависимости.

        Returns:
            ValidationResult: Результат проверки зависимостей
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        required_packages = {
            "requests": "2.31.0",
            "openpyxl": "3.1.2",
            "dotenv": "1.0.0",  # python-dotenv package
        }

        for package, min_version in required_packages.items():
            try:
                __import__(package)
            except ImportError:
                result.add_error(
                    f"Отсутствует обязательный пакет: {package}>={min_version}"
                )

        return result

    def validate_file_permissions(self, paths: List[Path]) -> ValidationResult:
        """
        Проверяет права доступа к файлам и директориям.

        Args:
            paths: Список путей для проверки

        Returns:
            ValidationResult: Результат проверки прав доступа
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        for path in paths:
            if path.exists():
                # Проверка прав чтения
                if not os.access(path, os.R_OK):
                    result.add_error(f"Нет прав на чтение: {path}")

                # Для директорий проверяем права записи
                if path.is_dir() and not os.access(path, os.W_OK):
                    result.add_error(f"Нет прав на запись в директорию: {path}")
            else:
                # Проверяем возможность создания файла/директории
                parent = path.parent
                if parent.exists() and not os.access(parent, os.W_OK):
                    result.add_error(f"Нет прав на создание в директории: {parent}")

        return result


class ConfigValidator:
    """Валидатор конфигурации приложения."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_bitrix_config(self, config: BitrixConfig) -> ValidationResult:
        """
        Валидирует конфигурацию Bitrix24.

        Args:
            config: Конфигурация Bitrix24

        Returns:
            ValidationResult: Результат валидации
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Проверка формата webhook URL
        if not re.match(ValidationSettings.PATTERNS["WEBHOOK_URL"], config.webhook_url):
            result.add_error(f"Некорректный формат webhook URL: {config.webhook_url}")

        # Проверка доступности webhook (опционально, может занимать время)
        try:
            # Быстрая проверка доступности домена
            import urllib.parse

            parsed = urllib.parse.urlparse(config.webhook_url)
            if not parsed.hostname:
                result.add_error("Не удалось извлечь hostname из webhook URL")
        except Exception as e:
            result.add_warning(f"Не удалось проверить webhook URL: {e}")

        return result

    def validate_app_config(self, config: AppConfig) -> ValidationResult:
        """
        Валидирует конфигурацию приложения.

        Args:
            config: Конфигурация приложения

        Returns:
            ValidationResult: Результат валидации
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Проверка папки сохранения
        save_path = Path(config.default_save_folder)

        if not save_path.exists():
            try:
                save_path.mkdir(parents=True, exist_ok=True)
                result.add_warning(f"Создана директория для сохранения: {save_path}")
            except PermissionError:
                result.add_error(f"Нет прав на создание директории: {save_path}")
            except Exception as e:
                result.add_error(f"Ошибка создания директории {save_path}: {e}")

        # Проверка прав записи
        if save_path.exists() and not os.access(save_path, os.W_OK):
            result.add_error(f"Нет прав на запись в директорию: {save_path}")

        # Проверка расширения файла
        if not config.default_filename.endswith(".xlsx"):
            result.add_error("Файл должен иметь расширение .xlsx")

        return result

    def validate_report_period_config(
        self, config: ReportPeriodConfig
    ) -> ValidationResult:
        """
        Валидирует конфигурацию периода отчёта.

        Args:
            config: Конфигурация периода отчёта

        Returns:
            ValidationResult: Результат валидации
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Проверка формата дат
        date_pattern = ValidationSettings.PATTERNS["RUSSIAN_DATE"]

        if not re.match(date_pattern, config.start_date):
            result.add_error(f"Некорректный формат даты начала: {config.start_date}")

        if not re.match(date_pattern, config.end_date):
            result.add_error(f"Некорректный формат даты окончания: {config.end_date}")

        # Проверка логичности дат (если формат корректен)
        if not result.has_errors():
            try:
                from datetime import datetime

                start_dt = datetime.strptime(config.start_date, "%d.%m.%Y")
                end_dt = datetime.strptime(config.end_date, "%d.%m.%Y")

                if start_dt >= end_dt:
                    result.add_error("Дата начала должна быть раньше даты окончания")

                # Проверка разумности диапазона
                from datetime import timedelta

                if (end_dt - start_dt) > timedelta(days=365):
                    result.add_warning(
                        "Период отчёта больше года, это может замедлить обработку"
                    )

            except ValueError as e:
                result.add_error(f"Ошибка парсинга дат: {e}")

        return result


class NetworkValidator:
    """Валидатор сетевых подключений."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_bitrix_connection(
        self, webhook_url: str, timeout: int = 10
    ) -> ValidationResult:
        """
        Проверяет подключение к Bitrix24.

        Args:
            webhook_url: URL webhook для проверки
            timeout: Таймаут подключения в секундах

        Returns:
            ValidationResult: Результат проверки подключения
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        try:
            # Пробуем простой метод для проверки доступности API
            test_method = webhook_url + "profile"

            response = requests.get(test_method, timeout=timeout)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "error" in data:
                        # API отвечает, но есть ошибка аутентификации/авторизации
                        if data["error"] == "INVALID_GRANT":
                            result.add_error(
                                "Недействительный webhook. Проверьте корректность URL"
                            )
                        else:
                            result.add_warning(
                                f"API ответил с ошибкой: {data.get('error_description', data['error'])}"
                            )
                    else:
                        # Успешное подключение
                        self.logger.info("Подключение к Bitrix24 API успешно проверено")
                except ValueError:
                    result.add_warning("API ответил некорректным JSON")
            else:
                result.add_error(f"API вернул статус {response.status_code}")

        except requests.exceptions.Timeout:
            result.add_error(f"Таймаут подключения к Bitrix24 (>{timeout}с)")
        except requests.exceptions.ConnectionError:
            result.add_error(
                "Не удалось подключиться к Bitrix24. Проверьте интернет-соединение"
            )
        except requests.exceptions.RequestException as e:
            result.add_error(f"Ошибка HTTP запроса: {e}")
        except Exception as e:
            result.add_error(f"Неожиданная ошибка при проверке подключения: {e}")

        return result


class ComprehensiveValidator:
    """Комплексный валидатор всех аспектов системы."""

    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path
        self.system_validator = SystemValidator()
        self.config_validator = ConfigValidator()
        self.network_validator = NetworkValidator()
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_all(self, check_network: bool = True) -> ValidationResult:
        """
        Проводит полную валидацию системы.

        Args:
            check_network: Проверять ли сетевые подключения

        Returns:
            ValidationResult: Агрегированный результат всех проверок
        """
        overall_result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # 1. Проверка системных требований
        self.logger.info("Проверка системных требований...")

        python_result = self.system_validator.validate_python_version()
        overall_result.errors.extend(python_result.errors)
        overall_result.warnings.extend(python_result.warnings)

        deps_result = self.system_validator.validate_dependencies()
        overall_result.errors.extend(deps_result.errors)
        overall_result.warnings.extend(deps_result.warnings)

        # 2. Проверка прав доступа
        self.logger.info("Проверка прав доступа...")
        paths_to_check = [Path(self.config_path), Path("logs"), Path("temp")]

        perms_result = self.system_validator.validate_file_permissions(paths_to_check)
        overall_result.errors.extend(perms_result.errors)
        overall_result.warnings.extend(perms_result.warnings)

        # 3. Проверка конфигурации
        self.logger.info("Проверка конфигурации...")
        try:
            config_reader = SecureConfigReader(self.config_path)
            config_reader.load_config()

            # Проверка Bitrix конфигурации
            bitrix_config = config_reader.get_bitrix_config()
            bitrix_result = self.config_validator.validate_bitrix_config(bitrix_config)
            overall_result.errors.extend(bitrix_result.errors)
            overall_result.warnings.extend(bitrix_result.warnings)

            # Проверка конфигурации приложения
            app_config = config_reader.get_app_config()
            app_result = self.config_validator.validate_app_config(app_config)
            overall_result.errors.extend(app_result.errors)
            overall_result.warnings.extend(app_result.warnings)

            # Проверка конфигурации периода
            period_config = config_reader.get_report_period_config()
            period_result = self.config_validator.validate_report_period_config(
                period_config
            )
            overall_result.errors.extend(period_result.errors)
            overall_result.warnings.extend(period_result.warnings)

            # 4. Проверка сетевых подключений (опционально)
            if check_network and not overall_result.has_errors():
                self.logger.info("Проверка сетевых подключений...")
                network_result = self.network_validator.validate_bitrix_connection(
                    bitrix_config.webhook_url
                )
                overall_result.errors.extend(network_result.errors)
                overall_result.warnings.extend(network_result.warnings)

        except Exception as e:
            overall_result.add_error(f"Ошибка при проверке конфигурации: {e}")

        # Финальная оценка
        overall_result.is_valid = not overall_result.has_errors()

        return overall_result

    def get_validation_report(self, result: ValidationResult) -> str:
        """
        Формирует текстовый отчёт о валидации.

        Args:
            result: Результат валидации

        Returns:
            str: Форматированный отчёт
        """
        report_lines = []

        if result.is_valid:
            report_lines.append("✅ ВАЛИДАЦИЯ ПРОЙДЕНА УСПЕШНО")
        else:
            report_lines.append("❌ ВАЛИДАЦИЯ НЕ ПРОЙДЕНА")

        if result.has_errors():
            report_lines.append("\n🚨 ОШИБКИ:")
            for i, error in enumerate(result.errors, 1):
                report_lines.append(f"  {i}. {error}")

        if result.has_warnings():
            report_lines.append("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for i, warning in enumerate(result.warnings, 1):
                report_lines.append(f"  {i}. {warning}")

        if result.is_valid:
            report_lines.append("\n🎉 Система готова к работе!")
        else:
            report_lines.append("\n🔧 Устраните ошибки перед запуском приложения.")

        return "\n".join(report_lines)


def validate_system(
    config_path: str = "config.ini", check_network: bool = True
) -> Tuple[bool, str]:
    """
    Удобная функция для быстрой валидации системы.

    Args:
        config_path: Путь к файлу конфигурации
        check_network: Проверять ли сетевые подключения

    Returns:
        Tuple[bool, str]: (успешность валидации, отчёт о валидации)
    """
    validator = ComprehensiveValidator(config_path)
    result = validator.validate_all(check_network)
    report = validator.get_validation_report(result)

    return result.is_valid, report
