#!/usr/bin/env python3
"""
Design System MCP Server for Palette.
Provides access to design tokens, component patterns, and design system validation.
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from palette.analysis.context import ProjectAnalyzer
from palette.utils.file_manager import FileManager


class DesignSystemMCPServer:
    """MCP Server for design system operations."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.analyzer = ProjectAnalyzer()
        self.file_manager = FileManager()
        
        # Cache for project analysis
        self._project_context = None
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the server and return capabilities."""
        return {
            "protocol_version": "0.1.0",
            "server_info": {
                "name": "design-system",
                "version": "1.0.0",
                "description": "Design system analysis and validation for Palette"
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
                    "name": "get_design_tokens",
                    "description": "Extract design tokens from the project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "token_type": {
                                "type": "string",
                                "enum": ["colors", "spacing", "typography", "shadows", "all"],
                                "description": "Type of design tokens to retrieve"
                            },
                            "format": {
                                "type": "string", 
                                "enum": ["json", "css", "tailwind"],
                                "default": "json",
                                "description": "Output format for tokens"
                            }
                        },
                        "required": ["token_type"]
                    }
                },
                {
                    "name": "validate_component_compliance",
                    "description": "Validate if a component follows design system rules",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_code": {
                                "type": "string",
                                "description": "React component code to validate"
                            },
                            "rules": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific rules to check (optional)"
                            }
                        },
                        "required": ["component_code"]
                    }
                },
                {
                    "name": "find_similar_components",
                    "description": "Find existing components similar to a description",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Description of the component to find"
                            },
                            "limit": {
                                "type": "integer",
                                "default": 5,
                                "description": "Maximum number of results"
                            }
                        },
                        "required": ["description"]
                    }
                },
                {
                    "name": "analyze_component_patterns",
                    "description": "Analyze existing component patterns in the project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "pattern_type": {
                                "type": "string",
                                "enum": ["props", "state", "styling", "structure", "all"],
                                "default": "all",
                                "description": "Type of patterns to analyze"
                            }
                        }
                    }
                },
                {
                    "name": "get_component_library_info",
                    "description": "Get information about the project's component library",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_examples": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include code examples"
                            }
                        }
                    }
                },
                {
                    "name": "suggest_design_improvements",
                    "description": "Suggest design system improvements for a component",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_code": {
                                "type": "string",
                                "description": "Component code to analyze"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["accessibility", "performance", "consistency", "maintainability"]
                                },
                                "description": "Areas to focus improvement suggestions on"
                            }
                        },
                        "required": ["component_code"]
                    }
                }
            ]
        }
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "resources": [
                {
                    "uri": "design-system://tokens/all",
                    "name": "All Design Tokens",
                    "description": "Complete design token collection",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://tokens/colors",
                    "name": "Color Tokens",
                    "description": "Project color palette and semantic colors",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://tokens/spacing",
                    "name": "Spacing Scale",
                    "description": "Spacing and sizing tokens",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://tokens/typography",
                    "name": "Typography Scale",
                    "description": "Font sizes, weights, and typography tokens",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://components/patterns",
                    "name": "Component Patterns",
                    "description": "Analyzed patterns from existing components",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://library/info",
                    "name": "Component Library Info",
                    "description": "Information about the project's component library",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-system://config/tailwind",
                    "name": "Tailwind Configuration",
                    "description": "Parsed Tailwind configuration",
                    "mimeType": "application/json"
                }
            ]
        }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        try:
            if name == "get_design_tokens":
                return await self._get_design_tokens(**arguments)
            elif name == "validate_component_compliance":
                return await self._validate_component_compliance(**arguments)
            elif name == "find_similar_components":
                return await self._find_similar_components(**arguments)
            elif name == "analyze_component_patterns":
                return await self._analyze_component_patterns(**arguments)
            elif name == "get_component_library_info":
                return await self._get_component_library_info(**arguments)
            elif name == "suggest_design_improvements":
                return await self._suggest_design_improvements(**arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource."""
        try:
            if uri == "design-system://tokens/all":
                return await self._get_all_tokens()
            elif uri == "design-system://tokens/colors":
                return await self._get_color_tokens()
            elif uri == "design-system://tokens/spacing":
                return await self._get_spacing_tokens()
            elif uri == "design-system://tokens/typography":
                return await self._get_typography_tokens()
            elif uri == "design-system://components/patterns":
                return await self._get_component_patterns()
            elif uri == "design-system://library/info":
                return await self._get_library_info()
            elif uri == "design-system://config/tailwind":
                return await self._get_tailwind_config()
            else:
                return {"error": f"Unknown resource: {uri}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_project_context(self) -> Dict[str, Any]:
        """Get cached project context."""
        if self._project_context is None:
            self._project_context = self.analyzer.analyze_project(str(self.project_path))
        return self._project_context
    
    async def _get_design_tokens(
        self, 
        token_type: str, 
        format: str = "json"
    ) -> Dict[str, Any]:
        """Get design tokens from the project."""
        context = await self._get_project_context()
        design_tokens = context.get("design_tokens", {})
        
        if token_type == "all":
            result = design_tokens
        elif token_type in design_tokens:
            result = {token_type: design_tokens[token_type]}
        else:
            return {
                "error": f"Unknown token type: {token_type}",
                "available_types": list(design_tokens.keys())
            }
        
        # Format conversion
        if format == "json":
            return {"tokens": result, "format": "json"}
        elif format == "css":
            return {"tokens": self._convert_tokens_to_css(result), "format": "css"}
        elif format == "tailwind":
            return {"tokens": self._convert_tokens_to_tailwind(result), "format": "tailwind"}
        
        return {"tokens": result, "format": format}
    
    async def _validate_component_compliance(
        self, 
        component_code: str, 
        rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate component against design system rules."""
        context = await self._get_project_context()
        issues = []
        suggestions = []
        
        # Default validation rules
        validation_rules = rules or [
            "color_usage", "spacing_consistency", "typography_scale", 
            "component_structure", "accessibility_basics"
        ]
        
        # Color usage validation
        if "color_usage" in validation_rules:
            color_issues = self._validate_color_usage(component_code, context)
            issues.extend(color_issues)
        
        # Spacing consistency
        if "spacing_consistency" in validation_rules:
            spacing_issues = self._validate_spacing_consistency(component_code, context)
            issues.extend(spacing_issues)
        
        # Typography scale
        if "typography_scale" in validation_rules:
            typography_issues = self._validate_typography_scale(component_code, context)
            issues.extend(typography_issues)
        
        # Component structure
        if "component_structure" in validation_rules:
            structure_issues = self._validate_component_structure(component_code, context)
            issues.extend(structure_issues)
        
        # Basic accessibility
        if "accessibility_basics" in validation_rules:
            a11y_issues = self._validate_accessibility_basics(component_code)
            issues.extend(a11y_issues)
        
        # Generate suggestions based on issues
        if issues:
            suggestions = self._generate_improvement_suggestions(issues, context)
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "rules_checked": validation_rules,
            "score": max(0, 100 - (len(issues) * 10))
        }
    
    async def _find_similar_components(
        self, 
        description: str, 
        limit: int = 5
    ) -> Dict[str, Any]:
        """Find components similar to description."""
        # This would use semantic search in a real implementation
        # For now, we'll do keyword-based matching
        
        similar_components = []
        
        # Search through component files
        component_patterns = ["**/*.tsx", "**/*.jsx"]
        
        for pattern in component_patterns:
            for file_path in self.project_path.glob(pattern):
                if 'node_modules' in str(file_path):
                    continue
                
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Simple similarity scoring
                    score = self._calculate_similarity(description, content)
                    
                    if score > 0.3:
                        similar_components.append({
                            "file_path": str(file_path.relative_to(self.project_path)),
                            "component_name": file_path.stem,
                            "similarity_score": score,
                            "preview": content[:300] + "..." if len(content) > 300 else content
                        })
                except:
                    continue
        
        # Sort by similarity and limit results
        similar_components.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "query": description,
            "results": similar_components[:limit],
            "total_found": len(similar_components)
        }
    
    async def _analyze_component_patterns(
        self, 
        pattern_type: str = "all"
    ) -> Dict[str, Any]:
        """Analyze component patterns in the project."""
        context = await self._get_project_context()
        
        patterns = {
            "props": [],
            "state": [],
            "styling": [],
            "structure": []
        }
        
        # Analyze component files
        component_files = list(self.project_path.glob("**/*.tsx")) + list(self.project_path.glob("**/*.jsx"))
        
        for file_path in component_files[:20]:  # Limit for performance
            if 'node_modules' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if pattern_type in ["props", "all"]:
                    prop_patterns = self._extract_prop_patterns(content)
                    patterns["props"].extend(prop_patterns)
                
                if pattern_type in ["state", "all"]:
                    state_patterns = self._extract_state_patterns(content)
                    patterns["state"].extend(state_patterns)
                
                if pattern_type in ["styling", "all"]:
                    styling_patterns = self._extract_styling_patterns(content)
                    patterns["styling"].extend(styling_patterns)
                
                if pattern_type in ["structure", "all"]:
                    structure_patterns = self._extract_structure_patterns(content)
                    patterns["structure"].extend(structure_patterns)
                    
            except:
                continue
        
        # Deduplicate and summarize patterns
        for key in patterns:
            patterns[key] = list(set(patterns[key]))
        
        return {
            "pattern_type": pattern_type,
            "patterns": patterns if pattern_type == "all" else {pattern_type: patterns[pattern_type]},
            "files_analyzed": len(component_files)
        }
    
    async def _get_component_library_info(
        self, 
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """Get component library information."""
        context = await self._get_project_context()
        
        library_info = {
            "detected_library": context.get("component_library", "none"),
            "framework": context.get("framework", "unknown"),
            "styling": context.get("styling", "unknown"),
            "typescript": context.get("typescript", False),
            "available_components": []
        }
        
        # Get available imports
        available_imports = context.get("available_imports", {})
        
        if available_imports.get("ui_components"):
            library_info["available_components"] = available_imports["ui_components"]
        
        # Add examples if requested
        if include_examples and library_info["detected_library"] == "shadcn/ui":
            library_info["examples"] = self._get_shadcn_examples()
        
        return library_info
    
    async def _suggest_design_improvements(
        self, 
        component_code: str, 
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Suggest design system improvements."""
        context = await self._get_project_context()
        suggestions = []
        
        focus_areas = focus_areas or ["accessibility", "performance", "consistency", "maintainability"]
        
        # Accessibility improvements
        if "accessibility" in focus_areas:
            a11y_suggestions = self._get_accessibility_suggestions(component_code)
            suggestions.extend(a11y_suggestions)
        
        # Performance improvements
        if "performance" in focus_areas:
            perf_suggestions = self._get_performance_suggestions(component_code)
            suggestions.extend(perf_suggestions)
        
        # Consistency improvements
        if "consistency" in focus_areas:
            consistency_suggestions = self._get_consistency_suggestions(component_code, context)
            suggestions.extend(consistency_suggestions)
        
        # Maintainability improvements
        if "maintainability" in focus_areas:
            maintainability_suggestions = self._get_maintainability_suggestions(component_code)
            suggestions.extend(maintainability_suggestions)
        
        return {
            "suggestions": suggestions,
            "focus_areas": focus_areas,
            "total_suggestions": len(suggestions)
        }
    
    # Resource methods
    
    async def _get_all_tokens(self) -> Dict[str, Any]:
        """Get all design tokens."""
        context = await self._get_project_context()
        return {"contents": [{"type": "text", "text": json.dumps(context.get("design_tokens", {}), indent=2)}]}
    
    async def _get_color_tokens(self) -> Dict[str, Any]:
        """Get color tokens."""
        context = await self._get_project_context()
        colors = context.get("design_tokens", {}).get("colors", {})
        return {"contents": [{"type": "text", "text": json.dumps(colors, indent=2)}]}
    
    async def _get_spacing_tokens(self) -> Dict[str, Any]:
        """Get spacing tokens."""
        context = await self._get_project_context()
        spacing = context.get("design_tokens", {}).get("spacing", [])
        return {"contents": [{"type": "text", "text": json.dumps(spacing, indent=2)}]}
    
    async def _get_typography_tokens(self) -> Dict[str, Any]:
        """Get typography tokens."""
        context = await self._get_project_context()
        typography = context.get("design_tokens", {}).get("typography", [])
        return {"contents": [{"type": "text", "text": json.dumps(typography, indent=2)}]}
    
    async def _get_component_patterns(self) -> Dict[str, Any]:
        """Get component patterns."""
        patterns = await self._analyze_component_patterns()
        return {"contents": [{"type": "text", "text": json.dumps(patterns, indent=2)}]}
    
    async def _get_library_info(self) -> Dict[str, Any]:
        """Get library info."""
        info = await self._get_component_library_info()
        return {"contents": [{"type": "text", "text": json.dumps(info, indent=2)}]}
    
    async def _get_tailwind_config(self) -> Dict[str, Any]:
        """Get Tailwind config."""
        context = await self._get_project_context()
        return {"contents": [{"type": "text", "text": json.dumps(context, indent=2)}]}
    
    # Helper methods
    
    def _convert_tokens_to_css(self, tokens: Dict[str, Any]) -> str:
        """Convert tokens to CSS custom properties."""
        css_lines = [":root {"]
        
        for category, values in tokens.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    css_lines.append(f"  --{category}-{key}: {value};")
            elif isinstance(values, list):
                for i, value in enumerate(values):
                    css_lines.append(f"  --{category}-{i}: {value};")
        
        css_lines.append("}")
        return "\n".join(css_lines)
    
    def _convert_tokens_to_tailwind(self, tokens: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tokens to Tailwind config format."""
        tailwind_config = {"theme": {"extend": {}}}
        
        for category, values in tokens.items():
            if category == "colors" and isinstance(values, dict):
                tailwind_config["theme"]["extend"]["colors"] = values
            elif category == "spacing" and isinstance(values, list):
                spacing_dict = {str(i): value for i, value in enumerate(values)}
                tailwind_config["theme"]["extend"]["spacing"] = spacing_dict
            elif category == "typography" and isinstance(values, list):
                font_sizes = {f"size-{i}": value for i, value in enumerate(values)}
                tailwind_config["theme"]["extend"]["fontSize"] = font_sizes
        
        return tailwind_config
    
    def _validate_color_usage(self, code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate color usage against design tokens."""
        issues = []
        design_tokens = context.get("design_tokens", {})
        available_colors = design_tokens.get("colors", {}).get("custom", [])
        
        # Extract color classes from code
        import re
        color_pattern = r'(bg|text|border)-(\w+)-?\d*'
        color_matches = re.findall(color_pattern, code)
        
        for prefix, color in color_matches:
            if color not in available_colors and color not in ['white', 'black', 'gray']:
                issues.append({
                    "type": "warning",
                    "category": "color_usage",
                    "message": f"Color '{color}' not in design system",
                    "suggestion": f"Use one of: {', '.join(available_colors[:5])}"
                })
        
        return issues
    
    def _validate_spacing_consistency(self, code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate spacing consistency."""
        issues = []
        design_tokens = context.get("design_tokens", {})
        spacing_scale = design_tokens.get("spacing", [])
        
        # Extract spacing classes
        import re
        spacing_pattern = r'(m|p)[a-z]*-(\d+)'
        spacing_matches = re.findall(spacing_pattern, code)
        
        for prefix, value in spacing_matches:
            if value not in [str(s) for s in spacing_scale]:
                issues.append({
                    "type": "info",
                    "category": "spacing_consistency",
                    "message": f"Spacing value '{value}' not in design scale",
                    "suggestion": f"Consider using: {', '.join(str(s) for s in spacing_scale[:5])}"
                })
        
        return issues
    
    def _validate_typography_scale(self, code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate typography scale usage."""
        issues = []
        design_tokens = context.get("design_tokens", {})
        typography_scale = design_tokens.get("typography", [])
        
        # Extract text size classes
        import re
        text_pattern = r'text-(\w+)'
        text_matches = re.findall(text_pattern, code)
        
        for size in text_matches:
            if size not in typography_scale and size not in ['xs', 'sm', 'base', 'lg', 'xl']:
                issues.append({
                    "type": "info",
                    "category": "typography_scale",
                    "message": f"Text size '{size}' not in typography scale",
                    "suggestion": f"Use standard sizes: {', '.join(typography_scale[:5])}"
                })
        
        return issues
    
    def _validate_component_structure(self, code: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate component structure."""
        issues = []
        
        # Check for basic React patterns
        if "export default" not in code and "export {" not in code:
            issues.append({
                "type": "error",
                "category": "component_structure",
                "message": "Component should be exported",
                "suggestion": "Add 'export default ComponentName' or named export"
            })
        
        # Check for TypeScript interfaces
        if context.get("typescript", True) and "interface" not in code and "type" not in code:
            issues.append({
                "type": "warning",
                "category": "component_structure",
                "message": "Consider adding TypeScript interface for props",
                "suggestion": "Define props interface for better type safety"
            })
        
        return issues
    
    def _validate_accessibility_basics(self, code: str) -> List[Dict[str, Any]]:
        """Validate basic accessibility."""
        issues = []
        
        # Check for alt text on images
        if '<img' in code and 'alt=' not in code:
            issues.append({
                "type": "error",
                "category": "accessibility",
                "message": "Images must have alt text",
                "suggestion": "Add alt attribute to all img elements"
            })
        
        # Check for button accessibility
        if '<button' in code:
            # Check if button has content or aria-label
            import re
            button_pattern = r'<button[^>]*>(.*?)</button>'
            buttons = re.findall(button_pattern, code, re.DOTALL)
            for button_content in buttons:
                if not button_content.strip() and 'aria-label' not in code:
                    issues.append({
                        "type": "error",
                        "category": "accessibility",
                        "message": "Buttons must have accessible text",
                        "suggestion": "Add text content or aria-label to button"
                    })
        
        return issues
    
    def _generate_improvement_suggestions(
        self, 
        issues: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement suggestions based on issues."""
        suggestions = []
        
        # Group issues by category
        issue_categories = {}
        for issue in issues:
            category = issue.get("category", "general")
            if category not in issue_categories:
                issue_categories[category] = []
            issue_categories[category].append(issue)
        
        # Generate category-specific suggestions
        for category, category_issues in issue_categories.items():
            if category == "color_usage":
                suggestions.append(f"Review color usage - {len(category_issues)} non-standard colors found")
            elif category == "spacing_consistency":
                suggestions.append(f"Consider using design system spacing scale for {len(category_issues)} instances")
            elif category == "accessibility":
                suggestions.append(f"Address {len(category_issues)} accessibility issues for WCAG compliance")
        
        return suggestions
    
    def _calculate_similarity(self, description: str, content: str) -> float:
        """Calculate similarity between description and content."""
        description_words = set(description.lower().split())
        content_words = set(content.lower().split())
        
        # Simple Jaccard similarity
        intersection = description_words.intersection(content_words)
        union = description_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_prop_patterns(self, content: str) -> List[str]:
        """Extract prop patterns from component code."""
        patterns = []
        
        # Look for interface definitions
        import re
        interface_pattern = r'interface\s+\w+Props\s*{([^}]+)}'
        interfaces = re.findall(interface_pattern, content, re.DOTALL)
        
        for interface in interfaces:
            # Extract prop names and types
            prop_pattern = r'(\w+)\??:\s*([^;]+);'
            props = re.findall(prop_pattern, interface)
            for prop_name, prop_type in props:
                patterns.append(f"{prop_name}: {prop_type.strip()}")
        
        return patterns
    
    def _extract_state_patterns(self, content: str) -> List[str]:
        """Extract state management patterns."""
        patterns = []
        
        if "useState" in content:
            patterns.append("useState hook")
        if "useReducer" in content:
            patterns.append("useReducer hook")
        if "useContext" in content:
            patterns.append("Context API")
        if "useEffect" in content:
            patterns.append("useEffect hook")
        
        return patterns
    
    def _extract_styling_patterns(self, content: str) -> List[str]:
        """Extract styling patterns."""
        patterns = []
        
        if "className=" in content:
            patterns.append("CSS classes")
        if "styled." in content:
            patterns.append("styled-components")
        if "css`" in content:
            patterns.append("CSS-in-JS")
        if "style={{" in content:
            patterns.append("inline styles")
        
        return patterns
    
    def _extract_structure_patterns(self, content: str) -> List[str]:
        """Extract component structure patterns."""
        patterns = []
        
        if "function" in content and "return" in content:
            patterns.append("functional component")
        if "class" in content and "extends Component" in content:
            patterns.append("class component")
        if "forwardRef" in content:
            patterns.append("forwardRef pattern")
        if "memo" in content:
            patterns.append("React.memo optimization")
        
        return patterns
    
    def _get_shadcn_examples(self) -> Dict[str, str]:
        """Get shadcn/ui usage examples."""
        return {
            "button": 'import { Button } from "@/components/ui/button"\n\n<Button variant="default">Click me</Button>',
            "card": 'import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"\n\n<Card>\n  <CardHeader>\n    <CardTitle>Title</CardTitle>\n  </CardHeader>\n  <CardContent>Content</CardContent>\n</Card>',
            "input": 'import { Input } from "@/components/ui/input"\n\n<Input placeholder="Enter text..." />'
        }
    
    def _get_accessibility_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get accessibility improvement suggestions."""
        suggestions = []
        
        if '<button' in code:
            suggestions.append({
                "category": "accessibility",
                "suggestion": "Add keyboard navigation support with proper focus management",
                "priority": "high"
            })
        
        if '<form' in code:
            suggestions.append({
                "category": "accessibility",
                "suggestion": "Ensure all form inputs have associated labels",
                "priority": "high"
            })
        
        return suggestions
    
    def _get_performance_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get performance improvement suggestions."""
        suggestions = []
        
        if "useState" in code and "useCallback" not in code:
            suggestions.append({
                "category": "performance",
                "suggestion": "Consider using useCallback for event handlers to prevent unnecessary re-renders",
                "priority": "medium"
            })
        
        if "map(" in code and "key=" not in code:
            suggestions.append({
                "category": "performance",
                "suggestion": "Add proper key props to list items for efficient re-rendering",
                "priority": "high"
            })
        
        return suggestions
    
    def _get_consistency_suggestions(
        self, 
        code: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get consistency improvement suggestions."""
        suggestions = []
        
        component_lib = context.get("component_library", "none")
        
        if component_lib == "shadcn/ui" and "@/components/ui/" not in code:
            suggestions.append({
                "category": "consistency",
                "suggestion": "Use shadcn/ui components for consistency with the design system",
                "priority": "medium"
            })
        
        return suggestions
    
    def _get_maintainability_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get maintainability improvement suggestions."""
        suggestions = []
        
        # Check component size
        lines = len(code.split('\n'))
        if lines > 200:
            suggestions.append({
                "category": "maintainability",
                "suggestion": f"Component is {lines} lines long. Consider breaking it into smaller components",
                "priority": "medium"
            })
        
        # Check for prop drilling
        if code.count("props.") > 10:
            suggestions.append({
                "category": "maintainability",
                "suggestion": "Consider using context or composition to avoid prop drilling",
                "priority": "low"
            })
        
        return suggestions


async def main():
    """Main server loop."""
    parser = argparse.ArgumentParser(description="Design System MCP Server")
    parser.add_argument("--project", default=".", help="Project path to analyze")
    args = parser.parse_args()
    
    server = DesignSystemMCPServer(args.project)
    
    # Initialize
    init_result = await server.initialize()
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": init_result
    }))
    
    # Main message loop
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                message = json.loads(line.strip())
                response = {"jsonrpc": "2.0", "id": message.get("id")}
                
                method = message.get("method")
                params = message.get("params", {})
                
                if method == "tools/list":
                    result = await server.list_tools()
                elif method == "resources/list":
                    result = await server.list_resources()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await server.call_tool(tool_name, arguments)
                elif method == "resources/read":
                    uri = params.get("uri")
                    result = await server.read_resource(uri)
                else:
                    result = {"error": f"Unknown method: {method}"}
                
                response["result"] = result
                print(json.dumps(response))
                
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response))
                
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())