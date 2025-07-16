import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import { PalettePanel } from './UICopilotPanel';
import { runPalettePreview } from './paletteRunner';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    console.log('Code Palette extension is now active!');

    // Register commands
    const generateCommand = vscode.commands.registerCommand('palette.generate', async (uri?: vscode.Uri) => {
        await generateComponent(uri);
    });

    const analyzeCommand = vscode.commands.registerCommand('palette.analyze', async () => {
        await analyzeProject();
    });

    const openWebviewCommand = vscode.commands.registerCommand('palette.openWebview', () => {
        PalettePanel.createOrShow(context.extensionUri);
    });

    context.subscriptions.push(generateCommand, analyzeCommand, openWebviewCommand);

    // Handle webview panel restoration
    if (vscode.window.registerWebviewPanelSerializer) {
        vscode.window.registerWebviewPanelSerializer('palette', {
            async deserializeWebviewPanel(webviewPanel: vscode.WebviewPanel, _state: any) {
                PalettePanel.revive(webviewPanel, context.extensionUri);
            }
        });
    }
}

async function generateComponent(uri?: vscode.Uri) {
    try {
        // Get the workspace root
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('Please open a workspace to use Code Palette');
            return;
        }

        // Get user input for component description
        const prompt = await vscode.window.showInputBox({
            prompt: 'Describe the component you want to generate',
            placeHolder: 'e.g., "modern pricing section with glassmorphism"',
            validateInput: (value) => {
                return value.trim() === '' ? 'Please enter a component description' : null;
            }
        });

        if (!prompt) {
            return; // User cancelled
        }

        // Show progress indicator
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Generating component...',
            cancellable: false
        }, async (progress) => {
            progress.report({ increment: 0, message: 'Analyzing project...' });

            try {
                progress.report({ increment: 30, message: 'Generating component code...' });
                
                // Use the shared function for consistent output
                const componentCode = await runPalettePreview(prompt, workspaceFolder.uri.fsPath);
                
                progress.report({ increment: 70, message: 'Component preview ready!' });
                
                // Ask user if they want to create the component
                const create = await vscode.window.showInformationMessage(
                    'Component generated successfully! Create the file?',
                    'Create',
                    'Cancel'
                );

                if (create === 'Create') {
                    // Get file name from user
                    const fileName = await vscode.window.showInputBox({
                        prompt: 'Enter component file name',
                        placeHolder: 'components/Button.tsx',
                        value: 'components/NewComponent.tsx'
                    });

                    if (fileName) {
                        // Add .tsx extension if not provided
                        const finalFileName = fileName.includes('.') ? fileName : fileName + '.tsx';
                        
                        // Create the component file
                        await createComponentFile(componentCode, finalFileName, workspaceFolder.uri.fsPath);
                        
                        vscode.window.showInformationMessage(`Component created: ${finalFileName}`);
                    }
                }

                progress.report({ increment: 100, message: 'Complete!' });

            } catch (error) {
                throw error;
            }
        });

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        
        if (errorMessage.includes('command not found') || errorMessage.includes('not found')) {
            vscode.window.showErrorMessage(
                'Palette CLI not found. Please install it first: pip install -e /path/to/code-palette',
                'Open Settings'
            ).then(selection => {
                if (selection === 'Open Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'palette.cliPath');
                }
            });
        } else if (errorMessage.includes('OpenAI API key not configured')) {
            vscode.window.showErrorMessage(
                'OpenAI API key not configured. Please set OPENAI_API_KEY in your environment.',
                'Learn More'
            );
        } else {
            vscode.window.showErrorMessage(`Code Palette Error: ${errorMessage}`);
        }
    }
}

async function createComponentFile(componentCode: string, fileName: string, workspacePath: string) {
    const fullPath = path.join(workspacePath, fileName);
    const fileUri = vscode.Uri.file(fullPath);
    
    // Ensure directory exists
    const directory = path.dirname(fullPath);
    const directoryUri = vscode.Uri.file(directory);
    
    try {
        await vscode.workspace.fs.stat(directoryUri);
    } catch {
        // Directory doesn't exist, create it
        await vscode.workspace.fs.createDirectory(directoryUri);
    }
    
    // Create the file
    await vscode.workspace.fs.writeFile(fileUri, Buffer.from(componentCode, 'utf8'));
    
    // Open the created file
    const document = await vscode.workspace.openTextDocument(fileUri);
    await vscode.window.showTextDocument(document);
}

async function analyzeProject() {
    try {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('Please open a workspace to use Code Palette');
            return;
        }

        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Analyzing project...',
            cancellable: false
        }, async () => {
            const config = vscode.workspace.getConfiguration('palette');
            const cliPath = config.get<string>('cliPath', 'palette');

            const command = `${cliPath} analyze`;
            const { stdout } = await execAsync(command, {
                cwd: workspaceFolder.uri.fsPath,
                timeout: 15000
            });

            // Show analysis results in information message
            const lines = stdout.split('\n').filter(line => 
                line.includes('Framework:') || 
                line.includes('Styling:') || 
                line.includes('Component Library:') ||
                line.includes('Colors:') ||
                line.includes('Spacing:')
            );

            if (lines.length > 0) {
                const summary = lines.join('\n');
                vscode.window.showInformationMessage(
                    `Project Analysis:\n${summary}`,
                    { modal: true }
                );
            } else {
                vscode.window.showInformationMessage('Project analysis completed. Check the terminal for details.');
            }
        });

    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        vscode.window.showErrorMessage(`Analysis Error: ${errorMessage}`);
    }
}

export function deactivate() {}