/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ComponentInfo, FileMetadata } from '../../types';
import { ILogService } from '../../platform/log/common/logService';

export interface DesignPattern {
	name: string;
	type: 'component' | 'layout' | 'utility' | 'interaction';
	description: string;
	filePath: string;
	codeSnippet: string;
	designSystem: 'tailwind' | 'shadcn' | 'custom' | 'css-modules';
	tags: string[];
	usageCount: number;
	accessibility: {
		hasAriaLabels: boolean;
		hasSemanticHTML: boolean;
		hasKeyboardSupport: boolean;
	};
}

export interface TailwindPattern {
	utility: string;
	category: 'layout' | 'spacing' | 'colors' | 'typography' | 'responsive';
	description: string;
	examples: string[];
	usage: number;
}

export interface SearchResult {
	patterns: DesignPattern[];
	tailwindUtilities: TailwindPattern[];
	components: ComponentInfo[];
	suggestions: string[];
}

export class WorkspacePatternSearch {
	private designPatternCache: Map<string, DesignPattern[]> = new Map();
	private tailwindPatternCache: Map<string, TailwindPattern[]> = new Map();

	constructor(private readonly logService: ILogService) {}

	async searchDesignPatterns(query: string, components: ComponentInfo[]): Promise<SearchResult> {
		this.logService.info('WorkspacePatternSearch: Searching patterns', { query });

		try {
			// Parse search query for specific patterns
			const searchTerms = this.parseSearchQuery(query);
			
			// Search for design patterns
			const patterns = await this.findDesignPatterns(searchTerms, components);
			
			// Extract Tailwind utility patterns
			const tailwindUtilities = await this.findTailwindPatterns(searchTerms, components);
			
			// Find relevant components
			const relevantComponents = this.findRelevantComponents(searchTerms, components);
			
			// Generate suggestions
			const suggestions = this.generateSearchSuggestions(searchTerms, patterns);

			return {
				patterns,
				tailwindUtilities,
				components: relevantComponents,
				suggestions
			};

		} catch (error) {
			this.logService.error('WorkspacePatternSearch: Search failed', error);
			return {
				patterns: [],
				tailwindUtilities: [],
				components: [],
				suggestions: ['Search failed. Please try again with different terms.']
			};
		}
	}

	private parseSearchQuery(query: string): {
		keywords: string[];
		componentTypes: string[];
		designSystems: string[];
		categories: string[];
	} {
		const keywords = query.toLowerCase().split(/\\s+/);
		
		// Detect component types
		const componentTypes = keywords.filter(keyword => 
			['button', 'card', 'modal', 'form', 'input', 'dropdown', 'nav', 'navigation', 
			 'header', 'footer', 'sidebar', 'table', 'list', 'grid', 'chart'].includes(keyword)
		);

		// Detect design systems
		const designSystems = keywords.filter(keyword =>
			['tailwind', 'shadcn', 'ui', 'css-modules', 'styled'].includes(keyword)
		);

		// Detect categories
		const categories = keywords.filter(keyword =>
			['layout', 'spacing', 'color', 'typography', 'responsive', 'animation', 'interaction'].includes(keyword)
		);

		return {
			keywords,
			componentTypes,
			designSystems,
			categories
		};
	}

	private async findDesignPatterns(
		searchTerms: ReturnType<typeof this.parseSearchQuery>, 
		components: ComponentInfo[]
	): Promise<DesignPattern[]> {
		const patterns: DesignPattern[] = [];

		for (const component of components) {
			try {
				// Read component file to analyze patterns
				const document = await vscode.workspace.openTextDocument(component.path);
				const content = document.getText();

				// Extract design patterns from component
				const componentPatterns = await this.extractPatternsFromComponent(
					component, 
					content, 
					searchTerms
				);
				
				patterns.push(...componentPatterns);

			} catch (error) {
				this.logService.warn('WorkspacePatternSearch: Could not read component', { 
					path: component.path, 
					error 
				});
			}
		}

		// Sort by relevance and usage
		return patterns
			.filter(pattern => this.isPatternRelevant(pattern, searchTerms))
			.sort((a, b) => b.usageCount - a.usageCount)
			.slice(0, 20); // Limit to top 20 patterns
	}

	private async extractPatternsFromComponent(
		component: ComponentInfo,
		content: string,
		searchTerms: ReturnType<typeof this.parseSearchQuery>
	): Promise<DesignPattern[]> {
		const patterns: DesignPattern[] = [];

		// Detect design system being used
		const designSystem = this.detectDesignSystem(content);

		// Extract layout patterns
		patterns.push(...this.extractLayoutPatterns(component, content, designSystem));

		// Extract component patterns
		patterns.push(...this.extractComponentPatterns(component, content, designSystem));

		// Extract interaction patterns
		patterns.push(...this.extractInteractionPatterns(component, content, designSystem));

		// Extract utility patterns (if Tailwind)
		if (designSystem === 'tailwind') {
			patterns.push(...this.extractTailwindUtilityPatterns(component, content));
		}

		return patterns;
	}

	private detectDesignSystem(content: string): 'tailwind' | 'shadcn' | 'custom' | 'css-modules' {
		if (content.includes('className=') && /\\b(bg-|text-|p-|m-|flex|grid)/.test(content)) {
			return 'tailwind';
		}
		if (content.includes('cn(') || content.includes('clsx(') || content.includes('@/components/ui')) {
			return 'shadcn';
		}
		if (content.includes('styles.') && content.includes('.module.css')) {
			return 'css-modules';
		}
		return 'custom';
	}

	private extractLayoutPatterns(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern[] {
		const patterns: DesignPattern[] = [];

		// Flexbox patterns
		if (content.includes('flex') || content.includes('display: flex')) {
			const flexPattern = this.createFlexPattern(component, content, designSystem);
			if (flexPattern) patterns.push(flexPattern);
		}

		// Grid patterns
		if (content.includes('grid') || content.includes('display: grid')) {
			const gridPattern = this.createGridPattern(component, content, designSystem);
			if (gridPattern) patterns.push(gridPattern);
		}

		// Container patterns
		if (content.includes('container') || content.includes('max-w-')) {
			const containerPattern = this.createContainerPattern(component, content, designSystem);
			if (containerPattern) patterns.push(containerPattern);
		}

		return patterns;
	}

	private extractComponentPatterns(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern[] {
		const patterns: DesignPattern[] = [];

		// Button patterns
		if (content.includes('button') || /\\b(btn|Button)\\b/.test(content)) {
			const buttonPattern = this.createButtonPattern(component, content, designSystem);
			if (buttonPattern) patterns.push(buttonPattern);
		}

		// Card patterns
		if (content.includes('card') || /\\b(Card|card)\\b/.test(content)) {
			const cardPattern = this.createCardPattern(component, content, designSystem);
			if (cardPattern) patterns.push(cardPattern);
		}

		// Form patterns
		if (content.includes('form') || content.includes('input') || content.includes('Form')) {
			const formPattern = this.createFormPattern(component, content, designSystem);
			if (formPattern) patterns.push(formPattern);
		}

		return patterns;
	}

	private extractInteractionPatterns(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern[] {
		const patterns: DesignPattern[] = [];

		// Hover patterns
		if (content.includes('hover:') || content.includes(':hover')) {
			const hoverPattern = this.createHoverPattern(component, content, designSystem);
			if (hoverPattern) patterns.push(hoverPattern);
		}

		// Focus patterns
		if (content.includes('focus:') || content.includes(':focus')) {
			const focusPattern = this.createFocusPattern(component, content, designSystem);
			if (focusPattern) patterns.push(focusPattern);
		}

		// Animation patterns
		if (content.includes('transition') || content.includes('animate')) {
			const animationPattern = this.createAnimationPattern(component, content, designSystem);
			if (animationPattern) patterns.push(animationPattern);
		}

		return patterns;
	}

	private extractTailwindUtilityPatterns(
		component: ComponentInfo,
		content: string
	): DesignPattern[] {
		const patterns: DesignPattern[] = [];

		// Extract responsive patterns
		const responsiveMatches = content.match(/(sm:|md:|lg:|xl:|2xl:)[\\w-]+/g);
		if (responsiveMatches) {
			const responsivePattern = this.createResponsivePattern(component, content, responsiveMatches);
			if (responsivePattern) patterns.push(responsivePattern);
		}

		// Extract spacing patterns
		const spacingMatches = content.match(/(p-|m-|px-|py-|mx-|my-|pt-|pb-|pl-|pr-|mt-|mb-|ml-|mr-)[\\d]+/g);
		if (spacingMatches) {
			const spacingPattern = this.createSpacingPattern(component, content, spacingMatches);
			if (spacingPattern) patterns.push(spacingPattern);
		}

		return patterns;
	}

	// Pattern creation methods
	private createFlexPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const flexClasses = content.match(/flex[\\w-]*/g) || [];
		if (flexClasses.length === 0) return null;

		return {
			name: 'Flexbox Layout',
			type: 'layout',
			description: `Flexbox layout pattern using ${flexClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'flex'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['layout', 'flexbox', ...flexClasses],
			usageCount: flexClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createGridPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const gridClasses = content.match(/grid[\\w-]*/g) || [];
		if (gridClasses.length === 0) return null;

		return {
			name: 'CSS Grid Layout',
			type: 'layout',
			description: `CSS Grid layout pattern using ${gridClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'grid'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['layout', 'grid', ...gridClasses],
			usageCount: gridClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createContainerPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const containerClasses = content.match(/(container|max-w-[\\w]+)/g) || [];
		if (containerClasses.length === 0) return null;

		return {
			name: 'Container Pattern',
			type: 'layout',
			description: `Container layout pattern using ${containerClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'container|max-w-'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['layout', 'container', ...containerClasses],
			usageCount: containerClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createButtonPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const buttonMatch = content.match(/<button[^>]*>[\\s\\S]*?<\/button>/);
		if (!buttonMatch) return null;

		return {
			name: 'Button Component',
			type: 'component',
			description: 'Interactive button component with styling and accessibility',
			filePath: component.path,
			codeSnippet: buttonMatch[0],
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['component', 'button', 'interactive'],
			usageCount: (content.match(/<button/g) || []).length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createCardPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const hasCardStructure = content.includes('card') || 
								content.match(/className="[^"]*(?:bg-white|border|shadow|rounded)/);
		if (!hasCardStructure) return null;

		return {
			name: 'Card Component',
			type: 'component',
			description: 'Card layout component with structured content',
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'card|bg-white|border|shadow'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['component', 'card', 'layout'],
			usageCount: (content.match(/\\bcard\\b/gi) || []).length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createFormPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const hasForm = content.includes('<form') || content.includes('<input');
		if (!hasForm) return null;

		return {
			name: 'Form Pattern',
			type: 'component',
			description: 'Form component with inputs and validation',
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'form|input'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['component', 'form', 'input', 'validation'],
			usageCount: (content.match(/<(?:form|input)/g) || []).length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createHoverPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const hoverClasses = content.match(/hover:[\\w-]+/g) || [];
		if (hoverClasses.length === 0) return null;

		return {
			name: 'Hover Interaction',
			type: 'interaction',
			description: `Hover effects using ${hoverClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'hover:'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['interaction', 'hover', ...hoverClasses],
			usageCount: hoverClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createFocusPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const focusClasses = content.match(/focus:[\\w-]+/g) || [];
		if (focusClasses.length === 0) return null;

		return {
			name: 'Focus Interaction',
			type: 'interaction',
			description: `Focus states using ${focusClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'focus:'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['interaction', 'focus', 'accessibility', ...focusClasses],
			usageCount: focusClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createAnimationPattern(
		component: ComponentInfo,
		content: string,
		designSystem: string
	): DesignPattern | null {
		const animationClasses = content.match(/(transition|animate)[\\w-]*/g) || [];
		if (animationClasses.length === 0) return null;

		return {
			name: 'Animation Pattern',
			type: 'interaction',
			description: `Animations using ${animationClasses.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'transition|animate'),
			designSystem: designSystem as 'tailwind' | 'shadcn' | 'custom' | 'css-modules',
			tags: ['interaction', 'animation', ...animationClasses],
			usageCount: animationClasses.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createResponsivePattern(
		component: ComponentInfo,
		content: string,
		responsiveMatches: string[]
	): DesignPattern | null {
		return {
			name: 'Responsive Design',
			type: 'utility',
			description: `Responsive design using ${responsiveMatches.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'sm:|md:|lg:|xl:|2xl:'),
			designSystem: 'tailwind',
			tags: ['responsive', 'utility', ...responsiveMatches],
			usageCount: responsiveMatches.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private createSpacingPattern(
		component: ComponentInfo,
		content: string,
		spacingMatches: string[]
	): DesignPattern | null {
		return {
			name: 'Spacing Pattern',
			type: 'utility',
			description: `Spacing utilities using ${spacingMatches.join(', ')}`,
			filePath: component.path,
			codeSnippet: this.extractRelevantCodeSnippet(content, 'p-|m-|px-|py-|mx-|my-'),
			designSystem: 'tailwind',
			tags: ['spacing', 'utility', ...spacingMatches],
			usageCount: spacingMatches.length,
			accessibility: this.analyzeAccessibility(content)
		};
	}

	private extractRelevantCodeSnippet(content: string, pattern: string): string {
		const regex = new RegExp(`.*${pattern}.*`, 'g');
		const matches = content.match(regex);
		if (!matches) return '';
		
		// Return the first few relevant lines
		return matches.slice(0, 3).join('\\n');
	}

	private analyzeAccessibility(content: string): {
		hasAriaLabels: boolean;
		hasSemanticHTML: boolean;
		hasKeyboardSupport: boolean;
	} {
		return {
			hasAriaLabels: /aria-[\\w]+=/i.test(content),
			hasSemanticHTML: /<(nav|main|section|article|aside|header|footer)/.test(content),
			hasKeyboardSupport: /onKey|tabIndex/i.test(content)
		};
	}

	private async findTailwindPatterns(
		searchTerms: ReturnType<typeof this.parseSearchQuery>,
		components: ComponentInfo[]
	): Promise<TailwindPattern[]> {
		const patterns: TailwindPattern[] = [];
		const utilityCounter = new Map<string, number>();

		// Analyze all components for Tailwind usage
		for (const component of components) {
			try {
				const document = await vscode.workspace.openTextDocument(component.path);
				const content = document.getText();

				// Extract Tailwind utilities
				const tailwindClasses = this.extractTailwindUtilities(content);
				
				tailwindClasses.forEach(utility => {
					utilityCounter.set(utility, (utilityCounter.get(utility) || 0) + 1);
				});

			} catch (error) {
				// Skip files that can't be read
			}
		}

		// Convert to patterns
		for (const [utility, count] of utilityCounter.entries()) {
			const pattern = this.createTailwindPattern(utility, count);
			if (pattern && this.isTailwindPatternRelevant(pattern, searchTerms)) {
				patterns.push(pattern);
			}
		}

		return patterns.sort((a, b) => b.usage - a.usage).slice(0, 15);
	}

	private extractTailwindUtilities(content: string): string[] {
		const classNameMatches = content.match(/className="([^"]*)"/g) || [];
		const utilities: string[] = [];

		classNameMatches.forEach(match => {
			const classes = match.replace(/className="|"/g, '').split(/\\s+/);
			utilities.push(...classes.filter(cls => this.isTailwindUtility(cls)));
		});

		return utilities;
	}

	private isTailwindUtility(className: string): boolean {
		// Common Tailwind utility patterns
		const tailwindPatterns = [
			/^(bg-|text-|border-|p-|m-|px-|py-|mx-|my-|pt-|pb-|pl-|pr-|mt-|mb-|ml-|mr-)/,
			/^(w-|h-|min-w-|min-h-|max-w-|max-h-)/,
			/^(flex|grid|block|inline|hidden)/,
			/^(rounded|shadow|opacity|z-)/,
			/^(sm:|md:|lg:|xl:|2xl:)/,
			/^(hover:|focus:|active:)/
		];

		return tailwindPatterns.some(pattern => pattern.test(className));
	}

	private createTailwindPattern(utility: string, usage: number): TailwindPattern | null {
		const category = this.categorizeTailwindUtility(utility);
		if (!category) return null;

		return {
			utility,
			category,
			description: this.describeTailwindUtility(utility),
			examples: this.generateTailwindExamples(utility),
			usage
		};
	}

	private categorizeTailwindUtility(utility: string): TailwindPattern['category'] | null {
		if (/^(flex|grid|block|inline|hidden|container)/.test(utility)) return 'layout';
		if (/^(p-|m-|px-|py-|mx-|my-|pt-|pb-|pl-|pr-|mt-|mb-|ml-|mr-)/.test(utility)) return 'spacing';
		if (/^(bg-|text-|border-)/.test(utility)) return 'colors';
		if (/^(text-|font-|leading-|tracking-)/.test(utility)) return 'typography';
		if (/^(sm:|md:|lg:|xl:|2xl:)/.test(utility)) return 'responsive';
		return null;
	}

	private describeTailwindUtility(utility: string): string {
		// Simplified descriptions for common utilities
		const descriptions: Record<string, string> = {
			'flex': 'Creates a flex container',
			'grid': 'Creates a grid container',
			'block': 'Sets display to block',
			'hidden': 'Hides the element',
			'container': 'Sets max-width and centers content'
		};

		return descriptions[utility] || `Tailwind utility: ${utility}`;
	}

	private generateTailwindExamples(utility: string): string[] {
		// Return simple examples
		return [`<div className="${utility}">`, `<span className="${utility}">`];
	}

	private findRelevantComponents(
		searchTerms: ReturnType<typeof this.parseSearchQuery>,
		components: ComponentInfo[]
	): ComponentInfo[] {
		return components.filter(component => {
			// Match component name
			const nameMatch = searchTerms.keywords.some(keyword =>
				component.name.toLowerCase().includes(keyword)
			);

			// Match component types
			const typeMatch = searchTerms.componentTypes.some(type =>
				component.name.toLowerCase().includes(type)
			);

			// Match exports
			const exportMatch = component.exports.some(exp =>
				searchTerms.keywords.some(keyword =>
					exp.toLowerCase().includes(keyword)
				)
			);

			return nameMatch || typeMatch || exportMatch;
		}).slice(0, 10); // Limit results
	}

	private isPatternRelevant(
		pattern: DesignPattern,
		searchTerms: ReturnType<typeof this.parseSearchQuery>
	): boolean {
		const relevantKeywords = [
			...searchTerms.keywords,
			...searchTerms.componentTypes,
			...searchTerms.categories
		];

		return relevantKeywords.some(keyword =>
			pattern.name.toLowerCase().includes(keyword) ||
			pattern.description.toLowerCase().includes(keyword) ||
			pattern.tags.some(tag => tag.toLowerCase().includes(keyword))
		);
	}

	private isTailwindPatternRelevant(
		pattern: TailwindPattern,
		searchTerms: ReturnType<typeof this.parseSearchQuery>
	): boolean {
		return searchTerms.keywords.some(keyword =>
			pattern.utility.includes(keyword) ||
			pattern.category.includes(keyword) ||
			pattern.description.toLowerCase().includes(keyword)
		);
	}

	private generateSearchSuggestions(
		searchTerms: ReturnType<typeof this.parseSearchQuery>,
		patterns: DesignPattern[]
	): string[] {
		const suggestions: string[] = [];

		// Suggest related patterns
		if (patterns.length > 0) {
			const commonTags = this.getCommonTags(patterns);
			suggestions.push(...commonTags.map(tag => `Try searching for "${tag}" patterns`));
		}

		// Suggest specific component types
		if (searchTerms.componentTypes.length === 0) {
			suggestions.push('Try searching for specific components like "button", "card", or "form"');
		}

		// Suggest design systems
		if (searchTerms.designSystems.length === 0) {
			suggestions.push('Try filtering by design system: "tailwind", "shadcn", or "css-modules"');
		}

		return suggestions.slice(0, 5);
	}

	private getCommonTags(patterns: DesignPattern[]): string[] {
		const tagCounts = new Map<string, number>();
		
		patterns.forEach(pattern => {
			pattern.tags.forEach(tag => {
				tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
			});
		});

		return Array.from(tagCounts.entries())
			.sort(([, a], [, b]) => b - a)
			.slice(0, 3)
			.map(([tag]) => tag);
	}
}