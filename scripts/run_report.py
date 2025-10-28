#!/usr/bin/env python3
"""
Генератор отчётов Bitrix24.

Использует данные из config.ini для автоматической генерации отчёта.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Добавить корень проекта в PYTHONPATH для корректных импортов из scripts/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from src.core.app import AppFactory


def print_progress(message, step=None, total_steps=None):
    """Вывод прогресса с простым индикатором."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if step and total_steps:
        progress = f"[{step}/{total_steps}]"
        print(f"{timestamp} {progress} {message}")
    else:
        print(f"{timestamp} {message}")


def main():
    """Основная функция запуска генератора отчётов."""
    start_time = time.time()

    print("\n" + "=" * 70)
    print("  ГЕНЕРАТОР ОТЧЁТОВ BITRIX24")
    print("=" * 70 + "\n")

    try:
        # Этап 1: Инициализация
        print_progress("► Инициализация приложения...", 1, 4)
        with AppFactory.create_app(config_path="config.ini") as app:

            # Получение конфигурации
            report_period_config = app.config_reader.get_report_period_config()
            app_config = app.config_reader.get_app_config()

            print_progress(
                f"  Период: {report_period_config.start_date} - {report_period_config.end_date}"
            )
            print_progress(f"  Выходной файл: {app_config.default_filename}")
            print()

            # Этап 2: Валидация
            print_progress("► Проверка конфигурации...", 2, 4)
            if not app.validate_configuration():
                print("  ✗ Ошибки в конфигурации")
                error_report = app.get_error_report()
                print(error_report)
                return False
            print_progress("  ✓ Конфигурация корректна")
            print()

            # Этап 3: Подключение
            print_progress("► Тестирование подключения к Bitrix24...", 3, 4)
            if not app.test_api_connection():
                print("  ✗ Не удалось подключиться к Bitrix24 API")
                return False
            print_progress("  ✓ Подключение установлено")
            print()

            # Этап 4: Генерация
            print_progress("► Генерация отчёта...", 4, 4)
            if app.generate_report():
                execution_time = time.time() - start_time
                save_path = app.config_reader.get_safe_save_path()

                print_progress(f"  ✓ Отчёт сохранён: {save_path}")
                print()

                # Итоговая сводка
                print("=" * 70)
                print("  ИТОГИ ГЕНЕРАЦИИ")
                print("=" * 70)
                print(
                    f"  Период:          {report_period_config.start_date} - {report_period_config.end_date}"
                )
                print(f"  Время:           {execution_time:.1f} сек")
                print(f"  Файл:            {save_path}")
                print("=" * 70)

                return True
            else:
                print("  ✗ Ошибка генерации отчёта")
                error_report = app.get_error_report()
                print(error_report)
                return False

    except KeyboardInterrupt:
        print("\n  ⏹ Работа прервана пользователем")
        return False
    except Exception as e:
        print(f"\n  ✗ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        print("\n✓ Работа завершена успешно\n")
    else:
        print("\n✗ Работа завершена с ошибками\n")

    print("Нажмите Enter для закрытия...")
    input()

    if not success:
        sys.exit(1)
