/**
 * Integration Manager
 * Centralized initialization and management of all AI integration systems
 */

import * as vscode from 'vscode';
import { MCPCommands } from '../commands/mcp-commands';
import { ShadcnCommands } from '../commands/shadcn-commands';
import { MCPManager } from '../mcp/mcp-manager';
import { ShadcnMCPIntegration } from '../mcp/shadcn-mcp-integration';
import { initializeToolSystem } from '../tools';
import { BatchFileManager } from '../tools/batch-file-manager';
import { EnhancedApprovalHandler } from '../tools/enhanced-approval-handler';
import { ToolExecutor } from '../tools/tool-executor';
import { ToolRegistry } from '../tools/tool-registry';

export class IntegrationManager {
    private static instance: IntegrationManager | null = null;
    
    private mcpManager?: MCPManager;
    private toolRegistry?: ToolRegistry;
    private toolExecutor?: ToolExecutor;
    private approvalHandler?: EnhancedApprovalHandler;
    private batchFileManager?: BatchFileManager;
    private shadcnIntegration?: ShadcnMCPIntegration;
    private shadcnCommands?: ShadcnCommands;
    private mcpCommands?: MCPCommands;
    private extensionUri?: vscode.Uri;
    private isInitialized: boolean = false;
    private commandsRegistered: boolean = false;

    private constructor() {
        console.log('🚀 Integration Manager created');
    }

    static getInstance(): IntegrationManager {
        if (!this.instance) {
            this.instance = new IntegrationManager();
        }
        return this.instance;
    }

    /**
     * Initialize all integration systems
     */
    async initialize(extensionUri?: vscode.Uri, extensionContext?: vscode.ExtensionContext): Promise<void> {
        this.extensionUri = extensionUri;
        if (this.isInitialized) {
            console.log('🚀 Integration Manager already initialized');
            return;
        }

        console.log('🚀 Initializing Integration Manager...');

        try {
            // 1. Initialize core tool system
            await this.initializeToolSystem();

            // 2. Initialize MCP system
            await this.initializeMCPSystem();

            // 3. Initialize shadcn/ui integration
            await this.initializeShadcnIntegration();

            // 4. Set up VS Code integration
            await this.initializeVSCodeIntegration(extensionContext);

            this.isInitialized = true;
            console.log('🚀 Integration Manager initialized successfully');

        } catch (error) {
            console.error('🚀 Failed to initialize Integration Manager:', error);
            throw error;
        }
    }

    /**
     * Shutdown all integration systems
     */
    async shutdown(): Promise<void> {
        if (!this.isInitialized) {
            return;
        }

        console.log('🚀 Shutting down Integration Manager...');

        try {
            // Stop MCP servers
            if (this.mcpManager) {
                await this.mcpManager.stop();
            }

            // Dispose of UI components
            if (this.approvalHandler) {
                this.approvalHandler.dispose();
            }

            if (this.batchFileManager) {
                this.batchFileManager.dispose();
            }

            this.isInitialized = false;
            console.log('🚀 Integration Manager shutdown complete');

        } catch (error) {
            console.error('🚀 Error during shutdown:', error);
        }
    }

    /**
     * Get MCP Manager instance
     */
    getMCPManager(): MCPManager | undefined {
        return this.mcpManager;
    }

    /**
     * Get Tool Registry instance
     */
    getToolRegistry(): ToolRegistry | undefined {
        return this.toolRegistry;
    }

    /**
     * Get Tool Executor instance
     */
    getToolExecutor(): ToolExecutor | undefined {
        return this.toolExecutor;
    }

    /**
     * Check if system is initialized
     */
    isSystemInitialized(): boolean {
        return this.isInitialized;
    }

    /**
     * Get system status
     */
    getSystemStatus(): {
        initialized: boolean;
        toolSystem: boolean;
        mcpSystem: boolean;
        totalTools: number;
        mcpServers: number;
        runningServers: number;
    } {
        const toolStats = this.toolRegistry?.getStatistics();
        const mcpStats = this.mcpManager?.getStatistics();

        return {
            initialized: this.isInitialized,
            toolSystem: !!this.toolRegistry,
            mcpSystem: !!this.mcpManager,
            totalTools: toolStats?.totalTools || 0,
            mcpServers: mcpStats?.totalServers || 0,
            runningServers: mcpStats?.runningServers || 0
        };
    }

    /**
     * Initialize the core tool system
     */
    private async initializeToolSystem(): Promise<void> {
        console.log('🔧 Initializing tool system...');

        // Initialize tool registry and executor
        this.toolRegistry = ToolRegistry.getInstance();
        this.toolExecutor = ToolExecutor.getInstance();

        // Register all core tools
        await initializeToolSystem();

        // Set up approval handler for dangerous operations
        this.setupToolApprovalHandler();

        console.log('🔧 Tool system initialized');
    }

    /**
     * Initialize the MCP system
     */
    private async initializeMCPSystem(): Promise<void> {
        console.log('🔌 Initializing MCP system...');

        this.mcpManager = MCPManager.getInstance();

        // Set up MCP event handlers
        this.setupMCPEventHandlers();

        // Start MCP manager (will auto-start enabled servers)
        await this.mcpManager.start();

        console.log('🔌 MCP system initialized');
    }

    /**
     * Initialize shadcn/ui integration
     */
    private async initializeShadcnIntegration(): Promise<void> {
        console.log('🎨 Initializing shadcn/ui integration...');

        try {
            // Initialize shadcn/ui MCP integration
            this.shadcnIntegration = new ShadcnMCPIntegration();
            await this.shadcnIntegration.initialize();

            console.log('🎨 shadcn/ui integration initialized');
        } catch (error) {
            console.warn('🎨 shadcn/ui integration failed, running in fallback mode:', error);
            // Continue without shadcn/ui MCP integration
        }
    }

    /**
     * Initialize VS Code integration
     */
    private async initializeVSCodeIntegration(extensionContext?: vscode.ExtensionContext): Promise<void> {
        console.log('📱 Setting up VS Code integration...');

        // Register commands for tool and MCP management
        this.registerVSCodeCommands();

        // Register shadcn/ui commands
        this.registerShadcnCommands(extensionContext);

        // Register MCP commands
        this.registerMCPCommands(extensionContext);

        // Set up status bar integration
        this.setupStatusBarIntegration();

        console.log('📱 VS Code integration ready');
    }

    /**
     * Set up tool approval handler
     */
    private setupToolApprovalHandler(): void {
        if (!this.toolExecutor || !this.extensionUri) return;

        // Initialize enhanced approval handler
        this.approvalHandler = new EnhancedApprovalHandler(this.extensionUri);
        this.batchFileManager = new BatchFileManager(this.extensionUri);

        // Set the enhanced approval handler on the tool executor
        this.toolExecutor.setApprovalHandler(this.approvalHandler);

        // Register batch file tool
        if (this.toolRegistry) {
            const batchFileTool = this.batchFileManager.createBatchFilesTool();
            this.toolRegistry.registerTool(batchFileTool, { enabled: true });
            console.log('📦 Registered batch file operations tool');
        }
    }

    /**
     * Set up MCP event handlers
     */
    private setupMCPEventHandlers(): void {
        if (!this.mcpManager) return;

        this.mcpManager.on('server-started', (serverName: string) => {
            vscode.window.showInformationMessage(`🔌 MCP Server started: ${serverName}`);
        });

        this.mcpManager.on('server-stopped', (serverName: string) => {
            vscode.window.showInformationMessage(`🔌 MCP Server stopped: ${serverName}`);
        });

        this.mcpManager.on('server-error', (serverName: string, error: string) => {
            vscode.window.showErrorMessage(`🔌 MCP Server error (${serverName}): ${error}`);
        });

        this.mcpManager.on('tool-registered', (tool) => {
            console.log(`🔧 MCP tool registered: ${tool.name} from ${tool.serverName}`);
        });
    }

    /**
     * Register VS Code commands
     */
    private registerVSCodeCommands(): void {
        const commands = [
            {
                command: 'palette.tools.status',
                title: '🔧 Show Tool System Status',
                callback: () => this.showToolSystemStatus()
            },
            {
                command: 'palette.mcp.status',
                title: '🔌 Show MCP Server Status',
                callback: () => this.showMCPStatus()
            },
            {
                command: 'palette.mcp.restart',
                title: '🔌 Restart MCP Servers',
                callback: () => this.restartMCPServers()
            },
            {
                command: 'palette.approvals.preferences',
                title: '⚙️ Show Approval Preferences',
                callback: () => this.showApprovalPreferences()
            },
            {
                command: 'palette.approvals.reset',
                title: '🔄 Reset Approval Preferences',
                callback: () => this.resetApprovalPreferences()
            },
            {
                command: 'palette.integration.status',
                title: '🚀 Show Integration Status',
                callback: () => this.showIntegrationStatus()
            }
        ];

        commands.forEach(({ command, callback }) => {
            vscode.commands.registerCommand(command, callback);
        });
    }

    /**
     * Register shadcn/ui commands
     */
    private registerShadcnCommands(extensionContext?: vscode.ExtensionContext): void {
        if (!this.extensionUri || !extensionContext || this.commandsRegistered) return;

        // Initialize shadcn commands
        this.shadcnCommands = new ShadcnCommands();

        // Register commands with VS Code
        this.shadcnCommands.registerCommands(extensionContext);
        
        console.log('🎨 shadcn/ui commands registered');
    }

    /**
     * Register MCP commands
     */
    private registerMCPCommands(extensionContext?: vscode.ExtensionContext): void {
        if (!extensionContext || this.commandsRegistered) return;

        // Initialize MCP commands
        this.mcpCommands = new MCPCommands();

        // Register commands with VS Code
        this.mcpCommands.registerCommands(extensionContext);
        this.commandsRegistered = true;
        
        console.log('🔌 MCP commands registered');
    }

    /**
     * Set up status bar integration
     */
    private setupStatusBarIntegration(): void {
        const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        statusBarItem.command = 'palette.integration.status';
        statusBarItem.text = '$(tools) Palette AI';
        statusBarItem.tooltip = 'Palette AI Integration Status';
        statusBarItem.show();

        // Update status periodically
        setInterval(() => {
            const status = this.getSystemStatus();
            const icon = status.initialized ? '$(check)' : '$(alert)';
            const shadcnStatus = this.shadcnIntegration ? '🎨' : '';
            statusBarItem.text = `${icon} Palette AI ${shadcnStatus}(${status.totalTools} tools, ${status.runningServers}/${status.mcpServers} servers)`;
        }, 10000); // Update every 10 seconds
    }

    /**
     * Show tool system status
     */
    private async showToolSystemStatus(): Promise<void> {
        if (!this.toolRegistry || !this.toolExecutor) {
            vscode.window.showErrorMessage('Tool system not initialized');
            return;
        }

        const stats = this.toolRegistry.getStatistics();
        const execStats = this.toolExecutor.getExecutionStatistics();

        const message = `
Tool System Status:
• Total Tools: ${stats.totalTools}
• Enabled Tools: ${stats.enabledTools}
• Total Executions: ${execStats.totalExecutions}
• Success Rate: ${execStats.successRate.toFixed(1)}%
• Average Execution Time: ${execStats.averageExecutionTime.toFixed(2)}ms

Categories:
${Object.entries(stats.categories).map(([cat, count]) => `• ${cat}: ${count}`).join('\n')}

Active Tools: ${execStats.activeTools.join(', ')}
        `.trim();

        vscode.window.showInformationMessage(message, { modal: true });
    }

    /**
     * Show MCP server status
     */
    private async showMCPStatus(): Promise<void> {
        if (!this.mcpManager) {
            vscode.window.showErrorMessage('MCP system not initialized');
            return;
        }

        const stats = this.mcpManager.getStatistics();
        const statuses = Object.entries(stats.serverStatuses)
            .map(([name, status]) => `• ${name}: ${status}`)
            .join('\n');

        const message = `
MCP Server Status:
• Total Servers: ${stats.totalServers}
• Running Servers: ${stats.runningServers}
• Total Tools: ${stats.totalTools}

Server Statuses:
${statuses}
        `.trim();

        vscode.window.showInformationMessage(message, { modal: true });
    }

    /**
     * Restart MCP servers
     */
    private async restartMCPServers(): Promise<void> {
        if (!this.mcpManager) {
            vscode.window.showErrorMessage('MCP system not initialized');
            return;
        }

        vscode.window.showInformationMessage('Restarting MCP servers...');
        
        try {
            await this.mcpManager.stop();
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
            await this.mcpManager.start();
            
            vscode.window.showInformationMessage('MCP servers restarted successfully');
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to restart MCP servers: ${error}`);
        }
    }

    /**
     * Show approval preferences
     */
    private async showApprovalPreferences(): Promise<void> {
        if (!this.approvalHandler) {
            vscode.window.showErrorMessage('Approval system not initialized');
            return;
        }

        await this.approvalHandler.showUserPreferences();
    }

    /**
     * Reset approval preferences
     */
    private async resetApprovalPreferences(): Promise<void> {
        if (!this.approvalHandler) {
            vscode.window.showErrorMessage('Approval system not initialized');
            return;
        }

        await this.approvalHandler.resetUserPreferences();
    }

    /**
     * Show overall integration status
     */
    private async showIntegrationStatus(): Promise<void> {
        const status = this.getSystemStatus();
        
        const message = `
Palette AI Integration Status:

System Status: ${status.initialized ? '✅ Initialized' : '❌ Not Initialized'}
Tool System: ${status.toolSystem ? '✅ Active' : '❌ Inactive'}
MCP System: ${status.mcpSystem ? '✅ Active' : '❌ Inactive'}

Statistics:
• Total Tools: ${status.totalTools}
• MCP Servers: ${status.runningServers}/${status.mcpServers} running

Features:
• GitHub Copilot-style file approval ✅
• Batch file operations with conflict resolution ✅
• MCP server integration ✅
• AI SDK 5 tool calling ✅
• shadcn/ui MCP integration ${this.shadcnIntegration ? '✅' : '⚠️ (fallback mode)'}

Ready for AI tool calling with MCP server integration!
        `.trim();

        vscode.window.showInformationMessage(message, { modal: true });
    }
}