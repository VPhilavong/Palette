import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';

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

    context.subscriptions.push(generateCommand, analyzeCommand);
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
                // Get CLI path from configuration
                const config = vscode.workspace.getConfiguration('palette');
                const cliPath = config.get<string>('cliPath', 'palette');

                // Determine output directory
                let outputDir = workspaceFolder.uri.fsPath;
                if (uri && uri.scheme === 'file') {
                    const stat = await vscode.workspace.fs.stat(uri);
                    if (stat.type === vscode.FileType.Directory) {
                        outputDir = uri.fsPath;
                    } else {
                        outputDir = path.dirname(uri.fsPath);
                    }
                }

                progress.report({ increment: 30, message: 'Generating component code...' });

                // Execute palette CLI command for preview
                const command = `echo "n" | ${cliPath} generate "${prompt}" --preview`;
                const { stdout, stderr } = await execAsync(command, {
                    cwd: workspaceFolder.uri.fsPath,
                    timeout: 30000 // 30 second timeout
                });

                progress.report({ increment: 70, message: 'Creating component file...' });

                if (stderr && !stderr.includes('Create this component?') && !stderr.includes('Error:')) {
                    throw new Error(stderr);
                }

                // Parse the output to get the generated component
                // Extract content between the component box borders
                const lines = stdout.split('\n');
                const startIndex = lines.findIndex(line => line.includes('Generated Component'));
                const endIndex = lines.findIndex((line, index) => index > startIndex && line.includes('╰'));
                
                if (startIndex === -1 || endIndex === -1) {
                    throw new Error('Failed to parse generated component from CLI output');
                }
                
                // Extract the component code, removing box borders and formatting
                const componentLines = lines.slice(startIndex + 1, endIndex)
                    .filter(line => line.startsWith('│'))
                    .map(line => line.substring(1).trim())
                    .filter(line => line !== '');
                
                const componentCode = componentLines.join('\n');

                // Ask user if they want to create the component
                const create = await vscode.window.showInformationMessage(
                    'Component generated successfully! Create the file?',
                    'Create',
                    'Cancel'
                );

                if (create === 'Create') {
                    // Execute the actual generation command without preview
                    const createCommand = `echo "y" | ${cliPath} generate "${prompt}"`;
                    const { stdout: createOutput } = await execAsync(createCommand, {
                        cwd: workspaceFolder.uri.fsPath,
                        timeout: 30000
                    });

                    // Extract file path from output
                    const filePathMatch = createOutput.match(/Component created at: (.+)/);
                    if (filePathMatch) {
                        const filePath = path.join(workspaceFolder.uri.fsPath, filePathMatch[1]);
                        const fileUri = vscode.Uri.file(filePath);
                        
                        // Open the created file
                        const document = await vscode.workspace.openTextDocument(fileUri);
                        await vscode.window.showTextDocument(document);
                        
                        vscode.window.showInformationMessage(`Component created: ${filePathMatch[1]}`);
                    } else {
                        vscode.window.showInformationMessage('Component created successfully!');
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
            const lines = stdout.split('\\n').filter(line => 
                line.includes('Framework:') || 
                line.includes('Styling:') || 
                line.includes('Component Library:') ||
                line.includes('Colors:') ||
                line.includes('Spacing:')
            );

            if (lines.length > 0) {
                const summary = lines.join('\\n');
                vscode.window.showInformationMessage(
                    `Project Analysis:\\n${summary}`,
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