"""
Модуль цветного вывода в консоль для улучшенного UI.

Предоставляет утилиты для красивого и информативного вывода
в процессе генерации отчетов.
"""

import sys
from typing import Optional


class Colors:
    """ANSI коды цветов для консоли."""

    # Основные цвета
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Цвета текста
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Яркие цвета
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    # Фоновые цвета
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


class ConsoleUI:
    """Утилиты для красивого вывода в консоль."""

    @staticmethod
    def print_header(text: str, color: str = Colors.BRIGHT_CYAN):
        """Печать заголовка раздела."""
        line = "═" * 60
        print(f"\n{color}{Colors.BOLD}{line}")
        print(f"  {text}")
        print(f"{line}{Colors.RESET}\n")

    @staticmethod
    def print_step(step_num: int, text: str, status: str = "⏳"):
        """Печать шага процесса."""
        print(
            f"{Colors.BRIGHT_BLUE}{Colors.BOLD}[{step_num}]{Colors.RESET} {status} {text}"
        )

    @staticmethod
    def print_success(text: str):
        """Печать сообщения об успехе."""
        print(f"{Colors.BRIGHT_GREEN}✅ {text}{Colors.RESET}")

    @staticmethod
    def print_warning(text: str):
        """Печать предупреждения."""
        print(f"{Colors.BRIGHT_YELLOW}⚠️  {text}{Colors.RESET}")

    @staticmethod
    def print_error(text: str):
        """Печать ошибки."""
        print(f"{Colors.BRIGHT_RED}❌ {text}{Colors.RESET}")

    @staticmethod
    def print_info(text: str, indent: int = 0):
        """Печать информационного сообщения."""
        spaces = "  " * indent
        print(f"{spaces}{Colors.CYAN}ℹ️  {text}{Colors.RESET}")

    @staticmethod
    def print_progress(
        current: int,
        total: int,
        prefix: str = "",
        suffix: str = "",
        bar_length: int = 40,
    ):
        """
        Печать прогресс-бара.

        Args:
            current: Текущее значение
            total: Максимальное значение
            prefix: Префикс перед прогресс-баром
            suffix: Суффикс после прогресс-бара
            bar_length: Длина прогресс-бара в символах
        """
        if total == 0:
            return

        percent = int((current / total) * 100)
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # Цвет в зависимости от прогресса
        if percent < 50:
            color = Colors.RED
        elif percent < 80:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN

        sys.stdout.write(f"\r{prefix} {color}|{bar}|{Colors.RESET} {percent}% {suffix}")
        sys.stdout.flush()

        if current == total:
            print()  # Новая строка в конце

    @staticmethod
    def print_stats_box(
        title: str,
        stats: dict,
        success_threshold: float = 90.0,
        warning_threshold: float = 70.0,
    ):
        """
        Печать статистики в рамке.

        Args:
            title: Заголовок статистики
            stats: Словарь со статистикой
            success_threshold: Порог успеха (%)
            warning_threshold: Порог предупреждения (%)
        """
        print(f"\n{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═' * 58}╗")
        print(f"║  {title:54}  ║")
        print(f"╠{'═' * 58}╣{Colors.RESET}")

        for key, value in stats.items():
            # Определяем цвет на основе значения
            color = Colors.RESET
            icon = "•"

            if isinstance(value, (int, float)):
                if value >= success_threshold:
                    color = Colors.BRIGHT_GREEN
                    icon = "✅"
                elif value >= warning_threshold:
                    color = Colors.BRIGHT_YELLOW
                    icon = "⚠️"
                else:
                    color = Colors.BRIGHT_RED
                    icon = "❌"

            # Форматирование значения
            if isinstance(value, float):
                value_str = f"{value:.1f}%"
            else:
                value_str = str(value)

            print(
                f"{Colors.CYAN}║{Colors.RESET}  {icon} {key:35} {color}{value_str:>15}{Colors.RESET} {Colors.CYAN}║{Colors.RESET}"
            )

        print(f"{Colors.BRIGHT_CYAN}╚{'═' * 58}╝{Colors.RESET}\n")

    @staticmethod
    def print_section_separator():
        """Печать разделителя между секциями."""
        print(f"{Colors.DIM}{'─' * 60}{Colors.RESET}")

    @staticmethod
    def print_completion_banner(output_path: str):
        """Печать баннера завершения."""
        print(f"\n{Colors.BRIGHT_GREEN}{Colors.BOLD}")
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 58 + "║")
        print("║" + "  🎉 ОТЧЁТ УСПЕШНО СГЕНЕРИРОВАН!".center(58) + "║")
        print("║" + " " * 58 + "║")
        print("╚" + "═" * 58 + "╝")
        print(Colors.RESET)
        print(
            f"{Colors.CYAN}📄 Файл сохранён: {Colors.WHITE}{output_path}{Colors.RESET}\n"
        )


def format_number(num: int) -> str:
    """Форматирование числа с разделителями тысяч."""
    return f"{num:,}".replace(",", " ")


def format_duration(seconds: float) -> str:
    """
    Форматирование длительности в читаемый вид.

    Args:
        seconds: Длительность в секундах

    Returns:
        str: Отформатированная строка
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}мс"
    elif seconds < 60:
        return f"{seconds:.1f}с"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}м {secs:.0f}с"
