#!/bin/bash
# Palette Backend Server Startup Script (Linux/Mac)

echo "🎨 Starting Palette Backend Server..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "📁 Project directory: $PROJECT_DIR"

# Check if we're in the right place
if [ ! -d "$PROJECT_DIR/src/palette" ]; then
    echo "❌ Error: Not in Palette project directory"
    echo "   Expected to find src/palette directory"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Check for virtual environment
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found, using system Python"
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_DIR/src"

# Start the server
echo "🚀 Starting server on http://localhost:8765..."
echo "📝 Press Ctrl+C to stop the server"
echo "-" * 50

python3 -m uvicorn palette.server.main:app --host 127.0.0.1 --port 8765 --reload