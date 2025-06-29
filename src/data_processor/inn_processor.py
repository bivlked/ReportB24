"""
INN (ИНН) Processor для валидации и обработки российских ИНН.
Поддерживает 10-цифровые (юридические лица) и 12-цифровые (ИП) ИНН.
"""
import re
from typing import Optional, Tuple, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class INNValidationResult:
    """Результат валидации ИНН"""
    is_valid: bool
    inn: Optional[str] = None
    entity_type: Optional[str] = None  # 'LEGAL' или 'INDIVIDUAL'
    error_message: Optional[str] = None
    formatted_inn: Optional[str] = None


class INNProcessor:
    """
    Процессор для валидации и обработки ИНН.
    
    Поддерживает:
    - 10-цифровые ИНН (юридические лица)
    - 12-цифровые ИНН (индивидуальные предприниматели)
    - Валидация контрольных сумм по российскому алгоритму
    - Форматирование и нормализация
    """
    
    # Коэффициенты для расчёта контрольных сумм
    LEGAL_COEFFICIENTS = [2, 4, 10, 3, 5, 9, 4, 6, 8]  # Для 10-цифрового ИНН
    INDIVIDUAL_COEFFICIENTS_11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]  # Для 11-й цифры 12-цифрового ИНН
    INDIVIDUAL_COEFFICIENTS_12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]  # Для 12-й цифры 12-цифрового ИНН
    
    def validate_inn(self, inn: Union[str, int, None]) -> INNValidationResult:
        """
        Валидация ИНН по российским стандартам.
        
        Args:
            inn: ИНН для валидации (строка или число)
            
        Returns:
            INNValidationResult: Результат валидации
        """
        # Проверяем на None или пустое значение
        if inn is None or inn == "":
            return INNValidationResult(
                is_valid=False,
                error_message="ИНН не может быть пустым"
            )
        
        # Нормализуем ИНН - приводим к строке и убираем пробелы
        inn_str = str(inn).strip()
        
        # Удаляем все нецифровые символы
        clean_inn = re.sub(r'\D', '', inn_str)
        
        if not clean_inn:
            return INNValidationResult(
                is_valid=False,
                error_message="ИНН должен содержать только цифры"
            )
        
        # Проверяем длину
        if len(clean_inn) == 10:
            return self._validate_legal_inn(clean_inn)
        elif len(clean_inn) == 12:
            return self._validate_individual_inn(clean_inn)
        else:
            return INNValidationResult(
                is_valid=False,
                error_message=f"Некорректная длина ИНН: {len(clean_inn)}. Должно быть 10 или 12 цифр"
            )
    
    def _validate_legal_inn(self, inn: str) -> INNValidationResult:
        """
        Валидация 10-цифрового ИНН (юридические лица).
        
        Args:
            inn: 10-цифровый ИНН
            
        Returns:
            INNValidationResult: Результат валидации
        """
        if len(inn) != 10:
            return INNValidationResult(
                is_valid=False,
                error_message="ИНН юридического лица должен содержать 10 цифр"
            )
        
        try:
            # Вычисляем контрольную сумму
            digits = [int(d) for d in inn]
            control_sum = sum(digit * coeff for digit, coeff in zip(digits[:9], self.LEGAL_COEFFICIENTS))
            expected_check_digit = control_sum % 11
            
            if expected_check_digit > 9:
                expected_check_digit = expected_check_digit % 10
            
            actual_check_digit = digits[9]
            
            if expected_check_digit == actual_check_digit:
                return INNValidationResult(
                    is_valid=True,
                    inn=inn,
                    entity_type='LEGAL',
                    formatted_inn=self._format_legal_inn(inn)
                )
            else:
                return INNValidationResult(
                    is_valid=False,
                    error_message=f"Некорректная контрольная сумма. Ожидается {expected_check_digit}, получено {actual_check_digit}"
                )
        
        except (ValueError, IndexError) as e:
            return INNValidationResult(
                is_valid=False,
                error_message=f"Ошибка при валидации ИНН: {e}"
            )
    
    def _validate_individual_inn(self, inn: str) -> INNValidationResult:
        """
        Валидация 12-цифрового ИНН (индивидуальные предприниматели).
        
        Args:
            inn: 12-цифровый ИНН
            
        Returns:
            INNValidationResult: Результат валидации
        """
        if len(inn) != 12:
            return INNValidationResult(
                is_valid=False,
                error_message="ИНН индивидуального предпринимателя должен содержать 12 цифр"
            )
        
        try:
            digits = [int(d) for d in inn]
            
            # Проверяем 11-ю цифру
            control_sum_11 = sum(digit * coeff for digit, coeff in zip(digits[:10], self.INDIVIDUAL_COEFFICIENTS_11))
            expected_check_digit_11 = control_sum_11 % 11
            
            if expected_check_digit_11 > 9:
                expected_check_digit_11 = expected_check_digit_11 % 10
            
            # Проверяем 12-ю цифру
            control_sum_12 = sum(digit * coeff for digit, coeff in zip(digits[:11], self.INDIVIDUAL_COEFFICIENTS_12))
            expected_check_digit_12 = control_sum_12 % 11
            
            if expected_check_digit_12 > 9:
                expected_check_digit_12 = expected_check_digit_12 % 10
            
            actual_check_digit_11 = digits[10]
            actual_check_digit_12 = digits[11]
            
            if (expected_check_digit_11 == actual_check_digit_11 and 
                expected_check_digit_12 == actual_check_digit_12):
                
                return INNValidationResult(
                    is_valid=True,
                    inn=inn,
                    entity_type='INDIVIDUAL',
                    formatted_inn=self._format_individual_inn(inn)
                )
            else:
                return INNValidationResult(
                    is_valid=False,
                    error_message=f"Некорректная контрольная сумма. 11-я цифра: ожидается {expected_check_digit_11}, получено {actual_check_digit_11}. 12-я цифра: ожидается {expected_check_digit_12}, получено {actual_check_digit_12}"
                )
        
        except (ValueError, IndexError) as e:
            return INNValidationResult(
                is_valid=False,
                error_message=f"Ошибка при валидации ИНН: {e}"
            )
    
    def _format_legal_inn(self, inn: str) -> str:
        """Форматирование 10-цифрового ИНН"""
        return f"{inn[:2]} {inn[2:4]} {inn[4:6]} {inn[6:]}"
    
    def _format_individual_inn(self, inn: str) -> str:
        """Форматирование 12-цифрового ИНН"""
        return f"{inn[:2]} {inn[2:4]} {inn[4:6]} {inn[6:8]} {inn[8:]}"
    
    def extract_inn_from_text(self, text: str) -> Optional[str]:
        """
        Извлечение ИНН из текста.
        
        Args:
            text: Текст, содержащий ИНН
            
        Returns:
            Optional[str]: Найденный ИНН или None
        """
        if not text:
            return None
        
        # Ищем последовательности из 10 или 12 цифр
        inn_patterns = re.findall(r'\b\d{10}\b|\b\d{12}\b', text)
        
        for potential_inn in inn_patterns:
            result = self.validate_inn(potential_inn)
            if result.is_valid:
                return potential_inn
        
        return None
    
    def normalize_inn(self, inn: Union[str, int, None]) -> Optional[str]:
        """
        Нормализация ИНН - приведение к стандартному виду.
        
        Args:
            inn: ИНН для нормализации
            
        Returns:
            Optional[str]: Нормализованный ИНН или None если невалидный
        """
        result = self.validate_inn(inn)
        return result.inn if result.is_valid else None
    
    def get_entity_type(self, inn: Union[str, int, None]) -> Optional[str]:
        """
        Определение типа субъекта по ИНН.
        
        Args:
            inn: ИНН для анализа
            
        Returns:
            Optional[str]: 'LEGAL' для юридических лиц, 'INDIVIDUAL' для ИП, None если невалидный
        """
        result = self.validate_inn(inn)
        return result.entity_type if result.is_valid else None
    
    def is_valid_inn(self, inn: Union[str, int, None]) -> bool:
        """
        Быстрая проверка валидности ИНН.
        
        Args:
            inn: ИНН для проверки
            
        Returns:
            bool: True если ИНН валидный
        """
        return self.validate_inn(inn).is_valid
    
    def format_inn(self, inn: Union[str, int, None]) -> str:
        """
        Форматирование ИНН для отображения.
        
        Args:
            inn: ИНН для форматирования
            
        Returns:
            str: Отформатированный ИНН или исходная строка если невалидный
        """
        result = self.validate_inn(inn)
        if result.is_valid and result.formatted_inn:
            return result.formatted_inn
        return str(inn) if inn is not None else "" 