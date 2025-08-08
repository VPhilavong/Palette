/**
 * Modern Chatbot Panel using VSCode Elements
 * Replaces the old React-based chatbot with native VS Code UI components
 */

import * as vscode from 'vscode';
import { AIIntegrationService } from '../ai-integration';
import { ConversationMessage } from '../conversation-manager';
import { getAIContextBuilder } from '../intelligence/ai-context-builder';

export class ModernChatbotPanel implements vscode.WebviewViewProvider {
    public static readonly viewType = 'palette.modernChatbot';
    
    private _view?: vscode.WebviewView;
    private _messages: ConversationMessage[] = [];
    private _isLoading = false;

    constructor(private readonly _extensionUri: vscode.Uri) {}

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

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage((data) => {
            this._handleWebviewMessage(data);
        });
    }

    private async _handleWebviewMessage(data: any) {
        switch (data.type) {
            case 'sendMessage':
                await this._handleSendMessage(data.message);
                break;
            case 'clearMessages':
                this._clearMessages();
                break;
            case 'createFile':
                await this._handleCreateFile(data.code, data.filename, data.language);
                break;
            case 'exportConversation':
                await this._handleExportConversation();
                break;
            case 'showSettings':
                await this._handleShowSettings();
                break;
            case 'changeModel':
                await this._handleChangeModel(data.model);
                break;
            case 'configureApiKey':
                await this._handleConfigureApiKey();
                break;
        }
    }

    private async _handleSendMessage(userMessage: string) {
        if (this._isLoading) {
            return;
        }

        // Check if API key is configured
        const config = vscode.workspace.getConfiguration('palette');
        const openaiKey = config.get<string>('openaiApiKey');
        const anthropicKey = config.get<string>('anthropicApiKey');
        
        if (!openaiKey && !anthropicKey) {
            // Show inline API key setup
            this._showApiKeySetup();
            return;
        }

        this._isLoading = true;
        
        // Add user message
        const userMsg: ConversationMessage = {
            role: 'user',
            content: userMessage,
            timestamp: Date.now().toString()
        };
        this._messages.push(userMsg);
        this._updateWebview();

        try {
            // Build enhanced context using pure TypeScript analysis
            const contextBuilder = getAIContextBuilder();
            const enhancedContext = await contextBuilder.buildEnhancedContext(userMessage);
            
            console.log('🧠 Enhanced context built:', {
                framework: enhancedContext.projectContext.framework,
                components: enhancedContext.projectContext.availableComponents.length,
                actions: enhancedContext.availableActions.length
            });
            
            // Initialize streaming response
            const assistantMsg: ConversationMessage = {
                role: 'assistant',
                content: '',
                timestamp: Date.now().toString(),
                metadata: {
                    codeBlocks: [],
                    intent: 'generating',
                    context: enhancedContext
                }
            };
            this._messages.push(assistantMsg);
            this._updateWebview();

            // Use AI SDK directly with enhanced context
            await this._generateWithEnhancedContext(userMessage, assistantMsg, enhancedContext);
            
        } catch (error: any) {
            // Add error message
            const errorMsg: ConversationMessage = {
                role: 'assistant',
                content: `❌ Error: ${error.message}`,
                timestamp: Date.now().toString()
            };
            this._messages.push(errorMsg);
        }

        this._isLoading = false;
        this._updateWebview();
    }

    private async _streamResponseFromBackend(userMessage: string, assistantMsg: ConversationMessage) {
        try {
            // Get VS Code configuration
            const config = vscode.workspace.getConfiguration('palette');
            const apiKey = config.get<string>('openaiApiKey') || config.get<string>('anthropicApiKey') || '';
            const model = config.get<string>('defaultModel') || 'gpt-4o-mini';
            const backendUrl = config.get<string>('backendUrl') || 'http://localhost:8765';
            
            // This method will be removed as we now use enhanced context builder
            const projectContext = {
                projectPath: 'legacy-fallback',
                framework: 'react'
            };
            
            // Prepare conversation history
            const conversationHistory = this._messages
                .slice(0, -1) // Exclude the current assistant message being generated
                .map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));
            
            // Make streaming request
            const response = await fetch(`${backendUrl}/api/generate/unified/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                body: JSON.stringify({
                    message: userMessage,
                    conversation_history: conversationHistory,
                    project_context: projectContext,
                    api_key: apiKey,
                    model: model
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (!response.body) {
                throw new Error('No response body for streaming');
            }
            
            // Process streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            switch (data.type) {
                                case 'start':
                                    console.log(`🎨 Streaming started with model: ${data.model}`);
                                    break;
                                    
                                case 'content':
                                    assistantMsg.content += data.content;
                                    this._updateWebview();
                                    break;
                                    
                                case 'complete':
                                    assistantMsg.content = data.full_content;
                                    assistantMsg.metadata = {
                                        codeBlocks: data.code_blocks || [],
                                        intent: data.intent
                                    };
                                    console.log(`🎨 Streaming complete. Generated ${data.code_blocks?.length || 0} code blocks`);
                                    this._updateWebview();
                                    return; // Exit the streaming loop
                                    
                                case 'error':
                                    throw new Error(data.error);
                            }
                        } catch (parseError) {
                            console.warn('🎨 Failed to parse streaming data:', parseError);
                        }
                    }
                }
            }
            
        } catch (error: any) {
            console.error('🎨 Streaming error:', error);
            assistantMsg.content = `❌ Streaming error: ${error.message}`;
            this._updateWebview();
        }
    }

    private async _generateWithEnhancedContext(
        userMessage: string, 
        assistantMsg: ConversationMessage, 
        enhancedContext: any
    ) {
        try {
            // Use AI SDK directly with enhanced context (no backend dependency)
            const response = await AIIntegrationService.generateStreamingResponse(
                userMessage,
                this._messages.slice(0, -1), // Exclude the current assistant message being generated
                enhancedContext.systemPrompt
            );

            // Update the assistant message with the response
            assistantMsg.content = response.content;
            assistantMsg.metadata = {
                codeBlocks: response.codeBlocks || [],
                intent: response.intent,
                context: enhancedContext,
                availableActions: enhancedContext.availableActions
            };
            
            console.log(`🎨 Generated response with ${response.codeBlocks?.length || 0} code blocks`);
            this._updateWebview();
            
        } catch (error: any) {
            console.error('🎨 Enhanced context generation error:', error);
            assistantMsg.content = `❌ Error generating response: ${error.message}\n\nThis appears to be a client-side error. Please check:\n- Your API key configuration\n- Your internet connection\n- The model selection`;
            assistantMsg.metadata = {
                ...assistantMsg.metadata,
                error: error.message
            };
            this._updateWebview();
        }
    }

    private async _showApiKeySetup() {
        // Add a system message explaining API key setup
        const setupMsg: ConversationMessage = {
            role: 'assistant',
            content: `🔑 **API Key Required**

To get started with Palette AI, you'll need to configure an API key from OpenAI or Anthropic.

**Quick Setup:**
1. Click the ⚙️ Settings button below
2. Choose "Configure API Keys"  
3. Enter your API key from:
   - [OpenAI](https://platform.openai.com/api-keys) (for GPT models)
   - [Anthropic](https://console.anthropic.com/) (for Claude models)

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

    private async _handleCreateFile(code: string, filename: string | undefined, language: string) {
        if (!filename) {
            filename = `Component.${language === 'tsx' ? 'tsx' : 'js'}`;
        }

        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        // Smart file placement based on project structure
        let targetDir = 'src/components';
        if (filename.includes('Page') || filename.toLowerCase().includes('page')) {
            targetDir = 'src/pages';
        } else if (filename.startsWith('use') && language === 'ts') {
            targetDir = 'src/hooks';
        }

        const filePath = vscode.Uri.joinPath(workspaceFolder.uri, targetDir, filename);
        
        try {
            // Ensure directory exists
            const dirPath = vscode.Uri.joinPath(workspaceFolder.uri, targetDir);
            try {
                await vscode.workspace.fs.stat(dirPath);
            } catch {
                await vscode.workspace.fs.createDirectory(dirPath);
            }

            // Write file
            await vscode.workspace.fs.writeFile(filePath, Buffer.from(code, 'utf8'));
            
            // Show success and open file
            vscode.window.showInformationMessage(`Created ${filename} in ${targetDir}`);
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to create file: ${error.message}`);
        }
    }

    private _clearMessages() {
        this._messages = [];
        this._updateWebview();
    }

    private async _handleExportConversation() {
        try {
            const timestamp = new Date().toISOString().split('T')[0];
            const filename = `palette-conversation-${timestamp}.json`;
            
            const exportData = {
                timestamp: new Date().toISOString(),
                messages: this._messages,
                messageCount: this._messages.length
            };
            
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                const filePath = vscode.Uri.joinPath(workspaceFolder.uri, filename);
                await vscode.workspace.fs.writeFile(filePath, Buffer.from(JSON.stringify(exportData, null, 2), 'utf8'));
                vscode.window.showInformationMessage(`Conversation exported to ${filename}`);
            } else {
                vscode.window.showErrorMessage('No workspace folder found for export');
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Export failed: ${error.message}`);
        }
    }

    private async _handleShowSettings() {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'palette');
    }

    private async _handleChangeModel(model: string) {
        const config = vscode.workspace.getConfiguration('palette');
        await config.update('defaultModel', model, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`Model changed to ${model}`);
        this._updateWebview();
    }

    private async _handleConfigureApiKey() {
        // Use the settings manager for API key configuration
        await vscode.commands.executeCommand('palette.showSettingsMenu');
    }

    private _updateWebview() {
        if (this._view) {
            const config = vscode.workspace.getConfiguration('palette');
            const currentModel = config.get<string>('defaultModel') || 'gpt-4o-mini';
            
            this._view.webview.postMessage({
                type: 'updateMessages',
                messages: this._messages,
                isLoading: this._isLoading
            });
            
            this._view.webview.postMessage({
                type: 'updateModel',
                model: currentModel
            });
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        // Get webview resource URIs
        const codiconsUri = webview.asWebviewUri(vscode.Uri.joinPath(
            this._extensionUri, 'node_modules', '@vscode/codicons', 'dist', 'codicon.css'
        ));
        
        // Use VS Code Elements for native styling
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI Assistant</title>
    <link href="${codiconsUri}" rel="stylesheet" />
    <style>
        :root {
            --codicon-font-family: codicon;
        }

        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            line-height: var(--vscode-font-weight);
            color: var(--vscode-foreground);
            background-color: var(--vscode-sideBar-background);
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 12px 16px;
            background-color: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-sideBar-border);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header h2 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--vscode-charts-green);
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .message.user {
            align-items: flex-end;
        }

        .message.assistant {
            align-items: flex-start;
        }

        .message-content {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 8px;
            word-wrap: break-word;
        }

        .message.user .message-content {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .message.assistant .message-content {
            background-color: var(--vscode-panel-background);
            border: 1px solid var(--vscode-panel-border);
        }

        .code-block {
            margin: 12px 0;
            background-color: var(--vscode-textCodeBlock-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            overflow: hidden;
        }

        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background-color: var(--vscode-editor-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            font-size: 12px;
        }

        .code-content {
            padding: 12px;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            overflow-x: auto;
            white-space: pre;
        }

        .create-file-btn {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        }

        .create-file-btn:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        .input-container {
            padding: 16px;
            background-color: var(--vscode-sideBar-background);
            border-top: 1px solid var(--vscode-sideBar-border);
            display: flex;
            gap: 8px;
        }

        .message-input {
            flex: 1;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            padding: 8px 12px;
            font-family: var(--vscode-font-family);
            resize: none;
            min-height: 36px;
            max-height: 120px;
        }

        .message-input:focus {
            outline: none;
            border-color: var(--vscode-focusBorder);
        }

        .send-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            cursor: pointer;
            font-weight: 600;
        }

        .send-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .toolbar {
            padding: 8px 16px;
            background-color: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-sideBar-border);
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .toolbar-btn {
            display: flex;
            align-items: center;
            gap: 4px;
            background-color: transparent;
            color: var(--vscode-foreground);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 12px;
            font-family: var(--vscode-font-family);
            transition: all 0.2s ease;
        }

        .toolbar-btn:hover {
            background-color: var(--vscode-list-hoverBackground);
            border-color: var(--vscode-button-background);
        }

        .toolbar-btn:active {
            background-color: var(--vscode-list-activeSelectionBackground);
        }

        .toolbar-btn .codicon {
            font-size: 14px;
        }

        .model-selector {
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }

        .model-select {
            background-color: var(--vscode-dropdown-background);
            color: var(--vscode-dropdown-foreground);
            border: 1px solid var(--vscode-dropdown-border);
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            cursor: pointer;
        }

        .loading-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--vscode-descriptionForeground);
            font-size: 12px;
            padding: 8px 0;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid var(--vscode-panel-border);
            border-top: 2px solid var(--vscode-charts-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="status-indicator"></div>
        <h2>Palette AI Assistant</h2>
    </div>
    
    <div class="toolbar">
        <button class="toolbar-btn" onclick="clearMessages()">
            <span class="codicon codicon-clear-all"></span>
            Clear
        </button>
        <button class="toolbar-btn" onclick="exportConversation()">
            <span class="codicon codicon-export"></span>
            Export
        </button>
        <button class="toolbar-btn" onclick="showSettings()">
            <span class="codicon codicon-settings-gear"></span>
            Settings
        </button>
        <div class="model-selector">
            <span>Model:</span>
            <select class="model-select" id="modelSelect" onchange="changeModel()">
                <option value="gpt-4o-mini">GPT-4o Mini (Fast)</option>
                <option value="gpt-4o">GPT-4o (Quality)</option>
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
            </select>
        </div>
    </div>

    <div class="messages-container" id="messagesContainer">
        <div class="message assistant">
            <div class="message-content">
                👋 Hi! I'm your AI-powered UI developer assistant. I can help you create React components, pages, and entire features using TypeScript, Tailwind CSS, and shadcn/ui.

                **What I can do:**
                - Generate complete pages and components
                - Create forms, dashboards, and interactive UIs  
                - Analyze your project structure
                - Suggest improvements and best practices
                - Handle file creation and routing

                What would you like to build today?
            </div>
        </div>
    </div>

    <div class="input-container">
        <textarea 
            class="message-input" 
            id="messageInput" 
            placeholder="Describe what you want to build..."
            rows="1"
        ></textarea>
        <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
    </div>

    <script>
        let messages = [];
        let isLoading = false;

        // Handle VS Code API
        const vscode = acquireVsCodeApi();

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'updateMessages':
                    messages = message.messages;
                    isLoading = message.isLoading;
                    renderMessages();
                    break;
                case 'updateModel':
                    const modelSelect = document.getElementById('modelSelect');
                    if (modelSelect && message.model) {
                        modelSelect.value = message.model;
                    }
                    break;
            }
        });

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || isLoading) return;

            vscode.postMessage({
                type: 'sendMessage',
                message: message
            });

            input.value = '';
            autoResize(input);
        }

        function clearMessages() {
            vscode.postMessage({ type: 'clearMessages' });
        }

        function exportConversation() {
            vscode.postMessage({ type: 'exportConversation' });
        }

        function showSettings() {
            vscode.postMessage({ type: 'showSettings' });
        }

        function changeModel() {
            const modelSelect = document.getElementById('modelSelect');
            const selectedModel = modelSelect.value;
            vscode.postMessage({ 
                type: 'changeModel', 
                model: selectedModel 
            });
        }

        function createFile(code, filename, language) {
            vscode.postMessage({
                type: 'createFile',
                code: code,
                filename: filename,
                language: language
            });
        }

        function renderMessages() {
            const container = document.getElementById('messagesContainer');
            
            // Keep existing welcome message if no messages
            if (messages.length === 0) {
                return;
            }

            container.innerHTML = '';

            messages.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.className = \`message \${message.role}\`;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';

                if (message.role === 'assistant' && message.metadata?.codeBlocks && message.metadata.codeBlocks.length > 0) {
                    // Split content by code blocks for proper rendering
                    let content = message.content;
                    let htmlContent = '';

                    message.metadata.codeBlocks.forEach((block, index) => {
                        const beforeCode = content.substring(0, content.indexOf('\`\`\`'));
                        htmlContent += beforeCode.replace(/\\n/g, '<br>');
                        
                        htmlContent += \`
                            <div class="code-block">
                                <div class="code-header">
                                    <span>\${block.language || 'text'}\${block.filename ? \` - \${block.filename}\` : ''}</span>
                                    <button class="create-file-btn" onclick="createFile('\${escapeHtml(block.code)}', '\${block.filename || ''}', '\${block.language}')">
                                        Add File
                                    </button>
                                </div>
                                <div class="code-content">\${escapeHtml(block.code)}</div>
                            </div>
                        \`;

                        // Move past this code block
                        const codeBlockEnd = content.indexOf('\`\`\`', content.indexOf('\`\`\`') + 3) + 3;
                        content = content.substring(codeBlockEnd);
                    });

                    // Add remaining content
                    htmlContent += content.replace(/\\n/g, '<br>');
                    contentDiv.innerHTML = htmlContent;
                } else {
                    contentDiv.innerHTML = message.content.replace(/\\n/g, '<br>');
                }

                messageDiv.appendChild(contentDiv);
                container.appendChild(messageDiv);
            });

            // Add loading indicator if needed
            if (isLoading) {
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading-indicator';
                loadingDiv.innerHTML = \`
                    <div class="spinner"></div>
                    <span>Generating response...</span>
                \`;
                container.appendChild(loadingDiv);
            }

            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
            
            // Update send button state
            document.getElementById('sendButton').disabled = isLoading;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        // Event listeners
        document.getElementById('messageInput').addEventListener('input', function() {
            autoResize(this);
        });

        document.getElementById('messageInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Initial render
        renderMessages();
    </script>
</body>
</html>`;
    }
}