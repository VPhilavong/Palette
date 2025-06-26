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
exports.UICopilotPanel = void 0;
const vscode = __importStar(require("vscode"));
class UICopilotPanel {
    static createOrShow(extensionUri, componentGenerator, codebaseAnalyzer) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;
        // If we already have a panel, show it
        if (UICopilotPanel.currentPanel) {
            UICopilotPanel.currentPanel._panel.reveal(column);
            return;
        }
        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(UICopilotPanel.viewType, 'UI Copilot', column || vscode.ViewColumn.One, {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.joinPath(extensionUri, 'src', 'webview')
            ]
        });
        UICopilotPanel.currentPanel = new UICopilotPanel(panel, extensionUri, componentGenerator, codebaseAnalyzer);
    }
    static revive(panel, extensionUri, componentGenerator, codebaseAnalyzer) {
        UICopilotPanel.currentPanel = new UICopilotPanel(panel, extensionUri, componentGenerator, codebaseAnalyzer);
    }
    constructor(panel, extensionUri, componentGenerator, codebaseAnalyzer) {
        this._disposables = [];
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._componentGenerator = componentGenerator;
        this._codebaseAnalyzer = codebaseAnalyzer;
        // Set the webview's initial html content
        this._update();
        // Listen for when the panel is disposed
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'generateComponent':
                    await this._handleGenerateComponent(message.prompt);
                    return;
                case 'iterateComponent':
                    await this._handleIterateComponent(message.selectedCode, message.modification);
                    return;
                case 'analyzeWorkspace':
                    await this._handleAnalyzeWorkspace();
                    return;
            }
        }, null, this._disposables);
    }
    async _handleGenerateComponent(prompt) {
        try {
            this._panel.webview.postMessage({
                command: 'showProgress',
                message: 'Generating component...'
            });
            const workspaceInfo = await this._codebaseAnalyzer.analyzeWorkspace();
            const generatedCode = await this._componentGenerator.generateComponent(prompt, workspaceInfo);
            this._panel.webview.postMessage({
                command: 'componentGenerated',
                code: generatedCode
            });
            // Also insert into active editor if available
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                await editor.edit(editBuilder => {
                    const position = editor.selection.active;
                    editBuilder.insert(position, generatedCode);
                });
                await vscode.commands.executeCommand('editor.action.formatDocument');
            }
        }
        catch (error) {
            this._panel.webview.postMessage({
                command: 'showError',
                message: `Error generating component: ${error}`
            });
        }
    }
    async _handleIterateComponent(selectedCode, modification) {
        try {
            this._panel.webview.postMessage({
                command: 'showProgress',
                message: 'Modifying component...'
            });
            const workspaceInfo = await this._codebaseAnalyzer.analyzeWorkspace();
            const modifiedCode = await this._componentGenerator.iterateComponent(selectedCode, modification, workspaceInfo);
            this._panel.webview.postMessage({
                command: 'componentIterated',
                code: modifiedCode
            });
        }
        catch (error) {
            this._panel.webview.postMessage({
                command: 'showError',
                message: `Error modifying component: ${error}`
            });
        }
    }
    async _handleAnalyzeWorkspace() {
        try {
            const workspaceInfo = await this._codebaseAnalyzer.analyzeWorkspace();
            this._panel.webview.postMessage({
                command: 'workspaceAnalyzed',
                data: workspaceInfo
            });
        }
        catch (error) {
            this._panel.webview.postMessage({
                command: 'showError',
                message: `Error analyzing workspace: ${error}`
            });
        }
    }
    dispose() {
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
    _update() {
        const webview = this._panel.webview;
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }
    _getHtmlForWebview(webview) {
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
                        <p>Generate and iterate on UI components with AI assistance</p>
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

                        <section class="iterate-section">
                            <h2>Iterate Component</h2>
                            <div class="input-group">
                                <textarea 
                                    id="selectedCode" 
                                    placeholder="Paste the component code you want to modify here..."
                                    rows="5"
                                ></textarea>
                                <textarea 
                                    id="modification" 
                                    placeholder="Describe how you want to modify the component (e.g., 'make it responsive', 'add loading state')"
                                    rows="2"
                                ></textarea>
                                <button id="iterateBtn" class="primary-btn">Modify Component</button>
                            </div>
                        </section>

                        <section class="workspace-section">
                            <h2>Workspace Analysis</h2>
                            <button id="analyzeBtn" class="secondary-btn">Analyze Current Workspace</button>
                            <div id="workspaceInfo" class="workspace-info"></div>
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
exports.UICopilotPanel = UICopilotPanel;
UICopilotPanel.viewType = 'ui-copilot-panel';
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
//# sourceMappingURL=UICopilotPanel.js.map