/**
 * Project Analysis Tools
 * Tools for analyzing project structure, dependencies, and components
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { z } from 'zod';
import { 
    PaletteTool, 
    ToolExecutionContext, 
    ToolResult, 
    ProjectAnalysisResult 
} from './types';

/**
 * Analyze project structure tool
 */
export const analyzeProjectTool: PaletteTool = {
    name: 'analyze_project',
    description: 'Analyze the project structure, dependencies, and framework',
    category: 'project-analysis',
    dangerLevel: 'safe',
    inputSchema: z.object({
        includeComponents: z.boolean().optional().default(true).describe('Include component analysis'),
        includeTypes: z.boolean().optional().default(true).describe('Include TypeScript type analysis'),
        maxFiles: z.number().optional().default(50).describe('Maximum number of files to analyze')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ProjectAnalysisResult> {
        const { includeComponents, includeTypes, maxFiles } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            console.log('🔍 Starting project analysis...');

            // Analyze package.json
            const packageInfo = await analyzePackageJson(context.workspacePath);
            
            // Analyze project structure
            const structure = await analyzeStructure(context.workspacePath);
            
            // Analyze components if requested
            let components: any[] = [];
            if (includeComponents) {
                components = await analyzeComponents(context.workspacePath, maxFiles);
            }
            
            // Analyze types if requested
            let types: any[] = [];
            if (includeTypes) {
                types = await analyzeTypes(context.workspacePath, maxFiles);
            }

            return {
                success: true,
                data: {
                    packageInfo,
                    structure,
                    components,
                    types,
                    summary: generateProjectSummary(packageInfo, structure, components)
                },
                framework: packageInfo.framework,
                components: components.map(c => ({
                    name: c.name,
                    path: c.path,
                    type: c.type,
                    complexity: c.complexity
                })),
                dependencies: packageInfo.dependencies || [],
                structure,
                followUpSuggestions: [
                    `Found ${components.length} components in ${packageInfo.framework || 'Unknown'} project`,
                    `Project uses ${Object.keys(packageInfo.dependencies || {}).length} dependencies`
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'PROJECT_ANALYSIS_ERROR',
                    message: `Failed to analyze project: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Find similar components tool
 */
export const findSimilarComponentsTool: PaletteTool = {
    name: 'find_similar_components',
    description: 'Find components similar to the specified component or pattern',
    category: 'project-analysis',
    dangerLevel: 'safe',
    inputSchema: z.object({
        componentName: z.string().optional().describe('Name of component to find similarities for'),
        pattern: z.string().optional().describe('Pattern or functionality to search for'),
        includeProps: z.boolean().optional().default(true).describe('Include prop analysis in similarity')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        const { componentName, pattern, includeProps } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        if (!componentName && !pattern) {
            return {
                success: false,
                error: {
                    code: 'INVALID_PARAMS',
                    message: 'Either componentName or pattern must be provided',
                    recoverable: true
                }
            };
        }

        try {
            const components = await analyzeComponents(context.workspacePath, 100);
            const similarComponents = [];

            for (const component of components) {
                let similarity = 0;
                
                if (componentName) {
                    // Name similarity
                    if (component.name.toLowerCase().includes(componentName.toLowerCase())) {
                        similarity += 50;
                    }
                    
                    // Type similarity
                    if (component.type === 'functional' && componentName.includes('Function')) {
                        similarity += 20;
                    }
                }
                
                if (pattern) {
                    // Content pattern matching
                    if (component.content && component.content.toLowerCase().includes(pattern.toLowerCase())) {
                        similarity += 40;
                    }
                }
                
                // Props similarity if enabled
                if (includeProps && component.props) {
                    similarity += Math.min(component.props.length * 5, 30);
                }
                
                if (similarity > 30) {
                    similarComponents.push({
                        ...component,
                        similarity
                    });
                }
            }
            
            similarComponents.sort((a, b) => b.similarity - a.similarity);

            return {
                success: true,
                data: {
                    query: { componentName, pattern },
                    similarComponents: similarComponents.slice(0, 10),
                    totalFound: similarComponents.length
                },
                followUpSuggestions: [
                    `Found ${similarComponents.length} similar components`,
                    similarComponents.length > 0 ? 
                        `Most similar: ${similarComponents[0].name} (${similarComponents[0].similarity}% match)` :
                        'No similar components found'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'SIMILARITY_ANALYSIS_ERROR',
                    message: `Failed to find similar components: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Check component dependencies tool
 */
export const checkComponentDependenciesTool: PaletteTool = {
    name: 'check_component_dependencies',
    description: 'Check what dependencies and imports a component uses',
    category: 'project-analysis',
    dangerLevel: 'safe',
    inputSchema: z.object({
        componentPath: z.string().describe('Path to component file to analyze'),
        includeTransitive: z.boolean().optional().default(false).describe('Include transitive dependencies')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        const { componentPath, includeTransitive } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, componentPath);
            const fileUri = vscode.Uri.file(fullPath);
            
            const contentBytes = await vscode.workspace.fs.readFile(fileUri);
            const content = new TextDecoder().decode(contentBytes);
            
            const analysis = analyzeComponentDependencies(content, componentPath);
            
            return {
                success: true,
                data: analysis,
                followUpSuggestions: [
                    `Component uses ${analysis.imports.length} imports`,
                    `External dependencies: ${analysis.externalDependencies.length}`,
                    `React hooks used: ${analysis.hooksUsed.join(', ') || 'none'}`
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'DEPENDENCY_ANALYSIS_ERROR',
                    message: `Failed to analyze dependencies: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

// Helper functions

async function analyzePackageJson(workspacePath: string) {
    try {
        const packageJsonPath = path.join(workspacePath, 'package.json');
        const packageJsonUri = vscode.Uri.file(packageJsonPath);
        const contentBytes = await vscode.workspace.fs.readFile(packageJsonUri);
        const packageJson = JSON.parse(new TextDecoder().decode(contentBytes));
        
        const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
        
        // Detect framework
        let framework = 'Unknown';
        if (dependencies.next) framework = 'Next.js';
        else if (dependencies.vite) framework = 'Vite + React';
        else if (dependencies.react) framework = 'React';
        else if (dependencies.vue) framework = 'Vue.js';
        else if (dependencies.svelte) framework = 'Svelte';
        
        // Detect UI library
        let uiLibrary = 'None';
        if (dependencies['@radix-ui/react-accordion'] || dependencies['shadcn-ui']) uiLibrary = 'shadcn/ui';
        else if (dependencies['@mui/material']) uiLibrary = 'Material-UI';
        else if (dependencies.antd) uiLibrary = 'Ant Design';
        else if (dependencies['@chakra-ui/react']) uiLibrary = 'Chakra UI';
        
        return {
            name: packageJson.name,
            version: packageJson.version,
            framework,
            uiLibrary,
            dependencies: packageJson.dependencies,
            devDependencies: packageJson.devDependencies,
            scripts: packageJson.scripts
        };
    } catch (error) {
        console.warn('Failed to analyze package.json:', error);
        return { framework: 'Unknown' };
    }
}

async function analyzeStructure(workspacePath: string) {
    try {
        const structure: any = {
            srcDir: 'src',
            hasComponents: false,
            hasPages: false,
            hasLib: false,
            hasUtils: false,
            hasStyles: false,
            hasTests: false
        };
        
        // Check common directories
        const dirs = ['src', 'app', 'components', 'pages', 'lib', 'utils', 'styles', 'test', 'tests', '__tests__'];
        
        for (const dir of dirs) {
            try {
                const dirPath = path.join(workspacePath, dir);
                const dirUri = vscode.Uri.file(dirPath);
                await vscode.workspace.fs.stat(dirUri);
                
                switch (dir) {
                    case 'src':
                    case 'app':
                        structure.srcDir = dir;
                        break;
                    case 'components':
                        structure.hasComponents = true;
                        structure.componentsDir = dir;
                        break;
                    case 'pages':
                        structure.hasPages = true;
                        structure.pagesDir = dir;
                        break;
                    case 'lib':
                        structure.hasLib = true;
                        structure.libDir = dir;
                        break;
                    case 'utils':
                        structure.hasUtils = true;
                        structure.utilsDir = dir;
                        break;
                    case 'styles':
                        structure.hasStyles = true;
                        structure.stylesDir = dir;
                        break;
                    case 'test':
                    case 'tests':
                    case '__tests__':
                        structure.hasTests = true;
                        structure.testsDir = dir;
                        break;
                }
            } catch {
                // Directory doesn't exist
            }
        }
        
        return structure;
    } catch (error) {
        console.warn('Failed to analyze project structure:', error);
        return { srcDir: 'src' };
    }
}

async function analyzeComponents(workspacePath: string, maxFiles: number) {
    try {
        const components = [];
        const componentPattern = new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx}');
        const files = await vscode.workspace.findFiles(componentPattern, '**/node_modules/**', maxFiles);
        
        for (const file of files) {
            try {
                const contentBytes = await vscode.workspace.fs.readFile(file);
                const content = new TextDecoder().decode(contentBytes);
                const relativePath = vscode.workspace.asRelativePath(file);
                const fileName = path.basename(file.fsPath, path.extname(file.fsPath));
                
                // Basic component detection
                if (looksLikeComponent(content, fileName)) {
                    components.push({
                        name: fileName,
                        path: relativePath,
                        type: detectComponentType(content),
                        props: extractProps(content),
                        hooks: extractHooks(content),
                        complexity: assessComplexity(content),
                        content: content.substring(0, 500) // First 500 chars for analysis
                    });
                }
            } catch (error) {
                console.warn(`Failed to analyze component ${file.fsPath}:`, error);
            }
        }
        
        return components;
    } catch (error) {
        console.warn('Failed to analyze components:', error);
        return [];
    }
}

async function analyzeTypes(workspacePath: string, maxFiles: number) {
    try {
        const types = [];
        const typePattern = new vscode.RelativePattern(workspacePath, '**/*.{ts,tsx,d.ts}');
        const files = await vscode.workspace.findFiles(typePattern, '**/node_modules/**', maxFiles);
        
        for (const file of files) {
            try {
                const contentBytes = await vscode.workspace.fs.readFile(file);
                const content = new TextDecoder().decode(contentBytes);
                const relativePath = vscode.workspace.asRelativePath(file);
                
                // Extract type definitions
                const typeDefinitions = extractTypeDefinitions(content);
                if (typeDefinitions.length > 0) {
                    types.push({
                        file: relativePath,
                        types: typeDefinitions
                    });
                }
            } catch (error) {
                console.warn(`Failed to analyze types in ${file.fsPath}:`, error);
            }
        }
        
        return types;
    } catch (error) {
        console.warn('Failed to analyze types:', error);
        return [];
    }
}

function looksLikeComponent(content: string, fileName: string): boolean {
    const isPascalCase = /^[A-Z][a-zA-Z0-9]*$/.test(fileName);
    const hasReactImport = /import.*React/.test(content);
    const hasJSXReturn = /return\s*\(?\s*</.test(content);
    const hasExport = /export\s+(default|const|function)/.test(content);
    
    return isPascalCase && (hasReactImport || hasJSXReturn) && hasExport;
}

function detectComponentType(content: string): 'functional' | 'class' | 'forwardRef' {
    if (/React\.forwardRef|forwardRef/.test(content)) return 'forwardRef';
    if (/class.*extends.*Component/.test(content)) return 'class';
    return 'functional';
}

function extractProps(content: string): string[] {
    const props: string[] = [];
    const propsInterfaceRegex = /interface\s+\w*Props\s*\{([^}]*)\}/gs;
    let match;
    
    while ((match = propsInterfaceRegex.exec(content)) !== null) {
        const propsContent = match[1];
        const propLines = propsContent.split('\n').filter(line => line.trim());
        
        for (const line of propLines) {
            const propMatch = line.match(/(\w+)(\??):\s*([^;]+)/);
            if (propMatch) {
                props.push(propMatch[1].trim());
            }
        }
    }
    
    return props;
}

function extractHooks(content: string): string[] {
    const hooks: Set<string> = new Set();
    const hookRegex = /\b(use[A-Z]\w*)\b/g;
    let match;
    
    while ((match = hookRegex.exec(content)) !== null) {
        hooks.add(match[1]);
    }
    
    return Array.from(hooks);
}

function assessComplexity(content: string): 'simple' | 'medium' | 'complex' {
    const lineCount = content.split('\n').length;
    const functionCount = (content.match(/function\s+\w+/g) || []).length;
    const hooksCount = (content.match(/use[A-Z]\w*/g) || []).length;
    
    const score = lineCount * 0.1 + functionCount * 5 + hooksCount * 3;
    
    if (score > 100) return 'complex';
    if (score > 40) return 'medium';
    return 'simple';
}

function extractTypeDefinitions(content: string): any[] {
    const types = [];
    const typeRegex = /(?:export\s+)?(?:interface|type|enum)\s+(\w+)/g;
    let match;
    
    while ((match = typeRegex.exec(content)) !== null) {
        types.push({
            name: match[1],
            type: match[0].includes('interface') ? 'interface' : 
                  match[0].includes('enum') ? 'enum' : 'type'
        });
    }
    
    return types;
}

function analyzeComponentDependencies(content: string, componentPath: string) {
    const imports: string[] = [];
    const externalDependencies: string[] = [];
    const internalImports: string[] = [];
    const hooksUsed: string[] = [];
    
    // Extract imports
    const importRegex = /import.*from\s+['"`]([^'"`]+)['"`]/g;
    let match;
    
    while ((match = importRegex.exec(content)) !== null) {
        const importPath = match[1];
        imports.push(importPath);
        
        if (importPath.startsWith('.') || importPath.startsWith('/')) {
            internalImports.push(importPath);
        } else {
            externalDependencies.push(importPath.split('/')[0]);
        }
    }
    
    // Extract hooks
    const hookRegex = /\b(use[A-Z]\w*)\b/g;
    while ((match = hookRegex.exec(content)) !== null) {
        if (!hooksUsed.includes(match[1])) {
            hooksUsed.push(match[1]);
        }
    }
    
    return {
        imports,
        externalDependencies: Array.from(new Set(externalDependencies)),
        internalImports,
        hooksUsed
    };
}

function generateProjectSummary(packageInfo: any, structure: any, components: any[]) {
    return {
        framework: packageInfo.framework,
        uiLibrary: packageInfo.uiLibrary,
        componentCount: components.length,
        hasTypeScript: structure.srcDir === 'src' || components.some((c: any) => c.path.endsWith('.tsx')),
        complexity: components.length > 20 ? 'large' : components.length > 5 ? 'medium' : 'small'
    };
}

/**
 * Project analysis tools collection
 */
export class ProjectAnalysisTools {
    static getAllTools(): PaletteTool[] {
        return [
            analyzeProjectTool,
            findSimilarComponentsTool,
            checkComponentDependenciesTool
        ];
    }

    static registerAll(registry: any): void {
        this.getAllTools().forEach(tool => {
            registry.registerTool(tool, { enabled: true });
        });
        console.log('🔍 Registered project analysis tools');
    }
}