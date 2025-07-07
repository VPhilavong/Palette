import { ComponentInfo, ProjectMetadata } from '../types';
import { CodebasePatterns } from '../codebase/codebaseAnalyzer';

/**
 * Builds context-aware prompts for component generation
 */
export class PromptBuilder {
    /**
     * Builds a prompt for generating a new component based on existing codebase context
     */
    buildComponentGenerationPrompt(
        request: string,
        context: ComponentInfo[],
        projectMetadata: ProjectMetadata,
        patterns?: CodebasePatterns,
        contextInfo?: string
    ): string {
        const frameworks = projectMetadata.frameworks.map(f => f.name).join(', ') || 'React';
        const hasTypeScript = projectMetadata.hasTypeScript;
        const uiLibraries = projectMetadata.uiLibraries.join(', ');
        
        let prompt = `Create a ${frameworks} component based on this request: "${request}"\n\n`;
        
        prompt += `Technical Requirements:\n`;
        prompt += `- Framework: ${frameworks}\n`;
        prompt += `- Language: ${hasTypeScript ? 'TypeScript' : 'JavaScript'}\n`;
        prompt += `- Available dependencies: ${Object.keys(projectMetadata.dependencies).slice(0, 10).join(', ')}\n`;
        
        if (uiLibraries) {
            prompt += `- UI Libraries: ${uiLibraries}\n`;
        }
        
        prompt += `\nComponent Requirements:\n`;
        prompt += `- Use modern functional components and hooks\n`;
        prompt += `- Include proper prop types/interfaces\n`;
        prompt += `- Add responsive design with appropriate breakpoints\n`;
        prompt += `- Include accessibility attributes (ARIA)\n`;
        prompt += `- Use semantic HTML elements\n`;
        prompt += `- Add hover and focus states for interactive elements\n`;
        prompt += `- DO NOT use external packages unless they are in the available dependencies list\n`;
        prompt += `- If icons are needed and no icon package is available, use text placeholders like [Icon]\n`;
        prompt += `- Create self-contained components with inline types if @/ imports don't exist\n`;
        
        if (uiLibraries.includes('Tailwind')) {
            prompt += `- Style with Tailwind CSS classes\n`;
        } else if (uiLibraries.includes('styled-components')) {
            prompt += `- Use styled-components for styling\n`;
        } else {
            prompt += `- Use modern CSS modules or inline styles\n`;
        }
        
        // Add codebase context if available
        if (contextInfo) {
            prompt += contextInfo;
        }
        
        // Add specific styling instructions based on patterns
        if (patterns) {
            switch (patterns.stylingApproach) {
                case 'css-modules':
                    prompt += `\n- Import styles as: import styles from './${request.replace(/\s+/g, '')}Component.module.css'\n`;
                    prompt += `- Use styles.className for styling\n`;
                    break;
                case 'tailwind':
                    prompt += `\n- Use Tailwind CSS classes for all styling\n`;
                    prompt += `- Include responsive breakpoints (sm:, md:, lg:)\n`;
                    break;
                case 'styled-components':
                    prompt += `\n- Use styled-components for styling\n`;
                    break;
            }
        }
        
        prompt += `\nGenerate ONLY the component code with appropriate imports. No explanations or markdown blocks.`;
        
        return prompt;
    }

    /**
     * Builds framework-specific system prompts
     */
    buildSystemPrompt(framework: string): string {
        const prompts = {
            'React': 'You are an expert React developer. Generate modern functional components using hooks.',
            'Vue': 'You are an expert Vue.js developer. Generate Vue 3 components using Composition API.',
            'Next.js': 'You are an expert Next.js developer. Generate SSR-ready React components.'
        };

        return prompts[framework as keyof typeof prompts] || prompts['React'];
    }

    /**
     * Builds context from similar components
     */
    private buildContextFromComponents(components: ComponentInfo[]): string {
        // TODO: Implement context building - Phase 5
        return '';
    }
}