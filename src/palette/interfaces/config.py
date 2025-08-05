"""
Configuration interface and data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class APIConfig:
    """Configuration for API providers."""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-sonnet"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 120


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1 hour default
    max_size_mb: int = 100
    cache_dir: Optional[str] = None


@dataclass
class AnalysisConfig:
    """Configuration for project analysis."""
    use_treesitter: bool = True
    max_file_size_kb: int = 500
    ignore_patterns: List[str] = field(default_factory=lambda: [
        "node_modules", ".git", "dist", "build", ".next", "coverage"
    ])
    component_file_extensions: List[str] = field(default_factory=lambda: [
        ".tsx", ".ts", ".jsx", ".js"
    ])


@dataclass
class GenerationConfig:
    """Configuration for component generation."""
    enhanced_mode: bool = True
    quality_assurance: bool = True
    use_intelligence: bool = True
    max_retries: int = 3
    format_code: bool = True
    add_tests: bool = False


@dataclass
class MCPConfig:
    """Configuration for MCP servers."""
    enabled: bool = True
    auto_discover: bool = True
    servers: List[Dict[str, Any]] = field(default_factory=list)
    connection_timeout: int = 30


@dataclass
class PaletteConfig:
    """Complete configuration for Palette."""
    api: APIConfig = field(default_factory=APIConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    
    # Global settings
    debug: bool = False
    log_level: str = "INFO"
    project_path: Optional[str] = None
    
    def merge(self, other: 'PaletteConfig') -> 'PaletteConfig':
        """Merge another config into this one, with other taking precedence."""
        # Implementation would merge all fields
        # For brevity, showing the pattern:
        new_config = PaletteConfig()
        
        # Merge API config
        new_config.api.openai_api_key = other.api.openai_api_key or self.api.openai_api_key
        new_config.api.anthropic_api_key = other.api.anthropic_api_key or self.api.anthropic_api_key
        new_config.api.openai_model = other.api.openai_model or self.api.openai_model
        # ... etc for all fields
        
        return new_config


class IConfigManager(ABC):
    """
    Abstract interface for configuration management.
    Handles loading, merging, and validating configuration.
    """
    
    @abstractmethod
    def load_config(self, config_path: Optional[Path] = None) -> PaletteConfig:
        """
        Load configuration from various sources.
        
        Args:
            config_path: Optional explicit config file path
            
        Returns:
            Loaded and merged configuration
        """
        pass
    
    @abstractmethod
    def save_config(self, config: PaletteConfig, path: Path) -> bool:
        """
        Save configuration to a file.
        
        Args:
            config: Configuration to save
            path: Path to save to
            
        Returns:
            True if successfully saved
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: PaletteConfig) -> List[str]:
        """
        Validate configuration for errors.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        pass
    
    @abstractmethod
    def load_from_env(self) -> PaletteConfig:
        """
        Load configuration from environment variables.
        
        Returns:
            Configuration loaded from environment
        """
        pass
    
    @abstractmethod
    def load_from_file(self, path: Path) -> PaletteConfig:
        """
        Load configuration from a file.
        
        Args:
            path: Path to config file
            
        Returns:
            Configuration loaded from file
        """
        pass
    
    @abstractmethod
    def get_default_config_paths(self) -> List[Path]:
        """
        Get list of default configuration file paths to check.
        
        Returns:
            List of paths in order of precedence
        """
        pass