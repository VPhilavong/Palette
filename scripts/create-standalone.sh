#!/bin/bash

# 🔥 Create Standalone Palette Executable
# Uses PyInstaller to create a single executable that can be bundled with VS Code extension

echo "🔥 Creating Standalone Palette Executable"
echo "========================================"

cd "$(dirname "$0")/.."
PALETTE_DIR=$(pwd)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Install PyInstaller if not present
if ! command -v pyinstaller >/dev/null 2>&1; then
    print_status "Installing PyInstaller..."
    pip install pyinstaller
fi

# Create spec file for better control
cat > palette-standalone.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/palette/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/palette', 'palette'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'palette.cli.main',
        'palette.conversation',
        'palette.generation',
        'palette.analysis',
        'palette.quality',
        'palette.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='palette-standalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

print_status "Building standalone executable..."
pyinstaller palette-standalone.spec --clean

if [[ -f "dist/palette-standalone" ]]; then
    print_success "Standalone executable created: dist/palette-standalone"
    
    # Test the executable
    print_status "Testing executable..."
    if ./dist/palette-standalone --version; then
        print_success "Executable test passed"
    else
        echo "Executable test failed"
    fi
    
    # Move to VS Code extension directory
    mkdir -p vscode-extension/binaries
    cp dist/palette-standalone vscode-extension/binaries/
    print_success "Executable copied to VS Code extension"
    
    echo ""
    echo "📦 VS Code Extension Integration:"
    echo "Update paletteService.ts to use:"
    echo "  const palettePath = path.join(__dirname, '..', 'binaries', 'palette-standalone');"
    
else
    echo "❌ Build failed"
    exit 1
fi