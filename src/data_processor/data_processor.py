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


class DataProcessor:
    """
    Главный процессор данных - оркестратор.
    
    Координирует работу специализированных процессоров:
    - INNProcessor: Валидация и обработка ИНН
    - DateProcessor: Обработка дат в российском формате
    - CurrencyProcessor: Обработка валют и расчёт НДС
    """
    
    def __init__(self, default_currency: str = 'RUB'):
        """Инициализация главного процессора"""
        self.inn_processor = INNProcessor()
        self.date_processor = DateProcessor()
        self.currency_processor = CurrencyProcessor(default_currency)
        
        self.default_currency = default_currency
    
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
        """Извлечение ИНН для Smart Invoice (будет дополнено через реквизиты)"""
        # Пока возвращаем пустую строку, ИНН будет получен через реквизиты
        return ""
    
    def _extract_smart_invoice_counterparty(self, raw_data: Dict[str, Any]) -> str:
        """Извлечение названия контрагента для Smart Invoice"""
        # Пока возвращаем пустую строку, название будет получено через реквизиты
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
