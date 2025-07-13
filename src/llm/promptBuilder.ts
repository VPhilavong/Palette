/**
 * Prompt Builder
 * 
 * This file constructs intelligent prompts for the AI model by:
 * - Building context-aware prompts from similar components
 * - Analyzing codebase patterns (styling, APIs, themes, etc.)
 * - Including relevant project metadata and frameworks
 * - Formatting component information for optimal AI understanding
 * - Creating structured prompts that lead to better code generation
 * 
 * The prompts include examples, patterns, and constraints from the codebase.
 */

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
        prompt += `- Include proper prop types/interfaces with clear, descriptive names\n`;
        prompt += `- Add responsive design with appropriate breakpoints\n`;
        prompt += `- Include accessibility attributes (ARIA) and semantic HTML\n`;
        prompt += `- Use semantic HTML elements (section, article, nav, main, etc.)\n`;
        prompt += `- Add hover and focus states for interactive elements\n`;
        prompt += `- DO NOT use external packages unless they are in the available dependencies list\n`;
        prompt += `- If icons are needed and no icon package is available, use text placeholders like [Icon]\n`;
        prompt += `- Create self-contained components with inline types if @/ imports don't exist\n`;
        
        // Add modern React patterns
        prompt += `\nModern React Patterns:\n`;
        prompt += `- Include loading, error, and empty states for data-driven components\n`;
        prompt += `- Consider custom hooks for data fetching when appropriate\n`;
        prompt += `- Add proper error handling and graceful degradation\n`;
        prompt += `- Include callback props for user interactions when needed\n`;
        prompt += `- Consider optimistic UI updates for better user experience\n`;
        prompt += `- Add appropriate loading states for async operations\n`;
        
        // Data fetching patterns
        const hasReactQuery = Object.keys(projectMetadata.dependencies).some(dep => 
            dep.includes('react-query') || dep.includes('@tanstack/react-query')
        );
        
        if (hasReactQuery) {
            prompt += `- Use React Query/TanStack Query for data fetching with proper loading/error states\n`;
        }
        
        // State management patterns
        const stateLibraries = projectMetadata.stateManagement || [];
        if (stateLibraries.length > 0) {
            prompt += `- Available state management: ${stateLibraries.join(', ')}\n`;
        }
        
        prompt += `\nAccessibility (a11y) Requirements:\n`;
        prompt += `- Use proper heading hierarchy (h1, h2, h3, etc.)\n`;
        prompt += `- Add ARIA labels, roles, and descriptions where needed\n`;
        prompt += `- Ensure keyboard navigation support\n`;
        prompt += `- Include focus management for modals and interactive elements\n`;
        prompt += `- Use aria-busy="true" during loading states\n`;
        prompt += `- Add aria-live regions for dynamic content updates\n`;
        
        prompt += `\nUser Experience (UX) Patterns:\n`;
        prompt += `- Provide immediate visual feedback for user actions\n`;
        prompt += `- Show loading spinners or skeleton screens during data fetching\n`;
        prompt += `- Display user-friendly error messages with retry options\n`;
        prompt += `- Include empty states with helpful messaging\n`;
        prompt += `- Add confirmation dialogs for destructive actions\n`;
        prompt += `- Implement proper form validation with inline error messages\n`;
        
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
        
        // Add component-specific patterns
        const componentPatterns = this.getComponentPatterns(request);
        if (componentPatterns) {
            prompt += componentPatterns;
        }
        
        // Add codebase-specific patterns
        if (patterns) {
            prompt += this.buildCodebaseSpecificInstructions(patterns);
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
        
        // Add testing guidance
        const hasTestingLibraries = Object.keys(projectMetadata.dependencies).some(dep => 
            dep.includes('testing-library') || dep.includes('vitest') || dep.includes('jest')
        );
        
        if (hasTestingLibraries) {
            prompt += `\nTesting Considerations:\n`;
            prompt += `- Structure component to be easily testable\n`;
            prompt += `- Use data-testid attributes for complex components\n`;
            prompt += `- Separate business logic into custom hooks when possible\n`;
            prompt += `- Make async operations mockable\n`;
        }
        
        prompt += `\nCode Structure:\n`;
        prompt += `- Start with all necessary imports\n`;
        prompt += `- Define TypeScript interfaces before the component\n`;
        prompt += `- Use descriptive variable and function names\n`;
        prompt += `- Add JSDoc comments for complex props or functions\n`;
        prompt += `- Keep components focused and single-responsibility\n`;
        prompt += `- Extract reusable logic into custom hooks\n`;
        
        prompt += `\nGenerate ONLY the component code with appropriate imports. Consider the suggestions above while ensuring the component meets the specified requirements. Adapt patterns as needed for the specific use case. No explanations or markdown blocks.`;
        
        return prompt;
    }

    /**
     * Builds framework-specific system prompts
     */
    buildSystemPrompt(framework: string): string {
        const prompts = {
            'React': `You are an expert React developer who creates production-ready, accessible, and user-friendly components. 
You always include proper TypeScript interfaces, loading/error states, accessibility features, and follow modern React patterns. 
Your components are interactive, handle edge cases gracefully, and provide excellent user experience.`,
            
            'Vue': `You are an expert Vue.js developer who creates production-ready Vue 3 components using Composition API. 
You always include proper TypeScript support, loading/error states, accessibility features, and follow modern Vue patterns.`,
            
            'Next.js': `You are an expert Next.js developer who creates SSR-ready, performance-optimized React components. 
You understand Next.js patterns, proper data fetching with loading states, accessibility, and modern React development practices.`
        };

        return prompts[framework as keyof typeof prompts] || prompts['React'];
    }

    /**
     * Builds context from similar components
     */
    buildContextFromComponents(components: ComponentInfo[]): string {
        if (components.length === 0) return '';
        
        let context = '\n\nExisting similar components in this codebase:\n';
        components.slice(0, 3).forEach(comp => {
            context += `- ${comp.name}: ${comp.summary || 'No description'}\n`;
            if (comp.props && comp.props.length > 0) {
                context += `  Props: ${comp.props.slice(0, 5).join(', ')}\n`;
            }
        });
        context += '\nUse similar patterns and naming conventions from these existing components.\n';
        
        return context;
    }

    /**
     * Gets component-specific patterns based on request type
     */
    getComponentPatterns(request: string): string {
        const requestLower = request.toLowerCase();
        let patterns = '';

        // Pricing/Plans components
        if (requestLower.includes('pricing') || requestLower.includes('plan')) {
            patterns += `\nPricing Component Suggestions:\n`;
            patterns += `- Consider creating a custom hook for plan data (e.g., usePlans)\n`;
            patterns += `- Include callback props for user interactions (onSelectPlan, etc.)\n`;
            patterns += `- Include loading states for plan data fetching\n`;
            patterns += `- Handle empty states gracefully\n`;
            patterns += `- Use proper currency formatting and display\n`;
            patterns += `- Consider highlighting recommended/popular plans\n`;
            patterns += `- Ensure pricing information is clear and accessible\n`;
        }

        // Form components
        if (requestLower.includes('form') || requestLower.includes('input')) {
            patterns += `\nForm Component Patterns:\n`;
            patterns += `- Include form validation with error messages\n`;
            patterns += `- Add loading state during submission\n`;
            patterns += `- Show success/error feedback after submission\n`;
            patterns += `- Use proper form labels and ARIA attributes\n`;
            patterns += `- Implement proper focus management\n`;
            patterns += `- Add onSubmit, onCancel callback props\n`;
        }

        // List/Table components
        if (requestLower.includes('list') || requestLower.includes('table') || requestLower.includes('grid')) {
            patterns += `\nList/Table Component Patterns:\n`;
            patterns += `- Create custom hook for data fetching (e.g., useItems)\n`;
            patterns += `- Include loading skeleton/spinner\n`;
            patterns += `- Show empty state with helpful message\n`;
            patterns += `- Add error state with retry button\n`;
            patterns += `- Implement pagination or infinite scroll if applicable\n`;
            patterns += `- Add sorting and filtering capabilities\n`;
        }

        // Modal/Dialog components
        if (requestLower.includes('modal') || requestLower.includes('dialog') || requestLower.includes('popup')) {
            patterns += `\nModal/Dialog Component Patterns:\n`;
            patterns += `- Add isOpen prop and onClose callback\n`;
            patterns += `- Implement proper focus trapping\n`;
            patterns += `- Add ESC key handler to close\n`;
            patterns += `- Include backdrop click to close\n`;
            patterns += `- Use proper ARIA roles and labels\n`;
            patterns += `- Add loading state for async actions\n`;
        }

        // Navigation components
        if (requestLower.includes('nav') || requestLower.includes('menu') || requestLower.includes('sidebar')) {
            patterns += `\nNavigation Component Patterns:\n`;
            patterns += `- Use proper semantic nav elements\n`;
            patterns += `- Add active state highlighting\n`;
            patterns += `- Implement keyboard navigation\n`;
            patterns += `- Include mobile responsive behavior\n`;
            patterns += `- Add ARIA labels and roles\n`;
        }

        // User Profile components
        if (requestLower.includes('profile') || requestLower.includes('user')) {
            patterns += `\nUser Profile Component Suggestions:\n`;
            patterns += `- Consider creating a custom hook for user data (e.g., useUserProfile)\n`;
            patterns += `- Use appropriate UI components for avatars, cards, and buttons if available\n`;
            patterns += `- Include loading and error states appropriate for user data\n`;
            patterns += `- Consider user privacy and data display best practices\n`;
            patterns += `- Include proper accessibility for user information\n`;
        }

        return patterns;
    }

    /**
     * Builds adaptive codebase suggestions based on detected patterns
     */
    private buildCodebaseSpecificInstructions(patterns: CodebasePatterns): string {
        let instructions = '';

        // API patterns - suggest rather than enforce
        if (patterns.apiPatterns.baseUrls.length > 0) {
            instructions += `\nDetected API Patterns (consider following these):\n`;
            instructions += `- Project appears to use backend API(s): ${patterns.apiPatterns.baseUrls.slice(0, 2).join(', ')}\n`;
            
            if (patterns.apiPatterns.customHooks.length > 0) {
                instructions += `- Consider using similar data fetching patterns as: ${patterns.apiPatterns.customHooks.slice(0, 3).join(', ')}\n`;
            }
            
            instructions += `- If creating API calls, consider following existing authentication patterns\n`;
        }

        // UI Component patterns - flexible suggestions
        if (patterns.uiComponents.componentLibrary !== 'none') {
            instructions += `\nDetected UI Patterns (adapt as needed):\n`;
            
            if (patterns.uiComponents.componentLibrary === 'custom') {
                instructions += `- Project has custom UI components\n`;
                if (Object.keys(patterns.uiComponents.commonComponents).length > 0) {
                    instructions += `- Available components include: ${Object.keys(patterns.uiComponents.commonComponents).slice(0, 5).join(', ')}\n`;
                }
                instructions += `- Consider using existing components when appropriate\n`;
                
                if (patterns.uiComponents.importPatterns.length > 0) {
                    instructions += `- Import pattern example: ${patterns.uiComponents.importPatterns[0]}\n`;
                }
            } else {
                instructions += `- Project uses ${patterns.uiComponents.componentLibrary} component library\n`;
                instructions += `- Consider using library components when appropriate\n`;
            }
        }

        // Theme patterns - flexible theming advice
        if (patterns.themePatterns.approach !== 'none') {
            instructions += `\nDetected Styling Patterns (consider consistency):\n`;
            
            if (patterns.themePatterns.approach === 'css-variables') {
                instructions += `- Project uses CSS variables for theming\n`;
                if (patterns.themePatterns.cssVariables.length > 0) {
                    instructions += `- Example variables: ${patterns.themePatterns.cssVariables.slice(0, 3).join(', ')}\n`;
                }
                
                if (patterns.themePatterns.darkModeSupport) {
                    instructions += `- Project supports dark mode - consider theme compatibility\n`;
                }
            }
            
            if (patterns.themePatterns.colorClasses.length > 0) {
                instructions += `- Common color patterns: ${patterns.themePatterns.colorClasses.slice(0, 3).join(', ')}\n`;
            }
        }

        // Loading and Error patterns - suggest consistency
        if (patterns.loadingErrorPatterns.loadingComponents.length > 0 || 
            patterns.loadingErrorPatterns.skeletonComponents.length > 0) {
            instructions += `\nDetected Loading/Error Patterns (consider consistency):\n`;
            
            if (patterns.loadingErrorPatterns.skeletonComponents.length > 0) {
                instructions += `- Project has skeleton components: ${patterns.loadingErrorPatterns.skeletonComponents.slice(0, 2).join(', ')}\n`;
            }
            
            if (patterns.loadingErrorPatterns.loadingComponents.length > 0) {
                instructions += `- Project has loading components: ${patterns.loadingErrorPatterns.loadingComponents.slice(0, 2).join(', ')}\n`;
            }
            
            if (patterns.loadingErrorPatterns.errorComponents.length > 0) {
                instructions += `- Project has error components: ${patterns.loadingErrorPatterns.errorComponents.slice(0, 2).join(', ')}\n`;
            }
        }

        if (instructions) {
            instructions += `\nGeneral Guidance:\n`;
            instructions += `- Adapt to existing codebase patterns when reasonable\n`;
            instructions += `- Maintain consistency with project architecture\n`;
            instructions += `- Use similar naming conventions and import styles\n`;
            instructions += `- Balance following patterns with component requirements\n`;
        }

        return instructions;
    }
}