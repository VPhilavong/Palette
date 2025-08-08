/**
 * MCP Management Commands
 * VS Code commands for managing MCP servers and configuration
 */

import * as vscode from 'vscode';
import { MCPManager } from './mcp-manager';
import { MCPConfigManager } from './mcp-config-manager';
import { MCPFallbackManager } from './mcp-fallback-manager';
import { MCPServerConfig } from './types';

export class MCPCommands {
    private mcpManager: MCPManager;
    private configManager: MCPConfigManager;
    private fallbackManager: MCPFallbackManager;

    constructor() {
        this.mcpManager = MCPManager.getInstance();
        this.configManager = MCPConfigManager.getInstance();
        this.fallbackManager = MCPFallbackManager.getInstance();
    }

    /**
     * Register all MCP-related commands
     */
    registerCommands(context: vscode.ExtensionContext): void {
        const commands = [
            vscode.commands.registerCommand('palette.mcp.status', () => this.showMCPStatus()),
            vscode.commands.registerCommand('palette.mcp.configure', () => this.configureMCP()),
            vscode.commands.registerCommand('palette.mcp.restart', () => this.restartMCP()),
            vscode.commands.registerCommand('palette.mcp.addServer', () => this.addServer()),
            vscode.commands.registerCommand('palette.mcp.removeServer', () => this.removeServer()),
            vscode.commands.registerCommand('palette.mcp.startServer', () => this.startServer()),
            vscode.commands.registerCommand('palette.mcp.stopServer', () => this.stopServer()),
            vscode.commands.registerCommand('palette.mcp.showLogs', () => this.showLogs()),
            vscode.commands.registerCommand('palette.mcp.resetConfig', () => this.resetConfiguration()),
            vscode.commands.registerCommand('palette.mcp.enableFallback', () => this.enableFallbackMode()),
            vscode.commands.registerCommand('palette.mcp.disableFallback', () => this.disableFallbackMode()),
            vscode.commands.registerCommand('palette.mcp.setupGuide', () => this.showSetupGuide())
        ];

        commands.forEach(command => context.subscriptions.push(command));
        console.log('🔌 MCP commands registered');
    }

    /**
     * Show MCP status and statistics
     */
    private async showMCPStatus(): Promise<void> {
        const stats = this.mcpManager.getStatistics();
        const configReport = stats.configurationReport;

        const statusItems: vscode.QuickPickItem[] = [
            {
                label: '$(info) MCP Status',
                detail: `Enabled: ${stats.enabled ? 'Yes' : 'No'} | Running Servers: ${stats.runningServers}/${stats.totalServers}`,
                kind: vscode.QuickPickItemKind.Separator
            }
        ];

        // Add server status items
        for (const [serverName, status] of Object.entries(stats.serverStatuses)) {
            const icon = this.getStatusIcon(status);
            const fallback = stats.fallbackStatus[serverName];
            const fallbackInfo = fallback?.hasFallback ? ` (${fallback.toolCount} fallback tools)` : '';
            
            statusItems.push({
                label: `${icon} ${serverName}`,
                detail: `Status: ${status}${fallbackInfo}`,
                description: status === 'error' ? 'Click to restart' : undefined
            });
        }

        statusItems.push(
            { label: '', kind: vscode.QuickPickItemKind.Separator },
            {
                label: '$(tools) Tools',
                detail: `MCP Tools: ${stats.totalTools} | Fallback Tools: ${stats.fallbackTools}`,
                kind: vscode.QuickPickItemKind.Separator
            },
            {
                label: '$(gear) Configure MCP',
                detail: 'Open MCP settings',
                description: 'Configure servers and options'
            },
            {
                label: '$(refresh) Restart MCP',
                detail: 'Restart all MCP servers',
                description: 'Fix connection issues'
            }
        );

        if (configReport.recommendations.length > 0) {
            statusItems.push(
                { label: '', kind: vscode.QuickPickItemKind.Separator },
                {
                    label: '$(warning) Recommendations',
                    detail: `${configReport.recommendations.length} suggestions available`,
                    kind: vscode.QuickPickItemKind.Separator
                }
            );

            configReport.recommendations.forEach((rec: string) => {
                statusItems.push({
                    label: `$(lightbulb) ${rec}`,
                    detail: 'Configuration recommendation'
                });
            });
        }

        const selected = await vscode.window.showQuickPick(statusItems, {
            title: 'MCP Status',
            placeHolder: 'Select an action or view status information'
        });

        if (selected) {
            if (selected.label.includes('Configure MCP')) {
                await this.configureMCP();
            } else if (selected.label.includes('Restart MCP')) {
                await this.restartMCP();
            } else if (selected.description === 'Click to restart') {
                const serverName = selected.label.split(' ')[1];
                await this.mcpManager.restartServer(serverName);
            }
        }
    }

    /**
     * Open MCP configuration
     */
    private async configureMCP(): Promise<void> {
        const options: vscode.QuickPickItem[] = [
            {
                label: '$(gear) General Settings',
                detail: 'MCP enabled, timeouts, retry settings',
                description: 'Open MCP settings page'
            },
            {
                label: '$(server) Server Configuration',
                detail: 'Add, remove, and configure MCP servers',
                description: 'Manage server list'
            },
            {
                label: '$(shield) Fallback Mode',
                detail: 'Configure fallback behavior when servers are unavailable',
                description: 'Graceful degradation options'
            },
            {
                label: '$(question) Setup Guide',
                detail: 'Step-by-step guide for setting up MCP servers',
                description: 'Learn how to configure MCP'
            }
        ];

        const selected = await vscode.window.showQuickPick(options, {
            title: 'Configure MCP',
            placeHolder: 'Select configuration category'
        });

        if (selected) {
            if (selected.label.includes('General Settings')) {
                vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp');
            } else if (selected.label.includes('Server Configuration')) {
                vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp.servers');
            } else if (selected.label.includes('Fallback Mode')) {
                await this.configureFallbackMode();
            } else if (selected.label.includes('Setup Guide')) {
                await this.showSetupGuide();
            }
        }
    }

    /**
     * Configure fallback mode
     */
    private async configureFallbackMode(): Promise<void> {
        const currentConfig = this.configManager.loadConfiguration();
        if (!currentConfig.config) return;

        const options: vscode.QuickPickItem[] = [
            {
                label: 'Graceful',
                detail: 'Use fallback tools when servers are unavailable (recommended)',
                picked: currentConfig.config.fallbackMode === 'graceful'
            },
            {
                label: 'Always',
                detail: 'Always use fallback tools instead of MCP servers',
                picked: currentConfig.config.fallbackMode === 'always'
            },
            {
                label: 'Disabled',
                detail: 'Never use fallback tools (may reduce functionality)',
                picked: currentConfig.config.fallbackMode === 'disabled'
            }
        ];

        const selected = await vscode.window.showQuickPick(options, {
            title: 'Configure Fallback Mode',
            placeHolder: 'Select fallback behavior when MCP servers are unavailable'
        });

        if (selected) {
            const mode = selected.label.toLowerCase() as 'graceful' | 'always' | 'disabled';
            const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
            await vsConfig.update('fallbackMode', mode, vscode.ConfigurationTarget.Global);
            
            vscode.window.showInformationMessage(`Fallback mode set to: ${selected.label}`);
        }
    }

    /**
     * Restart MCP manager
     */
    private async restartMCP(): Promise<void> {
        const confirm = await vscode.window.showWarningMessage(
            'Restart MCP Manager?',
            'This will restart all MCP servers and may interrupt ongoing operations.',
            'Restart',
            'Cancel'
        );

        if (confirm === 'Restart') {
            try {
                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'Restarting MCP Manager...',
                    cancellable: false
                }, async (progress) => {
                    progress.report({ increment: 25, message: 'Stopping servers...' });
                    await this.mcpManager.stop();
                    
                    progress.report({ increment: 50, message: 'Starting servers...' });
                    await this.mcpManager.start();
                    
                    progress.report({ increment: 100, message: 'Complete' });
                });

                vscode.window.showInformationMessage('MCP Manager restarted successfully');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to restart MCP Manager: ${error.message}`);
            }
        }
    }

    /**
     * Add a new MCP server
     */
    private async addServer(): Promise<void> {
        const templates: vscode.QuickPickItem[] = [
            {
                label: 'Filesystem Server',
                detail: 'File system operations and directory management',
                description: '@modelcontextprotocol/server-filesystem'
            },
            {
                label: 'Git Server',
                detail: 'Git version control operations',
                description: '@modelcontextprotocol/server-git'
            },
            {
                label: 'Custom Server',
                detail: 'Configure a custom MCP server',
                description: 'Manual configuration'
            }
        ];

        const selected = await vscode.window.showQuickPick(templates, {
            title: 'Add MCP Server',
            placeHolder: 'Select server type or template'
        });

        if (!selected) return;

        let config: MCPServerConfig;

        if (selected.label === 'Filesystem Server') {
            config = {
                name: 'filesystem',
                description: 'File system operations and directory management',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
                enabled: true,
                autoStart: false,
                tools: ['read_file', 'write_file', 'create_directory', 'list_directory', 'move_file', 'search_files'],
                resources: ['file', 'directory']
            };
        } else if (selected.label === 'Git Server') {
            config = {
                name: 'git',
                description: 'Git version control operations',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-git'],
                enabled: true,
                autoStart: false,
                tools: ['git_status', 'git_add', 'git_commit', 'git_log', 'git_diff', 'git_branch'],
                resources: ['repository', 'commit', 'branch']
            };
        } else {
            // Custom server - collect details
            const name = await vscode.window.showInputBox({
                title: 'Server Name',
                prompt: 'Enter a unique name for the MCP server',
                validateInput: (value) => {
                    if (!value || value.trim().length === 0) {
                        return 'Server name is required';
                    }
                    if (this.mcpManager.getServerConfig(value.trim())) {
                        return 'Server name already exists';
                    }
                    return undefined;
                }
            });

            if (!name) return;

            const command = await vscode.window.showInputBox({
                title: 'Command',
                prompt: 'Enter the command to start the server (e.g., node, python, npx)',
                value: 'npx'
            });

            if (!command) return;

            const description = await vscode.window.showInputBox({
                title: 'Description',
                prompt: 'Enter a description for the server',
                value: `Custom MCP server: ${name}`
            });

            config = {
                name: name.trim(),
                description: description || `Custom MCP server: ${name}`,
                command: command.trim(),
                args: [],
                enabled: true,
                autoStart: false,
                tools: [],
                resources: []
            };
        }

        try {
            await this.mcpManager.addServerConfig(config);
            vscode.window.showInformationMessage(`Added MCP server: ${config.name}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to add server: ${error.message}`);
        }
    }

    /**
     * Remove an MCP server
     */
    private async removeServer(): Promise<void> {
        const stats = this.mcpManager.getStatistics();
        const serverItems: vscode.QuickPickItem[] = [];

        for (const [serverName, status] of Object.entries(stats.serverStatuses)) {
            const icon = this.getStatusIcon(status);
            serverItems.push({
                label: `${icon} ${serverName}`,
                detail: `Status: ${status}`,
                description: status === 'running' ? 'Will stop server before removal' : undefined
            });
        }

        if (serverItems.length === 0) {
            vscode.window.showInformationMessage('No MCP servers configured');
            return;
        }

        const selected = await vscode.window.showQuickPick(serverItems, {
            title: 'Remove MCP Server',
            placeHolder: 'Select server to remove'
        });

        if (!selected) return;

        const serverName = selected.label.split(' ')[1];
        const confirm = await vscode.window.showWarningMessage(
            `Remove MCP server "${serverName}"?`,
            'This will permanently remove the server configuration.',
            'Remove',
            'Cancel'
        );

        if (confirm === 'Remove') {
            try {
                await this.mcpManager.removeServerConfig(serverName);
                vscode.window.showInformationMessage(`Removed MCP server: ${serverName}`);
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to remove server: ${error.message}`);
            }
        }
    }

    /**
     * Start a specific server
     */
    private async startServer(): Promise<void> {
        const stats = this.mcpManager.getStatistics();
        const serverItems: vscode.QuickPickItem[] = [];

        for (const [serverName, status] of Object.entries(stats.serverStatuses)) {
            if (status !== 'running') {
                const icon = this.getStatusIcon(status);
                serverItems.push({
                    label: `${icon} ${serverName}`,
                    detail: `Status: ${status}`
                });
            }
        }

        if (serverItems.length === 0) {
            vscode.window.showInformationMessage('All MCP servers are already running');
            return;
        }

        const selected = await vscode.window.showQuickPick(serverItems, {
            title: 'Start MCP Server',
            placeHolder: 'Select server to start'
        });

        if (!selected) return;

        const serverName = selected.label.split(' ')[1];
        try {
            await this.mcpManager.startServer(serverName);
            vscode.window.showInformationMessage(`Started MCP server: ${serverName}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to start server: ${error.message}`);
        }
    }

    /**
     * Stop a specific server
     */
    private async stopServer(): Promise<void> {
        const stats = this.mcpManager.getStatistics();
        const serverItems: vscode.QuickPickItem[] = [];

        for (const [serverName, status] of Object.entries(stats.serverStatuses)) {
            if (status === 'running') {
                serverItems.push({
                    label: `$(debug-start) ${serverName}`,
                    detail: 'Running'
                });
            }
        }

        if (serverItems.length === 0) {
            vscode.window.showInformationMessage('No MCP servers are currently running');
            return;
        }

        const selected = await vscode.window.showQuickPick(serverItems, {
            title: 'Stop MCP Server',
            placeHolder: 'Select server to stop'
        });

        if (!selected) return;

        const serverName = selected.label.split(' ')[1];
        try {
            await this.mcpManager.stopServer(serverName);
            vscode.window.showInformationMessage(`Stopped MCP server: ${serverName}`);
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to stop server: ${error.message}`);
        }
    }

    /**
     * Show MCP logs (placeholder)
     */
    private async showLogs(): Promise<void> {
        // In a real implementation, you would show logs in an output channel
        const outputChannel = vscode.window.createOutputChannel('MCP Logs');
        outputChannel.show();
        outputChannel.appendLine('MCP Server Logs');
        outputChannel.appendLine('==================');
        outputChannel.appendLine('Logs would be displayed here...');
        
        vscode.window.showInformationMessage('MCP logs opened in Output panel');
    }

    /**
     * Reset MCP configuration to defaults
     */
    private async resetConfiguration(): Promise<void> {
        const confirm = await vscode.window.showWarningMessage(
            'Reset MCP configuration to defaults?',
            'This will remove all custom server configurations and settings.',
            'Reset',
            'Cancel'
        );

        if (confirm === 'Reset') {
            try {
                await this.configManager.resetToDefaults();
                vscode.window.showInformationMessage('MCP configuration reset to defaults');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to reset configuration: ${error.message}`);
            }
        }
    }

    /**
     * Enable fallback mode
     */
    private async enableFallbackMode(): Promise<void> {
        const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
        await vsConfig.update('fallbackMode', 'always', vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage('Fallback mode enabled - using local tools instead of MCP servers');
    }

    /**
     * Disable fallback mode
     */
    private async disableFallbackMode(): Promise<void> {
        const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
        await vsConfig.update('fallbackMode', 'disabled', vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage('Fallback mode disabled - MCP servers required for functionality');
    }

    /**
     * Show setup guide
     */
    private async showSetupGuide(): Promise<void> {
        const guideItems: vscode.QuickPickItem[] = [
            {
                label: '$(question) What is MCP?',
                detail: 'Learn about Model Context Protocol and its benefits'
            },
            {
                label: '$(server) Common MCP Servers',
                detail: 'Popular MCP servers and their capabilities'
            },
            {
                label: '$(gear) Installation Guide',
                detail: 'How to install and configure MCP servers'
            },
            {
                label: '$(tools) Available Tools',
                detail: 'Tools provided by each MCP server type'
            },
            {
                label: '$(shield) Fallback Options',
                detail: 'What happens when MCP servers are unavailable'
            },
            {
                label: '$(bug) Troubleshooting',
                detail: 'Common issues and solutions'
            }
        ];

        const selected = await vscode.window.showQuickPick(guideItems, {
            title: 'MCP Setup Guide',
            placeHolder: 'Select a topic to learn more'
        });

        if (selected) {
            // In a real implementation, you would show detailed guides
            // For now, open the MCP documentation
            vscode.env.openExternal(vscode.Uri.parse('https://modelcontextprotocol.io/introduction'));
        }
    }

    /**
     * Get status icon for server status
     */
    private getStatusIcon(status: string): string {
        switch (status) {
            case 'running': return '$(debug-start)';
            case 'starting': return '$(loading~spin)';
            case 'error': return '$(error)';
            case 'disconnected': return '$(debug-disconnect)';
            case 'stopped': return '$(debug-stop)';
            default: return '$(circle-outline)';
        }
    }
}