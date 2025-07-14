/**
 * VS Code Extension Entry Point
 * 
 * This is the main entry point for the UI Copilot extension. It handles:
 * - Extension activation and initialization
 * - Command registration (askToBuild, openPanel, etc.)
 * - Workspace indexing and component analysis
 * - Automatic embedding generation for contextual understanding
 * - File watching for workspace changes
 * 
 * The extension automatically indexes the workspace on startup and provides
 * AI-powered code generation through the OpenAI API.
 */

import * as vscode from 'vscode';
import { FileIndexer } from '../codebase/fileIndexer';
import { FrameworkDetector } from '../codebase/frameworkDetector';
import { ComponentAnalyzer } from '../codebase/componentAnalyzer';
import { EmbeddingGenerator } from '../embeddings/embeddingGenerator';
import { ContextRanker } from '../embeddings/contextRanker';
import { WorkspaceIndex, ComponentInfo } from '../types';
import { PromptModal } from '../ui/promptModal';
import { ComponentGenerator } from '../llm/componentGenerator';
import { UICopilotPanel } from '../webview/UICopilotPanel'; // update path if needed
import { CodebaseAnalyzer } from '../codebase/codebaseAnalyzer';


let workspaceIndex: WorkspaceIndex | null = null;
let fileIndexer: FileIndexer;
let frameworkDetector: FrameworkDetector;
let componentAnalyzer: ComponentAnalyzer;
let embeddingGenerator: EmbeddingGenerator;
let componentGenerator: ComponentGenerator;
let codebaseAnalyzer: CodebaseAnalyzer;

export async function activate(context: vscode.ExtensionContext) {
    console.log('UI Copilot extension is now active!');

    // Initialize core components
    fileIndexer = new FileIndexer();
    frameworkDetector = new FrameworkDetector();
    componentAnalyzer = new ComponentAnalyzer();
    embeddingGenerator = new EmbeddingGenerator();
    componentGenerator = new ComponentGenerator();

    // Setup file watching
    const fileWatcher = fileIndexer.setupFileWatcher();
    context.subscriptions.push(fileWatcher);
 
    codebaseAnalyzer = new CodebaseAnalyzer();

    

    const openPanelCommand = vscode.commands.registerCommand('ui-copilot.openPanel', () => {
        UICopilotPanel.createOrShow(context.extensionUri, componentGenerator, codebaseAnalyzer);
    });
    
    
    context.subscriptions.push(openPanelCommand);
    

    // Primary command - Generate UI Component with prompt
    const generateComponentQuickCommand = vscode.commands.registerCommand('ui-copilot.generateComponentQuick', async () => {
        const promptModal = PromptModal.getInstance();
        const userPrompt = await promptModal.showPromptInput();
        
        if (userPrompt) {
            await componentGenerator.generateComponent(userPrompt, workspaceIndex);
        }
    });

    // Ask to Build command - opens UI Copilot Panel
    const askToBuildCommand = vscode.commands.registerCommand('ui-copilot.askToBuild', async () => {
        // Ensure workspace is analyzed first
        if (!workspaceIndex) {
            await initializeWorkspace();
        }
        
        // Open the UI Copilot Panel for interactive conversation
        UICopilotPanel.createOrShow(context.extensionUri, componentGenerator, codebaseAnalyzer);
    });

    context.subscriptions.push(
        generateComponentQuickCommand,
        askToBuildCommand
    );

    // Initialize workspace on activation
    await initializeWorkspace();
}

async function initializeWorkspace(): Promise<void> {
    if (!vscode.workspace.workspaceFolders) {
        return;
    }

    try {
        vscode.window.showInformationMessage('Indexing workspace...');
        
        const [files, projectMetadata] = await Promise.all([
            fileIndexer.indexWorkspace(),
            frameworkDetector.detectProjectFrameworks()
        ]);

        // Analyze components from the indexed files
        console.log('Analyzing components...');
        const components = await componentAnalyzer.analyzeComponents(files);

        // Generate embeddings for components automatically
        console.log('Generating component summaries and embeddings...');
        let embeddingsGenerated = 0;
        for (const component of components) {
            embeddingGenerator.generateComponentSummary(component);
            try {
                component.embedding = await embeddingGenerator.generateComponentEmbedding(component);
                if (component.embedding && component.embedding.length > 0) {
                    embeddingsGenerated++;
                }
            } catch (error) {
                console.error(`Failed to generate embedding for ${component.name}:`, error);
            }
        }
        
        console.log(`✅ Generated embeddings for ${embeddingsGenerated}/${components.length} components`);
        if (embeddingsGenerated > 0) {
            console.log('🎯 Embeddings are ready for context-aware code generation!');
        } else {
            console.log('⚠️ No embeddings generated - context search will be limited');
        }

        workspaceIndex = {
            files,
            components,
            project: projectMetadata,
            lastUpdated: new Date()
        };

        const stats = componentAnalyzer.getComponentStats(components);
        console.log(`Indexed ${files.length} files, ${components.length} components, detected frameworks:`, 
            projectMetadata.frameworks.map(f => f.name));
        console.log('Component stats:', stats);
        
    } catch (error) {
        console.error('Failed to initialize workspace:', error);
        vscode.window.showErrorMessage('Failed to index workspace');
    }
}

export function deactivate() {}

export function getWorkspaceIndex(): WorkspaceIndex | null {
    return workspaceIndex;
}

async function generateComponentEmbeddings(): Promise<void> {
    if (!workspaceIndex) return;

    try {
        vscode.window.showInformationMessage('Generating embeddings for components...');
        
        const componentsToEmbed = workspaceIndex.components.filter(comp => !comp.embedding);
        
        if (componentsToEmbed.length === 0) {
            vscode.window.showInformationMessage('All components already have embeddings.');
            return;
        }

        console.log(`Generating embeddings for ${componentsToEmbed.length} components...`);
        
        // Generate embeddings in parallel batches
        const batchSize = 5;
        for (let i = 0; i < componentsToEmbed.length; i += batchSize) {
            const batch = componentsToEmbed.slice(i, i + batchSize);
            
            await Promise.all(batch.map(async (component) => {
                try {
                    component.embedding = await embeddingGenerator.generateComponentEmbedding(component);
                    console.log(`Generated embedding for ${component.name}`);
                } catch (error) {
                    console.error(`Failed to generate embedding for ${component.name}:`, error);
                }
            }));
            
            // Update progress
            const progress = Math.round(((i + batch.length) / componentsToEmbed.length) * 100);
            console.log(`Embedding progress: ${progress}%`);
        }

        const embeddedCount = workspaceIndex.components.filter(comp => comp.embedding).length;
        const stats = embeddingGenerator.getUsageStats();
        
        vscode.window.showInformationMessage(
            `Generated embeddings for ${embeddedCount}/${workspaceIndex.components.length} components. ` +
            `API calls: ${stats.apiCalls}, Tokens: ${stats.tokens}, Cache hits: ${stats.cacheHits}`
        );
        
    } catch (error) {
        console.error('Failed to generate embeddings:', error);
        vscode.window.showErrorMessage(`Failed to generate embeddings: ${error}`);
    }
}

async function findSimilarComponents(): Promise<void> {
    if (!workspaceIndex) return;

    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {
        vscode.window.showWarningMessage('Open a component file to find similar components.');
        return;
    }

    const currentFilePath = vscode.workspace.asRelativePath(activeEditor.document.uri);
    const currentComponent = workspaceIndex.components.find(comp => comp.path === currentFilePath);
    
    if (!currentComponent) {
        vscode.window.showWarningMessage('Current file is not recognized as a component.');
        return;
    }

    if (!currentComponent.embedding) {
        vscode.window.showWarningMessage('Current component needs embedding. Run "Generate Embeddings" first.');
        return;
    }

    try {
        const similarComponents = ContextRanker.findSimilarToComponent(
            currentComponent,
            workspaceIndex.components,
            5,
            0.6
        );

        if (similarComponents.length === 0) {
            vscode.window.showInformationMessage('No similar components found.');
            return;
        }

        const similarList = similarComponents
            .map(result => `${result.component.name} (${(result.similarity * 100).toFixed(1)}% similar) - ${result.component.path}`)
            .join('\n');

        vscode.window.showInformationMessage(
            `Similar components to ${currentComponent.name}:\n${similarList}`,
            { modal: true }
        );
        
    } catch (error) {
        console.error('Failed to find similar components:', error);
        vscode.window.showErrorMessage(`Failed to find similar components: ${error}`);
    }
}

async function searchSimilarComponents(): Promise<void> {
    if (!workspaceIndex) return;

    const searchQuery = await vscode.window.showInputBox({
        prompt: 'Enter search query for components',
        placeHolder: 'e.g., "form with validation", "data table", "authentication"'
    });

    if (!searchQuery) return;

    try {
        const queryEmbedding = await embeddingGenerator.generateTextEmbedding(searchQuery);
        
        const searchResults = ContextRanker.findSimilarComponents(
            queryEmbedding,
            workspaceIndex.components,
            10,
            0.3
        );

        if (searchResults.length === 0) {
            vscode.window.showInformationMessage('No matching components found.');
            return;
        }

        const resultList = searchResults
            .map(result => `${result.component.name} (${(result.similarity * 100).toFixed(1)}% match) - ${result.component.path}`)
            .join('\n');

        vscode.window.showInformationMessage(
            `Search results for "${searchQuery}":\n${resultList}`,
            { modal: true }
        );
        
    } catch (error) {
        console.error('Failed to search components:', error);
        vscode.window.showErrorMessage(`Failed to search components: ${error}`);
    }
}