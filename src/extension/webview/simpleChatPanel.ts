/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ILogService } from '../../platform/log/common/logService';
import { ComponentGenerator } from '../../llm/componentGenerator';
import { FileIndexer } from '../../codebase/fileIndexer';
import { WorkspaceIndex } from '../../types';

export class SimpleChatPanel {
	public static currentPanel: SimpleChatPanel | undefined;
	public static readonly viewType = 'simpleChatPanel';

	private readonly panel: vscode.WebviewPanel;
	private readonly extensionUri: vscode.Uri;
	private disposables: vscode.Disposable[] = [];
	private componentGenerator: ComponentGenerator;
	private fileIndexer: FileIndexer;
	private workspaceIndex: WorkspaceIndex | null = null;

	public static createOrShow(extensionUri: vscode.Uri, logService: ILogService) {
		const column = vscode.window.activeTextEditor
			? vscode.window.activeTextEditor.viewColumn
			: undefined;

		// If we already have a panel, show it.
		if (SimpleChatPanel.currentPanel) {
			SimpleChatPanel.currentPanel.panel.reveal(column);
			return SimpleChatPanel.currentPanel;
		}

		// Otherwise, create a new panel.
		const panel = vscode.window.createWebviewPanel(
			SimpleChatPanel.viewType,
			'Build',
			column || vscode.ViewColumn.One,
			{
				enableScripts: true,
				localResourceRoots: [extensionUri]
			}
		);

		SimpleChatPanel.currentPanel = new SimpleChatPanel(panel, extensionUri, logService);
		return SimpleChatPanel.currentPanel;
	}

	private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, private readonly logService: ILogService) {
		this.panel = panel;
		this.extensionUri = extensionUri;

		// Initialize core components
		this.componentGenerator = new ComponentGenerator();
		this.fileIndexer = new FileIndexer();

		// Index workspace on startup
		this.initializeWorkspace();

		// Set the webview's initial html content
		this.update();

		// Listen for when the panel is disposed
		this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

		// Handle messages from the webview
		this.panel.webview.onDidReceiveMessage(
			async (message) => {
				if (message.type === 'build') {
					await this.handleBuild(message.prompt);
				}
			},
			null,
			this.disposables
		);
	}

	private async initializeWorkspace() {
		try {
			this.logService.info('Indexing workspace for component generation...');
			const files = await this.fileIndexer.indexWorkspace();
			// Create a proper WorkspaceIndex structure
			this.workspaceIndex = {
				files: files,
				components: [],
				project: {
					rootPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
					frameworks: [],
					dependencies: {},
					devDependencies: {},
					hasTypeScript: false,
					uiLibraries: [],
					stateManagement: []
				},
				lastUpdated: new Date()
			};
			this.logService.info('Workspace indexed successfully');
		} catch (error) {
			this.logService.error('Failed to index workspace', error);
		}
	}

	private async handleBuild(prompt: string) {
		try {
			this.sendMessage({
				type: 'response',
				content: '🔨 Building component...',
				isBuilding: true
			});

			// Use the full agentic generation that includes smart file insertion
			const generatedCode = await this.componentGenerator.generateComponent(
				prompt,
				this.workspaceIndex
			);

			if (!generatedCode) {
				this.sendMessage({
					type: 'response',
					content: '❌ Failed to generate component. Please try a different prompt.',
					isBuilding: false
				});
				return;
			}

			// Show success message with the generated code
			this.sendMessage({
				type: 'response',
				content: `✅ **Component created successfully!**

The component has been automatically placed in the optimal location based on your project structure.

**Generated Code:**
\`\`\`tsx
${generatedCode}
\`\`\`

Check your file explorer to see the new component file(s).`,
				isBuilding: false
			});

		} catch (error) {
			this.logService.error('Component generation failed', error);
			this.sendMessage({
				type: 'response',
				content: `❌ Generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
				isBuilding: false
			});
		}
	}

	private sendMessage(message: any) {
		this.panel.webview.postMessage(message);
	}

	public dispose() {
		SimpleChatPanel.currentPanel = undefined;
		this.panel.dispose();
		while (this.disposables.length) {
			const x = this.disposables.pop();
			if (x) {
				x.dispose();
			}
		}
	}

	private update() {
		const webview = this.panel.webview;
		this.panel.webview.html = this.getHtmlForWebview(webview);
	}

	private getHtmlForWebview(webview: vscode.Webview): string {
		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Build</title>
	<style>
		body {
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
			font-size: 14px;
			color: var(--vscode-foreground);
			background-color: var(--vscode-editor-background);
			margin: 0;
			padding: 20px;
			line-height: 1.6;
		}
		.container {
			max-width: 800px;
			margin: 0 auto;
			display: flex;
			flex-direction: column;
			height: calc(100vh - 40px);
		}
		.header {
			text-align: center;
			margin-bottom: 24px;
			padding-bottom: 16px;
			border-bottom: 1px solid var(--vscode-panel-border);
		}
		.title {
			font-size: 28px;
			font-weight: 700;
			color: var(--vscode-titleBar-activeForeground);
			margin: 0;
		}
		.subtitle {
			font-size: 16px;
			color: var(--vscode-descriptionForeground);
			margin: 8px 0 0 0;
		}
		.chat-area {
			flex: 1;
			overflow-y: auto;
			margin-bottom: 20px;
			padding: 20px;
			border: 1px solid var(--vscode-panel-border);
			border-radius: 8px;
			background-color: var(--vscode-panel-background);
		}
		.message {
			margin-bottom: 20px;
			padding: 16px;
			border-radius: 8px;
		}
		.message.user {
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			margin-left: 20%;
		}
		.message.assistant {
			background-color: var(--vscode-textBlockQuote-background);
			border-left: 4px solid var(--vscode-textBlockQuote-border);
		}
		.message.code {
			background-color: var(--vscode-textPreformat-background);
			font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
			font-size: 13px;
			overflow-x: auto;
			white-space: pre-wrap;
		}
		.building {
			display: inline-block;
			animation: pulse 1.5s ease-in-out infinite;
		}
		@keyframes pulse {
			0%, 100% { opacity: 1; }
			50% { opacity: 0.5; }
		}
		.input-area {
			display: flex;
			gap: 12px;
			align-items: stretch;
		}
		.input-container {
			flex: 1;
			display: flex;
			flex-direction: column;
		}
		.prompt-input {
			flex: 1;
			min-height: 80px;
			padding: 16px;
			border: 1px solid var(--vscode-input-border);
			border-radius: 8px;
			background-color: var(--vscode-input-background);
			color: var(--vscode-input-foreground);
			font-size: 14px;
			resize: vertical;
			font-family: inherit;
		}
		.prompt-input:focus {
			outline: none;
			border-color: var(--vscode-focusBorder);
		}
		.hint {
			font-size: 12px;
			color: var(--vscode-descriptionForeground);
			margin-top: 8px;
		}
		.build-button {
			padding: 16px 24px;
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			border: none;
			border-radius: 8px;
			cursor: pointer;
			font-size: 16px;
			font-weight: 600;
			min-width: 100px;
		}
		.build-button:hover {
			background-color: var(--vscode-button-hoverBackground);
		}
		.build-button:disabled {
			opacity: 0.6;
			cursor: not-allowed;
		}
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<h1 class="title">🔨 Build</h1>
			<p class="subtitle">Describe what you want to build and I'll generate the code</p>
		</div>
		
		<div class="chat-area" id="chatArea">
			<div class="message assistant">
				👋 <strong>Ready to build!</strong>
				<br><br>
				Describe the component you want and I'll generate the React code for you.
				<br><br>
				<em>Example:</em> "Create a responsive pricing card with three tiers using Tailwind CSS"
			</div>
		</div>
		
		<div class="input-area">
			<div class="input-container">
				<textarea 
					class="prompt-input" 
					id="promptInput" 
					placeholder="Describe the component you want to build..."
				></textarea>
				<div class="hint">Be specific about functionality, styling, and any special requirements</div>
			</div>
			<button class="build-button" id="buildButton" onclick="build()">
				Build
			</button>
		</div>
	</div>

	<script>
		const vscode = acquireVsCodeApi();
		let isBuilding = false;
		let currentCode = '';
		
		function build() {
			const input = document.getElementById('promptInput');
			const button = document.getElementById('buildButton');
			const prompt = input.value.trim();
			
			if (!prompt || isBuilding) return;
			
			isBuilding = true;
			button.disabled = true;
			button.textContent = 'Building...';
			
			// Add user message
			addMessage('user', prompt);
			
			// Clear input
			input.value = '';
			
			// Send to extension
			vscode.postMessage({
				type: 'build',
				prompt: prompt
			});
		}
		
		function addMessage(sender, content, isCode = false, isBuilding = false) {
			const chatArea = document.getElementById('chatArea');
			const messageDiv = document.createElement('div');
			messageDiv.className = 'message ' + sender + (isCode ? ' code' : '');
			
			if (isBuilding) {
				messageDiv.innerHTML = '<span class="building">' + content + '</span>';
			} else {
				// Convert markdown-like content to HTML
				const formattedContent = content
					.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
					.replace(/\\*(.*?)\\*/g, '<em>$1</em>')
					.replace(/\`\`\`(.*?)\`\`\`/gs, '<pre><code>$1</code></pre>')
					.replace(/\`(.*?)\`/g, '<code>$1</code>')
					.replace(/^### (.*$)/gm, '<h3>$1</h3>')
					.replace(/^## (.*$)/gm, '<h2>$1</h2>')
					.replace(/^# (.*$)/gm, '<h1>$1</h1>')
					.replace(/\\n/g, '<br>');
				messageDiv.innerHTML = formattedContent;
			}
			
			chatArea.appendChild(messageDiv);
			chatArea.scrollTop = chatArea.scrollHeight;
		}
		
		
		// Handle messages from extension
		window.addEventListener('message', event => {
			const message = event.data;
			const button = document.getElementById('buildButton');
			
			if (message.type === 'response') {
				addMessage('assistant', message.content, false, message.isBuilding);
				
				if (!message.isBuilding) {
					isBuilding = false;
					button.disabled = false;
					button.textContent = 'Build';
				}
			}
		});
		
		// Enter to build (Ctrl+Enter)
		document.getElementById('promptInput').addEventListener('keydown', function(e) {
			if (e.key === 'Enter' && e.ctrlKey) {
				build();
			}
		});
	</script>
</body>
</html>`;
	}
}