import * as vscode from 'vscode';
import { ComponentInfo, ImportInfo } from '../types';

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
            
            const fileName = vscode.workspace.asRelativePath(fileUri);
            const isVueFile = fileName.endsWith('.vue');
            console.log(`Parsing file: ${fileName} (${code.length} chars) - Vue: ${isVueFile}`);
            
            // Skip files that are too large
            if (code.length > 50000) {
                console.log(`Skipping ${fileName}: too large (${code.length} chars)`);
                return null;
            }
            
            // Check if it looks like a component
            const looksLikeComponent = this.looksLikeComponent(code);
            console.log(`${fileName} looks like component: ${looksLikeComponent}`);
            
            if (isVueFile) {
                console.log(`${fileName} is Vue file - checking for Vue patterns:`);
                console.log(`  - Has <template>: ${code.includes('<template>')}`);
                console.log(`  - Has <script setup>: ${code.includes('<script setup>')}`);
                console.log(`  - Has Vue imports: ${code.includes('vue')}`);
                console.log(`  - Has useData: ${code.includes('useData')}`);
            }
            
            if (!looksLikeComponent) {
                console.log(`Skipping ${fileName}: doesn't look like component`);
                return null;
            }

            const componentInfo: ComponentInfo = {
                name: this.getFileBaseName(fileUri),
                path: vscode.workspace.asRelativePath(fileUri),
                exports: [],
                imports: [],
                props: [],
                hooks: [],
                jsxElements: [],
                comments: []
            };

            // Parse using regex patterns (much more reliable than AST for our needs)
            this.extractImports(code, componentInfo);
            this.extractExports(code, componentInfo);
            this.extractHooks(code, componentInfo);
            this.extractProps(code, componentInfo);
            this.extractJsxElements(code, componentInfo);
            this.extractComments(code, componentInfo);

            // Only return if we found exports or hooks (indicating it's likely a component file)
            const hasExports = componentInfo.exports.length > 0;
            const hasHooks = componentInfo.hooks && componentInfo.hooks.length > 0;
            console.log(`${fileName} - exports: ${componentInfo.exports.length}, hooks: ${componentInfo.hooks?.length || 0}`);
            console.log(`${fileName} - exports:`, componentInfo.exports);
            console.log(`${fileName} - hooks:`, componentInfo.hooks);
            
            if (hasExports || hasHooks) {
                console.log(`✅ ${fileName} identified as component`);
                return componentInfo;
            } else {
                console.log(`❌ ${fileName} rejected: no exports or hooks`);
                return null;
            }

        } catch (error) {
            console.warn(`Component parsing failed for ${fileUri.fsPath}:`, error);
            return null;
        }
    }

    private looksLikeComponent(code: string): boolean {
        // Quick heuristics to identify component files
        const componentIndicators = [
            // React patterns
            /export\s+(default\s+)?function\s+[A-Z]/,  // Exported function starting with capital
            /export\s+(default\s+)?const\s+[A-Z]/,     // Exported const starting with capital
            /class\s+[A-Z]\w*\s+extends\s+.*Component/, // Class component
            /<[A-Z][^>]*>/,                             // JSX with capital letter tag
            /useState|useEffect|useContext|useUser|useRouter/, // React hooks + common library hooks
            /import.*from\s+['"]react['"]/,              // React import
            /import.*from\s+['"]next/,                   // Next.js imports
            /import.*@auth0/,                            // Auth0 imports
            /withPageAuthRequired|withAuth/,             // HOC patterns
            /React\.ReactNode|React\.FC/,                // TypeScript React types
            /return\s*\(\s*<|return\s*</,                // JSX return statements
            /function\s+[A-Z][A-Za-z0-9_$]*\s*\(/,      // Component function declarations
            /const\s+[A-Z][A-Za-z0-9_$]*\s*[=:]/,       // Component const declarations
            
            // Vue patterns
            /<template>/,                                // Vue template tag
            /<script.*setup/,                            // Vue Composition API setup
            /<script>/,                                  // Vue Options API
            /defineComponent/,                           // Vue defineComponent
            /useData|useRoute|useLayout|useRouter/,      // Vue composables
            /import.*from\s+['"]vue['"]/,                // Vue import
            /\.vue$/,                                    // Vue file extension
            /export\s+default\s+{/,                      // Vue options export
            /setup\s*\(/,                                // Vue setup function
            /<style.*scoped/,                            // Vue scoped styles
            /ref\(|reactive\(|computed\(/,               // Vue reactivity
            /onMounted|onUnmounted|watchEffect/,         // Vue lifecycle
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
        const exports = new Set<string>();

        // 1. Function exports
        const functionExportRegex = /export\s+(?:default\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        let match;
        while ((match = functionExportRegex.exec(code)) !== null) {
            exports.add(match[1]);
        }

        // 2. Const/let/var exports (including arrow functions)
        const constExportRegex = /export\s+(?:default\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        while ((match = constExportRegex.exec(code)) !== null) {
            exports.add(match[1]);
        }

        // 3. Class exports
        const classExportRegex = /export\s+(?:default\s+)?class\s+([A-Za-z_$][A-Za-z0-9_$]*)/g;
        while ((match = classExportRegex.exec(code)) !== null) {
            exports.add(match[1]);
        }

        // 4. Named exports
        const namedExportRegex = /export\s+{\s*([^}]+)\s*}/g;
        while ((match = namedExportRegex.exec(code)) !== null) {
            const namedExports = match[1].split(',').map(exp => exp.trim().split(' as ')[0].trim());
            namedExports.forEach(exp => exports.add(exp));
        }

        // 5. Default export identifiers (including HOCs)
        const defaultExportRegex = /export\s+default\s+([A-Za-z_$][A-Za-z0-9_$]*(?:\([^)]*\))?)/g;
        while ((match = defaultExportRegex.exec(code)) !== null) {
            exports.add(`default:${match[1]}`);
        }

        // 6. HOC patterns (withAuth, withPageAuth, etc.)
        const hocRegex = /export\s+default\s+(with[A-Za-z]+|connect)\s*\(\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\)/g;
        while ((match = hocRegex.exec(code)) !== null) {
            exports.add(`default:${match[1]}(${match[2]})`);
            exports.add(match[2]); // Also add the wrapped component
        }

        // 7. Multiple component declarations in same file
        const componentDeclRegex = /(?:const|let|var|function)\s+([A-Z][A-Za-z0-9_$]*)\s*[=:]/g;
        while ((match = componentDeclRegex.exec(code)) !== null) {
            // Only add if it looks like a component (starts with capital letter)
            if (/^[A-Z]/.test(match[1])) {
                exports.add(match[1]);
            }
        }

        // 8. Next.js specific patterns
        if (code.includes('getServerSideProps') || code.includes('getStaticProps')) {
            // Next.js page component - look for main component
            const pageComponentRegex = /(?:const|function)\s+([A-Z][A-Za-z0-9_$]*)\s*[=\(]/g;
            while ((match = pageComponentRegex.exec(code)) !== null) {
                exports.add(match[1]);
            }
        }

        // 9. Vue specific patterns
        if (code.includes('<template>') || code.includes('defineComponent')) {
            // Vue Single File Component - extract component name from filename
            const vueNameRegex = /(?:name\s*:\s*['"]([^'"]+)['"])|(?:defineComponent\s*\(\s*{\s*name\s*:\s*['"]([^'"]+)['"])/g;
            while ((match = vueNameRegex.exec(code)) !== null) {
                exports.add(match[1] || match[2]);
            }
            
            // Vue setup script components
            if (code.includes('<script setup>') || code.includes('<script lang="ts" setup>')) {
                // For setup script, component name usually comes from filename
                exports.add('VueComponent'); // Placeholder, will be replaced by filename
            }
        }

        componentInfo.exports = Array.from(exports);
    }

    private extractHooks(code: string, componentInfo: ComponentInfo): void {
        // Extract React hooks usage - both calls and imports
        const hooks = new Set<string>();

        // 1. Direct hook calls (existing)
        const hookCallRegex = /\b(use[A-Z][A-Za-z0-9]*)\s*\(/g;
        let match;
        while ((match = hookCallRegex.exec(code)) !== null) {
            hooks.add(match[1]);
        }

        // 2. Hook imports from libraries (Auth0, Next.js, etc.)
        const hookImportRegex = /import\s*{[^}]*\b(use[A-Z][A-Za-z0-9]*)[^}]*}\s*from\s*['"][^'"]*['"]/g;
        while ((match = hookImportRegex.exec(code)) !== null) {
            hooks.add(match[1]);
        }

        // 3. Destructured hook imports
        const destructuredHookRegex = /{\s*([^}]*)\s*}\s*=\s*\w*\(\)[\s\S]*?(?:use[A-Z][A-Za-z0-9]*)/g;
        while ((match = destructuredHookRegex.exec(code)) !== null) {
            // Look for hook patterns in destructured variables
            const destructured = match[1];
            const hookMatches = destructured.match(/\b(use[A-Z][A-Za-z0-9]*)\b/g);
            if (hookMatches) {
                hookMatches.forEach(hook => hooks.add(hook));
            }
        }

        // 4. Common framework hooks that might be aliased
        const commonHooks = [
            // React/Next.js/Auth0
            'useUser', 'useRouter', 'usePathname', 'useSearchParams',
            // Vue/VitePress
            'useData', 'useRoute', 'useLayout', 'useFrontmatter', 'usePageData',
            // Vue Composition API
            'ref', 'reactive', 'computed', 'watch', 'watchEffect', 
            'onMounted', 'onUnmounted', 'onUpdated', 'nextTick'
        ];
        commonHooks.forEach(hook => {
            if (code.includes(hook)) {
                hooks.add(hook);
            }
        });

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

    private extractJsxElements(code: string, componentInfo: ComponentInfo): void {
        const elements = new Set<string>();

        // Extract JSX element names
        const jsxElementRegex = /<([A-Z][A-Za-z0-9]*|[a-z][a-z0-9\-]*)/g;
        let match;
        while ((match = jsxElementRegex.exec(code)) !== null) {
            elements.add(match[1]);
        }

        // Extract common UI patterns
        const uiPatterns = [
            'form', 'table', 'list', 'grid', 'card', 'modal', 'dialog', 'button',
            'input', 'select', 'textarea', 'checkbox', 'radio', 'nav', 'menu',
            'header', 'footer', 'sidebar', 'main', 'section', 'article', 'aside',
            'Container', 'Layout', 'Row', 'Col', 'Grid', 'Card', 'Modal', 'Button'
        ];

        uiPatterns.forEach(pattern => {
            if (code.includes(`<${pattern}`) || code.includes(`<${pattern.charAt(0).toUpperCase() + pattern.slice(1)}`)) {
                elements.add(pattern.toLowerCase());
            }
        });

        componentInfo.jsxElements = Array.from(elements);
    }

    private extractComments(code: string, componentInfo: ComponentInfo): void {
        const comments = new Set<string>();

        // Extract single-line comments
        const singleLineCommentRegex = /\/\/\s*(.+)/g;
        let match;
        while ((match = singleLineCommentRegex.exec(code)) !== null) {
            const comment = match[1].trim();
            if (comment.length > 5 && !comment.startsWith('@') && !comment.startsWith('eslint')) {
                comments.add(comment);
            }
        }

        // Extract multi-line comments
        const multiLineCommentRegex = /\/\*\*([\s\S]*?)\*\//g;
        while ((match = multiLineCommentRegex.exec(code)) !== null) {
            const comment = match[1]
                .replace(/^\s*\*\s?/gm, '') // Remove leading asterisks
                .trim();
            if (comment.length > 10) {
                comments.add(comment);
            }
        }

        // Extract JSDoc comments
        const jsDocRegex = /\/\*\*\s*([\s\S]*?)\s*\*\//g;
        while ((match = jsDocRegex.exec(code)) !== null) {
            const comment = match[1]
                .replace(/^\s*\*\s?/gm, '')
                .replace(/@\w+\s*/g, '') // Remove JSDoc tags
                .trim();
            if (comment.length > 10) {
                comments.add(comment);
            }
        }

        componentInfo.comments = Array.from(comments).slice(0, 5); // Limit to first 5 comments
    }

    private getFileBaseName(uri: vscode.Uri): string {
        const fileName = uri.fsPath.split('/').pop() || '';
        return fileName.replace(/\.(js|jsx|ts|tsx|vue)$/, '');
    }
}