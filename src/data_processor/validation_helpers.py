"""
Helper функции для безопасного преобразования и валидации числовых значений.

Модуль предоставляет функции для обработки None, пустых строк и невалидных значений
при преобразовании в Decimal и float, предотвращая InvalidOperation и TypeError.

Версия: v2.4.1
Дата: 2025-10-27
Баг: БАГ-2 - Падение на None в суммах и НДС
"""

from typing import Any
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


def safe_decimal(value: Any, default: str = "0") -> Decimal:
    """
    Безопасное преобразование значения в Decimal с валидацией.

    Обрабатывает:
    - None → default
    - Пустые строки → default
    - Невалидные значения → default с warning

    Args:
        value: Значение для преобразования (может быть None, str, int, float, Decimal)
        default: Значение по умолчанию при ошибке (строка)

    Returns:
        Decimal: Безопасно преобразованное значение

    Examples:
        >>> safe_decimal(None, '0')
        Decimal('0')
        >>> safe_decimal('', '0')
        Decimal('0')
        >>> safe_decimal('invalid', '0')
        Decimal('0')  # + warning в лог
        >>> safe_decimal(1000.50, '0')
        Decimal('1000.50')
        >>> safe_decimal('  ', '0')  # Пробелы
        Decimal('0')
    """
    # None или пустая строка
    if value is None or value == "":
        return Decimal(default)

    # Уже Decimal - возвращаем как есть
    if isinstance(value, Decimal):
        return value

    # Пытаемся преобразовать
    try:
        # Очищаем от пробелов если строка
        if isinstance(value, str):
            value = value.strip()
            if not value:  # После strip пустая строка
                return Decimal(default)

        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.warning(
            f"Невалидное значение для Decimal: {repr(value)} ({type(value).__name__}), "
            f"использую default={default}. Ошибка: {e}"
        )
        return Decimal(default)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Безопасное преобразование значения в float с валидацией.

    Обрабатывает:
    - None → default
    - Пустые строки → default
    - Невалидные значения → default с warning

    Args:
        value: Значение для преобразования (может быть None, str, int, float, Decimal)
        default: Значение по умолчанию при ошибке

    Returns:
        float: Безопасно преобразованное значение

    Examples:
        >>> safe_float(None, 0.0)
        0.0
        >>> safe_float('', 0.0)
        0.0
        >>> safe_float('invalid', 0.0)
        0.0  # + warning в лог
        >>> safe_float(Decimal('1000.50'), 0.0)
        1000.5
        >>> safe_float('  ', 0.0)  # Пробелы
        0.0
    """
    # None или пустая строка
    if value is None or value == "":
        return default

    # Уже float - возвращаем как есть
    if isinstance(value, float):
        return value

    # Decimal - конвертируем
    if isinstance(value, Decimal):
        return float(value)

    # Пытаемся преобразовать
    try:
        # Очищаем от пробелов если строка
        if isinstance(value, str):
            value = value.strip()
            if not value:  # После strip пустая строка
                return default

        return float(value)
    except (ValueError, TypeError) as e:
        logger.warning(
            f"Невалидное значение для float: {repr(value)} ({type(value).__name__}), "
            f"использую default={default}. Ошибка: {e}"
        )
        return default
