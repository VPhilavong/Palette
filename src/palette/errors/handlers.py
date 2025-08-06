"""
Error handlers for different output targets.
"""

import sys
import json
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from .base import (
    PaletteError, AnalysisError, GenerationError, 
    ValidationError, ConfigurationError
)


class ErrorHandler(ABC):
    """Abstract base class for error handlers."""
    
    @abstractmethod
    def handle(self, error: Exception) -> None:
        """Handle an error."""
        pass
    
    @abstractmethod
    def handle_warning(self, message: str) -> None:
        """Handle a warning message."""
        pass


class ConsoleErrorHandler(ErrorHandler):
    """
    Error handler that outputs to console with formatting.
    Provides user-friendly error messages.
    """
    
    def __init__(self, verbose: bool = False, color: bool = True):
        self.verbose = verbose
        self.color = color and sys.stdout.isatty()
        
        # ANSI color codes
        self.colors = {
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "green": "\033[92m",
            "reset": "\033[0m"
        } if self.color else {k: "" for k in ["red", "yellow", "blue", "green", "reset"]}
    
    def handle(self, error: Exception) -> None:
        """Handle an error with console output."""
        if isinstance(error, PaletteError):
            self._handle_palette_error(error)
        else:
            self._handle_generic_error(error)
    
    def handle_warning(self, message: str) -> None:
        """Handle a warning message."""
        print(f"{self.colors['yellow']}⚠️  Warning: {message}{self.colors['reset']}")
    
    def _handle_palette_error(self, error: PaletteError) -> None:
        """Handle a Palette-specific error."""
        # Error header
        print(f"\n{self.colors['red']}❌ {error.__class__.__name__}: {error.message}{self.colors['reset']}")
        
        # Context information
        if error.context:
            print(f"\n{self.colors['blue']}Context:{self.colors['reset']}")
            for key, value in error.context.items():
                print(f"  • {key}: {value}")
        
        # Cause information
        if error.cause:
            print(f"\n{self.colors['blue']}Caused by:{self.colors['reset']}")
            print(f"  {error.cause}")
        
        # Suggestions based on error type
        suggestions = self._get_suggestions(error)
        if suggestions:
            print(f"\n{self.colors['green']}💡 Suggestions:{self.colors['reset']}")
            for suggestion in suggestions:
                print(f"  • {suggestion}")
        
        # Verbose mode shows traceback
        if self.verbose:
            print(f"\n{self.colors['blue']}Stack trace:{self.colors['reset']}")
            traceback.print_exc()
    
    def _handle_generic_error(self, error: Exception) -> None:
        """Handle a generic Python error."""
        print(f"\n{self.colors['red']}❌ Error: {str(error)}{self.colors['reset']}")
        
        if self.verbose:
            print(f"\n{self.colors['blue']}Stack trace:{self.colors['reset']}")
            traceback.print_exc()
    
    def _get_suggestions(self, error: PaletteError) -> list:
        """Get helpful suggestions based on error type."""
        suggestions = []
        
        if isinstance(error, ConfigurationError):
            if "api_key" in str(error).lower():
                suggestions.append("Set your API key in environment variables or .env file")
                suggestions.append("Example: export OPENAI_API_KEY='your-key-here'")
            elif "not found" in str(error).lower():
                suggestions.append("Check that the configuration file exists")
                suggestions.append("Run 'palette init' to create a default configuration")
        
        elif isinstance(error, AnalysisError):
            if "permission" in str(error).lower():
                suggestions.append("Check file permissions in the project directory")
            elif "not found" in str(error).lower():
                suggestions.append("Ensure you're running the command from the project root")
                suggestions.append("Check that the file or directory exists")
        
        elif isinstance(error, GenerationError):
            if "rate limit" in str(error).lower():
                suggestions.append("Wait a moment before retrying")
                suggestions.append("Consider using a different API key or model")
            elif "timeout" in str(error).lower():
                suggestions.append("Try with a simpler prompt")
                suggestions.append("Check your internet connection")
        
        elif isinstance(error, ValidationError):
            suggestions.append("Review the generated code for issues")
            suggestions.append("Ensure your project has proper TypeScript/ESLint configuration")
        
        return suggestions


class FileErrorHandler(ErrorHandler):
    """
    Error handler that logs to a file.
    Useful for debugging and production environments.
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path.home() / ".palette" / "error.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger("palette.errors")
        self.logger.setLevel(logging.ERROR)
        
        # File handler
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def handle(self, error: Exception) -> None:
        """Log error to file."""
        if isinstance(error, PaletteError):
            # Log structured error
            error_data = {
                "timestamp": datetime.now().isoformat(),
                "error": error.to_dict(),
                "traceback": traceback.format_exc()
            }
            self.logger.error(json.dumps(error_data, indent=2))
        else:
            # Log generic error
            self.logger.error(f"{error.__class__.__name__}: {str(error)}", exc_info=True)
    
    def handle_warning(self, message: str) -> None:
        """Log warning to file."""
        self.logger.warning(message)


class CompositeErrorHandler(ErrorHandler):
    """
    Composite error handler that delegates to multiple handlers.
    Useful for handling errors in multiple ways simultaneously.
    """
    
    def __init__(self, handlers: list[ErrorHandler]):
        self.handlers = handlers
    
    def handle(self, error: Exception) -> None:
        """Handle error with all registered handlers."""
        for handler in self.handlers:
            try:
                handler.handle(error)
            except Exception as e:
                # Don't let handler errors propagate
                print(f"Error in handler {handler.__class__.__name__}: {e}")
    
    def handle_warning(self, message: str) -> None:
        """Handle warning with all registered handlers."""
        for handler in self.handlers:
            try:
                handler.handle_warning(message)
            except Exception:
                pass