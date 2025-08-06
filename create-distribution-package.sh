#!/bin/bash

# 📦 Create Complete Palette Distribution Package
# Creates a self-contained package that users can install and run

echo "📦 Creating Palette Distribution Package"
echo "======================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

cd "$(dirname "$0")"
PALETTE_DIR=$(pwd)
DIST_DIR="palette-distribution"

print_status "Working from: $PALETTE_DIR"

# Step 1: Clean and create distribution directory
print_status "Step 1: Creating distribution structure..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Step 2: Copy core components
print_status "Step 2: Copying Palette components..."

# Copy source code (without heavy dependencies)
cp -r src "$DIST_DIR/"
cp setup.py "$DIST_DIR/"
cp README.md "$DIST_DIR/" || touch "$DIST_DIR/README.md"

# Create minimal requirements
cat > "$DIST_DIR/requirements.txt" << 'EOF'
click>=8.1.0
rich>=13.0.0
requests>=2.28.0
jinja2>=3.1.0
python-dotenv>=1.0.0
openai>=1.0.0
anthropic>=0.18.0
pathlib2>=2.3.0
EOF

# Step 3: Copy and prepare VS Code extension
print_status "Step 3: Preparing VS Code extension..."
mkdir -p "$DIST_DIR/vscode-extension"

# Copy extension files (excluding node_modules and bundled directory)
rsync -av --exclude='node_modules' --exclude='bundled' --exclude='out' vscode-extension/ "$DIST_DIR/vscode-extension/"

# Install VS Code extension dependencies in distribution
print_status "Installing VS Code extension dependencies..."
cd "$DIST_DIR/vscode-extension"
npm install --production=false
cd "$PALETTE_DIR"

# Create bundled directory in distribution
mkdir -p "$DIST_DIR/vscode-extension/bundled"
cp -r src "$DIST_DIR/vscode-extension/bundled/"
cp "$DIST_DIR/requirements.txt" "$DIST_DIR/vscode-extension/bundled/"

# Create bundle launcher
cat > "$DIST_DIR/vscode-extension/bundled/palette-cli.py" << 'EOF'
#!/usr/bin/env python3
"""
Bundled Palette CLI for VS Code Extension
"""
import sys
from pathlib import Path

# Add bundled source to Python path
bundle_dir = Path(__file__).parent
sys.path.insert(0, str(bundle_dir / "src"))

# Import and run CLI
from palette.cli.main import main

if __name__ == "__main__":
    main()
EOF

chmod +x "$DIST_DIR/vscode-extension/bundled/palette-cli.py"

# Step 4: Create installation scripts
print_status "Step 4: Creating installation scripts..."

# Main installer
cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash
echo "🎨 Installing Palette AI Distribution"
echo "===================================="

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Install VS Code extension
echo "🔧 Installing VS Code extension..."
cd vscode-extension
npm install
npm run compile

if [[ $? -eq 0 ]]; then
    echo "✅ Installation complete!"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Set your API key: export OPENAI_API_KEY=\"your-key\""
    echo "2. Open VS Code in your project directory"
    echo "3. Install extension: code --install-extension $(pwd)"
    echo "4. Press Ctrl+Shift+U to start!"
else
    echo "❌ VS Code extension installation failed"
    exit 1
fi
EOF

chmod +x "$DIST_DIR/install.sh"

# Windows installer
cat > "$DIST_DIR/install.bat" << 'EOF'
@echo off
echo 🎨 Installing Palette AI Distribution
echo ====================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3 is required but not installed
    pause
    exit /b 1
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install VS Code extension
echo 🔧 Installing VS Code extension...
cd vscode-extension
call npm install
call npm run compile

if %errorlevel% equ 0 (
    echo ✅ Installation complete!
    echo.
    echo 🚀 Next steps:
    echo 1. Set your API key: set OPENAI_API_KEY=your-key
    echo 2. Open VS Code in your project directory
    echo 3. Install extension: code --install-extension "%cd%"
    echo 4. Press Ctrl+Shift+U to start!
    pause
) else (
    echo ❌ VS Code extension installation failed
    pause
    exit /b 1
)
EOF

# Step 5: Create README for distribution
cat > "$DIST_DIR/README.md" << 'EOF'
# 🎨 Palette AI - Complete Distribution

Self-contained Palette AI package with VS Code extension and CLI.

## 📋 System Requirements

- **Python 3.8+** with pip
- **Node.js 16+** with npm  
- **VS Code 1.60+**

## 🚀 Quick Install

### Linux/Mac:
```bash
./install.sh
```

### Windows:
```cmd
install.bat
```

## 🔧 Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   ```

3. **Install VS Code extension:**
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   code --install-extension .
   ```

## 🎯 Usage

1. **Open VS Code** in your React/Next.js project
2. **Press `Ctrl+Shift+U`** to open Palette
3. **Type your request:** "create a button component"
4. **Get instant results!**

## 📁 What's Included

- **Palette CLI** - Full source code
- **VS Code Extension** - Conversational UI generator  
- **Bundled Runtime** - No separate CLI installation needed
- **Installation Scripts** - One-click setup

## 🆘 Support

- **Check logs:** VS Code → Output → "Code Palette"
- **Test CLI:** `python3 vscode-extension/bundled/palette-cli.py --help`
- **Verify API key:** Make sure `OPENAI_API_KEY` is set

## 🎉 Features

✅ **Conversational Interface** - Natural language component requests  
✅ **Context-Aware** - Analyzes your project automatically  
✅ **Framework Detection** - React, Next.js, Vue.js support  
✅ **Style Integration** - Tailwind, CSS Modules, styled-components  
✅ **Quality Assurance** - Built-in validation and auto-fixing  
✅ **Session Memory** - Remembers conversation context  

Ready to build amazing UI components with AI! 🚀
EOF

# Step 6: Create version info
cat > "$DIST_DIR/VERSION" << 'EOF'
Palette AI Distribution v0.1.1
Build Date: $(date)
Components:
- Palette CLI (Python)
- VS Code Extension (TypeScript)  
- Bundled Runtime
EOF

# Step 7: Create package info
print_status "Step 7: Creating package summary..."
TOTAL_SIZE=$(du -sh "$DIST_DIR" | cut -f1)

cat > "$DIST_DIR/PACKAGE_INFO.txt" << EOF
📦 PALETTE AI DISTRIBUTION PACKAGE
==================================

Package Size: $TOTAL_SIZE
Created: $(date)
Platform: Cross-platform (Linux, Mac, Windows)

Contents:
├── src/                     # Palette CLI source code
├── vscode-extension/        # VS Code extension 
│   └── bundled/            # Self-contained CLI runtime
├── requirements.txt         # Python dependencies
├── install.sh              # Linux/Mac installer
├── install.bat             # Windows installer  
└── README.md               # Setup instructions

Installation Methods:
1. Automated: Run install.sh (Linux/Mac) or install.bat (Windows)
2. Manual: Follow README.md instructions

Requirements:
- Python 3.8+
- Node.js 16+ 
- VS Code 1.60+
- OpenAI or Anthropic API key

After installation:
- Press Ctrl+Shift+U in VS Code to start
- Type natural language requests like "create a button component"
- Get professional, context-aware React components instantly

This is a complete, self-contained distribution of Palette AI.
No separate CLI installation required! 🎉
EOF

print_success "Distribution package created: $DIST_DIR/"
print_success "Package size: $TOTAL_SIZE"

echo ""
echo "📋 Distribution Contents:"
ls -la "$DIST_DIR/"

echo ""
echo "🧪 Testing package..."
if [[ -f "$DIST_DIR/vscode-extension/bundled/palette-cli.py" ]]; then
    if python3 "$DIST_DIR/vscode-extension/bundled/palette-cli.py" --version >/dev/null 2>&1; then
        print_success "✅ Package test passed"
    else
        print_warning "⚠️  Package test failed - CLI might need dependencies"
    fi
else
    print_warning "⚠️  Bundle CLI not found"
fi

echo ""
echo "🎉 Distribution Ready!"
echo "====================="
echo "📁 Location: $DIST_DIR/"
echo "📋 Install: Run ./install.sh (Linux/Mac) or install.bat (Windows)"
echo "🚀 Package this as ZIP/TAR for distribution"

# Create archive
print_status "Creating archive..."
tar czf "palette-ai-distribution-v0.1.1.tar.gz" "$DIST_DIR"
print_success "Archive created: palette-ai-distribution-v0.1.1.tar.gz"

echo ""
echo "✨ Ready to distribute! ✨"