#!/usr/bin/env python3

"""
Example usage of the enhanced Tailwind config parsing system.

This script demonstrates how to use the full pipeline to extract 
actual Tailwind theme values for use in code generation tools.
"""

import json
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from palette.analysis.context import ProjectAnalyzer


def analyze_project_theme(project_path: str):
    """
    Analyze a project's Tailwind theme and return structured data
    that can be used for code generation.
    """
    
    print(f"🔍 Analyzing Tailwind theme in: {project_path}")
    
    # Create the analyzer
    analyzer = ProjectAnalyzer()
    
    # Get full project context (includes Tailwind theme)
    context = analyzer.analyze_project(project_path)
    
    # Extract the design tokens (which includes our enhanced Tailwind parsing)
    design_tokens = context.get('design_tokens', {})
    
    return {
        'framework': context.get('framework'),
        'styling_system': context.get('styling'),
        'component_library': context.get('component_library'),
        'colors': design_tokens.get('colors', {}),
        'semantic_colors': design_tokens.get('semantic_colors', {}),
        'color_structure': design_tokens.get('color_structure', {}),
        'spacing': design_tokens.get('spacing', {}),
        'typography': design_tokens.get('typography', {}),
        'shadows': design_tokens.get('shadows', {}),
        'border_radius': design_tokens.get('border_radius', {}),
        'available_imports': context.get('available_imports', {}),
    }


def generate_theme_summary(theme_data: dict):
    """Generate a human-readable summary of the theme"""
    
    print("\n📊 Theme Analysis Summary")
    print("=" * 40)
    
    print(f"Framework: {theme_data.get('framework', 'Unknown')}")
    print(f"Styling: {theme_data.get('styling_system', 'Unknown')}")
    print(f"Component Library: {theme_data.get('component_library', 'None')}")
    
    # Colors
    colors = theme_data.get('colors', {})
    semantic_colors = theme_data.get('semantic_colors', [])
    
    print(f"\n🎨 Colors:")
    print(f"  - Custom colors: {len(colors) if isinstance(colors, dict) else len(colors) if isinstance(colors, list) else 0}")
    print(f"  - Semantic colors: {len(semantic_colors)}")
    
    if semantic_colors:
        print(f"  - Semantic names: {', '.join(semantic_colors[:5])}")
        if len(semantic_colors) > 5:
            print(f"    ... and {len(semantic_colors) - 5} more")
    
    # Show color structure if available
    color_structure = theme_data.get('color_structure', {})
    if color_structure:
        print(f"  - Full color palette available with {len(color_structure)} colors")
        
        # Show some examples
        examples = []
        for color_name, color_value in list(color_structure.items())[:3]:
            if isinstance(color_value, dict):
                examples.append(f"{color_name} ({len(color_value)} shades)")
            else:
                examples.append(f"{color_name}")
        
        if examples:
            print(f"  - Examples: {', '.join(examples)}")
    
    # Spacing
    spacing = theme_data.get('spacing', {})
    if spacing:
        spacing_count = len(spacing) if isinstance(spacing, dict) else len(spacing) if isinstance(spacing, list) else 0
        print(f"\n📏 Spacing: {spacing_count} values")
        
        if isinstance(spacing, dict):
            # Show some examples
            examples = list(spacing.items())[:5]
            for key, value in examples:
                print(f"  - {key}: {value}")
    
    # Typography
    typography = theme_data.get('typography', {})
    if typography:
        typo_count = len(typography) if isinstance(typography, dict) else len(typography) if isinstance(typography, list) else 0
        print(f"\n🔤 Typography: {typo_count} font sizes")
    
    # Available imports (useful for code generation)
    imports = theme_data.get('available_imports', {})
    if imports:
        print(f"\n📦 Available Imports:")
        
        ui_components = imports.get('ui_components', {})
        if ui_components.get('shadcn_ui'):
            print(f"  - shadcn/ui: {len(ui_components['shadcn_ui'])} components")
        
        if imports.get('icons'):
            print(f"  - Icons: {', '.join(imports['icons'])}")
        
        utilities = imports.get('utilities', {})
        if utilities.get('cn'):
            print(f"  - cn utility available")


def generate_code_example(theme_data: dict):
    """Generate an example of how this theme data could be used in code generation"""
    
    print("\n💻 Code Generation Example")
    print("=" * 30)
    
    colors = theme_data.get('semantic_colors', [])
    spacing = theme_data.get('spacing', {})
    
    # Generate a React component example
    primary_color = 'blue'
    if colors and len(colors) > 0:
        # Use the first semantic color if available
        primary_color = colors[0]
    elif 'primary' in theme_data.get('color_structure', {}):
        primary_color = 'primary'
    
    spacing_class = 'p-4'
    if isinstance(spacing, dict) and spacing:
        # Use a spacing value if available
        spacing_keys = list(spacing.keys())
        if '4' in spacing_keys:
            spacing_class = 'p-4'
        elif spacing_keys:
            spacing_class = f'p-{spacing_keys[0]}'
    
    component_example = f'''
// Generated component using actual project theme values
import React from 'react';
{("import { cn } from '@/lib/utils';" if theme_data.get('available_imports', {}).get('utilities', {}).get('cn') else "")}

export function GeneratedButton({{ children, variant = 'primary', ...props }}) {{
  return (
    <button
      className={{cn(
        "rounded-lg font-medium transition-colors",
        "{spacing_class}",
        variant === 'primary' && "bg-{primary_color}-500 text-white hover:bg-{primary_color}-600",
        variant === 'secondary' && "bg-gray-200 text-gray-900 hover:bg-gray-300"
      )}}
      {{...props}}
    >
      {{children}}
    </button>
  );
}}'''
    
    print(component_example)
    
    print(f"\n✨ This component uses:")
    print(f"  - Primary color: {primary_color} (from your theme)")
    print(f"  - Spacing: {spacing_class} (from your spacing scale)")
    if theme_data.get('available_imports', {}).get('utilities', {}).get('cn'):
        print(f"  - cn utility (detected in your project)")


def main():
    """Main function"""
    
    print("🎨 Tailwind Theme Analyzer")
    print("=" * 30)
    
    # Determine project path
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    if not os.path.exists(project_path):
        print(f"❌ Project path not found: {project_path}")
        return
    
    # Analyze the theme
    try:
        theme_data = analyze_project_theme(project_path)
        
        # Generate summary
        generate_theme_summary(theme_data)
        
        # Generate code example
        generate_code_example(theme_data)
        
        print(f"\n🎉 Analysis complete! Theme data extracted from actual Tailwind config.")
        
    except Exception as e:
        print(f"❌ Error analyzing theme: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()