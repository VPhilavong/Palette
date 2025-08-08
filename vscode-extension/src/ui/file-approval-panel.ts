/**
 * File Approval Panel
 * GitHub Copilot-style file approval interface with diff views and batch operations
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { FilePreview, ApprovalRequest, ApprovalResponse } from '../tools/types';

export class FileApprovalPanel {
    public static readonly viewType = 'palette.fileApproval';
    
    private panel: vscode.WebviewPanel | undefined;
    private extensionUri: vscode.Uri;
    private currentRequest: ApprovalRequest | undefined;
    private resolveApproval: ((response: ApprovalResponse) => void) | undefined;

    constructor(extensionUri: vscode.Uri) {
        this.extensionUri = extensionUri;
    }

    /**
     * Show approval panel for file operations
     */
    async requestApproval(request: ApprovalRequest): Promise<ApprovalResponse> {
        return new Promise((resolve) => {
            this.currentRequest = request;
            this.resolveApproval = resolve;
            this.createOrShowPanel();
        });
    }

    /**
     * Create or show the approval panel
     */
    private createOrShowPanel(): void {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.Beside);
            this.updateContent();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            FileApprovalPanel.viewType,
            '🎨 Palette AI - File Operations Approval',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.extensionUri, 'media'),
                    vscode.Uri.joinPath(this.extensionUri, 'out')
                ]
            }
        );

        // Handle panel disposal
        this.panel.onDidDispose(() => {
            this.panel = undefined;
            // Auto-reject if panel is closed without response
            if (this.resolveApproval) {
                this.resolveApproval({
                    approved: false,
                    skipInFuture: false
                });
                this.resolveApproval = undefined;
            }
        });

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage((message) => {
            this.handleWebviewMessage(message);
        });

        this.updateContent();
    }

    /**
     * Update panel content
     */
    private updateContent(): void {
        if (!this.panel || !this.currentRequest) {
            return;
        }

        this.panel.webview.html = this.getWebviewContent();
    }

    /**
     * Handle messages from webview
     */
    private handleWebviewMessage(message: any): void {
        switch (message.command) {
            case 'approve':
                this.handleApproval(true, message.skipInFuture || false);
                break;
            case 'reject':
                this.handleApproval(false, false);
                break;
            case 'getFileContent':
                this.handleGetFileContent(message.filePath);
                break;
            case 'previewFile':
                this.handlePreviewFile(message.filePath);
                break;
        }
    }

    /**
     * Handle approval response
     */
    private handleApproval(approved: boolean, skipInFuture: boolean): void {
        if (this.resolveApproval) {
            this.resolveApproval({
                approved,
                skipInFuture
            });
            this.resolveApproval = undefined;
        }

        if (this.panel) {
            this.panel.dispose();
        }
    }

    /**
     * Handle file content request
     */
    private async handleGetFileContent(filePath: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const content = await vscode.workspace.fs.readFile(uri);
            const textContent = new TextDecoder().decode(content);
            
            this.panel?.webview.postMessage({
                command: 'fileContent',
                filePath,
                content: textContent,
                exists: true
            });
        } catch (error) {
            this.panel?.webview.postMessage({
                command: 'fileContent',
                filePath,
                content: '',
                exists: false
            });
        }
    }

    /**
     * Handle file preview request
     */
    private async handlePreviewFile(filePath: string): Promise<void> {
        try {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            await vscode.window.showTextDocument(document, vscode.ViewColumn.One);
        } catch (error) {
            vscode.window.showErrorMessage(`Cannot preview file: ${filePath}`);
        }
    }

    /**
     * Generate webview content
     */
    private getWebviewContent(): string {
        if (!this.currentRequest) {
            return '<html><body>No approval request</body></html>';
        }

        const { operation, description, files, dangerLevel } = this.currentRequest;
        
        // Determine danger styling
        const dangerColor = {
            'safe': '#28a745',
            'caution': '#ffc107', 
            'dangerous': '#dc3545'
        }[dangerLevel];

        const dangerIcon = {
            'safe': '✅',
            'caution': '⚠️',
            'dangerous': '🚨'
        }[dangerLevel];

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Operations Approval</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 20px;
            margin: 0;
        }

        .header {
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .operation-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .danger-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
            background-color: ${dangerColor};
        }

        .description {
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
        }

        .files-section {
            margin: 20px 0;
        }

        .section-title {
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 16px;
        }

        .file-list {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
        }

        .file-item {
            padding: 12px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            justify-content: between;
            align-items: center;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .file-info {
            flex: 1;
        }

        .file-path {
            font-family: var(--vscode-editor-font-family);
            color: var(--vscode-textLink-foreground);
            font-size: 14px;
            margin-bottom: 4px;
        }

        .file-operation {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
            text-transform: uppercase;
        }

        .file-actions {
            display: flex;
            gap: 8px;
        }

        .btn {
            padding: 6px 12px;
            border: 1px solid var(--vscode-button-border);
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            cursor: pointer;
            border-radius: 2px;
            font-size: 12px;
        }

        .btn:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        .btn-primary {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .btn-secondary {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }

        .actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            padding-top: 20px;
            border-top: 1px solid var(--vscode-panel-border);
            margin-top: 20px;
        }

        .approve-btn {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            padding: 10px 20px;
            font-size: 14px;
        }

        .reject-btn {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            padding: 10px 20px;
            font-size: 14px;
        }

        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 15px 0;
        }

        .code-preview {
            background-color: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 12px;
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 8px;
            display: none;
        }

        .stats {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
        }

        .stats-item {
            display: inline-block;
            margin-right: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="operation-title">
            <span>${dangerIcon}</span>
            <span>${operation}</span>
            <span class="danger-badge">${dangerLevel}</span>
        </div>
        <div class="description">${description}</div>
    </div>

    ${files && files.length > 0 ? `
    <div class="stats">
        <span class="stats-item"><strong>${files.length}</strong> files affected</span>
        <span class="stats-item"><strong>${files.filter(f => f.operation === 'create').length}</strong> new files</span>
        <span class="stats-item"><strong>${files.filter(f => f.operation === 'update').length}</strong> modified files</span>
        <span class="stats-item"><strong>${files.filter(f => f.operation === 'delete').length}</strong> deleted files</span>
    </div>

    <div class="files-section">
        <div class="section-title">📁 Files to be modified:</div>
        <div class="file-list">
            ${files.map((file, index) => `
                <div class="file-item">
                    <div class="file-info">
                        <div class="file-path">${file.path}</div>
                        <div class="file-operation">${file.operation} • ${file.exists ? 'exists' : 'new file'}</div>
                        <div class="code-preview" id="preview-${index}"></div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-secondary" onclick="togglePreview(${index}, '${file.path}', ${file.content ? `'${file.content.replace(/'/g, "\\'")}'` : 'null'})">
                            👁️ Preview
                        </button>
                        <button class="btn btn-secondary" onclick="openFile('${file.path}')">
                            📂 Open
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    </div>
    ` : ''}

    ${dangerLevel !== 'safe' ? `
    <div class="checkbox-container">
        <input type="checkbox" id="skipInFuture" />
        <label for="skipInFuture">Don't ask again for ${dangerLevel} operations</label>
    </div>
    ` : ''}

    <div class="actions">
        <button class="btn reject-btn" onclick="reject()">
            ❌ Reject
        </button>
        <button class="btn approve-btn" onclick="approve()">
            ✅ Approve Changes
        </button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();

        function approve() {
            const skipInFuture = document.getElementById('skipInFuture')?.checked || false;
            vscode.postMessage({
                command: 'approve',
                skipInFuture: skipInFuture
            });
        }

        function reject() {
            vscode.postMessage({
                command: 'reject'
            });
        }

        function togglePreview(index, filePath, content) {
            const preview = document.getElementById('preview-' + index);
            if (preview.style.display === 'block') {
                preview.style.display = 'none';
                return;
            }

            if (content && content !== 'null') {
                preview.textContent = content;
                preview.style.display = 'block';
            } else {
                // Request file content from extension
                vscode.postMessage({
                    command: 'getFileContent',
                    filePath: filePath
                });
                
                // Listen for response
                window.addEventListener('message', function(event) {
                    const message = event.data;
                    if (message.command === 'fileContent' && message.filePath === filePath) {
                        preview.textContent = message.exists ? message.content : 'File does not exist';
                        preview.style.display = 'block';
                    }
                });
            }
        }

        function openFile(filePath) {
            vscode.postMessage({
                command: 'previewFile',
                filePath: filePath
            });
        }

        // Focus on approve button for accessibility
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelector('.approve-btn').focus();
        });
    </script>
</body>
</html>`;
    }

    /**
     * Dispose of the panel
     */
    dispose(): void {
        if (this.panel) {
            this.panel.dispose();
        }
    }
}