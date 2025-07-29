#!/usr/bin/env python3
"""
Design System Enforcer MCP Server for Palette.
Ensures generated code matches project design system and standards.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from palette.analysis.context import ProjectAnalyzer
from palette.utils.file_manager import FileManager


class DesignEnforcerMCPServer:
    """MCP Server for enforcing design system consistency."""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.analyzer = ProjectAnalyzer()
        self.file_manager = FileManager()
        
        # Cache project analysis
        self._project_context = None
        self._design_tokens = None
        self._component_patterns = None
        
    def _load_project_context(self):
        """Load and cache project context."""
        if not self._project_context:
            self._project_context = self.analyzer.analyze_project(str(self.project_path))
            self._extract_design_tokens()
            self._analyze_component_patterns()
    
    def _extract_design_tokens(self):
        """Extract design tokens from the project."""
        self._design_tokens = {
            "colors": {},
            "spacing": {},
            "typography": {},
            "shadows": {},
            "breakpoints": {}
        }
        
        # Check for Tailwind config
        tailwind_config = self.project_path / "tailwind.config.js"
        if tailwind_config.exists():
            self._parse_tailwind_config(tailwind_config)
        
        # Check for CSS variables
        css_files = list(self.project_path.glob("**/*.css"))
        for css_file in css_files[:5]:  # Limit to first 5 files
            self._extract_css_variables(css_file)
        
        # Check for theme files
        theme_files = list(self.project_path.glob("**/theme.*"))
        for theme_file in theme_files:
            self._extract_theme_tokens(theme_file)
    
    def _analyze_component_patterns(self):
        """Analyze existing component patterns."""
        self._component_patterns = {
            "naming_conventions": {},
            "file_structure": {},
            "prop_patterns": {},
            "state_patterns": {},
            "styling_patterns": {}
        }
        
        # Analyze component files
        component_files = list(self.project_path.glob("**/components/**/*.{jsx,tsx}"))
        for comp_file in component_files[:10]:  # Analyze first 10 components
            self._analyze_component_file(comp_file)
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the server and return capabilities."""
        return {
            "protocol_version": "0.1.0",
            "server_info": {
                "name": "design-enforcer",
                "version": "1.0.0",
                "description": "Enforces design system consistency in generated components"
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
                    "name": "validate_component",
                    "description": "Validate component against project design system",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Component code to validate"
                            },
                            "component_type": {
                                "type": "string",
                                "description": "Type of component (button, form, modal, etc.)",
                                "optional": True
                            },
                            "strict": {
                                "type": "boolean",
                                "description": "Enable strict validation",
                                "default": False
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "suggest_tokens",
                    "description": "Suggest design tokens for specific use cases",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "use_case": {
                                "type": "string",
                                "description": "What tokens are needed for (colors, spacing, etc.)"
                            },
                            "context": {
                                "type": "string",
                                "description": "Context of usage (button, heading, etc.)",
                                "optional": True
                            }
                        },
                        "required": ["use_case"]
                    }
                },
                {
                    "name": "check_consistency",
                    "description": "Check naming and structure consistency",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code to check"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Intended file path for the component",
                                "optional": True
                            }
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "generate_variants",
                    "description": "Generate component variants based on design system",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "base_component": {
                                "type": "string",
                                "description": "Base component code"
                            },
                            "variant_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of variants to generate (size, color, etc.)"
                            }
                        },
                        "required": ["base_component", "variant_types"]
                    }
                },
                {
                    "name": "export_to_storybook",
                    "description": "Generate Storybook stories for component",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component_code": {
                                "type": "string",
                                "description": "Component code"
                            },
                            "component_name": {
                                "type": "string",
                                "description": "Component name"
                            },
                            "props": {
                                "type": "object",
                                "description": "Component props definition",
                                "optional": True
                            }
                        },
                        "required": ["component_code", "component_name"]
                    }
                },
                {
                    "name": "get_design_system",
                    "description": "Get the current project's design system configuration",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Category to retrieve (colors, spacing, all)",
                                "default": "all"
                            }
                        }
                    }
                },
                {
                    "name": "enforce_styling",
                    "description": "Enforce consistent styling approach",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Code with styling to enforce"
                            },
                            "preferred_approach": {
                                "type": "string",
                                "description": "Override detected approach (tailwind, css-modules, styled)",
                                "optional": True
                            }
                        },
                        "required": ["code"]
                    }
                }
            ]
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        # Ensure project context is loaded
        self._load_project_context()
        
        try:
            if tool_name == "validate_component":
                return await self._validate_component(
                    arguments["code"],
                    arguments.get("component_type"),
                    arguments.get("strict", False)
                )
            elif tool_name == "suggest_tokens":
                return await self._suggest_tokens(
                    arguments["use_case"],
                    arguments.get("context")
                )
            elif tool_name == "check_consistency":
                return await self._check_consistency(
                    arguments["code"],
                    arguments.get("file_path")
                )
            elif tool_name == "generate_variants":
                return await self._generate_variants(
                    arguments["base_component"],
                    arguments["variant_types"]
                )
            elif tool_name == "export_to_storybook":
                return await self._export_to_storybook(
                    arguments["component_code"],
                    arguments["component_name"],
                    arguments.get("props", {})
                )
            elif tool_name == "get_design_system":
                return await self._get_design_system(
                    arguments.get("category", "all")
                )
            elif tool_name == "enforce_styling":
                return await self._enforce_styling(
                    arguments["code"],
                    arguments.get("preferred_approach")
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}
    
    async def _validate_component(
        self,
        code: str,
        component_type: Optional[str],
        strict: bool
    ) -> Dict[str, Any]:
        """Validate component against design system."""
        validation_result = {
            "valid": True,
            "violations": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check color usage
        color_violations = self._check_color_usage(code)
        validation_result["violations"].extend(color_violations)
        
        # Check spacing
        spacing_issues = self._check_spacing_usage(code)
        validation_result["warnings"].extend(spacing_issues)
        
        # Check typography
        typography_issues = self._check_typography_usage(code)
        validation_result["warnings"].extend(typography_issues)
        
        # Check component structure
        structure_issues = self._check_component_structure(code, component_type)
        validation_result["violations"].extend(structure_issues)
        
        # Generate suggestions
        suggestions = self._generate_design_suggestions(code, validation_result)
        validation_result["suggestions"] = suggestions
        
        # Update validity
        validation_result["valid"] = len(validation_result["violations"]) == 0
        
        return validation_result
    
    async def _suggest_tokens(
        self,
        use_case: str,
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Suggest appropriate design tokens."""
        suggestions = {
            "tokens": {},
            "examples": [],
            "best_practices": []
        }
        
        if use_case == "colors":
            suggestions["tokens"] = self._get_color_tokens(context)
            suggestions["examples"] = [
                "bg-primary hover:bg-primary-dark",
                "text-gray-700 dark:text-gray-300",
                "border-gray-200"
            ]
            suggestions["best_practices"] = [
                "Use semantic color names",
                "Consider dark mode variants",
                "Ensure proper contrast ratios"
            ]
        
        elif use_case == "spacing":
            suggestions["tokens"] = self._get_spacing_tokens(context)
            suggestions["examples"] = [
                "p-4 md:p-6 lg:p-8",
                "space-y-4",
                "gap-2"
            ]
            suggestions["best_practices"] = [
                "Use consistent spacing scale",
                "Consider responsive spacing",
                "Use logical properties"
            ]
        
        elif use_case == "typography":
            suggestions["tokens"] = self._get_typography_tokens(context)
            suggestions["examples"] = [
                "text-base font-medium",
                "text-2xl font-bold",
                "leading-relaxed"
            ]
            
        return suggestions
    
    async def _check_consistency(
        self,
        code: str,
        file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Check naming and structure consistency."""
        consistency_report = {
            "consistent": True,
            "issues": [],
            "recommendations": []
        }
        
        # Extract component name
        component_name = self._extract_component_name(code)
        
        # Check naming convention
        naming_issues = self._check_naming_convention(component_name, file_path)
        consistency_report["issues"].extend(naming_issues)
        
        # Check file structure
        if file_path:
            structure_issues = self._check_file_structure(file_path, component_name)
            consistency_report["issues"].extend(structure_issues)
        
        # Check prop naming
        prop_issues = self._check_prop_naming(code)
        consistency_report["issues"].extend(prop_issues)
        
        # Generate recommendations
        recommendations = self._generate_consistency_recommendations(
            code, consistency_report["issues"]
        )
        consistency_report["recommendations"] = recommendations
        
        consistency_report["consistent"] = len(consistency_report["issues"]) == 0
        
        return consistency_report
    
    async def _generate_variants(
        self,
        base_component: str,
        variant_types: List[str]
    ) -> Dict[str, Any]:
        """Generate component variants."""
        variants = {
            "base": base_component,
            "variants": {}
        }
        
        for variant_type in variant_types:
            if variant_type == "size":
                variants["variants"]["sizes"] = self._generate_size_variants(base_component)
            elif variant_type == "color":
                variants["variants"]["colors"] = self._generate_color_variants(base_component)
            elif variant_type == "state":
                variants["variants"]["states"] = self._generate_state_variants(base_component)
        
        return variants
    
    async def _export_to_storybook(
        self,
        component_code: str,
        component_name: str,
        props: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Storybook stories."""
        story = {
            "default": self._generate_default_story(component_name, props),
            "stories": [],
            "args": self._extract_story_args(props),
            "argTypes": self._generate_arg_types(props)
        }
        
        # Generate variant stories
        if "variant" in props:
            story["stories"].extend(self._generate_variant_stories(component_name, props))
        
        # Generate state stories
        story["stories"].extend(self._generate_state_stories(component_name, props))
        
        return {
            "component_name": component_name,
            "story_code": self._format_storybook_code(story),
            "file_name": f"{component_name}.stories.tsx"
        }
    
    async def _get_design_system(
        self,
        category: str
    ) -> Dict[str, Any]:
        """Get design system configuration."""
        if category == "all":
            return {
                "colors": self._design_tokens.get("colors", {}),
                "spacing": self._design_tokens.get("spacing", {}),
                "typography": self._design_tokens.get("typography", {}),
                "shadows": self._design_tokens.get("shadows", {}),
                "breakpoints": self._design_tokens.get("breakpoints", {}),
                "patterns": self._component_patterns
            }
        elif category in self._design_tokens:
            return {
                category: self._design_tokens[category]
            }
        else:
            return {"error": f"Unknown category: {category}"}
    
    async def _enforce_styling(
        self,
        code: str,
        preferred_approach: Optional[str]
    ) -> Dict[str, Any]:
        """Enforce consistent styling approach."""
        # Detect current styling approach
        current_approach = self._detect_styling_approach(code)
        
        # Use project default if no preference given
        if not preferred_approach:
            preferred_approach = self._project_context.get("styling_approach", "tailwind")
        
        # Convert styling if needed
        if current_approach != preferred_approach:
            converted_code = self._convert_styling(code, current_approach, preferred_approach)
            return {
                "original_approach": current_approach,
                "target_approach": preferred_approach,
                "converted_code": converted_code,
                "changes_made": True
            }
        
        return {
            "approach": current_approach,
            "code": code,
            "changes_made": False
        }
    
    # Helper methods
    def _parse_tailwind_config(self, config_path: Path):
        """Parse Tailwind configuration."""
        # In a real implementation, would parse the JS file
        # For now, use common defaults
        self._design_tokens["colors"] = {
            "primary": "#3b82f6",
            "secondary": "#8b5cf6",
            "success": "#10b981",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6"
        }
        
        self._design_tokens["spacing"] = {
            "xs": "0.5rem",
            "sm": "0.75rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem",
            "2xl": "3rem"
        }
    
    def _extract_css_variables(self, css_file: Path):
        """Extract CSS custom properties."""
        try:
            content = css_file.read_text()
            # Extract CSS variables
            variables = re.findall(r'--([^:]+):\s*([^;]+);', content)
            for var_name, var_value in variables:
                if "color" in var_name:
                    self._design_tokens["colors"][var_name] = var_value.strip()
                elif "space" in var_name or "spacing" in var_name:
                    self._design_tokens["spacing"][var_name] = var_value.strip()
        except Exception:
            pass
    
    def _extract_theme_tokens(self, theme_file: Path):
        """Extract tokens from theme files."""
        # Implementation would parse theme files
        pass
    
    def _analyze_component_file(self, component_file: Path):
        """Analyze a component file for patterns."""
        try:
            content = component_file.read_text()
            
            # Analyze naming
            component_name = component_file.stem
            if component_name[0].isupper():
                self._component_patterns["naming_conventions"]["components"] = "PascalCase"
            
            # Analyze prop patterns
            if "interface" in content and "Props" in content:
                self._component_patterns["prop_patterns"]["type_system"] = "TypeScript"
            elif "PropTypes" in content:
                self._component_patterns["prop_patterns"]["type_system"] = "PropTypes"
            
            # Analyze styling
            if "className=" in content:
                if "module.css" in content:
                    self._component_patterns["styling_patterns"]["approach"] = "css-modules"
                elif re.search(r'className=["\']\w+-\w+', content):
                    self._component_patterns["styling_patterns"]["approach"] = "tailwind"
                else:
                    self._component_patterns["styling_patterns"]["approach"] = "css-classes"
        except Exception:
            pass
    
    def _check_color_usage(self, code: str) -> List[str]:
        """Check if colors match design tokens."""
        violations = []
        
        # Check for hardcoded colors
        hex_colors = re.findall(r'#[0-9a-fA-F]{3,6}', code)
        rgb_colors = re.findall(r'rgb\([^)]+\)', code)
        
        if hex_colors or rgb_colors:
            violations.append({
                "type": "hardcoded_color",
                "message": "Use design token colors instead of hardcoded values",
                "found": hex_colors + rgb_colors
            })
        
        return violations
    
    def _check_spacing_usage(self, code: str) -> List[str]:
        """Check spacing consistency."""
        warnings = []
        
        # Check for arbitrary spacing values
        arbitrary_spacing = re.findall(r'(?:p|m|gap)-\[[\d.]+(?:px|rem|em)\]', code)
        if arbitrary_spacing:
            warnings.append({
                "type": "arbitrary_spacing",
                "message": "Use design token spacing values",
                "found": arbitrary_spacing
            })
        
        return warnings
    
    def _check_typography_usage(self, code: str) -> List[str]:
        """Check typography consistency."""
        warnings = []
        
        # Check for non-standard font sizes
        custom_sizes = re.findall(r'text-\[[\d.]+(?:px|rem|em)\]', code)
        if custom_sizes:
            warnings.append({
                "type": "custom_font_size",
                "message": "Use typography scale from design system",
                "found": custom_sizes
            })
        
        return warnings
    
    def _check_component_structure(self, code: str, component_type: Optional[str]) -> List[str]:
        """Check component structure consistency."""
        violations = []
        
        # Check for required patterns based on component type
        if component_type == "button" and "<button" not in code:
            violations.append({
                "type": "semantic_html",
                "message": "Buttons should use <button> element"
            })
        
        return violations
    
    def _generate_design_suggestions(
        self,
        code: str,
        validation_result: Dict[str, Any]
    ) -> List[str]:
        """Generate design improvement suggestions."""
        suggestions = []
        
        if validation_result["violations"]:
            suggestions.append("Fix design system violations before proceeding")
        
        if "className" in code and "dark:" not in code:
            suggestions.append("Consider adding dark mode support using dark: prefix")
        
        return suggestions
    
    def _get_color_tokens(self, context: Optional[str]) -> Dict[str, str]:
        """Get color tokens for context."""
        base_colors = self._design_tokens.get("colors", {})
        
        if context == "button":
            return {
                "primary": base_colors.get("primary", "#3b82f6"),
                "secondary": base_colors.get("secondary", "#6b7280"),
                "danger": base_colors.get("danger", "#ef4444")
            }
        
        return base_colors
    
    def _get_spacing_tokens(self, context: Optional[str]) -> Dict[str, str]:
        """Get spacing tokens."""
        return self._design_tokens.get("spacing", {
            "xs": "0.5rem",
            "sm": "0.75rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem"
        })
    
    def _get_typography_tokens(self, context: Optional[str]) -> Dict[str, str]:
        """Get typography tokens."""
        return self._design_tokens.get("typography", {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem",
            "2xl": "1.5rem",
            "3xl": "1.875rem"
        })
    
    def _extract_component_name(self, code: str) -> str:
        """Extract component name from code."""
        match = re.search(r'(?:function|const|class)\s+(\w+)', code)
        return match.group(1) if match else "Unknown"
    
    def _check_naming_convention(self, component_name: str, file_path: Optional[str]) -> List[str]:
        """Check naming convention consistency."""
        issues = []
        
        # Check PascalCase for components
        if not component_name[0].isupper():
            issues.append({
                "type": "naming",
                "message": f"Component '{component_name}' should use PascalCase"
            })
        
        # Check file name matches component
        if file_path:
            file_name = Path(file_path).stem
            if file_name != component_name:
                issues.append({
                    "type": "file_naming",
                    "message": f"File name should match component name: {component_name}"
                })
        
        return issues
    
    def _check_file_structure(self, file_path: str, component_name: str) -> List[str]:
        """Check file structure consistency."""
        issues = []
        
        # Check if in components directory
        if "components" not in file_path.lower():
            issues.append({
                "type": "structure",
                "message": "Components should be in a components directory"
            })
        
        return issues
    
    def _check_prop_naming(self, code: str) -> List[str]:
        """Check prop naming conventions."""
        issues = []
        
        # Check for onClick vs handleClick
        if "onClick={handle" in code:
            issues.append({
                "type": "prop_naming",
                "message": "Consider using onAction format for event handlers"
            })
        
        return issues
    
    def _generate_consistency_recommendations(
        self,
        code: str,
        issues: List[Dict[str, str]]
    ) -> List[str]:
        """Generate consistency recommendations."""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "naming":
                recommendations.append("Refactor component to use PascalCase naming")
            elif issue["type"] == "file_naming":
                recommendations.append("Rename file to match component name")
        
        return recommendations
    
    def _generate_size_variants(self, base_component: str) -> Dict[str, str]:
        """Generate size variants."""
        return {
            "small": base_component.replace("md", "sm"),
            "medium": base_component,
            "large": base_component.replace("md", "lg")
        }
    
    def _generate_color_variants(self, base_component: str) -> Dict[str, str]:
        """Generate color variants."""
        return {
            "primary": base_component,
            "secondary": base_component.replace("primary", "secondary"),
            "danger": base_component.replace("primary", "danger")
        }
    
    def _generate_state_variants(self, base_component: str) -> Dict[str, str]:
        """Generate state variants."""
        return {
            "default": base_component,
            "disabled": base_component.replace(">", " disabled>"),
            "loading": base_component.replace(">", " loading>")
        }
    
    def _generate_default_story(self, component_name: str, props: Dict[str, Any]) -> str:
        """Generate default Storybook story."""
        return f"""
export default {{
  title: 'Components/{component_name}',
  component: {component_name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
}};
"""
    
    def _extract_story_args(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Extract default args for stories."""
        return {
            prop: "default" for prop in props
        }
    
    def _generate_arg_types(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Generate argTypes for Storybook."""
        arg_types = {}
        
        for prop, prop_type in props.items():
            if prop_type == "boolean":
                arg_types[prop] = {"control": "boolean"}
            elif prop_type == "string":
                arg_types[prop] = {"control": "text"}
            elif "enum" in str(prop_type):
                arg_types[prop] = {"control": "select"}
        
        return arg_types
    
    def _generate_variant_stories(self, component_name: str, props: Dict[str, Any]) -> List[str]:
        """Generate variant stories."""
        stories = []
        
        if "variant" in props:
            for variant in ["primary", "secondary", "danger"]:
                stories.append(f"""
export const {variant.title()} = {{
  args: {{
    variant: '{variant}',
  }},
}};
""")
        
        return stories
    
    def _generate_state_stories(self, component_name: str, props: Dict[str, Any]) -> List[str]:
        """Generate state stories."""
        stories = []
        
        if "disabled" in props:
            stories.append("""
export const Disabled = {
  args: {
    disabled: true,
  },
};
""")
        
        if "loading" in props:
            stories.append("""
export const Loading = {
  args: {
    loading: true,
  },
};
""")
        
        return stories
    
    def _format_storybook_code(self, story: Dict[str, Any]) -> str:
        """Format complete Storybook code."""
        code = story["default"]
        
        for story_code in story["stories"]:
            code += "\n" + story_code
        
        return code
    
    def _detect_styling_approach(self, code: str) -> str:
        """Detect the styling approach used."""
        if "styled" in code and "css`" in code:
            return "styled-components"
        elif ".module.css" in code:
            return "css-modules"
        elif re.search(r'className=["\']\w+-\w+', code):
            return "tailwind"
        else:
            return "inline-styles"
    
    def _convert_styling(self, code: str, from_approach: str, to_approach: str) -> str:
        """Convert styling from one approach to another."""
        # This is a simplified version
        if from_approach == "inline-styles" and to_approach == "tailwind":
            # Convert style={{}} to className=""
            code = re.sub(
                r'style=\{\{([^}]+)\}\}',
                lambda m: f'className="{self._style_to_tailwind(m.group(1))}"',
                code
            )
        
        return code
    
    def _style_to_tailwind(self, style_string: str) -> str:
        """Convert inline styles to Tailwind classes."""
        classes = []
        
        # Simple mapping
        if "padding: 1rem" in style_string:
            classes.append("p-4")
        if "margin: 0 auto" in style_string:
            classes.append("mx-auto")
        if "display: flex" in style_string:
            classes.append("flex")
        
        return " ".join(classes)
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources."""
        return {
            "resources": [
                {
                    "uri": "design-enforcer://tokens/colors",
                    "name": "Color Tokens",
                    "description": "Project color design tokens",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-enforcer://tokens/spacing",
                    "name": "Spacing Tokens",
                    "description": "Project spacing design tokens",
                    "mimeType": "application/json"
                },
                {
                    "uri": "design-enforcer://patterns",
                    "name": "Component Patterns",
                    "description": "Detected component patterns",
                    "mimeType": "application/json"
                }
            ]
        }
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        self._load_project_context()
        
        if uri == "design-enforcer://tokens/colors":
            return {
                "contents": self._design_tokens.get("colors", {}),
                "mimeType": "application/json"
            }
        elif uri == "design-enforcer://tokens/spacing":
            return {
                "contents": self._design_tokens.get("spacing", {}),
                "mimeType": "application/json"
            }
        elif uri == "design-enforcer://patterns":
            return {
                "contents": self._component_patterns,
                "mimeType": "application/json"
            }
        
        return {"error": f"Unknown resource: {uri}"}


async def run_stdio_server():
    """Run the MCP server using stdio transport."""
    import mcp
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    
    # Create server instance
    enforcer_server = DesignEnforcerMCPServer()
    server = Server("design-enforcer")
    
    # Register handlers
    @server.list_tools()
    async def list_tools():
        return await enforcer_server.list_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        return await enforcer_server.call_tool(name, arguments)
    
    @server.list_resources()
    async def list_resources():
        return await enforcer_server.list_resources()
    
    @server.read_resource()
    async def read_resource(uri: str):
        return await enforcer_server.read_resource(uri)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, enforcer_server.initialize())


async def test_server():
    """Test the server functionality."""
    server = DesignEnforcerMCPServer()
    
    print("Testing Design Enforcer MCP Server")
    print("=" * 60)
    
    # Test component validation
    test_code = '''
    function Button({ children, onClick, variant = "primary" }) {
        return (
            <button 
                className="px-4 py-2 bg-#3b82f6 text-white rounded"
                onClick={onClick}
            >
                {children}
            </button>
        );
    }
    '''
    
    print("\n1. Testing validate_component")
    result = await server.call_tool("validate_component", {
        "code": test_code,
        "component_type": "button"
    })
    print(f"Validation: {json.dumps(result, indent=2)}")
    
    print("\n2. Testing suggest_tokens")
    result = await server.call_tool("suggest_tokens", {
        "use_case": "colors",
        "context": "button"
    })
    print(f"Token suggestions: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Design Enforcer MCP Server")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--project", type=str, help="Project path to analyze")
    args = parser.parse_args()
    
    if args.project:
        server = DesignEnforcerMCPServer(Path(args.project))
    
    if args.test:
        asyncio.run(test_server())
    else:
        try:
            asyncio.run(run_stdio_server())
        except ImportError:
            print("MCP SDK not installed. Running in test mode.")
            asyncio.run(test_server())