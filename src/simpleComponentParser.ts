import * as vscode from 'vscode';
import { ComponentInfo, ImportInfo } from './types';

export class SimpleComponentParser {
    async parseComponentsFromFiles(files: vscode.Uri[]): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];
        
        for (const file of files) {
            try {
                const componentInfo = await this.parseFile(file);
                if (componentInfo) {
                    components.push(componentInfo);
                }
            } catch (error) {
                console.warn(`Failed to parse ${file.fsPath}:`, error);
            }
        }
        
        return components;
    }

    private async parseFile(fileUri: vscode.Uri): Promise<ComponentInfo | null> {
        try {
            const content = await vscode.workspace.fs.readFile(fileUri);
            const code = content.toString();
            
            // Skip files that are too large or don't look like components
            if (code.length > 50000 || !this.looksLikeComponent(code)) {
                return null;
            }

            const componentInfo: ComponentInfo = {
                name: this.getFileBaseName(fileUri),
                path: vscode.workspace.asRelativePath(fileUri),
                exports: [],
                imports: [],
                props: [],
                hooks: []
            };

            // Parse using regex patterns (much more reliable than AST for our needs)
            this.extractImports(code, componentInfo);
            this.extractExports(code, componentInfo);
            this.extractHooks(code, componentInfo);
            this.extractProps(code, componentInfo);

            // Only return if we found exports or hooks (indicating it's likely a component file)
            return (componentInfo.exports.length > 0 || (componentInfo.hooks && componentInfo.hooks.length > 0)) ? componentInfo : null;

        } catch (error) {
            console.warn(`Component parsing failed for ${fileUri.fsPath}:`, error);
            return null;
        }
    }

    private looksLikeComponent(code: string): boolean {
        // Quick heuristics to identify component files
        const componentIndicators = [
            /export\s+(default\s+)?function\s+[A-Z]/,  // Exported function starting with capital
            /export\s+(default\s+)?const\s+[A-Z]/,     // Exported const starting with capital
            /class\s+[A-Z]\w*\s+extends\s+.*Component/, // Class component
            /<[A-Z][^>]*>/,                             // JSX with capital letter tag
            /useState|useEffect|useContext/,            // React hooks
            /import.*from\s+['"]react['"]/,              // React import
            /\.jsx?$|\.tsx?$/                           // File extension
        ];

        return componentIndicators.some(pattern => pattern.test(code));
    }

    private extractImports(code: string, componentInfo: ComponentInfo): void {
        // Match import statements
        const importRegex = /import\s+(?:(\w+)|{([^}]+)}|\*\s+as\s+(\w+))?\s*(?:,\s*)?(?:(\w+)|{([^}]+)}|\*\s+as\s+(\w+))?\s*from\s+['"]([^'"]+)['"]/g;
        let match;

        while ((match = importRegex.exec(code)) !== null) {
            const module = match[7];
            const importInfo: ImportInfo = {
                module,
                imports: [],
                isDefault: false
            };

            // Default import
            if (match[1]) {
                importInfo.imports.push(match[1]);
                importInfo.isDefault = true;
            }

            // Named imports
            if (match[2]) {
                const namedImports = match[2].split(',').map(imp => imp.trim().split(' as ')[0]);
                importInfo.imports.push(...namedImports);
            }

            // Namespace import
            if (match[3]) {
                importInfo.imports.push(`* as ${match[3]}`);
            }

            // Additional default import after named imports
            if (match[4]) {
                importInfo.imports.push(match[4]);
                importInfo.isDefault = true;
            }

            // Additional named imports
            if (match[5]) {
                const namedImports = match[5].split(',').map(imp => imp.trim().split(' as ')[0]);
                importInfo.imports.push(...namedImports);
            }

            // Additional namespace import
            if (match[6]) {
                importInfo.imports.push(`* as ${match[6]}`);
            }

            if (importInfo.imports.length > 0) {
                componentInfo.imports.push(importInfo);
            }
        }
    }

    private extractExports(code: string, componentInfo: ComponentInfo): void {
        // Extract function exports
        const functionExportRegex = /export\s+(?:default\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        let match;
        while ((match = functionExportRegex.exec(code)) !== null) {
            componentInfo.exports.push(match[1]);
        }

        // Extract const/let/var exports
        const constExportRegex = /export\s+(?:default\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        while ((match = constExportRegex.exec(code)) !== null) {
            componentInfo.exports.push(match[1]);
        }

        // Extract class exports
        const classExportRegex = /export\s+(?:default\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        while ((match = classExportRegex.exec(code)) !== null) {
            componentInfo.exports.push(match[1]);
        }

        // Extract named exports
        const namedExportRegex = /export\s+{\s*([^}]+)\s*}/g;
        while ((match = namedExportRegex.exec(code)) !== null) {
            const exports = match[1].split(',').map(exp => exp.trim().split(' as ')[0]);
            componentInfo.exports.push(...exports);
        }

        // Extract default export identifiers
        const defaultExportRegex = /export\s+default\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        while ((match = defaultExportRegex.exec(code)) !== null) {
            componentInfo.exports.push(`default:${match[1]}`);
        }
    }

    private extractHooks(code: string, componentInfo: ComponentInfo): void {
        // Extract React hooks usage
        const hookRegex = /\b(use[A-Z][A-Za-z0-9]*)\s*\(/g;
        let match;
        const hooks = new Set<string>();

        while ((match = hookRegex.exec(code)) !== null) {
            hooks.add(match[1]);
        }

        componentInfo.hooks = Array.from(hooks);
    }

    private extractProps(code: string, componentInfo: ComponentInfo): void {
        // Extract props from function parameters (simplified)
        const functionPropsRegex = /function\s+[A-Za-z_$][A-Za-z0-9_$]*\s*\(\s*{\s*([^}]+)\s*}\s*\)/g;
        let match;

        while ((match = functionPropsRegex.exec(code)) !== null) {
            const props = match[1].split(',').map(prop => prop.trim().split(':')[0].trim());
            componentInfo.props!.push(...props);
        }

        // Extract props from arrow function parameters
        const arrowPropsRegex = /(?:const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*\(\s*{\s*([^}]+)\s*}\s*\)\s*=>/g;
        while ((match = arrowPropsRegex.exec(code)) !== null) {
            const props = match[1].split(',').map(prop => prop.trim().split(':')[0].trim());
            componentInfo.props!.push(...props);
        }

        // Remove duplicates
        componentInfo.props = [...new Set(componentInfo.props!)];
    }

    private getFileBaseName(uri: vscode.Uri): string {
        const fileName = uri.fsPath.split('/').pop() || '';
        return fileName.replace(/\.(js|jsx|ts|tsx)$/, '');
    }
}