import * as vscode from 'vscode';
import { ComponentGenerator } from './componentGenerator';
import { CodebaseAnalyzer } from './codebaseAnalyzer';
import { CodebaseIndexer } from './codebaseIndexer';
import { ContextManager } from './contextManager';
import { ClaudeIntegration } from './claudeIntegration';
import { 
    ContextRequest, 
    AIRequest, 
    ClaudeConfig,
    ExtensionConfig 
} from './types';

let componentGenerator: ComponentGenerator;
let codebaseAnalyzer: CodebaseAnalyzer;
let codebaseIndexer: CodebaseIndexer;
let contextManager: ContextManager;
let claudeIntegration: ClaudeIntegration;
let extensionConfig: ExtensionConfig;

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 UI Copilot with Codebase Awareness is now active!');

    // Initialize configuration
    initializeConfiguration();

    // Initialize core services
    initializeServices();

    // Register all commands
    registerCommands(context);

    // Initialize workspace indexing
    initializeWorkspaceIndexing();

    console.log('✅ UI Copilot fully initialized with codebase awareness');
}

/**
 * Initialize extension configuration from VS Code settings
 */
function initializeConfiguration() {
    const config = vscode.workspace.getConfiguration('ui-copilot');
    
    const claudeConfig: ClaudeConfig = {
        apiKey: config.get<string>('claudeApiKey') || '',
        model: config.get<string>('claudeModel') || 'claude-3-sonnet-20240229',
        maxTokens: config.get<number>('maxTokens') || 4000,
        temperature: config.get<number>('temperature') || 0.3
    };

    extensionConfig = {
        claude: claudeConfig,
        indexing: {
            enabled: config.get<boolean>('indexing.enabled') ?? true,
            maxFileSize: config.get<number>('indexing.maxFileSize') ?? 100 * 1024,
            excludePatterns: config.get<string[]>('indexing.excludePatterns') ?? ['node_modules', '.git', 'dist', 'build'],
            includePatterns: config.get<string[]>('indexing.includePatterns') ?? ['**/*.{ts,tsx,js,jsx}'],
            watchForChanges: config.get<boolean>('indexing.watchForChanges') ?? true,
            debounceTime: config.get<number>('indexing.debounceTime') ?? 500
        },
        context: {
            maxTokens: config.get<number>('context.maxTokens') ?? 12000,
            maxFiles: config.get<number>('context.maxFiles') ?? 20,
            maxChunks: config.get<number>('context.maxChunks') ?? 50,
            relevanceThreshold: config.get<number>('context.relevanceThreshold') ?? 0.3,
            includeRelatedFiles: config.get<boolean>('context.includeRelatedFiles') ?? true,
            includeDependencies: config.get<boolean>('context.includeDependencies') ?? true
        },
        performance: {
            cacheEnabled: config.get<boolean>('performance.cacheEnabled') ?? true,
            cacheTTL: config.get<number>('performance.cacheTTL') ?? 3600000, // 1 hour
            maxCacheSize: config.get<number>('performance.maxCacheSize') ?? 100 * 1024 * 1024, // 100MB
            concurrentLimit: config.get<number>('performance.concurrentLimit') ?? 10,
            timeoutMs: config.get<number>('performance.timeoutMs') ?? 30000
        },
        features: {
            autoCompletion: config.get<boolean>('features.autoCompletion') ?? true,
            codeExplanation: config.get<boolean>('features.codeExplanation') ?? true,
            refactoring: config.get<boolean>('features.refactoring') ?? true,
            debugging: config.get<boolean>('features.debugging') ?? true,
            codeGeneration: config.get<boolean>('features.codeGeneration') ?? true
        }
    };
}

/**
 * Initialize all core services
 */
function initializeServices() {
    try {
        // Initialize existing services
        componentGenerator = new ComponentGenerator();
        codebaseAnalyzer = new CodebaseAnalyzer();
        
        // Initialize new codebase-aware services
        codebaseIndexer = new CodebaseIndexer();
        contextManager = new ContextManager(codebaseIndexer, extensionConfig.context.maxTokens, extensionConfig.context.maxFiles);
        
        // Initialize Claude integration if API key is provided
        if (extensionConfig.claude.apiKey) {
            claudeIntegration = new ClaudeIntegration(extensionConfig.claude);
            console.log('✅ Claude API integration initialized');
        } else {
            console.log('⚠️ Claude API key not configured - some features will be limited');
        }

        // Set up event listeners
        setupEventListeners();
        
        console.log('✅ All services initialized successfully');
    } catch (error) {
        console.error('❌ Failed to initialize services:', error);
        vscode.window.showErrorMessage(`Failed to initialize UI Copilot: ${error}`);
    }
}

/**
 * Set up event listeners for real-time updates
 */
function setupEventListeners() {
    // Listen for codebase indexer events
    codebaseIndexer.on('indexingStarted', () => {
        vscode.window.setStatusBarMessage('$(sync~spin) Indexing codebase...', 2000);
    });

    codebaseIndexer.on('indexingCompleted', (index) => {
        const message = `✅ Indexed ${index.indexedFiles} files with ${index.symbols.size} symbols`;
        vscode.window.setStatusBarMessage(message, 3000);
        console.log(message);
    });

    codebaseIndexer.on('fileIndexed', (filePath, processed, total) => {
        if (processed % 10 === 0) { // Update every 10 files to avoid spam
            vscode.window.setStatusBarMessage(`$(sync~spin) Indexing: ${processed}/${total} files`, 1000);
        }
    });

    codebaseIndexer.on('indexingError', (error) => {
        console.error('Indexing error:', error);
        vscode.window.showWarningMessage(`Indexing warning: ${error.message}`);
    });

    // Listen for configuration changes
    vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('ui-copilot')) {
            console.log('🔄 Configuration changed, reinitializing...');
            initializeConfiguration();
            // Optionally reinitialize services that depend on config
        }
    });
}

/**
 * Register all VS Code commands
 */
function registerCommands(context: vscode.ExtensionContext) {
    const commands = [
        // Existing commands
        vscode.commands.registerCommand('ui-copilot.generateComponent', handleGenerateComponent),
        vscode.commands.registerCommand('ui-copilot.iterateComponent', handleIterateComponent),
        
        // New codebase-aware commands
        vscode.commands.registerCommand('ui-copilot.explainCode', handleExplainCode),
        vscode.commands.registerCommand('ui-copilot.refactorCode', handleRefactorCode),
        vscode.commands.registerCommand('ui-copilot.completeCode', handleCompleteCode),
        vscode.commands.registerCommand('ui-copilot.debugCode', handleDebugCode),
        vscode.commands.registerCommand('ui-copilot.searchCodebase', handleSearchCodebase),
        vscode.commands.registerCommand('ui-copilot.findSimilar', handleFindSimilar),
        vscode.commands.registerCommand('ui-copilot.analyzeProject', handleAnalyzeProject),
        vscode.commands.registerCommand('ui-copilot.reindexWorkspace', handleReindexWorkspace),
        vscode.commands.registerCommand('ui-copilot.showIndexStatus', handleShowIndexStatus),
        vscode.commands.registerCommand('ui-copilot.configureExtension', handleConfigureExtension)
    ];

    context.subscriptions.push(...commands);
    console.log(`✅ Registered ${commands.length} commands`);
}

/**
 * Initialize workspace indexing
 */
async function initializeWorkspaceIndexing() {
    if (!extensionConfig.indexing.enabled) {
        console.log('📝 Workspace indexing disabled in configuration');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        console.log('📝 No workspace folder found, skipping indexing');
        return;
    }

    try {
        console.log('🔍 Starting workspace indexing...');
        
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Indexing workspace for AI assistance",
            cancellable: false
        }, async (progress) => {
            await codebaseIndexer.indexWorkspace(workspaceFolder.uri.fsPath, progress);
        });
        
        console.log('✅ Workspace indexing completed');
    } catch (error) {
        console.error('❌ Workspace indexing failed:', error);
        vscode.window.showWarningMessage(`Workspace indexing failed: ${error}. Some features may be limited.`);
    }
}

// =====================================================
// COMMAND HANDLERS
// =====================================================

/**
 * Enhanced component generation with full codebase context
 */
async function handleGenerateComponent() {
    if (!extensionConfig.features.codeGeneration) {
        vscode.window.showInformationMessage('Code generation feature is disabled');
        return;
    }

    try {
        // Get user input for what they want to build
        const prompt = await vscode.window.showInputBox({
            placeHolder: 'Describe the component you want to generate (e.g., "user profile card with avatar and bio")',
            prompt: 'What UI component would you like to generate?'
        });

        if (!prompt) return;

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating component with codebase awareness...",
            cancellable: false
        }, async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('Please open a file to insert the component');
                return;
            }

            // Use new codebase-aware approach if Claude is available
            if (claudeIntegration) {
                const contextRequest: ContextRequest = {
                    currentFile: editor.document.fileName,
                    cursorPosition: editor.selection.active,
                    query: prompt,
                    responseType: 'generation',
                    language: editor.document.languageId
                };

                const context = await contextManager.buildContext(contextRequest);
                const aiRequest: AIRequest = {
                    type: 'generation',
                    query: prompt,
                    language: editor.document.languageId
                };

                const response = await claudeIntegration.processRequest(aiRequest, context);
                
                await editor.edit(editBuilder => {
                    const position = editor.selection.active;
                    editBuilder.insert(position, response.content);
                });

                vscode.window.showInformationMessage(
                    `Component generated with ${context.metadata.filesIncluded} context files (${Math.round(response.confidence * 100)}% confidence)`
                );
            } else {
                // Fallback to existing approach
                const workspaceInfo = await codebaseAnalyzer.analyzeWorkspace();
                const generatedCode = await componentGenerator.generateComponent(prompt, workspaceInfo);
                
                await editor.edit(editBuilder => {
                    const position = editor.selection.active;
                    editBuilder.insert(position, generatedCode);
                });

                vscode.window.showInformationMessage('Component generated successfully!');
            }

            await vscode.commands.executeCommand('editor.action.formatDocument');
        });

    } catch (error) {
        vscode.window.showErrorMessage(`Error generating component: ${error}`);
        console.error('Component generation error:', error);
    }
}

/**
 * Explain selected code with full codebase context
 */
async function handleExplainCode() {
    if (!extensionConfig.features.codeExplanation) {
        vscode.window.showInformationMessage('Code explanation feature is disabled');
        return;
    }

    if (!claudeIntegration) {
        vscode.window.showErrorMessage('Claude API not configured. Please set your API key in settings.');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please open a file and select code to explain');
        return;
    }

    const selectedText = editor.document.getText(editor.selection);
    if (!selectedText) {
        vscode.window.showErrorMessage('Please select the code you want explained');
        return;
    }

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing code with codebase context...",
            cancellable: false
        }, async () => {
            const contextRequest: ContextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                responseType: 'explanation',
                language: editor.document.languageId
            };

            const context = await contextManager.buildContext(contextRequest);
            const aiRequest: AIRequest = {
                type: 'explanation',
                query: 'Explain this code',
                selectedCode: selectedText,
                language: editor.document.languageId
            };

            const response = await claudeIntegration.processRequest(aiRequest, context);
            
            // Show explanation in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: response.content,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Error explaining code: ${error}`);
        console.error('Code explanation error:', error);
    }
}

/**
 * Refactor selected code with codebase awareness
 */
async function handleRefactorCode() {
    if (!extensionConfig.features.refactoring) {
        vscode.window.showInformationMessage('Refactoring feature is disabled');
        return;
    }

    if (!claudeIntegration) {
        vscode.window.showErrorMessage('Claude API not configured. Please set your API key in settings.');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please open a file and select code to refactor');
        return;
    }

    const selectedText = editor.document.getText(editor.selection);
    if (!selectedText) {
        vscode.window.showErrorMessage('Please select the code you want to refactor');
        return;
    }

    const refactorGoal = await vscode.window.showInputBox({
        placeHolder: 'How would you like to refactor this code? (e.g., "improve performance", "make more readable")',
        prompt: 'Describe your refactoring goal'
    });

    if (!refactorGoal) return;

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Refactoring code with codebase awareness...",
            cancellable: false
        }, async () => {
            const contextRequest: ContextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                query: refactorGoal,
                responseType: 'refactor',
                language: editor.document.languageId
            };

            const context = await contextManager.buildContext(contextRequest);
            const aiRequest: AIRequest = {
                type: 'refactor',
                query: refactorGoal,
                selectedCode: selectedText,
                language: editor.document.languageId
            };

            const response = await claudeIntegration.processRequest(aiRequest, context);
            
            // Replace selected code with refactored version
            await editor.edit(editBuilder => {
                editBuilder.replace(editor.selection, response.content);
            });

            await vscode.commands.executeCommand('editor.action.formatDocument');
            vscode.window.showInformationMessage('Code refactored successfully!');
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Error refactoring code: ${error}`);
        console.error('Code refactoring error:', error);
    }
}

/**
 * Complete code at cursor with codebase context
 */
async function handleCompleteCode() {
    if (!extensionConfig.features.autoCompletion) {
        vscode.window.showInformationMessage('Auto-completion feature is disabled');
        return;
    }

    if (!claudeIntegration) {
        vscode.window.showErrorMessage('Claude API not configured. Please set your API key in settings.');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please open a file to complete code');
        return;
    }

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Completing code with codebase context...",
            cancellable: false
        }, async () => {
            const contextRequest: ContextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                responseType: 'completion',
                language: editor.document.languageId
            };

            const context = await contextManager.buildContext(contextRequest);
            const aiRequest: AIRequest = {
                type: 'completion',
                query: 'Complete this code',
                language: editor.document.languageId,
                cursorPosition: editor.selection.active
            };

            const response = await claudeIntegration.processRequest(aiRequest, context);
            
            // Insert completion at cursor
            await editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.active, response.content);
            });

            vscode.window.showInformationMessage('Code completed successfully!');
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Error completing code: ${error}`);
        console.error('Code completion error:', error);
    }
}

/**
 * Debug code with AI assistance
 */
async function handleDebugCode() {
    if (!extensionConfig.features.debugging) {
        vscode.window.showInformationMessage('Debugging feature is disabled');
        return;
    }

    if (!claudeIntegration) {
        vscode.window.showErrorMessage('Claude API not configured. Please set your API key in settings.');
        return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please open a file to debug');
        return;
    }

    const selectedText = editor.document.getText(editor.selection);
    const debugQuery = await vscode.window.showInputBox({
        placeHolder: 'Describe the issue you\'re experiencing (e.g., "function returns undefined", "infinite loop")',
        prompt: 'What debugging help do you need?'
    });

    if (!debugQuery) return;

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing code for debugging...",
            cancellable: false
        }, async () => {
            const contextRequest: ContextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                query: debugQuery,
                responseType: 'debug',
                language: editor.document.languageId
            };

            const context = await contextManager.buildContext(contextRequest);
            const aiRequest: AIRequest = {
                type: 'debug',
                query: debugQuery,
                selectedCode: selectedText,
                language: editor.document.languageId
            };

            const response = await claudeIntegration.processRequest(aiRequest, context);
            
            // Show debugging help in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: response.content,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Error debugging code: ${error}`);
        console.error('Code debugging error:', error);
    }
}

/**
 * Search codebase for patterns, symbols, or text
 */
async function handleSearchCodebase() {
    const query = await vscode.window.showInputBox({
        placeHolder: 'Search for functions, classes, patterns, or text...',
        prompt: 'What would you like to search for in the codebase?'
    });

    if (!query) return;

    try {
        const results = codebaseIndexer.searchFiles(query);
        
        if (results.length === 0) {
            vscode.window.showInformationMessage('No results found');
            return;
        }

        // Show results in quick pick
        const items = results.slice(0, 20).map(file => ({
            label: file.path,
            description: `${file.symbols.length} symbols, ${file.lineCount} lines`,
            detail: file.chunks.length > 0 ? file.chunks[0].content.substring(0, 100) + '...' : '',
            file
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: `Found ${results.length} files matching "${query}"`,
            matchOnDescription: true,
            matchOnDetail: true
        });

        if (selected) {
            const doc = await vscode.workspace.openTextDocument(selected.file.absolutePath);
            await vscode.window.showTextDocument(doc);
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Search error: ${error}`);
        console.error('Codebase search error:', error);
    }
}

/**
 * Find files similar to current file
 */
async function handleFindSimilar() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please open a file to find similar files');
        return;
    }

    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const relativePath = vscode.workspace.asRelativePath(editor.document.fileName);
        const relatedFiles = codebaseIndexer.getRelatedFiles(relativePath, 15);
        
        if (relatedFiles.length === 0) {
            vscode.window.showInformationMessage('No similar files found');
            return;
        }

        const items = relatedFiles.map(file => ({
            label: file.path,
            description: `${file.symbols.length} symbols, ${file.imports.length} imports`,
            detail: `Language: ${file.language}, Size: ${file.lineCount} lines`,
            file
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: `Found ${relatedFiles.length} similar files`,
            matchOnDescription: true
        });

        if (selected) {
            const doc = await vscode.workspace.openTextDocument(selected.file.absolutePath);
            await vscode.window.showTextDocument(doc);
        }
    } catch (error) {
        vscode.window.showErrorMessage(`Error finding similar files: ${error}`);
        console.error('Find similar error:', error);
    }
}

/**
 * Show comprehensive project analysis
 */
async function handleAnalyzeProject() {
    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing project architecture...",
            cancellable: false
        }, async () => {
            const workspaceInfo = await codebaseAnalyzer.analyzeWorkspace();
            const indexStats = codebaseIndexer.getIndexStatus();
            
            // Create analysis report
            const report = [
                '# Project Analysis Report\n',
                '## Overview',
                `- **Language**: ${workspaceInfo.hasTypeScript ? 'TypeScript' : 'JavaScript'}`,
                `- **Components**: ${workspaceInfo.existingComponents.length}`,
                `- **Architecture Patterns**: ${workspaceInfo.architecture?.patterns.join(', ') || 'None detected'}`,
                `- **State Management**: ${workspaceInfo.architecture?.dataFlow.stateManagement || 'Local'}`,
                '',
                '## Codebase Statistics',
                `- **Files Indexed**: ${indexStats.stats.indexedFiles}/${indexStats.stats.totalFiles}`,
                `- **Symbols Found**: ${indexStats.stats.totalSymbols}`,
                `- **Dependencies**: ${indexStats.stats.dependencyNodes} files, ${indexStats.stats.dependencyEdges} relationships`,
                '',
                '## Styling Approach',
                `- **Primary**: ${workspaceInfo.styling.primaryApproach || 'Unknown'}`,
                `- **Tailwind**: ${workspaceInfo.styling.hasTailwind ? 'Yes' : 'No'}`,
                `- **CSS Modules**: ${workspaceInfo.styling.hasCSSModules ? 'Yes' : 'No'}`,
                `- **Styled Components**: ${workspaceInfo.styling.hasStyledComponents ? 'Yes' : 'No'}`,
                '',
                '## Code Patterns',
                `- **Naming**: ${workspaceInfo.patterns?.namingConventions.components || 'Mixed'}`,
                `- **Testing**: ${workspaceInfo.patterns?.testingPatterns.join(', ') || 'None detected'}`,
                `- **State Management**: ${workspaceInfo.patterns?.stateManagementPatterns.join(', ') || 'None detected'}`,
            ].join('\n');

            const doc = await vscode.workspace.openTextDocument({
                content: report,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Error analyzing project: ${error}`);
        console.error('Project analysis error:', error);
    }
}

/**
 * Reindex the workspace
 */
async function handleReindexWorkspace() {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Reindexing workspace...",
            cancellable: false
        }, async (progress) => {
            await codebaseIndexer.indexWorkspace(workspaceFolder.uri.fsPath, progress);
        });
        
        vscode.window.showInformationMessage('Workspace reindexing completed!');
    } catch (error) {
        vscode.window.showErrorMessage(`Reindexing failed: ${error}`);
        console.error('Reindexing error:', error);
    }
}

/**
 * Show indexing status and statistics
 */
async function handleShowIndexStatus() {
    const status = codebaseIndexer.getIndexStatus();
    const stats = status.stats;
    
    const message = [
        `Status: ${status.status}`,
        `Files: ${stats.indexedFiles}/${stats.totalFiles}`,
        `Symbols: ${stats.totalSymbols}`,
        `Dependencies: ${stats.dependencyNodes} nodes, ${stats.dependencyEdges} edges`,
        `Last Updated: ${stats.lastUpdated?.toLocaleString() || 'Never'}`
    ].join('\n');

    vscode.window.showInformationMessage(message, { modal: true });
}

/**
 * Open extension configuration
 */
async function handleConfigureExtension() {
    await vscode.commands.executeCommand('workbench.action.openSettings', 'ui-copilot');
}

async function handleIterateComponent() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('Please select some code to iterate on');
        return;
    }

    const selectedText = editor.document.getText(editor.selection);
    if (!selectedText) {
        vscode.window.showErrorMessage('Please select the component code you want to modify');
        return;
    }

    const modification = await vscode.window.showInputBox({
        placeHolder: 'How would you like to modify this component? (e.g., "make it responsive", "add loading state")',
        prompt: 'Describe the changes you want to make'
    });

    if (!modification) {
        return;
    }

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Modifying component...",
            cancellable: false
        }, async (progress) => {
            const workspaceInfo = await codebaseAnalyzer.analyzeWorkspace();
            const modifiedCode = await componentGenerator.iterateComponent(selectedText, modification, workspaceInfo);
            
            await editor.edit(editBuilder => {
                editBuilder.replace(editor.selection, modifiedCode);
            });

            await vscode.commands.executeCommand('editor.action.formatDocument');
        });

        vscode.window.showInformationMessage('Component updated successfully!');
    } catch (error) {
        vscode.window.showErrorMessage(`Error modifying component: ${error}`);
        console.error('Component iteration error:', error);
    }
}

export function deactivate() {
    console.log('🛑 Deactivating UI Copilot...');
    
    // Cleanup services
    if (codebaseIndexer) {
        codebaseIndexer.dispose();
    }
    
    if (codebaseAnalyzer) {
        codebaseAnalyzer.dispose();
    }
    
    console.log('✅ UI Copilot deactivated successfully');
}