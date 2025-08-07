/**
 * Enhanced Palette Service using HTTP streaming instead of CLI subprocess
 */

import * as vscode from 'vscode';
import { 
    GenerateRequest, 
    GenerateResponse,
    AnalyzeRequest, 
    AnalyzeResponse,
    StreamingResponse 
} from '../types/messages';

export interface StreamingOptions {
    onChunk?: (chunk: string) => void;
    onComplete?: (response: string, metadata?: any) => void;
    onError?: (error: string) => void;
    onStatus?: (status: string, message?: string) => void;
}

export class StreamingPaletteService {
    private serverUrl: string;
    private outputChannel: vscode.OutputChannel;
    private workspaceRoot: string | undefined;

    constructor() {
        this.serverUrl = vscode.workspace.getConfiguration('palette').get('serverUrl', 'http://localhost:8765');
        this.outputChannel = vscode.window.createOutputChannel('Palette Streaming');
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    /**
     * Check if the streaming server is running and healthy
     */
    async checkHealth(): Promise<boolean> {
        try {
            const response = await fetch(`${this.serverUrl}/health`);
            return response.ok;
        } catch (error) {
            this.outputChannel.appendLine(`❌ Health check failed: ${error}`);
            return false;
        }
    }

    /**
     * Start the Python streaming server if it's not running
     */
    async ensureServerRunning(): Promise<boolean> {
        const isHealthy = await this.checkHealth();
        if (isHealthy) {
            this.outputChannel.appendLine('✅ Streaming server is already running');
            return true;
        }

        this.outputChannel.appendLine('🚀 Starting Palette streaming server...');
        
        // Try to start the server using Python
        try {
            const python = 'python3';
            const serverScript = this.getServerScriptPath();
            
            // Start server in background
            const { spawn } = await import('child_process');
            const serverProcess = spawn(python, [serverScript], {
                detached: true,
                stdio: 'ignore'
            });
            
            serverProcess.unref(); // Don't wait for it to finish

            // Wait a moment for server to start
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check if server is now healthy
            const isNowHealthy = await this.checkHealth();
            if (isNowHealthy) {
                this.outputChannel.appendLine('✅ Streaming server started successfully');
                return true;
            } else {
                this.outputChannel.appendLine('❌ Failed to start streaming server');
                return false;
            }
            
        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to start server: ${error}`);
            return false;
        }
    }

    /**
     * Get the path to the server script
     */
    private getServerScriptPath(): string {
        // Try to find the run_streaming_server.py script
        const possiblePaths = [
            // Relative to extension
            '../../../run_streaming_server.py',
            // In Palette project directory
            '/home/vphilavong/Projects/Palette/run_streaming_server.py',
            // User's home directory
            `${process.env.HOME}/Projects/Palette/run_streaming_server.py`
        ];

        const fs = require('fs');
        for (const scriptPath of possiblePaths) {
            if (fs.existsSync(scriptPath)) {
                return scriptPath;
            }
        }

        throw new Error('Could not find run_streaming_server.py script');
    }

    /**
     * Analyze project structure
     */
    async analyzeProject(): Promise<AnalyzeResponse['analysis']> {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder open');
        }

        await this.ensureServerRunning();

        try {
            const request = {
                projectPath: this.workspaceRoot
            };

            const response = await fetch(`${this.serverUrl}/api/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Analysis failed');
            }

            return data.analysis;

        } catch (error) {
            this.outputChannel.appendLine(`❌ Analysis failed: ${error}`);
            throw error;
        }
    }

    /**
     * Generate component with streaming
     */
    async generateWithStreaming(
        message: string, 
        conversationHistory: Array<{role: 'user' | 'assistant', content: string}> = [],
        options: StreamingOptions = {}
    ): Promise<void> {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder open');
        }

        await this.ensureServerRunning();

        try {
            // Start generation request
            const generateRequest: GenerateRequest = {
                message,
                conversationId: undefined, // Let server generate one
                projectPath: this.workspaceRoot,
                conversationHistory
            };

            options.onStatus?.('generating', 'Starting generation...');

            const response = await fetch(`${this.serverUrl}/api/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(generateRequest)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const streamingResponse: StreamingResponse = await response.json();
            
            // Connect to SSE stream
            await this.connectToStream(streamingResponse.streamUrl, options);

        } catch (error) {
            this.outputChannel.appendLine(`❌ Generation failed: ${error}`);
            options.onError?.(error instanceof Error ? error.message : String(error));
            throw error;
        }
    }

    /**
     * Connect to Server-Sent Events stream
     */
    private async connectToStream(streamUrl: string, options: StreamingOptions): Promise<void> {
        return new Promise((resolve, reject) => {
            // Use EventSource for SSE connection
            // Note: We'll implement this using fetch with streaming in VS Code environment
            this.streamWithFetch(streamUrl, options)
                .then(() => resolve())
                .catch(reject);
        });
    }

    /**
     * Stream using fetch API (since EventSource may not be available in VS Code extension context)
     */
    private async streamWithFetch(streamUrl: string, options: StreamingOptions): Promise<void> {
        try {
            const response = await fetch(streamUrl);
            
            if (!response.ok) {
                throw new Error(`Stream connection failed: ${response.status} ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No stream reader available');
            }

            const decoder = new TextDecoder();
            let buffer = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) {
                        break;
                    }

                    buffer += decoder.decode(value, { stream: true });
                    
                    // Process complete SSE events
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || ''; // Keep incomplete line in buffer

                    let currentEvent: any = {};
                    
                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            currentEvent.type = line.slice(7);
                        } else if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            try {
                                currentEvent.data = JSON.parse(data);
                            } catch {
                                currentEvent.data = data;
                            }
                        } else if (line === '') {
                            // Empty line marks end of event
                            if (currentEvent.type && currentEvent.data) {
                                this.handleSSEEvent(currentEvent, options);
                            }
                            currentEvent = {};
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }

        } catch (error) {
            this.outputChannel.appendLine(`❌ Stream error: ${error}`);
            options.onError?.(error instanceof Error ? error.message : String(error));
            throw error;
        }
    }

    /**
     * Handle individual SSE events
     */
    private handleSSEEvent(event: { type: string, data: any }, options: StreamingOptions) {
        this.outputChannel.appendLine(`📡 SSE Event: ${event.type}`);

        switch (event.type) {
            case 'status':
                options.onStatus?.(event.data.status, event.data.message);
                break;
                
            case 'chunk':
                options.onChunk?.(event.data.content);
                break;
                
            case 'complete':
                options.onComplete?.(event.data.response, event.data.metadata);
                break;
                
            case 'error':
                options.onError?.(event.data.error);
                break;
                
            case 'keepalive':
                // Just ignore keepalive events
                break;
                
            default:
                this.outputChannel.appendLine(`⚠️  Unknown event type: ${event.type}`);
        }
    }

    /**
     * Get output channel for debugging
     */
    getOutputChannel(): vscode.OutputChannel {
        return this.outputChannel;
    }
}