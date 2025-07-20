import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from ..analysis.context import ProjectAnalyzer
from ..generation.generator import UIGenerator
from ..utils.file_manager import FileManager

# Load environment variables from .env file
load_dotenv()

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Code Palette - Design-to-Code UI/UX Agent for React + Tailwind components"""
    pass


@main.command()
@click.argument("prompt", required=True)
@click.option("--preview", is_flag=True, help="Preview component before creating file")
@click.option("--output", "-o", help="Output file path (auto-detected if not provided)")
@click.option(
    "--model", default=None, help="LLM model to use (defaults to OPENAI_MODEL env var)"
)
@click.option(
    "--enhanced/--basic", default=True, help="Use enhanced prompt engineering with project analysis"
)
def generate(prompt: str, preview: bool, output: Optional[str], model: str, enhanced: bool):
    """Generate a React component from a natural language prompt"""

    console.print(
        Panel(
            f"[bold blue]Generating component:[/bold blue] {prompt}",
            title="Code Palette",
            border_style="blue",
        )
    )

    try:
        # Analyze project context
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())

        console.print(
            f"[green]✓[/green] Detected {context['framework']} project with {context['styling']}"
        )

        # Generate component with enhanced or basic mode
        generator = UIGenerator(model=model, project_path=os.getcwd(), enhanced_mode=enhanced)
        component_code = generator.generate_component(prompt, context)

        console.print("[yellow]Formatting and linting code...[/yellow]")

        # Format and lint the generated code
        formatted_code = generator.format_and_lint_code(component_code, os.getcwd())

        if preview:
            console.print(
                Panel(formatted_code, title="Generated Component", border_style="green")
            )
            if not click.confirm("Create this component?"):
                console.print("[yellow]Component generation cancelled[/yellow]")
                return

        # Save component
        file_manager = FileManager()
        file_path = file_manager.save_component(formatted_code, output, context, prompt)

        console.print(f"[green]✓[/green] Component created at: {file_path}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
def analyze():
    """Analyze project design patterns and configuration"""

    console.print(
        Panel(
            "[bold blue]Analyzing project...[/bold blue]",
            title="Code Palette",
            border_style="blue",
        )
    )

    try:
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())

        # Display analysis results
        console.print(f"[bold]Framework:[/bold] {context.get('framework', 'Unknown')}")
        console.print(f"[bold]Styling:[/bold] {context.get('styling', 'Unknown')}")
        console.print(
            f"[bold]Component Library:[/bold] {context.get('component_library', 'None detected')}"
        )

        # Display main CSS file path
        main_css_file = context.get("main_css_file")
        if main_css_file:
            console.print(f"[bold]Main CSS File:[/bold] {main_css_file}")
        else:
            console.print(f"[bold]Main CSS File:[/bold] Not found")

        if context.get("design_tokens"):
            tokens = context["design_tokens"]
            
            # Format colors with values if available
            if "color_structure" in tokens and tokens["color_structure"]:
                color_items = []
                for name, value in list(tokens["color_structure"].items())[:10]:  # Limit to 10 colors
                    if isinstance(value, str):
                        color_items.append(f"{name}={value}")
                    else:
                        color_items.append(name)
                colors_display = ", ".join(color_items)
            else:
                colors_display = ", ".join(tokens.get('colors', []))
            
            console.print(f"[bold]Colors:[/bold] {colors_display}")
            console.print(
                f"[bold]Spacing:[/bold] {', '.join(tokens.get('spacing', []))}"
            )
            console.print(
                f"[bold]Typography:[/bold] {', '.join(tokens.get('typography', []))}"
            )

        console.print("[green]✓[/green] Project analysis complete")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@main.command()
@click.argument("prompt", required=True)
def preview(prompt: str):
    """Preview a component without creating it"""

    console.print(
        Panel(
            f"[bold blue]Previewing component:[/bold blue] {prompt}",
            title="Code Palette",
            border_style="blue",
        )
    )

    try:
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())

        generator = UIGenerator()
        component_code = generator.generate_component(prompt, context)

        console.print("[yellow]Formatting and linting code...[/yellow]")

        # Format and lint the generated code
        formatted_code = generator.format_and_lint_code(component_code, os.getcwd())

        console.print(
            Panel(formatted_code, title="Component Preview", border_style="green")
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
