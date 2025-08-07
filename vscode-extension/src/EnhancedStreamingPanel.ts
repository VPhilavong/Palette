/**
 * Enhanced Palette Panel with VS Code Messenger and SSE streaming
 */

import * as vscode from 'vscode';
import { 
    PaletteMessage, 
    ExtensionToWebviewMessage, 
    WebviewToExtensionMessage,
    UserMessage,
    AIResponseMessage,
    AIStreamMessage,
    StatusMessage,
    ErrorMessage
} from './types/messages';
import { StreamingPaletteService } from './services/StreamingPaletteService';
import { getStreamingChatWebviewHtml } from './ui/streamingChat';

export class EnhancedStreamingPanel {
    public static currentPanel: EnhancedStreamingPanel | undefined;
    
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private readonly _disposables: vscode.Disposable[] = [];
    private readonly _paletteService: StreamingPaletteService;
    
    // Conversation state
    private _conversationHistory: Array<{role: 'user' | 'assistant', content: string}> = [];
    private _currentConversationId: string | undefined;

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._paletteService = new StreamingPaletteService();
        
        this._setupWebview();
        this._setupMessageHandling();
        this._setupLifecycle();
        
        // Send initial welcome
        this._sendWelcomeMessage();
    }

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.ViewColumn.Beside;

        if (EnhancedStreamingPanel.currentPanel) {
            EnhancedStreamingPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'paletteStreaming',
            'Palette Chat',
            column,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [vscode.Uri.joinPath(extensionUri, 'media')]
            }
        );

        EnhancedStreamingPanel.currentPanel = new EnhancedStreamingPanel(panel, extensionUri);
    }

    private _setupWebview() {
        this._panel.webview.html = getStreamingChatWebviewHtml(this._panel, this._extensionUri);
    }

    private _setupMessageHandling() {
        // Handle messages from webview using basic postMessage
        this._panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.type) {
                    case 'user-message':
                        await this._handleUserMessage(message as UserMessage);
                        break;
                    case 'analyze-request':
                        await this._handleAnalyzeRequest();
                        break;
                    case 'image-upload':
                        this._sendToWebview({
                            type: 'status',
                            status: 'ready',
                            message: `Image "${message.name}" received - image generation coming soon!`
                        });
                        break;
                }
            },
            undefined,
            this._disposables
        );
    }

    private _setupLifecycle() {
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    private async _sendWelcomeMessage() {
        // Check server health first
        this._sendToWebview({
            type: 'status',
            status: 'connecting',
            message: 'Checking Palette server connection...'
        });

        try {
            const isHealthy = await this._paletteService.checkHealth();
            
            if (!isHealthy) {
                // Try to start the server
                const serverStarted = await this._paletteService.ensureServerRunning();
                
                if (!serverStarted) {
                    this._sendToWebview({
                        type: 'error',
                        error: 'Failed to start Palette server',
                        details: 'Check the Output panel (View → Output → Palette Streaming) for details',
                        recoverable: true,
                        actions: [
                            { label: 'Retry', action: 'retry-connection' },
                            { label: 'View Output', action: 'show-output' }
                        ]
                    });
                    return;
                }
            }

            // Send welcome messages
            this._sendToWebview({
                type: 'status',
                status: 'ready',
                message: 'Connected to Palette server'
            });

            await this._sendMessage({
                type: 'ai-response',
                content: '👋 Hi! I\'m your AI UI developer assistant powered by Palette.',
                isComplete: true,
                conversationId: 'welcome'
            });

            await this._sendMessage({
                type: 'ai-response',
                content: 'I can help you create, modify, and improve React components through natural conversation.',
                isComplete: true,
                conversationId: 'welcome'
            });

            await this._sendMessage({
                type: 'ai-response',
                content: 'Just describe what you want: "Create a pricing card with three tiers" or "Make this button more accessible"',
                isComplete: true,
                conversationId: 'welcome'
            });

        } catch (error) {
            this._sendToWebview({
                type: 'error',
                error: 'Failed to initialize Palette',
                details: error instanceof Error ? error.message : String(error),
                recoverable: true
            });
        }
    }

    private async _handleUserMessage(data: UserMessage) {
        try {
            // Add user message to history
            this._conversationHistory.push({
                role: 'user',
                content: data.text
            });

            // Generate conversation ID if none exists
            if (!this._currentConversationId) {
                this._currentConversationId = 'conv_' + Date.now();
            }

            // Send acknowledgment
            this._sendToWebview({
                type: 'status',
                status: 'generating',
                message: 'Processing your request...'
            });

            let streamingContent = '';

            // Start streaming generation
            await this._paletteService.generateWithStreaming(
                data.text,
                this._conversationHistory,
                {
                    onStatus: (status, message) => {
                        this._sendToWebview({
                            type: 'status',
                            status: status as any,
                            message
                        });
                    },

                    onChunk: (chunk) => {
                        streamingContent += chunk;
                        this._sendToWebview({
                            type: 'ai-stream',
                            chunk: chunk,
                            conversationId: this._currentConversationId!,
                            isFirst: streamingContent === chunk
                        });
                    },

                    onComplete: (response, metadata) => {
                        // Add assistant message to history
                        this._conversationHistory.push({
                            role: 'assistant',
                            content: response
                        });

                        // Send completion
                        this._sendToWebview({
                            type: 'ai-response',
                            content: response,
                            isComplete: true,
                            conversationId: this._currentConversationId!,
                            metadata
                        });

                        // Reset status
                        this._sendToWebview({
                            type: 'status',
                            status: 'ready'
                        });
                    },

                    onError: (error) => {
                        this._sendToWebview({
                            type: 'error',
                            error: 'Generation failed',
                            details: error,
                            recoverable: true
                        });

                        this._sendToWebview({
                            type: 'status',
                            status: 'ready'
                        });
                    }
                }
            );

        } catch (error) {
            this._sendToWebview({
                type: 'error',
                error: 'Failed to process message',
                details: error instanceof Error ? error.message : String(error),
                recoverable: true
            });
        }
    }

    private async _handleAnalyzeRequest() {
        try {
            this._sendToWebview({
                type: 'status',
                status: 'generating',
                message: 'Analyzing project structure...'
            });

            const analysis = await this._paletteService.analyzeProject();

            // Format analysis response
            let response = '🔍 **Project Analysis**\n\n';
            response += `• **Framework**: ${analysis.framework}\n`;
            response += `• **Styling**: ${analysis.styling}\n`;
            response += `• **TypeScript**: ${analysis.hasTypeScript ? '✅' : '❌'}\n`;
            response += `• **Tailwind CSS**: ${analysis.hasTailwind ? '✅' : '❌'}\n`;
            
            if (analysis.componentsPath) {
                response += `• **Components**: \`${analysis.componentsPath}\`\n`;
            }
            
            response += '\nYour project is ready for component generation! 🚀';

            this._sendToWebview({
                type: 'ai-response',
                content: response,
                isComplete: true,
                conversationId: this._currentConversationId || 'analysis'
            });

            this._sendToWebview({
                type: 'status',
                status: 'ready'
            });

        } catch (error) {
            this._sendToWebview({
                type: 'error',
                error: 'Project analysis failed',
                details: error instanceof Error ? error.message : String(error),
                recoverable: true
            });
        }
    }

    private _sendToWebview(message: ExtensionToWebviewMessage) {
        this._panel.webview.postMessage({ type: 'message', data: message });
    }

    private async _sendMessage(message: ExtensionToWebviewMessage) {
        // Add small delay to make messages appear naturally
        await new Promise(resolve => setTimeout(resolve, 100));
        this._sendToWebview(message);
    }

    public dispose() {
        EnhancedStreamingPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}