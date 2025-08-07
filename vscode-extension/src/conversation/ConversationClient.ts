/**
 * Native conversation client that directly integrates with the Palette Python conversation engine
 * without CLI dependencies. Provides streaming responses and proper error handling.
 */

import { spawn, ChildProcess } from 'child_process';
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

export interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: any;
}

export interface ConversationResponse {
    response: string;
    sessionId: string;
    metadata?: {
        componentCode?: string;
        intent?: string;
        generationMethod?: string;
        previewResult?: any;
        [key: string]: any;
    };
}

export interface ConversationOptions {
    projectPath?: string;
    sessionId?: string;
    streamCallback?: (chunk: string) => void;
    errorCallback?: (error: string) => void;
    progressCallback?: (stage: string, progress: number) => void;
}

export class ConversationClient {
    private pythonPath: string;
    private palettePath: string;
    private outputChannel: vscode.OutputChannel;
    private conversationHistory: ConversationMessage[] = [];
    private currentSessionId: string | null = null;

    constructor(outputChannel: vscode.OutputChannel) {
        this.outputChannel = outputChannel;
        this.pythonPath = this.findPythonPath();
        this.palettePath = this.findPalettePath();
    }

    private findPythonPath(): string {
        // Try to find Python executable
        const possiblePaths = [
            'python3',
            'python',
            '/usr/bin/python3',
            '/usr/local/bin/python3'
        ];

        for (const pythonPath of possiblePaths) {
            try {
                // Test if this python path works
                return pythonPath;
            } catch (error) {
                continue;
            }
        }

        return 'python3'; // Default fallback
    }

    private findPalettePath(): string {
        // Try to find Palette project directory
        const possiblePaths = [
            '/home/vphilavong/Projects/Palette',
            path.join(process.env.HOME || '', 'Projects', 'Palette'),
            path.join(__dirname, '..', '..', '..', '..'),  // Relative to extension
        ];

        for (const possiblePath of possiblePaths) {
            if (fs.existsSync(path.join(possiblePath, 'src', 'palette'))) {
                this.outputChannel.appendLine(`✅ Found Palette project at: ${possiblePath}`);
                return possiblePath;
            }
        }

        throw new Error('Could not find Palette project directory. Please ensure Palette is installed.');
    }

    async initialize(): Promise<boolean> {
        try {
            this.outputChannel.appendLine('🚀 Initializing conversation client...');
            
            // Test Python availability
            const pythonTest = await this.runPythonCommand(['-c', 'import sys; print(sys.version)']);
            this.outputChannel.appendLine(`✅ Python available: ${pythonTest.trim()}`);

            // Test Palette module availability
            const moduleTest = await this.runPythonCommand([
                '-c',
                'import sys; sys.path.insert(0, "src"); from palette.conversation import ConversationEngine; print("Palette module OK")'
            ]);
            this.outputChannel.appendLine(`✅ Palette module: ${moduleTest.trim()}`);

            // Check API keys
            const hasApiKey = this.checkApiKeys();
            if (!hasApiKey) {
                this.outputChannel.appendLine('⚠️ Warning: No API keys configured');
                return false;
            }

            this.outputChannel.appendLine('🎉 Conversation client initialized successfully!');
            return true;

        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Initialization failed: ${error.message}`);
            return false;
        }
    }

    private checkApiKeys(): boolean {
        const config = vscode.workspace.getConfiguration('palette');
        const openaiKey = process.env.OPENAI_API_KEY || config.get<string>('openaiApiKey');
        const anthropicKey = process.env.ANTHROPIC_API_KEY || config.get<string>('anthropicApiKey');
        
        if (openaiKey) {
            this.outputChannel.appendLine('✅ OpenAI API key configured');
            return true;
        }
        
        if (anthropicKey) {
            this.outputChannel.appendLine('✅ Anthropic API key configured');
            return true;
        }

        return false;
    }

    async sendMessage(message: string, options: ConversationOptions = {}): Promise<ConversationResponse> {
        this.outputChannel.appendLine(`💬 Processing message: ${message.substring(0, 100)}...`);

        try {
            // Add user message to history
            const userMessage: ConversationMessage = {
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            };
            this.conversationHistory.push(userMessage);

            // Prepare the conversation script
            const response = await this.runConversation(message, options);

            // Add assistant response to history
            const assistantMessage: ConversationMessage = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
                metadata: response.metadata
            };
            this.conversationHistory.push(assistantMessage);

            // Update session ID
            this.currentSessionId = response.sessionId;

            return response;

        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Message processing failed: ${error.message}`);
            
            // Return error response
            return {
                response: `I encountered an error: ${error.message}`,
                sessionId: this.currentSessionId || 'error-session',
                metadata: { error: error.message }
            };
        }
    }

    private async runConversation(message: string, options: ConversationOptions): Promise<ConversationResponse> {
        return new Promise((resolve, reject) => {
            const env = { ...process.env };
            
            // Set API keys from VS Code settings
            const config = vscode.workspace.getConfiguration('palette');
            const openaiKey = env.OPENAI_API_KEY || config.get<string>('openaiApiKey');
            const anthropicKey = env.ANTHROPIC_API_KEY || config.get<string>('anthropicApiKey');
            
            if (openaiKey) env.OPENAI_API_KEY = openaiKey;
            if (anthropicKey) env.ANTHROPIC_API_KEY = anthropicKey;

            // Create the conversation script inline
            const conversationScript = `
import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))

try:
    from palette.conversation import ConversationEngine
    
    # Initialize conversation engine
    project_path = "${options.projectPath || process.cwd()}"
    engine = ConversationEngine(project_path=project_path)
    
    # Start conversation
    session_id = engine.start_conversation(${options.sessionId ? `"${options.sessionId}"` : 'None'})
    
    # Add conversation history if available
    ${this.conversationHistory.length > 0 ? `
    history = ${JSON.stringify(this.conversationHistory)}
    for msg in history:
        from palette.conversation.conversation_engine import ConversationMessage
        from datetime import datetime
        message_obj = ConversationMessage(
            role=msg['role'],
            content=msg['content'], 
            timestamp=datetime.fromisoformat(msg['timestamp'])
        )
        engine.current_context.messages.append(message_obj)
    ` : ''}
    
    # Process the message
    response, metadata = engine.process_message("${message.replace(/"/g, '\\"')}")
    
    # Serialize metadata safely
    def serialize_metadata(obj):
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif hasattr(obj, '__dict__'):
            return {k: serialize_metadata(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: serialize_metadata(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize_metadata(item) for item in obj]
        else:
            return str(obj)
    
    # Output result as JSON
    result = {
        "response": response,
        "sessionId": session_id,
        "metadata": serialize_metadata(metadata)
    }
    
    print(json.dumps(result, indent=2))
    
except Exception as e:
    import traceback
    error_result = {
        "response": f"I encountered an error: {str(e)}",
        "sessionId": "error-session",
        "metadata": {"error": str(e), "traceback": traceback.format_exc()}
    }
    print(json.dumps(error_result, indent=2))
`;

            // Create temporary script file
            const scriptPath = path.join(this.palettePath, 'temp_conversation.py');
            fs.writeFileSync(scriptPath, conversationScript);

            // Run the conversation
            const proc = spawn(this.pythonPath, [scriptPath], {
                cwd: this.palettePath,
                env: env,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let outputBuffer = '';
            let errorBuffer = '';

            proc.stdout?.on('data', (data) => {
                const chunk = data.toString();
                outputBuffer += chunk;
                
                // Send streaming updates if callback provided
                if (options.streamCallback) {
                    // Parse partial responses for streaming
                    this.parseStreamingResponse(chunk, options.streamCallback);
                }
            });

            proc.stderr?.on('data', (data) => {
                const chunk = data.toString();
                errorBuffer += chunk;
                this.outputChannel.append(`[stderr] ${chunk}`);
                
                // Send progress updates if callback provided
                if (options.progressCallback) {
                    this.parseProgressUpdate(chunk, options.progressCallback);
                }
            });

            proc.on('close', (code) => {
                // Clean up temporary script
                try {
                    fs.unlinkSync(scriptPath);
                } catch (error) {
                    // Ignore cleanup errors
                }

                if (code === 0) {
                    try {
                        const result = JSON.parse(outputBuffer.trim());
                        resolve(result);
                    } catch (parseError: any) {
                        reject(new Error(`Failed to parse response: ${parseError.message}\nOutput: ${outputBuffer}`));
                    }
                } else {
                    const errorMsg = errorBuffer || `Process exited with code ${code}`;
                    if (options.errorCallback) {
                        options.errorCallback(errorMsg);
                    }
                    reject(new Error(errorMsg));
                }
            });

            proc.on('error', (err) => {
                // Clean up temporary script
                try {
                    fs.unlinkSync(scriptPath);
                } catch (error) {
                    // Ignore cleanup errors
                }
                
                if (options.errorCallback) {
                    options.errorCallback(err.message);
                }
                reject(new Error(`Failed to start conversation process: ${err.message}`));
            });
        });
    }

    private parseStreamingResponse(chunk: string, callback: (chunk: string) => void): void {
        // Look for progress indicators in the output
        const lines = chunk.split('\n');
        for (const line of lines) {
            if (line.includes('🎨') || line.includes('✅') || line.includes('🚀') || 
                line.includes('Analyzing') || line.includes('Generating') || 
                line.includes('Processing')) {
                callback(line.trim());
            }
        }
    }

    private parseProgressUpdate(chunk: string, callback: (stage: string, progress: number) => void): void {
        // Parse progress from stderr debug output
        if (chunk.includes('Analyzing')) {
            callback('Analyzing project structure...', 20);
        } else if (chunk.includes('Generating')) {
            callback('Generating component...', 60);
        } else if (chunk.includes('Validating')) {
            callback('Validating code quality...', 80);
        } else if (chunk.includes('Complete')) {
            callback('Generation complete!', 100);
        }
    }

    private async runPythonCommand(args: string[]): Promise<string> {
        return new Promise((resolve, reject) => {
            const proc = spawn(this.pythonPath, args, {
                cwd: this.palettePath,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let output = '';
            let error = '';

            proc.stdout?.on('data', (data) => {
                output += data.toString();
            });

            proc.stderr?.on('data', (data) => {
                error += data.toString();
            });

            proc.on('close', (code) => {
                if (code === 0) {
                    resolve(output.trim());
                } else {
                    reject(new Error(error || `Command failed with code ${code}`));
                }
            });

            proc.on('error', (err) => {
                reject(err);
            });
        });
    }

    getConversationHistory(): ConversationMessage[] {
        return [...this.conversationHistory];
    }

    getCurrentSessionId(): string | null {
        return this.currentSessionId;
    }

    clearHistory(): void {
        this.conversationHistory = [];
        this.currentSessionId = null;
    }

    async analyzeProject(projectPath?: string): Promise<any> {
        this.outputChannel.appendLine('🔍 Analyzing project...');
        
        try {
            const analysisScript = `
import sys
import json
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path.cwd() / "src"))

try:
    from palette.analysis.context import ProjectAnalyzer
    
    analyzer = ProjectAnalyzer()
    result = analyzer.analyze("${projectPath || process.cwd()}")
    
    print(json.dumps(result, indent=2, default=str))
    
except Exception as e:
    import traceback
    error_result = {
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    print(json.dumps(error_result, indent=2))
`;

            const scriptPath = path.join(this.palettePath, 'temp_analyze.py');
            fs.writeFileSync(scriptPath, analysisScript);

            try {
                const output = await this.runPythonCommand([scriptPath]);
                fs.unlinkSync(scriptPath);
                
                const result = JSON.parse(output);
                this.outputChannel.appendLine('✅ Project analysis complete');
                return result;
                
            } catch (error) {
                try { fs.unlinkSync(scriptPath); } catch {}
                throw error;
            }
            
        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Project analysis failed: ${error.message}`);
            throw error;
        }
    }

    async generatePreview(componentCode: string, options: any = {}): Promise<any> {
        this.outputChannel.appendLine('🖼️ Generating component preview...');
        
        try {
            const previewScript = `
import sys
import json
import asyncio
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path.cwd() / "src"))

try:
    from palette.preview.preview_generator import PreviewGenerator, PreviewConfig, PreviewSize
    
    async def generate_preview():
        generator = PreviewGenerator("${options.projectPath || process.cwd()}")
        
        # Create preview config
        size = PreviewSize.DESKTOP
        if "${options.size}" == "mobile":
            size = PreviewSize.MOBILE
        elif "${options.size}" == "tablet":
            size = PreviewSize.TABLET
            
        config = PreviewConfig(
            size=size,
            theme="${options.theme || 'light'}",
            interactive=True,
            include_variants=${options.includeVariants || 'False'}
        )
        
        result = await generator.generate_component_preview(
            "${options.prompt || 'Preview component'}",
            config
        )
        
        # Serialize result
        return {
            "html": result.html,
            "css": result.css, 
            "javascript": result.javascript,
            "variants": result.variants,
            "metadata": result.metadata
        }
    
    # Run async function
    result = asyncio.run(generate_preview())
    print(json.dumps(result, indent=2, default=str))
    
except Exception as e:
    import traceback
    error_result = {
        "error": str(e),
        "traceback": traceback.format_exc()
    }
    print(json.dumps(error_result, indent=2))
`;

            const scriptPath = path.join(this.palettePath, 'temp_preview.py');
            fs.writeFileSync(scriptPath, previewScript);

            try {
                const output = await this.runPythonCommand([scriptPath]);
                fs.unlinkSync(scriptPath);
                
                const result = JSON.parse(output);
                this.outputChannel.appendLine('✅ Preview generation complete');
                return result;
                
            } catch (error) {
                try { fs.unlinkSync(scriptPath); } catch {}
                throw error;
            }
            
        } catch (error: any) {
            this.outputChannel.appendLine(`❌ Preview generation failed: ${error.message}`);
            throw error;
        }
    }
}