# 📘 Пользовательское руководство ReportB24

Добро пожаловать в руководство пользователя ReportB24. Здесь собраны практические инструкции по запуску отчётов, настройке периодов и фильтров, автоматизации и проверке результатов.

<a id="быстрый-обзор"></a>
## 🚀 Быстрый обзор

1. Следуйте разделу «Быстрый старт (Windows)» в [README](../README.md) для базовой установки.
2. Подготовьте `config.ini` и `.env`, указав рабочий период и webhook Bitrix24.
3. Запустите `py run_report.py`, чтобы получить двухлистовой отчёт в папке `reports/`.
4. Используйте сценарии из этого документа для расширенных задач.

<a id="работа-с-фильтрами-и-периодами"></a>
## 🧭 Работа с фильтрами и периодами

### Настройка периода в конфигурации

- `config.ini` → секция `[ReportPeriod]` управляет диапазоном дат.
- Формат дат: `дд.мм.гггг`.
- После редактирования перезапустите `run_report.py` для применения изменений.

### Программное изменение периода

```python
from datetime import datetime, timedelta
from src.core.app import AppFactory

with AppFactory.create_app('config.ini') as app:
    if not app.initialize():
        raise SystemExit('Конфигурация недоступна')

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    app.set_report_period(
        start_date.strftime('%d.%m.%Y'),
        end_date.strftime('%d.%m.%Y')
    )

    app.generate_report('reports/отчёт_последние_90_дней.xlsx')
```

### Фильтр по контрагенту (ИНН)

```python
from src.core.app import AppFactory

with AppFactory.create_app('config.ini') as app:
    if app.initialize():
        app.set_contractor_filter(inn='7701234567')
        app.generate_report('reports/контрагент_7701234567.xlsx')
```

### Частичная выгрузка по номерам счетов

```python
from src.core.app import AppFactory

invoice_numbers = ['СЧЕТ-001', 'СЧЕТ-025']

with AppFactory.create_app('config.ini') as app:
    if app.initialize():
        app.set_invoice_filter(numbers=invoice_numbers)
        app.generate_report('reports/счета_001_025.xlsx')
```

<a id="повторный-запуск-и-ротация-файлов"></a>
## 🔄 Повторный запуск и ротация файлов

- Измените `defaultfilename` в `config.ini`, чтобы переименовать создаваемый файл.
- Включите таймстемпы в имени при программном запуске: `f"reports/отчёт_{datetime.now():%Y%m%d_%H%M}.xlsx"`.
- Для автоматической очистки старых файлов используйте PowerShell: `Get-ChildItem reports -File -OlderThan 30d | Remove-Item`.

<a id="автоматизация-и-планировщики"></a>
## 🤖 Автоматизация и планировщики

### Windows Task Scheduler

1. Откройте «Планировщик заданий» → «Создать задачу».
2. Укажите триггер (например, ежедневный запуск в 07:00).
3. В действиях добавьте: `Program/script: py`, `Add arguments: run_report.py`, `Start in: C:\Projects\ReportB24`.
4. Включите «Запускать только при подключении к сети», чтобы избежать сбоев Bitrix24.

### GitHub Actions (self-hosted)

```yaml
name: Nightly Report
on:
  schedule:
    - cron: '0 3 * * *'

jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -r requirements.txt
      - name: Generate report
        env:
          BITRIX_WEBHOOK_URL: ${{ secrets.BITRIX_WEBHOOK_URL }}
        run: python run_report.py
```

### Docker-контейнер

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "run_report.py"]
```

<a id="проверка-результата"></a>
## 🔍 Проверка результата

- Файл отчёта: `reports/<имя из config.ini>`.
- Логи: `logs/app.log` (искомые сообщения: `✅ Конфигурация корректна`, `✅ Подключение к Bitrix24 успешно`).
- Код завершения `0` указывает на успешное выполнение скрипта.

## ❓ Часто задаваемые вопросы

**Как изменить папку сохранения?**  
Редактируйте `defaultsavefolder` в `config.ini` и убедитесь, что папка существует.

**Можно ли использовать macOS или Linux?**  
Да. Создайте окружение командой `python3 -m venv .venv` и запускайте `python3 run_report.py`.

**Как включить подробные логи?**  
Установите `loglevel = DEBUG` в секции `[AppSettings]` файла `config.ini`.

