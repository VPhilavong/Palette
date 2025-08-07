#!/usr/bin/env python3
"""
Quick runner for the streaming server
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from palette.server.streaming_server import start_streaming_server

def main():
    """Start the streaming server"""
    print("🚀 Starting Palette Streaming Server...")
    
    server = start_streaming_server(host="localhost", port=8765)
    print(f"✅ Server running at {server.base_url}")
    print("🔗 Health check: http://localhost:8765/health")
    print("📡 Ready for VS Code extension connections!")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Keep main thread alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop_server()
        print("✅ Server stopped")

if __name__ == "__main__":
    main()