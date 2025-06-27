import { ComponentInfo, ProjectMetadata } from '../types';

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
        projectMetadata: ProjectMetadata
    ): string {
        // TODO: Implement intelligent prompt building - Phase 5
        return `Generate a component based on: ${request}`;
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