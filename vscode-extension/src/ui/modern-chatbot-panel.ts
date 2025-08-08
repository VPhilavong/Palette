/**
 * Modern Chatbot Panel using VSCode Elements
 * Provides native VSCode UI components with no JavaScript errors
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { AIIntegrationService } from '../ai-integration';
import { ConversationMessage } from '../conversation-manager';
import { MCPManager } from '../mcp/mcp-manager';
import { ToolExecutor } from '../tools/tool-executor';
import { ToolRegistry } from '../tools/tool-registry';
import { ProgressManager } from './progress-manager';
import { WebviewTemplate } from './webview-template';

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
            localResourceRoots: [
                this._extensionUri,
                vscode.Uri.joinPath(this._extensionUri, 'node_modules'),
                vscode.Uri.joinPath(this._extensionUri, 'src', 'ui')
            ]
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
        
        // Read CSS file
        const stylePath = path.join(this._extensionUri.fsPath, 'src', 'ui', 'webview-styles.css');
        let styleContent = '';
        try {
            styleContent = fs.readFileSync(stylePath, 'utf8');
        } catch (error) {
            console.error('Failed to read CSS file:', error);
        }
        
        const nonce = this._getNonce();

        // Use WebviewTemplate to generate HTML
        return WebviewTemplate.generateHTML(
            scriptUri.toString(),
            playgroundUri.toString(),
            '', // We'll inline the CSS for now
            nonce
        ).replace('<link href="" rel="stylesheet">', `<style>${styleContent}</style>`);
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
        if (!text.trim() || this._isLoading) {
            return;
        }

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

            // Validate and generate filename if needed
            if (!filename || filename.trim() === '') {
                // Generate default filename based on language
                const timestamp = Date.now();
                const extension = this._getFileExtension(language);
                filename = `component-${timestamp}.${extension}`;
                
                // Ask user for filename
                const userFilename = await vscode.window.showInputBox({
                    prompt: 'Enter filename for the generated code',
                    value: filename,
                    validateInput: (value) => {
                        if (!value || value.trim() === '') {
                            return 'Filename cannot be empty';
                        }
                        if (value.includes('/') || value.includes('\\')) {
                            return 'Please enter just the filename, not a path';
                        }
                        return null;
                    }
                });

                if (!userFilename) {
                    vscode.window.showInformationMessage('File creation cancelled');
                    return;
                }
                
                filename = userFilename;
            }

            // Ensure filename has an extension
            if (!filename.includes('.')) {
                const extension = this._getFileExtension(language);
                filename = `${filename}.${extension}`;
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

    private _getFileExtension(language: string): string {
        const extensionMap: Record<string, string> = {
            'typescript': 'ts',
            'tsx': 'tsx',
            'javascript': 'js',
            'jsx': 'jsx',
            'css': 'css',
            'scss': 'scss',
            'html': 'html',
            'json': 'json',
            'python': 'py',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rust': 'rs',
            'text': 'txt'
        };
        
        return extensionMap[language.toLowerCase()] || 'txt';
    }

    private _extractCodeBlocks(content: string): any[] {
        const codeBlocks: any[] = [];
        // Improved regex to catch various filename formats
        const codeBlockRegex = /```(\w+)?(?:\s+([^\n]+))?\n([\s\S]*?)```/g;
        let match;
        
        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            let filename = match[2] || '';
            const code = match[3].trim();
            
            // Clean up filename if it starts with // or #
            if (filename) {
                filename = filename.replace(/^[\/\/#\s]+/, '').trim();
            }
            
            // If no filename, try to infer from code content
            if (!filename && (language === 'tsx' || language === 'jsx' || language === 'ts' || language === 'js')) {
                // Try to extract component/function name from the code
                const componentMatch = code.match(/(?:export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)|const\s+(\w+)\s*[:=])/);
                if (componentMatch) {
                    const componentName = componentMatch[1] || componentMatch[2];
                    if (componentName) {
                        const extension = this._getFileExtension(language);
                        filename = `${componentName}.${extension}`;
                    }
                }
            }
            
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