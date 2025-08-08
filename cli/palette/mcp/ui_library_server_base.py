#!/usr/bin/env python3
"""
Abstract base class for UI Library MCP servers.
Provides standardized interface for UI library-specific knowledge and operations.
"""

import sys
import json
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from palette.analysis.context import ProjectAnalyzer
from palette.utils.file_manager import FileManager


class UILibraryType(Enum):
    """Supported UI library types."""
    CHAKRA_UI = "chakra-ui"
    MATERIAL_UI = "material-ui"
    ANT_DESIGN = "ant-design"
    SHADCN_UI = "shadcn/ui"
    MANTINE = "mantine"
    TAILWIND_UI = "tailwind-ui"
    REACT_BOOTSTRAP = "react-bootstrap"
    SEMANTIC_UI = "semantic-ui"


@dataclass
class UIComponent:
    """Represents a UI component with its metadata."""
    name: str
    import_path: str
    props: List[Dict[str, Any]]
    variants: List[str]
    examples: List[str]
    description: str
    category: str
    tags: List[str]
    dependencies: List[str]
    typescript_types: Optional[str] = None
    accessibility_features: List[str] = None
    design_tokens_used: List[str] = None


@dataclass
class UILibraryContext:
    """Context information for a specific UI library."""
    library_type: UILibraryType
    version: str
    components: List[UIComponent]
    design_tokens: Dict[str, Any]
    theme_config: Dict[str, Any]
    installation_guide: str
    best_practices: List[str]
    common_patterns: List[str]
    typescript_support: bool
    openai_system_prompt: str
    openai_examples: List[Dict[str, str]]


class UILibraryMCPServer(ABC):
    """
    Abstract base class for UI Library MCP servers.
    Provides standardized interface for different UI libraries.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.analyzer = ProjectAnalyzer()
        self.file_manager = FileManager()
        
        # Cache for project analysis and library context
        self._project_context = None
        self._library_context = None
        
        # Initialize library-specific data
        self._initialize_library_data()
    
    @property
    @abstractmethod
    def library_type(self) -> UILibraryType:
        """Return the UI library type this server handles."""
        pass
    
    @property
    @abstractmethod
    def server_name(self) -> str:
        """Return the server name for MCP identification."""
        pass
    
    @property
    @abstractmethod
    def server_version(self) -> str:
        """Return the server version."""
        pass
    
    @abstractmethod
    def _initialize_library_data(self):
        """Initialize library-specific data structures."""
        pass
    
    @abstractmethod
    async def get_component_catalog(self) -> List[UIComponent]:
        """Get the complete component catalog for this library."""
        pass
    
    @abstractmethod
    async def get_design_tokens(self) -> Dict[str, Any]:
        """Get design tokens specific to this library."""
        pass
    
    @abstractmethod
    async def get_openai_system_prompt(self) -> str:
        """Get OpenAI-optimized system prompt for this library."""
        pass
    
    @abstractmethod
    async def get_openai_examples(self) -> List[Dict[str, str]]:
        """Get OpenAI few-shot examples for this library."""
        pass
    
    @abstractmethod
    async def validate_component_usage(self, component_code: str) -> Dict[str, Any]:
        """Validate component code against library-specific rules."""
        pass
    
    @abstractmethod
    async def suggest_component_alternatives(self, component_name: str) -> List[str]:
        """Suggest alternative components within the library."""
        pass
    
    @abstractmethod
    async def generate_usage_example(self, component_name: str, props: Dict[str, Any] = None) -> str:
        """Generate usage example for a specific component."""
        pass
    
    # Standard MCP server methods
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP server and return capabilities."""
        return {
            "protocol_version": "0.1.0",
            "server_info": {
                "name": self.server_name,
                "version": self.server_version,
                "description": f"{self.library_type.value} MCP server for Palette"
            },
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools for this UI library."""
        return {
            "tools": [
                {
                    "name": "get_component_info",
                    "description": f"Get detailed information about {self.library_type.value} components",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_name": {
                                "type": "string",
                                "description": "Name of the component to get info for"
                            },
                            "include_examples": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include usage examples"
                            }
                        },
                        "required": ["component_name"]
                    }
                },
                {
                    "name": "search_components",
                    "description": f"Search {self.library_type.value} components by category or functionality",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for components"
                            },
                            "category": {
                                "type": "string",
                                "description": "Component category to filter by"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 10,
                                "description": "Maximum number of results"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "validate_library_usage",
                    "description": f"Validate component code against {self.library_type.value} best practices",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_code": {
                                "type": "string",
                                "description": "Component code to validate"
                            },
                            "strict_mode": {
                                "type": "boolean",
                                "default": False,
                                "description": "Enable strict validation mode"
                            }
                        },
                        "required": ["component_code"]
                    }
                },
                {
                    "name": "get_migration_suggestions",
                    "description": f"Get suggestions for migrating components to {self.library_type.value}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source_code": {
                                "type": "string",
                                "description": "Source component code to migrate"
                            },
                            "source_library": {
                                "type": "string",
                                "description": "Source UI library (if known)"
                            }
                        },
                        "required": ["source_code"]
                    }
                },
                {
                    "name": "generate_openai_prompt",
                    "description": f"Generate OpenAI-optimized prompt with {self.library_type.value} context",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_request": {
                                "type": "string",
                                "description": "User's component generation request"
                            },
                            "component_type": {
                                "type": "string",
                                "description": "Type of component requested"
                            },
                            "complexity_level": {
                                "type": "string",
                                "enum": ["simple", "intermediate", "advanced"],
                                "default": "intermediate",
                                "description": "Complexity level for generation"
                            }
                        },
                        "required": ["user_request"]
                    }
                },
                {
                    "name": "get_theme_customization",
                    "description": f"Get theme customization options for {self.library_type.value}",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "theme_aspect": {
                                "type": "string",
                                "enum": ["colors", "typography", "spacing", "components", "all"],
                                "default": "all",
                                "description": "Theme aspect to customize"
                            }
                        }
                    }
                }
            ]
        }
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources for this UI library."""
        library_name = self.library_type.value
        return {
            "resources": [
                {
                    "uri": f"ui-library://{library_name}/catalog/all",
                    "name": f"{library_name} Component Catalog",
                    "description": f"Complete component catalog for {library_name}",
                    "mimeType": "application/json"
                },
                {
                    "uri": f"ui-library://{library_name}/design-tokens",
                    "name": f"{library_name} Design Tokens",
                    "description": f"Design tokens and theme configuration for {library_name}",
                    "mimeType": "application/json"
                },
                {
                    "uri": f"ui-library://{library_name}/openai/system-prompt",
                    "name": f"{library_name} OpenAI System Prompt",
                    "description": f"OpenAI-optimized system prompt for {library_name}",
                    "mimeType": "text/plain"
                },
                {
                    "uri": f"ui-library://{library_name}/openai/examples",
                    "name": f"{library_name} OpenAI Examples",
                    "description": f"Few-shot examples for OpenAI generation with {library_name}",
                    "mimeType": "application/json"
                },
                {
                    "uri": f"ui-library://{library_name}/best-practices",
                    "name": f"{library_name} Best Practices",
                    "description": f"Best practices and patterns for {library_name}",
                    "mimeType": "application/json"
                },
                {
                    "uri": f"ui-library://{library_name}/installation-guide",
                    "name": f"{library_name} Installation Guide",
                    "description": f"Installation and setup guide for {library_name}",
                    "mimeType": "text/markdown"
                }
            ]
        }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        try:
            if name == "get_component_info":
                return await self._get_component_info(**arguments)
            elif name == "search_components":
                return await self._search_components(**arguments)
            elif name == "validate_library_usage":
                return await self._validate_library_usage(**arguments)
            elif name == "get_migration_suggestions":
                return await self._get_migration_suggestions(**arguments)
            elif name == "generate_openai_prompt":
                return await self._generate_openai_prompt(**arguments)
            elif name == "get_theme_customization":
                return await self._get_theme_customization(**arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource."""
        try:
            library_name = self.library_type.value
            
            if uri == f"ui-library://{library_name}/catalog/all":
                catalog = await self.get_component_catalog()
                return {"contents": [{"type": "text", "text": json.dumps([c.__dict__ for c in catalog], indent=2)}]}
            
            elif uri == f"ui-library://{library_name}/design-tokens":
                tokens = await self.get_design_tokens()
                return {"contents": [{"type": "text", "text": json.dumps(tokens, indent=2)}]}
            
            elif uri == f"ui-library://{library_name}/openai/system-prompt":
                prompt = await self.get_openai_system_prompt()
                return {"contents": [{"type": "text", "text": prompt}]}
            
            elif uri == f"ui-library://{library_name}/openai/examples":
                examples = await self.get_openai_examples()
                return {"contents": [{"type": "text", "text": json.dumps(examples, indent=2)}]}
            
            elif uri == f"ui-library://{library_name}/best-practices":
                practices = await self._get_best_practices()
                return {"contents": [{"type": "text", "text": json.dumps(practices, indent=2)}]}
            
            elif uri == f"ui-library://{library_name}/installation-guide":
                guide = await self._get_installation_guide()
                return {"contents": [{"type": "text", "text": guide}]}
            
            else:
                return {"error": f"Unknown resource: {uri}"}
        except Exception as e:
            return {"error": str(e)}
    
    # Tool implementation methods
    
    async def _get_component_info(
        self, 
        component_name: str, 
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """Get detailed information about a specific component."""
        catalog = await self.get_component_catalog()
        
        # Find the component
        component = None
        for comp in catalog:
            if comp.name.lower() == component_name.lower():
                component = comp
                break
        
        if not component:
            return {
                "error": f"Component '{component_name}' not found",
                "available_components": [c.name for c in catalog[:10]]
            }
        
        result = {
            "name": component.name,
            "import_path": component.import_path,
            "description": component.description,
            "category": component.category,
            "props": component.props,
            "variants": component.variants,
            "tags": component.tags,
            "dependencies": component.dependencies,
            "typescript_support": bool(component.typescript_types),
            "accessibility_features": component.accessibility_features or [],
            "design_tokens_used": component.design_tokens_used or []
        }
        
        if include_examples:
            result["examples"] = component.examples
            
        if component.typescript_types:
            result["typescript_types"] = component.typescript_types
        
        return result
    
    async def _search_components(
        self, 
        query: str, 
        category: str = None, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search components by query and category."""
        catalog = await self.get_component_catalog()
        results = []
        
        query_lower = query.lower()
        
        for component in catalog:
            score = 0
            
            # Name matching (highest weight)
            if query_lower in component.name.lower():
                score += 10
            
            # Description matching
            if query_lower in component.description.lower():
                score += 5
            
            # Tag matching
            for tag in component.tags:
                if query_lower in tag.lower():
                    score += 3
            
            # Category filter
            if category and component.category.lower() != category.lower():
                continue
            
            if score > 0:
                results.append({
                    "component": component,
                    "score": score
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        return {
            "query": query,
            "category": category,
            "results": [
                {
                    "name": r["component"].name,
                    "description": r["component"].description,
                    "category": r["component"].category,
                    "import_path": r["component"].import_path,
                    "score": r["score"]
                }
                for r in results
            ],
            "total_found": len(results)
        }
    
    async def _validate_library_usage(
        self, 
        component_code: str, 
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """Validate component code against library-specific rules."""
        return await self.validate_component_usage(component_code)
    
    async def _get_migration_suggestions(
        self, 
        source_code: str, 
        source_library: str = None
    ) -> Dict[str, Any]:
        """Get migration suggestions for converting to this library."""
        suggestions = []
        
        # Analyze the source code for patterns
        import re
        
        # Extract imports
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, source_code)
        
        # Extract component usage
        component_pattern = r'<(\w+)'
        components_used = re.findall(component_pattern, source_code)
        
        # Get our component catalog
        catalog = await self.get_component_catalog()
        our_components = {c.name.lower(): c for c in catalog}
        
        # Generate migration suggestions
        for component in set(components_used):
            if component.lower() in our_components:
                our_component = our_components[component.lower()]
                suggestions.append({
                    "original_component": component,
                    "suggested_component": our_component.name,
                    "import_path": our_component.import_path,
                    "reason": f"Direct equivalent available in {self.library_type.value}",
                    "confidence": "high"
                })
        
        # Check for library-specific imports that need replacement
        migration_map = await self._get_library_migration_map()
        for import_path in imports:
            if import_path in migration_map:
                suggestions.append({
                    "original_import": import_path,
                    "suggested_import": migration_map[import_path],
                    "reason": f"Replace with {self.library_type.value} equivalent",
                    "confidence": "medium"
                })
        
        return {
            "source_library": source_library,
            "target_library": self.library_type.value,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }
    
    async def _generate_openai_prompt(
        self, 
        user_request: str, 
        component_type: str = None, 
        complexity_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Generate OpenAI-optimized prompt with library context."""
        system_prompt = await self.get_openai_system_prompt()
        examples = await self.get_openai_examples()
        
        # Build enhanced user prompt
        enhanced_prompt = f"User request: {user_request}\n\n"
        
        if component_type:
            enhanced_prompt += f"Component type: {component_type}\n"
            
        enhanced_prompt += f"Complexity level: {complexity_level}\n\n"
        
        # Add relevant examples
        relevant_examples = []
        if component_type:
            relevant_examples = [ex for ex in examples if component_type.lower() in ex.get("prompt", "").lower()]
        
        if not relevant_examples:
            relevant_examples = examples[:2]  # Use first 2 examples as fallback
        
        if relevant_examples:
            enhanced_prompt += "Examples:\n\n"
            for i, example in enumerate(relevant_examples):
                enhanced_prompt += f"Example {i+1}:\n"
                enhanced_prompt += f"Prompt: {example['prompt']}\n"
                enhanced_prompt += f"Response: {example['response']}\n\n"
        
        enhanced_prompt += f"Generate a {complexity_level} {component_type or 'component'} using {self.library_type.value}."
        
        return {
            "system_prompt": system_prompt,
            "enhanced_user_prompt": enhanced_prompt,
            "library_context": self.library_type.value,
            "complexity_level": complexity_level,
            "relevant_examples": len(relevant_examples)
        }
    
    async def _get_theme_customization(self, theme_aspect: str = "all") -> Dict[str, Any]:
        """Get theme customization options."""
        design_tokens = await self.get_design_tokens()
        
        if theme_aspect == "all":
            return {
                "theme_aspects": design_tokens,
                "customization_guide": await self._get_theme_customization_guide()
            }
        elif theme_aspect in design_tokens:
            return {
                "theme_aspect": theme_aspect,
                "options": design_tokens[theme_aspect],
                "customization_guide": await self._get_theme_customization_guide()
            }
        else:
            return {
                "error": f"Unknown theme aspect: {theme_aspect}",
                "available_aspects": list(design_tokens.keys())
            }
    
    # Helper methods that can be overridden by subclasses
    
    async def _get_project_context(self) -> Dict[str, Any]:
        """Get cached project context."""
        if self._project_context is None:
            self._project_context = self.analyzer.analyze_project(str(self.project_path))
        return self._project_context
    
    async def _get_library_context(self) -> UILibraryContext:
        """Get cached library context."""
        if self._library_context is None:
            self._library_context = UILibraryContext(
                library_type=self.library_type,
                version=await self._get_library_version(),
                components=await self.get_component_catalog(),
                design_tokens=await self.get_design_tokens(),
                theme_config=await self._get_theme_config(),
                installation_guide=await self._get_installation_guide(),
                best_practices=await self._get_best_practices(),
                common_patterns=await self._get_common_patterns(),
                typescript_support=await self._has_typescript_support(),
                openai_system_prompt=await self.get_openai_system_prompt(),
                openai_examples=await self.get_openai_examples()
            )
        return self._library_context
    
    @abstractmethod
    async def _get_library_version(self) -> str:
        """Get the library version."""
        pass
    
    @abstractmethod
    async def _get_theme_config(self) -> Dict[str, Any]:
        """Get theme configuration structure."""
        pass
    
    @abstractmethod
    async def _get_installation_guide(self) -> str:
        """Get installation guide."""
        pass
    
    @abstractmethod
    async def _get_best_practices(self) -> List[str]:
        """Get best practices for this library."""
        pass
    
    @abstractmethod
    async def _get_common_patterns(self) -> List[str]:
        """Get common patterns for this library."""
        pass
    
    @abstractmethod
    async def _has_typescript_support(self) -> bool:
        """Check if library has TypeScript support."""
        pass
    
    @abstractmethod
    async def _get_library_migration_map(self) -> Dict[str, str]:
        """Get migration mapping from other libraries to this one."""
        pass
    
    @abstractmethod
    async def _get_theme_customization_guide(self) -> str:
        """Get theme customization guide."""
        pass