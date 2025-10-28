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
from src.excel_generator.console_ui import ConsoleUI, Colors, Spinner
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

    ConsoleUI.print_header("ГЕНЕРАТОР ДЕТАЛЬНЫХ ОТЧЁТОВ BITRIX24", Colors.BRIGHT_CYAN)

    try:
        # Этап 1: Инициализация
        ConsoleUI.print_step(1, "Инициализация приложения...", "🚀")
        with AppFactory.create_app(config_path="config.ini") as app:

            # Получение конфигурации
            report_period_config = app.config_reader.get_report_period_config()
            app_config = app.config_reader.get_app_config()

            ConsoleUI.print_info(
                f"Период: {report_period_config.start_date} - {report_period_config.end_date}",
                indent=1,
            )
            ConsoleUI.print_info(
                f"Выходной файл: {app_config.default_filename}", indent=1
            )
            print()

            # Этап 2: Валидация
            ConsoleUI.print_step(2, "Проверка конфигурации...", "🔍")
            if not app.validate_configuration():
                ConsoleUI.print_error("Ошибки в конфигурации")
                error_report = app.get_error_report()
                print(error_report)
                return False
            ConsoleUI.print_success("Конфигурация корректна")
            print()

            # Этап 3: Подключение
            ConsoleUI.print_step(3, "Тестирование подключения к Bitrix24...", "🔌")
            if not app.test_api_connection():
                ConsoleUI.print_error("Не удалось подключиться к Bitrix24 API")
                return False
            ConsoleUI.print_success("Подключение установлено")
            print()

            # Этап 4: Получение данных
            ConsoleUI.print_step(4, "Получение данных из Bitrix24...", "📡")

            try:
                # Получаем компоненты
                bitrix_client = app.bitrix_client
                data_processor = app.data_processor
                data_processor.set_bitrix_client(bitrix_client)
                generator = ExcelReportGenerator()

                # Получение счетов
                spinner = Spinner("Загрузка счетов из Bitrix24")
                spinner.start()

                invoices = app.workflow_orchestrator._fetch_invoices_data(
                    report_period_config.start_date, report_period_config.end_date
                )

                spinner.stop(f"Загружено счетов: {len(invoices)}", success=True)

                if not invoices:
                    ConsoleUI.print_error("Нет данных за указанный период")
                    return False

                # Получение товаров с индикацией прогресса
                ConsoleUI.print_info("Загрузка товаров по счетам...", indent=1)
                detailed_data = []
                total_products = 0

                for i, invoice in enumerate(invoices, 1):
                    invoice_id = invoice.get("id")
                    if not invoice_id:
                        continue

                    # Более частый прогресс (каждые 5 счетов или последний)
                    if i % 5 == 0 or i == len(invoices):
                        progress_percent = (i / len(invoices)) * 100
                        ConsoleUI.print_progress(
                            current=i,
                            total=len(invoices),
                            prefix=f"    {Colors.CYAN}Обработка{Colors.RESET}",
                            suffix=f"{Colors.DIM}(счёт {i}/{len(invoices)}){Colors.RESET}",
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

                ConsoleUI.print_success(f"Обработано товаров: {len(detailed_data)}")

                # Обработка счетов для краткого отчета
                spinner = Spinner("Формирование краткого отчета")
                spinner.start()

                brief_data = []
                for invoice in invoices:
                    processed_invoice = data_processor.process_invoice_record(invoice)
                    if processed_invoice:
                        brief_data.append(processed_invoice)

                spinner.stop(f"Обработано счетов: {len(brief_data)}", success=True)
                print()

                # Этап 5: Генерация отчёта с валидацией (v2.5.0)
                ConsoleUI.print_step(5, "Создание Excel отчёта с валидацией...", "📊")
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

                # Итоговая сводка
                ConsoleUI.print_section_separator()
                print(f"\n{Colors.BRIGHT_CYAN}{Colors.BOLD}{'═' * 70}")
                print(f"  ИТОГИ ГЕНЕРАЦИИ")
                print(f"{'═' * 70}{Colors.RESET}\n")
                print(
                    f"  {Colors.CYAN}Период:{Colors.RESET}          {report_period_config.start_date} - {report_period_config.end_date}"
                )
                print(
                    f"  {Colors.CYAN}Счетов:{Colors.RESET}          {len(brief_data)} (валидных: {Colors.BRIGHT_GREEN}{result.quality_metrics.brief_valid}{Colors.RESET})"
                )
                print(
                    f"  {Colors.CYAN}Товаров:{Colors.RESET}         {len(detailed_data)} (валидных: {Colors.BRIGHT_GREEN}{result.quality_metrics.detailed_valid}{Colors.RESET})"
                )

                problems_color = (
                    Colors.BRIGHT_RED
                    if result.quality_metrics.total_issues > 0
                    else Colors.BRIGHT_GREEN
                )
                print(
                    f"  {Colors.CYAN}Проблем:{Colors.RESET}         {problems_color}{result.quality_metrics.total_issues}{Colors.RESET}"
                )
                print(
                    f"  {Colors.CYAN}Время:{Colors.RESET}           {execution_time:.1f} сек"
                )
                print(
                    f"  {Colors.CYAN}Файл:{Colors.RESET}            {Colors.WHITE}{result.output_path}{Colors.RESET}"
                )
                print(f"\n{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

                return True

            except Exception as e:
                ConsoleUI.print_error(f"Ошибка создания отчёта: {e}")
                return False

    except KeyboardInterrupt:
        ConsoleUI.print_warning("Работа прервана пользователем")
        return False
    except Exception as e:
        ConsoleUI.print_error(f"Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        ConsoleUI.print_success("Работа завершена успешно")
    else:
        ConsoleUI.print_error("Работа завершена с ошибками")

    print(f"\n{Colors.DIM}Нажмите Enter для закрытия...{Colors.RESET}")
    input()

    if not success:
        sys.exit(1)
