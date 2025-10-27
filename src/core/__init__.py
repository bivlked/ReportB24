"""
Основной модуль приложения для генератора отчётов Bitrix24.

Содержит главное приложение, обработчик ошибок и оркестратор workflow.
"""

from .app import (
    ReportGeneratorApp,
    AppFactory,
    AppStatus,
    main
)

from .error_handler import (
    ErrorHandler,
    ErrorReporter,
    ErrorContext,
    ErrorCategories,
    ErrorSeverity,
    get_error_handler,
    handle_error,
    get_error_summary,
    generate_error_report
)

from .workflow import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowProgress,
    WorkflowStages
)

__all__ = [
    # App
    'ReportGeneratorApp',
    'AppFactory',
    'AppStatus',
    'main',
    
    # Error Handler
    'ErrorHandler',
    'ErrorReporter',
    'ErrorContext',
    'ErrorCategories',
    'ErrorSeverity',
    'get_error_handler',
    'handle_error',
    'get_error_summary',
    'generate_error_report',
    
    # Workflow
    'WorkflowOrchestrator',
    'WorkflowResult',
    'WorkflowProgress',
    'WorkflowStages'
] 