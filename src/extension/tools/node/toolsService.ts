/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { IToolsService } from '../common/toolsService';
import { ILogService } from '../../../platform/log/common/logService';
import { IConfigurationService } from '../../../platform/configuration/common/configurationService';
import { IDisposable, DisposableStore } from '../../../util/common/services';
import { ComponentAnalysisTool } from './componentAnalysisTool';
import { ComponentGenerationTool } from './componentGenerationTool';

export class ToolsService implements IToolsService {
	declare readonly _serviceBrand: undefined;
	
	private componentAnalysisTool: ComponentAnalysisTool;
	private componentGenerationTool: ComponentGenerationTool;

	constructor(
		private readonly logService: ILogService,
		private readonly configurationService: IConfigurationService
	) {
		this.componentAnalysisTool = new ComponentAnalysisTool(logService);
		this.componentGenerationTool = new ComponentGenerationTool(logService, configurationService);
	}

	register(): IDisposable {
		const disposables = new DisposableStore();
		
		this.logService.info('ToolsService: Registering language model tools');
		
		// Register analyze component tool
		const analyzeComponentTool = vscode.lm.registerTool('palette_analyzeComponent', {
			invoke: this.handleAnalyzeComponent.bind(this),
			prepareInvocation: async (options, token) => {
				// Prepare the tool invocation
				return {
					invocationMessage: 'Analyzing React component for design patterns and accessibility...'
				};
			}
		});
		disposables.add(analyzeComponentTool);
		
		// Register generate component tool
		const generateComponentTool = vscode.lm.registerTool('palette_generateComponent', {
			invoke: this.handleGenerateComponent.bind(this),
			prepareInvocation: async (options, token) => {
				return {
					invocationMessage: 'Generating React component with design system compliance...'
				};
			}
		});
		disposables.add(generateComponentTool);
		
		// Register search design patterns tool
		const searchPatternsTool = vscode.lm.registerTool('palette_searchDesignPatterns', {
			invoke: this.handleSearchDesignPatterns.bind(this),
			prepareInvocation: async (options, token) => {
				return {
					invocationMessage: 'Searching for design patterns in codebase...'
				};
			}
		});
		disposables.add(searchPatternsTool);
		
		this.logService.info('ToolsService: Language model tools registered successfully');
		
		return disposables;
	}

	private async handleAnalyzeComponent(
		request: vscode.LanguageModelToolInvocationOptions<any>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		this.logService.info('Tool: Analyzing component', { input: request.input });
		
		try {
			const { filePath, analysisType = 'full' } = request.input as {
				filePath: string;
				analysisType?: 'full' | 'accessibility' | 'design' | 'performance';
			};
			
			// Use the enhanced component analysis tool
			const analysisResult = await this.componentAnalysisTool.analyzeComponent(filePath, analysisType);
			
			if (!analysisResult.component) {
				return new vscode.LanguageModelToolResult([
					new vscode.LanguageModelTextPart(`❌ Could not analyze component at: ${filePath}\\n\\nSuggestions:\\n${analysisResult.suggestions.map(s => `- ${s}`).join('\\n')}`)
				]);
			}

			// Build detailed analysis report
			let report = `🔍 **Component Analysis: ${analysisResult.component.name}**\\n\\n`;
			
			// Component info
			report += `**Component Details:**\\n`;
			report += `- File: ${filePath}\\n`;
			report += `- Props: ${analysisResult.component.props?.length || 0}\\n`;
			report += `- Hooks: ${analysisResult.component.hooks?.join(', ') || 'None'}\\n`;
			report += `- Exports: ${analysisResult.component.exports.join(', ')}\\n\\n`;

			// Design issues
			if (analysisResult.designIssues.length > 0) {
				report += `**🎨 Design Issues Found:**\\n`;
				analysisResult.designIssues.forEach(issue => {
					const severity = issue.severity === 'high' ? '🔴' : issue.severity === 'medium' ? '🟡' : '🟢';
					report += `${severity} **${issue.type}**: ${issue.message}\\n`;
				});
				report += '\\n';
			}

			// Accessibility issues  
			if (analysisResult.accessibilityIssues.length > 0) {
				report += `**♿ Accessibility Issues Found:**\\n`;
				analysisResult.accessibilityIssues.forEach(issue => {
					const level = issue.wcagLevel === 'AAA' ? '🏆' : issue.wcagLevel === 'AA' ? '⭐' : '✓';
					report += `${level} **WCAG ${issue.wcagLevel} - ${issue.type}**: ${issue.message}\\n`;
				});
				report += '\\n';
			}

			// Suggestions
			if (analysisResult.suggestions.length > 0) {
				report += `**💡 Recommendations:**\\n`;
				analysisResult.suggestions.forEach(suggestion => {
					report += `- ${suggestion}\\n`;
				});
			}

			// Summary
			const issueCount = analysisResult.designIssues.length + analysisResult.accessibilityIssues.length;
			if (issueCount === 0) {
				report += `\\n✅ **Great job!** No major issues found. This component follows good design and accessibility practices.`;
			} else {
				report += `\\n📊 **Summary**: Found ${issueCount} issues to address for better user experience.`;
			}
			
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(report)
			]);
			
		} catch (error) {
			this.logService.error('Tool: Error analyzing component', error);
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(`❌ Error analyzing component: ${error instanceof Error ? error.message : 'Unknown error'}`)
			]);
		}
	}

	private async handleGenerateComponent(
		request: vscode.LanguageModelToolInvocationOptions<any>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		this.logService.info('Tool: Generating component', { input: request.input });
		
		try {
			const { componentName, description, designSystem = 'tailwindui' } = request.input as {
				componentName: string;
				description: string;
				designSystem?: 'tailwindui' | 'shadcn' | 'custom';
			};
			
			// Use the enhanced component generation tool
			const generationResult = await this.componentGenerationTool.generateComponent({
				componentName,
				description,
				designSystem
			});
			
			if (!generationResult.success) {
				return new vscode.LanguageModelToolResult([
					new vscode.LanguageModelTextPart(`❌ Component generation failed: ${generationResult.error || 'Unknown error'}`)
				]);
			}

			// Build detailed generation report
			let report = `🎨 **Component Generated: ${componentName}**\\n\\n`;
			
			// Generation details
			report += `**Generation Details:**\\n`;
			report += `- Design System: ${designSystem}\\n`;
			report += `- Expected File: ${generationResult.filePath}\\n`;
			report += `- Description: ${description}\\n\\n`;

			// Design patterns implemented
			if (generationResult.designPatterns.length > 0) {
				report += `**🛠️ Design Patterns Implemented:**\\n`;
				generationResult.designPatterns.forEach(pattern => {
					report += `- ${pattern}\\n`;
				});
				report += '\\n';
			}

			// Accessibility features
			if (generationResult.accessibilityFeatures.length > 0) {
				report += `**♿ Accessibility Features:**\\n`;
				generationResult.accessibilityFeatures.forEach(feature => {
					report += `- ${feature}\\n`;
				});
				report += '\\n';
			}

			// Generated code
			if (generationResult.componentCode) {
				// Truncate very long code for the tool result
				const codePreview = generationResult.componentCode.length > 1000 
					? generationResult.componentCode.substring(0, 1000) + '\\n// ... (truncated)'
					: generationResult.componentCode;
					
				report += `**📝 Generated Code:**\\n\`\`\`tsx\\n${codePreview}\\n\`\`\`\\n\\n`;
			}

			report += `✅ **Component successfully generated!** Check your file system for the new component file.`;
			
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(report)
			]);
			
		} catch (error) {
			this.logService.error('Tool: Error generating component', error);
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(`❌ Error generating component: ${error instanceof Error ? error.message : 'Unknown error'}`)
			]);
		}
	}

	private async handleSearchDesignPatterns(
		request: vscode.LanguageModelToolInvocationOptions<any>,
		token: vscode.CancellationToken
	): Promise<vscode.LanguageModelToolResult> {
		this.logService.info('Tool: Searching design patterns', { input: request.input });
		
		try {
			const { query } = request.input as { query: string };
			
			// TODO: Implement pattern search using existing logic from src/embeddings/vectorStore.ts
			// This will integrate with your existing search and embedding capabilities
			
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(`🔍 **Design Pattern Search Results for: "${query}"**\\n\\n📁 **Matching Patterns Found:**\\n- Button variants pattern\\n- Form layout pattern\\n- Navigation pattern\\n\\n*Note: Full implementation pending integration with existing search.*`)
			]);
			
		} catch (error) {
			this.logService.error('Tool: Error searching patterns', error);
			return new vscode.LanguageModelToolResult([
				new vscode.LanguageModelTextPart(`❌ Error searching patterns: ${error instanceof Error ? error.message : 'Unknown error'}`)
			]);
		}
	}
}