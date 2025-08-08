/**
 * Project Analyzer
 * Analyzes workspace, project structure, and codebase for intelligence context
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { 
    WorkspaceInfo, 
    ProjectInfo, 
    CodebaseInfo, 
    ComponentInfo,
    HookInfo,
    UtilityInfo,
    TypeInfo,
    ProjectStructure,
    CodingConventions,
    PropDefinition,
    IntelligenceOptions
} from './types';

export class ProjectAnalyzer {
    
    /**
     * Analyze workspace-level information
     */
    async analyzeWorkspace(workspacePath: string): Promise<WorkspaceInfo> {
        try {
            const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(workspacePath));
            const folders = await this.getWorkspaceFolders(workspacePath);
            
            return {
                path: workspacePath,
                name: workspaceFolder?.name || path.basename(workspacePath),
                folders,
                settings: vscode.workspace.getConfiguration()
            };
        } catch (error) {
            console.warn('🧠 Workspace analysis failed:', error);
            return {
                path: workspacePath,
                folders: []
            };
        }
    }

    /**
     * Analyze project-level information
     */
    async analyzeProject(workspacePath: string): Promise<ProjectInfo> {
        try {
            console.log('🧠 Analyzing project structure...');

            const packageJson = await this.loadPackageJson(workspacePath);
            const tsConfig = await this.loadTsConfig(workspacePath);
            const structure = await this.analyzeProjectStructure(workspacePath);

            const framework = this.detectFramework(packageJson);
            const buildTool = this.detectBuildTool(packageJson);
            const packageManager = await this.detectPackageManager(workspacePath);

            return {
                framework,
                buildTool,
                packageManager,
                dependencies: packageJson?.dependencies || {},
                devDependencies: packageJson?.devDependencies || {},
                scripts: packageJson?.scripts || {},
                tsConfig,
                structure
            };
        } catch (error) {
            console.warn('🧠 Project analysis failed:', error);
            return this.getDefaultProjectInfo();
        }
    }

    /**
     * Analyze codebase for components, hooks, utilities, and patterns
     */
    async analyzeCodebase(workspacePath: string, options: IntelligenceOptions = {}): Promise<CodebaseInfo> {
        try {
            console.log('🧠 Analyzing codebase...');

            const analysisDepth = options.analysisDepth || 'medium';
            const focusAreas = options.focusAreas || ['components', 'patterns', 'conventions'];

            // Run analysis in parallel for performance
            const [components, hooks, utilities, types, conventions] = await Promise.all([
                focusAreas.includes('components') ? this.findComponents(workspacePath, analysisDepth) : [],
                focusAreas.includes('components') ? this.findHooks(workspacePath, analysisDepth) : [],
                this.findUtilities(workspacePath, analysisDepth),
                this.findTypes(workspacePath, analysisDepth),
                focusAreas.includes('conventions') ? this.analyzeCodingConventions(workspacePath) : this.getDefaultConventions()
            ]);

            return {
                components,
                hooks,
                utilities,
                types,
                patterns: [], // Will be filled by CodePatternRecognizer
                conventions
            };
        } catch (error) {
            console.warn('🧠 Codebase analysis failed:', error);
            return this.getDefaultCodebaseInfo();
        }
    }

    /**
     * Load and parse package.json
     */
    private async loadPackageJson(workspacePath: string): Promise<any> {
        try {
            const packageJsonPath = vscode.Uri.file(path.join(workspacePath, 'package.json'));
            const content = await vscode.workspace.fs.readFile(packageJsonPath);
            return JSON.parse(content.toString());
        } catch (error) {
            console.warn('🧠 Could not load package.json:', error);
            return null;
        }
    }

    /**
     * Load and parse tsconfig.json
     */
    private async loadTsConfig(workspacePath: string): Promise<any> {
        try {
            const tsConfigPath = vscode.Uri.file(path.join(workspacePath, 'tsconfig.json'));
            const content = await vscode.workspace.fs.readFile(tsConfigPath);
            return JSON.parse(content.toString());
        } catch (error) {
            // Try alternative locations
            const alternatives = ['tsconfig.app.json', 'tsconfig.base.json'];
            for (const alt of alternatives) {
                try {
                    const altPath = vscode.Uri.file(path.join(workspacePath, alt));
                    const content = await vscode.workspace.fs.readFile(altPath);
                    return JSON.parse(content.toString());
                } catch {}
            }
            return null;
        }
    }

    /**
     * Analyze project directory structure
     */
    private async analyzeProjectStructure(workspacePath: string): Promise<ProjectStructure> {
        const structure: ProjectStructure = {
            srcDir: 'src' // Default
        };

        try {
            // Check common directory patterns
            const directories = ['src', 'app', 'lib', 'components', 'pages', 'utils', 'styles', 'public', '__tests__', 'test', 'tests'];
            
            for (const dir of directories) {
                try {
                    const dirPath = vscode.Uri.file(path.join(workspacePath, dir));
                    const stat = await vscode.workspace.fs.stat(dirPath);
                    
                    if (stat.type === vscode.FileType.Directory) {
                        switch (dir) {
                            case 'src':
                            case 'app':
                                structure.srcDir = dir;
                                break;
                            case 'components':
                                structure.componentsDir = dir;
                                break;
                            case 'pages':
                                structure.pagesDir = dir;
                                break;
                            case 'lib':
                                structure.libDir = dir;
                                break;
                            case 'utils':
                                structure.utilsDir = dir;
                                break;
                            case 'styles':
                                structure.stylesDir = dir;
                                break;
                            case 'public':
                                structure.publicDir = dir;
                                break;
                            case '__tests__':
                            case 'test':
                            case 'tests':
                                structure.testsDir = dir;
                                break;
                        }
                    }
                } catch {
                    // Directory doesn't exist, continue
                }
            }

            // Check for nested components directory
            if (!structure.componentsDir && structure.srcDir) {
                try {
                    const srcComponentsPath = vscode.Uri.file(path.join(workspacePath, structure.srcDir, 'components'));
                    await vscode.workspace.fs.stat(srcComponentsPath);
                    structure.componentsDir = path.join(structure.srcDir, 'components');
                } catch {}
            }

        } catch (error) {
            console.warn('🧠 Project structure analysis failed:', error);
        }

        return structure;
    }

    /**
     * Find React components in the codebase
     */
    private async findComponents(workspacePath: string, depth: 'shallow' | 'medium' | 'deep'): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];
        
        try {
            // Find component files
            const componentPattern = new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx}');
            const excludePattern = '**/node_modules/**';
            const maxFiles = depth === 'shallow' ? 20 : depth === 'medium' ? 50 : 100;
            
            const files = await vscode.workspace.findFiles(componentPattern, excludePattern, maxFiles);

            for (const file of files) {
                try {
                    const componentInfo = await this.analyzeComponentFile(file);
                    if (componentInfo) {
                        components.push(componentInfo);
                    }
                } catch (error) {
                    console.warn(`🧠 Failed to analyze component ${file.fsPath}:`, error);
                }
            }

            console.log(`🧠 Found ${components.length} components`);
        } catch (error) {
            console.warn('🧠 Component search failed:', error);
        }

        return components;
    }

    /**
     * Analyze individual component file
     */
    private async analyzeComponentFile(fileUri: vscode.Uri): Promise<ComponentInfo | null> {
        try {
            const content = await vscode.workspace.fs.readFile(fileUri);
            const text = content.toString();
            
            const fileName = path.basename(fileUri.fsPath, path.extname(fileUri.fsPath));
            
            // Skip non-component files based on patterns
            if (!this.looksLikeComponent(text, fileName)) {
                return null;
            }

            // Basic component analysis
            const componentType = this.detectComponentType(text);
            const props = this.extractProps(text);
            const hooks = this.extractHooks(text);
            const dependencies = this.extractDependencies(text);
            const stylingApproach = this.detectStylingApproach(text);
            const complexity = this.assessComplexity(text, props.length, hooks.length);

            return {
                name: fileName,
                path: vscode.workspace.asRelativePath(fileUri),
                type: componentType,
                props,
                hooks,
                dependencies,
                stylingApproach,
                complexity
            };
        } catch (error) {
            console.warn(`🧠 Component analysis failed for ${fileUri.fsPath}:`, error);
            return null;
        }
    }

    /**
     * Check if file looks like a React component
     */
    private looksLikeComponent(content: string, fileName: string): boolean {
        // Component name pattern (PascalCase)
        const isPascalCase = /^[A-Z][a-zA-Z0-9]*$/.test(fileName);
        
        // Component patterns
        const hasReactImport = /import.*React/.test(content);
        const hasJSXReturn = /return\s*\(?\s*</.test(content);
        const hasExportDefault = /export\s+default/.test(content);
        const hasExportNamed = new RegExp(`export.*${fileName}`).test(content);
        const hasFunctionComponent = new RegExp(`(function|const|let)\\s+${fileName}`).test(content);
        
        // Exclude utility files
        const isUtility = /\.(util|utils|helper|helpers|lib|config|constant|constants)\./i.test(fileName);
        
        return isPascalCase && 
               (hasReactImport || hasJSXReturn) && 
               (hasExportDefault || hasExportNamed || hasFunctionComponent) &&
               !isUtility;
    }

    /**
     * Detect component type (functional, class, forwardRef)
     */
    private detectComponentType(content: string): 'functional' | 'class' | 'forwardRef' {
        if (/React\.forwardRef|forwardRef/.test(content)) {
            return 'forwardRef';
        }
        if (/class.*extends.*Component/.test(content)) {
            return 'class';
        }
        return 'functional';
    }

    /**
     * Extract component props from TypeScript interfaces
     */
    private extractProps(content: string): PropDefinition[] {
        const props: PropDefinition[] = [];
        
        // Look for Props interfaces
        const propsInterfaceRegex = /interface\s+\w*Props\s*\{([^}]*)\}/gs;
        let match;
        
        while ((match = propsInterfaceRegex.exec(content)) !== null) {
            const propsContent = match[1];
            const propLines = propsContent.split('\n').filter(line => line.trim());
            
            for (const line of propLines) {
                const propMatch = line.match(/(\w+)(\??):\s*([^;]+)/);
                if (propMatch) {
                    const [, name, optional, type] = propMatch;
                    props.push({
                        name: name.trim(),
                        type: type.trim(),
                        required: !optional,
                        description: this.extractPropComment(content, name)
                    });
                }
            }
        }
        
        return props;
    }

    /**
     * Extract JSDoc comment for a prop
     */
    private extractPropComment(content: string, propName: string): string | undefined {
        const commentRegex = new RegExp(`\\/\\*\\*([^*]|\\*(?!\\/))*\\*\\/\\s*${propName}`, 'g');
        const match = commentRegex.exec(content);
        if (match) {
            return match[0].replace(/\/\*\*|\*\/|\*/g, '').trim();
        }
        return undefined;
    }

    /**
     * Extract React hooks used in component
     */
    private extractHooks(content: string): string[] {
        const hooks: Set<string> = new Set();
        
        // Built-in React hooks
        const builtinHooks = ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo', 'useRef', 'useImperativeHandle', 'useLayoutEffect', 'useDebugValue'];
        
        builtinHooks.forEach(hook => {
            if (new RegExp(`\\b${hook}\\b`).test(content)) {
                hooks.add(hook);
            }
        });
        
        // Custom hooks (functions starting with 'use')
        const customHookRegex = /\buse[A-Z]\w*\b/g;
        let match;
        while ((match = customHookRegex.exec(content)) !== null) {
            hooks.add(match[0]);
        }
        
        return Array.from(hooks);
    }

    /**
     * Extract import dependencies
     */
    private extractDependencies(content: string): string[] {
        const dependencies: Set<string> = new Set();
        
        const importRegex = /import.*from\s+['"`]([^'"`]+)['"`]/g;
        let match;
        
        while ((match = importRegex.exec(content)) !== null) {
            const dep = match[1];
            // Skip relative imports
            if (!dep.startsWith('.') && !dep.startsWith('/')) {
                dependencies.add(dep.split('/')[0]); // Get package name
            }
        }
        
        return Array.from(dependencies);
    }

    /**
     * Detect styling approach used
     */
    private detectStylingApproach(content: string): 'tailwind' | 'css' | 'styled-components' | 'emotion' | 'other' {
        if (/className.*\b(bg-|text-|p-|m-|flex|grid)/i.test(content)) {
            return 'tailwind';
        }
        if (/styled\.|styled\(/i.test(content)) {
            return 'styled-components';
        }
        if (/@emotion|css`/.test(content)) {
            return 'emotion';
        }
        if (/\.module\.css|styles\./i.test(content)) {
            return 'css';
        }
        return 'other';
    }

    /**
     * Assess component complexity
     */
    private assessComplexity(content: string, propsCount: number, hooksCount: number): 'simple' | 'medium' | 'complex' {
        const lineCount = content.split('\n').length;
        const functionCount = (content.match(/function\s+\w+/g) || []).length;
        const conditionalCount = (content.match(/if\s*\(|switch\s*\(|\?\s*:/g) || []).length;
        
        const complexityScore = lineCount * 0.1 + propsCount * 2 + hooksCount * 3 + functionCount * 2 + conditionalCount * 1.5;
        
        if (complexityScore > 100) return 'complex';
        if (complexityScore > 50) return 'medium';
        return 'simple';
    }

    /**
     * Find custom hooks in the codebase
     */
    private async findHooks(workspacePath: string, depth: 'shallow' | 'medium' | 'deep'): Promise<HookInfo[]> {
        const hooks: HookInfo[] = [];
        
        try {
            const hookPattern = new vscode.RelativePattern(workspacePath, '**/use*.{ts,tsx,js,jsx}');
            const excludePattern = '**/node_modules/**';
            const maxFiles = depth === 'shallow' ? 10 : depth === 'medium' ? 25 : 50;
            
            const files = await vscode.workspace.findFiles(hookPattern, excludePattern, maxFiles);
            
            for (const file of files) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    const text = content.toString();
                    const fileName = path.basename(file.fsPath, path.extname(file.fsPath));
                    
                    if (this.looksLikeCustomHook(text, fileName)) {
                        hooks.push({
                            name: fileName,
                            path: vscode.workspace.asRelativePath(file),
                            type: 'custom',
                            usage: this.extractHookUsage(text),
                            dependencies: this.extractDependencies(text)
                        });
                    }
                } catch (error) {
                    console.warn(`🧠 Failed to analyze hook ${file.fsPath}:`, error);
                }
            }
            
        } catch (error) {
            console.warn('🧠 Hook search failed:', error);
        }
        
        return hooks;
    }

    /**
     * Check if file looks like a custom hook
     */
    private looksLikeCustomHook(content: string, fileName: string): boolean {
        return fileName.startsWith('use') && 
               fileName.length > 3 && 
               /^use[A-Z]/.test(fileName) &&
               /export.*function|export.*const/.test(content);
    }

    /**
     * Extract hook usage patterns
     */
    private extractHookUsage(content: string): string[] {
        const usage: Set<string> = new Set();
        
        // Look for React hooks used
        const builtinHooks = ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo', 'useRef'];
        builtinHooks.forEach(hook => {
            if (new RegExp(`\\b${hook}\\b`).test(content)) {
                usage.add(hook);
            }
        });
        
        return Array.from(usage);
    }

    /**
     * Find utility functions
     */
    private async findUtilities(workspacePath: string, depth: 'shallow' | 'medium' | 'deep'): Promise<UtilityInfo[]> {
        const utilities: UtilityInfo[] = [];
        
        try {
            const utilPattern = new vscode.RelativePattern(workspacePath, '**/{utils,util,helpers,helper,lib}/**/*.{ts,tsx,js,jsx}');
            const excludePattern = '**/node_modules/**';
            const maxFiles = depth === 'shallow' ? 15 : depth === 'medium' ? 30 : 60;
            
            const files = await vscode.workspace.findFiles(utilPattern, excludePattern, maxFiles);
            
            for (const file of files) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    const text = content.toString();
                    const fileName = path.basename(file.fsPath, path.extname(file.fsPath));
                    
                    utilities.push({
                        name: fileName,
                        path: vscode.workspace.asRelativePath(file),
                        type: this.detectUtilityType(text),
                        usage: this.extractUtilityUsage(text),
                        dependencies: this.extractDependencies(text)
                    });
                } catch (error) {
                    console.warn(`🧠 Failed to analyze utility ${file.fsPath}:`, error);
                }
            }
        } catch (error) {
            console.warn('🧠 Utility search failed:', error);
        }
        
        return utilities;
    }

    /**
     * Detect type of utility (function, class, constant)
     */
    private detectUtilityType(content: string): 'function' | 'class' | 'constant' {
        if (/export\s+(function|const\s+\w+\s*=\s*\([^)]*\)\s*=>)/.test(content)) {
            return 'function';
        }
        if (/export\s+(class|default\s+class)/.test(content)) {
            return 'class';
        }
        return 'constant';
    }

    /**
     * Extract utility usage patterns
     */
    private extractUtilityUsage(content: string): string[] {
        const usage: string[] = [];
        
        // This is a simplified analysis - in a real implementation,
        // you'd use AST parsing for more accurate results
        if (/fetch|axios|http/i.test(content)) usage.push('api');
        if (/format|parse|validate/i.test(content)) usage.push('data-processing');
        if (/localStorage|sessionStorage/i.test(content)) usage.push('storage');
        if (/date|time/i.test(content)) usage.push('datetime');
        
        return usage;
    }

    /**
     * Find TypeScript type definitions
     */
    private async findTypes(workspacePath: string, depth: 'shallow' | 'medium' | 'deep'): Promise<TypeInfo[]> {
        const types: TypeInfo[] = [];
        
        try {
            const typePattern = new vscode.RelativePattern(workspacePath, '**/{types,@types}/**/*.{ts,d.ts}');
            const excludePattern = '**/node_modules/**';
            const maxFiles = depth === 'shallow' ? 10 : depth === 'medium' ? 20 : 40;
            
            const files = await vscode.workspace.findFiles(typePattern, excludePattern, maxFiles);
            
            for (const file of files) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    const text = content.toString();
                    const fileName = path.basename(file.fsPath, path.extname(file.fsPath));
                    
                    // Extract type definitions (simplified)
                    const typeMatches = text.match(/(?:export\s+)?(?:interface|type|enum)\s+(\w+)/g);
                    if (typeMatches) {
                        for (const match of typeMatches) {
                            const nameMatch = match.match(/(?:interface|type|enum)\s+(\w+)/);
                            if (nameMatch) {
                                types.push({
                                    name: nameMatch[1],
                                    path: vscode.workspace.asRelativePath(file),
                                    type: this.detectTypeDefinitionType(match),
                                    definition: match,
                                    usage: []
                                });
                            }
                        }
                    }
                } catch (error) {
                    console.warn(`🧠 Failed to analyze types ${file.fsPath}:`, error);
                }
            }
        } catch (error) {
            console.warn('🧠 Types search failed:', error);
        }
        
        return types;
    }

    /**
     * Detect type definition type
     */
    private detectTypeDefinitionType(definition: string): 'interface' | 'type' | 'enum' | 'class' {
        if (definition.includes('interface')) return 'interface';
        if (definition.includes('enum')) return 'enum';
        if (definition.includes('class')) return 'class';
        return 'type';
    }

    /**
     * Analyze coding conventions used in the project
     */
    private async analyzeCodingConventions(workspacePath: string): Promise<CodingConventions> {
        try {
            // Sample files to analyze conventions
            const sampleFiles = await this.getSampleFiles(workspacePath, 10);
            
            let componentNaming: 'PascalCase' | 'camelCase' | 'kebab-case' = 'PascalCase';
            let fileNaming: 'PascalCase' | 'camelCase' | 'kebab-case' = 'camelCase';
            let variableNaming: 'camelCase' | 'snake_case' = 'camelCase';
            let stylingApproach: 'tailwind' | 'css-modules' | 'styled-components' | 'emotion' | 'mixed' = 'mixed';
            
            // Analyze naming patterns from sample files
            const namingPatterns = await this.analyzeNamingPatterns(sampleFiles);
            componentNaming = namingPatterns.components;
            fileNaming = namingPatterns.files;
            variableNaming = namingPatterns.variables;
            
            // Analyze styling approach
            const stylingPatterns = await this.analyzeStylingPatterns(sampleFiles);
            stylingApproach = stylingPatterns.approach;

            return {
                naming: {
                    components: componentNaming,
                    files: fileNaming,
                    variables: variableNaming
                },
                structure: {
                    fileOrganization: 'mixed', // Would need deeper analysis
                    importStyle: 'mixed',
                    exportStyle: 'mixed'
                },
                styling: {
                    approach: stylingApproach,
                    conventions: stylingPatterns.conventions
                }
            };
        } catch (error) {
            console.warn('🧠 Convention analysis failed:', error);
            return this.getDefaultConventions();
        }
    }

    /**
     * Get sample files for convention analysis
     */
    private async getSampleFiles(workspacePath: string, count: number): Promise<vscode.Uri[]> {
        const pattern = new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx,ts,js}');
        const exclude = '**/node_modules/**';
        return vscode.workspace.findFiles(pattern, exclude, count);
    }

    /**
     * Analyze naming patterns from files
     */
    private async analyzeNamingPatterns(files: vscode.Uri[]): Promise<{
        components: 'PascalCase' | 'camelCase' | 'kebab-case';
        files: 'PascalCase' | 'camelCase' | 'kebab-case';
        variables: 'camelCase' | 'snake_case';
    }> {
        let pascalCaseCount = 0;
        let camelCaseCount = 0;
        let kebabCaseCount = 0;

        for (const file of files) {
            const fileName = path.basename(file.fsPath, path.extname(file.fsPath));
            
            if (/^[A-Z][a-zA-Z0-9]*$/.test(fileName)) pascalCaseCount++;
            else if (/^[a-z][a-zA-Z0-9]*$/.test(fileName)) camelCaseCount++;
            else if (/^[a-z][a-z0-9-]*$/.test(fileName)) kebabCaseCount++;
        }

        const predominantFileNaming: 'PascalCase' | 'camelCase' | 'kebab-case' = 
            pascalCaseCount > camelCaseCount && pascalCaseCount > kebabCaseCount ? 'PascalCase' :
            camelCaseCount > kebabCaseCount ? 'camelCase' : 'kebab-case';

        return {
            components: 'PascalCase', // React components are typically PascalCase
            files: predominantFileNaming,
            variables: 'camelCase' // JavaScript/TypeScript standard
        };
    }

    /**
     * Analyze styling patterns from files
     */
    private async analyzeStylingPatterns(files: vscode.Uri[]): Promise<{
        approach: 'tailwind' | 'css-modules' | 'styled-components' | 'emotion' | 'mixed';
        conventions: string[];
    }> {
        const stylingCounts = {
            tailwind: 0,
            'css-modules': 0,
            'styled-components': 0,
            emotion: 0,
            other: 0
        };

        const conventions: Set<string> = new Set();

        for (const file of files) {
            try {
                const content = await vscode.workspace.fs.readFile(file);
                const text = content.toString();

                if (/className.*\b(bg-|text-|p-|m-|flex|grid)/i.test(text)) {
                    stylingCounts.tailwind++;
                    conventions.add('Tailwind CSS utility classes');
                }
                if (/styled\.|styled\(/i.test(text)) {
                    stylingCounts['styled-components']++;
                    conventions.add('Styled Components');
                }
                if (/@emotion|css`/.test(text)) {
                    stylingCounts.emotion++;
                    conventions.add('Emotion CSS-in-JS');
                }
                if (/\.module\.css|styles\./i.test(text)) {
                    stylingCounts['css-modules']++;
                    conventions.add('CSS Modules');
                }
            } catch (error) {
                // Skip files that can't be read
            }
        }

        const maxCount = Math.max(...Object.values(stylingCounts));
        const predominantApproach = Object.entries(stylingCounts).find(([, count]) => count === maxCount)?.[0] as any || 'mixed';

        return {
            approach: predominantApproach,
            conventions: Array.from(conventions)
        };
    }

    /**
     * Helper methods for defaults
     */
    private detectFramework(packageJson: any): string {
        if (!packageJson?.dependencies && !packageJson?.devDependencies) return 'Unknown';
        
        const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
        
        if (deps.next) return 'Next.js';
        if (deps.vite) return 'Vite + React';
        if (deps.react) return 'React';
        if (deps.vue) return 'Vue.js';
        if (deps.svelte) return 'Svelte';
        if (deps.angular) return 'Angular';
        
        return 'Unknown';
    }

    private detectBuildTool(packageJson: any): string {
        const deps = { ...packageJson?.dependencies, ...packageJson?.devDependencies };
        
        if (deps.vite) return 'Vite';
        if (deps.webpack) return 'Webpack';
        if (deps.parcel) return 'Parcel';
        if (deps.rollup) return 'Rollup';
        if (packageJson?.scripts?.build) return 'npm scripts';
        
        return 'Unknown';
    }

    private async detectPackageManager(workspacePath: string): Promise<string> {
        try {
            // Check for lock files
            const lockFiles = ['pnpm-lock.yaml', 'yarn.lock', 'package-lock.json'];
            
            for (const lockFile of lockFiles) {
                try {
                    await vscode.workspace.fs.stat(vscode.Uri.file(path.join(workspacePath, lockFile)));
                    if (lockFile === 'pnpm-lock.yaml') return 'pnpm';
                    if (lockFile === 'yarn.lock') return 'yarn';
                    if (lockFile === 'package-lock.json') return 'npm';
                } catch {}
            }
        } catch {}
        
        return 'npm'; // Default
    }

    private async getWorkspaceFolders(workspacePath: string): Promise<string[]> {
        try {
            const folders: string[] = [];
            const entries = await vscode.workspace.fs.readDirectory(vscode.Uri.file(workspacePath));
            
            for (const [name, type] of entries) {
                if (type === vscode.FileType.Directory && !name.startsWith('.') && name !== 'node_modules') {
                    folders.push(name);
                }
            }
            
            return folders;
        } catch {
            return [];
        }
    }

    private getDefaultProjectInfo(): ProjectInfo {
        return {
            framework: 'Unknown',
            buildTool: 'Unknown',
            packageManager: 'npm',
            dependencies: {},
            devDependencies: {},
            scripts: {},
            structure: {
                srcDir: 'src'
            }
        };
    }

    private getDefaultCodebaseInfo(): CodebaseInfo {
        return {
            components: [],
            hooks: [],
            utilities: [],
            types: [],
            patterns: [],
            conventions: this.getDefaultConventions()
        };
    }

    private getDefaultConventions(): CodingConventions {
        return {
            naming: {
                components: 'PascalCase',
                files: 'camelCase',
                variables: 'camelCase'
            },
            structure: {
                fileOrganization: 'mixed',
                importStyle: 'mixed',
                exportStyle: 'mixed'
            },
            styling: {
                approach: 'mixed',
                conventions: []
            }
        };
    }
}