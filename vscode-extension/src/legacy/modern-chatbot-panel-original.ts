/**
 * Enhanced Modern Chatbot Panel with Claude-inspired design
 * Beautiful, responsive chat interface with improved UX
 */

import * as vscode from 'vscode';
import { AICapabilityRouter } from '../ai-sdk-integration/capability-router';
import { GenerationOrchestrator } from '../ai-sdk-integration/generation-orchestrator';
import { ConversationMessage } from '../conversation-manager';
import { IntegrationManager } from '../initialization/integration-manager';
import { MCPManager } from '../mcp/mcp-manager';
import { ToolExecutor } from '../tools/tool-executor';
import { ToolRegistry } from '../tools/tool-registry';
import { ProgressManager } from '../ui/progress-manager';

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
        this.initializeToolIntegration();
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

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage((data) => {
            this._handleWebviewMessage(data);
        });

        // Update tool status periodically
        this.updateToolStatus();
        setInterval(() => this.updateToolStatus(), 10000); // Every 10 seconds
    }

    private async _handleWebviewMessage(data: any) {
        console.log('🎨 Received message from webview:', data.type, data);
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
            case 'showMessage':
                vscode.window.showInformationMessage(data.message);
                break;
            case 'listAvailableTools':
                await this._handleListTools();
                break;
            case 'executeTool':
                await this._handleExecuteTool(data.toolName, data.params);
                break;
            case 'showMCPStatus':
                await this._handleShowMCPStatus();
                break;
            case 'refreshToolStatus':
                await this.updateToolStatus();
                break;
            case 'installShadcnComponents':
                await this._handleInstallShadcnComponents(data.components);
                break;
            case 'browseShadcnComponents':
                await this._handleBrowseShadcnComponents();
                break;
            case 'initShadcnProject':
                await this._handleInitShadcnProject();
                break;
            case 'clearMessages':
                this._handleClearMessages();
                break;
        }
    }

    private async _handleSendMessage(userMessage: string) {
        console.log('🎨 _handleSendMessage called with:', userMessage);
        
        if (this._isLoading) {
            console.log('🎨 Already loading, returning');
            return;
        }

        // Check if API key is configured
        const config = vscode.workspace.getConfiguration('palette');
    const openaiKey = config.get<string>('openaiApiKey');
        
    console.log('🎨 API Keys - OpenAI:', !!openaiKey);
        
    if (!openaiKey) {
            console.log('🎨 No API keys found, showing setup');
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
            // Get current model and check capabilities
            const currentModel = AICapabilityRouter.getCurrentModel();
            const capabilities = AICapabilityRouter.getModelCapabilities(currentModel);
            
            console.log(`🎨 Using ${currentModel} (${capabilities.tier} tier) with tool calling`);

            // Initialize streaming response with tool awareness
            const assistantMsg: ConversationMessage = {
                role: 'assistant',
                content: '',
                timestamp: Date.now().toString(),
                metadata: {
                    codeBlocks: [],
                    intent: 'generating',
                    model: currentModel,
                    tier: capabilities.tier,
                    availableTools: this._availableTools.length,
                    mcpServers: this._mcpServerStatus.size
                }
            };
            this._messages.push(assistantMsg);
            this._updateWebview();

            // Use progress manager for AI operations
            const result = await this._progressManager.showGenerationProgress(async (progress, token) => {
                progress.report({ message: 'Initializing AI generation...', increment: 10 });
                
                // Use AI SDK 5 integration with tool awareness
                const orchestrator = GenerationOrchestrator.getInstance();
                
                progress.report({ message: 'Processing with tool capabilities...', increment: 20 });
                
                // Generate response with full context, tools, and capabilities
                const generationResult = await orchestrator.generate(userMessage, {
                    includeContext: true,
                    temperature: config.get<number>('temperature') || 0.7,
                    stream: capabilities.streaming, // Enable streaming if supported
                    validateOutput: true
                });
                
                progress.report({ message: 'Generation complete', increment: 70 });
                
                return generationResult;
            });

            if (result.success) {
                console.log(`🎨 Generated response with ${result.metadata?.files?.length || 0} files`);
                
                // Update assistant message with successful result
                assistantMsg.content = result.content;
                assistantMsg.metadata = {
                    codeBlocks: result.metadata?.codeBlocks || [],
                    files: result.metadata?.files || [],
                    strategy: result.metadata?.strategy,
                    model: result.metadata?.model,
                    tier: result.metadata?.tier,
                    tokensUsed: result.metadata?.tokensUsed
                };
            } else {
                // Handle generation failure
                console.error('🎨 Generation failed:', result.error);
                assistantMsg.content = `❌ Error generating response: ${result.error}\n\nPlease check:\n- Your API key configuration\n- Your internet connection\n- The selected model (${currentModel})`;
                assistantMsg.metadata = {
                    error: result.error,
                    model: currentModel,
                    tier: capabilities.tier
                };
            }
            
        } catch (error: any) {
            console.error('🎨 AI SDK integration error:', error);
            const assistantMsg: ConversationMessage = {
                role: 'assistant',
                content: `❌ Error generating response: ${error.message}\n\nThis appears to be a client-side error. Please check:\n- Your API key configuration\n- Your internet connection\n- The model selection`,
                timestamp: Date.now().toString(),
                metadata: {
                    error: error.message
                }
            };
            this._messages.push(assistantMsg);
        }

        this._isLoading = false;
        this._updateWebview();
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
1. Click the ⚙️ Settings button below
2. Choose "Configure API Keys"  
3. Enter your API key from:
    - [OpenAI](https://platform.openai.com/api-keys) (for GPT models)

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

    private _handleClearMessages() {
        this._messages = [];
        this._updateWebview();
    }

    private async _handleCreateFile(code: string, filename: string | undefined, language: string) {
        if (!filename) {
            vscode.window.showErrorMessage('No filename specified for the code block');
            return;
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
            await vscode.workspace.fs.writeFile(filePath, Buffer.from(code, 'utf8'));
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);
            vscode.window.showInformationMessage(`Created ${filename} in ${targetDir}`);
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
            const conversationText = this._messages
                .map(msg => `**${msg.role.toUpperCase()}:**\n${msg.content}\n\n`)
                .join('');
            
            const document = await vscode.workspace.openTextDocument({
                content: conversationText,
                language: 'markdown'
            });
            
            await vscode.window.showTextDocument(document);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to export conversation: ${error.message}`);
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

    /**
     * Initialize tool system integration
     */
    private async initializeToolIntegration(): Promise<void> {
        try {
            const integrationManager = IntegrationManager.getInstance();
            
            // Wait for system to be initialized
            let retries = 0;
            while (!integrationManager.isSystemInitialized() && retries < 10) {
                await new Promise(resolve => setTimeout(resolve, 500));
                retries++;
            }

            if (integrationManager.isSystemInitialized()) {
                this._toolRegistry = integrationManager.getToolRegistry();
                this._toolExecutor = integrationManager.getToolExecutor();
                this._mcpManager = integrationManager.getMCPManager();
                
                console.log('🎨 ModernChatbotPanel: Tool system integration initialized');
                await this.updateToolStatus();
            } else {
                console.warn('🎨 ModernChatbotPanel: Tool system not available');
            }
        } catch (error) {
            console.error('🎨 ModernChatbotPanel: Failed to initialize tool integration:', error);
        }
    }

    /**
     * Update available tools and MCP server status
     */
    private async updateToolStatus(): Promise<void> {
        try {
            // Update available tools
            if (this._toolRegistry) {
                const allTools = this._toolRegistry.getAllTools();
                this._availableTools = allTools.map(tool => ({
                    name: tool.name,
                    description: tool.description,
                    category: tool.category
                }));
            }

            // Update MCP server status
            if (this._mcpManager) {
                const stats = this._mcpManager.getStatistics();
                this._mcpServerStatus.clear();
                Object.entries(stats.serverStatuses).forEach(([name, status]) => {
                    this._mcpServerStatus.set(name, status);
                });
            }

            // Update webview with new status
            if (this._view) {
                this._view.webview.postMessage({
                    type: 'updateToolStatus',
                    availableTools: this._availableTools,
                    mcpServerStatus: Array.from(this._mcpServerStatus.entries())
                });
            }
        } catch (error) {
            console.error('🎨 Failed to update tool status:', error);
        }
    }

    /**
     * Handle list available tools request
     */
    private async _handleListTools(): Promise<void> {
        if (!this._toolRegistry) {
            vscode.window.showWarningMessage('Tool system not available');
            return;
        }

        const tools = this._toolRegistry.getAllTools();
        const toolList = tools.map(tool => `• **${tool.name}** (${tool.category}): ${tool.description}`).join('\n');
        
        const toolMsg: ConversationMessage = {
            role: 'assistant',
            content: `🛠️ **Available Tools** (${tools.length} total)\n\n${toolList}\n\nYou can use these tools by including requests in your messages. For example: "Create a new React component" will automatically use file creation tools.`,
            timestamp: Date.now().toString(),
            metadata: {
                toolList: true,
                totalTools: tools.length
            }
        };
        
        this._messages.push(toolMsg);
        this._updateWebview();
    }

    /**
     * Handle tool execution request
     */
    private async _handleExecuteTool(toolName: string, params: any): Promise<void> {
        if (!this._toolExecutor || !this._toolRegistry) {
            vscode.window.showErrorMessage('Tool system not available');
            return;
        }

        try {
            const extensionContext = vscode.extensions.getExtension('palette')?.exports;
            const context = {
                workspacePath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
                extensionContext: extensionContext || ({} as vscode.ExtensionContext),
                outputChannel: vscode.window.createOutputChannel('Palette Tool Execution')
            };

            const result = await this._toolExecutor.executeTool(toolName, params, context);
            
            const resultMsg: ConversationMessage = {
                role: 'assistant',
                content: result.success 
                    ? `✅ Tool **${toolName}** executed successfully!\n\n${result.followUpSuggestions?.join('\n') || ''}`
                    : `❌ Tool **${toolName}** failed: ${result.error?.message}`,
                timestamp: Date.now().toString(),
                metadata: {
                    toolExecution: true,
                    toolName,
                    success: result.success
                }
            };
            
            this._messages.push(resultMsg);
            this._updateWebview();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Tool execution failed: ${error.message}`);
        }
    }

    /**
     * Handle show MCP status request
     */
    private async _handleShowMCPStatus(): Promise<void> {
        if (!this._mcpManager) {
            vscode.window.showWarningMessage('MCP system not available');
            return;
        }

        const stats = this._mcpManager.getStatistics();
        const serversList = Object.entries(stats.serverStatuses)
            .map(([name, status]) => `• **${name}**: ${status}`)
            .join('\n');

        const mcpMsg: ConversationMessage = {
            role: 'assistant',
            content: `🔌 **MCP Server Status**\n\n**Total Servers**: ${stats.totalServers}\n**Running Servers**: ${stats.runningServers}\n**Available Tools**: ${stats.totalTools}\n\n**Server Details**:\n${serversList || 'No servers configured'}`,
            timestamp: Date.now().toString(),
            metadata: {
                mcpStatus: true,
                totalServers: stats.totalServers,
                runningServers: stats.runningServers
            }
        };
        
        this._messages.push(mcpMsg);
        this._updateWebview();
    }

    /**
     * Handle shadcn/ui component installation
     */
    private async _handleInstallShadcnComponents(components: string[]): Promise<void> {
        if (!components || components.length === 0) {
            vscode.window.showWarningMessage('No components specified');
            return;
        }

        try {
            // Use shadcn commands
            await vscode.commands.executeCommand('palette.shadcn.install');
            
            const installMsg: ConversationMessage = {
                role: 'assistant',
                content: `🎨 **Installing shadcn/ui components**: ${components.join(', ')}\n\nPlease use the component picker dialog that opened to select and install your components.`,
                timestamp: Date.now().toString(),
                metadata: {
                    shadcnInstall: true,
                    components: components.length
                }
            };
            
            this._messages.push(installMsg);
            this._updateWebview();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to install shadcn/ui components: ${error.message}`);
        }
    }

    /**
     * Handle browsing shadcn/ui components
     */
    private async _handleBrowseShadcnComponents(): Promise<void> {
        try {
            // Use shadcn browser command
            await vscode.commands.executeCommand('palette.shadcn.browse');
            
            const browseMsg: ConversationMessage = {
                role: 'assistant',
                content: `🎨 **shadcn/ui Component Browser** opened!\n\nYou can now:\n• Browse available components\n• View component previews\n• Install components directly\n• See usage examples`,
                timestamp: Date.now().toString(),
                metadata: {
                    shadcnBrowser: true
                }
            };
            
            this._messages.push(browseMsg);
            this._updateWebview();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to open component browser: ${error.message}`);
        }
    }

    /**
     * Handle shadcn/ui project initialization
     */
    private async _handleInitShadcnProject(): Promise<void> {
        try {
            // Use shadcn init command
            await vscode.commands.executeCommand('palette.shadcn.init');
            
            const initMsg: ConversationMessage = {
                role: 'assistant',
                content: `🎨 **Initializing shadcn/ui** in your project...\n\nThis will:\n• Set up components.json configuration\n• Install required dependencies\n• Create utility functions\n• Set up CSS variables\n\nPlease follow the setup wizard that opened.`,
                timestamp: Date.now().toString(),
                metadata: {
                    shadcnInit: true
                }
            };
            
            this._messages.push(initMsg);
            this._updateWebview();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to initialize shadcn/ui: ${error.message}`);
        }
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

    private _getHtmlForWebview(webview: vscode.Webview): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Palette AI Assistant</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline' ${webview.cspSource}; script-src 'unsafe-inline' ${webview.cspSource}; font-src ${webview.cspSource};">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        html, body {
            height: 100%;
            overflow: hidden;
        }

        :root {
            --chat-radius: 14px;
            --chat-spacing: 14px;
            --chat-max-width: 700px;
            --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.1);
            --shadow-elevated: 0 8px 24px rgba(0, 0, 0, 0.15);
            --gradient-primary: linear-gradient(135deg, #7c8cff 0%, #6a79ff 100%);
            --gradient-user: linear-gradient(135deg, #0ea5e9 0%, #22c1dc 100%);
            --bg: linear-gradient(180deg, rgba(6,7,10,0.95) 0%, rgba(12,12,14,0.96) 100%);
            --panel: rgba(255,255,255,0.03);
            --panel-border: rgba(255,255,255,0.06);
            --muted: rgba(255,255,255,0.55);
            --ring: rgba(124,140,255,0.35);
        }

    body {
            font-family: var(--vscode-font-family, 'Segoe UI', system-ui, sans-serif);
            font-size: var(--vscode-font-size, 13px);
            line-height: 1.6;
            color: var(--vscode-foreground, #cccccc);
            background: var(--vscode-sideBar-background, #0b0b0f);
            background-image: radial-gradient(600px 300px at 50% -100px, rgba(124,140,255,0.08), transparent), radial-gradient(500px 200px at 10% 120%, rgba(94,234,212,0.06), transparent), radial-gradient(500px 200px at 90% 120%, rgba(99,102,241,0.06), transparent);
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            overflow: hidden;
        }
        /* Shell */
        .centered {
            width: 100%;
            max-width: var(--chat-max-width);
            margin: 0 auto;
        }

        /* Top toolbar */
        .topbar {
            padding: 8px 12px;
            border-bottom: 1px solid var(--panel-border);
            background: var(--vscode-sideBar-background, #0b0b0f);
            flex-shrink: 0;
        }
        .topbar-inner { display: flex; align-items: center; }
        .topbar-actions { margin-left: auto; display: flex; align-items: center; gap: 8px; }
        .tool-status-indicators { display: flex; align-items: center; gap: 12px; }
        .status-indicator { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--muted); }
        .status-dot { font-size: 12px; }
        .status-count { font-weight: 600; color: var(--vscode-foreground); }

    /* Messages Container */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px 12px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            scroll-behavior: smooth;
        }

        .messages-container::-webkit-scrollbar {
            width: 8px;
        }

        .messages-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .messages-container::-webkit-scrollbar-thumb {
            background: var(--vscode-scrollbarSlider-background, #424242);
            border-radius: 4px;
        }

        .messages-container::-webkit-scrollbar-thumb:hover {
            background: var(--vscode-scrollbarSlider-hoverBackground, #4f4f4f);
        }

        /* Hero / Header */
        .hero {
            text-align: center;
            padding: 16px 12px 12px 12px;
        }

        .hero-title {
            font-size: 20px;
            font-weight: 400;
            letter-spacing: -0.01em;
            color: var(--vscode-foreground, #e6e6e6);
            margin: 8px 0 12px 0;
            line-height: 1.3;
        }

        .model-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            border-radius: 999px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            font-size: 11px;
            color: var(--muted);
        }

        /* Message Bubbles */
        .message {
            display: flex;
            flex-direction: column;
            gap: 10px;
            opacity: 1;
        }

        .message.user {
            align-items: flex-end;
        }

        .message.assistant {
            align-items: flex-start;
        }

        .message-content {
            width: 100%;
            padding: 16px 18px;
            border-radius: var(--chat-radius);
            word-wrap: break-word;
            position: relative;
            transition: var(--transition-smooth);
            box-shadow: var(--shadow-soft);
            line-height: 1.6;
            font-size: 14px;
            border: 1px solid var(--panel-border);
        }

        .message-content:hover {
            box-shadow: var(--shadow-elevated);
            transform: translateY(-1px);
        }

        .message.user .message-content {
            background: rgba(34,211,238,0.08);
            color: var(--vscode-foreground, #e6e6e6);
            border-color: rgba(34,211,238,0.25);
            border-bottom-right-radius: 8px;
        }

        .message.assistant .message-content {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-bottom-left-radius: 8px;
            color: var(--vscode-foreground, #dddddd);
        }

        /* Code Blocks */
        .code-block {
            margin: 16px 0;
            background: var(--vscode-textCodeBlock-background, #0f1115);
            border: 1px solid var(--panel-border);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: var(--shadow-soft);
        }

        .code-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: var(--panel);
            border-bottom: 1px solid var(--panel-border);
            font-size: 12px;
            font-weight: 600;
        }

        .code-lang {
            color: var(--vscode-descriptionForeground);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .code-content {
            padding: 16px;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            overflow-x: auto;
            white-space: pre;
            line-height: 1.5;
        }

    .create-file-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 600;
            transition: var(--transition-smooth);
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .create-file-btn:hover {
            background: var(--vscode-button-hoverBackground);
            transform: translateY(-1px);
        }

        /* Composer */
        .input-container { 
            padding: 8px 12px; 
            background: var(--vscode-sideBar-background, #252526); 
            border-top: 1px solid var(--panel-border); 
            flex-shrink: 0;
        }

        .input-wrapper {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: end;
            gap: 8px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            padding: 8px 12px;
            transition: var(--transition-smooth);
            box-shadow: var(--shadow-soft);
        }

        .input-wrapper:focus-within {
            border-color: var(--ring);
            box-shadow: 0 0 0 4px var(--ring);
        }

        .message-input {
            background: transparent;
            color: var(--vscode-input-foreground, #e6e6e6);
            border: none;
            outline: none;
            font-family: inherit;
            font-size: 14px;
            resize: none;
            min-height: 24px;
            max-height: 140px;
            line-height: 1.5;
            padding: 8px 4px;
        }

        .message-input::placeholder {
            color: var(--muted);
        }

        .icon-btn {
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 6px 10px;
            height: 28px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-smooth);
            flex-shrink: 0;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }

    .icon-btn:hover { color: #fff; background: rgba(255,255,255,0.06); }
    .icon-btn[title="Clear"] { border-style: dashed; }

        .send-button {
            background: var(--gradient-primary);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 6px 12px;
            height: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: var(--transition-smooth);
            box-shadow: var(--shadow-soft);
            flex-shrink: 0;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
        }

        .send-button:hover { transform: translateY(-1px); box-shadow: var(--shadow-elevated); }
        .send-button:active { transform: translateY(0); }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; }

        .model-select {
            background: rgba(255,255,255,0.06);
            color: var(--vscode-foreground);
            border: 1px solid var(--panel-border);
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 10px;
            font-weight: 600;
            outline: none;
            max-width: 80px;
            text-overflow: ellipsis;
        }

        /* Scroll to bottom */
        #scrollDownBtn {
            position: fixed;
            right: 20px;
            bottom: 96px; /* above composer */
            z-index: 50;
            opacity: 0;
            pointer-events: none;
            transition: var(--transition-smooth);
        }
        #scrollDownBtn.visible { opacity: 1; pointer-events: auto; }

        /* Loading States */
        .loading-indicator {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--vscode-descriptionForeground);
            font-size: 13px;
            padding: 16px 0;
            opacity: 0;
            animation: fadeIn 0.3s ease-out forwards;
        }

        @keyframes fadeIn {
            to { opacity: 1; }
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 16px 20px;
            background: var(--vscode-panel-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: var(--chat-radius);
            border-bottom-left-radius: 4px;
            max-width: 80px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--vscode-descriptionForeground);
            animation: typingBounce 1.4s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }

        @keyframes typingBounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

    /* Welcome */
    .welcome-message { color: var(--muted); }
    .welcome-subtitle { font-size: 13px; opacity: 0.9; margin-bottom: 16px; }
    .welcome-features { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
    .feature-card { padding: 12px; background: var(--panel); border: 1px solid var(--panel-border); border-radius: 10px; text-align: left; transition: var(--transition-smooth); cursor: pointer; display: flex; align-items: center; gap: 10px; }
    .feature-card:hover { transform: translateY(-1px); box-shadow: var(--shadow-elevated); border-color: var(--ring); }
    .feature-icon { font-size: 16px; color: #9aa8ff; flex-shrink: 0; }
    .feature-content { flex: 1; min-width: 0; }
    .feature-title { font-weight: 600; margin-bottom: 2px; color: var(--vscode-foreground, #e6e6e6); font-size: 12px; }
    .feature-desc { font-size: 11px; color: var(--muted); line-height: 1.4; }

        /* Responsive Design */
        @media (max-width: 400px) {
            .input-wrapper {
        border-radius: 16px;
        padding: 8px 10px;
            }
            
            .message-content {
        padding: 12px 14px;
            }
        .centered { padding: 0 2px; }
        }

        /* Accessibility */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
</head>
<body>
    <div class="topbar">
        <div class="centered topbar-inner">
            <div class="tool-status-indicators" id="toolStatus">
                <div class="status-indicator" id="toolIndicator" title="Available Tools">
                    <span class="status-dot">🛠️</span>
                    <span class="status-count" id="toolCount">0</span>
                </div>
                <div class="status-indicator" id="mcpIndicator" title="MCP Servers">
                    <span class="status-dot">🔌</span>
                    <span class="status-count" id="mcpCount">0</span>
                </div>
            </div>
            <div class="topbar-actions">
                <select class="model-select" id="modelSelect" onchange="changeModel()" title="Select AI model">
                    <option value="gpt-5-mini-2025-08-07" selected>GPT-5 Mini</option>
                    <option value="gpt-5-2025-08-07">GPT-5</option>
                    <option value="gpt-5-nano-2025-08-07">GPT-5 Nano</option>
                </select>
                <button class="icon-btn" onclick="showTools()" title="Available Tools">
                    Tools
                </button>
                <button class="icon-btn" onclick="showMCPStatus()" title="MCP Status">
                    MCP
                </button>
                <button class="icon-btn" id="clearButtonTop" onclick="clearMessages()" title="Clear">
                    Clear
                </button>
            </div>
        </div>
    </div>
    <div class="messages-container">
        <div class="centered" id="messagesContainer">
            <div class="hero">
                <div class="model-pill" id="modelPill">GPT‑5 Mini</div>
                <div class="hero-title">What's on your mind tonight?</div>
                <div class="welcome-message">
                    <div class="welcome-subtitle">
                        I can help you design components, build pages, and organize files in your project.
                    </div>
                    <div class="welcome-features">
                        <div class="feature-card" onclick="vscode.postMessage({type:'showSettings'})">
                            <div class="feature-icon">🎨</div>
                            <div class="feature-title">Build Pages</div>
                            <div class="feature-desc">Design complete pages and layouts with responsive design</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🧠</div>
                            <div class="feature-title">Smart Analysis</div>
                            <div class="feature-desc">Analyze your project structure and suggest improvements</div>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">⚡</div>
                            <div class="feature-title">Instant Files</div>
                            <div class="feature-desc">Create and organize files with intelligent placement</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="scrollDownBtn" class="icon-btn" title="Jump to latest" onclick="scrollToBottom()" aria-label="Scroll to bottom">
        ↓
    </div>

    <div class="input-container">
        <div class="centered">
            <div class="input-wrapper">
                <textarea 
                    class="message-input" 
                    id="messageInput" 
                    placeholder="How can I help you today?"
                    rows="1"
                    aria-label="Message input"
                ></textarea>
                <button class="send-button" id="sendButton" onclick="sendMessage()" title="Send message">
                    Send
                </button>
            </div>
        </div>
    </div>

    <script>
    let messages = [];
    let isLoading = false;
    let atBottom = true;

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
            const pill = document.getElementById('modelPill');
            if (pill) pill.textContent = modelSelect.options[modelSelect.selectedIndex].text;
                    }
                    break;
                case 'updateToolStatus':
                    updateToolStatusDisplay(message.availableTools, message.mcpServerStatus);
                    break;
            }
        });

        function sendMessage() {
            console.log('📤 sendMessage() called');
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            console.log('📤 Message value:', message, 'isLoading:', isLoading);
            
            if (!message || isLoading) {
                console.log('📤 Returning early - no message or loading');
                return;
            }

            console.log('📤 Posting message to VS Code');
            vscode.postMessage({
                type: 'sendMessage',
                message: message
            });

            input.value = '';
            autoResize(input);
            input.focus();
        }

    function clearMessages() {
            vscode.postMessage({ type: 'clearMessages' });
        }

    // exportConversation and showSettings are still available via commands if needed

        function changeModel() {
            const modelSelect = document.getElementById('modelSelect');
            const selectedModel = modelSelect.value;
            console.log('🤖 Model changed to:', selectedModel);
            vscode.postMessage({ 
                type: 'changeModel', 
                model: selectedModel 
            });
            const pill = document.getElementById('modelPill');
            if (pill) pill.textContent = modelSelect.options[modelSelect.selectedIndex].text;
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
            
            // Show welcome hero if no messages
            if (messages.length === 0) {
                container.innerHTML = \`
                    <div class="hero">
                        <div class="model-pill">GPT‑5 Mini</div>
                        <div class="hero-title">What's on your mind tonight?</div>
                        <div class="welcome-message">
                            <div class="welcome-subtitle">
                                I'm your AI-powered UI developer assistant. I can help you create beautiful React components, pages, and entire features using TypeScript, Tailwind CSS, and shadcn/ui.
                            </div>
                            <div class="welcome-features">
                                <div class="feature-card">
                                    <div class="feature-icon">🎨</div>
                                    <div class="feature-content">
                                        <div class="feature-title">Generate Components</div>
                                        <div class="feature-desc">Create functional React components</div>
                                    </div>
                                </div>
                                <div class="feature-card">
                                    <div class="feature-icon">📱</div>
                                    <div class="feature-content">
                                        <div class="feature-title">Build Pages</div>
                                        <div class="feature-desc">Design complete page layouts</div>
                                    </div>
                                </div>
                                <div class="feature-card">
                                    <div class="feature-icon">🔧</div>
                                    <div class="feature-content">
                                        <div class="feature-title">Smart Analysis</div>
                                        <div class="feature-desc">Analyze project structure</div>
                                    </div>
                                </div>
                                <div class="feature-card">
                                    <div class="feature-icon">⚡</div>
                                    <div class="feature-content">
                                        <div class="feature-title">Instant Files</div>
                                        <div class="feature-desc">Create files intelligently</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                \`;
                return;
            }

            container.innerHTML = '';

            messages.forEach((message, index) => {
                const messageDiv = document.createElement('div');
                messageDiv.className = \`message \${message.role}\`;
                messageDiv.style.animationDelay = \`\${index * 0.1}s\`;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';

                if (message.role === 'assistant' && message.metadata?.codeBlocks && message.metadata.codeBlocks.length > 0) {
                    // Enhanced code block rendering
                    let content = message.content;
                    let htmlContent = '';

                    message.metadata.codeBlocks.forEach((block, blockIndex) => {
                        const beforeCode = content.substring(0, content.indexOf('\`\`\`'));
                        htmlContent += formatMessageContent(beforeCode);
                        
                        htmlContent += \`
                            <div class="code-block">
                                <div class="code-header">
                                    <span class="code-lang">\${block.language || 'text'}\${block.filename ? ' • ' + block.filename : ''}</span>
                                    <button class="create-file-btn" onclick="createFile('\${escapeJsString(block.code)}', '\${escapeJsString(block.filename || '')}', '\${escapeJsString(block.language || '')}')">
                                        + Add File
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
                    htmlContent += formatMessageContent(content);
                    contentDiv.innerHTML = htmlContent;
                } else {
                    contentDiv.innerHTML = formatMessageContent(message.content);
                }

                messageDiv.appendChild(contentDiv);
                container.appendChild(messageDiv);
            });

            // Add typing indicator if loading
            if (isLoading) {
                const typingDiv = document.createElement('div');
                typingDiv.className = 'message assistant';
                typingDiv.innerHTML = \`
                    <div class="typing-indicator">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                \`;
                container.appendChild(typingDiv);
            }

            // Only auto-scroll if at bottom
            setTimeout(() => {
                if (atBottom) {
                    const messagesContainer = document.querySelector('.messages-container');
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
                updateScrollButton();
            }, 50);
            
            // Update send button state
            const input = document.getElementById('messageInput');
            document.getElementById('sendButton').disabled = isLoading || input.value.trim().length === 0;
        }

        function formatMessageContent(content) {
            // Simple formatting - replace newlines with breaks
            if (!content) return '';
            return content.replace(/\n/g, '<br>');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function escapeJsString(text) {
            if (!text) return '';
            return text
                .replace(/\\/g, '\\\\')
                .replace(/'/g, "\\'")
                .replace(/"/g, '\\"')
                .replace(/\n/g, '\\n')
                .replace(/\r/g, '\\r')
                .replace(/\t/g, '\\t');
        }

        // Auto-resize textarea
        function autoResize(textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        }

        function updateScrollButton() {
            const btn = document.getElementById('scrollDownBtn');
            if (!btn) return;
            btn.classList.toggle('visible', !atBottom);
        }

        function scrollToBottom() {
            const messagesContainer = document.querySelector('.messages-container');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            atBottom = true;
            updateScrollButton();
        }

        // Event listeners
        const messageInput = document.getElementById('messageInput');
        
        messageInput.addEventListener('input', function() {
            autoResize(this);
            document.getElementById('sendButton').disabled = isLoading || this.value.trim().length === 0;
        });

        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });

        // Track user scroll to manage auto-scroll and button
        const messagesContainer = document.querySelector('.messages-container');
        messagesContainer.addEventListener('scroll', function() {
            const threshold = 40; // px from bottom
            atBottom = this.scrollTop + this.clientHeight >= this.scrollHeight - threshold;
            updateScrollButton();
        });

        // Focus input on load
        messageInput.focus();

    // Set initial model to GPT-5 default
    document.getElementById('modelSelect').value = 'gpt-5-mini-2025-08-07';
        changeModel();

        // Tool system functions
        function showTools() {
            vscode.postMessage({ type: 'listAvailableTools' });
        }

        function showMCPStatus() {
            vscode.postMessage({ type: 'showMCPStatus' });
        }

        function clearMessages() {
            vscode.postMessage({ type: 'clearMessages' });
        }

        function executeTool(toolName, params) {
            vscode.postMessage({ 
                type: 'executeTool', 
                toolName: toolName,
                params: params || {}
            });
        }

        function refreshToolStatus() {
            vscode.postMessage({ type: 'refreshToolStatus' });
        }

        function installShadcnComponents(components) {
            vscode.postMessage({ 
                type: 'installShadcnComponents', 
                components: components || []
            });
        }

        function browseShadcnComponents() {
            vscode.postMessage({ type: 'browseShadcnComponents' });
        }

        function initShadcnProject() {
            vscode.postMessage({ type: 'initShadcnProject' });
        }

        function updateToolStatusDisplay(availableTools, mcpServerStatus) {
            const toolCount = document.getElementById('toolCount');
            const mcpCount = document.getElementById('mcpCount');
            
            if (toolCount) toolCount.textContent = availableTools?.length || 0;
            if (mcpCount) mcpCount.textContent = mcpServerStatus?.length || 0;

            // Update tool indicator colors based on status
            const toolIndicator = document.getElementById('toolIndicator');
            const mcpIndicator = document.getElementById('mcpIndicator');
            
            if (toolIndicator) {
                toolIndicator.style.opacity = (availableTools?.length > 0) ? '1' : '0.5';
            }
            if (mcpIndicator) {
                mcpIndicator.style.opacity = (mcpServerStatus?.length > 0) ? '1' : '0.5';
            }
        }

        // Enhanced welcome message for tool-aware system
        function renderEnhancedWelcome() {
            const container = document.getElementById('messagesContainer');
            container.innerHTML = \`
                <div class="hero">
                    <div class="model-pill">GPT‑5 Mini with Tools</div>
                    <div class="hero-title">Ready to build with AI tools</div>
                    <div class="welcome-message">
                        <div class="welcome-subtitle">
                            I have access to powerful development tools, MCP servers, and can create files, analyze code, and manage your project.
                        </div>
                        <div class="welcome-features">
                            <div class="feature-card" onclick="showTools()">
                                <div class="feature-icon">🛠️</div>
                                <div class="feature-content">
                                    <div class="feature-title">Available Tools</div>
                                    <div class="feature-desc">View and use development tools</div>
                                </div>
                            </div>
                            <div class="feature-card" onclick="showMCPStatus()">
                                <div class="feature-icon">🔌</div>
                                <div class="feature-content">
                                    <div class="feature-title">MCP Servers</div>
                                    <div class="feature-desc">Check server connectivity</div>
                                </div>
                            </div>
                            <div class="feature-card">
                                <div class="feature-icon">🎨</div>
                                <div class="feature-content">
                                    <div class="feature-title">Smart Creation</div>
                                    <div class="feature-desc">Build components with approval flow</div>
                                </div>
                            </div>
                            <div class="feature-card">
                                <div class="feature-icon">⚡</div>
                                <div class="feature-content">
                                    <div class="feature-title">Real-time Analysis</div>
                                    <div class="feature-desc">Project-aware suggestions</div>
                                </div>
                            </div>
                            <div class="feature-card" onclick="browseShadcnComponents()">
                                <div class="feature-icon">📚</div>
                                <div class="feature-content">
                                    <div class="feature-title">shadcn/ui Browser</div>
                                    <div class="feature-desc">Browse and install components</div>
                                </div>
                            </div>
                            <div class="feature-card" onclick="initShadcnProject()">
                                <div class="feature-icon">🚀</div>
                                <div class="feature-content">
                                    <div class="feature-title">Setup shadcn/ui</div>
                                    <div class="feature-desc">Initialize project with components</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            \`;
        }

        // Initial render
        renderMessages();

        // Initialize tool status
        refreshToolStatus();
    </script>
</body>
</html>`;
    }

    // ... (keep your existing methods for handling messages, etc.) ...
}