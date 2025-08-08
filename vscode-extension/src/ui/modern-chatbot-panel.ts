/**
 * Modern Chatbot Panel using VSCode Elements
 * Provides native VSCode UI components with no JavaScript errors
 */

import * as vscode from 'vscode';
import { AIIntegrationService } from '../ai-integration';
import { ConversationMessage } from '../conversation-manager';
import { MCPManager } from '../mcp/mcp-manager';
import { ToolExecutor } from '../tools/tool-executor';
import { ToolRegistry } from '../tools/tool-registry';
import { ProgressManager } from './progress-manager';

export class ModernChatbotPanel implements vscode.WebviewViewProvider {
    public static readonly viewType = 'palette.modernChatbot';
    
    private _view?: vscode.WebviewView;
    private _messages: ConversationMessage[] = [];
    private _isLoading = false;
    private _toolRegistry?: ToolRegistry;
    private _toolExecutor?: ToolExecutor;
    private _mcpManager?: MCPManager;
    private _progressManager: ProgressManager;
    private _availableTools: Array<{name: string, description: string, category: string}> = [];
    private _mcpServerStatus: Map<string, string> = new Map();

    constructor(private readonly _extensionUri: vscode.Uri) {
        this._progressManager = ProgressManager.getInstance();
        
        // Check if tool system is available
        const toolSystemAvailable = this._toolRegistry && this._toolExecutor;
        if (!toolSystemAvailable) {
            console.log('🎨 ModernChatbotPanel: Tool system not available');
        }
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Set up message handling
        webviewView.webview.onDidReceiveMessage(
            (message) => this._handleWebviewMessage(message),
            undefined,
            []
        );

        // Load existing messages
        this._updateWebview();
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'node_modules', '@vscode-elements/elements', 'dist', 'bundled.js'));
        const playgroundUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'node_modules', '@vscode-elements/webview-playground', 'dist', 'index.js'));
        const nonce = this._getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI Assistant</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}' ${webview.cspSource}; style-src 'unsafe-inline' ${webview.cspSource};">
    <script type="module" nonce="${nonce}" src="${playgroundUri}"></script>
    <script type="module" nonce="${nonce}" src="${scriptUri}"></script>
    <style>
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-sideBar-background);
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .toolbar {
            padding: 8px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
        }

        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message-bubble {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            word-wrap: break-word;
        }

        .message-bubble.user {
            align-self: flex-end;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .message-bubble.assistant {
            align-self: flex-start;
            background-color: var(--vscode-textCodeBlock-background);
            border: 1px solid var(--vscode-panel-border);
        }

        .message-content {
            line-height: 1.6;
        }

        .message-content p {
            margin: 0 0 12px 0;
        }

        .message-content p:last-child {
            margin-bottom: 0;
        }

        .message-content strong {
            color: var(--vscode-foreground);
            font-weight: 600;
        }

        .message-content em {
            color: var(--vscode-descriptionForeground);
            font-style: italic;
        }

        .message-content ul, .message-content ol {
            margin: 8px 0;
            padding-left: 20px;
        }

        .message-content li {
            margin: 4px 0;
        }

        .message-content code {
            background-color: var(--vscode-textCodeBlock-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 3px;
            padding: 2px 4px;
            font-family: var(--vscode-editor-font-family);
            font-size: 0.9em;
        }

        .input-area {
            padding: 12px;
            border-top: 1px solid var(--vscode-panel-border);
            flex-shrink: 0;
        }

        .input-container {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        .welcome-message {
            text-align: center;
            padding: 32px 16px;
            color: var(--vscode-descriptionForeground);
        }

        .welcome-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--vscode-foreground);
        }

        .feature-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin-top: 16px;
        }

        .feature-card {
            padding: 12px;
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        .feature-card:hover {
            background-color: var(--vscode-list-hoverBackground);
        }

        .feature-title {
            font-weight: 600;
            font-size: 13px;
            margin-bottom: 4px;
        }

        .feature-desc {
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }

        .code-block {
            background-color: var(--vscode-textCodeBlock-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            margin: 8px 0;
            overflow: hidden;
        }

        .code-header {
            padding: 8px 12px;
            background-color: var(--vscode-panel-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }

        .code-content {
            padding: 12px;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            white-space: pre-wrap;
            overflow-x: auto;
        }

        vscode-textarea {
            flex: 1;
        }

        .status-indicators {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-left: auto;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }

        .message-text {
            margin: 4px 0;
            line-height: 1.5;
        }

        .message-text p {
            margin: 8px 0;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <!-- Toolbar -->
        <div class="toolbar">
            <vscode-button id="toolsBtn" appearance="secondary" size="small">Tools</vscode-button>
            <vscode-button id="mcpBtn" appearance="secondary" size="small">MCP</vscode-button>
            <vscode-button id="clearBtn" appearance="secondary" size="small">Clear</vscode-button>
            
            <div class="status-indicators">
                <div class="status-indicator">
                    <span>🛠️</span>
                    <span id="toolCount">0</span>
                </div>
                <div class="status-indicator">
                    <span>🔌</span>
                    <span id="mcpCount">0</span>
                </div>
            </div>
        </div>

        <!-- Messages Area -->
        <div class="messages-area" id="messagesArea">
            <div class="welcome-message" id="welcomeMessage">
                <div class="welcome-title">Palette AI Assistant</div>
                <div>I can help you design components, build pages, and organize files in your project.</div>
                
                <div class="feature-grid">
                    <div class="feature-card" data-action="generate">
                        <div class="feature-title">🎨 Generate Components</div>
                        <div class="feature-desc">Create React components with TypeScript</div>
                    </div>
                    <div class="feature-card" data-action="analyze">
                        <div class="feature-title">🔍 Analyze Project</div>
                        <div class="feature-desc">Get insights about your codebase</div>
                    </div>
                    <div class="feature-card" data-action="tools">
                        <div class="feature-title">🛠️ Show Tools</div>
                        <div class="feature-desc">View available development tools</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
            <div class="input-container">
                <vscode-textarea 
                    id="messageInput" 
                    placeholder="Ask me anything about your project..."
                    rows="1"
                    resize="vertical"
                    maxlength="4000">
                </vscode-textarea>
                <vscode-button id="sendBtn">Send</vscode-button>
            </div>
        </div>
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        let messages = [];
        let isLoading = false;

        // DOM elements
        const messagesArea = document.getElementById('messagesArea');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const welcomeMessage = document.getElementById('welcomeMessage');
        const toolsBtn = document.getElementById('toolsBtn');
        const mcpBtn = document.getElementById('mcpBtn');
        const clearBtn = document.getElementById('clearBtn');

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        clearBtn.addEventListener('click', clearMessages);
        toolsBtn.addEventListener('click', showTools);
        mcpBtn.addEventListener('click', showMCPStatus);

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Feature card clicks
        document.addEventListener('click', (e) => {
            const featureCard = e.target.closest('.feature-card');
            if (featureCard) {
                const action = featureCard.dataset.action;
                if (action === 'tools') {
                    showTools();
                } else if (action === 'generate') {
                    messageInput.value = 'Help me create a new React component';
                    messageInput.focus();
                } else if (action === 'analyze') {
                    messageInput.value = 'Analyze my project structure';
                    messageInput.focus();
                }
            }
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'updateMessages':
                    messages = message.messages || [];
                    isLoading = message.isLoading || false;
                    renderMessages();
                    break;
                case 'updateToolStatus':
                    updateToolStatus(message.availableTools, message.mcpServerStatus);
                    break;
                case 'clearMessages':
                    clearMessagesUI();
                    break;
            }
        });

        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text || isLoading) return;

            vscode.postMessage({
                type: 'sendMessage',
                message: text
            });

            messageInput.value = '';
        }

        function clearMessages() {
            vscode.postMessage({ type: 'clearMessages' });
        }

        function showTools() {
            vscode.postMessage({ type: 'listAvailableTools' });
        }

        function showMCPStatus() {
            vscode.postMessage({ type: 'showMCPStatus' });
        }

        function clearMessagesUI() {
            messages = [];
            renderMessages();
        }

        function renderMessages() {
            if (messages.length === 0) {
                welcomeMessage.style.display = 'block';
                // Clear any existing message bubbles
                const existingBubbles = messagesArea.querySelectorAll('.message-bubble');
                existingBubbles.forEach(bubble => bubble.remove());
                return;
            }

            welcomeMessage.style.display = 'none';

            // Clear existing messages
            const existingBubbles = messagesArea.querySelectorAll('.message-bubble');
            existingBubbles.forEach(bubble => bubble.remove());

            // Render messages
            messages.forEach(message => {
                const bubble = document.createElement('div');
                bubble.className = \`message-bubble \${message.role}\`;
                
                if (message.metadata?.codeBlocks?.length > 0) {
                    bubble.innerHTML = renderMessageWithCode(message);
                } else {
                    bubble.innerHTML = '<div class="message-content">' + formatMessageContent(message.content) + '</div>';
                }
                
                messagesArea.appendChild(bubble);
            });

            // Add typing indicator if loading
            if (isLoading) {
                const typingBubble = document.createElement('div');
                typingBubble.className = 'message-bubble assistant';
                typingBubble.innerHTML = '<em>Thinking...</em>';
                messagesArea.appendChild(typingBubble);
            }

            // Scroll to bottom
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }

        function formatMessageContent(content) {
            // Convert newlines to <br> and handle basic formatting
            let formatted = escapeHtml(content)
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
                .replace(/\*(.*?)\*/g, '<em>$1</em>');              // *italic*
            
            return formatted;
        }

        function renderMessageWithCode(message) {
            // Simple approach: render text and code blocks separately
            if (!message.metadata?.codeBlocks?.length) {
                return '<div class="message-content">' + formatMessageContent(message.content) + '</div>';
            }

            let html = '';
            
            // For messages with code blocks, just show the content and code blocks
            html += '<div class="message-content">' + formatMessageContent(message.content) + '</div>';

            // Add each code block
            message.metadata.codeBlocks.forEach(block => {
                html += '<div class="code-block">';
                html += '<div class="code-header">';
                html += '<span>' + (block.language || 'text');
                if (block.filename) {
                    html += ' • ' + escapeHtml(block.filename);
                }
                html += '</span>';
                html += '<vscode-button onclick="createFile(' + 
                       "'" + escapeForAttribute(block.code) + "', " +
                       "'" + escapeForAttribute(block.filename || '') + "', " +
                       "'" + escapeForAttribute(block.language || '') + "'" +
                       ')">Add File</vscode-button>';
                html += '</div>';
                html += '<div class="code-content">' + escapeHtml(block.code) + '</div>';
                html += '</div>';
            });

            return html;
        }

        function createFile(code, filename, language) {
            vscode.postMessage({
                type: 'createFile',
                code: code,
                filename: filename,
                language: language
            });
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/\\n/g, '<br>');
        }

        function escapeForAttribute(text) {
            if (!text) return '';
            return text
                .replace(/&/g, '&amp;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }

        function updateToolStatus(availableTools, mcpServerStatus) {
            const toolCount = document.getElementById('toolCount');
            const mcpCount = document.getElementById('mcpCount');
            
            if (toolCount) toolCount.textContent = availableTools?.length || 0;
            if (mcpCount) mcpCount.textContent = Object.keys(mcpServerStatus || {}).length;
        }

        // Initialize
        vscode.postMessage({ type: 'refreshToolStatus' });
    </script>
</body>
</html>`;
    }

    private _handleWebviewMessage(message: any) {
        switch (message.type) {
            case 'sendMessage':
                this._handleSendMessage(message.message);
                break;
            case 'clearMessages':
                this._handleClearMessages();
                break;
            case 'listAvailableTools':
                this._handleListAvailableTools();
                break;
            case 'showMCPStatus':
                this._handleShowMCPStatus();
                break;
            case 'createFile':
                this._handleCreateFile(message.code, message.filename, message.language);
                break;
            case 'refreshToolStatus':
                this._refreshToolStatus();
                break;
        }
    }

    private async _handleSendMessage(text: string) {
        if (!text.trim() || this._isLoading) return;

        // Check if API key is configured
        const config = vscode.workspace.getConfiguration('palette');
        const openaiKey = config.get<string>('openaiApiKey');
        
        if (!openaiKey) {
            // Show API key setup message in chat
            this._showApiKeySetup();
            return;
        }

        const userMessage: ConversationMessage = {
            role: 'user',
            content: text,
            timestamp: Date.now().toString()
        };

        this._messages.push(userMessage);
        this._isLoading = true;
        this._updateWebview();

        try {
            console.log('🎨 Generating AI response for:', text);
            
            // Use AI Integration Service to generate response
            const aiResponse = await AIIntegrationService.generateStreamingResponse(
                text,
                this._messages.slice(0, -1), // Pass conversation history without the current message
                undefined // No custom system prompt
            );
            
            // Extract code blocks if any
            const codeBlocks = this._extractCodeBlocks(aiResponse.content);
            
            const assistantMessage: ConversationMessage = {
                role: 'assistant',
                content: aiResponse.content,
                timestamp: Date.now().toString(),
                metadata: {
                    codeBlocks: codeBlocks,
                    intent: aiResponse.intent,
                    availableActions: aiResponse.suggestedActions
                }
            };

            this._messages.push(assistantMessage);
            console.log('🎨 AI response generated successfully');
            
        } catch (error: any) {
            console.error('🎨 Error generating AI response:', error);
            
            const errorMessage: ConversationMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error generating a response: ${error.message || error}. Please check your API key configuration and network connection.`,
                timestamp: Date.now().toString()
            };
            this._messages.push(errorMessage);
            
            // Show user-friendly error
            vscode.window.showErrorMessage(
                'Failed to generate AI response. Check your API key and network connection.',
                'Check Settings',
                'Retry'
            ).then(selection => {
                if (selection === 'Check Settings') {
                    vscode.commands.executeCommand('palette.showSettingsMenu');
                } else if (selection === 'Retry') {
                    this._handleSendMessage(text);
                }
            });
        } finally {
            this._isLoading = false;
            this._updateWebview();
        }
    }

    private _handleClearMessages() {
        this._messages = [];
        this._updateWebview();
    }

    private _handleListAvailableTools() {
        const tools = this._availableTools.map(tool => `• ${tool.name}: ${tool.description}`).join('\n');
        const message: ConversationMessage = {
            role: 'assistant',
            content: tools.length > 0 ? `Available tools:\n${tools}` : 'No tools currently available.',
            timestamp: Date.now().toString()
        };
        this._messages.push(message);
        this._updateWebview();
    }

    private _handleShowMCPStatus() {
        const statusEntries = Array.from(this._mcpServerStatus.entries());
        const status = statusEntries.map(([server, status]) => `• ${server}: ${status}`).join('\n');
        const message: ConversationMessage = {
            role: 'assistant',
            content: status.length > 0 ? `MCP Server Status:\n${status}` : 'No MCP servers configured.',
            timestamp: Date.now().toString()
        };
        this._messages.push(message);
        this._updateWebview();
    }

    private async _handleCreateFile(code: string, filename: string, language: string) {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder found');
                return;
            }

            const filePath = vscode.Uri.joinPath(workspaceFolder.uri, filename);
            await vscode.workspace.fs.writeFile(filePath, Buffer.from(code, 'utf8'));
            
            vscode.window.showInformationMessage(`File created: ${filename}`);
            
            // Open the file
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);
        } catch (error) {
            console.error('Error creating file:', error);
            vscode.window.showErrorMessage(`Failed to create file: ${error}`);
        }
    }

    private _extractCodeBlocks(content: string): any[] {
        const codeBlocks: any[] = [];
        const codeBlockRegex = /```(\w+)?\s*(?:\/\/ (.+))?\n([\s\S]*?)```/g;
        let match;
        
        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const filename = match[2] || '';
            const code = match[3].trim();
            
            codeBlocks.push({
                language,
                filename,
                code
            });
        }
        
        return codeBlocks;
    }

    private async _showApiKeySetup() {
        // Add a system message explaining API key setup
        const setupMsg: ConversationMessage = {
            role: 'assistant',
            content: `🔑 **API Key Required**

To get started with Palette AI, you'll need to configure an API key from OpenAI.

**Quick Setup:**
1. Click the ⚙️ Tools button above or use Command Palette
2. Run "Palette: Settings Menu"
3. Choose "Configure API Keys"  
4. Enter your API key from [OpenAI](https://platform.openai.com/api-keys)

Once configured, you can start building UIs with natural language!

**Need help?** Try these example prompts once set up:
• "Create a modern landing page with hero section"
• "Build a dashboard with sidebar navigation"
• "Design a product card with image and details"`,
            timestamp: Date.now().toString(),
            metadata: {
                isSetup: true,
                showSettings: true
            }
        };
        
        this._messages.push(setupMsg);
        this._updateWebview();
    }

    private _refreshToolStatus() {
        // Update tool status
        this._view?.webview.postMessage({
            type: 'updateToolStatus',
            availableTools: this._availableTools,
            mcpServerStatus: Object.fromEntries(this._mcpServerStatus)
        });
    }

    private _updateWebview() {
        if (this._view) {
            this._view.webview.postMessage({
                type: 'updateMessages',
                messages: this._messages,
                isLoading: this._isLoading
            });
        }
    }

    public setToolRegistry(toolRegistry: ToolRegistry) {
        this._toolRegistry = toolRegistry;
        this._refreshAvailableTools();
    }

    public setToolExecutor(toolExecutor: ToolExecutor) {
        this._toolExecutor = toolExecutor;
    }

    public setMCPManager(mcpManager: MCPManager) {
        this._mcpManager = mcpManager;
    }

    private _refreshAvailableTools() {
        if (this._toolRegistry) {
            this._availableTools = this._toolRegistry.getAllTools().map(tool => ({
                name: tool.name,
                description: tool.description,
                category: tool.category || 'general'
            }));
            this._refreshToolStatus();
        }
    }

    private _getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
}
