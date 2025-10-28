#!/usr/bin/env python3
"""
Генератор детальных отчётов Bitrix24 с товарами.

Создаёт Excel отчёт с двумя листами:
- "Краткий": Обзор всех счетов
- "Полный": Детализация всех товаров с зебра-группировкой
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Добавить корень проекта в PYTHONPATH для корректных импортов из scripts/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from src.core.app import AppFactory
from src.excel_generator.generator import ExcelReportGenerator
from src.data_processor.data_processor import DataProcessor


def print_progress(message, step=None, total_steps=None):
    """Вывод прогресса с простым индикатором."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if step and total_steps:
        progress = f"[{step}/{total_steps}]"
        print(f"{timestamp} {progress} {message}")
    else:
        print(f"{timestamp} {message}")


def main():
    """Основная функция запуска генератора детальных отчётов."""
    start_time = time.time()

    print("\n" + "=" * 70)
    print("  ГЕНЕРАТОР ДЕТАЛЬНЫХ ОТЧЁТОВ BITRIX24")
    print("=" * 70 + "\n")

    try:
        # Этап 1: Инициализация
        print_progress("► Инициализация приложения...", 1, 5)
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
            print_progress("► Проверка конфигурации...", 2, 5)
            if not app.validate_configuration():
                print("  ✗ Ошибки в конфигурации")
                error_report = app.get_error_report()
                print(error_report)
                return False
            print_progress("  ✓ Конфигурация корректна")
            print()

            # Этап 3: Подключение
            print_progress("► Тестирование подключения к Bitrix24...", 3, 5)
            if not app.test_api_connection():
                print("  ✗ Не удалось подключиться к Bitrix24 API")
                return False
            print_progress("  ✓ Подключение установлено")
            print()

            # Этап 4: Получение данных
            print_progress("► Получение данных из Bitrix24...", 4, 5)

            try:
                # Получаем компоненты
                bitrix_client = app.bitrix_client
                data_processor = app.data_processor
                data_processor.set_bitrix_client(bitrix_client)
                generator = ExcelReportGenerator()

                # Получение счетов
                print_progress("  Загрузка счетов...")
                invoices = app.workflow_orchestrator._fetch_invoices_data(
                    report_period_config.start_date, report_period_config.end_date
                )

                if not invoices:
                    print("  ✗ Нет данных за указанный период")
                    return False

                print_progress(f"  ✓ Получено счетов: {len(invoices)}")

                # Получение товаров с индикацией прогресса
                print_progress("  Загрузка товаров...")
                detailed_data = []
                total_products = 0
                processed_invoices = 0

                for i, invoice in enumerate(invoices, 1):
                    invoice_id = invoice.get("id")
                    if not invoice_id:
                        continue

                    # Простой индикатор прогресса
                    if i % 10 == 0 or i == len(invoices):
                        print(
                            f"\r    Обработано {i}/{len(invoices)} счетов...",
                            end="",
                            flush=True,
                        )

                    # 🔧 БАГ-9 FIX: get_products_by_invoice теперь возвращает Dict
                    products_result = bitrix_client.get_products_by_invoice(invoice_id)
                    products = products_result.get("products", [])
                    total_products += len(products)

                    account_number = invoice.get("accountNumber", f"Счет #{invoice_id}")
                    company_name, inn = (
                        bitrix_client.get_company_info_by_invoice(account_number)
                        if account_number
                        else ("Не найдено", "Не найдено")
                    )

                    invoice_info = {
                        "account_number": account_number,
                        "company_name": (
                            company_name
                            if company_name not in ["Не найдено", "Ошибка"]
                            else "Не найдено"
                        ),
                        "inn": (
                            inn if inn not in ["Не найдено", "Ошибка"] else "Не найдено"
                        ),
                        "invoice_id": invoice_id,
                    }

                    invoice_products = (
                        data_processor.format_detailed_products_for_excel(
                            products, invoice_info
                        )
                    )
                    detailed_data.extend(invoice_products)
                    processed_invoices += 1

                print()  # Новая строка после прогресс-индикатора
                print_progress(f"  ✓ Обработано товаров: {len(detailed_data)}")

                # Обработка счетов для краткого отчета
                print_progress("  Формирование краткого отчета...")
                brief_data = []
                for invoice in invoices:
                    processed_invoice = data_processor.process_invoice_record(invoice)
                    if processed_invoice:
                        brief_data.append(processed_invoice)

                print_progress(f"  ✓ Обработано счетов: {len(brief_data)}")
                print()

                # Этап 5: Генерация отчёта с валидацией (v2.5.0)
                print_progress("► Создание Excel отчёта с валидацией...", 5, 5)
                full_path = (
                    f"{app_config.default_save_folder}/{app_config.default_filename}"
                )

                # 🆕 v2.5.0: Используем новый метод с валидацией и цветным выводом
                print()  # Пустая строка перед цветным выводом
                result = generator.generate_comprehensive_report(
                    brief_data,
                    detailed_data,
                    full_path,
                    return_metrics=True,  # Получаем метрики
                    verbose=True,  # Цветной вывод
                )

                execution_time = time.time() - start_time
                print()
                print_progress(f"  ✓ Отчёт сохранён: {result.output_path}")
                print()

                # Итоговая сводка
                print("=" * 70)
                print("  ИТОГИ ГЕНЕРАЦИИ")
                print("=" * 70)
                print(
                    f"  Период:          {report_period_config.start_date} - {report_period_config.end_date}"
                )
                print(
                    f"  Счетов:          {len(brief_data)} (валидных: {result.quality_metrics.brief_valid})"
                )
                print(
                    f"  Товаров:         {len(detailed_data)} (валидных: {result.quality_metrics.detailed_valid})"
                )
                print(f"  Проблем:         {result.quality_metrics.total_issues}")
                print(f"  Время:           {execution_time:.1f} сек")
                print(f"  Файл:            {result.output_path}")
                print("=" * 70)

                return True

            except Exception as e:
                print(f"\n  ✗ Ошибка создания отчёта: {e}")
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
