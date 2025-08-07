#!/usr/bin/env python3
"""
Server launcher for Palette Intelligence Server
Runs the FastAPI server with proper module imports
"""

import os
import sys
from pathlib import Path

# Add src to Python path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Launch the Palette server"""
    print("🎨 Starting Palette Intelligence Server...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {src_path}")
    
    try:
        import uvicorn
        from palette.server.main import app
        
        # Run the server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8765,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Failed to import server modules: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("   pip install -r requirements-test.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()