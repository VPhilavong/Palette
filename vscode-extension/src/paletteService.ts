import * as vscode from 'vscode';
import { exec, spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export interface GenerateOptions {
    prompt: string;
    outputPath?: string;
    framework?: string;
    model?: string;
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
    private palettePath: string;
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        this.palettePath = vscode.workspace.getConfiguration('palette').get('cliPath', 'palette');
        this.outputChannel = vscode.window.createOutputChannel('Code Palette');
    }

    private async findPaletteCLI(): Promise<string> {
        // First try the configured path
        if (this.palettePath !== 'palette') {
            if (fs.existsSync(this.palettePath)) {
                this.outputChannel.appendLine(`✅ Using configured palette path: ${this.palettePath}`);
                return this.palettePath;
            } else {
                this.outputChannel.appendLine(`⚠️  Configured palette path not found: ${this.palettePath}`);
            }
        }

        // Try to find palette in common locations
        const possiblePaths = [
            // First check the local venv relative to VS Code extension
            path.join(__dirname, '..', '..', '..', 'venv', 'bin', 'palette'),
            // Then check user's home directory project
            path.join(process.env.HOME || '', 'Projects', 'Palette', 'venv', 'bin', 'palette'),
            // Then check system-wide installations
            path.join(process.env.HOME || '', '.local', 'bin', 'palette'),
            '/usr/local/bin/palette',
            '/usr/bin/palette'
        ];

        this.outputChannel.appendLine('🔍 Searching for Palette CLI in the following locations:');
        
        for (const palettePath of possiblePaths) {
            this.outputChannel.appendLine(`  Checking: ${palettePath}`);
            
            if (fs.existsSync(palettePath)) {
                try {
                    // Test that it actually works by checking version
                    await this.execCommand(`"${palettePath}" --version`);
                    this.outputChannel.appendLine(`✅ Found working Palette CLI: ${palettePath}`);
                    return palettePath;
                } catch (error) {
                    this.outputChannel.appendLine(`⚠️  Found file but execution failed: ${error}`);
                }
            }
        }

        // Try using 'which' as final fallback for PATH-based installations
        try {
            const whichResult = await this.execCommand('which palette');
            if (whichResult.trim()) {
                this.outputChannel.appendLine(`✅ Found Palette CLI in PATH: ${whichResult.trim()}`);
                return whichResult.trim();
            }
        } catch {
            // Continue to error
        }

        this.outputChannel.appendLine('❌ Palette CLI not found in any location');
        throw new Error('Palette CLI not found. Please install it or configure the path in VS Code settings (palette.cliPath).');
    }

    private execCommand(command: string): Promise<string> {
        return new Promise((resolve, reject) => {
            // Create environment with API keys from both env vars and VS Code settings
            const processEnv = { ...process.env };
            
            // Get API keys from VS Code settings if not in environment
            const openaiKey = process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('openaiApiKey');
            const anthropicKey = process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('anthropicApiKey');
            
            if (openaiKey) {
                processEnv.OPENAI_API_KEY = openaiKey;
            }
            if (anthropicKey) {
                processEnv.ANTHROPIC_API_KEY = anthropicKey;
            }
            
            exec(command, { 
                cwd: this.workspaceRoot,
                env: processEnv
            }, (error, stdout, stderr) => {
                if (error) {
                    reject(new Error(`Command failed: ${error.message}\n${stderr}`));
                } else {
                    resolve(stdout.trim());
                }
            });
        });
    }

    async checkInstallation(): Promise<boolean> {
        this.outputChannel.appendLine('🔍 Checking Palette installation...');
        
        try {
            // Check CLI availability
            const palettePath = await this.findPaletteCLI();
            const version = await this.execCommand(`"${palettePath}" --version`);
            this.outputChannel.appendLine(`✅ Palette CLI found: ${version}`);
            
            // Check for API keys from both environment and VS Code settings
            const hasOpenAI = !!(process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get('openaiApiKey'));
            const hasAnthropic = !!(process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get('anthropicApiKey'));
            
            if (!hasOpenAI && !hasAnthropic) {
                this.outputChannel.appendLine('⚠️  Warning: No API keys found');
                this.outputChannel.appendLine('  Please set either:');
                this.outputChannel.appendLine('  - OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables');
                this.outputChannel.appendLine('  - Configure keys in VS Code settings (palette.openaiApiKey or palette.anthropicApiKey)');
                return false;
            } else {
                const provider = hasOpenAI ? 'OpenAI' : 'Anthropic';
                this.outputChannel.appendLine(`✅ ${provider} API key configured`);
            }
            
            // Test a simple CLI command to ensure everything works
            try {
                await this.execCommand(`"${palettePath}" --help`);
                this.outputChannel.appendLine('✅ CLI execution test passed');
            } catch (testError) {
                this.outputChannel.appendLine(`⚠️  CLI execution test failed: ${testError}`);
                return false;
            }
            
            this.outputChannel.appendLine('🎉 All checks passed! Palette is ready to use.');
            return true;
        } catch (error) {
            this.outputChannel.appendLine(`❌ Installation check failed: ${error}`);
            return false;
        }
    }

    async analyzeProject(): Promise<AnalyzeResult> {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder open');
        }

        try {
            const palettePath = await this.findPaletteCLI();
            const output = await this.execCommand(`cd "${this.workspaceRoot}" && ${palettePath} analyze --json`);
            
            // Try to parse JSON output
            try {
                return JSON.parse(output);
            } catch {
                // Fallback to parsing text output
                const result: AnalyzeResult = {};
                
                if (output.includes('Next.js')) result.framework = 'next.js';
                else if (output.includes('React')) result.framework = 'react';
                else if (output.includes('Vue')) result.framework = 'vue';
                
                if (output.includes('Tailwind')) result.hasTailwind = true;
                if (output.includes('TypeScript')) result.hasTypeScript = true;
                if (output.includes('CSS Modules')) result.styling = 'css-modules';
                else if (output.includes('styled-components')) result.styling = 'styled-components';
                else if (output.includes('Tailwind')) result.styling = 'tailwind';
                
                return result;
            }
        } catch (error) {
            this.outputChannel.appendLine(`Analysis failed: ${error}`);
            throw error;
        }
    }

    async generateComponent(options: GenerateOptions): Promise<string> {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder open');
        }

        const palettePath = await this.findPaletteCLI();
        
        // Build command with properly escaped prompt
        const escapedPrompt = options.prompt.replace(/"/g, '\\"');
        let command = `cd "${this.workspaceRoot}" && "${palettePath}" generate "${escapedPrompt}"`;
        
        if (options.framework) {
            command += ` --framework ${options.framework}`;
        }
        
        if (options.model) {
            command += ` --model ${options.model}`;
        }
        
        if (options.outputPath) {
            command += ` --output "${options.outputPath}"`;
        }

        // Don't add --json flag as it doesn't exist in the CLI
        // command += ' --json';

        this.outputChannel.appendLine(`Running: ${command}`);
        this.outputChannel.show();

        try {
            const output = await this.execCommand(command);
            
            // Try to parse JSON response
            try {
                const result = JSON.parse(output);
                if (result.error) {
                    throw new Error(result.error);
                }
                return result.component || result.output || output;
            } catch {
                // Return raw output if not JSON
                return output;
            }
        } catch (error) {
            this.outputChannel.appendLine(`Generation failed: ${error}`);
            throw error;
        }
    }

    async generateWithProgress(options: GenerateOptions): Promise<string> {
        return vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating component...",
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: "Analyzing project..." });
            
            // First analyze the project if framework not specified
            if (!options.framework) {
                try {
                    const analysis = await this.analyzeProject();
                    options.framework = analysis.framework;
                    progress.report({ increment: 30, message: "Detected " + (analysis.framework || 'React') });
                } catch {
                    // Continue without framework detection
                }
            }
            
            progress.report({ increment: 50, message: "Generating with AI..." });
            
            const result = await this.generateComponent(options);
            
            progress.report({ increment: 100, message: "Complete!" });
            
            return result;
        });
    }

    streamGenerate(options: GenerateOptions, onData: (data: string) => void, onError: (error: string) => void): Promise<void> {
        return new Promise(async (resolve, reject) => {
            console.log('streamGenerate called with options:', options);
            console.log('workspaceRoot:', this.workspaceRoot);
            
            if (!this.workspaceRoot) {
                const error = 'No workspace folder open';
                console.error('streamGenerate error:', error);
                onError(error);
                reject(new Error(error));
                return;
            }

            // Check for API keys before starting
            const hasOpenAI = !!(process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get('openaiApiKey'));
            const hasAnthropic = !!(process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get('anthropicApiKey'));
            
            if (!hasOpenAI && !hasAnthropic) {
                const error = 'No API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in environment variables or VS Code settings';
                this.outputChannel.appendLine(`❌ ${error}`);
                onError(error);
                reject(new Error(error));
                return;
            }

            try {
                const palettePath = await this.findPaletteCLI();
                this.outputChannel.appendLine(`Using Palette CLI: ${palettePath}`);
                
                // Build command arguments
                // The prompt needs to be properly quoted for the CLI
                const args = ['generate', options.prompt];
                
                if (options.framework) {
                    args.push('--framework', options.framework);
                }
                
                if (options.model) {
                    args.push('--model', options.model);
                }
                
                if (options.outputPath) {
                    args.push('--output', options.outputPath);
                }

                // Create environment with API keys from both env vars and VS Code settings
                const processEnv = { ...process.env };
                
                // Get API keys from VS Code settings if not in environment
                const openaiKey = process.env.OPENAI_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('openaiApiKey');
                const anthropicKey = process.env.ANTHROPIC_API_KEY || vscode.workspace.getConfiguration('palette').get<string>('anthropicApiKey');
                
                if (openaiKey) {
                    processEnv.OPENAI_API_KEY = openaiKey;
                }
                if (anthropicKey) {
                    processEnv.ANTHROPIC_API_KEY = anthropicKey;
                }

                // Debug: Log environment variables being passed (without exposing keys)
                this.outputChannel.appendLine('Environment variables being passed to CLI:');
                this.outputChannel.appendLine(`  OPENAI_API_KEY: ${processEnv.OPENAI_API_KEY ? 'Set (***' + processEnv.OPENAI_API_KEY.slice(-4) + ')' : 'Not set'}`);
                this.outputChannel.appendLine(`  ANTHROPIC_API_KEY: ${processEnv.ANTHROPIC_API_KEY ? 'Set (***' + processEnv.ANTHROPIC_API_KEY.slice(-4) + ')' : 'Not set'}`);
                this.outputChannel.appendLine(`  Working Directory: ${this.workspaceRoot}`);

                // For shell execution, we need to build the full command as a string
                // to properly handle quotes and spaces in the prompt
                let fullCommand = `"${palettePath}" generate "${options.prompt.replace(/"/g, '\\"')}"`;
                
                if (options.framework) {
                    fullCommand += ` --framework ${options.framework}`;
                }
                
                if (options.model) {
                    fullCommand += ` --model ${options.model}`;
                }
                
                if (options.outputPath) {
                    fullCommand += ` --output "${options.outputPath}"`;
                }
                
                this.outputChannel.appendLine(`Executing command: ${fullCommand}`);

                // Spawn the process with shell to handle the command properly
                const proc = spawn(fullCommand, [], {
                    cwd: this.workspaceRoot,
                    env: processEnv,
                    shell: true  // Use shell to handle quotes properly
                });

                let buffer = '';
                let errorBuffer = '';

                proc.stdout.on('data', (data) => {
                    const text = data.toString();
                    buffer += text;
                    
                    // Send only the new text, not the entire buffer
                    onData(text);
                    this.outputChannel.append(text);
                });

                proc.stderr.on('data', (data) => {
                    const text = data.toString();
                    errorBuffer += text;
                    
                    // Only send to UI if it's a real error, not just info
                    if (text.toLowerCase().includes('error') || text.toLowerCase().includes('failed')) {
                        onError(text);
                    }
                    
                    this.outputChannel.append(`[STDERR] ${text}`);
                });

                proc.on('close', (code) => {
                    if (code === 0) {
                        resolve();
                    } else {
                        const errorMsg = errorBuffer || `Process exited with code ${code}`;
                        onError(`Generation failed: ${errorMsg}`);
                        reject(new Error(errorMsg));
                    }
                });

                proc.on('error', (err) => {
                    onError(`Failed to start process: ${err.message}`);
                    reject(err);
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    async testEnvironment(): Promise<void> {
        this.outputChannel.appendLine('=== Testing Environment Variables ===');
        this.outputChannel.appendLine(`Node process.env.OPENAI_API_KEY: ${process.env.OPENAI_API_KEY ? 'Set' : 'Not set'}`);
        this.outputChannel.appendLine(`Node process.env.ANTHROPIC_API_KEY: ${process.env.ANTHROPIC_API_KEY ? 'Set' : 'Not set'}`);
        
        try {
            // Test with Python script
            const testScript = path.join(__dirname, '..', '..', '..', 'test_env.py');
            const output = await this.execCommand(`python3 ${testScript}`);
            this.outputChannel.appendLine('Python subprocess output:');
            this.outputChannel.appendLine(output);
        } catch (error) {
            this.outputChannel.appendLine(`Test failed: ${error}`);
        }
    }

    getOutputChannel(): vscode.OutputChannel {
        return this.outputChannel;
    }
}