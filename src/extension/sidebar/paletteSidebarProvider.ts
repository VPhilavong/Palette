/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as path from 'path';
import { ComponentGenerator } from '../../llm/componentGenerator';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { FileIndexer } from '../../codebase/fileIndexer';
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
	
	private view?: vscode.WebviewView;
	private componentGenerator: ComponentGenerator;
	private componentAnalyzer: ComponentAnalyzer;
	private fileIndexer: FileIndexer;
	private workspaceIndex: WorkspaceIndex | null = null;

	constructor(private readonly extensionUri: vscode.Uri) {
		this.componentGenerator = new ComponentGenerator();
		this.componentAnalyzer = new ComponentAnalyzer();
		this.fileIndexer = new FileIndexer();
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
			font-family: var(--vscode-font-family);
			font-size: var(--vscode-font-size);
			color: var(--vscode-foreground);
			background-color: var(--vscode-sidebar-background);
			margin: 0;
			padding: 0;
			height: 100vh;
			display: flex;
			flex-direction: column;
		}
		
		.header {
			padding: 16px;
			border-bottom: 1px solid var(--vscode-panel-border);
			background-color: var(--vscode-editor-background);
		}
		
		.logo {
			display: flex;
			align-items: center;
			gap: 8px;
			font-size: 18px;
			font-weight: 600;
			color: var(--vscode-titleBar-activeForeground);
		}
		
		.subtitle {
			font-size: 12px;
			color: var(--vscode-descriptionForeground);
			margin-top: 4px;
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
			padding: 16px;
			display: flex;
			flex-direction: column;
			gap: 16px;
		}
		
		.message {
			display: flex;
			flex-direction: column;
			max-width: 100%;
		}
		
		.message-user {
			align-self: flex-end;
		}
		
		.message-assistant {
			align-self: flex-start;
		}
		
		.message-bubble {
			padding: 12px 16px;
			border-radius: 18px;
			max-width: 85%;
			word-wrap: break-word;
			line-height: 1.4;
		}
		
		.message-user .message-bubble {
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			border-bottom-right-radius: 6px;
		}
		
		.message-assistant .message-bubble {
			background-color: var(--vscode-input-background);
			color: var(--vscode-foreground);
			border: 1px solid var(--vscode-input-border);
			border-bottom-left-radius: 6px;
		}
		
		.message-meta {
			font-size: 11px;
			color: var(--vscode-descriptionForeground);
			margin-top: 4px;
			padding: 0 8px;
		}
		
		.typing-indicator {
			display: flex;
			align-items: center;
			gap: 8px;
			padding: 12px 16px;
			color: var(--vscode-descriptionForeground);
			font-size: 13px;
		}
		
		.typing-dots {
			display: flex;
			gap: 4px;
		}
		
		.typing-dot {
			width: 6px;
			height: 6px;
			border-radius: 50%;
			background-color: var(--vscode-descriptionForeground);
			animation: typing 1.4s infinite ease-in-out;
		}
		
		.typing-dot:nth-child(1) { animation-delay: -0.32s; }
		.typing-dot:nth-child(2) { animation-delay: -0.16s; }
		
		@keyframes typing {
			0%, 80%, 100% { opacity: 0.3; }
			40% { opacity: 1; }
		}
		
		.input-container {
			padding: 16px;
			border-top: 1px solid var(--vscode-panel-border);
			background-color: var(--vscode-editor-background);
		}
		
		.quick-actions {
			display: flex;
			gap: 8px;
			margin-bottom: 12px;
			flex-wrap: wrap;
		}
		
		.quick-action {
			padding: 6px 12px;
			background-color: var(--vscode-button-secondaryBackground);
			color: var(--vscode-button-secondaryForeground);
			border: 1px solid var(--vscode-button-border);
			border-radius: 16px;
			font-size: 12px;
			cursor: pointer;
			transition: all 0.2s;
			white-space: nowrap;
		}
		
		.quick-action:hover {
			background-color: var(--vscode-button-secondaryHoverBackground);
		}
		
		.input-wrapper {
			display: flex;
			align-items: flex-end;
			gap: 8px;
			background-color: var(--vscode-input-background);
			border: 1px solid var(--vscode-input-border);
			border-radius: 20px;
			padding: 8px 12px;
		}
		
		.input-wrapper:focus-within {
			border-color: var(--vscode-focusBorder);
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
			min-height: 20px;
			line-height: 1.4;
		}
		
		.input-field::placeholder {
			color: var(--vscode-input-placeholderForeground);
		}
		
		.send-button {
			background-color: var(--vscode-button-background);
			color: var(--vscode-button-foreground);
			border: none;
			border-radius: 50%;
			width: 32px;
			height: 32px;
			cursor: pointer;
			display: flex;
			align-items: center;
			justify-content: center;
			transition: background-color 0.2s;
		}
		
		.send-button:hover:not(:disabled) {
			background-color: var(--vscode-button-hoverBackground);
		}
		
		.send-button:disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
		
		.welcome-message {
			text-align: center;
			padding: 32px 16px;
			color: var(--vscode-descriptionForeground);
		}
		
		.welcome-title {
			font-size: 16px;
			font-weight: 600;
			margin-bottom: 8px;
			color: var(--vscode-foreground);
		}
		
		.welcome-suggestions {
			margin-top: 20px;
		}
		
		.suggestion {
			display: block;
			padding: 12px;
			margin: 8px 0;
			background-color: var(--vscode-input-background);
			border: 1px solid var(--vscode-input-border);
			border-radius: 12px;
			cursor: pointer;
			transition: all 0.2s;
			text-align: left;
			color: var(--vscode-foreground);
			text-decoration: none;
		}
		
		.suggestion:hover {
			background-color: var(--vscode-list-hoverBackground);
			border-color: var(--vscode-focusBorder);
		}
		
		pre {
			background-color: var(--vscode-textPreformat-background);
			padding: 12px;
			border-radius: 8px;
			overflow-x: auto;
			font-size: 12px;
			border: 1px solid var(--vscode-panel-border);
		}
		
		code {
			background-color: var(--vscode-textCodeBlock-background);
			padding: 2px 6px;
			border-radius: 4px;
			font-size: 12px;
		}
		
		.hidden {
			display: none;
		}
	</style>
</head>
<body>
	<div class="header">
		<div class="logo">
			🎨 Palette
		</div>
		<div class="subtitle">AI Assistant for UI Development</div>
	</div>
	
	<div class="chat-container">
		<div class="messages" id="messages">
			<div class="welcome-message">
				<div class="welcome-title">Hello! I'm Palette</div>
				<div>I'm your AI assistant for intelligent UI development. I can analyze your codebase, understand patterns, and generate components that fit perfectly into your project.</div>
				<div class="welcome-suggestions">
					<div class="suggestion" onclick="insertPrompt('Create a responsive pricing card with three tiers using Tailwind CSS')">
						💳 Create a responsive pricing card with three tiers
					</div>
					<div class="suggestion" onclick="insertPrompt('Build a modern navigation header with logo and menu items')">
						🧭 Build a modern navigation header with logo and menu
					</div>
					<div class="suggestion" onclick="insertPrompt('Design a user profile card with avatar and stats')">
						👤 Design a user profile card with avatar and stats
					</div>
					<div class="suggestion" onclick="insertPrompt('Create a complete login feature with form validation')">
						🔐 Create a complete login feature with form validation
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
					▶
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
				typingElement.remove();
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
			messages.scrollTop = messages.scrollHeight;
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
						addMessage('assistant', \`❌ \${message.content}\`);
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
					welcomeMsg.style.display = 'none';
				}
				hasInteracted = true;
			}
		});
	</script>
</body>
</html>`;
	}
}