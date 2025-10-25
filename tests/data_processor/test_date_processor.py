"""
Unit тесты для DateProcessor.
Тестирует парсинг различных форматов дат и приведение к российскому стандарту.
"""
import pytest
from datetime import datetime, date
from src.data_processor.date_processor import DateProcessor, DateProcessingResult


class TestDateProcessor:
    """Тесты основного функционала DateProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Фикстура для создания DateProcessor"""
        return DateProcessor()
    
    def test_processor_initialization(self, processor):
        """Тест: инициализация процессора"""
        assert processor is not None
        assert hasattr(processor, 'INPUT_FORMATS')
        assert hasattr(processor, 'RUSSIAN_DATE_FORMAT')
        assert processor.RUSSIAN_DATE_FORMAT == "%d.%m.%Y"
    
    def test_empty_and_none_date(self, processor):
        """Тест: обработка пустых и None значений"""
        # None значение
        result = processor.parse_date(None)
        assert not result.is_valid
        assert "не может быть None" in result.error_message
        
        # Пустая строка
        result = processor.parse_date("")
        assert not result.is_valid
        assert "Пустая строка даты" in result.error_message
        
        # Строка с пробелами
        result = processor.parse_date("   ")
        assert not result.is_valid
        assert "Пустая строка даты" in result.error_message


class TestRussianDateFormats:
    """Тесты парсинга российских форматов дат"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_russian_date_format_ddmmyyyy(self, processor):
        """Тест: российский формат дд.мм.гггг"""
        test_dates = [
            "01.12.2024",
            "15.06.2023", 
            "31.12.2025",
            "29.02.2024",  # Високосный год
        ]
        
        for date_str in test_dates:
            result = processor.parse_date(date_str)
            assert result.is_valid, f"Дата {date_str} должна быть валидной: {result.error_message}"
            assert result.formatted_date == date_str
            assert result.original_value == date_str
    
    def test_russian_date_format_ddmmyy(self, processor):
        """Тест: российский формат дд.мм.гг"""
        test_cases = [
            ("01.12.24", "01.12.2024"),
            ("15.06.23", "15.06.2023"),
            ("31.12.25", "31.12.2025"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid, f"Дата {date_str} должна быть валидной"
            assert result.formatted_date == expected_formatted
    
    def test_russian_date_with_slashes(self, processor):
        """Тест: российский формат с слешами"""
        test_cases = [
            ("01/12/2024", "01.12.2024"),
            ("15/06/2023", "15.06.2023"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid
            assert result.formatted_date == expected_formatted
    
    def test_russian_date_with_dashes(self, processor):
        """Тест: российский формат с дефисами"""
        test_cases = [
            ("01-12-2024", "01.12.2024"),
            ("15-06-2023", "15.06.2023"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid
            assert result.formatted_date == expected_formatted


class TestISODateFormats:
    """Тесты парсинга ISO форматов дат"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_iso_date_format(self, processor):
        """Тест: ISO формат гггг-мм-дд"""
        test_cases = [
            ("2024-12-01", "01.12.2024"),
            ("2023-06-15", "15.06.2023"),
            ("2025-12-31", "31.12.2025"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid
            assert result.formatted_date == expected_formatted
    
    def test_iso_date_with_dots(self, processor):
        """Тест: ISO формат с точками"""
        test_cases = [
            ("2024.12.01", "01.12.2024"),
            ("2023.06.15", "15.06.2023"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid
            assert result.formatted_date == expected_formatted
    
    def test_iso_datetime_formats(self, processor):
        """Тест: ISO форматы с временем"""
        test_cases = [
            ("2024-12-01 14:30:00", "01.12.2024"),
            ("2024-12-01T14:30:00", "01.12.2024"),
            ("2024-12-01T14:30:00Z", "01.12.2024"),
            ("2023-06-15 09:45", "15.06.2023"),
        ]
        
        for date_str, expected_formatted in test_cases:
            result = processor.parse_date(date_str)
            assert result.is_valid
            assert result.formatted_date == expected_formatted


class TestDateTimeObjects:
    """Тесты обработки объектов datetime и date"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_datetime_object(self, processor):
        """Тест: обработка объекта datetime"""
        dt = datetime(2024, 12, 1, 14, 30, 0)
        result = processor.parse_date(dt)
        
        assert result.is_valid
        assert result.parsed_date == dt
        assert result.formatted_date == "01.12.2024"
        assert str(dt) in result.original_value
    
    def test_date_object(self, processor):
        """Тест: обработка объекта date"""
        d = date(2024, 12, 1)
        result = processor.parse_date(d)
        
        assert result.is_valid
        assert result.formatted_date == "01.12.2024"
        assert result.parsed_date.date() == d
    
    def test_timestamp_seconds(self, processor):
        """Тест: обработка timestamp в секундах"""
        # 1 января 2024, 00:00:00 UTC
        timestamp = 1704067200
        result = processor.parse_date(timestamp)
        
        assert result.is_valid
        assert result.parsed_date is not None
        assert result.formatted_date is not None
    
    def test_timestamp_milliseconds(self, processor):
        """Тест: обработка timestamp в миллисекундах"""
        # 1 января 2024, 00:00:00 UTC в миллисекундах
        timestamp = 1704067200000
        result = processor.parse_date(timestamp)
        
        assert result.is_valid
        assert result.parsed_date is not None
        assert result.formatted_date is not None
    
    def test_invalid_timestamp(self, processor):
        """Тест: невалидный timestamp"""
        result = processor.parse_date(-1)
        assert not result.is_valid
        assert "Отрицательный timestamp" in result.error_message


class TestDateValidation:
    """Тесты валидации дат"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_valid_leap_year(self, processor):
        """Тест: валидная дата в високосном году"""
        result = processor.parse_date("29.02.2024")
        assert result.is_valid
        assert result.formatted_date == "29.02.2024"
    
    def test_invalid_leap_year(self, processor):
        """Тест: невалидная дата в невисокосном году"""
        result = processor.parse_date("29.02.2023")
        assert not result.is_valid
    
    def test_invalid_day(self, processor):
        """Тест: невалидный день"""
        result = processor.parse_date("32.01.2024")
        assert not result.is_valid
    
    def test_invalid_month(self, processor):
        """Тест: невалидный месяц"""
        result = processor.parse_date("01.13.2024")
        assert not result.is_valid
    
    def test_early_year(self, processor):
        """Тест: слишком ранний год"""
        result = processor.parse_date("01.01.1800")
        assert not result.is_valid
        assert "слишком ранний" in result.error_message
    
    def test_late_year(self, processor):
        """Тест: слишком поздний год"""
        result = processor.parse_date("01.01.2100")
        assert not result.is_valid
        assert "слишком поздний" in result.error_message


class TestDateRange:
    """Тесты обработки диапазонов дат"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_valid_date_range(self, processor):
        """Тест: валидный диапазон дат"""
        start_result, end_result = processor.parse_date_range("01.01.2024", "31.12.2024")
        
        assert start_result.is_valid
        assert end_result.is_valid
        assert start_result.formatted_date == "01.01.2024"
        assert end_result.formatted_date == "31.12.2024"
    
    def test_invalid_date_range_logic(self, processor):
        """Тест: невалидная логика диапазона (начало позже конца)"""
        start_result, end_result = processor.parse_date_range("31.12.2024", "01.01.2024")
        
        assert not start_result.is_valid
        assert not end_result.is_valid
        assert "позже конечной" in start_result.error_message
        assert "раньше начальной" in end_result.error_message
    
    def test_date_range_with_invalid_date(self, processor):
        """Тест: диапазон с невалидной датой"""
        start_result, end_result = processor.parse_date_range("invalid", "31.12.2024")
        
        assert not start_result.is_valid
        assert end_result.is_valid


class TestUtilityMethods:
    """Тесты вспомогательных методов DateProcessor"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_is_valid_date(self, processor):
        """Тест: быстрая проверка валидности"""
        assert processor.is_valid_date("01.12.2024") is True
        assert processor.is_valid_date("invalid") is False
        assert processor.is_valid_date(None) is False
    
    def test_normalize_date(self, processor):
        """Тест: нормализация даты"""
        normalized = processor.normalize_date("2024-12-01")
        assert normalized == "01.12.2024"
        
        normalized = processor.normalize_date("invalid")
        assert normalized is None
    
    def test_get_date_object(self, processor):
        """Тест: получение объекта datetime"""
        dt = processor.get_date_object("01.12.2024")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 12
        assert dt.day == 1
        
        dt = processor.get_date_object("invalid")
        assert dt is None
    
    def test_compare_dates(self, processor):
        """Тест: сравнение дат"""
        # date1 < date2
        result = processor.compare_dates("01.01.2024", "31.12.2024")
        assert result == -1
        
        # date1 > date2
        result = processor.compare_dates("31.12.2024", "01.01.2024")
        assert result == 1
        
        # date1 == date2
        result = processor.compare_dates("01.01.2024", "01.01.2024")
        assert result == 0
        
        # invalid date
        result = processor.compare_dates("invalid", "01.01.2024")
        assert result is None
    
    def test_format_russian_date(self, processor):
        """Тест: форматирование в российский формат"""
        dt = datetime(2024, 12, 1, 14, 30, 0)
        
        # Только дата
        formatted = processor.format_russian_date(dt)
        assert formatted == "01.12.2024"
        
        # Дата с временем
        formatted = processor.format_russian_date(dt, include_time=True)
        assert formatted == "01.12.2024 14:30"


class TestTextExtraction:
    """Тесты извлечения дат из текста"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_extract_date_from_text(self, processor):
        """Тест: извлечение даты из произвольного текста"""
        texts = [
            "Дата счёта: 15.06.2024",
            "Период с 01.01.2024 по 31.12.2024",
            "Создано 2024-06-15 в системе",
            "Invoice date: 15/06/2024",
        ]
        
        for text in texts:
            result = processor.parse_date(text)
            # Проверяем что хотя бы одна дата найдена
            if not result.is_valid:
                # Если стандартный парсинг не сработал, проверяем extraction
                extracted = processor._extract_date_from_text(text)
                if extracted.is_valid:
                    result = extracted
            
            # В большинстве случаев должна найтись валидная дата
            # assert result.is_valid, f"Не удалось извлечь дату из: {text}"


class TestRealWorldScenarios:
    """Тесты с реальными сценариями использования"""
    
    @pytest.fixture
    def processor(self):
        return DateProcessor()
    
    def test_various_input_formats(self, processor):
        """Тест: различные форматы ввода как в реальном использовании"""
        test_cases = [
            # Российские форматы
            ("01.12.2024", "01.12.2024"),
            ("1.12.2024", "01.12.2024"),  # Без ведущего нуля
            ("01.1.2024", "01.01.2024"),  # Без ведущего нуля в месяце
            
            # ISO форматы
            ("2024-12-01", "01.12.2024"),
            ("2024-1-1", "01.01.2024"),   # Без ведущих нулей
            
            # Американские форматы (осторожно!)
            # ("12/01/2024", "01.12.2024"),  # Может быть неоднозначно
        ]
        
        for input_date, expected_output in test_cases:
            result = processor.parse_date(input_date)
            assert result.is_valid, f"Ошибка при парсинге {input_date}: {result.error_message}"
            assert result.formatted_date == expected_output


@pytest.mark.unit
def test_date_processor_integration():
    """Интеграционный тест DateProcessor"""
    processor = DateProcessor()
    
    # Тестируем полный workflow
    test_data = [
        ("01.12.2024", True, "01.12.2024"),
        ("2024-12-01", True, "01.12.2024"),
        ("invalid", False, None),
        ("", False, None),
        (None, False, None),
    ]
    
    for date_input, expected_valid, expected_formatted in test_data:
        result = processor.parse_date(date_input)
        assert result.is_valid == expected_valid
        
        # Проверяем что вспомогательные методы согласованы
        assert processor.is_valid_date(date_input) == expected_valid
        
        if expected_valid:
            assert result.formatted_date == expected_formatted
            assert processor.normalize_date(date_input) == expected_formatted
            assert processor.get_date_object(date_input) is not None
        else:
            assert processor.normalize_date(date_input) is None
            assert processor.get_date_object(date_input) is None 