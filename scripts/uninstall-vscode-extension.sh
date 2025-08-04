#!/bin/bash

# Code Palette VS Code Extension Uninstallation Script

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🗑️  Uninstalling Code Palette VS Code Extension...${NC}"
echo ""

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo -e "${RED}❌ VS Code CLI not found.${NC}"
    exit 1
fi

# Check if the extension is installed
if code --list-extensions | grep -q "sail-project.code-palette"; then
    # Uninstall the extension
    code --uninstall-extension sail-project.code-palette
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Code Palette extension uninstalled successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to uninstall extension${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Code Palette extension is not installed${NC}"
fi

echo ""
echo "To reinstall, run: ./scripts/install-vscode-extension.sh"