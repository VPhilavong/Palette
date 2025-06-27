import * as vscode from 'vscode';

/**
 * WebView panel for live component preview
 */
export class LivePreviewPanel {
    private static currentPanel: LivePreviewPanel | undefined;
    private readonly panel: vscode.WebviewPanel;
    private disposables: vscode.Disposable[] = [];

    private constructor(panel: vscode.WebviewPanel) {
        this.panel = panel;
        this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
        this.panel.webview.html = this.getWebviewContent();
    }

    public static createOrShow(): void {
        const column = vscode.window.activeTextEditor?.viewColumn;

        if (LivePreviewPanel.currentPanel) {
            LivePreviewPanel.currentPanel.panel.reveal(column);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'uiCopilotPreview',
            'UI Copilot Preview',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true
            }
        );

        LivePreviewPanel.currentPanel = new LivePreviewPanel(panel);
    }

    public updatePreview(componentCode: string): void {
        // TODO: Implement live preview - Phase 6
        // Render React/Vue component in webview
        this.panel.webview.postMessage({ 
            command: 'updateComponent', 
            code: componentCode 
        });
    }

    private getWebviewContent(): string {
        // TODO: Implement webview HTML - Phase 6
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Component Preview</title>
            </head>
            <body>
                <div id="preview">
                    <h1>Component Preview</h1>
                    <p>Live preview coming in Phase 6!</p>
                </div>
            </body>
            </html>
        `;
    }

    public dispose(): void {
        LivePreviewPanel.currentPanel = undefined;
        this.panel.dispose();
        while (this.disposables.length) {
            const disposable = this.disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}