#!/bin/bash

# Code Palette VS Code Extension Installation Script

echo "🎨 Installing Code Palette VS Code Extension..."

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "❌ VS Code CLI not found. Please install VS Code first."
    echo "   Add 'code' to your PATH or install VS Code."
    exit 1
fi

# Check if palette CLI is installed
if ! command -v palette &> /dev/null; then
    echo "❌ Palette CLI not found."
    echo "   Please install it first:"
    echo "   pip install -e /path/to/code-palette"
    exit 1
fi

# Check if OpenAI API key is configured
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not found in environment"
    echo "   You'll need to set this before using the extension"
fi

# Compile the extension
echo "📦 Compiling extension..."
npm run compile

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed"
    exit 1
fi

# Package the extension
echo "📦 Packaging extension..."
if ! command -v vsce &> /dev/null; then
    echo "Installing vsce..."
    npm install -g vsce
fi

vsce package

if [ $? -ne 0 ]; then
    echo "❌ Packaging failed"
    exit 1
fi

# Install the extension
echo "🚀 Installing extension..."
EXTENSION_FILE=$(find . -name "*.vsix" | head -n 1)

if [ -z "$EXTENSION_FILE" ]; then
    echo "❌ No .vsix file found"
    exit 1
fi

code --install-extension "$EXTENSION_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Code Palette extension installed successfully!"
    echo ""
    echo "🎯 Next steps:"
    echo "1. Restart VS Code"
    echo "2. Open a React project"
    echo "3. Press Ctrl+Shift+P and type 'Palette: Generate Component'"
    echo "4. Enter a component description and enjoy!"
else
    echo "❌ Installation failed"
    exit 1
fi