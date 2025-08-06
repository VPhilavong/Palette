#!/bin/bash

# 📦 Simple VS Code Bundle - Core CLI Only
# Creates a lightweight bundle without heavy ML dependencies

echo "📦 Creating Simple Palette Bundle"
echo "================================="

cd "$(dirname "$0")/.."
PALETTE_DIR=$(pwd)
BUNDLE_DIR="$PALETTE_DIR/vscode-extension/bundled"

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

# Step 1: Clean and create bundle directory
print_status "Step 1: Creating bundle structure..."
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Step 2: Copy core Python files
print_status "Step 2: Copying Palette source..."
cp -r "$PALETTE_DIR/src" "$BUNDLE_DIR/"
cp "$PALETTE_DIR/setup.py" "$BUNDLE_DIR/"

# Create requirements-minimal.txt (without heavy ML dependencies)
cat > "$BUNDLE_DIR/requirements-minimal.txt" << 'EOF'
click>=8.1.0
rich>=13.0.0
requests>=2.28.0
jinja2>=3.1.0
python-dotenv>=1.0.0
openai>=1.0.0
anthropic>=0.18.0
pathlib2>=2.3.0
EOF

print_success "Core files copied"

# Step 3: Create lightweight Python launcher
print_status "Step 3: Creating bundle launcher..."
cat > "$BUNDLE_DIR/run-palette.py" << 'EOF'
#!/usr/bin/env python3
"""
Lightweight Palette CLI Bundle Launcher
Uses system Python with minimal dependencies
"""
import sys
import os
from pathlib import Path

# Get bundle directory
bundle_dir = Path(__file__).parent

# Add bundle source to Python path
sys.path.insert(0, str(bundle_dir / "src"))

# Check for required packages
try:
    import click
    import rich
    import openai
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please install: pip install click rich openai anthropic requests jinja2 python-dotenv")
    sys.exit(1)

# Import and run Palette CLI
try:
    from palette.cli.main import main
    main()
except Exception as e:
    print(f"❌ Error starting Palette: {e}")
    sys.exit(1)
EOF

chmod +x "$BUNDLE_DIR/run-palette.py"
print_success "Bundle launcher created"

# Step 4: Create installation check script
cat > "$BUNDLE_DIR/check-deps.py" << 'EOF'
#!/usr/bin/env python3
"""Check if required dependencies are available"""
import sys

required = ['click', 'rich', 'openai', 'anthropic', 'requests', 'jinja2', 'dotenv']
missing = []

for pkg in required:
    try:
        if pkg == 'dotenv':
            __import__('dotenv')
        else:
            __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print("❌ Missing dependencies:")
    for pkg in missing:
        print(f"  - {pkg}")
    print("\nInstall with: pip install " + " ".join(missing))
    sys.exit(1)
else:
    print("✅ All dependencies available")
    sys.exit(0)
EOF

chmod +x "$BUNDLE_DIR/check-deps.py"

# Step 5: Update VS Code extension service
print_status "Step 5: Creating bundled service implementation..."

cat > "$PALETTE_DIR/vscode-extension/src/paletteService.bundled.ts" << 'EOF'
import * as vscode from 'vscode';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export interface GenerateOptions {
    prompt: string;
    outputPath?: string;
    framework?: string;
    model?: string;
    uiLibrary?: string;
    showLibraryWarnings?: boolean;
}

export class PaletteService {
    private workspaceRoot: string | undefined;
    private bundledPath: string;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        this.bundledPath = path.join(__dirname, '..', 'bundled');
        this.outputChannel = vscode.window.createOutputChannel('Code Palette (Bundled)');
        
        this.outputChannel.appendLine('📦 Using bundled Palette CLI');
        this.outputChannel.appendLine(`📁 Bundle path: ${this.bundledPath}`);
    }

    private async checkDependencies(): Promise<boolean> {
        const checkScript = path.join(this.bundledPath, 'check-deps.py');
        
        return new Promise((resolve) => {
            const proc = spawn('python3', [checkScript], {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            proc.on('close', (code) => {
                resolve(code === 0);
            });
        });
    }

    async checkInstallation(): Promise<boolean> {
        this.outputChannel.appendLine('🔍 Checking bundled installation...');
        
        try {
            // Check if bundle directory exists
            if (!fs.existsSync(this.bundledPath)) {
                this.outputChannel.appendLine('❌ Bundle directory not found');
                return false;
            }

            // Check if launcher exists
            const launcher = path.join(this.bundledPath, 'run-palette.py');
            if (!fs.existsSync(launcher)) {
                this.outputChannel.appendLine('❌ Bundle launcher not found');
                return false;
            }

            // Check dependencies
            const depsOk = await this.checkDependencies();
            if (!depsOk) {
                this.outputChannel.appendLine('❌ Missing Python dependencies');
                this.outputChannel.appendLine('Please install: pip install click rich openai anthropic requests jinja2 python-dotenv');
                return false;
            }

            // Check API keys
            const hasOpenAI = !!(process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get('openaiApiKey'));
            const hasAnthropic = !!(process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get('anthropicApiKey'));
            
            if (!hasOpenAI && !hasAnthropic) {
                this.outputChannel.appendLine('⚠️  Warning: No API keys found');
                return false;
            }

            this.outputChannel.appendLine('✅ Bundled installation ready');
            return true;
            
        } catch (error) {
            this.outputChannel.appendLine(`❌ Installation check failed: ${error}`);
            return false;
        }
    }

    async conversationalGenerate(
        message: string,
        conversationHistory: Array<{role: string, content: string}> = []
    ): Promise<{response: string, metadata?: any}> {
        
        this.outputChannel.appendLine('🚀 Starting conversation with bundled CLI...');
        
        try {
            const launcher = path.join(this.bundledPath, 'run-palette.py');
            
            // Build command arguments
            const args = [
                launcher,
                'conversation',
                '--message', message,
                '--project-path', this.workspaceRoot || process.cwd()
            ];

            if (conversationHistory.length > 0) {
                args.push('--history', JSON.stringify(conversationHistory));
            }

            // Create environment with API keys
            const processEnv = { ...process.env };
            const openaiKey = process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('openaiApiKey');
            const anthropicKey = process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('anthropicApiKey');
            
            if (openaiKey) processEnv.OPENAI_API_KEY = openaiKey;
            if (anthropicKey) processEnv.ANTHROPIC_API_KEY = anthropicKey;

            this.outputChannel.appendLine(`📝 Command: python3 ${args.join(' ')}`);
            
            return new Promise((resolve, reject) => {
                const proc = spawn('python3', args, {
                    cwd: this.workspaceRoot,
                    env: processEnv,
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
            this.outputChannel.appendLine(`❌ Bundled conversation failed: ${error.message}`);
            throw error;
        }
    }

    getOutputChannel(): vscode.OutputChannel {
        return this.outputChannel;
    }
}
EOF

print_success "Bundled service created"

# Step 6: Create simple installer script
cat > "$BUNDLE_DIR/INSTALL.md" << 'EOF'
# 📦 Bundled Palette Installation

## Requirements
- Python 3.8+
- pip

## Quick Install Dependencies
```bash
pip install click rich openai anthropic requests jinja2 python-dotenv
```

## Set API Key
Choose one:
- Environment: `export OPENAI_API_KEY="your-key"`  
- VS Code Settings: Set `palette.openaiApiKey`

## Test Bundle
```bash
python3 run-palette.py --version
```

That's it! The VS Code extension will use this bundle automatically.
EOF

# Step 7: Update VS Code extension to use bundled version  
print_status "Step 7: Compiling extension..."
cd "$PALETTE_DIR/vscode-extension"

# Create a simple switch to use bundled service
cat > src/extension.bundled.ts << 'EOF'
import * as vscode from 'vscode';
import { PaletteService } from './paletteService.bundled';
import { PalettePanel } from './PalettePanel';

let paletteService: PaletteService;

export function activate(context: vscode.ExtensionContext) {
    paletteService = new PaletteService();
    
    // Register commands
    const disposables = [
        vscode.commands.registerCommand('palette.openWebview', () => {
            PalettePanel.createOrShow(context.extensionUri, paletteService);
        }),
        
        vscode.commands.registerCommand('palette.checkInstallation', async () => {
            const isReady = await paletteService.checkInstallation();
            if (isReady) {
                vscode.window.showInformationMessage('✅ Bundled Palette is ready!');
            } else {
                vscode.window.showErrorMessage('❌ Bundled Palette setup incomplete. Check Output panel.');
            }
        })
    ];
    
    context.subscriptions.push(...disposables);
    
    // Show welcome message
    vscode.window.showInformationMessage(
        '📦 Bundled Palette loaded! Press Ctrl+Shift+U to start.',
        'Check Setup'
    ).then(selection => {
        if (selection === 'Check Setup') {
            vscode.commands.executeCommand('palette.checkInstallation');
        }
    });
}

export function deactivate() {}
EOF

npm run compile

if [[ $? -eq 0 ]]; then
    print_success "Extension compiled successfully"
else
    echo "❌ Extension compilation failed"
    exit 1
fi

# Final summary
echo ""
echo "🎉 Simple Bundle Created!"
echo "========================="
print_success "Bundle location: $BUNDLE_DIR"
print_success "Size: $(du -sh "$BUNDLE_DIR" | cut -f1)"

echo ""
echo "📋 What's Included:"
echo "  • Core Palette source code (no ML dependencies)"
echo "  • Lightweight Python launcher"
echo "  • Dependency checker" 
echo "  • Bundled VS Code service"

echo ""
echo "📦 To Use:"
echo "1. Install Python dependencies:"
echo "   pip install click rich openai anthropic requests jinja2 python-dotenv"
echo ""
echo "2. Set API key (choose one):"
echo "   export OPENAI_API_KEY=\"your-key\""
echo "   # OR set in VS Code settings: palette.openaiApiKey"
echo ""
echo "3. Test bundle:"
echo "   python3 $BUNDLE_DIR/run-palette.py --version"
echo ""
echo "4. Use VS Code extension normally!"

echo ""
print_status "Bundle ready for distribution! 🚀"