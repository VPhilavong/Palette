import * as babel from '@babel/parser';
// @ts-ignore - Babel traverse doesn't have proper types
import traverse from '@babel/traverse';
import * as t from '@babel/types';
import * as fs from 'fs';
import * as path from 'path';
import {
    DetectedPattern,
    PatternType,
    CodeSnippet,
    SnippetContext,
    DesignSystemAnalysis,
    StateManagementAnalysis,
    TypeScriptPatterns,
    ExampleLibrary,
    ComponentInfo,
    ComponentAST,
    ThemeStructure,
    ColorPalette,
    SpacingSystem
} from './types';

export class AdvancedPatternAnalyzer {
    private patternCache: Map<string, DetectedPattern[]> = new Map();
    private snippetCache: Map<string, CodeSnippet[]> = new Map();
    
    /**
     * Analyze codebase patterns comprehensively
     */
    async analyzeCodebasePatterns(components: ComponentInfo[], rootPath: string): Promise<ExampleLibrary> {
        console.log('🔍 Starting advanced pattern analysis...');
        
        const snippets: Record<string, CodeSnippet[]> = {};
        const patterns: Record<PatternType, DetectedPattern[]> = {} as Record<PatternType, DetectedPattern[]>;
        
        // Analyze each component for patterns
        for (const component of components) {
            const filePath = path.join(rootPath, component.path);
            const componentPatterns = await this.analyzeComponentPatterns(filePath, component);
            const componentSnippets = await this.extractCodeSnippets(filePath, component);
            
            // Group by pattern type
            componentPatterns.forEach(pattern => {
                if (!patterns[pattern.type]) {
                    patterns[pattern.type] = [];
                }
                patterns[pattern.type].push(pattern);
            });
            
            // Group snippets by category
            const category = component.category || 'utility';
            if (!snippets[category]) {
                snippets[category] = [];
            }
            snippets[category].push(...componentSnippets);
        }
        
        // Build templates from patterns
        const templates = await this.buildComponentTemplates(snippets, patterns);
        const bestPractices = await this.identifyBestPractices(patterns, snippets);
        
        return {
            snippets,
            patterns,
            templates,
            bestPractices
        };
    }
    
    /**
     * Analyze patterns in a single component
     */
    private async analyzeComponentPatterns(filePath: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const cacheKey = `${filePath}:${fs.statSync(filePath).mtime.getTime()}`;
        if (this.patternCache.has(cacheKey)) {
            return this.patternCache.get(cacheKey)!;
        }
        
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const patterns: DetectedPattern[] = [];
            
            const isTypeScript = filePath.endsWith('.tsx') || filePath.endsWith('.ts');
            const plugins: any[] = ['jsx', 'decorators-legacy', 'classProperties'];
            if (isTypeScript) plugins.push('typescript');
            
            const ast = babel.parse(content, {
                sourceType: 'module',
                plugins
            });
            
            // Analyze different pattern types
            patterns.push(...await this.analyzeHookPatterns(ast, content, component));
            patterns.push(...await this.analyzeStateManagementPatterns(ast, content, component));
            patterns.push(...await this.analyzeStylingPatterns(ast, content, component));
            patterns.push(...await this.analyzeCompositionPatterns(ast, content, component));
            patterns.push(...await this.analyzeTypeScriptPatterns(ast, content, component));
            patterns.push(...await this.analyzeErrorHandlingPatterns(ast, content, component));
            patterns.push(...await this.analyzeLoadingStatePatterns(ast, content, component));
            patterns.push(...await this.analyzeAccessibilityPatterns(ast, content, component));
            patterns.push(...await this.analyzePerformancePatterns(ast, content, component));
            
            this.patternCache.set(cacheKey, patterns);
            return patterns;
        } catch (error) {
            console.warn(`Error analyzing patterns in ${filePath}:`, error);
            return [];
        }
    }
    
    /**
     * Analyze hook usage patterns
     */
    private async analyzeHookPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        const hookPatterns = new Map<string, { usage: number; examples: string[] }>();
        
        traverse(ast, {
            CallExpression(path: any) {
                if (t.isIdentifier(path.node.callee) && path.node.callee.name.startsWith('use')) {
                    const hookName = path.node.callee.name;
                    const hookCode = content.slice(path.node.start, path.node.end);
                    
                    if (!hookPatterns.has(hookName)) {
                        hookPatterns.set(hookName, { usage: 0, examples: [] });
                    }
                    
                    const pattern = hookPatterns.get(hookName)!;
                    pattern.usage++;
                    if (pattern.examples.length < 3) {
                        pattern.examples.push(hookCode);
                    }
                }
            }
        });
        
        // Detect advanced hook patterns
        if (content.includes('useCallback') && content.includes('useMemo')) {
            patterns.push({
                type: 'hook-pattern',
                name: 'performance-optimization',
                description: 'Uses useCallback and useMemo for performance optimization',
                examples: this.extractExamples(content, ['useCallback', 'useMemo']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        if (content.includes('useEffect') && content.includes('cleanup')) {
            patterns.push({
                type: 'hook-pattern',
                name: 'effect-cleanup',
                description: 'Properly implements useEffect cleanup',
                examples: this.extractExamples(content, ['useEffect.*cleanup', 'return.*\\(\\)']),
                confidence: 0.85,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze state management patterns
     */
    private async analyzeStateManagementPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        // Detect reducer pattern
        if (content.includes('useReducer') || content.includes('reducer')) {
            patterns.push({
                type: 'state-management',
                name: 'reducer-pattern',
                description: 'Uses reducer pattern for complex state',
                examples: this.extractExamples(content, ['useReducer', 'reducer']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect context usage
        if (content.includes('useContext') || content.includes('createContext')) {
            patterns.push({
                type: 'state-management',
                name: 'context-api',
                description: 'Uses React Context for state sharing',
                examples: this.extractExamples(content, ['useContext', 'createContext']),
                confidence: 0.85,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect external state management
        if (content.includes('useStore') || content.includes('useSelector')) {
            patterns.push({
                type: 'state-management',
                name: 'external-store',
                description: 'Uses external state management library',
                examples: this.extractExamples(content, ['useStore', 'useSelector']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze styling patterns
     */
    private async analyzeStylingPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        // Detect Tailwind patterns
        if (content.includes('className') && /className.*["'].*\b(bg-|text-|p-|m-|flex|grid)/.test(content)) {
            const tailwindClasses = this.extractTailwindClasses(content);
            patterns.push({
                type: 'styling-pattern',
                name: 'tailwind-utility-classes',
                description: 'Uses Tailwind CSS utility classes',
                examples: tailwindClasses.slice(0, 5),
                confidence: 0.95,
                usage: {
                    frequency: tailwindClasses.length,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect component variants
        if (content.includes('variant') || /className.*\$\{/.test(content)) {
            patterns.push({
                type: 'styling-pattern',
                name: 'component-variants',
                description: 'Implements component style variants',
                examples: this.extractExamples(content, ['variant', 'className.*\\$\\{']),
                confidence: 0.8,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect CSS-in-JS
        if (content.includes('styled') || content.includes('css`')) {
            patterns.push({
                type: 'styling-pattern',
                name: 'css-in-js',
                description: 'Uses CSS-in-JS styling approach',
                examples: this.extractExamples(content, ['styled', 'css`']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze composition patterns
     */
    private async analyzeCompositionPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        // Detect render props
        if (content.includes('children') && /children.*\(/.test(content)) {
            patterns.push({
                type: 'composition-pattern',
                name: 'render-props',
                description: 'Uses render props pattern',
                examples: this.extractExamples(content, ['children.*\\(']),
                confidence: 0.8,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect compound components
        if (content.includes('.displayName') || /\w+\.\w+/.test(content)) {
            patterns.push({
                type: 'composition-pattern',
                name: 'compound-components',
                description: 'Uses compound component pattern',
                examples: this.extractExamples(content, ['\\.displayName', '\\w+\\.\\w+']),
                confidence: 0.7,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze TypeScript patterns
     */
    private async analyzeTypeScriptPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        // Detect proper return type usage
        if (content.includes('React.JSX.Element') || content.includes('JSX.Element')) {
            patterns.push({
                type: 'typescript-pattern',
                name: 'proper-return-types',
                description: 'Uses proper React return types',
                examples: this.extractExamples(content, ['React\\.JSX\\.Element', 'JSX\\.Element']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        // Detect generic props interfaces
        if (content.includes('interface') && content.includes('Props')) {
            patterns.push({
                type: 'typescript-pattern',
                name: 'props-interface',
                description: 'Defines proper Props interface',
                examples: this.extractExamples(content, ['interface.*Props']),
                confidence: 0.85,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze error handling patterns
     */
    private async analyzeErrorHandlingPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        if (content.includes('try') && content.includes('catch')) {
            patterns.push({
                type: 'error-handling',
                name: 'try-catch-blocks',
                description: 'Implements proper error handling',
                examples: this.extractExamples(content, ['try.*catch']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        if (content.includes('ErrorBoundary') || content.includes('error')) {
            patterns.push({
                type: 'error-handling',
                name: 'error-boundary',
                description: 'Uses error boundaries',
                examples: this.extractExamples(content, ['ErrorBoundary', 'error']),
                confidence: 0.8,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze loading state patterns
     */
    private async analyzeLoadingStatePatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        if (content.includes('loading') || content.includes('isLoading')) {
            patterns.push({
                type: 'loading-state',
                name: 'loading-states',
                description: 'Implements loading states',
                examples: this.extractExamples(content, ['loading', 'isLoading']),
                confidence: 0.85,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        if (content.includes('Suspense') || content.includes('fallback')) {
            patterns.push({
                type: 'loading-state',
                name: 'suspense-pattern',
                description: 'Uses React Suspense for loading',
                examples: this.extractExamples(content, ['Suspense', 'fallback']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze accessibility patterns
     */
    private async analyzeAccessibilityPatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        if (content.includes('aria-') || content.includes('role=')) {
            patterns.push({
                type: 'accessibility-pattern',
                name: 'aria-attributes',
                description: 'Uses ARIA attributes for accessibility',
                examples: this.extractExamples(content, ['aria-', 'role=']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Analyze performance patterns
     */
    private async analyzePerformancePatterns(ast: t.File, content: string, component: ComponentInfo): Promise<DetectedPattern[]> {
        const patterns: DetectedPattern[] = [];
        
        if (content.includes('React.memo') || content.includes('memo(')) {
            patterns.push({
                type: 'performance-pattern',
                name: 'memoization',
                description: 'Uses React.memo for performance',
                examples: this.extractExamples(content, ['React\\.memo', 'memo\\(']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        if (content.includes('lazy(') || content.includes('React.lazy')) {
            patterns.push({
                type: 'performance-pattern',
                name: 'code-splitting',
                description: 'Uses code splitting with React.lazy',
                examples: this.extractExamples(content, ['lazy\\(', 'React\\.lazy']),
                confidence: 0.9,
                usage: {
                    frequency: 1,
                    components: [component.name],
                    evolution: 'stable',
                    bestPractice: true
                }
            });
        }
        
        return patterns;
    }
    
    /**
     * Extract code snippets from components
     */
    private async extractCodeSnippets(filePath: string, component: ComponentInfo): Promise<CodeSnippet[]> {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const lines = content.split('\n');
            const snippets: CodeSnippet[] = [];
            
            // Extract function/component definitions
            const functionMatches = content.match(/(?:const|function)\s+\w+.*?{[\s\S]*?^}/gm);
            if (functionMatches) {
                functionMatches.forEach((match, index) => {
                    const startLine = content.indexOf(match);
                    const endLine = startLine + match.length;
                    
                    snippets.push({
                        id: `${component.name}-${index}`,
                        componentName: component.name,
                        category: component.category || 'utility',
                        snippet: match,
                        context: {
                            filePath,
                            startLine: content.substring(0, startLine).split('\n').length,
                            endLine: content.substring(0, endLine).split('\n').length,
                            surrounding: this.getSurroundingLines(lines, startLine, 3),
                            imports: this.extractImportsFromContent(content),
                            exports: this.extractExportsFromContent(content)
                        },
                        patterns: [],
                        usageFrequency: 1
                    });
                });
            }
            
            return snippets;
        } catch (error) {
            console.warn(`Error extracting snippets from ${filePath}:`, error);
            return [];
        }
    }
    
    /**
     * Extract Tailwind classes from content
     */
    private extractTailwindClasses(content: string): string[] {
        const classMatches = content.match(/className=["']([^"']*?)["']/g);
        if (!classMatches) return [];
        
        const classes: string[] = [];
        classMatches.forEach(match => {
            const classContent = match.match(/className=["']([^"']*?)["']/);
            if (classContent && classContent[1]) {
                classes.push(...classContent[1].split(/\s+/).filter(Boolean));
            }
        });
        
        return [...new Set(classes)];
    }
    
    /**
     * Extract examples based on regex patterns
     */
    private extractExamples(content: string, patterns: string[]): string[] {
        const examples: string[] = [];
        
        patterns.forEach(pattern => {
            const regex = new RegExp(pattern, 'g');
            let match;
            while ((match = regex.exec(content)) !== null && examples.length < 3) {
                // Get surrounding context
                const start = Math.max(0, match.index - 50);
                const end = Math.min(content.length, match.index + match[0].length + 50);
                examples.push(content.substring(start, end).trim());
            }
        });
        
        return examples;
    }
    
    /**
     * Get surrounding lines for context
     */
    private getSurroundingLines(lines: string[], startLine: number, context: number): string[] {
        const start = Math.max(0, startLine - context);
        const end = Math.min(lines.length, startLine + context);
        return lines.slice(start, end);
    }
    
    /**
     * Extract imports from content
     */
    private extractImportsFromContent(content: string): string[] {
        const imports: string[] = [];
        const importMatches = content.match(/import.*?from\s+["']([^"']+)["']/g);
        if (importMatches) {
            importMatches.forEach(match => {
                const source = match.match(/from\s+["']([^"']+)["']/);
                if (source) {
                    imports.push(source[1]);
                }
            });
        }
        return imports;
    }
    
    /**
     * Extract exports from content
     */
    private extractExportsFromContent(content: string): string[] {
        const exports: string[] = [];
        const exportMatches = content.match(/export\s+(?:default\s+)?(\w+)/g);
        if (exportMatches) {
            exportMatches.forEach(match => {
                const name = match.match(/export\s+(?:default\s+)?(\w+)/);
                if (name) {
                    exports.push(name[1]);
                }
            });
        }
        return exports;
    }
    
    /**
     * Build component templates from patterns
     */
    private async buildComponentTemplates(
        snippets: Record<string, CodeSnippet[]>, 
        patterns: Record<PatternType, DetectedPattern[]>
    ) {
        // Implementation for building templates from patterns
        return [];
    }
    
    /**
     * Identify best practices from patterns
     */
    private async identifyBestPractices(
        patterns: Record<PatternType, DetectedPattern[]>,
        snippets: Record<string, CodeSnippet[]>
    ) {
        // Implementation for identifying best practices
        return [];
    }
}