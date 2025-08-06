# Enhanced CLI for UI/UX Copilot
# Supports multi-file generation, editing, and multiple frameworks/libraries

import os
import sys
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in current directory and parent directories
load_dotenv(verbose=False)

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
              type=click.Choice(['auto-detect', 'none', 'shadcn/ui', 'material-ui', 'chakra-ui', 'ant-design', 'headless-ui', 'mantine', 'react-bootstrap', 'semantic-ui', 'grommet']),
              default='auto-detect',
              help="UI component library (auto-detect will analyze your project)")
@click.option("--output", "-o", help="Output directory (auto-detected if not provided)")
@click.option("--preview", is_flag=True, help="Preview before creating files")
@click.option("--no-tests", is_flag=True, help="Skip test file generation")
@click.option("--storybook", is_flag=True, help="Include Storybook stories")
@click.option("--basic-mode", is_flag=True, help="Disable zero-fix validation (basic generation only)")
@click.option("--explain", is_flag=True, help="Show detailed explanations of generation decisions")
@click.option("--interactive", is_flag=True, help="Enable interactive refinement mode for conversational development")
def generate(prompt: str, type: Optional[str], framework: Optional[str], 
             styling: Optional[str], ui: str, output: Optional[str],
             preview: bool, no_tests: bool, storybook: bool, basic_mode: bool, explain: bool, interactive: bool):
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
        
        
        # Auto-detect settings from project using enhanced intelligence
        detected_config = None
        if not framework or not styling:
            try:
                from ..intelligence.configuration_hub import ConfigurationIntelligenceHub
                config_hub = ConfigurationIntelligenceHub()
                
                console.print("🔍 [dim]Auto-detecting project configuration...[/dim]")
                detected_config = config_hub.analyze_configuration(output)
                
                # Use detected settings if not explicitly provided
                if not framework:
                    framework = detected_config.framework.value if detected_config.framework else 'react'
                if not styling:
                    styling = detected_config.styling_system.value.lower() if detected_config.styling_system else 'tailwind'
                
                # Show smart detection results
                confidence = getattr(detected_config, 'confidence_score', 1.0)
                if confidence >= 0.8:
                    console.print(f"✅ [green]Auto-detected: {framework} + {styling} ({confidence:.0%} confidence)[/green]")
                else:
                    console.print(f"⚠️ [yellow]Best guess: {framework} + {styling} ({confidence:.0%} confidence)[/yellow]")
                    
            except Exception as e:
                console.print(f"[dim yellow]⚠️ Auto-detection unavailable: {str(e)}[/dim yellow]")
                # Fallback to basic detection
                if not framework:
                    framework = generator.project_context.get('framework', 'react')
                if not styling:
                    styling = generator.project_context.get('styling', 'tailwind')
        
        if not type:
            type = generator._detect_generation_type(prompt)
        
        # Handle UI library selection and validation
        ui = _resolve_ui_library_selection(ui, output, detected_config)
        
        # Show detected/selected configuration with intelligence insights
        _show_configuration_enhanced(framework, styling, ui, type, detected_config)
        
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
        
        # Enable explanation tracking if requested
        generation_explanations = []
        if explain:
            console.print("\n[bold blue]🧠 GENERATION EXPLANATIONS ENABLED[/bold blue]")
            console.print("Tracking decision-making process...\n")
            
            # Store explanations for post-generation display
            generation_explanations = _create_generation_explanations(
                prompt, framework, styling, ui, type, detected_config
            )
        
        # Generate files
        files = generator.generate(request)
        
        # Interactive refinement mode
        if interactive:
            from .interactive_refiner import InteractiveRefiner
            
            console.print("\\n🤝 [bold blue]Starting Interactive Refinement Mode[/bold blue]")
            console.print("[dim]You can now iteratively improve the generated component through conversation.[/dim]")
            
            refiner = InteractiveRefiner()
            session = refiner.start_refinement_session(prompt, files, detected_config)
            
            # Run interactive session
            refined_files = refiner.run_interactive_session()
            files = refined_files  # Use refined version
            
            # Show session summary
            session_summary = refiner.get_session_summary()
            if session_summary.get('refinements_applied', 0) > 0:
                console.print(f"\\n✨ [green]Applied {session_summary['refinements_applied']} refinements through conversation![/green]")
        
        elif preview:
            _preview_files(files)
            if not click.confirm("\\nCreate these files?"):
                console.print("[yellow]Generation cancelled[/yellow]")
                return
        
        # Save files
        saved_files = _save_files(files, output)
        
        # Show summary with explanations if requested
        _show_summary(saved_files)
        
        # Display generation explanations if enabled
        if explain and generation_explanations:
            _display_generation_explanations(generation_explanations, files)
        
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
@click.option("--wireframe", help="Path to wireframe file (SVG or JSON)")
@click.option("--wireframe-prompt", help="Description of what to build from wireframe")
def init(type: Optional[str], styling: Optional[str], ui_lib: Optional[str], components: bool, utils: bool, wireframe: Optional[str], wireframe_prompt: Optional[str]):
    """Initialize a new project with Palette templates"""
    
    console.print(Panel(
        "[bold blue]🚀 Palette Project Initializer[/bold blue]",
        title="Initializing",
        border_style="blue",
    ))
    
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
@click.option("--show", is_flag=True, help="Show detailed project context analysis")
@click.option("--format", "-f", type=click.Choice(['table', 'json', 'detailed']), 
              default='detailed', help="Output format")
@click.option("--explain", is_flag=True, help="Explain how context affects generation")
def context(show: bool, format: str, explain: bool):
    """Context Lens - See what Palette understands about your project"""
    
    console.print(Panel(
        "[bold blue]🔍 Context Lens[/bold blue]\nAnalyzing your project context...",
        title="Context Analysis",
        border_style="blue",
    ))
    
    try:
        # Import enhanced analysis components
        from ..intelligence.configuration_hub import ConfigurationIntelligenceHub
        from ..generation.config_aware_context_manager import ConfigurationAwareContextManager
        from ..generation.framework_pattern_library import FrameworkPatternLibrary
        
        # Initialize analysis components
        config_hub = ConfigurationIntelligenceHub()
        context_manager = ConfigurationAwareContextManager()
        pattern_library = FrameworkPatternLibrary()
        
        # Analyze project configuration
        console.print("🔄 Analyzing project configuration...")
        project_config = config_hub.analyze_configuration(".")
        
        # Get context insights
        console.print("🔄 Gathering context insights...")
        sample_request = "Create a responsive component"
        project_context = {'project_path': '.'}
        
        try:
            optimized_system, optimized_user, context_stats = context_manager.optimize_context_with_configuration(
                user_request=sample_request,
                project_context=project_context,
                configuration=project_config,
                system_prompt_base="You are an expert frontend developer.",
                user_prompt_base=sample_request
            )
        except Exception as e:
            console.print(f"[yellow]⚠️ Context optimization unavailable: {str(e)}[/yellow]")
            context_stats = {}
        
        # Get pattern recommendations
        console.print("🔄 Finding relevant patterns...")
        try:
            pattern_recommendations = pattern_library.get_recommended_patterns(
                user_request=sample_request,
                framework=project_config.framework,
                styling_system=project_config.styling_system,
                max_results=5
            )
        except Exception as e:
            console.print(f"[yellow]⚠️ Pattern recommendations unavailable: {str(e)}[/yellow]")
            pattern_recommendations = []
        
        # Display results based on format
        if format == 'json':
            _show_context_json(project_config, context_stats, pattern_recommendations)
        elif format == 'table':
            _show_context_table(project_config, context_stats, pattern_recommendations)
        else:  # detailed
            _show_context_detailed(project_config, context_stats, pattern_recommendations, explain)
            
    except Exception as e:
        console.print(f"[red]Error analyzing project context:[/red] {str(e)}")
        console.print("[yellow]Tip: Make sure you're in a project directory with a package.json file[/yellow]")
        sys.exit(1)


@main.command()
@click.option("--complete", "-c", help="Get completions for partial prompt")
@click.option("--category", help="Filter suggestions by category")
@click.option("--format", "-f", type=click.Choice(['detailed', 'simple', 'json']), 
              default='detailed', help="Output format")
def suggest(complete: Optional[str], category: Optional[str], format: str):
    """Get context-aware prompt suggestions based on your current location"""
    
    console.print(Panel(
        "[bold blue]💡 Smart Suggestions[/bold blue]\nAnalyzing context for relevant prompts...",
        title="Contextual Suggestions",
        border_style="blue",
    ))
    
    try:
        from .smart_suggestions import SmartSuggestionEngine
        
        suggestion_engine = SmartSuggestionEngine()
        
        if complete:
            # Get prompt completions
            console.print(f"🔍 [dim]Getting completions for: '{complete}'[/dim]")
            suggestions = suggestion_engine.get_prompt_completions(complete, ".")
        else:
            # Get contextual suggestions
            console.print("🔍 [dim]Analyzing current directory context...[/dim]")
            suggestions = suggestion_engine.get_contextual_suggestions(".")
        
        # Filter by category if specified
        if category:
            suggestions = [s for s in suggestions if category.lower() in s.category.lower()]
        
        if not suggestions:
            console.print("[yellow]No relevant suggestions found for current context.[/yellow]")
            console.print("[dim]Try moving to a component directory or specify a partial prompt with --complete[/dim]")
            return
        
        # Display suggestions based on format
        if format == 'json':
            _show_suggestions_json(suggestions)
        elif format == 'simple': 
            _show_suggestions_simple(suggestions)
        else:  # detailed
            _show_suggestions_detailed(suggestions, complete is not None)
            
    except Exception as e:
        console.print(f"[red]Error generating suggestions:[/red] {str(e)}")
        console.print("[yellow]Tip: Make sure you're in a project directory[/yellow]")
        sys.exit(1)


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
        type=click.Choice(['auto-detect', 'none', 'shadcn/ui', 'material-ui', 'chakra-ui', 'ant-design', 'headless-ui', 'mantine', 'react-bootstrap', 'semantic-ui', 'grommet']),
        default='auto-detect'
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
    
    # Show current configuration
    console.print("\n[bold]Current Configuration:[/bold]")
    console.print(f"  Framework: {framework}")
    console.print(f"  Styling: {styling}")
    console.print(f"  UI Library: {ui_lib}")


def _create_project_structure(project_name: str, framework: str, styling: str, ui_lib: str, components: bool, utils: bool):
    """Create the project structure with templates"""
    
    # Create package.json
    _create_package_json(project_name, framework, styling, ui_lib)
    
    # Create project structure based on framework
    if framework == "react":
        _create_react_structure(os.path.join(project_name, "src"), styling, ui_lib)
        _create_react_public_files(project_name)
    elif framework == "nextjs":
        _create_nextjs_structure(project_name, styling, ui_lib)
    elif framework == "vue":
        _create_vue_structure(os.path.join(project_name, "src"), styling, ui_lib)
    
    # Create configuration files
    _create_config_files(project_name, framework, styling)
    
    # Create component templates if requested
    if components:
        _create_component_templates(os.path.join(project_name, "src"), framework)
    
    # Create utility templates if requested
    if utils:
        _create_utility_templates(os.path.join(project_name, "src"))


def _create_package_json(base_path: str, framework: str, styling: str, ui_lib: str):
    """Create package.json file"""
    package_json = {
        "name": os.path.basename(base_path),
        "version": "0.1.0",
        "private": True,
        "dependencies": {},
        "devDependencies": {},
        "scripts": {}
    }
    
    # Add framework-specific dependencies
    if framework == "react":
        package_json["dependencies"].update({
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        })
        package_json["devDependencies"].update({
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^4.9.5",
            "react-scripts": "^5.0.1"
        })
        package_json["scripts"].update({
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject",
            "dev": "react-scripts start"
        })
        package_json["browserslist"] = {
            "production": [
                ">0.2%",
                "not dead",
                "not op_mini all"
            ],
            "development": [
                "last 1 chrome version",
                "last 1 firefox version",
                "last 1 safari version"
            ]
        }
    elif framework == "nextjs":
        package_json["dependencies"].update({
            "next": "^13.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        })
        package_json["devDependencies"].update({
            "@types/node": "^18.0.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "typescript": "^4.9.5"
        })
        package_json["scripts"].update({
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        })
    elif framework == "vue":
        package_json["dependencies"].update({
            "vue": "^3.3.0"
        })
        package_json["devDependencies"].update({
            "@vitejs/plugin-vue": "^4.0.0",
            "vite": "^4.0.0",
            "typescript": "^4.9.5"
        })
        package_json["scripts"].update({
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        })
    
    # Add styling dependencies
    if styling == "tailwind":
        package_json["devDependencies"].update({
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.0",
            "postcss": "^8.4.0"
        })
    
    # Add UI library dependencies
    if ui_lib == "shadcn":
        package_json["devDependencies"].update({
            "@types/node": "^18.0.0"
        })
    
    # Write package.json
    with open(os.path.join(base_path, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)


def _create_react_structure(src_path: str, styling: str, ui_lib: str):
    """Create React project structure"""
    
    # Create src directory
    os.makedirs(src_path, exist_ok=True)
    
    # Create main App component
    if styling == "tailwind":
        app_content = '''import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to React</h1>
        <p className="text-gray-600">Edit src/App.tsx and save to reload.</p>
      </div>
    </div>
  );
}

export default App;
'''
    else:
        app_content = '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to React</h1>
        <p>Edit src/App.tsx and save to reload.</p>
      </header>
    </div>
  );
}

export default App;
'''
    
    with open(os.path.join(src_path, "App.tsx"), "w") as f:
        f.write(app_content)
    
    # Create index file
    index_content = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
'''
    
    with open(os.path.join(src_path, "index.tsx"), "w") as f:
        f.write(index_content)
    
    # Create CSS files
    if styling == "tailwind":
        css_content = '''@tailwind base;
@tailwind components;
@tailwind utilities;
'''
    else:
        css_content = '''body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
}
'''
    
    with open(os.path.join(src_path, "index.css"), "w") as f:
        f.write(css_content)
    
    if styling != "tailwind":
        with open(os.path.join(src_path, "App.css"), "w") as f:
            f.write(css_content)


def _create_react_public_files(base_path: str):
    """Create React public files"""
    
    # Create public directory
    public_path = os.path.join(base_path, "public")
    os.makedirs(public_path, exist_ok=True)
    
    # Create index.html
    index_html = '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Web site created using create-react-app"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
'''
    
    with open(os.path.join(public_path, "index.html"), "w") as f:
        f.write(index_html)
    
    # Create manifest.json
    manifest_json = '''{
  "short_name": "React App",
  "name": "Sample React App",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
'''
    
    with open(os.path.join(public_path, "manifest.json"), "w") as f:
        f.write(manifest_json)


def _create_nextjs_structure(base_path: str, styling: str, ui_lib: str):
    """Create Next.js project structure"""
    # Implementation for Next.js structure
    pass


def _create_vue_structure(src_path: str, styling: str, ui_lib: str):
    """Create Vue project structure"""
    # Implementation for Vue structure
    pass


def _create_component_templates(src_path: str, framework: str):
    """Create component templates"""
    # Implementation for component templates
    pass


def _create_utility_templates(src_path: str):
    """Create utility templates"""
    # Implementation for utility templates
    pass


def _create_config_files(base_path: str, framework: str, styling: str):
    """Create configuration files"""
    
    # Create TypeScript config
    if framework in ["react", "nextjs"]:
        tsconfig = '''{
  "compilerOptions": {
    "target": "es5",
    "lib": [
      "dom",
      "dom.iterable",
      "es6"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
'''
        with open(os.path.join(base_path, "tsconfig.json"), "w") as f:
            f.write(tsconfig)
    
    # Create Tailwind config
    if styling == "tailwind":
        tailwind_config = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''
        with open(os.path.join(base_path, "tailwind.config.js"), "w") as f:
            f.write(tailwind_config)
        
        postcss_config = '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''
        with open(os.path.join(base_path, "postcss.config.js"), "w") as f:
            f.write(postcss_config)


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


def _show_configuration_enhanced(framework: str, styling: str, ui: str, type: str, detected_config=None):
    """Show enhanced configuration with intelligence insights"""
    
    # Basic configuration table
    config_table = Table(title="Generation Configuration", show_header=True, header_style="bold cyan")
    config_table.add_column("Setting", style="cyan", width=20)
    config_table.add_column("Value", style="green", width=25)
    config_table.add_column("Source", style="yellow", width=15)
    config_table.add_column("Confidence", style="white", width=12)
    
    # Determine sources and confidence
    framework_source = "Auto-detected" if detected_config and detected_config.framework else "Default"
    styling_source = "Auto-detected" if detected_config and detected_config.styling_system else "Default"
    confidence = getattr(detected_config, 'confidence_score', 0.0) if detected_config else 0.0
    
    config_table.add_row(
        "Framework", 
        framework, 
        framework_source,
        f"{confidence:.0%}" if confidence > 0 else "N/A"
    )
    config_table.add_row(
        "Styling", 
        styling, 
        styling_source,
        "High" if detected_config and detected_config.styling_system else "Low"
    )
    config_table.add_row(
        "UI Library", 
        ui, 
        "Manual",
        "N/A"
    )
    config_table.add_row(
        "Generation Type", 
        type, 
        "Auto-detected",
        "High"
    )
    
    console.print(config_table)
    
    # Show intelligence insights if available
    if detected_config:
        insights = []
        
        # TypeScript insight
        if detected_config.typescript:
            insights.append("• TypeScript interfaces will be generated")
        
        # Styling system insights
        if detected_config.styling_system:
            if detected_config.styling_system.value == "TAILWIND":
                insights.append("• Tailwind CSS classes will be used for styling")
            elif detected_config.styling_system.value == "CHAKRA_UI":
                insights.append("• Chakra UI components will be prioritized")
                insights.append("• Tailwind classes will be avoided to prevent conflicts")
        
        # Component library insight
        if detected_config.component_library and detected_config.component_library.value != "none":
            insights.append(f"• {detected_config.component_library.value} components will be used")
        
        if insights:
            console.print("\n[bold blue]🤖 Generation Intelligence:[/bold blue]")
            for insight in insights:
                console.print(f"[dim]{insight}[/dim]")
    
    console.print("") # Add spacing


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
    """Generate components based on wireframe analysis (supports SVG and JSON)"""
    
    console.print(f"[yellow]Analyzing wireframe: {wireframe_path}[/yellow]")
    
    try:
        # Parse wireframe based on file type
        wireframe_data = _parse_wireframe(wireframe_path)
        
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


def _parse_wireframe(wireframe_path: str) -> dict:
    """Universal wireframe parser supporting SVG and JSON formats"""
    
    file_ext = Path(wireframe_path).suffix.lower()
    
    if file_ext == '.svg':
        return _parse_svg_wireframe(wireframe_path)
    elif file_ext == '.json':
        return _parse_json_wireframe(wireframe_path)
    else:
        raise ValueError(f"Unsupported wireframe format: {file_ext}. Supported formats: .svg, .json")


def _parse_json_wireframe(json_path: str) -> dict:
    """Parse JSON wireframe file and extract design information"""
    
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        # Convert JSON structure to match SVG parser output format
        wireframe_data = {
            "type": json_data.get("type", "unknown"),
            "layout": {
                "rectangles": [],
                "circles": [],
                "text": [],
                "paths": []
            },
            "colors": set(),
            "fonts": set(),
            "metadata": json_data.get("metadata", {}),
            "styling": json_data.get("styling", {})
        }
        
        # Extract colors from styling
        if "styling" in json_data and "colors" in json_data["styling"]:
            wireframe_data["colors"].update(json_data["styling"]["colors"])
        
        # Extract fonts from styling
        if "styling" in json_data and "fonts" in json_data["styling"]:
            wireframe_data["fonts"].update(json_data["styling"]["fonts"])
        
        # Process layout elements
        if "layout" in json_data:
            _process_json_layout(json_data["layout"], wireframe_data)
        
        # Convert sets to lists for JSON serialization
        wireframe_data["colors"] = list(wireframe_data["colors"])
        wireframe_data["fonts"] = list(wireframe_data["fonts"])
        
        return wireframe_data
        
    except Exception as e:
        raise Exception(f"Failed to parse JSON wireframe file: {str(e)}")


def _process_json_layout(layout: dict, wireframe_data: dict):
    """Process JSON layout structure and convert to wireframe data format"""
    
    def extract_colors_from_styling(styling: dict):
        """Extract colors from styling object"""
        if not styling:
            return
        
        color_props = ["background", "color", "fill", "stroke"]
        for prop in color_props:
            if prop in styling and styling[prop]:
                wireframe_data["colors"].add(styling[prop])
    
    def process_element(element: dict, parent_position: dict = None):
        """Recursively process layout elements"""
        element_type = element.get("type", "")
        position = element.get("position", {})
        styling = element.get("styling", {})
        
        # Extract colors from styling
        extract_colors_from_styling(styling)
        
        # Convert element to wireframe format based on type
        if element_type in ["logo", "text", "label"]:
            text_data = {
                "x": position.get("x", 0),
                "y": position.get("y", 0),
                "content": element.get("text", ""),
                "font-family": styling.get("font-family", "Arial"),
                "font-size": styling.get("font-size", "16px"),
                "fill": styling.get("color", "black")
            }
            wireframe_data["layout"]["text"].append(text_data)
            wireframe_data["fonts"].add(text_data["font-family"])
        
        elif element_type in ["stat-card", "card", "section"]:
            # Convert cards to rectangles
            rect_data = {
                "x": position.get("x", 0),
                "y": position.get("y", 0),
                "width": styling.get("width", 120),
                "height": styling.get("height", 40),
                "fill": styling.get("background", "white"),
                "stroke": styling.get("border", "none"),
                "stroke-width": "1"
            }
            wireframe_data["layout"]["rectangles"].append(rect_data)
        
        elif element_type in ["nav-item", "menu-item"]:
            # Convert nav items to rectangles with text
            rect_data = {
                "x": position.get("x", 0),
                "y": position.get("y", 0),
                "width": styling.get("width", 180),
                "height": styling.get("height", 40),
                "fill": styling.get("background", "white"),
                "stroke": styling.get("border", "#e2e8f0"),
                "stroke-width": "1"
            }
            wireframe_data["layout"]["rectangles"].append(rect_data)
            
            # Add text for nav items
            if "text" in element:
                text_data = {
                    "x": position.get("x", 0) + 10,
                    "y": position.get("y", 0) + 25,
                    "content": element["text"],
                    "font-family": "Arial",
                    "font-size": "12px",
                    "fill": styling.get("color", "#2d3748")
                }
                wireframe_data["layout"]["text"].append(text_data)
        
        # Process nested elements
        if "elements" in element:
            for nested_element in element["elements"]:
                process_element(nested_element, position)
        
        # Process sections
        if "sections" in element:
            for section in element["sections"]:
                process_element(section, position)


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


def _show_context_detailed(project_config, context_stats: dict, pattern_recommendations: list, explain: bool):
    """Show detailed context analysis with rich formatting"""
    
    # Project Configuration Overview
    console.print("\n📊 PROJECT ANALYSIS", style="bold blue")
    console.print("=" * 50)
    
    config_table = Table(title="Project Configuration", show_header=True, header_style="bold cyan")
    config_table.add_column("Setting", style="cyan", width=25)
    config_table.add_column("Value", style="green", width=30)
    config_table.add_column("Confidence", style="yellow", width=15)
    
    config_table.add_row(
        "Framework", 
        project_config.framework.value if project_config.framework else "Unknown",
        f"{project_config.confidence_score:.1%}" if hasattr(project_config, 'confidence_score') else "N/A"
    )
    config_table.add_row(
        "Styling System", 
        project_config.styling_system.value if project_config.styling_system else "Unknown",
        "High" if project_config.styling_system else "Low"
    )
    config_table.add_row(
        "TypeScript", 
        "✅ Yes" if project_config.typescript else "❌ No",
        "High"
    )
    config_table.add_row(
        "Components Found", 
        str(len(project_config.component_patterns)) if hasattr(project_config, 'component_patterns') else "0",
        "Medium"
    )
    
    console.print(config_table)
    
    # Context Optimization Stats
    if context_stats:
        console.print("\n🎯 CONTEXT OPTIMIZATION", style="bold blue")
        console.print("=" * 50)
        
        optimization_table = Table(title="Context Intelligence", show_header=True, header_style="bold cyan")
        optimization_table.add_column("Metric", style="cyan")
        optimization_table.add_column("Value", style="green")
        optimization_table.add_column("Target", style="yellow")
        optimization_table.add_column("Status", style="white")
        
        token_budget = context_stats.get('token_budget', {})
        utilization = token_budget.get('utilization', 0)
        target_utilization = 0.087  # 8.7% target
        
        optimization_table.add_row(
            "Token Utilization",
            f"{utilization:.1%}",
            f"{target_utilization:.1%}",
            "✅ Optimal" if utilization <= target_utilization else "⚠️ High"
        )
        
        context_quality = context_stats.get('context_quality', {})
        relevance_score = context_quality.get('relevance_score', 0)
        optimization_table.add_row(
            "Context Relevance",
            f"{relevance_score:.1%}" if relevance_score else "N/A",
            "≥90%",
            "✅ Good" if relevance_score >= 0.9 else "⚠️ Low" if relevance_score else "❓ Unknown"
        )
        
        priority_weights = context_stats.get('priority_weights', {})
        framework_weight = priority_weights.get('framework_specific', 0)
        optimization_table.add_row(
            "Framework Focus",
            f"{framework_weight:.1%}" if framework_weight else "N/A",
            "≥70%",
            "✅ High" if framework_weight >= 0.7 else "⚠️ Low" if framework_weight else "❓ Unknown"
        )
        
        console.print(optimization_table)
    
    # Pattern Recommendations
    if pattern_recommendations:
        console.print("\n🎨 PATTERN RECOMMENDATIONS", style="bold blue")
        console.print("=" * 50)
        
        patterns_table = Table(title="Available Patterns", show_header=True, header_style="bold cyan")
        patterns_table.add_column("Pattern", style="cyan")
        patterns_table.add_column("Framework", style="green")
        patterns_table.add_column("Styling", style="yellow")
        patterns_table.add_column("Use Cases", style="white")
        
        for pattern in pattern_recommendations[:5]:  # Show top 5
            use_cases = ", ".join(pattern.use_cases[:2]) if hasattr(pattern, 'use_cases') and pattern.use_cases else "General"
            patterns_table.add_row(
                pattern.name,
                pattern.framework.value if hasattr(pattern, 'framework') and pattern.framework else "Any",
                pattern.styling_system.value if hasattr(pattern, 'styling_system') and pattern.styling_system else "Any",
                use_cases
            )
        
        console.print(patterns_table)
    
    # Generation Intelligence Preview
    console.print("\n🤖 GENERATION INTELLIGENCE", style="bold blue")
    console.print("=" * 50)
    
    intelligence_info = []
    
    # Framework-specific intelligence
    if project_config.framework:
        intelligence_info.append(f"• Will generate {project_config.framework.value} components with appropriate imports")
    
    # Styling intelligence
    if project_config.styling_system:
        if project_config.styling_system.value == "TAILWIND":
            intelligence_info.append("• Will use Tailwind CSS classes for styling")
        elif project_config.styling_system.value == "CHAKRA_UI":
            intelligence_info.append("• Will use Chakra UI components and props")
            intelligence_info.append("• Will avoid Tailwind classes to prevent conflicts")
    
    # TypeScript intelligence
    if project_config.typescript:
        intelligence_info.append("• Will include TypeScript interfaces and proper typing")
    
    # Component patterns intelligence
    if hasattr(project_config, 'component_patterns') and project_config.component_patterns:
        intelligence_info.append(f"• Will follow your existing component patterns ({len(project_config.component_patterns)} detected)")
    
    for info in intelligence_info:
        console.print(info, style="dim white")
    
    # Explanations if requested
    if explain:
        console.print("\n💡 HOW CONTEXT AFFECTS GENERATION", style="bold blue")
        console.print("=" * 50)
        
        explanation_panel = Panel(
            """[bold]Context Prioritization:[/bold]
• Framework-specific patterns get 70% priority weight
• Styling system patterns get 25% priority weight  
• Project-specific patterns get 5% priority weight

[bold]Conflict Resolution:[/bold]
• Chakra UI + Tailwind → Prioritizes Chakra UI, filters Tailwind
• Multiple styling systems → Uses most confident detection
• Missing patterns → Falls back to framework defaults

[bold]Quality Validation:[/bold]
• Validates against detected styling system
• Ensures import consistency with project structure
• Applies framework-specific best practices""",
            title="Intelligence Details",
            border_style="dim"
        )
        console.print(explanation_panel)
    
    # Helpful tips
    console.print("\n💡 TIPS", style="bold yellow")
    console.print("=" * 50)
    console.print("• Use specific prompts: 'Create a Chakra UI button' vs 'Create a button'")
    console.print("• Mention styling preferences: 'with dark mode support' or 'responsive design'")
    console.print("• Reference existing components: 'similar to the existing UserCard component'")
    console.print(f"• Run 'palette generate --help' to see all available options")


def _show_context_table(project_config, context_stats: dict, pattern_recommendations: list):
    """Show context analysis in compact table format"""
    
    table = Table(title="Project Context Summary", show_header=True, header_style="bold cyan")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="green")
    table.add_column("Status", style="yellow")
    
    # Basic config
    table.add_row(
        "Framework",
        project_config.framework.value if project_config.framework else "Unknown",
        "✅" if project_config.framework else "❌"
    )
    
    table.add_row(
        "Styling",
        project_config.styling_system.value if project_config.styling_system else "Unknown",
        "✅" if project_config.styling_system else "❌"
    )
    
    table.add_row(
        "TypeScript",
        "Enabled" if project_config.typescript else "Disabled",
        "✅" if project_config.typescript else "⚠️"
    )
    
    # Context stats
    if context_stats:
        token_budget = context_stats.get('token_budget', {})
        utilization = token_budget.get('utilization', 0)
        table.add_row(
            "Token Usage",
            f"{utilization:.1%}",
            "✅" if utilization <= 0.087 else "⚠️"
        )
    
    # Patterns
    table.add_row(
        "Patterns Available",
        str(len(pattern_recommendations)),
        "✅" if pattern_recommendations else "⚠️"
    )
    
    console.print(table)


def _show_context_json(project_config, context_stats: dict, pattern_recommendations: list):
    """Show context analysis in JSON format"""
    
    context_data = {
        "project_config": {
            "framework": project_config.framework.value if project_config.framework else None,
            "styling_system": project_config.styling_system.value if project_config.styling_system else None,
            "typescript": project_config.typescript,
            "confidence_score": getattr(project_config, 'confidence_score', None)
        },
        "context_optimization": context_stats,
        "pattern_recommendations": [
            {
                "name": pattern.name,
                "framework": pattern.framework.value if hasattr(pattern, 'framework') and pattern.framework else None,
                "styling_system": pattern.styling_system.value if hasattr(pattern, 'styling_system') and pattern.styling_system else None,
                "use_cases": getattr(pattern, 'use_cases', [])
            }
            for pattern in pattern_recommendations
        ]
    }
    
    console.print(json.dumps(context_data, indent=2))


def _create_generation_explanations(prompt: str, framework: str, styling: str, ui: str, type: str, detected_config) -> List[Dict[str, Any]]:
    """Create explanations for generation decisions"""
    
    explanations = []
    
    # Framework selection explanation
    if detected_config and detected_config.framework:
        explanations.append({
            "category": "Framework Selection",
            "decision": f"Selected {framework}",
            "reasoning": f"Auto-detected {framework} from package.json dependencies and project structure",
            "confidence": getattr(detected_config, 'confidence_score', 1.0),
            "impact": "Determines component syntax, imports, and best practices"
        })
    else:
        explanations.append({
            "category": "Framework Selection", 
            "decision": f"Using {framework} (default)",
            "reasoning": "No framework auto-detected, using default React",
            "confidence": 0.5,
            "impact": "May not match your project structure perfectly"
        })
    
    # Styling system explanation
    if detected_config and detected_config.styling_system:
        styling_system = detected_config.styling_system.value
        if styling_system == "TAILWIND":
            explanations.append({
                "category": "Styling Strategy",
                "decision": "Using Tailwind CSS classes",
                "reasoning": "Detected tailwind.config.js and Tailwind dependencies",
                "confidence": 0.95,
                "impact": "Component will use utility-first CSS classes"
            })
        elif styling_system == "CHAKRA_UI":
            explanations.append({
                "category": "Styling Strategy",
                "decision": "Using Chakra UI components",
                "reasoning": "Detected @chakra-ui packages in dependencies",
                "confidence": 0.95,
                "impact": "Will use Chakra component props and avoid Tailwind conflicts"
            })
    
    # Component type explanation
    component_type_reasoning = {
        "single": "Simple, self-contained component in one file",
        "multi": "Complex component split across multiple files",
        "page": "Full page component with routing structure",
        "feature": "Feature module with multiple related components"
    }
    
    explanations.append({
        "category": "Component Architecture",
        "decision": f"Generating {type} component",
        "reasoning": component_type_reasoning.get(type, "Based on prompt analysis"),
        "confidence": 0.8,
        "impact": "Determines file structure and component organization"
    })
    
    # TypeScript explanation
    if detected_config and detected_config.typescript:
        explanations.append({
            "category": "Type Safety",
            "decision": "Including TypeScript interfaces",
            "reasoning": "Detected TypeScript configuration and .ts/.tsx files",
            "confidence": 1.0,
            "impact": "Provides type safety and better IDE support"
        })
    
    # UI Library explanation
    if ui != "none":
        explanations.append({
            "category": "UI Components",
            "decision": f"Integrating {ui} components",
            "reasoning": "Manually specified component library",
            "confidence": 1.0,
            "impact": "Will use pre-built components and design system"
        })
    
    # Prompt analysis explanation
    prompt_insights = _analyze_prompt_complexity(prompt)
    explanations.append({
        "category": "Prompt Analysis",
        "decision": f"Complexity level: {prompt_insights['complexity']}",
        "reasoning": prompt_insights['reasoning'],
        "confidence": prompt_insights['confidence'],
        "impact": prompt_insights['impact']
    })
    
    return explanations


def _analyze_prompt_complexity(prompt: str) -> Dict[str, Any]:
    """Analyze prompt complexity and requirements"""
    
    prompt_lower = prompt.lower()
    
    # Check for complexity indicators
    complex_keywords = ['dashboard', 'form', 'validation', 'authentication', 'api', 'database', 'chart', 'graph']
    interactive_keywords = ['modal', 'dropdown', 'tabs', 'accordion', 'carousel', 'navigation']
    simple_keywords = ['button', 'card', 'header', 'footer', 'text', 'image']
    
    complexity_score = 0
    detected_features = []
    
    # Score complexity
    for keyword in complex_keywords:
        if keyword in prompt_lower:
            complexity_score += 3
            detected_features.append(keyword)
    
    for keyword in interactive_keywords:
        if keyword in prompt_lower:
            complexity_score += 2
            detected_features.append(keyword)
    
    for keyword in simple_keywords:
        if keyword in prompt_lower:
            complexity_score += 1
            detected_features.append(keyword)
    
    # Determine complexity level
    if complexity_score >= 8:
        complexity = "High"
        reasoning = f"Complex component with multiple features: {', '.join(detected_features[:3])}"
        impact = "Will generate comprehensive component with proper state management"
        confidence = 0.9
    elif complexity_score >= 4:
        complexity = "Medium"
        reasoning = f"Interactive component with moderate complexity: {', '.join(detected_features[:2])}"
        impact = "Will include necessary interactivity and styling"
        confidence = 0.8
    else:
        complexity = "Simple"
        reasoning = "Basic component with minimal features"
        impact = "Will generate clean, focused component"
        confidence = 0.7
    
    return {
        "complexity": complexity,
        "reasoning": reasoning,
        "impact": impact,
        "confidence": confidence,
        "features": detected_features
    }


def _display_generation_explanations(explanations: List[Dict[str, Any]], generated_files: Dict[str, str]):
    """Display detailed generation explanations"""
    
    console.print("\n🧠 GENERATION DECISION EXPLANATIONS", style="bold blue")
    console.print("=" * 60)
    
    for i, explanation in enumerate(explanations, 1):
        # Create explanation panel  
        confidence_color = "green" if explanation['confidence'] >= 0.8 else "yellow" if explanation['confidence'] >= 0.6 else "red"
        confidence_text = f"[{confidence_color}]{explanation['confidence']:.0%} confidence[/{confidence_color}]"
        
        explanation_content = f"""[bold]{explanation['decision']}[/bold]

[yellow]Why:[/yellow] {explanation['reasoning']}

[blue]Impact:[/blue] {explanation['impact']}

[white]Confidence:[/white] {confidence_text}"""
        
        panel = Panel(
            explanation_content,
            title=f"{i}. {explanation['category']}",
            border_style="dim",
            expand=False
        )
        console.print(panel)
    
    # Code generation insights
    console.print("\n📝 CODE GENERATION INSIGHTS", style="bold blue")
    console.print("=" * 60)
    
    insights = []
    
    # File analysis
    file_count = len(generated_files)
    if file_count == 1:
        insights.append("• Generated single-file component for simplicity")
    else:
        insights.append(f"• Generated {file_count} files for better code organization")
    
    # Check for common patterns in generated code
    all_code = " ".join(generated_files.values())
    
    if "useState" in all_code:
        insights.append("• Added React hooks for state management")
    if "interface" in all_code:
        insights.append("• Included TypeScript interfaces for type safety")
    if "className=" in all_code:
        insights.append("• Used CSS classes for styling")
    if "onClick" in all_code or "onChange" in all_code:
        insights.append("• Added event handlers for interactivity")
    if "export default" in all_code:
        insights.append("• Used default exports following React conventions")
    
    for insight in insights:
        console.print(f"[dim]{insight}[/dim]")
    
    # Tips based on explanations
    console.print("\n💡 OPTIMIZATION TIPS", style="bold yellow")
    console.print("=" * 60)
    
    tips = []
    
    # Framework-specific tips
    framework_explanation = next((e for e in explanations if e['category'] == 'Framework Selection'), None)
    if framework_explanation and framework_explanation['confidence'] < 0.8:
        tips.append("• Specify framework explicitly: --framework react|next.js|remix")
    
    # Styling tips
    styling_explanation = next((e for e in explanations if e['category'] == 'Styling Strategy'), None) 
    if not styling_explanation:
        tips.append("• Add styling system to project for better auto-detection")
    
    # Complexity tips
    prompt_explanation = next((e for e in explanations if e['category'] == 'Prompt Analysis'), None)
    if prompt_explanation and prompt_explanation['complexity'] == 'Simple':
        tips.append("• For more complex components, describe specific features needed")
    
    if not tips:
        tips.append("• Your project is well-configured for optimal generation!")
    
    for tip in tips:
        console.print(f"[dim]{tip}[/dim]")


def _show_suggestions_detailed(suggestions: List, is_completion: bool = False):
    """Show detailed suggestions with rich formatting"""
    
    suggestion_type = "Prompt Completions" if is_completion else "Contextual Suggestions"
    console.print(f"\n💡 {suggestion_type.upper()}", style="bold blue")
    console.print("=" * 60)
    
    for i, suggestion in enumerate(suggestions, 1):
        # Confidence indicator
        confidence_color = "green" if suggestion.confidence >= 0.8 else "yellow" if suggestion.confidence >= 0.6 else "red"
        confidence_indicator = "🔥" if suggestion.confidence >= 0.9 else "✨" if suggestion.confidence >= 0.7 else "💡"
        
        # Complexity indicator
        complexity_colors = {"simple": "green", "medium": "yellow", "complex": "red"}
        complexity_color = complexity_colors.get(suggestion.complexity, "white")
        
        suggestion_content = f"""[bold cyan]💻 {suggestion.prompt}[/bold cyan]

[yellow]Category:[/yellow] {suggestion.category}
[blue]Reasoning:[/blue] {suggestion.reasoning}
[{complexity_color}]Complexity:[/{complexity_color}] {suggestion.complexity.title()}
[white]Confidence:[/white] [{confidence_color}]{suggestion.confidence:.0%}[/{confidence_color}] {confidence_indicator}"""
        
        if suggestion.related_files:
            files_str = ", ".join([Path(f).name for f in suggestion.related_files[:3]])
            suggestion_content += f"\n[dim]Related files:[/dim] {files_str}"
        
        panel = Panel(
            suggestion_content,
            title=f"{i}. Suggestion",
            border_style="dim",
            expand=False
        )
        console.print(panel)
    
    # Show usage tips
    console.print(f"\n💡 USAGE TIPS", style="bold yellow")
    console.print("=" * 60)
    console.print("• Copy any prompt above and use with: [cyan]palette generate \"<prompt>\"[/cyan]")
    console.print("• Add [cyan]--explain[/cyan] to see generation decision details")
    console.print("• Use [cyan]--preview[/cyan] to review code before creating files")
    if not is_completion:
        console.print("• Try [cyan]palette suggest --complete \"partial prompt\"[/cyan] for auto-completion")


def _show_suggestions_simple(suggestions: List):
    """Show simple list of suggestions"""
    
    console.print("\n💡 SUGGESTED PROMPTS", style="bold blue")
    console.print("=" * 50)
    
    for i, suggestion in enumerate(suggestions, 1):
        confidence_indicator = "🔥" if suggestion.confidence >= 0.8 else "✨" if suggestion.confidence >= 0.6 else "💡"
        console.print(f"{i:2d}. {confidence_indicator} [cyan]{suggestion.prompt}[/cyan] [dim]({suggestion.category})[/dim]")
    
    console.print(f"\n[dim]Use: palette generate \"<prompt from above>\"[/dim]")


def _show_suggestions_json(suggestions: List):
    """Show suggestions in JSON format"""
    
    suggestions_data = []
    for suggestion in suggestions:
        suggestions_data.append({
            "prompt": suggestion.prompt,
            "category": suggestion.category,
            "confidence": suggestion.confidence,
            "reasoning": suggestion.reasoning,
            "complexity": suggestion.complexity,
            "related_files": suggestion.related_files
        })
    
    console.print(json.dumps({"suggestions": suggestions_data}, indent=2))


def _resolve_ui_library_selection(ui_choice: str, project_path: str, detected_config: Optional[Any]) -> str:
    """
    Resolve UI library selection with comprehensive validation and auto-detection.
    
    Args:
        ui_choice: User's UI library choice ('auto-detect' or specific library)
        project_path: Path to the project
        detected_config: Configuration detected by intelligence hub
        
    Returns:
        Resolved UI library name
    """
    
    try:
        from ..intelligence.ui_library_validator import EnhancedUILibraryValidator, UILibraryCompatibility
        validator = EnhancedUILibraryValidator()
        
        if ui_choice == 'auto-detect':
            # Use comprehensive analysis to recommend UI library
            recommended_ui = validator.get_recommended_ui_library(project_path)
            
            if recommended_ui and recommended_ui != 'none':
                # Validate the recommendation
                validation_result = validator.validate_ui_library_choice(recommended_ui, project_path)
                
                if validation_result.compatibility in [UILibraryCompatibility.PERFECT, UILibraryCompatibility.GOOD]:
                    console.print(f"✅ [green]Auto-detected UI library: {recommended_ui}[/green]")
                    console.print(f"   [dim]Confidence: {validation_result.confidence:.1%}[/dim]")
                    
                    # Show evidence if available
                    if validation_result.evidence:
                        for evidence in validation_result.evidence[:2]:  # Show top 2 pieces of evidence
                            console.print(f"   [dim]• {evidence}[/dim]")
                    
                    return recommended_ui
                else:
                    console.print(f"⚠️ [yellow]Detected {recommended_ui} but compatibility issues found[/yellow]")
                    for warning in validation_result.warnings[:2]:
                        console.print(f"   [dim]• {warning}[/dim]")
            
            console.print("ℹ️ [dim]No UI library auto-detected - using 'none'[/dim]")
            return 'none'
        
        elif ui_choice != 'none':
            # Comprehensive validation of explicit UI library choice
            validation_result = validator.validate_ui_library_choice(ui_choice, project_path)
            
            if validation_result.compatibility == UILibraryCompatibility.PERFECT:
                console.print(f"✅ [green]Using {ui_choice} (perfect compatibility)[/green]")
                console.print(f"   [dim]Confidence: {validation_result.confidence:.1%}[/dim]")
                
            elif validation_result.compatibility == UILibraryCompatibility.GOOD:
                console.print(f"✅ [green]Using {ui_choice} (good compatibility)[/green]")
                if validation_result.warnings:
                    console.print(f"   [yellow]Note: {validation_result.warnings[0]}[/yellow]")
                    
            elif validation_result.compatibility == UILibraryCompatibility.WARNING:
                console.print(f"⚠️ [yellow]Using {ui_choice} with warnings[/yellow]")
                for warning in validation_result.warnings[:2]:
                    console.print(f"   [yellow]• {warning}[/yellow]")
                
                # Show missing dependencies
                if validation_result.missing_dependencies:
                    missing_deps = ', '.join(validation_result.missing_dependencies)
                    console.print(f"   [dim]Install: npm install {missing_deps}[/dim]")
                    
            elif validation_result.compatibility == UILibraryCompatibility.CONFLICT:
                console.print(f"🚨 [red]CRITICAL: {ui_choice} conflicts with project setup[/red]")
                for conflict in validation_result.conflicting_systems:
                    console.print(f"   [red]• Conflicts with {conflict}[/red]")
                
                # Show recommendations for resolving conflicts
                if validation_result.recommendations:
                    console.print("   [dim]Recommendations:[/dim]")
                    for rec in validation_result.recommendations[:2]:
                        console.print(f"   [dim]• {rec}[/dim]")
                
                # Still proceed but warn user
                if not click.confirm(f"\nProceed with {ui_choice} despite conflicts?", default=False):
                    console.print("[yellow]Switching to 'none' - no UI library[/yellow]")
                    return 'none'
            
            else:  # UNKNOWN compatibility
                console.print(f"❓ [yellow]Using {ui_choice} (compatibility unknown)[/yellow]")
                console.print(f"   [dim]Confidence: {validation_result.confidence:.1%}[/dim]")
        
        return ui_choice
    
    except ImportError:
        # Fallback to basic validation if enhanced validator not available
        console.print("[dim]Using basic UI library validation[/dim]")
        return _resolve_ui_library_selection_basic(ui_choice, project_path, detected_config)
    
    except Exception as e:
        console.print(f"[yellow]Warning: UI library validation failed: {e}[/yellow]")
        console.print("[dim]Proceeding with basic validation[/dim]")
        return _resolve_ui_library_selection_basic(ui_choice, project_path, detected_config)


def _resolve_ui_library_selection_basic(ui_choice: str, project_path: str, detected_config: Optional[Any]) -> str:
    """
    Basic UI library selection (fallback when enhanced validation fails).
    """
    
    # UI library dependency patterns
    ui_library_deps = {
        'chakra-ui': ['@chakra-ui/react', '@emotion/react', '@emotion/styled'],
        'material-ui': ['@mui/material', '@emotion/react', '@emotion/styled'],
        'ant-design': ['antd', '@ant-design/icons'],
        'mantine': ['@mantine/core', '@mantine/hooks'],
        'react-bootstrap': ['react-bootstrap', 'bootstrap'],
        'semantic-ui': ['semantic-ui-react', 'semantic-ui-css'],
        'grommet': ['grommet', 'grommet-icons'],
        'headless-ui': ['@headlessui/react'],
        'shadcn/ui': ['@radix-ui/react-slot', 'class-variance-authority', 'clsx']
    }
    
    if ui_choice == 'auto-detect':
        # Try to detect UI library from project dependencies
        detected_ui = _detect_ui_library_from_project(project_path, ui_library_deps)
        
        if detected_ui:
            console.print(f"✅ [green]Auto-detected UI library: {detected_ui}[/green]")
            return detected_ui
        else:
            # Check if detected_config has styling system info
            if detected_config and hasattr(detected_config, 'styling_analysis'):
                styling_analysis = detected_config.styling_analysis
                if hasattr(styling_analysis, 'primary_system'):
                    primary_system = styling_analysis.primary_system.value
                    if primary_system in ['chakra-ui', 'material-ui']:
                        console.print(f"✅ [green]Auto-detected UI library from styling analysis: {primary_system}[/green]")
                        return primary_system
            
            console.print("ℹ️ [dim]No UI library detected - using 'none'[/dim]")
            return 'none'
    
    elif ui_choice != 'none':
        # Validate explicit UI library choice
        is_valid = _validate_ui_library_choice(ui_choice, project_path, ui_library_deps)
        
        if not is_valid:
            # Show warning but don't block generation
            required_deps = ui_library_deps.get(ui_choice, [])
            if required_deps:
                console.print(f"⚠️ [yellow]Warning: {ui_choice} requires dependencies: {', '.join(required_deps)}[/yellow]")
                console.print(f"   [dim]Install with: npm install {' '.join(required_deps)}[/dim]")
            else:
                console.print(f"⚠️ [yellow]Warning: {ui_choice} dependencies not found in project[/yellow]")
        else:
            console.print(f"✅ [green]Using {ui_choice} (found in dependencies)[/green]")
    
    return ui_choice


def _detect_ui_library_from_project(project_path: str, ui_library_deps: Dict[str, List[str]]) -> Optional[str]:
    """
    Detect UI library from project's package.json dependencies.
    
    Args:
        project_path: Path to the project
        ui_library_deps: Mapping of UI libraries to their required dependencies
        
    Returns:
        Detected UI library name or None
    """
    
    package_json_path = Path(project_path) / "package.json" 
    
    if not package_json_path.exists():
        return None
    
    try:
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # Get all dependencies
        all_deps = set()
        all_deps.update(package_data.get('dependencies', {}).keys())
        all_deps.update(package_data.get('devDependencies', {}).keys())
        
        # Check each UI library
        for ui_lib, required_deps in ui_library_deps.items():
            # Check if any of the required dependencies are present
            if any(dep in all_deps for dep in required_deps):
                # For more specific detection, check primary deps first
                primary_deps = {
                    'chakra-ui': '@chakra-ui/react',
                    'material-ui': '@mui/material', 
                    'ant-design': 'antd',
                    'mantine': '@mantine/core',
                    'react-bootstrap': 'react-bootstrap',
                    'semantic-ui': 'semantic-ui-react',
                    'grommet': 'grommet',
                    'headless-ui': '@headlessui/react',
                    'shadcn/ui': '@radix-ui/react-slot'
                }
                
                if ui_lib in primary_deps and primary_deps[ui_lib] in all_deps:
                    return ui_lib
        
        return None
        
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return None


def _validate_ui_library_choice(ui_choice: str, project_path: str, ui_library_deps: Dict[str, List[str]]) -> bool:
    """
    Validate that the chosen UI library has required dependencies in the project.
    
    Args:
        ui_choice: Chosen UI library
        project_path: Path to the project  
        ui_library_deps: Mapping of UI libraries to their required dependencies
        
    Returns:
        True if valid, False otherwise
    """
    
    if ui_choice not in ui_library_deps:
        return True  # Unknown library, assume valid
    
    package_json_path = Path(project_path) / "package.json"
    
    if not package_json_path.exists():
        return False
    
    try:
        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # Get all dependencies
        all_deps = set()
        all_deps.update(package_data.get('dependencies', {}).keys())
        all_deps.update(package_data.get('devDependencies', {}).keys())
        
        required_deps = ui_library_deps[ui_choice]
        
        # Check if at least one required dependency is present
        return any(dep in all_deps for dep in required_deps)
        
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return False


if __name__ == "__main__":
    main()