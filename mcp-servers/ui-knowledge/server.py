#!/usr/bin/env python3
"""
UI Knowledge MCP Server for Palette.
Provides comprehensive UI/UX knowledge, patterns, and best practices to make AI a professional frontend developer.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UIKnowledgeMCPServer:
    """MCP Server providing comprehensive UI/UX knowledge and patterns."""
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path(__file__).parent / "data"
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load all UI/UX knowledge from data files."""
        knowledge = {
            "components": {},
            "patterns": {},
            "principles": {},
            "frameworks": {},
            "accessibility": {},
            "performance": {},
            "animations": {}
        }
        
        # Load component patterns
        components_path = self.data_path / "components"
        if components_path.exists():
            for comp_file in components_path.glob("*.json"):
                with open(comp_file, 'r') as f:
                    component_data = json.load(f)
                    knowledge["components"][comp_file.stem] = component_data
        
        # Load design patterns
        patterns_path = self.data_path / "patterns"
        if patterns_path.exists():
            for pattern_file in patterns_path.glob("*.json"):
                with open(pattern_file, 'r') as f:
                    knowledge["patterns"][pattern_file.stem] = json.load(f)
        
        # Load design principles
        principles_path = self.data_path / "principles"
        if principles_path.exists():
            for principle_file in principles_path.glob("*.json"):
                with open(principle_file, 'r') as f:
                    knowledge["principles"][principle_file.stem] = json.load(f)
        
        # Load framework-specific patterns
        frameworks_path = self.data_path / "frameworks"
        if frameworks_path.exists():
            for fw_file in frameworks_path.glob("*.json"):
                with open(fw_file, 'r') as f:
                    knowledge["frameworks"][fw_file.stem] = json.load(f)
        
        return knowledge
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the server and return capabilities."""
        return {
            "protocol_version": "0.1.0",
            "server_info": {
                "name": "ui-knowledge",
                "version": "1.0.0",
                "description": "Comprehensive UI/UX knowledge base for professional frontend development"
            },
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": False
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "get_component_patterns",
                    "description": "Get comprehensive patterns and best practices for a specific UI component",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_type": {
                                "type": "string",
                                "description": "Type of component (button, form, modal, table, etc.)"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Optional: Specific framework (react, vue, angular)",
                                "optional": True
                            },
                            "requirements": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional: Specific requirements (accessibility, animations, etc.)",
                                "optional": True
                            }
                        },
                        "required": ["component_type"]
                    }
                },
                {
                    "name": "get_design_principles",
                    "description": "Get UX principles, accessibility guidelines, and design best practices",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Category of principles (ux, accessibility, responsive, performance)"
                            },
                            "context": {
                                "type": "string",
                                "description": "Optional: Specific context or use case",
                                "optional": True
                            }
                        },
                        "required": ["category"]
                    }
                },
                {
                    "name": "get_styling_guide",
                    "description": "Get CSS best practices, Tailwind utilities, and theme system guidance",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Styling topic (layout, colors, spacing, typography, animations)"
                            },
                            "library": {
                                "type": "string",
                                "description": "Optional: Specific CSS library (tailwind, styled-components, css-modules)",
                                "optional": True
                            }
                        },
                        "required": ["topic"]
                    }
                },
                {
                    "name": "get_framework_patterns",
                    "description": "Get framework-specific patterns and best practices",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "framework": {
                                "type": "string",
                                "description": "Framework name (react, next.js, vue, angular)"
                            },
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of pattern (hooks, state-management, routing, data-fetching)"
                            }
                        },
                        "required": ["framework", "pattern_type"]
                    }
                },
                {
                    "name": "search_ui_knowledge",
                    "description": "Natural language search across all UI/UX knowledge",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_accessibility_guidelines",
                    "description": "Get WCAG guidelines and ARIA best practices",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_type": {
                                "type": "string",
                                "description": "Component type or general accessibility topic"
                            },
                            "level": {
                                "type": "string",
                                "description": "WCAG level (A, AA, AAA)",
                                "default": "AA"
                            }
                        },
                        "required": ["component_type"]
                    }
                },
                {
                    "name": "get_performance_tips",
                    "description": "Get performance optimization tips for frontend development",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "area": {
                                "type": "string",
                                "description": "Performance area (rendering, bundle-size, loading, runtime)"
                            },
                            "framework": {
                                "type": "string",
                                "description": "Optional: Specific framework",
                                "optional": True
                            }
                        },
                        "required": ["area"]
                    }
                },
                {
                    "name": "get_animation_patterns",
                    "description": "Get animation and interaction patterns",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "animation_type": {
                                "type": "string",
                                "description": "Type of animation (transitions, micro-interactions, page-transitions, loading)"
                            },
                            "library": {
                                "type": "string",
                                "description": "Optional: Animation library (framer-motion, gsap, css)",
                                "optional": True
                            }
                        },
                        "required": ["animation_type"]
                    }
                }
            ]
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        try:
            if tool_name == "get_component_patterns":
                return await self._get_component_patterns(
                    arguments["component_type"],
                    arguments.get("framework"),
                    arguments.get("requirements", [])
                )
            elif tool_name == "get_design_principles":
                return await self._get_design_principles(
                    arguments["category"],
                    arguments.get("context")
                )
            elif tool_name == "get_styling_guide":
                return await self._get_styling_guide(
                    arguments["topic"],
                    arguments.get("library")
                )
            elif tool_name == "get_framework_patterns":
                return await self._get_framework_patterns(
                    arguments["framework"],
                    arguments["pattern_type"]
                )
            elif tool_name == "search_ui_knowledge":
                return await self._search_knowledge(
                    arguments["query"],
                    arguments.get("limit", 5)
                )
            elif tool_name == "get_accessibility_guidelines":
                return await self._get_accessibility_guidelines(
                    arguments["component_type"],
                    arguments.get("level", "AA")
                )
            elif tool_name == "get_performance_tips":
                return await self._get_performance_tips(
                    arguments["area"],
                    arguments.get("framework")
                )
            elif tool_name == "get_animation_patterns":
                return await self._get_animation_patterns(
                    arguments["animation_type"],
                    arguments.get("library")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    async def _get_component_patterns(
        self, 
        component_type: str, 
        framework: Optional[str] = None,
        requirements: List[str] = []
    ) -> Dict[str, Any]:
        """Get comprehensive patterns for a component type."""
        # Look up component patterns
        component_data = self.knowledge_base["components"].get(component_type, {})
        
        if not component_data:
            # Fallback to general patterns
            component_data = self._get_general_component_patterns(component_type)
        
        # Filter by framework if specified
        if framework and "frameworks" in component_data:
            framework_specific = component_data["frameworks"].get(framework, {})
            if framework_specific:
                component_data = {**component_data, **framework_specific}
        
        # Filter by requirements
        if requirements:
            filtered_patterns = []
            for pattern in component_data.get("patterns", []):
                if any(req.lower() in pattern.lower() for req in requirements):
                    filtered_patterns.append(pattern)
            if filtered_patterns:
                component_data["filtered_patterns"] = filtered_patterns
        
        return {
            "component_type": component_type,
            "data": component_data,
            "framework": framework,
            "requirements_matched": requirements
        }
    
    async def _get_design_principles(
        self, 
        category: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get design principles for a category."""
        principles = self.knowledge_base["principles"].get(category, {})
        
        if not principles:
            # Return general principles
            principles = self._get_general_design_principles(category)
        
        if context:
            # Filter principles by context
            context_specific = []
            for principle in principles.get("guidelines", []):
                if context.lower() in principle.lower():
                    context_specific.append(principle)
            if context_specific:
                principles["context_specific"] = context_specific
        
        return {
            "category": category,
            "principles": principles,
            "context": context
        }
    
    async def _get_styling_guide(
        self,
        topic: str,
        library: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get styling guidelines."""
        # This would load from a comprehensive styling knowledge base
        styling_guide = {
            "topic": topic,
            "general_guidelines": self._get_general_styling_tips(topic),
            "best_practices": self._get_styling_best_practices(topic)
        }
        
        if library:
            library_specific = self._get_library_specific_styling(library, topic)
            if library_specific:
                styling_guide["library_specific"] = library_specific
        
        return styling_guide
    
    async def _get_framework_patterns(
        self,
        framework: str,
        pattern_type: str
    ) -> Dict[str, Any]:
        """Get framework-specific patterns."""
        framework_data = self.knowledge_base["frameworks"].get(framework, {})
        patterns = framework_data.get(pattern_type, {})
        
        if not patterns:
            patterns = self._get_general_framework_patterns(framework, pattern_type)
        
        return {
            "framework": framework,
            "pattern_type": pattern_type,
            "patterns": patterns
        }
    
    async def _search_knowledge(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search across all knowledge base."""
        results = []
        query_lower = query.lower()
        
        # Search components
        for comp_type, comp_data in self.knowledge_base["components"].items():
            if query_lower in comp_type or self._search_in_dict(query_lower, comp_data):
                results.append({
                    "type": "component",
                    "name": comp_type,
                    "data": comp_data
                })
        
        # Search patterns
        for pattern_name, pattern_data in self.knowledge_base["patterns"].items():
            if query_lower in pattern_name or self._search_in_dict(query_lower, pattern_data):
                results.append({
                    "type": "pattern",
                    "name": pattern_name,
                    "data": pattern_data
                })
        
        # Limit results
        results = results[:limit]
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    async def _get_accessibility_guidelines(
        self,
        component_type: str,
        level: str = "AA"
    ) -> Dict[str, Any]:
        """Get accessibility guidelines."""
        # This would return comprehensive WCAG guidelines
        return {
            "component_type": component_type,
            "wcag_level": level,
            "guidelines": self._get_wcag_guidelines(component_type, level),
            "aria_patterns": self._get_aria_patterns(component_type),
            "keyboard_navigation": self._get_keyboard_patterns(component_type)
        }
    
    async def _get_performance_tips(
        self,
        area: str,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance optimization tips."""
        tips = {
            "area": area,
            "general_tips": self._get_general_performance_tips(area),
            "metrics": self._get_performance_metrics(area)
        }
        
        if framework:
            tips["framework_specific"] = self._get_framework_performance_tips(framework, area)
        
        return tips
    
    async def _get_animation_patterns(
        self,
        animation_type: str,
        library: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get animation patterns."""
        patterns = {
            "type": animation_type,
            "principles": self._get_animation_principles(animation_type),
            "examples": self._get_animation_examples(animation_type)
        }
        
        if library:
            patterns["library_examples"] = self._get_library_animations(library, animation_type)
        
        return patterns
    
    # Helper methods for fallback data
    def _get_general_component_patterns(self, component_type: str) -> Dict[str, Any]:
        """Fallback patterns for unknown components."""
        return {
            "patterns": [
                "Use semantic HTML elements",
                "Implement proper accessibility",
                "Support keyboard navigation",
                "Provide visual feedback",
                "Handle edge cases gracefully"
            ],
            "best_practices": [
                "Follow single responsibility principle",
                "Make components reusable",
                "Use proper prop validation",
                "Document component API",
                "Write unit tests"
            ]
        }
    
    def _get_general_design_principles(self, category: str) -> Dict[str, Any]:
        """Fallback design principles."""
        principles = {
            "ux": {
                "guidelines": [
                    "Keep it simple and intuitive",
                    "Provide clear feedback",
                    "Maintain consistency",
                    "Design for errors",
                    "Make it accessible"
                ]
            },
            "accessibility": {
                "guidelines": [
                    "Ensure keyboard navigation",
                    "Provide text alternatives",
                    "Use sufficient color contrast",
                    "Design for screen readers",
                    "Test with assistive technologies"
                ]
            },
            "responsive": {
                "guidelines": [
                    "Mobile-first approach",
                    "Flexible grid systems",
                    "Responsive typography",
                    "Touch-friendly interactions",
                    "Performance optimization"
                ]
            }
        }
        return principles.get(category, {"guidelines": ["Follow best practices"]})
    
    def _get_general_styling_tips(self, topic: str) -> List[str]:
        """General styling tips."""
        tips = {
            "layout": [
                "Use CSS Grid for 2D layouts",
                "Use Flexbox for 1D layouts",
                "Implement responsive design",
                "Consider container queries",
                "Use proper spacing scales"
            ],
            "colors": [
                "Use a consistent color palette",
                "Ensure sufficient contrast",
                "Consider color blindness",
                "Use semantic color names",
                "Implement dark mode support"
            ],
            "typography": [
                "Use a type scale",
                "Limit font families",
                "Ensure readability",
                "Use relative units",
                "Consider line height and spacing"
            ]
        }
        return tips.get(topic, ["Follow established patterns"])
    
    def _get_styling_best_practices(self, topic: str) -> List[str]:
        """Styling best practices."""
        return [
            "Use CSS custom properties for theming",
            "Implement a consistent spacing system",
            "Follow BEM or similar naming convention",
            "Optimize for performance",
            "Test across browsers"
        ]
    
    def _get_library_specific_styling(self, library: str, topic: str) -> Dict[str, Any]:
        """Library-specific styling guidance."""
        if library == "tailwind":
            return {
                "utilities": self._get_tailwind_utilities(topic),
                "best_practices": [
                    "Use the design system tokens",
                    "Leverage utility classes",
                    "Extract components for reusability",
                    "Use responsive modifiers",
                    "Optimize for production"
                ]
            }
        return {}
    
    def _get_tailwind_utilities(self, topic: str) -> List[str]:
        """Get relevant Tailwind utilities."""
        utilities = {
            "layout": ["flex", "grid", "space-x-*", "gap-*", "container"],
            "colors": ["bg-*", "text-*", "border-*", "ring-*", "divide-*"],
            "typography": ["text-*", "font-*", "leading-*", "tracking-*", "prose"]
        }
        return utilities.get(topic, [])
    
    def _get_general_framework_patterns(self, framework: str, pattern_type: str) -> Dict[str, Any]:
        """General framework patterns."""
        patterns = {
            "react": {
                "hooks": {
                    "patterns": ["useState", "useEffect", "useContext", "useReducer", "custom hooks"],
                    "best_practices": ["Follow rules of hooks", "Extract custom hooks", "Optimize dependencies"]
                },
                "state-management": {
                    "patterns": ["Context API", "Redux", "Zustand", "Jotai"],
                    "best_practices": ["Minimize global state", "Normalize data", "Use proper selectors"]
                }
            },
            "vue": {
                "composition-api": {
                    "patterns": ["ref", "reactive", "computed", "watch", "composables"],
                    "best_practices": ["Use composition API", "Extract composables", "Type your components"]
                }
            }
        }
        return patterns.get(framework, {}).get(pattern_type, {})
    
    def _search_in_dict(self, query: str, data: Any) -> bool:
        """Recursively search for query in dictionary/list."""
        if isinstance(data, dict):
            for key, value in data.items():
                if query in str(key).lower() or self._search_in_dict(query, value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if query in str(item).lower() or self._search_in_dict(query, item):
                    return True
        elif isinstance(data, str):
            return query in data.lower()
        return False
    
    def _get_wcag_guidelines(self, component_type: str, level: str) -> List[str]:
        """Get WCAG guidelines."""
        return [
            f"Ensure {component_type} meets WCAG {level} standards",
            "Provide appropriate ARIA labels",
            "Ensure keyboard accessibility",
            "Test with screen readers",
            "Maintain focus management"
        ]
    
    def _get_aria_patterns(self, component_type: str) -> Dict[str, Any]:
        """Get ARIA patterns."""
        return {
            "required_attributes": ["role", "aria-label", "aria-describedby"],
            "states": ["aria-expanded", "aria-selected", "aria-disabled"],
            "live_regions": ["aria-live", "aria-atomic", "aria-relevant"]
        }
    
    def _get_keyboard_patterns(self, component_type: str) -> List[str]:
        """Get keyboard navigation patterns."""
        return [
            "Tab for navigation between elements",
            "Enter/Space for activation",
            "Arrow keys for selection",
            "Escape for dismissal",
            "Focus trapping for modals"
        ]
    
    def _get_general_performance_tips(self, area: str) -> List[str]:
        """General performance tips."""
        tips = {
            "rendering": [
                "Minimize re-renders",
                "Use React.memo/Vue.memo",
                "Virtualize long lists",
                "Optimize images",
                "Lazy load components"
            ],
            "bundle-size": [
                "Code splitting",
                "Tree shaking",
                "Lazy loading",
                "Optimize dependencies",
                "Compress assets"
            ]
        }
        return tips.get(area, ["Measure and optimize"])
    
    def _get_performance_metrics(self, area: str) -> Dict[str, Any]:
        """Performance metrics to track."""
        return {
            "core_web_vitals": ["LCP", "FID", "CLS"],
            "custom_metrics": ["Time to Interactive", "First Contentful Paint"],
            "tools": ["Lighthouse", "WebPageTest", "Chrome DevTools"]
        }
    
    def _get_framework_performance_tips(self, framework: str, area: str) -> List[str]:
        """Framework-specific performance tips."""
        if framework == "react" and area == "rendering":
            return [
                "Use React.memo for expensive components",
                "Implement useMemo and useCallback",
                "Avoid inline functions in render",
                "Use React DevTools Profiler",
                "Consider React.lazy for code splitting"
            ]
        return []
    
    def _get_animation_principles(self, animation_type: str) -> List[str]:
        """Animation principles."""
        return [
            "Keep animations purposeful",
            "Use appropriate duration (200-500ms)",
            "Apply easing functions",
            "Respect reduced motion preferences",
            "Ensure smooth 60fps performance"
        ]
    
    def _get_animation_examples(self, animation_type: str) -> Dict[str, Any]:
        """Animation examples."""
        examples = {
            "transitions": {
                "hover": "transition-all duration-200 ease-in-out",
                "focus": "focus:ring-2 focus:ring-offset-2",
                "active": "active:scale-95"
            },
            "micro-interactions": {
                "button_press": "transform scale on click",
                "loading": "skeleton screens or spinners",
                "success": "checkmark animation"
            }
        }
        return examples.get(animation_type, {})
    
    def _get_library_animations(self, library: str, animation_type: str) -> Dict[str, Any]:
        """Library-specific animations."""
        if library == "framer-motion":
            return {
                "initial": "opacity: 0, y: 20",
                "animate": "opacity: 1, y: 0",
                "transition": "duration: 0.3, ease: 'easeOut'"
            }
        return {}
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "resources": [
                {
                    "uri": "ui-knowledge://components",
                    "name": "Component Patterns",
                    "description": "Comprehensive patterns for all UI components",
                    "mimeType": "application/json"
                },
                {
                    "uri": "ui-knowledge://principles",
                    "name": "Design Principles",
                    "description": "UX and design principles",
                    "mimeType": "application/json"
                },
                {
                    "uri": "ui-knowledge://frameworks",
                    "name": "Framework Patterns",
                    "description": "Framework-specific patterns and best practices",
                    "mimeType": "application/json"
                }
            ]
        }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        parts = uri.split("://")[1].split("/")
        resource_type = parts[0]
        
        if resource_type == "components":
            return {
                "contents": self.knowledge_base["components"],
                "mimeType": "application/json"
            }
        elif resource_type == "principles":
            return {
                "contents": self.knowledge_base["principles"],
                "mimeType": "application/json"
            }
        elif resource_type == "frameworks":
            return {
                "contents": self.knowledge_base["frameworks"],
                "mimeType": "application/json"
            }
        
        return {"error": f"Unknown resource: {uri}"}


async def run_stdio_server():
    """Run the MCP server using stdio transport."""
    import mcp
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    
    # Create server instance
    ui_knowledge_server = UIKnowledgeMCPServer()
    server = Server("ui-knowledge")
    
    # Register handlers
    @server.list_tools()
    async def list_tools():
        return await ui_knowledge_server.list_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        return await ui_knowledge_server.call_tool(name, arguments)
    
    @server.list_resources()
    async def list_resources():
        return await ui_knowledge_server.list_resources()
    
    @server.read_resource()
    async def read_resource(uri: str):
        return await ui_knowledge_server.read_resource(uri)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, ui_knowledge_server.initialize())


async def test_server():
    """Test the server functionality."""
    server = UIKnowledgeMCPServer()
    
    print("Testing UI Knowledge MCP Server")
    print("=" * 60)
    
    # Test component patterns
    print("\n1. Testing get_component_patterns")
    result = await server.call_tool("get_component_patterns", {
        "component_type": "button",
        "framework": "react",
        "requirements": ["accessibility", "loading"]
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test design principles
    print("\n2. Testing get_design_principles")
    result = await server.call_tool("get_design_principles", {
        "category": "accessibility",
        "context": "forms"
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test search
    print("\n3. Testing search_ui_knowledge")
    result = await server.call_tool("search_ui_knowledge", {
        "query": "button",
        "limit": 3
    })
    print(f"Result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="UI Knowledge MCP Server")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_server())
    else:
        try:
            asyncio.run(run_stdio_server())
        except ImportError:
            print("MCP SDK not installed. Running in test mode.")
            asyncio.run(test_server())