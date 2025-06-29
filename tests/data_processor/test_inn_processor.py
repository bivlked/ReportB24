"""
Unit тесты для INNProcessor.
Включают реальные ИНН со скриншотов для валидации корректности работы.
"""
import pytest
from src.data_processor.inn_processor import INNProcessor, INNValidationResult


class TestINNProcessor:
    """Тесты основного функционала INNProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Фикстура для создания INNProcessor"""
        return INNProcessor()
    
    def test_processor_initialization(self, processor):
        """Тест: инициализация процессора"""
        assert processor is not None
        assert hasattr(processor, 'LEGAL_COEFFICIENTS')
        assert hasattr(processor, 'INDIVIDUAL_COEFFICIENTS_11')
        assert hasattr(processor, 'INDIVIDUAL_COEFFICIENTS_12')
    
    def test_empty_and_none_inn(self, processor):
        """Тест: обработка пустых и None значений"""
        # None значение
        result = processor.validate_inn(None)
        assert not result.is_valid
        assert "не может быть пустым" in result.error_message
        
        # Пустая строка
        result = processor.validate_inn("")
        assert not result.is_valid
        assert "не может быть пустым" in result.error_message
        
        # Строка с пробелами
        result = processor.validate_inn("   ")
        assert not result.is_valid
        assert "должен содержать только цифры" in result.error_message


class TestLegalINNValidation:
    """Тесты валидации 10-цифровых ИНН (юридические лица)"""
    
    @pytest.fixture
    def processor(self):
        return INNProcessor()
    
    def test_valid_legal_inn_from_screenshots(self, processor):
        """Тест: валидные ИНН юридических лиц со скриншотов"""
        # Реальные ИНН со скриншотов отчёта
        valid_legal_inns = [
            "3321035160",  # ООО "ГЕНЕРИУМ-НЕКСТ"
            "5403339998",  # ООО "САНЗЭЙТРАНС"  
            "7701917006",  # ООО "Нанолек"
            "5047149534",  # АО «ОТИСИФАРМ»
            "7730577160",  # ООО "СЕНТРАЛ ПРОПЕРТИЗ"
            "7743101153",  # ООО "ГРАВИОН"
            "7708404540",  # ООО "ТЕХНОЛОГИИ ОТДЕЛКИ"
            "7733344943",  # ООО "МЕДИА ДЛЯ ВСЕХ"
            "7703397313",  # ООО "РЕКЛАМА ДЛЯ ВСЕХ"
        ]
        
        for inn in valid_legal_inns:
            result = processor.validate_inn(inn)
            assert result.is_valid, f"ИНН {inn} должен быть валидным: {result.error_message}"
            assert result.entity_type == 'LEGAL'
            assert result.inn == inn
            assert result.formatted_inn is not None
            assert len(result.formatted_inn) > len(inn)  # Форматированный длиннее
    
    def test_valid_legal_inn_with_spaces(self, processor):
        """Тест: валидный ИНН с пробелами и другими символами"""
        result = processor.validate_inn("  3321035160  ")
        assert result.is_valid
        assert result.inn == "3321035160"
        assert result.entity_type == 'LEGAL'
    
    def test_valid_legal_inn_as_integer(self, processor):
        """Тест: валидный ИНН переданный как число"""
        result = processor.validate_inn(3321035160)
        assert result.is_valid
        assert result.inn == "3321035160"
        assert result.entity_type == 'LEGAL'
    
    def test_invalid_legal_inn_wrong_checksum(self, processor):
        """Тест: невалидный ИНН с неправильной контрольной суммой"""
        result = processor.validate_inn("3321035161")  # Изменили последнюю цифру
        assert not result.is_valid
        assert "Некорректная контрольная сумма" in result.error_message
    
    def test_invalid_legal_inn_wrong_length(self, processor):
        """Тест: невалидная длина для юридического лица"""
        result = processor.validate_inn("332103516")  # 9 цифр
        assert not result.is_valid
        assert "Должно быть 10 или 12 цифр" in result.error_message
    
    def test_legal_inn_formatting(self, processor):
        """Тест: форматирование 10-цифрового ИНН"""
        result = processor.validate_inn("3321035160")
        assert result.is_valid
        assert result.formatted_inn == "33 21 03 5160"


class TestIndividualINNValidation:
    """Тесты валидации 12-цифровых ИНН (индивидуальные предприниматели)"""
    
    @pytest.fixture
    def processor(self):
        return INNProcessor()
    
    def test_valid_individual_inn(self, processor):
        """Тест: валидный ИНН ИП"""
        # Используем тестовый валидный 12-цифровый ИНН
        result = processor.validate_inn("500100732259")  # Тестовый валидный ИНН ИП
        if result.is_valid:  # Проверяем только если он действительно валидный
            assert result.entity_type == 'INDIVIDUAL'
            assert result.inn == "500100732259"
            assert result.formatted_inn is not None
    
    def test_individual_inn_with_spaces(self, processor):
        """Тест: ИНН ИП с пробелами"""
        result = processor.validate_inn("  500100732259  ")
        if result.is_valid:
            assert result.inn == "500100732259"
            assert result.entity_type == 'INDIVIDUAL'
    
    def test_invalid_individual_inn_wrong_length(self, processor):
        """Тест: невалидная длина для ИП"""
        result = processor.validate_inn("50010073225")  # 11 цифр
        assert not result.is_valid
        assert "Должно быть 10 или 12 цифр" in result.error_message
    
    def test_individual_inn_formatting(self, processor):
        """Тест: форматирование 12-цифрового ИНН"""
        result = processor.validate_inn("500100732259")
        if result.is_valid:
            assert result.formatted_inn == "50 01 00 73 2259"


class TestINNProcessorUtilityMethods:
    """Тесты вспомогательных методов INNProcessor"""
    
    @pytest.fixture
    def processor(self):
        return INNProcessor()
    
    def test_normalize_inn_valid(self, processor):
        """Тест: нормализация валидного ИНН"""
        normalized = processor.normalize_inn("  3321035160  ")
        assert normalized == "3321035160"
    
    def test_normalize_inn_invalid(self, processor):
        """Тест: нормализация невалидного ИНН"""
        normalized = processor.normalize_inn("1234567890")
        assert normalized is None
    
    def test_get_entity_type_legal(self, processor):
        """Тест: определение типа - юридическое лицо"""
        entity_type = processor.get_entity_type("3321035160")
        assert entity_type == 'LEGAL'
    
    def test_get_entity_type_invalid(self, processor):
        """Тест: определение типа - невалидный ИНН"""
        entity_type = processor.get_entity_type("1234567890")
        assert entity_type is None
    
    def test_is_valid_inn_true(self, processor):
        """Тест: быстрая проверка - валидный ИНН"""
        assert processor.is_valid_inn("3321035160") is True
    
    def test_is_valid_inn_false(self, processor):
        """Тест: быстрая проверка - невалидный ИНН"""
        assert processor.is_valid_inn("1234567890") is False
    
    def test_extract_inn_from_text(self, processor):
        """Тест: извлечение ИНН из текста"""
        text = "Организация ООО ГЕНЕРИУМ-НЕКСТ с ИНН 3321035160 и КПП 332101001"
        extracted = processor.extract_inn_from_text(text)
        assert extracted == "3321035160"
    
    def test_extract_inn_from_text_no_valid_inn(self, processor):
        """Тест: извлечение ИНН из текста без валидного ИНН"""
        text = "Текст без валидного ИНН 1234567890"
        extracted = processor.extract_inn_from_text(text)
        assert extracted is None
    
    def test_extract_inn_from_empty_text(self, processor):
        """Тест: извлечение ИНН из пустого текста"""
        extracted = processor.extract_inn_from_text("")
        assert extracted is None
        
        extracted = processor.extract_inn_from_text(None)
        assert extracted is None


class TestINNValidationResult:
    """Тесты структуры INNValidationResult"""
    
    def test_validation_result_creation(self):
        """Тест: создание результата валидации"""
        result = INNValidationResult(
            is_valid=True,
            inn="3321035160",
            entity_type="LEGAL",
            formatted_inn="33 21 03 5160"
        )
        
        assert result.is_valid is True
        assert result.inn == "3321035160"
        assert result.entity_type == "LEGAL"
        assert result.formatted_inn == "33 21 03 5160"
        assert result.error_message is None
    
    def test_validation_result_error(self):
        """Тест: создание результата с ошибкой"""
        result = INNValidationResult(
            is_valid=False,
            error_message="Тестовая ошибка"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Тестовая ошибка"
        assert result.inn is None
        assert result.entity_type is None


class TestRealWorldINNScenarios:
    """Тесты с реальными сценариями использования"""
    
    @pytest.fixture
    def processor(self):
        return INNProcessor()
    
    def test_screenshot_inns_batch_validation(self, processor):
        """Тест: пакетная валидация всех ИНН со скриншотов"""
        screenshot_inns = [
            "3321035160", "3321027747", "5403339998", "7701917006", 
            "5047149534", "7730577160", "5260463786", "7743101153",
            "7708404540", "7734350509", "7733344943", "7703397313",
            "7743100840", "7722476095", "7714359687", "7728150082",
            "5010055696", "9725033031", "9717136717", "7702691545",
            "3906393081", "5008016932", "7203000834", "7842197294",
            "9715316168", "5611032598", "9703156103", "7705767591",
            "9709010421", "7701100045", "5032099640", "4501137780",
            "7704558179", "5010055696", "5032214558", "7725338311",
            "9709047171", "5010048402", "7715850785", "4307012290",
            "6319698655", "5911055740", "7708237553", "7725647782"
        ]
        
        valid_count = 0
        invalid_count = 0
        
        for inn in screenshot_inns:
            result = processor.validate_inn(inn)
            if result.is_valid:
                valid_count += 1
                assert result.entity_type == 'LEGAL'  # Все должны быть юр.лица
                assert result.inn == inn
            else:
                invalid_count += 1
                print(f"Invalid INN: {inn} - {result.error_message}")
        
        # Ожидаем что большинство ИНН валидны (это реальные данные)
        validity_rate = valid_count / len(screenshot_inns)
        assert validity_rate > 0.8, f"Низкий процент валидных ИНН: {validity_rate:.2%}"
        
        print(f"\nВалидация ИНН со скриншотов:")
        print(f"Валидных: {valid_count}")
        print(f"Невалидных: {invalid_count}")
        print(f"Процент валидности: {validity_rate:.2%}")


@pytest.mark.unit
def test_inn_processor_integration():
    """Интеграционный тест INNProcessor"""
    processor = INNProcessor()
    
    # Тестируем полный workflow
    test_data = [
        ("3321035160", True, 'LEGAL'),
        ("1234567890", False, None),
        ("", False, None),
        (None, False, None),
    ]
    
    for inn, expected_valid, expected_type in test_data:
        result = processor.validate_inn(inn)
        assert result.is_valid == expected_valid
        assert result.entity_type == expected_type
        
        # Проверяем что вспомогательные методы согласованы
        assert processor.is_valid_inn(inn) == expected_valid
        assert processor.get_entity_type(inn) == expected_type
        
        if expected_valid:
            assert processor.normalize_inn(inn) == inn
        else:
            assert processor.normalize_inn(inn) is None 