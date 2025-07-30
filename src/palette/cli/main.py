# Enhanced CLI for UI/UX Copilot
# Supports multi-file generation, editing, and multiple frameworks/libraries

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

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
@click.argument("component_type",
                type=click.Choice(['button', 'card', 'form', 'modal', 'table', 'navigation']))
@click.option("--name", "-n", help="Component name")
@click.option("--multi", is_flag=True, help="Generate as multi-file component")
def template(component_type: str, name: Optional[str], multi: bool):
    """Generate from pre-defined component templates"""
    
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
def knowledge_status():
    """Show knowledge base status and statistics"""
    
    console.print(Panel(
        "[bold blue]🧠 Knowledge Base Status[/bold blue]",
        title="Status",
        border_style="blue",
    ))
    
    if KNOWLEDGE_AVAILABLE:
        from ..generation.knowledge_generator import KnowledgeUIGenerator
        generator = KnowledgeUIGenerator()
        status = generator.get_knowledge_status()
        
        if status["available"]:
            console.print("[green]✅ Local knowledge base is available[/green]")
            
            # Create status table
            table = Table(title="Knowledge Base Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Type", status.get("type", "unknown"))
            table.add_row("Rate Limits", "No" if not status.get("rate_limits", True) else "Yes")
            table.add_row("Total Chunks", str(status.get("total_chunks", 0)))
            table.add_row("Embedding Model", status.get("embedding_model", "unknown"))
            table.add_row("Storage Path", status.get("storage_path", "unknown"))
            
            console.print(table)
            
            # Show categories if available
            categories = status.get("categories", {})
            if categories:
                cat_table = Table(title="Knowledge Categories")
                cat_table.add_column("Category", style="yellow")
                cat_table.add_column("Count", style="green")
                
                for category, count in categories.items():
                    cat_table.add_row(category, str(count))
                
                console.print(cat_table)
        else:
            console.print(f"[red]❌ Knowledge base not available: {status.get('reason', 'Unknown error')}[/red]")
            console.print("[yellow]Install dependencies: pip install sentence-transformers faiss-cpu numpy[/yellow]")
    else:
        console.print("[red]❌ Knowledge enhancement not available[/red]")
        console.print("[yellow]Install dependencies: pip install sentence-transformers faiss-cpu numpy[/yellow]")


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
    
    styling = click.prompt(
        "Default styling",
        type=click.Choice(['tailwind', 'styled-components', 'emotion', 'css-modules']),
        default='tailwind'
    )
    
    ui_lib = click.prompt(
        "Default UI library",
        type=click.Choice(['none', 'shadcn/ui', 'material-ui', 'chakra-ui']),
        default='none'
    )
    
    # Save configuration
    config_path = Path.home() / '.palette' / 'config.json'
    config_path.parent.mkdir(exist_ok=True)
    
    import json
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


if __name__ == "__main__":
    main()