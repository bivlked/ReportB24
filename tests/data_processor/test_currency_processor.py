"""
Unit тесты для CurrencyProcessor.
Тестирует парсинг валют, российское форматирование и расчёт НДС.
"""
import pytest
from decimal import Decimal
from src.data_processor.currency_processor import CurrencyProcessor, CurrencyProcessingResult, VATCalculationResult


class TestCurrencyProcessor:
    """Тесты основного функционала CurrencyProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Фикстура для создания CurrencyProcessor"""
        return CurrencyProcessor()
    
    def test_processor_initialization(self, processor):
        """Тест: инициализация процессора"""
        assert processor is not None
        assert processor.default_currency == 'RUB'
        assert 'RUB' in processor.SUPPORTED_CURRENCIES
        assert '20%' in processor.VAT_RATES
    
    def test_custom_default_currency(self):
        """Тест: инициализация с пользовательской валютой"""
        processor = CurrencyProcessor(default_currency='USD')
        assert processor.default_currency == 'USD'
    
    def test_empty_and_none_amount(self, processor):
        """Тест: обработка пустых и None значений"""
        # None значение
        result = processor.parse_amount(None)
        assert not result.is_valid
        assert "не может быть None" in result.error_message
        
        # Пустая строка
        result = processor.parse_amount("")
        assert not result.is_valid
        assert "Пустая строка суммы" in result.error_message
        
        # Строка с пробелами
        result = processor.parse_amount("   ")
        assert not result.is_valid
        assert "Пустая строка суммы" in result.error_message

    def test_parse_russian_amounts(self, processor):
        """Тест: парсинг российских сумм"""
        test_cases = [
            ("1000 руб", Decimal('1000')),
            ("1 000,50 ₽", Decimal('1000.50')),
            ("500 рублей", Decimal('500')),
            ("123,45 р.", Decimal('123.45')),
        ]
        
        for amount_str, expected_amount in test_cases:
            result = processor.parse_amount(amount_str)
            assert result.is_valid, f"Ошибка парсинга {amount_str}: {result.error_message}"
            assert result.amount == expected_amount
    
    def test_format_amount(self, processor):
        """Тест: форматирование сумм"""
        test_cases = [
            (Decimal('1000'), "1 000 ₽"),
            (Decimal('1000.50'), "1 000,50 ₽"),
            (Decimal('123.45'), "123,45 ₽"),
        ]
        
        for amount, expected_formatted in test_cases:
            formatted = processor.format_amount(amount, 'RUB')
            assert formatted == expected_formatted
    
    def test_vat_calculations(self, processor):
        """Тест: расчёт НДС"""
        # НДС 20% - извлечение из суммы с НДС
        result = processor.calculate_vat(Decimal('120'), '20%', amount_includes_vat=True)
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('20.00')
        assert result.total_amount == Decimal('120.00')
        
        # НДС 20% - добавление к сумме без НДС
        result = processor.calculate_vat(Decimal('100'), '20%', amount_includes_vat=False)
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('20.00')
        assert result.total_amount == Decimal('120.00')
    
    def test_number_formats(self, processor):
        """Тест: различные числовые форматы"""
        test_cases = [
            ("1000", Decimal('1000')),
            ("1 000", Decimal('1000')),
            ("1 000,50", Decimal('1000.50')),
            ("1000.50", Decimal('1000.50')),
        ]
        
        for amount_str, expected_amount in test_cases:
            result = processor.parse_amount(amount_str)
            assert result.is_valid, f"Ошибка парсинга {amount_str}"
            assert result.amount == expected_amount
    
    def test_screenshot_amounts(self, processor):
        """Тест: суммы как со скриншотов"""
        screenshot_amounts = [
            "1 234 567,89",
            "500 000,00", 
            "123 456,78",
            "1 000,50",
            "999,99",
        ]
        
        for amount_str in screenshot_amounts:
            result = processor.parse_amount(amount_str)
            assert result.is_valid, f"Сумма {amount_str} должна быть валидной"
            assert result.amount > 0
    
    def test_invalid_inputs(self, processor):
        """Тест: невалидные входные данные"""
        invalid_inputs = [None, "", "   ", -1000, "invalid"]
        
        for invalid_input in invalid_inputs:
            result = processor.parse_amount(invalid_input)
            assert not result.is_valid
    
    def test_utility_methods(self, processor):
        """Тест: вспомогательные методы"""
        # Проверка валидности
        assert processor.is_valid_amount("1000 руб") is True
        assert processor.is_valid_amount("invalid") is False
        
        # Нормализация
        normalized = processor.normalize_amount("1000,50 руб")
        assert normalized is not None
        assert "1 000,50" in normalized
        
        # Получение Decimal
        decimal_amount = processor.get_decimal_amount("1000 руб")
        assert decimal_amount == Decimal('1000')
        
        # Сравнение
        assert processor.compare_amounts("1000 руб", "2000 руб") == -1
        assert processor.compare_amounts("2000 руб", "1000 руб") == 1
        assert processor.compare_amounts("1000 руб", "1000 руб") == 0
        
        # Суммирование
        total = processor.sum_amounts(["1000 руб", "500 руб", "250,50 руб"])
        assert total == Decimal('1750.50')


class TestRussianCurrencyFormats:
    """Тесты парсинга российских форматов валют"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_ruble_formats(self, processor):
        """Тест: различные форматы рублей"""
        test_cases = [
            ("1000 руб", Decimal('1000'), 'RUB'),
            ("1 000,50 ₽", Decimal('1000.50'), 'RUB'),
            ("500 рублей", Decimal('500'), 'RUB'),
            ("123,45 р.", Decimal('123.45'), 'RUB'),
            ("1 000 000 RUB", Decimal('1000000'), 'RUB'),
        ]
        
        for amount_str, expected_amount, expected_currency in test_cases:
            result = processor.parse_amount(amount_str)
            assert result.is_valid, f"Ошибка парсинга {amount_str}: {result.error_message}"
            assert result.amount == expected_amount
            assert result.currency == expected_currency
    
    def test_integer_and_float_inputs(self, processor):
        """Тест: целые числа и float"""
        # Целое число
        result = processor.parse_amount(1000)
        assert result.is_valid
        assert result.amount == Decimal('1000')
        assert result.currency == 'RUB'
        
        # Float
        result = processor.parse_amount(1000.50)
        assert result.is_valid
        assert result.amount == Decimal('1000.50')
        
        # Decimal
        result = processor.parse_amount(Decimal('1000.50'))
        assert result.is_valid
        assert result.amount == Decimal('1000.50')
    
    def test_negative_amounts(self, processor):
        """Тест: отрицательные суммы"""
        result = processor.parse_amount(-1000)
        assert not result.is_valid
        assert "не может быть отрицательной" in result.error_message
        
        result = processor.parse_amount("-1000 руб")
        assert not result.is_valid


class TestForeignCurrencyFormats:
    """Тесты парсинга иностранных валют"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_usd_formats(self, processor):
        """Тест: форматы долларов"""
        test_cases = [
            ("$1000", Decimal('1000'), 'USD'),
            ("1000 USD", Decimal('1000'), 'USD'),
            ("1 000,50 долларов", Decimal('1000.50'), 'USD'),
        ]
        
        for amount_str, expected_amount, expected_currency in test_cases:
            result = processor.parse_amount(amount_str)
            assert result.is_valid
            assert result.amount == expected_amount
            # Примечание: валюта может определяться из строки
    
    def test_eur_formats(self, processor):
        """Тест: форматы евро"""
        test_cases = [
            ("€500", Decimal('500'), 'EUR'),
            ("500 EUR", Decimal('500'), 'EUR'),
            ("500 евро", Decimal('500'), 'EUR'),
        ]
        
        for amount_str, expected_amount, expected_currency in test_cases:
            result = processor.parse_amount(amount_str)
            assert result.is_valid
            assert result.amount == expected_amount


class TestAmountFormatting:
    """Тесты форматирования сумм"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_russian_formatting(self, processor):
        """Тест: российское форматирование"""
        test_cases = [
            (Decimal('1000'), "1 000 ₽"),
            (Decimal('1000.50'), "1 000,50 ₽"),
            (Decimal('123'), "123 ₽"),
            (Decimal('123.45'), "123,45 ₽"),
            (Decimal('1000000'), "1 000 000 ₽"),
            (Decimal('1234567.89'), "1 234 567,89 ₽"),
        ]
        
        for amount, expected_formatted in test_cases:
            formatted = processor.format_amount(amount, 'RUB')
            assert formatted == expected_formatted
    
    def test_formatting_without_currency_symbol(self, processor):
        """Тест: форматирование без символа валюты"""
        formatted = processor.format_amount(Decimal('1000.50'), 'RUB', include_currency_symbol=False)
        assert formatted == "1 000,50"
    
    def test_formatting_different_currencies(self, processor):
        """Тест: форматирование разных валют"""
        amount = Decimal('1000.50')
        
        usd_formatted = processor.format_amount(amount, 'USD')
        assert "$" in usd_formatted
        
        eur_formatted = processor.format_amount(amount, 'EUR')
        assert "€" in eur_formatted


class TestVATCalculations:
    """Тесты расчёта НДС"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_vat_20_percent_extract(self, processor):
        """Тест: извлечение НДС 20% из суммы с НДС"""
        # Сумма 120 руб включает НДС 20%
        # Без НДС: 100 руб, НДС: 20 руб
        result = processor.calculate_vat(Decimal('120'), '20%', amount_includes_vat=True)
        
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('20.00')
        assert result.total_amount == Decimal('120.00')
        assert result.vat_rate == Decimal('0.20')
    
    def test_vat_20_percent_add(self, processor):
        """Тест: добавление НДС 20% к сумме без НДС"""
        # Сумма 100 руб без НДС
        # НДС: 20 руб, Итого: 120 руб
        result = processor.calculate_vat(Decimal('100'), '20%', amount_includes_vat=False)
        
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('20.00')
        assert result.total_amount == Decimal('120.00')
    
    def test_vat_10_percent(self, processor):
        """Тест: НДС 10%"""
        result = processor.calculate_vat(Decimal('110'), '10%', amount_includes_vat=True)
        
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('10.00')
        assert result.total_amount == Decimal('110.00')
    
    def test_vat_0_percent(self, processor):
        """Тест: НДС 0%"""
        result = processor.calculate_vat(Decimal('100'), '0%', amount_includes_vat=True)
        
        assert result.is_valid
        assert result.base_amount == Decimal('100.00')
        assert result.vat_amount == Decimal('0.00')
        assert result.total_amount == Decimal('100.00')
    
    def test_vat_without_vat(self, processor):
        """Тест: без НДС"""
        result = processor.calculate_vat(Decimal('100'), 'Без НДС', amount_includes_vat=True)
        
        assert result.is_valid
        assert result.vat_amount == Decimal('0.00')
    
    def test_vat_with_string_amount(self, processor):
        """Тест: расчёт НДС со строковой суммой"""
        result = processor.calculate_vat("1200 руб", '20%', amount_includes_vat=True)
        
        assert result.is_valid
        assert result.base_amount == Decimal('1000.00')
        assert result.vat_amount == Decimal('200.00')
    
    def test_vat_invalid_rate(self, processor):
        """Тест: невалидная ставка НДС"""
        result = processor.calculate_vat(Decimal('100'), '25%', amount_includes_vat=True)
        
        assert not result.is_valid
        assert "Неизвестная ставка НДС" in result.error_message
    
    def test_vat_rounding(self, processor):
        """Тест: округление при расчёте НДС"""
        # Сумма, которая при расчёте НДС даёт не целые копейки
        result = processor.calculate_vat(Decimal('123.33'), '20%', amount_includes_vat=True)
        
        assert result.is_valid
        # Проверяем что все суммы округлены до копеек
        assert result.base_amount == result.base_amount.quantize(Decimal('0.01'))
        assert result.vat_amount == result.vat_amount.quantize(Decimal('0.01'))
        assert result.total_amount == result.total_amount.quantize(Decimal('0.01'))


class TestUtilityMethods:
    """Тесты вспомогательных методов CurrencyProcessor"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_is_valid_amount(self, processor):
        """Тест: быстрая проверка валидности"""
        assert processor.is_valid_amount("1000 руб") is True
        assert processor.is_valid_amount("invalid") is False
        assert processor.is_valid_amount(None) is False
        assert processor.is_valid_amount(-1000) is False
    
    def test_normalize_amount(self, processor):
        """Тест: нормализация суммы"""
        normalized = processor.normalize_amount("1000,50 руб")
        assert "1 000,50" in normalized
        
        normalized = processor.normalize_amount("invalid")
        assert normalized is None
    
    def test_get_decimal_amount(self, processor):
        """Тест: получение Decimal суммы"""
        decimal_amount = processor.get_decimal_amount("1000,50 руб")
        assert decimal_amount == Decimal('1000.50')
        
        decimal_amount = processor.get_decimal_amount("invalid")
        assert decimal_amount is None
    
    def test_compare_amounts(self, processor):
        """Тест: сравнение сумм"""
        # amount1 < amount2
        result = processor.compare_amounts("1000 руб", "2000 руб")
        assert result == -1
        
        # amount1 > amount2
        result = processor.compare_amounts(Decimal('2000'), Decimal('1000'))
        assert result == 1
        
        # amount1 == amount2
        result = processor.compare_amounts("1000 руб", Decimal('1000'))
        assert result == 0
        
        # invalid amount
        result = processor.compare_amounts("invalid", "1000 руб")
        assert result is None
    
    def test_sum_amounts(self, processor):
        """Тест: суммирование сумм"""
        amounts = ["1000 руб", Decimal('500'), "250,50 руб"]
        total = processor.sum_amounts(amounts)
        
        assert total == Decimal('1750.50')
        
        # С невалидной суммой
        amounts_invalid = ["1000 руб", "invalid", "500 руб"]
        total = processor.sum_amounts(amounts_invalid)
        assert total is None
    
    def test_convert_currency(self, processor):
        """Тест: конвертация валют"""
        # 1000 RUB * 0.012 = 12 USD
        converted = processor.convert_currency(
            Decimal('1000'), 'RUB', 'USD', Decimal('0.012')
        )
        assert converted == Decimal('12.00')


class TestRealWorldScenarios:
    """Тесты с реальными сценариями использования"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_screenshot_amounts_parsing(self, processor):
        """Тест: парсинг сумм как со скриншотов"""
        # Примеры реальных сумм из скриншотов отчёта
        screenshot_amounts = [
            "1 234 567,89",
            "500 000,00",
            "123 456,78",
            "1 000,50",
            "999,99",
            "50 000",
            "1 500 000",
        ]
        
        valid_count = 0
        
        for amount_str in screenshot_amounts:
            result = processor.parse_amount(amount_str)
            if result.is_valid:
                valid_count += 1
                assert result.amount > 0
                assert result.currency == 'RUB'  # По умолчанию
                assert result.formatted_amount is not None
        
        # Все суммы должны быть валидными
        assert valid_count == len(screenshot_amounts)
    
    def test_report_calculations(self, processor):
        """Тест: расчёты как в отчёте"""
        # Моделируем строку отчёта: сумма с НДС, извлекаем НДС
        total_amount = "120 000 руб"
        
        # Парсим общую сумму
        parse_result = processor.parse_amount(total_amount)
        assert parse_result.is_valid
        
        # Рассчитываем НДС 20%
        vat_result = processor.calculate_vat(
            parse_result.amount, '20%', amount_includes_vat=True
        )
        
        assert vat_result.is_valid
        assert vat_result.base_amount == Decimal('100000.00')
        assert vat_result.vat_amount == Decimal('20000.00')
        assert vat_result.total_amount == Decimal('120000.00')
        
        # Проверяем форматирование для отчёта
        assert "100 000" in vat_result.formatted_base
        assert "20 000" in vat_result.formatted_vat
        assert "120 000" in vat_result.formatted_total
    
    def test_edge_cases(self, processor):
        """Тест: граничные случаи"""
        # Очень большая сумма
        result = processor.parse_amount("999999999999,99")
        assert result.is_valid
        
        # Слишком большая сумма
        result = processor.parse_amount("9999999999999999")
        assert not result.is_valid
        assert "слишком большая" in result.error_message
        
        # Копейки
        result = processor.parse_amount("0,01")
        assert result.is_valid
        assert result.amount == Decimal('0.01')
        
        # Нулевая сумма
        result = processor.parse_amount("0")
        assert result.is_valid
        assert result.amount == Decimal('0')


class TestCurrencyDetection:
    """Тесты определения валют"""
    
    @pytest.fixture
    def processor(self):
        return CurrencyProcessor()
    
    def test_currency_detection_from_string(self, processor):
        """Тест: определение валюты из строки"""
        test_cases = [
            ("1000 руб", 'RUB'),
            ("$1000", 'USD'),
            ("€500", 'EUR'),
            ("1000 долларов", 'USD'),
            ("500 евро", 'EUR'),
            ("1000", 'RUB'),  # По умолчанию
        ]
        
        for amount_str, expected_currency in test_cases:
            detected = processor._detect_currency_from_string(amount_str)
            assert detected == expected_currency


@pytest.mark.unit
def test_currency_processor_integration():
    """Интеграционный тест CurrencyProcessor"""
    processor = CurrencyProcessor()
    
    # Полный workflow
    test_data = [
        ("1000 руб", True, Decimal('1000')),
        ("invalid", False, None),
        (None, False, None),
        (-1000, False, None),
    ]
    
    for amount_input, expected_valid, expected_amount in test_data:
        result = processor.parse_amount(amount_input)
        assert result.is_valid == expected_valid
        
        if expected_valid:
            assert result.amount == expected_amount
            assert processor.normalize_amount(amount_input) is not None
        else:
            assert processor.normalize_amount(amount_input) is None 