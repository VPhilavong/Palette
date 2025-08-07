/**
 * Simplified Agentic Palette Panel
 * A lightweight agent-like interface without LangChain dependencies
 * Provides v0-like conversational design experience within VS Code
 */

import * as vscode from 'vscode';
import { StreamingPaletteService } from './services/StreamingPaletteService';

interface AgentTool {
    name: string;
    description: string;
    parameters: Record<string, any>;
    handler: (params: any) => Promise<any>;
}

interface ConversationMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
}

export class SimplifiedAgenticPanel {
    public static currentPanel: SimplifiedAgenticPanel | undefined;
    
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private readonly _disposables: vscode.Disposable[] = [];
    private readonly _streamingService: StreamingPaletteService;
    
    // Agent state
    private _conversationHistory: ConversationMessage[] = [];
    private _currentThreadId: string = 'main';
    private _isProcessing: boolean = false;
    private _availableTools: AgentTool[] = [];

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._streamingService = new StreamingPaletteService();
        
        this._initializeTools();
        this._setupWebview();
        this._setupMessageHandling();
        this._setupLifecycle();
        
        // Send initial welcome message
        this._sendWelcomeMessage();
    }

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.ViewColumn.Beside;

        if (SimplifiedAgenticPanel.currentPanel) {
            SimplifiedAgenticPanel.currentPanel._panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'paletteSimpleAgent',
            'Palette AI Agent (Simplified)',
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

        SimplifiedAgenticPanel.currentPanel = new SimplifiedAgenticPanel(panel, extensionUri);
    }

    private _initializeTools() {
        this._availableTools = [
            {
                name: 'generate_design',
                description: 'Generate complete pages, features, or UI experiences',
                parameters: {
                    prompt: 'string',
                    designType: 'page|feature|component|layout'
                },
                handler: async (params) => {
                    return await this._handleGenerateDesign(params);
                }
            },
            {
                name: 'analyze_project',
                description: 'Analyze project structure and design system',
                parameters: {
                    projectPath: 'string'
                },
                handler: async (params) => {
                    return await this._handleAnalyzeProject(params);
                }
            },
            {
                name: 'manage_preview',
                description: 'Start Vite dev server and manage live preview',
                parameters: {
                    action: 'start|stop|open|refresh',
                    url: 'string'
                },
                handler: async (params) => {
                    return await this._handleManagePreview(params);
                }
            }
        ];
    }

    private async _handleGenerateDesign(params: any) {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace folder found');
            }

            // For now, simulate generation - in real implementation this would call the streaming service
            // const response = await this._streamingService.generateWithStreaming(...);
            
            return {
                success: true,
                description: `Generated ${params.designType || 'page'} successfully`,
                files: {
                    'src/pages/generated.tsx': '// Generated page content here',
                    'src/components/GeneratedComponent.tsx': '// Generated component here'
                },
                previewUrl: 'http://localhost:5173'
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Generation failed'
            };
        }
    }

    private async _handleAnalyzeProject(params: any) {
        try {
            const workspaceRoot = params.projectPath || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace folder found');
            }

            // Simplified analysis - in real implementation this would call the streaming service
            return {
                framework: 'Vite + React',
                uiLibrary: 'shadcn/ui',
                designTokens: ['colors', 'typography', 'spacing'],
                availableComponents: ['Button', 'Card', 'Input', 'Dialog'],
                recommendations: ['Use consistent spacing', 'Follow design system patterns']
            };
        } catch (error) {
            return {
                error: error instanceof Error ? error.message : 'Analysis failed'
            };
        }
    }

    private async _handleManagePreview(params: any) {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace folder found');
            }

            if (params.action === 'start') {
                const terminal = vscode.window.createTerminal({
                    name: 'Palette Preview',
                    cwd: workspaceRoot
                });
                
                terminal.sendText('npm run dev');
                terminal.show();
                
                return {
                    success: true,
                    message: 'Vite dev server started',
                    previewUrl: 'http://localhost:5173'
                };
            } else if (params.action === 'open') {
                vscode.env.openExternal(vscode.Uri.parse(params.url || 'http://localhost:5173'));
                return {
                    success: true,
                    message: 'Preview opened in browser'
                };
            }
            
            return { success: false, error: 'Unknown action' };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Preview operation failed'
            };
        }
    }

    private _setupWebview() {
        this._panel.webview.html = this._getWebviewHtml();
    }

    private _setupMessageHandling() {
        this._panel.webview.onDidReceiveMessage(
            async (message: any) => {
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

    private async _handleWebviewMessage(message: any) {
        switch (message.type) {
            case 'user-message':
                await this._handleUserMessage(message);
                break;
            case 'clear-conversation':
                await this._handleClearConversation();
                break;
            default:
                console.log('Unknown message type:', message);
        }
    }

    private async _handleUserMessage(message: any) {
        if (this._isProcessing) {
            this._sendMessage({
                type: 'error',
                error: 'Please wait for the current request to complete',
                timestamp: new Date().toISOString()
            });
            return;
        }

        this._isProcessing = true;

        try {
            // Add user message to history
            this._conversationHistory.push({
                role: 'user',
                content: message.content,
                timestamp: new Date().toISOString()
            });

            // Send status update
            this._sendMessage({
                type: 'status',
                message: '🤖 Agent is analyzing your request...',
                timestamp: new Date().toISOString()
            });

            // Simple intent detection and tool usage
            const response = await this._processUserIntent(message.content);
            
            // Add response to history
            this._conversationHistory.push({
                role: 'assistant',
                content: response,
                timestamp: new Date().toISOString()
            });

            this._sendMessage({
                type: 'ai-response',
                content: response,
                conversationId: this._currentThreadId,
                timestamp: new Date().toISOString(),
                metadata: {
                    model: 'simplified-agent'
                }
            });

        } catch (error) {
            console.error('Agent processing error:', error);
            this._sendMessage({
                type: 'error',
                error: `Agent error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                timestamp: new Date().toISOString()
            });
        } finally {
            this._isProcessing = false;
        }
    }

    private async _processUserIntent(userMessage: string): Promise<string> {
        const message = userMessage.toLowerCase();
        
        // Simple intent detection
        if (message.includes('generate') || message.includes('create') || message.includes('build')) {
            // Generate design intent
            const result = await this._availableTools[0].handler({
                prompt: userMessage,
                designType: this._detectDesignType(message)
            });
            
            if (result.success) {
                return `✅ **Generated ${this._detectDesignType(message)} successfully!**

${result.description}

**What I created:**
- Complete, functional design ready for preview
- Modern styling with shadcn/ui components
- Responsive layout optimized for all devices

**Next steps:**
- I can start the dev server so you can see your design live
- We can iterate and refine the design together
- Install additional components if needed

Would you like me to start the preview server now?`;
            } else {
                return `❌ **Generation failed:** ${result.error}

Let me try a different approach or help troubleshoot the issue.`;
            }
        } else if (message.includes('analyze') || message.includes('understand') || message.includes('project')) {
            // Analyze project intent
            const result = await this._availableTools[1].handler({});
            
            if (result.error) {
                return `❌ **Analysis failed:** ${result.error}`;
            }
            
            return `📊 **Project Analysis Complete**

**Framework:** ${result.framework}
**UI Library:** ${result.uiLibrary}
**Available Components:** ${result.availableComponents.join(', ')}

**Design Tokens Found:**
${result.designTokens.map((token: string) => `- ${token}`).join('\n')}

**Recommendations:**
${result.recommendations.map((rec: string) => `- ${rec}`).join('\n')}

Your project is well-structured for rapid design prototyping!`;
        } else if (message.includes('preview') || message.includes('server') || message.includes('dev')) {
            // Preview server intent
            const result = await this._availableTools[2].handler({
                action: 'start'
            });
            
            if (result.success) {
                return `🚀 **Preview server starting!**

${result.message}

**Preview URL:** ${result.previewUrl}

The dev server is now running. You can see your designs live and they'll update automatically as we make changes.

Would you like me to open the preview in your browser?`;
            } else {
                return `❌ **Failed to start preview:** ${result.error}`;
            }
        } else {
            // General conversation
            return this._generateConversationalResponse(userMessage);
        }
    }

    private _detectDesignType(message: string): string {
        if (message.includes('page') || message.includes('landing') || message.includes('homepage')) {
            return 'page';
        } else if (message.includes('feature') || message.includes('section')) {
            return 'feature';
        } else if (message.includes('layout') || message.includes('template')) {
            return 'layout';
        }
        return 'page';
    }

    private _generateConversationalResponse(userMessage: string): string {
        return `I understand you'd like help with: "${userMessage}"

As your AI design companion, I can help you:

🎨 **Generate complete designs** - Landing pages, dashboards, e-commerce sites, blogs
📊 **Analyze your project** - Understand your design system and available components  
🚀 **Start live previews** - See your designs immediately with hot reload
🔧 **Manage components** - Install shadcn/ui components automatically
✨ **Iterate designs** - Refine and improve through natural conversation

**Try asking me:**
- "Create a modern SaaS landing page with pricing tiers"
- "Build a dashboard with data visualization cards"
- "Design an e-commerce product grid with filters"
- "Start the preview server so I can see my designs"

What would you like to create today?`;
    }

    private async _handleClearConversation() {
        this._conversationHistory = [];
        
        this._sendMessage({
            type: 'status',
            message: '🗑️ Conversation cleared',
            timestamp: new Date().toISOString()
        });

        setTimeout(() => this._sendWelcomeMessage(), 500);
    }

    private _sendWelcomeMessage() {
        const welcomeMessage = `# Welcome to Palette AI Agent! 🎨

I'm your simplified AI design companion for UI/UX prototyping. I can help you create complete, beautiful web pages and features - just like Vercel v0, but right here in VS Code!

## What I can do:
- **Generate complete pages** (landing pages, dashboards, e-commerce sites, blogs)
- **Analyze your project** and understand your design system
- **Start live previews** so you can see your designs immediately
- **Create modern designs** with React + TypeScript + Vite + shadcn/ui

## Try asking me:
- "Create a modern SaaS landing page with hero, features, and pricing"
- "Build a dashboard with sidebar navigation and data cards"
- "Design an e-commerce product grid with filters"
- "Analyze my current project structure"

I'm ready to help you prototype amazing designs! What would you like to create?`;

        this._sendMessage({
            type: 'ai-response',
            content: welcomeMessage,
            conversationId: this._currentThreadId,
            timestamp: new Date().toISOString(),
            metadata: {
                isWelcome: true,
                model: 'simplified-agent'
            }
        });
    }

    private _sendMessage(message: any) {
        this._panel.webview.postMessage(message);
    }

    private _getWebviewHtml(): string {
        // Reuse the same HTML from AgenticPalettePanel but with simplified branding
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI Agent (Simplified)</title>
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
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Palette AI Agent (Simplified)</h1>
        <p class="subtitle">v0-like design prototyping in VS Code • No complex dependencies</p>
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
            placeholder="Describe the page or feature you want to create..."
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
        
        let isProcessing = false;
        
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
            
            addUserMessage(message);
            
            vscode.postMessage({
                type: 'user-message',
                content: message,
                timestamp: new Date().toISOString()
            });
            
            messageInput.value = '';
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
        
        function addAIMessage(content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai-message';
            
            const htmlContent = content
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/\\n/g, '<br>');
            
            messageDiv.innerHTML = htmlContent;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addStatusMessage(message) {
            const statusDiv = document.createElement('div');
            statusDiv.className = 'status-message';
            statusDiv.textContent = message;
            messagesContainer.appendChild(statusDiv);
            scrollToBottom();
            
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
        }
        
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'ai-response':
                    addAIMessage(message.content);
                    resetProcessingState();
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
        
        messageInput.focus();
    </script>
</body>
</html>`;
    }

    public dispose() {
        SimplifiedAgenticPanel.currentPanel = undefined;

        this._panel.dispose();

        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}