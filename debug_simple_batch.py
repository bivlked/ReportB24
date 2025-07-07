#!/usr/bin/env python3
"""
Простой тест batch API
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.app import AppFactory

def test_batch_api():
    """Простой тест batch API"""
    
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Инициализация через AppFactory
        app = AppFactory.create_app()
        
        print("🔍 Простой тест batch API...")
        
        # Тестовые данные
        invoice_id = 2499  # Знаем что у него есть 1 товар
        
        # Формируем batch данные
        batch_data = {
            f'products_invoice_{invoice_id}': {
                'method': 'crm.item.productrow.list',
                'params': {
                    'filter': {
                        '=ownerType': 'SI',
                        '=ownerId': invoice_id
                    }
                }
            }
        }
        
        print(f"📤 Отправляем batch запрос:")
        print(f"   Данные: {batch_data}")
        
        # Прямой вызов _make_request
        response = app.bitrix_client._make_request('POST', 'batch', data=batch_data)
        
        print(f"📥 Ответ batch API:")
        print(f"   Success: {response.success}")
        print(f"   Status: {response.status_code}")  
        print(f"   Data type: {type(response.data)}")
        print(f"   Data: {response.data}")
        
        # Проверим одиночный запрос для сравнения
        print(f"\n🔍 Одиночный запрос для сравнения:")
        single_response = app.bitrix_client._make_request(
            'POST', 
            'crm.item.productrow.list', 
            data={
                'filter': {
                    '=ownerType': 'SI',
                    '=ownerId': invoice_id
                }
            }
        )
        
        print(f"   Success: {single_response.success}")
        print(f"   Status: {single_response.status_code}")
        print(f"   Data type: {type(single_response.data)}")
        print(f"   Data: {single_response.data}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_api() 