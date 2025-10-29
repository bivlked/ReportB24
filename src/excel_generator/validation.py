"""
Модуль валидации данных и метрик качества отчета.

Реализует систему проверки качества данных перед генерацией Excel отчета,
предоставляя детальную информацию о проблемах и статистику.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Одна проблема валидации данных."""

    record_id: str
    field: str
    issue_type: str  # 'missing', 'invalid', 'suspicious', 'critical'
    message: str

    def __str__(self) -> str:
        """Строковое представление проблемы."""
        emoji = {
            "missing": "⚠️",
            "invalid": "❌",
            "suspicious": "🔍",
            "critical": "🔥",
        }.get(self.issue_type, "ℹ️")
        return f"{emoji} [{self.record_id}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """Результат валидации данных."""

    total_records: int
    valid_records: int
    issues: List[ValidationIssue] = field(default_factory=list)

    def has_issues(self) -> bool:
        """Есть ли какие-либо проблемы."""
        return len(self.issues) > 0

    def has_critical_issues(self) -> bool:
        """Есть ли критические проблемы."""
        return any(i.issue_type == "critical" for i in self.issues)

    @property
    def invalid_records(self) -> int:
        """Количество невалидных записей."""
        return self.total_records - self.valid_records

    @property
    def success_rate(self) -> float:
        """Процент успешной валидации."""
        if self.total_records == 0:
            return 100.0
        return (self.valid_records / self.total_records) * 100


@dataclass
class QualityMetrics:
    """Метрики качества отчёта."""

    brief_total: int
    brief_valid: int
    brief_issues: List[ValidationIssue] = field(default_factory=list)

    detailed_total: int = 0
    detailed_valid: int = 0
    detailed_issues: List[ValidationIssue] = field(default_factory=list)

    generation_time: str = ""
    generator_version: str = "2.5.0"

    def __post_init__(self):
        """Инициализация дополнительных полей."""
        if not self.generation_time:
            self.generation_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    @property
    def total_issues(self) -> int:
        """Общее количество проблем."""
        return len(self.brief_issues) + len(self.detailed_issues)

    @property
    def brief_success_rate(self) -> float:
        """Процент успешности краткого отчета."""
        if self.brief_total == 0:
            return 100.0
        return (self.brief_valid / self.brief_total) * 100

    @property
    def detailed_success_rate(self) -> float:
        """Процент успешности полного отчета."""
        if self.detailed_total == 0:
            return 100.0
        return (self.detailed_valid / self.detailed_total) * 100

    def has_critical_issues(self) -> bool:
        """Есть ли критические проблемы."""
        all_issues = self.brief_issues + self.detailed_issues
        return any(i.issue_type == "critical" for i in all_issues)

    def to_summary(self) -> str:
        """Форматированная сводка для консоли."""
        # Символы статуса
        brief_icon = (
            "✅"
            if self.brief_success_rate >= 90
            else "⚠️" if self.brief_success_rate >= 70 else "❌"
        )
        detailed_icon = (
            "✅"
            if self.detailed_success_rate >= 90
            else "⚠️" if self.detailed_success_rate >= 70 else "❌"
        )

        return f"""
╔═══════════════════════════════════════════════════════════╗
║           📊 МЕТРИКИ КАЧЕСТВА ОТЧЁТА                      ║
╠═══════════════════════════════════════════════════════════╣
║ {brief_icon} Лист "Краткий":                                       ║
║   └─ Записей: {self.brief_valid}/{self.brief_total} валидных ({self.brief_success_rate:.1f}%)    ║
║                                                           ║
║ {detailed_icon} Лист "Полный":                                        ║
║   └─ Записей: {self.detailed_valid}/{self.detailed_total} валидных ({self.detailed_success_rate:.1f}%)  ║
║                                                           ║
║ Проблем обнаружено: {self.total_issues}                               ║
║ Дата генерации: {self.generation_time}                    ║
║ Версия: {self.generator_version}                                  ║
╚═══════════════════════════════════════════════════════════╝
"""


class DataQualityValidator:
    """Валидатор качества данных для отчетов."""

    def __init__(self):
        """Инициализация валидатора."""
        self.logger = logging.getLogger(__name__)

    def validate_brief_data(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Валидация данных краткого отчёта.

        Args:
            data: Список записей краткого отчета

        Returns:
            ValidationResult: Результат валидации с найденными проблемами
        """
        issues = []
        valid_count = 0

        for idx, record in enumerate(data):
            record_id = record.get("account_number", f"Запись_{idx + 1}")
            has_issues = False

            # Проверка обязательных полей
            if not record.get("account_number"):
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="account_number",
                        issue_type="critical",
                        message="Отсутствует номер счёта",
                    )
                )
                has_issues = True

            if not record.get("inn"):
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="inn",
                        issue_type="missing",
                        message="Отсутствует ИНН",
                    )
                )
                has_issues = True

            # Проверка подозрительных значений
            inn_value = record.get("inn", "")
            if inn_value in ["Не найдено", "Ошибка", "ERROR", ""]:
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="inn",
                        issue_type="suspicious",
                        message=f'Подозрительное значение ИНН: "{inn_value}"',
                    )
                )
                has_issues = True

            # Проверка контрагента
            if not record.get("counterparty"):
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="counterparty",
                        issue_type="missing",
                        message="Отсутствует контрагент",
                    )
                )
                has_issues = True

            # Проверка суммы
            amount = record.get("amount")
            if amount is None or amount <= 0:
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="amount",
                        issue_type="invalid",
                        message=f"Некорректная сумма: {amount}",
                    )
                )
                has_issues = True

            if not has_issues:
                valid_count += 1

        self.logger.debug(
            f"Валидация краткого отчета: {valid_count}/{len(data)} валидных записей"
        )

        return ValidationResult(
            total_records=len(data), valid_records=valid_count, issues=issues
        )

    def validate_detailed_data(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Валидация данных полного отчёта.

        Args:
            data: Список записей полного отчета

        Returns:
            ValidationResult: Результат валидации с найденными проблемами
        """
        issues = []
        valid_count = 0

        for idx, record in enumerate(data):
            record_id = record.get("account_number", f"Товар_{idx + 1}")
            has_issues = False

            # Проверка наименования товара
            if not record.get("product_name"):
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="product_name",
                        issue_type="missing",
                        message="Отсутствует наименование товара",
                    )
                )
                has_issues = True

            # Проверка количества
            quantity = record.get("quantity")
            if quantity is None or quantity <= 0:
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="quantity",
                        issue_type="invalid",
                        message=f"Некорректное количество: {quantity}",
                    )
                )
                has_issues = True

            # Проверка цены
            price = record.get("price")
            if price is None or price < 0:
                issues.append(
                    ValidationIssue(
                        record_id=record_id,
                        field="price",
                        issue_type="invalid",
                        message=f"Некорректная цена: {price}",
                    )
                )
                has_issues = True

            if not has_issues:
                valid_count += 1

        self.logger.debug(
            f"Валидация полного отчета: {valid_count}/{len(data)} валидных записей"
        )

        return ValidationResult(
            total_records=len(data), valid_records=valid_count, issues=issues
        )


@dataclass
class ComprehensiveReportResult:
    """Результат генерации отчёта с метриками качества."""

    output_path: str
    quality_metrics: QualityMetrics

    def print_summary(self):
        """Печать сводки метрик в консоль."""
        print(self.quality_metrics.to_summary())

    def log_issues(self, max_issues: int = 10):
        """
        Логирование найденных проблем.

        Args:
            max_issues: Максимальное количество проблем для вывода
        """
        all_issues = (
            self.quality_metrics.brief_issues + self.quality_metrics.detailed_issues
        )

        if all_issues:
            logger.warning(f"⚠️ Обнаружено проблем: {len(all_issues)}")
            for issue in all_issues[:max_issues]:
                logger.warning(f"  {issue}")

            if len(all_issues) > max_issues:
                remaining = len(all_issues) - max_issues
                logger.warning(f"  ... и ещё {remaining} проблем(а)")
