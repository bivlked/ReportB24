"""
Модуль конфигурации для генератора отчётов Bitrix24.

Обеспечивает централизованное управление настройками,
валидацию конфигурации и системных требований.
"""

from .config_reader import (
    ConfigReader,
    BitrixConfig,
    AppConfig,
    ReportPeriodConfig,
    create_config_reader
)

from .settings import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    BitrixAPISettings,
    DataProcessingSettings,
    ExcelSettings,
    LoggingSettings,
    ValidationSettings,
    TestSettings,
    get_environment_settings,
    get_runtime_info,
    get_all_settings
)

from .validation import (
    ValidationResult,
    SystemValidator,
    ConfigValidator,
    NetworkValidator,
    ComprehensiveValidator,
    validate_system
)

__all__ = [
    # Config Reader
    'ConfigReader',
    'BitrixConfig',
    'AppConfig', 
    'ReportPeriodConfig',
    'create_config_reader',
    
    # Settings
    'APP_NAME',
    'APP_VERSION',
    'APP_DESCRIPTION',
    'BitrixAPISettings',
    'DataProcessingSettings',
    'ExcelSettings',
    'LoggingSettings',
    'ValidationSettings',
    'TestSettings',
    'get_environment_settings',
    'get_runtime_info',
    'get_all_settings',
    
    # Validation
    'ValidationResult',
    'SystemValidator',
    'ConfigValidator',
    'NetworkValidator',
    'ComprehensiveValidator',
    'validate_system'
] 