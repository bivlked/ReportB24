#!/usr/bin/env python3
"""
🔥 Генератор ДВУХЛИСТОВЫХ отчётов Bitrix24 с товарами.

Создаёт Excel отчёт с двумя листами:
- "Краткий": Обзор всех счетов (как обычный отчёт)
- "Полный": Детализация всех товаров с зебра-группировкой

Использует новую функциональность v2.1.0 с ProductRows API.
"""

import sys
from src.core.app import AppFactory
from src.excel_generator.generator import ExcelReportGenerator
from src.data_processor.data_processor import DataProcessor


def main():
    """Основная функция запуска генератора двухлистовых отчётов."""
    
    print("🔥 Генератор ДВУХЛИСТОВЫХ отчётов Bitrix24 v2.1.1")
    print("=" * 60)
    print("📦 Новинка: Детальные отчёты с товарами из Smart Invoices")
    print("🦓 Особенности: Зебра-группировка, корректные данные ИНН/Контрагент")
    print("=" * 60)
    print("📁 Читаю данные из config.ini...")
    
    try:
        # Создание и инициализация приложения (как в run_report.py)
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
            
            # Безопасное отображение конфигурации
            safe_config = app.config_reader.get_safe_config_info()
            print("⚙️ Настройки из конфигурации:")
            print(f"   🌐 Bitrix24: {safe_config['config']['bitrix']['webhook_url']}")
            print(f"   📅 Период: {report_period_config.start_date} - {report_period_config.end_date}")
            print(f"   📂 Папка: {app_config.default_save_folder}")
            print(f"   📄 Имя файла: {app_config.default_filename}")
            print(f"   🔐 Источники: config.ini {'✅' if safe_config['sources']['config_ini_exists'] else '❌'}, .env {'✅' if safe_config['sources']['env_file_exists'] else '❌'}")
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
                print("   Проверьте webhook URL в config.ini/.env")
                return False
            print("✅ Подключение к Bitrix24 успешно")
            print("")
            
            # 🔥 НОВАЯ ФУНКЦИОНАЛЬНОСТЬ: Создание двухлистового отчёта
            print("")
            print("🔥 Создание ДВУХЛИСТОВОГО отчёта...")
            print("📋 Лист 'Краткий': Обзор всех счетов")
            print("📦 Лист 'Полный': Детализация товаров с зебра-эффектом")
            print("")
            
            try:
                # 🔧 ИСПРАВЛЕНИЕ: Используем имя файла из конфига БЕЗ ИЗМЕНЕНИЙ (требование пользователя)
                detailed_filename = app_config.default_filename
                
                # Получение данных через workflow orchestrator (как в обычном отчёте)
                print("📊 Получение данных счетов за период...")
                
                # Получаем компоненты из приложения
                bitrix_client = app.bitrix_client
                data_processor = app.data_processor
                
                # 🔧 ИСПРАВЛЕНИЕ: Устанавливаем Bitrix24Client в DataProcessor для корректного получения ИНН и Контрагент
                data_processor.set_bitrix_client(bitrix_client)
                
                generator = ExcelReportGenerator()
                
                # Получение данных через workflow (используем существующую логику)
                report_period_config = app.config_reader.get_report_period_config()
                
                # Получение счетов через workflow orchestrator 
                invoices = app.workflow_orchestrator._fetch_invoices_data(
                    report_period_config.start_date,
                    report_period_config.end_date
                )
                
                if not invoices:
                    print("⚠️  Нет данных за указанный период")
                    print(f"   Период: {report_period_config.start_date} - {report_period_config.end_date}")
                    return False
                print(f"✅ Получено {len(invoices)} счетов")
                
                # 🔧 ИСПРАВЛЕНИЕ: Убираем BATCH API и используем индивидуальные запросы
                print("📦 Получение данных товаров (индивидуальные запросы)...")
                
                # 🔧 ИСПРАВЛЕНИЕ: Использование DataProcessor для унификации данных
                detailed_data = []
                total_products = 0
                
                for invoice in invoices:
                    invoice_id = invoice.get('id')
                    if not invoice_id:
                        continue
                        
                    # Получаем товары для текущего счета
                    products = bitrix_client.get_products_by_invoice(invoice_id)
                    total_products += len(products)
                    
                    # Получаем информацию о счете для каждого товара
                    account_number = invoice.get('accountNumber', f'Счет #{invoice_id}')
                    company_name, inn = bitrix_client.get_company_info_by_invoice(account_number) if account_number else ('Не найдено', 'Не найдено')
                    
                    # 🔧 ИСПРАВЛЕНИЕ: Используем DataProcessor для форматирования товаров
                    invoice_info = {
                        'account_number': account_number,
                        'company_name': company_name if company_name not in ["Не найдено", "Ошибка"] else 'Не найдено',
                        'inn': inn if inn not in ["Не найдено", "Ошибка"] else 'Не найдено',
                        'invoice_id': invoice_id
                    }
                    
                    # Используем новый метод DataProcessor для правильного форматирования
                    invoice_products = data_processor.format_detailed_products_for_excel(products, invoice_info)
                    detailed_data.extend(invoice_products)
                
                print(f"✅ Обработано {len(detailed_data)} товаров из {len(invoices)} счетов")
                
                # 🔧 ИСПРАВЛЕНИЕ: Обработка данных счетов для краткого отчета
                print("📋 Обработка данных счетов для листа 'Краткий'...")
                brief_data = []
                for invoice in invoices:
                    processed_invoice = data_processor.process_invoice_record(invoice)
                    if processed_invoice:
                        brief_data.append(processed_invoice)
                print(f"✅ Обработано {len(brief_data)} счетов для краткого отчета")
                
                # Сохранение отчёта (используем путь из конфига)
                full_path = f"{app_config.default_save_folder}/{detailed_filename}"
                
                # Создание двухлистового отчёта с правильными данными
                generator.create_multi_sheet_report(brief_data, detailed_data, full_path)
                
                print("🎉 Двухлистовой отчёт успешно создан!")
                print(f"📄 Файл сохранён: {full_path}")
                print("")
                print("📋 Структура отчёта:")
                print("   📊 Лист 'Краткий': Стандартный обзор счетов")
                print("   📦 Лист 'Полный': Детализация товаров:")
                print("      • Номер счёта")
                print("      • Контрагент") 
                print("      • ИНН")
                print("      • Наименование товара")
                print("      • Количество")
                print("      • Единица измерения")
                print("      • Цена")
                print("      • Сумма (с автоматическим НДС 20%)")
                print("   🦓 Зебра-группировка: Товары группируются по счетам")
                print("   🎨 Зелёные заголовки: #C6E0B4")
                
                return True
                
            except Exception as e:
                print(f"❌ Ошибка создания отчёта: {e}")
                print("\n📋 Возможные причины:")
                print("   • Проблемы с доступом к API товаров")
                print("   • Недостаточно места на диске")
                print("   • Файл уже открыт в Excel")
                print(f"\n📋 Подробности ошибки: {str(e)}")
                return False
                
    except KeyboardInterrupt:
        print("\n⏹️ Работа прервана пользователем")
        return False
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("   Проверьте config.ini и доступность Bitrix24")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    success = main()
    
    if success:
        print("\n✅ Работа завершена успешно!")
        print("🎯 Результат: Двухлистовой Excel отчёт готов!")
        print("🔥 Новинка v2.1.1: Детальные отчёты с корректными данными")
        print("✅ Качество данных: Правильные ИНН и Контрагент на всех листах")
    else:
        print("\n❌ Работа завершена с ошибками")
        print("🔍 Проверьте config.ini и подключение к интернету")
        print("💡 Совет: Попробуйте сначала run_report.py для проверки базового функционала")
    
    print("="*60)
    print("\n⏸️  Нажмите Enter для закрытия...")
    input()  # Пауза для чтения результата
    
    if not success:
        sys.exit(1) 