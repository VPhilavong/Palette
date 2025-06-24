import * as babel from '@babel/parser';
// @ts-ignore - Babel traverse doesn't have proper types
import traverse from '@babel/traverse';
import * as t from '@babel/types';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import {
    ComponentAST,
    PropAnalysis,
    HookUsage,
    ImportInfo,
    ExportInfo,
    JSXAnalysis,
    ComponentStyling,
    ComplexityMetrics,
    AccessibilityInfo,
    InteractivityInfo,
    ComponentCategory
} from './types';

export class ASTAnalyzer {
    
    /**
     * Quick check if content contains React component patterns
     */
    private isLikelyReactComponent(content: string): boolean {
        // Quick regex checks for React patterns
        const hasReactImport = /import.*react/i.test(content);
        const hasJSX = /<[A-Z]/.test(content) || /jsx/i.test(content);
        const hasExport = /export\s+(default\s+)?(function|const|class)/.test(content);
        const hasReturn = /return\s*\(?\s*</.test(content);
        
        return (hasJSX || hasReturn) && (hasReactImport || hasExport);
    }
    
    /**
     * Parse and analyze a React component file using AST (optimized)
     */
    async analyzeComponent(filePath: string): Promise<ComponentAST | null> {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Skip large files to prevent hanging
            if (content.length > 100000) { // 100KB limit
                console.warn(`Skipping large file ${filePath} (${content.length} chars)`);
                return null;
            }
            
            const isTypeScript = filePath.endsWith('.tsx') || filePath.endsWith('.ts');
            
            // Quick check if this is likely a React component
            if (!this.isLikelyReactComponent(content)) {
                return null;
            }
            
            // Parse with TypeScript support
            const plugins: any[] = [
                'jsx',
                'decorators-legacy',
                'classProperties',
                'objectRestSpread',
                'functionBind',
                'exportDefaultFrom',
                'dynamicImport'
            ];
            
            if (isTypeScript) {
                plugins.push('typescript');
            }
            
            const ast = babel.parse(content, {
                sourceType: 'module',
                plugins,
                strictMode: false // More permissive parsing
            });

            const analysis: Partial<ComponentAST> = {
                props: [],
                hooks: [],
                imports: [],
                exports: [],
                complexity: {
                    cyclomaticComplexity: 1,
                    cognitiveComplexity: 0,
                    linesOfCode: content.split('\n').length,
                    depth: 0
                }
            };

            let componentName = '';
            let componentType: 'functional' | 'class' = 'functional';
            let jsxElements: t.JSXElement[] = [];
            let maxDepth = 0;
            let currentDepth = 0;

            traverse(ast, {
                enter(path: any) {
                    currentDepth++;
                    maxDepth = Math.max(maxDepth, currentDepth);
                },
                exit() {
                    currentDepth--;
                },

                // Analyze imports
                ImportDeclaration(path: any) {
                    const importInfo = this.analyzeImport(path.node);
                    analysis.imports!.push(importInfo);
                },

                // Analyze exports and find component
                ExportDefaultDeclaration(path: any) {
                    const exportInfo = this.analyzeExport(path.node, true);
                    analysis.exports!.push(exportInfo);
                    
                    if (exportInfo.isComponent) {
                        componentName = exportInfo.name;
                    }
                },

                ExportNamedDeclaration(path: any) {
                    if (path.node.declaration) {
                        const exportInfo = this.analyzeExport(path.node, false);
                        analysis.exports!.push(exportInfo);
                    }
                },

                // Analyze function components
                FunctionDeclaration(path: any) {
                    if (this.isReactComponent(path.node)) {
                        componentName = path.node.id?.name || 'Anonymous';
                        componentType = 'functional';
                        analysis.props = this.analyzeProps(path.node);
                    }
                },

                ArrowFunctionExpression(path: any) {
                    const parent = path.parent;
                    if (t.isVariableDeclarator(parent) && t.isIdentifier(parent.id)) {
                        if (this.isReactComponent(path.node)) {
                            componentName = parent.id.name;
                            componentType = 'functional';
                            analysis.props = this.analyzeProps(path.node);
                        }
                    }
                },

                // Analyze class components
                ClassDeclaration(path: any) {
                    if (this.isReactClassComponent(path.node)) {
                        componentName = path.node.id?.name || 'Anonymous';
                        componentType = 'class';
                    }
                },

                // Analyze hooks
                CallExpression(path: any) {
                    const hookUsage = this.analyzeHook(path.node);
                    if (hookUsage) {
                        analysis.hooks!.push(hookUsage);
                    }

                    // Count complexity for conditionals and loops
                    if (this.isComplexityNode(path.node)) {
                        analysis.complexity!.cyclomaticComplexity++;
                        analysis.complexity!.cognitiveComplexity++;
                    }
                },

                // Collect JSX elements
                JSXElement(path: any) {
                    jsxElements.push(path.node);
                },

                // Analyze control flow for complexity
                IfStatement(path: any) {
                    analysis.complexity!.cyclomaticComplexity++;
                    analysis.complexity!.cognitiveComplexity++;
                },

                ConditionalExpression(path: any) {
                    analysis.complexity!.cyclomaticComplexity++;
                    analysis.complexity!.cognitiveComplexity++;
                },

                LogicalExpression(path: any) {
                    if (path.node.operator === '&&' || path.node.operator === '||') {
                        analysis.complexity!.cognitiveComplexity++;
                    }
                },

                WhileStatement(path: any) {
                    analysis.complexity!.cyclomaticComplexity++;
                    analysis.complexity!.cognitiveComplexity += 2;
                },

                ForStatement(path: any) {
                    analysis.complexity!.cyclomaticComplexity++;
                    analysis.complexity!.cognitiveComplexity += 2;
                }
            });

            analysis.complexity!.depth = maxDepth;

            // Analyze JSX
            analysis.jsx = this.analyzeJSX(jsxElements);
            
            // Analyze styling
            analysis.styling = this.analyzeStyling(content, jsxElements);

            return {
                name: componentName,
                type: componentType,
                props: analysis.props!,
                hooks: analysis.hooks!,
                imports: analysis.imports!,
                exports: analysis.exports!,
                jsx: analysis.jsx!,
                styling: analysis.styling!,
                complexity: analysis.complexity!
            };

        } catch (error) {
            console.error(`Error analyzing component ${filePath}:`, error);
            return null;
        }
    }

    private analyzeImport(node: t.ImportDeclaration): ImportInfo {
        const source = node.source.value;
        const isExternal = !source.startsWith('.') && !source.startsWith('/');
        
        let imports: string[] = [];
        let type: 'default' | 'named' | 'namespace' = 'named';

        if (node.specifiers) {
            node.specifiers.forEach(spec => {
                if (t.isImportDefaultSpecifier(spec)) {
                    imports.push(spec.local.name);
                    type = 'default';
                } else if (t.isImportSpecifier(spec)) {
                    imports.push(spec.local.name);
                } else if (t.isImportNamespaceSpecifier(spec)) {
                    imports.push(spec.local.name);
                    type = 'namespace';
                }
            });
        }

        const category = this.categorizeImport(source, imports);

        return {
            source,
            type,
            imports,
            isExternal,
            category
        };
    }

    private categorizeImport(source: string, imports: string[]): ImportInfo['category'] {
        if (source === 'react' || imports.some(imp => ['React', 'useState', 'useEffect'].includes(imp))) {
            return 'react';
        }
        if (source.includes('styled') || source.includes('.css') || source.includes('.scss')) {
            return 'style';
        }
        if (source.startsWith('.')) {
            // Check if it's likely a component based on naming
            if (imports.some(imp => /^[A-Z]/.test(imp))) {
                return 'component';
            }
            return 'utility';
        }
        return 'library';
    }

    private analyzeExport(node: t.ExportDefaultDeclaration | t.ExportNamedDeclaration, isDefault: boolean): ExportInfo {
        let name = 'Unknown';
        let isComponent = false;

        if (isDefault && 'declaration' in node && node.declaration) {
            if (t.isFunctionDeclaration(node.declaration) && node.declaration.id) {
                name = node.declaration.id.name;
                isComponent = this.isReactComponent(node.declaration);
            } else if (t.isIdentifier(node.declaration)) {
                name = node.declaration.name;
                isComponent = /^[A-Z]/.test(name); // Likely component if starts with capital
            }
        }

        return {
            name,
            type: isDefault ? 'default' : 'named',
            isComponent
        };
    }

    private isReactComponent(node: t.Function): boolean {
        // Check if function returns JSX
        let hasJSXReturn = false;
        
        if (node.body && t.isBlockStatement(node.body)) {
            traverse(node.body, {
                ReturnStatement(path: any) {
                    if (path.node.argument && this.containsJSX(path.node.argument)) {
                        hasJSXReturn = true;
                    }
                }
            }, undefined, {}, node);
        }

        return hasJSXReturn;
    }

    private isReactClassComponent(node: t.ClassDeclaration): boolean {
        return node.superClass !== null && 
               t.isIdentifier(node.superClass) && 
               (node.superClass.name === 'Component' || node.superClass.name === 'PureComponent');
    }

    private containsJSX(node: t.Node): boolean {
        let hasJSX = false;
        traverse(node, {
            JSXElement(path: any) {
                hasJSX = true;
            },
            JSXFragment(path: any) {
                hasJSX = true;
            }
        }, undefined, {});
        return hasJSX;
    }

    private analyzeProps(node: t.Function): PropAnalysis[] {
        const props: PropAnalysis[] = [];
        
        if (node.params.length > 0) {
            const firstParam = node.params[0];
            
            if (t.isObjectPattern(firstParam)) {
                // Destructured props
                firstParam.properties.forEach(prop => {
                    if (t.isObjectProperty(prop) && t.isIdentifier(prop.key)) {
                        props.push({
                            name: prop.key.name,
                            type: 'unknown', // Would need TypeScript analysis for exact types
                            optional: false,
                            defaultValue: t.isAssignmentPattern(prop.value) ? 'has default' : undefined
                        });
                    }
                });
            } else if (t.isIdentifier(firstParam)) {
                // Props passed as single parameter
                props.push({
                    name: firstParam.name,
                    type: 'object',
                    optional: false
                });
            }
        }

        return props;
    }

    private analyzeHook(node: t.CallExpression): HookUsage | null {
        if (t.isIdentifier(node.callee)) {
            const hookName = node.callee.name;
            
            if (hookName.startsWith('use')) {
                const type = this.categorizeHook(hookName);
                const complexity = this.calculateHookComplexity(node);
                
                return {
                    name: hookName,
                    type,
                    complexity,
                    dependencies: this.extractHookDependencies(node)
                };
            }
        }
        
        return null;
    }

    private categorizeHook(hookName: string): HookUsage['type'] {
        const mapping: Record<string, HookUsage['type']> = {
            'useState': 'state',
            'useEffect': 'effect',
            'useContext': 'context',
            'useCallback': 'callback',
            'useMemo': 'memo',
            'useRef': 'ref'
        };
        
        return mapping[hookName] || 'custom';
    }

    private calculateHookComplexity(node: t.CallExpression): number {
        let complexity = 1;
        
        // Increase complexity based on number of arguments and their complexity
        complexity += node.arguments.length;
        
        node.arguments.forEach(arg => {
            if (t.isArrowFunctionExpression(arg) || t.isFunctionExpression(arg)) {
                complexity += 2;
            }
        });
        
        return complexity;
    }

    private extractHookDependencies(node: t.CallExpression): string[] {
        const deps: string[] = [];
        
        // For useEffect, useCallback, useMemo - look at dependency array
        if (node.arguments.length > 1) {
            const depArg = node.arguments[1];
            if (t.isArrayExpression(depArg)) {
                depArg.elements.forEach(element => {
                    if (t.isIdentifier(element)) {
                        deps.push(element.name);
                    }
                });
            }
        }
        
        return deps;
    }

    private analyzeJSX(elements: t.JSXElement[]): JSXAnalysis {
        const patterns: string[] = [];
        const accessibility = this.analyzeAccessibility(elements);
        const interactivity = this.analyzeInteractivity(elements);
        
        // Detect common patterns
        if (elements.some(el => this.hasConditionalRendering(el))) {
            patterns.push('conditional-rendering');
        }
        
        if (elements.some(el => this.hasListRendering(el))) {
            patterns.push('list-rendering');
        }
        
        if (elements.some(el => this.hasFormElements(el))) {
            patterns.push('form-handling');
        }

        return {
            elementCount: elements.length,
            complexity: this.calculateJSXComplexity(elements),
            patterns,
            accessibility,
            interactivity
        };
    }

    private analyzeAccessibility(elements: t.JSXElement[]): AccessibilityInfo {
        const ariaAttributes: string[] = [];
        const semanticElements: string[] = [];
        let keyboardHandling = false;
        let focusManagement = false;

        elements.forEach(element => {
            // Check element name for semantic HTML
            if (t.isJSXIdentifier(element.openingElement.name)) {
                const tagName = element.openingElement.name.name;
                if (['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'].includes(tagName)) {
                    semanticElements.push(tagName);
                }
            }

            // Check for ARIA attributes
            element.openingElement.attributes.forEach(attr => {
                if (t.isJSXAttribute(attr) && t.isJSXIdentifier(attr.name)) {
                    const attrName = attr.name.name;
                    if (attrName.startsWith('aria-')) {
                        ariaAttributes.push(attrName);
                    }
                    if (attrName === 'onKeyDown' || attrName === 'onKeyUp') {
                        keyboardHandling = true;
                    }
                    if (attrName === 'autoFocus' || attrName === 'tabIndex') {
                        focusManagement = true;
                    }
                }
            });
        });

        const score = this.calculateAccessibilityScore(ariaAttributes, semanticElements, keyboardHandling, focusManagement);

        return {
            ariaAttributes: [...new Set(ariaAttributes)],
            semanticElements: [...new Set(semanticElements)],
            keyboardHandling,
            focusManagement,
            score
        };
    }

    private analyzeInteractivity(elements: t.JSXElement[]): InteractivityInfo {
        const eventHandlers: string[] = [];
        let formElements = false;
        let animations = false;
        let stateManagement: InteractivityInfo['stateManagement'] = 'none';

        elements.forEach(element => {
            element.openingElement.attributes.forEach(attr => {
                if (t.isJSXAttribute(attr) && t.isJSXIdentifier(attr.name)) {
                    const attrName = attr.name.name;
                    if (attrName.startsWith('on')) {
                        eventHandlers.push(attrName);
                    }
                    if (['className', 'style'].includes(attrName) && attr.value) {
                        // Simple check for animation-related classes/styles
                        const value = this.getAttributeValue(attr.value);
                        if (value && (value.includes('transition') || value.includes('animation'))) {
                            animations = true;
                        }
                    }
                }
            });

            // Check for form elements
            if (t.isJSXIdentifier(element.openingElement.name)) {
                const tagName = element.openingElement.name.name;
                if (['input', 'select', 'textarea', 'form', 'button'].includes(tagName)) {
                    formElements = true;
                }
            }
        });

        // Determine state management complexity
        if (eventHandlers.length > 3) {
            stateManagement = 'complex';
        } else if (eventHandlers.length > 0) {
            stateManagement = 'simple';
        }

        return {
            eventHandlers: [...new Set(eventHandlers)],
            formElements,
            animations,
            stateManagement
        };
    }

    private analyzeStyling(content: string, elements: t.JSXElement[]): ComponentStyling {
        const classes: string[] = [];
        let inlineStyles = false;
        let responsive = false;
        let animations = false;
        const variants: string[] = [];

        // Detect styling approach
        let approach = 'unknown';
        if (content.includes('styled.') || content.includes('styled(')) {
            approach = 'styled-components';
        } else if (content.includes('className')) {
            approach = 'css-classes';
        } else if (content.includes('style={{')) {
            approach = 'inline-styles';
            inlineStyles = true;
        }

        // Extract classes and detect patterns
        elements.forEach(element => {
            element.openingElement.attributes.forEach(attr => {
                if (t.isJSXAttribute(attr) && t.isJSXIdentifier(attr.name)) {
                    if (attr.name.name === 'className' && attr.value) {
                        const value = this.getAttributeValue(attr.value);
                        if (value) {
                            const classNames = value.split(/\s+/);
                            classes.push(...classNames);
                            
                            // Check for responsive patterns
                            if (classNames.some(cls => /^(sm|md|lg|xl):/i.test(cls))) {
                                responsive = true;
                            }
                            
                            // Check for animations
                            if (classNames.some(cls => cls.includes('transition') || cls.includes('animate'))) {
                                animations = true;
                            }
                            
                            // Check for variant patterns
                            if (classNames.some(cls => /(primary|secondary|danger|success|warning)/i.test(cls))) {
                                variants.push('color-variants');
                            }
                            if (classNames.some(cls => /(small|large|xs|xl)/i.test(cls))) {
                                variants.push('size-variants');
                            }
                        }
                    }
                }
            });
        });

        return {
            approach,
            classes: [...new Set(classes)],
            inlineStyles,
            responsive,
            variants: [...new Set(variants)],
            animations
        };
    }

    private getAttributeValue(value: t.JSXExpressionContainer | t.StringLiteral | t.JSXElement | t.JSXFragment | null): string | null {
        if (t.isStringLiteral(value)) {
            return value.value;
        }
        if (t.isJSXExpressionContainer(value) && t.isStringLiteral(value.expression)) {
            return value.expression.value;
        }
        // Handle template literals and other expressions
        if (t.isJSXExpressionContainer(value) && t.isTemplateLiteral(value.expression)) {
            return value.expression.quasis.map(q => q.value.raw).join('');
        }
        return null;
    }

    private hasConditionalRendering(element: t.JSXElement): boolean {
        // Simple check for conditional rendering patterns
        let hasConditional = false;
        traverse(element, {
            ConditionalExpression(path: any) {
                hasConditional = true;
            },
            LogicalExpression(path: any) {
                if (path.node.operator === '&&') {
                    hasConditional = true;
                }
            }
        }, undefined, {});
        return hasConditional;
    }

    private hasListRendering(element: t.JSXElement): boolean {
        // Check for .map() calls which indicate list rendering
        let hasMap = false;
        traverse(element, {
            CallExpression(path: any) {
                if (t.isMemberExpression(path.node.callee) && 
                    t.isIdentifier(path.node.callee.property) && 
                    path.node.callee.property.name === 'map') {
                    hasMap = true;
                }
            }
        }, undefined, {});
        return hasMap;
    }

    private hasFormElements(element: t.JSXElement): boolean {
        let hasForm = false;
        traverse(element, {
            JSXElement(path: any) {
                if (t.isJSXIdentifier(path.node.openingElement.name)) {
                    const tagName = path.node.openingElement.name.name;
                    if (['input', 'select', 'textarea', 'form'].includes(tagName)) {
                        hasForm = true;
                    }
                }
            }
        }, undefined, {});
        return hasForm;
    }

    private calculateJSXComplexity(elements: t.JSXElement[]): number {
        let complexity = elements.length;
        
        elements.forEach(element => {
            // Add complexity for each attribute
            complexity += element.openingElement.attributes.length;
            
            // Add complexity for nested elements
            const nestedElements = this.countNestedElements(element);
            complexity += nestedElements;
        });
        
        return complexity;
    }

    private countNestedElements(element: t.JSXElement): number {
        let count = 0;
        element.children.forEach(child => {
            if (t.isJSXElement(child)) {
                count += 1 + this.countNestedElements(child);
            }
        });
        return count;
    }

    private calculateAccessibilityScore(
        ariaAttributes: string[], 
        semanticElements: string[], 
        keyboardHandling: boolean, 
        focusManagement: boolean
    ): number {
        let score = 0;
        
        // Score based on ARIA attributes (max 30 points)
        score += Math.min(ariaAttributes.length * 5, 30);
        
        // Score based on semantic elements (max 30 points)
        score += Math.min(semanticElements.length * 6, 30);
        
        // Score for keyboard handling (20 points)
        if (keyboardHandling) score += 20;
        
        // Score for focus management (20 points)
        if (focusManagement) score += 20;
        
        return Math.min(score, 100);
    }

    private isComplexityNode(node: t.CallExpression): boolean {
        // Add complexity for certain function calls that indicate control flow
        if (t.isIdentifier(node.callee)) {
            const name = node.callee.name;
            return ['map', 'filter', 'reduce', 'forEach'].includes(name);
        }
        return false;
    }

    /**
     * Categorize component based on its analysis
     */
    categorizeComponent(ast: ComponentAST): ComponentCategory {
        const { jsx, hooks, styling, imports } = ast;
        
        // Layout components
        if (jsx.patterns.includes('conditional-rendering') && jsx.elementCount > 5) {
            return 'layout';
        }
        
        // Form components
        if (jsx.patterns.includes('form-handling') || jsx.interactivity.formElements) {
            return 'form';
        }
        
        // Navigation components
        if (imports.some(imp => imp.imports.includes('router') || imp.imports.includes('Link'))) {
            return 'navigation';
        }
        
        // UI primitives (simple, reusable)
        if (hooks.length <= 2 && jsx.elementCount <= 3 && styling.variants.length > 0) {
            return 'ui-primitive';
        }
        
        // Data display components
        if (jsx.patterns.includes('list-rendering')) {
            return 'data-display';
        }
        
        // Feedback components (modals, alerts, etc.)
        if (jsx.interactivity.animations || styling.animations) {
            return 'feedback';
        }
        
        // Complex business logic
        if (hooks.length > 5 || ast.complexity.cyclomaticComplexity > 10) {
            return 'business-logic';
        }
        
        // Default to utility
        return 'utility';
    }
}