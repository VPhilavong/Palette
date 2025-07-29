# Enhanced CLI for UI/UX Copilot
# Supports multi-file generation, editing, and multiple frameworks/libraries

import os
import sys
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from ..generation.generator import UIGenerator
from ..generation.prompts import (
    GenerationRequest,
    FrameworkType,
    StylingLibrary,
    ComponentLibrary,
    GenerationType,
    create_generation_request
)

# Try to import knowledge-enhanced generator
try:
    from ..generation.knowledge_generator import KnowledgeUIGenerator
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False

# Try to import enhanced generator (legacy, now disabled)
try:
    from ..generation.enhanced_generator import EnhancedUIGenerator
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

console = Console()


@click.group()
@click.version_option(version="2.0.0")
def main():
    """UI/UX Copilot - AI-powered UI/UX code generation for modern web frameworks"""
    pass


@main.command()
@click.argument("prompt", required=True)
@click.option("--type", "-t", 
              type=click.Choice(['single', 'multi', 'page', 'feature', 'hooks', 'utils', 'context', 'store']),
              help="Generation type")
@click.option("--framework", "-f",
              type=click.Choice(['react', 'next.js', 'remix', 'vite']),
              help="Framework to use")
@click.option("--styling", "-s",
              type=click.Choice(['tailwind', 'styled-components', 'emotion', 'css-modules', 'sass', 'css', 'panda-css']),
              help="Styling library")
@click.option("--ui", "-u",
              type=click.Choice(['none', 'shadcn/ui', 'material-ui', 'chakra-ui', 'ant-design', 'headless-ui']),
              default='none',
              help="UI component library")
@click.option("--output", "-o", help="Output directory (auto-detected if not provided)")
@click.option("--preview", is_flag=True, help="Preview before creating files")
@click.option("--no-tests", is_flag=True, help="Skip test file generation")
@click.option("--storybook", is_flag=True, help="Include Storybook stories")
@click.option("--basic-mode", is_flag=True, help="Disable zero-fix validation (basic generation only)")
def generate(prompt: str, type: Optional[str], framework: Optional[str], 
             styling: Optional[str], ui: str, output: Optional[str],
             preview: bool, no_tests: bool, storybook: bool, basic_mode: bool):
    """Generate UI/UX code from natural language prompts"""
    
    console.print(Panel(
        f"[bold blue]🎨 UI/UX Copilot[/bold blue]\n{prompt}",
        title="Generating",
        border_style="blue",
    ))
    
    try:
        # Default output to current directory if not specified
        if output is None:
            output = "."
        
        # Initialize generator with zero-fix validation enabled by default
        # Use enhanced generator if available and MCP servers exist
        # Check both current directory and Palette installation directory
        palette_dir = Path(__file__).parent.parent.parent.parent  # Go up to Palette root
        mcp_in_cwd = Path("mcp-servers").exists()
        mcp_in_palette = (palette_dir / "mcp-servers").exists()
        
        # Use Knowledge-enhanced generator if available
        if KNOWLEDGE_AVAILABLE:
            generator = KnowledgeUIGenerator(project_path=output, quality_assurance=True)
            console.print("[green]🧠 Using Knowledge-Enhanced Generator[/green]")
        else:
            generator = UIGenerator(project_path=output, quality_assurance=True)
            console.print("[blue]🎨 Using Standard Generator with Enhanced Analysis[/blue]")
        
        # Legacy MCP integration (temporarily disabled)
        # TODO: Remove after confirming knowledge base works well
        # if ENHANCED_AVAILABLE and (mcp_in_cwd or mcp_in_palette):
        #     generator = EnhancedUIGenerator(project_path=output, quality_assurance=True)
        #     console.print("[green]✨ Using Enhanced Generator with Professional MCP[/green]")
        #     if mcp_in_palette and not mcp_in_cwd:
        #         console.print(f"[dim]   MCP servers loaded from: {palette_dir / 'mcp-servers'}[/dim]")
        
        # Auto-detect settings from project if not specified
        if not framework:
            framework = generator.project_context.get('framework', 'react')
        if not styling:
            styling = generator.project_context.get('styling', 'tailwind')
        if not type:
            type = generator._detect_generation_type(prompt)
        
        # Show detected/selected configuration
        _show_configuration(framework, styling, ui, type)
        
        # Create generation request
        request = create_generation_request(
            prompt=prompt,
            framework=framework,
            styling=styling,
            component_library=ui,
            generation_type=type
        )
        request.include_tests = not no_tests
        request.include_storybook = storybook
        
        # Enable zero-fix validation by default, disable only in basic mode
        if basic_mode:
            generator.quality_assurance = False
            generator.validator = None
        
        # Generate files
        files = generator.generate(request)
        
        if preview:
            _preview_files(files)
            if not click.confirm("\nCreate these files?"):
                console.print("[yellow]Generation cancelled[/yellow]")
                return
        
        # Save files
        saved_files = _save_files(files, output)
        
        # Show summary
        _show_summary(saved_files)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.argument("file_path", required=True)
@click.argument("prompt", required=True)
@click.option("--mode", "-m",
              type=click.Choice(['add', 'modify', 'refactor', 'enhance']),
              default='modify',
              help="Edit mode")
@click.option("--preview", is_flag=True, help="Preview changes before applying")
def edit(file_path: str, prompt: str, mode: str, preview: bool):
    """Edit existing files with AI assistance"""
    
    console.print(Panel(
        f"[bold yellow]✏️ Editing File[/bold yellow]\n{file_path}\n\n{prompt}",
        title="Edit Mode",
        border_style="yellow",
    ))
    
    try:
        generator = UIGenerator()
        
        # Edit the file
        files = generator.edit_file(file_path, prompt, edit_mode=mode)
        
        if preview:
            _preview_files(files)
            if not click.confirm("\nApply these changes?"):
                console.print("[yellow]Edit cancelled[/yellow]")
                return
        
        # Save changes
        saved_files = _save_files(files)
        _show_summary(saved_files)
        
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
def analyze():
    """Analyze project structure and patterns"""
    
    console.print(Panel(
        "[bold blue]📊 Project Analysis[/bold blue]",
        title="Analyzing",
        border_style="blue",
    ))
    
    try:
        generator = UIGenerator()
        context = generator.project_context
        
        # Display analysis results
        table = Table(title="Project Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Framework", context.get('framework', 'Unknown'))
        table.add_row("Styling", context.get('styling', 'Unknown'))
        table.add_row("Component Library", context.get('component_library', 'None'))
        table.add_row("TypeScript", "Yes" if context.get('typescript', True) else "No")
        
        console.print(table)
        
        # File structure
        structure = context.get('file_structure', {})
        if structure:
            struct_table = Table(title="File Structure")
            struct_table.add_column("Pattern", style="cyan")
            struct_table.add_column("Value", style="green")
            
            struct_table.add_row("Component Pattern", structure.get('component_pattern', 'Unknown'))
            struct_table.add_row("Test Pattern", structure.get('test_pattern', 'Unknown'))
            struct_table.add_row("Has App Directory", "Yes" if structure.get('has_app_dir') else "No")
            
            console.print(struct_table)
        
        # Design tokens
        tokens = context.get('design_tokens', {})
        if tokens:
            console.print("\n[bold]Design Tokens:[/bold]")
            if tokens.get('colors'):
                colors = tokens['colors'][:8] if isinstance(tokens['colors'], list) else list(tokens['colors'].keys())[:8]
                console.print(f"Colors: {', '.join(colors)}")
            if tokens.get('spacing'):
                spacing = tokens['spacing'][:8] if isinstance(tokens['spacing'], list) else list(tokens['spacing'].keys())[:8]
                console.print(f"Spacing: {', '.join(str(s) for s in spacing)}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.option("--type", help="Framework type (react, nextjs, vue)")
@click.option("--styling", help="Styling library (tailwind, css)")
@click.option("--ui-lib", help="UI library (shadcn, none)")
@click.option("--components", is_flag=True, help="Include component templates")
@click.option("--utils", is_flag=True, help="Include utility templates")
@click.option("--wireframe", help="Path to SVG wireframe file")
@click.option("--wireframe-prompt", help="Description of what to build from wireframe")
def init(type: Optional[str], styling: Optional[str], ui_lib: Optional[str], components: bool, utils: bool, wireframe: Optional[str], wireframe_prompt: Optional[str]):
    """Initialize a new project with Palette templates"""
    
    # Template prompts
    templates = {
        'button': "Create a Button component with variants (primary, secondary, outline), sizes (sm, md, lg), loading state, and icon support",
        'card': "Create a Card component with header, body, footer sections, hover effects, and optional image",
        'form': "Create a Form component with validation, error handling, loading state, and accessible field components",
        'modal': "Create a Modal component with backdrop, close button, keyboard handling (ESC), and focus trap",
        'table': "Create a Table component with sorting, pagination, row selection, and responsive design",
        'navigation': "Create a Navigation component with mobile menu, active states, and keyboard navigation"
    }
    
    prompt = templates[component_type]
    if name:
        prompt = prompt.replace("component", f"{name} component")
    
    # Forward to generate command
    gen_type = 'multi' if multi else 'single'
    ctx = click.get_current_context()
    ctx.invoke(generate, prompt=prompt, type=gen_type)


@main.command()
@click.argument("component_type",
                type=click.Choice(['button', 'card', 'form', 'modal', 'table', 'navigation']))
@click.option("--name", "-n", help="Component name")
@click.option("--multi", is_flag=True, help="Generate as multi-file component")
def template(component_type: str, name: Optional[str], multi: bool):
    """Generate from pre-defined component templates"""


@main.command()
def config():
    """Configure UI/UX Copilot settings"""
    
    console.print(Panel(
        "[bold green]⚙️ Configuration[/bold green]",
        title="Settings",
        border_style="green",
    ))
    
    # Interactive configuration
    framework = click.prompt(
        "Default framework",
        type=click.Choice(['react', 'next.js', 'remix', 'vite']),
        default='react'
    )
    
    try:
        # Interactive prompts if not provided via flags
        if not type:
            type = Prompt.ask(
                "Choose framework",
                choices=["react", "nextjs", "vue"],
                default="react"
            )
        
        if not styling:
            styling = Prompt.ask(
                "Choose styling library",
                choices=["tailwind", "css"],
                default="tailwind"
            )
        
        if not ui_lib:
            ui_lib = Prompt.ask(
                "Choose UI library",
                choices=["shadcn", "none"],
                default="shadcn"
            )
        
        # Get project name
        project_name = Prompt.ask("Enter project name")
        if not project_name:
            console.print("[red]Error:[/red] Project name is required")
            sys.exit(1)
        
        # Wireframe workflow
        wireframe_path = wireframe
        wireframe_description = wireframe_prompt
        
        if not wireframe_path:
            has_wireframe = Confirm.ask("Do you have a wireframe?")
            if has_wireframe:
                wireframe_path = Prompt.ask("Enter wireframe file path (SVG)")
                if not wireframe_path or not os.path.exists(wireframe_path):
                    console.print("[red]Error:[/red] Wireframe file not found")
                    sys.exit(1)
                wireframe_description = Prompt.ask("Describe what you want to build from this wireframe")
        
        # Create project directory
        if os.path.exists(project_name):
            if not Confirm.ask(f"Directory '{project_name}' already exists. Overwrite?"):
                console.print("[yellow]Project initialization cancelled[/yellow]")
                return
            shutil.rmtree(project_name)
        
        os.makedirs(project_name)
        console.print(f"[green]✓[/green] Created project directory: {project_name}")
        
        # Generate project structure based on selections
        _create_project_structure(project_name, type, styling, ui_lib, components, utils)
        
        # Generate wireframe-based components if provided
        if wireframe_path and wireframe_description:
            _generate_wireframe_components(project_name, wireframe_path, wireframe_description, type, styling, ui_lib)
        
        console.print(f"[green]✓[/green] Project '{project_name}' initialized successfully!")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  cd {project_name}")
        console.print(f"  npm install")
        console.print(f"  npm run dev")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


def _create_project_structure(project_name: str, framework: str, styling: str, ui_lib: str, components: bool, utils: bool):
    """Create the project structure with templates"""
    
    ui_lib = click.prompt(
        "Default UI library",
        type=click.Choice(['none', 'shadcn/ui', 'material-ui', 'chakra-ui']),
        default='none'
    )
    
    # Save configuration
    config_path = Path.home() / '.palette' / 'config.json'
    config_path.parent.mkdir(exist_ok=True)
    
    config_data = {
        'framework': framework,
        'styling': styling,
        'ui_library': ui_lib
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    console.print(f"[green]✓[/green] Configuration saved to {config_path}")


def _show_configuration(framework: str, styling: str, ui: str, type: str):
    """Show the selected configuration"""
    config_table = Table(title="Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Framework", framework)
    config_table.add_row("Styling", styling)
    config_table.add_row("UI Library", ui)
    config_table.add_row("Generation Type", type)
    
    console.print(config_table)


def _preview_files(files: Dict[str, str]):
    """Preview generated files"""
    console.print("\n[bold]Generated Files:[/bold]\n")
    
    for file_path, content in files.items():
        console.print(f"[cyan]{file_path}[/cyan]")
        
        # Determine language for syntax highlighting
        lang = 'typescript' if file_path.endswith('.tsx') or file_path.endswith('.ts') else 'javascript'
        if file_path.endswith('.css'):
            lang = 'css'
        
        # Show first 30 lines
        lines = content.split('\n')[:30]
        preview_content = '\n'.join(lines)
        if len(content.split('\n')) > 30:
            preview_content += '\n... (truncated)'
        
        syntax = Syntax(preview_content, lang, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=file_path, border_style="dim"))
        console.print("")


def _save_files(files: Dict[str, str], output_dir: Optional[str] = None) -> List[str]:
    """Save generated files to disk"""
    saved_files = []
    base_path = Path(output_dir) if output_dir else Path.cwd()
    
    for file_path, content in files.items():
        full_path = base_path / file_path
        
        # Create directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(full_path, 'w') as f:
            f.write(content)
        
        saved_files.append(str(full_path))
    
    return saved_files


def _show_summary(saved_files: List[str]):
    """Show generation summary"""
    console.print("\n[bold green]✅ Generation Complete![/bold green]\n")
    
    summary_table = Table(title="Created Files")
    summary_table.add_column("File", style="cyan")
    summary_table.add_column("Status", style="green")
    
    for file_path in saved_files:
        summary_table.add_row(file_path, "✓ Created")
    
    console.print(summary_table)
    
    # Show next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. Review the generated files")
    console.print("2. Install any new dependencies if needed")
    console.print("3. Import and use your new components")


def _generate_wireframe_components(project_name: str, wireframe_path: str, wireframe_description: str, framework: str, styling: str, ui_lib: str):
    """Generate components based on SVG wireframe analysis"""
    
    console.print(f"[yellow]Analyzing wireframe: {wireframe_path}[/yellow]")
    
    try:
        # Parse SVG wireframe
        wireframe_data = _parse_svg_wireframe(wireframe_path)
        
        console.print(f"[green]✓[/green] Wireframe analyzed successfully")
        console.print(f"[yellow]Generating components based on wireframe...[/yellow]")
        
        # Generate components based on wireframe analysis
        components = _generate_components_from_wireframe(wireframe_data, wireframe_description, framework, styling, ui_lib)
        
        # Save components to project
        src_path = os.path.join(project_name, "src")
        components_path = os.path.join(src_path, "components")
        os.makedirs(components_path, exist_ok=True)
        
        for component_name, component_code in components.items():
            file_extension = ".tsx" if framework in ["react", "nextjs"] else ".vue"
            file_path = os.path.join(components_path, f"{component_name}{file_extension}")
            
            with open(file_path, "w") as f:
                f.write(component_code)
            
            console.print(f"[green]✓[/green] Created component: {component_name}{file_extension}")
        
        console.print(f"[green]✓[/green] Wireframe-based components generated successfully!")
        
    except Exception as e:
        console.print(f"[red]Error generating wireframe components:[/red] {str(e)}")
        console.print("[yellow]Continuing with standard project setup...[/yellow]")


def _parse_svg_wireframe(svg_path: str) -> dict:
    """Parse SVG file and extract design information"""
    
    import xml.etree.ElementTree as ET
    
    try:
        # Parse SVG without namespace handling for simplicity
        with open(svg_path, 'r') as f:
            content = f.read()
        
        # Remove XML declaration and parse
        if content.startswith('<?xml'):
            content = content.split('?>', 1)[1]
        
        root = ET.fromstring(content)
        
        # Extract basic SVG information
        svg_data = {
            "width": root.get("width", "100%"),
            "height": root.get("height", "100%"),
            "viewBox": root.get("viewBox", ""),
            "elements": [],
            "colors": set(),
            "fonts": set(),
            "layout": {
                "rectangles": [],
                "circles": [],
                "text": [],
                "paths": []
            }
        }
        
        # Parse SVG elements
        for element in root.iter():
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            
            if tag == "rect":
                rect_data = {
                    "x": float(element.get("x", 0)),
                    "y": float(element.get("y", 0)),
                    "width": float(element.get("width", 0)),
                    "height": float(element.get("height", 0)),
                    "fill": element.get("fill", "none"),
                    "stroke": element.get("stroke", "none"),
                    "stroke-width": element.get("stroke-width", "0")
                }
                svg_data["layout"]["rectangles"].append(rect_data)
                if rect_data["fill"] != "none":
                    svg_data["colors"].add(rect_data["fill"])
            
            elif tag == "circle":
                circle_data = {
                    "cx": float(element.get("cx", 0)),
                    "cy": float(element.get("cy", 0)),
                    "r": float(element.get("r", 0)),
                    "fill": element.get("fill", "none"),
                    "stroke": element.get("stroke", "none")
                }
                svg_data["layout"]["circles"].append(circle_data)
                if circle_data["fill"] != "none":
                    svg_data["colors"].add(circle_data["fill"])
            
            elif tag == "text":
                text_data = {
                    "x": float(element.get("x", 0)),
                    "y": float(element.get("y", 0)),
                    "content": element.text or "",
                    "font-family": element.get("font-family", "Arial"),
                    "font-size": element.get("font-size", "16"),
                    "fill": element.get("fill", "black")
                }
                svg_data["layout"]["text"].append(text_data)
                svg_data["fonts"].add(text_data["font-family"])
                svg_data["colors"].add(text_data["fill"])
            
            elif tag == "path":
                path_data = {
                    "d": element.get("d", ""),
                    "fill": element.get("fill", "none"),
                    "stroke": element.get("stroke", "none")
                }
                svg_data["layout"]["paths"].append(path_data)
                if path_data["fill"] != "none":
                    svg_data["colors"].add(path_data["fill"])
        
        # Convert sets to lists for JSON serialization
        svg_data["colors"] = list(svg_data["colors"])
        svg_data["fonts"] = list(svg_data["fonts"])
        
        return svg_data
        
    except Exception as e:
        raise Exception(f"Failed to parse SVG file: {str(e)}")


def _generate_components_from_wireframe(wireframe_data: dict, description: str, framework: str, styling: str, ui_lib: str) -> dict:
    """Generate React/Vue components based on wireframe analysis"""
    
    components = {}
    
    # Analyze layout to determine component structure
    layout = wireframe_data["layout"]
    colors = wireframe_data["colors"]
    fonts = wireframe_data["fonts"]
    
    # Create main component based on wireframe
    if framework in ["react", "nextjs"]:
        main_component = _create_react_component_from_wireframe(layout, colors, fonts, description, styling, ui_lib)
        components["WireframeComponent"] = main_component
    elif framework == "vue":
        main_component = _create_vue_component_from_wireframe(layout, colors, fonts, description, styling, ui_lib)
        components["WireframeComponent"] = main_component
    
    return components


def _create_react_component_from_wireframe(layout: dict, colors: list, fonts: list, description: str, styling: str, ui_lib: str) -> str:
    """Create React component based on wireframe analysis"""
    
    # Analyze layout structure
    rectangles = layout["rectangles"]
    circles = layout["circles"]
    text_elements = layout["text"]
    
    # Analyze the description to determine component type and features
    description_lower = description.lower()
    
    # Determine if this is a dashboard, form, or other UI type
    is_dashboard = any(word in description_lower for word in ['dashboard', 'admin', 'analytics', 'metrics'])
    is_form = any(word in description_lower for word in ['form', 'input', 'submit', 'login', 'signup'])
    is_navigation = any(word in description_lower for word in ['nav', 'menu', 'sidebar', 'navigation'])
    has_charts = any(word in description_lower for word in ['chart', 'graph', 'visualization', 'data'])
    
    # Generate component code with semantic structure
    component_code = '''import React from 'react';

interface WireframeComponentProps {
  className?: string;
}

const WireframeComponent: React.FC<WireframeComponentProps> = ({ className }) => {
  // State management based on component type
  ''' + _generate_state_management(description) + '''
  
  return (
    <div className={`wireframe-component ${className || ''}`}>
      {/* Generated from wireframe analysis */}
      {/* Description: ''' + description + ''' */}
      
      {/* Semantic structure based on prompt */}
      ''' + _generate_semantic_structure(rectangles, circles, text_elements, styling, description) + '''
      
    </div>
  );
};

export default WireframeComponent;
'''
    
    return component_code


def _create_vue_component_from_wireframe(layout: dict, colors: list, fonts: list, description: str, styling: str, ui_lib: str) -> str:
    """Create Vue component based on wireframe analysis"""
    
    # Analyze layout structure
    rectangles = layout["rectangles"]
    circles = layout["circles"]
    text_elements = layout["text"]
    
    # Generate component code
    component_code = f'''<template>
  <div class="wireframe-component">
    <!-- Generated from wireframe analysis -->
    <!-- Description: {description} -->
    
    <!-- Layout elements -->
    {_generate_vue_layout_elements(rectangles, circles, text_elements, styling)}
    
  </div>
</template>

<script lang="ts">
import {{ defineComponent }} from 'vue'

export default defineComponent({{
  name: 'WireframeComponent'
}})
</script>

<style scoped>
.wireframe-component {{
  /* Component styles */
}}
</style>
'''
    
    return component_code


def _generate_react_layout_elements(rectangles: list, circles: list, text_elements: list, styling: str) -> str:
    """Generate React JSX for layout elements"""
    
    elements = []
    
    # Add rectangles
    for i, rect in enumerate(rectangles):
        if styling == "tailwind":
            elements.append(f'''      <div 
        key="rect-{i}"
        className="absolute"
        style={{{{ left: '{rect["x"]}px', top: '{rect["y"]}px', width: '{rect["width"]}px', height: '{rect["height"]}px', backgroundColor: '{rect["fill"]}', border: '{rect["stroke"]} {rect["stroke-width"]}px solid' }}}}
      />''')
        else:
            elements.append(f'''      <div 
        key="rect-{i}"
        className="layout-rectangle"
        style={{{{ left: '{rect["x"]}px', top: '{rect["y"]}px', width: '{rect["width"]}px', height: '{rect["height"]}px', backgroundColor: '{rect["fill"]}', border: '{rect["stroke"]} {rect["stroke-width"]}px solid' }}}}
      />''')
    
    # Add text elements
    for i, text in enumerate(text_elements):
        if styling == "tailwind":
            elements.append(f'''      <div 
        key="text-{i}"
        className="absolute"
        style={{{{ left: '{text["x"]}px', top: '{text["y"]}px', fontFamily: '{text["font-family"]}', fontSize: '{text["font-size"]}px', color: '{text["fill"]}' }}}}
      >
        {text["content"]}
      </div>''')
        else:
            elements.append(f'''      <div 
        key="text-{i}"
        className="layout-text"
        style={{{{ left: '{text["x"]}px', top: '{text["y"]}px', fontFamily: '{text["font-family"]}', fontSize: '{text["font-size"]}px', color: '{text["fill"]}' }}}}
      >
        {text["content"]}
      </div>''')
    
    return "\n".join(elements)


def _generate_state_management(description: str) -> str:
    """Generate appropriate state management based on component description"""
    description_lower = description.lower()
    
    # Determine what kind of state we need
    if any(word in description_lower for word in ['form', 'input', 'submit', 'login', 'signup']):
        return '''  const [formData, setFormData] = React.useState({});
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  
  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // Handle form submission logic here
    console.log('Form submitted:', formData);
    setIsSubmitting(false);
  };'''
    
    elif any(word in description_lower for word in ['dashboard', 'admin', 'analytics', 'metrics']):
        return '''  const [isLoading, setIsLoading] = React.useState(false);
  const [data, setData] = React.useState({});
  
  React.useEffect(() => {
    // Load dashboard data
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setData({ users: 1234, revenue: 56789, growth: 12.5 });
      setIsLoading(false);
    }, 1000);
  }, []);'''
    
    elif any(word in description_lower for word in ['nav', 'menu', 'sidebar', 'navigation']):
        return '''  const [isMenuOpen, setIsMenuOpen] = React.useState(false);
  const [activeItem, setActiveItem] = React.useState('dashboard');
  
  const handleMenuToggle = () => setIsMenuOpen(!isMenuOpen);
  const handleItemClick = (item: string) => setActiveItem(item);'''
    
    else:
        return '''  // Basic state management
  const [isVisible, setIsVisible] = React.useState(true);'''


def _generate_semantic_structure(rectangles: list, circles: list, text_elements: list, styling: str, description: str) -> str:
    """Generate semantic HTML structure based on wireframe and description"""
    description_lower = description.lower()
    
    # Determine component type
    is_dashboard = any(word in description_lower for word in ['dashboard', 'admin', 'analytics', 'metrics'])
    is_form = any(word in description_lower for word in ['form', 'input', 'submit', 'login', 'signup'])
    is_navigation = any(word in description_lower for word in ['nav', 'menu', 'sidebar', 'navigation'])
    has_charts = any(word in description_lower for word in ['chart', 'graph', 'visualization', 'data'])
    
    if is_dashboard:
        return _generate_dashboard_structure(rectangles, circles, text_elements, styling)
    elif is_form:
        return _generate_form_structure(rectangles, circles, text_elements, styling)
    elif is_navigation:
        return _generate_navigation_structure(rectangles, circles, text_elements, styling)
    else:
        # Fallback to basic layout
        return _generate_react_layout_elements(rectangles, circles, text_elements, styling)


def _generate_dashboard_structure(rectangles: list, circles: list, text_elements: list, styling: str) -> str:
    """Generate dashboard-specific structure"""
    elements = []
    
    # Find header/navigation area
    header_rects = [r for r in rectangles if r["y"] < 100]
    sidebar_rects = [r for r in rectangles if r["x"] < 250 and r["width"] < 250]
    main_content = [r for r in rectangles if r["x"] > 200]
    
    # Generate header
    if header_rects:
        elements.append('''      {/* Header */}
      <header className="bg-gray-800 text-white p-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
      </header>''')
    
    # Generate sidebar
    if sidebar_rects:
        elements.append('''      {/* Sidebar Navigation */}
      <nav className="bg-gray-100 p-4 w-64 min-h-screen">
        <ul className="space-y-2">
          <li><a href="#" className="block p-2 bg-blue-500 text-white rounded">Dashboard</a></li>
          <li><a href="#" className="block p-2 hover:bg-gray-200 rounded">Analytics</a></li>
          <li><a href="#" className="block p-2 hover:bg-gray-200 rounded">Settings</a></li>
        </ul>
      </nav>''')
    
    # Generate main content
    if main_content:
        elements.append('''      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Total Users</h3>
            <p className="text-3xl font-bold text-blue-600">1,234</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Revenue</h3>
            <p className="text-3xl font-bold text-green-600">$56,789</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-2">Growth</h3>
            <p className="text-3xl font-bold text-purple-600">+12.5%</p>
          </div>
        </div>
        
        {/* Chart placeholder */}
        <div className="mt-8 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Activity Chart</h3>
          <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
            <p className="text-gray-500">Chart placeholder</p>
          </div>
        </div>
      </main>''')
    
    return "\n".join(elements)


def _generate_form_structure(rectangles: list, circles: list, text_elements: list, styling: str) -> str:
    """Generate form-specific structure"""
    return '''      {/* Form Structure */}
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
          <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(e) => handleInputChange('password', e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:opacity-50"
            >
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>
      </div>'''


def _generate_navigation_structure(rectangles: list, circles: list, text_elements: list, styling: str) -> str:
    """Generate navigation-specific structure"""
    return '''      {/* Navigation Structure */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Logo</h1>
            </div>
            <div className="hidden md:flex items-center space-x-4">
              <a href="#" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Home</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">About</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Services</a>
              <a href="#" className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Contact</a>
            </div>
            <div className="md:hidden">
              <button onClick={handleMenuToggle} className="text-gray-700 hover:text-gray-900">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        {isMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              <a href="#" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Home</a>
              <a href="#" className="block px-3 py-2 text-gray-700 hover:text-gray-900">About</a>
              <a href="#" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Services</a>
              <a href="#" className="block px-3 py-2 text-gray-700 hover:text-gray-900">Contact</a>
            </div>
          </div>
        )}
      </nav>'''


def _generate_vue_layout_elements(rectangles: list, circles: list, text_elements: list, styling: str) -> str:
    """Generate Vue template for layout elements"""
    
    elements = []
    
    # Add rectangles
    for i, rect in enumerate(rectangles):
        elements.append(f'''    <div 
      :key="'rect-{i}'"
      class="layout-rectangle"
      :style="{{
        left: '{rect["x"]}px',
        top: '{rect["y"]}px',
        width: '{rect["width"]}px',
        height: '{rect["height"]}px',
        backgroundColor: '{rect["fill"]}',
        border: '{rect["stroke"]} {rect["stroke-width"]}px solid'
      }}"
    />''')
    
    # Add text elements
    for i, text in enumerate(text_elements):
        elements.append(f'''    <div 
      :key="'text-{i}'"
      class="layout-text"
      :style="{{
        left: '{text["x"]}px',
        top: '{text["y"]}px',
        fontFamily: '{text["font-family"]}',
        fontSize: '{text["font-size"]}px',
        color: '{text["fill"]}'
      }}"
    >
      {text["content"]}
    </div>''')
    
    return "\n".join(elements)


if __name__ == "__main__":
    main()