#!/usr/bin/env python3

"""
Test script for the enhanced Tailwind config parsing system.

This script demonstrates the full pipeline:
1. Node.js script evaluates and extracts actual Tailwind theme with defaults
2. Python parses the JSON output and processes resolved theme data

Usage: python test_tailwind_parsing.py [path_to_tailwind_config]
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from palette.analysis.context import ProjectAnalyzer


def test_node_parser(config_path: str):
    """Test the Node.js parser directly"""
    
    print("=== Testing Node.js Tailwind Parser ===")
    
    # Get the path to our Node.js helper script
    parser_script = Path(__file__).parent / "src" / "palette" / "utils" / "tailwind_parser.js"
    
    try:
        # Run the Node.js script to parse the config
        result = subprocess.run(
            ["node", str(parser_script), config_path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        
        if result.returncode == 0:
            try:
                parsed_config = json.loads(result.stdout)
                
                print(f"✅ Successfully parsed config: {config_path}")
                print(f"📊 Resolved with defaults: {parsed_config.get('_resolved', False)}")
                
                # Print summary statistics
                colors = parsed_config.get('colors', {})
                spacing = parsed_config.get('spacing', {})
                font_sizes = parsed_config.get('fontSize', {})
                
                print(f"🎨 Colors found: {len(colors)}")
                print(f"📏 Spacing values: {len(spacing)}")
                print(f"🔤 Font sizes: {len(font_sizes)}")
                
                # Show some sample values
                if colors:
                    print("\n📝 Sample colors:")
                    for i, (name, value) in enumerate(list(colors.items())[:5]):
                        if isinstance(value, dict):
                            # Color scale - show the number of shades
                            print(f"  {name}: {len(value)} shades")
                        else:
                            print(f"  {name}: {value}")
                
                if spacing:
                    print("\n📝 Sample spacing:")
                    for i, (name, value) in enumerate(list(spacing.items())[:5]):
                        print(f"  {name}: {value}")
                
                return parsed_config
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw output: {result.stdout}")
                return None
        else:
            print(f"❌ Node.js parser failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Parser timed out")
        return None
    except FileNotFoundError:
        print("❌ Node.js not found. Install Node.js to test.")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_python_integration(config_path: str):
    """Test the full Python integration"""
    
    print("\n=== Testing Python Integration ===")
    
    try:
        # Create analyzer and parse the project
        analyzer = ProjectAnalyzer()
        
        # Get the directory containing the config
        project_path = os.path.dirname(os.path.abspath(config_path))
        
        # Parse Tailwind config
        tailwind_config = analyzer._parse_tailwind_config(project_path)
        
        if tailwind_config:
            print(f"✅ Successfully parsed via Python integration")
            
            # Test color extraction
            color_data = analyzer._extract_colors_from_config(tailwind_config, project_path)
            
            print(f"🎨 Custom colors: {len(color_data['custom'])}")
            print(f"🎨 Semantic colors: {len(color_data['semantic'])}")
            
            if color_data['custom']:
                print(f"📝 Custom colors: {color_data['custom'][:10]}")
            
            if color_data['semantic']:
                print(f"📝 Semantic colors: {color_data['semantic'][:10]}")
            
            return True
        else:
            print("❌ Failed to parse config via Python")
            return False
            
    except Exception as e:
        print(f"❌ Python integration error: {e}")
        return False


def create_test_config():
    """Create a test Tailwind config for demonstration"""
    
    test_config_path = "/tmp/test_tailwind.config.js"
    
    test_config_content = """
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        secondary: '#64748b',
        accent: '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Playfair Display', 'serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      }
    },
  },
  plugins: [],
}
"""
    
    with open(test_config_path, 'w') as f:
        f.write(test_config_content)
    
    print(f"📁 Created test config: {test_config_path}")
    return test_config_path


def main():
    """Main test function"""
    
    print("🧪 Enhanced Tailwind Config Parsing Test")
    print("=" * 50)
    
    # Determine config path
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return
    else:
        # Look for config in current directory
        possible_configs = [
            "tailwind.config.js",
            "tailwind.config.ts", 
            "tailwind.config.mjs"
        ]
        
        config_path = None
        for config in possible_configs:
            if os.path.exists(config):
                config_path = config
                break
        
        if not config_path:
            print("📁 No Tailwind config found, creating test config...")
            config_path = create_test_config()
    
    print(f"🔧 Testing with config: {config_path}")
    
    # Test Node.js parser
    node_result = test_node_parser(config_path)
    
    # Test Python integration
    python_result = test_python_integration(config_path)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Node.js parser: {'✅ PASSED' if node_result else '❌ FAILED'}")
    print(f"Python integration: {'✅ PASSED' if python_result else '❌ FAILED'}")
    
    if node_result and python_result:
        print("\n🎉 All tests passed! The enhanced Tailwind parsing system is working correctly.")
        
        # Show the resolved flag status
        if node_result and node_result.get('_resolved'):
            print("✨ Full theme resolution with Tailwind defaults is active!")
        else:
            print("⚠️  Basic theme parsing mode (install tailwindcss npm package for full resolution)")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()