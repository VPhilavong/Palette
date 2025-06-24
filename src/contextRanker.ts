import * as vscode from 'vscode';
import {
    ComponentInfo,
    ComponentAST,
    RelevantComponent,
    RelevanceReason,
    SimilarityMetrics,
    GenerationContext,
    ComponentCategory
} from './types';

export class ContextRanker {
    
    /**
     * Rank components by relevance to the generation prompt
     */
    rankComponentsByRelevance(
        prompt: string,
        components: ComponentInfo[],
        context?: Partial<GenerationContext>
    ): RelevantComponent[] {
        const relevantComponents: RelevantComponent[] = [];
        
        for (const component of components) {
            const relevanceData = this.calculateRelevance(prompt, component, context);
            
            if (relevanceData.relevanceScore > 0.3) { // Only include reasonably relevant components
                relevantComponents.push({
                    component,
                    ...relevanceData
                });
            }
        }
        
        // Sort by relevance score (highest first)
        return relevantComponents.sort((a, b) => b.relevanceScore - a.relevanceScore);
    }

    /**
     * Calculate detailed relevance metrics for a component
     */
    private calculateRelevance(
        prompt: string,
        component: ComponentInfo,
        context?: Partial<GenerationContext>
    ): {
        relevanceScore: number;
        reasons: RelevanceReason[];
        similarity: SimilarityMetrics;
    } {
        const reasons: RelevanceReason[] = [];
        const similarity = this.calculateSimilarity(prompt, component);
        
        // Semantic similarity (based on names and descriptions)
        const semanticScore = this.calculateSemanticSimilarity(prompt, component);
        if (semanticScore > 0.5) {
            reasons.push({
                type: 'naming',
                confidence: semanticScore,
                description: `Component name/description semantically similar to prompt`
            });
        }
        
        // Pattern matching
        const patternScore = this.calculatePatternSimilarity(prompt, component);
        if (patternScore > 0.4) {
            reasons.push({
                type: 'pattern-match',
                confidence: patternScore,
                description: `Similar patterns detected (${this.getMatchingPatterns(prompt, component).join(', ')})`
            });
        }
        
        // Structural similarity
        if (component.ast) {
            const structuralScore = this.calculateStructuralSimilarity(prompt, component.ast);
            if (structuralScore > 0.4) {
                reasons.push({
                    type: 'structure',
                    confidence: structuralScore,
                    description: `Similar component structure and complexity`
                });
            }
        }
        
        // Styling approach similarity
        const stylingScore = this.calculateStylingSimilarity(prompt, component, context);
        if (stylingScore > 0.3) {
            reasons.push({
                type: 'styling',
                confidence: stylingScore,
                description: `Compatible styling approach`
            });
        }
        
        // Dependency relevance
        if (component.dependencies) {
            const depScore = this.calculateDependencyRelevance(prompt, component.dependencies);
            if (depScore > 0.3) {
                reasons.push({
                    type: 'dependency',
                    confidence: depScore,
                    description: `Uses relevant dependencies or libraries`
                });
            }
        }
        
        // Calculate overall relevance score
        const relevanceScore = this.calculateOverallRelevance(similarity, reasons);
        
        return {
            relevanceScore,
            reasons,
            similarity
        };
    }

    /**
     * Calculate multi-dimensional similarity metrics
     */
    private calculateSimilarity(prompt: string, component: ComponentInfo): SimilarityMetrics {
        const structural = component.ast ? 
            this.calculateStructuralSimilarity(prompt, component.ast) : 0;
        const semantic = this.calculateSemanticSimilarity(prompt, component);
        const stylistic = this.calculatePatternSimilarity(prompt, component);
        const functional = this.calculateFunctionalSimilarity(prompt, component);
        
        const overall = (structural * 0.25 + semantic * 0.35 + stylistic * 0.25 + functional * 0.15);
        
        return {
            structural,
            semantic,
            stylistic,
            functional,
            overall
        };
    }

    /**
     * Calculate semantic similarity based on NLP-like techniques
     */
    private calculateSemanticSimilarity(prompt: string, component: ComponentInfo): number {
        const promptTokens = this.tokenize(prompt.toLowerCase());
        const componentTokens = this.tokenize(`${component.name} ${component.description}`.toLowerCase());
        
        // Calculate Jaccard similarity
        const intersection = promptTokens.filter(token => componentTokens.includes(token));
        const union = [...new Set([...promptTokens, ...componentTokens])];
        
        const jaccardSimilarity = intersection.length / union.length;
        
        // Boost score for exact keyword matches
        const exactMatches = this.findExactMatches(promptTokens, componentTokens);
        const exactMatchBoost = exactMatches.length * 0.2;
        
        // Boost score for component category matches
        const categoryBoost = this.calculateCategoryRelevance(prompt, component.category);
        
        return Math.min(1.0, jaccardSimilarity + exactMatchBoost + categoryBoost);
    }

    /**
     * Calculate structural similarity based on AST analysis
     */
    private calculateStructuralSimilarity(prompt: string, ast: ComponentAST): number {
        let score = 0;
        
        // Complexity-based scoring
        const promptComplexity = this.estimatePromptComplexity(prompt);
        const componentComplexity = this.normalizeComplexity(ast.complexity);
        const complexityDiff = Math.abs(promptComplexity - componentComplexity);
        score += Math.max(0, 1 - complexityDiff); // 0.25 weight
        
        // Hook usage similarity
        const expectedHooks = this.predictRequiredHooks(prompt);
        const actualHooks = ast.hooks.map(h => h.name);
        const hookSimilarity = this.calculateArraySimilarity(expectedHooks, actualHooks);
        score += hookSimilarity * 0.3;
        
        // JSX patterns
        const expectedPatterns = this.predictJSXPatterns(prompt);
        const actualPatterns = ast.jsx.patterns;
        const patternSimilarity = this.calculateArraySimilarity(expectedPatterns, actualPatterns);
        score += patternSimilarity * 0.25;
        
        // Accessibility consideration
        if (prompt.includes('accessible') || prompt.includes('a11y')) {
            score += ast.jsx.accessibility.score > 70 ? 0.2 : 0;
        }
        
        return Math.min(1.0, score);
    }

    /**
     * Calculate pattern-based similarity
     */
    private calculatePatternSimilarity(prompt: string, component: ComponentInfo): number {
        const matchingPatterns = this.getMatchingPatterns(prompt, component);
        const totalPossiblePatterns = this.getPossiblePatterns(prompt).length;
        
        if (totalPossiblePatterns === 0) return 0;
        
        return matchingPatterns.length / totalPossiblePatterns;
    }

    /**
     * Calculate functional similarity (what the component does)
     */
    private calculateFunctionalSimilarity(prompt: string, component: ComponentInfo): number {
        let score = 0;
        
        // UI element type matching
        const promptUIElements = this.extractUIElements(prompt);
        const componentUIElements = this.extractUIElementsFromComponent(component);
        
        if (promptUIElements.length > 0) {
            const overlap = promptUIElements.filter(el => componentUIElements.includes(el));
            score += (overlap.length / promptUIElements.length) * 0.5;
        }
        
        // Interaction pattern matching
        const promptInteractions = this.extractInteractionPatterns(prompt);
        const componentInteractions = component.ast?.jsx.interactivity.eventHandlers || [];
        
        if (promptInteractions.length > 0) {
            const interactionScore = this.calculateInteractionSimilarity(promptInteractions, componentInteractions);
            score += interactionScore * 0.3;
        }
        
        // State management needs
        const promptStateNeeds = this.analyzeStateNeeds(prompt);
        const componentStateComplexity = component.ast?.jsx.interactivity.stateManagement || 'none';
        
        if (this.stateNeedsMatch(promptStateNeeds, componentStateComplexity)) {
            score += 0.2;
        }
        
        return Math.min(1.0, score);
    }

    /**
     * Calculate styling approach compatibility
     */
    private calculateStylingSimilarity(
        prompt: string, 
        component: ComponentInfo, 
        context?: Partial<GenerationContext>
    ): number {
        let score = 0;
        
        // Check if styling approach matches workspace
        const workspaceStyling = context?.workspaceInfo?.styling;
        const componentStyling = component.ast?.styling;
        
        if (workspaceStyling && componentStyling) {
            if (workspaceStyling.hasTailwind && componentStyling.approach.includes('tailwind')) {
                score += 0.4;
            }
            if (workspaceStyling.hasStyledComponents && componentStyling.approach.includes('styled')) {
                score += 0.4;
            }
            if (workspaceStyling.hasCSSModules && componentStyling.approach.includes('css')) {
                score += 0.4;
            }
        }
        
        // Check for responsive requirements
        if (prompt.includes('responsive') && componentStyling?.responsive) {
            score += 0.3;
        }
        
        // Check for animation requirements
        if ((prompt.includes('animation') || prompt.includes('transition')) && componentStyling?.animations) {
            score += 0.3;
        }
        
        return Math.min(1.0, score);
    }

    /**
     * Calculate dependency relevance
     */
    private calculateDependencyRelevance(prompt: string, dependencies: string[]): number {
        const relevantLibraries = this.extractRelevantLibraries(prompt);
        const overlap = dependencies.filter(dep => 
            relevantLibraries.some(lib => dep.includes(lib))
        );
        
        return relevantLibraries.length > 0 ? overlap.length / relevantLibraries.length : 0;
    }

    /**
     * Calculate overall relevance score from individual metrics
     */
    private calculateOverallRelevance(similarity: SimilarityMetrics, reasons: RelevanceReason[]): number {
        // Base score from similarity metrics
        let score = similarity.overall;
        
        // Boost from confidence in reasons
        const reasonBoost = reasons.reduce((sum, reason) => sum + reason.confidence * 0.1, 0);
        score += reasonBoost;
        
        // Boost for multiple strong reasons
        const strongReasons = reasons.filter(r => r.confidence > 0.7);
        if (strongReasons.length > 2) {
            score += 0.15;
        }
        
        return Math.min(1.0, score);
    }

    // Utility methods for pattern detection and analysis

    private tokenize(text: string): string[] {
        return text
            .toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(token => token.length > 2)
            .filter(token => !['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'].includes(token));
    }

    private findExactMatches(tokens1: string[], tokens2: string[]): string[] {
        return tokens1.filter(token => tokens2.includes(token));
    }

    private calculateCategoryRelevance(prompt: string, category?: ComponentCategory): number {
        if (!category) return 0;
        
        const categoryKeywords: Record<ComponentCategory, string[]> = {
            'layout': ['layout', 'container', 'grid', 'flex', 'wrapper'],
            'ui-primitive': ['button', 'input', 'text', 'icon', 'badge'],
            'form': ['form', 'input', 'select', 'textarea', 'validation'],
            'data-display': ['table', 'list', 'card', 'grid', 'chart'],
            'navigation': ['nav', 'menu', 'breadcrumb', 'tabs', 'link'],
            'feedback': ['modal', 'alert', 'toast', 'notification', 'spinner'],
            'overlay': ['modal', 'dropdown', 'tooltip', 'popover'],
            'business-logic': ['dashboard', 'workflow', 'complex'],
            'page': ['page', 'view', 'screen', 'route'],
            'utility': ['util', 'helper', 'common']
        };
        
        const keywords = categoryKeywords[category] || [];
        const promptLower = prompt.toLowerCase();
        
        return keywords.some(keyword => promptLower.includes(keyword)) ? 0.3 : 0;
    }

    private estimatePromptComplexity(prompt: string): number {
        let complexity = 0.1; // Base complexity
        
        // Add complexity for specific requirements
        if (prompt.includes('state') || prompt.includes('interactive')) complexity += 0.3;
        if (prompt.includes('animation') || prompt.includes('transition')) complexity += 0.2;
        if (prompt.includes('form') || prompt.includes('validation')) complexity += 0.3;
        if (prompt.includes('responsive')) complexity += 0.2;
        if (prompt.includes('accessible') || prompt.includes('a11y')) complexity += 0.2;
        if (prompt.includes('dynamic') || prompt.includes('configurable')) complexity += 0.3;
        
        // Add complexity based on number of features mentioned
        const features = prompt.split(/[,;]/).length;
        complexity += Math.min(features * 0.1, 0.4);
        
        return Math.min(1.0, complexity);
    }

    private normalizeComplexity(complexity: ComponentComplexityMetrics): number {
        // Normalize complexity metrics to 0-1 scale
        const cyclomaticNorm = Math.min(complexity.cyclomaticComplexity / 20, 1);
        const cognitiveNorm = Math.min(complexity.cognitiveComplexity / 30, 1);
        const locNorm = Math.min(complexity.linesOfCode / 200, 1);
        const depthNorm = Math.min(complexity.depth / 10, 1);
        
        return (cyclomaticNorm + cognitiveNorm + locNorm + depthNorm) / 4;
    }

    private predictRequiredHooks(prompt: string): string[] {
        const hooks: string[] = [];
        
        if (prompt.includes('state') || prompt.includes('interactive') || prompt.includes('toggle')) {
            hooks.push('useState');
        }
        if (prompt.includes('fetch') || prompt.includes('api') || prompt.includes('data')) {
            hooks.push('useEffect');
        }
        if (prompt.includes('form') || prompt.includes('input')) {
            hooks.push('useState', 'useCallback');
        }
        if (prompt.includes('optimize') || prompt.includes('performance')) {
            hooks.push('useMemo', 'useCallback');
        }
        if (prompt.includes('ref') || prompt.includes('focus')) {
            hooks.push('useRef');
        }
        
        return [...new Set(hooks)];
    }

    private predictJSXPatterns(prompt: string): string[] {
        const patterns: string[] = [];
        
        if (prompt.includes('list') || prompt.includes('array') || prompt.includes('multiple')) {
            patterns.push('list-rendering');
        }
        if (prompt.includes('conditional') || prompt.includes('if') || prompt.includes('show/hide')) {
            patterns.push('conditional-rendering');
        }
        if (prompt.includes('form') || prompt.includes('input')) {
            patterns.push('form-handling');
        }
        
        return patterns;
    }

    private calculateArraySimilarity(arr1: string[], arr2: string[]): number {
        if (arr1.length === 0 && arr2.length === 0) return 1;
        if (arr1.length === 0 || arr2.length === 0) return 0;
        
        const intersection = arr1.filter(item => arr2.includes(item));
        const union = [...new Set([...arr1, ...arr2])];
        
        return intersection.length / union.length;
    }

    private getMatchingPatterns(prompt: string, component: ComponentInfo): string[] {
        const promptPatterns = this.extractPatternsFromPrompt(prompt);
        const componentPatterns = component.ast?.jsx.patterns || [];
        
        return promptPatterns.filter(pattern => componentPatterns.includes(pattern));
    }

    private getPossiblePatterns(prompt: string): string[] {
        return this.extractPatternsFromPrompt(prompt);
    }

    private extractPatternsFromPrompt(prompt: string): string[] {
        const patterns: string[] = [];
        const promptLower = prompt.toLowerCase();
        
        if (promptLower.includes('list') || promptLower.includes('array')) patterns.push('list-rendering');
        if (promptLower.includes('conditional') || promptLower.includes('toggle')) patterns.push('conditional-rendering');
        if (promptLower.includes('form') || promptLower.includes('input')) patterns.push('form-handling');
        if (promptLower.includes('responsive')) patterns.push('responsive-design');
        if (promptLower.includes('animation') || promptLower.includes('transition')) patterns.push('animations');
        
        return patterns;
    }

    private extractUIElements(prompt: string): string[] {
        const elements: string[] = [];
        const promptLower = prompt.toLowerCase();
        
        const uiElements = ['button', 'input', 'select', 'textarea', 'modal', 'card', 'table', 'list', 'nav', 'menu'];
        
        uiElements.forEach(element => {
            if (promptLower.includes(element)) {
                elements.push(element);
            }
        });
        
        return elements;
    }

    private extractUIElementsFromComponent(component: ComponentInfo): string[] {
        // Extract UI elements from component name and description
        const text = `${component.name} ${component.description}`.toLowerCase();
        const elements: string[] = [];
        
        const uiElements = ['button', 'input', 'select', 'textarea', 'modal', 'card', 'table', 'list', 'nav', 'menu'];
        
        uiElements.forEach(element => {
            if (text.includes(element)) {
                elements.push(element);
            }
        });
        
        return elements;
    }

    private extractInteractionPatterns(prompt: string): string[] {
        const interactions: string[] = [];
        const promptLower = prompt.toLowerCase();
        
        if (promptLower.includes('click')) interactions.push('onClick');
        if (promptLower.includes('hover')) interactions.push('onMouseEnter', 'onMouseLeave');
        if (promptLower.includes('focus')) interactions.push('onFocus', 'onBlur');
        if (promptLower.includes('submit')) interactions.push('onSubmit');
        if (promptLower.includes('change')) interactions.push('onChange');
        if (promptLower.includes('key')) interactions.push('onKeyDown');
        
        return interactions;
    }

    private calculateInteractionSimilarity(expected: string[], actual: string[]): number {
        if (expected.length === 0) return 1;
        
        const matches = expected.filter(interaction => actual.includes(interaction));
        return matches.length / expected.length;
    }

    private analyzeStateNeeds(prompt: string): 'none' | 'simple' | 'complex' {
        const promptLower = prompt.toLowerCase();
        
        if (promptLower.includes('complex') || promptLower.includes('multiple states') || promptLower.includes('workflow')) {
            return 'complex';
        }
        if (promptLower.includes('state') || promptLower.includes('interactive') || promptLower.includes('toggle')) {
            return 'simple';
        }
        return 'none';
    }

    private stateNeedsMatch(needs: 'none' | 'simple' | 'complex', actual: 'none' | 'simple' | 'complex'): boolean {
        if (needs === actual) return true;
        if (needs === 'simple' && actual === 'complex') return true; // Complex can handle simple needs
        return false;
    }

    private extractRelevantLibraries(prompt: string): string[] {
        const libraries: string[] = [];
        const promptLower = prompt.toLowerCase();
        
        if (promptLower.includes('animation') || promptLower.includes('motion')) {
            libraries.push('framer-motion', 'react-spring');
        }
        if (promptLower.includes('form') || promptLower.includes('validation')) {
            libraries.push('react-hook-form', 'formik', 'yup');
        }
        if (promptLower.includes('icon')) {
            libraries.push('react-icons', 'lucide');
        }
        if (promptLower.includes('date') || promptLower.includes('calendar')) {
            libraries.push('date-fns', 'moment');
        }
        
        return libraries;
    }

    /**
     * Get the top N most relevant components for context
     */
    getTopRelevantComponents(
        prompt: string,
        components: ComponentInfo[],
        maxComponents: number = 5,
        context?: Partial<GenerationContext>
    ): RelevantComponent[] {
        const rankedComponents = this.rankComponentsByRelevance(prompt, components, context);
        return rankedComponents.slice(0, maxComponents);
    }

    /**
     * Generate context summary for AI prompt
     */
    generateContextSummary(relevantComponents: RelevantComponent[]): string {
        if (relevantComponents.length === 0) {
            return "No relevant components found in codebase.";
        }

        let summary = "RELEVANT EXISTING COMPONENTS:\n\n";
        
        relevantComponents.forEach((rc, index) => {
            const { component, relevanceScore, reasons } = rc;
            
            summary += `${index + 1}. ${component.name} (Relevance: ${Math.round(relevanceScore * 100)}%)\n`;
            summary += `   Path: ${component.path}\n`;
            summary += `   Description: ${component.description}\n`;
            
            if (component.ast) {
                summary += `   Structure: ${component.ast.type} component with ${component.ast.hooks.length} hooks\n`;
                if (component.ast.props.length > 0) {
                    summary += `   Props: ${component.ast.props.map(p => `${p.name}${p.optional ? '?' : ''}: ${p.type}`).join(', ')}\n`;
                }
                if (component.ast.jsx.patterns.length > 0) {
                    summary += `   Patterns: ${component.ast.jsx.patterns.join(', ')}\n`;
                }
                if (component.ast.styling.approach) {
                    summary += `   Styling: ${component.ast.styling.approach}\n`;
                }
            }
            
            const topReasons = reasons.slice(0, 2);
            if (topReasons.length > 0) {
                summary += `   Why relevant: ${topReasons.map(r => r.description).join('; ')}\n`;
            }
            
            summary += "\n";
        });
        
        summary += "Use these components as inspiration for similar patterns, styling approaches, and architectural decisions.\n";
        
        return summary;
    }
}

// Type import for complexity metrics
import { ComplexityMetrics as ComponentComplexityMetrics } from './types';