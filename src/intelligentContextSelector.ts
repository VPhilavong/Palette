import {
    IntelligentContext,
    ComponentInfo,
    CodeSnippet,
    DetectedPattern,
    DesignSystemAnalysis,
    StateManagementAnalysis,
    TypeScriptPatterns,
    ComponentCategory,
    ExampleLibrary
} from './types';

export class IntelligentContextSelector {
    
    /**
     * Select the most relevant context for a given prompt
     */
    async selectIntelligentContext(
        prompt: string,
        components: ComponentInfo[],
        exampleLibrary: ExampleLibrary,
        designSystemAnalysis: DesignSystemAnalysis,
        stateManagementAnalysis: StateManagementAnalysis,
        typeScriptAnalysis: TypeScriptPatterns
    ): Promise<IntelligentContext> {
        console.log('🧠 Selecting intelligent context for prompt:', prompt);
        
        // Analyze the prompt to understand intent
        const promptAnalysis = this.analyzePrompt(prompt);
        
        // Select relevant components
        const relevantComponents = this.selectRelevantComponents(
            components, 
            promptAnalysis,
            5
        );
        
        // Select relevant code examples
        const codeExamples = this.selectRelevantExamples(
            exampleLibrary,
            promptAnalysis,
            8
        );
        
        // Select relevant patterns
        const patternSuggestions = this.selectRelevantPatterns(
            exampleLibrary.patterns,
            promptAnalysis,
            6
        );
        
        // Generate context summary
        const contextSummary = this.generateContextSummary(
            relevantComponents,
            codeExamples,
            patternSuggestions,
            promptAnalysis
        );
        
        // Calculate confidence score
        const confidenceScore = this.calculateConfidenceScore(
            relevantComponents,
            codeExamples,
            patternSuggestions
        );
        
        return {
            relevantComponents,
            codeExamples,
            patternSuggestions,
            designSystemContext: designSystemAnalysis,
            stateManagementContext: stateManagementAnalysis,
            typeScriptContext: typeScriptAnalysis,
            contextSummary,
            confidenceScore
        };
    }
    
    /**
     * Analyze user prompt to understand intent and requirements
     */
    private analyzePrompt(prompt: string) {
        const lowercasePrompt = prompt.toLowerCase();
        
        const analysis = {
            category: this.inferComponentCategory(lowercasePrompt),
            complexity: this.inferComplexity(lowercasePrompt),
            features: this.extractFeatures(lowercasePrompt),
            stylingHints: this.extractStylingHints(lowercasePrompt),
            interactivityHints: this.extractInteractivityHints(lowercasePrompt),
            dataHints: this.extractDataHints(lowercasePrompt),
            keywords: this.extractKeywords(lowercasePrompt)
        };
        
        return analysis;
    }
    
    /**
     * Infer component category from prompt
     */
    private inferComponentCategory(prompt: string): ComponentCategory {
        const categoryKeywords: Record<ComponentCategory, string[]> = {
            'form': ['form', 'input', 'field', 'validation', 'submit', 'checkbox', 'radio', 'select'],
            'ui-primitive': ['button', 'badge', 'chip', 'tag', 'avatar', 'icon', 'divider'],
            'layout': ['layout', 'grid', 'container', 'wrapper', 'sidebar', 'header', 'footer'],
            'navigation': ['nav', 'menu', 'breadcrumb', 'tab', 'link', 'route'],
            'data-display': ['table', 'list', 'card', 'profile', 'stats', 'chart', 'data'],
            'feedback': ['alert', 'notification', 'toast', 'modal', 'dialog', 'loading', 'spinner'],
            'overlay': ['modal', 'popup', 'dropdown', 'tooltip', 'popover'],
            'page': ['page', 'view', 'screen', 'dashboard'],
            'business-logic': ['api', 'service', 'logic', 'hook', 'provider'],
            'utility': ['util', 'helper', 'common']
        };
        
        for (const [category, keywords] of Object.entries(categoryKeywords)) {
            if (keywords.some(keyword => prompt.includes(keyword))) {
                return category as ComponentCategory;
            }
        }
        
        return 'ui-primitive'; // Default
    }
    
    /**
     * Infer complexity level from prompt
     */
    private inferComplexity(prompt: string): 'simple' | 'medium' | 'complex' {
        const complexityIndicators = {
            simple: ['simple', 'basic', 'minimal', 'clean'],
            medium: ['responsive', 'interactive', 'styled', 'with'],
            complex: ['advanced', 'sophisticated', 'dynamic', 'state', 'api', 'real-time', 'dashboard']
        };
        
        for (const [level, indicators] of Object.entries(complexityIndicators)) {
            if (indicators.some(indicator => prompt.includes(indicator))) {
                return level as 'simple' | 'medium' | 'complex';
            }
        }
        
        return 'medium'; // Default
    }
    
    /**
     * Extract specific features mentioned in prompt
     */
    private extractFeatures(prompt: string): string[] {
        const features: string[] = [];
        
        const featurePatterns = [
            /loading|spinner|skeleton/g,
            /error|validation|toast/g,
            /responsive|mobile|desktop/g,
            /dark mode|theme/g,
            /animation|transition/g,
            /search|filter|sort/g,
            /pagination|infinite scroll/g,
            /drag|drop|sortable/g,
            /real-time|websocket|live/g,
            /accessibility|a11y|screen reader/g
        ];
        
        featurePatterns.forEach(pattern => {
            const matches = prompt.match(pattern);
            if (matches) {
                features.push(...matches);
            }
        });
        
        return [...new Set(features)];
    }
    
    /**
     * Extract styling hints from prompt
     */
    private extractStylingHints(prompt: string): string[] {
        const stylingHints: string[] = [];
        
        const stylePatterns = [
            /tailwind|utility classes/g,
            /styled-components|css-in-js/g,
            /material|mui/g,
            /chakra|ui library/g,
            /gradient|shadow|rounded/g,
            /color scheme|palette/g,
            /modern|minimalist|elegant/g
        ];
        
        stylePatterns.forEach(pattern => {
            const matches = prompt.match(pattern);
            if (matches) {
                stylingHints.push(...matches);
            }
        });
        
        return [...new Set(stylingHints)];
    }
    
    /**
     * Extract interactivity hints from prompt
     */
    private extractInteractivityHints(prompt: string): string[] {
        const interactivityHints: string[] = [];
        
        const interactivityPatterns = [
            /click|hover|focus/g,
            /submit|validate/g,
            /toggle|switch/g,
            /drag|drop/g,
            /keyboard|shortcut/g,
            /gesture|touch/g
        ];
        
        interactivityPatterns.forEach(pattern => {
            const matches = prompt.match(pattern);
            if (matches) {
                interactivityHints.push(...matches);
            }
        });
        
        return [...new Set(interactivityHints)];
    }
    
    /**
     * Extract data-related hints from prompt
     */
    private extractDataHints(prompt: string): string[] {
        const dataHints: string[] = [];
        
        const dataPatterns = [
            /api|fetch|async/g,
            /state|redux|zustand/g,
            /context|provider/g,
            /cache|persistence/g,
            /real-time|websocket/g
        ];
        
        dataPatterns.forEach(pattern => {
            const matches = prompt.match(pattern);
            if (matches) {
                dataHints.push(...matches);
            }
        });
        
        return [...new Set(dataHints)];
    }
    
    /**
     * Extract key terms from prompt
     */
    private extractKeywords(prompt: string): string[] {
        // Remove common words and extract meaningful terms
        const commonWords = new Set(['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'that', 'this', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can']);
        
        return prompt
            .toLowerCase()
            .split(/\s+/)
            .filter(word => word.length > 2 && !commonWords.has(word))
            .slice(0, 10); // Limit to top 10 keywords
    }
    
    /**
     * Select most relevant components based on prompt analysis
     */
    private selectRelevantComponents(
        components: ComponentInfo[],
        promptAnalysis: any,
        limit: number
    ): ComponentInfo[] {
        const scoredComponents = components.map(component => {
            let score = 0;
            
            // Category match
            if (component.category === promptAnalysis.category) {
                score += 50;
            }
            
            // Complexity match
            if (component.complexity === promptAnalysis.complexity) {
                score += 30;
            }
            
            // Keyword matches in name or description
            promptAnalysis.keywords.forEach((keyword: string) => {
                if (component.name.toLowerCase().includes(keyword)) {
                    score += 20;
                }
                if (component.description.toLowerCase().includes(keyword)) {
                    score += 10;
                }
            });
            
            // Feature matches in AST
            if (component.ast) {
                promptAnalysis.features.forEach((feature: string) => {
                    if (component.ast!.jsx.patterns.some(pattern => pattern.includes(feature))) {
                        score += 15;
                    }
                });
            }
            
            // Styling hints match
            if (component.ast?.styling) {
                promptAnalysis.stylingHints.forEach((hint: string) => {
                    if (component.ast!.styling.approach.includes(hint)) {
                        score += 10;
                    }
                });
            }
            
            return { component, score };
        });
        
        return scoredComponents
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(item => item.component);
    }
    
    /**
     * Select most relevant code examples
     */
    private selectRelevantExamples(
        exampleLibrary: ExampleLibrary,
        promptAnalysis: any,
        limit: number
    ): CodeSnippet[] {
        const allSnippets = Object.values(exampleLibrary.snippets).flat();
        
        const scoredSnippets = allSnippets.map(snippet => {
            let score = 0;
            
            // Category match
            if (snippet.category === promptAnalysis.category) {
                score += 40;
            }
            
            // Keyword matches in snippet content
            promptAnalysis.keywords.forEach((keyword: string) => {
                if (snippet.snippet.toLowerCase().includes(keyword)) {
                    score += 15;
                }
            });
            
            // Pattern matches
            snippet.patterns.forEach(pattern => {
                if (promptAnalysis.features.some((feature: string) => pattern.name.includes(feature))) {
                    score += 20;
                }
            });
            
            // Usage frequency bonus
            score += Math.min(snippet.usageFrequency * 2, 10);
            
            return { snippet, score };
        });
        
        return scoredSnippets
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(item => item.snippet);
    }
    
    /**
     * Select most relevant patterns
     */
    private selectRelevantPatterns(
        patterns: Record<string, DetectedPattern[]>,
        promptAnalysis: any,
        limit: number
    ): DetectedPattern[] {
        const allPatterns = Object.values(patterns).flat();
        
        const scoredPatterns = allPatterns.map(pattern => {
            let score = 0;
            
            // Feature-specific patterns
            promptAnalysis.features.forEach((feature: string) => {
                if (pattern.name.includes(feature) || pattern.description.includes(feature)) {
                    score += 30;
                }
            });
            
            // Best practice bonus
            if (pattern.usage.bestPractice) {
                score += 25;
            }
            
            // Frequency bonus
            score += Math.min(pattern.usage.frequency * 3, 15);
            
            // Confidence bonus
            score += pattern.confidence * 10;
            
            // Keyword matches
            promptAnalysis.keywords.forEach((keyword: string) => {
                if (pattern.description.toLowerCase().includes(keyword)) {
                    score += 10;
                }
            });
            
            return { pattern, score };
        });
        
        return scoredPatterns
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(item => item.pattern);
    }
    
    /**
     * Generate a comprehensive context summary
     */
    private generateContextSummary(
        relevantComponents: ComponentInfo[],
        codeExamples: CodeSnippet[],
        patternSuggestions: DetectedPattern[],
        promptAnalysis: any
    ): string {
        let summary = `CODEBASE CONTEXT ANALYSIS:\n\n`;
        
        // Component insights
        if (relevantComponents.length > 0) {
            summary += `RELEVANT COMPONENTS (${relevantComponents.length}):\n`;
            relevantComponents.forEach((comp, index) => {
                summary += `${index + 1}. ${comp.name} (${comp.category})\n`;
                summary += `   - Complexity: ${comp.complexity}\n`;
                summary += `   - Description: ${comp.description}\n`;
                if (comp.ast?.styling) {
                    summary += `   - Styling: ${comp.ast.styling.approach}\n`;
                }
                if (comp.ast?.hooks && comp.ast.hooks.length > 0) {
                    summary += `   - Hooks: ${comp.ast.hooks.map(h => h.name).join(', ')}\n`;
                }
                summary += `\n`;
            });
        }
        
        // Pattern insights
        if (patternSuggestions.length > 0) {
            summary += `RECOMMENDED PATTERNS (${patternSuggestions.length}):\n`;
            patternSuggestions.forEach((pattern, index) => {
                summary += `${index + 1}. ${pattern.name} (${pattern.type})\n`;
                summary += `   - ${pattern.description}\n`;
                summary += `   - Confidence: ${Math.round(pattern.confidence * 100)}%\n`;
                summary += `   - Best Practice: ${pattern.usage.bestPractice ? 'Yes' : 'No'}\n`;
                summary += `\n`;
            });
        }
        
        // Code example insights
        if (codeExamples.length > 0) {
            summary += `CODE EXAMPLES AVAILABLE: ${codeExamples.length} relevant snippets\n`;
            const categories = [...new Set(codeExamples.map(ex => ex.category))];
            summary += `Categories: ${categories.join(', ')}\n\n`;
        }
        
        // Inferred requirements
        summary += `INFERRED REQUIREMENTS:\n`;
        summary += `- Category: ${promptAnalysis.category}\n`;
        summary += `- Complexity: ${promptAnalysis.complexity}\n`;
        if (promptAnalysis.features.length > 0) {
            summary += `- Features: ${promptAnalysis.features.join(', ')}\n`;
        }
        if (promptAnalysis.stylingHints.length > 0) {
            summary += `- Styling: ${promptAnalysis.stylingHints.join(', ')}\n`;
        }
        
        return summary;
    }
    
    /**
     * Calculate confidence score for the selected context
     */
    private calculateConfidenceScore(
        relevantComponents: ComponentInfo[],
        codeExamples: CodeSnippet[],
        patternSuggestions: DetectedPattern[]
    ): number {
        let score = 0;
        let maxScore = 100;
        
        // Component relevance (40% of score)
        if (relevantComponents.length > 0) {
            score += Math.min(relevantComponents.length * 8, 40);
        }
        
        // Code examples (30% of score)
        if (codeExamples.length > 0) {
            score += Math.min(codeExamples.length * 4, 30);
        }
        
        // Pattern confidence (30% of score)
        if (patternSuggestions.length > 0) {
            const avgPatternConfidence = patternSuggestions.reduce((sum, p) => sum + p.confidence, 0) / patternSuggestions.length;
            score += avgPatternConfidence * 30;
        }
        
        return Math.min(score, maxScore) / maxScore;
    }
}