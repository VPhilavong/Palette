/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ComponentInfo } from '../../types';
import { ILogService } from '../../platform/log/common/logService';

export interface AccessibilityIssue {
	rule: string;
	wcagLevel: 'A' | 'AA' | 'AAA';
	severity: 'error' | 'warning' | 'info';
	message: string;
	element?: string;
	line?: number;
	column?: number;
	suggestion: string;
	helpUrl?: string;
}

export interface AccessibilityReport {
	component: ComponentInfo;
	issues: AccessibilityIssue[];
	score: number;
	compliance: {
		levelA: boolean;
		levelAA: boolean;
		levelAAA: boolean;
	};
	recommendations: string[];
}

export class WCAGValidator {
	constructor(private readonly logService: ILogService) {}

	async validateComponent(component: ComponentInfo): Promise<AccessibilityReport> {
		this.logService.info('WCAGValidator: Starting validation', { component: component.name });

		try {
			// Read component file
			const document = await vscode.workspace.openTextDocument(component.path);
			const content = document.getText();
			const lines = content.split('\\n');

			// Run all WCAG checks
			const issues: AccessibilityIssue[] = [];

			// WCAG 1.1 - Non-text Content (A)
			issues.push(...this.checkNonTextContent(content, lines));

			// WCAG 1.3 - Adaptable (A/AA)
			issues.push(...this.checkAdaptableContent(content, lines));

			// WCAG 1.4 - Distinguishable (A/AA/AAA)
			issues.push(...this.checkDistinguishableContent(content, lines));

			// WCAG 2.1 - Keyboard Accessible (A/AA)
			issues.push(...this.checkKeyboardAccessible(content, lines));

			// WCAG 2.4 - Navigable (A/AA/AAA)
			issues.push(...this.checkNavigable(content, lines));

			// WCAG 3.1 - Readable (A/AA/AAA)
			issues.push(...this.checkReadable(content, lines));

			// WCAG 3.2 - Predictable (A/AA)
			issues.push(...this.checkPredictable(content, lines));

			// WCAG 4.1 - Compatible (A/AA)
			issues.push(...this.checkCompatible(content, lines));

			// Calculate scores and compliance
			const report = this.generateReport(component, issues);

			this.logService.info('WCAGValidator: Validation complete', {
				component: component.name,
				issues: issues.length,
				score: report.score
			});

			return report;

		} catch (error) {
			this.logService.error('WCAGValidator: Validation failed', error);
			return {
				component,
				issues: [{
					rule: 'VALIDATION_ERROR',
					wcagLevel: 'A',
					severity: 'error',
					message: 'Failed to validate component',
					suggestion: 'Please check if the component file is accessible and contains valid React code'
				}],
				score: 0,
				compliance: { levelA: false, levelAA: false, levelAAA: false },
				recommendations: ['Fix validation errors before running accessibility audit']
			};
		}
	}

	private checkNonTextContent(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for images without alt text (WCAG 1.1.1 - A)
		const imgMatches = content.matchAll(/<img[^>]*>/g);
		for (const match of imgMatches) {
			if (!match[0].includes('alt=')) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 1.1.1',
					wcagLevel: 'A',
					severity: 'error',
					message: 'Image missing alt attribute',
					element: match[0],
					line,
					suggestion: 'Add alt="" for decorative images or alt="description" for informative images',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
				});
			}
		}

		// Check for icons without accessible text
		const iconMatches = content.matchAll(/(<svg[^>]*>|<i[^>]*class="[^"]*icon[^"]*"[^>]*>)/g);
		for (const match of iconMatches) {
			if (!match[0].includes('aria-label') && !match[0].includes('title')) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 1.1.1',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'Icon missing accessible text',
					element: match[0],
					line,
					suggestion: 'Add aria-label or title attribute to describe the icon purpose',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html'
				});
			}
		}

		return issues;
	}

	private checkAdaptableContent(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for proper heading structure (WCAG 1.3.1 - A)
		const headingMatches = content.matchAll(/<h([1-6])[^>]*>/g);
		const headingLevels = Array.from(headingMatches).map(match => parseInt(match[1]));
		
		if (headingLevels.length > 0) {
			for (let i = 1; i < headingLevels.length; i++) {
				if (headingLevels[i] > headingLevels[i - 1] + 1) {
					issues.push({
						rule: 'WCAG 1.3.1',
						wcagLevel: 'A',
						severity: 'warning',
						message: 'Heading levels should not skip (e.g., h1 to h3)',
						line: this.getLineNumber(content, 0), // Would need more precise location
						suggestion: 'Use heading levels in sequential order (h1, h2, h3, etc.)',
						helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
					});
					break;
				}
			}
		}

		// Check for form labels (WCAG 1.3.1 - A)
		const inputMatches = content.matchAll(/<input[^>]*>/g);
		for (const match of inputMatches) {
			const inputElement = match[0];
			const hasId = /id="([^"]*)"/.test(inputElement);
			const hasAriaLabel = inputElement.includes('aria-label');
			const hasAriaLabelledBy = inputElement.includes('aria-labelledby');
			
			if (hasId) {
				const idMatch = inputElement.match(/id="([^"]*)"/);
				const id = idMatch ? idMatch[1] : '';
				const hasCorrespondingLabel = content.includes(`for="${id}"`);
				
				if (!hasCorrespondingLabel && !hasAriaLabel && !hasAriaLabelledBy) {
					const line = this.getLineNumber(content, match.index || 0);
					issues.push({
						rule: 'WCAG 1.3.1',
						wcagLevel: 'A',
						severity: 'error',
						message: 'Form input missing accessible label',
						element: inputElement,
						line,
						suggestion: 'Add a <label for="id"> element or aria-label attribute',
						helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
					});
				}
			}
		}

		// Check for semantic HTML (WCAG 1.3.1 - A)
		const hasSemanticElements = /(<nav|<main|<section|<article|<aside|<header|<footer)/.test(content);
		const hasOnlyDivs = /<div[^>]*>/.test(content) && !hasSemanticElements;
		
		if (hasOnlyDivs) {
			issues.push({
				rule: 'WCAG 1.3.1',
				wcagLevel: 'A',
				severity: 'info',
				message: 'Consider using semantic HTML elements',
				suggestion: 'Replace generic divs with semantic elements like nav, main, section, article, aside, header, footer',
				helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html'
			});
		}

		return issues;
	}

	private checkDistinguishableContent(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for color-only information (WCAG 1.4.1 - A)
		const colorOnlyPatterns = [
			/color:\s*red.*error/i,
			/text-red.*error/i,
			/bg-green.*success/i
		];

		for (const pattern of colorOnlyPatterns) {
			if (pattern.test(content)) {
				issues.push({
					rule: 'WCAG 1.4.1',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'Information may be conveyed by color alone',
					suggestion: 'Add text, icons, or other visual indicators in addition to color',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html'
				});
				break;
			}
		}

		// Check for sufficient text size (WCAG 1.4.4 - AA)
		const smallTextPatterns = [
			/text-xs(?!.*text-)/,
			/font-size:\s*[0-9]{1}px/,
			/font-size:\s*0\./
		];

		for (const pattern of smallTextPatterns) {
			if (pattern.test(content)) {
				issues.push({
					rule: 'WCAG 1.4.4',
					wcagLevel: 'AA',
					severity: 'warning',
					message: 'Text may be too small for accessibility',
					suggestion: 'Ensure text is at least 14px or use text-sm as minimum in Tailwind',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html'
				});
				break;
			}
		}

		return issues;
	}

	private checkKeyboardAccessible(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for keyboard event handlers (WCAG 2.1.1 - A)
		const clickHandlers = content.matchAll(/onClick={[^}]*}/g);
		const keyHandlers = content.matchAll(/onKey(Down|Up|Press)={[^}]*}/g);
		
		if (Array.from(clickHandlers).length > 0 && Array.from(keyHandlers).length === 0) {
			// Check if using proper interactive elements
			const hasButtons = /<button/.test(content);
			const hasLinks = /<a[^>]*href/.test(content);
			
			if (!hasButtons && !hasLinks) {
				issues.push({
					rule: 'WCAG 2.1.1',
					wcagLevel: 'A',
					severity: 'error',
					message: 'Interactive elements may not be keyboard accessible',
					suggestion: 'Use button or link elements, or add onKeyDown handlers with proper tabIndex',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html'
				});
			}
		}

		// Check for focus management (WCAG 2.1.2 - A)
		const tabIndexValues = content.matchAll(/tabIndex={(-?[0-9]+)}/g);
		for (const match of tabIndexValues) {
			const value = parseInt(match[1]);
			if (value > 0) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 2.1.2',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'Positive tabIndex values can cause keyboard navigation issues',
					line,
					suggestion: 'Use tabIndex={0} for focusable elements or tabIndex={-1} to remove from tab order',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html'
				});
			}
		}

		return issues;
	}

	private checkNavigable(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for skip links (WCAG 2.4.1 - A)
		const hasSkipLink = /skip.{0,20}(content|navigation|main)/i.test(content);
		const hasNavigation = /<nav/.test(content);
		
		if (hasNavigation && !hasSkipLink) {
			issues.push({
				rule: 'WCAG 2.4.1',
				wcagLevel: 'A',
				severity: 'info',
				message: 'Consider adding skip links for better navigation',
				suggestion: 'Add a "Skip to main content" link at the beginning of the page',
				helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html'
			});
		}

		// Check for page titles (WCAG 2.4.2 - A)
		const hasTitleOrHeading = /<title|<h1/.test(content);
		if (!hasTitleOrHeading && content.includes('function') && content.includes('return')) {
			issues.push({
				rule: 'WCAG 2.4.2',
				wcagLevel: 'A',
				severity: 'warning',
				message: 'Page or section should have a descriptive title or heading',
				suggestion: 'Add an h1 element or ensure the page has a proper title',
				helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html'
			});
		}

		// Check for link text (WCAG 2.4.4 - A)
		const linkMatches = content.matchAll(/<a[^>]*href[^>]*>([^<]*)</g);
		for (const match of linkMatches) {
			const linkText = match[1].trim();
			const genericTexts = ['click here', 'read more', 'here', 'more', 'link'];
			
			if (genericTexts.includes(linkText.toLowerCase())) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 2.4.4',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'Link text should be descriptive',
					element: match[0],
					line,
					suggestion: 'Use descriptive link text that makes sense out of context',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html'
				});
			}
		}

		return issues;
	}

	private checkReadable(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for language specification (WCAG 3.1.1 - A)
		// This would typically be handled at the document level, so we'll check for lang attributes
		const hasLangAttribute = /lang="[a-z]{2}(-[A-Z]{2})?"/i.test(content);
		
		// For components, this might not always be applicable
		// Only flag if it's likely a main page component
		if (content.includes('<html') && !hasLangAttribute) {
			issues.push({
				rule: 'WCAG 3.1.1',
				wcagLevel: 'A',
				severity: 'error',
				message: 'Page language not specified',
				suggestion: 'Add lang attribute to html element (e.g., lang="en")',
				helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html'
			});
		}

		return issues;
	}

	private checkPredictable(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for context changes on focus (WCAG 3.2.1 - A)
		const onFocusHandlers = content.matchAll(/onFocus={[^}]*}/g);
		for (const match of onFocusHandlers) {
			const handler = match[0];
			// Simple heuristic - if it contains navigation or state changes, flag it
			if (/navigate|router|window\.location|setState/.test(handler)) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 3.2.1',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'Focus events should not cause unexpected context changes',
					line,
					suggestion: 'Avoid navigation or major state changes on focus events',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html'
				});
			}
		}

		return issues;
	}

	private checkCompatible(content: string, lines: string[]): AccessibilityIssue[] {
		const issues: AccessibilityIssue[] = [];

		// Check for proper element parsing (WCAG 4.1.1 - A)
		const unclosedTags = this.findUnclosedTags(content);
		if (unclosedTags.length > 0) {
			issues.push({
				rule: 'WCAG 4.1.1',
				wcagLevel: 'A',
				severity: 'error',
				message: 'HTML elements may not be properly formed',
				suggestion: 'Ensure all HTML elements are properly closed and nested',
				helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/parsing.html'
			});
		}

		// Check for valid ARIA usage (WCAG 4.1.2 - A)
		const ariaAttributes = content.matchAll(/aria-[a-z]+="[^"]*"/g);
		for (const match of ariaAttributes) {
			const attribute = match[0];
			// Basic validation for common ARIA attributes
			if (attribute.includes('aria-labelledby') && !/aria-labelledby="[a-zA-Z][a-zA-Z0-9_-]*"/.test(attribute)) {
				const line = this.getLineNumber(content, match.index || 0);
				issues.push({
					rule: 'WCAG 4.1.2',
					wcagLevel: 'A',
					severity: 'warning',
					message: 'ARIA attribute may have invalid value',
					element: attribute,
					line,
					suggestion: 'Ensure ARIA attribute values reference valid element IDs',
					helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html'
				});
			}
		}

		return issues;
	}

	private findUnclosedTags(content: string): string[] {
		// Simplified check for common unclosed tags
		const selfClosingTags = ['img', 'input', 'br', 'hr', 'meta', 'link'];
		const openTags = content.match(/<[a-zA-Z][a-zA-Z0-9]*(?:[^>]*[^/])>/g) || [];
		const closeTagMatches = content.match(/<\/[a-zA-Z][a-zA-Z0-9]*>/g) || [];
		const closeTags = closeTagMatches.map(tag => tag);
		
		const unclosed: string[] = [];
		
		// This is a simplified check - a full parser would be more accurate
		for (const openTag of openTags) {
			const tagName = openTag.match(/<([a-zA-Z][a-zA-Z0-9]*)/)?.[1];
			if (tagName && !selfClosingTags.includes(tagName)) {
				const closeTag = `</${tagName}>`;
				if (!closeTags.includes(closeTag)) {
					unclosed.push(tagName);
				}
			}
		}
		
		return [...new Set(unclosed)];
	}

	private getLineNumber(content: string, index: number): number {
		return content.substring(0, index).split('\\n').length;
	}

	private generateReport(component: ComponentInfo, issues: AccessibilityIssue[]): AccessibilityReport {
		// Calculate compliance levels
		const errorsByLevel = {
			A: issues.filter(i => i.wcagLevel === 'A' && i.severity === 'error').length,
			AA: issues.filter(i => i.wcagLevel === 'AA' && i.severity === 'error').length,
			AAA: issues.filter(i => i.wcagLevel === 'AAA' && i.severity === 'error').length
		};

		const compliance = {
			levelA: errorsByLevel.A === 0,
			levelAA: errorsByLevel.A === 0 && errorsByLevel.AA === 0,
			levelAAA: errorsByLevel.A === 0 && errorsByLevel.AA === 0 && errorsByLevel.AAA === 0
		};

		// Calculate score (0-100)
		const totalChecks = 20; // Approximate number of checks we perform
		const penaltyByLevel = { error: 5, warning: 2, info: 1 };
		const totalPenalty = issues.reduce((sum, issue) => sum + penaltyByLevel[issue.severity], 0);
		const score = Math.max(0, Math.round(((totalChecks * 5) - totalPenalty) / (totalChecks * 5) * 100));

		// Generate recommendations
		const recommendations = this.generateRecommendations(issues, compliance);

		return {
			component,
			issues,
			score,
			compliance,
			recommendations
		};
	}

	private generateRecommendations(issues: AccessibilityIssue[], compliance: any): string[] {
		const recommendations: string[] = [];

		if (!compliance.levelA) {
			recommendations.push('Address Level A issues first - these are fundamental accessibility requirements');
		}

		if (!compliance.levelAA) {
			recommendations.push('Work toward WCAG AA compliance for better accessibility standards');
		}

		const issuesByRule = new Map<string, number>();
		issues.forEach(issue => {
			issuesByRule.set(issue.rule, (issuesByRule.get(issue.rule) || 0) + 1);
		});

		// Specific recommendations based on common issues
		if (issuesByRule.get('WCAG 1.1.1')) {
			recommendations.push('Add alt text to images and accessible labels to icons');
		}

		if (issuesByRule.get('WCAG 1.3.1')) {
			recommendations.push('Improve semantic structure with proper headings and form labels');
		}

		if (issuesByRule.get('WCAG 2.1.1')) {
			recommendations.push('Ensure all interactive elements are keyboard accessible');
		}

		if (issuesByRule.get('WCAG 2.4.4')) {
			recommendations.push('Write descriptive link text that makes sense out of context');
		}

		// General recommendations
		recommendations.push('Test with screen readers like NVDA or JAWS');
		recommendations.push('Test keyboard navigation without using a mouse');
		recommendations.push('Verify color contrast meets WCAG AA standards (4.5:1 ratio)');

		return recommendations;
	}
}