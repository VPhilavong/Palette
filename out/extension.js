"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const componentGenerator_1 = require("./componentGenerator");
const codebaseAnalyzer_1 = require("./codebaseAnalyzer");
const codebaseIndexer_1 = require("./codebaseIndexer");
const contextManager_1 = require("./contextManager");
const geminiContextManager_1 = require("./geminiContextManager");
const claudeIntegration_1 = require("./claudeIntegration");
const geminiIntegration_1 = require("./geminiIntegration");
let componentGenerator;
let codebaseAnalyzer;
let codebaseIndexer;
let contextManager;
let geminiContextManager;
let claudeIntegration;
let geminiIntegration;
let extensionConfig;
function activate(context) {
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
exports.activate = activate;
/**
 * Initialize extension configuration from VS Code settings
 */
function initializeConfiguration() {
    const config = vscode.workspace.getConfiguration('ui-copilot');
    const aiProvider = config.get('aiProvider') || 'gemini';
    const claudeConfig = {
        apiKey: config.get('claudeApiKey') || '',
        model: config.get('claudeModel') || 'claude-3-sonnet-20240229',
        maxTokens: config.get('maxTokens') || 4000,
        temperature: config.get('temperature') || 0.3
    };
    const geminiConfig = {
        apiKey: config.get('geminiApiKey') || '',
        model: config.get('geminiModel') || 'gemini-2.0-flash-exp',
        maxTokens: config.get('maxTokens') || 100000,
        temperature: config.get('temperature') || 0.3,
        topP: config.get('topP') || 0.8,
        topK: config.get('topK') || 20
    };
    extensionConfig = {
        aiProvider: aiProvider,
        claude: claudeConfig,
        gemini: geminiConfig,
        indexing: {
            enabled: config.get('indexing.enabled') ?? true,
            maxFileSize: config.get('indexing.maxFileSize') ?? 100 * 1024,
            excludePatterns: config.get('indexing.excludePatterns') ?? ['node_modules', '.git', 'dist', 'build'],
            includePatterns: config.get('indexing.includePatterns') ?? ['**/*.{ts,tsx,js,jsx}'],
            watchForChanges: config.get('indexing.watchForChanges') ?? true,
            debounceTime: config.get('indexing.debounceTime') ?? 500
        },
        context: {
            maxTokens: aiProvider === 'gemini' ?
                config.get('context.maxTokens') ?? 2000000 : // 2M for Gemini
                config.get('context.maxTokens') ?? 12000,
            maxFiles: aiProvider === 'gemini' ?
                config.get('context.maxFiles') ?? 200 : // 200 for Gemini
                config.get('context.maxFiles') ?? 20,
            maxChunks: config.get('context.maxChunks') ?? 50,
            relevanceThreshold: config.get('context.relevanceThreshold') ?? 0.3,
            includeRelatedFiles: config.get('context.includeRelatedFiles') ?? true,
            includeDependencies: config.get('context.includeDependencies') ?? true
        },
        performance: {
            cacheEnabled: config.get('performance.cacheEnabled') ?? true,
            cacheTTL: config.get('performance.cacheTTL') ?? 3600000,
            maxCacheSize: config.get('performance.maxCacheSize') ?? 100 * 1024 * 1024,
            concurrentLimit: config.get('performance.concurrentLimit') ?? 10,
            timeoutMs: config.get('performance.timeoutMs') ?? 30000
        },
        features: {
            autoCompletion: config.get('features.autoCompletion') ?? true,
            codeExplanation: config.get('features.codeExplanation') ?? true,
            refactoring: config.get('features.refactoring') ?? true,
            debugging: config.get('features.debugging') ?? true,
            codeGeneration: config.get('features.codeGeneration') ?? true
        }
    };
}
/**
 * Initialize all core services
 */
function initializeServices() {
    try {
        // Initialize existing services
        componentGenerator = new componentGenerator_1.ComponentGenerator();
        codebaseAnalyzer = new codebaseAnalyzer_1.CodebaseAnalyzer();
        // Initialize new codebase-aware services
        codebaseIndexer = new codebaseIndexer_1.CodebaseIndexer();
        // Initialize context managers for both AI providers
        contextManager = new contextManager_1.ContextManager(codebaseIndexer, 12000, 20); // For Claude
        geminiContextManager = new geminiContextManager_1.GeminiContextManager(codebaseIndexer, 2000000, 200); // For Gemini
        // Initialize AI integrations based on provider preference
        if (extensionConfig.aiProvider === 'gemini' && extensionConfig.gemini?.apiKey) {
            geminiIntegration = new geminiIntegration_1.GeminiIntegration(extensionConfig.gemini);
            console.log('🚀 Gemini 2.0 Flash integration initialized with massive context');
        }
        else if (extensionConfig.claude?.apiKey) {
            claudeIntegration = new claudeIntegration_1.ClaudeIntegration(extensionConfig.claude);
            console.log('✅ Claude API integration initialized');
        }
        else {
            console.log('⚠️ No AI provider configured - please set your API key in settings');
        }
        // Set up event listeners
        setupEventListeners();
        console.log('✅ All services initialized successfully');
    }
    catch (error) {
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
function registerCommands(context) {
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
 * Get current AI integration and context manager
 */
function getCurrentAIProvider() {
    if (geminiIntegration) {
        return {
            aiIntegration: geminiIntegration,
            contextManager: geminiContextManager,
            provider: 'gemini'
        };
    }
    else if (claudeIntegration) {
        return {
            aiIntegration: claudeIntegration,
            contextManager: contextManager,
            provider: 'claude'
        };
    }
    return {
        aiIntegration: null,
        contextManager: geminiContextManager,
        provider: null
    };
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
    }
    catch (error) {
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
        if (!prompt)
            return;
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
            // Use new codebase-aware approach with preferred AI provider
            if (geminiIntegration) {
                const contextRequest = {
                    currentFile: editor.document.fileName,
                    cursorPosition: editor.selection.active,
                    query: prompt,
                    responseType: 'generation',
                    language: editor.document.languageId
                };
                const context = await geminiContextManager.buildMassiveContext(contextRequest);
                const aiRequest = {
                    type: 'generation',
                    query: prompt,
                    language: editor.document.languageId
                };
                const response = await geminiIntegration.processRequest(aiRequest, context);
                await editor.edit(editBuilder => {
                    const position = editor.selection.active;
                    editBuilder.insert(position, response.content);
                });
                const utilization = geminiContextManager.getContextUtilization(context);
                vscode.window.showInformationMessage(`Component generated with ${context.metadata.filesIncluded} files (${Math.round(utilization.utilizationPercentage)}% context used, ${Math.round(response.confidence * 100)}% confidence)`);
            }
            else if (claudeIntegration) {
                const contextRequest = {
                    currentFile: editor.document.fileName,
                    cursorPosition: editor.selection.active,
                    query: prompt,
                    responseType: 'generation',
                    language: editor.document.languageId
                };
                const context = await contextManager.buildContext(contextRequest);
                const aiRequest = {
                    type: 'generation',
                    query: prompt,
                    language: editor.document.languageId
                };
                const response = await claudeIntegration.processRequest(aiRequest, context);
                await editor.edit(editBuilder => {
                    const position = editor.selection.active;
                    editBuilder.insert(position, response.content);
                });
                vscode.window.showInformationMessage(`Component generated with ${context.metadata.filesIncluded} context files (${Math.round(response.confidence * 100)}% confidence)`);
            }
            else {
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
    }
    catch (error) {
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
            const contextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                responseType: 'explanation',
                language: editor.document.languageId
            };
            const context = await contextManager.buildContext(contextRequest);
            const aiRequest = {
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
    }
    catch (error) {
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
    if (!refactorGoal)
        return;
    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Refactoring code with codebase awareness...",
            cancellable: false
        }, async () => {
            const contextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                query: refactorGoal,
                responseType: 'refactor',
                language: editor.document.languageId
            };
            const context = await contextManager.buildContext(contextRequest);
            const aiRequest = {
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
    }
    catch (error) {
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
            const contextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                responseType: 'completion',
                language: editor.document.languageId
            };
            const context = await contextManager.buildContext(contextRequest);
            const aiRequest = {
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
    }
    catch (error) {
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
    if (!debugQuery)
        return;
    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing code for debugging...",
            cancellable: false
        }, async () => {
            const contextRequest = {
                currentFile: editor.document.fileName,
                cursorPosition: editor.selection.active,
                selectedCode: selectedText,
                query: debugQuery,
                responseType: 'debug',
                language: editor.document.languageId
            };
            const context = await contextManager.buildContext(contextRequest);
            const aiRequest = {
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
    }
    catch (error) {
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
    if (!query)
        return;
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
    }
    catch (error) {
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
    }
    catch (error) {
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
            // Enhanced analysis with better detection
            const { aiIntegration, provider } = getCurrentAIProvider();
            // Enhanced component counting
            const tsxFiles = workspaceInfo.existingComponents.filter(c => c.path.endsWith('.tsx')).length;
            const jsxFiles = workspaceInfo.existingComponents.filter(c => c.path.endsWith('.jsx')).length;
            const totalReactComponents = tsxFiles + jsxFiles;
            // Better state management detection
            const statePatterns = workspaceInfo.patterns?.stateManagementPatterns || [];
            let stateManagementSummary = 'Local state only';
            if (statePatterns.includes('tanstack-query')) {
                stateManagementSummary = 'TanStack Query + Local state';
            }
            else if (statePatterns.includes('redux')) {
                stateManagementSummary = 'Redux + Local state';
            }
            else if (statePatterns.includes('zustand')) {
                stateManagementSummary = 'Zustand + Local state';
            }
            else if (statePatterns.length > 1) {
                stateManagementSummary = 'Mixed state management';
            }
            const report = [
                '# Enhanced Project Analysis Report\n',
                '## Project Overview',
                `- **Language**: ${workspaceInfo.hasTypeScript ? 'TypeScript' : 'JavaScript'}`,
                `- **React Components**: ${totalReactComponents} (${tsxFiles} .tsx, ${jsxFiles} .jsx)`,
                `- **Total Components**: ${workspaceInfo.existingComponents.length} (${totalReactComponents} React components, ${workspaceInfo.existingComponents.length - totalReactComponents} other components)`,
                `- **Architecture**: Component-based React application`,
                '',
                '## Architecture & Patterns',
                `- **Architecture Patterns**: ${workspaceInfo.architecture?.patterns.join(', ') || 'Component-based React'}`,
                `- **State Management**: ${stateManagementSummary}`,
                `- **Routing**: ${statePatterns.includes('tanstack-router') ? 'TanStack Router' : statePatterns.includes('react-router') ? 'React Router' : 'Not detected'}`,
                `- **Data Fetching**: ${statePatterns.includes('tanstack-query') ? 'TanStack Query (React Query)' : statePatterns.includes('swr') ? 'SWR' : 'Custom/Fetch'}`,
                '',
                '## Codebase Statistics',
                `- **Files Indexed**: ${indexStats.stats.indexedFiles}/${indexStats.stats.totalFiles}`,
                `- **Symbols Found**: ${indexStats.stats.totalSymbols}`,
                `- **Dependencies**: ${indexStats.stats.dependencyNodes} files, ${indexStats.stats.dependencyEdges} relationships`,
                `- **TypeScript Usage**: ${(tsxFiles / Math.max(totalReactComponents, 1) * 100).toFixed(1)}% of React components`,
                '',
                '## UI & Styling',
                `- **UI Framework**: ${workspaceInfo.styling.uiLibrary || 'Custom/None'}`,
                `- **Primary Approach**: ${formatPrimaryApproach(workspaceInfo.styling.primaryApproach, workspaceInfo.styling.uiLibrary)}`,
                `- **Tailwind CSS**: ${workspaceInfo.styling.hasTailwind ? 'Yes' : 'No'}`,
                `- **CSS Modules**: ${workspaceInfo.styling.hasCSSModules ? 'Yes' : 'No'}`,
                `- **Styled Components**: ${workspaceInfo.styling.hasStyledComponents ? 'Yes' : 'No'}`,
                `- **Chakra UI**: ${workspaceInfo.styling.uiLibrary?.includes('Chakra') ? (workspaceInfo.styling.uiLibrary.includes('v3') ? 'Yes (v3)' : 'Yes') : 'No'}`,
                '',
                '## Development Tools',
                `- **Testing Framework**: ${categorizeTesting(workspaceInfo.patterns?.testingPatterns || [])}`,
                `- **TypeScript**: ${workspaceInfo.hasTypeScript ? 'Yes' : 'No'}`,
                '',
                '## State Management Details',
                `- **Patterns Detected**: ${statePatterns.join(', ') || 'Local state only'}`,
                `- **Hook Usage**: ${formatHookUsage(statePatterns, workspaceInfo.existingComponents)}`,
                '',
                '## Code Quality Insights',
                `- **Naming Convention**: ${workspaceInfo.patterns?.namingConventions.components || 'PascalCase'} (Components)`,
                `- **File Organization**: ${workspaceInfo.patterns?.stylePatterns?.organization || 'Component-based'}`,
                `- **Modern React Patterns**: ${statePatterns.includes('tanstack-query') || statePatterns.includes('tanstack-router') ? 'Yes (TanStack ecosystem)' : 'Partial'}`,
            ].join('\n');
            const doc = await vscode.workspace.openTextDocument({
                content: report,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error analyzing project: ${error}`);
        console.error('Project analysis error:', error);
    }
}
/**
 * Helper to categorize testing frameworks correctly
 */
function categorizeTesting(testingPatterns) {
    if (testingPatterns.length === 0)
        return 'None detected';
    // PRIORITY FIX: Prioritize Playwright as the primary E2E framework
    const e2eFrameworks = testingPatterns.filter(p => p.includes('playwright') || p.includes('cypress') || p.includes('e2e'));
    const unitFrameworks = testingPatterns.filter(p => p.includes('jest') || p.includes('vitest') || p.includes('testing-library') || p.includes('react-testing'));
    // Check for Playwright specifically
    const hasPlaywright = testingPatterns.some(p => p.includes('playwright'));
    if (hasPlaywright && unitFrameworks.length === 0) {
        return 'Playwright (E2E)';
    }
    if (e2eFrameworks.length > 0 && unitFrameworks.length > 0) {
        const primary = hasPlaywright ? 'Playwright' : e2eFrameworks[0];
        return `${primary} (E2E) + ${unitFrameworks[0]} (Unit)`;
    }
    else if (e2eFrameworks.length > 0) {
        const primary = hasPlaywright ? 'Playwright' : e2eFrameworks[0];
        return `${primary} (E2E Testing)`;
    }
    else if (unitFrameworks.length > 0) {
        return `${unitFrameworks.join(', ')} (Unit Testing)`;
    }
    return testingPatterns.join(', ');
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
    }
    catch (error) {
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
    }
    catch (error) {
        vscode.window.showErrorMessage(`Error modifying component: ${error}`);
        console.error('Component iteration error:', error);
    }
}
/**
 * Helper to format primary styling approach in a user-friendly way
 */
function formatPrimaryApproach(primaryApproach, uiLibrary) {
    if (!primaryApproach)
        return 'CSS/Inline';
    switch (primaryApproach) {
        case 'chakra-ui':
            return 'Chakra UI Components';
        case 'shadcn-ui':
            return 'shadcn/ui Components';
        case 'material-ui':
            return 'Material-UI Components';
        case 'antd':
            return 'Ant Design Components';
        case 'mantine':
            return 'Mantine Components';
        case 'nextui':
            return 'NextUI Components';
        case 'ui-library':
            return `${uiLibrary} Components`;
        case 'tailwind':
            return 'Tailwind CSS';
        case 'styled-components':
            return 'Styled Components';
        case 'css-modules':
            return 'CSS Modules';
        case 'emotion':
            return 'Emotion (CSS-in-JS)';
        case 'inline':
            return 'CSS/Inline';
        default:
            return primaryApproach || 'CSS/Inline';
    }
}
/**
 * Helper to format hook usage in a comprehensive way
 */
function formatHookUsage(statePatterns, components) {
    const hooksList = [];
    // Basic React hooks from patterns
    if (statePatterns.includes('local-state'))
        hooksList.push('useState');
    if (statePatterns.includes('lifecycle-effects'))
        hooksList.push('useEffect');
    if (statePatterns.includes('context-api'))
        hooksList.push('useContext');
    if (statePatterns.includes('reducer-pattern'))
        hooksList.push('useReducer');
    if (statePatterns.includes('callback-optimization'))
        hooksList.push('useCallback');
    if (statePatterns.includes('memo-optimization'))
        hooksList.push('useMemo');
    // Advanced hooks from actual component analysis
    const allHooks = components.flatMap(c => c.ast?.hooks || []);
    const hookTypes = new Set(allHooks.map(h => h.name));
    // Add additional hooks found in the components
    const additionalHooks = Array.from(hookTypes).filter(hook => !hooksList.includes(hook) && (hook.startsWith('use') ||
        ['useRef', 'useLayoutEffect', 'useImperativeHandle', 'useDebugValue'].includes(hook)));
    hooksList.push(...additionalHooks);
    // External library hooks
    if (statePatterns.includes('tanstack-query'))
        hooksList.push('useQuery');
    if (statePatterns.includes('tanstack-router'))
        hooksList.push('useRouter');
    return hooksList.length > 0 ? hooksList.join(', ') : 'Standard React hooks';
}
function deactivate() {
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
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map