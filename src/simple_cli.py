#!/usr/bin/env python3
"""
Simple CLI for Code Palette without rich dependency
For testing and development purposes
"""

import click
import os
import sys
from typing import Optional

from .generator import UIGenerator
from .context import ProjectAnalyzer
from .file_manager import FileManager

@click.group()
@click.version_option(version="0.1.0")
def main():
    """Code Palette - Design-to-Code UI/UX Agent for React + Tailwind components"""
    pass

@main.command()
@click.argument('prompt', required=True)
@click.option('--preview', is_flag=True, help='Preview component before creating file')
@click.option('--output', '-o', help='Output file path (auto-detected if not provided)')
@click.option('--model', default='gpt-4', help='LLM model to use')
def generate(prompt: str, preview: bool, output: Optional[str], model: str):
    """Generate a React component from a natural language prompt"""
    
    print(f"🎨 Generating component: {prompt}")
    
    try:
        # Analyze project context
        print("📊 Analyzing project...")
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())
        
        print(f"✓ Detected {context['framework']} project with {context['styling']}")
        
        # Generate component
        print("🤖 Generating component code...")
        generator = UIGenerator(model=model)
        component_code = generator.generate_component(prompt, context)
        
        if preview:
            print("\n" + "="*60)
            print("GENERATED COMPONENT:")
            print("="*60)
            print(component_code)
            print("="*60)
            
            if not click.confirm("\nCreate this component?"):
                print("❌ Component generation cancelled")
                return
        
        # Save component
        print("💾 Saving component...")
        file_manager = FileManager()
        file_path = file_manager.save_component(component_code, output, context)
        
        print(f"✅ Component created at: {file_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

@main.command()
def analyze():
    """Analyze project design patterns and configuration"""
    
    print("📊 Analyzing project...")
    
    try:
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())
        
        # Display analysis results
        print("\n📋 PROJECT ANALYSIS:")
        print("-" * 40)
        print(f"Framework:         {context.get('framework', 'Unknown')}")
        print(f"Styling:           {context.get('styling', 'Unknown')}")
        print(f"Component Library: {context.get('component_library', 'None detected')}")
        
        if context.get('design_tokens'):
            tokens = context['design_tokens']
            print(f"Colors:            {', '.join(tokens.get('colors', []))}")
            print(f"Spacing:           {', '.join(tokens.get('spacing', []))}")
            print(f"Typography:        {', '.join(tokens.get('typography', []))}")
        
        structure = context.get('project_structure', {})
        print(f"Components Dir:    {structure.get('components_dir', 'Not found')}")
        print(f"Pages Dir:         {structure.get('pages_dir', 'Not found')}")
        
        print("\n✅ Project analysis complete")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

@main.command()
@click.argument('prompt', required=True)
def preview(prompt: str):
    """Preview a component without creating it"""
    
    print(f"👀 Previewing component: {prompt}")
    
    try:
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(os.getcwd())
        
        generator = UIGenerator()
        component_code = generator.generate_component(prompt, context)
        
        print("\n" + "="*60)
        print("COMPONENT PREVIEW:")
        print("="*60)
        print(component_code)
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()