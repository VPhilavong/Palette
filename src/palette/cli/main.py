import os
import sys
import shutil
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

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
@click.option(
    "--qa/--no-qa", default=True, help="Enable quality assurance with auto-fixing"
)
def generate(prompt: str, preview: bool, output: Optional[str], model: str, enhanced: bool, qa: bool):
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

        # Generate component with enhanced mode and QA
        generator = UIGenerator(
            model=model, 
            project_path=os.getcwd(), 
            enhanced_mode=enhanced,
            quality_assurance=qa
        )
        
        if qa:
            # Use QA-enabled generation
            component_code, quality_report = generator.generate_component_with_qa(prompt, context)
            
            # QA includes formatting, so use the refined code directly
            formatted_code = component_code
            
            # Show quality summary
            if quality_report.score < 85:
                console.print(f"[yellow]⚠️ Quality score: {quality_report.score:.1f}/100 (below 85)[/yellow]")
            else:
                console.print(f"[green]✅ Quality score: {quality_report.score:.1f}/100[/green]")
        else:
            # Use basic generation without QA
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
    
    console.print(
        Panel(
            "[bold blue]Palette Project Initializer[/bold blue]",
            title="Code Palette",
            border_style="blue",
        )
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
    
    # Create base directories
    base_path = os.path.join(project_name)
    src_path = os.path.join(base_path, "src")
    os.makedirs(src_path, exist_ok=True)
    
    # Create package.json based on framework
    _create_package_json(base_path, framework, styling, ui_lib)
    
    # Create framework-specific files
    if framework == "react":
        _create_react_structure(src_path, styling, ui_lib)
    elif framework == "nextjs":
        _create_nextjs_structure(base_path, styling, ui_lib)
    elif framework == "vue":
        _create_vue_structure(src_path, styling, ui_lib)
    
    # Add components if requested
    if components:
        _create_component_templates(src_path, framework)
    
    # Add utils if requested
    if utils:
        _create_utility_templates(src_path)
    
    # Create configuration files
    _create_config_files(base_path, framework, styling)
    
    # Create public directory and index.html for React projects
    if framework == "react":
        _create_react_public_files(base_path)


def _create_package_json(base_path: str, framework: str, styling: str, ui_lib: str):
    """Create package.json with appropriate dependencies"""
    
    # Base dependencies for all frameworks
    dependencies = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0"
    }
    
    dev_dependencies = {
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0",
        "typescript": "^4.9.5"  # Use TypeScript 4.x for React Scripts compatibility
    }
    
    # Add framework-specific dependencies
    if framework == "nextjs":
        dependencies.update({
            "next": "^14.0.0"
        })
        dev_dependencies.update({
            "@types/node": "^20.0.0"
        })
    elif framework == "vue":
        dependencies = {
            "vue": "^3.3.0"
        }
        dev_dependencies = {
            "@vue/compiler-sfc": "^3.3.0",
            "typescript": "^5.0.0"
        }
    else:  # React
        # Add react-scripts for Create React App functionality
        dev_dependencies.update({
            "react-scripts": "^5.0.1"
        })
    
    # Add styling dependencies
    if styling == "tailwind":
        dev_dependencies.update({
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.0",
            "postcss": "^8.4.0"
        })
    
    # Add UI library dependencies
    if ui_lib == "shadcn":
        dev_dependencies.update({
            "class-variance-authority": "^0.7.0",
            "clsx": "^2.0.0",
            "tailwind-merge": "^2.0.0"
        })
    
    # Create package.json content
    package_json = {
        "name": os.path.basename(base_path),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev" if framework == "nextjs" else "vite" if framework == "vue" else "react-scripts start",
            "build": "next build" if framework == "nextjs" else "vite build" if framework == "vue" else "react-scripts build",
            "start": "next start" if framework == "nextjs" else "vite preview" if framework == "vue" else "react-scripts start"
        },
        "dependencies": dependencies,
        "devDependencies": dev_dependencies
    }
    
    # Add browser field for React projects (required by react-scripts)
    if framework == "react":
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
    
    # Write package.json
    import json
    with open(os.path.join(base_path, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)


def _create_react_structure(src_path: str, styling: str, ui_lib: str):
    """Create React project structure"""
    
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
    
    # Only create App.css for non-Tailwind projects
    if styling != "tailwind":
        app_css_content = '''body {
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
        with open(os.path.join(src_path, "App.css"), "w") as f:
            f.write(app_css_content)


def _create_nextjs_structure(base_path: str, styling: str, ui_lib: str):
    """Create Next.js project structure"""
    
    # Create pages directory
    pages_path = os.path.join(base_path, "pages")
    os.makedirs(pages_path, exist_ok=True)
    
    # Create main page
    page_content = '''import type { NextPage } from 'next'
import Head from 'next/head'

const Home: NextPage = () => {
  return (
    <div>
      <Head>
        <title>Next.js App</title>
        <meta name="description" content="Generated with Palette" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <h1>Welcome to Next.js!</h1>
        <p>Get started by editing pages/index.tsx</p>
      </main>
    </div>
  )
}

export default Home
'''
    
    with open(os.path.join(pages_path, "index.tsx"), "w") as f:
        f.write(page_content)
    
    # Create _app.tsx
    app_content = '''import type { AppProps } from 'next/app'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}
'''
    
    with open(os.path.join(pages_path, "_app.tsx"), "w") as f:
        f.write(app_content)
    
    # Create styles directory
    styles_path = os.path.join(base_path, "styles")
    os.makedirs(styles_path, exist_ok=True)
    
    # Create global CSS
    if styling == "tailwind":
        css_content = '''@tailwind base;
@tailwind components;
@tailwind utilities;
'''
    else:
        css_content = '''html,
body {
  padding: 0;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen,
    Ubuntu, Cantarell, Fira Sans, Droid Sans, Helvetica Neue, sans-serif;
}

* {
  box-sizing: border-box;
}
'''
    
    with open(os.path.join(styles_path, "globals.css"), "w") as f:
        f.write(css_content)


def _create_vue_structure(src_path: str, styling: str, ui_lib: str):
    """Create Vue project structure"""
    
    # Create main App component
    app_content = '''<template>
  <div id="app">
    <header>
      <h1>Welcome to Vue</h1>
      <p>Edit src/App.vue and save to reload.</p>
    </header>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'App'
})
</script>

<style>
#app {
  text-align: center;
  padding: 20px;
}
</style>
'''
    
    with open(os.path.join(src_path, "App.vue"), "w") as f:
        f.write(app_content)
    
    # Create main.ts
    main_content = '''import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')
'''
    
    with open(os.path.join(src_path, "main.ts"), "w") as f:
        f.write(main_content)
    
    # Create style.css
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
'''
    
    with open(os.path.join(src_path, "style.css"), "w") as f:
        f.write(css_content)


def _create_component_templates(src_path: str, framework: str):
    """Create component template files"""
    
    components_path = os.path.join(src_path, "components")
    os.makedirs(components_path, exist_ok=True)
    
    if framework == "react":
        # Create a sample React component
        component_content = '''import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  disabled = false 
}) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors';
  const variantClasses = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300'
  };
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;
'''
        
        with open(os.path.join(components_path, "Button.tsx"), "w") as f:
            f.write(component_content)
    
    elif framework == "vue":
        # Create a sample Vue component
        component_content = '''<template>
  <button
    :class="buttonClasses"
    @click="$emit('click')"
    :disabled="disabled"
  >
    <slot></slot>
  </button>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'

export default defineComponent({
  name: 'Button',
  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: (value: string) => ['primary', 'secondary'].includes(value)
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click'],
  setup(props) {
    const buttonClasses = computed(() => {
      const baseClasses = 'px-4 py-2 rounded font-medium transition-colors'
      const variantClasses = {
        primary: 'bg-blue-500 text-white hover:bg-blue-600',
        secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300'
      }
      return `${baseClasses} ${variantClasses[props.variant]}`
    })
    
    return { buttonClasses }
  }
})
</script>
'''
        
        with open(os.path.join(components_path, "Button.vue"), "w") as f:
            f.write(component_content)


def _create_utility_templates(src_path: str):
    """Create utility template files"""
    
    utils_path = os.path.join(src_path, "utils")
    os.makedirs(utils_path, exist_ok=True)
    
    # Create a utility function file
    utils_content = '''/**
 * Utility functions for the application
 */

/**
 * Combines multiple class names into a single string
 * @param classes - Array of class names or objects
 * @returns Combined class string
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Formats a date to a readable string
 * @param date - Date to format
 * @returns Formatted date string
 */
export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

/**
 * Debounces a function call
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
'''
    
    with open(os.path.join(utils_path, "index.ts"), "w") as f:
        f.write(utils_content)


def _create_config_files(base_path: str, framework: str, styling: str):
    """Create configuration files"""
    
    # Create TypeScript config
    tsconfig_content = '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
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
  "include": ["src"]
}
'''
    
    with open(os.path.join(base_path, "tsconfig.json"), "w") as f:
        f.write(tsconfig_content)
    
    # Create Tailwind config if using Tailwind
    if styling == "tailwind":
        tailwind_content = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./pages/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
'''
        
        with open(os.path.join(base_path, "tailwind.config.js"), "w") as f:
            f.write(tailwind_content)
        
        # Create PostCSS config
        postcss_content = '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''
        
        with open(os.path.join(base_path, "postcss.config.js"), "w") as f:
            f.write(postcss_content)
    
    # Create README
    readme_content = f'''# {os.path.basename(base_path)}

This project was generated with Palette.

## Getting Started

First, install the dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Framework: {framework}
## Styling: {styling}

## Learn More

To learn more about the technologies used in this project:

- [React](https://reactjs.org/) - A JavaScript library for building user interfaces
- [Next.js](https://nextjs.org/) - The React Framework for Production
- [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework
- [TypeScript](https://www.typescriptlang.org/) - JavaScript with syntax for types
'''
    
    with open(os.path.join(base_path, "README.md"), "w") as f:
        f.write(readme_content)


def _create_react_public_files(base_path: str):
    """Create public directory and files for React projects"""
    
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
      content="Web site created using Palette"
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
