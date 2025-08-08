/**
 * Modern Chatbot Extension for Palette AI
 * Provides conversational AI interface with memory and session management
 */

import * as path from 'path';
import * as vscode from 'vscode';
import { SettingsCommands } from '../commands/settings-commands';
import { ConversationManager } from '../conversation-manager';
import { IntegrationManager } from '../initialization/integration-manager';
import { ModernChatbotPanel } from '../ui/modern-chatbot-panel';
import { ChatbotServer } from './chatbot-server';

let conversationManager: ConversationManager;
let chatbotServer: ChatbotServer;
let modernChatbotProvider: ModernChatbotPanel;
let settingsCommands: SettingsCommands;
let integrationManager: IntegrationManager;

export async function activate(context: vscode.ExtensionContext) {
    console.log('🎨 Palette Chatbot: Extension activation started');
    
    // Initialize integration manager (tools and MCP)
    integrationManager = IntegrationManager.getInstance();
    
    try {
        await integrationManager.initialize(context.extensionUri, context);
        console.log('🎨 Integration system initialized');
    } catch (error) {
        console.error('🎨 Failed to initialize integration system:', error);
        vscode.window.showWarningMessage(`Palette AI integration system failed to start: ${error}`);
    }
    
    // Initialize conversation manager
    conversationManager = new ConversationManager(context);
    
    // Initialize chatbot server
    chatbotServer = new ChatbotServer(context.extensionPath);
    
    // Check if user wants to use VSCode Elements UI
    const useVSCodeElements = vscode.workspace.getConfiguration('palette').get('ui.useVSCodeElements', true); // Default to true for fixed UI
    
    // Initialize modern chatbot panel provider
    if (useVSCodeElements) {
        console.log('🎨 Using VSCode Elements UI (fixed version)');
        modernChatbotProvider = new ModernChatbotPanel(context.extensionUri);
    } else {
        console.log('🎨 Using standard UI (may have errors)');
        modernChatbotProvider = new ModernChatbotPanel(context.extensionUri);
    }
    
    // Register the modern webview panel
    const modernChatbotDisposable = vscode.window.registerWebviewViewProvider(
        ModernChatbotPanel.viewType, 
        modernChatbotProvider
    );
    
    // Initialize and register settings commands
    settingsCommands = new SettingsCommands();
    settingsCommands.registerCommands(context);
    
    // Set up file operation handler for API bridge
    chatbotServer.setFileOperationHandler(async (operation) => {
        return await handleFileOperationFromAPI(operation);
    });
    
    try {
        // Register chatbot command
        const chatbotCommand = vscode.commands.registerCommand('palette.openChatbot', async () => {
            console.log('🎨 Opening Palette Chatbot');
            await openChatbotInSimpleBrowser(context);
        });

        // Register backend status command
        const backendStatusCommand = vscode.commands.registerCommand('palette.checkBackendStatus', () => {
            console.log('🎨 Checking Backend Status');
            checkBackendStatus();
        });

        // Register stop server command
        const stopServerCommand = vscode.commands.registerCommand('palette.stopChatbotServer', async () => {
            console.log('🎨 Stopping Chatbot Server');
            await stopChatbotServer();
        });

        // Register open in browser command
        const openInBrowserCommand = vscode.commands.registerCommand('palette.openChatbotInBrowser', async () => {
            console.log('🎨 Opening Chatbot directly in Browser');
            await openChatbotDirectlyInBrowser(context);
        });

        // Register start backend server command
        const startBackendCommand = vscode.commands.registerCommand('palette.startBackendServer', async () => {
            console.log('🎨 Starting Backend Server');
            await startBackendServer(context);
        });

        // Register modern chatbot command
        const modernChatbotCommand = vscode.commands.registerCommand('palette.openModernChatbot', async () => {
            console.log('🎨 Opening Modern Palette Chatbot');
            await vscode.commands.executeCommand('palette.modernChatbot.focus');
        });

        // Register enable fixed UI command
        const enableFixedUICommand = vscode.commands.registerCommand('palette.ui.enableFixedUI', async () => {
            console.log('🔧 Enabling Fixed UI (VSCode Elements)');
            await vscode.workspace.getConfiguration('palette').update('ui.useVSCodeElements', true, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage('✅ Fixed UI enabled! Please reload window for changes to take effect.', 'Reload').then(selection => {
                if (selection === 'Reload') {
                    vscode.commands.executeCommand('workbench.action.reloadWindow');
                }
            });
        });
        
        
        context.subscriptions.push(
            chatbotCommand, 
            backendStatusCommand, 
            stopServerCommand, 
            openInBrowserCommand, 
            startBackendCommand, 
            modernChatbotCommand,
            enableFixedUICommand,
            modernChatbotDisposable
        );
        
        console.log('🎨 Palette Chatbot: Commands registered successfully');
        vscode.window.showInformationMessage('🎨 Palette Chatbot activated');
        
    } catch (error) {
        console.error('🎨 Palette Chatbot: Activation failed:', error);
        vscode.window.showErrorMessage(`Palette Chatbot activation failed: ${error}`);
    }
}

async function openChatbotInSimpleBrowser(context: vscode.ExtensionContext) {
    console.log('🎨 Opening Palette Chatbot in VSCode Simple Browser');
    
    try {
        // Check if the HTML file exists
        const chatbotHtmlPath = vscode.Uri.joinPath(context.extensionUri, 'chatbot', 'index.html');
        try {
            await vscode.workspace.fs.stat(chatbotHtmlPath);
        } catch (error) {
            console.error('🎨 Chatbot HTML file not found:', chatbotHtmlPath.fsPath);
            vscode.window.showErrorMessage(
                'Palette AI Chatbot HTML file not found. Please ensure the chatbot folder exists in the extension directory.'
            );
            return;
        }

        // Start the local HTTP server if not already running
        let serverUrl: string;
        if (!chatbotServer.isRunning()) {
            console.log('🎨 Starting chatbot server...');
            vscode.window.showInformationMessage('🎨 Starting Palette AI Chatbot server...');
            
            try {
                serverUrl = await chatbotServer.start();
                console.log('🎨 Chatbot server started:', serverUrl);
            } catch (error) {
                console.error('🎨 Failed to start chatbot server:', error);
                vscode.window.showErrorMessage(`Failed to start chatbot server: ${error}`);
                return;
            }
        } else {
            serverUrl = chatbotServer.getUrl()!;
            console.log('🎨 Using existing chatbot server:', serverUrl);
        }

        // Get VSCode settings and pass to chatbot
        const config = vscode.workspace.getConfiguration('palette');
        const apiKey = config.get<string>('openaiApiKey') || '';
    const model = config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
        const backendUrl = config.get<string>('backendUrl') || 'http://localhost:8765';
        
        // Build URL with configuration parameters
        const configParams = new URLSearchParams({
            apiKey: apiKey,
            model: model,
            backendUrl: backendUrl,
            timestamp: Date.now().toString()
        });
        const chatbotUrl = `${serverUrl}?${configParams.toString()}`;
        
        // Open in VSCode Simple Browser with message handling
        console.log('🎨 Opening Simple Browser with configured URL');
        
        // Set up global message listener for file operations
        setupFileOperationListener();
        
        try {
            await vscode.commands.executeCommand('simpleBrowser.show', chatbotUrl);
            console.log('🎨 Simple Browser opened successfully');
            
            // Give user option to switch to external browser if Simple Browser has issues
            vscode.window.showInformationMessage(
                '🎨 Palette AI Chatbot opened in VSCode tab!',
                'Open in Browser Instead',
                'Show Backend Status'
            ).then(selection => {
                if (selection === 'Open in Browser Instead') {
                    vscode.env.openExternal(vscode.Uri.parse(chatbotUrl));
                } else if (selection === 'Show Backend Status') {
                    checkBackendStatus();
                }
            });
            
        } catch (error) {
            console.error('🎨 Failed to open Simple Browser:', error);
            
            // Offer choice when Simple Browser fails
            const choice = await vscode.window.showWarningMessage(
                '🎨 VSCode Simple Browser had issues. Would you like to open in your regular browser instead?',
                'Open in Browser',
                'Try Again',
                'Cancel'
            );
            
            if (choice === 'Open in Browser') {
                const externalOpened = await vscode.env.openExternal(vscode.Uri.parse(chatbotUrl));
                if (externalOpened) {
                    vscode.window.showInformationMessage('🎨 Palette AI Chatbot opened in your browser!');
                } else {
                    vscode.window.showErrorMessage('Failed to open chatbot in browser');
                }
            } else if (choice === 'Try Again') {
                // Retry Simple Browser
                try {
                    await vscode.commands.executeCommand('simpleBrowser.show', chatbotUrl);
                    vscode.window.showInformationMessage('🎨 Simple Browser retry successful!');
                } catch (retryError) {
                    vscode.window.showErrorMessage('Simple Browser still not working. Try "Open in Browser" option.');
                }
            }
        }
        
    } catch (error) {
        console.error('🎨 Error opening chatbot:', error);
        vscode.window.showErrorMessage(`Failed to open chatbot: ${error}`);
    }
}

async function checkBackendStatus() {
    console.log('🎨 Checking backend status');
    
    try {
        const { AIIntegrationService } = await import('../ai-integration');
        const status = await AIIntegrationService.getBackendStatus();
        
        if (status.connected) {
            vscode.window.showInformationMessage(
                `✅ Palette Backend: Connected${status.version ? ` (v${status.version})` : ''}`,
                'Open Chatbot'
            ).then(selection => {
                if (selection === 'Open Chatbot') {
                    vscode.commands.executeCommand('palette.openChatbot');
                }
            });
        } else {
            vscode.window.showWarningMessage(
                `⚠️ Palette Backend: Disconnected (${status.error})`,
                'Start Backend',
                'Help'
            ).then(selection => {
                if (selection === 'Start Backend') {
                    vscode.commands.executeCommand('palette.startBackendServer');
                } else if (selection === 'Help') {
                    vscode.env.openExternal(vscode.Uri.parse('https://github.com/your-palette-repo#backend-setup'));
                }
            });
        }
    } catch (error) {
        console.error('🎨 Error checking backend status:', error);
        vscode.window.showErrorMessage(`Failed to check backend status: ${error}`);
    }
}

async function stopChatbotServer() {
    console.log('🎨 Stopping chatbot server');
    
    if (!chatbotServer || !chatbotServer.isRunning()) {
        vscode.window.showInformationMessage('🎨 Chatbot server is not currently running');
        return;
    }
    
    try {
        await chatbotServer.stop();
        vscode.window.showInformationMessage('🎨 Chatbot server stopped successfully');
        console.log('🎨 Chatbot server stopped via command');
    } catch (error) {
        console.error('🎨 Error stopping chatbot server:', error);
        vscode.window.showErrorMessage(`Failed to stop chatbot server: ${error}`);
    }
}

async function openChatbotDirectlyInBrowser(context: vscode.ExtensionContext) {
    console.log('🎨 Opening Palette Chatbot directly in browser');
    
    try {
        // Check if the HTML file exists
        const chatbotHtmlPath = vscode.Uri.joinPath(context.extensionUri, 'chatbot', 'index.html');
        try {
            await vscode.workspace.fs.stat(chatbotHtmlPath);
        } catch (error) {
            console.error('🎨 Chatbot HTML file not found:', chatbotHtmlPath.fsPath);
            vscode.window.showErrorMessage(
                'Palette AI Chatbot HTML file not found. Please ensure the chatbot folder exists in the extension directory.'
            );
            return;
        }

        // Start the local HTTP server if not already running
        let serverUrl: string;
        if (!chatbotServer.isRunning()) {
            console.log('🎨 Starting chatbot server for browser...');
            
            try {
                serverUrl = await chatbotServer.start();
                console.log('🎨 Chatbot server started for browser:', serverUrl);
            } catch (error) {
                console.error('🎨 Failed to start chatbot server:', error);
                vscode.window.showErrorMessage(`Failed to start chatbot server: ${error}`);
                return;
            }
        } else {
            serverUrl = chatbotServer.getUrl()!;
            console.log('🎨 Using existing chatbot server for browser:', serverUrl);
        }

        // Get VSCode settings and pass to chatbot
        const config = vscode.workspace.getConfiguration('palette');
        const apiKey = config.get<string>('openaiApiKey') || '';
    const model = config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
        const backendUrl = config.get<string>('backendUrl') || 'http://localhost:8765';
        
        // Build URL with configuration parameters
        const configParams = new URLSearchParams({
            apiKey: apiKey,
            model: model,
            backendUrl: backendUrl,
            timestamp: Date.now().toString()
        });
        const chatbotUrl = `${serverUrl}?${configParams.toString()}`;

        // Open directly in external browser
        console.log('🎨 Opening browser with configured URL');
        const opened = await vscode.env.openExternal(vscode.Uri.parse(chatbotUrl));
        
        if (opened) {
            vscode.window.showInformationMessage(
                '🎨 Palette AI Chatbot opened in your browser!',
                'Show Backend Status'
            ).then(selection => {
                if (selection === 'Show Backend Status') {
                    checkBackendStatus();
                }
            });
        } else {
            vscode.window.showErrorMessage('Failed to open Palette AI Chatbot in browser');
        }
        
    } catch (error) {
        console.error('🎨 Error opening chatbot in browser:', error);
        vscode.window.showErrorMessage(`Failed to open chatbot: ${error}`);
    }
}

async function startBackendServer(context: vscode.ExtensionContext) {
    console.log('🎨 Starting Palette Backend Server');
    
    try {
        // Show progress indicator
        const startupResult = await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "🎨 Starting Palette Backend Server...",
            cancellable: true
        }, async (progress, token) => {
            
            progress.report({ increment: 10, message: "Finding Palette project..." });
            
            // Check if we can find the Python startup script
            const extensionDir = context.extensionPath;
            const startupScript = vscode.Uri.file(`${extensionDir}/scripts/start-backend.py`);
            
            try {
                await vscode.workspace.fs.stat(startupScript);
            } catch (error) {
                throw new Error(`Backend startup script not found at: ${startupScript.fsPath}`);
            }
            
            progress.report({ increment: 20, message: "Found startup script..." });
            
            // Try to run the Python script
            const terminal = vscode.window.createTerminal({
                name: 'Palette Backend Server',
                cwd: extensionDir
            });
            
            progress.report({ increment: 50, message: "Starting server in terminal..." });
            
            // Run the startup script
            terminal.sendText(`python3 scripts/start-backend.py`);
            terminal.show();
            
            progress.report({ increment: 80, message: "Server starting..." });
            
            // Wait a bit for the server to start
            await new Promise(resolve => setTimeout(resolve, 3000));
            
            progress.report({ increment: 100, message: "Server startup initiated!" });
            
            return true;
        });
        
        if (startupResult) {
            // Check backend status after a few seconds
            setTimeout(async () => {
                const choice = await vscode.window.showInformationMessage(
                    '🎨 Palette Backend Server started in terminal!',
                    'Check Status',
                    'Open Chatbot'
                );
                
                if (choice === 'Check Status') {
                    await checkBackendStatus();
                } else if (choice === 'Open Chatbot') {
                    await vscode.commands.executeCommand('palette.openChatbot');
                }
            }, 5000);
        }
        
    } catch (error) {
        console.error('🎨 Error starting backend server:', error);
        
        // Show error with helpful options
        const choice = await vscode.window.showErrorMessage(
            `Failed to start backend server: ${error}`,
            'Manual Instructions',
            'Open Scripts Folder'
        );
        
        if (choice === 'Manual Instructions') {
            vscode.window.showInformationMessage(
                `To manually start the backend:\n\n1. Open terminal in Palette project root\n2. Run: source venv/bin/activate (or venv\\Scripts\\activate on Windows)\n3. Run: python3 -m palette.server.main\n4. Server should start on http://localhost:8765`
            );
        } else if (choice === 'Open Scripts Folder') {
            const scriptsFolder = vscode.Uri.file(`${context.extensionPath}/scripts`);
            await vscode.commands.executeCommand('vscode.openFolder', scriptsFolder);
        }
    }
}

/**
 * Set up message listening for file operations from React chatbot
 * Since Simple Browser doesn't support direct message passing,
 * we'll use VSCode commands as communication bridge
 */
function setupFileOperationListener() {
    console.log('🔗 Setting up file operation listener');
    
    // Register a command that the React app can trigger
    const fileOperationCommand = vscode.commands.registerCommand('palette.createFileFromChatbot', async (fileData) => {
        console.log('📁 Received file creation request:', fileData);
        await handleFileCreation(fileData);
    });
}

/**
 * Handle file creation from chatbot
 */
async function handleFileCreation(fileData: {
    code: string;
    language: string;
    filePath: string;
    timestamp: number;
}) {
    try {
        console.log('🎨 Creating file:', fileData.filePath);
        
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder open. Please open a project first.');
            return;
        }

        // Clean and validate file path
        const cleanPath = fileData.filePath.replace(/^\/+/, ''); // Remove leading slashes
        const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, cleanPath);
        
        // Ensure directory exists
        const directory = vscode.Uri.joinPath(workspaceFolder.uri, path.dirname(cleanPath));
        try {
            await vscode.workspace.fs.createDirectory(directory);
        } catch (error) {
            // Directory might already exist, that's okay
        }

        // Check if file already exists
        let shouldWrite = true;
        try {
            await vscode.workspace.fs.stat(fullPath);
            // File exists, ask for confirmation
            const choice = await vscode.window.showWarningMessage(
                `File "${cleanPath}" already exists. Do you want to overwrite it?`,
                'Overwrite',
                'Cancel'
            );
            shouldWrite = choice === 'Overwrite';
        } catch {
            // File doesn't exist, proceed
        }

        if (shouldWrite) {
            // Write the file
            const content = Buffer.from(fileData.code, 'utf8');
            await vscode.workspace.fs.writeFile(fullPath, content);
            
            // Show success message with options
            const result = await vscode.window.showInformationMessage(
                `✅ Created file: ${cleanPath}`,
                'Open File',
                'Show in Explorer'
            );
            
            if (result === 'Open File') {
                const document = await vscode.workspace.openTextDocument(fullPath);
                await vscode.window.showTextDocument(document);
            } else if (result === 'Show in Explorer') {
                await vscode.commands.executeCommand('revealFileInOS', fullPath);
            }

            // Auto-route for page components (similar to extension-diagnostic.ts)
            if (cleanPath.includes('/pages/') && fileData.code.includes('export')) {
                await handleAutoRouting(fileData, cleanPath);
            }
        }
        
    } catch (error) {
        console.error('🎨 Error creating file:', error);
        vscode.window.showErrorMessage(`Failed to create file: ${error}`);
    }
}

/**
 * Handle automatic routing for page components
 */
async function handleAutoRouting(fileData: {code: string, language: string}, filePath: string) {
    try {
        console.log('🔀 Checking for auto-routing opportunity');
        
        // Extract component name from code (same logic as extension-diagnostic.ts)
        const componentName = extractComponentName(fileData.code) || 'UnknownComponent';
        
        // Check if this looks like a page component
        if (filePath.includes('/pages/') && componentName.includes('Page')) {
            const choice = await vscode.window.showInformationMessage(
                `Would you like to add a route for ${componentName}?`,
                'Add Route',
                'Skip'
            );
            
            if (choice === 'Add Route') {
                // This would integrate with the routing system
                // For now, just show info about manual routing
                vscode.window.showInformationMessage(
                    `To add routing for ${componentName}:\n1. Import in your App.tsx\n2. Add <Route> element\n3. Update navigation`
                );
            }
        }
    } catch (error) {
        console.log('🔀 Auto-routing failed:', error);
    }
}

/**
 * Handle file operations from API bridge
 */
async function handleFileOperationFromAPI(operation: any): Promise<any> {
    try {
        console.log('🎨 API File Operation:', operation.type, operation.path || 'N/A');

        switch (operation.type) {
            case 'create':
                return await handleCreateFileFromAPI(operation);
            
            case 'read':
                return await handleReadFileFromAPI(operation);
            
            case 'list':
                return await handleListFilesFromAPI(operation);
            
            case 'workspace-info':
                return await handleWorkspaceInfoFromAPI();
            
            default:
                throw new Error(`Unknown operation type: ${operation.type}`);
        }
    } catch (error: any) {
        console.error('🎨 API File Operation Error:', error);
        throw error; // Re-throw for API error handling
    }
}

/**
 * Handle file creation from API
 */
async function handleCreateFileFromAPI(operation: { path: string; content: string; language: string }): Promise<any> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        throw new Error('No workspace folder open. Please open a project first.');
    }

    // Sanitize and validate path
    const cleanPath = operation.path.replace(/^\/+/, '').replace(/\.\./g, '');
    const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, cleanPath);
    
    // Security: Ensure path is within workspace
    if (!fullPath.fsPath.startsWith(workspaceFolder.uri.fsPath)) {
        throw new Error('File path must be within workspace boundary');
    }

    // Ensure directory exists
    const directory = vscode.Uri.joinPath(workspaceFolder.uri, path.dirname(cleanPath));
    try {
        await vscode.workspace.fs.createDirectory(directory);
    } catch (error) {
        // Directory might already exist, that's okay
    }

    // Check if file already exists
    let fileExists = false;
    try {
        await vscode.workspace.fs.stat(fullPath);
        fileExists = true;
    } catch {
        // File doesn't exist
    }

    // Write the file
    const content = Buffer.from(operation.content, 'utf8');
    await vscode.workspace.fs.writeFile(fullPath, content);
    
    // Show success notification
    const action = fileExists ? 'Updated' : 'Created';
    const result = await vscode.window.showInformationMessage(
        `✅ ${action} file: ${cleanPath}`,
        'Open File',
        'Show in Explorer'
    );
    
    if (result === 'Open File') {
        const document = await vscode.workspace.openTextDocument(fullPath);
        await vscode.window.showTextDocument(document);
    } else if (result === 'Show in Explorer') {
        await vscode.commands.executeCommand('revealFileInOS', fullPath);
    }

    // Auto-route for page components
    if (cleanPath.includes('/pages/') && operation.content.includes('export')) {
        setTimeout(() => handleAutoRouting({ 
            code: operation.content, 
            language: operation.language 
        }, cleanPath), 1000);
    }

    return {
        path: cleanPath,
        fullPath: fullPath.fsPath,
        action,
        fileExists: fileExists
    };
}

/**
 * Handle reading file from API
 */
async function handleReadFileFromAPI(operation: { path: string }): Promise<any> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        throw new Error('No workspace folder open');
    }

    const cleanPath = operation.path.replace(/^\/+/, '').replace(/\.\./g, '');
    const fullPath = vscode.Uri.joinPath(workspaceFolder.uri, cleanPath);

    try {
        const content = await vscode.workspace.fs.readFile(fullPath);
        return {
            path: cleanPath,
            content: Buffer.from(content).toString('utf8'),
            size: content.length
        };
    } catch (error) {
        throw new Error(`Failed to read file: ${cleanPath}`);
    }
}

/**
 * Handle listing files from API
 */
async function handleListFilesFromAPI(operation: any): Promise<any> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        throw new Error('No workspace folder open');
    }

    try {
        const srcDir = vscode.Uri.joinPath(workspaceFolder.uri, 'src');
        const entries = await vscode.workspace.fs.readDirectory(srcDir);
        
        const files: any[] = [];
        for (const [name, type] of entries) {
            if (type === vscode.FileType.File && (name.endsWith('.tsx') || name.endsWith('.ts') || name.endsWith('.jsx') || name.endsWith('.js'))) {
                files.push({
                    name,
                    path: `src/${name}`,
                    type: 'file'
                });
            } else if (type === vscode.FileType.Directory) {
                files.push({
                    name,
                    path: `src/${name}`,
                    type: 'directory'
                });
            }
        }
        
        return { files };
    } catch (error) {
        return { files: [] };
    }
}

/**
 * Handle workspace info from API
 */
async function handleWorkspaceInfoFromAPI(): Promise<any> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        throw new Error('No workspace folder open');
    }

    return {
        name: workspaceFolder.name,
        path: workspaceFolder.uri.fsPath,
        folders: vscode.workspace.workspaceFolders?.map(folder => ({
            name: folder.name,
            path: folder.uri.fsPath
        })) || []
    };
}

/**
 * Extract component name from generated code
 */
function extractComponentName(code: string): string | null {
    const patterns = [
        /export\s+const\s+(\w+):\s*React\.FC/,
        /export\s+const\s+(\w+):\s*FC/,
        /const\s+(\w+):\s*React\.FC/,
        /export\s+default\s+function\s+(\w+)/,
        /export\s+function\s+(\w+)/,
        /export\s+const\s+(\w+)\s*=/,
        /function\s+(\w+)\s*\(/,
        /const\s+(\w+)\s*=\s*\(/
    ];
    
    for (const pattern of patterns) {
        const match = code.match(pattern);
        if (match && match[1]) {
            return match[1];
        }
    }
    
    return null;
}


export async function deactivate() {
    console.log('🎨 Palette Chatbot: Extension deactivation started');
    
    // Shutdown integration system
    if (integrationManager) {
        console.log('🎨 Shutting down integration system...');
        try {
            await integrationManager.shutdown();
            console.log('🎨 Integration system shutdown successfully');
        } catch (error) {
            console.error('🎨 Error shutting down integration system:', error);
        }
    }
    
    // Stop the chatbot server if running
    if (chatbotServer && chatbotServer.isRunning()) {
        console.log('🎨 Stopping chatbot server...');
        try {
            await chatbotServer.stop();
            console.log('🎨 Chatbot server stopped successfully');
        } catch (error) {
            console.error('🎨 Error stopping chatbot server:', error);
        }
    }
    
    console.log('🎨 Palette Chatbot: Extension deactivated');
}