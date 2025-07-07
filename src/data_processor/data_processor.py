"""
Main Data Processor - оркестратор для обработки данных отчёта.
Координирует работу специализированных процессоров: INN, Date, Currency.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import logging

from .inn_processor import INNProcessor
from .date_processor import DateProcessor  
from .currency_processor import CurrencyProcessor

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
    
    def __init__(self, default_currency: str = 'RUB', bitrix_client=None):
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
    
    def process_invoice_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка записи Smart Invoice для workflow.
        
        Args:
            raw_data: Сырые данные счёта из Smart Invoices API
            
        Returns:
            Dict[str, Any]: Обработанные данные в формате для Excel
        """
        try:
            # Извлекаем данные из Smart Invoice структуры
            return {
                'account_number': raw_data.get('accountNumber', ''),
                'inn': self._extract_smart_invoice_inn(raw_data),
                'counterparty': self._extract_smart_invoice_counterparty(raw_data),
                'amount': self._format_amount(raw_data.get('opportunity', 0)),
                'vat_amount': self._format_amount(raw_data.get('taxValue', 0)),
                'vat_text': 'нет' if float(raw_data.get('taxValue', 0)) == 0 else self._format_amount(raw_data.get('taxValue', 0)),
                'invoice_date': self._format_date(raw_data.get('begindate')),
                'shipping_date': self._format_date(raw_data.get('UFCRM_SMART_INVOICE_1651168135187')),
                'payment_date': self._format_date(raw_data.get('UFCRM_626D6ABE98692')),
                'is_unpaid': not bool(raw_data.get('UFCRM_626D6ABE98692')),  # нет даты оплаты = неоплачен
                'stage_id': raw_data.get('stageId', '')
            }
        except Exception as e:
            logger.error(f"Ошибка обработки Smart Invoice: {e}")
            return None
    
    def _extract_smart_invoice_inn(self, raw_data: Dict[str, Any]) -> str:
        """
        🔧 ИСПРАВЛЕНИЕ: Извлечение ИНН для Smart Invoice через реквизиты
        
        Для получения ИНН используется номер счета (accountNumber) 
        и метод get_company_info_by_invoice() из Bitrix24Client
        """
        account_number = raw_data.get('accountNumber', '')
        if account_number and hasattr(self, '_bitrix_client'):
            try:
                company_name, inn = self._bitrix_client.get_company_info_by_invoice(account_number)
                return inn if inn not in ["Не найдено", "Ошибка", "Нет реквизитов", "Некорректный реквизит", "Ошибка реквизита"] else ""
            except Exception as e:
                logger.warning(f"Ошибка получения ИНН для счета {account_number}: {e}")
        return ""
    
    def _extract_smart_invoice_counterparty(self, raw_data: Dict[str, Any]) -> str:
        """
        🔧 ИСПРАВЛЕНИЕ: Извлечение названия контрагента для Smart Invoice через реквизиты
        
        Для получения названия контрагента используется номер счета (accountNumber) 
        и метод get_company_info_by_invoice() из Bitrix24Client
        """
        account_number = raw_data.get('accountNumber', '')
        if account_number and hasattr(self, '_bitrix_client'):
            try:
                company_name, inn = self._bitrix_client.get_company_info_by_invoice(account_number)
                return company_name if company_name not in ["Не найдено", "Ошибка", "Нет реквизитов", "Некорректный реквизит", "Ошибка реквизита"] else ""
            except Exception as e:
                logger.warning(f"Ошибка получения контрагента для счета {account_number}: {e}")
        return ""
    
    def _format_amount(self, amount) -> str:
        """Форматирование суммы"""
        try:
            return f"{float(amount):,.2f}".replace(',', ' ').replace('.', ',')
        except:
            return "0,00"
    
    def _format_date(self, date_str) -> str:
        """Форматирование даты"""
        if not date_str:
            return ""
        try:
            from datetime import datetime
            d = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
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
        """Извлечение номера счёта"""
        possible_keys = ['number', 'invoice_number', 'ACCOUNT_NUMBER']
        
        for key in possible_keys:
            if key in raw_data and raw_data[key]:
                return str(raw_data[key]).strip()
        
        return None
    
    def _process_inn(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка ИНН"""
        possible_keys = ['inn', 'INN', 'UF_CRM_INN']
        inn_value = None
        
        for key in possible_keys:
            if key in raw_data and raw_data[key]:
                inn_value = raw_data[key]
                break
        
        if inn_value:
            result = self.inn_processor.validate_inn(inn_value)
            invoice.inn = result.inn if result.is_valid else str(inn_value)
            invoice.formatted_inn = result.formatted_inn if result.is_valid else str(inn_value)
            invoice.inn_valid = result.is_valid
            
            if not result.is_valid:
                invoice.validation_errors.append(f"Невалидный ИНН: {result.error_message}")
        else:
            invoice.validation_errors.append("ИНН не найден")
    
    def _process_dates(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка дат"""
        date_keys = ['date_bill', 'DATE_BILL', 'created_time']
        date_value = None
        
        for key in date_keys:
            if key in raw_data and raw_data[key]:
                date_value = raw_data[key]
                break
        
        if date_value:
            result = self.date_processor.parse_date(date_value)
            
            if result.is_valid:
                invoice.invoice_date = result.parsed_date
                invoice.formatted_invoice_date = result.formatted_date
                invoice.dates_valid = True
            else:
                invoice.validation_errors.append(f"Невалидная дата: {result.error_message}")
    
    def _process_amounts(self, raw_data: Dict[str, Any], invoice: InvoiceData) -> None:
        """Обработка сумм"""
        amount_keys = ['opportunity', 'OPPORTUNITY', 'amount']
        amount_value = None
        
        for key in amount_keys:
            if key in raw_data and raw_data[key] is not None:
                amount_value = raw_data[key]
                break
        
        if amount_value is not None:
            result = self.currency_processor.parse_amount(amount_value)
            
            if result.is_valid:
                invoice.amount = result.amount
                invoice.formatted_amount = result.formatted_amount
                invoice.amounts_valid = True
                
                # Рассчитываем НДС 20%
                vat_result = self.currency_processor.calculate_vat(
                    result.amount, '20%', amount_includes_vat=True
                )
                
                if vat_result.is_valid:
                    invoice.vat_amount = vat_result.vat_amount
                    
            else:
                invoice.validation_errors.append(f"Невалидная сумма: {result.error_message}")
        else:
            invoice.validation_errors.append("Сумма не найдена")
    
    def _extract_counterparty(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Извлечение наименования контрагента"""
        possible_keys = ['title', 'TITLE', 'company_title']
        
        for key in possible_keys:
            if key in raw_data and raw_data[key]:
                return str(raw_data[key]).strip()
        
        return None
    
    def _validate_invoice(self, invoice: InvoiceData) -> None:
        """Финальная валидация счёта"""
        required_fields = [
            ('invoice_number', 'номер счёта'),
            ('inn', 'ИНН'),
            ('counterparty', 'контрагент'),
            ('amount', 'сумма'),
        ]
        
        for field, description in required_fields:
            if not getattr(invoice, field):
                invoice.validation_errors.append(f"Отсутствует {description}")
    
    def process_invoice_batch(self, raw_data_list: List[Dict[str, Any]]) -> List[InvoiceData]:
        """
        Пакетная обработка списка счетов.
        
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
        self, 
        detailed_data: Dict[str, Any]
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
            result.invoice_info = detailed_data.get('invoice', {})
            result.company_name = detailed_data.get('company_name', 'Не найдено')
            result.inn = detailed_data.get('inn', 'Не найдено')
            result.account_number = detailed_data.get('account_number')
            result.total_products = detailed_data.get('total_products', 0)
            
            # 2. Обработка товаров
            raw_products = detailed_data.get('products', [])
            logger.debug(f"Обработка {len(raw_products)} товаров для счета {result.account_number}")
            
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
        Форматирование данных товара из productRows
        
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
            product.product_id = str(raw_product.get('id', '')).strip()
            product_name = str(raw_product.get('productName', 'Товар без названия')).strip()
            product.product_name = product_name if product_name else 'Товар без названия'
            product.unit_measure = str(raw_product.get('measureName', 'шт')).strip()
            
            # Обработка цены
            price_result = self.currency_processor.parse_amount(
                raw_product.get('price', 0)
            )
            if price_result.is_valid:
                product.price = price_result.amount
                product.formatted_price = price_result.formatted_amount
            else:
                product.validation_errors.append(f"Невалидная цена: {raw_product.get('price')}")
                product.price = Decimal('0')
                product.formatted_price = "0,00"
            
            # Обработка количества
            quantity_result = self.currency_processor.parse_amount(
                raw_product.get('quantity', 0)
            )
            if quantity_result.is_valid:
                product.quantity = quantity_result.amount
                product.formatted_quantity = f"{float(product.quantity):,.3f}".replace(',', ' ').replace('.', ',')
            else:
                product.validation_errors.append(f"Невалидное количество: {raw_product.get('quantity')}")
                product.quantity = Decimal('0')
                product.formatted_quantity = "0,000"
            
            # Расчет общей суммы товара
            product.total_amount = product.price * product.quantity
            product.formatted_total = f"{float(product.total_amount):,.2f}".replace(',', ' ').replace('.', ',')
            
            # Расчет НДС (предполагаем 20%)
            vat_result = self.currency_processor.calculate_vat(
                product.total_amount, '20%', amount_includes_vat=True
            )
            if vat_result.is_valid:
                product.vat_amount = vat_result.vat_amount
                product.vat_rate = "20%"
                product.formatted_vat = f"{float(product.vat_amount):,.2f}".replace(',', ' ').replace('.', ',')
            else:
                product.vat_amount = Decimal('0')
                product.vat_rate = "0%"
                product.formatted_vat = "0,00"
            
            # Валидация товара
            product.is_valid = bool(
                product.product_name and 
                product.price >= 0 and 
                product.quantity >= 0
            )
            
            if not product.is_valid:
                product.validation_errors.append("Товар не прошел базовую валидацию")
            
            logger.debug(f"Товар обработан: {product.product_name} - {product.formatted_total}")
            
        except Exception as e:
            logger.error(f"Ошибка форматирования товара: {e}")
            product.validation_errors.append(f"Критическая ошибка: {e}")
            product.is_valid = False
        
        return product
    
    def group_products_by_invoice(
        self, 
        invoices_products: Dict[int, List[Dict[str, Any]]]
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
                
                logger.debug(f"Счет {invoice_id}: {len(valid_products)} товаров, сумма {invoice_data.total_amount}")
                
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
            invoice_data.total_amount = Decimal('0')
            invoice_data.total_vat = Decimal('0')
            return
        
        total_amount = Decimal('0')
        total_vat = Decimal('0')
        
        for product in invoice_data.products:
            if product.is_valid:
                total_amount += product.total_amount or Decimal('0')
                total_vat += product.vat_amount or Decimal('0')
        
        invoice_data.total_amount = total_amount
        invoice_data.total_vat = total_vat
        
        logger.debug(f"Агрегация для {invoice_data.account_number}: "
                    f"сумма {total_amount}, НДС {total_vat}")

    def format_products_for_excel(
        self, 
        grouped_data: Dict[int, DetailedInvoiceData]
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
            for product in invoice_data.products:
                if product.is_valid:
                    excel_row = {
                        'invoice_number': invoice_data.account_number,
                        'company_name': invoice_data.company_name or 'Не найдено',
                        'inn': invoice_data.inn or 'Не найдено',
                        'product_name': product.product_name,
                        'quantity': product.formatted_quantity,
                        'unit_measure': product.unit_measure,
                        'price': product.formatted_price,
                        'total_amount': product.formatted_total,
                        'vat_amount': product.formatted_vat,
                        
                        # Метаданные для группировки
                        'invoice_id': invoice_id,
                        'is_first_product': len(excel_rows) == 0 or excel_rows[-1].get('invoice_id') != invoice_id
                    }
                    excel_rows.append(excel_row)
        
        logger.info(f"Excel форматирование завершено: {len(excel_rows)} строк товаров")
        return excel_rows
