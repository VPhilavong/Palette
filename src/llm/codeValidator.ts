import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WorkspaceIndex } from '../types';

export interface ValidationResult {
    isValid: boolean;
    errors: string[];
    warnings: string[];
    fixedCode?: string;
}

export interface DependencyInfo {
    name: string;
    isInstalled: boolean;
    isDevDependency: boolean;
    suggestedAlternative?: string;
}

export class CodeValidator {
    
    async validateAndFixGeneratedCode(
        code: string, 
        workspaceIndex: WorkspaceIndex
    ): Promise<ValidationResult> {
        const result: ValidationResult = {
            isValid: true,
            errors: [],
            warnings: [],
            fixedCode: code
        };

        try {
            // Extract imports from the code
            const imports = this.extractImports(code);
            
            // Check each import
            for (const importInfo of imports) {
                const depCheck = await this.checkDependency(importInfo, workspaceIndex);
                
                if (!depCheck.isInstalled) {
                    if (depCheck.suggestedAlternative) {
                        result.warnings.push(
                            `Package '${importInfo.module}' not found. Replacing with '${depCheck.suggestedAlternative}'`
                        );
                        result.fixedCode = this.replaceImport(
                            result.fixedCode || code, 
                            importInfo.module, 
                            depCheck.suggestedAlternative
                        );
                    } else {
                        result.errors.push(`Missing dependency: ${importInfo.module}`);
                        result.isValid = false;
                    }
                }
            }

            // Check for type imports that don't exist
            result.fixedCode = await this.fixTypeImports(result.fixedCode || code, workspaceIndex);
            
            // Fix common React patterns
            result.fixedCode = this.fixReactPatterns(result.fixedCode || code);
            
            // Remove problematic imports
            result.fixedCode = this.removeProblematicImports(result.fixedCode || code, workspaceIndex);

        } catch (error) {
            result.errors.push(`Validation error: ${error}`);
            result.isValid = false;
        }

        return result;
    }

    private extractImports(code: string): Array<{module: string, imports: string[], line: string}> {
        const importRegex = /import\s+(.*?)\s+from\s+['"]([^'"]+)['"];?/g;
        const imports: Array<{module: string, imports: string[], line: string}> = [];
        let match;

        while ((match = importRegex.exec(code)) !== null) {
            const [fullMatch, importedItems, module] = match;
            const importsList = importedItems
                .replace(/[{}]/g, '')
                .split(',')
                .map(item => item.trim())
                .filter(item => item.length > 0);

            imports.push({
                module,
                imports: importsList,
                line: fullMatch
            });
        }

        return imports;
    }

    private async checkDependency(
        importInfo: {module: string, imports: string[], line: string}, 
        workspaceIndex: WorkspaceIndex
    ): Promise<DependencyInfo> {
        const module = importInfo.module;
        
        // Check if it's a relative import
        if (module.startsWith('.') || module.startsWith('@/')) {
            return { name: module, isInstalled: true, isDevDependency: false };
        }

        // Check for framework-provided dependencies
        const isFrameworkProvided = this.isFrameworkProvidedDependency(module, workspaceIndex);
        if (isFrameworkProvided) {
            return { name: module, isInstalled: true, isDevDependency: false };
        }

        // Check if it's installed
        const isInstalled = !!(
            workspaceIndex.project.dependencies[module] || 
            workspaceIndex.project.devDependencies[module]
        );

        const isDevDep = !!workspaceIndex.project.devDependencies[module];

        // Suggest alternatives for common missing packages
        let suggestedAlternative: string | undefined;
        
        if (!isInstalled) {
            suggestedAlternative = this.getSuggestedAlternative(module, workspaceIndex);
        }

        return {
            name: module,
            isInstalled,
            isDevDependency: isDevDep,
            suggestedAlternative
        };
    }

    private isFrameworkProvidedDependency(module: string, workspaceIndex: WorkspaceIndex): boolean {
        const frameworks = workspaceIndex.project.frameworks.map(f => f.name.toLowerCase());
        const dependencies = Object.keys(workspaceIndex.project.dependencies);
        const devDependencies = Object.keys(workspaceIndex.project.devDependencies);
        
        // Next.js provides React, React-DOM internally
        if ((dependencies.includes('next') || devDependencies.includes('next')) ||
            frameworks.includes('next.js') || frameworks.includes('nextjs')) {
            const nextJsProvided = ['react', 'react-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'];
            if (nextJsProvided.includes(module)) {
                return true;
            }
        }

        // Nuxt provides Vue internally
        if ((dependencies.includes('nuxt') || devDependencies.includes('nuxt')) ||
            frameworks.includes('nuxt') || frameworks.includes('nuxt.js')) {
            const nuxtProvided = ['vue', '@vue/runtime-core', '@vue/runtime-dom'];
            if (nuxtProvided.includes(module)) {
                return true;
            }
        }

        // Vite projects often have these bundled
        if (dependencies.includes('vite') || devDependencies.includes('vite')) {
            const viteProvided = ['vite/client'];
            if (viteProvided.includes(module)) {
                return true;
            }
        }

        // Gatsby provides React
        if (dependencies.includes('gatsby') || devDependencies.includes('gatsby')) {
            const gatsbyProvided = ['react', 'react-dom'];
            if (gatsbyProvided.includes(module)) {
                return true;
            }
        }

        return false;
    }

    private getSuggestedAlternative(module: string, workspaceIndex: WorkspaceIndex): string | undefined {
        const dependencies = Object.keys(workspaceIndex.project.dependencies);
        const devDependencies = Object.keys(workspaceIndex.project.devDependencies);
        const allDeps = [...dependencies, ...devDependencies];

        // Common replacements
        const replacements: Record<string, string | undefined> = {
            'lucide-react': allDeps.includes('react-icons') ? 'react-icons' : undefined,
            '@heroicons/react': allDeps.includes('react-icons') ? 'react-icons' : undefined,
            '@/types/user': undefined, // Will be handled by fixTypeImports
            'clsx': allDeps.includes('classnames') ? 'classnames' : undefined,
            'cn': allDeps.includes('classnames') ? 'classnames' : undefined,
        };

        return replacements[module] || 
               allDeps.find(dep => dep.includes(module.split('/')[0]));
    }

    private replaceImport(code: string, oldModule: string, newModule: string): string {
        const escapedOld = oldModule.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`from\\s+['"]${escapedOld}['"]`, 'g');
        return code.replace(regex, `from '${newModule}'`);
    }

    private async fixTypeImports(code: string, workspaceIndex: WorkspaceIndex): Promise<string> {
        let fixedCode = code;

        // Check for @/ type imports that don't exist
        const typeImportRegex = /import\s+.*?\s+from\s+['"]@\/types\/([^'"]+)['"];?/g;
        let match;

        while ((match = typeImportRegex.exec(code)) !== null) {
            const [fullMatch, typeName] = match;
            
            // Check if the type file exists
            const typeFileExists = await this.checkTypeFileExists(typeName, workspaceIndex);
            
            if (!typeFileExists) {
                // Replace with inline type definition
                const inlineType = this.generateInlineType(typeName);
                fixedCode = fixedCode.replace(fullMatch, '');
                fixedCode = this.addInlineTypeDefinition(fixedCode, inlineType);
            }
        }

        return fixedCode;
    }

    private async checkTypeFileExists(typeName: string, workspaceIndex: WorkspaceIndex): Promise<boolean> {
        const possiblePaths = [
            `src/types/${typeName}.ts`,
            `types/${typeName}.ts`,
            `src/@types/${typeName}.ts`,
            `@types/${typeName}.ts`
        ];

        return possiblePaths.some(typePath => 
            workspaceIndex.files.some(file => file.path.includes(typePath))
        );
    }

    private generateInlineType(typeName: string): string {
        const commonTypes: Record<string, string> = {
            'user': `interface User {
  id: string;
  name: string;
  email: string;
  username?: string;
  profilePicture?: string;
  location?: string;
  bio?: string;
}`,
            'auth': `interface AuthUser {
  id: string;
  email: string;
  name: string;
}`,
            'profile': `interface Profile {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}`
        };

        return commonTypes[typeName.toLowerCase()] || `interface ${typeName.charAt(0).toUpperCase() + typeName.slice(1)} {
  id: string;
  [key: string]: any;
}`;
    }

    private addInlineTypeDefinition(code: string, typeDefinition: string): string {
        // Add the type definition after imports and before the component
        const componentMatch = code.match(/(const|function)\s+\w+/);
        if (componentMatch) {
            const insertIndex = componentMatch.index || 0;
            return code.slice(0, insertIndex) + typeDefinition + '\n\n' + code.slice(insertIndex);
        }
        return typeDefinition + '\n\n' + code;
    }

    private fixReactPatterns(code: string): string {
        let fixedCode = code;

        // For Next.js 13+ App Router, we often don't need explicit React import
        const hasNextImport = fixedCode.includes('next/') || fixedCode.includes("'next");
        const isNextProject = fixedCode.includes('next/') || fixedCode.includes('app/') || fixedCode.includes('pages/');

        // Fix React import if missing (but not for Next.js 13+ in many cases)
        if (!fixedCode.includes("import React") && fixedCode.includes('React.FC')) {
            if (!isNextProject || fixedCode.includes('useState') || fixedCode.includes('useEffect')) {
                fixedCode = "import React from 'react';\n" + fixedCode;
            }
        }

        // Fix useState, useEffect imports
        const usedHooks = [];
        if (fixedCode.includes('useState')) usedHooks.push('useState');
        if (fixedCode.includes('useEffect')) usedHooks.push('useEffect');
        if (fixedCode.includes('useContext')) usedHooks.push('useContext');
        if (fixedCode.includes('useCallback')) usedHooks.push('useCallback');
        if (fixedCode.includes('useMemo')) usedHooks.push('useMemo');

        if (usedHooks.length > 0) {
            const reactImportMatch = fixedCode.match(/import React.*?from 'react';/);
            if (reactImportMatch) {
                // Update existing React import
                const existingImport = reactImportMatch[0];
                if (existingImport.includes('{')) {
                    // Already has named imports, merge them
                    const existingHooks = existingImport.match(/\{([^}]+)\}/)?.[1]?.split(',').map(s => s.trim()) || [];
                    const allHooks = [...new Set([...existingHooks, ...usedHooks])];
                    const newImport = `import React, { ${allHooks.join(', ')} } from 'react';`;
                    fixedCode = fixedCode.replace(existingImport, newImport);
                } else {
                    // Add named imports
                    const newImport = `import React, { ${usedHooks.join(', ')} } from 'react';`;
                    fixedCode = fixedCode.replace(existingImport, newImport);
                }
            } else if (!isNextProject || usedHooks.length > 0) {
                // Add React import with hooks
                fixedCode = `import React, { ${usedHooks.join(', ')} } from 'react';\n` + fixedCode;
            } else {
                // Next.js 13+ - just import the hooks
                fixedCode = `import { ${usedHooks.join(', ')} } from 'react';\n` + fixedCode;
            }
        }

        return fixedCode;
    }

    private removeProblematicImports(code: string, workspaceIndex: WorkspaceIndex): string {
        let fixedCode = code;

        // Remove icon imports if the package isn't available
        const iconPackages = ['lucide-react', '@heroicons/react', 'react-icons'];
        const hasIconPackage = iconPackages.some(pkg => 
            workspaceIndex.project.dependencies[pkg] || 
            workspaceIndex.project.devDependencies[pkg]
        );

        if (!hasIconPackage) {
            // Remove icon imports and replace with text
            fixedCode = fixedCode.replace(/import\s+\{[^}]*\}\s+from\s+['"](?:lucide-react|@heroicons\/react|react-icons)['"];?\n?/g, '');
            
            // Replace icon components with text
            fixedCode = fixedCode.replace(/<(\w+)\s+className="[^"]*"\s*\/>/g, '[$1]');
            fixedCode = fixedCode.replace(/<(\w+)\s+[^>]*aria-hidden="true"\s*\/>/g, '[$1]');
        }

        return fixedCode;
    }

    getValidationSummary(result: ValidationResult): string {
        let summary = '';
        
        if (result.errors.length > 0) {
            summary += `❌ Errors fixed: ${result.errors.length}\n`;
            result.errors.forEach(error => summary += `  • ${error}\n`);
        }
        
        if (result.warnings.length > 0) {
            summary += `⚠️ Warnings: ${result.warnings.length}\n`;
            result.warnings.forEach(warning => summary += `  • ${warning}\n`);
        }
        
        if (result.errors.length === 0 && result.warnings.length === 0) {
            summary = '✅ Code generated successfully with no issues!';
        }

        return summary;
    }
}