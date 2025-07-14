/**
 * UI Copilot Panel
 * 
 * This file manages the main webview panel for the UI Copilot extension:
 * - Creates and manages the webview panel lifecycle
 * - Handles communication between webview and extension
 * - Integrates with component generator and codebase analyzer
 * - Provides the main chat interface for AI interaction
 * - Manages panel state and message passing
 * - Handles user input and displays AI responses
 * 
 * Primary user interface for the extension.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { ComponentGenerator } from '../llm/componentGenerator';
import { CodebaseAnalyzer } from '../codebase/codebaseAnalyzer';
import { indexWorkspace } from '../codebase/fileIndexer';

import { FileIndexer } from '../codebase/fileIndexer';
import { FrameworkDetector } from '../codebase/frameworkDetector';
import { ComponentAnalyzer } from '../codebase/componentAnalyzer';
import { WorkspaceIndex } from '../types';

export class UICopilotPanel {
    public static currentPanel: UICopilotPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private readonly _componentGenerator: ComponentGenerator;
    private readonly _codebaseAnalyzer: CodebaseAnalyzer;


    public static readonly viewType = 'ui-copilot-panel';
    

    public static createOrShow(extensionUri: vscode.Uri, componentGenerator: ComponentGenerator, codebaseAnalyzer: CodebaseAnalyzer) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (UICopilotPanel.currentPanel) {
            UICopilotPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            UICopilotPanel.viewType,
            'UI Copilot',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(extensionUri, 'src', 'webview')
                ]
            }
        );

        UICopilotPanel.currentPanel = new UICopilotPanel(panel, extensionUri, componentGenerator, codebaseAnalyzer);
    }

    public static revive(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, componentGenerator: ComponentGenerator, codebaseAnalyzer: CodebaseAnalyzer) {
        UICopilotPanel.currentPanel = new UICopilotPanel(panel, extensionUri, componentGenerator, codebaseAnalyzer);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, componentGenerator: ComponentGenerator, codebaseAnalyzer: CodebaseAnalyzer) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._componentGenerator = componentGenerator;
        this._codebaseAnalyzer = codebaseAnalyzer;

        // Set the webview's initial html content
        this._update();

        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'generateComponent':
                        await this._handleGenerateComponent(message.prompt);
                        return;
                    

                }
            },
            null,
            this._disposables
        );
    }

    private async _handleGenerateComponent(prompt: string) {
        try {
            this._panel.webview.postMessage({
                command: 'showProgress',
                message: 'Analyzing workspace and generating component...'
            });

            // Create workspace index for code generation (same as in extension.ts)
            const fileIndexer = new FileIndexer();
            const frameworkDetector = new FrameworkDetector();
            const componentAnalyzer = new ComponentAnalyzer();
            
            const files = await fileIndexer.indexWorkspace();
            const project = await frameworkDetector.detectProjectFrameworks();
            const components = await componentAnalyzer.analyzeComponents(files);
            
            const workspaceIndex: WorkspaceIndex = {
                files,
                components,
                project,
                lastUpdated: new Date()
            };

            // Use the full generateComponent method (not just generateComponentCode)
            // This creates files in the correct location and handles all the "Ask to Build" functionality
            const result = await this._componentGenerator.generateComponent(prompt, workspaceIndex);
            
            if (result) {
                this._panel.webview.postMessage({
                    command: 'componentGenerated',
                    message: 'Component successfully generated and saved to your project!',
                    result: result
                });
                
                // Show success notification
                vscode.window.showInformationMessage('Component generated successfully!');
            } else {
                this._panel.webview.postMessage({
                    command: 'showError',
                    message: 'Failed to generate component. Please check your prompt and try again.'
                });
            }

        } catch (error) {
            console.error('Component generation error:', error);
            this._panel.webview.postMessage({
                command: 'showError',
                message: `Error generating component: ${error}`
            });
            vscode.window.showErrorMessage(`Failed to generate component: ${error}`);
        }
    }

    

    
    public dispose() {
        UICopilotPanel.currentPanel = undefined;

        // Clean up our resources
        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private _update() {
        const webview = this._panel.webview;
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        // Get the local path to main script run in the webview, then convert it to a uri we can use in the webview
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'main.js'));
        const styleResetUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'reset.css'));
        const styleVSCodeUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'vscode.css'));
        const styleMainUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'main.css'));

        // Use a nonce to only allow specific scripts to be run
        const nonce = getNonce();

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="${styleResetUri}" rel="stylesheet">
                <link href="${styleVSCodeUri}" rel="stylesheet">
                <link href="${styleMainUri}" rel="stylesheet">
                <title>UI Copilot</title>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>🎨 UI Copilot</h1>
                        <p>Generate UI components with AI assistance</p>
                    </header>

                    <main>
                        <section class="generate-section">
                            <h2>Generate Component</h2>
                            <div class="input-group">
                                <textarea 
                                    id="componentPrompt" 
                                    placeholder="Describe the component you want to generate (e.g., 'user profile card with avatar and bio')"
                                    rows="3"
                                ></textarea>
                                <button id="generateBtn" class="primary-btn">Generate Component</button>
                            </div>
                        </section>

                        

                        
                        <section class="output-section">
                            <h2>Generated Code</h2>
                            <div class="code-output">
                                <pre id="codeOutput" class="code-block">Generated code will appear here...</pre>
                                <div class="code-actions">
                                    <button id="copyBtn" class="secondary-btn">Copy to Clipboard</button>
                                    <button id="insertBtn" class="secondary-btn">Insert at Cursor</button>
                                </div>
                            </div>
                        </section>
                    </main>

                    <div id="progressIndicator" class="progress-indicator hidden">
                        <div class="spinner"></div>
                        <span id="progressMessage">Processing...</span>
                    </div>

                    <div id="errorMessage" class="error-message hidden"></div>
                </div>

                <script nonce="${nonce}" src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
