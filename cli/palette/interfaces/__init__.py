"""
Abstract interfaces for Palette components.
Provides contracts for dependency injection and loose coupling.
"""

from .analyzer import IAnalyzer, AnalysisResult, ComponentInfo, DesignTokens, ProjectStructure
from .generator import IGenerator, IPromptBuilder, GenerationResult
from .validator import IValidator, ValidationResult
from .mcp import IMCPClient, MCPResponse
from .cache import ICache
from .config import IConfigManager, PaletteConfig

__all__ = [
    # Analyzer
    "IAnalyzer",
    "AnalysisResult",
    "ComponentInfo",
    "DesignTokens", 
    "ProjectStructure",
    
    # Generator
    "IGenerator",
    "IPromptBuilder",
    "GenerationResult",
    
    # Validator
    "IValidator",
    "ValidationResult",
    
    # MCP
    "IMCPClient",
    "MCPResponse",
    
    # Cache
    "ICache",
    
    # Config
    "IConfigManager",
    "PaletteConfig",
]