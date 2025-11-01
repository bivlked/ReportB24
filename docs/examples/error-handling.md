# 🛡️ Обработка ошибок

Правильная обработка ошибок API, валидация данных и recovery стратегии для надёжной работы приложения.

---

## 🎯 Типы ошибок

### 1. Сетевые ошибки
- **Timeout** - превышено время ожидания
- **ConnectionError** - нет подключения к интернету
- **DNS Error** - не удаётся разрешить домен

### 2. API ошибки Bitrix24
- **Authentication Error** - неверный webhook URL
- **Rate Limit Error** - превышен лимит запросов (2/сек)
- **Server Error** - ошибка сервера Bitrix24 (5xx)
- **Not Found** - ресурс не найден (404)

### 3. Ошибки данных
- **ValidationError** - некорректные данные
- **MissingDataError** - отсутствуют обязательные поля
- **FormatError** - неправильный формат (даты, числа)

---

## 💻 Базовая обработка ошибок

### Проверка конфигурации

```python
from src.core.app import AppFactory

# Безопасный запуск с обработкой ошибок
def safe_report_generation():
    """Генерация отчёта с полной обработкой ошибок."""
    
    try:
        with AppFactory.create_app("config.ini") as app:
            # 1. Проверяем конфигурацию
            if not app.validate_configuration():
                error_report = app.get_error_report()
                print("❌ Ошибки конфигурации:")
                print(error_report)
                return False
            
            # 2. Тестируем API подключение
            if not app.test_api_connection():
                print("❌ Не удалось подключиться к Bitrix24")
                print("Проверьте:")
                print("  - Webhook URL в config.ini")
                print("  - Подключение к интернету")
                print("  - Доступность портала Bitrix24")
                return False
            
            # 3. Генерируем отчёт
            result = app.generate_report(
                output_path="reports/report.xlsx",
                return_metrics=True
            )
            
            if result.success:
                print(f"✅ Отчёт создан: {result.output_path}")
                return True
            else:
                print(f"❌ Ошибка генерации: {result.error}")
                return False
    
    except KeyboardInterrupt:
        print("\n⚠️ Операция прервана пользователем")
        return False
    
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

# Использование
if __name__ == "__main__":
    success = safe_report_generation()
    exit(0 if success else 1)
```

---

## 🔄 Retry механизм

### Автоматический retry для API запросов

Система автоматически повторяет запросы при временных ошибках:

```python
from src.bitrix24_client.client import Bitrix24Client

# Встроенный retry в Bitrix24Client
client = Bitrix24Client("https://portal.bitrix24.ru/rest/1/token/")

# Автоматический retry при:
# - Timeout (3 попытки)
# - Server Error 5xx (3 попытки)
# - Rate Limit (автоматическая задержка + retry)

invoices = client.get_smart_invoices()  # Автоматически обрабатывает ошибки
```

### Ручной retry для критичных операций

```python
import time
from typing import Any, Callable

def retry_on_error(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Выполняет функцию с повторными попытками при ошибках.
    
    Args:
        func: Функция для выполнения
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками (сек)
        backoff: Множитель задержки (exponential backoff)
        exceptions: Кортеж исключений для повтора
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Последнее исключение если все попытки исчерпаны
    """
    current_delay = delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_attempts:
                print(f"⚠️ Попытка {attempt}/{max_attempts} неудачна: {e}")
                print(f"   Повтор через {current_delay:.1f} сек...")
                time.sleep(current_delay)
                current_delay *= backoff
            else:
                print(f"❌ Все {max_attempts} попытки исчерпаны")
                raise last_exception

# Использование
def fetch_invoices():
    """Функция, которая может временно fail."""
    client = Bitrix24Client(webhook_url)
    return client.get_smart_invoices()

# Автоматический retry с exponential backoff
invoices = retry_on_error(
    func=fetch_invoices,
    max_attempts=5,
    delay=1.0,
    backoff=2.0,
    exceptions=(ConnectionError, TimeoutError)
)
```

---

## 🔍 Валидация данных

### Проверка качества отчёта

```python
from src.excel_generator.validation import validate_brief_data, validate_detailed_data

# Валидация кратких данных
brief_data = [...]  # Ваши данные
brief_metrics = validate_brief_data(brief_data)

print(f"✅ Валидных записей: {brief_metrics.valid_count}")
print(f"⚠️ Предупреждений: {brief_metrics.warning_count}")
print(f"❌ Ошибок: {brief_metrics.error_count}")

# Проблемы с высоким приоритетом
critical_issues = [
    issue for issue in brief_metrics.issues
    if issue.severity == "ERROR"
]

if critical_issues:
    print("\n❌ Критичные проблемы:")
    for issue in critical_issues:
        print(f"  - {issue.message}")
        print(f"    Контекст: {issue.context}")

# Валидация детальных данных
detailed_data = [...]  # Ваши данные
detailed_metrics = validate_detailed_data(detailed_data)

# Анализ проблем
if detailed_metrics.total_issues > 0:
    print(f"\n⚠️ Обнаружено проблем: {detailed_metrics.total_issues}")
    
    # Группируем по типу
    by_type = {}
    for issue in detailed_metrics.issues:
        issue_type = issue.message.split(":")[0]
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
    
    print("Распределение по типам:")
    for issue_type, count in by_type.items():
        print(f"  {issue_type}: {count}")
```

### Кастомная валидация

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationIssue:
    """Проблема валидации."""
    severity: str  # ERROR, WARNING, INFO
    message: str
    context: dict

def validate_invoice_data(invoices: List[dict]) -> List[ValidationIssue]:
    """Валидирует данные счетов."""
    issues = []
    
    for i, invoice in enumerate(invoices):
        # Проверка обязательных полей
        required_fields = ["id", "accountNumber", "opportunity"]
        for field in required_fields:
            if field not in invoice or not invoice[field]:
                issues.append(ValidationIssue(
                    severity="ERROR",
                    message=f"Отсутствует обязательное поле: {field}",
                    context={"invoice_index": i, "invoice_id": invoice.get("id")}
                ))
        
        # Проверка формата суммы
        if "opportunity" in invoice:
            try:
                amount = float(invoice["opportunity"])
                if amount < 0:
                    issues.append(ValidationIssue(
                        severity="WARNING",
                        message="Отрицательная сумма счёта",
                        context={"invoice_id": invoice.get("id"), "amount": amount}
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity="ERROR",
                    message="Некорректный формат суммы",
                    context={"invoice_id": invoice.get("id"), "value": invoice["opportunity"]}
                ))
        
        # Проверка формата даты
        if "dateCreate" in invoice:
            date_str = invoice["dateCreate"]
            if not isinstance(date_str, str) or len(date_str) < 10:
                issues.append(ValidationIssue(
                    severity="WARNING",
                    message="Некорректный формат даты",
                    context={"invoice_id": invoice.get("id"), "date": date_str}
                ))
    
    return issues

# Использование
invoices = client.get_smart_invoices()
validation_issues = validate_invoice_data(invoices)

if validation_issues:
    print(f"⚠️ Найдено проблем: {len(validation_issues)}")
    
    # Показываем первые 5
    for issue in validation_issues[:5]:
        print(f"  [{issue.severity}] {issue.message}")
else:
    print("✅ Данные валидны")
```

---

## 🛠️ Recovery стратегии

### Частичная генерация при ошибках

```python
def generate_report_with_fallback(output_path="reports/report.xlsx"):
    """Генерирует отчёт даже при частичных ошибках."""
    
    with AppFactory.create_app() as app:
        client = app.bitrix_client
        processor = app.data_processor
        processor.set_bitrix_client(client)
        generator = app.excel_generator
        
        # Загружаем счета
        invoices = client.get_smart_invoices()
        print(f"Загружено счетов: {len(invoices)}")
        
        # Обрабатываем с отслеживанием ошибок
        brief_data = []
        detailed_data = []
        failed_invoices = []
        
        for invoice in invoices:
            try:
                # Обрабатываем краткие данные
                brief_record = processor.process_invoice_record(invoice)
                if brief_record:
                    brief_data.append(brief_record)
                
                # Загружаем товары
                invoice_id = invoice.get("id")
                products_result = client.get_products_by_invoice(invoice_id)
                
                if products_result["has_error"]:
                    failed_invoices.append({
                        "id": invoice_id,
                        "number": invoice.get("accountNumber"),
                        "error": products_result["error_message"]
                    })
                    continue
                
                # Обрабатываем детальные данные
                products = products_result["products"]
                invoice_info = {
                    "account_number": invoice.get("accountNumber"),
                    "company_name": brief_record.get("company_name", "Не указано"),
                    "inn": brief_record.get("inn", "Не указано"),
                    "invoice_id": invoice_id
                }
                
                formatted = processor.format_detailed_products_for_excel(
                    products, invoice_info
                )
                detailed_data.extend(formatted)
            
            except Exception as e:
                print(f"⚠️ Ошибка обработки счёта {invoice.get('accountNumber')}: {e}")
                failed_invoices.append({
                    "id": invoice.get("id"),
                    "number": invoice.get("accountNumber"),
                    "error": str(e)
                })
                continue
        
        # Генерируем отчёт с доступными данными
        if brief_data:
            result = generator.generate_comprehensive_report(
                brief_data,
                detailed_data,
                output_path,
                return_metrics=True
            )
            
            print(f"\n✅ Отчёт создан: {output_path}")
            print(f"   Обработано: {len(brief_data)}/{len(invoices)} счетов")
            
            # Отчёт об ошибках
            if failed_invoices:
                print(f"\n⚠️ Ошибки при обработке {len(failed_invoices)} счетов:")
                for failed in failed_invoices[:10]:  # Первые 10
                    print(f"   {failed['number']}: {failed['error']}")
                
                # Сохраняем в файл
                error_log_path = "reports/error_log.txt"
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Отчёт об ошибках генерации\n")
                    f.write(f"Всего ошибок: {len(failed_invoices)}\n\n")
                    for failed in failed_invoices:
                        f.write(f"Счёт: {failed['number']}\n")
                        f.write(f"ID: {failed['id']}\n")
                        f.write(f"Ошибка: {failed['error']}\n")
                        f.write("-" * 50 + "\n")
                
                print(f"   Подробности сохранены в: {error_log_path}")
            
            return True
        else:
            print("❌ Нет данных для генерации отчёта")
            return False

# Использование
generate_report_with_fallback()
```

---

## 📊 Логирование ошибок

### Настройка детального логирования

```python
import logging
from pathlib import Path

def setup_error_logging():
    """Настраивает детальное логирование ошибок."""
    
    # Создаём директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настраиваем logger
    logger = logging.getLogger("ReportB24")
    logger.setLevel(logging.DEBUG)
    
    # Файловый handler для всех логов
    all_logs = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    all_logs.setLevel(logging.DEBUG)
    all_logs.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    # Файловый handler только для ошибок
    error_logs = logging.FileHandler(log_dir / "errors.log", encoding="utf-8")
    error_logs.setLevel(logging.ERROR)
    error_logs.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s\n"
        "%(pathname)s:%(lineno)d\n"
        "%(exc_info)s\n"
    ))
    
    # Добавляем handlers
    logger.addHandler(all_logs)
    logger.addHandler(error_logs)
    
    return logger

# Использование
logger = setup_error_logging()

try:
    # Ваш код
    result = app.generate_report()
except Exception as e:
    logger.error("Ошибка генерации отчёта", exc_info=True)
    raise
```

---

## 🔔 Уведомления об ошибках

### Email уведомления

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_error_notification(error_message: str, context: dict):
    """Отправляет email уведомление об ошибке."""
    
    # Настройки из config.ini
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "your-email@gmail.com"
    sender_password = "your-app-password"
    recipient_email = "admin@company.com"
    
    # Формируем сообщение
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "❌ Ошибка генерации отчёта ReportB24"
    
    body = f"""
    Произошла ошибка при генерации отчёта:
    
    Ошибка: {error_message}
    
    Контекст:
    {context}
    
    Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    ---
    Автоматическое уведомление от ReportB24
    """
    
    message.attach(MIMEText(body, "plain"))
    
    # Отправляем
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        print("✅ Email уведомление отправлено")
    except Exception as e:
        print(f"⚠️ Не удалось отправить email: {e}")
```

---

## 📚 Дополнительные материалы

### Документация

- **[Bitrix24Client API](../technical/api/bitrix24-client.md)** - Обработка API ошибок
- **[Validation Guide](../technical/api/excel-generator.md#validation)** - Валидация данных
- **[Error Handler](../technical/development.md#error-handling)** - Архитектура обработки ошибок

### Примеры

- **[Basic Report](basic-report.md)** - Базовая генерация
- **[Batch Processing](batch-processing.md)** - Обработка больших объёмов
- **[Integration](integration.md)** - Автоматизация с error handling

---

[← Назад к примерам](index.md) | [Integration →](integration.md)
