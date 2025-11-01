# 🔗 Интеграция и автоматизация

Интеграция ReportB24 с другими системами, автоматизация генерации отчётов, и расширенные сценарии использования.

---

## 🎯 Сценарии интеграции

### 1. Автоматическая генерация по расписанию
- ✅ Ежедневные/еженедельные/месячные отчёты
- ✅ Автоматическая отправка на email
- ✅ Сохранение в облачное хранилище

### 2. Интеграция с ERP системами
- ✅ Импорт данных в 1С
- ✅ Синхронизация с SAP
- ✅ Передача в бухгалтерские системы

### 3. Web API и микросервисы
- ✅ REST API для внешних систем
- ✅ Webhooks для событий
- ✅ Микросервис генерации отчётов

---

## ⏰ Автоматизация по расписанию

### Windows Task Scheduler

**Шаг 1**: Создайте скрипт `scheduled_report.py`

```python
#!/usr/bin/env python3
"""
Автоматическая генерация отчёта для планировщика.
Отправляет результат на email.
"""

import sys
import smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

sys.path.insert(0, str(Path(__file__).parent))

from src.core.app import AppFactory

def send_report_email(report_path: str, recipient: str, smtp_config: dict):
    """Отправляет отчёт на email."""
    
    message = MIMEMultipart()
    message["From"] = smtp_config["sender"]
    message["To"] = recipient
    message["Subject"] = f"Отчёт Bitrix24 за {datetime.now().strftime('%Y-%m-%d')}"
    
    # Текст письма
    body = f"""
    Добрый день!
    
    Во вложении автоматически сгенерированный отчёт из Bitrix24.
    
    Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    ---
    Автоматическое письмо от ReportB24
    """
    message.attach(MIMEText(body, "plain"))
    
    # Прикрепляем отчёт
    with open(report_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="xlsx")
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename={Path(report_path).name}"
        )
        message.attach(attachment)
    
    # Отправляем
    with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
        server.starttls()
        server.login(smtp_config["sender"], smtp_config["password"])
        server.send_message(message)

def main():
    """Основная функция для планировщика."""
    
    # Конфигурация email
    smtp_config = {
        "server": "smtp.gmail.com",
        "port": 587,
        "sender": "reports@company.com",
        "password": "your-app-password"  # Лучше из .env
    }
    recipient = "manager@company.com"
    
    # Генерируем отчёт
    try:
        with AppFactory.create_app("config.ini") as app:
            today = datetime.now().strftime("%Y-%m-%d")
            output_path = f"reports/report_{today}.xlsx"
            
            result = app.generate_report(
                output_path=output_path,
                return_metrics=True
            )
            
            if result.success:
                print(f"✅ Отчёт создан: {output_path}")
                
                # Отправляем на email
                send_report_email(output_path, recipient, smtp_config)
                print(f"✅ Отчёт отправлен на {recipient}")
                
                return 0
            else:
                print(f"❌ Ошибка: {result.error}")
                return 1
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Шаг 2**: Создайте bat-файл `run_scheduled_report.bat`

```batch
@echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
python scheduled_report.py >> logs\scheduled.log 2>&1
```

**Шаг 3**: Настройте Task Scheduler

```powershell
# PowerShell скрипт для создания задания
$action = New-ScheduledTaskAction -Execute "D:\CursorProgs\ReportB24\run_scheduled_report.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount

Register-ScheduledTask -TaskName "ReportB24 Daily" -Action $action -Trigger $trigger -Principal $principal
```

---

### Linux Cron

**Шаг 1**: Создайте скрипт `run_report.sh`

```bash
#!/bin/bash
cd /opt/ReportB24
source .venv/bin/activate
python scheduled_report.py >> logs/scheduled.log 2>&1
```

**Шаг 2**: Настройте cron

```bash
# Редактируем crontab
crontab -e

# Добавляем задание (каждый день в 9:00)
0 9 * * * /opt/ReportB24/run_report.sh

# Или каждый понедельник в 9:00
0 9 * * 1 /opt/ReportB24/run_report.sh

# Или первое число каждого месяца
0 9 1 * * /opt/ReportB24/run_report.sh
```

---

## 🌐 REST API сервис

### Flask API для генерации отчётов

```python
from flask import Flask, request, send_file, jsonify
from pathlib import Path
import uuid
from datetime import datetime

from src.core.app import AppFactory

app = Flask(__name__)

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """
    Генерирует отчёт по API запросу.
    
    POST /api/generate-report
    {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "email": "optional@email.com"  // Опционально
    }
    """
    
    try:
        # Получаем параметры
        data = request.get_json()
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        email = data.get("email")
        
        # Валидация
        if not start_date or not end_date:
            return jsonify({
                "success": False,
                "error": "start_date и end_date обязательны"
            }), 400
        
        # Генерируем отчёт
        report_id = str(uuid.uuid4())
        output_path = f"reports/api_{report_id}.xlsx"
        
        with AppFactory.create_app() as app_instance:
            result = app_instance.generate_report(
                output_path=output_path,
                return_metrics=True
            )
        
        if result.success:
            response = {
                "success": True,
                "report_id": report_id,
                "download_url": f"/api/download/{report_id}",
                "metrics": {
                    "invoices": result.quality_metrics.brief_valid,
                    "products": result.quality_metrics.detailed_valid,
                    "issues": result.quality_metrics.total_issues
                }
            }
            
            # Отправляем на email если указан
            if email:
                send_report_email(output_path, email, smtp_config)
                response["email_sent"] = True
            
            return jsonify(response), 200
        else:
            return jsonify({
                "success": False,
                "error": str(result.error)
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/download/<report_id>', methods=['GET'])
def download_report(report_id):
    """Скачивание сгенерированного отчёта."""
    
    file_path = Path(f"reports/api_{report_id}.xlsx")
    
    if not file_path.exists():
        return jsonify({
            "success": False,
            "error": "Отчёт не найден"
        }), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

@app.route('/api/status', methods=['GET'])
def api_status():
    """Статус API."""
    return jsonify({
        "status": "online",
        "version": "3.1.0",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Использование API**:

```python
import requests

# Генерация отчёта
response = requests.post('http://localhost:5000/api/generate-report', json={
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "email": "manager@company.com"
})

if response.status_code == 200:
    data = response.json()
    report_id = data["report_id"]
    
    # Скачиваем отчёт
    report = requests.get(f'http://localhost:5000/api/download/{report_id}')
    with open('downloaded_report.xlsx', 'wb') as f:
        f.write(report.content)
    
    print(f"✅ Отчёт скачан: {data['metrics']}")
```

---

## ☁️ Облачные хранилища

### Yandex Disk

```python
import yadisk

def upload_to_yandex_disk(local_path: str, token: str, remote_path: str):
    """Загружает отчёт на Яндекс.Диск."""
    
    y = yadisk.YaDisk(token=token)
    
    # Проверяем авторизацию
    if not y.check_token():
        raise Exception("Неверный токен Яндекс.Диска")
    
    # Загружаем файл
    y.upload(local_path, remote_path, overwrite=True)
    
    # Получаем ссылку для скачивания
    download_link = y.get_download_link(remote_path)
    
    print(f"✅ Загружено на Яндекс.Диск: {remote_path}")
    print(f"   Ссылка: {download_link}")

# Использование
upload_to_yandex_disk(
    local_path="reports/report.xlsx",
    token="YOUR_YANDEX_DISK_TOKEN",
    remote_path="/Reports/report_2024-01-01.xlsx"
)
```

### Google Drive

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_google_drive(local_path: str, credentials_path: str, folder_id: str):
    """Загружает отчёт на Google Drive."""
    
    # Аутентификация
    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    
    service = build('drive', 'v3', credentials=creds)
    
    # Метаданные файла
    file_metadata = {
        'name': Path(local_path).name,
        'parents': [folder_id]
    }
    
    # Загружаем
    media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    print(f"✅ Загружено на Google Drive")
    print(f"   ID: {file.get('id')}")
    print(f"   Ссылка: {file.get('webViewLink')}")

# Использование
upload_to_google_drive(
    local_path="reports/report.xlsx",
    credentials_path="credentials.json",
    folder_id="YOUR_FOLDER_ID"
)
```

---

## 📊 Интеграция с 1С

### Экспорт для 1С

```python
import csv
from decimal import Decimal

def export_for_1c(brief_data: list, output_path: str):
    """Экспортирует данные в формат для импорта в 1С."""
    
    # Формат CSV для 1С
    with open(output_path, 'w', newline='', encoding='cp1251') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Заголовок
        writer.writerow([
            'НомерСчета',
            'Контрагент',
            'ИНН',
            'Сумма',
            'Дата',
            'Валюта'
        ])
        
        # Данные
        for record in brief_data:
            writer.writerow([
                record.get('account_number', ''),
                record.get('company_name', ''),
                record.get('inn', ''),
                f"{record.get('total_amount', 0):.2f}".replace('.', ','),  # 1С любит запятые
                record.get('date_create', ''),
                'RUB'
            ])
    
    print(f"✅ Файл для 1С создан: {output_path}")

# Использование в workflow
with AppFactory.create_app() as app:
    result = app.generate_report(return_metrics=True)
    
    # Экспортируем для 1С
    brief_data = app.data_processor.get_brief_data()
    export_for_1c(brief_data, "reports/1c_import.csv")
```

---

## 🔄 Webhook обработчик

### Webhook сервер для событий Bitrix24

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# Секретный ключ для проверки подписи
WEBHOOK_SECRET = "your-secret-key"

@app.route('/webhook/bitrix24', methods=['POST'])
def bitrix24_webhook():
    """
    Обрабатывает webhook от Bitrix24.
    Автоматически генерирует отчёт при создании счёта.
    """
    
    # Проверяем подпись
    signature = request.headers.get('X-Bitrix-Signature')
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 403
    
    # Получаем данные
    data = request.get_json()
    event_type = data.get('event')
    
    if event_type == 'ONCRM_SMART_INVOICE_ADD':
        # Новый счёт создан
        invoice_id = data.get('data', {}).get('FIELDS', {}).get('ID')
        
        print(f"📨 Получен webhook: новый счёт #{invoice_id}")
        
        # Запускаем генерацию отчёта в фоне
        from threading import Thread
        thread = Thread(target=generate_report_async)
        thread.start()
        
        return jsonify({"status": "accepted"}), 202
    
    return jsonify({"status": "ignored"}), 200

def verify_signature(payload: bytes, signature: str) -> bool:
    """Проверяет подпись webhook."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def generate_report_async():
    """Генерирует отчёт асинхронно."""
    try:
        with AppFactory.create_app() as app:
            result = app.generate_report()
            if result.success:
                print(f"✅ Отчёт автоматически создан")
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

---

## 🐳 Docker контейнер

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём директории
RUN mkdir -p reports logs

# Переменные окружения
ENV PYTHONUNBUFFERED=1

# Порт для API
EXPOSE 5000

# Точка входа
CMD ["python", "api_server.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  reportb24:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
      - ./config.ini:/app/config.ini
      - ./.env:/app/.env
    environment:
      - TZ=Europe/Moscow
    restart: unless-stopped
    
  # Опционально: планировщик
  scheduler:
    build: .
    command: python scheduled_report.py
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
      - ./config.ini:/app/config.ini
    depends_on:
      - reportb24
```

**Запуск**:

```bash
# Сборка и запуск
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down
```

---

## 📚 Дополнительные материалы

### Документация

- **[Configuration Guide](../user/configuration.md)** - Настройка для автоматизации
- **[API Reference](../technical/api/index.md)** - API для интеграции
- **[Deployment Guide](../technical/deployment.md)** - Production развёртывание

### Примеры

- **[Basic Report](basic-report.md)** - Базовая генерация
- **[Batch Processing](batch-processing.md)** - Оптимизация для больших объёмов
- **[Error Handling](error-handling.md)** - Обработка ошибок в автоматизации

---

[← Назад к примерам](index.md) | [Troubleshooting →](../user/troubleshooting.md)
