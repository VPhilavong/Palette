"""
Comprehensive error handling for Palette.
"""

from .base import (
    PaletteError,
    AnalysisError,
    GenerationError,
    ValidationError,
    CacheError,
    ConfigurationError,
    IntegrationError
)
from .handlers import ErrorHandler, ConsoleErrorHandler, FileErrorHandler
from .decorators import handle_errors, retry_on_error

__all__ = [
    # Base errors
    "PaletteError",
    "AnalysisError",
    "GenerationError", 
    "ValidationError",
    "CacheError",
    "ConfigurationError",
    "IntegrationError",
    
    # Handlers
    "ErrorHandler",
    "ConsoleErrorHandler",
    "FileErrorHandler",
    
    # Decorators
    "handle_errors",
    "retry_on_error",
]