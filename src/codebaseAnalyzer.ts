import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as chokidar from 'chokidar';
import { 
    WorkspaceInfo, 
    ComponentInfo, 
    StylingInfo, 
    DependencyGraph,
    ComponentNode,
    DependencyEdge,
    ComponentCluster,
    GraphMetrics,
    CodePatterns,
    NamingConventions,
    StylePatterns,
    ArchitectureInfo,
    ComponentCategory
} from './types';
import { ASTAnalyzer } from './astAnalyzer';
import { ContextRanker } from './contextRanker';
import { AnalyzerUtils } from './analyzerUtils';
import { AdvancedPatternAnalyzer } from './advancedPatternAnalyzer';
import { DesignSystemAnalyzer } from './designSystemAnalyzer';
import { IntelligentContextSelector } from './intelligentContextSelector';

export class CodebaseAnalyzer {
    private astAnalyzer: ASTAnalyzer;
    private contextRanker: ContextRanker;
    private advancedPatternAnalyzer: AdvancedPatternAnalyzer;
    private designSystemAnalyzer: DesignSystemAnalyzer;
    private intelligentContextSelector: IntelligentContextSelector;
    private fileWatcher?: chokidar.FSWatcher;
    private analysisCache: Map<string, ComponentInfo> = new Map();
    private dependencyCache: Map<string, string[]> = new Map();
    private exampleLibraryCache?: import('./types').ExampleLibrary;
    private designSystemCache?: import('./types').DesignSystemAnalysis;
    private stateManagementCache?: import('./types').StateManagementAnalysis;
    private typeScriptCache?: import('./types').TypeScriptPatterns;
    
    constructor() {
        this.astAnalyzer = new ASTAnalyzer();
        this.contextRanker = new ContextRanker();
        this.advancedPatternAnalyzer = new AdvancedPatternAnalyzer();
        this.designSystemAnalyzer = new DesignSystemAnalyzer();
        this.intelligentContextSelector = new IntelligentContextSelector();
    }

    /**
     * Perform comprehensive workspace analysis with caching and real-time updates
     */
    async analyzeWorkspace(): Promise<WorkspaceInfo> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return this.getDefaultWorkspaceInfo();
        }

        const rootPath = workspaceFolder.uri.fsPath;
        
        console.log('🔍 Starting comprehensive codebase analysis...');
        
        // Parallel analysis for better performance
        const [
            hasTypeScript,
            styling,
            components,
            projectStructure
        ] = await Promise.all([
            this.detectTypeScript(rootPath),
            this.analyzeStyling(rootPath),
            this.findAndAnalyzeComponents(rootPath),
            this.analyzeProjectStructure(rootPath)
        ]);

        console.log(`📊 Found ${components.length} components for analysis`);

        // Advanced analysis
        const [dependencyGraph, patterns, architecture] = await Promise.all([
            this.buildDependencyGraph(components, rootPath),
            this.analyzeCodePatterns(components, rootPath),
            this.analyzeArchitecture(components, rootPath)
        ]);

        console.log('✅ Advanced codebase analysis complete');

        const workspaceInfo: WorkspaceInfo = {
            hasTypeScript,
            styling,
            existingComponents: components,
            projectStructure,
            dependencyGraph,
            patterns,
            architecture
        };

        // Start file watching for real-time updates
        this.startFileWatching(rootPath);

        return workspaceInfo;
    }

    /**
     * Find and perform lightweight analysis on React components (optimized)
     */
    private async findAndAnalyzeComponents(rootPath: string): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];
        const componentPaths = await this.findComponentFiles(rootPath);
        
        console.log(`🔍 Found ${componentPaths.length} component files for analysis`);
        
        // INCREASED LIMIT: Allow more components (user has 49 tsx files) 
        const maxComponents = 100; // Increased from 50
        const limitedPaths = componentPaths.slice(0, maxComponents);
        
        if (componentPaths.length > maxComponents) {
            console.log(`⚡ Limiting analysis to first ${maxComponents} components for performance`);
        } else {
            console.log(`📋 Analyzing all ${componentPaths.length} components found`);
        }
        
        // Process components with timeout protection
        const batchSize = 5;
        for (let i = 0; i < limitedPaths.length; i += batchSize) {
            const batch = limitedPaths.slice(i, i + batchSize);
            const batchPromises = batch.map(async (filePath) => {
                try {
                    // Add timeout to prevent hanging
                    return await Promise.race([
                        this.analyzeComponentFile(filePath, rootPath),
                        new Promise<null>((_, reject) => 
                            setTimeout(() => reject(new Error('Analysis timeout')), 5000)
                        )
                    ]);
                } catch (error) {
                    console.warn(`Failed to analyze ${filePath}:`, error);
                    return this.createBasicComponentInfo(filePath, rootPath);
                }
            });
            
            const batchResults = await Promise.all(batchPromises);
            components.push(...batchResults.filter(Boolean) as ComponentInfo[]);
            
            // Progress feedback
            console.log(`📈 Analyzed ${Math.min(i + batchSize, limitedPaths.length)}/${limitedPaths.length} components`);
        }
        
        console.log(`✅ Component analysis complete: ${components.length} components analyzed`);
        return components;
    }

    /**
     * Perform lightweight analysis of a single component file (optimized)
     */
    private async analyzeComponentFile(filePath: string, rootPath: string): Promise<ComponentInfo | null> {
        // Check cache first
        const cacheKey = `${filePath}:${fs.statSync(filePath).mtime.getTime()}`;
        if (this.analysisCache.has(cacheKey)) {
            return this.analysisCache.get(cacheKey)!;
        }

        try {
            // Try AST analysis with fallback to basic analysis
            let ast: import('./types').ComponentAST | null = null;
            
            try {
                ast = await this.astAnalyzer.analyzeComponent(filePath);
            } catch (astError) {
                console.warn(`AST analysis failed for ${filePath}, using basic analysis:`, astError);
            }
            
            const relativePath = path.relative(rootPath, filePath);
            const dependencies = await this.extractFileDependencies(filePath, rootPath);
            
            let componentInfo: ComponentInfo;
            
            if (ast) {
                // Full analysis with AST
                const category = this.astAnalyzer.categorizeComponent(ast);
                const complexity = this.categorizeComplexity(ast);
                
                componentInfo = {
                    name: ast.name,
                    path: relativePath,
                    description: this.generateComponentDescription(ast),
                    props: this.formatPropsString(ast.props),
                    ast,
                    dependencies,
                    complexity,
                    category
                };
            } else {
                // Basic analysis without AST
                componentInfo = this.createBasicComponentInfo(filePath, rootPath);
                componentInfo.dependencies = dependencies;
            }

            // Cache the result
            this.analysisCache.set(cacheKey, componentInfo);
            
            return componentInfo;
        } catch (error) {
            console.error(`Error analyzing component ${filePath}:`, error);
            // Final fallback to basic analysis
            return this.createBasicComponentInfo(filePath, rootPath);
        }
    }

    /**
     * Create basic component info when AST analysis fails
     */
    private createBasicComponentInfo(filePath: string, rootPath: string): ComponentInfo {
        const fileName = path.basename(filePath, path.extname(filePath));
        const relativePath = path.relative(rootPath, filePath);
        
        return {
            name: fileName,
            path: relativePath,
            description: `${fileName} component (basic analysis)`,
            props: '',
            dependencies: [],
            complexity: 'simple',
            category: 'utility'
        };
    }

    /**
     * Extract file dependencies and imports
     */
    private async extractFileDependencies(filePath: string, rootPath: string): Promise<string[]> {
        // Check cache
        if (this.dependencyCache.has(filePath)) {
            return this.dependencyCache.get(filePath)!;
        }

        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const dependencies: string[] = [];
            
            // Extract import statements
            const importRegex = /import\s+.*?\s+from\s+['"]([^'"]+)['"]/g;
            let match;
            
            while ((match = importRegex.exec(content)) !== null) {
                let importPath = match[1];
                
                // Resolve relative imports to absolute paths
                if (importPath.startsWith('.')) {
                    const resolvedPath = path.resolve(path.dirname(filePath), importPath);
                    const relativePath = path.relative(rootPath, resolvedPath);
                    dependencies.push(relativePath);
                } else {
                    // External dependency
                    dependencies.push(importPath);
                }
            }
            
            this.dependencyCache.set(filePath, dependencies);
            return dependencies;
        } catch (error) {
            console.error(`Error extracting dependencies from ${filePath}:`, error);
            return [];
        }
    }

    /**
     * Build comprehensive dependency graph
     */
    private async buildDependencyGraph(components: ComponentInfo[], rootPath: string): Promise<DependencyGraph> {
        console.log('🕸️ Building dependency graph...');
        
        const nodes: ComponentNode[] = [];
        const edges: DependencyEdge[] = [];
        const componentMap = new Map<string, ComponentInfo>();
        
        // Create nodes
        components.forEach(component => {
            componentMap.set(component.path, component);
            
            nodes.push({
                id: component.path,
                name: component.name,
                path: component.path,
                type: component.category || 'utility',
                weight: this.calculateNodeWeight(component),
                connections: 0 // Will be calculated later
            });
        });
        
        // Create edges
        components.forEach(component => {
            if (!component.dependencies) return;
            
            component.dependencies.forEach(dep => {
                const targetComponent = componentMap.get(dep);
                if (targetComponent) {
                    edges.push({
                        from: component.path,
                        to: dep,
                        type: 'import',
                        weight: 1
                    });
                }
            });
        });
        
        // Update connection counts
        const connectionCounts = new Map<string, number>();
        edges.forEach(edge => {
            connectionCounts.set(edge.from, (connectionCounts.get(edge.from) || 0) + 1);
            connectionCounts.set(edge.to, (connectionCounts.get(edge.to) || 0) + 1);
        });
        
        nodes.forEach(node => {
            node.connections = connectionCounts.get(node.id) || 0;
        });
        
        // Build clusters and calculate metrics
        const clusters = this.identifyComponentClusters(nodes, edges);
        const metrics = this.calculateGraphMetrics(nodes, edges);
        
        return {
            nodes,
            edges,
            clusters,
            metrics
        };
    }

    /**
     * Analyze code patterns across the codebase
     */
    private async analyzeCodePatterns(components: ComponentInfo[], rootPath: string): Promise<CodePatterns> {
        console.log('🔍 Analyzing code patterns...');
        
        const namingConventions = this.analyzeNamingConventions(components);
        const architecturalPatterns = this.identifyArchitecturalPatterns(components);
        const stylePatterns = this.analyzeStylePatterns(components);
        const stateManagementPatterns = this.analyzeStateManagementPatterns(components);
        const testingPatterns = await this.analyzeTestingPatterns(rootPath);
        
        return {
            namingConventions,
            architecturalPatterns,
            stylePatterns,
            stateManagementPatterns,
            testingPatterns
        };
    }

    /**
     * Analyze overall architecture
     */
    private async analyzeArchitecture(components: ComponentInfo[], rootPath: string): Promise<ArchitectureInfo> {
        console.log('🏗️ Analyzing architecture...');
        
        // Identify architectural patterns
        const patterns = this.identifyArchitecturalPatterns(components);
        
        // Analyze layering
        const layering = this.analyzeLayering(components);
        
        // Analyze component hierarchy
        const componentHierarchy = this.analyzeComponentHierarchy(components);
        
        // Analyze data flow
        const dataFlow = this.analyzeDataFlow(components);
        
        return {
            patterns,
            layering,
            componentHierarchy,
            dataFlow
        };
    }

    // Delegate utility methods to AnalyzerUtils
    private async findComponentFiles(rootPath: string): Promise<string[]> {
        return AnalyzerUtils.findComponentFiles(rootPath);
    }

    private generateComponentDescription(ast: import('./types').ComponentAST): string {
        return AnalyzerUtils.generateComponentDescription(ast);
    }

    private formatPropsString(props: import('./types').ComponentAST['props']): string {
        return AnalyzerUtils.formatPropsString(props);
    }

    private categorizeComplexity(ast: import('./types').ComponentAST): 'simple' | 'medium' | 'complex' {
        return AnalyzerUtils.categorizeComplexity(ast);
    }

    private calculateNodeWeight(component: ComponentInfo): number {
        return AnalyzerUtils.calculateNodeWeight(component);
    }

    private identifyComponentClusters(nodes: ComponentNode[], edges: DependencyEdge[]): ComponentCluster[] {
        return AnalyzerUtils.identifyComponentClusters(nodes, edges);
    }

    private calculateGraphMetrics(nodes: ComponentNode[], edges: DependencyEdge[]): GraphMetrics {
        return AnalyzerUtils.calculateGraphMetrics(nodes, edges);
    }

    private analyzeNamingConventions(components: ComponentInfo[]): NamingConventions {
        return AnalyzerUtils.analyzeNamingConventions(components);
    }

    private analyzeStylePatterns(components: ComponentInfo[]): StylePatterns {
        return AnalyzerUtils.analyzeStylePatterns(components);
    }

    // Implementation methods for advanced analysis
    private identifyArchitecturalPatterns(components: ComponentInfo[]): string[] {
        const patterns: string[] = [];
        
        // Detect common architectural patterns
        const hasContainerComponents = components.some(c => 
            c.name.includes('Container') || c.category === 'business-logic'
        );
        const hasPresentationalComponents = components.some(c => 
            c.category === 'ui-primitive' || c.category === 'data-display'
        );
        
        if (hasContainerComponents && hasPresentationalComponents) {
            patterns.push('container-presentational');
        }
        
        // Check for HOC pattern
        const hasHOCs = components.some(c => 
            c.name.startsWith('with') || c.description.includes('higher-order')
        );
        if (hasHOCs) {
            patterns.push('higher-order-components');
        }
        
        // Check for render props
        const hasRenderProps = components.some(c => 
            c.ast?.props.some(p => p.name.includes('render') || p.name.includes('children'))
        );
        if (hasRenderProps) {
            patterns.push('render-props');
        }
        
        // Check for hooks pattern
        const hasCustomHooks = components.some(c => 
            c.ast?.hooks.some(h => h.type === 'custom')
        );
        if (hasCustomHooks) {
            patterns.push('custom-hooks');
        }
        
        return patterns;
    }

    private analyzeStateManagementPatterns(components: ComponentInfo[]): string[] {
        const patterns: string[] = [];
        
        // Analyze hook usage patterns
        const allHooks = components.flatMap(c => c.ast?.hooks || []);
        const hookTypes = new Set(allHooks.map(h => h.name));
        
        if (hookTypes.has('useState')) patterns.push('local-state');
        if (hookTypes.has('useContext')) patterns.push('context-api');
        if (hookTypes.has('useReducer')) patterns.push('reducer-pattern');
        if (hookTypes.has('useCallback')) patterns.push('callback-optimization');
        if (hookTypes.has('useMemo')) patterns.push('memo-optimization');
        if (hookTypes.has('useEffect')) patterns.push('lifecycle-effects');
        
        // Modern state management detection
        const allDependencies = components.flatMap(c => c.dependencies || []);
        const depSet = new Set(allDependencies);
        
        // TanStack Query (React Query)
        if (depSet.has('@tanstack/react-query') || depSet.has('react-query')) {
            patterns.push('tanstack-query');
        }
        
        // TanStack Router
        if (depSet.has('@tanstack/react-router')) {
            patterns.push('tanstack-router');
        }
        
        // React Router
        if (depSet.has('react-router-dom') || depSet.has('react-router')) {
            patterns.push('react-router');
        }
        
        // Check for external state management
        if (depSet.has('redux') || depSet.has('@reduxjs/toolkit')) {
            patterns.push('redux');
        }
        
        if (depSet.has('zustand')) {
            patterns.push('zustand');
        }
        
        if (depSet.has('jotai')) {
            patterns.push('jotai');
        }
        
        if (depSet.has('recoil')) {
            patterns.push('recoil');
        }
        
        if (depSet.has('valtio')) {
            patterns.push('valtio');
        }
        
        // SWR for data fetching
        if (depSet.has('swr')) {
            patterns.push('swr');
        }
        
        // Analyze advanced patterns from component content
        components.forEach(component => {
            try {
                const filePath = path.resolve(component.path);
                if (fs.existsSync(filePath)) {
                    const content = fs.readFileSync(filePath, 'utf8');
                    
                    // Check for caching patterns
                    if (content.includes('localStorage') || content.includes('sessionStorage')) {
                        patterns.push('client-side-caching');
                    }
                    
                    // Check for Promise.race timeout patterns
                    if (content.includes('Promise.race')) {
                        patterns.push('promise-racing');
                    }
                    
                    // Check for loading state patterns
                    if (content.includes('LoadingState') || content.includes('loading')) {
                        patterns.push('loading-states');
                    }
                    
                    // Check for error boundary patterns
                    if (content.includes('error') && content.includes('useState')) {
                        patterns.push('error-handling');
                    }
                }
            } catch (error) {
                // Silently handle file reading errors
            }
        });
        
        return [...new Set(patterns)]; // Remove duplicates
    }

    private async analyzeTestingPatterns(rootPath: string): Promise<string[]> {
        const patterns: string[] = [];
        
        try {
            // Check for test files with broader patterns
            const testExtensions = [
                '.test.ts', '.test.tsx', '.test.js', '.test.jsx', 
                '.spec.ts', '.spec.tsx', '.spec.js', '.spec.jsx',
                '.e2e.ts', '.e2e.js'
            ];
            
            const testDirectories = ['tests', 'test', '__tests__', 'e2e', 'playwright'];
            let hasTests = false;
            let hasE2ETests = false;
            
            const checkForTests = (dirPath: string) => {
                const entries = fs.readdirSync(dirPath, { withFileTypes: true });
                for (const entry of entries) {
                    if (entry.isDirectory() && !['node_modules', '.git', 'dist', 'build'].includes(entry.name)) {
                        // Check for test directories
                        if (testDirectories.includes(entry.name.toLowerCase())) {
                            hasTests = true;
                            if (entry.name.toLowerCase().includes('e2e') || entry.name.toLowerCase().includes('playwright')) {
                                hasE2ETests = true;
                            }
                        }
                        checkForTests(path.join(dirPath, entry.name));
                    } else if (entry.isFile()) {
                        if (testExtensions.some(ext => entry.name.endsWith(ext))) {
                            hasTests = true;
                            if (entry.name.includes('e2e') || entry.name.includes('playwright')) {
                                hasE2ETests = true;
                            }
                        }
                    }
                }
            };
            
            checkForTests(rootPath);
            
            if (hasTests) {
                patterns.push('unit-testing');
            }
            
            if (hasE2ETests) {
                patterns.push('e2e-testing');
            }
            
            // Check package.json for testing libraries
            const packageJsonPath = path.join(rootPath, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
                
                // Unit testing frameworks
                if ('@testing-library/react' in allDeps) patterns.push('react-testing-library');
                if ('@testing-library/jest-dom' in allDeps) patterns.push('jest-dom');
                if ('jest' in allDeps) patterns.push('jest');
                if ('vitest' in allDeps) patterns.push('vitest');
                if ('mocha' in allDeps) patterns.push('mocha');
                if ('jasmine' in allDeps) patterns.push('jasmine');
                
                // E2E testing frameworks
                if ('playwright' in allDeps || '@playwright/test' in allDeps) {
                    patterns.push('playwright');
                    patterns.push('e2e-testing');
                }
                if ('cypress' in allDeps) {
                    patterns.push('cypress');
                    patterns.push('e2e-testing');
                }
                if ('puppeteer' in allDeps) patterns.push('puppeteer');
                if ('selenium-webdriver' in allDeps) patterns.push('selenium');
                
                // Additional testing utilities
                if ('@storybook/react' in allDeps) patterns.push('storybook');
                if ('msw' in allDeps) patterns.push('mock-service-worker');
                if ('jsdom' in allDeps) patterns.push('jsdom');
                if ('@testing-library/user-event' in allDeps) patterns.push('user-event-testing');
            }
            
            // Check for specific config files
            const configFiles = [
                'playwright.config.ts', 'playwright.config.js',
                'cypress.config.ts', 'cypress.config.js',
                'jest.config.js', 'jest.config.ts',
                'vitest.config.ts', 'vitest.config.js'
            ];
            
            configFiles.forEach(configFile => {
                if (fs.existsSync(path.join(rootPath, configFile))) {
                    const framework = configFile.split('.')[0];
                    if (!patterns.includes(framework)) {
                        patterns.push(framework);
                    }
                }
            });
            
        } catch (error) {
            console.warn('Error analyzing testing patterns:', error);
        }
        
        return [...new Set(patterns)]; // Remove duplicates
    }

    private analyzeLayering(components: ComponentInfo[]): import('./types').LayerInfo[] {
        const layers: import('./types').LayerInfo[] = [];
        
        // Group components by category/layer
        const layerMap = new Map<string, ComponentInfo[]>();
        
        components.forEach(component => {
            const layer = this.mapCategoryToLayer(component.category);
            if (!layerMap.has(layer)) {
                layerMap.set(layer, []);
            }
            layerMap.get(layer)!.push(component);
        });
        
        // Create layer info
        layerMap.forEach((comps, layerName) => {
            layers.push({
                name: layerName,
                components: comps.map(c => c.name),
                responsibilities: this.getLayerResponsibilities(layerName)
            });
        });
        
        return layers;
    }

    private mapCategoryToLayer(category?: ComponentCategory): string {
        const layerMap: Record<ComponentCategory, string> = {
            'page': 'Presentation Layer',
            'layout': 'Layout Layer',
            'ui-primitive': 'UI Components',
            'form': 'Form Layer',
            'data-display': 'Data Layer',
            'navigation': 'Navigation Layer',
            'feedback': 'Feedback Layer',
            'overlay': 'Overlay Layer',
            'business-logic': 'Business Logic',
            'utility': 'Utility Layer'
        };
        
        return category ? layerMap[category] : 'Utility Layer';
    }

    private getLayerResponsibilities(layerName: string): string[] {
        const responsibilities: Record<string, string[]> = {
            'Presentation Layer': ['Page layout', 'Route handling', 'User interface coordination'],
            'Layout Layer': ['Component arrangement', 'Responsive design', 'Grid systems'],
            'UI Components': ['Reusable elements', 'Visual consistency', 'User interactions'],
            'Form Layer': ['Data input', 'Validation', 'Form submission'],
            'Data Layer': ['Data presentation', 'List rendering', 'Table display'],
            'Navigation Layer': ['Routing', 'Menu systems', 'Breadcrumbs'],
            'Feedback Layer': ['User notifications', 'Loading states', 'Error messages'],
            'Overlay Layer': ['Modals', 'Dropdowns', 'Tooltips'],
            'Business Logic': ['Domain logic', 'State management', 'API integration'],
            'Utility Layer': ['Helper functions', 'Common utilities', 'Shared logic']
        };
        
        return responsibilities[layerName] || ['General purpose'];
    }

    private analyzeComponentHierarchy(components: ComponentInfo[]): import('./types').HierarchyInfo {
        const depths = components.map(c => c.ast?.complexity.depth || 1);
        const maxDepth = Math.max(...depths);
        
        // Calculate fan-out (number of dependencies per component)
        const fanOut: Record<string, number> = {};
        components.forEach(component => {
            fanOut[component.name] = component.dependencies?.length || 0;
        });
        
        // Determine abstraction levels
        const abstractionLevels = [
            'Page Level',
            'Container Level', 
            'Component Level',
            'Element Level'
        ];
        
        return {
            depth: maxDepth,
            fanOut,
            abstractionLevels
        };
    }

    private analyzeDataFlow(components: ComponentInfo[]): import('./types').DataFlowInfo {
        // Analyze state management approach
        const statePatterns = this.analyzeStateManagementPatterns(components);
        
        let stateManagement: import('./types').DataFlowInfo['stateManagement'] = 'local';
        if (statePatterns.includes('redux')) stateManagement = 'redux';
        else if (statePatterns.includes('zustand')) stateManagement = 'zustand';
        else if (statePatterns.includes('context-api')) stateManagement = 'context';
        else if (statePatterns.length > 1) stateManagement = 'mixed';
        
        // Check for prop drilling (many props being passed down)
        const propDrilling = components.some(c => 
            c.ast?.props.length && c.ast.props.length > 5
        );
        
        // Identify event patterns
        const eventPatterns = this.identifyEventPatterns(components);
        
        return {
            stateManagement,
            propDrilling,
            eventPatterns
        };
    }

    private identifyEventPatterns(components: ComponentInfo[]): string[] {
        const patterns: string[] = [];
        
        const allEventHandlers = components.flatMap(c => 
            c.ast?.jsx.interactivity.eventHandlers || []
        );
        
        if (allEventHandlers.includes('onClick')) patterns.push('click-handling');
        if (allEventHandlers.includes('onSubmit')) patterns.push('form-submission');
        if (allEventHandlers.some(h => h.includes('Key'))) patterns.push('keyboard-interaction');
        if (allEventHandlers.some(h => h.includes('Mouse'))) patterns.push('mouse-interaction');
        
        return patterns;
    }

    /**
     * Start file watching for real-time updates
     */
    private startFileWatching(rootPath: string): void {
        if (this.fileWatcher) {
            this.fileWatcher.close();
        }

        const watchPatterns = [
            path.join(rootPath, '**/*.{tsx,jsx,ts,js}'),
            path.join(rootPath, '**/package.json'),
            path.join(rootPath, '**/tsconfig.json')
        ];

        this.fileWatcher = chokidar.watch(watchPatterns, {
            ignored: /(^|[\/\\])\../, // ignore dotfiles
            persistent: true,
            ignoreInitial: true
        });

        this.fileWatcher
            .on('change', (filePath) => this.handleFileChange(filePath))
            .on('add', (filePath) => this.handleFileAdd(filePath))
            .on('unlink', (filePath) => this.handleFileDelete(filePath));

        console.log('👁️ Started file watching for real-time analysis updates');
    }

    private handleFileChange(filePath: string): void {
        console.log(`🔄 File changed: ${filePath}`);
        // Clear cache for changed file
        const cacheKeys = Array.from(this.analysisCache.keys());
        const relevantKeys = cacheKeys.filter(key => key.startsWith(filePath));
        relevantKeys.forEach(key => this.analysisCache.delete(key));
        this.dependencyCache.delete(filePath);
        
        // Clear advanced caches to trigger re-analysis
        this.clearAdvancedCaches();
    }

    private handleFileAdd(filePath: string): void {
        console.log(`➕ File added: ${filePath}`);
        // Clear advanced caches to trigger re-analysis
        this.clearAdvancedCaches();
    }

    private handleFileDelete(filePath: string): void {
        console.log(`🗑️ File deleted: ${filePath}`);
        // Remove from caches
        const cacheKeys = Array.from(this.analysisCache.keys());
        const relevantKeys = cacheKeys.filter(key => key.startsWith(filePath));
        relevantKeys.forEach(key => this.analysisCache.delete(key));
        this.dependencyCache.delete(filePath);
        
        // Clear advanced caches to trigger re-analysis
        this.clearAdvancedCaches();
    }

    /**
     * Get sophisticated intelligent context for component generation
     */
    async getIntelligentContext(prompt: string): Promise<import('./types').IntelligentContext> {
        console.log('🚀 Building sophisticated intelligent context...');
        
        // Get current workspace analysis
        const workspaceInfo = await this.analyzeWorkspace();
        
        // Build comprehensive analysis caches if not available
        if (!this.exampleLibraryCache) {
            console.log('📚 Building example library...');
            this.exampleLibraryCache = await this.advancedPatternAnalyzer.analyzeCodebasePatterns(
                workspaceInfo.existingComponents,
                vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ''
            );
        }
        
        if (!this.designSystemCache) {
            console.log('🎨 Analyzing design system...');
            this.designSystemCache = await this.designSystemAnalyzer.analyzeDesignSystem(
                workspaceInfo.existingComponents,
                vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || ''
            );
        }
        
        if (!this.stateManagementCache) {
            console.log('📊 Analyzing state management...');
            this.stateManagementCache = await this.analyzeAdvancedStateManagement(workspaceInfo.existingComponents);
        }
        
        if (!this.typeScriptCache) {
            console.log('📝 Analyzing TypeScript patterns...');
            this.typeScriptCache = await this.analyzeAdvancedTypeScriptPatterns(workspaceInfo.existingComponents);
        }
        
        // Use intelligent context selector to choose the best examples
        const intelligentContext = await this.intelligentContextSelector.selectIntelligentContext(
            prompt,
            workspaceInfo.existingComponents,
            this.exampleLibraryCache,
            this.designSystemCache,
            this.stateManagementCache,
            this.typeScriptCache
        );
        
        console.log(`✅ Intelligent context ready - Confidence: ${Math.round(intelligentContext.confidenceScore * 100)}%`);
        
        return intelligentContext;
    }
    
    /**
     * Analyze advanced state management patterns
     */
    private async analyzeAdvancedStateManagement(components: ComponentInfo[]): Promise<import('./types').StateManagementAnalysis> {
        const statePatterns = this.analyzeStateManagementPatterns(components);
        
        return {
            primary: this.determinePrimaryStateManagement(statePatterns),
            patterns: statePatterns.map(pattern => ({
                name: pattern,
                type: this.categorizeStatePattern(pattern),
                usage: this.getPatternUsage(pattern, components),
                examples: this.getPatternExamples(pattern, components)
            })),
            stores: [],
            reducers: [],
            contexts: []
        };
    }
    
    /**
     * Analyze advanced TypeScript patterns
     */
    private async analyzeAdvancedTypeScriptPatterns(components: ComponentInfo[]): Promise<import('./types').TypeScriptPatterns> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {
                strictMode: false,
                interfaceUsage: [],
                genericUsage: [],
                utilityTypes: [],
                customTypes: [],
                returnTypes: []
            };
        }
        
        const rootPath = workspaceFolder.uri.fsPath;
        const tsconfigPath = path.join(rootPath, 'tsconfig.json');
        
        let strictMode = false;
        if (fs.existsSync(tsconfigPath)) {
            try {
                const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf8'));
                strictMode = tsconfig.compilerOptions?.strict === true;
            } catch {
                // Ignore errors
            }
        }
        
        // Analyze interfaces and types from components
        const interfaceUsage = this.extractInterfaceUsage(components);
        const returnTypes = this.extractReturnTypePatterns(components);
        
        return {
            strictMode,
            interfaceUsage,
            genericUsage: [],
            utilityTypes: this.extractUtilityTypes(components),
            customTypes: [],
            returnTypes
        };
    }
    
    /**
     * Clear caches when files change
     */
    private clearAdvancedCaches(): void {
        this.exampleLibraryCache = undefined;
        this.designSystemCache = undefined;
        this.stateManagementCache = undefined;
        this.typeScriptCache = undefined;
    }
    
    // Helper methods for advanced analysis
    
    private determinePrimaryStateManagement(patterns: string[]): import('./types').StateManagementType {
        if (patterns.includes('redux')) return 'redux';
        if (patterns.includes('zustand')) return 'zustand';
        if (patterns.includes('context-api')) return 'context';
        if (patterns.includes('jotai')) return 'jotai';
        if (patterns.includes('recoil')) return 'recoil';
        if (patterns.length > 1) return 'mixed';
        return 'local';
    }
    
    private categorizeStatePattern(pattern: string): 'action' | 'selector' | 'middleware' | 'reducer' | 'hook' {
        if (pattern.includes('action')) return 'action';
        if (pattern.includes('selector')) return 'selector';
        if (pattern.includes('middleware')) return 'middleware';
        if (pattern.includes('reducer')) return 'reducer';
        return 'hook';
    }
    
    private getPatternUsage(pattern: string, components: ComponentInfo[]): number {
        return components.filter(c => 
            c.dependencies?.some(dep => dep.includes(pattern)) ||
            c.ast?.hooks.some(hook => hook.name.includes(pattern))
        ).length;
    }
    
    private getPatternExamples(pattern: string, components: ComponentInfo[]): string[] {
        const examples: string[] = [];
        components.forEach(component => {
            if (component.ast?.hooks) {
                component.ast.hooks.forEach(hook => {
                    if (hook.name.includes(pattern) && examples.length < 3) {
                        examples.push(`${component.name}: ${hook.name}`);
                    }
                });
            }
        });
        return examples;
    }
    
    private extractInterfaceUsage(components: ComponentInfo[]): import('./types').InterfaceUsage[] {
        const interfaces: import('./types').InterfaceUsage[] = [];
        
        components.forEach(component => {
            if (component.ast?.props && component.ast.props.length > 0) {
                interfaces.push({
                    name: `${component.name}Props`,
                    category: 'props',
                    complexity: component.ast.props.length,
                    usage: 1
                });
            }
        });
        
        return interfaces;
    }
    
    private extractReturnTypePatterns(components: ComponentInfo[]): import('./types').ReturnTypeAnalysis[] {
        const patterns: import('./types').ReturnTypeAnalysis[] = [];
        const returnTypeMap = new Map<string, number>();
        
        // This would require deeper AST analysis to extract actual return types
        // For now, we'll infer common patterns
        returnTypeMap.set('React.JSX.Element', 0);
        returnTypeMap.set('JSX.Element', 0);
        returnTypeMap.set('ReactNode', 0);
        
        components.forEach(component => {
            if (component.ast?.type === 'functional') {
                // Increment count for functional components (likely returning JSX.Element)
                returnTypeMap.set('React.JSX.Element', (returnTypeMap.get('React.JSX.Element') || 0) + 1);
            }
        });
        
        returnTypeMap.forEach((usage, pattern) => {
            if (usage > 0) {
                patterns.push({
                    pattern,
                    usage,
                    examples: [`${usage} components use ${pattern}`]
                });
            }
        });
        
        return patterns;
    }
    
    private extractUtilityTypes(components: ComponentInfo[]): string[] {
        const utilityTypes = new Set<string>();
        
        // This would require deeper analysis of actual TypeScript code
        // For now, return common utility types
        if (components.some(c => c.ast?.props.some(p => p.optional))) {
            utilityTypes.add('Partial');
        }
        
        return Array.from(utilityTypes);
    }

    private suggestPatterns(prompt: string, workspaceInfo: WorkspaceInfo): string[] {
        const suggestions: string[] = [];
        const existingPatterns = workspaceInfo.patterns?.architecturalPatterns || [];
        
        // Suggest based on prompt content
        if (prompt.includes('form') && existingPatterns.includes('custom-hooks')) {
            suggestions.push('Use custom hook for form logic like existing components');
        }
        
        if (prompt.includes('list') && existingPatterns.includes('render-props')) {
            suggestions.push('Consider render props pattern for list customization');
        }
        
        if (prompt.includes('state') && existingPatterns.includes('context-api')) {
            suggestions.push('Integrate with existing Context API pattern');
        }
        
        // Suggest based on styling patterns
        const stylePatterns = workspaceInfo.patterns?.stylePatterns;
        if (stylePatterns?.classNaming === 'BEM') {
            suggestions.push('Follow BEM naming convention for CSS classes');
        }
        
        return suggestions;
    }

    /**
     * Cleanup method to stop file watching
     */
    dispose(): void {
        if (this.fileWatcher) {
            this.fileWatcher.close();
            console.log('🛑 Stopped file watching');
        }
    }

    private async detectTypeScript(rootPath: string): Promise<boolean> {
        try {
            // Check for tsconfig.json
            const tsconfigPath = path.join(rootPath, 'tsconfig.json');
            if (fs.existsSync(tsconfigPath)) return true;
            
            // Check for TypeScript files
            const hasTypeScriptFiles = await this.hasTypeScriptFiles(rootPath);
            if (hasTypeScriptFiles) return true;
            
            // Check package.json for TypeScript dependencies
            const packageJsonPath = path.join(rootPath, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const allDeps = { 
                    ...packageJson.dependencies, 
                    ...packageJson.devDependencies 
                };
                
                if ('typescript' in allDeps || '@types/react' in allDeps) {
                    return true;
                }
            }
            
            return false;
        } catch {
            return false;
        }
    }
    
    private async hasTypeScriptFiles(rootPath: string): Promise<boolean> {
        try {
            const files = await this.findComponentFiles(rootPath);
            return files.some(file => file.endsWith('.ts') || file.endsWith('.tsx'));
        } catch {
            return false;
        }
    }

    private async analyzeStyling(rootPath: string): Promise<StylingInfo> {
        const styling: StylingInfo = {
            hasTailwind: false,
            hasStyledComponents: false,
            hasCSSModules: false,
            hasEmotion: false
        };

        try {
            const packageJsonPath = path.join(rootPath, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const allDeps = { 
                    ...packageJson.dependencies, 
                    ...packageJson.devDependencies 
                };

                styling.hasTailwind = 'tailwindcss' in allDeps;
                styling.hasStyledComponents = 'styled-components' in allDeps;
                styling.hasEmotion = '@emotion/react' in allDeps || '@emotion/styled' in allDeps;
                
                // Check for CSS modules
                styling.hasCSSModules = await this.hasModuleCSSFiles(rootPath);
                
                // Enhanced styling analysis
                styling.primaryApproach = this.determinePrimaryApproach(styling);
                styling.customTheme = this.detectCustomTheme(allDeps);
                styling.responsivePatterns = this.detectResponsivePatterns(allDeps);
                
                // Detect UI libraries and frameworks
                styling.uiLibrary = this.detectUILibrary(allDeps);
                styling.hasNextJS = 'next' in allDeps;
                styling.hasLucideIcons = 'lucide-react' in allDeps;
                styling.hasShadcnUI = this.detectShadcnUI(rootPath);
            }
        } catch (error) {
            console.error('Error analyzing styling:', error);
        }

        return styling;
    }

    private async analyzeProjectStructure(rootPath: string): Promise<string[]> {
        const structure: string[] = [];
        
        try {
            const commonDirs = ['src', 'components', 'pages', 'utils', 'hooks', 'context', 'lib', 'styles'];
            
            for (const dir of commonDirs) {
                const fullPath = path.join(rootPath, dir);
                if (fs.existsSync(fullPath)) {
                    structure.push(dir);
                }
            }
        } catch (error) {
            console.error('Error analyzing project structure:', error);
        }
        
        return structure;
    }

    // Helper methods for enhanced styling analysis
    private determinePrimaryApproach(styling: StylingInfo): StylingInfo['primaryApproach'] {
        if (styling.hasTailwind) return 'tailwind';
        if (styling.hasStyledComponents) return 'styled-components';
        if (styling.hasCSSModules) return 'css-modules';
        if (styling.hasEmotion) return 'emotion';
        return 'inline';
    }

    private detectCustomTheme(dependencies: Record<string, string>): boolean {
        return Boolean(
            dependencies['@mui/material'] ||
            dependencies['@chakra-ui/react'] ||
            dependencies['antd'] ||
            dependencies['theme-ui']
        );
    }

    private detectResponsivePatterns(dependencies: Record<string, string>): string[] {
        const patterns: string[] = [];
        
        if (dependencies['tailwindcss']) {
            patterns.push('responsive-classes', 'mobile-first');
        }
        
        if (dependencies['styled-components'] || dependencies['@emotion/styled']) {
            patterns.push('css-in-js-media-queries');
        }
        
        return patterns;
    }

    private detectUILibrary(dependencies: Record<string, string>): string {
        console.log('🔍 Detecting UI library from dependencies:', Object.keys(dependencies).filter(dep => 
            dep.includes('chakra') || dep.includes('ui') || dep.includes('@radix') || dep.includes('@mui')
        ));
        
        // PRIORITY FIX: Chakra UI detection (multiple detection methods)
        if (dependencies['@chakra-ui/react'] || 
            dependencies['@chakra-ui/next-js'] ||
            dependencies['@chakra-ui/core'] ||
            dependencies['@chakra-ui/system']) {
            
            const version = dependencies['@chakra-ui/react'];
            console.log('✅ Chakra UI detected! Version:', version);
            
            if (version && (version.startsWith('^3.') || version.startsWith('3.'))) {
                return 'Chakra UI v3';
            }
            return 'Chakra UI';
        }
        
        // shadcn/ui detection (multiple ways to detect)
        const shadcnIndicators = [
            '@radix-ui/react-slot',
            '@radix-ui/react-button', 
            '@radix-ui/react-dialog',
            'class-variance-authority',
            'clsx',
            'tailwind-merge'
        ];
        
        if (shadcnIndicators.some(indicator => dependencies[indicator])) {
            console.log('✅ shadcn/ui detected');
            return 'shadcn/ui';
        }
        
        // Material UI (MUI)
        if (dependencies['@mui/material'] || dependencies['@mui/x-data-grid']) {
            console.log('✅ Material-UI detected');
            return 'Material-UI (MUI)';
        }
        
        // Ant Design
        if (dependencies['antd']) {
            console.log('✅ Ant Design detected');
            return 'Ant Design';
        }
        
        // Mantine
        if (dependencies['@mantine/core'] || dependencies['@mantine/hooks']) {
            console.log('✅ Mantine detected');
            return 'Mantine';
        }
        
        // React Bootstrap
        if (dependencies['react-bootstrap'] || dependencies['bootstrap']) {
            console.log('✅ React Bootstrap detected');
            return 'React Bootstrap';
        }
        
        // Semantic UI
        if (dependencies['semantic-ui-react']) {
            console.log('✅ Semantic UI React detected');
            return 'Semantic UI React';
        }
        
        // Headless UI
        if (dependencies['@headlessui/react']) {
            console.log('✅ Headless UI detected');
            return 'Headless UI';
        }
        
        // Next UI
        if (dependencies['@nextui-org/react']) {
            console.log('✅ NextUI detected');
            return 'NextUI';
        }
        
        console.log('⚠️ No UI library detected');
        return 'Custom/None';
    }

    private detectShadcnUI(rootPath: string): boolean {
        try {
            // Check for shadcn/ui components folder
            const uiPath = path.join(rootPath, 'components', 'ui');
            if (fs.existsSync(uiPath)) {
                const uiFiles = fs.readdirSync(uiPath);
                return uiFiles.some(file => 
                    ['button.tsx', 'input.tsx', 'dialog.tsx'].includes(file)
                );
            }
            
            // Check for components.json (shadcn/ui config)
            const componentsJsonPath = path.join(rootPath, 'components.json');
            return fs.existsSync(componentsJsonPath);
        } catch {
            return false;
        }
    }

    private async hasModuleCSSFiles(rootPath: string): Promise<boolean> {
        try {
            const srcPath = path.join(rootPath, 'src');
            if (fs.existsSync(srcPath)) {
                return this.hasModuleCSSInDir(srcPath);
            }
        } catch {
            // Ignore errors
        }
        return false;
    }

    private hasModuleCSSInDir(dirPath: string): boolean {
        try {
            const files = fs.readdirSync(dirPath);
            
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    if (this.hasModuleCSSInDir(filePath)) {
                        return true;
                    }
                } else if (file.endsWith('.module.css')) {
                    return true;
                }
            }
        } catch {
            // Ignore errors
        }
        return false;
    }

    private getDefaultWorkspaceInfo(): WorkspaceInfo {
        return {
            hasTypeScript: true,
            styling: {
                hasTailwind: false,
                hasStyledComponents: false,
                hasCSSModules: false,
                hasEmotion: false,
                primaryApproach: 'inline',
                customTheme: false,
                responsivePatterns: []
            },
            existingComponents: [],
            projectStructure: ['src'],
            dependencyGraph: {
                nodes: [],
                edges: [],
                clusters: [],
                metrics: {
                    density: 0,
                    modularity: 0,
                    avgPathLength: 0,
                    centralityScores: {}
                }
            },
            patterns: {
                namingConventions: {
                    components: 'PascalCase',
                    files: 'PascalCase',
                    props: 'camelCase',
                    constants: 'UPPER_CASE'
                },
                architecturalPatterns: [],
                stylePatterns: {
                    classNaming: 'semantic',
                    organization: 'component-based',
                    responsiveStrategy: 'mobile-first'
                },
                stateManagementPatterns: [],
                testingPatterns: []
            },
            architecture: {
                patterns: [],
                layering: [],
                componentHierarchy: {
                    depth: 1,
                    fanOut: {},
                    abstractionLevels: ['Component Level']
                },
                dataFlow: {
                    stateManagement: 'local',
                    propDrilling: false,
                    eventPatterns: []
                }
            }
        };
    }
}
