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
import { StructuredRequest } from '../extension/tools/node/codebaseAnalysisTool';

/**
 * Builds context-aware prompts for component generation
 */
export class PromptBuilder {
    /**
     * Builds a highly detailed prompt from structured NLU entities
     */
    buildStructuredComponentPrompt(
        structuredRequest: StructuredRequest,
        context: ComponentInfo[],
        projectMetadata: ProjectMetadata,
        patterns?: CodebasePatterns,
        contextInfo?: string
    ): string {
        const frameworks = projectMetadata.frameworks?.map(f => f.name).join(', ') || 'React';
        const hasTypeScript = projectMetadata.hasTypeScript;
        
        // Check if we need client directive
        const nextFramework = projectMetadata.frameworks.find(f => f.name === 'Next.js');
        const needsClient = this.structuredRequestNeedsClient(structuredRequest, nextFramework);
        
        let prompt = `Create a ${frameworks} component: ${structuredRequest.component_name}\n\n`;
        
        // Add App Router specific instructions FIRST if needed
        if (needsClient) {
            prompt += `## CRITICAL NEXT.JS APP ROUTER REQUIREMENT\n`;
            prompt += `This component requires client-side functionality (`;
            
            const reasons = [];
            if (structuredRequest.behavior?.interactions?.length && structuredRequest.behavior.interactions.length > 0) {
                reasons.push('user interactions');
            }
            if (structuredRequest.behavior?.states?.length && structuredRequest.behavior.states.length > 0) {
                reasons.push('state management');
            }
            if (structuredRequest.elements.some(e => ['button', 'form', 'input'].includes(e.type.toLowerCase()))) {
                reasons.push('interactive elements');
            }
            
            prompt += reasons.join(', ');
            prompt += `).\n\n`;
            
            prompt += `**You MUST add 'use client' as the VERY FIRST LINE of the file:**\n`;
            prompt += `\`\`\`\n`;
            prompt += `'use client'\n\n`;
            prompt += `import { useState } from 'react'\n`;
            prompt += `// ... other imports\n`;
            prompt += `\`\`\`\n\n`;
        }
        
        // Add detailed component specification based on structured entities
        prompt += `## Component Specification\n`;
        prompt += `**Type:** ${structuredRequest.component_type}\n`;
        prompt += `**Name:** ${structuredRequest.component_name}\n`;
        
        // Add element details if specified
        if (structuredRequest.elements.length > 0) {
            prompt += `**Elements to include:**\n`;
            structuredRequest.elements.forEach((element, index) => {
                prompt += `${index + 1}. ${element.type}`;
                if (element.field_name) prompt += ` (${element.field_name})`;
                if (element.attributes && element.attributes.length > 0) {
                    prompt += ` with attributes: ${element.attributes.join(', ')}`;
                }
                if (element.children && element.children.length > 0) {
                    prompt += ` containing: ${element.children.join(', ')}`;
                }
                prompt += '\n';
            });
        }
        
        // Add specific attributes and behaviors
        if (structuredRequest.attributes.length > 0) {
            prompt += `**Required attributes:** ${structuredRequest.attributes.join(', ')}\n`;
        }
        
        if (structuredRequest.behavior?.interactions && structuredRequest.behavior.interactions.length > 0) {
            prompt += `**Interactions:** ${structuredRequest.behavior.interactions.join(', ')}\n`;
        }
        
        if (structuredRequest.behavior?.states && structuredRequest.behavior.states.length > 0) {
            prompt += `**States to handle:** ${structuredRequest.behavior.states.join(', ')}\n`;
        }
        
        if (structuredRequest.behavior?.async_operations && structuredRequest.behavior.async_operations.length > 0) {
            prompt += `**Async operations:** ${structuredRequest.behavior.async_operations.join(', ')}\n`;
        }
        
        prompt += '\n';
        
        // Add styling specifications
        if (structuredRequest.styling) {
            prompt += `## Styling Requirements\n`;
            prompt += `**Approach:** ${structuredRequest.styling.approach}\n`;
            
            if (structuredRequest.styling.classes && structuredRequest.styling.classes.length > 0) {
                prompt += `**Style themes:** ${structuredRequest.styling.classes.join(', ')}\n`;
            }
            
            if (structuredRequest.styling.responsive) {
                prompt += `**Responsive:** Yes, include mobile, tablet, and desktop breakpoints\n`;
            }
            
            prompt += '\n';
        }
        
        // Add codebase-specific patterns FIRST (most important)
        if (patterns) {
            prompt += this.buildCodebaseSpecificInstructions(patterns);
            prompt += '\n';
        }
        
        // Add context from similar components
        if (contextInfo) {
            prompt += contextInfo;
        }
        
        // Add technical requirements
        prompt += `## Technical Requirements\n`;
        prompt += `- Framework: ${frameworks}\n`;
        prompt += `- Language: ${hasTypeScript ? 'TypeScript' : 'JavaScript'}\n`;
        prompt += `- Use modern functional components and hooks\n`;
        prompt += `- Define props with TypeScript \`interface\` or \`type\`; **do NOT use \`prop-types\`**\n`;
        prompt += `- **CRITICAL: Do NOT use \`React.FC\` or \`FC\`**. Instead, type props on the function directly\n`;
        prompt += `- Include accessibility attributes (ARIA) and semantic HTML\n`;
        prompt += `- Add proper error handling and edge cases\n`;
        prompt += `- **Do NOT** add \`import React from 'react'\`; modern build tools handle it automatically\n`;
        
        // Add component-specific patterns
        const componentPatterns = this.getComponentPatterns(`${structuredRequest.component_type} ${structuredRequest.component_name}`);
        if (componentPatterns) {
            prompt += componentPatterns;
        }
        
        prompt += `\n## Output Format\n`;
        prompt += `Generate ONLY the complete, functional component code with appropriate imports. `;
        prompt += `No explanations, markdown blocks, or additional text. `;
        prompt += `The component should be production-ready and follow all specified requirements.`;
        
        return prompt;
    }

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
        
        // Check if we need client directive
        const nextFramework = projectMetadata.frameworks.find(f => f.name === 'Next.js');
        const needsClient = this.needsClientDirective(request, nextFramework);
        
        let prompt = `Create a ${frameworks} component based on this request: "${request}"\n\n`;
        
        // Add App Router specific instructions FIRST if needed
        if (needsClient) {
            prompt += `**CRITICAL NEXT.JS APP ROUTER REQUIREMENT**:\n`;
            prompt += `This component will likely need client-side interactivity (hooks, event handlers, etc).\n`;
            prompt += `You MUST add 'use client' as the VERY FIRST LINE of the file, before any imports.\n`;
            prompt += `Example:\n`;
            prompt += `'use client'\n\n`;
            prompt += `import { useState } from 'react'\n`;
            prompt += `// ... other imports\n\n`;
        }
        
        // Add codebase-specific patterns FIRST (most important)
        if (patterns) {
            prompt += this.buildCodebaseSpecificInstructions(patterns);
            prompt += '\n';
        }
        
        // Router-specific patterns (critical for project compatibility)
        const routerInfo = this.getRouterInstructions(projectMetadata.frameworks);
        if (routerInfo) {
            prompt += routerInfo;
        }
        
        prompt += `Technical Requirements:\n`;
        prompt += `- Framework: ${frameworks}\n`;
        prompt += `- Language: ${hasTypeScript ? 'TypeScript' : 'JavaScript'}\n`;
        prompt += `- Available dependencies: ${Object.keys(projectMetadata.dependencies).slice(0, 10).join(', ')}\n`;
        
        if (uiLibraries) {
            prompt += `- UI Libraries: ${uiLibraries}\n`;
        }
        
        prompt += `\nComponent Requirements:\n`;
        prompt += `- Use modern functional components and hooks\n`;
        prompt += `- Define props with TypeScript \`interface\` or \`type\`; **do NOT use \`prop-types\`**\n`;
        prompt += `- Add responsive design with appropriate breakpoints\n`;
        prompt += `- Include accessibility attributes (ARIA) and semantic HTML\n`;
        prompt += `- Use semantic HTML elements (section, article, nav, main, etc.)\n`;
        prompt += `- Add hover and focus states for interactive elements\n`;
        prompt += `- DO NOT use external packages unless they are in the available dependencies list\n`;
        prompt += `- If icons are needed and no icon package is available, use text placeholders like [Icon]\n`;
        prompt += `- Create self-contained components with inline types if \`@/\` imports don’t exist\n`;
        prompt += `- **Do NOT** add \`import React from 'react'\`; Vite/ESBuild handles it automatically\n`;
        prompt += `- **CRITICAL: Do NOT use \`React.FC\` or \`FC\`**. Instead, type props on the function directly. For example: \`export default function Component(props: Props) { … }\` or \`const Component = (props: Props) => { … }\`.\n`;
        
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
        
        if (uiLibraries.includes('Tailwind CSS') || uiLibraries.includes('tailwindcss')) {
            prompt += `- Style with Tailwind CSS classes\n`;
        } else if (uiLibraries.includes('Chakra UI') || uiLibraries.includes('@chakra-ui/react')) {
            prompt += `- Use Chakra UI components for styling and layout\n`;
            prompt += `- Import components from '@chakra-ui/react'\n`;
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
You do NOT use \`React.FC\` or \`FC\` for typing components, instead typing props directly on the function.
Your components are interactive, handle edge cases gracefully, and provide excellent user experience.`,
            
            'Vue': `You are an expert Vue.js developer who creates production-ready Vue 3 components using Composition API. 
You always include proper TypeScript support, loading/error states, accessibility features, and follow modern Vue patterns.`,
            
            'Next.js': `You are an expert Next.js developer who creates SSR-ready, performance-optimized React components. 
You understand Next.js patterns, proper data fetching with loading states, accessibility, and modern React development practices.
You do NOT use \`React.FC\` or \`FC\` for typing components, instead typing props directly on the function.`
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

        // API patterns - suggest following existing approach
        if (patterns.apiPatterns.serviceImports.length > 0 || patterns.apiPatterns.sdkPatterns.length > 0 || patterns.apiPatterns.baseUrls.length > 0) {
            instructions += `\nDetected API Patterns (follow existing approach):\n`;
            
            if (patterns.apiPatterns.sdkPatterns.length > 0) {
                instructions += `- Project uses generated SDK services: ${patterns.apiPatterns.sdkPatterns.slice(0, 3).join(', ')}\n`;
                instructions += `- IMPORTANT: Use existing SDK services instead of custom fetch functions\n`;
                instructions += `- Example usage: ${patterns.apiPatterns.sdkPatterns[0]}.methodName(params)\n`;
            }
            
            if (patterns.apiPatterns.serviceImports.length > 0) {
                instructions += `- API service imports found: ${patterns.apiPatterns.serviceImports.slice(0, 2).join(', ')}\n`;
                instructions += `- Use existing service imports for API calls\n`;
            }
            
            if (patterns.apiPatterns.baseUrls.length > 0) {
                instructions += `- Project appears to use backend API(s): ${patterns.apiPatterns.baseUrls.slice(0, 2).join(', ')}\n`;
            }
            
            if (patterns.apiPatterns.customHooks.length > 0) {
                instructions += `- Project has custom hooks: ${patterns.apiPatterns.customHooks.slice(0, 3).join(', ')}\n`;
                instructions += `- Consider using existing hooks for data fetching patterns\n`;
            }
            
            instructions += `- If creating API calls, consider following existing authentication patterns\n`;
        }

        // UI Component patterns - flexible suggestions
        if (patterns.uiComponents.componentLibrary !== 'none') {
            instructions += `\nDetected UI Patterns (follow project standards):\n`;
            
            if (patterns.uiComponents.componentLibrary === 'chakra-ui') {
                instructions += `- Project uses Chakra UI components\n`;
                instructions += `- IMPORTANT: Use Chakra UI components instead of HTML elements\n`;
                instructions += `- Use Box, VStack, HStack, Text, Heading, Container, etc.\n`;
                instructions += `- Import from '@chakra-ui/react'\n`;
                if (Object.keys(patterns.uiComponents.commonComponents).length > 0) {
                    const commonComponents = Object.keys(patterns.uiComponents.commonComponents).slice(0, 5).join(', ');
                    instructions += `- Commonly used components: ${commonComponents}\n`;
                }
            } else if (patterns.uiComponents.componentLibrary === 'custom') {
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

    /**
     * Get router-specific instructions based on detected frameworks
     */
    private getRouterInstructions(frameworks: { name: string; version?: string; variant?: string }[]): string | null {
        const nextFramework = frameworks.find(f => f.name === 'Next.js');
        
        if (nextFramework) {
            if (nextFramework.variant === 'app-router') {
                return `\nRouter Instructions (Next.js App Router):\n` +
                       `- **CRITICAL**: This is a Next.js App Router project (app/ directory)\n` +
                       `- **CRITICAL**: Components are Server Components by default\n` +
                       `- **CRITICAL**: If using useState, useEffect, or any client-side hooks, you MUST add 'use client' directive at the very top of the file\n` +
                       `- **CRITICAL**: The 'use client' directive must be the FIRST line, before any imports\n` +
                       `- Use 'next/navigation' for routing: import { useRouter, useParams, useSearchParams } from 'next/navigation'\n` +
                       `- Use Link from 'next/link' for internal navigation\n` +
                       `- For metadata, export a metadata object or generateMetadata function\n` +
                       `- Server Components can be async and fetch data directly\n` +
                       `- Example with client hooks:\n` +
                       `  'use client'\n` +
                       `  \n` +
                       `  import { useState } from 'react'\n` +
                       `  // ... rest of imports\n`;
            } else if (nextFramework.variant === 'pages-router') {
                return `\nRouter Instructions (Next.js Pages Router):\n` +
                       `- This is a Next.js Pages Router project (pages/ directory)\n` +
                       `- Use 'next/router' for routing: import { useRouter } from 'next/router'\n` +
                       `- Use Link from 'next/link' for internal navigation\n` +
                       `- Use Head from 'next/head' for page metadata\n` +
                       `- Components can use hooks without any special directives\n`;
            } else {
                // Fallback for when variant is not detected
                return `\nRouter Instructions (Next.js - Unknown Router Type):\n` +
                       `- **IMPORTANT**: Could not detect if this uses App Router or Pages Router\n` +
                       `- If you see an app/ directory, assume App Router and add 'use client' for components with hooks\n` +
                       `- If you see a pages/ directory, assume Pages Router (no 'use client' needed)\n` +
                       `- When in doubt, check the project structure\n`;
            }
        }
        
        // TanStack Router
        if (frameworks.some(f => f.name === 'TanStack Router')) {
            return `\nRouter Instructions (TanStack Router):\n` +
                   `- Use TanStack Router for navigation: import { useRouter, Link } from '@tanstack/react-router'\n` +
                   `- Use Link component for internal navigation instead of anchor tags\n` +
                   `- Use useRouter() hook to access router functions like navigate()\n` +
                   `- DO NOT use Next.js router imports (next/router, next/navigation, next/head)\n` +
                   `- For route parameters, use useParams() from TanStack Router\n` +
                   `- For search params, use useSearch() from TanStack Router\n` +
                   `- Components can use hooks without any special directives\n`;
        }
        
        // React Router
        if (frameworks.some(f => f.name === 'React Router')) {
            return `\nRouter Instructions (React Router):\n` +
                   `- Use React Router for navigation: import { useNavigate, Link, useParams } from 'react-router-dom'\n` +
                   `- Use Link component for internal navigation instead of anchor tags\n` +
                   `- Use useNavigate() hook for programmatic navigation\n` +
                   `- Components can use hooks without any special directives\n`;
        }
        
        // Generic React
        if (frameworks.some(f => f.name === 'React')) {
            return `\nRouter Instructions (Generic React):\n` +
                   `- DO NOT assume any specific router is available\n` +
                   `- Use standard anchor tags for external links\n` +
                   `- Components can use hooks without any special directives\n`;
        }
        
        return null;
    }

    /**
     * Add this helper method to detect if component needs client directive
     */
    private needsClientDirective(request: string, framework: any): boolean {
        const clientIndicators = [
            'form', 'input', 'button', 'click', 'submit', 'interactive',
            'modal', 'dialog', 'dropdown', 'toggle', 'carousel', 'tabs',
            'state', 'effect', 'ref', 'context', 'reducer'
        ];
        
        const requestLower = request.toLowerCase();
        const hasClientIndicator = clientIndicators.some(indicator => requestLower.includes(indicator));
        const isAppRouter = framework?.name === 'Next.js' && framework?.variant === 'app-router';
        
        return isAppRouter && hasClientIndicator;
    }

    /**
     * Determines if a structured request requires client-side functionality
     */
    private structuredRequestNeedsClient(
        structuredRequest: StructuredRequest,
        framework: any
    ): boolean {
        if (framework?.name !== 'Next.js' || framework?.variant !== 'app-router') {
            return false; // Only matters for Next.js App Router
        }
        
        // Check behavior for client-side indicators
        const hasInteractions = structuredRequest.behavior?.interactions?.length ? structuredRequest.behavior.interactions.length > 0 : false;
        const hasStates = structuredRequest.behavior?.states?.length ? structuredRequest.behavior.states.length > 0 : false;
        const hasAsync = structuredRequest.behavior?.async_operations?.length ? structuredRequest.behavior.async_operations.length > 0 : false;
        
        // Check elements for interactive components
        const hasInteractiveElements = structuredRequest.elements.some(element => 
            ['button', 'form', 'input', 'select', 'textarea'].includes(element.type.toLowerCase())
        );
        
        // Check component type
        const interactiveTypes = ['form', 'modal', 'dialog', 'carousel', 'tabs', 'accordion'];
        const isInteractiveType = structuredRequest.component_type ? interactiveTypes.some(type => 
            structuredRequest.component_type!.toLowerCase().includes(type)
        ) : false;
        
        return hasInteractions || hasStates || hasAsync || hasInteractiveElements || isInteractiveType;
    }
}