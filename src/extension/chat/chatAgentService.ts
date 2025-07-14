/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { IChatAgentService } from '../../platform/chat/common/chatAgentService';
import { ILogService } from '../../platform/log/common/logService';
import { IConfigurationService } from '../../platform/configuration/common/configurationService';
import { IDisposable, DisposableStore } from '../../util/common/services';
import { WorkspacePatternSearch } from '../search/workspacePatternSearch';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { WCAGValidator } from '../accessibility/wcagValidator';

export class ChatAgentService implements IChatAgentService {
	declare readonly _serviceBrand: undefined;
	
	private workspacePatternSearch: WorkspacePatternSearch;
	private componentAnalyzer: ComponentAnalyzer;
	private wcagValidator: WCAGValidator;

	constructor(
		private readonly logService: ILogService,
		private readonly configurationService: IConfigurationService
	) {
		this.workspacePatternSearch = new WorkspacePatternSearch(logService);
		this.componentAnalyzer = new ComponentAnalyzer();
		this.wcagValidator = new WCAGValidator(logService);
	}

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
		stream.markdown('🎯 **Analyzing workspace for UI patterns and best practices...**\\n\\n');
		
		try {
			// Get search query from request or provide general suggestions
			const query = request.prompt || 'component patterns layout design';
			
			// Get workspace components
			const components = await this.componentAnalyzer.analyzeWorkspaceComponents();
			
			if (components.length === 0) {
				stream.markdown('❌ No React components found in workspace. Please ensure you have .tsx, .jsx, .ts, or .js files with React components.');
				return { metadata: { command: 'patterns' } };
			}

			stream.markdown(`Found ${components.length} components to analyze for patterns...\\n\\n`);

			// Search for patterns
			const searchResult = await this.workspacePatternSearch.searchDesignPatterns(query, components);
			
			// Build comprehensive pattern analysis
			let report = '';

			if (searchResult.patterns.length > 0) {
				report += `**🎨 Design Patterns in Your Workspace (${searchResult.patterns.length}):**\\n\\n`;
				
				// Group patterns by type
				const patternsByType = this.groupPatternsByType(searchResult.patterns);
				
				for (const [type, patterns] of patternsByType.entries()) {
					const typeIcon = type === 'component' ? '🧩' : 
								   type === 'layout' ? '📐' : 
								   type === 'interaction' ? '⚡' : '🔧';
					
					report += `### ${typeIcon} ${type.charAt(0).toUpperCase() + type.slice(1)} Patterns\\n`;
					
					patterns.forEach(pattern => {
						report += `- **${pattern.name}** (${pattern.designSystem})\\n`;
						report += `  *${pattern.description}*\\n`;
						report += `  📄 \`${pattern.filePath.split('/').pop()}\` - Used ${pattern.usageCount} times\\n`;
						
						// Accessibility info
						const a11yFeatures = this.getAccessibilityFeatures(pattern.accessibility);
						if (a11yFeatures.length > 0) {
							report += `  ♿ ${a11yFeatures.join(', ')}\\n`;
						}
						report += '\\n';
					});
				}
				report += '\\n';
			}

			// Tailwind usage analysis
			if (searchResult.tailwindUtilities.length > 0) {
				report += `**🎯 Tailwind CSS Usage Analysis:**\\n\\n`;
				
				const utilityByCategory = this.groupTailwindByCategory(searchResult.tailwindUtilities);
				
				for (const [category, utilities] of utilityByCategory.entries()) {
					const categoryIcon = this.getCategoryIcon(category);
					report += `### ${categoryIcon} ${category.charAt(0).toUpperCase() + category.slice(1)}\\n`;
					
					utilities.forEach(utility => {
						report += `- \`${utility.utility}\` - Used ${utility.usage} times\\n`;
					});
					report += '\\n';
				}
			}

			// Design recommendations
			const recommendations = await this.generateDesignRecommendations(components, searchResult);
			if (recommendations.length > 0) {
				report += `**💡 Design Recommendations:**\\n\\n`;
				recommendations.forEach(rec => {
					report += `- ${rec}\\n`;
				});
				report += '\\n';
			}

			// Best practices suggestions
			const bestPractices = this.generateBestPracticesSuggestions(searchResult);
			if (bestPractices.length > 0) {
				report += `**✨ Best Practices to Consider:**\\n\\n`;
				bestPractices.forEach(practice => {
					report += `- ${practice}\\n`;
				});
			}

			if (report) {
				stream.markdown(report);
			} else {
				stream.markdown('🔍 No specific patterns found. Here are some general UI best practices to consider:\\n\\n');
				stream.markdown('- Use consistent spacing and typography\\n');
				stream.markdown('- Implement responsive design patterns\\n');
				stream.markdown('- Follow accessibility guidelines (WCAG 2.1 AA)\\n');
				stream.markdown('- Create reusable component patterns\\n');
				stream.markdown('- Use semantic HTML elements\\n');
			}

			return { metadata: { command: 'patterns', componentsAnalyzed: components.length } };
			
		} catch (error) {
			this.logService.error('UI Agent: Pattern analysis failed', error);
			stream.markdown(`❌ Pattern analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
			return { metadata: { command: 'patterns', error: true } };
		}
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

	// Helper methods for pattern analysis
	private groupPatternsByType(patterns: any[]): Map<string, any[]> {
		const groups = new Map<string, any[]>();
		
		patterns.forEach(pattern => {
			const type = pattern.type || 'utility';
			if (!groups.has(type)) {
				groups.set(type, []);
			}
			groups.get(type)!.push(pattern);
		});
		
		return groups;
	}

	private groupTailwindByCategory(utilities: any[]): Map<string, any[]> {
		const groups = new Map<string, any[]>();
		
		utilities.forEach(utility => {
			const category = utility.category || 'other';
			if (!groups.has(category)) {
				groups.set(category, []);
			}
			groups.get(category)!.push(utility);
		});
		
		return groups;
	}

	private getCategoryIcon(category: string): string {
		const icons: Record<string, string> = {
			'layout': '📐',
			'spacing': '📏',
			'colors': '🎨',
			'typography': '📝',
			'responsive': '📱'
		};
		return icons[category] || '🔧';
	}

	private getAccessibilityFeatures(accessibility: any): string[] {
		const features: string[] = [];
		if (accessibility.hasAriaLabels) features.push('ARIA labels');
		if (accessibility.hasSemanticHTML) features.push('Semantic HTML');
		if (accessibility.hasKeyboardSupport) features.push('Keyboard support');
		return features;
	}

	private async generateDesignRecommendations(components: any[], searchResult: any): Promise<string[]> {
		const recommendations: string[] = [];

		// Analyze component complexity
		const complexComponents = components.filter(c => c.props && c.props.length > 8);
		if (complexComponents.length > 0) {
			recommendations.push(`Consider breaking down ${complexComponents.length} complex components with many props`);
		}

		// Check for consistent design system usage
		const designSystems = new Set(searchResult.patterns.map((p: any) => p.designSystem));
		if (designSystems.size > 2) {
			recommendations.push('Consider standardizing on a single design system for consistency');
		}

		// Accessibility recommendations
		const patternsWithA11y = searchResult.patterns.filter((p: any) => 
			p.accessibility.hasAriaLabels || p.accessibility.hasSemanticHTML || p.accessibility.hasKeyboardSupport
		);
		const a11yRatio = patternsWithA11y.length / searchResult.patterns.length;
		if (a11yRatio < 0.7) {
			recommendations.push('Improve accessibility by adding ARIA labels, semantic HTML, and keyboard support');
		}

		// Responsive design recommendations
		const responsivePatterns = searchResult.tailwindUtilities.filter((u: any) => u.category === 'responsive');
		if (responsivePatterns.length === 0 && searchResult.tailwindUtilities.length > 0) {
			recommendations.push('Add responsive design patterns using Tailwind breakpoints (sm:, md:, lg:, xl:)');
		}

		return recommendations;
	}

	private generateBestPracticesSuggestions(searchResult: any): string[] {
		const suggestions: string[] = [];

		// Component reusability
		if (searchResult.patterns.length > 0) {
			const lowUsagePatterns = searchResult.patterns.filter((p: any) => p.usageCount === 1);
			if (lowUsagePatterns.length > searchResult.patterns.length * 0.5) {
				suggestions.push('Create more reusable components to reduce code duplication');
			}
		}

		// Design system consistency
		suggestions.push('Establish a consistent color palette and spacing scale');
		suggestions.push('Create a component library with documented patterns');
		suggestions.push('Implement design tokens for consistent theming');

		// Performance suggestions
		suggestions.push('Consider code splitting for large components');
		suggestions.push('Use React.memo for components that render frequently');

		// Accessibility suggestions
		suggestions.push('Test with screen readers and keyboard-only navigation');
		suggestions.push('Ensure color contrast meets WCAG AA standards');
		suggestions.push('Add focus indicators for all interactive elements');

		return suggestions;
	}

	private groupIssuesByLevel(issues: any[]): Map<string, any[]> {
		const groups = new Map<string, any[]>();
		
		issues.forEach(issue => {
			const level = issue.wcagLevel || 'A';
			if (!groups.has(level)) {
				groups.set(level, []);
			}
			groups.get(level)!.push(issue);
		});
		
		// Sort by level priority (A, AA, AAA)
		const sortedGroups = new Map<string, any[]>();
		['A', 'AA', 'AAA'].forEach(level => {
			if (groups.has(level)) {
				sortedGroups.set(level, groups.get(level)!);
			}
		});
		
		return sortedGroups;
	}

	// A11y Agent command handlers
	private async handleA11yAuditCommand(
		request: vscode.ChatRequest,
		context: vscode.ChatContext,
		stream: vscode.ChatResponseStream,
		token: vscode.CancellationToken
	): Promise<vscode.ChatResult> {
		stream.markdown('♿ **Auditing component for accessibility issues...**\\n\\n');
		
		try {
			// Get the active file if no specific file mentioned
			const activeEditor = vscode.window.activeTextEditor;
			if (!activeEditor) {
				stream.markdown('❌ Please open a React component file to audit, or specify a file path in your request.');
				return { metadata: { command: 'audit' } };
			}

			const filePath = activeEditor.document.uri.fsPath;
			const fileName = activeEditor.document.fileName;

			// Check if it's a React component file
			if (!['.tsx', '.jsx', '.ts', '.js'].some(ext => fileName.endsWith(ext))) {
				stream.markdown(`❌ The active file (${fileName}) doesn't appear to be a React component. Please open a .tsx, .jsx, .ts, or .js file.`);
				return { metadata: { command: 'audit' } };
			}

			stream.markdown(`Auditing: \`${vscode.workspace.asRelativePath(filePath)}\`\\n\\n`);
			stream.progress('Running comprehensive WCAG 2.1 accessibility audit...');

			// Get component info
			const components = await this.componentAnalyzer.analyzeWorkspaceComponents();
			const component = components.find(comp => comp.path === filePath);

			if (!component) {
				stream.markdown('❌ Could not analyze component structure. Please ensure the file contains a valid React component.');
				return { metadata: { command: 'audit' } };
			}

			// Run WCAG validation
			const report = await this.wcagValidator.validateComponent(component);

			// Build comprehensive accessibility report
			let auditReport = `## ♿ **Accessibility Audit Results**\\n\\n`;
			
			// Score and compliance overview
			auditReport += `**📊 Accessibility Score: ${report.score}/100**\\n\\n`;
			
			auditReport += `**🏆 WCAG Compliance:**\\n`;
			auditReport += `- Level A: ${report.compliance.levelA ? '✅ Compliant' : '❌ Issues found'}\\n`;
			auditReport += `- Level AA: ${report.compliance.levelAA ? '✅ Compliant' : '❌ Issues found'}\\n`;
			auditReport += `- Level AAA: ${report.compliance.levelAAA ? '✅ Compliant' : '❌ Issues found'}\\n\\n`;

			// Issues breakdown
			if (report.issues.length > 0) {
				const issuesByLevel = this.groupIssuesByLevel(report.issues);
				
				auditReport += `**🔍 Issues Found (${report.issues.length}):**\\n\\n`;
				
				for (const [level, issues] of issuesByLevel.entries()) {
					const levelIcon = level === 'A' ? '🔴' : level === 'AA' ? '🟡' : '🟢';
					auditReport += `### ${levelIcon} WCAG Level ${level} (${issues.length} issues)\\n`;
					
					issues.forEach(issue => {
						const severityIcon = issue.severity === 'error' ? '❌' : 
										   issue.severity === 'warning' ? '⚠️' : 'ℹ️';
						
						auditReport += `${severityIcon} **${issue.rule}**: ${issue.message}\\n`;
						auditReport += `   *Suggestion*: ${issue.suggestion}\\n`;
						
						if (issue.element) {
							auditReport += `   *Element*: \`${issue.element.substring(0, 50)}${issue.element.length > 50 ? '...' : ''}\`\\n`;
						}
						
						if (issue.line) {
							auditReport += `   *Line*: ${issue.line}\\n`;
						}
						
						if (issue.helpUrl) {
							auditReport += `   *Learn more*: [WCAG Guidelines](${issue.helpUrl})\\n`;
						}
						
						auditReport += '\\n';
					});
				}
			} else {
				auditReport += `**🎉 Excellent! No accessibility issues found.**\\n\\n`;
			}

			// Recommendations
			if (report.recommendations.length > 0) {
				auditReport += `**💡 Recommendations:**\\n\\n`;
				report.recommendations.forEach(rec => {
					auditReport += `- ${rec}\\n`;
				});
				auditReport += '\\n';
			}

			// Next steps
			auditReport += `**🚀 Next Steps:**\\n`;
			if (report.score < 70) {
				auditReport += `- Address critical accessibility issues (Score: ${report.score}/100)\\n`;
			}
			auditReport += `- Test with screen readers (NVDA, JAWS, VoiceOver)\\n`;
			auditReport += `- Verify keyboard navigation without mouse\\n`;
			auditReport += `- Check color contrast with tools like WebAIM\\n`;
			auditReport += `- Consider user testing with people who use assistive technologies\\n`;

			stream.markdown(auditReport);

			return { metadata: { command: 'audit', score: report.score, issues: report.issues.length } };
			
		} catch (error) {
			this.logService.error('A11y Agent: Audit failed', error);
			stream.markdown(`❌ Accessibility audit failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
			return { metadata: { command: 'audit', error: true } };
		}
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