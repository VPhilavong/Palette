import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { WorkspaceInfo, ComponentInfo, StylingInfo } from './types';

export class CodebaseAnalyzer {
    
    async analyzeWorkspace(): Promise<WorkspaceInfo> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            // Return default workspace info for testing
            return this.getDefaultWorkspaceInfo();
        }

        const rootPath = workspaceFolder.uri.fsPath;
        
        const workspaceInfo: WorkspaceInfo = {
            hasTypeScript: await this.detectTypeScript(rootPath),
            styling: await this.analyzeStyling(rootPath),
            existingComponents: await this.findExistingComponents(rootPath),
            projectStructure: await this.analyzeProjectStructure(rootPath)
        };

        return workspaceInfo;
    }

    private async detectTypeScript(rootPath: string): Promise<boolean> {
        try {
            const tsconfigPath = path.join(rootPath, 'tsconfig.json');
            return fs.existsSync(tsconfigPath);
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
                
                // Check for CSS modules by looking for .module.css files
                styling.hasCSSModules = await this.hasFilePattern(rootPath, '**/*.module.css');
            }
        } catch (error) {
            console.error('Error analyzing styling:', error);
        }

        return styling;
    }

    private async findExistingComponents(rootPath: string): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];
        
        try {
            // Look for common component directories
            const commonDirs = ['src/components', 'components', 'src/ui', 'ui'];
            
            for (const dir of commonDirs) {
                const fullPath = path.join(rootPath, dir);
                if (fs.existsSync(fullPath)) {
                    await this.scanForComponents(fullPath, components);
                }
            }
        } catch (error) {
            console.error('Error finding components:', error);
        }

        return components.slice(0, 10); // Limit to 10 components for now
    }

    private async scanForComponents(dirPath: string, components: ComponentInfo[]): Promise<void> {
        try {
            const files = fs.readdirSync(dirPath);
            
            for (const file of files) {
                const filePath = path.join(dirPath, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isDirectory()) {
                    await this.scanForComponents(filePath, components);
                } else if (this.isComponentFile(file)) {
                    const componentInfo = await this.analyzeComponentFile(filePath);
                    if (componentInfo) {
                        components.push(componentInfo);
                    }
                }
            }
        } catch (error) {
            console.error('Error scanning directory:', error);
        }
    }

    private isComponentFile(filename: string): boolean {
        return /\.(jsx?|tsx?)$/.test(filename) && 
               /^[A-Z]/.test(filename); // Starts with capital letter
    }

    private async analyzeComponentFile(filePath: string): Promise<ComponentInfo | null> {
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
        } catch (error) {
            console.error('Error analyzing component file:', error);
            return null;
        }
    }

    private async analyzeProjectStructure(rootPath: string): Promise<string[]> {
        const structure: string[] = [];
        
        try {
            const commonDirs = ['src', 'components', 'pages', 'utils', 'hooks', 'context'];
            
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

    private async hasFilePattern(rootPath: string, pattern: string): Promise<boolean> {
        try {
            // Simple check for CSS modules - look for any .module.css file
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
                hasEmotion: false
            },
            existingComponents: [],
            projectStructure: ['src']
        };
    }
}