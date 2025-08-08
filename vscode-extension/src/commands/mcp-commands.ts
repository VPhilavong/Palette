/**
 * MCP Server Commands
 * User-friendly commands for managing MCP server configurations
 */

import * as vscode from 'vscode';
import { MCPManager } from '../mcp/mcp-manager';

export class MCPCommands {
    private mcpManager: MCPManager;

    constructor() {
        this.mcpManager = MCPManager.getInstance();
    }

    /**
     * Register all MCP-related commands
     */
    registerCommands(context: vscode.ExtensionContext): void {
        const commands = [
            {
                command: 'palette.mcp.setup',
                callback: () => this.showSetupGuide()
            },
            {
                command: 'palette.mcp.status',
                callback: () => this.showStatus()
            },
            {
                command: 'palette.mcp.configure',
                callback: () => this.openConfiguration()
            },
            {
                command: 'palette.mcp.troubleshoot',
                callback: () => this.showTroubleshooting()
            }
        ];

        commands.forEach(({ command, callback }) => {
            try {
                const disposable = vscode.commands.registerCommand(command, callback);
                context.subscriptions.push(disposable);
            } catch (error) {
                console.warn(`🔌 Command ${command} already registered, skipping`);
            }
        });

        console.log('🔌 Registered MCP commands');
    }

    /**
     * Show MCP setup guide
     */
    private async showSetupGuide(): Promise<void> {
        const setupOptions = [
            'Open MCP Settings',
            'View Documentation',
            'Skip (Use Fallback Mode)'
        ];

        const choice = await vscode.window.showInformationMessage(
            '🔌 **MCP Server Setup**\n\nMCP (Model Context Protocol) servers provide additional AI capabilities. The system works without them using fallback tools.\n\n**Available MCP Servers:**\n• **Git** - Enhanced version control operations\n• **Filesystem** - Advanced file management\n• **shadcn/ui** - Component management (requires separate installation)\n\nWould you like to configure MCP servers or continue with fallback mode?',
            { modal: true },
            ...setupOptions
        );

        switch (choice) {
            case 'Open MCP Settings':
                await this.openConfiguration();
                break;
            case 'View Documentation':
                await vscode.env.openExternal(vscode.Uri.parse('https://modelcontextprotocol.io/docs'));
                break;
            case 'Skip (Use Fallback Mode)':
                vscode.window.showInformationMessage('👍 Using fallback mode. All features will work with built-in alternatives.');
                break;
        }
    }

    /**
     * Show current MCP status
     */
    private async showStatus(): Promise<void> {
        const stats = this.mcpManager.getStatistics();
        
        const serverDetails = Object.entries(stats.serverStatuses)
            .map(([name, status]) => `• **${name}**: ${status}`)
            .join('\n');

        const message = `🔌 **MCP Server Status**

**System Overview:**
• Total Servers: ${stats.totalServers}
• Running Servers: ${stats.runningServers}
• Available Tools: ${stats.totalTools}

**Server Details:**
${serverDetails || 'No servers configured'}

**Fallback Mode:** ${stats.runningServers === 0 ? '✅ Active (recommended for beginners)' : 'Inactive'}`;

        const actions = ['Configure Servers', 'Troubleshoot'];
        const choice = await vscode.window.showInformationMessage(
            message,
            { modal: true },
            ...actions
        );

        switch (choice) {
            case 'Configure Servers':
                await this.openConfiguration();
                break;
            case 'Troubleshoot':
                await this.showTroubleshooting();
                break;
        }
    }

    /**
     * Open MCP configuration settings
     */
    private async openConfiguration(): Promise<void> {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp');
        
        // Show helpful guidance
        vscode.window.showInformationMessage(
            '⚙️ **MCP Configuration Tips:**\n\n• Start with **disabled servers** - the system works great without them\n• **Git server** requires `@modelcontextprotocol/server-git` package\n• **Filesystem server** requires `@modelcontextprotocol/server-filesystem` package\n• **shadcn/ui server** is optional for enhanced component management',
            'View Examples'
        ).then(choice => {
            if (choice === 'View Examples') {
                this.showConfigurationExamples();
            }
        });
    }

    /**
     * Show troubleshooting guide
     */
    private async showTroubleshooting(): Promise<void> {
        const issues = [
            {
                issue: '🚨 Server timeout errors',
                solution: 'Servers are not installed or accessible. This is normal - fallback mode provides all functionality.'
            },
            {
                issue: '🚨 "Module not found" errors',
                solution: 'Install MCP servers with: `npm install @modelcontextprotocol/server-git @modelcontextprotocol/server-filesystem`'
            },
            {
                issue: '🚨 Permission errors',
                solution: 'MCP servers need proper file permissions. Try running VS Code as administrator or adjust file permissions.'
            },
            {
                issue: '💡 Performance is fine without MCP',
                solution: 'MCP servers are optional enhancements. The system includes high-quality fallback tools.'
            }
        ];

        const troubleshootingText = issues.map(({ issue, solution }) => 
            `**${issue}**\n${solution}\n`
        ).join('\n');

        const actions = ['Install MCP Servers', 'Disable All Servers', 'View Logs'];
        const choice = await vscode.window.showInformationMessage(
            `🔧 **MCP Troubleshooting Guide**\n\n${troubleshootingText}`,
            { modal: true },
            ...actions
        );

        switch (choice) {
            case 'Install MCP Servers':
                await this.showInstallationGuide();
                break;
            case 'Disable All Servers':
                await this.disableAllServers();
                break;
            case 'View Logs':
                vscode.commands.executeCommand('workbench.action.showLogs');
                break;
        }
    }

    /**
     * Show configuration examples
     */
    private showConfigurationExamples(): void {
        const exampleConfig = {
            "palette.mcp.enabled": true,
            "palette.mcp.servers": [
                {
                    "name": "git",
                    "description": "Git operations",
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-git", "--repository", "${workspaceFolder}"],
                    "enabled": false,
                    "autoStart": false
                },
                {
                    "name": "filesystem",
                    "description": "File operations", 
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-filesystem", "${workspaceFolder}"],
                    "enabled": false,
                    "autoStart": false
                }
            ]
        };

        vscode.workspace.openTextDocument({
            content: JSON.stringify(exampleConfig, null, 2),
            language: 'json'
        }).then(doc => {
            vscode.window.showTextDocument(doc);
        });
    }

    /**
     * Show installation guide
     */
    private async showInstallationGuide(): Promise<void> {
        const installCommands = [
            'npm install -g @modelcontextprotocol/server-git',
            'npm install -g @modelcontextprotocol/server-filesystem',
            'npm install -g @shadcn/mcp-server'
        ];

        const terminal = vscode.window.createTerminal('MCP Server Installation');
        terminal.show();
        
        const choice = await vscode.window.showInformationMessage(
            '📦 **Installing MCP Servers**\n\nRun these commands in the terminal to install MCP servers:\n\n' + installCommands.join('\n'),
            'Run in Terminal',
            'Copy Commands'
        );

        if (choice === 'Run in Terminal') {
            installCommands.forEach(cmd => terminal.sendText(cmd));
        } else if (choice === 'Copy Commands') {
            vscode.env.clipboard.writeText(installCommands.join('\n'));
            vscode.window.showInformationMessage('📋 Commands copied to clipboard');
        }
    }

    /**
     * Disable all MCP servers for users who want fallback-only mode
     */
    private async disableAllServers(): Promise<void> {
        const config = vscode.workspace.getConfiguration('palette.mcp');
        await config.update('enabled', false, vscode.ConfigurationTarget.Global);
        
        vscode.window.showInformationMessage(
            '✅ **MCP servers disabled**\n\nAll features will use high-quality fallback tools. You can re-enable MCP servers anytime in settings.',
            'Open Settings'
        ).then(choice => {
            if (choice === 'Open Settings') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp');
            }
        });
    }
}