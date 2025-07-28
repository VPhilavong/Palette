"""
MCP Server Registry for managing available MCP servers and their configurations.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from .client import MCPServerConfig


class MCPServerRegistry:
    """Registry for managing MCP server configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.servers: Dict[str, MCPServerConfig] = {}
        self.load_config()
    
    def _get_default_config_path(self) -> Path:
        """Get the default config path."""
        # Try project-specific config first
        if os.path.exists("palette.json"):
            return Path("palette.json")
        
        # Fall back to user config
        config_dir = Path.home() / ".palette"
        config_dir.mkdir(exist_ok=True)
        return config_dir / "mcp-servers.json"
    
    def load_config(self) -> None:
        """Load server configurations from file."""
        if not self.config_path.exists():
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            
            # Handle both palette.json format and dedicated mcp config
            mcp_config = data.get("mcp", {}) if "mcp" in data else data
            servers_config = mcp_config.get("servers", {})
            
            for name, config in servers_config.items():
                self.servers[name] = MCPServerConfig(
                    name=name,
                    **config
                )
                
        except Exception as e:
            print(f"Warning: Failed to load MCP config: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create a default configuration with example servers."""
        default_servers = {
            "design-system": {
                "type": "stdio",
                "command": "mcp-design-system",
                "args": ["--project", "./"],
                "enabled": True,
                "env": {}
            },
            "shadcn-ui": {
                "type": "stdio", 
                "command": "mcp-shadcn-ui",
                "args": [],
                "enabled": False,
                "env": {}
            },
            "figma": {
                "type": "http",
                "url": "http://localhost:3000/mcp",
                "enabled": False,
                "env": {
                    "FIGMA_TOKEN": "${FIGMA_TOKEN}"
                }
            },
            "icons": {
                "type": "stdio",
                "command": "mcp-icons",
                "args": ["--providers", "lucide,heroicons"],
                "enabled": False,
                "env": {}
            }
        }
        
        config_data = {
            "mcp": {
                "servers": default_servers,
                "default_servers": ["design-system"],
                "timeout": 30
            }
        }
        
        # Create directories if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Load the default config
        self.load_config()
        
        print(f"✅ Created default MCP config at {self.config_path}")
    
    def save_config(self) -> None:
        """Save current server configurations to file."""
        try:
            # Read existing config to preserve other settings
            existing_data = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Update MCP section
            if "mcp" not in existing_data:
                existing_data["mcp"] = {}
            
            existing_data["mcp"]["servers"] = {
                name: asdict(config) for name, config in self.servers.items()
            }
            
            # Write back to file
            with open(self.config_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving MCP config: {e}")
    
    def add_server(self, config: MCPServerConfig) -> None:
        """Add a new server configuration."""
        self.servers[config.name] = config
        self.save_config()
    
    def remove_server(self, name: str) -> bool:
        """Remove a server configuration."""
        if name in self.servers:
            del self.servers[name]
            self.save_config()
            return True
        return False
    
    def update_server(self, name: str, **kwargs) -> bool:
        """Update a server configuration."""
        if name not in self.servers:
            return False
        
        config = self.servers[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config()
        return True
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> List[MCPServerConfig]:
        """List all server configurations."""
        return list(self.servers.values())
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get only enabled server configurations."""
        return [config for config in self.servers.values() if config.enabled]
    
    def enable_server(self, name: str) -> bool:
        """Enable a server."""
        return self.update_server(name, enabled=True)
    
    def disable_server(self, name: str) -> bool:
        """Disable a server."""
        return self.update_server(name, enabled=False)
    
    def get_server_by_type(self, server_type: str) -> List[MCPServerConfig]:
        """Get servers by type (stdio or http)."""
        return [config for config in self.servers.values() if config.type == server_type]
    
    def validate_server_config(self, config: MCPServerConfig) -> List[str]:
        """Validate a server configuration and return any issues."""
        issues = []
        
        if not config.name:
            issues.append("Server name is required")
        
        if config.type not in ["stdio", "http"]:
            issues.append("Server type must be 'stdio' or 'http'")
        
        if config.type == "stdio":
            if not config.command:
                issues.append("Command is required for stdio servers")
        elif config.type == "http":
            if not config.url:
                issues.append("URL is required for http servers")
        
        return issues
    
    def get_predefined_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get a list of predefined server configurations."""
        return {
            "design-system": {
                "name": "design-system",
                "type": "stdio",
                "command": "mcp-design-system",
                "args": ["--project", "./"],
                "description": "Extract design tokens and component patterns from your project",
                "tools": ["get_design_tokens", "validate_compliance", "find_similar_components"],
                "resources": ["/tokens/*", "/components/*", "/patterns/*"]
            },
            "shadcn-ui": {
                "name": "shadcn-ui",
                "type": "stdio",
                "command": "mcp-shadcn-ui",
                "args": [],
                "description": "Access shadcn/ui component registry and examples",
                "tools": ["search_components", "get_component_code", "list_variants"],
                "resources": ["/components/*", "/examples/*"]
            },
            "tailwind": {
                "name": "tailwind",
                "type": "stdio",
                "command": "mcp-tailwind",
                "args": [],
                "description": "Advanced Tailwind CSS utilities and patterns",
                "tools": ["generate_classes", "validate_config", "suggest_utilities"],
                "resources": ["/utilities/*", "/patterns/*"]
            },
            "figma": {
                "name": "figma",
                "type": "http",
                "url": "http://localhost:3000/mcp",
                "description": "Import designs and styles from Figma",
                "tools": ["import_design", "extract_styles", "get_component_specs"],
                "resources": ["/files/*", "/styles/*"],
                "env": {"FIGMA_TOKEN": "${FIGMA_TOKEN}"}
            },
            "icons": {
                "name": "icons",
                "type": "stdio",
                "command": "mcp-icons",
                "args": ["--providers", "lucide,heroicons,phosphor"],
                "description": "Search and retrieve icons from multiple libraries",
                "tools": ["search_icons", "get_icon_svg", "list_categories"],
                "resources": ["/icons/*"]
            },
            "storybook": {
                "name": "storybook",
                "type": "stdio",
                "command": "mcp-storybook",
                "args": [],
                "description": "Generate Storybook stories for components",
                "tools": ["generate_story", "analyze_component", "create_controls"],
                "resources": ["/stories/*", "/docs/*"]
            },
            "testing": {
                "name": "testing",
                "type": "stdio",
                "command": "mcp-testing",
                "args": [],
                "description": "Generate comprehensive test suites",
                "tools": ["generate_tests", "create_mocks", "suggest_test_cases"],
                "resources": ["/tests/*", "/mocks/*"]
            },
            "accessibility": {
                "name": "accessibility",
                "type": "stdio",
                "command": "mcp-a11y",
                "args": [],
                "description": "Accessibility analysis and compliance checking",
                "tools": ["check_accessibility", "suggest_improvements", "validate_aria"],
                "resources": ["/guidelines/*", "/examples/*"]
            }
        }
    
    def install_predefined_server(self, server_name: str) -> bool:
        """Install a predefined server configuration."""
        predefined = self.get_predefined_servers()
        
        if server_name not in predefined:
            return False
        
        server_def = predefined[server_name]
        config = MCPServerConfig(**{k: v for k, v in server_def.items() 
                                   if k in MCPServerConfig.__dataclass_fields__})
        
        self.add_server(config)
        return True
    
    def export_config(self, export_path: str) -> bool:
        """Export server configurations to a file."""
        try:
            export_data = {
                "mcp": {
                    "servers": {name: asdict(config) for name, config in self.servers.items()},
                    "exported_at": json.dumps({"timestamp": "now"}),
                    "version": "1.0"
                }
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """Import server configurations from a file."""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            mcp_config = data.get("mcp", {})
            servers_config = mcp_config.get("servers", {})
            
            if not merge:
                self.servers.clear()
            
            for name, config in servers_config.items():
                self.servers[name] = MCPServerConfig(name=name, **config)
            
            self.save_config()
            return True
            
        except Exception as e:
            print(f"Import failed: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        enabled_count = len(self.get_enabled_servers())
        disabled_count = len(self.servers) - enabled_count
        
        by_type = {}
        for config in self.servers.values():
            by_type[config.type] = by_type.get(config.type, 0) + 1
        
        return {
            "total_servers": len(self.servers),
            "enabled_servers": enabled_count,
            "disabled_servers": disabled_count,
            "by_type": by_type,
            "config_path": str(self.config_path),
            "servers": list(self.servers.keys())
        }