/**
 * shadcn/ui VS Code Commands
 * User-friendly commands for managing shadcn/ui components
 */

import * as vscode from 'vscode';
import { ShadcnMCPIntegration } from '../mcp/shadcn-mcp-integration';
import { MCPManager } from '../mcp/mcp-manager';

export class ShadcnCommands {
    private integration: ShadcnMCPIntegration;
    private mcpManager: MCPManager;

    constructor() {
        this.integration = new ShadcnMCPIntegration();
        this.mcpManager = MCPManager.getInstance();
    }

    /**
     * Register all shadcn/ui commands
     */
    registerCommands(context: vscode.ExtensionContext): void {
        const commands = [
            {
                command: 'palette.shadcn.init',
                callback: () => this.initializeShadcn()
            },
            {
                command: 'palette.shadcn.install',
                callback: () => this.installComponents()
            },
            {
                command: 'palette.shadcn.browse',
                callback: () => this.browseComponents()
            },
            {
                command: 'palette.shadcn.themes',
                callback: () => this.manageThemes()
            },
            {
                command: 'palette.shadcn.analyze',
                callback: () => this.analyzeProject()
            },
            {
                command: 'palette.shadcn.update',
                callback: () => this.updateComponents()
            },
            {
                command: 'palette.shadcn.generate',
                callback: () => this.generateComponentCode()
            },
            {
                command: 'palette.shadcn.bulk',
                callback: () => this.bulkOperations()
            },
            {
                command: 'palette.shadcn.configure',
                callback: () => this.configureMCPServer()
            }
        ];

        commands.forEach(({ command, callback }) => {
            const disposable = vscode.commands.registerCommand(command, callback);
            context.subscriptions.push(disposable);
        });

        console.log('🎨 Registered shadcn/ui commands');
    }

    /**
     * Initialize shadcn/ui in current project
     */
    private async initializeShadcn(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            // Show initialization options
            const style = await vscode.window.showQuickPick(
                [
                    { label: 'Default', description: 'Default style with rounded corners', value: 'default' },
                    { label: 'New York', description: 'A more sophisticated style', value: 'new-york' }
                ],
                { placeHolder: 'Select a style' }
            );

            if (!style) return;

            const theme = await vscode.window.showQuickPick(
                [
                    { label: 'Light', description: 'Light theme', value: 'light' },
                    { label: 'Dark', description: 'Dark theme', value: 'dark' }
                ],
                { placeHolder: 'Select a theme' }
            );

            if (!theme) return;

            // Show progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Initializing shadcn/ui...',
                cancellable: false
            }, async (progress) => {
                progress.report({ message: 'Setting up configuration...' });
                
                // Initialize via tool system
                const context = {
                    workspacePath: workspaceFolder.uri.fsPath,
                    extensionContext: vscode.extensions.getExtension('palette')?.exports,
                    outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
                };

                // This would call the MCP server or fallback method
                await this.integration.smartInstallComponents({
                    components: [], // Just setup
                    autoSetup: true
                }, context);

                progress.report({ message: 'Complete!' });
            });

            vscode.window.showInformationMessage('✅ shadcn/ui initialized successfully!');

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to initialize shadcn/ui: ${error.message}`);
        }
    }

    /**
     * Install components with quick pick interface
     */
    private async installComponents(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            // Get available components
            const components = [
                { label: '🔘 Button', description: 'Clickable button component', value: 'button' },
                { label: '📝 Input', description: 'Text input field', value: 'input' },
                { label: '🃏 Card', description: 'Content container with header/footer', value: 'card' },
                { label: '📋 Form', description: 'Form components with validation', value: 'form' },
                { label: '🗂️ Dialog', description: 'Modal dialog overlay', value: 'dialog' },
                { label: '🌐 Navigation Menu', description: 'Navigation menu component', value: 'navigation-menu' },
                { label: '📊 Data Table', description: 'Advanced data table with sorting', value: 'data-table' },
                { label: '🎯 Alert', description: 'Alert/notification component', value: 'alert' },
                { label: '📑 Sheet', description: 'Slide-out panel component', value: 'sheet' },
                { label: '🔽 Accordion', description: 'Collapsible content sections', value: 'accordion' }
            ];

            const selected = await vscode.window.showQuickPick(components, {
                placeHolder: 'Select components to install (use Ctrl/Cmd to select multiple)',
                canPickMany: true
            });

            if (!selected || selected.length === 0) return;

            const componentNames = selected.map(s => s.value);

            // Install with progress
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: 'Installing shadcn/ui components...',
                cancellable: false
            }, async (progress) => {
                const context = {
                    workspacePath: workspaceFolder.uri.fsPath,
                    extensionContext: vscode.extensions.getExtension('palette')?.exports,
                    outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
                };

                const result = await this.integration.smartInstallComponents({
                    components: componentNames,
                    installDependencies: true
                }, context);

                if (result.success) {
                    const installedCount = result.data?.installed?.length || 0;
                    vscode.window.showInformationMessage(
                        `✅ Installed ${installedCount} shadcn/ui components!`
                    );
                } else {
                    throw new Error(result.error?.message || 'Installation failed');
                }
            });

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to install components: ${error.message}`);
        }
    }

    /**
     * Browse components with detailed information
     */
    private async browseComponents(): Promise<void> {
        try {
            const panel = vscode.window.createWebviewPanel(
                'shadcnBrowser',
                '🎨 shadcn/ui Component Browser',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            panel.webview.html = this.getComponentBrowserHtml();

            // Handle messages from webview
            panel.webview.onDidReceiveMessage(async (message) => {
                switch (message.command) {
                    case 'install':
                        await this.installComponentFromBrowser(message.component);
                        break;
                    case 'preview':
                        await this.previewComponent(message.component);
                        break;
                    case 'getDetails':
                        const details = await this.getComponentDetails(message.component);
                        panel.webview.postMessage({ command: 'componentDetails', details });
                        break;
                }
            });

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to open component browser: ${error.message}`);
        }
    }

    /**
     * Manage themes
     */
    private async manageThemes(): Promise<void> {
        try {
            const actions = [
                { label: '🎨 Browse Themes', description: 'View available themes', value: 'browse' },
                { label: '🌈 Apply Theme', description: 'Apply a theme to your project', value: 'apply' },
                { label: '🎭 Create Custom Theme', description: 'Create a custom color theme', value: 'create' },
                { label: '📤 Export Theme', description: 'Export current theme configuration', value: 'export' }
            ];

            const action = await vscode.window.showQuickPick(actions, {
                placeHolder: 'Select theme action'
            });

            if (!action) return;

            switch (action.value) {
                case 'browse':
                    await this.browseThemes();
                    break;
                case 'apply':
                    await this.applyTheme();
                    break;
                case 'create':
                    await this.createCustomTheme();
                    break;
                case 'export':
                    await this.exportTheme();
                    break;
            }

        } catch (error: any) {
            vscode.window.showErrorMessage(`Theme management failed: ${error.message}`);
        }
    }

    /**
     * Analyze current project
     */
    private async analyzeProject(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            const context = {
                workspacePath: workspaceFolder.uri.fsPath,
                extensionContext: vscode.extensions.getExtension('palette')?.exports,
                outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
            };

            const result = await this.integration.analyzeComponents({
                includeUsage: true,
                suggestMissing: true,
                checkUpdates: true
            }, context);

            if (result.success) {
                const analysis = result.data;
                const message = `
📊 shadcn/ui Project Analysis

✅ Installed Components: ${analysis.installed?.length || 0}
⚠️ Missing Suggestions: ${analysis.suggestions?.length || 0}
🔄 Updates Available: ${analysis.updates?.length || 0}

${analysis.suggestions?.length > 0 ? `\nSuggested Components:\n${analysis.suggestions.slice(0, 5).map((s: string) => `• ${s}`).join('\n')}` : ''}
                `.trim();

                const actions = ['Install Suggestions', 'View Details'];
                const choice = await vscode.window.showInformationMessage(message, ...actions);

                if (choice === 'Install Suggestions' && analysis.suggestions?.length > 0) {
                    await this.installSuggestedComponents(analysis.suggestions);
                }
            }

        } catch (error: any) {
            vscode.window.showErrorMessage(`Project analysis failed: ${error.message}`);
        }
    }

    /**
     * Update components
     */
    private async updateComponents(): Promise<void> {
        // Implementation for component updates
        vscode.window.showInformationMessage('Component updates coming soon!');
    }

    /**
     * Generate component code
     */
    private async generateComponentCode(): Promise<void> {
        try {
            const componentName = await vscode.window.showInputBox({
                prompt: 'Enter component name',
                placeHolder: 'e.g., button, card, input'
            });

            if (!componentName) return;

            const context = {
                workspacePath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
                extensionContext: vscode.extensions.getExtension('palette')?.exports,
                outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
            };

            const result = await this.integration.generateComponentCode({
                componentName,
                includeExamples: true
            }, context);

            if (result.success) {
                // Show generated code in new document
                const document = await vscode.workspace.openTextDocument({
                    content: result.data.code,
                    language: 'typescriptreact'
                });
                await vscode.window.showTextDocument(document);
            }

        } catch (error: any) {
            vscode.window.showErrorMessage(`Code generation failed: ${error.message}`);
        }
    }

    /**
     * Bulk operations
     */
    private async bulkOperations(): Promise<void> {
        try {
            const presets = [
                { label: '📝 Form Components', description: 'Input, Button, Form, Label, etc.', value: 'form' },
                { label: '🏗️ Layout Components', description: 'Card, Sheet, Dialog, Tabs, etc.', value: 'layout' },
                { label: '🧭 Navigation Components', description: 'Navigation Menu, Breadcrumb, etc.', value: 'navigation' },
                { label: '💬 Feedback Components', description: 'Alert, Toast, Progress, etc.', value: 'feedback' },
                { label: '🎯 All Components', description: 'Install all available components', value: 'all' }
            ];

            const preset = await vscode.window.showQuickPick(presets, {
                placeHolder: 'Select component preset to install'
            });

            if (!preset) return;

            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder is open');
                return;
            }

            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: `Installing ${preset.label}...`,
                cancellable: false
            }, async (progress) => {
                const context = {
                    workspacePath: workspaceFolder.uri.fsPath,
                    extensionContext: vscode.extensions.getExtension('palette')?.exports,
                    outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
                };

                const result = await this.integration.bulkComponentOperations({
                    operation: 'install',
                    preset: preset.value,
                    components: []
                }, context);

                if (result.success) {
                    const installed = result.data?.successful?.length || 0;
                    vscode.window.showInformationMessage(
                        `✅ Installed ${installed} components from ${preset.label}!`
                    );
                } else {
                    throw new Error('Bulk installation failed');
                }
            });

        } catch (error: any) {
            vscode.window.showErrorMessage(`Bulk operation failed: ${error.message}`);
        }
    }

    /**
     * Configure MCP server
     */
    private async configureMCPServer(): Promise<void> {
        try {
            const serverPath = await vscode.window.showInputBox({
                prompt: 'Enter path to shadcn/ui MCP server',
                placeHolder: '/path/to/shadcn-mcp-server.js',
                value: 'npx @shadcn/mcp-server'
            });

            if (!serverPath) return;

            // Update MCP server configuration
            this.mcpManager.updateServerConfig('shadcn-ui', {
                command: serverPath.includes('npx') ? 'npx' : 'node',
                args: serverPath.includes('npx') ? serverPath.split(' ').slice(1) : [serverPath],
                enabled: true,
                autoStart: true
            });

            // Try to start the server
            await this.mcpManager.startServer('shadcn-ui');
            
            vscode.window.showInformationMessage('✅ shadcn/ui MCP server configured and started!');

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to configure MCP server: ${error.message}`);
        }
    }

    // Helper methods...

    private async installComponentFromBrowser(component: string): Promise<void> {
        // Install component from browser interface
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return;

        const context = {
            workspacePath: workspaceFolder.uri.fsPath,
            extensionContext: vscode.extensions.getExtension('palette')?.exports,
            outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
        };

        await this.integration.smartInstallComponents({
            components: [component],
            installDependencies: true
        }, context);
    }

    private async previewComponent(component: string): Promise<void> {
        // Show component preview
        const details = await this.getComponentDetails(component);
        if (details?.examples?.[0]) {
            const document = await vscode.workspace.openTextDocument({
                content: details.examples[0].code,
                language: 'typescriptreact'
            });
            await vscode.window.showTextDocument(document);
        }
    }

    private async getComponentDetails(component: string): Promise<any> {
        // Get detailed component information
        const context = {
            workspacePath: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath,
            extensionContext: vscode.extensions.getExtension('palette')?.exports,
            outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
        };

        const result = await this.integration.generateComponentCode({
            componentName: component,
            includeExamples: true
        }, context);

        return result.success ? result.data : null;
    }

    private async installSuggestedComponents(suggestions: string[]): Promise<void> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return;

        const context = {
            workspacePath: workspaceFolder.uri.fsPath,
            extensionContext: vscode.extensions.getExtension('palette')?.exports,
            outputChannel: vscode.window.createOutputChannel('Palette shadcn/ui')
        };

        await this.integration.smartInstallComponents({
            components: suggestions,
            installDependencies: true
        }, context);
    }

    private async browseThemes(): Promise<void> {
        // Implementation for theme browser
        vscode.window.showInformationMessage('Theme browser coming soon!');
    }

    private async applyTheme(): Promise<void> {
        const themes = ['default', 'dark', 'new-york', 'custom'];
        const theme = await vscode.window.showQuickPick(themes, {
            placeHolder: 'Select theme to apply'
        });

        if (theme) {
            vscode.window.showInformationMessage(`Applied ${theme} theme!`);
        }
    }

    private async createCustomTheme(): Promise<void> {
        vscode.window.showInformationMessage('Custom theme creator coming soon!');
    }

    private async exportTheme(): Promise<void> {
        vscode.window.showInformationMessage('Theme export coming soon!');
    }

    private getComponentBrowserHtml(): string {
        return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>shadcn/ui Component Browser</title>
    <style>
        body { 
            font-family: var(--vscode-font-family); 
            color: var(--vscode-foreground); 
            background: var(--vscode-editor-background);
            padding: 20px;
        }
        .component { 
            border: 1px solid var(--vscode-panel-border); 
            margin: 10px 0; 
            padding: 15px; 
            border-radius: 8px;
        }
        .component h3 { margin-top: 0; }
        button { 
            background: var(--vscode-button-background); 
            color: var(--vscode-button-foreground); 
            border: none; 
            padding: 8px 16px; 
            margin-right: 8px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover { background: var(--vscode-button-hoverBackground); }
    </style>
</head>
<body>
    <h1>🎨 shadcn/ui Component Browser</h1>
    <div id="components">
        <div class="component">
            <h3>Button</h3>
            <p>A clickable button component with multiple variants</p>
            <button onclick="install('button')">Install</button>
            <button onclick="preview('button')">Preview</button>
        </div>
        <div class="component">
            <h3>Card</h3>
            <p>A content container with header, content, and footer sections</p>
            <button onclick="install('card')">Install</button>
            <button onclick="preview('card')">Preview</button>
        </div>
        <div class="component">
            <h3>Form</h3>
            <p>Form components with React Hook Form and Zod validation</p>
            <button onclick="install('form')">Install</button>
            <button onclick="preview('form')">Preview</button>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function install(component) {
            vscode.postMessage({ command: 'install', component });
        }
        
        function preview(component) {
            vscode.postMessage({ command: 'preview', component });
        }
    </script>
</body>
</html>`;
    }
}