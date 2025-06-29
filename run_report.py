#!/usr/bin/env python3
"""
Простой запуск генератора отчётов Bitrix24.

Использует данные из config.ini для автоматической генерации отчёта.
Замена ручного ввода данных на автоматическое чтение из конфигурации.
"""

import sys
from src.core.app import AppFactory


def main():
    """Основная функция запуска генератора отчётов."""
    
    print("🚀 Генератор отчётов Bitrix24 Excel v1.0.0")
    print("=" * 50)
    print("📁 Читаю данные из config.ini...")
    
    try:
        # Создание и инициализация приложения
        with AppFactory.create_app(config_path="config.ini") as app:
            
            # Получение информации о конфигурации
            app_info = app.get_app_info()
            print(f"✅ Приложение инициализировано")
            print(f"📄 Конфигурация: {app_info['configuration']['config_path']}")
            print("")
            
            # Показать настройки из config.ini
            bitrix_config = app.config_reader.get_bitrix_config()
            app_config = app.config_reader.get_app_config()
            report_period_config = app.config_reader.get_report_period_config()
            
            print("⚙️ Настройки из config.ini:")
            print(f"   🌐 Bitrix24: {bitrix_config.webhook_url[:50]}...")
            print(f"   📅 Период: {report_period_config.start_date} - {report_period_config.end_date}")
            print(f"   📂 Папка: {app_config.default_save_folder}")
            print(f"   📄 Файл: {app_config.default_filename}")
            print("")
            
            # Валидация конфигурации
            print("🔍 Проверка конфигурации...")
            if not app.validate_configuration():
                print("❌ Ошибки в конфигурации. Проверьте config.ini")
                error_report = app.get_error_report()
                print(error_report)
                return False
            print("✅ Конфигурация корректна")
            
            # Тестирование API
            print("🔌 Тестирование подключения к Bitrix24...")
            if not app.test_api_connection():
                print("❌ Не удалось подключиться к Bitrix24 API")
                print("   Проверьте webhook URL в config.ini")
                return False
            print("✅ Подключение к Bitrix24 успешно")
            print("")
            
            # Генерация отчёта
            print("📊 Генерация отчёта...")
            if app.generate_report():
                print("🎉 Отчёт успешно сгенерирован!")
                
                # Показать путь к сгенерированному файлу
                save_path = app.config_reader.get_safe_save_path()
                print(f"📄 Файл сохранён: {save_path}")
                
                return True
            else:
                print("❌ Ошибка генерации отчёта")
                error_report = app.get_error_report()
                print("\n📋 Подробная информация об ошибке:")
                print(error_report)
                return False
                
    except KeyboardInterrupt:
        print("\n⏹️ Работа прервана пользователем")
        return False
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("   Проверьте config.ini и доступность Bitrix24")
        return False


if __name__ == "__main__":
    print("\n" + "="*50)
    success = main()
    
    if success:
        print("\n✅ Работа завершена успешно!")
        print("🎯 Результат: Отчёт Excel готов к использованию")
    else:
        print("\n❌ Работа завершена с ошибками")
        print("🔍 Проверьте config.ini и подключение к интернету")
    
    print("="*50)
    print("\n⏸️  Нажмите Enter для закрытия...")
    input()  # Пауза для чтения результата
    
    if not success:
        sys.exit(1) 