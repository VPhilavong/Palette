/**
 * shadcn/ui Integration Tools
 * Tools for managing shadcn/ui components installation and usage
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { z } from 'zod';
import { 
    PaletteTool, 
    ToolExecutionContext, 
    ToolResult 
} from './types';

/**
 * Install shadcn/ui component tool
 */
export const installShadcnComponentTool: PaletteTool = {
    name: 'install_shadcn_component',
    description: 'Install a shadcn/ui component in the project',
    category: 'component-management',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        componentName: z.string().describe('Name of the shadcn/ui component to install'),
        overwrite: z.boolean().optional().default(false).describe('Overwrite existing component')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        const { componentName, overwrite } = params;
        
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
            console.log(`🎨 Installing shadcn/ui component: ${componentName}`);

            // Check if npx shadcn-ui@latest add is available
            const terminal = vscode.window.createTerminal({
                name: 'Palette shadcn/ui',
                cwd: context.workspacePath
            });

            const command = overwrite 
                ? `npx shadcn-ui@latest add ${componentName} --overwrite`
                : `npx shadcn-ui@latest add ${componentName}`;

            terminal.sendText(command);
            terminal.show();

            // Note: In a real implementation, we'd wait for command completion
            // For now, return success assuming the command will work
            return {
                success: true,
                data: {
                    component: componentName,
                    command,
                    terminal: terminal.name
                },
                followUpSuggestions: [
                    `Installing ${componentName} via shadcn/ui CLI`,
                    'Check terminal for installation progress',
                    `Component will be available at src/components/ui/${componentName}.tsx`
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'SHADCN_INSTALL_ERROR',
                    message: `Failed to install shadcn/ui component: ${error.message}`,
                    details: error,
                    recoverable: true,
                    suggestedAction: 'Ensure shadcn/ui is set up in your project'
                }
            };
        }
    }
};

/**
 * List available shadcn/ui components tool
 */
export const listShadcnComponentsTool: PaletteTool = {
    name: 'list_shadcn_components',
    description: 'List available shadcn/ui components',
    category: 'component-management',
    dangerLevel: 'safe',
    inputSchema: z.object({
        includeInstalled: z.boolean().optional().default(true).describe('Include already installed components')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            // Common shadcn/ui components
            const availableComponents = [
                'accordion', 'alert', 'alert-dialog', 'aspect-ratio', 'avatar',
                'badge', 'button', 'calendar', 'card', 'carousel', 'checkbox',
                'collapsible', 'combobox', 'command', 'context-menu', 'data-table',
                'date-picker', 'dialog', 'drawer', 'dropdown-menu', 'form',
                'hover-card', 'input', 'label', 'menubar', 'navigation-menu',
                'pagination', 'popover', 'progress', 'radio-group', 'scroll-area',
                'select', 'separator', 'sheet', 'skeleton', 'slider', 'switch',
                'table', 'tabs', 'textarea', 'toast', 'toggle', 'toggle-group',
                'tooltip'
            ];

            let installedComponents: string[] = [];
            
            if (params.includeInstalled && context.workspacePath) {
                try {
                    const componentsDir = path.join(context.workspacePath, 'src/components/ui');
                    const componentsUri = vscode.Uri.file(componentsDir);
                    const files = await vscode.workspace.fs.readDirectory(componentsUri);
                    
                    installedComponents = files
                        .filter(([name, type]) => type === vscode.FileType.File && name.endsWith('.tsx'))
                        .map(([name]) => name.replace('.tsx', ''));
                } catch {
                    // Components directory doesn't exist or can't be read
                }
            }

            return {
                success: true,
                data: {
                    available: availableComponents,
                    installed: installedComponents,
                    notInstalled: availableComponents.filter(comp => !installedComponents.includes(comp))
                },
                followUpSuggestions: [
                    `${availableComponents.length} components available`,
                    `${installedComponents.length} components already installed`,
                    'Use install_shadcn_component to add new components'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'COMPONENT_LIST_ERROR',
                    message: `Failed to list components: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Check shadcn/ui setup tool
 */
export const checkShadcnSetupTool: PaletteTool = {
    name: 'check_shadcn_setup',
    description: 'Check if shadcn/ui is properly set up in the project',
    category: 'project-analysis',
    dangerLevel: 'safe',
    inputSchema: z.object({}),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
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
            const setup = {
                hasPackageJson: false,
                hasTailwind: false,
                hasComponentsJson: false,
                hasUtilsLib: false,
                hasComponentsDir: false,
                installedComponents: [] as string[]
            };

            // Check package.json
            try {
                const packageJsonPath = path.join(context.workspacePath, 'package.json');
                const packageJsonUri = vscode.Uri.file(packageJsonPath);
                const contentBytes = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(new TextDecoder().decode(contentBytes));
                
                setup.hasPackageJson = true;
                setup.hasTailwind = !!(packageJson.dependencies?.tailwindcss || packageJson.devDependencies?.tailwindcss);
            } catch {
                // Package.json not found or invalid
            }

            // Check components.json
            try {
                const componentsJsonPath = path.join(context.workspacePath, 'components.json');
                const componentsJsonUri = vscode.Uri.file(componentsJsonPath);
                await vscode.workspace.fs.stat(componentsJsonUri);
                setup.hasComponentsJson = true;
            } catch {
                // components.json not found
            }

            // Check utils lib
            try {
                const utilsPath = path.join(context.workspacePath, 'src/lib/utils.ts');
                const utilsUri = vscode.Uri.file(utilsPath);
                await vscode.workspace.fs.stat(utilsUri);
                setup.hasUtilsLib = true;
            } catch {
                // utils.ts not found
            }

            // Check components directory and installed components
            try {
                const componentsPath = path.join(context.workspacePath, 'src/components/ui');
                const componentsUri = vscode.Uri.file(componentsPath);
                const files = await vscode.workspace.fs.readDirectory(componentsUri);
                
                setup.hasComponentsDir = true;
                setup.installedComponents = files
                    .filter(([name, type]) => type === vscode.FileType.File && name.endsWith('.tsx'))
                    .map(([name]) => name.replace('.tsx', ''));
            } catch {
                // Components directory not found
            }

            const isSetup = setup.hasPackageJson && setup.hasTailwind && 
                           setup.hasComponentsJson && setup.hasUtilsLib && setup.hasComponentsDir;

            return {
                success: true,
                data: {
                    ...setup,
                    isSetup,
                    setupScore: Object.values(setup).filter(v => typeof v === 'boolean' && v).length
                },
                followUpSuggestions: isSetup 
                    ? ['shadcn/ui is properly set up', `${setup.installedComponents.length} components installed`]
                    : ['shadcn/ui setup incomplete', 'Run: npx shadcn-ui@latest init']
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'SETUP_CHECK_ERROR',
                    message: `Failed to check shadcn/ui setup: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * shadcn/ui tools collection
 */
export class ShadcnTools {
    static getAllTools(): PaletteTool[] {
        return [
            installShadcnComponentTool,
            listShadcnComponentsTool,
            checkShadcnSetupTool
        ];
    }

    static registerAll(registry: any): void {
        this.getAllTools().forEach(tool => {
            registry.registerTool(tool, { enabled: true });
        });
        console.log('🎨 Registered shadcn/ui tools');
    }
}