import * as vscode from 'vscode';
import { ComponentGenerator } from './componentGenerator';
import { CodebaseAnalyzer } from './codebaseAnalyzer';
import { UICopilotPanel } from './webview/UICopilotPanel';

let componentGenerator: ComponentGenerator;
let codebaseAnalyzer: CodebaseAnalyzer;

export function activate(context: vscode.ExtensionContext) {
    console.log('UI Copilot is now active!');

    // Initialize our services
    componentGenerator = new ComponentGenerator();
    codebaseAnalyzer = new CodebaseAnalyzer();

    // Register the generate component command
    const generateCommand = vscode.commands.registerCommand('ui-copilot.generateComponent', async () => {
        await handleGenerateComponent();
    });

    // Register the iterate component command  
    const iterateCommand = vscode.commands.registerCommand('ui-copilot.iterateComponent', async () => {
        await handleIterateComponent();
    });

    // Register the open panel command
    const openPanelCommand = vscode.commands.registerCommand('ui-copilot.openPanel', () => {
        UICopilotPanel.createOrShow(context.extensionUri, componentGenerator, codebaseAnalyzer);
    });

    context.subscriptions.push(generateCommand, iterateCommand, openPanelCommand);
}

async function handleGenerateComponent() {
    try {
        // Get user input for what they want to build
        const prompt = await vscode.window.showInputBox({
            placeHolder: 'Describe the component you want to generate (e.g., "user profile card with avatar and bio")',
            prompt: 'What UI component would you like to generate?'
        });

        if (!prompt) {
            return;
        }

        // Show progress
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating component...",
            cancellable: false
        }, async (progress) => {
            // Analyze current workspace
            const workspaceInfo = await codebaseAnalyzer.analyzeWorkspace();
            
            // Generate the component
            const generatedCode = await componentGenerator.generateComponent(prompt, workspaceInfo);
            
            // Get active editor
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('Please open a file to insert the component');
                return;
            }

            // Insert the generated code
            await editor.edit(editBuilder => {
                const position = editor.selection.active;
                editBuilder.insert(position, generatedCode);
            });

            // Format the document
            await vscode.commands.executeCommand('editor.action.formatDocument');
        });

        vscode.window.showInformationMessage('Component generated successfully!');
    } catch (error) {
        vscode.window.showErrorMessage(`Error generating component: ${error}`);
        console.error('Component generation error:', error);
    }
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
    // Cleanup if needed
}