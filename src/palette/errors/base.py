"""
Base error classes for Palette.
"""

from typing import Optional, Dict, Any


class PaletteError(Exception):
    """
    Base exception for all Palette errors.
    Provides context and structured error information.
    """
    
    def __init__(
        self, 
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }
    
    def add_context(self, **kwargs) -> 'PaletteError':
        """Add additional context to the error."""
        self.context.update(kwargs)
        return self


class AnalysisError(PaletteError):
    """
    Error during project analysis phase.
    Includes issues with parsing, file access, or pattern detection.
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if file_path:
            self.context["file_path"] = file_path


class GenerationError(PaletteError):
    """
    Error during component generation phase.
    Includes API failures, prompt issues, or generation logic errors.
    """
    
    def __init__(self, message: str, prompt: Optional[str] = None, model: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if prompt:
            self.context["prompt"] = prompt[:200] + "..." if len(prompt) > 200 else prompt
        if model:
            self.context["model"] = model


class ValidationError(PaletteError):
    """
    Error during validation phase.
    Includes type checking, import validation, or quality issues.
    """
    
    def __init__(self, message: str, validation_type: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if validation_type:
            self.context["validation_type"] = validation_type


class CacheError(PaletteError):
    """
    Error related to caching operations.
    Includes serialization issues, storage problems, or corruption.
    """
    
    def __init__(self, message: str, cache_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if cache_key:
            self.context["cache_key"] = cache_key


class ConfigurationError(PaletteError):
    """
    Error in configuration or setup.
    Includes missing API keys, invalid settings, or environment issues.
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if config_key:
            self.context["config_key"] = config_key


class IntegrationError(PaletteError):
    """
    Error with external integrations.
    Includes MCP server issues, API failures, or network problems.
    """
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if service:
            self.context["service"] = service