#!/usr/bin/env python3
"""
Palette Backend Server Startup Script
Automatically starts the Palette FastAPI backend server
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def find_palette_project():
    """Find the main Palette project directory"""
    current_dir = Path(__file__).parent.parent  # vscode-extension directory
    palette_project = current_dir.parent  # Palette directory
    
    # Check if this looks like the Palette project
    if (palette_project / "src" / "palette").exists():
        return palette_project
    
    # Try common locations
    possible_paths = [
        Path.home() / "Projects" / "Palette",
        Path.cwd().parent,
        Path("/home/vphilavong/Projects/Palette"),  # Your specific path
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "src" / "palette").exists():
            return path
    
    return None

def check_python_environment(project_path):
    """Check if Python environment is set up correctly"""
    venv_path = project_path / "venv"
    if venv_path.exists():
        if os.name == 'nt':  # Windows
            python_exe = venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/Mac
            python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            return str(python_exe)
    
    # Fallback to system Python
    return sys.executable

def start_backend_server():
    """Start the Palette backend server"""
    print("🎨 Starting Palette Backend Server...")
    
    # Find Palette project
    project_path = find_palette_project()
    if not project_path:
        print("❌ Error: Could not find Palette project directory")
        print("   Make sure you're running this from the correct location")
        return False
    
    print(f"📁 Found Palette project: {project_path}")
    
    # Get Python executable
    python_exe = check_python_environment(project_path)
    print(f"🐍 Using Python: {python_exe}")
    
    # Check if server module exists
    server_module = project_path / "src" / "palette" / "server" / "main.py"
    if not server_module.exists():
        print(f"❌ Error: Server module not found at {server_module}")
        print("   The Palette backend might not be installed correctly")
        return False
    
    try:
        # Change to project directory
        os.chdir(project_path)
        
        # Set PYTHONPATH to include src directory
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_path / "src")
        
        # Start the server
        print("🚀 Starting server on http://localhost:8765...")
        print("📝 Server logs will appear below:")
        print("-" * 50)
        
        # Run the server using uvicorn
        cmd = [python_exe, "-m", "uvicorn", "palette.server.main:app", "--host", "127.0.0.1", "--port", "8765", "--reload"]
        process = subprocess.run(
            cmd,
            cwd=project_path,
            env=env,
            capture_output=False  # Let output stream to console
        )
        
        return process.returncode == 0
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def main():
    """Main function"""
    print("🎨 Palette Backend Server Startup Script")
    print("=" * 40)
    
    success = start_backend_server()
    
    if success:
        print("\n✅ Server startup completed")
    else:
        print("\n❌ Server startup failed")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the Palette project directory")
        print("2. Check that the virtual environment is set up: python3 -m venv venv")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Try running manually: python3 -m palette.server.main")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())