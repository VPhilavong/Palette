#!/bin/bash

# Quick sanitize script for Palette repository
# Removes test projects and temporary files

echo "🧹 Quick sanitization of Palette repository..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Remove test projects
echo "📁 Removing test projects..."
rm -rf "$SCRIPT_DIR/test-project"
rm -rf "$SCRIPT_DIR/test_projects"
rm -rf "$SCRIPT_DIR/temp"
rm -rf "$SCRIPT_DIR/tmp"

# Remove temporary files
echo "📄 Removing temporary files..."
rm -f "$SCRIPT_DIR/test_aggregated_output.txt"
rm -f "$SCRIPT_DIR/test_output.txt"
rm -f "$SCRIPT_DIR/debug.log"
rm -f "$SCRIPT_DIR/analysis_output.txt"

# Clean Python cache
echo "🐍 Cleaning Python cache..."
find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null

# Clean node_modules in test directories
echo "📦 Cleaning test node_modules..."
find "$SCRIPT_DIR" -path "*/test*/node_modules" -type d -exec rm -rf {} + 2>/dev/null

echo "✅ Quick sanitization complete!"
echo ""
echo "📋 Ready for testing. Usage:"
echo "  1. Clone test project: git clone <repo-url> test-project"
echo "  2. cd test-project"
echo "  3. PYTHONPATH=/home/vphilavong/Projects/Palette python3 -m src.cli analyze"
