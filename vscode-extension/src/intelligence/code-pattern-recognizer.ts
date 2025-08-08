/**
 * Code Pattern Recognizer
 * Identifies patterns in the codebase for intelligent suggestions
 */

import * as vscode from 'vscode';
import { 
    IntelligenceContext, 
    PatternMatch, 
    PatternType, 
    IntelligenceOptions,
    ComponentInfo
} from './types';

export class CodePatternRecognizer {

    /**
     * Recognize patterns in the given intelligence context
     */
    async recognizePatterns(
        context: IntelligenceContext, 
        options: IntelligenceOptions = {}
    ): Promise<PatternMatch[]> {
        try {
            console.log('🧠 Recognizing code patterns...');
            
            const patterns: PatternMatch[] = [];
            const analysisDepth = options.analysisDepth || 'medium';

            // Run pattern recognition in parallel
            const [
                componentPatterns,
                propPatterns,
                statePatterns,
                stylingPatterns,
                layoutPatterns
            ] = await Promise.all([
                this.recognizeComponentStructurePatterns(context, analysisDepth),
                this.recognizePropPatterns(context, analysisDepth),
                this.recognizeStateManagementPatterns(context, analysisDepth),
                this.recognizeStylingPatterns(context, analysisDepth),
                this.recognizeLayoutPatterns(context, analysisDepth)
            ]);

            patterns.push(...componentPatterns, ...propPatterns, ...statePatterns, ...stylingPatterns, ...layoutPatterns);

            // Sort patterns by confidence
            patterns.sort((a, b) => b.confidence - a.confidence);

            console.log(`🧠 Recognized ${patterns.length} patterns`);
            return patterns;

        } catch (error) {
            console.warn('🧠 Pattern recognition failed:', error);
            return [];
        }
    }

    /**
     * Recognize component structure patterns
     */
    private async recognizeComponentStructurePatterns(
        context: IntelligenceContext,
        depth: string
    ): Promise<PatternMatch[]> {
        const patterns: PatternMatch[] = [];
        const components = context.codebase.components;

        if (components.length === 0) return patterns;

        // Pattern: Functional components with hooks
        const functionalWithHooks = components.filter(c => 
            c.type === 'functional' && c.hooks && c.hooks.length > 0
        );

        if (functionalWithHooks.length >= 3) {
            const commonHooks = this.findCommonHooks(functionalWithHooks);
            patterns.push({
                type: 'component-structure',
                name: 'Functional Components with Hooks',
                confidence: Math.min(90, (functionalWithHooks.length / components.length) * 100),
                locations: functionalWithHooks.map(c => c.path),
                usage: {
                    frequency: functionalWithHooks.length,
                    contexts: ['functional-components'],
                    variations: commonHooks
                },
                suggestion: `Continue using functional components with ${commonHooks.slice(0, 3).join(', ')}`
            });
        }

        // Pattern: Props with TypeScript interfaces
        const componentsWithProps = components.filter(c => c.props && c.props.length > 0);
        if (componentsWithProps.length >= 2) {
            patterns.push({
                type: 'component-structure',
                name: 'TypeScript Props Interfaces',
                confidence: Math.min(85, (componentsWithProps.length / components.length) * 100),
                locations: componentsWithProps.map(c => c.path),
                usage: {
                    frequency: componentsWithProps.length,
                    contexts: ['typescript', 'props'],
                    variations: ['Props interface', 'Type definitions']
                },
                suggestion: 'Continue defining props with TypeScript interfaces for type safety'
            });
        }

        // Pattern: ForwardRef components
        const forwardRefComponents = components.filter(c => c.type === 'forwardRef');
        if (forwardRefComponents.length >= 2) {
            patterns.push({
                type: 'component-structure',
                name: 'ForwardRef Pattern',
                confidence: Math.min(80, (forwardRefComponents.length / components.length) * 100),
                locations: forwardRefComponents.map(c => c.path),
                usage: {
                    frequency: forwardRefComponents.length,
                    contexts: ['ref-forwarding', 'reusable-components'],
                    variations: ['React.forwardRef']
                },
                suggestion: 'Use forwardRef pattern for reusable components that need ref access'
            });
        }

        return patterns;
    }

    /**
     * Find common hooks across functional components
     */
    private findCommonHooks(components: ComponentInfo[]): string[] {
        const hookCounts = new Map<string, number>();
        
        components.forEach(component => {
            component.hooks?.forEach(hook => {
                hookCounts.set(hook, (hookCounts.get(hook) || 0) + 1);
            });
        });

        // Return hooks used in at least 50% of components
        const threshold = Math.ceil(components.length * 0.5);
        return Array.from(hookCounts.entries())
            .filter(([, count]) => count >= threshold)
            .map(([hook]) => hook)
            .sort();
    }

    /**
     * Recognize prop patterns
     */
    private async recognizePropPatterns(
        context: IntelligenceContext,
        depth: string
    ): Promise<PatternMatch[]> {
        const patterns: PatternMatch[] = [];
        const components = context.codebase.components.filter(c => c.props && c.props.length > 0);

        if (components.length === 0) return patterns;

        // Pattern: Common prop names
        const propNameCounts = new Map<string, number>();
        const propTypes = new Map<string, Set<string>>();

        components.forEach(component => {
            component.props?.forEach(prop => {
                propNameCounts.set(prop.name, (propNameCounts.get(prop.name) || 0) + 1);
                
                if (!propTypes.has(prop.name)) {
                    propTypes.set(prop.name, new Set());
                }
                propTypes.get(prop.name)!.add(prop.type);
            });
        });

        // Find frequently used prop names
        const commonProps = Array.from(propNameCounts.entries())
            .filter(([, count]) => count >= 3)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 5);

        if (commonProps.length > 0) {
            patterns.push({
                type: 'prop-pattern',
                name: 'Common Prop Names',
                confidence: 75,
                locations: components.map(c => c.path),
                usage: {
                    frequency: commonProps.reduce((acc, [, count]) => acc + count, 0),
                    contexts: ['component-props'],
                    variations: commonProps.map(([name]) => name)
                },
                suggestion: `Standardize common props: ${commonProps.map(([name]) => name).join(', ')}`
            });
        }

        // Pattern: Optional vs Required props
        const optionalPropCounts = new Map<boolean, number>();
        let totalProps = 0;

        components.forEach(component => {
            component.props?.forEach(prop => {
                optionalPropCounts.set(prop.required, (optionalPropCounts.get(prop.required) || 0) + 1);
                totalProps++;
            });
        });

        const requiredCount = optionalPropCounts.get(true) || 0;
        const optionalCount = optionalPropCounts.get(false) || 0;

        if (totalProps > 0) {
            const requiredRatio = requiredCount / totalProps;
            patterns.push({
                type: 'prop-pattern',
                name: 'Props Optionality Pattern',
                confidence: 70,
                locations: components.map(c => c.path),
                usage: {
                    frequency: totalProps,
                    contexts: ['prop-design'],
                    variations: [`${Math.round(requiredRatio * 100)}% required props`]
                },
                suggestion: requiredRatio > 0.7 
                    ? 'Consider making more props optional with sensible defaults'
                    : 'Good balance of required and optional props'
            });
        }

        return patterns;
    }

    /**
     * Recognize state management patterns
     */
    private async recognizeStateManagementPatterns(
        context: IntelligenceContext,
        depth: string
    ): Promise<PatternMatch[]> {
        const patterns: PatternMatch[] = [];
        const components = context.codebase.components;

        // Pattern: useState usage
        const useStateComponents = components.filter(c => 
            c.hooks?.includes('useState')
        );

        if (useStateComponents.length >= 3) {
            patterns.push({
                type: 'state-management',
                name: 'useState Pattern',
                confidence: Math.min(80, (useStateComponents.length / components.length) * 100),
                locations: useStateComponents.map(c => c.path),
                usage: {
                    frequency: useStateComponents.length,
                    contexts: ['local-state'],
                    variations: ['useState hook']
                },
                suggestion: 'Continue using useState for local component state'
            });
        }

        // Pattern: useEffect for side effects
        const useEffectComponents = components.filter(c => 
            c.hooks?.includes('useEffect')
        );

        if (useEffectComponents.length >= 3) {
            patterns.push({
                type: 'state-management',
                name: 'useEffect Side Effects',
                confidence: Math.min(75, (useEffectComponents.length / components.length) * 100),
                locations: useEffectComponents.map(c => c.path),
                usage: {
                    frequency: useEffectComponents.length,
                    contexts: ['side-effects'],
                    variations: ['useEffect hook']
                },
                suggestion: 'Good use of useEffect for side effects and lifecycle management'
            });
        }

        // Pattern: useContext usage (suggests global state)
        const useContextComponents = components.filter(c => 
            c.hooks?.includes('useContext')
        );

        if (useContextComponents.length >= 2) {
            patterns.push({
                type: 'state-management',
                name: 'Context API Usage',
                confidence: 70,
                locations: useContextComponents.map(c => c.path),
                usage: {
                    frequency: useContextComponents.length,
                    contexts: ['global-state'],
                    variations: ['useContext hook']
                },
                suggestion: 'Context API is being used for state sharing across components'
            });
        }

        return patterns;
    }

    /**
     * Recognize styling patterns
     */
    private async recognizeStylingPatterns(
        context: IntelligenceContext,
        depth: string
    ): Promise<PatternMatch[]> {
        const patterns: PatternMatch[] = [];
        const components = context.codebase.components;

        if (components.length === 0) return patterns;

        // Group components by styling approach
        const stylingGroups = new Map<string, ComponentInfo[]>();
        components.forEach(component => {
            const approach = component.stylingApproach;
            if (!stylingGroups.has(approach)) {
                stylingGroups.set(approach, []);
            }
            stylingGroups.get(approach)!.push(component);
        });

        // Identify dominant styling approach
        const dominantApproach = Array.from(stylingGroups.entries())
            .sort(([, a], [, b]) => b.length - a.length)[0];

        if (dominantApproach && dominantApproach[1].length >= 3) {
            const [approach, componentsUsingIt] = dominantApproach;
            const confidence = Math.min(90, (componentsUsingIt.length / components.length) * 100);

            patterns.push({
                type: 'styling-pattern',
                name: `${approach.charAt(0).toUpperCase() + approach.slice(1)} Styling`,
                confidence,
                locations: componentsUsingIt.map(c => c.path),
                usage: {
                    frequency: componentsUsingIt.length,
                    contexts: ['component-styling'],
                    variations: [approach]
                },
                suggestion: `Continue using ${approach} for consistent styling across components`
            });
        }

        // Tailwind-specific patterns
        if (context.designSystem.library === 'shadcn/ui' || 
            context.codebase.conventions.styling.approach === 'tailwind') {
            
            const tailwindComponents = components.filter(c => c.stylingApproach === 'tailwind');
            if (tailwindComponents.length >= 3) {
                patterns.push({
                    type: 'styling-pattern',
                    name: 'Tailwind CSS Utility Classes',
                    confidence: 85,
                    locations: tailwindComponents.map(c => c.path),
                    usage: {
                        frequency: tailwindComponents.length,
                        contexts: ['utility-first-css'],
                        variations: ['Tailwind utility classes']
                    },
                    suggestion: 'Leverage Tailwind CSS utilities for consistent and maintainable styling'
                });
            }
        }

        return patterns;
    }

    /**
     * Recognize layout patterns
     */
    private async recognizeLayoutPatterns(
        context: IntelligenceContext,
        depth: string
    ): Promise<PatternMatch[]> {
        const patterns: PatternMatch[] = [];

        // Check for common layout components based on naming
        const layoutComponents = context.codebase.components.filter(c =>
            /layout|header|footer|sidebar|nav|navigation|container|wrapper/i.test(c.name)
        );

        if (layoutComponents.length >= 3) {
            patterns.push({
                type: 'layout-pattern',
                name: 'Layout Components',
                confidence: 75,
                locations: layoutComponents.map(c => c.path),
                usage: {
                    frequency: layoutComponents.length,
                    contexts: ['page-structure'],
                    variations: layoutComponents.map(c => c.name)
                },
                suggestion: 'Good separation of layout concerns into dedicated components'
            });
        }

        // Check for responsive design patterns
        const hasResponsiveDesign = context.designSystem.tokens.breakpoints && 
            Object.keys(context.designSystem.tokens.breakpoints).length > 0;

        if (hasResponsiveDesign) {
            patterns.push({
                type: 'layout-pattern',
                name: 'Responsive Design',
                confidence: 80,
                locations: ['design-system'],
                usage: {
                    frequency: Object.keys(context.designSystem.tokens.breakpoints).length,
                    contexts: ['responsive-design'],
                    variations: Object.keys(context.designSystem.tokens.breakpoints)
                },
                suggestion: 'Continue using responsive breakpoints for mobile-first design'
            });
        }

        return patterns;
    }

    /**
     * Analyze specific pattern types for deeper insights
     */
    async analyzeSpecificPattern(
        context: IntelligenceContext,
        patternType: PatternType
    ): Promise<PatternMatch[]> {
        switch (patternType) {
            case 'component-structure':
                return this.recognizeComponentStructurePatterns(context, 'deep');
            case 'prop-pattern':
                return this.recognizePropPatterns(context, 'deep');
            case 'state-management':
                return this.recognizeStateManagementPatterns(context, 'deep');
            case 'styling-pattern':
                return this.recognizeStylingPatterns(context, 'deep');
            case 'layout-pattern':
                return this.recognizeLayoutPatterns(context, 'deep');
            default:
                return [];
        }
    }

    /**
     * Get pattern suggestions based on recognized patterns
     */
    getPatternSuggestions(patterns: PatternMatch[]): string[] {
        const suggestions: string[] = [];
        
        // High-confidence patterns get priority suggestions
        const highConfidencePatterns = patterns.filter(p => p.confidence >= 80);
        
        highConfidencePatterns.forEach(pattern => {
            if (pattern.suggestion) {
                suggestions.push(pattern.suggestion);
            }
        });

        // Add general suggestions based on pattern types
        const patternTypes = new Set(patterns.map(p => p.type));
        
        if (patternTypes.has('component-structure') && !patternTypes.has('state-management')) {
            suggestions.push('Consider adding state management patterns for better component organization');
        }
        
        if (patternTypes.has('styling-pattern') && patterns.some(p => p.name.includes('Tailwind'))) {
            suggestions.push('Consider using a component library like shadcn/ui with Tailwind CSS');
        }

        return suggestions;
    }

    /**
     * Calculate pattern similarity score between two components
     */
    calculatePatternSimilarity(component1: ComponentInfo, component2: ComponentInfo): number {
        let score = 0;
        let maxScore = 0;

        // Type similarity (20 points)
        maxScore += 20;
        if (component1.type === component2.type) score += 20;

        // Styling approach similarity (15 points)
        maxScore += 15;
        if (component1.stylingApproach === component2.stylingApproach) score += 15;

        // Hook usage similarity (25 points)
        maxScore += 25;
        const commonHooks = component1.hooks?.filter(h => component2.hooks?.includes(h)) || [];
        const totalUniqueHooks = new Set([...(component1.hooks || []), ...(component2.hooks || [])]).size;
        if (totalUniqueHooks > 0) {
            score += Math.round((commonHooks.length / totalUniqueHooks) * 25);
        }

        // Complexity similarity (10 points)
        maxScore += 10;
        if (component1.complexity === component2.complexity) score += 10;

        // Dependency similarity (15 points)
        maxScore += 15;
        const commonDeps = component1.dependencies.filter(d => component2.dependencies.includes(d));
        const totalUniqueDeps = new Set([...component1.dependencies, ...component2.dependencies]).size;
        if (totalUniqueDeps > 0) {
            score += Math.round((commonDeps.length / totalUniqueDeps) * 15);
        }

        // Props count similarity (15 points)
        maxScore += 15;
        const props1Count = component1.props?.length || 0;
        const props2Count = component2.props?.length || 0;
        if (props1Count > 0 || props2Count > 0) {
            const propsRatio = Math.min(props1Count, props2Count) / Math.max(props1Count, props2Count);
            score += Math.round(propsRatio * 15);
        }

        return Math.round((score / maxScore) * 100);
    }

    /**
     * Find components with similar patterns
     */
    findSimilarComponents(
        targetComponent: ComponentInfo, 
        allComponents: ComponentInfo[], 
        minSimilarity: number = 70
    ): Array<{ component: ComponentInfo; similarity: number }> {
        return allComponents
            .filter(c => c.name !== targetComponent.name)
            .map(component => ({
                component,
                similarity: this.calculatePatternSimilarity(targetComponent, component)
            }))
            .filter(({ similarity }) => similarity >= minSimilarity)
            .sort((a, b) => b.similarity - a.similarity);
    }
}