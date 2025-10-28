"""
Модуль цветного вывода в консоль для улучшенного UI.

Предоставляет утилиты для красивого и информативного вывода
в процессе генерации отчетов.
"""

import sys
import time
import threading
from typing import Optional


class Spinner:
    """Простой спиннер для индикации прогресса."""

    def __init__(self, message: str = "Загрузка", color: str = None):
        """
        Инициализация спиннера.

        Args:
            message: Сообщение для отображения
            color: Цвет спиннера (необязательно)
        """
        self.message = message
        self.color = color or Colors.CYAN
        self.spinning = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0

    def _spin(self):
        """Внутренний метод для вращения спиннера."""
        while self.spinning:
            frame = self.frames[self.current_frame % len(self.frames)]
            sys.stdout.write(f"\r{self.color}{frame}{Colors.RESET} {self.message}...")
            sys.stdout.flush()
            self.current_frame += 1
            time.sleep(0.1)

    def start(self):
        """Запустить спиннер."""
        self.spinning = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self, final_message: str = None, success: bool = True):
        """
        Остановить спиннер.

        Args:
            final_message: Финальное сообщение (необязательно)
            success: Успешное ли завершение
        """
        self.spinning = False
        if self.thread:
            self.thread.join()

        # Очищаем строку
        sys.stdout.write("\r" + " " * (len(self.message) + 20) + "\r")
        sys.stdout.flush()

        # Выводим финальное сообщение если задано
        if final_message:
            if success:
                print(f"{Colors.BRIGHT_GREEN}✅{Colors.RESET} {final_message}")
            else:
                print(f"{Colors.BRIGHT_RED}❌{Colors.RESET} {final_message}")


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
        box_width = 60
        print(f"\n{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═' * box_width}╗")
        print(f"║ {title:^{box_width-2}} ║")
        print(f"╠{'═' * box_width}╣{Colors.RESET}")

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

            # Создаем строку БЕЗ цветов нужной длины (ровно box_width символов)
            # Формат: " ✅ Текст...                           Значение "
            icon_part = f" {icon} "  # 3 символа (пробел + иконка + пробел)
            key_part = f"{key}"  # Переменная длина
            value_part = f"{value_str}"  # Переменная длина

            # Вычисляем сколько нужно пробелов между текстом и значением
            # Всего должно быть ровно box_width (60) символов
            used_space = len(icon_part) + len(key_part) + len(value_part)
            padding = " " * max(1, box_width - used_space)  # Минимум 1 пробел

            # Собираем строку: иконка + текст + padding + цветное_значение
            # Цветные коды НЕ считаются в длину, поэтому выравнивание будет правильным
            print(
                f"{Colors.BRIGHT_CYAN}║{Colors.RESET}{icon_part}{key_part}{padding}{color}{value_part}{Colors.RESET}{Colors.BRIGHT_CYAN}║{Colors.RESET}"
            )

        print(f"{Colors.BRIGHT_CYAN}╚{'═' * box_width}╝{Colors.RESET}\n")

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
