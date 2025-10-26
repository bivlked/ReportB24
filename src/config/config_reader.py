"""
Модуль для чтения и валидации конфигурационного файла.

Обеспечивает централизованное чтение config.ini и предоставляет
валидированные настройки для всех компонентов приложения.

Версия 2.1.0: добавлена поддержка .env файлов для безопасного хранения секретов.
"""

import configparser
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from dotenv import dotenv_values, load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    dotenv_values = None
    load_dotenv = None


@dataclass
class BitrixConfig:
    """Конфигурация для подключения к Bitrix24."""
    webhook_url: str
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.webhook_url:
            raise ValueError("Webhook URL не может быть пустым")
        
        # Проверка формата webhook URL
        webhook_pattern = r"https://[\w\-.]+(\.bitrix24\.[a-z]{2,3})?/rest/\d+/[a-zA-Z0-9_]+/?$"
        if not re.match(webhook_pattern, self.webhook_url):
            raise ValueError(f"Некорректный формат webhook URL: {self.webhook_url}")


@dataclass  
class AppConfig:
    """Настройки приложения."""
    default_save_folder: str
    default_filename: str
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.default_save_folder:
            raise ValueError("Папка сохранения не может быть пустой")
        
        if not self.default_filename:
            raise ValueError("Имя файла по умолчанию не может быть пустым")
        
        # Проверка расширения файла
        if not self.default_filename.endswith('.xlsx'):
            raise ValueError("Файл должен иметь расширение .xlsx")


@dataclass
class ReportPeriodConfig:
    """Конфигурация периода отчёта."""
    start_date: str
    end_date: str
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if not self.start_date or not self.end_date:
            raise ValueError("Даты начала и окончания периода обязательны")
        
        # Проверка формата дат
        date_pattern = r"\d{2}\.\d{2}\.\d{4}"
        if not re.match(date_pattern, self.start_date):
            raise ValueError(f"Некорректный формат даты начала: {self.start_date}")
        
        if not re.match(date_pattern, self.end_date):
            raise ValueError(f"Некорректный формат даты окончания: {self.end_date}")
        
        # Проверка корректности дат
        try:
            from datetime import datetime
            start_dt = datetime.strptime(self.start_date, "%d.%m.%Y")
            end_dt = datetime.strptime(self.end_date, "%d.%m.%Y")
            
            if start_dt > end_dt:
                raise ValueError(f"Дата начала ({self.start_date}) не может быть позже даты окончания ({self.end_date})")
                
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError(f"Некорректная дата: {e}")
            raise


class ConfigReader:
    """
    Класс для чтения и валидации конфигурационного файла.
    
    Обеспечивает централизованное управление конфигурацией приложения
    с автоматической валидацией всех параметров.
    """
    
    def __init__(self, config_path: str = "config.ini"):
        """
        Инициализация ConfigReader.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._bitrix_config: Optional[BitrixConfig] = None
        self._app_config: Optional[AppConfig] = None
        self._report_period_config: Optional[ReportPeriodConfig] = None
        
    def load_config(self) -> None:
        """
        Загружает конфигурацию из файла.
        
        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            configparser.Error: Если файл имеет некорректный формат
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        
        try:
            self.config.read(self.config_path, encoding='utf-8')
        except configparser.Error as e:
            raise ValueError(f"Ошибка чтения файла конфигурации: {e}")
        
        # Валидация обязательных секций
        required_sections = ['BitrixAPI', 'AppSettings', 'ReportPeriod']
        missing_sections = [section for section in required_sections 
                          if section not in self.config.sections()]
        
        if missing_sections:
            raise ValueError(f"Отсутствуют обязательные секции в config.ini: {missing_sections}")
    
    def get_bitrix_config(self) -> BitrixConfig:
        """
        Возвращает конфигурацию Bitrix24.
        
        Returns:
            BitrixConfig: Валидированная конфигурация Bitrix24
        """
        if self._bitrix_config is None:
            if 'BitrixAPI' not in self.config.sections():
                raise ValueError("Секция 'BitrixAPI' не найдена в config.ini")
            
            webhook_url = self.config.get('BitrixAPI', 'webhookurl', fallback='')
            self._bitrix_config = BitrixConfig(webhook_url=webhook_url)
        
        return self._bitrix_config
    
    def get_app_config(self) -> AppConfig:
        """
        Возвращает конфигурацию приложения.
        
        Returns:
            AppConfig: Валидированная конфигурация приложения
        """
        if self._app_config is None:
            if 'AppSettings' not in self.config.sections():
                raise ValueError("Секция 'AppSettings' не найдена в config.ini")
            
            save_folder = self.config.get('AppSettings', 'defaultsavefolder', fallback='')
            filename = self.config.get('AppSettings', 'defaultfilename', fallback='')
            
            self._app_config = AppConfig(
                default_save_folder=save_folder,
                default_filename=filename
            )
        
        return self._app_config
    
    def get_report_period_config(self) -> ReportPeriodConfig:
        """
        Возвращает конфигурацию периода отчёта.
        
        Returns:
            ReportPeriodConfig: Валидированная конфигурация периода
        """
        if self._report_period_config is None:
            if 'ReportPeriod' not in self.config.sections():
                raise ValueError("Секция 'ReportPeriod' не найдена в config.ini")
            
            start_date = self.config.get('ReportPeriod', 'startdate', fallback='')
            end_date = self.config.get('ReportPeriod', 'enddate', fallback='')
            
            self._report_period_config = ReportPeriodConfig(
                start_date=start_date,
                end_date=end_date
            )
        
        return self._report_period_config
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Возвращает всю конфигурацию в виде словаря.
        
        Returns:
            Dict: Словарь со всеми конфигурационными объектами
        """
        return {
            'bitrix': self.get_bitrix_config(),
            'app': self.get_app_config(),
            'report_period': self.get_report_period_config()
        }
    
    def validate_all(self) -> bool:
        """
        Проводит полную валидацию всех секций конфигурации.
        
        Returns:
            bool: True если вся конфигурация валидна
            
        Raises:
            ValueError: При обнаружении ошибок в конфигурации
        """
        try:
            self.load_config()
            self.get_bitrix_config()
            self.get_app_config()
            self.get_report_period_config()
            return True
        except (ValueError, FileNotFoundError) as e:
            raise ValueError(f"Ошибка валидации конфигурации: {e}")
    
    def get_safe_save_path(self, custom_filename: Optional[str] = None) -> Path:
        """
        Возвращает безопасный путь для сохранения файла.
        
        Args:
            custom_filename: Пользовательское имя файла (опционально)
            
        Returns:
            Path: Полный путь к файлу для сохранения
        """
        app_config = self.get_app_config()
        filename = custom_filename or app_config.default_filename
        
        # Обеспечиваем корректное расширение
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        save_path = Path(app_config.default_save_folder)
        
        # Создаём директорию если не существует
        save_path.mkdir(parents=True, exist_ok=True)
        
        return save_path / filename


def create_config_reader(config_path: str = "config.ini") -> ConfigReader:
    """
    Фабричная функция для создания и инициализации ConfigReader.
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        ConfigReader: Инициализированный объект ConfigReader
    """
    reader = ConfigReader(config_path)
    reader.load_config()
    return reader 


class SecureConfigReader(ConfigReader):
    """
    Расширенный ConfigReader с поддержкой .env файлов для безопасного хранения секретов.
    
    Реализует гибридную систему конфигурации:
    - Приоритет: os.environ > .env > config.ini
    - Автоматическая миграция секретов из config.ini в .env
    - Маскирование конфиденциальных данных в логах
    - Обратная совместимость с существующим ConfigReader
    
    Версия: 2.1.0
    """
    
    # Список конфиденциальных ключей, которые должны храниться в .env
    SENSITIVE_KEYS = {
        'webhook_url', 'webhookurl', 'api_key', 'secret_key', 
        'password', 'token', 'access_token', 'private_key'
    }
    
    def __init__(self, config_path: str = "config.ini", env_path: str = ".env"):
        """
        Инициализация SecureConfigReader.
        
        Args:
            config_path: Путь к файлу конфигурации
            env_path: Путь к .env файлу с секретами
        """
        super().__init__(config_path)
        self.env_path = Path(env_path)
        self._env_values: Dict[str, str] = {}
        self._merged_config: Dict[str, Dict[str, str]] = {}
        self._migration_performed = False
        
    def _load_env_values(self) -> Dict[str, str]:
        """
        Загружает значения из .env файла без изменения os.environ.
        
        Returns:
            Dict[str, str]: Словарь с переменными из .env файла
        """
        if not HAS_DOTENV:
            print("Warning: python-dotenv не установлен. .env файлы не поддерживаются.")
            return {}
        
        if not self.env_path.exists():
            return {}
        
        try:
            return dotenv_values(str(self.env_path)) or {}
        except Exception as e:
            print(f"Warning: Ошибка чтения {self.env_path}: {e}")
            return {}
    
    def _get_merged_value(self, section: str, key: str, fallback: str = '') -> str:
        """
        Получает значение с учётом приоритета: os.environ > .env > config.ini
        
        Args:
            section: Секция конфигурации
            key: Ключ параметра
            fallback: Значение по умолчанию
            
        Returns:
            str: Значение с учётом приоритета источников
        """
        # Формируем возможные имена переменных окружения
        env_variants = [
            f"{section.upper()}_{key.upper()}",
            key.upper(),
            f"BITRIX24_{key.upper()}" if section.lower() == 'bitrixapi' else f"{section.upper()}_{key.upper()}"
        ]
        
        # 1. Приоритет: переменные окружения
        for env_key in env_variants:
            if env_key in os.environ:
                return os.environ[env_key]
        
        # 2. Приоритет: .env файл
        for env_key in env_variants:
            if env_key in self._env_values:
                return self._env_values[env_key]
        
        # 3. Приоритет: config.ini
        if section in self.config.sections():
            return self.config.get(section, key, fallback=fallback)
        
        return fallback
    
    def _mask_sensitive_value(self, key: str, value: str) -> str:
        """
        Маскирует конфиденциальные значения для логирования.
        
        Args:
            key: Ключ параметра
            value: Значение параметра
            
        Returns:
            str: Маскированное значение
        """
        if not value or key.lower() not in self.SENSITIVE_KEYS:
            return value
        
        # Специальная обработка для webhook URL
        if 'webhook' in key.lower() and 'https://' in value:
            # Маскируем токен в URL: https://portal.bitrix24.ru/rest/12345/abc123def456 -> https://portal.bitrix24.ru/rest/12345/***/
            import re
            masked = re.sub(r'(/rest/\d+/)[a-zA-Z0-9_]+(/?)$', r'\1***/\2', value)
            return masked
        
        # Общее маскирование для других секретов
        if len(value) <= 4:
            return "***"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]
    
    def _migrate_secrets_to_env(self) -> bool:
        """
        Автоматически мигрирует секреты из config.ini в .env файл.
        
        Returns:
            bool: True если миграция была выполнена
        """
        if self._migration_performed or not self.config.sections():
            return False
        
        secrets_to_migrate = {}
        
        # Ищем конфиденциальные ключи в config.ini
        for section_name in self.config.sections():
            for key, value in self.config[section_name].items():
                if key.lower() in self.SENSITIVE_KEYS and value:
                    env_key = f"{section_name.upper()}_{key.upper()}"
                    secrets_to_migrate[env_key] = value
        
        if not secrets_to_migrate:
            self._migration_performed = True
            return False
        
        # Создаём или дополняем .env файл
        env_content = []
        
        # Читаем существующий .env если есть
        if self.env_path.exists():
            try:
                with open(self.env_path, 'r', encoding='utf-8') as f:
                    env_content = f.readlines()
            except Exception as e:
                print(f"Warning: Не удалось прочитать существующий .env файл: {e}")
        
        # Добавляем новые секреты
        migrated_keys = []
        for env_key, value in secrets_to_migrate.items():
            # Проверяем, что ключ ещё не существует в .env
            key_exists = any(line.strip().startswith(f"{env_key}=") for line in env_content)
            if not key_exists:
                env_content.append(f"{env_key}={value}\n")
                migrated_keys.append(env_key)
        
        if migrated_keys:
            try:
                # Обеспечиваем директорию
                self.env_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Записываем обновлённый .env
                with open(self.env_path, 'w', encoding='utf-8') as f:
                    f.writelines(env_content)
                
                print(f"✅ Мигрированы секреты в .env: {', '.join(migrated_keys)}")
                print(f"⚠️  Рекомендуется удалить эти ключи из config.ini и добавить .env в .gitignore")
                
                # Перезагружаем .env значения после миграции
                self._env_values = self._load_env_values()
                
                self._migration_performed = True
                return True
                
            except Exception as e:
                print(f"Warning: Не удалось записать .env файл: {e}")
                return False
        
        self._migration_performed = True
        return False
    
    def load_config(self) -> None:
        """
        Загружает конфигурацию из всех источников с учётом приоритета.
        
        Raises:
            FileNotFoundError: Если config.ini не найден
            ValueError: Если конфигурация имеет ошибки
        """
        # Загружаем переменные из .env в окружение
        if HAS_DOTENV and load_dotenv and self.env_path.exists():
            load_dotenv(self.env_path)
        
        # Загружаем базовую конфигурацию
        super().load_config()
        
        # Загружаем .env значения
        self._env_values = self._load_env_values()
        
        # Выполняем автоматическую миграцию секретов
        self._migrate_secrets_to_env()
        
        # Обновляем кэшированные конфигурации для перезагрузки с новыми источниками
        self._bitrix_config = None
        self._app_config = None
        self._report_period_config = None
    
    def get_bitrix_config(self) -> BitrixConfig:
        """
        Возвращает конфигурацию Bitrix24 с учётом приоритета источников.
        
        Returns:
            BitrixConfig: Валидированная конфигурация Bitrix24
        """
        if self._bitrix_config is None:
            webhook_url = self._get_merged_value('BitrixAPI', 'webhookurl', '')
            
            if not webhook_url:
                raise ValueError("Webhook URL не найден ни в переменных окружения, ни в .env, ни в config.ini")
            
            self._bitrix_config = BitrixConfig(webhook_url=webhook_url)
        
        return self._bitrix_config
    
    def get_app_config(self) -> AppConfig:
        """
        Возвращает конфигурацию приложения с учётом приоритета источников.
        
        Returns:
            AppConfig: Валидированная конфигурация приложения
        """
        if self._app_config is None:
            save_folder = self._get_merged_value('AppSettings', 'defaultsavefolder', '')
            filename = self._get_merged_value('AppSettings', 'defaultfilename', '')
            
            self._app_config = AppConfig(
                default_save_folder=save_folder,
                default_filename=filename
            )
        
        return self._app_config
    
    def get_report_period_config(self) -> ReportPeriodConfig:
        """
        Возвращает конфигурацию периода отчёта с учётом приоритета источников.
        
        Returns:
            ReportPeriodConfig: Валидированная конфигурация периода
        """
        if self._report_period_config is None:
            start_date = self._get_merged_value('ReportPeriod', 'startdate', '')
            end_date = self._get_merged_value('ReportPeriod', 'enddate', '')
            
            self._report_period_config = ReportPeriodConfig(
                start_date=start_date,
                end_date=end_date
            )
        
        return self._report_period_config
    
    def get_safe_config_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о конфигурации с маскированными секретами.
        
        Returns:
            Dict: Безопасная информация о конфигурации для логирования
        """
        info = {
            'sources': {
                'config_ini_exists': self.config_path.exists(),
                'env_file_exists': self.env_path.exists(),
                'env_vars_count': len([k for k in os.environ.keys() if 'BITRIX' in k.upper()]),
                'dotenv_available': HAS_DOTENV
            },
            'config': {}
        }
        
        # Безопасная информация о битрикс конфигурации
        try:
            bitrix_config = self.get_bitrix_config()
            info['config']['bitrix'] = {
                'webhook_url': self._mask_sensitive_value('webhook_url', bitrix_config.webhook_url)
            }
        except Exception as e:
            info['config']['bitrix'] = {'error': str(e)}
        
        # Информация о приложении (не конфиденциальная)
        try:
            app_config = self.get_app_config()
            info['config']['app'] = {
                'default_save_folder': app_config.default_save_folder,
                'default_filename': app_config.default_filename
            }
        except Exception as e:
            info['config']['app'] = {'error': str(e)}
        
        return info


def create_secure_config_reader(config_path: str = "config.ini", env_path: str = ".env") -> SecureConfigReader:
    """
    Фабричная функция для создания и инициализации SecureConfigReader.
    
    Args:
        config_path: Путь к файлу конфигурации
        env_path: Путь к .env файлу
        
    Returns:
        SecureConfigReader: Инициализированный объект SecureConfigReader
    """
    reader = SecureConfigReader(config_path, env_path)
    reader.load_config()
    return reader 