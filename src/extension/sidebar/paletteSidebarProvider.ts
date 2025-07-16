/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { ComponentGenerator } from '../../llm/componentGenerator';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { FileIndexer } from '../../codebase/fileIndexer';
import { FrameworkDetector } from '../../codebase/frameworkDetector';
import { WorkspaceIndex } from '../../types';
import { ModelClientFactory } from '../../llm/modelClient';

interface StreamMessage {
	type: 'stream' | 'complete' | 'error';
	content: string;
	requestId: string;
}

interface ActionRequest {
	type: 'build' | 'analyze' | 'fix';
	prompt?: string;
	requestId: string;
}

export class PaletteSidebarProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'palette.sidebar';
	
	private view?: vscode.WebviewView;  private componentGenerator: ComponentGenerator;
  private componentAnalyzer: ComponentAnalyzer;
  private fileIndexer: FileIndexer;
  private frameworkDetector: FrameworkDetector;
	private workspaceIndex: WorkspaceIndex | null = null;

	constructor(private readonly extensionUri: vscode.Uri) {    this.componentGenerator = new ComponentGenerator();
    this.componentAnalyzer = new ComponentAnalyzer();
    this.fileIndexer = new FileIndexer();
    this.frameworkDetector = new FrameworkDetector();
		this.initializeWorkspace();
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
		webviewView.webview.onDidReceiveMessage(async (message: any) => {
			if (message.type === 'chat') {
				await this.handleChatMessage(message);
			} else {
				// Legacy support for old action format
				await this.handleAction(message);
			}
		});
	}

	private async initializeWorkspace() {
		try {
			const files = await this.fileIndexer.indexWorkspace();
			
			// Use proper framework detection
			const projectMetadata = await this.frameworkDetector.detectProjectFrameworks();
			
			console.log('🔍 Framework detection results:', {
				frameworks: projectMetadata.frameworks.map(f => f.name),
				uiLibraries: projectMetadata.uiLibraries,
				hasTypeScript: projectMetadata.hasTypeScript
			});
			
			this.workspaceIndex = {
				files: files,
				components: [],
				project: {
					rootPath: projectMetadata.rootPath || vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
					frameworks: projectMetadata.frameworks,
					dependencies: projectMetadata.dependencies,
					devDependencies: projectMetadata.devDependencies,
					hasTypeScript: projectMetadata.hasTypeScript,
					uiLibraries: projectMetadata.uiLibraries,
					stateManagement: projectMetadata.stateManagement
				},
				lastUpdated: new Date()
			};
		} catch (error) {
			console.error('Failed to index workspace:', error);
		}
	}

	private async handleChatMessage(request: { type: 'chat'; prompt: string; requestId: string }) {
		if (!this.view) return;

		const { prompt, requestId } = request;
		
		try {
			// Check if OpenAI is configured
			const isConfigured = await ModelClientFactory.isConfigured();
			if (!isConfigured) {
				this.sendMessage({
					type: 'error',
					content: '🔑 **OpenAI API Key Required**\n\nPalette needs an OpenAI API key to work. Please configure it in VS Code settings.\n\n[Open Settings](command:workbench.action.openSettings?palette.openai.apiKey) | [Get API Key](https://platform.openai.com/api-keys)',
					requestId
				});
				ModelClientFactory.showConfigurationHelp();
				return;
			}
			
			// Determine action type based on prompt content
			let actionType: 'build' | 'analyze' | 'fix' = 'build';
			
			if (prompt.toLowerCase().includes('analyze') || prompt.toLowerCase().includes('current file')) {
				actionType = 'analyze';
			} else if (prompt.toLowerCase().includes('fix') || prompt.toLowerCase().includes('issue') || prompt.toLowerCase().includes('accessibility')) {
				actionType = 'fix';
			}
			
			switch (actionType) {
				case 'build':
					await this.handleBuild(prompt, requestId);
					break;
				case 'analyze':
					await this.handleAnalyze(requestId);
					break;
				case 'fix':
					await this.handleFix(prompt, requestId);
					break;
			}
		} catch (error) {
			this.sendMessage({
				type: 'error',
				content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
				requestId
			});
		}
	}

	private async handleAction(request: ActionRequest) {
		if (!this.view) return;

		const { type, prompt, requestId } = request;
		
		try {
			switch (type) {
				case 'build':
					await this.handleBuild(prompt || '', requestId);
					break;
				case 'analyze':
					await this.handleAnalyze(requestId);
					break;
				case 'fix':
					await this.handleFix(prompt || '', requestId);
					break;
			}
		} catch (error) {
			this.sendMessage({
				type: 'error',
				content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
				requestId
			});
		}
	}

	private async handleBuild(prompt: string, requestId: string) {
		if (!prompt.trim()) {
			this.sendMessage({
				type: 'error',
				content: 'Please provide a description of what to build',
				requestId
			});
			return;
		}

		// Stream initial response
		this.sendMessage({
			type: 'stream',
			content: '🔨 **Building Component**\n\nAnalyzing your request and project structure...',
			requestId
		});

		await this.delay(500);

		this.sendMessage({
			type: 'stream',
			content: '🔨 **Building Component**\n\n🎯 Analyzing intent and determining optimal file placement...',
			requestId
		});

		await this.delay(1000);

		this.sendMessage({
			type: 'stream',
			content: '🔨 **Building Component**\n\n🧠 Generating intelligent, context-aware code...',
			requestId
		});

		try {
			if (!this.workspaceIndex) {
				await this.initializeWorkspace();
			}

			// Use the enhanced multi-file generation method
			const result = await this.componentGenerator.generateComponentWithAnalysis(
				prompt,
				this.workspaceIndex
			);

			if (result && result.files.length > 0) {
				const { files, intent } = result;
				
				// Build success message
				let successMessage = `✅ **Files Created Successfully!**

**Request:** ${prompt}
**Intent:** ${intent.type} - ${intent.rationale}

**Generated Files:**
`;

				files.forEach((file, index) => {
					const relativePath = vscode.workspace.asRelativePath(file.path);
					successMessage += `${index + 1}. \`${relativePath}\`\n`;
				});

				// Show preview of main file
				const mainFile = files[0];
				if (mainFile.content.length > 0) {
					successMessage += `\n**Preview of ${path.basename(mainFile.path)}:**
\`\`\`tsx
${mainFile.content.length > 600 ? mainFile.content.slice(0, 600) + '...' : mainFile.content}
\`\`\``;
				}

				successMessage += `\n\nCheck your file explorer to see all generated files.`;

				if (intent.relatedFiles.length > 0) {
					successMessage += `\n\n**Related Files Found:**\n${intent.relatedFiles.map(f => `- ${f}`).join('\n')}`;
				}

				this.sendMessage({
					type: 'complete',
					content: successMessage,
					requestId
				});

				// Refresh workspace index
				this.initializeWorkspace();
			} else {
				throw new Error('Failed to generate any files');
			}
		} catch (error) {
			this.sendMessage({
				type: 'error',
				content: `Failed to build component: ${error instanceof Error ? error.message : 'Unknown error'}`,
				requestId
			});
		}
	}

	private async handleAnalyze(requestId: string) {
		const activeEditor = vscode.window.activeTextEditor;
		
		if (!activeEditor) {
			this.sendMessage({
				type: 'error',
				content: 'Please open a React component file to analyze',
				requestId
			});
			return;
		}

		this.sendMessage({
			type: 'stream',
			content: '🔍 **Analyzing Component**\n\nScanning current file...',
			requestId
		});

		await this.delay(800);

		try {
			const currentFile = activeEditor.document.uri.fsPath;
			const fileName = currentFile.split('/').pop() || 'Unknown';
			
			this.sendMessage({
				type: 'stream',
				content: '🔍 **Analyzing Component**\n\nRunning workspace analysis...',
				requestId
			});

			const components = await this.componentAnalyzer.analyzeWorkspaceComponents();
			const currentComponent = components.find(c => c.path === currentFile);

			let analysisResult = `🔍 **Component Analysis Complete**

**File:** ${fileName}
**Path:** ${currentFile}

`;

			if (currentComponent) {
				analysisResult += `### Component Details:
- **Name:** ${currentComponent.name}
- **Exports:** ${currentComponent.exports?.length || 0}
- **Imports:** ${currentComponent.imports?.length || 0}
- **Props:** ${currentComponent.props?.length || 0} detected
- **Hooks:** ${currentComponent.hooks?.length || 0} detected

### Code Quality Assessment:
✅ Component follows React best practices
${currentComponent.jsxElements?.length ? `✅ Uses ${currentComponent.jsxElements.length} JSX elements` : ''}
${currentComponent.props?.length ? `✅ Accepts ${currentComponent.props.length} props` : '⚠️ No props detected'}

### Recommendations:
${currentComponent.props?.length ? '• Consider adding TypeScript prop types for better type safety' : '• Consider adding props to make component more reusable'}
• Ensure accessibility attributes are included
• Consider responsive design patterns`;
			} else {
				analysisResult += '⚠️ Component not found in workspace analysis. Make sure it\'s a valid React component.';
			}

			this.sendMessage({
				type: 'complete',
				content: analysisResult,
				requestId
			});

		} catch (error) {
			this.sendMessage({
				type: 'error',
				content: `Analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
				requestId
			});
		}
	}

	private async handleFix(prompt: string, requestId: string) {
		this.sendMessage({
			type: 'stream',
			content: '🔧 **Fix Component**\n\nAnalyzing issues...',
			requestId
		});

		await this.delay(1000);

		this.sendMessage({
			type: 'complete',
			content: `🔧 **Fix Component Issues**

**Request:** ${prompt || 'General fixes'}

🚧 **Feature in Development**

The fix functionality is currently being developed. For now, you can:

1. **Use /analyze** to identify potential issues
2. **Use /build** to generate new components with best practices
3. **Manual fixes:** Based on analysis results, apply recommended changes

**Coming Soon:**
- Automatic accessibility fixes
- Code style improvements  
- Performance optimizations
- Design pattern updates`,
			requestId
		});
	}

	private sendMessage(message: StreamMessage) {
		if (this.view) {
			this.view.webview.postMessage(message);
		}
	}

	private delay(ms: number): Promise<void> {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	private getHtmlForWebview(webview: vscode.Webview): string {
		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Palette Assistant</title>
	<style>
		* {
			box-sizing: border-box;
		}
		
		body {
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
			font-size: 14px;
			color: var(--vscode-foreground);
			background: linear-gradient(135deg, var(--vscode-sidebar-background) 0%, rgba(var(--vscode-sidebar-background), 0.95) 100%);
			margin: 0;
			padding: 0;
			height: 100vh;
			display: flex;
			flex-direction: column;
			position: relative;
		}
		
		/* Subtle background pattern */
		body::before {
			content: '';
			position: fixed;
			top: 0;
			left: 0;
			right: 0;
			bottom: 0;
			background: 
				radial-gradient(circle at 25% 25%, rgba(100, 100, 255, 0.03) 0%, transparent 50%),
				radial-gradient(circle at 75% 75%, rgba(255, 100, 100, 0.03) 0%, transparent 50%);
			pointer-events: none;
			z-index: -1;
		}
		
		.header {
			padding: 20px;
			background: linear-gradient(135deg, var(--vscode-editor-background) 0%, rgba(var(--vscode-editor-background), 0.9) 100%);
			backdrop-filter: blur(10px);
			border-bottom: 1px solid rgba(var(--vscode-panel-border), 0.3);
			position: sticky;
			top: 0;
			z-index: 10;
			box-shadow: 0 2px 20px rgba(0, 0, 0, 0.05);
		}
		
		.logo {
			display: flex;
			align-items: center;
			gap: 12px;
			font-size: 22px;
			font-weight: 700;
			color: var(--vscode-titleBar-activeForeground);
			margin-bottom: 4px;
		}
		
		.logo::before {
			content: '🎨';
			font-size: 28px;
			filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
		}
		
		.subtitle {
			font-size: 13px;
			color: var(--vscode-descriptionForeground);
			font-weight: 500;
			opacity: 0.8;
		}
		
		.chat-container {
			flex: 1;
			display: flex;
			flex-direction: column;
			overflow: hidden;
		}
		
		.messages {
			flex: 1;
			overflow-y: auto;
			padding: 20px;
			display: flex;
			flex-direction: column;
			gap: 20px;
		}
		
		.messages::-webkit-scrollbar {
			width: 6px;
		}
		
		.messages::-webkit-scrollbar-track {
			background: transparent;
		}
		
		.messages::-webkit-scrollbar-thumb {
			background: rgba(var(--vscode-scrollbarSlider-background), 0.3);
			border-radius: 3px;
		}
		
		.messages::-webkit-scrollbar-thumb:hover {
			background: rgba(var(--vscode-scrollbarSlider-hoverBackground), 0.5);
		}
		
		.message {
			display: flex;
			flex-direction: column;
			max-width: 100%;
			animation: slideIn 0.3s ease-out;
		}
		
		@keyframes slideIn {
			from {
				opacity: 0;
				transform: translateY(10px);
			}
			to {
				opacity: 1;
				transform: translateY(0);
			}
		}
		
		.message-user {
			align-self: flex-end;
		}
		
		.message-assistant {
			align-self: flex-start;
		}
		
		.message-bubble {
			padding: 16px 20px;
			border-radius: 20px;
			max-width: 90%;
			word-wrap: break-word;
			line-height: 1.5;
			position: relative;
			backdrop-filter: blur(10px);
			transition: all 0.2s ease;
		}
		
		.message-bubble:hover {
			transform: translateY(-1px);
			box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
		}
		
		.message-user .message-bubble {
			background: linear-gradient(135deg, var(--vscode-button-background) 0%, rgba(var(--vscode-button-background), 0.9) 100%);
			color: var(--vscode-button-foreground);
			border-bottom-right-radius: 8px;
			border: 1px solid rgba(255, 255, 255, 0.1);
		}
		
		.message-assistant .message-bubble {
			background: linear-gradient(135deg, var(--vscode-input-background) 0%, rgba(var(--vscode-input-background), 0.95) 100%);
			color: var(--vscode-foreground);
			border: 1px solid rgba(var(--vscode-input-border), 0.3);
			border-bottom-left-radius: 8px;
			box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
		}
		
		.message-meta {
			font-size: 11px;
			color: var(--vscode-descriptionForeground);
			margin-top: 6px;
			padding: 0 12px;
			opacity: 0.7;
		}
		
		.typing-indicator {
			display: flex;
			align-items: center;
			gap: 10px;
			padding: 16px 20px;
			color: var(--vscode-descriptionForeground);
			font-size: 13px;
			font-weight: 500;
		}
		
		.typing-dots {
			display: flex;
			gap: 6px;
		}
		
		.typing-dot {
			width: 8px;
			height: 8px;
			border-radius: 50%;
			background: linear-gradient(135deg, var(--vscode-button-background) 0%, rgba(var(--vscode-button-background), 0.7) 100%);
			animation: typing 1.4s infinite ease-in-out;
		}
		
		.typing-dot:nth-child(1) { animation-delay: -0.32s; }
		.typing-dot:nth-child(2) { animation-delay: -0.16s; }
		
		@keyframes typing {
			0%, 80%, 100% { 
				opacity: 0.3;
				transform: scale(0.8);
			}
			40% { 
				opacity: 1;
				transform: scale(1.2);
			}
		}
		
		.input-container {
			padding: 20px;
			background: linear-gradient(135deg, var(--vscode-editor-background) 0%, rgba(var(--vscode-editor-background), 0.95) 100%);
			border-top: 1px solid rgba(var(--vscode-panel-border), 0.3);
			backdrop-filter: blur(10px);
		}
		
		.quick-actions {
			display: flex;
			gap: 8px;
			margin-bottom: 16px;
			flex-wrap: wrap;
		}
		
		.quick-action {
			padding: 8px 16px;
			background: linear-gradient(135deg, var(--vscode-button-secondaryBackground) 0%, rgba(var(--vscode-button-secondaryBackground), 0.9) 100%);
			color: var(--vscode-button-secondaryForeground);
			border: 1px solid rgba(var(--vscode-button-border), 0.3);
			border-radius: 20px;
			font-size: 12px;
			font-weight: 500;
			cursor: pointer;
			transition: all 0.2s ease;
			white-space: nowrap;
			backdrop-filter: blur(10px);
		}
		
		.quick-action:hover {
			background: linear-gradient(135deg, var(--vscode-button-secondaryHoverBackground) 0%, rgba(var(--vscode-button-secondaryHoverBackground), 0.9) 100%);
			transform: translateY(-1px);
			box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
		}
		
		.quick-action:active {
			transform: translateY(0);
		}
		
		.input-wrapper {
			display: flex;
			align-items: flex-end;
			gap: 12px;
			background: linear-gradient(135deg, var(--vscode-input-background) 0%, rgba(var(--vscode-input-background), 0.95) 100%);
			border: 1px solid rgba(var(--vscode-input-border), 0.3);
			border-radius: 24px;
			padding: 12px 16px;
			backdrop-filter: blur(10px);
			transition: all 0.2s ease;
		}
		
		.input-wrapper:focus-within {
			border-color: var(--vscode-focusBorder);
			box-shadow: 0 0 0 2px rgba(var(--vscode-focusBorder), 0.2);
		}
		
		.input-field {
			flex: 1;
			background: none;
			border: none;
			outline: none;
			color: var(--vscode-input-foreground);
			font-size: 14px;
			resize: none;
			max-height: 120px;
			min-height: 22px;
			line-height: 1.4;
			font-family: inherit;
		}
		
		.input-field::placeholder {
			color: var(--vscode-input-placeholderForeground);
			opacity: 0.7;
		}
		
		.send-button {
			background: linear-gradient(135deg, var(--vscode-button-background) 0%, rgba(var(--vscode-button-background), 0.9) 100%);
			color: var(--vscode-button-foreground);
			border: none;
			border-radius: 50%;
			width: 36px;
			height: 36px;
			cursor: pointer;
			display: flex;
			align-items: center;
			justify-content: center;
			transition: all 0.2s ease;
			font-size: 14px;
			backdrop-filter: blur(10px);
		}
		
		.send-button:hover:not(:disabled) {
			background: linear-gradient(135deg, var(--vscode-button-hoverBackground) 0%, rgba(var(--vscode-button-hoverBackground), 0.9) 100%);
			transform: translateY(-1px);
			box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
		}
		
		.send-button:active:not(:disabled) {
			transform: translateY(0);
		}
		
		.send-button:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
		
		.welcome-message {
			text-align: center;
			padding: 40px 20px;
			color: var(--vscode-descriptionForeground);
			animation: fadeIn 0.5s ease-out;
		}
		
		@keyframes fadeIn {
			from { opacity: 0; transform: translateY(20px); }
			to { opacity: 1; transform: translateY(0); }
		}
		
		.welcome-title {
			font-size: 24px;
			font-weight: 700;
			margin-bottom: 12px;
			color: var(--vscode-foreground);
			background: linear-gradient(135deg, var(--vscode-foreground) 0%, rgba(var(--vscode-foreground), 0.7) 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}
		
		.welcome-description {
			font-size: 15px;
			line-height: 1.6;
			margin-bottom: 30px;
			opacity: 0.9;
		}
		
		.welcome-suggestions {
			display: grid;
			gap: 12px;
			max-width: 400px;
			margin: 0 auto;
		}
		
		.suggestion {
			display: flex;
			align-items: center;
			gap: 12px;
			padding: 16px;
			background: linear-gradient(135deg, var(--vscode-input-background) 0%, rgba(var(--vscode-input-background), 0.95) 100%);
			border: 1px solid rgba(var(--vscode-input-border), 0.3);
			border-radius: 16px;
			cursor: pointer;
			transition: all 0.2s ease;
			text-align: left;
			color: var(--vscode-foreground);
			text-decoration: none;
			backdrop-filter: blur(10px);
		}
		
		.suggestion:hover {
			background: linear-gradient(135deg, var(--vscode-list-hoverBackground) 0%, rgba(var(--vscode-list-hoverBackground), 0.95) 100%);
			border-color: var(--vscode-focusBorder);
			transform: translateY(-2px);
			box-shadow: 0 6px 25px rgba(0, 0, 0, 0.1);
		}
		
		.suggestion-icon {
			font-size: 20px;
			flex-shrink: 0;
		}
		
		.suggestion-text {
			font-size: 14px;
			font-weight: 500;
		}
		
		pre {
			background: linear-gradient(135deg, var(--vscode-textPreformat-background) 0%, rgba(var(--vscode-textPreformat-background), 0.95) 100%);
			padding: 16px;
			border-radius: 12px;
			overflow-x: auto;
			font-size: 13px;
			border: 1px solid rgba(var(--vscode-panel-border), 0.3);
			margin: 12px 0;
			backdrop-filter: blur(10px);
		}
		
		code {
			background: linear-gradient(135deg, var(--vscode-textCodeBlock-background) 0%, rgba(var(--vscode-textCodeBlock-background), 0.95) 100%);
			padding: 3px 8px;
			border-radius: 6px;
			font-size: 13px;
			font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
		}
		
		h1, h2, h3, h4, h5, h6 {
			margin: 16px 0 8px 0;
			font-weight: 600;
		}
		
		h1 { font-size: 20px; }
		h2 { font-size: 18px; }
		h3 { font-size: 16px; }
		
		strong {
			font-weight: 600;
		}
		
		.hidden {
			display: none;
		}
		
		/* Responsive design */
		@media (max-width: 480px) {
			.header {
				padding: 16px;
			}
			
			.messages {
				padding: 16px;
			}
			
			.input-container {
				padding: 16px;
			}
			
			.welcome-message {
				padding: 32px 16px;
			}
			
			.message-bubble {
				max-width: 95%;
			}
		}
	</style>
</head>
<body>
	<div class="header">
		<div class="logo">
			Palette
		</div>
		<div class="subtitle">AI Assistant for Intelligent UI Development</div>
	</div>
	
	<div class="chat-container">
		<div class="messages" id="messages">
			<div class="welcome-message">
				<div class="welcome-title">Hello! I'm Palette</div>
				<div class="welcome-description">I'm your AI assistant for intelligent UI development. I can analyze your codebase, understand patterns, and generate components that fit perfectly into your project.</div>
				<div class="welcome-suggestions">
					<div class="suggestion" onclick="insertPrompt('Create a responsive pricing card with three tiers using Tailwind CSS')">
						<div class="suggestion-icon">💳</div>
						<div class="suggestion-text">Create a responsive pricing card with three tiers</div>
					</div>
					<div class="suggestion" onclick="insertPrompt('Build a modern navigation header with logo and menu items')">
						<div class="suggestion-icon">🧭</div>
						<div class="suggestion-text">Build a modern navigation header with logo and menu</div>
					</div>
					<div class="suggestion" onclick="insertPrompt('Design a user profile card with avatar and stats')">
						<div class="suggestion-icon">👤</div>
						<div class="suggestion-text">Design a user profile card with avatar and stats</div>
					</div>
					<div class="suggestion" onclick="insertPrompt('Create a complete login feature with form validation')">
						<div class="suggestion-icon">🔐</div>
						<div class="suggestion-text">Create a complete login feature with form validation</div>
					</div>
				</div>
			</div>
		</div>
		
		<div class="input-container">
			<div class="quick-actions">
				<button class="quick-action" onclick="insertPrompt('Analyze current file')">🔍 Analyze</button>
				<button class="quick-action" onclick="insertPrompt('Fix accessibility issues')">♿ Fix A11y</button>
				<button class="quick-action" onclick="insertPrompt('Create a feature with multiple components')">📦 Feature</button>
				<button class="quick-action" onclick="insertPrompt('Build a complete page')">📄 Page</button>
			</div>
			
			<div class="input-wrapper">
				<textarea 
					id="messageInput" 
					class="input-field" 
					placeholder="Describe what you want to build, analyze, or fix. I'll understand your intent and place files intelligently..."
					rows="1"
				></textarea>
				<button class="send-button" id="sendButton" onclick="sendMessage()">
					<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
						<path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
					</svg>
				</button>
			</div>
		</div>
	</div>

	<script>
		const vscode = acquireVsCodeApi();
		let currentRequestId = null;
		let messageCounter = 0;
		
		// DOM elements
		const messages = document.getElementById('messages');
		const messageInput = document.getElementById('messageInput');
		const sendButton = document.getElementById('sendButton');
		
		// Auto-resize textarea
		messageInput.addEventListener('input', function() {
			this.style.height = 'auto';
			this.style.height = this.scrollHeight + 'px';
		});
		
		// Send on Enter (but not Shift+Enter)
		messageInput.addEventListener('keydown', function(e) {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				sendMessage();
			}
		});
		
		function insertPrompt(text) {
			messageInput.value = text;
			messageInput.focus();
			messageInput.style.height = 'auto';
			messageInput.style.height = messageInput.scrollHeight + 'px';
		}
		
		function sendMessage() {
			const prompt = messageInput.value.trim();
			if (!prompt) return;
			
			// Clear input
			messageInput.value = '';
			messageInput.style.height = 'auto';
			
			// Add user message
			addMessage('user', prompt);
			
			// Show typing indicator
			const typingId = addTypingIndicator();
			
			// Send to extension
			currentRequestId = generateRequestId();
			sendButton.disabled = true;
			
			vscode.postMessage({
				type: 'chat',
				prompt: prompt,
				requestId: currentRequestId
			});
		}
		
		function addMessage(sender, content, isStreaming = false) {
			const messageDiv = document.createElement('div');
			messageDiv.className = \`message message-\${sender}\`;
			
			const bubbleDiv = document.createElement('div');
			bubbleDiv.className = 'message-bubble';
			
			if (isStreaming) {
				bubbleDiv.id = \`streaming-\${currentRequestId}\`;
			}
			
			// Format content for assistant messages
			if (sender === 'assistant') {
				bubbleDiv.innerHTML = formatMessage(content);
			} else {
				bubbleDiv.textContent = content;
			}
			
			messageDiv.appendChild(bubbleDiv);
			
			// Add timestamp
			const metaDiv = document.createElement('div');
			metaDiv.className = 'message-meta';
			metaDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
			messageDiv.appendChild(metaDiv);
			
			messages.appendChild(messageDiv);
			scrollToBottom();
			
			return messageDiv;
		}
		
		function addTypingIndicator() {
			const typingDiv = document.createElement('div');
			typingDiv.className = 'message message-assistant';
			typingDiv.id = 'typing-indicator';
			
			const bubbleDiv = document.createElement('div');
			bubbleDiv.className = 'message-bubble typing-indicator';
			bubbleDiv.innerHTML = \`
				<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
					<path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,6A1,1 0 0,1 13,7A1,1 0 0,1 12,8A1,1 0 0,1 11,7A1,1 0 0,1 12,6M15,7A1,1 0 0,1 16,8A1,1 0 0,1 15,9A1,1 0 0,1 14,8A1,1 0 0,1 15,7M9,7A1,1 0 0,1 10,8A1,1 0 0,1 9,9A1,1 0 0,1 8,8A1,1 0 0,1 9,7Z"/>
				</svg>
				Palette is thinking...
				<div class="typing-dots">
					<div class="typing-dot"></div>
					<div class="typing-dot"></div>
					<div class="typing-dot"></div>
				</div>
			\`;
			
			typingDiv.appendChild(bubbleDiv);
			messages.appendChild(typingDiv);
			scrollToBottom();
			
			return 'typing-indicator';
		}
		
		function removeTypingIndicator() {
			const typingElement = document.getElementById('typing-indicator');
			if (typingElement) {
				typingElement.style.animation = 'slideOut 0.2s ease-in';
				setTimeout(() => typingElement.remove(), 200);
			}
		}
		
		function formatMessage(content) {
			return content
				.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
				.replace(/\\*(.*?)\\*/g, '<em>$1</em>')
				.replace(/\`\`\`([\\s\\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>')
				.replace(/\`(.*?)\`/g, '<code>$1</code>')
				.replace(/^### (.*$)/gm, '<h3>$1</h3>')
				.replace(/^## (.*$)/gm, '<h2>$1</h2>')
				.replace(/^# (.*$)/gm, '<h1>$1</h1>')
				.replace(/\\n/g, '<br>');
		}
		
		function scrollToBottom() {
			requestAnimationFrame(() => {
				messages.scrollTo({
					top: messages.scrollHeight,
					behavior: 'smooth'
				});
			});
		}
		
		function generateRequestId() {
			return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
		}
		
		// Handle messages from extension
		window.addEventListener('message', (event) => {
			const message = event.data;
			
			if (message.requestId === currentRequestId) {
				switch (message.type) {
					case 'stream':
						removeTypingIndicator();
						const streamingElement = document.getElementById(\`streaming-\${currentRequestId}\`);
						if (streamingElement) {
							streamingElement.innerHTML = formatMessage(message.content);
						} else {
							addMessage('assistant', message.content, true);
						}
						break;
					case 'complete':
						removeTypingIndicator();
						const completedElement = document.getElementById(\`streaming-\${currentRequestId}\`);
						if (completedElement) {
							completedElement.innerHTML = formatMessage(message.content);
							completedElement.id = '';
						} else {
							addMessage('assistant', message.content);
						}
						sendButton.disabled = false;
						currentRequestId = null;
						break;
					case 'error':
						removeTypingIndicator();
						addMessage('assistant', \`<div style="color: var(--vscode-errorForeground); background: rgba(var(--vscode-errorBackground), 0.1); padding: 12px; border-radius: 8px; border-left: 3px solid var(--vscode-errorForeground);">❌ \${message.content}</div>\`);
						sendButton.disabled = false;
						currentRequestId = null;
						break;
				}
			}
		});
		
		// Clear welcome message on first interaction
		let hasInteracted = false;
		messageInput.addEventListener('focus', function() {
			if (!hasInteracted) {
				const welcomeMsg = document.querySelector('.welcome-message');
				if (welcomeMsg) {
					welcomeMsg.style.animation = 'fadeOut 0.3s ease-out';
					setTimeout(() => welcomeMsg.style.display = 'none', 300);
				}
				hasInteracted = true;
			}
		});
		
		// Add fade out animation
		const style = document.createElement('style');
		style.textContent = \`
			@keyframes slideOut {
				from { opacity: 1; transform: translateY(0); }
				to { opacity: 0; transform: translateY(-10px); }
			}
			
			@keyframes fadeOut {
				from { opacity: 1; transform: scale(1); }
				to { opacity: 0; transform: scale(0.95); }
			}
		\`;
		document.head.appendChild(style);
		
		// Add keyboard shortcuts
		document.addEventListener('keydown', function(e) {
			// Ctrl/Cmd + K to focus input
			if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
				e.preventDefault();
				messageInput.focus();
			}
			
			// Escape to clear input
			if (e.key === 'Escape' && document.activeElement === messageInput) {
				messageInput.value = '';
				messageInput.style.height = 'auto';
				messageInput.blur();
			}
		});
		
		// Initialize
		messageInput.focus();
	</script>
</body>
</html>`;
	}
}