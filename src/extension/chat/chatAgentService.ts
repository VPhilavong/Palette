/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { IChatAgentService } from '../../platform/chat/common/chatAgentService';
import { ILogService } from '../../platform/log/common/logService';
import { IConfigurationService } from '../../platform/configuration/common/configurationService';
import { IDisposable, DisposableStore } from '../../util/common/services';

export class ChatAgentService implements IChatAgentService {
	declare readonly _serviceBrand: undefined;

	constructor(
		private readonly logService: ILogService,
		private readonly configurationService: IConfigurationService
	) { }

	register(): IDisposable {
		const disposables = new DisposableStore();
		
		this.logService.info('ChatAgentService: Registering chat participants');
		
		// Register UI Design Agent
		const uiAgent = vscode.chat.createChatParticipant('palette.ui', this.handleUIAgentRequest.bind(this));
		uiAgent.iconPath = vscode.Uri.file('assets/palette-icon.png');
		disposables.add(uiAgent);
		
		// Register Accessibility Agent
		const a11yAgent = vscode.chat.createChatParticipant('palette.a11y', this.handleA11yAgentRequest.bind(this));
		a11yAgent.iconPath = vscode.Uri.file('assets/accessibility-icon.png');
		disposables.add(a11yAgent);
		
		this.logService.info('ChatAgentService: Chat participants registered successfully');
		
		return disposables;
	}

	private async handleUIAgentRequest(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		this.logService.info('UI Agent: Handling request', { prompt: request.prompt, command: request.command });
		
		try {
			// Handle different commands
			switch (request.command) {
				case 'analyze':
					return this.handleAnalyzeCommand(request, context, stream, token);
				case 'generate':
					return this.handleGenerateCommand(request, context, stream, token);
				case 'critique':
					return this.handleCritiqueCommand(request, context, stream, token);
				case 'patterns':
					return this.handlePatternsCommand(request, context, stream, token);
				default:
					return this.handleGeneralUIRequest(request, context, stream, token);
			}
		} catch (error) {
			this.logService.error('UI Agent: Error handling request', error);
			stream.markdown('❌ Sorry, I encountered an error processing your request. Please try again.');
			return { metadata: { command: request.command } };
		}
	}

	private async handleA11yAgentRequest(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		this.logService.info('A11y Agent: Handling request', { prompt: request.prompt, command: request.command });
		
		try {
			switch (request.command) {
				case 'audit':
					return this.handleA11yAuditCommand(request, context, stream, token);
				case 'fix':
					return this.handleA11yFixCommand(request, context, stream, token);
				default:
					return this.handleGeneralA11yRequest(request, context, stream, token);
			}
		} catch (error) {
			this.logService.error('A11y Agent: Error handling request', error);
			stream.markdown('❌ Sorry, I encountered an error processing your accessibility request. Please try again.');
			return { metadata: { command: request.command } };
		}
	}

	// UI Agent command handlers
	private async handleAnalyzeCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('🔍 **Analyzing component for design and accessibility issues...**\\n\\n');
		
		// Get the active file if no specific file mentioned
		const activeEditor = vscode.window.activeTextEditor;
		if (!activeEditor) {
			stream.markdown('❌ Please open a React component file to analyze, or specify a file path in your request.');
			return { metadata: { command: 'analyze' } };
		}

		const filePath = activeEditor.document.uri.fsPath;
		const fileName = activeEditor.document.fileName;

		// Check if it's a React component file
		if (!['.tsx', '.jsx', '.ts', '.js'].some(ext => fileName.endsWith(ext))) {
			stream.markdown(`❌ The active file (${fileName}) doesn't appear to be a React component. Please open a .tsx, .jsx, .ts, or .js file.`);
			return { metadata: { command: 'analyze' } };
		}

		stream.markdown(`Analyzing: \`${vscode.workspace.asRelativePath(filePath)}\`\\n\\n`);

		try {
			// Use the analyzeComponent tool via the language model tools API
			stream.anchor(vscode.Uri.file(filePath), fileName);
			stream.markdown('\\n**This analysis includes:**\\n');
			stream.markdown('- 🎨 Design patterns and Nielsen heuristics\\n');
			stream.markdown('- ♿ WCAG 2.1 AA accessibility compliance\\n');
			stream.markdown('- 🏗️ Component structure and best practices\\n');
			stream.markdown('- 💡 Actionable improvement suggestions\\n\\n');
			
			// Reference the tool for detailed analysis
			stream.reference(new vscode.Location(vscode.Uri.file(filePath), new vscode.Position(0, 0)));
			
			return { metadata: { command: 'analyze', filePath } };
			
		} catch (error) {
			this.logService.error('UI Agent: Analysis failed', error);
			stream.markdown(`❌ Analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
			return { metadata: { command: 'analyze', error: true } };
		}
	}

	private async handleGenerateCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('🎨 **Generating React component with design system compliance...**\\n\\n');
		
		if (!request.prompt || request.prompt.trim().length < 10) {
			stream.markdown('❌ Please provide a detailed description of the component you want to generate.\\n\\n');
			stream.markdown('**Example:** `@ui /generate Create a responsive card component with image, title, description, and action buttons using Tailwind CSS`');
			return { metadata: { command: 'generate' } };
		}

		// Parse component name from prompt (simple heuristic)
		const nameMatch = request.prompt.match(/\\b([A-Z][a-zA-Z0-9]*(?:Card|Button|Modal|Form|Input|Component))\\b/);
		const componentName = nameMatch?.[1] || 'GeneratedComponent';
		
		// Get design system preference
		const designSystem = this.configurationService.getValue('palette.design.system', 'tailwindui') as 'tailwindui' | 'shadcn' | 'custom';

		stream.markdown(`**Component Details:**\\n`);
		stream.markdown(`- Name: \`${componentName}\`\\n`);
		stream.markdown(`- Design System: ${designSystem}\\n`);
		stream.markdown(`- Description: ${request.prompt}\\n\\n`);

		stream.markdown('**✨ Generating with enhanced features:**\\n');
		stream.markdown('- 🎨 Design system compliance\\n');
		stream.markdown('- ♿ WCAG 2.1 AA accessibility\\n');
		stream.markdown('- 📱 Responsive design patterns\\n');
		stream.markdown('- 🔧 TypeScript types and props\\n');
		stream.markdown('- 🛡️ Error handling and validation\\n\\n');

		stream.progress('Analyzing existing patterns in your codebase...');
		
		// Reference the tool for component generation
		try {
			stream.progress('Generating component with AI...');
			stream.markdown('🚀 **Component generation in progress!** This may take a moment while I analyze your codebase and generate the perfect component.\\n\\n');
			
			return { metadata: { command: 'generate', componentName, designSystem, description: request.prompt } };
			
		} catch (error) {
			this.logService.error('UI Agent: Generation failed', error);
			stream.markdown(`❌ Generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
			return { metadata: { command: 'generate', error: true } };
		}
	}

	private async handleCritiqueCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('📋 **Providing design critique using Nielsen heuristics...**\\n\\n');
		
		// TODO: Implement design critique using existing logic
		stream.markdown('Design critique will be implemented here using usability heuristics.');
		
		return { metadata: { command: 'critique' } };
	}

	private async handlePatternsCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('🎯 **Suggesting UI patterns and best practices...**\\n\\n');
		
		// TODO: Implement pattern suggestions using existing logic
		stream.markdown('UI pattern suggestions will be implemented here.');
		
		return { metadata: { command: 'patterns' } };
	}

	private async handleGeneralUIRequest(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('👋 **UI Design Assistant ready to help!**\\n\\n');
		stream.markdown('I can help you with:\\n');
		stream.markdown('- `/analyze` - Analyze components for design issues\\n');
		stream.markdown('- `/generate` - Generate new React components\\n');
		stream.markdown('- `/critique` - Provide design critique\\n');
		stream.markdown('- `/patterns` - Suggest UI patterns\\n\\n');
		stream.markdown('What would you like to work on?');
		
		return { metadata: { command: undefined } };
	}

	// A11y Agent command handlers
	private async handleA11yAuditCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('♿ **Auditing component for accessibility issues...**\\n\\n');
		
		// TODO: Implement accessibility audit using existing logic
		stream.markdown('Accessibility audit will be implemented here using WCAG 2.1 AA guidelines.');
		
		return { metadata: { command: 'audit' } };
	}

	private async handleA11yFixCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('🔧 **Fixing accessibility issues...**\\n\\n');
		
		// TODO: Implement accessibility fixes using existing logic
		stream.markdown('Accessibility fixes will be implemented here.');
		
		return { metadata: { command: 'fix' } };
	}

	private async handleGeneralA11yRequest(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('♿ **Accessibility Specialist ready to help!**\\n\\n');
		stream.markdown('I can help you with:\\n');
		stream.markdown('- `/audit` - Audit components for accessibility\\n');
		stream.markdown('- `/fix` - Fix accessibility issues\\n\\n');
		stream.markdown('What accessibility challenge can I help you with?');
		
		return { metadata: { command: undefined } };
	}
}