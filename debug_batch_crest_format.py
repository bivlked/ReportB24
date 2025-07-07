#!/usr/bin/env python3
"""
Тест batch API в формате CRest как в Context7 документации
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.app import AppFactory

def test_crest_batch_api():
    """Тест batch API в формате CRest"""
    
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        # Инициализация через AppFactory
        app = AppFactory.create_app()
        
        print("🔍 Тест batch API в формате CRest...")
        
        # Тестовые данные
        invoice_id = 2499  # Знаем что у него есть 1 товар
        
        # ФОРМАТ 1: Как в Context7 документации CRest::callBatch
        batch_data_crest = {
            'cmd': {
                f'products_invoice_{invoice_id}': f'crm.item.productrow.list?filter[=ownerType]=SI&filter[=ownerId]={invoice_id}'
            }
        }
        
        print(f"📤 Тест 1 - CRest формат:")
        print(f"   Данные: {batch_data_crest}")
        
        response1 = app.bitrix_client._make_request('POST', 'batch', data=batch_data_crest)
        
        print(f"📥 Ответ CRest формат:")
        print(f"   Success: {response1.success}")
        print(f"   Data: {response1.data}")
        
        # ФОРМАТ 2: JSON параметры в params
        batch_data_params = {
            'cmd': {
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
        }
        
        print(f"\n📤 Тест 2 - JSON params формат:")
        print(f"   Данные: {batch_data_params}")
        
        response2 = app.bitrix_client._make_request('POST', 'batch', data=batch_data_params)
        
        print(f"📥 Ответ JSON params формат:")
        print(f"   Success: {response2.success}")
        print(f"   Data: {response2.data}")
        
        # ФОРМАТ 3: Простой известный метод для проверки
        batch_data_simple = {
            'cmd': {
                'test_method': 'crm.enum.ownertype'
            }
        }
        
        print(f"\n📤 Тест 3 - Простой метод:")
        print(f"   Данные: {batch_data_simple}")
        
        response3 = app.bitrix_client._make_request('POST', 'batch', data=batch_data_simple)
        
        print(f"📥 Ответ простой метод:")
        print(f"   Success: {response3.success}")
        print(f"   Data: {response3.data}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crest_batch_api() 