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
