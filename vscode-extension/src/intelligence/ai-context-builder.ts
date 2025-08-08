/**
 * Enhanced AI Context Builder
 * Builds intelligent context for AI prompts using VS Code APIs and project analysis
 * Following VS Code API best practices: https://code.visualstudio.com/api
 */

import * as vscode from 'vscode';
import { analyzeWorkspaceProject, ProjectStructure, ComponentType } from './typescript-project-analyzer';
import { getShadcnSpecialist, ShadcnAnalysis } from './shadcn-specialization';

export interface EnhancedAIContext {
    systemPrompt: string;
    projectContext: ProjectContext;
    availableActions: string[];
    codeInsights: CodeInsights;
    shadcnAnalysis?: ShadcnAnalysis;
}

export interface ProjectContext {
    projectPath: string;
    framework: string;
    buildTool: string;
    hasTypeScript: boolean;
    hasTailwind: boolean;
    hasShadcnUI: boolean;
    availableComponents: string[];
    projectStructure: {
        pages: string[];
        routes: string[];
        componentCount: number;
        complexityLevel: 'low' | 'medium' | 'high';
    };
    designSystem: {
        hasDesignTokens: boolean;
        tailwindConfigured: boolean;
        shadcnConfigured: boolean;
        cssVariables: string[];
    };
}

export interface CodeInsights {
    currentFile?: {
        fileName: string;
        language: string;
        isComponent: boolean;
        imports: string[];
        exports: string[];
    };
    selectedText?: string;
    workspaceStats: {
        totalFiles: number;
        componentFiles: number;
        pageFiles: number;
    };
}

export class AIContextBuilder {
    private static instance: AIContextBuilder;
    private cachedAnalysis: { structure: ProjectStructure; summary: any } | null = null;
    private cacheTimestamp: number = 0;
    private readonly CACHE_DURATION = 30000; // 30 seconds

    private constructor() {}

    static getInstance(): AIContextBuilder {
        if (!AIContextBuilder.instance) {
            AIContextBuilder.instance = new AIContextBuilder();
        }
        return AIContextBuilder.instance;
    }

    /**
     * Build comprehensive AI context using VS Code APIs and project analysis
     */
    async buildEnhancedContext(userMessage: string): Promise<EnhancedAIContext> {
        console.log('🧠 Building enhanced AI context...');

        // Get fresh project analysis (with caching)
        const analysis = await this.getProjectAnalysis();
        
        // Get current editor context
        const editorContext = await this.getCurrentEditorContext();
        
        // Build project context
        const projectContext = this.buildProjectContext(analysis);
        
        // Build code insights
        const codeInsights = await this.buildCodeInsights(analysis, editorContext);
        
        // Analyze shadcn/ui setup if project uses it
        let shadcnAnalysis: ShadcnAnalysis | undefined;
        if (projectContext.hasShadcnUI) {
            console.log('🎨 Analyzing shadcn/ui setup...');
            const shadcnSpecialist = getShadcnSpecialist();
            shadcnAnalysis = await shadcnSpecialist.analyzeShadcnSetup(analysis?.structure);
        }
        
        // Generate context-aware system prompt
        const systemPrompt = this.generateSystemPrompt(projectContext, userMessage, codeInsights, shadcnAnalysis);
        
        // Determine available actions
        const availableActions = this.determineAvailableActions(projectContext, userMessage);

        return {
            systemPrompt,
            projectContext,
            availableActions,
            codeInsights,
            shadcnAnalysis
        };
    }

    /**
     * Get project analysis with intelligent caching
     */
    private async getProjectAnalysis(): Promise<{ structure: ProjectStructure; summary: any } | null> {
        const now = Date.now();
        
        // Return cached analysis if still valid
        if (this.cachedAnalysis && (now - this.cacheTimestamp) < this.CACHE_DURATION) {
            return this.cachedAnalysis;
        }

        // Perform new analysis
        try {
            console.log('🔄 Refreshing project analysis cache...');
            this.cachedAnalysis = await analyzeWorkspaceProject();
            this.cacheTimestamp = now;
            return this.cachedAnalysis;
        } catch (error) {
            console.error('Failed to analyze project:', error);
            return null;
        }
    }

    /**
     * Get current editor context using VS Code APIs
     */
    private async getCurrentEditorContext(): Promise<any> {
        const activeEditor = vscode.window.activeTextEditor;
        if (!activeEditor) {
            return null;
        }

        const document = activeEditor.document;
        const selection = activeEditor.selection;

        return {
            fileName: document.fileName,
            language: document.languageId,
            isUntitled: document.isUntitled,
            lineCount: document.lineCount,
            selectedText: selection.isEmpty ? null : document.getText(selection),
            cursorPosition: {
                line: selection.active.line,
                character: selection.active.character
            }
        };
    }

    /**
     * Build comprehensive project context
     */
    private buildProjectContext(analysis: { structure: ProjectStructure; summary: any } | null): ProjectContext {
        if (!analysis) {
            return this.getDefaultProjectContext();
        }

        const { structure, summary } = analysis;

        return {
            projectPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
            framework: structure.framework,
            buildTool: structure.buildTool,
            hasTypeScript: structure.hasTypeScript,
            hasTailwind: structure.hasTailwind,
            hasShadcnUI: structure.hasShadcnUI,
            availableComponents: structure.components
                .filter(c => c.componentType === ComponentType.UI_LIBRARY)
                .map(c => c.name),
            projectStructure: {
                pages: structure.pages,
                routes: structure.routes,
                componentCount: structure.components.length,
                complexityLevel: this.determineComplexityLevel(summary.componentsSummary?.averageComplexity || 0)
            },
            designSystem: {
                hasDesignTokens: Object.keys(structure.designTokens).length > 0,
                tailwindConfigured: structure.hasTailwind,
                shadcnConfigured: structure.hasShadcnUI,
                cssVariables: this.extractCssVariableNames(structure.designTokens)
            }
        };
    }

    /**
     * Build code insights from current context
     */
    private async buildCodeInsights(
        analysis: { structure: ProjectStructure; summary: any } | null, 
        editorContext: any
    ): Promise<CodeInsights> {
        const insights: CodeInsights = {
            workspaceStats: {
                totalFiles: 0,
                componentFiles: 0,
                pageFiles: 0
            }
        };

        if (analysis) {
            insights.workspaceStats = {
                totalFiles: analysis.structure.components.length,
                componentFiles: analysis.structure.components.filter(c => 
                    c.componentType === ComponentType.UI_LIBRARY || c.componentType === ComponentType.FEATURE
                ).length,
                pageFiles: analysis.structure.components.filter(c => c.componentType === ComponentType.PAGE).length
            };
        }

        // Add current file context if available
        if (editorContext) {
            insights.currentFile = {
                fileName: editorContext.fileName,
                language: editorContext.language,
                isComponent: this.isReactComponent(editorContext.fileName, editorContext.language),
                imports: [], // Could be extracted from document analysis
                exports: []  // Could be extracted from document analysis
            };

            if (editorContext.selectedText) {
                insights.selectedText = editorContext.selectedText;
            }
        }

        return insights;
    }

    /**
     * Generate context-aware system prompt
     */
    private generateSystemPrompt(projectContext: ProjectContext, userMessage: string, codeInsights: CodeInsights, shadcnAnalysis?: ShadcnAnalysis): string {
        const basePrompt = `You are Palette AI, an expert UI developer assistant specialized in modern frontend development.

**Your Role:**
- Create beautiful, functional UI components and complete pages
- Generate production-ready code that follows best practices
- Understand and work with existing project structure and design systems
- Provide intelligent file management and code organization

**Current Project Context:**
- Framework: ${projectContext.framework}
- Build Tool: ${projectContext.buildTool}
- Language: ${projectContext.hasTypeScript ? 'TypeScript' : 'JavaScript'}
- Styling: ${projectContext.hasTailwind ? 'Tailwind CSS' : 'Standard CSS'}${projectContext.hasShadcnUI ? ' + shadcn/ui' : ''}
- Project Complexity: ${projectContext.projectStructure.complexityLevel}
`;

        // Add shadcn/ui specific context
        if (shadcnAnalysis) {
            const shadcnSpecialist = getShadcnSpecialist();
            const shadcnContext = shadcnSpecialist.buildShadcnContext(shadcnAnalysis, userMessage);
            const prompt = basePrompt + shadcnContext;
            return this.addContextualGuidance(prompt, userMessage, projectContext, codeInsights, shadcnAnalysis);
        }
        
        // Fallback: Add available components context
        if (projectContext.availableComponents.length > 0) {
            const components = projectContext.availableComponents.slice(0, 15); // Limit for token efficiency
            const prompt = basePrompt + `
**Available shadcn/ui Components:**
${components.join(', ')}${projectContext.availableComponents.length > 15 ? ` (and ${projectContext.availableComponents.length - 15} more)` : ''}

**Important:** Always use these existing components when appropriate. Import them using the pattern:
\`import { ComponentName } from "@/components/ui/component-name"\`
`;
            return this.addContextualGuidance(prompt, userMessage, projectContext, codeInsights);
        }

        return this.addContextualGuidance(basePrompt, userMessage, projectContext, codeInsights);
    }

    /**
     * Add contextual guidance based on user message and current context
     */
    private addContextualGuidance(
        basePrompt: string, 
        userMessage: string, 
        projectContext: ProjectContext,
        codeInsights: CodeInsights,
        shadcnAnalysis?: ShadcnAnalysis
    ): string {
        let prompt = basePrompt;

        // Add file-specific guidance
        if (codeInsights.currentFile) {
            prompt += `
**Current File Context:**
- File: ${codeInsights.currentFile.fileName}
- Language: ${codeInsights.currentFile.language}
- Is Component: ${codeInsights.currentFile.isComponent ? 'Yes' : 'No'}
`;

            if (codeInsights.selectedText) {
                prompt += `- Selected Code: Yes (${codeInsights.selectedText.length} characters)
`;
            }
        }

        // Add intent-specific guidance
        const intent = this.detectUserIntent(userMessage);
        prompt += this.getIntentSpecificGuidance(intent, projectContext, shadcnAnalysis);

        // Add general best practices
        prompt += `
**Code Generation Guidelines:**
- Use ${projectContext.hasTypeScript ? 'TypeScript' : 'JavaScript'} with proper typing
- Follow React functional component patterns with hooks
- Use ${projectContext.hasTailwind ? 'Tailwind CSS classes' : 'CSS modules or styled components'}
- Ensure components are accessible (ARIA attributes, semantic HTML)
- Create responsive designs that work on mobile and desktop
- Include proper imports and exports
- Generate complete, working code that users can immediately use

**File Placement Intelligence:**
- Components: \`src/components/\` (or \`src/components/ui/\` for shadcn/ui)
- Pages: \`src/pages/\` or \`src/app/\` 
- Hooks: \`src/hooks/\` (files starting with \`use\`)
- Utilities: \`src/lib/\` or \`src/utils/\`
- Types: \`src/types/\` (for TypeScript interfaces)

Focus on creating high-quality, maintainable code that integrates well with the existing project structure.
`;

        return prompt;
    }

    /**
     * Detect user intent from message
     */
    private detectUserIntent(message: string): string {
        const lowerMessage = message.toLowerCase();

        if (/\b(create|generate|make|build)\b.*\b(page|route|screen)\b/.test(lowerMessage)) return 'create_page';
        if (/\b(create|generate|make|build)\b.*\b(component|widget|element)\b/.test(lowerMessage)) return 'create_component';
        if (/\b(create|generate|make|build)\b.*\b(form|modal|dialog|popup)\b/.test(lowerMessage)) return 'create_form';
        if (/\b(fix|improve|refactor|update|modify)\b/.test(lowerMessage)) return 'modify_code';
        if (/\b(explain|how|what|why|help)\b/.test(lowerMessage)) return 'explain';
        if (/\b(style|design|theme|color|layout)\b/.test(lowerMessage)) return 'styling';

        return 'general';
    }

    /**
     * Get intent-specific guidance
     */
    private getIntentSpecificGuidance(intent: string, projectContext: ProjectContext, shadcnAnalysis?: ShadcnAnalysis): string {
        const guidanceMap: Record<string, string> = {
            create_page: `
**Page Creation Focus:**
- Create complete, functional pages with proper routing integration
- Include navigation elements if needed
- Use layout components for consistent structure
- Add loading states and error boundaries
- Consider SEO and accessibility requirements
`,
            create_component: `
**Component Creation Focus:**
- Build reusable, composable components
- Use proper TypeScript interfaces for props
- Include variant support using class-variance-authority (cva) if applicable
- Add proper JSDoc comments for documentation
- Consider component composition and flexibility
`,
            create_form: `
**Form Creation Focus:**
- Use proper form validation (React Hook Form + Zod recommended)
- Include accessibility features (labels, ARIA attributes)
- Add loading and error states
- Use ${projectContext.hasShadcnUI ? `shadcn/ui form components${shadcnAnalysis ? ` (${shadcnAnalysis.installedComponents.filter(c => ['button', 'input', 'label', 'form'].includes(c)).join(', ')})` : ''}` : 'appropriate form libraries'}
- Implement proper submit handling and feedback
${shadcnAnalysis && !shadcnAnalysis.installedComponents.includes('button') ? '\n- **Note**: Button component not installed - consider installing: `npx shadcn-ui@latest add button`' : ''}
`,
            styling: `
**Styling Focus:**
- Use ${projectContext.hasTailwind ? 'Tailwind utility classes' : 'CSS best practices'}
- Follow design system tokens and spacing scales
- Ensure responsive design across all screen sizes
- Consider dark mode support if applicable
- Use consistent color palette and typography
`,
            general: ''
        };

        return guidanceMap[intent] || guidanceMap.general;
    }

    /**
     * Determine available actions based on context
     */
    private determineAvailableActions(projectContext: ProjectContext, userMessage: string): string[] {
        const actions = ['Generate Code', 'Create File'];

        if (projectContext.hasShadcnUI) {
            actions.push('Install shadcn/ui Component');
        }

        if (projectContext.projectStructure.routes.length > 0) {
            actions.push('Add Route');
        }

        const intent = this.detectUserIntent(userMessage);
        if (intent === 'create_page') {
            actions.push('Update Navigation', 'Add to Routing');
        }

        return actions;
    }

    /**
     * Helper methods
     */
    private getDefaultProjectContext(): ProjectContext {
        return {
            projectPath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
            framework: 'react',
            buildTool: 'vite',
            hasTypeScript: true,
            hasTailwind: true,
            hasShadcnUI: false,
            availableComponents: [],
            projectStructure: {
                pages: [],
                routes: [],
                componentCount: 0,
                complexityLevel: 'low'
            },
            designSystem: {
                hasDesignTokens: false,
                tailwindConfigured: false,
                shadcnConfigured: false,
                cssVariables: []
            }
        };
    }

    private determineComplexityLevel(averageComplexity: number): 'low' | 'medium' | 'high' {
        if (averageComplexity < 5) return 'low';
        if (averageComplexity < 10) return 'medium';
        return 'high';
    }

    private extractCssVariableNames(designTokens: Record<string, any>): string[] {
        const variables: string[] = [];
        
        if (designTokens.cssVariables) {
            Object.values(designTokens.cssVariables).forEach((vars: any) => {
                if (Array.isArray(vars)) {
                    vars.forEach((v: string) => {
                        const match = v.match(/^(--[\w-]+):/);
                        if (match) variables.push(match[1]);
                    });
                }
            });
        }

        return variables;
    }

    private isReactComponent(fileName: string, language: string): boolean {
        return (language === 'typescriptreact' || language === 'javascriptreact') && 
               (fileName.endsWith('.tsx') || fileName.endsWith('.jsx'));
    }

    /**
     * Clear the analysis cache (useful for testing or after major project changes)
     */
    clearCache(): void {
        this.cachedAnalysis = null;
        this.cacheTimestamp = 0;
        console.log('🗑️ AI context cache cleared');
    }
}

// Factory function for easy access
export function getAIContextBuilder(): AIContextBuilder {
    return AIContextBuilder.getInstance();
}