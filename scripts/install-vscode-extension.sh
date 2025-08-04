#!/bin/bash

# Code Palette VS Code Extension Installation Script
# This script installs the Code Palette VS Code extension

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXTENSION_DIR="$PROJECT_ROOT/vscode-extension"

# Source .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}📄 Loading environment variables from .env file...${NC}"
    set -a  # Export all variables
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo -e "${GREEN}🎨 Installing Code Palette VS Code Extension...${NC}"
echo ""

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo -e "${RED}❌ VS Code CLI not found. Please install VS Code first.${NC}"
    echo "   Add 'code' to your PATH or install VS Code from https://code.visualstudio.com/"
    exit 1
fi

# Check if palette CLI is installed
if ! command -v palette &> /dev/null; then
    echo -e "${YELLOW}⚠️  Palette CLI not found in PATH.${NC}"
    echo "   Checking for local installation..."
    
    # Check for virtual environment
    if [ -f "$PROJECT_ROOT/venv/bin/palette" ]; then
        echo -e "${GREEN}✓ Found palette in virtual environment${NC}"
    else
        echo -e "${RED}❌ Palette CLI not found.${NC}"
        echo "   Please install it first:"
        echo "   cd $PROJECT_ROOT && pip install -e ."
        exit 1
    fi
fi

# Check if OpenAI API key is configured
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: OPENAI_API_KEY not found in environment${NC}"
    echo "   You'll need to set this before using the extension:"
    echo "   export OPENAI_API_KEY='your-key-here'"
    echo ""
fi

# Navigate to extension directory
cd "$EXTENSION_DIR"

# Install dependencies
echo -e "${GREEN}📦 Installing npm dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ npm install failed${NC}"
    exit 1
fi

# Compile the extension
echo -e "${GREEN}🔨 Compiling TypeScript...${NC}"
npm run compile

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Compilation failed${NC}"
    exit 1
fi

# Check if vsce is installed
if ! command -v vsce &> /dev/null; then
    echo -e "${GREEN}📥 Installing vsce...${NC}"
    npm install -g vsce
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install vsce${NC}"
        echo "   You may need to use sudo: sudo npm install -g vsce"
        exit 1
    fi
fi

# Remove old .vsix files
echo -e "${GREEN}🧹 Cleaning up old packages...${NC}"
rm -f *.vsix

# Package the extension
echo -e "${GREEN}📦 Packaging extension...${NC}"
vsce package --allow-missing-repository

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Packaging failed${NC}"
    exit 1
fi

# Find the generated .vsix file
VSIX_FILE=$(find . -name "*.vsix" -type f | head -n 1)

if [ -z "$VSIX_FILE" ]; then
    echo -e "${RED}❌ No .vsix file found${NC}"
    exit 1
fi

# Install the extension
echo -e "${GREEN}🚀 Installing extension in VS Code...${NC}"
code --install-extension "$VSIX_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Code Palette extension installed successfully!${NC}"
    echo ""
    echo -e "${GREEN}🎯 Next steps:${NC}"
    echo "1. Restart VS Code"
    echo "2. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
    echo "3. Open a React project"
    echo "4. Press Ctrl+Shift+P and type 'Palette' to see available commands"
    echo ""
    echo -e "${GREEN}📋 Available commands:${NC}"
    echo "   • Palette: Open Palette - Opens the Palette interface"
    echo "   • Palette: Generate - Generate components with AI"
    echo "   • Palette: Analyze Project - Analyze your current project"
else
    echo -e "${RED}❌ Installation failed${NC}"
    exit 1
fi