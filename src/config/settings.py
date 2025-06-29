"""
Настройки и константы приложения.

Централизованное хранение всех настроек, констант и параметров
конфигурации для генератора отчётов Bitrix24.
"""

import os
from pathlib import Path
from typing import Dict, Any, List


# ==================== ВЕРСИЯ ПРИЛОЖЕНИЯ ====================

APP_NAME = "Генератор отчётов Bitrix24"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Система генерации Excel отчётов на основе данных Bitrix24"


# ==================== ПУТИ И ФАЙЛЫ ====================

# Корневая директория проекта
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Путь к файлу конфигурации по умолчанию
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.ini"

# Директория для логов
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"

# Директория для временных файлов
DEFAULT_TEMP_DIR = PROJECT_ROOT / "temp"


# ==================== API НАСТРОЙКИ ====================

# Настройки Bitrix24 API
class BitrixAPISettings:
    """Настройки для работы с Bitrix24 API."""
    
    # Максимальное количество запросов в секунду (согласно лимитам Bitrix24)
    MAX_REQUESTS_PER_SECOND = 2
    
    # Таймаут запросов в секундах
    REQUEST_TIMEOUT = 30
    
    # Количество попыток повтора при ошибках
    MAX_RETRY_ATTEMPTS = 3
    
    # Размер страницы для пагинации
    DEFAULT_PAGE_SIZE = 50
    
    # Максимальный размер страницы
    MAX_PAGE_SIZE = 50
    
    # Методы API для работы с сущностями
    API_METHODS = {
        'get_invoices': 'crm.item.list',
        'get_requisite_links': 'crm.requisite.link.list',
        'get_requisite_details': 'crm.requisite.get'
    }
    
    # ID типа сущности для "Счёта" (Smart Invoice)
    SMART_INVOICE_ENTITY_TYPE_ID = 31
    
    # Статусы счетов для фильтрации
    INVOICE_STATUSES = {
        'DRAFT': 'D',           # Черновик
        'SENT': 'S',            # Отправлен
        'VIEWED': 'V',          # Просмотрен  
        'PAID': 'P',            # Оплачен
        'DECLINED': 'R'         # Отклонён
    }


# ==================== ОБРАБОТКА ДАННЫХ ====================

class DataProcessingSettings:
    """Настройки обработки данных."""
    
    # Форматы дат
    RUSSIAN_DATE_FORMATS = [
        "%d.%m.%Y",      # 01.12.2023
        "%d.%m.%y",      # 01.12.23
        "%d/%m/%Y",      # 01/12/2023
        "%d-%m-%Y"       # 01-12-2023
    ]
    
    ISO_DATE_FORMATS = [
        "%Y-%m-%d",              # 2023-12-01
        "%Y-%m-%dT%H:%M:%S",     # 2023-12-01T15:30:45
        "%Y-%m-%dT%H:%M:%SZ"     # 2023-12-01T15:30:45Z
    ]
    
    # Настройки валют
    DEFAULT_CURRENCY = "RUB"
    CURRENCY_SYMBOLS = {
        "RUB": "₽",
        "USD": "$", 
        "EUR": "€"
    }
    
    # Ставки НДС
    VAT_RATES = {
        20: "20%",
        10: "10%", 
        0: "0%",
        None: "Без НДС"
    }
    
    # Минимальная и максимальная длина ИНН
    INN_LENGTH_INDIVIDUAL = 12  # ИП
    INN_LENGTH_ORGANIZATION = 10  # Юрлица
    
    # Диапазоны годов для валидации дат
    MIN_YEAR = 2000
    MAX_YEAR = 2100


# ==================== EXCEL ГЕНЕРАЦИЯ ====================

class ExcelSettings:
    """Настройки для генерации Excel файлов."""
    
    # Цветовая схема (точно по скриншотам)
    COLORS = {
        'HEADER_FILL': '#C4D79B',        # Зелёный фон заголовков
        'NO_VAT_FILL': '#D9D9D9',        # Серый фон для "Без НДС"
        'NORMAL_FILL': '#FFFFFF',        # Белый фон для обычных строк
        'BORDER_COLOR': '#000000'        # Чёрные границы
    }
    
    # Настройки шрифтов
    FONTS = {
        'DEFAULT_FONT': 'Calibri',
        'DEFAULT_SIZE': 11,
        'HEADER_SIZE': 11,
        'HEADER_BOLD': True
    }
    
    # Выравнивание колонок
    COLUMN_ALIGNMENTS = {
        'serial_number': 'center',    # № п/п
        'contractor': 'left',         # Контрагент  
        'inn': 'center',             # ИНН
        'shipping_date': 'right',     # Дата отгрузки
        'invoice_number': 'center',   # № счёта
        'amount': 'right',           # Сумма
        'vat_amount': 'right',       # Сумма НДС
        'vat_rate': 'center'         # Ставка НДС
    }
    
    # Ширины колонок (в символах)
    COLUMN_WIDTHS = {
        'serial_number': 8,      # № п/п
        'contractor': 35,        # Контрагент
        'inn': 15,              # ИНН  
        'shipping_date': 12,     # Дата отгрузки
        'invoice_number': 12,    # № счёта
        'amount': 15,           # Сумма
        'vat_amount': 15,       # Сумма НДС
        'vat_rate': 10          # Ставка НДС
    }
    
    # Заголовки колонок (русские)
    COLUMN_HEADERS = {
        'serial_number': '№ п/п',
        'contractor': 'Контрагент',
        'inn': 'ИНН',
        'shipping_date': 'Дата отгрузки',
        'invoice_number': '№ счёта',
        'amount': 'Сумма',
        'vat_amount': 'Сумма НДС',
        'vat_rate': 'Ставка НДС'
    }
    
    # Начальные позиции (с отступами)
    LAYOUT = {
        'START_ROW': 2,          # Начальная строка данных (1-indexed)
        'START_COLUMN': 2,       # Начальная колонка данных (1-indexed)
        'HEADER_ROW': 1,         # Строка заголовков (1-indexed)
        'FREEZE_PANES': 'B2'     # Фиксация заголовков
    }


# ==================== ЛОГИРОВАНИЕ ====================

class LoggingSettings:
    """Настройки системы логирования."""
    
    # Уровни логирования
    LOG_LEVEL = "INFO"
    
    # Формат логов
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Формат даты в логах  
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Максимальный размер лог-файла (в байтах)
    MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    # Количество резервных копий лог-файлов
    LOG_BACKUP_COUNT = 5


# ==================== ВАЛИДАЦИЯ ====================

class ValidationSettings:
    """Настройки валидации данных."""
    
    # Обязательные поля для счетов
    REQUIRED_INVOICE_FIELDS = [
        'ACCOUNT_NUMBER',    # Номер счёта
        'OPPORTUNITY',       # Сумма
        'UF_CRM_INN'        # ИНН (пользовательское поле)
    ]
    
    # Минимальные требования к данным
    MIN_AMOUNT = 0.01        # Минимальная сумма
    MAX_AMOUNT = 999999999   # Максимальная сумма
    
    # Регулярные выражения для валидации
    PATTERNS = {
        'WEBHOOK_URL': r'https://[\w\-.]+(\.bitrix24\.[a-z]{2,3})?/rest/\d+/[a-zA-Z0-9_]+/?$',
        'RUSSIAN_DATE': r'\d{2}\.\d{2}\.\d{4}',
        'INVOICE_NUMBER': r'[A-Za-z0-9\-/]+',
        'INN_10': r'^\d{10}$',       # ИНН юрлица
        'INN_12': r'^\d{12}$'        # ИНН ИП
    }


# ==================== ТЕСТИРОВАНИЕ ====================

class TestSettings:
    """Настройки для тестирования."""
    
    # Минимальное покрытие тестами
    MIN_COVERAGE_PERCENT = 95
    
    # Тестовые данные
    TEST_CONFIG_DATA = {
        'BitrixAPI': {
            'webhookurl': 'https://test.bitrix24.ru/rest/1/test_webhook_code/'
        },
        'AppSettings': {
            'defaultsavefolder': 'test_reports',
            'defaultfilename': 'test_report.xlsx'
        },
        'ReportPeriod': {
            'startdate': '01.01.2023',
            'enddate': '31.12.2023'
        }
    }
    
    # Тестовые ИНН (валидные)
    VALID_TEST_INNS = {
        'organization': '7710140679',      # 10 цифр
        'individual': '370214631827'      # 12 цифр
    }


# ==================== УТИЛИТЫ ====================

def get_environment_settings() -> Dict[str, Any]:
    """
    Возвращает настройки окружения.
    
    Returns:
        Dict: Словарь с настройками окружения
    """
    return {
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'production'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', LoggingSettings.LOG_LEVEL),
        'CONFIG_PATH': os.getenv('CONFIG_PATH', str(DEFAULT_CONFIG_PATH))
    }


def get_runtime_info() -> Dict[str, Any]:
    """
    Возвращает информацию о рантайме.
    
    Returns:
        Dict: Информация о текущем состоянии приложения
    """
    import sys
    import platform
    
    return {
        'app_name': APP_NAME,
        'app_version': APP_VERSION,
        'python_version': sys.version,
        'platform': platform.platform(),
        'working_directory': os.getcwd(),
        'project_root': str(PROJECT_ROOT)
    }


# ==================== ЭКСПОРТ НАСТРОЕК ====================

# Агрегированные настройки для удобного доступа
ALL_SETTINGS = {
    'api': BitrixAPISettings,
    'data': DataProcessingSettings, 
    'excel': ExcelSettings,
    'logging': LoggingSettings,
    'validation': ValidationSettings,
    'testing': TestSettings
}


def get_all_settings() -> Dict[str, Any]:
    """
    Возвращает все настройки приложения.
    
    Returns:
        Dict: Полный набор настроек
    """
    return {
        'app_info': {
            'name': APP_NAME,
            'version': APP_VERSION,
            'description': APP_DESCRIPTION
        },
        'paths': {
            'project_root': PROJECT_ROOT,
            'config_path': DEFAULT_CONFIG_PATH,
            'log_dir': DEFAULT_LOG_DIR,
            'temp_dir': DEFAULT_TEMP_DIR
        },
        'settings': ALL_SETTINGS,
        'environment': get_environment_settings(),
        'runtime': get_runtime_info()
    } 