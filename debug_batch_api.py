#!/usr/bin/env python3
"""
Отладка batch API для получения товаров
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.app import AppFactory

def debug_batch_api():
    """Отладка batch API для товаров"""
    
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Инициализация через AppFactory
        app = AppFactory.create_app()
        
        print("🔍 Отладка batch API для товаров...")
        
        # Получаем несколько счетов для тестирования
        print("📊 Получение счетов...")
        invoices = app.workflow_orchestrator._fetch_invoices_data(
            start_date="01.05.2025",
            end_date="31.05.2025"
        )
        
        if not invoices:
            print("❌ Нет счетов для тестирования")
            return
        
        # Берем первые 3 счета для тестирования
        test_invoices = invoices[:3]
        invoice_ids = [inv.get('id') for inv in test_invoices if inv.get('id')]
        
        print(f"🧪 Тестируем {len(invoice_ids)} счетов: {invoice_ids}")
        
        # Тест 1: Одиночные запросы
        print("\n=== ТЕСТ 1: Одиночные запросы ===")
        for invoice_id in invoice_ids:
            products = app.bitrix_client.get_products_by_invoice(invoice_id)
            print(f"Счет {invoice_id}: {len(products)} товаров")
            if products:
                print(f"  Первый товар: {products[0].get('productName', 'Без названия')}")
        
        # Тест 2: Batch запрос
        print("\n=== ТЕСТ 2: Batch запрос ===")
        batch_products = app.bitrix_client.get_products_by_invoices_batch(invoice_ids, chunk_size=3)
        
        print(f"Batch результат: {len(batch_products)} счетов")
        for invoice_id, products in batch_products.items():
            print(f"Счет {invoice_id}: {len(products)} товаров")
            if products:
                print(f"  Первый товар: {products[0].get('productName', 'Без названия')}")
        
        # Сравнение результатов
        print("\n=== СРАВНЕНИЕ ===")
        for invoice_id in invoice_ids:
            single_count = len(app.bitrix_client.get_products_by_invoice(invoice_id))
            batch_count = len(batch_products.get(invoice_id, []))
            
            status = "✅" if single_count == batch_count else "❌"
            print(f"{status} Счет {invoice_id}: одиночный={single_count}, batch={batch_count}")
        
    except Exception as e:
        print(f"❌ Ошибка отладки: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'app' in locals():
            app.close()

if __name__ == "__main__":
    debug_batch_api() 