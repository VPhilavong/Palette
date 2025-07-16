#!/usr/bin/env python3
"""
Test script for Code Palette CLI
Run this to test the basic functionality without installing the package
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from cli import main
        from context import ProjectAnalyzer
        from generator import UIGenerator
        from prompts import UIPromptBuilder
        from file_manager import FileManager
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_project_analysis():
    """Test project analysis functionality"""
    try:
        from context import ProjectAnalyzer
        
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project('.')
        
        print(f"✓ Project analysis complete:")
        print(f"  Framework: {context.get('framework', 'unknown')}")
        print(f"  Styling: {context.get('styling', 'unknown')}")
        print(f"  Component Library: {context.get('component_library', 'none')}")
        
        return True
    except Exception as e:
        print(f"✗ Project analysis error: {e}")
        return False

def test_prompt_building():
    """Test prompt building functionality"""
    try:
        from prompts import UIPromptBuilder
        
        builder = UIPromptBuilder()
        
        # Test context
        context = {
            'framework': 'react',
            'styling': 'tailwind',
            'component_library': 'none',
            'design_tokens': {
                'colors': ['blue', 'gray', 'green'],
                'spacing': ['4', '8', '16'],
                'typography': ['sm', 'base', 'lg']
            }
        }
        
        system_prompt = builder.build_ui_system_prompt(context)
        user_prompt = builder.build_user_prompt("Create a button component", context)
        
        print(f"✓ Prompt building successful")
        print(f"  System prompt length: {len(system_prompt)} chars")
        print(f"  User prompt length: {len(user_prompt)} chars")
        
        return True
    except Exception as e:
        print(f"✗ Prompt building error: {e}")
        return False

def test_file_management():
    """Test file management functionality"""
    try:
        from file_manager import FileManager
        
        manager = FileManager()
        
        # Test component name extraction
        sample_code = '''
const MyButton = ({ children }) => {
  return <button>{children}</button>;
};

export default MyButton;
'''
        
        component_name = manager._extract_component_name(sample_code)
        print(f"✓ File management tests passed")
        print(f"  Extracted component name: {component_name}")
        
        return True
    except Exception as e:
        print(f"✗ File management error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Code Palette CLI Components\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Project Analysis", test_project_analysis),
        ("Prompt Building", test_prompt_building),
        ("File Management", test_file_management),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! CLI is ready for use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up your API keys in .env file")
        print("3. Install the CLI: pip install -e .")
        print("4. Test with: code-palette --help")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()