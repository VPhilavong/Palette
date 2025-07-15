/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ILogService } from '../../../platform/log/common/logService';

export interface ProjectStructure {
    framework: 'nextjs' | 'react' | 'vue' | 'unknown';
    routing: 'app-router' | 'pages-router' | 'react-router' | 'vue-router' | 'none';
    styling: 'tailwind' | 'css-modules' | 'styled-components' | 'scss' | 'css' | 'none';
    directories: {
        components: string;
        pages: string;
        styles: string;
        ui: string;
        utils: string;
        api: string;
        types: string;
    };
    conventions: {
        componentExtension: 'tsx' | 'jsx' | 'vue';
        pageExtension: 'tsx' | 'jsx' | 'vue';
        styleExtension: 'css' | 'scss' | 'module.css';
        exportStyle: 'default' | 'named' | 'mixed';
    };
    patterns: {
        componentNaming: 'PascalCase' | 'kebab-case' | 'camelCase';
        fileNaming: 'PascalCase' | 'kebab-case' | 'camelCase';
        importStyle: 'relative' | 'absolute' | 'mixed';
    };
}

export interface IntentAnalysis {
    type: 'page' | 'component' | 'feature' | 'api' | 'utility' | 'style';
    suggestedPath: string;
    fileName: string;
    rationale: string;
    relatedFiles: string[];
}

export interface CodebaseContext {
    existingComponents: string[];
    existingPages: string[];
    commonPatterns: string[];
    styleSystem: string;
    routingStructure: string[];
}

export class CodebaseAnalysisTool {
    private workspaceRoot: string;
    private projectStructure: ProjectStructure | null = null;
    private codebaseContext: CodebaseContext | null = null;

    constructor(private readonly logService: ILogService) {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
    }

    async analyzeProject(): Promise<ProjectStructure> {
        if (this.projectStructure) {
            return this.projectStructure;
        }

        this.logService.info('CodebaseAnalysisTool: Starting project analysis');

        const framework = this.detectFramework();
        const routing = this.detectRoutingSystem(framework);
        const styling = this.detectStylingSystem();
        const directories = this.mapDirectories(framework, routing);
        const conventions = this.analyzeConventions();
        const patterns = this.analyzePatterns();

        this.projectStructure = {
            framework,
            routing,
            styling,
            directories,
            conventions,
            patterns
        };

        this.logService.info('CodebaseAnalysisTool: Project analysis completed', {
            framework,
            routing,
            styling
        });

        return this.projectStructure;
    }

    async analyzeIntent(userPrompt: string): Promise<IntentAnalysis> {
        const project = await this.analyzeProject();
        const context = await this.getCodebaseContext();
        
        const intent = this.classifyIntent(userPrompt);
        const suggestedPath = this.suggestFilePath(intent, userPrompt, project);
        const fileName = this.suggestFileName(userPrompt, intent, project);
        const rationale = this.explainPlacement(intent, suggestedPath, fileName, project);
        const relatedFiles = this.findRelatedFiles(intent, userPrompt, context);

        return {
            type: intent,
            suggestedPath,
            fileName,
            rationale,
            relatedFiles
        };
    }

    private detectFramework(): ProjectStructure['framework'] {
        try {
            const packageJsonPath = path.join(this.workspaceRoot, 'package.json');
            if (!fs.existsSync(packageJsonPath)) {
                return 'unknown';
            }

            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };

            if (dependencies['next']) return 'nextjs';
            if (dependencies['vue']) return 'vue';
            if (dependencies['react']) return 'react';

            return 'unknown';
        } catch (error) {
            this.logService.error('Failed to detect framework', error);
            return 'unknown';
        }
    }

    private detectRoutingSystem(framework: ProjectStructure['framework']): ProjectStructure['routing'] {
        try {
            if (framework === 'nextjs') {
                // Check for Next.js app router
                const appDir = path.join(this.workspaceRoot, 'app');
                const pagesDir = path.join(this.workspaceRoot, 'pages');
                
                if (fs.existsSync(appDir) && fs.statSync(appDir).isDirectory()) {
                    return 'app-router';
                }
                if (fs.existsSync(pagesDir) && fs.statSync(pagesDir).isDirectory()) {
                    return 'pages-router';
                }
            }

            if (framework === 'react') {
                const packageJsonPath = path.join(this.workspaceRoot, 'package.json');
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
                
                if (dependencies['react-router-dom']) return 'react-router';
            }

            if (framework === 'vue') {
                return 'vue-router';
            }

            return 'none';
        } catch (error) {
            this.logService.error('Failed to detect routing system', error);
            return 'none';
        }
    }

    private detectStylingSystem(): ProjectStructure['styling'] {
        try {
            const packageJsonPath = path.join(this.workspaceRoot, 'package.json');
            if (!fs.existsSync(packageJsonPath)) {
                return 'css';
            }

            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };

            if (dependencies['tailwindcss']) return 'tailwind';
            if (dependencies['styled-components']) return 'styled-components';
            if (dependencies['sass'] || dependencies['scss']) return 'scss';

            // Check for CSS modules
            const files = this.findFiles('**/*.module.css');
            if (files.length > 0) return 'css-modules';

            return 'css';
        } catch (error) {
            this.logService.error('Failed to detect styling system', error);
            return 'css';
        }
    }

    private mapDirectories(framework: ProjectStructure['framework'], routing: ProjectStructure['routing']): ProjectStructure['directories'] {
        const defaults = {
            components: 'components',
            pages: 'pages',
            styles: 'styles',
            ui: 'components/ui',
            utils: 'utils',
            api: 'api',
            types: 'types'
        };

        if (framework === 'nextjs' && routing === 'app-router') {
            return {
                ...defaults,
                pages: 'app',
                api: 'app/api',
                styles: 'app/css'
            };
        }

        if (framework === 'nextjs' && routing === 'pages-router') {
            return {
                ...defaults,
                pages: 'pages',
                api: 'pages/api'
            };
        }

        // Auto-detect existing directories
        const existingDirs = this.findExistingDirectories();
        return {
            ...defaults,
            ...existingDirs
        };
    }

    private findExistingDirectories(): Partial<ProjectStructure['directories']> {
        const dirs: Partial<ProjectStructure['directories']> = {};
        
        const candidates = [
            { key: 'components', paths: ['components', 'src/components', 'app/components'] },
            { key: 'ui', paths: ['components/ui', 'src/components/ui', 'ui'] },
            { key: 'utils', paths: ['utils', 'src/utils', 'lib', 'src/lib'] },
            { key: 'types', paths: ['types', 'src/types', '@types'] },
            { key: 'styles', paths: ['styles', 'src/styles', 'app/css', 'css'] }
        ];

        for (const candidate of candidates) {
            for (const dirPath of candidate.paths) {
                const fullPath = path.join(this.workspaceRoot, dirPath);
                if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
                    dirs[candidate.key as keyof ProjectStructure['directories']] = dirPath;
                    break;
                }
            }
        }

        return dirs;
    }

    private analyzeConventions(): ProjectStructure['conventions'] {
        const componentFiles = this.findFiles('**/*.{tsx,jsx,vue}');
        const hasTypeScript = componentFiles.some(file => file.endsWith('.tsx'));
        
        return {
            componentExtension: hasTypeScript ? 'tsx' : 'jsx',
            pageExtension: hasTypeScript ? 'tsx' : 'jsx',
            styleExtension: this.detectStyleExtension(),
            exportStyle: this.detectExportStyle(componentFiles)
        };
    }

    private detectStyleExtension(): ProjectStructure['conventions']['styleExtension'] {
        const styleFiles = this.findFiles('**/*.{css,scss,module.css}');
        
        if (styleFiles.some(file => file.endsWith('.module.css'))) return 'module.css';
        if (styleFiles.some(file => file.endsWith('.scss'))) return 'scss';
        return 'css';
    }

    private detectExportStyle(files: string[]): ProjectStructure['conventions']['exportStyle'] {
        let defaultExports = 0;
        let namedExports = 0;

        for (const file of files.slice(0, 10)) { // Sample first 10 files
            try {
                const content = fs.readFileSync(path.join(this.workspaceRoot, file), 'utf8');
                if (content.includes('export default')) defaultExports++;
                if (content.includes('export const') || content.includes('export function')) namedExports++;
            } catch (error) {
                // Ignore read errors
            }
        }

        if (defaultExports > namedExports) return 'default';
        if (namedExports > defaultExports) return 'named';
        return 'mixed';
    }

    private analyzePatterns(): ProjectStructure['patterns'] {
        const files = this.findFiles('**/*.{tsx,jsx,vue}');
        
        return {
            componentNaming: this.detectNamingPattern(files),
            fileNaming: this.detectNamingPattern(files),
            importStyle: this.detectImportStyle(files)
        };
    }

    private detectNamingPattern(files: string[]): 'PascalCase' | 'kebab-case' | 'camelCase' {
        const fileNames = files.map(file => path.basename(file, path.extname(file)));
        
        const pascalCount = fileNames.filter(name => /^[A-Z][a-zA-Z0-9]*$/.test(name)).length;
        const kebabCount = fileNames.filter(name => /^[a-z][a-z0-9-]*$/.test(name)).length;
        const camelCount = fileNames.filter(name => /^[a-z][a-zA-Z0-9]*$/.test(name)).length;

        if (pascalCount >= kebabCount && pascalCount >= camelCount) return 'PascalCase';
        if (kebabCount >= camelCount) return 'kebab-case';
        return 'camelCase';
    }

    private detectImportStyle(files: string[]): 'relative' | 'absolute' | 'mixed' {
        let relativeCount = 0;
        let absoluteCount = 0;

        for (const file of files.slice(0, 10)) {
            try {
                const content = fs.readFileSync(path.join(this.workspaceRoot, file), 'utf8');
                const imports = content.match(/import.*from ['"]([^'"]+)['"]/g) || [];
                
                for (const imp of imports) {
                    if (imp.includes('./') || imp.includes('../')) {
                        relativeCount++;
                    } else if (!imp.includes('node_modules') && !imp.includes('react') && !imp.includes('next')) {
                        absoluteCount++;
                    }
                }
            } catch (error) {
                // Ignore read errors
            }
        }

        if (relativeCount > absoluteCount) return 'relative';
        if (absoluteCount > relativeCount) return 'absolute';
        return 'mixed';
    }

    private classifyIntent(userPrompt: string): IntentAnalysis['type'] {
        const prompt = userPrompt.toLowerCase();
        
        // Page indicators
        if (prompt.includes('page') || prompt.includes('route') || prompt.includes('screen')) {
            return 'page';
        }
        
        // API indicators
        if (prompt.includes('api') || prompt.includes('endpoint') || prompt.includes('route handler')) {
            return 'api';
        }
        
        // Feature indicators (multiple related files)
        if (prompt.includes('feature') || prompt.includes('module') || prompt.includes('section')) {
            return 'feature';
        }
        
        // Utility indicators
        if (prompt.includes('util') || prompt.includes('helper') || prompt.includes('function')) {
            return 'utility';
        }
        
        // Style indicators
        if (prompt.includes('style') || prompt.includes('css') || prompt.includes('theme')) {
            return 'style';
        }
        
        // Default to component
        return 'component';
    }

    private suggestFilePath(intent: IntentAnalysis['type'], userPrompt: string, project: ProjectStructure): string {
        const baseDir = this.workspaceRoot;
        
        switch (intent) {
            case 'page':
                return path.join(baseDir, project.directories.pages);
            case 'api':
                return path.join(baseDir, project.directories.api);
            case 'component':
                // Check if it's a UI component
                if (userPrompt.toLowerCase().includes('ui') || userPrompt.toLowerCase().includes('button') || userPrompt.toLowerCase().includes('input')) {
                    return path.join(baseDir, project.directories.ui);
                }
                return path.join(baseDir, project.directories.components);
            case 'utility':
                return path.join(baseDir, project.directories.utils);
            case 'style':
                return path.join(baseDir, project.directories.styles);
            case 'feature':
                return path.join(baseDir, project.directories.components);
            default:
                return path.join(baseDir, project.directories.components);
        }
    }

    private suggestFileName(userPrompt: string, intent: IntentAnalysis['type'], project: ProjectStructure): string {
        // Extract key terms from prompt
        const words = userPrompt.toLowerCase().split(/\s+/);
        const meaningfulWords = words.filter(word => 
            !['create', 'generate', 'build', 'make', 'add', 'new', 'the', 'a', 'an'].includes(word)
        );

        let baseName = meaningfulWords.join('-');
        
        // Apply naming convention
        if (project.patterns.fileNaming === 'PascalCase') {
            baseName = baseName.split('-').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join('');
        } else if (project.patterns.fileNaming === 'camelCase') {
            const parts = baseName.split('-');
            baseName = parts[0] + parts.slice(1).map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join('');
        }

        // Add appropriate extension and suffix
        switch (intent) {
            case 'page':
                if (project.routing === 'app-router') {
                    return `page.${project.conventions.pageExtension}`;
                }
                return `${baseName}.${project.conventions.pageExtension}`;
            case 'api':
                return `route.ts`;
            case 'component':
                return `${baseName}.${project.conventions.componentExtension}`;
            case 'utility':
                return `${baseName}.ts`;
            case 'style':
                return `${baseName}.${project.conventions.styleExtension}`;
            default:
                return `${baseName}.${project.conventions.componentExtension}`;
        }
    }

    private explainPlacement(intent: IntentAnalysis['type'], suggestedPath: string, fileName: string, project: ProjectStructure): string {
        const relativePath = path.relative(this.workspaceRoot, suggestedPath);
        const fullPath = path.join(relativePath, fileName);

        switch (intent) {
            case 'page':
                if (project.routing === 'app-router') {
                    return `Creating a page in Next.js App Router. Files go in ${relativePath}/ with filename 'page.tsx' for routing.`;
                }
                return `Creating a page component in ${relativePath}/ following ${project.framework} conventions.`;
            case 'api':
                return `Creating an API route in ${relativePath}/ with filename 'route.ts' for Next.js App Router.`;
            case 'component':
                const isUI = suggestedPath.includes('/ui');
                return `Creating a ${isUI ? 'UI component' : 'component'} in ${relativePath}/ following ${project.patterns.componentNaming} naming convention.`;
            case 'utility':
                return `Creating a utility function in ${relativePath}/ for reusable helper logic.`;
            case 'style':
                return `Creating styles in ${relativePath}/ using ${project.styling} styling system.`;
            default:
                return `Creating file at ${fullPath} based on project structure analysis.`;
        }
    }

    private findRelatedFiles(intent: IntentAnalysis['type'], userPrompt: string, context: CodebaseContext): string[] {
        const related: string[] = [];
        
        // Find similar components or pages
        const searchTerm = userPrompt.toLowerCase();
        
        if (intent === 'page') {
            related.push(...context.existingPages.filter(page => 
                this.calculateSimilarity(page.toLowerCase(), searchTerm) > 0.3
            ));
        } else if (intent === 'component') {
            related.push(...context.existingComponents.filter(component => 
                this.calculateSimilarity(component.toLowerCase(), searchTerm) > 0.3
            ));
        }
        
        return related.slice(0, 5); // Limit to 5 most relevant
    }

    private calculateSimilarity(str1: string, str2: string): number {
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }

    private levenshteinDistance(str1: string, str2: string): number {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }

    private async getCodebaseContext(): Promise<CodebaseContext> {
        if (this.codebaseContext) {
            return this.codebaseContext;
        }

        const existingComponents = this.findFiles('components/**/*.{tsx,jsx,vue}')
            .map(file => path.basename(file, path.extname(file)));
        
        const existingPages = this.findFiles('{pages,app}/**/*.{tsx,jsx,vue}')
            .map(file => path.basename(file, path.extname(file)));
        
        const styleFiles = this.findFiles('**/*.{css,scss}');
        const styleSystem = this.detectStylingSystem();
        
        const routingStructure = this.findFiles('{pages,app}/**/*.{tsx,jsx,vue}')
            .map(file => path.dirname(file));

        this.codebaseContext = {
            existingComponents,
            existingPages,
            commonPatterns: [], // TODO: Implement pattern detection
            styleSystem,
            routingStructure
        };

        return this.codebaseContext;
    }

    private findFiles(pattern: string): string[] {
        try {
            // This is a simplified file finder - in a real implementation,
            // you'd use a proper glob library or VS Code's findFiles API
            const files: string[] = [];
            const walkDir = (dir: string, relativePath: string = '') => {
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                
                for (const entry of entries) {
                    const fullPath = path.join(dir, entry.name);
                    const relativeFilePath = path.join(relativePath, entry.name);
                    
                    if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
                        walkDir(fullPath, relativeFilePath);
                    } else if (entry.isFile()) {
                        files.push(relativeFilePath);
                    }
                }
            };
            
            walkDir(this.workspaceRoot);
            return files;
        } catch (error) {
            this.logService.error('Error finding files', error);
            return [];
        }
    }

    // Public method to get project analysis summary
    async getProjectSummary(): Promise<string> {
        const project = await this.analyzeProject();
        const context = await this.getCodebaseContext();
        
        return `**Project Analysis Summary**

**Framework:** ${project.framework}
**Routing:** ${project.routing}
**Styling:** ${project.styling}

**Directory Structure:**
- Components: ${project.directories.components}
- Pages: ${project.directories.pages}
- UI Components: ${project.directories.ui}
- Styles: ${project.directories.styles}

**Conventions:**
- Component Extension: ${project.conventions.componentExtension}
- Naming Style: ${project.patterns.componentNaming}
- Export Style: ${project.conventions.exportStyle}

**Existing Files:**
- ${context.existingComponents.length} components
- ${context.existingPages.length} pages`;
    }
}