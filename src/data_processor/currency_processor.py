"""
Currency Processor для обработки валют и денежных сумм в российском формате.
Поддерживает форматирование, валидацию и вычисления НДС.
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CurrencyProcessingResult:
    """Результат обработки валютной суммы"""

    is_valid: bool
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    formatted_amount: Optional[str] = None
    original_value: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class VATCalculationResult:
    """Результат расчёта НДС"""

    is_valid: bool
    base_amount: Optional[Decimal] = None  # Сумма без НДС
    vat_amount: Optional[Decimal] = None  # Сумма НДС
    total_amount: Optional[Decimal] = None  # Общая сумма с НДС
    vat_rate: Optional[Decimal] = None  # Ставка НДС
    formatted_base: Optional[str] = None
    formatted_vat: Optional[str] = None
    formatted_total: Optional[str] = None
    error_message: Optional[str] = None


class CurrencyProcessor:
    """
    Процессор для обработки валют и денежных сумм.

    Поддерживает:
    - Российское форматирование валют
    - Парсинг различных форматов сумм
    - Расчёт НДС по российским ставкам
    - Валидация финансовых данных
    - Округление до копеек
    """

    # Поддерживаемые валюты
    SUPPORTED_CURRENCIES = {
        "RUB": {"symbol": "₽", "code": "RUB", "name": "Российский рубль"},
        "RUR": {
            "symbol": "₽",
            "code": "RUB",
            "name": "Российский рубль",
        },  # Старое обозначение
        "USD": {"symbol": "$", "code": "USD", "name": "Доллар США"},
        "EUR": {"symbol": "€", "code": "EUR", "name": "Евро"},
        "CNY": {"symbol": "¥", "code": "CNY", "name": "Китайский юань"},
    }

    # Российские ставки НДС
    VAT_RATES = {
        "20%": Decimal("0.20"),  # Основная ставка
        "10%": Decimal("0.10"),  # Льготная ставка
        "0%": Decimal("0.00"),  # Без НДС
        "Без НДС": Decimal("0.00"),
    }

    # Паттерны для парсинга валют
    CURRENCY_PATTERNS = [
        # Российские форматы
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)\s*(?:руб\.?|₽|RUB|рублей?)",
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)\s*р\.?",
        # Доллары
        r"\$\s*(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)",
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)\s*(?:USD|долларов?)",
        # Евро
        r"€\s*(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)",
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)\s*(?:EUR|евро)",
        # Юани
        r"¥\s*(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)",
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)\s*(?:CNY|юаней?)",
        # Общий числовой формат
        r"(\d+(?:\s\d{3})*(?:[.,]\d{1,2})?)",
    ]

    def __init__(self, default_currency: str = "RUB"):
        """
        Инициализация процессора валют.

        Args:
            default_currency: Валюта по умолчанию
        """
        self.default_currency = default_currency.upper()
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.CURRENCY_PATTERNS
        ]

    def parse_amount(
        self,
        amount_value: Union[str, int, float, Decimal, None],
        currency: Optional[str] = None,
    ) -> CurrencyProcessingResult:
        """
        Парсинг денежной суммы из различных форматов.

        Args:
            amount_value: Значение суммы для парсинга
            currency: Валюта (если не указана, используется из строки или по умолчанию)

        Returns:
            CurrencyProcessingResult: Результат парсинга
        """
        if amount_value is None:
            return CurrencyProcessingResult(
                is_valid=False,
                original_value=None,
                error_message="Сумма не может быть None",
            )

        # Если уже Decimal
        if isinstance(amount_value, Decimal):
            return self._create_valid_result(
                amount_value, currency or self.default_currency, str(amount_value)
            )

        # Если число
        if isinstance(amount_value, (int, float)):
            if amount_value < 0:
                return CurrencyProcessingResult(
                    is_valid=False,
                    original_value=str(amount_value),
                    error_message="Сумма не может быть отрицательной",
                )

            decimal_amount = Decimal(str(amount_value))
            return self._create_valid_result(
                decimal_amount, currency or self.default_currency, str(amount_value)
            )

        # Обработка строки
        amount_str = str(amount_value).strip()

        if not amount_str:
            return CurrencyProcessingResult(
                is_valid=False,
                original_value=amount_str,
                error_message="Пустая строка суммы",
            )

        # Парсинг из строки
        return self._parse_from_string(amount_str, currency)

    def _parse_from_string(
        self, amount_str: str, currency: Optional[str]
    ) -> CurrencyProcessingResult:
        """Парсинг суммы из строки"""
        detected_currency = currency or self.default_currency

        # Проверяем на отрицательную сумму в начале строки
        if amount_str.strip().startswith("-"):
            return CurrencyProcessingResult(
                is_valid=False,
                original_value=amount_str,
                error_message="Сумма не может быть отрицательной",
            )

        # Определяем валюту из строки если не указана
        if currency is None:
            detected_currency = self._detect_currency_from_string(amount_str)

        # Пробуем каждый паттерн
        for pattern in self._compiled_patterns:
            match = pattern.search(amount_str)
            if match:
                try:
                    # Извлекаем числовую часть
                    number_str = match.group(1)

                    # Очищаем и нормализуем число
                    cleaned_number = self._clean_number_string(number_str)

                    if not cleaned_number:
                        continue

                    decimal_amount = Decimal(cleaned_number)

                    # Валидация суммы
                    if decimal_amount < 0:
                        return CurrencyProcessingResult(
                            is_valid=False,
                            original_value=amount_str,
                            error_message="Сумма не может быть отрицательной",
                        )

                    if decimal_amount > Decimal(
                        "999999999999.99"
                    ):  # Ограничение на огромные суммы
                        return CurrencyProcessingResult(
                            is_valid=False,
                            original_value=amount_str,
                            error_message="Сумма слишком большая",
                        )

                    return self._create_valid_result(
                        decimal_amount, detected_currency, amount_str
                    )

                except (ValueError, TypeError, ArithmeticError):
                    continue

        return CurrencyProcessingResult(
            is_valid=False,
            original_value=amount_str,
            error_message=f"Не удалось распознать формат суммы: {amount_str}",
        )

    def _detect_currency_from_string(self, amount_str: str) -> str:
        """Определение валюты из строки"""
        amount_lower = amount_str.lower()

        currency_indicators = {
            "RUB": ["руб", "₽", "rub", "рубл", "р."],
            "USD": ["$", "usd", "доллар"],
            "EUR": ["€", "eur", "евро"],
            "CNY": ["¥", "cny", "юань"],
        }

        for currency, indicators in currency_indicators.items():
            for indicator in indicators:
                if indicator in amount_lower:
                    return currency

        return self.default_currency

    def _clean_number_string(self, number_str: str) -> str:
        """Очистка и нормализация числовой строки"""
        # Убираем пробелы (разделители тысяч)
        cleaned = re.sub(r"\s+", "", number_str)

        # Заменяем запятую на точку (российский формат)
        cleaned = cleaned.replace(",", ".")

        # Проверяем что остались только цифры и точка
        if not re.match(r"^\d+(?:\.\d{1,2})?$", cleaned):
            return ""

        return cleaned

    def _create_valid_result(
        self, amount: Decimal, currency: str, original: str
    ) -> CurrencyProcessingResult:
        """Создание результата успешного парсинга"""
        # Округляем до копеек
        rounded_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return CurrencyProcessingResult(
            is_valid=True,
            amount=rounded_amount,
            currency=currency.upper(),
            formatted_amount=self.format_amount(rounded_amount, currency),
            original_value=original,
        )

    def format_amount(
        self,
        amount: Decimal,
        currency: str = None,
        include_currency_symbol: bool = True,
    ) -> str:
        """
        Форматирование суммы в российском стиле.

        Args:
            amount: Сумма для форматирования
            currency: Валюта
            include_currency_symbol: Включать ли символ валюты

        Returns:
            str: Отформатированная сумма
        """
        if currency is None:
            currency = self.default_currency

        currency_upper = currency.upper()

        # Округляем до копеек
        rounded_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Разделяем на целую и дробную части
        integer_part = int(rounded_amount)
        decimal_part = rounded_amount % 1

        # Форматируем целую часть с разделителями тысяч (пробелы)
        integer_str = f"{integer_part:,}".replace(",", " ")

        # Форматируем дробную часть (копейки)
        if decimal_part > 0:
            cents = int(decimal_part * 100)
            formatted = f"{integer_str},{cents:02d}"
        else:
            formatted = integer_str

        # Добавляем символ валюты если нужно
        if include_currency_symbol and currency_upper in self.SUPPORTED_CURRENCIES:
            symbol = self.SUPPORTED_CURRENCIES[currency_upper]["symbol"]
            formatted = f"{formatted} {symbol}"

        return formatted

    def calculate_vat(
        self,
        amount: Union[Decimal, str, float],
        vat_rate: Union[str, Decimal],
        amount_includes_vat: bool = True,
    ) -> VATCalculationResult:
        """
        Расчёт НДС.

        Args:
            amount: Сумма для расчёта
            vat_rate: Ставка НДС ('20%', '10%', '0%' или Decimal)
            amount_includes_vat: True если сумма включает НДС, False если без НДС

        Returns:
            VATCalculationResult: Результат расчёта НДС
        """
        # Парсим сумму
        if isinstance(amount, str):
            parse_result = self.parse_amount(amount)
            if not parse_result.is_valid:
                return VATCalculationResult(
                    is_valid=False,
                    error_message=f"Ошибка парсинга суммы: {parse_result.error_message}",
                )
            decimal_amount = parse_result.amount
        elif isinstance(amount, (float, int)):
            decimal_amount = Decimal(str(amount))
        else:
            decimal_amount = amount

        # Определяем ставку НДС
        if isinstance(vat_rate, str):
            vat_rate_clean = vat_rate.strip()
            if vat_rate_clean in self.VAT_RATES:
                vat_decimal = self.VAT_RATES[vat_rate_clean]
            else:
                return VATCalculationResult(
                    is_valid=False, error_message=f"Неизвестная ставка НДС: {vat_rate}"
                )
        else:
            vat_decimal = Decimal(str(vat_rate))

        try:
            if amount_includes_vat:
                # Сумма включает НДС, извлекаем НДС
                total_amount = decimal_amount
                base_amount = total_amount / (Decimal("1") + vat_decimal)
                vat_amount = total_amount - base_amount
            else:
                # Сумма без НДС, добавляем НДС
                base_amount = decimal_amount
                vat_amount = base_amount * vat_decimal
                total_amount = base_amount + vat_amount

            # Округляем до копеек
            base_amount = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            vat_amount = vat_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_amount = total_amount.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            return VATCalculationResult(
                is_valid=True,
                base_amount=base_amount,
                vat_amount=vat_amount,
                total_amount=total_amount,
                vat_rate=vat_decimal,
                formatted_base=self.format_amount(base_amount),
                formatted_vat=self.format_amount(vat_amount),
                formatted_total=self.format_amount(total_amount),
            )

        except (ValueError, ArithmeticError) as e:
            return VATCalculationResult(
                is_valid=False, error_message=f"Ошибка расчёта НДС: {e}"
            )

    def is_valid_amount(
        self, amount_value: Union[str, int, float, Decimal, None]
    ) -> bool:
        """
        Быстрая проверка валидности суммы.

        Args:
            amount_value: Значение суммы для проверки

        Returns:
            bool: True если сумма валидна
        """
        return self.parse_amount(amount_value).is_valid

    def normalize_amount(
        self,
        amount_value: Union[str, int, float, Decimal, None],
        currency: Optional[str] = None,
    ) -> Optional[str]:
        """
        Нормализация суммы к стандартному формату.

        Args:
            amount_value: Значение суммы для нормализации
            currency: Валюта

        Returns:
            Optional[str]: Нормализованная сумма или None если невалидна
        """
        result = self.parse_amount(amount_value, currency)
        return result.formatted_amount if result.is_valid else None

    def get_decimal_amount(
        self, amount_value: Union[str, int, float, Decimal, None]
    ) -> Optional[Decimal]:
        """
        Получение Decimal объекта суммы.

        Args:
            amount_value: Значение суммы

        Returns:
            Optional[Decimal]: Decimal сумма или None если невалидна
        """
        result = self.parse_amount(amount_value)
        return result.amount if result.is_valid else None

    def compare_amounts(
        self, amount1: Union[str, Decimal, None], amount2: Union[str, Decimal, None]
    ) -> Optional[int]:
        """
        Сравнение двух сумм.

        Args:
            amount1: Первая сумма
            amount2: Вторая сумма

        Returns:
            Optional[int]: -1 если amount1 < amount2, 0 если равны, 1 если amount1 > amount2, None если ошибка
        """
        decimal1 = self.get_decimal_amount(amount1)
        decimal2 = self.get_decimal_amount(amount2)

        if decimal1 is None or decimal2 is None:
            return None

        if decimal1 < decimal2:
            return -1
        elif decimal1 > decimal2:
            return 1
        else:
            return 0

    def sum_amounts(
        self, amounts: List[Union[str, Decimal, None]]
    ) -> Optional[Decimal]:
        """
        Суммирование списка сумм.

        Args:
            amounts: Список сумм для суммирования

        Returns:
            Optional[Decimal]: Общая сумма или None если ошибка
        """
        total = Decimal("0")

        for amount in amounts:
            decimal_amount = self.get_decimal_amount(amount)
            if decimal_amount is None:
                return None
            total += decimal_amount

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def convert_currency(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        exchange_rate: Decimal,
    ) -> Decimal:
        """
        Конвертация валют.

        Args:
            amount: Сумма для конвертации
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            exchange_rate: Курс обмена

        Returns:
            Decimal: Конвертированная сумма
        """
        converted = amount * exchange_rate
        return converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def process_vat_rate(self, vat_rate: str) -> dict:
        """
        Обработка ставки НДС для Excel formatter.

        Args:
            vat_rate: Ставка НДС в виде строки

        Returns:
            dict: Информация о НДС включая is_no_vat флаг
        """
        vat_rate_clean = vat_rate.strip() if vat_rate else ""

        if vat_rate_clean in ["Без НДС", "0%", "нет"]:
            return {
                "rate": Decimal("0.00"),
                "rate_str": vat_rate_clean,
                "is_no_vat": True,
            }
        elif vat_rate_clean in self.VAT_RATES:
            return {
                "rate": self.VAT_RATES[vat_rate_clean],
                "rate_str": vat_rate_clean,
                "is_no_vat": False,
            }
        else:
            # Попытка извлечь числовое значение
            try:
                numeric_match = re.search(r"(\d+(?:[.,]\d+)?)", vat_rate_clean)
                if numeric_match:
                    rate_value = Decimal(numeric_match.group(1).replace(",", ".")) / 100
                    return {
                        "rate": rate_value,
                        "rate_str": vat_rate_clean,
                        "is_no_vat": rate_value == Decimal("0.00"),
                    }
            except (ValueError, TypeError):
                pass

        # По умолчанию считаем что НДС есть
        return {
            "rate": Decimal("0.20"),  # 20% по умолчанию
            "rate_str": vat_rate_clean,
            "is_no_vat": False,
        }

    def format_currency_russian(self, amount: Union[Decimal, str, float, None]) -> str:
        """
        Форматирование суммы в российском формате для отображения.

        Args:
            amount: Сумма для форматирования

        Returns:
            str: Отформатированная сумма или исходная строка если невалидна
        """
        if amount is None:
            return ""

        result = self.parse_amount(amount)
        if result.is_valid and result.formatted_amount:
            # Убираем символ валюты для Excel (только число)
            formatted = result.formatted_amount
            # Убираем ₽ или другие символы валют
            for currency_info in self.SUPPORTED_CURRENCIES.values():
                formatted = formatted.replace(f" {currency_info['symbol']}", "")
            return formatted

        return str(amount)
