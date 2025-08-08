#!/usr/bin/env python3
"""
Simple Palette CLI - Focus on working generation over complex features
"""

import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv(verbose=False)

from .simple_generator import create_generator
from .simple_analyzer import SimpleAnalyzer  
from .simple_file_manager import SimpleFileManager


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Palette - Simple, reliable React component generator"""
    pass


@main.command()
@click.argument("prompt", required=True)
@click.option("--preview", is_flag=True, help="Preview component before saving")
@click.option("--output", "-o", help="Output file path")
@click.option("--model", default="gpt-4o-mini", help="LLM model to use")
@click.option("--ui", default="auto", help="UI library (auto, shadcn/ui, none)")
@click.option("--style", default="auto", help="Styling (auto, tailwind, css)")
@click.option("--no-save", is_flag=True, help="Generate without saving to file")
def generate(
    prompt: str, 
    preview: bool, 
    output: Optional[str], 
    model: str,
    ui: str,
    style: str,
    no_save: bool
):
    """Generate a React component from a natural language prompt"""
    
    try:
        # Analyze project
        print("📊 Analyzing project...")
        analyzer = SimpleAnalyzer()
        context = analyzer.analyze()
        
        # Override context with CLI options
        if ui != "auto":
            context['ui_library'] = ui
        if style != "auto":
            context['styling'] = style
        
        print(f"✓ {context['framework']} + {context['styling']} + {context['ui_library']}")
        
        # Generate component
        print(f"🎨 Generating: {prompt}")
        generator = create_generator(context['ui_library'], model)
        component_code = generator.generate_component(prompt, context)
        
        # Preview if requested
        if preview or no_save:
            print("\n" + "=" * 60)
            print("GENERATED COMPONENT:")
            print("=" * 60)
            print(component_code)
            print("=" * 60)
            
            if no_save:
                return
            
            if not click.confirm("\nSave this component?"):
                print("❌ Generation cancelled")
                return
        
        # Save component
        if not no_save:
            print("💾 Saving component...")
            file_manager = SimpleFileManager()
            file_path = file_manager.save_component(component_code, output, context)
            print(f"✅ Component saved: {file_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
def analyze():
    """Analyze current project structure and configuration"""
    
    try:
        analyzer = SimpleAnalyzer()
        analyzer.print_analysis()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument("prompt", required=True)
@click.option("--model", default="gpt-4o-mini", help="LLM model to use")
@click.option("--ui", default="auto", help="UI library (auto, shadcn/ui, none)")
def preview(prompt: str, model: str, ui: str):
    """Preview a component without saving it"""
    
    try:
        # Analyze project
        analyzer = SimpleAnalyzer()
        context = analyzer.analyze()
        
        # Override UI library if specified
        if ui != "auto":
            context['ui_library'] = ui
        
        # Generate component
        print(f"👀 Previewing: {prompt}")
        generator = create_generator(context['ui_library'], model)
        component_code = generator.generate_component(prompt, context)
        
        # Display preview
        print("\n" + "=" * 60)
        print("COMPONENT PREVIEW:")
        print("=" * 60)
        print(component_code)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument("prompt", required=True) 
@click.option("--output", "-o", help="Output directory")
@click.option("--model", default="gpt-4o-mini", help="LLM model to use")
@click.option("--stories", is_flag=True, help="Include Storybook stories")
@click.option("--tests", is_flag=True, help="Include test files")
def create(
    prompt: str, 
    output: Optional[str], 
    model: str, 
    stories: bool, 
    tests: bool
):
    """Create complete component with styles, stories, and tests"""
    
    try:
        # Analyze project
        print("📊 Analyzing project...")
        analyzer = SimpleAnalyzer()
        context = analyzer.analyze()
        
        print(f"✓ {context['framework']} + {context['styling']} + {context['ui_library']}")
        
        # Generate component
        print(f"🎨 Creating component: {prompt}")
        generator = create_generator(context['ui_library'], model)
        component_code = generator.generate_component(prompt, context)
        
        # Extract component name
        import re
        match = re.search(r'const\s+(\w+)|function\s+(\w+)|export\s+default\s+(\w+)', component_code)
        component_name = 'Component'
        if match:
            component_name = match.group(1) or match.group(2) or match.group(3)
        
        # Save with additional files
        print("💾 Creating component files...")
        file_manager = SimpleFileManager()
        
        if output:
            file_manager.project_path = output
        
        saved_files = file_manager.save_component_with_files(
            component_code,
            component_name, 
            context,
            include_styles=True,
            include_stories=stories,
            include_tests=tests
        )
        
        print("✅ Component created successfully:")
        for file_type, file_path in saved_files.items():
            print(f"  {file_type}: {file_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
def check():
    """Check system requirements and API keys"""
    
    print("🔍 Checking Palette setup...")
    print("-" * 40)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}"
        print(f"✅ OpenAI API Key: {masked_key}")
    else:
        print("❌ OpenAI API Key: Not found")
        print("   Set OPENAI_API_KEY environment variable")
    
    # Check project
    try:
        analyzer = SimpleAnalyzer()
        context = analyzer.analyze()
        print(f"✅ Project Type: {context['framework']} + {context['styling']}")
        print(f"✅ UI Library: {context['ui_library']}")
        print(f"✅ TypeScript: {'Yes' if context['typescript'] else 'No'}")
    except Exception as e:
        print(f"❌ Project Analysis: {e}")
    
    print("-" * 40)
    
    if not api_key:
        print("\n❌ Setup incomplete. Please set OPENAI_API_KEY")
        sys.exit(1)
    else:
        print("\n✅ Setup complete! Try: palette generate 'simple button'")


if __name__ == "__main__":
    main()