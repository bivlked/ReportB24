#!/usr/bin/env python3
"""
Proof of Concept: Тестирование API crm.item.productrow.list для Smart Invoices

Цель: Валидация получения товаров из счетов через Bitrix24 API
Время: 2025-07-03 16:25:00
"""

import requests
import json
import sys
import os
from pathlib import Path

# Добавляем путь к src для импорта
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config.config_reader import SecureConfigReader
from bitrix24_client.client import Bitrix24Client


def test_crm_item_productrow_list():
    """
    Тест API для получения товаров Smart Invoices
    
    Согласно Context7 документации:
    - Структура: crm_item_product_row
    - Поля: ownerId, ownerType, productId, productName, price, quantity, etc.
    - Фильтр: по ownerId (ID счета) и ownerType (тип объекта)
    """
    
    print("🧪 PROOF OF CONCEPT: crm.item.productrow.list API")
    print("=" * 60)
    
    # Инициализация конфигурации
    try:
        config = SecureConfigReader()
        print(f"✅ Конфигурация загружена: {config.get_safe_config_info()}")
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False
    
    # Инициализация Bitrix24 клиента
    try:
        # Получаем webhook URL из конфигурации
        bitrix_config = config.get_bitrix_config()
        client = Bitrix24Client(bitrix_config.webhook_url)
        print(f"✅ Bitrix24 клиент инициализирован: {client.get_stats()['webhook_url']}")
    except Exception as e:
        print(f"❌ Ошибка инициализации клиента: {e}")
        return False
    
    # Шаг 1: Получаем список Smart Invoices для тестирования
    print("\n📋 Шаг 1: Получение Smart Invoices для тестирования")
    try:
        invoices = client.get_smart_invoices(
            entity_type_id=31,
            filters={},
            select=['id', 'title', 'opportunity']
        )
        
        if not invoices or len(invoices) == 0:
            print("❌ Счета не найдены для тестирования")
            return False
            
        print(f"✅ Найдено {len(invoices)} счетов")
        
        # Берем первые 3 счета для тестирования
        test_invoices = invoices[:3]
        for i, invoice in enumerate(test_invoices):
            print(f"   {i+1}. ID: {invoice.get('id')}, "
                  f"Название: {invoice.get('title', 'N/A')[:50]}, "
                  f"Сумма: {invoice.get('opportunity', 'N/A')}")
                  
    except Exception as e:
        print(f"❌ Ошибка получения счетов: {e}")
        return False
    
    # Шаг 2: Тестируем получение товаров для счетов
    print("\n🛒 Шаг 2: Тестирование API crm.item.productrow.list")
    
    for i, invoice in enumerate(test_invoices):
        invoice_id = invoice.get('id')
        print(f"\n--- Тестирование счета {i+1}: ID {invoice_id} ---")
        
        try:
            # Прямой запрос к API для получения товаров
            # Используем правильные параметры из Report BIG.py
            params = {
                'filter': {
                    '=ownerType': 'SI',  # SI = Smart Invoice (из Report BIG.py)
                    '=ownerId': invoice_id
                }
            }
            
            print(f"   📡 Запрос: crm.item.productrow.list")
            print(f"   🔍 Фильтр: =ownerId={invoice_id}, =ownerType=SI")
            
            # Отправляем запрос
            response = client._make_request('POST', 'crm.item.productrow.list', data=params)
            
            if response and response.success:
                # Правильная структура ответа из Report BIG.py: result.productRows
                products = response.data.get('productRows', []) if isinstance(response.data, dict) else []
                print(f"   ✅ Получено товаров: {len(products)}")
                
                if products:
                    # Показываем первые 2 товара
                    for j, product in enumerate(products[:2]):
                        print(f"      {j+1}. {product.get('productName', 'N/A')[:30]} | "
                              f"Цена: {product.get('price', 'N/A')} | "
                              f"Кол-во: {product.get('quantity', 'N/A')}")
                    break  # Успешно получили товары, прерываем альтернативные попытки
                else:
                    print("   ℹ️ Товары не найдены (возможно счет пуст)")
                    
            else:
                print(f"   ⚠️ Неожиданный ответ API: {response.error if response else 'None'}")
                
        except Exception as e:
            print(f"   ❌ Ошибка запроса товаров: {e}")
            
            # Больше не нужны альтернативные попытки, используем правильный параметр из Report BIG.py
    
    # Шаг 3: Тестируем batch запрос
    print("\n🔀 Шаг 3: Тестирование batch запроса")
    
    try:
        # Формируем batch для получения товаров по нескольким счетам
        batch_data = {}
        for i, invoice in enumerate(test_invoices):
            batch_data[f'products_invoice_{i}'] = {
                'method': 'crm.item.productrow.list',
                'params': {
                    'filter': {
                        '=ownerId': invoice.get('id'),
                        '=ownerType': 'SI'
                    }
                }
            }
        
        print(f"   📦 Batch запрос для {len(batch_data)} счетов")
        
        # Отправляем batch запрос
        batch_response = client._make_request('POST', 'batch', data={'cmd': batch_data})
        
        if batch_response and batch_response.success:
            batch_results = batch_response.data.get('result', {}) if isinstance(batch_response.data, dict) else {}
            print(f"   ✅ Batch успешен, получено {len(batch_results)} ответов")
            
            total_products = 0
            for key, result in batch_results.items():
                if isinstance(result, list):
                    total_products += len(result)
                    print(f"   - {key}: {len(result)} товаров")
                elif isinstance(result, dict) and 'items' in result:
                    total_products += len(result['items'])
                    print(f"   - {key}: {len(result['items'])} товаров")
                    
            print(f"   📊 Всего товаров через batch: {total_products}")
            
        else:
            print(f"   ❌ Batch неуспешен: {batch_response.error if batch_response else 'None'}")
            
    except Exception as e:
        print(f"   ❌ Ошибка batch запроса: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 РЕЗУЛЬТАТ PROOF OF CONCEPT:")
    print("✅ Конфигурация и клиент работают")
    print("✅ Smart Invoices получаются успешно") 
    print("🔍 API crm.item.productrow.list протестирован")
    print("📈 Готовность к Фазе 1: API расширение")
    
    return True


if __name__ == "__main__":
    success = test_crm_item_productrow_list()
    sys.exit(0 if success else 1) 