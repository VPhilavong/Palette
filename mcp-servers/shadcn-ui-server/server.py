#!/usr/bin/env python3
"""
Shadcn/UI MCP Server for Beautiful Component Generation

This MCP server specializes in generating beautiful, professional UI components
using shadcn/ui patterns and modern design principles. It acts as a dedicated
design system server that can be consumed by the main Palette system.
"""

import json
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, asdict

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from palette.aesthetics.aesthetic_prompts import AestheticPromptBuilder, DesignStyle, AestheticConfig


@dataclass
class ShadcnComponent:
    """Represents a shadcn/ui component with all its metadata"""
    name: str
    category: str
    description: str
    dependencies: List[str]
    variants: List[str]
    props: Dict[str, Any]
    code_template: str
    css_variables: Dict[str, str]
    animations: List[str]
    accessibility_features: List[str]


class ShadcnUIServer:
    """MCP Server for shadcn/ui component generation"""
    
    def __init__(self):
        self.server = Server("shadcn-ui-server")
        self.aesthetic_builder = AestheticPromptBuilder()
        self.component_registry = self._build_component_registry()
        self.design_tokens = {}
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all MCP tools for shadcn/ui generation"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="generate_shadcn_component",
                    description="Generate a beautiful shadcn/ui component from a description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Natural language description of the component needed"
                            },
                            "component_type": {
                                "type": "string",
                                "description": "Type of component (button, card, form, etc.)",
                                "enum": ["button", "card", "form", "modal", "table", "navigation", "hero", "dashboard", "layout"]
                            },
                            "style": {
                                "type": "string",
                                "description": "Design style preference",
                                "enum": ["modern_minimal", "bold_vibrant", "enterprise", "playful", "glassmorphism"],
                                "default": "modern_minimal"
                            },
                            "size": {
                                "type": "string",
                                "description": "Component size variant",
                                "enum": ["sm", "default", "lg", "xl"],
                                "default": "default"
                            },
                            "with_animations": {
                                "type": "boolean",
                                "description": "Include micro-interactions and animations",
                                "default": True
                            }
                        },
                        "required": ["description", "component_type"]
                    }
                ),
                types.Tool(
                    name="get_component_variants",
                    description="Get all available variants for a shadcn/ui component",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "component_name": {
                                "type": "string",
                                "description": "Name of the shadcn/ui component"
                            }
                        },
                        "required": ["component_name"]
                    }
                ),
                types.Tool(
                    name="compose_component_layout",
                    description="Compose multiple shadcn/ui components into a beautiful layout",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "layout_description": {
                                "type": "string",
                                "description": "Description of the desired layout composition"
                            },
                            "components": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of component types to include"
                            },
                            "responsive": {
                                "type": "boolean",
                                "description": "Make the layout responsive",
                                "default": True
                            }
                        },
                        "required": ["layout_description", "components"]
                    }
                ),
                types.Tool(
                    name="analyze_design_system",
                    description="Analyze a project's design system and suggest shadcn/ui implementation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_path": {
                                "type": "string",
                                "description": "Path to the project to analyze"
                            }
                        },
                        "required": ["project_path"]
                    }
                ),
                types.Tool(
                    name="generate_theme_config",
                    description="Generate shadcn/ui theme configuration based on design requirements",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "brand_colors": {
                                "type": "object",
                                "description": "Brand color palette",
                                "properties": {
                                    "primary": {"type": "string"},
                                    "secondary": {"type": "string"},
                                    "accent": {"type": "string"}
                                }
                            },
                            "style_preference": {
                                "type": "string",
                                "enum": ["modern", "classic", "playful", "enterprise"],
                                "default": "modern"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for shadcn/ui generation"""
            
            if name == "generate_shadcn_component":
                return await self._generate_component(arguments)
            elif name == "get_component_variants":
                return await self._get_component_variants(arguments)
            elif name == "compose_component_layout":
                return await self._compose_layout(arguments)
            elif name == "analyze_design_system":
                return await self._analyze_design_system(arguments)
            elif name == "generate_theme_config":
                return await self._generate_theme_config(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _generate_component(self, args: dict) -> List[types.TextContent]:
        """Generate a beautiful shadcn/ui component"""
        description = args.get("description", "")
        component_type = args.get("component_type", "button")
        style = DesignStyle(args.get("style", "modern_minimal"))
        size = args.get("size", "default")
        with_animations = args.get("with_animations", True)
        
        # Get component template
        component_template = self.component_registry.get(component_type)
        if not component_template:
            return [types.TextContent(type="text", text=f"Component type '{component_type}' not found")]
        
        # Build aesthetic configuration
        config = AestheticConfig(
            style=style,
            enable_animations=with_animations,
            enable_gradients=True,
            shadow_intensity="medium",
            border_radius="medium"
        )
        
        # Generate component code
        component_code = self._build_component_code(
            component_template, 
            description, 
            config, 
            size
        )
        
        # Generate supporting files
        type_definitions = self._generate_type_definitions(component_template)
        css_variables = self._generate_css_variables(component_template, config)
        usage_example = self._generate_usage_example(component_template, size)
        
        result = {
            "component_code": component_code,
            "type_definitions": type_definitions,
            "css_variables": css_variables,
            "usage_example": usage_example,
            "dependencies": component_template.dependencies,
            "animations": component_template.animations if with_animations else [],
            "accessibility_notes": component_template.accessibility_features
        }
        
        return [types.TextContent(
            type="text", 
            text=json.dumps(result, indent=2)
        )]

    async def _get_component_variants(self, args: dict) -> List[types.TextContent]:
        """Get available variants for a component"""
        component_name = args.get("component_name", "")
        component = self.component_registry.get(component_name)
        
        if not component:
            return [types.TextContent(type="text", text=f"Component '{component_name}' not found")]
        
        variants_info = {
            "component": component_name,
            "variants": component.variants,
            "props": component.props,
            "description": component.description,
            "category": component.category
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(variants_info, indent=2)
        )]

    async def _compose_layout(self, args: dict) -> List[types.TextContent]:
        """Compose multiple components into a layout"""
        description = args.get("layout_description", "")
        components = args.get("components", [])
        responsive = args.get("responsive", True)
        
        # Generate layout composition
        layout_code = self._generate_layout_composition(description, components, responsive)
        
        result = {
            "layout_code": layout_code,
            "components_used": components,
            "responsive_features": self._get_responsive_features() if responsive else [],
            "layout_description": description
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    async def _analyze_design_system(self, args: dict) -> List[types.TextContent]:
        """Analyze project's design system for shadcn/ui integration"""
        project_path = args.get("project_path", "")
        
        # Analyze existing design tokens, components, and patterns
        analysis = {
            "existing_components": self._scan_existing_components(project_path),
            "design_tokens": self._extract_design_tokens(project_path),
            "shadcn_recommendations": self._generate_shadcn_recommendations(project_path),
            "migration_plan": self._create_migration_plan(project_path)
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(analysis, indent=2)
        )]

    async def _generate_theme_config(self, args: dict) -> List[types.TextContent]:
        """Generate shadcn/ui theme configuration"""
        brand_colors = args.get("brand_colors", {})
        style_preference = args.get("style_preference", "modern")
        
        theme_config = self._build_theme_config(brand_colors, style_preference)
        
        return [types.TextContent(
            type="text",
            text=json.dumps(theme_config, indent=2)
        )]

    def _build_component_registry(self) -> Dict[str, ShadcnComponent]:
        """Build registry of shadcn/ui components with templates"""
        return {
            "button": ShadcnComponent(
                name="Button",
                category="Form",
                description="A customizable button component with multiple variants",
                dependencies=["@radix-ui/react-slot", "class-variance-authority", "clsx", "tailwind-merge"],
                variants=["default", "destructive", "outline", "secondary", "ghost", "link"],
                props={
                    "variant": "string",
                    "size": "string", 
                    "asChild": "boolean",
                    "disabled": "boolean"
                },
                code_template="""
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
""",
                css_variables={
                    "--primary": "222.2 84% 4.9%",
                    "--primary-foreground": "210 40% 98%",
                    "--secondary": "210 40% 96%",
                    "--secondary-foreground": "222.2 84% 4.9%"
                },
                animations=["hover:scale-105", "active:scale-95", "transition-transform"],
                accessibility_features=["ARIA compliant", "Keyboard navigation", "Focus indicators"]
            ),
            
            "card": ShadcnComponent(
                name="Card",
                category="Layout",
                description="A flexible card component for content display",
                dependencies=["clsx", "tailwind-merge"],
                variants=["default", "elevated", "outlined"],
                props={
                    "className": "string",
                    "children": "ReactNode"
                },
                code_template="""
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
""",
                css_variables={
                    "--card": "0 0% 100%",
                    "--card-foreground": "222.2 84% 4.9%"
                },
                animations=["hover:shadow-lg", "transition-shadow", "duration-300"],
                accessibility_features=["Semantic markup", "Screen reader friendly"]
            )
            
            # Add more components here...
        }

    def _build_component_code(self, template: ShadcnComponent, description: str, config: AestheticConfig, size: str) -> str:
        """Build customized component code based on description and config"""
        # This would use the aesthetic prompt builder to customize the template
        # based on the specific requirements
        
        base_code = template.code_template
        
        # Apply style-specific modifications
        if config.style == DesignStyle.GLASSMORPHISM:
            base_code = self._apply_glassmorphism_styles(base_code)
        elif config.style == DesignStyle.BOLD_VIBRANT:
            base_code = self._apply_vibrant_styles(base_code)
        
        # Add animations if enabled
        if config.enable_animations:
            base_code = self._add_animations(base_code, template.animations)
        
        return base_code

    def _apply_glassmorphism_styles(self, code: str) -> str:
        """Apply glassmorphism styling to component code"""
        # Replace background classes with glass effects
        code = code.replace(
            "bg-card", 
            "backdrop-blur-md bg-white/30 dark:bg-gray-900/30 border border-white/20"
        )
        return code

    def _apply_vibrant_styles(self, code: str) -> str:
        """Apply bold, vibrant styling to component code"""
        # Add gradient backgrounds and stronger shadows
        code = code.replace(
            "bg-primary", 
            "bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
        )
        code = code.replace("shadow-sm", "shadow-lg shadow-blue-500/25")
        return code

    def _add_animations(self, code: str, animations: List[str]) -> str:
        """Add animation classes to component code"""
        for animation in animations:
            # Insert animations into className strings
            code = code.replace(
                'className={cn(',
                f'className={{cn("{"}" ".join(animations)}", '
            )
        return code

    def _generate_type_definitions(self, template: ShadcnComponent) -> str:
        """Generate TypeScript type definitions"""
        return f"// {template.name} Types\n// Props: {json.dumps(template.props, indent=2)}"

    def _generate_css_variables(self, template: ShadcnComponent, config: AestheticConfig) -> Dict[str, str]:
        """Generate CSS variables for theming"""
        variables = template.css_variables.copy()
        
        # Modify based on style config
        if config.style == DesignStyle.DARK_ELEGANT:
            variables.update({
                "--background": "222.2 84% 4.9%",
                "--foreground": "210 40% 98%"
            })
        
        return variables

    def _generate_usage_example(self, template: ShadcnComponent, size: str) -> str:
        """Generate usage example for the component"""
        return f"""
// Usage Example for {template.name}
import {{ {template.name} }} from "@/components/ui/{template.name.lower()}"

export function Example() {{
  return (
    <{template.name} size="{size}" variant="default">
      Click me
    </{template.name}>
  )
}}
"""

    def _generate_layout_composition(self, description: str, components: List[str], responsive: bool) -> str:
        """Generate layout composition code"""
        # This would use advanced composition logic to arrange components beautifully
        layout_classes = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" if responsive else "flex flex-col gap-4"
        
        component_imports = "\n".join([f'import {{ {comp.capitalize()} }} from "@/components/ui/{comp}"' for comp in components])
        
        return f"""
{component_imports}

export function ComposedLayout() {{
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="{layout_classes}">
        {chr(10).join([f'        <{comp.capitalize()} />' for comp in components])}
      </div>
    </div>
  )
}}
"""

    def _get_responsive_features(self) -> List[str]:
        """Get responsive design features"""
        return [
            "Mobile-first approach",
            "Flexible grid system",
            "Responsive typography",
            "Touch-friendly interactions",
            "Optimized for all screen sizes"
        ]

    def _scan_existing_components(self, project_path: str) -> List[str]:
        """Scan for existing components in the project"""
        # Implementation would scan the project structure
        return ["Button", "Card", "Modal"]  # Placeholder

    def _extract_design_tokens(self, project_path: str) -> Dict[str, Any]:
        """Extract design tokens from the project"""
        # Implementation would analyze CSS variables, Tailwind config, etc.
        return {
            "colors": {"primary": "blue-500", "secondary": "gray-500"},
            "spacing": [4, 8, 16, 24, 32],
            "typography": ["text-sm", "text-base", "text-lg"]
        }

    def _generate_shadcn_recommendations(self, project_path: str) -> List[str]:
        """Generate recommendations for shadcn/ui adoption"""
        return [
            "Replace custom Button with shadcn/ui Button component",
            "Standardize Card layouts using shadcn/ui Card",
            "Implement consistent form validation with shadcn/ui Form"
        ]

    def _create_migration_plan(self, project_path: str) -> Dict[str, Any]:
        """Create migration plan to shadcn/ui"""
        return {
            "phase1": ["Install shadcn/ui", "Set up theme configuration"],
            "phase2": ["Migrate core components", "Update existing usage"],
            "phase3": ["Add new components", "Optimize and refine"]
        }

    def _build_theme_config(self, brand_colors: Dict[str, str], style: str) -> Dict[str, Any]:
        """Build shadcn/ui theme configuration"""
        return {
            "tailwind_config": {
                "extend": {
                    "colors": {
                        "primary": brand_colors.get("primary", "hsl(222.2 84% 4.9%)"),
                        "secondary": brand_colors.get("secondary", "hsl(210 40% 96%)")
                    }
                }
            },
            "css_variables": {
                "--primary": "222.2 84% 4.9%",
                "--secondary": "210 40% 96%"
            }
        }


async def main():
    """Run the shadcn/ui MCP server"""
    server_instance = ShadcnUIServer()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="shadcn-ui-server",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())