"""
Main Data Processor - оркестратор для обработки данных отчёта.
Координирует работу специализированных процессоров: INN, Date, Currency.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import logging

from .inn_processor import INNProcessor
from .date_processor import DateProcessor
from .currency_processor import CurrencyProcessor
from .validation_helpers import safe_decimal, safe_float  # БАГ-2 FIX

logger = logging.getLogger(__name__)


@dataclass
class InvoiceData:
    """Структура данных счёта для отчёта"""

    # Основные поля
    invoice_number: Optional[str] = None
    inn: Optional[str] = None
    counterparty: Optional[str] = None
    amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    invoice_date: Optional[datetime] = None

    # Результаты валидации
    inn_valid: bool = False
    dates_valid: bool = False
    amounts_valid: bool = False

    # Форматированные значения
    formatted_inn: Optional[str] = None
    formatted_amount: Optional[str] = None
    formatted_invoice_date: Optional[str] = None

    # Ошибки валидации
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class ProcessedInvoice:
    """
    Обработанные данные счета с валидацией (v2.4.0).
    
    Используется в новой гибридной архитектуре для batch обработки.
    Все суммы хранятся как Decimal для корректного форматирования в Excel.
    
    🔥 БАГ-8 FIX: invoice_date и shipping_date теперь Optional[datetime].
    Отсутствующие даты НЕ подменяются на datetime.now(), чтобы не искажать данные.
    """
    
    # Основные поля
    account_number: str
    inn: str
    counterparty: str
    amount: Decimal  # Числовой тип для Excel!
    vat_amount: Decimal | str  # Decimal или "нет"
    invoice_date: Optional[datetime]  # БАГ-8 FIX: Optional для честных данных
    shipping_date: Optional[datetime]  # БАГ-8 FIX: Optional для честных данных
    payment_date: Optional[datetime]
    
    # Метаданные
    is_unpaid: bool
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    def _determine_vat_rate(self) -> str:
        """
        🔥 БАГ-4 FIX: Определение ставки НДС для корректной статистики.
        
        Returns:
            "no_vat" - нет НДС (vat_amount == "нет" или vat_amount == 0)
            "with_vat" - есть НДС (vat_amount > 0)
        
        Note:
            Товары с НДС=0% должны классифицироваться как "no_vat",
            а не "with_vat" (критично для корректной статистики).
        """
        if isinstance(self.vat_amount, str):
            return "no_vat"  # vat_amount == "нет"
        
        if isinstance(self.vat_amount, Decimal):
            return "no_vat" if self.vat_amount == Decimal('0') else "with_vat"
        
        # Fallback для неожиданных типов
        return "no_vat"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Конвертация в dict для передачи в Excel генератор.
        Даты форматируются в строки, суммы остаются Decimal.
        """
        # 🔥 БАГ-4 FIX: Используем _determine_vat_rate() для корректной классификации
        vat_status = self._determine_vat_rate()
        is_no_vat = (vat_status == "no_vat")
        
        return {
            'account_number': self.account_number,
            'inn': self.inn,
            'counterparty': self.counterparty,
            'amount': self.amount,  # Decimal!
            'vat_amount': self.vat_amount,  # Decimal или "нет"
            'invoice_date': self.invoice_date.strftime('%d.%m.%Y') if self.invoice_date else '',
            'shipping_date': self.shipping_date.strftime('%d.%m.%Y') if self.shipping_date else '',
            'payment_date': self.payment_date.strftime('%d.%m.%Y') if self.payment_date else '',
            'is_unpaid': self.is_unpaid,
            'is_valid': self.is_valid,
            'is_no_vat': is_no_vat,
            # Для обратной совместимости с ExcelReportGenerator
            'amount_numeric': float(self.amount),
            'vat_amount_numeric': float(self.vat_amount) if not is_no_vat else 0,
        }


@dataclass
class ProductData:
    """Структура данных товара для детального отчета"""

    # Основные поля товара
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Optional[Decimal] = None
    unit_measure: Optional[str] = None

    # Вычисляемые поля
    total_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[str] = None

    # Форматированные значения
    formatted_price: Optional[str] = None
    formatted_quantity: Optional[str] = None
    formatted_total: Optional[str] = None
    formatted_vat: Optional[str] = None

    # Валидация
    is_valid: bool = False
    validation_errors: List[str] = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class DetailedInvoiceData:
    """Структура детальных данных счета с товарами"""

    # Базовая информация счета
    invoice_info: Dict[str, Any] = None
    products: List[ProductData] = None
    company_name: Optional[str] = None
    inn: Optional[str] = None

    # Агрегированные данные
    total_products: int = 0
    total_amount: Optional[Decimal] = None
    total_vat: Optional[Decimal] = None

    # Метаданные
    account_number: Optional[str] = None
    processing_timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.products is None:
            self.products = []
        if self.processing_timestamp is None:
            self.processing_timestamp = datetime.now()


class DataProcessor:
    """
    Главный процессор данных - оркестратор.

    Координирует работу специализированных процессоров:
    - INNProcessor: Валидация и обработка ИНН
    - DateProcessor: Обработка дат в российском формате
    - CurrencyProcessor: Обработка валют и расчёт НДС
    """

    def __init__(self, default_currency: str = "RUB", bitrix_client=None):
        """Инициализация главного процессора"""
        self.inn_processor = INNProcessor()
        self.date_processor = DateProcessor()
        self.currency_processor = CurrencyProcessor(default_currency)

        self.default_currency = default_currency

        # 🔧 ИСПРАВЛЕНИЕ: Поддержка Bitrix24Client для получения реквизитов
        self._bitrix_client = bitrix_client

    def set_bitrix_client(self, bitrix_client):
        """
        Устанавливает Bitrix24Client для получения реквизитов

        Args:
            bitrix_client: Экземпляр Bitrix24Client
        """
        self._bitrix_client = bitrix_client

    def process_invoice_batch(self, raw_invoices: List[Dict[str, Any]]) -> List[ProcessedInvoice]:
        """
        Обрабатывает batch счетов с валидацией (v2.4.0).
        
        Новая гибридная архитектура: DataProcessor обрабатывает данные,
        возвращает ProcessedInvoice с Decimal типами для Excel.
        
        Args:
            raw_invoices: Сырые данные счетов из Bitrix24
            
        Returns:
            List[ProcessedInvoice]: Обработанные счета с числовыми типами
        """
        processed = []
        for invoice in raw_invoices:
            try:
                processed_invoice = self._process_single_invoice(invoice)
                processed.append(processed_invoice)
            except Exception as e:
                logger.error(f"Ошибка обработки счета {invoice.get('id', 'N/A')}: {e}")
                # БАГ-8 FIX: Создаем invalid invoice с None для дат (не подменяем)
                invalid = ProcessedInvoice(
                    account_number=invoice.get('accountNumber', 'N/A'),
                    inn='ERROR',
                    counterparty='ERROR',
                    amount=Decimal('0'),
                    vat_amount='ERROR',
                    invoice_date=None,  # БАГ-8 FIX: None вместо datetime.now()
                    shipping_date=None,  # БАГ-8 FIX: None вместо datetime.now()
                    payment_date=None,
                    is_unpaid=True,
                    is_valid=False,
                    validation_errors=[str(e)]
                )
                processed.append(invalid)
        
        return processed
    
    def _process_single_invoice(self, invoice: Dict[str, Any]) -> ProcessedInvoice:
        """
        Обработка одного счета (v2.4.0).
        
        Args:
            invoice: Сырые данные счета
            
        Returns:
            ProcessedInvoice: Обработанный счет с валидацией
        """
        # Извлечение и валидация данных
        account_number = invoice.get('accountNumber', '')
        
        # 🔥 БАГ-2 FIX: Безопасная обработка сумм с валидацией
        amount = safe_decimal(invoice.get('opportunity'), '0')
        tax_val = safe_float(invoice.get('taxValue'), 0.0)
        vat_amount = safe_decimal(tax_val, '0') if tax_val > 0 else "нет"

        # Обработка дат (используем DateProcessor)
        invoice_date = self._parse_date(invoice.get('begindate'))
        shipping_date = self._parse_date(invoice.get('UFCRM_SMART_INVOICE_1651168135187'))
        payment_date = self._parse_date(invoice.get('UFCRM_626D6ABE98692'))
        
        # Обработка реквизитов
        counterparty = self._extract_smart_invoice_counterparty(invoice)
        if not counterparty:
            counterparty = invoice.get('title', 'Не найдено')
        
        inn = self._extract_smart_invoice_inn(invoice)
        if not inn:
            inn = 'Не найдено'
        
        # Валидация данных
        validation_errors = []
        is_valid = True
        
        # Проверка критичных полей
        if not account_number or account_number.strip() == '':
            validation_errors.append('Отсутствует номер счета')
            is_valid = False
        
        if inn in ['Не найдено', 'не указан', 'ERROR'] or not inn:
            validation_errors.append('ИНН не найден или некорректен')
            is_valid = False
        else:
            # Проверка валидности ИНН через InnProcessor
            inn_result = self.inn_processor.validate_inn(inn)
            if not inn_result.is_valid:
                validation_errors.append(f'ИНН невалиден: {inn_result.error_message}')
                is_valid = False
        
        if amount <= Decimal('0'):
            validation_errors.append('Сумма счета должна быть больше нуля')
            is_valid = False
        
        # БАГ-8 FIX: Валидация дат - отсутствующие даты помечаются как ошибка
        if invoice_date is None:
            validation_errors.append('Отсутствует дата счета')
            is_valid = False
        
        if shipping_date is None:
            validation_errors.append('Отсутствует дата отгрузки')
            is_valid = False
        
        # Дополнительная валидация
        is_unpaid = payment_date is None
        
        return ProcessedInvoice(
            account_number=account_number,
            inn=inn,
            counterparty=counterparty,
            amount=amount,
            vat_amount=vat_amount,
            invoice_date=invoice_date,  # БАГ-8 FIX: НЕ подменяем None на datetime.now()
            shipping_date=shipping_date,  # БАГ-8 FIX: НЕ подменяем None на datetime.now()
            payment_date=payment_date,
            is_unpaid=is_unpaid,
            is_valid=is_valid,
            validation_errors=validation_errors
        )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Парсинг даты с использованием DateProcessor.
        
        Args:
            date_str: Строка с датой
            
        Returns:
            Optional[datetime]: Распарсенная дата или None
        """
        if not date_str:
            return None
        result = self.date_processor.parse_date(date_str)
        return result.parsed_date if result.is_valid else None

    def process_invoice_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка записи Smart Invoice для workflow.

        🔧 ИСПРАВЛЕНИЕ (v2.1.2): Dual Data Structure для корректного Excel форматирования.
        Возвращает ДВА набора полей:
        - amount / vat_amount: числа (float) для Excel форматирования
        - amount_formatted / vat_amount_formatted: строки для отображения

        Args:
            raw_data: Сырые данные счёта из Smart Invoices API

        Returns:
            Dict[str, Any]: Обработанные данные в формате для Excel
        """
        try:
            # 🔥 БАГ-6 FIX: Безопасная обработка сумм с валидацией
            tax_val = safe_float(raw_data.get("taxValue"), 0.0)
            amount_val = safe_float(raw_data.get("opportunity"), 0.0)

            # Форматированные строки для отображения
            tax_text = "нет" if tax_val == 0 else self._format_amount(tax_val)
            amount_text = self._format_amount(amount_val)

            return {
                "account_number": raw_data.get("accountNumber", ""),
                "inn": self._extract_smart_invoice_inn(raw_data),
                "counterparty": self._extract_smart_invoice_counterparty(raw_data),
                # 🔥 НОВАЯ СТРУКТУРА: Dual Data - числа для Excel
                "amount": amount_val,  # float для Excel NUMBER_FORMAT
                "vat_amount": tax_val if tax_val > 0 else "нет",  # float или "нет"
                # 🔥 НОВАЯ СТРУКТУРА: Форматированные строки (опционально)
                "amount_formatted": amount_text,
                "vat_amount_formatted": tax_text,
                # Даты
                "invoice_date": self._format_date(raw_data.get("begindate")),
                "shipping_date": self._format_date(
                    raw_data.get("UFCRM_SMART_INVOICE_1651168135187")
                ),
                "payment_date": self._format_date(raw_data.get("UFCRM_626D6ABE98692")),
                # Флаги
                "is_unpaid": not bool(
                    raw_data.get("UFCRM_626D6ABE98692")
                ),  # нет даты оплаты = неоплачен
                "is_no_vat": tax_text == "нет",  # Флаг для серой заливки
                "stage_id": raw_data.get("stageId", ""),
                # 🔧 ОБРАТНАЯ СОВМЕСТИМОСТЬ: Старые поля для расчета итогов
                "amount_numeric": amount_val,
                "vat_amount_numeric": tax_val,
            }
        except Exception as e:
            logger.error(f"Ошибка обработки Smart Invoice: {e}")
            return None

    def _extract_smart_invoice_inn(self, raw_data: Dict[str, Any]) -> str:
        """
        🔧 ИСПРАВЛЕНИЕ: Извлечение ИНН для Smart Invoice через реквизиты
        
        🔥 БАГ-8 FIX: Сначала проверяем обогащенные данные из WorkflowOrchestrator!
        
        Приоритет:
        1. Обогащенные данные: raw_data['company_inn'] (из Workflow)
        2. API запрос: get_company_info_by_invoice() (только если данных нет)
        3. Fallback: ufCrmInn (резервный вариант)
        
        Performance: Снижение API запросов с 3x до 1x (66% улучшение)
        """
        # 🔥 БАГ-8 FIX: PRIORITY 1 - Используем обогащенные данные
        # БАГ-4 FIX: Проверка на None перед .strip()
        enriched_inn = (raw_data.get("company_inn") or "").strip()
        if enriched_inn and enriched_inn not in [
            "Не найдено",
            "Ошибка",
            "Нет реквизитов",
            "Некорректный реквизит",
            "Ошибка реквизита",
        ]:
            logger.debug(f"✅ БАГ-8: Использованы обогащенные данные ИНН (пропущен API запрос)")
            return enriched_inn
        
        # PRIORITY 2 - API запрос (только если данных нет)
        account_number = raw_data.get("accountNumber", "")
        if account_number and self._bitrix_client is not None:
            try:
                company_name, inn = self._bitrix_client.get_company_info_by_invoice(
                    account_number
                )
                if inn and inn not in [
                    "Не найдено",
                    "Ошибка",
                    "Нет реквизитов",
                    "Некорректный реквизит",
                    "Ошибка реквизита",
                ]:
                    logger.info(f"⚠️ БАГ-8: API запрос ИНН (данные не были обогащены)")
                    return inn
            except Exception as e:
                logger.warning(f"Ошибка получения ИНН для счета {account_number}: {e}")
        
        # PRIORITY 3 - Fallback: прямое извлечение из ufCrmInn
        fallback_inn = raw_data.get("ufCrmInn", "")
        return fallback_inn if fallback_inn else ""

    def _extract_smart_invoice_counterparty(self, raw_data: Dict[str, Any]) -> str:
        """
        🔧 ИСПРАВЛЕНИЕ: Извлечение названия контрагента для Smart Invoice через реквизиты
        
        🔥 БАГ-8 FIX: Сначала проверяем обогащенные данные из WorkflowOrchestrator!
        
        Приоритет:
        1. Обогащенные данные: raw_data['company_name'] (из Workflow)
        2. API запрос: get_company_info_by_invoice() (только если данных нет)
        
        Performance: Снижение API запросов с 3x до 1x (66% улучшение)
        """
        # 🔥 БАГ-8 FIX: PRIORITY 1 - Используем обогащенные данные
        # БАГ-4 FIX: Проверка на None перед .strip()
        enriched_name = (raw_data.get("company_name") or "").strip()
        if enriched_name and enriched_name not in [
            "Не найдено",
            "Ошибка",
            "Нет реквизитов",
            "Некорректный реквизит",
            "Ошибка реквизита",
        ]:
            logger.debug(f"✅ БАГ-8: Использованы обогащенные данные контрагента (пропущен API запрос)")
            return enriched_name
        
        # PRIORITY 2 - API запрос (только если данных нет)
        account_number = raw_data.get("accountNumber", "")
        if account_number and self._bitrix_client is not None:
            try:
                company_name, inn = self._bitrix_client.get_company_info_by_invoice(
                    account_number
                )
                if company_name and company_name not in [
                    "Не найдено",
                    "Ошибка",
                    "Нет реквизитов",
                    "Некорректный реквизит",
                    "Ошибка реквизита",
                ]:
                    logger.info(f"⚠️ БАГ-8: API запрос контрагента (данные не были обогащены)")
                    return company_name
            except Exception as e:
                logger.warning(
                    f"Ошибка получения контрагента для счета {account_number}: {e}"
                )
        return ""

    def _format_amount(self, amount) -> str:
        """Форматирование суммы"""
        try:
            return f"{float(amount):,.2f}".replace(",", " ").replace(".", ",")
        except:
            return "0,00"

    def _format_date(self, date_str) -> str:
        """Форматирование даты"""
        if not date_str:
            return ""
        try:
            from datetime import datetime

            d = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
            return d.strftime("%d.%m.%Y")
        except:
            return ""

    def process_invoice_data(self, raw_data: Dict[str, Any]) -> InvoiceData:
        """
        Обработка данных одного счёта.

        Args:
            raw_data: Сырые данные счёта из API

        Returns:
            InvoiceData: Обработанные и валидированные данные
        """
        invoice = InvoiceData()

        try:
            # Обработка номера счёта
            invoice.invoice_number = self._extract_invoice_number(raw_data)

            # Обработка ИНН
            self._process_inn(raw_data, invoice)

            # Обработка дат
            self._process_dates(raw_data, invoice)

            # Обработка сумм
            self._process_amounts(raw_data, invoice)

            # Обработка контрагента
            invoice.counterparty = self._extract_counterparty(raw_data)

            # Финальная валидация
            self._validate_invoice(invoice)

        except Exception as e:
            logger.error(f"Ошибка обработки счёта: {e}")
            invoice.validation_errors.append(f"Критическая ошибка: {e}")

        return invoice

    def _extract_invoice_number(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Извлечение номера счёта (v2.4.0 - optimized)"""
        possible_keys = ["number", "invoice_number", "ACCOUNT_NUMBER"]
        return next((str(raw_data[key]).strip() for key in possible_keys if key in raw_data and raw_data[key]), None)

    def _process_inn(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка ИНН (v2.4.0 - optimized)"""
        possible_keys = ["inn", "INN", "UF_CRM_INN"]
        inn_value = next((raw_data[key] for key in possible_keys if key in raw_data and raw_data[key]), None)

        if inn_value:
            result = self.inn_processor.validate_inn(inn_value)
            invoice.inn = result.inn if result.is_valid else str(inn_value)
            invoice.formatted_inn = (
                result.formatted_inn if result.is_valid else str(inn_value)
            )
            invoice.inn_valid = result.is_valid

            if not result.is_valid:
                invoice.validation_errors.append(
                    f"Невалидный ИНН: {result.error_message}"
                )
        else:
            invoice.validation_errors.append("ИНН не найден")

    def _process_dates(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка дат (v2.4.0 - optimized)"""
        date_keys = ["date_bill", "DATE_BILL", "created_time"]
        date_value = next((raw_data[key] for key in date_keys if key in raw_data and raw_data[key]), None)

        if date_value:
            result = self.date_processor.parse_date(date_value)

            if result.is_valid:
                invoice.invoice_date = result.parsed_date
                invoice.formatted_invoice_date = result.formatted_date
                invoice.dates_valid = True
            else:
                invoice.validation_errors.append(
                    f"Невалидная дата: {result.error_message}"
                )

    def _process_amounts(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка сумм (v2.4.0 - optimized)"""
        amount_keys = ["opportunity", "OPPORTUNITY", "amount"]
        amount_value = next((raw_data[key] for key in amount_keys if key in raw_data and raw_data[key] is not None), None)

        if amount_value is not None:
            result = self.currency_processor.parse_amount(amount_value)

            if result.is_valid:
                invoice.amount = result.amount
                invoice.formatted_amount = result.formatted_amount
                invoice.amounts_valid = True

                # Рассчитываем НДС 20%
                vat_result = self.currency_processor.calculate_vat(
                    result.amount, "20%", amount_includes_vat=True
                )

                if vat_result.is_valid:
                    invoice.vat_amount = vat_result.vat_amount

            else:
                invoice.validation_errors.append(
                    f"Невалидная сумма: {result.error_message}"
                )
        else:
            invoice.validation_errors.append("Сумма не найдена")

    def _extract_counterparty(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Извлечение наименования контрагента (v2.4.0 - optimized)"""
        possible_keys = ["title", "TITLE", "company_title"]
        return next((str(raw_data[key]).strip() for key in possible_keys if key in raw_data and raw_data[key]), None)

    def _validate_invoice(self, invoice: InvoiceData) -> None:
        """Финальная валидация счёта"""
        required_fields = [
            ("invoice_number", "номер счёта"),
            ("inn", "ИНН"),
            ("counterparty", "контрагент"),
            ("amount", "сумма"),
        ]

        for field, description in required_fields:
            if not getattr(invoice, field):
                invoice.validation_errors.append(f"Отсутствует {description}")

    def process_invoice_batch_legacy(
        self, raw_data_list: List[Dict[str, Any]]
    ) -> List[InvoiceData]:
        """
        Пакетная обработка списка счетов (LEGACY).
        
        DEPRECATED: Используйте process_invoice_batch() для новой архитектуры v2.4.0.

        Args:
            raw_data_list: Список сырых данных счетов

        Returns:
            List[InvoiceData]: Список обработанных счетов
        """
        processed_invoices = []

        logger.info(f"Начинаю обработку {len(raw_data_list)} счетов")

        for i, raw_data in enumerate(raw_data_list):
            try:
                invoice = self.process_invoice_data(raw_data)
                processed_invoices.append(invoice)

            except Exception as e:
                logger.error(f"Критическая ошибка обработки счёта #{i}: {e}")
                error_invoice = InvoiceData()
                error_invoice.validation_errors.append(f"Критическая ошибка: {e}")
                processed_invoices.append(error_invoice)

        logger.info(f"Обработка завершена: {len(processed_invoices)} счетов")

        return processed_invoices

    # ============================================================================
    # НОВЫЕ МЕТОДЫ ДЛЯ ДЕТАЛЬНОГО ОТЧЕТА - ФАЗА 3: ОБРАБОТКА ДАННЫХ
    # ============================================================================

    def process_detailed_invoice_data(
        self, detailed_data: Dict[str, Any]
    ) -> DetailedInvoiceData:
        """
        Обработка детальных данных счета включая товары

        Интегрируется с новыми API методами из Фазы 2:
        - get_detailed_invoice_data() результаты
        - Обработка товаров из productRows
        - Агрегация данных для детального отчета

        Args:
            detailed_data: Результат get_detailed_invoice_data() из Bitrix24Client

        Returns:
            DetailedInvoiceData: Обработанные детальные данные
        """
        try:
            result = DetailedInvoiceData()

            # 1. Базовая информация счета
            result.invoice_info = detailed_data.get("invoice", {})
            result.company_name = detailed_data.get("company_name", "Не найдено")
            result.inn = detailed_data.get("inn", "Не найдено")
            result.account_number = detailed_data.get("account_number")
            result.total_products = detailed_data.get("total_products", 0)

            # 2. Обработка товаров
            raw_products = detailed_data.get("products", [])
            logger.debug(
                f"Обработка {len(raw_products)} товаров для счета {result.account_number}"
            )

            for raw_product in raw_products:
                product = self.format_product_data(raw_product)
                if product and product.is_valid:
                    result.products.append(product)

            # 3. Агрегация данных
            self._calculate_invoice_totals(result)

            logger.info(f"Детальные данные обработаны: {len(result.products)} товаров")
            return result

        except Exception as e:
            logger.error(f"Ошибка обработки детальных данных: {e}")
            return DetailedInvoiceData()

    def format_product_data(self, raw_product: Dict[str, Any]) -> ProductData:
        """
        Форматирование данных товара из productRows (v2.4.0 - refactored).

        Обрабатывает структуру товара из API crm.item.productrow.list:
        - Валидация цены и количества
        - Расчет общей суммы и НДС
        - Форматирование для Excel отчета

        Args:
            raw_product: Сырые данные товара из productRows

        Returns:
            ProductData: Обработанные данные товара
        """
        product = ProductData()

        try:
            # Извлечение базовых данных
            self._extract_product_basics(raw_product, product)
            
            # Обработка цены и количества
            self._process_product_price(raw_product, product)
            self._process_product_quantity(raw_product, product)
            
            # Расчет общей суммы товара
            product.total_amount = product.price * product.quantity
            product.formatted_total = f"{float(product.total_amount):,.2f}".replace(",", " ").replace(".", ",")
            
            # Расчет НДС
            self._calculate_product_vat(raw_product, product)
            
            # Валидация товара
            self._validate_product(product)
            
            logger.debug(f"Товар обработан: {product.product_name} - {product.formatted_total}")

        except Exception as e:
            logger.error(f"Ошибка форматирования товара: {e}")
            product.validation_errors.append(f"Критическая ошибка: {e}")
            product.is_valid = False

        return product
    
    def _extract_product_basics(self, raw_product: Dict[str, Any], product: ProductData) -> None:
        """Извлечение базовых данных товара."""
        product.product_id = str(raw_product.get("id", "")).strip()
        product_name = str(raw_product.get("productName", "Товар без названия")).strip()
        product.product_name = product_name if product_name else "Товар без названия"
        product.unit_measure = str(raw_product.get("measureName", "шт")).strip()
    
    def _process_product_price(self, raw_product: Dict[str, Any], product: ProductData) -> None:
        """Обработка и валидация цены товара."""
        price_result = self.currency_processor.parse_amount(raw_product.get("price", 0))
        if price_result.is_valid:
            product.price = price_result.amount
            product.formatted_price = price_result.formatted_amount
        else:
            product.validation_errors.append(f"Невалидная цена: {raw_product.get('price')}")
            product.price = Decimal("0")
            product.formatted_price = "0,00"
    
    def _process_product_quantity(self, raw_product: Dict[str, Any], product: ProductData) -> None:
        """Обработка и валидация количества товара."""
        quantity_result = self.currency_processor.parse_amount(raw_product.get("quantity", 0))
        if quantity_result.is_valid:
            product.quantity = quantity_result.amount
            product.formatted_quantity = f"{float(product.quantity):,.3f}".replace(",", " ").replace(".", ",")
        else:
            product.validation_errors.append(f"Невалидное количество: {raw_product.get('quantity')}")
            product.quantity = Decimal("0")
            product.formatted_quantity = "0,000"
    
    def _calculate_product_vat(self, raw_product: Dict[str, Any], product: ProductData) -> None:
        """
        Расчет НДС на основе данных API.
        
        Поддерживает:
        - Специальную российскую логику НДС 20% (Report BIG.py совместимость)
        - Универсальную логику для других ставок НДС
        - Товары без НДС
        """
        tax_rate = raw_product.get("taxRate", 0)
        tax_included = raw_product.get("taxIncluded", "N") == "Y"

        if tax_rate == 20:
            # Специальная российская логика НДС 20% (по образцу Report BIG.py)
            # ВАЖНО: Report BIG.py ВСЕГДА использует формулу /1.2 * 0.2 независимо от tax_included
            price = safe_float(product.price, 0.0)  # БАГ-7 FIX: валидированные данные
            quantity = safe_float(product.quantity, 0.0)  # БАГ-7 FIX
            total_amount = price * quantity

            # Формула Report BIG.py: ВСЕГДА (price * qty) / 1.2 * 0.2 (игнорируем tax_included)
            # ОПТИМИЗАЦИЯ: /1.2 * 0.2 = 1/6, используем более эффективную формулу
            vat_amount = total_amount / 6

            product.vat_amount = safe_decimal(round(vat_amount, 2), '0')  # БАГ-6 FIX
            product.vat_rate = "20%"
            product.formatted_vat = f"{vat_amount:,.2f}".replace(",", " ").replace(".", ",")
        elif tax_rate and tax_rate > 0:
            # Универсальная логика для других ставок НДС (сохраняем совместимость)
            vat_result = self.currency_processor.calculate_vat(
                product.total_amount,
                f"{tax_rate}%",
                amount_includes_vat=tax_included,
            )
            if vat_result.is_valid:
                product.vat_amount = vat_result.vat_amount
                product.vat_rate = f"{tax_rate}%"
                product.formatted_vat = f"{float(product.vat_amount):,.2f}".replace(",", " ").replace(".", ",")
            else:
                product.vat_amount = Decimal("0")
                product.vat_rate = "0%"
                product.formatted_vat = "нет"
        else:
            # Товар без НДС (текст "нет" как в Report BIG.py)
            product.vat_amount = Decimal("0")
            product.vat_rate = "0%"
            product.formatted_vat = "нет"
    
    def _validate_product(self, product: ProductData) -> None:
        """Валидация обработанных данных товара."""
        product.is_valid = bool(
            product.product_name and product.price >= 0 and product.quantity >= 0
        )
        
        if not product.is_valid:
            product.validation_errors.append("Товар не прошел базовую валидацию")

    def group_products_by_invoice(
        self, invoices_products: Dict[int, List[Dict[str, Any]]]
    ) -> Dict[int, DetailedInvoiceData]:
        """
        Группировка товаров по счетам для batch обработки

        Обрабатывает результат get_products_by_invoices_batch():
        - Группирует товары по invoice_id
        - Создает DetailedInvoiceData для каждого счета
        - Агрегирует данные для зебра-эффекта в Excel

        Args:
            invoices_products: Результат get_products_by_invoices_batch()
                               {invoice_id: [products_list]}

        Returns:
            Dict[invoice_id, DetailedInvoiceData]: Сгруппированные данные
        """
        grouped_data = {}

        logger.info(f"Группировка товаров для {len(invoices_products)} счетов")

        for invoice_id, raw_products in invoices_products.items():
            try:
                # Создаем структуру детальных данных
                invoice_data = DetailedInvoiceData()
                invoice_data.account_number = f"Счет #{invoice_id}"
                invoice_data.total_products = len(raw_products)

                # Обрабатываем товары
                valid_products = []
                for raw_product in raw_products:
                    product = self.format_product_data(raw_product)
                    if product and product.is_valid:
                        valid_products.append(product)

                invoice_data.products = valid_products

                # Агрегируем данные
                self._calculate_invoice_totals(invoice_data)

                grouped_data[invoice_id] = invoice_data

                logger.debug(
                    f"Счет {invoice_id}: {len(valid_products)} товаров, сумма {invoice_data.total_amount}"
                )

            except Exception as e:
                logger.error(f"Ошибка группировки товаров для счета {invoice_id}: {e}")
                # Создаем пустую структуру для счета с ошибкой
                error_data = DetailedInvoiceData()
                error_data.account_number = f"Счет #{invoice_id} (ошибка)"
                grouped_data[invoice_id] = error_data

        logger.info(f"Группировка завершена: {len(grouped_data)} счетов обработано")
        return grouped_data

    def _calculate_invoice_totals(self, invoice_data: DetailedInvoiceData) -> None:
        """
        Расчет агрегированных данных по счету

        Args:
            invoice_data: Структура данных счета для обновления
        """
        if not invoice_data.products:
            invoice_data.total_amount = Decimal("0")
            invoice_data.total_vat = Decimal("0")
            return

        total_amount = Decimal("0")
        total_vat = Decimal("0")

        for product in invoice_data.products:
            if product.is_valid:
                total_amount += product.total_amount or Decimal("0")
                total_vat += product.vat_amount or Decimal("0")

        invoice_data.total_amount = total_amount
        invoice_data.total_vat = total_vat

        logger.debug(
            f"Агрегация для {invoice_data.account_number}: "
            f"сумма {total_amount}, НДС {total_vat}"
        )

    def format_products_for_excel(
        self, grouped_data: Dict[int, DetailedInvoiceData]
    ) -> List[Dict[str, Any]]:
        """
        Форматирование товаров для Excel с зебра-эффектом по счетам

        Создает список строк для детального Excel отчета:
        - Группировка по счетам для зебра-эффекта
        - Форматированные суммы и количества
        - Правильный порядок колонок для отчета

        Args:
            grouped_data: Сгруппированные данные по счетам

        Returns:
            List[Dict]: Строки для Excel отчета
        """
        excel_rows = []

        logger.info(f"Форматирование для Excel: {len(grouped_data)} счетов")

        # Сортируем счета по номеру для консистентности
        sorted_invoices = sorted(grouped_data.items(), key=lambda x: x[0])

        for invoice_id, invoice_data in sorted_invoices:
            # Добавляем товары этого счета
            is_first_product_in_invoice = True
            for product in invoice_data.products:
                if product.is_valid:
                    excel_row = {
                        # Мета-поля заполняются только для первой строки каждого счета
                        "invoice_number": (
                            invoice_data.account_number
                            if is_first_product_in_invoice
                            else ""
                        ),
                        "company_name": (
                            (invoice_data.company_name or "Не найдено")
                            if is_first_product_in_invoice
                            else ""
                        ),
                        "inn": (
                            (invoice_data.inn or "Не найдено")
                            if is_first_product_in_invoice
                            else ""
                        ),
                        "product_name": product.product_name,
                        "quantity": product.formatted_quantity,
                        "unit_measure": product.unit_measure,
                        "price": product.formatted_price,
                        "total_amount": product.formatted_total,
                        "vat_amount": product.formatted_vat,
                        # Метаданные для группировки
                        "invoice_id": invoice_id,
                        "is_first_product": is_first_product_in_invoice,
                    }
                    excel_rows.append(excel_row)
                    is_first_product_in_invoice = False  # Следующие товары не первые

        logger.info(f"Excel форматирование завершено: {len(excel_rows)} строк товаров")
        return excel_rows

    def format_detailed_products_for_excel(
        self, products: List[Dict[str, Any]], invoice_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Форматирование товаров для детального Excel отчета.

        Использует существующую логику расчета НДС и форматирования
        для обеспечения консистентности с кратким отчетом.

        Args:
            products: Список товаров из API crm.item.productrow.list
            invoice_info: Информация о счете (номер, контрагент, ИНН)

        Returns:
            List[Dict]: Строки для Excel отчета с правильными типами данных
        """
        excel_rows = []

        logger.info(
            f"Форматирование детальных товаров для Excel: {len(products)} товаров"
        )

        for product in products:
            # Используем существующий метод format_product_data
            product_data = self.format_product_data(product)

            if product_data.is_valid:
                # Формируем строку для Excel с правильными типами данных
                excel_row = {
                    "invoice_number": invoice_info.get("account_number", ""),
                    "company_name": invoice_info.get("company_name", "Не найдено"),
                    "inn": invoice_info.get("inn", "Не найдено"),
                    "product_name": product_data.product_name,
                    "quantity": float(product_data.quantity),  # 🔥 БАГ-9 FIX: Сохраняем дробные количества
                    "unit_measure": product_data.unit_measure,
                    "price": float(product_data.price),  # Число, не строка
                    "total_amount": float(
                        product_data.total_amount
                    ),  # Число, не строка
                    "vat_amount": (
                        product_data.vat_amount
                        if product_data.vat_amount > 0
                        else "нет"
                    ),  # Число или текст
                    "invoice_id": invoice_info.get("invoice_id"),
                }
                excel_rows.append(excel_row)
            else:
                logger.warning(
                    f"Товар не прошел валидацию: {product.get('productName', 'Неизвестный')}"
                )

        logger.info(
            f"Детальное форматирование завершено: {len(excel_rows)} строк товаров"
        )
        return excel_rows
