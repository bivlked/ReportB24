"""
Тесты инфраструктуры проекта.
Проверяют что система тестирования работает корректно.
"""
import pytest
import sys
from pathlib import Path


class TestInfrastructure:
    """Тесты базовой инфраструктуры проекта"""
    
    def test_python_version(self):
        """Тест: проверка версии Python 3.12"""
        assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version_info}"
    
    def test_project_structure(self):
        """Тест: проверка базовой структуры проекта"""
        project_root = Path(__file__).parent.parent
        
        # Проверяем наличие ключевых файлов
        assert (project_root / ".gitignore").exists(), ".gitignore должен существовать"
        assert (project_root / "pytest.ini").exists(), "pytest.ini должен существовать"
        assert (project_root / "tasks.md").exists(), "tasks.md должен существовать"
        assert (project_root / "config.ini").exists(), "config.ini должен существовать"
    
    def test_virtual_environment_active(self):
        """Тест: проверка активации виртуального окружения"""
        import sys
        venv_path = Path(sys.executable).parent.parent
        assert venv_path.name == ".venv", f"Виртуальное окружение не активно: {sys.executable}"
    
    def test_pytest_coverage_setup(self):
        """Тест: проверка настройки coverage"""
        try:
            import coverage
            assert True, "Coverage module доступен"
        except ImportError:
            pytest.fail("Coverage module не установлен")
    
    def test_basic_calculations(self):
        """Тест: базовые расчёты для проверки pytest"""
        assert 2 + 2 == 4
        assert 10 * 0.1 == 1.0
        assert round(3.14159, 2) == 3.14


@pytest.mark.unit
def test_dummy_function():
    """Простой dummy тест для проверки системы"""
    def dummy_add(a, b):
        return a + b
    
    assert dummy_add(2, 3) == 5
    assert dummy_add(-1, 1) == 0
    assert dummy_add(0, 0) == 0


if __name__ == "__main__":
    pytest.main([__file__]) 