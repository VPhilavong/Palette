import * as vscode from 'vscode';
import { FileIndexer } from '../codebase/fileIndexer';
import { FrameworkDetector } from '../codebase/frameworkDetector';
import { ComponentAnalyzer } from '../codebase/componentAnalyzer';
import { WorkspaceIndex } from '../types';

let workspaceIndex: WorkspaceIndex | null = null;
let fileIndexer: FileIndexer;
let frameworkDetector: FrameworkDetector;
let componentAnalyzer: ComponentAnalyzer;

export async function activate(context: vscode.ExtensionContext) {
    console.log('UI Copilot extension is now active!');

    // Initialize core components
    fileIndexer = new FileIndexer();
    frameworkDetector = new FrameworkDetector();
    componentAnalyzer = new ComponentAnalyzer();

    // Setup file watching
    const fileWatcher = fileIndexer.setupFileWatcher();
    context.subscriptions.push(fileWatcher);

    // Commands
    const generateCommand = vscode.commands.registerCommand('ui-copilot.generateComponent', () => {
        vscode.window.showInformationMessage('UI Copilot: Component generation coming soon!');
    });

    const explainCommand = vscode.commands.registerCommand('ui-copilot.explainCode', () => {
        vscode.window.showInformationMessage('UI Copilot: Code explanation coming soon!');
    });

    const reindexCommand = vscode.commands.registerCommand('ui-copilot.reindexWorkspace', async () => {
        await initializeWorkspace();
        vscode.window.showInformationMessage('Workspace reindexed successfully!');
    });

    const showStatusCommand = vscode.commands.registerCommand('ui-copilot.showIndexStatus', () => {
        if (workspaceIndex) {
            const fileCount = workspaceIndex.files.length;
            const componentCount = workspaceIndex.components.length;
            const frameworks = workspaceIndex.project.frameworks.map(f => f.name).join(', ');
            const stats = componentAnalyzer.getComponentStats(workspaceIndex.components);
            
            const topHooks = Object.entries(stats.hooksUsage)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 3)
                .map(([hook, count]) => `${hook} (${count})`)
                .join(', ');

            vscode.window.showInformationMessage(
                `Index: ${fileCount} files, ${componentCount} components. Frameworks: ${frameworks || 'None detected'}. Top hooks: ${topHooks || 'None'}`
            );
        } else {
            vscode.window.showWarningMessage('Workspace not indexed yet. Run "Reindex Workspace" command.');
        }
    });

    const showComponentsCommand = vscode.commands.registerCommand('ui-copilot.showComponents', () => {
        if (workspaceIndex && workspaceIndex.components.length > 0) {
            const componentList = workspaceIndex.components
                .slice(0, 10) // Show first 10
                .map(comp => `${comp.name} (${comp.exports.join(', ')}) - ${comp.hooks?.length || 0} hooks`)
                .join('\n');
            
            vscode.window.showInformationMessage(
                `Components found:\n${componentList}${workspaceIndex.components.length > 10 ? '\n...(showing first 10)' : ''}`,
                { modal: true }
            );
        } else {
            vscode.window.showWarningMessage('No components found. Try reindexing the workspace.');
        }
    });

    context.subscriptions.push(generateCommand, explainCommand, reindexCommand, showStatusCommand, showComponentsCommand);

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