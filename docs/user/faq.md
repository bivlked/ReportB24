# ❓ Frequently Asked Questions (FAQ)

Ответы на частые вопросы о ReportB24.

---

## 🚀 Начало работы

### Q: Нужна ли лицензия Bitrix24 для работы?

**A**: Да, требуется активный аккаунт Bitrix24 с доступом к REST API. Подходят все тарифы, включая бесплатный, где доступны вебхуки.

### Q: Какая версия Python нужна?

**A**: Python 3.8 или выше. Рекомендуется Python 3.11+ для лучшей производительности.

```bash
# Проверка версии
python --version  # Windows
python3 --version # Linux/Mac
```

### Q: Работает ли на Mac/Linux?

**A**: Да! ReportB24 кросс-платформенный:
- ✅ Windows 10+
- ✅ macOS 10.14+
- ✅ Linux (Ubuntu 18.04+, Debian, Fedora и др.)

---

## ⚙️ Настройка и конфигурация

### Q: Где получить Webhook URL?

**A**: 
1. Войдите в Bitrix24
2. **Приложения** → **Вебхуки**
3. Создайте **входящий вебхук**
4. Выберите права: `crm`, `smart_invoice`
5. Скопируйте URL

**Формат**: `https://your-portal.bitrix24.ru/rest/12/abc123/`

### Q: Можно ли использовать без .env файла?

**A**: Да, через переменные окружения:

```bash
# Windows (PowerShell)
$env:BITRIX_WEBHOOK_URL = "your_webhook_url"

# Linux/Mac
export BITRIX_WEBHOOK_URL="your_webhook_url"
```

Приоритет: `os.environ` > `.env` > `config.ini`

### Q: Безопасно ли хранить webhook в .env?

**A**: Да, если:
- ✅ `.env` в `.gitignore` (уже настроено)
- ✅ Права доступа ограничены (только владелец)
- ✅ Регулярная ротация webhook

См. [Security Guide](../technical/security-deep-dive.md)

---

## 📊 Отчеты и данные

### Q: В чем разница между базовым и детальным отчетом?

**A**:

| Тип | Листы | Содержимое |
|-----|-------|-----------|
| **Базовый** | 1 лист "Краткий" | Обзор счетов (№, контрагент, ИНН, сумма, НДС) |
| **Детальный** | 2 листа | "Краткий" + "Полный" с детализацией всех товаров |

```bash
# Базовый
python scripts/run_report.py

# Детальный
python scripts/run_detailed_report.py
```

### Q: Какой максимальный период отчета?

**A**: Технически не ограничен, но:
- ✅ **Рекомендуется**: До 1 года (12 месяцев)
- ⚠️ **Работает, но медленно**: 1-3 года
- ❌ **Не рекомендуется**: Более 3 лет (разбейте на части)

**Производительность**:
- 100 счетов: ~2-3 минуты
- 500 счетов: ~8-12 минут
- 1000 счетов: ~15-20 минут

### Q: Можно ли выбрать конкретных контрагентов?

**A**: В текущей версии (v2.4.1) фильтрация по периоду. Фильтр по контрагентам в roadmap (v2.5.0).

**Workaround** (программно):

```python
from src.core.app import create_app

app = create_app('config.ini')
app.initialize()

# Фильтруйте после получения данных
invoices = app.bitrix_client.get_invoices_by_period('01.01.2024', '31.03.2024')
filtered = [inv for inv in invoices if inv.get('company_inn') == '1234567890']
```

### Q: Почему в отчете нет товаров?

**A**: Проверьте:

1. **Права webhook**: Должно быть `smart_invoice`
2. **API метод**: Используете `run_detailed_report.py`?
3. **Товары в Bitrix24**: Есть ли товары у счетов?

```bash
# Тест API
python -c "from src.bitrix24_client.client import Bitrix24Client; \
           from src.config.config_reader import SecureConfigReader; \
           config = SecureConfigReader('config.ini'); \
           client = Bitrix24Client(config.get_webhook_url()); \
           print(client.get_products_by_invoice('123'))"
```

---

## 🔧 Ошибки и проблемы

### Q: "ModuleNotFoundError: No module named 'openpyxl'"

**A**: Не установлены зависимости:

```bash
# Активируйте venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Установите зависимости
pip install -r requirements.txt
```

### Q: "Bitrix24 API Error: 401 Unauthorized"

**A**: Проблема с webhook:

1. Проверьте URL в `.env`
2. Убедитесь, что webhook активен
3. Пересоздайте webhook в Bitrix24
4. Обновите `.env`

```bash
# Тест webhook
curl "https://your-portal.bitrix24.ru/rest/12/abc123/crm.item.list?entityTypeId=31"
```

### Q: "FileNotFoundError: [Errno 2] No such file or directory: 'config.ini'"

**A**: Не создан config.ini:

```bash
copy config.ini.example config.ini  # Windows
cp config.ini.example config.ini    # Linux/Mac
```

### Q: Отчет создается, но файл пустой/поврежден

**A**: Возможные причины:

1. **Нет данных** за период в Bitrix24
2. **Недостаточно прав** для записи в `reports/`
3. **Антивирус** блокирует запись

**Решение**:

```bash
# Проверьте права
mkdir reports  # Создайте если нет
chmod 755 reports  # Linux/Mac

# Проверьте данные
python scripts/run_report.py  # Смотрите логи
```

---

## ⚡ Производительность

### Q: Почему отчет генерируется долго?

**A**: Факторы:

1. **Количество счетов** (основной фактор)
2. **Количество товаров** (для детального отчета)
3. **Скорость интернета** (API запросы)
4. **Batch size** в config.ini

**Оптимизация**:

```ini
[Performance]
batch_size = 50  # Увеличьте до 50-100
max_concurrent_requests = 3  # Увеличьте до 3-5
company_cache_size = 2000  # Увеличьте кэш
```

### Q: Как ускорить генерацию для больших периодов?

**A**: Стратегии:

1. **Разбейте на части**:
   ```bash
   # Q1
   # config.ini: startdate=01.01.2024, enddate=31.03.2024
   python scripts/run_report.py
   
   # Q2
   # config.ini: startdate=01.04.2024, enddate=30.06.2024
   python scripts/run_report.py
   ```

2. **Используйте batch API** (уже включен в v2.4.0+)

3. **Запускайте в нерабочее время** (меньше нагрузка на Bitrix24)

### Q: Сколько памяти потребляет?

**A**: Зависит от объема:

- 100 счетов: ~50-100 МБ
- 500 счетов: ~100-200 МБ
- 1000 счетов: ~200-400 МБ

**Минимум**: 512 МБ RAM  
**Рекомендуется**: 1+ ГБ RAM

---

## 🔒 Безопасность

### Q: Безопасно ли использовать в production?

**A**: Да, ReportB24 production-ready с:

- ✅ Secure configuration (hybrid .env + config.ini)
- ✅ URL masking в логах
- ✅ Input validation
- ✅ 530+ тестов, 77% coverage
- ✅ Security audit пройден

См. [Security Policy](../../SECURITY.md)

### Q: Что делать если webhook утек?

**A**: Немедленно:

1. **Отзовите webhook** в Bitrix24
2. **Создайте новый webhook**
3. **Обновите `.env`**
4. **Проверьте логи** на подозрительную активность
5. **Сообщите** в [security@reportb24.ru](mailto:security@reportb24.ru)

### Q: Логируются ли секреты?

**A**: Нет! ReportB24 маскирует все чувствительные данные:

```
# В логах webhook выглядит так:
INFO: Using webhook: https://portal.bitrix24.ru/rest/12/***/
```

Полный URL **никогда** не логируется.

---

## 🛠️ Разработка и кастомизация

### Q: Можно ли изменить формат Excel?

**A**: Да, через код или config.ini:

```ini
[Excel]
summary_header_color = #FFD700  # Золотой
detailed_header_color = #87CEEB  # Голубой
zebra_color_1 = #F0F0F0
freeze_panes = true
```

Для глубокой кастомизации: `src/excel_generator/formatter.py`

### Q: Как добавить свои поля в отчет?

**A**: Модифицируйте:

1. `src/data_processor/data_processor.py` - обработка данных
2. `src/excel_generator/layout.py` - структура Excel
3. `src/excel_generator/generator.py` - генерация

Пример в [Development Guide](../technical/development.md)

### Q: Можно ли использовать как библиотеку?

**A**: Да!

```python
from src.core.app import create_app

app = create_app('config.ini')
app.initialize()

# Получите данные
invoices = app.bitrix_client.get_invoices_by_period('01.01.2024', '31.03.2024')

# Обработайте
processed = app.data_processor.process_invoices(invoices)

# Создайте отчет
report_path = app.generate_report('my_report.xlsx')
```

---

## 📚 Документация и поддержка

### Q: Где полная документация?

**A**: 

- 📖 [User Documentation](../user/) - Для пользователей
- 🔧 [Technical Documentation](../technical/) - Для разработчиков
- 📊 [Examples](../examples/) - Примеры использования
- 📈 [API Reference](../technical/api-reference.md) - API документация

### Q: Как сообщить об ошибке?

**A**:

1. **Проверьте** [FAQ](faq.md) и [Troubleshooting](troubleshooting.md)
2. **Поищите** в [Issues](https://github.com/bivlked/ReportB24/issues)
3. **Создайте Issue** с:
   - Описанием проблемы
   - Шагами воспроизведения
   - Версией Python и ОС
   - Логами (без секретов!)

### Q: Есть ли community?

**A**: Да!

- 💬 [GitHub Discussions](https://github.com/bivlked/ReportB24/discussions) - Вопросы и обсуждения
- 🐛 [GitHub Issues](https://github.com/bivlked/ReportB24/issues) - Баги и feature requests
- 📧 Email: [ivan@bondarev.net](mailto:ivan@bondarev.net)

---

## 🆕 Обновления и версионирование

### Q: Как узнать текущую версию?

**A**:

```bash
# Из Git
git describe --tags

# Из кода
python -c "from src import __version__; print(__version__)"

# Из README
cat README.md | grep "Version"
```

### Q: Как обновиться до новой версии?

**A**:

```bash
# С Git
git pull origin main
pip install -r requirements.txt --upgrade

# Без Git: Скачайте и распакуйте новую версию, скопируйте .env и config.ini
```

См. [CHANGELOG.md](../../CHANGELOG.md) для истории версий

### Q: Что означают версии (X.Y.Z)?

**A**: [Semantic Versioning](https://semver.org/):

- **X** (Major): Breaking changes (несовместимые изменения)
- **Y** (Minor): Новые features (обратно совместимые)
- **Z** (Patch): Bug fixes (исправления)

Пример: `2.4.1`
- `2` - Major version
- `4` - Minor (новые features с v2.0.0)
- `1` - Patch (bug fixes с v2.4.0)

---

## 💡 Дополнительные вопросы?

**Не нашли ответ?**

1. 📖 [Troubleshooting Guide](troubleshooting.md)
2. 💬 [Create Discussion](https://github.com/bivlked/ReportB24/discussions/new)
3. 🐛 [Create Issue](https://github.com/bivlked/ReportB24/issues/new)

---

<div align="center">

[← User Guide](usage-guide.md) • [Troubleshooting →](troubleshooting.md)

**Помогли FAQ?** ⭐ [Star проект](https://github.com/bivlked/ReportB24) на GitHub!

</div>
