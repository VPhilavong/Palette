/**
 * UnifiedPalettePanel - The new unified interface for Palette
 * Uses PaletteCommManager to orchestrate between AI SDK and Python backend
 */

import * as vscode from 'vscode';
import { PaletteCommManager, PaletteResponse, StreamingOptions, PaletteMessage } from './services/PaletteCommManager';
import { GenerationProvider, RoutingDecision } from './intelligence/RequestRouter';
import { RequestComplexity } from './intelligence/ComplexityAnalyzer';

interface WebviewMessage {
    type: 'user-message' | 'clear-conversation' | 'export-conversation' | 'get-status' | 'update-preferences';
    content?: string;
    preferences?: any;
    timestamp?: string;
}

interface PanelMessage {
    type: 'ai-response' | 'ai-stream' | 'status-update' | 'routing-info' | 'system-status' | 'error' | 'conversation-history';
    content?: string;
    chunk?: string;
    status?: string;
    phase?: string;
    routing?: RoutingDecision;
    response?: PaletteResponse;
    systemStatus?: any;
    history?: PaletteMessage[];
    error?: string;
    timestamp: string;
}

export class UnifiedPalettePanel {
    public static currentPanel: UnifiedPalettePanel | undefined;
    
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private readonly _disposables: vscode.Disposable[] = [];
    private readonly _commManager: PaletteCommManager;
    
    // UI state
    private _isProcessing: boolean = false;

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._commManager = PaletteCommManager.getInstance();
        
        this._setupWebview();
        this._setupMessageHandling();
        this._setupLifecycle();
        
        // Send initial data
        this._sendSystemStatus();
        this._sendConversationHistory();
    }

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.ViewColumn.Beside;

        if (UnifiedPalettePanel.currentPanel) {
            UnifiedPalettePanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'paletteUnified',
            'Palette AI (Unified)',
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

        UnifiedPalettePanel.currentPanel = new UnifiedPalettePanel(panel, extensionUri);
    }

    private _setupWebview() {
        this._panel.webview.html = this._getWebviewHtml();
    }

    private _setupMessageHandling() {
        this._panel.webview.onDidReceiveMessage(
            async (message: WebviewMessage) => {
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
        this._panel.onDidDispose(
            () => this.dispose(),
            null,
            this._disposables
        );
    }

    private async _handleWebviewMessage(message: WebviewMessage) {
        switch (message.type) {
            case 'user-message':
                if (!message.content?.trim() || this._isProcessing) {
                    return;
                }
                await this._handleUserMessage(message.content);
                break;
                
            case 'clear-conversation':
                await this._handleClearConversation();
                break;
                
            case 'export-conversation':
                await this._handleExportConversation();
                break;
                
            case 'get-status':
                await this._sendSystemStatus();
                break;
                
            case 'update-preferences':
                if (message.preferences) {
                    this._commManager.updatePreferences(message.preferences);
                    await this._sendSystemStatus();
                }
                break;
        }
    }

    private async _handleUserMessage(content: string) {
        this._isProcessing = true;
        
        try {
            const streamingOptions: StreamingOptions = {
                onMessage: (chunk: string, metadata?: any) => {
                    this._sendMessage({
                        type: 'ai-stream',
                        chunk: chunk,
                        timestamp: new Date().toISOString()
                    });
                },
                
                onStatusUpdate: (status: string, phase?: string) => {
                    this._sendMessage({
                        type: 'status-update',
                        status: status,
                        phase: phase,
                        timestamp: new Date().toISOString()
                    });
                },
                
                onRouting: (decision: RoutingDecision) => {
                    this._sendMessage({
                        type: 'routing-info',
                        routing: decision,
                        timestamp: new Date().toISOString()
                    });
                },
                
                onComplete: (response: PaletteResponse) => {
                    this._sendMessage({
                        type: 'ai-response',
                        response: response,
                        timestamp: new Date().toISOString()
                    });
                },
                
                onError: (error: string) => {
                    this._sendMessage({
                        type: 'error',
                        error: error,
                        timestamp: new Date().toISOString()
                    });
                }
            };
            
            // Process the message through the unified system
            await this._commManager.processMessage(content, streamingOptions);
            
        } catch (error) {
            this._sendMessage({
                type: 'error',
                error: `Processing failed: ${error instanceof Error ? error.message : String(error)}`,
                timestamp: new Date().toISOString()
            });
        } finally {
            this._isProcessing = false;
        }
    }

    private async _handleClearConversation() {
        await this._commManager.clearConversation();
        this._sendConversationHistory();
    }

    private async _handleExportConversation() {
        const conversation = this._commManager.exportConversation();
        if (conversation) {
            const jsonString = JSON.stringify(conversation, null, 2);
            const doc = await vscode.workspace.openTextDocument({
                content: jsonString,
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);
        }
    }

    private _sendMessage(message: PanelMessage) {
        this._panel.webview.postMessage(message);
    }

    private async _sendSystemStatus() {
        const status = await this._commManager.getSystemStatus();
        this._sendMessage({
            type: 'system-status',
            systemStatus: status,
            timestamp: new Date().toISOString()
        });
    }

    private _sendConversationHistory() {
        const history = this._commManager.getConversationHistory();
        this._sendMessage({
            type: 'conversation-history',
            history: history,
            timestamp: new Date().toISOString()
        });
    }

    private _getWebviewHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI - Unified</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            height: 100vh;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 16px;
            background: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-sideBar-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .title {
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--vscode-charts-green);
        }

        .status-indicator.warning { background: var(--vscode-charts-yellow); }
        .status-indicator.error { background: var(--vscode-charts-red); }

        .system-info {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }

        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 8px;
            line-height: 1.5;
        }

        .message.user {
            align-self: flex-end;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .message.assistant {
            align-self: flex-start;
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
        }

        .message.system {
            align-self: center;
            background: var(--vscode-notifications-background);
            border: 1px solid var(--vscode-notifications-border);
            font-size: 12px;
            max-width: 70%;
            text-align: center;
        }

        .message-metadata {
            font-size: 10px;
            color: var(--vscode-descriptionForeground);
            margin-top: 4px;
        }

        .routing-info {
            background: var(--vscode-textBlockQuote-background);
            border-left: 3px solid var(--vscode-textBlockQuote-border);
            padding: 8px;
            margin: 8px 0;
            font-size: 12px;
        }

        .provider-badge {
            display: inline-block;
            padding: 2px 6px;
            background: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            border-radius: 3px;
            font-size: 10px;
            font-weight: 500;
        }

        .input-container {
            padding: 16px;
            background: var(--vscode-sideBar-background);
            border-top: 1px solid var(--vscode-sideBar-border);
        }

        .input-wrapper {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        .message-input {
            flex: 1;
            min-height: 40px;
            max-height: 120px;
            padding: 8px 12px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            resize: vertical;
            font-family: inherit;
            font-size: 14px;
            line-height: 1.4;
        }

        .message-input:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }

        .send-button, .action-button {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
            white-space: nowrap;
        }

        .send-button:hover, .action-button:hover {
            background: var(--vscode-button-hoverBackground);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }

        .processing-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--vscode-charts-blue);
            font-size: 12px;
            margin-bottom: 8px;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .complexity-indicator {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 500;
        }

        .complexity-simple { background: var(--vscode-charts-green); color: white; }
        .complexity-hybrid { background: var(--vscode-charts-yellow); color: black; }
        .complexity-complex { background: var(--vscode-charts-orange); color: white; }
        .complexity-analysis { background: var(--vscode-charts-purple); color: white; }

        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">
            <span>🎨 Palette AI</span>
            <span class="status-indicator" id="statusIndicator"></span>
        </div>
        <div class="system-info" id="systemInfo">Initializing...</div>
    </div>

    <div class="chat-container">
        <div class="messages" id="messages"></div>
        
        <div class="input-container">
            <div class="processing-indicator hidden" id="processingIndicator">
                <div class="spinner"></div>
                <span id="processingStatus">Processing...</span>
            </div>
            
            <div class="input-wrapper">
                <textarea 
                    class="message-input" 
                    id="messageInput" 
                    placeholder="Describe what you want to create..."
                    rows="1"
                ></textarea>
                <button class="send-button" id="sendButton">Send</button>
            </div>
            
            <div class="actions">
                <button class="action-button" id="clearButton">Clear</button>
                <button class="action-button" id="exportButton">Export</button>
                <button class="action-button" id="statusButton">Status</button>
            </div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        // DOM elements
        const messagesEl = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');
        const exportButton = document.getElementById('exportButton');
        const statusButton = document.getElementById('statusButton');
        const processingIndicator = document.getElementById('processingIndicator');
        const processingStatus = document.getElementById('processingStatus');
        const statusIndicator = document.getElementById('statusIndicator');
        const systemInfo = document.getElementById('systemInfo');

        let isProcessing = false;
        let currentStreamMessage = null;

        // Auto-resize textarea
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Send message on Enter (Shift+Enter for new line)
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendButton.addEventListener('click', sendMessage);
        clearButton.addEventListener('click', () => {
            vscode.postMessage({ type: 'clear-conversation' });
        });
        exportButton.addEventListener('click', () => {
            vscode.postMessage({ type: 'export-conversation' });
        });
        statusButton.addEventListener('click', () => {
            vscode.postMessage({ type: 'get-status' });
        });

        function sendMessage() {
            const content = messageInput.value.trim();
            if (!content || isProcessing) return;

            vscode.postMessage({
                type: 'user-message',
                content: content,
                timestamp: new Date().toISOString()
            });

            addMessage('user', content);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            setProcessing(true);
        }

        function setProcessing(processing) {
            isProcessing = processing;
            sendButton.disabled = processing;
            
            if (processing) {
                processingIndicator.classList.remove('hidden');
            } else {
                processingIndicator.classList.add('hidden');
                processingStatus.textContent = 'Processing...';
            }
        }

        function addMessage(role, content, metadata = {}) {
            const messageEl = document.createElement('div');
            messageEl.className = 'message ' + role;
            
            const contentEl = document.createElement('div');
            contentEl.textContent = content;
            messageEl.appendChild(contentEl);

            if (metadata.provider || metadata.complexity) {
                const metadataEl = document.createElement('div');
                metadataEl.className = 'message-metadata';
                
                let metadataText = '';
                if (metadata.provider) {
                    metadataText += 'Provider: ' + metadata.provider;
                }
                if (metadata.complexity) {
                    metadataText += (metadataText ? ' • ' : '') + 'Complexity: ' + metadata.complexity;
                }
                if (metadata.duration) {
                    metadataText += (metadataText ? ' • ' : '') + 'Duration: ' + metadata.duration + 'ms';
                }
                
                metadataEl.textContent = metadataText;
                messageEl.appendChild(metadataEl);
            }

            messagesEl.appendChild(messageEl);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            
            return messageEl;
        }

        function addSystemMessage(content, type = 'info') {
            const messageEl = document.createElement('div');
            messageEl.className = 'message system';
            messageEl.textContent = content;
            messagesEl.appendChild(messageEl);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function addRoutingInfo(routing) {
            const routingEl = document.createElement('div');
            routingEl.className = 'routing-info';
            routingEl.innerHTML = 
                '<strong>🎯 Routing Decision:</strong><br>' +
                'Primary: <span class="provider-badge">' + routing.primaryProvider + '</span><br>' +
                'Estimated: ' + routing.estimatedDuration + '<br>' +
                'Reasoning: ' + routing.reasoning.join(', ');
            
            messagesEl.appendChild(routingEl);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'ai-stream':
                    if (!currentStreamMessage) {
                        currentStreamMessage = addMessage('assistant', '');
                    }
                    const contentEl = currentStreamMessage.querySelector('div');
                    contentEl.textContent += message.chunk;
                    messagesEl.scrollTop = messagesEl.scrollHeight;
                    break;

                case 'ai-response':
                    if (currentStreamMessage) {
                        // Update metadata
                        const response = message.response;
                        if (response.performance) {
                            let metadataEl = currentStreamMessage.querySelector('.message-metadata');
                            if (!metadataEl) {
                                metadataEl = document.createElement('div');
                                metadataEl.className = 'message-metadata';
                                currentStreamMessage.appendChild(metadataEl);
                            }
                            metadataEl.textContent = 
                                'Provider: ' + response.provider + ' • ' +
                                'Complexity: ' + response.performance.classification + ' • ' +
                                'Duration: ' + response.performance.duration + 'ms';
                        }
                    } else {
                        addMessage('assistant', message.response.content, {
                            provider: message.response.provider,
                            complexity: message.response.performance.classification,
                            duration: message.response.performance.duration
                        });
                    }
                    currentStreamMessage = null;
                    setProcessing(false);
                    break;

                case 'status-update':
                    processingStatus.textContent = message.status + (message.phase ? ' (' + message.phase + ')' : '');
                    break;

                case 'routing-info':
                    addRoutingInfo(message.routing);
                    break;

                case 'system-status':
                    updateSystemStatus(message.systemStatus);
                    break;

                case 'conversation-history':
                    loadConversationHistory(message.history);
                    break;

                case 'error':
                    addSystemMessage('Error: ' + message.error, 'error');
                    setProcessing(false);
                    currentStreamMessage = null;
                    break;
            }
        });

        function updateSystemStatus(status) {
            if (status.pythonBackend.isRunning) {
                statusIndicator.className = 'status-indicator';
                systemInfo.textContent = 
                    'Python Backend: Port ' + status.pythonBackend.port + ' • ' +
                    'Messages: ' + status.session.messageCount;
            } else {
                statusIndicator.className = 'status-indicator warning';
                systemInfo.textContent = 'Python Backend: Starting...';
            }
        }

        function loadConversationHistory(history) {
            messagesEl.innerHTML = '';
            currentStreamMessage = null;
            
            history.forEach(msg => {
                addMessage(msg.role, msg.content, msg.metadata || {});
            });
        }

        // Request initial status
        vscode.postMessage({ type: 'get-status' });
    </script>
</body>
</html>`;
    }

    public dispose() {
        UnifiedPalettePanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}