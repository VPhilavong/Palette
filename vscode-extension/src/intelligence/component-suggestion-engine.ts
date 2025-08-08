/**
 * Component Suggestion Engine
 * Generates intelligent suggestions for component creation and reuse
 */

import { 
    IntelligenceContext, 
    ComponentSuggestion, 
    SuggestionType,
    IntelligenceOptions,
    ComponentInfo,
    PatternMatch
} from './types';

export class ComponentSuggestionEngine {

    /**
     * Generate intelligent suggestions based on context
     */
    async generateSuggestions(
        context: IntelligenceContext, 
        options: IntelligenceOptions = {}
    ): Promise<ComponentSuggestion[]> {
        try {
            console.log('🧠 Generating component suggestions...');
            
            const suggestions: ComponentSuggestion[] = [];
            
            // Run different suggestion strategies in parallel
            const [
                reuseSuggestions,
                composeSuggestions,
                extendSuggestions,
                generateSuggestions,
                patternSuggestions
            ] = await Promise.all([
                this.generateReuseSuggestions(context),
                this.generateComposeSuggestions(context),
                this.generateExtendSuggestions(context),
                this.generateNewComponentSuggestions(context),
                this.generatePatternBasedSuggestions(context)
            ]);

            suggestions.push(
                ...reuseSuggestions,
                ...composeSuggestions,
                ...extendSuggestions,
                ...generateSuggestions,
                ...patternSuggestions
            );

            // Sort by priority and confidence
            suggestions.sort((a, b) => {
                const priorityOrder = { high: 3, medium: 2, low: 1 };
                const aPriorityValue = priorityOrder[a.priority];
                const bPriorityValue = priorityOrder[b.priority];
                
                if (aPriorityValue !== bPriorityValue) {
                    return bPriorityValue - aPriorityValue;
                }
                
                return b.confidence - a.confidence;
            });

            // Limit suggestions based on options
            const maxSuggestions = options.analysisDepth === 'shallow' ? 5 : 
                                 options.analysisDepth === 'deep' ? 15 : 10;
            
            const finalSuggestions = suggestions.slice(0, maxSuggestions);
            
            console.log(`🧠 Generated ${finalSuggestions.length} suggestions`);
            return finalSuggestions;

        } catch (error) {
            console.warn('🧠 Suggestion generation failed:', error);
            return [];
        }
    }

    /**
     * Generate suggestions for reusing existing components
     */
    private async generateReuseSuggestions(context: IntelligenceContext): Promise<ComponentSuggestion[]> {
        const suggestions: ComponentSuggestion[] = [];
        const components = context.codebase.components;

        if (components.length === 0) return suggestions;

        // Identify highly reusable components
        const reusableComponents = components.filter(c => {
            // Components with generic names and props are more reusable
            const hasGenericName = /button|input|card|modal|form|list|item|container|wrapper/i.test(c.name);
            const hasProps = c.props && c.props.length > 0;
            const isSimpleToMedium = c.complexity !== 'complex';
            
            return hasGenericName && hasProps && isSimpleToMedium;
        });

        reusableComponents.forEach(component => {
            suggestions.push({
                type: 'reuse-existing',
                name: `Reuse ${component.name}`,
                description: `Leverage existing ${component.name} component`,
                rationale: `${component.name} is well-structured with ${component.props?.length || 0} props and follows established patterns`,
                confidence: this.calculateReuseConfidence(component),
                priority: 'high',
                implementation: {
                    strategy: 'reuse',
                    baseComponents: [component.name],
                    requiredProps: component.props,
                    suggestedStructure: this.generateReuseStructure(component),
                    dependencies: component.dependencies
                }
            });
        });

        // Suggest combinations of simple components
        const simpleComponents = components.filter(c => c.complexity === 'simple');
        if (simpleComponents.length >= 2) {
            suggestions.push({
                type: 'reuse-existing',
                name: 'Combine Simple Components',
                description: 'Combine existing simple components for complex UI patterns',
                rationale: `You have ${simpleComponents.length} simple components that can be composed together`,
                confidence: 75,
                priority: 'medium',
                implementation: {
                    strategy: 'compose',
                    baseComponents: simpleComponents.slice(0, 3).map(c => c.name),
                    suggestedStructure: 'Compose components in a container with proper prop passing'
                }
            });
        }

        return suggestions;
    }

    /**
     * Generate suggestions for composing multiple components
     */
    private async generateComposeSuggestions(context: IntelligenceContext): Promise<ComponentSuggestion[]> {
        const suggestions: ComponentSuggestion[] = [];
        const components = context.codebase.components;

        // Look for complementary component patterns
        const componentsByType = this.groupComponentsByType(components);

        // Suggest form compositions
        if (componentsByType.input && componentsByType.button) {
            suggestions.push({
                type: 'compose-multiple',
                name: 'Form Component Composition',
                description: 'Create forms by composing input and button components',
                rationale: 'You have input and button components that work well together',
                confidence: 80,
                priority: 'high',
                implementation: {
                    strategy: 'compose',
                    baseComponents: ['Input', 'Button'],
                    suggestedStructure: this.generateFormCompositionStructure(),
                    requiredProps: [
                        { name: 'onSubmit', type: '() => void', required: true },
                        { name: 'fields', type: 'FormField[]', required: true }
                    ]
                }
            });
        }

        // Suggest layout compositions
        const layoutComponents = components.filter(c => 
            /header|footer|sidebar|navigation|layout/i.test(c.name)
        );

        if (layoutComponents.length >= 2) {
            suggestions.push({
                type: 'compose-multiple',
                name: 'Layout Component Composition',
                description: 'Compose layout components for page structures',
                rationale: `Found ${layoutComponents.length} layout components that can work together`,
                confidence: 75,
                priority: 'medium',
                implementation: {
                    strategy: 'compose',
                    baseComponents: layoutComponents.map(c => c.name),
                    suggestedStructure: 'Create a main layout that composes header, content area, and footer'
                }
            });
        }

        // Suggest list and item compositions
        if (componentsByType.list && componentsByType.item) {
            suggestions.push({
                type: 'compose-multiple',
                name: 'List-Item Composition',
                description: 'Compose list and item components for data display',
                rationale: 'List and item components can be composed for dynamic data rendering',
                confidence: 85,
                priority: 'high',
                implementation: {
                    strategy: 'compose',
                    baseComponents: ['List', 'ListItem'],
                    suggestedStructure: 'List component renders array of items using ListItem'
                }
            });
        }

        return suggestions;
    }

    /**
     * Generate suggestions for extending existing components
     */
    private async generateExtendSuggestions(context: IntelligenceContext): Promise<ComponentSuggestion[]> {
        const suggestions: ComponentSuggestion[] = [];
        const components = context.codebase.components;

        // Find components that could benefit from variants
        const extendableComponents = components.filter(c => {
            const hasBasicProps = c.props && c.props.length > 0 && c.props.length < 8;
            const isNotTooComplex = c.complexity !== 'complex';
            const hasGenericName = /button|card|input|modal|alert/i.test(c.name);
            
            return hasBasicProps && isNotTooComplex && hasGenericName;
        });

        extendableComponents.forEach(component => {
            // Suggest adding variants
            suggestions.push({
                type: 'extend-component',
                name: `Add ${component.name} Variants`,
                description: `Create variants of ${component.name} for different use cases`,
                rationale: `${component.name} is well-structured and could benefit from variants (size, color, style)`,
                confidence: 70,
                priority: 'medium',
                implementation: {
                    strategy: 'extend',
                    baseComponents: [component.name],
                    suggestedStructure: this.generateVariantStructure(component),
                    requiredProps: [
                        { name: 'variant', type: `'primary' | 'secondary' | 'outline'`, required: false },
                        { name: 'size', type: `'sm' | 'md' | 'lg'`, required: false }
                    ]
                }
            });

            // Suggest adding enhanced functionality
            if (component.hooks && component.hooks.length < 3) {
                suggestions.push({
                    type: 'extend-component',
                    name: `Enhanced ${component.name}`,
                    description: `Add advanced features to ${component.name}`,
                    rationale: 'Component has room for additional functionality without becoming too complex',
                    confidence: 65,
                    priority: 'low',
                    implementation: {
                        strategy: 'extend',
                        baseComponents: [component.name],
                        suggestedStructure: this.generateEnhancedStructure(component)
                    }
                });
            }
        });

        return suggestions;
    }

    /**
     * Generate suggestions for new components
     */
    private async generateNewComponentSuggestions(context: IntelligenceContext): Promise<ComponentSuggestion[]> {
        const suggestions: ComponentSuggestion[] = [];
        const components = context.codebase.components;

        // Analyze missing common components
        const existingComponentTypes = new Set(
            components.map(c => this.inferComponentType(c.name))
        );

        const commonComponents = [
            { type: 'button', priority: 'high', confidence: 90 },
            { type: 'input', priority: 'high', confidence: 85 },
            { type: 'card', priority: 'medium', confidence: 80 },
            { type: 'modal', priority: 'medium', confidence: 75 },
            { type: 'form', priority: 'high', confidence: 85 },
            { type: 'list', priority: 'medium', confidence: 70 },
            { type: 'navigation', priority: 'medium', confidence: 75 },
            { type: 'header', priority: 'medium', confidence: 70 },
            { type: 'footer', priority: 'low', confidence: 60 }
        ];

        commonComponents.forEach(({ type, priority, confidence }) => {
            if (!existingComponentTypes.has(type)) {
                suggestions.push({
                    type: 'generate-new',
                    name: `Create ${type.charAt(0).toUpperCase() + type.slice(1)} Component`,
                    description: `Generate a new ${type} component`,
                    rationale: `${type} is a common UI component that's missing from your codebase`,
                    confidence,
                    priority: priority as 'high' | 'medium' | 'low',
                    implementation: {
                        strategy: 'generate',
                        suggestedStructure: this.generateNewComponentStructure(type, context),
                        requiredProps: this.getStandardProps(type),
                        dependencies: this.getStandardDependencies(type, context)
                    }
                });
            }
        });

        // Suggest components based on design system
        if (context.designSystem.library === 'shadcn/ui') {
            const shadcnComponents = [
                'Alert', 'Avatar', 'Badge', 'Calendar', 'Checkbox', 'Dialog', 
                'DropdownMenu', 'Label', 'Progress', 'RadioGroup', 'Select', 
                'Separator', 'Sheet', 'Switch', 'Table', 'Tabs', 'Toast', 'Tooltip'
            ];

            const missingComponents = shadcnComponents.filter(comp => 
                !components.some(c => c.name.toLowerCase().includes(comp.toLowerCase()))
            );

            missingComponents.slice(0, 3).forEach(comp => {
                suggestions.push({
                    type: 'generate-new',
                    name: `Add shadcn/ui ${comp}`,
                    description: `Integrate shadcn/ui ${comp} component`,
                    rationale: `${comp} is a useful shadcn/ui component that would enhance your UI library`,
                    confidence: 80,
                    priority: 'medium',
                    implementation: {
                        strategy: 'generate',
                        suggestedStructure: `Use shadcn/ui CLI to add ${comp} component`,
                        dependencies: ['@radix-ui/*', 'class-variance-authority', 'clsx']
                    }
                });
            });
        }

        return suggestions;
    }

    /**
     * Generate pattern-based suggestions
     */
    private async generatePatternBasedSuggestions(context: IntelligenceContext): Promise<ComponentSuggestion[]> {
        const suggestions: ComponentSuggestion[] = [];
        const components = context.codebase.components;

        // Analyze patterns and suggest improvements
        
        // Pattern: Many components with similar styling approach
        const stylingGroups = this.groupComponentsByStyling(components);
        const dominantStyling = Object.entries(stylingGroups)
            .sort(([, a], [, b]) => b.length - a.length)[0];

        if (dominantStyling && dominantStyling[1].length >= 5) {
            const [approach, componentsUsingIt] = dominantStyling;
            
            suggestions.push({
                type: 'pattern-application',
                name: `Standardize ${approach} Usage`,
                description: `Create consistent ${approach} patterns across components`,
                rationale: `${componentsUsingIt.length} components use ${approach}, suggesting a pattern`,
                confidence: 75,
                priority: 'medium',
                implementation: {
                    strategy: 'refactor',
                    baseComponents: componentsUsingIt.map(c => c.name),
                    suggestedStructure: `Create shared ${approach} utilities or patterns`
                }
            });
        }

        // Pattern: Components with similar complexity could share utilities
        const complexComponents = components.filter(c => c.complexity === 'complex');
        if (complexComponents.length >= 3) {
            suggestions.push({
                type: 'pattern-application',
                name: 'Shared Utility Functions',
                description: 'Extract common logic from complex components',
                rationale: `${complexComponents.length} complex components might share similar logic`,
                confidence: 70,
                priority: 'medium',
                implementation: {
                    strategy: 'refactor',
                    baseComponents: complexComponents.map(c => c.name),
                    suggestedStructure: 'Create shared utility functions or custom hooks'
                }
            });
        }

        // Pattern: Missing error boundaries
        const hasErrorBoundary = components.some(c => 
            /error.*boundary|boundary.*error/i.test(c.name)
        );

        if (!hasErrorBoundary && components.length >= 5) {
            suggestions.push({
                type: 'pattern-application',
                name: 'Add Error Boundary',
                description: 'Implement error boundary for better error handling',
                rationale: 'Large component tree without error boundary could benefit from error handling',
                confidence: 80,
                priority: 'high',
                implementation: {
                    strategy: 'generate',
                    suggestedStructure: 'Create error boundary component to wrap component trees',
                    requiredProps: [
                        { name: 'fallback', type: 'React.ComponentType', required: false },
                        { name: 'onError', type: '(error: Error) => void', required: false }
                    ]
                }
            });
        }

        return suggestions;
    }

    /**
     * Helper methods
     */
    private calculateReuseConfidence(component: ComponentInfo): number {
        let score = 50; // Base score

        // Props increase reusability
        if (component.props && component.props.length > 0) score += 20;
        if (component.props && component.props.length > 3) score += 10;

        // Simple/medium complexity is better for reuse
        if (component.complexity === 'simple') score += 20;
        if (component.complexity === 'medium') score += 10;

        // Generic names are more reusable
        if (/button|input|card|modal|form/i.test(component.name)) score += 15;

        // Good styling approach
        if (component.stylingApproach === 'tailwind') score += 5;

        return Math.min(95, score);
    }

    private groupComponentsByType(components: ComponentInfo[]): Record<string, ComponentInfo[]> {
        const groups: Record<string, ComponentInfo[]> = {};
        
        components.forEach(component => {
            const type = this.inferComponentType(component.name);
            if (!groups[type]) groups[type] = [];
            groups[type].push(component);
        });

        return groups;
    }

    private groupComponentsByStyling(components: ComponentInfo[]): Record<string, ComponentInfo[]> {
        const groups: Record<string, ComponentInfo[]> = {};
        
        components.forEach(component => {
            const approach = component.stylingApproach;
            if (!groups[approach]) groups[approach] = [];
            groups[approach].push(component);
        });

        return groups;
    }

    private inferComponentType(name: string): string {
        const lowerName = name.toLowerCase();
        
        if (/button|btn/.test(lowerName)) return 'button';
        if (/input|field|text/.test(lowerName)) return 'input';
        if (/card/.test(lowerName)) return 'card';
        if (/modal|dialog/.test(lowerName)) return 'modal';
        if (/form/.test(lowerName)) return 'form';
        if (/list/.test(lowerName)) return 'list';
        if (/item/.test(lowerName)) return 'item';
        if (/nav|navigation/.test(lowerName)) return 'navigation';
        if (/header/.test(lowerName)) return 'header';
        if (/footer/.test(lowerName)) return 'footer';
        if (/layout/.test(lowerName)) return 'layout';
        
        return 'other';
    }

    private generateReuseStructure(component: ComponentInfo): string {
        return `
import { ${component.name} } from './${component.path}';

// Use existing ${component.name} with props
<${component.name} 
  ${component.props?.slice(0, 3).map(p => `${p.name}={${p.name}}`).join('\n  ') || ''}
/>`;
    }

    private generateFormCompositionStructure(): string {
        return `
const FormComponent = ({ fields, onSubmit }) => (
  <form onSubmit={onSubmit}>
    {fields.map(field => (
      <Input key={field.name} {...field} />
    ))}
    <Button type="submit">Submit</Button>
  </form>
);`;
    }

    private generateVariantStructure(component: ComponentInfo): string {
        return `
// Add variant support to ${component.name}
interface ${component.name}Props {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  ${component.props?.map(p => `${p.name}${p.required ? '' : '?'}: ${p.type};`).join('\n  ') || ''}
}`;
    }

    private generateEnhancedStructure(component: ComponentInfo): string {
        return `
// Enhanced ${component.name} with additional features
const Enhanced${component.name} = ({ 
  loading, 
  error, 
  ...props 
}) => {
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return <${component.name} {...props} />;
};`;
    }

    private generateNewComponentStructure(type: string, context: IntelligenceContext): string {
        const framework = context.project.framework;
        const styling = context.codebase.conventions.styling.approach;
        
        const templates: Record<string, string> = {
            button: `
interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  ...props 
}) => (
  <button 
    className={\`btn btn-\${variant} btn-\${size}\`}
    {...props}
  >
    {children}
  </button>
);`,
            input: `
interface InputProps {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  required?: boolean;
}

const Input: React.FC<InputProps> = ({ 
  label, 
  error, 
  ...props 
}) => (
  <div className="input-group">
    {label && <label>{label}</label>}
    <input {...props} />
    {error && <span className="error">{error}</span>}
  </div>
);`,
            card: `
interface CardProps {
  children: React.ReactNode;
  title?: string;
  footer?: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ 
  children, 
  title, 
  footer,
  className 
}) => (
  <div className={\`card \${className || ''}\`}>
    {title && <h3 className="card-title">{title}</h3>}
    <div className="card-content">{children}</div>
    {footer && <div className="card-footer">{footer}</div>}
  </div>
);`
        };

        return templates[type] || `// ${type} component implementation`;
    }

    private getStandardProps(type: string) {
        const standardProps: Record<string, any[]> = {
            button: [
                { name: 'children', type: 'React.ReactNode', required: true },
                { name: 'onClick', type: '() => void', required: false },
                { name: 'disabled', type: 'boolean', required: false }
            ],
            input: [
                { name: 'value', type: 'string', required: true },
                { name: 'onChange', type: '(value: string) => void', required: true },
                { name: 'placeholder', type: 'string', required: false }
            ],
            card: [
                { name: 'children', type: 'React.ReactNode', required: true },
                { name: 'title', type: 'string', required: false }
            ]
        };

        return standardProps[type] || [];
    }

    private getStandardDependencies(type: string, context: IntelligenceContext): string[] {
        const dependencies: string[] = ['react'];
        
        if (context.codebase.conventions.styling.approach === 'tailwind') {
            dependencies.push('tailwindcss');
        }

        if (context.designSystem.library === 'shadcn/ui') {
            dependencies.push('@radix-ui/react-slot', 'class-variance-authority');
        }

        return dependencies;
    }
}