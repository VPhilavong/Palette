"""
OpenAI integration module for advanced AI capabilities.
Includes Assistants API, Code Interpreter, and Structured Outputs.
"""

from .assistant import PaletteAssistant
from .structured_output import StructuredOutputGenerator
from .function_calling import FunctionCallingSystem

__all__ = [
    "PaletteAssistant",
    "StructuredOutputGenerator", 
    "FunctionCallingSystem"
]