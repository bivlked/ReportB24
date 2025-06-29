"""
Модуль для чтения и валидации конфигурационного файла.

Обеспечивает централизованное чтение config.ini и предоставляет
валидированные настройки для всех компонентов приложения.
"""

import configparser
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


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