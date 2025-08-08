#!/bin/bash

# 🎁 Bundle Palette CLI + VS Code Extension Script
# Creates a self-contained extension with embedded Python CLI

echo "🚀 Creating bundled Palette VS Code Extension"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to Palette project directory
cd "$(dirname "$0")/.."
PALETTE_DIR=$(pwd)
BUNDLE_DIR="$PALETTE_DIR/vscode-extension/bundled"

print_status "Working in: $PALETTE_DIR"
print_status "Bundle directory: $BUNDLE_DIR"

# Step 1: Clean previous bundle
print_status "Step 1: Cleaning previous bundle..."
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"
print_success "Bundle directory created"

# Step 2: Create portable Python environment
print_status "Step 2: Creating portable Python environment..."
python3 -m venv "$BUNDLE_DIR/python-env"
source "$BUNDLE_DIR/python-env/bin/activate"

# Install Palette CLI as editable in bundle environment
pip install -e "$PALETTE_DIR"

# Install additional dependencies if needed
if [[ -f "$PALETTE_DIR/requirements.txt" ]]; then
    pip install -r "$PALETTE_DIR/requirements.txt"
fi

print_success "Portable Python environment created"

# Step 3: Copy Palette source code
print_status "Step 3: Copying Palette source code..."
cp -r "$PALETTE_DIR/src" "$BUNDLE_DIR/"
cp "$PALETTE_DIR/setup.py" "$BUNDLE_DIR/"
cp "$PALETTE_DIR/requirements.txt" "$BUNDLE_DIR/"
print_success "Source code copied"

# Step 4: Create bundle launcher script
print_status "Step 4: Creating bundle launcher..."
cat > "$BUNDLE_DIR/palette-launcher.py" << 'EOF'
#!/usr/bin/env python3
"""
Bundled Palette CLI Launcher
This script ensures the bundled Python environment is used
"""
import sys
import os
from pathlib import Path

# Get the directory containing this script
bundle_dir = Path(__file__).parent
python_env = bundle_dir / "python-env"

# Add the bundled source to Python path
sys.path.insert(0, str(bundle_dir / "src"))

# Set up environment for the bundled CLI
os.environ["PYTHONPATH"] = str(bundle_dir / "src")

# Import and run the main CLI
try:
    from palette.cli.main import main
    main()
except ImportError as e:
    print(f"Error: Could not import Palette CLI: {e}")
    print(f"Bundle directory: {bundle_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)
EOF

chmod +x "$BUNDLE_DIR/palette-launcher.py"
print_success "Bundle launcher created"

# Step 5: Update VS Code extension to use bundled CLI
print_status "Step 5: Updating VS Code extension..."

# Create updated paletteService.ts that uses bundled CLI
cat > "$PALETTE_DIR/vscode-extension/src/paletteService.bundled.ts" << 'EOF'
import * as vscode from 'vscode';
import { exec, spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

// Import existing interface definitions
export interface GenerateOptions {
    prompt: string;
    outputPath?: string;
    framework?: string;
    model?: string;
    uiLibrary?: string;
    showLibraryWarnings?: boolean;
}

export interface AnalyzeResult {
    framework?: string;
    styling?: string;
    hasTypeScript?: boolean;
    hasTailwind?: boolean;
    componentsPath?: string;
}

export class PaletteService {
    private workspaceRoot: string | undefined;
    private bundledCliPath: string;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        
        // Use bundled CLI instead of system CLI
        this.bundledCliPath = path.join(__dirname, '..', 'bundled', 'python-env', 'bin', 'python3');
        this.outputChannel = vscode.window.createOutputChannel('Code Palette');
        
        this.outputChannel.appendLine('🎁 Using bundled Palette CLI');
        this.outputChannel.appendLine(`📁 Bundle path: ${this.bundledCliPath}`);
    }

    private async findPaletteCLI(): Promise<string> {
        const bundledLauncher = path.join(__dirname, '..', 'bundled', 'palette-launcher.py');
        
        if (fs.existsSync(bundledLauncher)) {
            this.outputChannel.appendLine(`✅ Using bundled Palette CLI: ${bundledLauncher}`);
            return bundledLauncher;
        }
        
        throw new Error('Bundled Palette CLI not found. Extension may be corrupted.');
    }

    async conversationalGenerate(
        message: string,
        conversationHistory: Array<{role: string, content: string}> = []
    ): Promise<{response: string, metadata?: any}> {
        this.outputChannel.appendLine('🚀 Starting conversational generation with bundled CLI...');
        
        try {
            const bundledCliPath = await this.findPaletteCLI();
            
            // Build command for conversational generation using bundled launcher
            const args = [
                bundledCliPath,  // Python script to run
                'conversation',
                '--message', message,
                '--project-path', this.workspaceRoot || process.cwd()
            ];

            if (conversationHistory.length > 0) {
                args.push('--history', JSON.stringify(conversationHistory));
            }

            // Use bundled Python environment
            const pythonExe = path.join(__dirname, '..', 'bundled', 'python-env', 'bin', 'python3');
            
            this.outputChannel.appendLine(`🎯 Command: ${pythonExe} ${args.join(' ')}`);
            
            return new Promise((resolve, reject) => {
                const proc = spawn(pythonExe, args, {
                    cwd: this.workspaceRoot,
                    stdio: ['pipe', 'pipe', 'pipe']
                });

                let outputBuffer = '';
                let errorBuffer = '';

                proc.stdout?.on('data', (data) => {
                    const chunk = data.toString();
                    outputBuffer += chunk;
                    this.outputChannel.append(`[stdout] ${chunk}`);
                });

                proc.stderr?.on('data', (data) => {
                    const chunk = data.toString();
                    errorBuffer += chunk;
                    this.outputChannel.append(`[stderr] ${chunk}`);
                });

                proc.on('close', (code) => {
                    if (code === 0 && outputBuffer.trim()) {
                        try {
                            const parsed = JSON.parse(outputBuffer.trim());
                            resolve(parsed);
                        } catch {
                            resolve({ response: outputBuffer.trim() });
                        }
                    } else {
                        reject(new Error(errorBuffer.trim() || `Process exited with code ${code}`));
                    }
                });

                proc.on('error', (err) => {
                    reject(new Error(`Failed to start bundled CLI: ${err.message}`));
                });
            });

        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Bundled CLI failed: ${error.message}`);
            throw error;
        }
    }

    // Add other methods from original PaletteService here...
    // (checkInstallation, analyzeProject, generateComponent, etc.)
}
EOF

print_success "Updated VS Code extension for bundled CLI"

# Step 6: Update package.json to include bundled files
print_status "Step 6: Updating package.json..."

# Backup original package.json
cp "$PALETTE_DIR/vscode-extension/package.json" "$PALETTE_DIR/vscode-extension/package.json.backup"

# Add bundled files to package.json
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('$PALETTE_DIR/vscode-extension/package.json', 'utf8'));

// Add bundled directory to files that should be included
if (!pkg.files) pkg.files = [];
pkg.files.push('bundled/**');
pkg.files.push('out/**');

// Update display name to indicate it's bundled
pkg.displayName = 'Palette AI (Bundled)';
pkg.description = 'AI-powered component generator with embedded CLI - no separate installation required';

// Add bundled version to package info
pkg.bundled = true;
pkg.version = pkg.version + '-bundled';

fs.writeFileSync('$PALETTE_DIR/vscode-extension/package.json', JSON.stringify(pkg, null, 2));
console.log('✅ package.json updated for bundled distribution');
"

print_success "package.json updated"

# Step 7: Create installation script for bundled extension
print_status "Step 7: Creating installation script..."
cat > "$BUNDLE_DIR/install-bundled-extension.sh" << 'EOF'
#!/bin/bash
echo "📦 Installing Bundled Palette VS Code Extension"
echo "This will install the extension with embedded Palette CLI"

cd "$(dirname "$0")/.."
npm install
npm run compile

echo "✅ To install in VS Code:"
echo "1. Open VS Code"
echo "2. Press Ctrl+Shift+P"  
echo "3. Type 'Extensions: Install from VSIX'"
echo "4. Select the generated .vsix file"
echo ""
echo "Or run: code --install-extension palette-bundled.vsix"
EOF

chmod +x "$BUNDLE_DIR/install-bundled-extension.sh"
print_success "Installation script created"

# Step 8: Compile extension
print_status "Step 8: Compiling bundled extension..."
cd "$PALETTE_DIR/vscode-extension"
npm install
npm run compile

if [[ $? -eq 0 ]]; then
    print_success "Extension compiled successfully"
else
    print_error "Extension compilation failed"
    exit 1
fi

# Step 9: Package as VSIX
print_status "Step 9: Creating VSIX package..."
if command -v vsce >/dev/null 2>&1; then
    vsce package --out palette-bundled.vsix
    print_success "VSIX package created: palette-bundled.vsix"
else
    print_warning "vsce not found. Install with: npm install -g @vscode/vsce"
    print_warning "Then run: vsce package --out palette-bundled.vsix"
fi

echo ""
echo "🎉 Bundling Complete!"
echo "===================="
print_success "Bundled extension ready for distribution"
print_success "Bundle size: $(du -sh "$BUNDLE_DIR" | cut -f1)"

echo ""
echo "📋 Distribution Files:"
echo "  • palette-bundled.vsix (if vsce available)"
echo "  • vscode-extension/ (entire directory)"
echo "  • bundled/ (embedded CLI)"

echo ""
echo "📦 To Install:"
echo "1. Run: code --install-extension palette-bundled.vsix"
echo "2. Or use VS Code Extensions view → Install from VSIX"
echo "3. No separate Palette CLI installation needed!"

echo ""
print_status "Bundle contents:"
ls -la "$BUNDLE_DIR"