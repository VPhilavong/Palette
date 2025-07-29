"""
MCP Server Registry for managing available MCP servers and their configurations.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict

from .client import MCPServerConfig
import logging


class MCPServerRegistry:
    """Registry for managing MCP server configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self.servers: Dict[str, MCPServerConfig] = {}
        self.logger = logging.getLogger(__name__)
        self.load_config()
        # Auto-discover servers if running in a project
        self._auto_discover_project_servers()
    
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
        # Create config without 'name' field to avoid conflicts, then set name explicitly
        config_data = {k: v for k, v in server_def.items() if k != 'name' and k in MCPServerConfig.__dataclass_fields__}
        config = MCPServerConfig(name=server_name, **config_data)
        
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
                # Remove 'name' from config to avoid conflicts
                config_data = {k: v for k, v in config.items() if k != 'name'}
                self.servers[name] = MCPServerConfig(name=name, **config_data)
            
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
    
    def auto_discover_servers(self, project_path: str = ".") -> Dict[str, List[str]]:
        """
        Auto-discover MCP servers based on project configuration and dependencies.
        Returns a dict with 'discovered' and 'enabled' server names.
        """
        project_path = Path(project_path)
        discovered_servers = []
        enabled_servers = []
        
        print("🔍 Auto-discovering MCP servers...")
        
        # Check for framework and UI library dependencies
        dependencies = self._analyze_project_dependencies(project_path)
        framework_info = self._detect_project_framework(project_path)
        
        print(f"   📦 Found dependencies: {', '.join(dependencies[:5])}{'...' if len(dependencies) > 5 else ''}")
        print(f"   🚀 Detected framework: {framework_info.get('framework', 'unknown')}")
        
        # Always enable design-system server for project analysis
        if "design-system" not in self.servers:
            self._auto_add_server("design-system", enabled=True)
            discovered_servers.append("design-system")
            enabled_servers.append("design-system")
        
        # Framework-specific servers
        framework = framework_info.get('framework', '')
        if framework in ['next.js', 'react']:
            # Enable React-related servers
            if any(dep in dependencies for dep in ['@shadcn/ui', 'shadcn-ui']):
                if self._auto_add_server("shadcn-ui", enabled=True):
                    discovered_servers.append("shadcn-ui")
                    enabled_servers.append("shadcn-ui")
        
        # Styling and UI dependencies
        if any(dep in dependencies for dep in ['tailwindcss', '@tailwindcss/forms', '@tailwindcss/typography']):
            if self._auto_add_server("tailwind", enabled=True):
                discovered_servers.append("tailwind")
                enabled_servers.append("tailwind")
        
        # Icon libraries
        icon_libs = ['lucide-react', 'heroicons', '@heroicons/react', 'react-icons', 'phosphor-icons']
        if any(dep in dependencies for dep in icon_libs):
            if self._auto_add_server("icons", enabled=True):
                discovered_servers.append("icons")
                enabled_servers.append("icons")
        
        # Testing frameworks
        test_deps = ['@testing-library/react', 'jest', 'vitest', 'cypress', '@playwright/test']
        if any(dep in dependencies for dep in test_deps):
            if self._auto_add_server("testing", enabled=False):  # Available but not auto-enabled
                discovered_servers.append("testing")
        
        # Storybook
        if any(dep in dependencies for dep in ['@storybook/react', '@storybook/nextjs']):
            if self._auto_add_server("storybook", enabled=True):
                discovered_servers.append("storybook")
                enabled_servers.append("storybook")
        
        # Accessibility tools
        a11y_deps = ['@axe-core/react', 'eslint-plugin-jsx-a11y', 'react-aria']
        if any(dep in dependencies for dep in a11y_deps):
            if self._auto_add_server("accessibility", enabled=True):
                discovered_servers.append("accessibility")
                enabled_servers.append("accessibility")
        
        # Check for Figma integration (environment variables or config)
        if self._check_figma_integration(project_path):
            if self._auto_add_server("figma", enabled=False):  # Available but requires token
                discovered_servers.append("figma")
        
        # Save the updated configuration
        if discovered_servers:
            self.save_config()
            
        print(f"   ✅ Discovered {len(discovered_servers)} servers")
        print(f"   🟢 Auto-enabled {len(enabled_servers)} servers")
        
        if discovered_servers:
            print(f"   📋 Discovered: {', '.join(discovered_servers)}")
        if enabled_servers:
            print(f"   ⚡ Enabled: {', '.join(enabled_servers)}")
        
        return {
            "discovered": discovered_servers,
            "enabled": enabled_servers
        }
    
    def _analyze_project_dependencies(self, project_path: Path) -> List[str]:
        """Analyze project dependencies from package.json, requirements.txt, etc."""
        dependencies = []
        
        # JavaScript/Node.js projects
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                # Collect all dependencies
                for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                    if dep_type in data:
                        dependencies.extend(data[dep_type].keys())
                        
            except Exception as e:
                print(f"   ⚠️ Failed to parse package.json: {e}")
        
        # Python projects
        requirements_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
        for req_file in requirements_files:
            req_path = project_path / req_file
            if req_path.exists():
                try:
                    if req_file.endswith('.toml'):
                        # Handle pyproject.toml (simplified)
                        with open(req_path, 'r') as f:
                            content = f.read()
                            # Basic extraction - could be improved with proper TOML parsing
                            if 'dependencies' in content:
                                # This is a simplified approach
                                pass
                    else:
                        # Handle requirements.txt format
                        with open(req_path, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    # Extract package name (before version specifiers)
                                    pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                                    dependencies.append(pkg_name)
                except Exception as e:
                    print(f"   ⚠️ Failed to parse {req_file}: {e}")
        
        return dependencies
    
    def _detect_project_framework(self, project_path: Path) -> Dict[str, Any]:
        """Detect the project framework and configuration."""
        framework_info = {}
        
        # Check for Next.js
        next_config_files = ['next.config.js', 'next.config.mjs', 'next.config.ts']
        if any((project_path / config).exists() for config in next_config_files):
            framework_info['framework'] = 'next.js'
            framework_info['routing'] = 'app' if (project_path / 'app').exists() else 'pages'
        
        # Check for Vite
        elif (project_path / 'vite.config.js').exists() or (project_path / 'vite.config.ts').exists():
            framework_info['framework'] = 'vite'
        
        # Check for Create React App
        elif (project_path / 'src' / 'App.js').exists() or (project_path / 'src' / 'App.tsx').exists():
            framework_info['framework'] = 'react'
        
        # Check for Remix
        elif (project_path / 'remix.config.js').exists():
            framework_info['framework'] = 'remix'
        
        # Check for TypeScript
        if (project_path / 'tsconfig.json').exists():
            framework_info['typescript'] = True
        
        # Check for Tailwind
        tailwind_configs = ['tailwind.config.js', 'tailwind.config.ts', 'tailwind.config.cjs']
        if any((project_path / config).exists() for config in tailwind_configs):
            framework_info['styling'] = 'tailwind'
        
        return framework_info
    
    def _check_figma_integration(self, project_path: Path) -> bool:
        """Check if Figma integration is configured."""
        # Check for Figma token in environment or config files
        if os.getenv('FIGMA_TOKEN'):
            return True
        
        # Check for Figma-related config files
        figma_configs = ['.figmarc', 'figma.config.js', '.env.local']
        for config in figma_configs:
            config_path = project_path / config
            if config_path.exists():
                try:
                    content = config_path.read_text()
                    if 'FIGMA' in content.upper():
                        return True
                except:
                    pass
        
        return False
    
    def _auto_add_server(self, server_name: str, enabled: bool = False) -> bool:
        """Auto-add a predefined server if it doesn't exist."""
        if server_name in self.servers:
            # Server already exists, maybe update enabled status
            if enabled and not self.servers[server_name].enabled:
                self.servers[server_name].enabled = enabled
                return True
            return False
        
        # Add new server from predefined configs
        predefined = self.get_predefined_servers()
        if server_name in predefined:
            server_def = predefined[server_name]
            # Create config without 'name' field to avoid conflicts
            config_data = {k: v for k, v in server_def.items() if k != 'name' and k in MCPServerConfig.__dataclass_fields__}
            config = MCPServerConfig(
                name=server_name,
                enabled=enabled,
                **config_data
            )
            
            self.servers[server_name] = config
            return True
        
        return False
    
    def _auto_discover_project_servers(self) -> None:
        """Auto-discover MCP servers in the project."""
        # Check for Palette's built-in MCP servers
        cwd = Path.cwd()
        mcp_servers_dir = cwd / "mcp-servers"
        
        if mcp_servers_dir.exists():
            self.logger.info("Auto-discovering Palette MCP servers...")
            
            for server_dir in mcp_servers_dir.iterdir():
                if server_dir.is_dir() and (server_dir / "server.py").exists():
                    server_name = server_dir.name
                    
                    # Skip if already configured
                    if server_name in self.servers:
                        continue
                    
                    # Add the server
                    config = MCPServerConfig(
                        name=server_name,
                        type="stdio",
                        command="python",
                        args=[str(server_dir / "server.py")],
                        enabled=True,  # Enable by default for built-in servers
                        description=f"Palette built-in {server_name} server"
                    )
                    
                    self.servers[server_name] = config
                    self.logger.info(f"Auto-discovered server: {server_name}")
    
    def _discover_project_servers(self, project_path: Path) -> Dict[str, Dict[str, Any]]:
        """Discover MCP servers from project configuration."""
        servers = {}
        
        # Check for .palette/mcp-servers.json
        config_file = project_path / ".palette" / "mcp-servers.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    for name, server_def in config.items():
                        servers[name] = server_def
                        self.logger.info(f"Found project server: {name}")
            except Exception as e:
                self.logger.error(f"Failed to load project MCP config: {e}")
        
        # Check for palette.json with mcp section
        palette_config = project_path / "palette.json"
        if palette_config.exists():
            try:
                with open(palette_config, 'r') as f:
                    config = json.load(f)
                    if "mcp_servers" in config:
                        for name, server_def in config["mcp_servers"].items():
                            servers[name] = server_def
                            self.logger.info(f"Found server in palette.json: {name}")
            except Exception as e:
                self.logger.error(f"Failed to load palette.json: {e}")
        
        # Auto-discover Palette's built-in MCP servers
        mcp_servers_dir = project_path / "mcp-servers"
        if mcp_servers_dir.exists():
            for server_dir in mcp_servers_dir.iterdir():
                if server_dir.is_dir() and (server_dir / "server.py").exists():
                    server_name = server_dir.name
                    if server_name not in servers:  # Don't override user config
                        servers[server_name] = {
                            "command": "python",
                            "args": [str(server_dir / "server.py")],
                            "description": f"Auto-discovered Palette {server_name} server"
                        }
                        self.logger.info(f"Auto-discovered built-in server: {server_name}")
        
        return servers
    
    def get_all_servers(self) -> List[MCPServerConfig]:
        """Get all registered servers (enabled and disabled)."""
        return list(self.servers.values())
    
    def register_server(self, name: str, server_def: Dict[str, Any]) -> None:
        """Register a new server dynamically."""
        if name not in self.servers:
            config_data = {k: v for k, v in server_def.items() if k != 'name' and k in MCPServerConfig.__dataclass_fields__}
            config = MCPServerConfig(name=name, **config_data)
            self.servers[name] = config