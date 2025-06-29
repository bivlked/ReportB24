#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест API Bitrix24 без Excel
Только проверка доступности методов и данных
"""

import requests
import configparser
import time
from datetime import datetime

def main():
    print("=" * 50)
    print("🧪 ПРОСТОЙ ТЕСТ API BITRIX24")
    print(f"⏰ {datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Читаем конфиг
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        webhook_url = config.get('BitrixAPI', 'webhookurl')
        
        print(f"🔗 Webhook URL: {webhook_url}")
        
        # Тест 1: Простой запрос Smart Invoices
        print("\n📋 Тест 1: Получение Smart Invoices...")
        params = {
            'entityTypeId': 31,
            'start': 0,
            'filter': {'!stageId': 'DT31_1:D'},
            'select': ['id', 'accountNumber', 'opportunity']
        }
        
        resp = requests.post(f"{webhook_url}crm.item.list", json=params, timeout=10)
        print(f"   📡 Статус ответа: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('result', {}).get('items', [])
            print(f"   ✅ Получено записей: {len(items)}")
            
            if items:
                # Показываем первую запись
                first = items[0]
                print(f"   📊 Первая запись:")
                print(f"      ID: {first.get('id')}")
                print(f"      Номер: {first.get('accountNumber')}")
                print(f"      Сумма: {first.get('opportunity')}")
                
                # Тест 2: Проверим реквизиты для первого счета
                acc_num = first.get('accountNumber', '')
                if acc_num:
                    print(f"\n🔍 Тест 2: Реквизиты для счета {acc_num}")
                    
                    # Поиск по номеру счета
                    search_resp = requests.get(f"{webhook_url}crm.item.list", params={
                        'filter[accountNumber]': acc_num,
                        'entityTypeId': 31
                    }, timeout=10)
                    
                    print(f"   📡 Поиск счета: {search_resp.status_code}")
                    
                    if search_resp.status_code == 200:
                        search_data = search_resp.json()
                        search_items = search_data.get('result', {}).get('items', [])
                        
                        if search_items:
                            inv_id = search_items[0].get('id')
                            print(f"   ✅ Счет найден, ID: {inv_id}")
                            
                            # Поиск связей реквизитов
                            time.sleep(0.5)
                            link_resp = requests.get(f"{webhook_url}crm.requisite.link.list", params={
                                'filter[ENTITY_TYPE_ID]': 31,
                                'filter[ENTITY_ID]': inv_id
                            }, timeout=10)
                            
                            print(f"   📡 Поиск связей: {link_resp.status_code}")
                            
                            if link_resp.status_code == 200:
                                link_data = link_resp.json()
                                link_items = link_data.get('result', [])
                                print(f"   📋 Найдено связей: {len(link_items)}")
                                
                                if link_items:
                                    req_id = link_items[0].get('REQUISITE_ID')
                                    print(f"   ✅ ID реквизита: {req_id}")
                                    
                                    # Получение реквизита
                                    time.sleep(0.5)
                                    req_resp = requests.post(f"{webhook_url}crm.requisite.get", 
                                                           json={"id": str(req_id)}, timeout=10)
                                    
                                    print(f"   📡 Получение реквизита: {req_resp.status_code}")
                                    
                                    if req_resp.status_code == 200:
                                        req_data = req_resp.json()
                                        if req_data.get('result'):
                                            fields = req_data['result']
                                            print(f"   ✅ Реквизиты получены:")
                                            print(f"      ИНН: {fields.get('RQ_INN', 'Нет')}")
                                            print(f"      Компания: {fields.get('RQ_COMPANY_NAME', 'Нет')}")
                                            print(f"      Имя: {fields.get('RQ_NAME', 'Нет')}")
                                        else:
                                            print(f"   ❌ Пустой ответ реквизита")
                                    else:
                                        print(f"   ❌ Ошибка получения реквизита: {req_resp.text}")
                                else:
                                    print(f"   ⚠️ Нет связанных реквизитов")
                            else:
                                print(f"   ❌ Ошибка поиска связей: {link_resp.text}")
                        else:
                            print(f"   ❌ Счет не найден при повторном поиске")
                    else:
                        print(f"   ❌ Ошибка поиска счета: {search_resp.text}")
                
                print(f"\n🎯 ЗАКЛЮЧЕНИЕ:")
                print(f"✅ API доступен")
                print(f"✅ Smart Invoices получаются ({len(items)} записей)")
                if 'req_id' in locals():
                    print(f"✅ Реквизиты доступны")
                    print(f"✅ Все методы работают правильно!")
                    print(f"\n📝 ГОТОВ К СОЗДАНИЮ ПОЛНОГО ОТЧЕТА")
                else:
                    print(f"⚠️ Проблемы с реквизитами")
                    
            else:
                print(f"   ⚠️ Нет данных в ответе")
        else:
            print(f"   ❌ Ошибка API: {resp.text}")
            
    except Exception as e:
        print(f"\n💥 Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n⏰ Завершено: {datetime.now().strftime('%Y.%m.%d %H:%M:%S')}")
    input("⏸️ Нажмите Enter для выхода...")

if __name__ == "__main__":
    main() 