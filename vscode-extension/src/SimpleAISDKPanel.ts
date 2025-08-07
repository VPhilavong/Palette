/**
 * Simple AI SDK Palette Panel
 * Using simplified AI SDK agent without complex tool system
 */

import * as vscode from 'vscode';
import { SimpleAISDKAgent, createSimpleAISDKAgent, AgentResponse } from './SimpleAISDKAgent';

interface ConversationMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    intent?: string;
    actions?: string[];
}

interface PanelMessage {
    type: 'user-message' | 'clear-conversation' | 'stop-generation';
    content?: string;
    timestamp?: string;
}

interface WebviewMessage {
    type: 'ai-response' | 'ai-stream' | 'status' | 'error' | 'intent-detected';
    content?: string;
    chunk?: string;
    error?: string;
    message?: string;
    intent?: string;
    actions?: string[];
    timestamp: string;
    metadata?: any;
}

export class SimpleAISDKPanel {
    public static currentPanel: SimpleAISDKPanel | undefined;
    
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private readonly _disposables: vscode.Disposable[] = [];
    private _aiAgent: SimpleAISDKAgent | null = null;
    
    // Conversation state
    private _conversationHistory: ConversationMessage[] = [];
    private _isProcessing: boolean = false;

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        
        this._setupWebview();
        this._setupMessageHandling();
        this._setupLifecycle();
        
        // Send initial welcome message
        this._sendWelcomeMessage();
    }

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.ViewColumn.Beside;

        if (SimpleAISDKPanel.currentPanel) {
            SimpleAISDKPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'paletteSimpleAISDK',
            'Palette AI (Simple AI SDK)',
            column,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'media'),
                    vscode.Uri.joinPath(extensionUri, 'out')
                ],
                retainContextWhenHidden: true
            }
        );

        SimpleAISDKPanel.currentPanel = new SimpleAISDKPanel(panel, extensionUri);
    }

    /**
     * Lazy-initialize the AI agent to avoid constructor errors during import
     */
    private async _ensureAgent(): Promise<SimpleAISDKAgent> {
        if (!this._aiAgent) {
            try {
                console.log('Initializing SimpleAISDKAgent...');
                this._aiAgent = createSimpleAISDKAgent({
                    enableStreaming: true,
                    temperature: 0.7
                });
                console.log('SimpleAISDKAgent initialized successfully');
            } catch (error) {
                console.error('Failed to initialize SimpleAISDKAgent:', error);
                this._sendMessage({
                    type: 'error',
                    error: `Failed to initialize AI agent: ${error instanceof Error ? error.message : String(error)}`,
                    timestamp: new Date().toISOString()
                });
                throw error;
            }
        }
        return this._aiAgent;
    }

    private _setupWebview() {
        this._panel.webview.html = this._getWebviewHtml();
    }

    private _setupMessageHandling() {
        this._panel.webview.onDidReceiveMessage(
            async (message: PanelMessage) => {
                try {
                    await this._handleWebviewMessage(message);
                } catch (error) {
                    console.error('Error handling webview message:', error);
                    this._sendMessage({
                        type: 'error',
                        error: error instanceof Error ? error.message : 'Unknown error',
                        timestamp: new Date().toISOString()
                    });
                }
            },
            null,
            this._disposables
        );
    }

    private _setupLifecycle() {
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    private async _handleWebviewMessage(message: PanelMessage) {
        switch (message.type) {
            case 'user-message':
                await this._handleUserMessage(message);
                break;
            case 'clear-conversation':
                await this._handleClearConversation();
                break;
            case 'stop-generation':
                await this._handleStopGeneration();
                break;
            default:
                console.log('Unknown message type:', message);
        }
    }

    private async _handleUserMessage(message: PanelMessage) {
        if (this._isProcessing || !message.content) {
            this._sendMessage({
                type: 'error',
                error: 'Please wait for the current request to complete',
                timestamp: new Date().toISOString()
            });
            return;
        }

        this._isProcessing = true;

        try {
            // Ensure agent is initialized
            const agent = await this._ensureAgent();
            
            // Analyze user intent first
            const intentAnalysis = await agent.analyzeIntent(message.content);
            
            // Send intent detection
            this._sendMessage({
                type: 'intent-detected',
                intent: intentAnalysis.intent,
                actions: intentAnalysis.suggestedActions,
                timestamp: new Date().toISOString()
            });

            // Add user message to history
            const userMessage: ConversationMessage = {
                role: 'user',
                content: message.content,
                timestamp: new Date().toISOString(),
                intent: intentAnalysis.intent,
                actions: intentAnalysis.suggestedActions
            };
            this._conversationHistory.push(userMessage);

            // Send status update
            this._sendMessage({
                type: 'status',
                message: '🤖 AI is processing your request...',
                timestamp: new Date().toISOString()
            });

            // Process with AI SDK agent
            let fullResponse = '';
            const response = await agent.processMessage(
                message.content,
                // Stream callback
                (chunk: string) => {
                    fullResponse += chunk;
                    this._sendMessage({
                        type: 'ai-stream',
                        chunk: chunk,
                        timestamp: new Date().toISOString()
                    });
                }
            );

            // Add response to history
            const assistantMessage: ConversationMessage = {
                role: 'assistant',
                content: response.content || fullResponse,
                timestamp: new Date().toISOString(),
                intent: intentAnalysis.intent
            };
            this._conversationHistory.push(assistantMessage);

            // Send completion message
            this._sendMessage({
                type: 'ai-response',
                content: response.content || fullResponse,
                timestamp: new Date().toISOString(),
                metadata: {
                    model: 'simple-ai-sdk-agent',
                    intent: intentAnalysis.intent,
                    confidence: intentAnalysis.confidence,
                    isComplete: response.isComplete
                }
            });

            // Execute suggested actions if applicable
            await this._executeSuggestedActions(intentAnalysis);

        } catch (error) {
            console.error('Simple AI Agent processing error:', error);
            this._sendMessage({
                type: 'error',
                error: `AI Agent error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                timestamp: new Date().toISOString()
            });
        } finally {
            this._isProcessing = false;
        }
    }

    private async _executeSuggestedActions(intentAnalysis: any) {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        
        try {
            switch (intentAnalysis.intent) {
                case 'preview':
                    if (workspaceRoot) {
                        this._sendMessage({
                            type: 'status',
                            message: '🚀 Starting dev server...',
                            timestamp: new Date().toISOString()
                        });
                        
                        const terminal = vscode.window.createTerminal({
                            name: 'Palette Preview',
                            cwd: workspaceRoot
                        });
                        
                        terminal.sendText('npm run dev');
                        terminal.show();
                    }
                    break;
                    
                case 'install':
                    // Could trigger shadcn/ui component installation
                    this._sendMessage({
                        type: 'status',
                        message: '📦 Component installation guidance provided above',
                        timestamp: new Date().toISOString()
                    });
                    break;
                    
                default:
                    // No automatic actions for other intents
                    break;
            }
        } catch (error) {
            console.error('Error executing suggested actions:', error);
        }
    }

    private async _handleClearConversation() {
        this._conversationHistory = [];
        
        this._sendMessage({
            type: 'status',
            message: '🗑️ Conversation cleared',
            timestamp: new Date().toISOString()
        });

        // Send fresh welcome message
        setTimeout(() => this._sendWelcomeMessage(), 500);
    }

    private async _handleStopGeneration() {
        this._isProcessing = false;
        this._sendMessage({
            type: 'status',
            message: '⏹️ Generation stopped',
            timestamp: new Date().toISOString()
        });
    }

    private _sendWelcomeMessage() {
        const welcomeMessage = `# Welcome to Palette AI (Simple AI SDK)! 🎨

I'm your AI design companion, powered by Vercel's AI SDK for UI/UX prototyping. I can help you create complete, beautiful web pages and features - just like Vercel v0, but right here in VS Code!

## What I can do:
- **Generate complete pages** (landing pages, dashboards, e-commerce sites, blogs)
- **Analyze your project** and understand your design system
- **Guide shadcn/ui setup** and component installation
- **Start live previews** with step-by-step instructions
- **Provide design guidance** through natural conversation
- **Detect your intent** and provide relevant actions

## Powered by Simple AI SDK:
✅ **Clean TypeScript** integration without complex dependencies
✅ **Streaming responses** with real-time feedback
✅ **Intent detection** to understand what you want to do
✅ **Actionable guidance** with specific next steps

## Try asking me:
- "Create a modern SaaS landing page with hero, features, and pricing"
- "Build a dashboard with sidebar navigation and data cards"
- "How do I start the dev server to preview my designs?"
- "What shadcn/ui components should I install for an e-commerce site?"
- "Analyze my project structure and suggest improvements"

I'm ready to help you prototype amazing designs! What would you like to create?`;

        this._sendMessage({
            type: 'ai-response',
            content: welcomeMessage,
            timestamp: new Date().toISOString(),
            metadata: {
                isWelcome: true,
                model: 'simple-ai-sdk-agent'
            }
        });
    }

    private _sendMessage(message: WebviewMessage) {
        this._panel.webview.postMessage(message);
    }

    private _getWebviewHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI (Simple AI SDK)</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 8px;
            background: var(--vscode-panel-background);
        }
        
        .header h1 {
            color: var(--vscode-textLink-foreground);
            margin: 0 0 10px 0;
            font-size: 1.5em;
        }
        
        .header .subtitle {
            color: var(--vscode-descriptionForeground);
            font-style: italic;
            margin: 0;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-width: 100%;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            max-width: 85%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: var(--vscode-inputValidation-infoBorder);
            color: var(--vscode-input-foreground);
            align-self: flex-end;
            margin-left: auto;
        }
        
        .ai-message {
            background: var(--vscode-panel-background);
            border: 1px solid var(--vscode-panel-border);
            align-self: flex-start;
        }
        
        .ai-message.streaming {
            border-left: 3px solid var(--vscode-progressBar-background);
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .intent-detected {
            background: var(--vscode-inputValidation-infoBackground);
            color: var(--vscode-inputValidation-infoForeground);
            padding: 10px 15px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 0.9em;
            border-left: 3px solid var(--vscode-textLink-foreground);
        }
        
        .intent-detected .intent-name {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
            text-transform: capitalize;
        }
        
        .intent-actions {
            margin-top: 8px;
            list-style: none;
            padding-left: 0;
        }
        
        .intent-actions li {
            padding: 2px 0;
            color: var(--vscode-descriptionForeground);
        }
        
        .intent-actions li::before {
            content: "→ ";
            color: var(--vscode-textLink-foreground);
        }
        
        .status-message {
            background: var(--vscode-inputValidation-warningBackground);
            color: var(--vscode-inputValidation-warningForeground);
            padding: 10px 15px;
            border-radius: 6px;
            font-style: italic;
            text-align: center;
            margin: 10px 0;
        }
        
        .error-message {
            background: var(--vscode-inputValidation-errorBackground);
            color: var(--vscode-inputValidation-errorForeground);
            padding: 10px 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--vscode-editor-background);
            border-top: 1px solid var(--vscode-panel-border);
            padding: 15px 20px;
            display: flex;
            gap: 10px;
        }
        
        .input-field {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid var(--vscode-input-border);
            border-radius: 6px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            font-family: inherit;
            font-size: inherit;
            resize: vertical;
            min-height: 20px;
        }
        
        .send-button, .clear-button {
            padding: 10px 20px;
            border: 1px solid var(--vscode-button-border);
            border-radius: 6px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            cursor: pointer;
            font-family: inherit;
            font-size: inherit;
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .messages-container {
            margin-bottom: 100px;
            padding-bottom: 20px;
        }
        
        /* Markdown-like styling */
        .ai-message h1, .ai-message h2, .ai-message h3 {
            color: var(--vscode-textLink-foreground);
            margin: 15px 0 10px 0;
        }
        
        .ai-message ul, .ai-message ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .ai-message code {
            background: var(--vscode-textBlockQuote-background);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: var(--vscode-editor-font-family);
        }
        
        .ai-message strong {
            font-weight: bold;
            color: var(--vscode-textLink-foreground);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Palette AI (Simple AI SDK)</h1>
        <p class="subtitle">Clean AI SDK implementation • Intent detection • Step-by-step guidance</p>
    </div>
    
    <div class="messages-container">
        <div id="chat-messages" class="chat-container">
            <!-- Messages will be inserted here -->
        </div>
    </div>
    
    <div class="input-container">
        <textarea 
            id="message-input" 
            class="input-field" 
            placeholder="Describe what you want to create or ask for help..."
            rows="1"
        ></textarea>
        <button id="send-button" class="send-button">Send</button>
        <button id="clear-button" class="clear-button">Clear</button>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        const messagesContainer = document.getElementById('chat-messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const clearButton = document.getElementById('clear-button');
        
        let currentStreamingMessage = null;
        let isProcessing = false;
        
        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Send message on Enter (but allow Shift+Enter for new lines)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
        clearButton.addEventListener('click', clearConversation);
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || isProcessing) return;
            
            // Add user message to UI
            addUserMessage(message);
            
            // Send to extension
            vscode.postMessage({
                type: 'user-message',
                content: message,
                timestamp: new Date().toISOString()
            });
            
            // Clear input and update state
            messageInput.value = '';
            messageInput.style.height = 'auto';
            isProcessing = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Processing...';
        }
        
        function clearConversation() {
            if (confirm('Clear entire conversation?')) {
                messagesContainer.innerHTML = '';
                vscode.postMessage({ type: 'clear-conversation' });
            }
        }
        
        function addUserMessage(content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user-message';
            messageDiv.textContent = content;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addAIMessage(content, isStreaming = false) {
            if (currentStreamingMessage && !isStreaming) {
                // Complete the streaming message
                currentStreamingMessage.classList.remove('streaming');
                currentStreamingMessage = null;
            } else if (!currentStreamingMessage && isStreaming) {
                // Start a new streaming message
                currentStreamingMessage = document.createElement('div');
                currentStreamingMessage.className = 'message ai-message streaming';
                messagesContainer.appendChild(currentStreamingMessage);
            }
            
            const targetMessage = currentStreamingMessage || document.createElement('div');
            
            if (!currentStreamingMessage) {
                targetMessage.className = 'message ai-message';
                messagesContainer.appendChild(targetMessage);
            }
            
            // Simple markdown rendering
            const htmlContent = content
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/\`(.*?)\`/g, '<code>$1</code>')
                .replace(/\\n/g, '<br>');
            
            targetMessage.innerHTML = htmlContent;
            scrollToBottom();
        }
        
        function addIntentDetected(intent, actions) {
            const intentDiv = document.createElement('div');
            intentDiv.className = 'intent-detected';
            
            let actionsHtml = '';
            if (actions && actions.length > 0) {
                actionsHtml = '<ul class="intent-actions">' +
                    actions.map(action => '<li>' + action + '</li>').join('') +
                    '</ul>';
            }
            
            intentDiv.innerHTML = 
                '<div class="intent-name">🎯 Detected: ' + intent + '</div>' +
                actionsHtml;
            
            messagesContainer.appendChild(intentDiv);
            scrollToBottom();
        }
        
        function addStatusMessage(message) {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'status-message';
            statusDiv.textContent = message;
            messagesContainer.appendChild(statusDiv);
            scrollToBottom();
            
            // Remove status messages after 3 seconds
            setTimeout(() => {
                if (statusDiv.parentNode) {
                    statusDiv.parentNode.removeChild(statusDiv);
                }
            }, 3000);
        }
        
        function addErrorMessage(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            messagesContainer.appendChild(errorDiv);
            scrollToBottom();
        }
        
        function scrollToBottom() {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function resetProcessingState() {
            isProcessing = false;
            sendButton.disabled = false;
            sendButton.textContent = 'Send';
            if (currentStreamingMessage) {
                currentStreamingMessage.classList.remove('streaming');
                currentStreamingMessage = null;
            }
        }
        
        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'ai-response':
                    addAIMessage(message.content);
                    resetProcessingState();
                    break;
                    
                case 'ai-stream':
                    addAIMessage(message.chunk, true);
                    break;
                    
                case 'intent-detected':
                    addIntentDetected(message.intent, message.actions);
                    break;
                    
                case 'status':
                    addStatusMessage(message.message);
                    break;
                    
                case 'error':
                    addErrorMessage('Error: ' + message.error);
                    resetProcessingState();
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
            }
        });
        
        // Initialize
        messageInput.focus();
    </script>
</body>
</html>`;
    }

    public dispose() {
        SimpleAISDKPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}