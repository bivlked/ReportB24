# 📖 User Guide

Полное руководство по использованию ReportB24 - от базовых до продвинутых сценариев.

---

## 📚 Содержание

1. [Базовое использование](#-базовое-использование)
2. [Генерация отчетов](#-генерация-отчетов)
3. [Программное использование](#-программное-использование)
4. [Продвинутые сценарии](#-продвинутые-сценарии)
5. [Настройка и оптимизация](#-настройка-и-оптимизация)
6. [Лучшие практики](#-лучшие-практики)

---

## 🚀 Базовое использование

### Подготовка к работе

**Активация виртуального окружения**:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

**Проверка готовности**:

```bash
# Проверка конфигурации
python -c "from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           print('✅ Configuration loaded')"

# Проверка подключения к Bitrix24
python -c "from src.bitrix24_client.client import Bitrix24Client; \
           from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           client = Bitrix24Client(config.get_webhook_url()); \
           profile = client.call('profile'); \
           print(f'✅ Connected as: {profile.get(\"NAME\")}')"
```

---

## 📊 Генерация отчетов

### Базовый отчет (один лист)

**Использование скрипта**:

```bash
python scripts/run_report.py
```

**Что создается**:
- 📄 Excel файл в `reports/`
- 📋 Один лист "Краткий" с обзором счетов
- 📈 Сводная информация по НДС

**Содержимое отчета**:
- Номер счета
- Контрагент
- ИНН
- Дата счета
- Дата оплаты
- Сумма
- НДС

---

### Детальный отчет (два листа)

**Использование скрипта**:

```bash
python scripts/run_detailed_report.py
```

**Что создается**:
- 📄 Excel файл в `reports/`
- 📋 Два листа:
  - "Краткий" - обзор счетов
  - "Полный" - детализация всех товаров с зебра-эффектом

**Содержимое листа "Полный"**:
- Номер счета
- Контрагент
- ИНН
- Наименование товара
- Количество
- Единица измерения
- Цена
- Сумма

---

### Настройка периода отчета

**Через config.ini**:

```ini
[ReportPeriod]
# Формат: дд.мм.гггг
startdate = 01.01.2024
enddate = 31.03.2024
```

**Примеры периодов**:

```ini
# Один месяц (январь 2024)
startdate = 01.01.2024
enddate = 31.01.2024

# Квартал (Q1 2024)
startdate = 01.01.2024
enddate = 31.03.2024

# Полугодие
startdate = 01.01.2024
enddate = 30.06.2024

# Год
startdate = 01.01.2024
enddate = 31.12.2024
```

---

## 💻 Программное использование

### Базовый пример

```python
from src.core.app import create_app

# Создание приложения
app = create_app('config.ini')

# Инициализация
if app.initialize():
    print("✅ Application initialized")
    
    # Генерация отчета
    report_path = app.generate_report('my_report.xlsx')
    print(f"Report created: {report_path}")
else:
    print("❌ Initialization failed")
    print(app.get_error_report())
```

---

### Программная настройка периода

```python
from src.core.app import create_app
from datetime import datetime, timedelta

app = create_app('config.ini')
app.initialize()

# Последние 30 дней
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

app.set_report_period(
    start_date.strftime('%d.%m.%Y'),
    end_date.strftime('%d.%m.%Y')
)

# Генерация
filename = f"report_last_30_days_{datetime.now().strftime('%Y%m%d')}.xlsx"
app.generate_report(filename)
```

---

### Получение данных без генерации отчета

```python
from src.bitrix24_client.client import Bitrix24Client
from src.config.config_reader import SecureConfigReader
from src.data_processor.data_processor import DataProcessor

# Инициализация
config = SecureConfigReader('config.ini')
client = Bitrix24Client(config.get_webhook_url())
processor = DataProcessor()

# Получение счетов
invoices = client.get_invoices_by_period('01.01.2024', '31.03.2024')
print(f"Found {len(invoices)} invoices")

# Обработка данных
processed_invoices = []
for invoice in invoices:
    processed = processor.process_invoice_record(invoice)
    processed_invoices.append(processed)
    print(f"Invoice {processed['invoice_number']}: {processed['total_amount']} руб.")
```

---

### Генерация с товарами программно

```python
from src.excel_generator.generator import ExcelReportGenerator
from src.bitrix24_client.client import Bitrix24Client
from src.data_processor.data_processor import DataProcessor
from src.config.config_reader import SecureConfigReader

# Инициализация
config = SecureConfigReader('config.ini')
client = Bitrix24Client(config.get_webhook_url())
processor = DataProcessor()
generator = ExcelReportGenerator()

# Получение данных
invoices = client.get_invoices_by_period('01.01.2024', '31.03.2024')

# Создание двухлистового отчета
workbook = generator.create_multi_sheet_report(invoices, client, processor)

# Сохранение
filename = f"detailed_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
workbook.save(f"reports/{filename}")
print(f"✅ Detailed report created: reports/{filename}")
```

---

## 🎯 Продвинутые сценарии

### Автоматизированная месячная отчетность

**Скрипт `generate_monthly.py`**:

```python
from src.core.app import create_app
from datetime import datetime
from calendar import monthrange

def generate_monthly_report(year: int, month: int):
    """Генерация отчета за конкретный месяц"""
    # Первый день месяца
    start_date = datetime(year, month, 1)
    
    # Последний день месяца
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day)
    
    # Создание приложения
    app = create_app('config.ini')
    if not app.initialize():
        print(f"❌ Initialization failed: {app.get_error_report()}")
        return False
    
    # Установка периода
    app.set_report_period(
        start_date.strftime('%d.%m.%Y'),
        end_date.strftime('%d.%m.%Y')
    )
    
    # Генерация отчета
    month_name = start_date.strftime('%B_%Y').lower()
    filename = f"report_{month_name}.xlsx"
    
    success = app.generate_report(filename)
    if success:
        print(f"✅ Monthly report for {month_name} created: {filename}")
    else:
        print(f"❌ Failed to generate report: {app.get_error_report()}")
    
    return success

# Использование
if __name__ == "__main__":
    # Отчет за март 2024
    generate_monthly_report(2024, 3)
    
    # Отчеты за весь квартал
    for month in [1, 2, 3]:
        generate_monthly_report(2024, month)
```

---

### Фильтрация по контрагентам

```python
from src.core.app import create_app

def generate_contractor_report(inn: str, start_date: str, end_date: str):
    """Отчет по конкретному контрагенту"""
    app = create_app('config.ini')
    app.initialize()
    
    # Получение всех счетов
    invoices = app.bitrix_client.get_invoices_by_period(start_date, end_date)
    
    # Фильтрация по ИНН
    filtered_invoices = [
        inv for inv in invoices 
        if inv.get('company', {}).get('inn') == inn
    ]
    
    print(f"Found {len(filtered_invoices)} invoices for INN {inn}")
    
    # Генерация отчета только для отфильтрованных счетов
    # Используйте ExcelReportGenerator напрямую с filtered_invoices
    from src.excel_generator.generator import ExcelReportGenerator
    
    generator = ExcelReportGenerator()
    workbook = generator.create_multi_sheet_report(
        filtered_invoices, 
        app.bitrix_client, 
        app.data_processor
    )
    
    filename = f"contractor_{inn}_{start_date.replace('.', '')}_{end_date.replace('.', '')}.xlsx"
    workbook.save(f"reports/{filename}")
    print(f"✅ Contractor report created: reports/{filename}")

# Использование
generate_contractor_report('1234567890', '01.01.2024', '31.03.2024')
```

---

### Пакетная генерация для нескольких периодов

```python
from src.core.app import create_app
from datetime import datetime, timedelta

def generate_batch_reports(start_date: datetime, end_date: datetime, interval_days: int = 30):
    """Генерация отчетов пакетом с заданным интервалом"""
    app = create_app('config.ini')
    if not app.initialize():
        return
    
    current_start = start_date
    report_num = 1
    
    while current_start < end_date:
        # Конец текущего периода
        current_end = min(current_start + timedelta(days=interval_days - 1), end_date)
        
        # Генерация отчета
        app.set_report_period(
            current_start.strftime('%d.%m.%Y'),
            current_end.strftime('%d.%m.%Y')
        )
        
        filename = f"batch_report_{report_num:02d}_{current_start.strftime('%Y%m%d')}_{current_end.strftime('%Y%m%d')}.xlsx"
        
        if app.generate_report(filename):
            print(f"✅ Report {report_num} created: {filename}")
        else:
            print(f"❌ Failed to create report {report_num}")
        
        # Следующий период
        current_start = current_end + timedelta(days=1)
        report_num += 1
    
    print(f"✅ Batch generation complete: {report_num - 1} reports")

# Использование: Отчеты за год по месяцам
generate_batch_reports(
    datetime(2024, 1, 1), 
    datetime(2024, 12, 31), 
    interval_days=30
)
```

---

### Статистика и аналитика

```python
from src.bitrix24_client.client import Bitrix24Client
from src.config.config_reader import SecureConfigReader
from src.data_processor.data_processor import DataProcessor
from collections import defaultdict

def generate_statistics(start_date: str, end_date: str):
    """Генерация статистики по счетам"""
    config = SecureConfigReader('config.ini')
    client = Bitrix24Client(config.get_webhook_url())
    processor = DataProcessor()
    
    # Получение данных
    invoices = client.get_invoices_by_period(start_date, end_date)
    
    # Статистика
    stats = {
        'total_invoices': len(invoices),
        'total_amount': 0,
        'total_vat': 0,
        'by_contractor': defaultdict(lambda: {'count': 0, 'amount': 0}),
        'by_month': defaultdict(lambda: {'count': 0, 'amount': 0})
    }
    
    # Обработка
    for invoice in invoices:
        processed = processor.process_invoice_record(invoice)
        
        # Общие суммы
        stats['total_amount'] += float(processed.get('total_amount', 0))
        stats['total_vat'] += float(processed.get('vat_amount', 0))
        
        # По контрагентам
        contractor = processed.get('company_name', 'Unknown')
        stats['by_contractor'][contractor]['count'] += 1
        stats['by_contractor'][contractor]['amount'] += float(processed.get('total_amount', 0))
        
        # По месяцам
        invoice_date = processed.get('invoice_date', '')
        if invoice_date:
            month = invoice_date[3:10]  # мм.гггг
            stats['by_month'][month]['count'] += 1
            stats['by_month'][month]['amount'] += float(processed.get('total_amount', 0))
    
    # Вывод
    print(f"\n📊 Статистика за период {start_date} - {end_date}")
    print(f"━" * 60)
    print(f"Всего счетов: {stats['total_invoices']}")
    print(f"Общая сумма: {stats['total_amount']:,.2f} руб.")
    print(f"Общий НДС: {stats['total_vat']:,.2f} руб.")
    
    print(f"\n📈 Топ-5 контрагентов по сумме:")
    sorted_contractors = sorted(
        stats['by_contractor'].items(), 
        key=lambda x: x[1]['amount'], 
        reverse=True
    )[:5]
    
    for i, (contractor, data) in enumerate(sorted_contractors, 1):
        print(f"{i}. {contractor}: {data['count']} счетов, {data['amount']:,.2f} руб.")
    
    print(f"\n📅 По месяцам:")
    for month, data in sorted(stats['by_month'].items()):
        print(f"{month}: {data['count']} счетов, {data['amount']:,.2f} руб.")
    
    return stats

# Использование
stats = generate_statistics('01.01.2024', '31.03.2024')
```

---

## ⚙️ Настройка и оптимизация

### Оптимизация для больших объемов

**config.ini для больших отчетов**:

```ini
[Performance]
# Увеличьте batch size для ускорения
batch_size = 100

# Больше параллельных запросов
max_concurrent_requests = 5

# Увеличьте кэш
company_cache_size = 5000

# Включите multiprocessing
use_multiprocessing = true
max_workers = 8

# Увеличьте timeout
api_timeout = 120
```

---

### Настройка логирования

**Подробное логирование для отладки**:

```ini
[AppSettings]
loglevel = DEBUG
logfile = logs/debug.log
maxlogsize = 50
backupcount = 10
```

**Минимальное логирование для production**:

```ini
[AppSettings]
loglevel = WARNING
logfile = /var/log/reportb24/app.log
maxlogsize = 100
backupcount = 30
```

---

### Кастомизация форматирования Excel

**Через config.ini**:

```ini
[Excel]
# Цвета заголовков
summary_header_color = #FFD700  # Золотой
detailed_header_color = #87CEEB  # Небесно-голубой

# Зебра-эффект
zebra_color_1 = #F5F5F5
zebra_color_2 = #FFFFFF

# Настройки
freeze_panes = true
auto_width = true
show_gridlines = false
```

**Программно**:

```python
from src.excel_generator.formatter import ExcelFormatter

# Создайте кастомный formatter
formatter = ExcelFormatter()
formatter.set_header_color('#FF6B35')  # Оранжевый
formatter.set_zebra_colors('#F0F0F0', '#FFFFFF')

# Используйте в генераторе
generator = ExcelReportGenerator(formatter=formatter)
```

---

## 🎓 Лучшие практики

### Безопасность

1. **Никогда не коммитьте .env**:
   ```bash
   # Убедитесь что .env в .gitignore
   cat .gitignore | grep .env
   ```

2. **Регулярно обновляйте webhook**:
   - Меняйте webhook каждые 3-6 месяцев
   - Отзывайте старые webhook после замены

3. **Ограничьте права webhook**:
   - Только необходимые: `crm`, `smart_invoice`
   - Не давайте избыточные права

---

### Производительность

1. **Разбивайте большие периоды**:
   ```python
   # ❌ Неэффективно: Весь год за раз
   generate_report('01.01.2024', '31.12.2024')
   
   # ✅ Эффективно: По кварталам
   for quarter in [(1,3), (4,6), (7,9), (10,12)]:
       generate_report(f'01.{quarter[0]:02d}.2024', f'30.{quarter[1]:02d}.2024')
   ```

2. **Используйте batch API**:
   - Уже включен в v2.4.0+
   - Настройте batch_size в config.ini

3. **Оптимизируйте config.ini**:
   - Увеличьте кэш для повторяющихся запросов
   - Настройте multiprocessing для CPU-intensive задач

---

### Управление отчетами

1. **Структурированное именование**:
   ```python
   # Формат: report_YYYY-MM-DD_HHMMSS.xlsx
   filename = f"report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx"
   
   # С периодом: report_2024-01-01_2024-03-31.xlsx
   filename = f"report_{start_date.replace('.', '-')}_{end_date.replace('.', '-')}.xlsx"
   ```

2. **Организация по папкам**:
   ```python
   import os
   
   # Создайте структуру
   year = '2024'
   month = '03'
   report_dir = f"reports/{year}/{month}"
   os.makedirs(report_dir, exist_ok=True)
   
   # Сохраняйте в структуру
   filename = f"{report_dir}/report_{datetime.now().strftime('%Y%m%d')}.xlsx"
   ```

3. **Автоматическая очистка старых отчетов**:
   ```python
   import os
   from datetime import datetime, timedelta
   
   def cleanup_old_reports(directory='reports', days=90):
       """Удаление отчетов старше N дней"""
       cutoff = datetime.now() - timedelta(days=days)
       
       for root, dirs, files in os.walk(directory):
           for file in files:
               if file.endswith('.xlsx'):
                   filepath = os.path.join(root, file)
                   file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                   
                   if file_time < cutoff:
                       os.remove(filepath)
                       print(f"Removed old report: {filepath}")
   
   # Использование
   cleanup_old_reports(days=90)
   ```

---

### Мониторинг и логирование

1. **Проверяйте логи регулярно**:
   ```bash
   # Последние ошибки
   cat logs/app.log | grep ERROR | tail -20
   
   # Статистика за сегодня
   cat logs/app.log | grep $(date +%Y-%m-%d)
   ```

2. **Автоматические уведомления**:
   ```python
   import smtplib
   from email.mime.text import MIMEText
   
   def send_notification(subject, body):
       """Отправка email уведомления"""
       msg = MIMEText(body)
       msg['Subject'] = subject
       msg['From'] = 'reportb24@example.com'
       msg['To'] = 'admin@example.com'
       
       # Настройте SMTP
       with smtplib.SMTP('smtp.example.com', 587) as server:
           server.starttls()
           server.login('user', 'password')
           server.send_message(msg)
   
   # Используйте после генерации
   if success:
       send_notification('Report Generated', f'Report {filename} created successfully')
   else:
       send_notification('Report Generation Failed', f'Failed to generate report: {error}')
   ```

---

## 📚 Дополнительно

### Полезные ресурсы

- 🚀 [Quick Start](quick-start.md) - Быстрый старт
- ⚙️ [Configuration](configuration.md) - Настройка
- ❓ [FAQ](faq.md) - Частые вопросы
- 🔧 [Troubleshooting](troubleshooting.md) - Решение проблем
- 🔒 [Security Deep Dive](../technical/security-deep-dive.md) - Безопасность
- 📊 [Examples](../examples/) - Примеры кода

---

<div align="center">

[← Configuration](configuration.md) • [FAQ →](faq.md)

**Нужна помощь?** [Create Issue](https://github.com/bivlked/ReportB24/issues) • [Discussions](https://github.com/bivlked/ReportB24/discussions)

</div>
