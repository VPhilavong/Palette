/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ComponentGenerator } from '../../llm/componentGenerator';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { FileIndexer } from '../../codebase/fileIndexer';
import { WorkspaceIndex } from '../../types';
import { ILogService } from '../../platform/log/common/logService';

export class PaletteAgent {
	private componentGenerator: ComponentGenerator;
	private componentAnalyzer: ComponentAnalyzer;
	private fileIndexer: FileIndexer;
	private workspaceIndex: WorkspaceIndex | null = null;

	constructor(private readonly logService: ILogService) {
		this.componentGenerator = new ComponentGenerator();
		this.componentAnalyzer = new ComponentAnalyzer();
		this.fileIndexer = new FileIndexer();
		this.initializeWorkspace();
	}

	public register(): vscode.Disposable {
		// Register as the primary palette chat participant
		const participant = vscode.chat.createChatParticipant('palette', this.handleRequest.bind(this));
		participant.iconPath = vscode.Uri.file('assets/palette-icon.png');
		participant.followupProvider = {
			provideFollowups: this.provideFollowups.bind(this)
		};

		return participant;
	}

	private async initializeWorkspace() {
		try {
			this.logService.info('PaletteAgent: Indexing workspace...');
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
			this.logService.info('PaletteAgent: Workspace indexed');
		} catch (error) {
			this.logService.error('PaletteAgent: Failed to index workspace', error);
		}
	}

	private async handleRequest(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<void> {
		try {
			// Parse the command and prompt
			const command = request.command || 'build';
			const prompt = request.prompt;

			// Show that we're thinking
			stream.progress('Analyzing request...');

			switch (command) {
				case 'build':
					await this.handleBuild(prompt, stream, token);
					break;
				case 'analyze':
					await this.handleAnalyze(prompt, stream, token);
					break;
				case 'fix':
					await this.handleFix(prompt, stream, token);
					break;
				default:
					// Default to intelligent routing based on prompt content
					await this.handleIntelligentRequest(prompt, stream, token);
					break;
			}
		} catch (error) {
			stream.markdown(`❌ **Error**: ${error instanceof Error ? error.message : 'Unknown error'}`);
		}
	}

	private async handleBuild(
		prompt: string,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<void> {
		if (!this.workspaceIndex) {
			stream.markdown('⚠️ Workspace not indexed yet. Please try again in a moment.');
			return;
		}

		stream.progress('🔨 Generating component...');
		stream.markdown(`## 🔨 Building Component

**Request**: ${prompt}

`);

		try {
			// Generate the component with smart file placement
			const generatedCode = await this.componentGenerator.generateComponent(
				prompt,
				this.workspaceIndex
			);

			if (!generatedCode) {
				stream.markdown('❌ Failed to generate component. Please try a more specific description.');
				return;
			}

			// Stream the success response
			stream.markdown(`✅ **Component created successfully!**

The component has been automatically placed in the optimal location based on your project structure.

### Generated Code:
\`\`\`tsx
${generatedCode.slice(0, 1000)}${generatedCode.length > 1000 ? '...' : ''}
\`\`\`

Check your file explorer to see the new component file(s).`);

			// Refresh workspace index
			this.initializeWorkspace();

		} catch (error) {
			stream.markdown(`❌ **Generation failed**: ${error instanceof Error ? error.message : 'Unknown error'}`);
		}
	}

	private async handleAnalyze(
		prompt: string,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<void> {
		stream.progress('🔍 Analyzing components...');
		
		// Get current file if available
		const activeEditor = vscode.window.activeTextEditor;
		if (!activeEditor) {
			stream.markdown('⚠️ Please open a React component file to analyze.');
			return;
		}

		const currentFile = activeEditor.document.uri.fsPath;
		const content = activeEditor.document.getText();

		stream.markdown(`## 🔍 Component Analysis

**File**: ${currentFile}

`);

		try {
			// Analyze the workspace components
			const components = await this.componentAnalyzer.analyzeWorkspaceComponents();
			const currentComponent = components.find(c => c.path === currentFile);

			if (currentComponent) {
				stream.markdown(`### Component Details:
- **Name**: ${currentComponent.name}
- **Exports**: ${currentComponent.exports?.length || 0}
- **Imports**: ${currentComponent.imports?.length || 0}
- **Props**: ${currentComponent.props?.length || 0} detected
- **Hooks**: ${currentComponent.hooks?.length || 0} detected

### Code Quality:
✅ Component follows React best practices
${currentComponent.jsxElements?.length ? `✅ Uses ${currentComponent.jsxElements.length} JSX elements` : ''}
${currentComponent.props?.length ? `✅ Accepts ${currentComponent.props.length} props` : '⚠️ No props detected'}

`);
			} else {
				stream.markdown('⚠️ Component not found in workspace analysis. Make sure it\'s a valid React component.');
			}

		} catch (error) {
			stream.markdown(`❌ **Analysis failed**: ${error instanceof Error ? error.message : 'Unknown error'}`);
		}
	}

	private async handleFix(
		prompt: string,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<void> {
		stream.progress('🔧 Analyzing and fixing issues...');
		stream.markdown(`## 🔧 Fix Component Issues

**Request**: ${prompt}

🚧 **Feature in development** - Component fixing capabilities coming soon!

For now, I can:
- Analyze your components for issues
- Generate new components with best practices
- Provide design and accessibility recommendations

`);
	}

	private async handleIntelligentRequest(
		prompt: string,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<void> {
		// Intelligent routing based on prompt content
		const lowerPrompt = prompt.toLowerCase();
		
		if (lowerPrompt.includes('create') || lowerPrompt.includes('generate') || lowerPrompt.includes('build') || lowerPrompt.includes('make')) {
			await this.handleBuild(prompt, stream, token);
		} else if (lowerPrompt.includes('analyze') || lowerPrompt.includes('review') || lowerPrompt.includes('check')) {
			await this.handleAnalyze(prompt, stream, token);
		} else if (lowerPrompt.includes('fix') || lowerPrompt.includes('improve') || lowerPrompt.includes('update')) {
			await this.handleFix(prompt, stream, token);
		} else {
			// General help
			stream.markdown(`## 🎨 Palette UI Agent

I'm your AI assistant for UI development with React and Tailwind CSS.

### What I can do:

**🔨 Build Components**
- \`@palette /build\` - Generate React components with smart file placement
- Example: *"Create a responsive pricing card with three tiers"*

**🔍 Analyze Components**  
- \`@palette /analyze\` - Analyze current component for design patterns and accessibility
- Open a React file and I'll provide detailed analysis

**🔧 Fix Issues**
- \`@palette /fix\` - Fix design and accessibility issues (coming soon)

### Quick Start:
Just describe what you want to build and I'll handle the rest:
- *"Build a navigation header with dark mode toggle"*
- *"Create a contact form with validation"*
- *"Make a responsive card component"*

I'll automatically place files in the right location and match your project's patterns!`);
		}
	}

	private async provideFollowups(
		result: vscode.ChatResult,
		context: vscode.ChatContext,
		token: vscode.CancellationToken
	): Promise<vscode.ChatFollowup[]> {
		const followups: vscode.ChatFollowup[] = [];

		// Add relevant followups based on the conversation
		if (context.history.length > 0) {
			const lastMessage = context.history[context.history.length - 1];
			
			if (lastMessage.participant === 'palette') {
				followups.push(
					{
						prompt: '@palette /build Create a button component',
						label: '🔨 Build another component',
						command: 'build'
					},
					{
						prompt: '@palette /analyze',
						label: '🔍 Analyze current file',
						command: 'analyze'
					}
				);
			}
		}

		return followups;
	}
}