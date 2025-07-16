#!/usr/bin/env python3
"""
Sanitize script to clean up the Palette repository for fresh testing.
This script removes temporary files, test projects, and resets the workspace.
"""

import os
import shutil
import sys
from pathlib import Path

def remove_directory(path: str, description: str):
    """Safely remove a directory if it exists"""
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✓ Removed {description}: {path}")
        except Exception as e:
            print(f"✗ Failed to remove {description}: {e}")
    else:
        print(f"- {description} not found: {path}")

def remove_file(path: str, description: str):
    """Safely remove a file if it exists"""
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✓ Removed {description}: {path}")
        except Exception as e:
            print(f"✗ Failed to remove {description}: {e}")
    else:
        print(f"- {description} not found: {path}")

def clean_pycache(root_dir: str):
    """Remove all __pycache__ directories recursively"""
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"✓ Removed __pycache__: {pycache_path}")
            except Exception as e:
                print(f"✗ Failed to remove __pycache__: {e}")

def main():
    """Main sanitization function"""
    
    print("🧹 Starting Palette repository sanitization...")
    print("=" * 50)
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Remove test projects
    print("\n📁 Cleaning test projects:")
    test_directories = [
        os.path.join(project_root, "test-project"),
        os.path.join(project_root, "test_projects"),
        os.path.join(project_root, "temp"),
        os.path.join(project_root, "tmp"),
    ]
    
    for test_dir in test_directories:
        remove_directory(test_dir, "Test directory")
    
    # 2. Remove temporary test files
    print("\n📄 Cleaning temporary files:")
    temp_files = [
        os.path.join(project_root, "test_aggregated_output.txt"),
        os.path.join(project_root, "test_output.txt"),
        os.path.join(project_root, "debug.log"),
        os.path.join(project_root, "analysis_output.txt"),
    ]
    
    for temp_file in temp_files:
        remove_file(temp_file, "Temporary file")
    
    # 3. Clean test CSS files (keep only essential ones)
    print("\n🎨 Cleaning test CSS files:")
    test_css_dir = os.path.join(project_root, "test_css")
    if os.path.exists(test_css_dir):
        # Keep only essential test files
        essential_files = {'style.css', 'theme.css', 'components.css', 'buttons.css'}
        
        for file in os.listdir(test_css_dir):
            file_path = os.path.join(test_css_dir, file)
            if os.path.isfile(file_path) and file not in essential_files:
                remove_file(file_path, "Extra test CSS file")
            elif os.path.isdir(file_path):
                remove_directory(file_path, "Test CSS subdirectory")
    
    # 4. Remove Python cache files
    print("\n🐍 Cleaning Python cache:")
    clean_pycache(project_root)
    
    # Remove .pyc files
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                remove_file(pyc_path, "Python cache file")
    
    # 5. Remove generated components (if any)
    print("\n⚛️ Cleaning generated components:")
    component_dirs = [
        os.path.join(project_root, "app"),
        os.path.join(project_root, "components"),
    ]
    
    for comp_dir in component_dirs:
        if os.path.exists(comp_dir):
            # Only remove if it looks like a generated test component
            for file in os.listdir(comp_dir):
                file_path = os.path.join(comp_dir, file)
                if file.endswith(('.tsx', '.jsx')) and 'test' in file.lower():
                    remove_file(file_path, "Generated test component")
    
    # 6. Remove VS Code specific temp files
    print("\n💻 Cleaning VS Code temporary files:")
    vscode_temp = [
        os.path.join(project_root, ".vscode", "settings.json"),
    ]
    
    for temp_file in vscode_temp:
        if os.path.exists(temp_file):
            # Only remove if it contains temporary settings
            try:
                with open(temp_file, 'r') as f:
                    content = f.read()
                    if 'temp' in content.lower() or 'test' in content.lower():
                        remove_file(temp_file, "Temporary VS Code settings")
            except:
                pass
    
    # 7. Clean node_modules if they exist in test projects
    print("\n📦 Cleaning node modules:")
    node_modules_dirs = []
    for root, dirs, files in os.walk(project_root):
        if 'node_modules' in dirs and 'test' in root.lower():
            node_modules_path = os.path.join(root, 'node_modules')
            node_modules_dirs.append(node_modules_path)
    
    for node_modules in node_modules_dirs:
        remove_directory(node_modules, "Test node_modules")
    
    # 8. Reset git status (optional)
    print("\n🔄 Git status check:")
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=project_root)
        if result.stdout.strip():
            print("⚠️  Git has uncommitted changes:")
            print(result.stdout)
            print("💡 Consider committing or stashing changes before testing")
        else:
            print("✓ Git working directory is clean")
    except Exception as e:
        print(f"- Could not check git status: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Repository sanitization complete!")
    print("✨ Ready for fresh testing on new projects")
    
    # Provide usage instructions
    print("\n📋 Next steps:")
    print("1. Clone a test project: git clone <repo-url> test-project")
    print("2. Run analysis: cd test-project && PYTHONPATH=/path/to/palette python3 -m src.cli analyze")
    print("3. Generate components: PYTHONPATH=/path/to/palette python3 -m src.cli generate \"your prompt\"")

if __name__ == "__main__":
    main()
