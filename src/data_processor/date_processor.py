"""
Date Processor для обработки дат в российском формате.
Поддерживает парсинг различных форматов и приведение к российскому стандарту.
"""
import re
from datetime import datetime, date
from typing import Optional, Union, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DateProcessingResult:
    """Результат обработки даты"""
    is_valid: bool
    parsed_date: Optional[datetime] = None
    formatted_date: Optional[str] = None
    original_value: Optional[str] = None
    error_message: Optional[str] = None


class DateProcessor:
    """
    Процессор для обработки дат в российском формате.
    
    Поддерживает:
    - Различные входные форматы дат
    - Парсинг российских дат (дд.мм.гггг)
    - Парсинг ISO дат (гггг-мм-дд)
    - Парсинг дат с временем
    - Форматирование в российский стандарт
    - Валидация корректности дат
    """
    
    # Поддерживаемые форматы входных дат
    INPUT_FORMATS = [
        # Российские форматы
        "%d.%m.%Y",           # 01.12.2024
        "%d.%m.%y",           # 01.12.24
        "%d/%m/%Y",           # 01/12/2024
        "%d/%m/%y",           # 01/12/24
        "%d-%m-%Y",           # 01-12-2024
        "%d-%m-%y",           # 01-12-24
        
        # ISO форматы
        "%Y-%m-%d",           # 2024-12-01
        "%Y.%m.%d",           # 2024.12.01
        "%Y/%m/%d",           # 2024/12/01
        
        # Форматы с временем
        "%d.%m.%Y %H:%M:%S",  # 01.12.2024 14:30:00
        "%d.%m.%Y %H:%M",     # 01.12.2024 14:30
        "%Y-%m-%d %H:%M:%S",  # 2024-12-01 14:30:00
        "%Y-%m-%d %H:%M",     # 2024-12-01 14:30
        "%Y-%m-%dT%H:%M:%S",  # 2024-12-01T14:30:00 (ISO)
        "%Y-%m-%dT%H:%M:%SZ", # 2024-12-01T14:30:00Z (ISO с UTC)
        
        # Американские форматы (частая проблема в интеграциях)
        "%m/%d/%Y",           # 12/01/2024
        "%m-%d-%Y",           # 12-01-2024
    ]
    
    # Российский формат для вывода
    RUSSIAN_DATE_FORMAT = "%d.%m.%Y"
    RUSSIAN_DATETIME_FORMAT = "%d.%m.%Y %H:%M"
    
    def __init__(self):
        """Инициализация процессора дат"""
        self._compiled_patterns = self._compile_regex_patterns()
    
    def _compile_regex_patterns(self) -> List[tuple]:
        """Компиляция regex паттернов для извлечения дат из текста"""
        patterns = [
            # Российские форматы
            (r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', '%d.%m.%Y'),
            (r'\b(\d{1,2})\.(\d{1,2})\.(\d{2})\b', '%d.%m.%y'),
            (r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', '%d/%m/%Y'),
            (r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b', '%d-%m-%Y'),
            
            # ISO форматы
            (r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', '%Y-%m-%d'),
            (r'\b(\d{4})\.(\d{1,2})\.(\d{1,2})\b', '%Y.%m.%d'),
            (r'\b(\d{4})/(\d{1,2})/(\d{1,2})\b', '%Y/%m/%d'),
        ]
        
        return [(re.compile(pattern), fmt) for pattern, fmt in patterns]
    
    def parse_date(self, date_value: Union[str, datetime, date, int, float, None]) -> DateProcessingResult:
        """
        Парсинг даты из различных форматов.
        
        Args:
            date_value: Значение даты для парсинга
            
        Returns:
            DateProcessingResult: Результат парсинга
        """
        if date_value is None:
            return DateProcessingResult(
                is_valid=False,
                original_value=None,
                error_message="Дата не может быть None"
            )
        
        # Если уже datetime объект
        if isinstance(date_value, datetime):
            return DateProcessingResult(
                is_valid=True,
                parsed_date=date_value,
                formatted_date=date_value.strftime(self.RUSSIAN_DATE_FORMAT),
                original_value=str(date_value)
            )
        
        # Если date объект
        if isinstance(date_value, date):
            dt = datetime.combine(date_value, datetime.min.time())
            return DateProcessingResult(
                is_valid=True,
                parsed_date=dt,
                formatted_date=dt.strftime(self.RUSSIAN_DATE_FORMAT),
                original_value=str(date_value)
            )
        
        # Если число (timestamp)
        if isinstance(date_value, (int, float)):
            try:
                # Проверяем что это timestamp в секундах или миллисекундах
                if date_value > 1e10:  # Миллисекунды
                    dt = datetime.fromtimestamp(date_value / 1000)
                else:  # Секунды
                    dt = datetime.fromtimestamp(date_value)
                
                return DateProcessingResult(
                    is_valid=True,
                    parsed_date=dt,
                    formatted_date=dt.strftime(self.RUSSIAN_DATE_FORMAT),
                    original_value=str(date_value)
                )
            except (ValueError, OSError) as e:
                return DateProcessingResult(
                    is_valid=False,
                    original_value=str(date_value),
                    error_message=f"Некорректный timestamp: {e}"
                )
        
        # Приводим к строке и очищаем
        date_str = str(date_value).strip()
        
        if not date_str:
            return DateProcessingResult(
                is_valid=False,
                original_value=date_str,
                error_message="Пустая строка даты"
            )
        
        # Пробуем парсить по известным форматам
        for date_format in self.INPUT_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, date_format)
                
                # Валидация логичности даты
                validation_result = self._validate_date_logic(parsed_date)
                if not validation_result.is_valid:
                    return validation_result
                
                return DateProcessingResult(
                    is_valid=True,
                    parsed_date=parsed_date,
                    formatted_date=parsed_date.strftime(self.RUSSIAN_DATE_FORMAT),
                    original_value=date_str
                )
            
            except ValueError:
                continue
        
        # Если стандартные форматы не подошли, пробуем извлечь из текста
        extracted_result = self._extract_date_from_text(date_str)
        if extracted_result.is_valid:
            return extracted_result
        
        return DateProcessingResult(
            is_valid=False,
            original_value=date_str,
            error_message=f"Не удалось распознать формат даты: {date_str}"
        )
    
    def _extract_date_from_text(self, text: str) -> DateProcessingResult:
        """Извлечение даты из произвольного текста"""
        for pattern, date_format in self._compiled_patterns:
            match = pattern.search(text)
            if match:
                try:
                    parsed_date = datetime.strptime(match.group(0), date_format)
                    
                    # Валидация логичности даты
                    validation_result = self._validate_date_logic(parsed_date)
                    if not validation_result.is_valid:
                        continue
                    
                    return DateProcessingResult(
                        is_valid=True,
                        parsed_date=parsed_date,
                        formatted_date=parsed_date.strftime(self.RUSSIAN_DATE_FORMAT),
                        original_value=text
                    )
                except ValueError:
                    continue
        
        return DateProcessingResult(
            is_valid=False,
            original_value=text,
            error_message=f"Дата не найдена в тексте: {text}"
        )
    
    def _validate_date_logic(self, dt: datetime) -> DateProcessingResult:
        """Валидация логичности даты"""
        current_year = datetime.now().year
        
        # Проверяем разумные границы года
        if dt.year < 1900:
            return DateProcessingResult(
                is_valid=False,
                error_message=f"Год слишком ранний: {dt.year}"
            )
        
        if dt.year > current_year + 50:
            return DateProcessingResult(
                is_valid=False,
                error_message=f"Год слишком поздний: {dt.year}"
            )
        
        return DateProcessingResult(is_valid=True)
    
    def format_russian_date(self, dt: datetime, include_time: bool = False) -> str:
        """
        Форматирование даты в российский формат.
        
        Args:
            dt: Объект datetime
            include_time: Включать ли время
            
        Returns:
            str: Дата в российском формате
        """
        if include_time:
            return dt.strftime(self.RUSSIAN_DATETIME_FORMAT)
        return dt.strftime(self.RUSSIAN_DATE_FORMAT)
    
    def parse_date_range(self, start_date: Union[str, datetime, None], 
                        end_date: Union[str, datetime, None]) -> tuple[DateProcessingResult, DateProcessingResult]:
        """
        Парсинг диапазона дат.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            tuple: Результаты парсинга начальной и конечной дат
        """
        start_result = self.parse_date(start_date)
        end_result = self.parse_date(end_date)
        
        # Проверяем логику диапазона если обе даты валидны
        if (start_result.is_valid and end_result.is_valid and 
            start_result.parsed_date > end_result.parsed_date):
            
            start_result.error_message = "Начальная дата позже конечной"
            start_result.is_valid = False
            
            end_result.error_message = "Конечная дата раньше начальной"
            end_result.is_valid = False
        
        return start_result, end_result
    
    def is_valid_date(self, date_value: Union[str, datetime, date, None]) -> bool:
        """
        Быстрая проверка валидности даты.
        
        Args:
            date_value: Значение даты для проверки
            
        Returns:
            bool: True если дата валидна
        """
        return self.parse_date(date_value).is_valid
    
    def normalize_date(self, date_value: Union[str, datetime, date, None]) -> Optional[str]:
        """
        Нормализация даты к российскому формату.
        
        Args:
            date_value: Значение даты для нормализации
            
        Returns:
            Optional[str]: Дата в российском формате или None если невалидна
        """
        result = self.parse_date(date_value)
        return result.formatted_date if result.is_valid else None
    
    def get_date_object(self, date_value: Union[str, datetime, date, None]) -> Optional[datetime]:
        """
        Получение объекта datetime.
        
        Args:
            date_value: Значение даты
            
        Returns:
            Optional[datetime]: Объект datetime или None если невалидна
        """
        result = self.parse_date(date_value)
        return result.parsed_date if result.is_valid else None
    
    def compare_dates(self, date1: Union[str, datetime, date, None], 
                     date2: Union[str, datetime, date, None]) -> Optional[int]:
        """
        Сравнение двух дат.
        
        Args:
            date1: Первая дата
            date2: Вторая дата
            
        Returns:
            Optional[int]: -1 если date1 < date2, 0 если равны, 1 если date1 > date2, None если ошибка
        """
        dt1 = self.get_date_object(date1)
        dt2 = self.get_date_object(date2)
        
        if dt1 is None or dt2 is None:
            return None
        
        if dt1 < dt2:
            return -1
        elif dt1 > dt2:
            return 1
        else:
            return 0 