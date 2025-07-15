/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ILogService } from '../../platform/log/common/logService';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { WCAGValidator } from '../accessibility/wcagValidator';
import { WorkspacePatternSearch } from '../search/workspacePatternSearch';

export class PaletteChatPanel {
	public static currentPanel: PaletteChatPanel | undefined;
	public static readonly viewType = 'paletteChatPanel';

	private readonly panel: vscode.WebviewPanel;
	private readonly extensionUri: vscode.Uri;
	private disposables: vscode.Disposable[] = [];
	private componentAnalyzer: ComponentAnalyzer;
	private wcagValidator: WCAGValidator;
	private patternSearch: WorkspacePatternSearch;

	public static createOrShow(extensionUri: vscode.Uri, logService: ILogService) {
		const column = vscode.window.activeTextEditor
			? vscode.window.activeTextEditor.viewColumn
			: undefined;

		// If we already have a panel, show it.
		if (PaletteChatPanel.currentPanel) {
			PaletteChatPanel.currentPanel.panel.reveal(column);
			return PaletteChatPanel.currentPanel;
		}

		// Otherwise, create a new panel.
		const panel = vscode.window.createWebviewPanel(
			PaletteChatPanel.viewType,
			'AI Chat',
			column || vscode.ViewColumn.One,
			{
				enableScripts: true,
				localResourceRoots: [
					vscode.Uri.joinPath(extensionUri, 'media'),
					vscode.Uri.joinPath(extensionUri, 'out', 'compiled')
				]
			}
		);

		PaletteChatPanel.currentPanel = new PaletteChatPanel(panel, extensionUri, logService);
		return PaletteChatPanel.currentPanel;
	}

	public static kill() {
		PaletteChatPanel.currentPanel?.dispose();
		PaletteChatPanel.currentPanel = undefined;
	}

	public static revive(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, logService: ILogService) {
		PaletteChatPanel.currentPanel = new PaletteChatPanel(panel, extensionUri, logService);
	}

	private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, private readonly logService: ILogService) {
		this.panel = panel;
		this.extensionUri = extensionUri;

		// Initialize AI components
		this.componentAnalyzer = new ComponentAnalyzer();
		this.wcagValidator = new WCAGValidator(logService);
		this.patternSearch = new WorkspacePatternSearch(logService);

		// Set the webview's initial html content
		this.update();

		// Listen for when the panel is disposed
		// This happens when the user closes the panel or when the panel is closed programmatically
		this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

		// Handle messages from the webview
		this.panel.webview.onDidReceiveMessage(
			async (message) => {
				switch (message.type) {
					case 'analyze':
						await this.handleAnalyze(message.fileUri);
						break;
					case 'generate':
						await this.handleGenerate(message.prompt);
						break;
					case 'audit':
						await this.handleAudit(message.fileUri);
						break;
					case 'patterns':
						await this.handlePatterns();
						break;
					case 'chat':
						await this.handleChat(message.message);
						break;
				}
			},
			null,
			this.disposables
		);
	}

	public triggerAnalyze(uri?: vscode.Uri) {
		this.panel.webview.postMessage({
			type: 'trigger-analyze',
			uri: uri?.toString()
		});
	}

	public triggerGenerate() {
		this.panel.webview.postMessage({
			type: 'trigger-generate'
		});
	}

	private async handleAnalyze(fileUri?: string) {
		try {
			let targetUri = fileUri;
			if (!targetUri) {
				const activeEditor = vscode.window.activeTextEditor;
				if (!activeEditor) {
					this.sendMessage({
						type: 'response',
						content: '⚠️ Please open a React component file to analyze.',
						isError: true
					});
					return;
				}
				targetUri = activeEditor.document.uri.toString();
			}

			const uri = vscode.Uri.parse(targetUri);
			const document = await vscode.workspace.openTextDocument(uri);
			const content = document.getText();

			// Show loading
			this.sendMessage({
				type: 'response',
				content: '🔍 Analyzing component...',
				isError: false
			});

			// Analyze component - get all workspace components first
			const allComponents = await this.componentAnalyzer.analyzeWorkspaceComponents();
			
			// Find the current component in the analyzed components
			const currentComponent = allComponents.find(comp => comp.path === uri.fsPath) || {
				name: 'Current Component',
				path: uri.fsPath,
				exports: [],
				imports: []
			} as any;
			
			// Run WCAG validation
			const wcagResults = await this.wcagValidator.validateComponent(currentComponent);

			this.sendMessage({
				type: 'response',
				content: this.formatAnalysisResponse(allComponents, wcagResults, currentComponent),
				isError: false
			});

		} catch (error) {
			this.logService.error('Analysis failed', error);
			this.sendMessage({
				type: 'response',
				content: '❌ Analysis failed. Please ensure you have a valid React component open.',
				isError: true
			});
		}
	}

	private async handleGenerate(prompt: string) {
		this.sendMessage({
			type: 'response',
			content: `✨ Generating component: ${prompt}...\n\n🚧 Component generation is in development.`,
			isError: false
		});
	}

	private async handleAudit(fileUri?: string) {
		try {
			let targetUri = fileUri;
			if (!targetUri) {
				const activeEditor = vscode.window.activeTextEditor;
				if (!activeEditor) {
					this.sendMessage({
						type: 'response',
						content: '⚠️ Please open a React component file to audit.',
						isError: true
					});
					return;
				}
				targetUri = activeEditor.document.uri.toString();
			}

			const uri = vscode.Uri.parse(targetUri);
			const document = await vscode.workspace.openTextDocument(uri);

			// Show loading
			this.sendMessage({
				type: 'response',
				content: '♿ Running accessibility audit...',
				isError: false
			});

			// Create component info for WCAG validation
			const componentInfo = {
				name: 'Current Component',
				path: uri.fsPath,
				exports: [],
				imports: []
			} as any;

			const wcagResults = await this.wcagValidator.validateComponent(componentInfo);

			this.sendMessage({
				type: 'response',
				content: this.formatWCAGResponse(wcagResults),
				isError: false
			});

		} catch (error) {
			this.logService.error('Accessibility audit failed', error);
			this.sendMessage({
				type: 'response',
				content: '❌ Accessibility audit failed. Please ensure you have a valid React component open.',
				isError: true
			});
		}
	}

	private async handlePatterns() {
		try {
			this.sendMessage({
				type: 'response',
				content: '🎨 Searching for design patterns...',
				isError: false
			});

			// Get workspace components first
			const allComponents = await this.componentAnalyzer.analyzeWorkspaceComponents();
			const patterns = await this.patternSearch.searchDesignPatterns('common patterns', allComponents);
			
			this.sendMessage({
				type: 'response',
				content: this.formatPatternsResponse(patterns),
				isError: false
			});

		} catch (error) {
			this.logService.error('Pattern search failed', error);
			this.sendMessage({
				type: 'response',
				content: '❌ Pattern search failed.',
				isError: true
			});
		}
	}

	private async handleChat(message: string) {
		// Simple command routing based on message content
		const command = message.toLowerCase().trim();
		
		if (command.includes('analyze') || command.includes('review')) {
			await this.handleAnalyze();
		} else if (command.includes('generate') || command.includes('create')) {
			await this.handleGenerate(message);
		} else if (command.includes('audit') || command.includes('accessibility') || command.includes('a11y')) {
			await this.handleAudit();
		} else if (command.includes('pattern') || command.includes('suggest')) {
			await this.handlePatterns();
		} else {
			this.sendMessage({
				type: 'response',
				content: `I can help with:

• **analyze** - Analyze current component for design and accessibility
• **generate** - Generate new React components  
• **audit** - Run accessibility compliance checks
• **patterns** - Find design patterns in your codebase

Try: "analyze this component", "audit accessibility", or "find button patterns"`,
				isError: false
			});
		}
	}

	private sendMessage(message: any) {
		this.panel.webview.postMessage(message);
	}

	private formatAnalysisResponse(components: any[], wcagResults: any, currentComponent: any): string {
		const componentCount = components.length;
		return `## 🔍 Component Analysis Complete

**File:** ${currentComponent.name}
**Workspace Components:** ${componentCount}
**Accessibility Score:** ${wcagResults.score}/100

### Current Component:
• **Path:** ${currentComponent.path}
• **Exports:** ${currentComponent.exports?.length || 0}
• **Imports:** ${currentComponent.imports?.length || 0}

### WCAG Compliance:
${wcagResults.violations?.map((v: any) => `• ❌ **${v.level}**: ${v.message}`).join('\n') || '✅ All accessibility checks passed!'}

### Recommendations:
${wcagResults.recommendations?.map((r: any) => `• 💡 ${r}`).join('\n') || '• Component follows accessibility best practices'}`;
	}

	private formatWCAGResponse(wcagResults: any): string {
		return `## ♿ Accessibility Audit Complete

**Overall Score:** ${wcagResults.score}/100
**Compliance Level:** ${wcagResults.level}

### Issues Found:
${wcagResults.violations?.map((v: any) => `• ❌ **${v.level}**: ${v.message}`).join('\n') || '✅ No accessibility violations found!'}

### Recommendations:
${wcagResults.recommendations?.map((r: any) => `• 💡 ${r}`).join('\n') || '• Component is fully accessible'}`;
	}

	private formatPatternsResponse(searchResult: any): string {
		const patterns = searchResult.patterns || [];
		const tailwindUtils = searchResult.tailwindUtilities || [];
		const components = searchResult.relevantComponents || [];
		
		return `## 🎨 Design Patterns Found

**Pattern Types:** ${patterns.length}
**Tailwind Utilities:** ${tailwindUtils.length}  
**Relevant Components:** ${components.length}

### Common Patterns:
${patterns.slice(0, 5).map((p: any) => `• **${p.name}** (${p.type})`).join('\n') || '• No patterns detected'}

### Suggested Components:
${components.slice(0, 3).map((c: any) => `• ${c.name}`).join('\n') || '• No component suggestions'}

### Tailwind Utilities:
${tailwindUtils.slice(0, 3).map((u: any) => `• ${u.utility} - ${u.description}`).join('\n') || '• No utility patterns found'}`;
	}

	public dispose() {
		PaletteChatPanel.currentPanel = undefined;

		// Clean up our resources
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
	<title>AI Chat</title>
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
		.chat-container {
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
			font-size: 24px;
			font-weight: 600;
			color: var(--vscode-titleBar-activeForeground);
			margin: 0;
		}
		.subtitle {
			font-size: 14px;
			color: var(--vscode-descriptionForeground);
			margin: 8px 0 0 0;
		}
		.chat-messages {
			flex: 1;
			overflow-y: auto;
			margin-bottom: 20px;
			padding: 16px;
			border: 1px solid var(--vscode-panel-border);
			border-radius: 8px;
			background-color: var(--vscode-panel-background);
		}
		.message {
			margin-bottom: 16px;
			padding: 12px 16px;
			border-radius: 8px;
			max-width: 85%;
		}
		.message.user {
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			margin-left: auto;
			text-align: right;
		}
		.message.assistant {
			background-color: var(--vscode-textBlockQuote-background);
			border-left: 4px solid var(--vscode-textBlockQuote-border);
		}
		.message.error {
			background-color: var(--vscode-inputValidation-errorBackground);
			color: var(--vscode-inputValidation-errorForeground);
			border-left: 4px solid var(--vscode-inputValidation-errorBorder);
		}
		.quick-actions {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
			gap: 12px;
			margin-bottom: 20px;
		}
		.quick-action {
			padding: 12px 16px;
			background-color: var(--vscode-button-secondaryBackground);
			color: var(--vscode-button-secondaryForeground);
			border: 1px solid var(--vscode-button-border);
			border-radius: 6px;
			cursor: pointer;
			text-align: center;
			font-size: 13px;
			font-weight: 500;
			transition: all 0.2s;
		}
		.quick-action:hover {
			background-color: var(--vscode-button-secondaryHoverBackground);
			transform: translateY(-1px);
		}
		.input-container {
			display: flex;
			gap: 12px;
			align-items: center;
		}
		.chat-input {
			flex: 1;
			padding: 12px 16px;
			border: 1px solid var(--vscode-input-border);
			border-radius: 6px;
			background-color: var(--vscode-input-background);
			color: var(--vscode-input-foreground);
			font-size: 14px;
		}
		.chat-input:focus {
			outline: none;
			border-color: var(--vscode-focusBorder);
		}
		.send-button {
			padding: 12px 20px;
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			border: none;
			border-radius: 6px;
			cursor: pointer;
			font-size: 14px;
			font-weight: 500;
		}
		.send-button:hover {
			background-color: var(--vscode-button-hoverBackground);
		}
		pre {
			background-color: var(--vscode-textPreformat-background);
			padding: 12px;
			border-radius: 4px;
			overflow-x: auto;
			font-size: 12px;
		}
		code {
			background-color: var(--vscode-textCodeBlock-background);
			padding: 2px 4px;
			border-radius: 3px;
			font-size: 12px;
		}
	</style>
</head>
<body>
	<div class="chat-container">
		<div class="header">
			<h1 class="title">🎨 AI Chat</h1>
			<p class="subtitle">Your AI assistant for UI design, accessibility, and React development</p>
		</div>
		
		<div class="quick-actions">
			<button class="quick-action" onclick="quickAction('analyze')">🔍 Analyze Component</button>
			<button class="quick-action" onclick="quickAction('generate')">✨ Generate Component</button>
			<button class="quick-action" onclick="quickAction('audit')">♿ Accessibility Audit</button>
			<button class="quick-action" onclick="quickAction('patterns')">🎨 Find Patterns</button>
		</div>
		
		<div class="chat-messages" id="messages">
			<div class="message assistant">
				👋 Hi! I'm your AI assistant for UI development. I can help you with:
				<br><br>
				• <strong>Component Analysis</strong> - Review design patterns and accessibility
				<br>• <strong>Code Generation</strong> - Create new React components with best practices  
				<br>• <strong>Accessibility Audits</strong> - WCAG compliance checking
				<br>• <strong>Pattern Discovery</strong> - Find reusable patterns in your codebase
				<br><br>
				Click the buttons above or ask me anything!
			</div>
		</div>
		
		<div class="input-container">
			<input type="text" class="chat-input" id="chatInput" placeholder="Ask about UI design, accessibility, or React patterns..." />
			<button class="send-button" onclick="sendMessage()">Send</button>
		</div>
	</div>

	<script>
		const vscode = acquireVsCodeApi();
		
		function quickAction(action) {
			addMessage('user', action);
			vscode.postMessage({
				type: action
			});
		}
		
		function sendMessage() {
			const input = document.getElementById('chatInput');
			const message = input.value.trim();
			if (message) {
				addMessage('user', message);
				input.value = '';
				vscode.postMessage({
					type: 'chat',
					message: message
				});
			}
		}
		
		function addMessage(sender, content, isError = false) {
			const messages = document.getElementById('messages');
			const messageDiv = document.createElement('div');
			messageDiv.className = 'message ' + sender + (isError ? ' error' : '');
			// Convert markdown-like content to HTML
			const formattedContent = content
				.replace(/\\n/g, '<br>')
				.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
				.replace(/\\*(.*?)\\*/g, '<em>$1</em>')
				.replace(/^### (.*$)/gm, '<h3>$1</h3>')
				.replace(/^## (.*$)/gm, '<h2>$1</h2>')
				.replace(/^# (.*$)/gm, '<h1>$1</h1>')
				.replace(/^• (.*$)/gm, '<li>$1</li>')
				.replace(/(<li>.*<\\/li>)/s, '<ul>$1</ul>');
			messageDiv.innerHTML = formattedContent;
			messages.appendChild(messageDiv);
			messages.scrollTop = messages.scrollHeight;
		}
		
		// Handle messages from extension
		window.addEventListener('message', event => {
			const message = event.data;
			if (message.type === 'response') {
				addMessage('assistant', message.content, message.isError);
			} else if (message.type === 'trigger-analyze') {
				addMessage('user', 'analyze');
				vscode.postMessage({ type: 'analyze', fileUri: message.uri });
			} else if (message.type === 'trigger-generate') {
				addMessage('user', 'generate');
				vscode.postMessage({ type: 'generate', prompt: 'Generate component' });
			}
		});
		
		// Enter key to send
		document.getElementById('chatInput').addEventListener('keypress', function(e) {
			if (e.key === 'Enter') {
				sendMessage();
			}
		});
	</script>
</body>
</html>`;
	}
}