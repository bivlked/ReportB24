#!/usr/bin/env python3
"""
Упрощённый генератор отчётов Bitrix24.
Простой и надёжный подход.
"""

import sys
import os
import configparser
import traceback


def generate_report_simple():
    """Простая генерация отчёта."""
    
    print("🚀 Упрощённый генератор отчётов Bitrix24")
    print("=" * 50)
    
    try:
        # Читаем config.ini
        print("📁 Чтение config.ini...")
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        
        webhook_url = config.get('BitrixAPI', 'webhookurl')
        save_folder = config.get('AppSettings', 'defaultsavefolder')
        filename = config.get('AppSettings', 'defaultfilename')
        start_date = config.get('ReportPeriod', 'startdate')
        end_date = config.get('ReportPeriod', 'enddate')
        
        print("⚙️ Настройки:")
        print(f"   🌐 Bitrix24: {webhook_url[:50]}...")
        print(f"   📅 Период: {start_date} - {end_date}")
        print(f"   📂 Папка: {save_folder}")
        print(f"   📄 Файл: {filename}")
        
        # Создаем папку если нет
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, filename)
        
        # Простой тест API
        print("\n🧪 Тест API...")
        import requests
        response = requests.get(f"{webhook_url}profile", timeout=10)
        if response.status_code != 200:
            print(f"❌ API не работает: статус {response.status_code}")
            return False
        print("✅ API работает")
        
        # Создание компонентов напрямую
        print("\n🔧 Создание компонентов...")
        
        # Импорт модулей
        from src.config.config_reader import create_config_reader
        from src.bitrix24_client.client import Bitrix24Client
        from src.data_processor.data_processor import DataProcessor
        from src.excel_generator.generator import ExcelReportGenerator
        from src.core.workflow import WorkflowOrchestrator
        
        # Создание объектов
        config_reader = create_config_reader('config.ini')
        bitrix_client = Bitrix24Client(webhook_url)
        data_processor = DataProcessor()
        excel_generator = ExcelReportGenerator()
        
        workflow = WorkflowOrchestrator(
            bitrix_client=bitrix_client,
            data_processor=data_processor,
            excel_generator=excel_generator,
            config_reader=config_reader
        )
        
        print("✅ Компоненты созданы")
        
        # Генерация
        print(f"\n📊 Генерация отчёта в {save_path}...")
        result = workflow.execute_full_workflow(save_path)
        
        if result.success:
            print("🎉 Отчёт создан успешно!")
            print(f"📄 Файл: {save_path}")
            print(f"📊 Записей: {result.records_processed}")
            
            if os.path.exists(save_path):
                size = os.path.getsize(save_path)
                print(f"📦 Размер: {size:,} байт")
            
            return True
        else:
            print("❌ Ошибка генерации")
            print(f"📝 Ошибка: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    success = generate_report_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ГОТОВО! Отчёт создан!")
        print("📂 Проверьте папку reports/")
    else:
        print("❌ Ошибка создания отчёта")
    
    print("\n⏸️  Нажмите Enter...")
    input()
    
    return success


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 