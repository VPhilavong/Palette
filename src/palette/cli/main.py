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
def generate(prompt: str, preview: bool, output: Optional[str], model: str):
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

        # Generate component
        generator = UIGenerator(model=model)
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
def init(type: Optional[str], styling: Optional[str], ui_lib: Optional[str], components: bool, utils: bool):
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


if __name__ == "__main__":
    main()
