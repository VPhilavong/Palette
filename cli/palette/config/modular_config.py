"""
Modular configuration implementation with error handling.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..interfaces import IConfig
from ..errors import ConfigurationError
from ..errors.decorators import handle_errors, validate_result


class ModularConfig(IConfig):
    """
    Modular configuration implementation with validation and error handling.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from file or defaults.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Check various locations
        locations = [
            Path.cwd() / "palette.json",
            Path.cwd() / ".palette.json",
            Path.home() / ".palette" / "config.json",
            Path.home() / ".config" / "palette" / "config.json",
        ]
        
        for location in locations:
            if location.exists():
                return str(location)
        
        # Return first location as default
        return str(locations[0])
    
    @handle_errors(reraise=True)
    def _load_config(self):
        """Load configuration from file with error handling."""
        if not os.path.exists(self.config_path):
            # Use defaults if no config file
            self._config = self._get_defaults()
            return
        
        try:
            with open(self.config_path, "r") as f:
                self._config = json.load(f)
                
            # Merge with defaults for missing keys
            defaults = self._get_defaults()
            for key, value in defaults.items():
                if key not in self._config:
                    self._config[key] = value
                    
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {self.config_path}",
                config_key="file",
                cause=e
            )
        except IOError as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {self.config_path}",
                config_key="file",
                cause=e
            )
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "api": {
                "openai_model": "gpt-4o-mini",
                "anthropic_model": "claude-3-haiku-20240307",
                "temperature": 0.7,
                "max_tokens": 4000,
                "timeout": 120,
            },
            "generation": {
                "validate_output": True,
                "format_output": True,
                "add_imports": True,
                "use_typescript": True,
            },
            "analysis": {
                "use_ast": True,
                "cache_results": True,
                "cache_ttl": 3600,
                "max_file_size": 1024 * 1024,  # 1MB
            },
            "output": {
                "directory": "generated",
                "overwrite": False,
                "create_backup": True,
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            }
        }
    
    @validate_result(
        validator=lambda x: x is not None,
        error_message="Configuration key returned None"
    )
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If required key is missing
        """
        # Support dot notation
        keys = key.split(".")
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            else:
                raise ConfigurationError(
                    f"Required configuration key not found: {key}",
                    config_key=key
                )
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        # Support dot notation
        keys = key.split(".")
        target = self._config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # Set value
        target[keys[-1]] = value
    
    @handle_errors(reraise=True)
    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            path: Optional path to save to (uses current path if not provided)
            
        Raises:
            ConfigurationError: If save fails
        """
        save_path = path or self.config_path
        
        # Create directory if needed
        save_dir = os.path.dirname(save_path)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        
        try:
            with open(save_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            raise ConfigurationError(
                f"Failed to save configuration to: {save_path}",
                config_key="file",
                cause=e
            )
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Check API keys
        api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
        has_key = False
        
        for key in api_keys:
            if os.environ.get(key):
                has_key = True
                break
        
        if not has_key:
            raise ConfigurationError(
                "No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in environment",
                config_key="api_key"
            )
        
        # Validate model names
        valid_openai_models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        openai_model = self.get("api.openai_model")
        if openai_model and openai_model not in valid_openai_models:
            raise ConfigurationError(
                f"Invalid OpenAI model: {openai_model}",
                config_key="api.openai_model",
                context={"valid_models": valid_openai_models}
            )
        
        # Validate numeric values
        temperature = self.get("api.temperature", 0.7)
        if not 0 <= temperature <= 2:
            raise ConfigurationError(
                f"Temperature must be between 0 and 2, got: {temperature}",
                config_key="api.temperature"
            )
        
        max_tokens = self.get("api.max_tokens", 4000)
        if max_tokens < 100:
            raise ConfigurationError(
                f"Max tokens must be at least 100, got: {max_tokens}",
                config_key="api.max_tokens"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()