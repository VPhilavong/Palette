/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ComponentAnalyzer } from '../../../codebase/componentAnalyzer';
import { ComponentInfo } from '../../../types';
import { ILogService } from '../../../platform/log/common/logService';

export interface ComponentAnalysisResult {
	component: ComponentInfo | null;
	designIssues: DesignIssue[];
	accessibilityIssues: AccessibilityIssue[];
	suggestions: string[];
}

export interface DesignIssue {
	type: 'layout' | 'spacing' | 'hierarchy' | 'consistency';
	severity: 'low' | 'medium' | 'high';
	message: string;
	line?: number;
}

export interface AccessibilityIssue {
	type: 'semantic' | 'keyboard' | 'screen-reader' | 'color-contrast';
	wcagLevel: 'A' | 'AA' | 'AAA';
	message: string;
	line?: number;
}

export class ComponentAnalysisTool {
	private componentAnalyzer: ComponentAnalyzer;

	constructor(private readonly logService: ILogService) {
		this.componentAnalyzer = new ComponentAnalyzer();
	}

	async analyzeComponent(filePath: string, analysisType: string = 'full'): Promise<ComponentAnalysisResult> {
		this.logService.info('ComponentAnalysisTool: Starting analysis', { filePath, analysisType });

		try {
			// Parse the component using existing analyzer
			const uri = vscode.Uri.file(filePath);
			const components = await this.componentAnalyzer.analyzeWorkspaceComponents();
			const component = components.find(comp => comp.path === filePath) || null;

			if (!component) {
				this.logService.warn('ComponentAnalysisTool: No component found', { filePath });
				return {
					component: null,
					designIssues: [],
					accessibilityIssues: [],
					suggestions: ['Could not parse component. Please ensure it exports a valid React component.']
				};
			}

			// Perform analysis based on type
			const result: ComponentAnalysisResult = {
				component,
				designIssues: [],
				accessibilityIssues: [],
				suggestions: []
			};

			if (analysisType === 'full' || analysisType === 'design') {
				result.designIssues = await this.analyzeDesignPatterns(component, filePath);
				result.suggestions.push(...this.generateDesignSuggestions(component));
			}

			if (analysisType === 'full' || analysisType === 'accessibility') {
				result.accessibilityIssues = await this.analyzeAccessibility(component, filePath);
				result.suggestions.push(...this.generateA11ySuggestions(component));
			}

			if (analysisType === 'full' || analysisType === 'performance') {
				result.suggestions.push(...this.generatePerformanceSuggestions(component));
			}

			this.logService.info('ComponentAnalysisTool: Analysis complete', {
				designIssues: result.designIssues.length,
				accessibilityIssues: result.accessibilityIssues.length,
				suggestions: result.suggestions.length
			});

			return result;

		} catch (error) {
			this.logService.error('ComponentAnalysisTool: Analysis failed', error);
			throw error;
		}
	}

	private async analyzeDesignPatterns(component: ComponentInfo, filePath: string): Promise<DesignIssue[]> {
		const issues: DesignIssue[] = [];

		// Read the actual file content to analyze patterns
		try {
			const document = await vscode.workspace.openTextDocument(filePath);
			const content = document.getText();

			// Nielsen's Heuristics Analysis
			issues.push(...this.checkVisibilityOfSystemStatus(content, component));
			issues.push(...this.checkUserControl(content, component));
			issues.push(...this.checkConsistency(content, component));
			issues.push(...this.checkErrorPrevention(content, component));

		} catch (error) {
			this.logService.warn('ComponentAnalysisTool: Could not read file for design analysis', { filePath, error });
		}

		return issues;
	}

	private checkVisibilityOfSystemStatus(content: string, component: ComponentInfo): DesignIssue[] {
		const issues: DesignIssue[] = [];

		// Check for loading states
		if (!content.includes('loading') && !content.includes('Loading') && component.hooks?.includes('useState')) {
			issues.push({
				type: 'hierarchy',
				severity: 'medium',
				message: 'Consider adding loading states to provide feedback to users about system status'
			});
		}

		// Check for error states
		if (!content.includes('error') && !content.includes('Error') && component.hooks?.includes('useState')) {
			issues.push({
				type: 'hierarchy',
				severity: 'medium',
				message: 'Consider adding error handling to inform users when something goes wrong'
			});
		}

		return issues;
	}

	private checkUserControl(content: string, component: ComponentInfo): DesignIssue[] {
		const issues: DesignIssue[] = [];

		// Check for form controls without proper labeling
		if (content.includes('<input') && !content.includes('label')) {
			issues.push({
				type: 'consistency',
				severity: 'high',
				message: 'Form inputs should have associated labels for better user control and accessibility'
			});
		}

		return issues;
	}

	private checkConsistency(content: string, component: ComponentInfo): DesignIssue[] {
		const issues: DesignIssue[] = [];

		// Check for inline styles (potential inconsistency)
		const inlineStyleMatches = content.match(/style={{.*?}}/g);
		if (inlineStyleMatches && inlineStyleMatches.length > 3) {
			issues.push({
				type: 'consistency',
				severity: 'medium',
				message: 'Consider using consistent styling approach instead of numerous inline styles'
			});
		}

		// Check for consistent naming patterns
		const classNameMatches = content.match(/className="([^"]+)"/g);
		if (classNameMatches) {
			const hasConsistentNaming = this.checkNamingConsistency(classNameMatches);
			if (!hasConsistentNaming) {
				issues.push({
					type: 'consistency',
					severity: 'low',
					message: 'Consider using consistent naming patterns for CSS classes'
				});
			}
		}

		return issues;
	}

	private checkErrorPrevention(content: string, component: ComponentInfo): DesignIssue[] {
		const issues: DesignIssue[] = [];

		// Check for validation in forms
		if (content.includes('<form') && !content.includes('validation') && !content.includes('required')) {
			issues.push({
				type: 'layout',
				severity: 'medium',
				message: 'Consider adding validation to prevent user errors in forms'
			});
		}

		return issues;
	}

	private checkNamingConsistency(classNames: string[]): boolean {
		// Simple heuristic: check if classes follow a consistent pattern (kebab-case, camelCase, etc.)
		const kebabCase = classNames.filter(cn => cn.includes('-')).length;
		const camelCase = classNames.filter(cn => /[A-Z]/.test(cn)).length;
		
		// If more than 80% follow one pattern, consider it consistent
		const total = classNames.length;
		return (kebabCase / total > 0.8) || (camelCase / total > 0.8);
	}

	private async analyzeAccessibility(component: ComponentInfo, filePath: string): Promise<AccessibilityIssue[]> {
		const issues: AccessibilityIssue[] = [];

		try {
			const document = await vscode.workspace.openTextDocument(filePath);
			const content = document.getText();

			// WCAG 2.1 AA Analysis
			issues.push(...this.checkSemanticHTML(content));
			issues.push(...this.checkKeyboardNavigation(content));
			issues.push(...this.checkScreenReaderSupport(content));
			issues.push(...this.checkColorContrast(content));

		} catch (error) {
			this.logService.warn('ComponentAnalysisTool: Could not read file for accessibility analysis', { filePath, error });
		}

		return issues;
	}

	private checkSemanticHTML(content: string): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for semantic elements
		if (content.includes('<div') && !content.match(/<(nav|main|section|article|aside|header|footer)/)) {
			issues.push({
				type: 'semantic',
				wcagLevel: 'AA',
				message: 'Consider using semantic HTML elements (nav, main, section, etc.) instead of generic divs'
			});
		}

		// Check for buttons without accessible text
		if (content.includes('<button') && !content.includes('aria-label') && !content.match(/>[^<]*\w[^<]*</)) {
			issues.push({
				type: 'semantic',
				wcagLevel: 'AA',
				message: 'Buttons should have accessible text or aria-label attributes'
			});
		}

		return issues;
	}

	private checkKeyboardNavigation(content: string): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for interactive elements without keyboard support
		if (content.includes('onClick') && !content.includes('onKeyDown') && !content.includes('<button')) {
			issues.push({
				type: 'keyboard',
				wcagLevel: 'AA',
				message: 'Interactive elements should support keyboard navigation (onKeyDown, tabIndex)'
			});
		}

		return issues;
	}

	private checkScreenReaderSupport(content: string): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for images without alt text
		if (content.includes('<img') && !content.includes('alt=')) {
			issues.push({
				type: 'screen-reader',
				wcagLevel: 'AA',
				message: 'Images should have alt text for screen readers'
			});
		}

		// Check for form inputs without labels
		if (content.includes('<input') && !content.includes('aria-label') && !content.includes('<label')) {
			issues.push({
				type: 'screen-reader',
				wcagLevel: 'AA',
				message: 'Form inputs should have associated labels or aria-label attributes'
			});
		}

		return issues;
	}

	private checkColorContrast(content: string): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Basic check for potential contrast issues (would need more sophisticated analysis)
		if (content.includes('color:') && content.includes('background')) {
			issues.push({
				type: 'color-contrast',
				wcagLevel: 'AA',
				message: 'Verify that color combinations meet WCAG AA contrast requirements (4.5:1 ratio)'
			});
		}

		return issues;
	}

	private generateDesignSuggestions(component: ComponentInfo): string[] {
		const suggestions: string[] = [];

		// Suggest design system patterns
		if (component.props && component.props.length > 5) {
			suggestions.push('Consider breaking down this component into smaller, more focused components');
		}

		if (component.hooks && component.hooks.includes('useState') && component.hooks.length > 3) {
			suggestions.push('Consider using useReducer for complex state management');
		}

		// Suggest Tailwind patterns if applicable
		suggestions.push('Consider using Tailwind utility classes for consistent spacing and sizing');
		suggestions.push('Implement responsive design with Tailwind breakpoint utilities (sm:, md:, lg:, xl:)');

		return suggestions;
	}

	private generateA11ySuggestions(component: ComponentInfo): string[] {
		const suggestions: string[] = [];

		suggestions.push('Add focus management for keyboard users');
		suggestions.push('Consider adding skip links for better navigation');
		suggestions.push('Use semantic HTML elements for better screen reader support');
		suggestions.push('Test with screen readers and keyboard-only navigation');

		return suggestions;
	}

	private generatePerformanceSuggestions(component: ComponentInfo): string[] {
		const suggestions: string[] = [];

		if (component.hooks && component.hooks.includes('useEffect')) {
			suggestions.push('Review useEffect dependencies to prevent unnecessary re-renders');
		}

		suggestions.push('Consider using React.memo for expensive components');
		suggestions.push('Optimize images with next/image or lazy loading');

		return suggestions;
	}
}