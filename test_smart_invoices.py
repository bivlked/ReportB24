#!/usr/bin/env python3
"""
Тестер Smart Invoices - проверка данных без фильтров.
"""

import configparser
from src.bitrix24_client.client import Bitrix24Client


def test_smart_invoices():
    """Тестирует получение Smart Invoices"""
    
    print("🧪 Тестер Smart Invoices")
    print("=" * 40)
    
    # Читаем config
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    webhook_url = config.get('BitrixAPI', 'webhookurl')
    
    print(f"🌐 Webhook: {webhook_url[:50]}...")
    
    # Создаем клиент
    client = Bitrix24Client(webhook_url)
    
    try:
        # Получаем Smart Invoices без фильтров (первые 5)
        print("\n📋 Получение первых 5 Smart Invoices...")
        invoices = client.get_smart_invoices(entity_type_id=31)
        
        print(f"✅ Получено: {len(invoices)} Smart Invoices")
        
        if invoices:
            print("\n📄 Пример первого счёта:")
            first_invoice = invoices[0]
            
            for key, value in first_invoice.items():
                print(f"   {key}: {value}")
            
            print(f"\n🔍 Доступные поля в счёте:")
            fields = list(first_invoice.keys())
            print(f"   Всего полей: {len(fields)}")
            for i, field in enumerate(fields[:10]):  # Первые 10 полей
                print(f"   {i+1}. {field}")
            if len(fields) > 10:
                print(f"   ... и ещё {len(fields)-10} полей")
                
        else:
            print("❌ Smart Invoices не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        client.close()
    
    print("\n⏸️  Нажмите Enter...")
    input()


if __name__ == "__main__":
    test_smart_invoices() 