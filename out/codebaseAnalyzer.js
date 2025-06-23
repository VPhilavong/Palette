"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodebaseAnalyzer = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class CodebaseAnalyzer {
    async analyzeWorkspace() {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            // Return default workspace info for testing
            return this.getDefaultWorkspaceInfo();
        }
        const rootPath = workspaceFolder.uri.fsPath;
        const workspaceInfo = {
            hasTypeScript: await this.detectTypeScript(rootPath),
            styling: await this.analyzeStyling(rootPath),
            existingComponents: await this.findExistingComponents(rootPath),
            projectStructure: await this.analyzeProjectStructure(rootPath)
        };
        return workspaceInfo;
    }
    async detectTypeScript(rootPath) {
        try {
            const tsconfigPath = path.join(rootPath, 'tsconfig.json');
            return fs.existsSync(tsconfigPath);
        }
        catch {
            return false;
        }
    }
    async analyzeStyling(rootPath) {
        const styling = {
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
                // Check for CSS modules by looking for .module.css files
                styling.hasCSSModules = await this.hasFilePattern(rootPath, '**/*.module.css');
            }
        }
        catch (error) {
            console.error('Error analyzing styling:', error);
        }
        return styling;
    }
    async findExistingComponents(rootPath) {
        const components = [];
        try {
            // Look for common component directories
            const commonDirs = ['src/components', 'components', 'src/ui', 'ui'];
            for (const dir of commonDirs) {
                const fullPath = path.join(rootPath, dir);
                if (fs.existsSync(fullPath)) {
                    await this.scanForComponents(fullPath, components);
                }
            }
        }
        catch (error) {
            console.error('Error finding components:', error);
        }
        return components.slice(0, 10); // Limit to 10 components for now
    }
    async scanForComponents(dirPath, components) {
        try {
            const files = fs.readdirSync(dirPath);
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = fs.statSync(filePath);
                if (stat.isDirectory()) {
                    await this.scanForComponents(filePath, components);
                }
                else if (this.isComponentFile(file)) {
                    const componentInfo = await this.analyzeComponentFile(filePath);
                    if (componentInfo) {
                        components.push(componentInfo);
                    }
                }
            }
        }
        catch (error) {
            console.error('Error scanning directory:', error);
        }
    }
    isComponentFile(filename) {
        return /\.(jsx?|tsx?)$/.test(filename) &&
            /^[A-Z]/.test(filename); // Starts with capital letter
    }
    async analyzeComponentFile(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            const filename = path.basename(filePath, path.extname(filePath));
            // Simple regex to find component exports
            const exportMatch = content.match(/export\s+(?:default\s+)?(?:function|const)\s+(\w+)/);
            const componentName = exportMatch?.[1] || filename;
            // Try to extract props from TypeScript interface or simple prop destructuring
            const propsMatch = content.match(/interface\s+\w*Props\s*{([^}]*)}/s) ||
                content.match(/{\s*([^}]*)\s*}:\s*\w*Props/) ||
                content.match(/{\s*([^}]*)\s*}\s*\)/); // Simple destructuring
            let description = `${componentName} component`;
            if (propsMatch) {
                const props = propsMatch[1].split(',').map(p => p.trim().split(':')[0].trim());
                description += ` (props: ${props.join(', ')})`;
            }
            return {
                name: componentName,
                path: filePath,
                description,
                props: propsMatch ? propsMatch[1].trim() : undefined
            };
        }
        catch (error) {
            console.error('Error analyzing component file:', error);
            return null;
        }
    }
    async analyzeProjectStructure(rootPath) {
        const structure = [];
        try {
            const commonDirs = ['src', 'components', 'pages', 'utils', 'hooks', 'context'];
            for (const dir of commonDirs) {
                const fullPath = path.join(rootPath, dir);
                if (fs.existsSync(fullPath)) {
                    structure.push(dir);
                }
            }
        }
        catch (error) {
            console.error('Error analyzing project structure:', error);
        }
        return structure;
    }
    async hasFilePattern(rootPath, pattern) {
        try {
            // Simple check for CSS modules - look for any .module.css file
            const srcPath = path.join(rootPath, 'src');
            if (fs.existsSync(srcPath)) {
                return this.hasModuleCSSInDir(srcPath);
            }
        }
        catch {
            // Ignore errors
        }
        return false;
    }
    hasModuleCSSInDir(dirPath) {
        try {
            const files = fs.readdirSync(dirPath);
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = fs.statSync(filePath);
                if (stat.isDirectory()) {
                    if (this.hasModuleCSSInDir(filePath)) {
                        return true;
                    }
                }
                else if (file.endsWith('.module.css')) {
                    return true;
                }
            }
        }
        catch {
            // Ignore errors
        }
        return false;
    }
    getDefaultWorkspaceInfo() {
        return {
            hasTypeScript: true,
            styling: {
                hasTailwind: false,
                hasStyledComponents: false,
                hasCSSModules: false,
                hasEmotion: false
            },
            existingComponents: [],
            projectStructure: ['src']
        };
    }
}
exports.CodebaseAnalyzer = CodebaseAnalyzer;
//# sourceMappingURL=codebaseAnalyzer.js.map