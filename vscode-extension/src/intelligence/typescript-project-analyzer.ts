/**
 * Pure TypeScript Project Analyzer
 * Replaces Python backend with native VS Code extension analysis
 */

import * as vscode from 'vscode';
import * as path from 'path';

export enum ComponentType {
    UI_LIBRARY = 'ui_library',
    PAGE = 'page',
    FEATURE = 'feature',
    LAYOUT = 'layout',
    HOOK = 'hook',
    UTILITY = 'utility',
    UNKNOWN = 'unknown'
}

export interface ComponentInfo {
    name: string;
    filePath: string;
    componentType: ComponentType;
    exports: string[];
    imports: string[];
    props: string[];
    dependencies: string[];
    isTypeScript: boolean;
    hasTailwind: boolean;
    lineCount: number;
    complexityScore: number;
}

export interface ProjectStructure {
    framework: string;
    buildTool: string;
    packageManager: string;
    hasTypeScript: boolean;
    hasTailwind: boolean;
    hasShadcnUI: boolean;
    components: ComponentInfo[];
    pages: string[];
    routes: string[];
    designTokens: Record<string, any>;
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
}

export class TypeScriptProjectAnalyzer {
    private workspaceFolder: vscode.WorkspaceFolder;
    private srcPath: string;
    private componentsPath: string;
    private uiComponentsPath: string;

    constructor(workspaceFolder: vscode.WorkspaceFolder) {
        this.workspaceFolder = workspaceFolder;
        this.srcPath = path.join(workspaceFolder.uri.fsPath, 'src');
        this.componentsPath = path.join(this.srcPath, 'components');
        this.uiComponentsPath = path.join(this.componentsPath, 'ui');
    }

    async analyzeProject(): Promise<ProjectStructure> {
        console.log('🔍 Starting pure TypeScript project analysis...');

        const [
            framework,
            buildTool,
            packageManager,
            hasTypeScript,
            hasTailwind,
            hasShadcnUI,
            components,
            pages,
            routes,
            designTokens,
            { dependencies, devDependencies }
        ] = await Promise.all([
            this.detectFramework(),
            this.detectBuildTool(),
            this.detectPackageManager(),
            this.detectTypeScript(),
            this.detectTailwind(),
            this.detectShadcnUI(),
            this.analyzeComponents(),
            this.analyzePages(),
            this.analyzeRoutes(),
            this.extractDesignTokens(),
            this.analyzeDependencies()
        ]);

        return {
            framework,
            buildTool,
            packageManager,
            hasTypeScript,
            hasTailwind,
            hasShadcnUI,
            components,
            pages,
            routes,
            designTokens,
            dependencies,
            devDependencies
        };
    }

    private async detectFramework(): Promise<string> {
        const packageJson = await this.readPackageJson();
        if (!packageJson) return 'unknown';

        const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };

        if ('next' in allDeps) return 'nextjs';
        if ('vite' in allDeps && 'react' in allDeps) return 'vite-react';
        if ('react' in allDeps) return 'react';
        if ('vue' in allDeps) return 'vue';
        if ('svelte' in allDeps) return 'svelte';

        return 'unknown';
    }

    private async detectBuildTool(): Promise<string> {
        const rootPath = this.workspaceFolder.uri.fsPath;
        
        if (await this.fileExists(path.join(rootPath, 'vite.config.ts')) || 
            await this.fileExists(path.join(rootPath, 'vite.config.js'))) {
            return 'vite';
        }
        if (await this.fileExists(path.join(rootPath, 'next.config.js')) ||
            await this.fileExists(path.join(rootPath, 'next.config.ts'))) {
            return 'nextjs';
        }
        if (await this.fileExists(path.join(rootPath, 'webpack.config.js'))) {
            return 'webpack';
        }

        return 'unknown';
    }

    private async detectPackageManager(): Promise<string> {
        const rootPath = this.workspaceFolder.uri.fsPath;
        
        if (await this.fileExists(path.join(rootPath, 'pnpm-lock.yaml'))) return 'pnpm';
        if (await this.fileExists(path.join(rootPath, 'yarn.lock'))) return 'yarn';
        if (await this.fileExists(path.join(rootPath, 'package-lock.json'))) return 'npm';

        return 'npm';
    }

    private async detectTypeScript(): Promise<boolean> {
        const rootPath = this.workspaceFolder.uri.fsPath;
        
        // Check for tsconfig.json
        if (await this.fileExists(path.join(rootPath, 'tsconfig.json'))) {
            return true;
        }

        // Check for .ts or .tsx files
        try {
            const files = await vscode.workspace.findFiles(
                new vscode.RelativePattern(this.workspaceFolder, '**/*.{ts,tsx}'),
                new vscode.RelativePattern(this.workspaceFolder, '**/node_modules/**'),
                5 // Limit to 5 files for performance
            );
            return files.length > 0;
        } catch {
            return false;
        }
    }

    private async detectTailwind(): Promise<boolean> {
        const packageJson = await this.readPackageJson();
        if (packageJson) {
            const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
            if ('tailwindcss' in allDeps) return true;
        }

        const rootPath = this.workspaceFolder.uri.fsPath;
        return (
            await this.fileExists(path.join(rootPath, 'tailwind.config.js')) ||
            await this.fileExists(path.join(rootPath, 'tailwind.config.ts'))
        );
    }

    private async detectShadcnUI(): Promise<boolean> {
        const rootPath = this.workspaceFolder.uri.fsPath;
        
        // Check for components.json
        if (await this.fileExists(path.join(rootPath, 'components.json'))) {
            return true;
        }

        // Check for typical shadcn/ui component structure
        if (await this.directoryExists(this.uiComponentsPath)) {
            try {
                const files = await vscode.workspace.findFiles(
                    new vscode.RelativePattern(this.workspaceFolder, 'src/components/ui/*.tsx'),
                    null,
                    3
                );

                for (const file of files) {
                    const content = await this.readFile(file.fsPath);
                    if (content && this.isShadcnComponent(content)) {
                        return true;
                    }
                }
            } catch {
                // Ignore errors
            }
        }

        return false;
    }

    private isShadcnComponent(content: string): boolean {
        const shadcnPatterns = [
            /import.*class-variance-authority/,
            /import.*clsx/,
            /import.*tailwind-merge/,
            /\bcn\s*\(/,
            /\bcva\s*\(/,
            /VariantProps/,
            /@radix-ui/
        ];

        return shadcnPatterns.some(pattern => pattern.test(content));
    }

    private async analyzeComponents(): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];

        if (!await this.directoryExists(this.srcPath)) {
            return components;
        }

        try {
            // Find all React component files
            const tsxFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(this.workspaceFolder, 'src/**/*.tsx'),
                new vscode.RelativePattern(this.workspaceFolder, '**/node_modules/**')
            );

            const jsxFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(this.workspaceFolder, 'src/**/*.jsx'),
                new vscode.RelativePattern(this.workspaceFolder, '**/node_modules/**')
            );

            const allFiles = [...tsxFiles, ...jsxFiles];

            for (const file of allFiles) {
                const componentInfo = await this.analyzeComponentFile(file.fsPath);
                if (componentInfo) {
                    components.push(componentInfo);
                }
            }
        } catch (error) {
            console.error('Error analyzing components:', error);
        }

        return components;
    }

    private async analyzeComponentFile(filePath: string): Promise<ComponentInfo | null> {
        try {
            const content = await this.readFile(filePath);
            if (!content) return null;

            const relativePath = path.relative(this.workspaceFolder.uri.fsPath, filePath);
            const fileName = path.basename(filePath, path.extname(filePath));

            const name = this.extractComponentName(content, fileName);
            const componentType = this.classifyComponent(filePath, content);
            const exports = this.extractExports(content);
            const imports = this.extractImports(content);
            const props = this.extractProps(content);
            const dependencies = this.extractDependencies(imports);
            const isTypeScript = filePath.endsWith('.tsx');
            const hasTailwind = this.hasTailwindClasses(content);
            const lineCount = content.split('\n').length;
            const complexityScore = this.calculateComplexity(content);

            return {
                name,
                filePath: relativePath,
                componentType,
                exports,
                imports,
                props,
                dependencies,
                isTypeScript,
                hasTailwind,
                lineCount,
                complexityScore
            };
        } catch (error) {
            console.error(`Error analyzing ${filePath}:`, error);
            return null;
        }
    }

    private extractComponentName(content: string, fallbackName: string): string {
        const patterns = [
            /export\s+default\s+function\s+(\w+)/,
            /export\s+default\s+(\w+)/,
            /const\s+(\w+):\s*React\.FC/,
            /const\s+(\w+)\s*=\s*forwardRef/,
            /function\s+(\w+)\s*\(/
        ];

        for (const pattern of patterns) {
            const match = content.match(pattern);
            if (match) return match[1];
        }

        return this.capitalizeFirst(fallbackName);
    }

    private classifyComponent(filePath: string, content: string): ComponentType {
        const pathLower = filePath.toLowerCase();

        if (pathLower.includes('/ui/')) return ComponentType.UI_LIBRARY;
        if (pathLower.includes('/pages/') || pathLower.includes('/app/')) return ComponentType.PAGE;
        if (pathLower.includes('layout')) return ComponentType.LAYOUT;
        if (pathLower.includes('/hooks/') || path.basename(filePath).startsWith('use')) return ComponentType.HOOK;
        if (pathLower.includes('/utils/') || pathLower.includes('/lib/')) return ComponentType.UTILITY;

        const contentLower = content.toLowerCase();
        if (['form', 'modal', 'dialog', 'dashboard'].some(keyword => contentLower.includes(keyword))) {
            return ComponentType.FEATURE;
        }

        return ComponentType.UNKNOWN;
    }

    private extractExports(content: string): string[] {
        const exports: string[] = [];

        // Default export
        const defaultMatch = content.match(/export\s+default\s+(\w+)/);
        if (defaultMatch) exports.push(defaultMatch[1]);

        // Named exports
        const namedExports = content.match(/export\s+(?:const|function|class)\s+(\w+)/g);
        if (namedExports) {
            namedExports.forEach(exp => {
                const match = exp.match(/export\s+(?:const|function|class)\s+(\w+)/);
                if (match) exports.push(match[1]);
            });
        }

        // Export statements
        const exportStatements = content.match(/export\s*\{\s*([^}]+)\s*\}/g);
        if (exportStatements) {
            exportStatements.forEach(statement => {
                const match = statement.match(/export\s*\{\s*([^}]+)\s*\}/);
                if (match) {
                    const names = match[1].split(',').map(name => name.trim().split(' as ')[0].trim());
                    exports.push(...names);
                }
            });
        }

        return [...new Set(exports)];
    }

    private extractImports(content: string): string[] {
        const imports: string[] = [];

        const importMatches = content.match(/import.*?from\s+['"]([^'"]+)['"]/g);
        if (importMatches) {
            importMatches.forEach(imp => {
                const match = imp.match(/from\s+['"]([^'"]+)['"]/);
                if (match) imports.push(match[1]);
            });
        }

        return imports;
    }

    private extractProps(content: string): string[] {
        const props: string[] = [];

        // TypeScript interface props
        const interfaceMatches = content.match(/interface\s+\w+Props\s*\{([^}]+)\}/g);
        if (interfaceMatches) {
            interfaceMatches.forEach(interfaceMatch => {
                const propsMatch = interfaceMatch.match(/\{([^}]+)\}/);
                if (propsMatch) {
                    const propLines = propsMatch[1].split('\n').map(line => line.trim()).filter(line => line);
                    propLines.forEach(line => {
                        const propMatch = line.match(/^(\w+)[\?\:]/);
                        if (propMatch) props.push(propMatch[1]);
                    });
                }
            });
        }

        // Function parameter destructuring
        const paramMatches = content.match(/function\s+\w+\s*\(\s*\{([^}]+)\}/g);
        if (paramMatches) {
            paramMatches.forEach(paramMatch => {
                const match = paramMatch.match(/\{([^}]+)\}/);
                if (match) {
                    const params = match[1].split(',').map(param => param.trim().split(':')[0].trim());
                    props.push(...params);
                }
            });
        }

        return [...new Set(props)];
    }

    private extractDependencies(imports: string[]): string[] {
        const dependencies: string[] = [];

        imports.forEach(imp => {
            // Skip relative imports
            if (imp.startsWith('.') || imp.startsWith('/')) return;

            // Extract package name (handle scoped packages)
            let packageName: string;
            if (imp.startsWith('@')) {
                packageName = imp.split('/').slice(0, 2).join('/');
            } else {
                packageName = imp.split('/')[0];
            }

            dependencies.push(packageName);
        });

        return [...new Set(dependencies)];
    }

    private hasTailwindClasses(content: string): boolean {
        const tailwindPatterns = [
            /className=.*?(?:flex|grid|p-|m-|text-|bg-|border-|rounded)/,
            /class=.*?(?:flex|grid|p-|m-|text-|bg-|border-|rounded)/,
            /\bcn\(/
        ];

        return tailwindPatterns.some(pattern => pattern.test(content));
    }

    private calculateComplexity(content: string): number {
        let score = 0;

        score += (content.match(/\bif\b/g) || []).length;
        score += (content.match(/\bfor\b|\bwhile\b/g) || []).length;
        score += (content.match(/\bswitch\b/g) || []).length;
        score += (content.match(/\bcatch\b/g) || []).length;
        score += (content.match(/\bfunction\b|\b=>\b/g) || []).length;
        score += (content.match(/useState|useEffect|useCallback/g) || []).length;

        return score;
    }

    private async analyzePages(): Promise<string[]> {
        const pages: string[] = [];
        const pageDirs = ['pages', 'app', 'routes'];

        for (const dirName of pageDirs) {
            const pageDir = path.join(this.srcPath, dirName);
            if (await this.directoryExists(pageDir)) {
                try {
                    const files = await vscode.workspace.findFiles(
                        new vscode.RelativePattern(this.workspaceFolder, `src/${dirName}/**/*.{tsx,jsx}`),
                        null
                    );

                    files.forEach(file => {
                        const fileName = path.basename(file.fsPath);
                        if (fileName !== 'layout.tsx' && fileName !== 'layout.jsx') {
                            pages.push(path.relative(this.workspaceFolder.uri.fsPath, file.fsPath));
                        }
                    });
                } catch {
                    // Ignore errors
                }
            }
        }

        return pages;
    }

    private async analyzeRoutes(): Promise<string[]> {
        const routes: string[] = [];
        const routingFiles = ['App.tsx', 'App.jsx', 'router.tsx', 'router.jsx', 'routes.tsx', 'routes.jsx'];

        for (const fileName of routingFiles) {
            const filePath = path.join(this.srcPath, fileName);
            if (await this.fileExists(filePath)) {
                const content = await this.readFile(filePath);
                if (content) {
                    const routeMatches = content.match(/path=['"]([^'"]+)['"]/g);
                    if (routeMatches) {
                        routeMatches.forEach(routeMatch => {
                            const match = routeMatch.match(/path=['"]([^'"]+)['"]/);
                            if (match) routes.push(match[1]);
                        });
                    }
                }
            }
        }

        return [...new Set(routes)];
    }

    private async extractDesignTokens(): Promise<Record<string, any>> {
        const designTokens: Record<string, any> = {};

        // Tailwind config
        const tailwindConfig = await this.parseTailwindConfig();
        if (tailwindConfig) {
            designTokens.tailwind = tailwindConfig;
        }

        // shadcn/ui config
        const componentsConfig = await this.parseComponentsConfig();
        if (componentsConfig) {
            designTokens.shadcn = componentsConfig;
        }

        // CSS variables
        const cssVariables = await this.extractCssVariables();
        if (Object.keys(cssVariables).length > 0) {
            designTokens.cssVariables = cssVariables;
        }

        return designTokens;
    }

    private async parseTailwindConfig(): Promise<Record<string, any> | null> {
        const configFiles = ['tailwind.config.js', 'tailwind.config.ts'];
        const rootPath = this.workspaceFolder.uri.fsPath;

        for (const configFile of configFiles) {
            const configPath = path.join(rootPath, configFile);
            if (await this.fileExists(configPath)) {
                return { configured: true, configFile };
            }
        }

        return null;
    }

    private async parseComponentsConfig(): Promise<Record<string, any> | null> {
        const configPath = path.join(this.workspaceFolder.uri.fsPath, 'components.json');
        if (await this.fileExists(configPath)) {
            try {
                const content = await this.readFile(configPath);
                return content ? JSON.parse(content) : null;
            } catch {
                return { error: 'Invalid JSON in components.json' };
            }
        }

        return null;
    }

    private async extractCssVariables(): Promise<Record<string, string[]>> {
        const cssVars: Record<string, string[]> = {};

        try {
            const cssFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(this.workspaceFolder, '**/*.css'),
                new vscode.RelativePattern(this.workspaceFolder, '**/node_modules/**')
            );

            for (const file of cssFiles) {
                const content = await this.readFile(file.fsPath);
                if (content) {
                    const variables = content.match(/--[\w-]+:\s*[^;]+/g);
                    if (variables) {
                        const relativePath = path.relative(this.workspaceFolder.uri.fsPath, file.fsPath);
                        cssVars[relativePath] = variables;
                    }
                }
            }
        } catch {
            // Ignore errors
        }

        return cssVars;
    }

    private async analyzeDependencies(): Promise<{ dependencies: Record<string, string>, devDependencies: Record<string, string> }> {
        const packageJson = await this.readPackageJson();
        if (!packageJson) {
            return { dependencies: {}, devDependencies: {} };
        }

        return {
            dependencies: packageJson.dependencies || {},
            devDependencies: packageJson.devDependencies || {}
        };
    }

    private async readPackageJson(): Promise<any> {
        const packagePath = path.join(this.workspaceFolder.uri.fsPath, 'package.json');
        try {
            const content = await this.readFile(packagePath);
            return content ? JSON.parse(content) : null;
        } catch {
            return null;
        }
    }

    // Utility methods
    private async fileExists(filePath: string): Promise<boolean> {
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
            return true;
        } catch {
            return false;
        }
    }

    private async directoryExists(dirPath: string): Promise<boolean> {
        try {
            const stat = await vscode.workspace.fs.stat(vscode.Uri.file(dirPath));
            return stat.type === vscode.FileType.Directory;
        } catch {
            return false;
        }
    }

    private async readFile(filePath: string): Promise<string | null> {
        try {
            const uri = vscode.Uri.file(filePath);
            const content = await vscode.workspace.fs.readFile(uri);
            return new TextDecoder('utf-8').decode(content);
        } catch (error) {
            // Log error for debugging but don't expose it
            console.log(`Failed to read file ${filePath}:`, error);
            return null;
        }
    }

    private capitalizeFirst(str: string): string {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    getAnalysisSummary(structure: ProjectStructure): Record<string, any> {
        const uiComponents = structure.components.filter(c => c.componentType === ComponentType.UI_LIBRARY);
        const pageComponents = structure.components.filter(c => c.componentType === ComponentType.PAGE);
        const featureComponents = structure.components.filter(c => c.componentType === ComponentType.FEATURE);

        return {
            projectType: `${structure.framework} with ${structure.buildTool}`,
            technologyStack: {
                typescript: structure.hasTypeScript,
                tailwind: structure.hasTailwind,
                shadcnUI: structure.hasShadcnUI,
                packageManager: structure.packageManager
            },
            componentsSummary: {
                total: structure.components.length,
                uiLibrary: uiComponents.length,
                pages: pageComponents.length,
                features: featureComponents.length,
                averageComplexity: structure.components.length > 0 
                    ? structure.components.reduce((sum, c) => sum + c.complexityScore, 0) / structure.components.length 
                    : 0
            },
            availableComponents: uiComponents.map(c => c.name),
            pages: structure.pages,
            routes: structure.routes,
            dependenciesCount: Object.keys(structure.dependencies).length,
            designSystemConfigured: Object.keys(structure.designTokens).length > 0
        };
    }
}

// Factory function for easy usage
export async function analyzeWorkspaceProject(): Promise<{ structure: ProjectStructure; summary: Record<string, any> } | null> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return null;
    }

    const analyzer = new TypeScriptProjectAnalyzer(workspaceFolder);
    const structure = await analyzer.analyzeProject();
    const summary = analyzer.getAnalysisSummary(structure);

    return { structure, summary };
}