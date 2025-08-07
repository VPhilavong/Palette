/**
 * Enhanced Palette Panel with native conversation integration,
 * rich UI, streaming responses, and VS Code integration
 */

import * as vscode from 'vscode';
import { ConversationClient, ConversationMessage } from './conversation/ConversationClient';
import { getEnhancedChatWebviewHtml } from './ui/enhancedChat';
import { ConversationStorage, ConversationSession } from './storage/ConversationStorage';
import * as path from 'path';
import * as fs from 'fs';

interface StreamingState {
    isActive: boolean;
    currentMessage: string;
    messageId: string;
}

interface FileOperation {
    type: 'create' | 'edit' | 'preview';
    filePath: string;
    content: string;
    description: string;
}

export class EnhancedPalettePanel {
    public static currentPanel: EnhancedPalettePanel | undefined;
    
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private readonly _disposables: vscode.Disposable[] = [];
    private readonly _conversationClient: ConversationClient;
    private readonly _outputChannel: vscode.OutputChannel;
    private readonly _storage: ConversationStorage;
    
    private _streamingState: StreamingState = {
        isActive: false,
        currentMessage: '',
        messageId: ''
    };
    
    private _projectAnalysis: any = null;
    private _workspaceRoot: string | undefined;
    private _currentSession: ConversationSession | null = null;

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._outputChannel = vscode.window.createOutputChannel('Palette Enhanced');
        this._conversationClient = new ConversationClient(this._outputChannel);
        this._storage = new ConversationStorage(context);
        this._workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;

        // Set up the webview
        this._update();

        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                await this._handleWebviewMessage(message);
            },
            null,
            this._disposables
        );

        // Initialize the conversation client
        this._initialize();
    }

    public static createOrShow(extensionUri: vscode.Uri, context?: vscode.ExtensionContext) {
        const column = vscode.ViewColumn.Beside;

        // If we already have a panel, show it
        if (EnhancedPalettePanel.currentPanel) {
            EnhancedPalettePanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            'enhancedPalettePanel',
            '🎨 Palette AI',
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

        EnhancedPalettePanel.currentPanel = new EnhancedPalettePanel(panel, extensionUri, context!);
    }

    private async _initialize() {
        this._outputChannel.appendLine('🚀 Initializing Enhanced Palette Panel...');
        
        try {
            // Send initialization message
            this._sendToWebview({
                type: 'system',
                content: '🔄 Initializing Palette AI...'
            });

            // Initialize conversation client
            const initialized = await this._conversationClient.initialize();
            
            if (initialized) {
                this._sendToWebview({
                    type: 'system',
                    content: '✅ Palette AI ready! What would you like to create?'
                });

                // Initialize or load conversation session
                await this._initializeSession();
                
                // Analyze project in background
                if (this._workspaceRoot) {
                    this._analyzeProjectAsync();
                }
            } else {
                this._sendToWebview({
                    type: 'error',
                    content: '❌ Failed to initialize Palette AI. Please check your API keys in VS Code settings.'
                });
            }

        } catch (error: any) {
            this._outputChannel.appendLine(`❌ Initialization failed: ${error.message}`);
            this._sendToWebview({
                type: 'error',
                content: `❌ Initialization failed: ${error.message}`
            });
        }
    }

    private async _analyzeProjectAsync() {
        try {
            this._sendToWebview({
                type: 'system',
                content: '🔍 Analyzing your project...'
            });

            this._projectAnalysis = await this._conversationClient.analyzeProject(this._workspaceRoot);
            
            // Send project info to webview
            const framework = this._projectAnalysis?.framework || 'React';
            const styling = this._projectAnalysis?.styling || 'CSS';
            const hasTypeScript = this._projectAnalysis?.hasTypeScript || false;
            
            this._sendToWebview({
                type: 'projectAnalysis',
                content: `📊 **Project Analysis Complete**\n• Framework: ${framework}\n• Styling: ${styling}${hasTypeScript ? '\n• TypeScript: ✅' : ''}`
            });

        } catch (error: any) {
            this._outputChannel.appendLine(`Project analysis failed: ${error.message}`);
        }
    }

    private async _handleWebviewMessage(message: any) {
        switch (message.command) {
            case 'sendMessage':
                await this._handleUserMessage(message.text);
                break;

            case 'createFile':
                await this._handleCreateFile(message.operation);
                break;

            case 'previewComponent':
                await this._handlePreviewComponent(message.code, message.options);
                break;

            case 'clearConversation':
                this._handleClearConversation();
                break;

            case 'analyzeProject':
                await this._analyzeProjectAsync();
                break;

            case 'imageUpload':
                await this._handleImageUpload(message);
                break;

            case 'loadSession':
                await this._handleLoadSession(message.sessionId);
                break;

            case 'saveSession':
                await this._handleSaveSession(message.name);
                break;

            case 'listSessions':
                await this._handleListSessions();
                break;

            case 'deleteSession':
                await this._handleDeleteSession(message.sessionId);
                break;

            default:
                this._outputChannel.appendLine(`Unknown command: ${message.command}`);
        }
    }

    private async _handleUserMessage(text: string) {
        if (!text.trim()) {
            return;
        }

        this._outputChannel.appendLine(`💬 User message: ${text}`);

        // Add user message to chat
        this._sendToWebview({
            type: 'userMessage',
            content: text,
            timestamp: new Date().toISOString()
        });

        // Save user message to session
        const userMessage: ConversationMessage = {
            role: 'user',
            content: text,
            timestamp: new Date().toISOString()
        };
        await this._saveMessageToSession(userMessage);

        // Start streaming response
        const messageId = `msg-${Date.now()}`;
        this._streamingState = {
            isActive: true,
            currentMessage: '',
            messageId: messageId
        };

        // Send initial streaming message
        this._sendToWebview({
            type: 'startStreaming',
            messageId: messageId,
            content: '🤔 Thinking...'
        });

        try {
            const response = await this._conversationClient.sendMessage(text, {
                projectPath: this._workspaceRoot,
                streamCallback: (chunk: string) => {
                    this._handleStreamingUpdate(messageId, chunk);
                },
                progressCallback: (stage: string, progress: number) => {
                    this._handleProgressUpdate(messageId, stage, progress);
                },
                errorCallback: (error: string) => {
                    this._handleStreamingError(messageId, error);
                }
            });

            // Complete streaming
            this._streamingState.isActive = false;
            
            this._sendToWebview({
                type: 'completeStreaming',
                messageId: messageId,
                content: response.response,
                metadata: response.metadata,
                timestamp: new Date().toISOString()
            });

            // Save assistant message to session
            const assistantMessage: ConversationMessage = {
                role: 'assistant',
                content: response.response,
                timestamp: new Date().toISOString(),
                metadata: response.metadata
            };
            await this._saveMessageToSession(assistantMessage);

            // Handle special responses
            await this._handleSpecialResponse(response);

        } catch (error: any) {
            this._streamingState.isActive = false;
            
            this._sendToWebview({
                type: 'errorMessage',
                messageId: messageId,
                content: `❌ I encountered an error: ${error.message}`,
                timestamp: new Date().toISOString()
            });
        }
    }

    private _handleStreamingUpdate(messageId: string, chunk: string) {
        if (this._streamingState.messageId === messageId && this._streamingState.isActive) {
            this._streamingState.currentMessage += chunk;
            
            this._sendToWebview({
                type: 'streamingUpdate',
                messageId: messageId,
                content: chunk
            });
        }
    }

    private _handleProgressUpdate(messageId: string, stage: string, progress: number) {
        if (this._streamingState.messageId === messageId && this._streamingState.isActive) {
            this._sendToWebview({
                type: 'progressUpdate',
                messageId: messageId,
                stage: stage,
                progress: progress
            });
        }
    }

    private _handleStreamingError(messageId: string, error: string) {
        if (this._streamingState.messageId === messageId) {
            this._sendToWebview({
                type: 'streamingError',
                messageId: messageId,
                error: error
            });
        }
    }

    private async _handleSpecialResponse(response: any) {
        if (!response.metadata) return;

        // Handle component generation
        if (response.metadata.componentCode) {
            this._sendToWebview({
                type: 'componentGenerated',
                code: response.metadata.componentCode,
                intent: response.metadata.intent,
                componentType: response.metadata.componentType,
                actions: [
                    { id: 'create-file', label: '📄 Create File', primary: true },
                    { id: 'preview', label: '👁️ Preview', secondary: true },
                    { id: 'copy-code', label: '📋 Copy Code', secondary: true }
                ]
            });
        }

        // Handle preview generation  
        if (response.metadata.previewResult) {
            this._sendToWebview({
                type: 'previewGenerated',
                preview: response.metadata.previewResult
            });
        }

        // Handle multi-step features
        if (response.metadata.featurePlan) {
            this._sendToWebview({
                type: 'featurePlan',
                plan: response.metadata.featurePlan,
                actions: [
                    { id: 'execute-plan', label: '🚀 Execute Plan', primary: true },
                    { id: 'step-by-step', label: '👣 Step by Step', secondary: true },
                    { id: 'modify-plan', label: '✏️ Modify Plan', secondary: true }
                ]
            });
        }
    }

    private async _handleCreateFile(operation: FileOperation) {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder open');
                return;
            }

            // Determine file path
            let filePath = operation.filePath;
            if (!path.isAbsolute(filePath)) {
                filePath = path.join(workspaceFolder.uri.fsPath, filePath);
            }

            // Ensure directory exists
            const dirPath = path.dirname(filePath);
            if (!fs.existsSync(dirPath)) {
                await fs.promises.mkdir(dirPath, { recursive: true });
            }

            // Create file
            await fs.promises.writeFile(filePath, operation.content, 'utf8');

            // Open file in editor
            const document = await vscode.workspace.openTextDocument(filePath);
            await vscode.window.showTextDocument(document);

            // Send success message
            this._sendToWebview({
                type: 'fileCreated',
                filePath: filePath,
                content: `✅ Created file: ${path.relative(workspaceFolder.uri.fsPath, filePath)}`
            });

            // Show success notification
            const fileName = path.basename(filePath);
            vscode.window.showInformationMessage(`Created ${fileName} successfully!`);

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `❌ Failed to create file: ${error.message}`
            });
            vscode.window.showErrorMessage(`Failed to create file: ${error.message}`);
        }
    }

    private async _handlePreviewComponent(code: string, options: any = {}) {
        try {
            this._sendToWebview({
                type: 'system',
                content: '🖼️ Generating component preview...'
            });

            const preview = await this._conversationClient.generatePreview(code, {
                projectPath: this._workspaceRoot,
                size: options.size || 'desktop',
                theme: options.theme || 'light',
                includeVariants: options.includeVariants || false,
                prompt: options.prompt || 'Preview component'
            });

            this._sendToWebview({
                type: 'previewGenerated',
                preview: preview,
                options: options
            });

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `❌ Preview generation failed: ${error.message}`
            });
        }
    }

    private _handleClearConversation() {
        this._conversationClient.clearHistory();
        this._sendToWebview({
            type: 'conversationCleared'
        });
    }

    private async _handleImageUpload(message: any) {
        // TODO: Implement image-based component generation
        this._sendToWebview({
            type: 'system',
            content: `📸 Image uploaded: ${message.name}. Image-based generation coming soon!`
        });
    }

    private async _initializeSession() {
        try {
            if (!this._workspaceRoot) {
                this._outputChannel.appendLine('No workspace root, creating temporary session');
                this._currentSession = await this._storage.createSession(process.cwd());
                return;
            }

            // Try to load the most recent session for this project
            const recentSessions = await this._storage.getRecentSessions(1, this._workspaceRoot);
            
            if (recentSessions.length > 0) {
                this._currentSession = recentSessions[0];
                this._outputChannel.appendLine(`Loaded recent session: ${this._currentSession.name}`);
                
                // Send session info to webview
                this._sendToWebview({
                    type: 'sessionLoaded',
                    session: {
                        id: this._currentSession.id,
                        name: this._currentSession.name,
                        messageCount: this._currentSession.metadata.messageCount
                    }
                });
            } else {
                // Create new session
                this._currentSession = await this._storage.createSession(this._workspaceRoot);
                this._outputChannel.appendLine(`Created new session: ${this._currentSession.name}`);
            }
        } catch (error: any) {
            this._outputChannel.appendLine(`Session initialization failed: ${error.message}`);
            // Create temporary session as fallback
            this._currentSession = await this._storage.createSession(this._workspaceRoot || process.cwd());
        }
    }

    private async _handleLoadSession(sessionId?: string) {
        try {
            if (!sessionId) {
                // Show session picker
                const session = await this._storage.showSessionPicker(this._workspaceRoot);
                if (!session) return;
                sessionId = session.id;
            }

            const session = await this._storage.loadSession(sessionId);
            if (!session) {
                this._sendToWebview({
                    type: 'error',
                    content: 'Session not found'
                });
                return;
            }

            this._currentSession = session;

            // Clear current chat and load session messages
            this._sendToWebview({
                type: 'conversationCleared'
            });

            // Send all messages from the session
            for (const message of session.messages) {
                this._sendToWebview({
                    type: message.role === 'user' ? 'userMessage' : 'assistantMessage',
                    content: message.content,
                    timestamp: message.timestamp,
                    metadata: message.metadata
                });
            }

            this._sendToWebview({
                type: 'sessionLoaded',
                session: {
                    id: session.id,
                    name: session.name,
                    messageCount: session.metadata.messageCount
                }
            });

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `Failed to load session: ${error.message}`
            });
        }
    }

    private async _handleSaveSession(name?: string) {
        try {
            if (!this._currentSession) {
                return;
            }

            if (name) {
                this._currentSession.name = name;
            }

            await this._storage.saveSession(this._currentSession);

            this._sendToWebview({
                type: 'system',
                content: `💾 Session saved: ${this._currentSession.name}`
            });

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `Failed to save session: ${error.message}`
            });
        }
    }

    private async _handleListSessions() {
        try {
            const sessions = await this._storage.getRecentSessions(20, this._workspaceRoot);

            this._sendToWebview({
                type: 'sessionList',
                sessions: sessions.map(session => ({
                    id: session.id,
                    name: session.name,
                    messageCount: session.metadata.messageCount,
                    lastMessageAt: session.lastMessageAt,
                    tags: session.metadata.tags || []
                }))
            });

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `Failed to load sessions: ${error.message}`
            });
        }
    }

    private async _handleDeleteSession(sessionId: string) {
        try {
            const session = await this._storage.loadSession(sessionId);
            if (!session) {
                this._sendToWebview({
                    type: 'error',
                    content: 'Session not found'
                });
                return;
            }

            const confirmed = await this._storage.showDeleteConfirmation(session);
            if (!confirmed) {
                return;
            }

            const deleted = await this._storage.deleteSession(sessionId);
            if (deleted) {
                this._sendToWebview({
                    type: 'system',
                    content: `🗑️ Deleted session: ${session.name}`
                });

                // If we deleted the current session, create a new one
                if (this._currentSession?.id === sessionId) {
                    await this._initializeSession();
                }
            }

        } catch (error: any) {
            this._sendToWebview({
                type: 'error',
                content: `Failed to delete session: ${error.message}`
            });
        }
    }

    private async _saveMessageToSession(message: ConversationMessage) {
        if (this._currentSession) {
            try {
                await this._storage.addMessage(this._currentSession.id, message);
            } catch (error: any) {
                this._outputChannel.appendLine(`Failed to save message to session: ${error.message}`);
            }
        }
    }

    private _sendToWebview(message: any) {
        this._panel.webview.postMessage(message);
    }

    private _update() {
        const webview = this._panel.webview;
        this._panel.webview.html = getEnhancedChatWebviewHtml(webview, this._extensionUri);
    }

    public dispose() {
        EnhancedPalettePanel.currentPanel = undefined;

        // Clean up resources
        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    // Public methods for external access
    public sendMessage(message: string) {
        this._sendToWebview({
            type: 'externalMessage',
            content: message
        });
    }

    public getConversationHistory(): ConversationMessage[] {
        return this._conversationClient.getConversationHistory();
    }

    public async analyzeProject(): Promise<any> {
        if (!this._projectAnalysis && this._workspaceRoot) {
            this._projectAnalysis = await this._conversationClient.analyzeProject(this._workspaceRoot);
        }
        return this._projectAnalysis;
    }
}