/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { ComponentGenerator } from '../../../llm/componentGenerator';
import { FileIndexer } from '../../../codebase/fileIndexer';
import { ComponentAnalyzer } from '../../../codebase/componentAnalyzer';
import { ILogService } from '../../../platform/log/common/logService';
import { IConfigurationService } from '../../../platform/configuration/common/configurationService';

export interface ComponentGenerationOptions {
	componentName: string;
	description: string;
	designSystem: 'tailwindui' | 'shadcn' | 'custom';
	includeTests?: boolean;
	includeStories?: boolean;
}

export interface ComponentGenerationResult {
	success: boolean;
	componentCode: string | null;
	filePath: string | null;
	designPatterns: string[];
	accessibilityFeatures: string[];
	error?: string;
}

export class ComponentGenerationTool {
	private componentGenerator: ComponentGenerator;
	private fileIndexer: FileIndexer;
	private componentAnalyzer: ComponentAnalyzer;

	constructor(
		private readonly logService: ILogService,
		private readonly configurationService: IConfigurationService
	) {
		this.componentGenerator = new ComponentGenerator();
		this.fileIndexer = new FileIndexer();
		this.componentAnalyzer = new ComponentAnalyzer();
	}

	async generateComponent(options: ComponentGenerationOptions): Promise<ComponentGenerationResult> {
		this.logService.info('ComponentGenerationTool: Starting generation', options);

		try {
			// Get current workspace index for context
			const workspaceIndex = await this.getWorkspaceIndex();
			
			// Enhance the description with design system and accessibility requirements
			const enhancedDescription = this.enhanceDescriptionWithDesignRequirements(
				options.description, 
				options.designSystem
			);

			this.logService.info('ComponentGenerationTool: Generating with enhanced description', { enhancedDescription });

			// Generate the component using existing logic
			const generatedCode = await this.componentGenerator.generateComponent(
				enhancedDescription,
				workspaceIndex
			);

			if (!generatedCode) {
				return {
					success: false,
					componentCode: null,
					filePath: null,
					designPatterns: [],
					accessibilityFeatures: [],
					error: 'Failed to generate component code'
				};
			}

			// Analyze the generated component for patterns and features
			const analysis = this.analyzeGeneratedComponent(generatedCode, options.designSystem);

			this.logService.info('ComponentGenerationTool: Generation successful', {
				designPatterns: analysis.designPatterns.length,
				accessibilityFeatures: analysis.accessibilityFeatures.length
			});

			return {
				success: true,
				componentCode: generatedCode,
				filePath: this.getExpectedFilePath(options.componentName),
				designPatterns: analysis.designPatterns,
				accessibilityFeatures: analysis.accessibilityFeatures
			};

		} catch (error) {
			this.logService.error('ComponentGenerationTool: Generation failed', error);
			return {
				success: false,
				componentCode: null,
				filePath: null,
				designPatterns: [],
				accessibilityFeatures: [],
				error: error instanceof Error ? error.message : 'Unknown error'
			};
		}
	}

	private async getWorkspaceIndex() {
		try {
			// Create a simple workspace index using file indexer and component analyzer
			const files = await this.fileIndexer.indexWorkspace();
			const components = await this.componentAnalyzer.analyzeComponents(files);
			
			// Create a complete workspace index structure
			return {
				files,
				components,
				project: {
					rootPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
					name: vscode.workspace.name || 'Unknown',
					frameworks: [{ 
						name: 'React', 
						version: 'unknown',
						detected: true,
						confidence: 0.8 
					}],
					dependencies: {},
					devDependencies: {},
					hasTypeScript: files.some(f => f.extension === '.ts' || f.extension === '.tsx'),
					uiLibraries: [],
					stateManagement: []
				},
				lastUpdated: new Date()
			};
		} catch (error) {
			this.logService.warn('ComponentGenerationTool: Could not get workspace index', error);
			return null;
		}
	}

	private enhanceDescriptionWithDesignRequirements(
		description: string, 
		designSystem: string
	): string {
		const designSystemInstructions = this.getDesignSystemInstructions(designSystem);
		const accessibilityRequirements = this.getAccessibilityRequirements();
		const responsiveDesignRequirements = this.getResponsiveDesignRequirements();

		return `${description}

DESIGN SYSTEM REQUIREMENTS:
${designSystemInstructions}

ACCESSIBILITY REQUIREMENTS (WCAG 2.1 AA):
${accessibilityRequirements}

RESPONSIVE DESIGN REQUIREMENTS:
${responsiveDesignRequirements}

ADDITIONAL REQUIREMENTS:
- Follow Nielsen's 10 usability heuristics
- Implement proper error states and loading states
- Use semantic HTML elements
- Include proper TypeScript types
- Add meaningful hover and focus states
- Follow the existing project's patterns and conventions`;
	}

	private getDesignSystemInstructions(designSystem: string): string {
		switch (designSystem) {
			case 'tailwindui':
				return `- Use Tailwind UI design patterns and components
- Apply Tailwind CSS utility classes for styling
- Follow Tailwind UI color palette and spacing scale
- Use Tailwind UI's form patterns and button styles
- Implement Tailwind UI's layout and grid systems`;

			case 'shadcn':
				return `- Use shadcn/ui component patterns and styling approach
- Apply CSS variables for theming consistency
- Follow shadcn/ui's composition patterns
- Use shadcn/ui's color system and design tokens
- Implement shadcn/ui's form and input patterns`;

			case 'custom':
				return `- Follow the existing project's custom design system
- Use consistent spacing, colors, and typography from the project
- Match existing component patterns and conventions
- Apply the project's established styling approach`;

			default:
				return '- Use modern CSS practices and consistent design patterns';
		}
	}

	private getAccessibilityRequirements(): string {
		return `- Use semantic HTML elements (nav, main, section, article, etc.)
- Add proper ARIA labels and roles where needed
- Ensure keyboard navigation support (tabIndex, onKeyDown)
- Include focus management and visible focus indicators
- Add alt text for images and meaningful labels for form inputs
- Ensure color contrast meets WCAG AA standards (4.5:1 ratio)
- Support screen readers with proper content structure
- Add skip links for better navigation where applicable`;
	}

	private getResponsiveDesignRequirements(): string {
		const designSystem = this.configurationService.getValue('palette.design.system', 'tailwindui');
		
		if (designSystem === 'tailwindui' || designSystem === 'custom') {
			return `- Use Tailwind responsive breakpoints (sm:, md:, lg:, xl:, 2xl:)
- Implement mobile-first responsive design
- Ensure touch-friendly interface on mobile devices
- Use responsive typography and spacing
- Apply responsive layout patterns (grid, flex)`;
		}

		return `- Implement responsive design for mobile, tablet, and desktop
- Use CSS Grid and Flexbox for responsive layouts
- Apply responsive typography and spacing
- Ensure touch-friendly interface on mobile devices`;
	}

	private analyzeGeneratedComponent(code: string, designSystem: string): {
		designPatterns: string[];
		accessibilityFeatures: string[];
	} {
		const designPatterns: string[] = [];
		const accessibilityFeatures: string[] = [];

		// Analyze design patterns
		if (code.includes('className=')) {
			designPatterns.push('CSS class-based styling');
		}
		if (code.includes('bg-') || code.includes('text-') || code.includes('p-') || code.includes('m-')) {
			designPatterns.push('Tailwind utility classes');
		}
		if (code.includes('useState') || code.includes('useEffect')) {
			designPatterns.push('React Hooks pattern');
		}
		if (code.includes('interface ') || code.includes('type ')) {
			designPatterns.push('TypeScript type definitions');
		}
		if (code.includes('grid') || code.includes('flex')) {
			designPatterns.push('Modern CSS layout (Grid/Flexbox)');
		}

		// Analyze accessibility features
		if (code.includes('aria-label') || code.includes('aria-')) {
			accessibilityFeatures.push('ARIA labels and attributes');
		}
		if (code.includes('<nav') || code.includes('<main') || code.includes('<section')) {
			accessibilityFeatures.push('Semantic HTML elements');
		}
		if (code.includes('alt=')) {
			accessibilityFeatures.push('Image alt text');
		}
		if (code.includes('tabIndex') || code.includes('onKeyDown')) {
			accessibilityFeatures.push('Keyboard navigation support');
		}
		if (code.includes('focus:') || code.includes(':focus')) {
			accessibilityFeatures.push('Focus indicators');
		}
		if (code.includes('<label') || code.includes('htmlFor')) {
			accessibilityFeatures.push('Form labels');
		}

		return { designPatterns, accessibilityFeatures };
	}

	private getExpectedFilePath(componentName: string): string {
		const workspaceFolders = vscode.workspace.workspaceFolders;
		if (!workspaceFolders) {
			return '';
		}

		// Use common component directory patterns
		const rootPath = workspaceFolders[0].uri.fsPath;
		const commonPaths = [
			'src/components',
			'components',
			'src/ui',
			'ui',
			'app/components',
			'src'
		];

		// Return the first existing path, or default to src/components
		for (const relativePath of commonPaths) {
			const fullPath = vscode.Uri.joinPath(workspaceFolders[0].uri, relativePath);
			try {
				// This would need to be made async in a real implementation
				return `${fullPath.fsPath}/${componentName}.tsx`;
			} catch {
				continue;
			}
		}

		return `${rootPath}/src/components/${componentName}.tsx`;
	}

	async generateComponentCode(options: ComponentGenerationOptions): Promise<string | null> {
		this.logService.info('ComponentGenerationTool: Generating code only', options);

		try {
			const workspaceIndex = await this.getWorkspaceIndex();
			const enhancedDescription = this.enhanceDescriptionWithDesignRequirements(
				options.description,
				options.designSystem
			);

			return await this.componentGenerator.generateComponentCode(
				enhancedDescription,
				workspaceIndex
			);

		} catch (error) {
			this.logService.error('ComponentGenerationTool: Code generation failed', error);
			return null;
		}
	}
}