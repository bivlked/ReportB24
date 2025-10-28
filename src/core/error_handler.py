"""
Модуль централизованной обработки ошибок.

Обеспечивает единообразную обработку, логирование и представление
ошибок во всём приложении с поддержкой детализированной отчётности.
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import json

from ..bitrix24_client.exceptions import (
    Bitrix24APIError,
    RateLimitError,
    AuthenticationError,
    ServerError,
    NetworkError,
    BadRequestError,
    NotFoundError,
    TimeoutError,
)


@dataclass
class ErrorContext:
    """Контекст ошибки для детального анализа."""

    timestamp: datetime
    operation: str
    component: str
    error_type: str
    error_message: str
    stack_trace: Optional[str]
    additional_data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует контекст ошибки в словарь."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "component": self.component,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "additional_data": self.additional_data,
        }


class ErrorCategories:
    """Категории ошибок для классификации."""

    CONFIGURATION = "configuration"  # Ошибки конфигурации
    API_CONNECTION = "api_connection"  # Ошибки подключения к API
    API_AUTHENTICATION = "api_auth"  # Ошибки аутентификации
    API_RATE_LIMIT = "api_rate_limit"  # Превышение лимитов API
    DATA_VALIDATION = "data_validation"  # Ошибки валидации данных
    DATA_PROCESSING = "data_processing"  # Ошибки обработки данных
    FILE_OPERATIONS = "file_operations"  # Ошибки файловых операций
    EXCEL_GENERATION = "excel_generation"  # Ошибки генерации Excel
    SYSTEM = "system"  # Системные ошибки
    UNKNOWN = "unknown"  # Неизвестные ошибки


class ErrorSeverity:
    """Уровни критичности ошибок."""

    CRITICAL = "critical"  # Критические ошибки, останавливающие работу
    HIGH = "high"  # Серьёзные ошибки, требующие вмешательства
    MEDIUM = "medium"  # Средние ошибки, можно продолжать работу
    LOW = "low"  # Незначительные ошибки, предупреждения


class ErrorHandler:
    """
    Централизованный обработчик ошибок.

    Обеспечивает единообразную обработку всех типов ошибок
    с автоматической классификацией, логированием и reporting.
    """

    def __init__(self, log_errors: bool = True, save_error_reports: bool = True):
        """
        Инициализация обработчика ошибок.

        Args:
            log_errors: Логировать ли ошибки
            save_error_reports: Сохранять ли отчёты об ошибках в файлы
        """
        self.log_errors = log_errors
        self.save_error_reports = save_error_reports
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_history: List[ErrorContext] = []

        # Карта типов ошибок к категориям
        self.error_mapping = {
            # API ошибки
            RateLimitError: (ErrorCategories.API_RATE_LIMIT, ErrorSeverity.HIGH),
            AuthenticationError: (
                ErrorCategories.API_AUTHENTICATION,
                ErrorSeverity.CRITICAL,
            ),
            ServerError: (ErrorCategories.API_CONNECTION, ErrorSeverity.HIGH),
            NetworkError: (ErrorCategories.API_CONNECTION, ErrorSeverity.HIGH),
            BadRequestError: (ErrorCategories.API_CONNECTION, ErrorSeverity.MEDIUM),
            NotFoundError: (ErrorCategories.API_CONNECTION, ErrorSeverity.MEDIUM),
            TimeoutError: (ErrorCategories.API_CONNECTION, ErrorSeverity.HIGH),
            Bitrix24APIError: (ErrorCategories.API_CONNECTION, ErrorSeverity.MEDIUM),
            # Стандартные ошибки Python
            ValueError: (ErrorCategories.DATA_VALIDATION, ErrorSeverity.MEDIUM),
            TypeError: (ErrorCategories.DATA_PROCESSING, ErrorSeverity.MEDIUM),
            KeyError: (ErrorCategories.DATA_PROCESSING, ErrorSeverity.MEDIUM),
            FileNotFoundError: (ErrorCategories.FILE_OPERATIONS, ErrorSeverity.HIGH),
            PermissionError: (ErrorCategories.FILE_OPERATIONS, ErrorSeverity.HIGH),
            ConnectionError: (ErrorCategories.API_CONNECTION, ErrorSeverity.HIGH),
            OSError: (ErrorCategories.SYSTEM, ErrorSeverity.HIGH),
            MemoryError: (ErrorCategories.SYSTEM, ErrorSeverity.CRITICAL),
        }

    def handle_error(
        self,
        error: Exception,
        operation: str,
        component: str = "unknown",
        additional_data: Optional[Dict[str, Any]] = None,
        reraise: bool = False,
    ) -> ErrorContext:
        """
        Обрабатывает ошибку с полным контекстом.

        Args:
            error: Исключение для обработки
            operation: Название операции, в которой произошла ошибка
            component: Компонент, в котором произошла ошибка
            additional_data: Дополнительные данные для контекста
            reraise: Повторно выбросить исключение после обработки

        Returns:
            ErrorContext: Контекст обработанной ошибки

        Raises:
            Exception: Повторно выбрасывает исключение если reraise=True
        """
        # Создание контекста ошибки
        error_context = ErrorContext(
            timestamp=datetime.now(),
            operation=operation,
            component=component,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            additional_data=additional_data or {},
        )

        # Добавление в историю
        self.error_history.append(error_context)

        # Логирование
        if self.log_errors:
            self._log_error(error_context)

        # Сохранение отчёта
        if self.save_error_reports:
            self._save_error_report(error_context)

        # Повторное выбрасывание при необходимости
        # БАГ-2 FIX: Bare raise сохраняет оригинальный стек вызовов
        if reraise:
            raise  # Не raise error! Bare raise сохраняет traceback

        return error_context

    def _log_error(self, context: ErrorContext) -> None:
        """Логирует ошибку с соответствующим уровнем."""
        category, severity = self._classify_error(context.error_type)

        log_message = (
            f"[{context.component}] {context.operation}: "
            f"{context.error_type} - {context.error_message}"
        )

        # Выбор уровня логирования в зависимости от критичности
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
            if context.stack_trace:
                self.logger.critical(f"Stack trace:\n{context.stack_trace}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
            if context.stack_trace:
                self.logger.debug(f"Stack trace:\n{context.stack_trace}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:  # LOW
            self.logger.info(log_message)

    def _classify_error(self, error_type: str) -> tuple:
        """
        Классифицирует ошибку по типу.

        Args:
            error_type: Тип ошибки (имя класса)

        Returns:
            tuple: (категория, уровень критичности)
        """
        # Поиск по точному совпадению типа
        for exc_type, (category, severity) in self.error_mapping.items():
            if exc_type.__name__ == error_type:
                return category, severity

        # Категория по умолчанию
        return ErrorCategories.UNKNOWN, ErrorSeverity.MEDIUM

    def _save_error_report(self, context: ErrorContext) -> None:
        """Сохраняет отчёт об ошибке в файл."""
        try:
            # Создание директории для отчётов
            reports_dir = Path("logs/error_reports")
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Имя файла с timestamp
            timestamp_str = context.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"error_{timestamp_str}_{context.component}.json"
            filepath = reports_dir / filename

            # Сохранение в JSON формате
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Не можем сохранить отчёт - просто логируем
            self.logger.warning(f"Не удалось сохранить отчёт об ошибке: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку по всем обработанным ошибкам.

        Returns:
            Dict: Статистика и сводка ошибок
        """
        if not self.error_history:
            return {"total_errors": 0, "categories": {}, "components": {}}

        # Подсчёт по категориям
        categories = {}
        components = {}
        severity_counts = {}

        for error_ctx in self.error_history:
            category, severity = self._classify_error(error_ctx.error_type)

            # По категориям
            categories[category] = categories.get(category, 0) + 1

            # По компонентам
            components[error_ctx.component] = components.get(error_ctx.component, 0) + 1

            # По уровням критичности
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "categories": categories,
            "components": components,
            "severity_levels": severity_counts,
            "most_recent": (
                self.error_history[-1].to_dict() if self.error_history else None
            ),
            "time_range": (
                {
                    "first_error": self.error_history[0].timestamp.isoformat(),
                    "last_error": self.error_history[-1].timestamp.isoformat(),
                }
                if self.error_history
                else None
            ),
        }

    def clear_error_history(self) -> None:
        """Очищает историю ошибок."""
        self.error_history.clear()
        self.logger.info("История ошибок очищена")

    def get_recent_errors(self, count: int = 10) -> List[ErrorContext]:
        """
        Возвращает последние N ошибок.

        Args:
            count: Количество последних ошибок

        Returns:
            List: Список последних ошибок
        """
        return self.error_history[-count:] if self.error_history else []

    def has_critical_errors(self) -> bool:
        """
        Проверяет наличие критических ошибок.

        Returns:
            bool: True если есть критические ошибки
        """
        for error_ctx in self.error_history:
            _, severity = self._classify_error(error_ctx.error_type)
            if severity == ErrorSeverity.CRITICAL:
                return True
        return False


class ErrorReporter:
    """Генератор отчётов об ошибках."""

    def __init__(self, error_handler: ErrorHandler):
        """
        Инициализация генератора отчётов.

        Args:
            error_handler: Обработчик ошибок для получения данных
        """
        self.error_handler = error_handler

    def generate_summary_report(self) -> str:
        """
        Генерирует текстовый отчёт с сводкой ошибок.

        Returns:
            str: Форматированный отчёт
        """
        summary = self.error_handler.get_error_summary()

        if summary["total_errors"] == 0:
            return "🎉 Ошибок не обнаружено!"

        lines = [
            "📊 ОТЧЁТ ОБ ОШИБКАХ",
            "=" * 50,
            f"Всего ошибок: {summary['total_errors']}",
            "",
        ]

        # По категориям
        if summary["categories"]:
            lines.append("📋 По категориям:")
            for category, count in sorted(summary["categories"].items()):
                lines.append(f"  • {category}: {count}")
            lines.append("")

        # По компонентам
        if summary["components"]:
            lines.append("🔧 По компонентам:")
            for component, count in sorted(summary["components"].items()):
                lines.append(f"  • {component}: {count}")
            lines.append("")

        # По уровням критичности
        if summary["severity_levels"]:
            lines.append("⚠️  По уровням критичности:")
            severity_order = [
                ErrorSeverity.CRITICAL,
                ErrorSeverity.HIGH,
                ErrorSeverity.MEDIUM,
                ErrorSeverity.LOW,
            ]
            for severity in severity_order:
                if severity in summary["severity_levels"]:
                    count = summary["severity_levels"][severity]
                    emoji = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "⚡",
                        "low": "ℹ️",
                    }.get(severity, "❓")
                    lines.append(f"  {emoji} {severity}: {count}")
            lines.append("")

        # Последняя ошибка
        if summary["most_recent"]:
            recent = summary["most_recent"]
            lines.extend(
                [
                    "🕒 Последняя ошибка:",
                    f"  • Время: {recent['timestamp']}",
                    f"  • Компонент: {recent['component']}",
                    f"  • Операция: {recent['operation']}",
                    f"  • Тип: {recent['error_type']}",
                    f"  • Сообщение: {recent['error_message']}",
                ]
            )

        return "\n".join(lines)

    def generate_detailed_report(self, last_n_errors: int = 5) -> str:
        """
        Генерирует детальный отчёт с последними ошибками.

        Args:
            last_n_errors: Количество последних ошибок для детального отчёта

        Returns:
            str: Детальный отчёт
        """
        recent_errors = self.error_handler.get_recent_errors(last_n_errors)

        if not recent_errors:
            return "🎉 Ошибок не обнаружено!"

        lines = [
            "📋 ДЕТАЛЬНЫЙ ОТЧЁТ ОБ ОШИБКАХ",
            "=" * 60,
            f"Показаны последние {len(recent_errors)} ошибок:",
            "",
        ]

        for i, error_ctx in enumerate(recent_errors, 1):
            category, severity = self.error_handler._classify_error(
                error_ctx.error_type
            )

            lines.extend(
                [
                    f"🚨 ОШИБКА #{i}",
                    "-" * 30,
                    f"⏰ Время: {error_ctx.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"🔧 Компонент: {error_ctx.component}",
                    f"⚙️  Операция: {error_ctx.operation}",
                    f"📦 Тип: {error_ctx.error_type}",
                    f"📝 Сообщение: {error_ctx.error_message}",
                    f"📂 Категория: {category}",
                    f"⚠️  Критичность: {severity}",
                    "",
                ]
            )

            # Дополнительные данные
            if error_ctx.additional_data:
                lines.append("📊 Дополнительные данные:")
                for key, value in error_ctx.additional_data.items():
                    lines.append(f"  • {key}: {value}")
                lines.append("")

        return "\n".join(lines)


# Глобальный экземпляр обработчика ошибок
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Возвращает глобальный экземпляр обработчика ошибок.

    Returns:
        ErrorHandler: Глобальный обработчик ошибок
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(
    error: Exception,
    operation: str,
    component: str = "unknown",
    additional_data: Optional[Dict[str, Any]] = None,
    reraise: bool = False,
) -> ErrorContext:
    """
    Удобная функция для обработки ошибки через глобальный обработчик.

    Args:
        error: Исключение для обработки
        operation: Название операции
        component: Компонент, в котором произошла ошибка
        additional_data: Дополнительные данные
        reraise: Повторно выбросить исключение

    Returns:
        ErrorContext: Контекст обработанной ошибки
    """
    return get_error_handler().handle_error(
        error, operation, component, additional_data, reraise
    )


def get_error_summary() -> Dict[str, Any]:
    """
    Возвращает сводку ошибок через глобальный обработчик.

    Returns:
        Dict: Сводка ошибок
    """
    return get_error_handler().get_error_summary()


def generate_error_report() -> str:
    """
    Генерирует отчёт об ошибках через глобальный обработчик.

    Returns:
        str: Текстовый отчёт об ошибках
    """
    reporter = ErrorReporter(get_error_handler())
    return reporter.generate_summary_report()
