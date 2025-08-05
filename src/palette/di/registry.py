"""
Service registry for automatic service discovery and registration.
"""

import importlib
import inspect
from typing import Type, List, Optional
from pathlib import Path

from .container import Container, ServiceLifetime
from ..interfaces import (
    IAnalyzer, IGenerator, IValidator, IMCPClient,
    ICache, IConfigManager, IPromptBuilder
)


class ServiceRegistry:
    """
    Automatic service discovery and registration.
    Scans modules for injectable services and registers them.
    """
    
    # Known interface mappings
    INTERFACE_MAPPINGS = {
        IAnalyzer: "analyzer",
        IGenerator: "generator", 
        IValidator: "validator",
        IMCPClient: "mcp_client",
        ICache: "cache",
        IConfigManager: "config_manager",
        IPromptBuilder: "prompt_builder",
    }
    
    def __init__(self, container: Container):
        self.container = container
    
    def auto_register(self, scan_path: Optional[Path] = None) -> None:
        """
        Automatically scan and register services.
        
        Args:
            scan_path: Optional path to scan for services
        """
        if scan_path is None:
            # Default to scanning the palette package
            import palette
            scan_path = Path(palette.__file__).parent
        
        # Scan for implementations
        self._scan_implementations(scan_path)
    
    def register_defaults(self) -> None:
        """Register default service implementations."""
        # Import default implementations
        try:
            # Analyzer
            from ..analysis.modular_analyzer import ModularAnalyzer
            self.container.register_singleton(IAnalyzer, ModularAnalyzer)
        except ImportError:
            pass
        
        try:
            # Generator  
            from ..generation.modular_generator import ModularGenerator
            self.container.register_transient(IGenerator, ModularGenerator)
        except ImportError:
            pass
        
        try:
            # Validator
            from ..quality.modular_validator import ModularValidator
            self.container.register_transient(IValidator, ModularValidator)
        except ImportError:
            pass
        
        try:
            # Cache
            from ..cache.memory_cache import MemoryCache
            self.container.register_singleton(ICache, MemoryCache)
        except ImportError:
            pass
        
        try:
            # Config Manager
            from ..config.config_manager import ConfigManager
            self.container.register_singleton(IConfigManager, ConfigManager)
        except ImportError:
            pass
    
    def _scan_implementations(self, scan_path: Path) -> None:
        """Scan directory for service implementations."""
        # This would scan for classes with @Injectable decorator
        # or that implement known interfaces
        # For now, we'll use register_defaults()
        pass
    
    def register_from_config(self, config: dict) -> None:
        """
        Register services from configuration.
        
        Args:
            config: Configuration dictionary with service mappings
        """
        services = config.get("services", {})
        
        for interface_name, impl_config in services.items():
            # Get interface type
            interface_type = self._get_interface_type(interface_name)
            if not interface_type:
                continue
            
            # Load implementation
            impl_class = self._load_class(impl_config["class"])
            if not impl_class:
                continue
            
            # Register with specified lifetime
            lifetime = ServiceLifetime(impl_config.get("lifetime", "transient"))
            self.container.register(interface_type, impl_class, lifetime)
    
    def _get_interface_type(self, name: str) -> Optional[Type]:
        """Get interface type from name."""
        for interface, key in self.INTERFACE_MAPPINGS.items():
            if key == name:
                return interface
        return None
    
    def _load_class(self, class_path: str) -> Optional[Type]:
        """Load a class from module path string."""
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError, ValueError):
            return None