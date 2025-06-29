#!/usr/bin/env python3
"""
Простой тестер webhook URL для Bitrix24.
Проверяет подключение и права доступа.
"""

import requests
import configparser
import json
from datetime import datetime


def test_webhook():
    """Тестирует webhook URL из config.ini"""
    
    print("🔍 Тестер Bitrix24 Webhook")
    print("=" * 40)
    
    # Читаем config.ini
    try:
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='utf-8')
        webhook_url = config.get('BitrixAPI', 'webhookurl')
        print(f"📡 Webhook URL: {webhook_url}")
        print()
    except Exception as e:
        print(f"❌ Ошибка чтения config.ini: {e}")
        return False
    
    # Тест 1: Простой запрос методов
    print("🧪 Тест 1: Проверка доступности методов...")
    try:
        response = requests.get(f"{webhook_url}profile", timeout=10)
        print(f"   📊 Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Подключение успешно!")
            print(f"   👤 Пользователь: {data.get('result', {}).get('NAME', 'Неизвестно')}")
            print(f"   🏢 Портал: {data.get('result', {}).get('SERVER_NAME', 'Неизвестно')}")
        elif response.status_code == 401:
            print("   ❌ Ошибка 401: Неавторизованный доступ")
            print("   🔧 Проверьте webhook URL в Bitrix24")
            return False
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
            print(f"   📄 Ответ: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Тайм-аут: Битрикс24 не отвечает")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Ошибка подключения: Проверьте интернет")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    print()
    
    # Тест 2: Проверка CRM прав
    print("🧪 Тест 2: Проверка прав на CRM...")
    try:
        # Пробуем получить список элементов CRM
        response = requests.post(
            f"{webhook_url}crm.item.list",
            json={
                'entityTypeId': 31,  # Smart Invoices
                'start': 0,
                'select': ['id', 'accountNumber']
            },
            timeout=10
        )
        
        print(f"   📊 Статус код: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('result', {}).get('items', [])
            print(f"   ✅ Доступ к CRM есть!")
            print(f"   📋 Найдено Smart Invoices: {len(items)}")
            
            if len(items) > 0:
                print(f"   📄 Пример счёта: {items[0].get('accountNumber', 'Без номера')}")
            else:
                print("   ⚠️  Smart Invoices не найдены (возможно, их просто нет)")
                
        elif response.status_code == 401:
            print("   ❌ Ошибка 401: Нет прав на CRM")
            return False
        else:
            print(f"   ⚠️  Статус: {response.status_code}")
            data = response.json()
            error_msg = data.get('error_description', data.get('error', 'Неизвестная ошибка'))
            print(f"   📄 Ошибка: {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    print()
    print("✅ Все тесты пройдены! Webhook работает корректно.")
    return True


def main():
    """Главная функция"""
    success = test_webhook()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Webhook URL работает правильно!")
        print("   Теперь можно запускать run_report.py")
    else:
        print("❌ Проблемы с webhook URL")
        print("\n🔧 КАК ИСПРАВИТЬ:")
        print("1. Войдите в Bitrix24: softway.bitrix24.ru")
        print("2. Приложения → Разработчикам → Другое → Входящий вебхук")
        print("3. Проверьте что webhook активен")
        print("4. Убедитесь что есть права на CRM")
        print("5. Скопируйте правильный URL в config.ini")
    
    print("\n⏸️  Нажмите Enter для закрытия...")
    input()


if __name__ == "__main__":
    main() 