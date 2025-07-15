/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ILogService } from '../../platform/log/common/logService';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { WCAGValidator } from '../accessibility/wcagValidator';
import { WorkspacePatternSearch } from '../search/workspacePatternSearch';

export class PaletteWebviewProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'palette.chatView';
	private view?: vscode.WebviewView;
	private componentAnalyzer: ComponentAnalyzer;
	private wcagValidator: WCAGValidator;
	private patternSearch: WorkspacePatternSearch;

	constructor(
		private readonly extensionUri: vscode.Uri,
		private readonly logService: ILogService
	) {
		this.componentAnalyzer = new ComponentAnalyzer();
		this.wcagValidator = new WCAGValidator(logService);
		this.patternSearch = new WorkspacePatternSearch(logService);
	}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	) {
		this.view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this.extensionUri]
		};

		webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

		// Handle messages from webview
		webviewView.webview.onDidReceiveMessage(async (data) => {
			switch (data.type) {
				case 'analyze':
					await this.handleAnalyze(data.fileUri);
					break;
				case 'generate':
					await this.handleGenerate(data.prompt);
					break;
				case 'critique':
					await this.handleCritique(data.fileUri);
					break;
				case 'audit':
					await this.handleAudit(data.fileUri);
					break;
				case 'patterns':
					await this.handlePatterns();
					break;
				case 'chat':
					await this.handleChat(data.message);
					break;
			}
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
						content: 'Please open a React component file to analyze.',
						isError: true
					});
					return;
				}
				targetUri = activeEditor.document.uri.toString();
			}

			const uri = vscode.Uri.parse(targetUri);
			const document = await vscode.workspace.openTextDocument(uri);
			const content = document.getText();

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
				content: this.formatAnalysisResponse(allComponents, wcagResults),
				isError: false
			});

		} catch (error) {
			this.logService.error('Analysis failed', error);
			this.sendMessage({
				type: 'response',
				content: 'Analysis failed. Please ensure you have a valid React component open.',
				isError: true
			});
		}
	}

	private async handleGenerate(prompt: string) {
		// Implementation for component generation
		this.sendMessage({
			type: 'response',
			content: `Generating component: ${prompt}...`,
			isError: false
		});
	}

	private async handleCritique(fileUri?: string) {
		// Implementation for design critique
		await this.handleAnalyze(fileUri);
	}

	private async handleAudit(fileUri?: string) {
		try {
			let targetUri = fileUri;
			if (!targetUri) {
				const activeEditor = vscode.window.activeTextEditor;
				if (!activeEditor) {
					this.sendMessage({
						type: 'response',
						content: 'Please open a React component file to audit.',
						isError: true
					});
					return;
				}
				targetUri = activeEditor.document.uri.toString();
			}

			const uri = vscode.Uri.parse(targetUri);
			const document = await vscode.workspace.openTextDocument(uri);
			const content = document.getText();

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
				content: 'Accessibility audit failed. Please ensure you have a valid React component open.',
				isError: true
			});
		}
	}

	private async handlePatterns() {
		try {
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
				content: 'Pattern search failed.',
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
• **analyze** - Analyze current component
• **generate** - Generate new component
• **audit** - Accessibility audit
• **patterns** - Find design patterns

Try: "analyze this component" or "audit accessibility"`,
				isError: false
			});
		}
	}

	private sendMessage(message: any) {
		if (this.view) {
			this.view.webview.postMessage(message);
		}
	}

	private formatAnalysisResponse(components: any[], wcagResults: any): string {
		const componentCount = components.length;
		return `## 🔍 Component Analysis

**Components Found:** ${componentCount}
**Accessibility Score:** ${wcagResults.score}/100

### Components in Workspace:
${components.slice(0, 5).map((comp: any) => `• ${comp.name || 'Unnamed'} (${comp.path || 'Unknown path'})`).join('\n') || 'No components found'}

### WCAG Compliance:
${wcagResults.violations?.map((v: any) => `• ${v.message}`).join('\n') || 'All checks passed'}`;
	}

	private formatWCAGResponse(wcagResults: any): string {
		return `## ♿ Accessibility Audit

**Overall Score:** ${wcagResults.score}/100
**Level:** ${wcagResults.level}

### Violations:
${wcagResults.violations?.map((v: any) => `• **${v.level}**: ${v.message}`).join('\n') || 'No violations found!'}

### Recommendations:
${wcagResults.recommendations?.map((r: any) => `• ${r}`).join('\n') || 'Component is accessible'}`;
	}

	private formatPatternsResponse(searchResult: any): string {
		const patterns = searchResult.patterns || [];
		const tailwindUtils = searchResult.tailwindUtilities || [];
		const components = searchResult.relevantComponents || [];
		
		return `## 🎨 Design Patterns Found

**Patterns:** ${patterns.length}
**Tailwind Utilities:** ${tailwindUtils.length}
**Relevant Components:** ${components.length}

### Common Patterns:
${patterns.slice(0, 5).map((p: any) => `• ${p.name} (${p.type})`).join('\n') || 'No patterns detected'}

### Suggested Components:
${components.slice(0, 3).map((c: any) => `• ${c.name}`).join('\n') || 'No suggestions'}`;
	}

	private getHtmlForWebview(webview: vscode.Webview): string {
		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Palette UI Agent</title>
	<style>
		body {
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
			color: var(--vscode-foreground);
			background-color: var(--vscode-editor-background);
			margin: 0;
			padding: 16px;
		}
		.chat-container {
			display: flex;
			flex-direction: column;
			height: 100vh;
		}
		.chat-messages {
			flex: 1;
			overflow-y: auto;
			margin-bottom: 16px;
			padding: 8px;
			border: 1px solid var(--vscode-panel-border);
			border-radius: 4px;
		}
		.message {
			margin-bottom: 12px;
			padding: 8px;
			border-radius: 4px;
		}
		.message.user {
			background-color: var(--vscode-textBlockQuote-background);
			text-align: right;
		}
		.message.assistant {
			background-color: var(--vscode-editor-background);
		}
		.message.error {
			background-color: var(--vscode-inputValidation-errorBackground);
			color: var(--vscode-inputValidation-errorForeground);
		}
		.input-container {
			display: flex;
			gap: 8px;
		}
		.chat-input {
			flex: 1;
			padding: 8px;
			border: 1px solid var(--vscode-input-border);
			border-radius: 4px;
			background-color: var(--vscode-input-background);
			color: var(--vscode-input-foreground);
		}
		.send-button {
			padding: 8px 16px;
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			border: none;
			border-radius: 4px;
			cursor: pointer;
		}
		.quick-actions {
			display: flex;
			gap: 8px;
			margin-bottom: 16px;
			flex-wrap: wrap;
		}
		.quick-action {
			padding: 6px 12px;
			background-color: var(--vscode-button-secondaryBackground);
			color: var(--vscode-button-secondaryForeground);
			border: none;
			border-radius: 4px;
			cursor: pointer;
			font-size: 12px;
		}
		.quick-action:hover {
			background-color: var(--vscode-button-secondaryHoverBackground);
		}
		h1 {
			color: var(--vscode-titleBar-activeForeground);
			margin-bottom: 16px;
			font-size: 18px;
		}
	</style>
</head>
<body>
	<div class="chat-container">
		<h1>🎨 Palette UI Agent</h1>
		
		<div class="quick-actions">
			<button class="quick-action" onclick="quickAction('analyze')">🔍 Analyze</button>
			<button class="quick-action" onclick="quickAction('generate')">✨ Generate</button>
			<button class="quick-action" onclick="quickAction('audit')">♿ Audit</button>
			<button class="quick-action" onclick="quickAction('patterns')">🎨 Patterns</button>
		</div>
		
		<div class="chat-messages" id="messages">
			<div class="message assistant">
				Hi! I'm your Palette UI Agent. I can help you with:
				<br><br>
				• <strong>Analyze</strong> components for design issues
				<br>• <strong>Generate</strong> new React components
				<br>• <strong>Audit</strong> accessibility compliance
				<br>• <strong>Find patterns</strong> in your codebase
				<br><br>
				Try clicking the buttons above or type a message!
			</div>
		</div>
		
		<div class="input-container">
			<input type="text" class="chat-input" id="chatInput" placeholder="Ask me about UI design, accessibility, or React patterns..." />
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
			messageDiv.innerHTML = content.replace(/\\n/g, '<br>');
			messages.appendChild(messageDiv);
			messages.scrollTop = messages.scrollHeight;
		}
		
		// Handle messages from extension
		window.addEventListener('message', event => {
			const message = event.data;
			if (message.type === 'response') {
				addMessage('assistant', message.content, message.isError);
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