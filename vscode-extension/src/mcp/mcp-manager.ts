/**
 * MCP Manager
 * Central manager for all MCP server connections and tool integration
 */

import * as vscode from 'vscode';
import { EventEmitter } from 'events';
import { 
    MCPServerConfig, 
    MCPServerInstance, 
    MCPServerStatus,
    MCPTool, 
    MCPResource, 
    MCPToolCallRequest, 
    MCPToolCallResponse,
    MCPManagerConfig,
    MCPConnectionEvents
} from './types';
import { MCPClientImpl } from './mcp-client';
import { MCPConfigManager } from './mcp-config-manager';
import { MCPFallbackManager } from './mcp-fallback-manager';
import { ToolRegistry } from '../tools/tool-registry';
import { PaletteTool, ToolExecutionContext, ToolResult } from '../tools/types';

export class MCPManager extends EventEmitter {
    private static instance: MCPManager | null = null;
    
    private servers: Map<string, MCPServerInstance> = new Map();
    private config: MCPManagerConfig = { 
        enabled: false, 
        servers: [], 
        maxRetries: 3, 
        retryDelay: 1000, 
        connectionTimeout: 10000,
        healthCheckInterval: 30000,
        autoRestart: true,
        fallbackMode: 'graceful',
        showSetupGuide: true
    };
    private healthCheckTimer?: NodeJS.Timeout;
    private toolRegistry: ToolRegistry;
    private configManager: MCPConfigManager;
    private fallbackManager: MCPFallbackManager;
    private isEnabled: boolean = true;
    
    private constructor() {
        super();
        
        this.toolRegistry = ToolRegistry.getInstance();
        this.configManager = MCPConfigManager.getInstance();
        this.fallbackManager = MCPFallbackManager.getInstance();
        
        // Load initial configuration
        this.loadConfiguration();
        
        // Listen for configuration changes
        this.configManager.onConfigChange(newConfig => {
            console.log('🔌 MCP configuration changed, reloading...');
            this.handleConfigurationChange(newConfig);
        });
        
        console.log('🔌 MCP Manager initialized');
    }

    static getInstance(): MCPManager {
        if (!this.instance) {
            this.instance = new MCPManager();
        }
        return this.instance;
    }

    /**
     * Start the MCP Manager and auto-start enabled servers
     */
    async start(): Promise<void> {
        console.log('🔌 Starting MCP Manager...');
        
        if (!this.isEnabled) {
            console.log('🔌 MCP is disabled in configuration');
            return;
        }
        
        // Start auto-start servers
        const autoStartServers = this.config.servers.filter(
            config => config.enabled && config.autoStart
        );

        const startPromises = autoStartServers.map(config => this.startServer(config.name));
        const results = await Promise.allSettled(startPromises);
        
        // Count successful starts
        const successfulStarts = results.filter(result => result.status === 'fulfilled').length;
        const failedStarts = results.filter(result => result.status === 'rejected');
        
        // Log failed starts
        failedStarts.forEach((result, index) => {
            if (result.status === 'rejected') {
                console.error(`🔌 Failed to start ${autoStartServers[index].name}:`, result.reason);
            }
        });

        // Start health check timer
        this.startHealthCheck();
        
        console.log(`🔌 MCP Manager started: ${successfulStarts}/${autoStartServers.length} servers started`);
        
        // Show setup guidance if no servers started and guidance is enabled
        if (successfulStarts === 0 && autoStartServers.length > 0 && this.config.showSetupGuide) {
            this.showSetupGuidance();
        }
    }

    /**
     * Stop the MCP Manager and all servers
     */
    async stop(): Promise<void> {
        console.log('🔌 Stopping MCP Manager...');
        
        // Stop health check
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = undefined;
        }

        // Stop all servers
        const stopPromises = Array.from(this.servers.keys()).map(name => this.stopServer(name));
        await Promise.allSettled(stopPromises);
        
        this.servers.clear();
        console.log('🔌 MCP Manager stopped');
    }

    /**
     * Start a specific MCP server
     */
    async startServer(serverName: string): Promise<void> {
        const config = this.config.servers.find(c => c.name === serverName);
        if (!config) {
            throw new Error(`Server configuration not found: ${serverName}`);
        }

        if (!config.enabled) {
            console.log(`🔌 Server ${serverName} is disabled in configuration`);
            return;
        }

        if (this.servers.has(serverName)) {
            const instance = this.servers.get(serverName)!;
            if (instance.status === 'running') {
                console.log(`🔌 Server ${serverName} is already running`);
                return;
            }
        }

        console.log(`🔌 Starting MCP server: ${serverName}`);
        
        // Create client with enhanced configuration
        const client = new MCPClientImpl(config, {
            maxRetries: this.config.maxRetries,
            baseRetryDelay: this.config.retryDelay,
            connectionTimeout: this.config.connectionTimeout
        });
        
        const instance: MCPServerInstance = {
            config,
            status: 'starting',
            client,
            startedAt: new Date()
        };

        this.servers.set(serverName, instance);

        try {
            // Set up client event handlers
            client.on('connected', () => {
                instance.status = 'running';
                instance.lastHeartbeat = new Date();
                this.onServerConnected(serverName);
            });

            client.on('disconnected', () => {
                instance.status = 'disconnected';
                this.onServerDisconnected(serverName);
            });

            client.on('error', (error) => {
                instance.status = 'error';
                instance.lastError = error.message;
                this.onServerError(serverName, error);
            });

            // Connect to the server
            await client.connect();
            
            // Register server tools
            await this.registerServerTools(serverName);
            
            console.log(`🔌 MCP server started successfully: ${serverName}`);
            this.emit('server-started', serverName);

        } catch (error: any) {
            console.error(`🔌 Failed to start MCP server ${serverName}:`, error);
            instance.status = 'error';
            instance.lastError = error.message;
            
            // Enable fallback if appropriate
            if (this.fallbackManager.shouldUseFallback(serverName, false)) {
                console.log(`🔌 Enabling fallback tools for ${serverName}`);
                this.fallbackManager.registerFallbackTools(serverName);
                this.fallbackManager.showServerUnavailableError(serverName, error.message);
            }
            
            this.emit('server-error', serverName, error.message);
            throw error;
        }
    }

    /**
     * Stop a specific MCP server
     */
    async stopServer(serverName: string): Promise<void> {
        const instance = this.servers.get(serverName);
        if (!instance) {
            console.log(`🔌 Server ${serverName} is not running`);
            return;
        }

        console.log(`🔌 Stopping MCP server: ${serverName}`);

        try {
            // Unregister server tools
            this.unregisterServerTools(serverName);

            // Disconnect client
            if (instance.client) {
                await instance.client.disconnect();
            }

            instance.status = 'stopped';
            this.servers.delete(serverName);
            
            console.log(`🔌 MCP server stopped: ${serverName}`);
            this.emit('server-stopped', serverName);

        } catch (error: any) {
            console.error(`🔌 Error stopping MCP server ${serverName}:`, error);
            instance.status = 'error';
            instance.lastError = error.message;
        }
    }

    /**
     * Restart a server
     */
    async restartServer(serverName: string): Promise<void> {
        await this.stopServer(serverName);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Brief delay
        await this.startServer(serverName);
    }

    /**
     * Get server status
     */
    getServerStatus(serverName: string): MCPServerStatus {
        const instance = this.servers.get(serverName);
        return instance?.status || 'stopped';
    }

    /**
     * Get all server statuses
     */
    getAllServerStatuses(): Record<string, MCPServerStatus> {
        const statuses: Record<string, MCPServerStatus> = {};
        
        for (const config of this.config.servers) {
            statuses[config.name] = this.getServerStatus(config.name);
        }
        
        return statuses;
    }

    /**
     * List available tools from all running servers
     */
    async listAllTools(): Promise<MCPTool[]> {
        const allTools: MCPTool[] = [];
        
        for (const [serverName, instance] of this.servers) {
            if (instance.status === 'running' && instance.client) {
                try {
                    const tools = await instance.client.listTools();
                    allTools.push(...tools);
                } catch (error) {
                    console.warn(`🔌 Failed to list tools from ${serverName}:`, error);
                }
            }
        }
        
        return allTools;
    }

    /**
     * Call a tool on a specific server
     */
    async callTool(request: MCPToolCallRequest): Promise<MCPToolCallResponse> {
        const instance = this.servers.get(request.serverName);
        if (!instance || instance.status !== 'running' || !instance.client) {
            return {
                success: false,
                error: {
                    code: 'SERVER_NOT_AVAILABLE',
                    message: `MCP server not available: ${request.serverName}`
                }
            };
        }

        try {
            return await instance.client.callTool(request);
        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'TOOL_CALL_ERROR',
                    message: `Failed to call tool: ${error.message}`,
                    details: error
                }
            };
        }
    }

    /**
     * Get server configuration
     */
    getServerConfig(serverName: string): MCPServerConfig | undefined {
        return this.config.servers.find(c => c.name === serverName);
    }

    /**
     * Update server configuration
     */
    async updateServerConfig(serverName: string, updates: Partial<MCPServerConfig>): Promise<void> {
        await this.configManager.updateServerConfig(serverName, updates);
    }

    /**
     * Add a new server configuration
     */
    async addServerConfig(config: MCPServerConfig): Promise<void> {
        await this.configManager.addServerConfig(config);
    }

    /**
     * Remove a server configuration
     */
    async removeServerConfig(serverName: string): Promise<void> {
        // Stop server if running
        if (this.servers.has(serverName)) {
            await this.stopServer(serverName);
        }

        await this.configManager.removeServerConfig(serverName);
    }

    /**
     * Show setup guidance when no servers are available
     */
    private showSetupGuidance(): void {
        if (!this.config.showSetupGuide) {
            return;
        }

        const message = '🔌 No MCP servers are currently running. Would you like to configure MCP servers for enhanced functionality?';
        
        vscode.window.showInformationMessage(
            message,
            'Configure Servers',
            'View Documentation',
            'Use Without MCP'
        ).then(async (action) => {
            switch (action) {
                case 'Configure Servers':
                    vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp.servers');
                    break;
                case 'View Documentation':
                    vscode.env.openExternal(vscode.Uri.parse('https://modelcontextprotocol.io/introduction'));
                    break;
                case 'Use Without MCP':
                    const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
                    await vsConfig.update('fallbackMode', 'always', vscode.ConfigurationTarget.Global);
                    break;
            }
        });
    }

    /**
     * Start health check monitoring
     */
    private startHealthCheck(): void {
        this.healthCheckTimer = setInterval(async () => {
            for (const [serverName, instance] of this.servers) {
                if (instance.status === 'running' && instance.client) {
                    const isHealthy = await instance.client.ping();
                    if (!isHealthy) {
                        console.warn(`🔌 Health check failed for ${serverName}`);
                        if (this.config.autoRestart) {
                            this.restartServer(serverName).catch(error => {
                                console.error(`🔌 Auto-restart failed for ${serverName}:`, error);
                            });
                        }
                    } else {
                        instance.lastHeartbeat = new Date();
                    }
                }
            }
        }, this.config.healthCheckInterval);
    }

    /**
     * Handle server connected event
     */
    private async onServerConnected(serverName: string): Promise<void> {
        console.log(`🔌 Server connected: ${serverName}`);
        
        // Disable fallback tools if they were enabled
        this.fallbackManager.unregisterFallbackTools(serverName);
        
        // Register server tools with the tool registry
        try {
            await this.registerServerTools(serverName);
        } catch (error) {
            console.error(`🔌 Failed to register tools for ${serverName}:`, error);
        }
    }

    /**
     * Handle server disconnected event
     */
    private onServerDisconnected(serverName: string): void {
        console.log(`🔌 Server disconnected: ${serverName}`);
        this.unregisterServerTools(serverName);
        
        // Enable fallback tools if appropriate
        if (this.fallbackManager.shouldUseFallback(serverName, false)) {
            console.log(`🔌 Enabling fallback tools for disconnected server: ${serverName}`);
            this.fallbackManager.registerFallbackTools(serverName);
        }
    }

    /**
     * Handle server error event
     */
    private onServerError(serverName: string, error: any): void {
        console.error(`🔌 Server error (${serverName}):`, error);
        
        // Enable fallback tools if appropriate
        if (this.fallbackManager.shouldUseFallback(serverName, false)) {
            console.log(`🔌 Enabling fallback tools for errored server: ${serverName}`);
            this.fallbackManager.registerFallbackTools(serverName);
            this.fallbackManager.showServerUnavailableError(serverName, error.message || error);
        }
        
        this.emit('server-error', serverName, error.message || error);
    }

    /**
     * Register tools from a server with the tool registry
     */
    private async registerServerTools(serverName: string): Promise<void> {
        const instance = this.servers.get(serverName);
        if (!instance || !instance.client || instance.status !== 'running') {
            return;
        }

        try {
            const mcpTools = await instance.client.listTools();
            
            for (const mcpTool of mcpTools) {
                // Convert MCP tool to Palette tool format
                const paletteTool: PaletteTool = {
                    name: `mcp_${serverName}_${mcpTool.name}`,
                    description: `[MCP:${serverName}] ${mcpTool.description}`,
                    category: 'external-api',
                    inputSchema: mcpTool.inputSchema,
                    dangerLevel: 'safe',
                    async execute(params: any, context: ToolExecutionContext): Promise<ToolResult> {
                        const response = await MCPManager.getInstance().callTool({
                            toolName: mcpTool.name,
                            parameters: params,
                            serverName
                        });

                        if (response.success) {
                            return {
                                success: true,
                                data: response.result
                            };
                        } else {
                            return {
                                success: false,
                                error: {
                                    code: response.error?.code || 'MCP_ERROR',
                                    message: response.error?.message || 'MCP tool call failed',
                                    details: response.error?.details,
                                    recoverable: true
                                }
                            };
                        }
                    }
                };

                this.toolRegistry.registerTool(paletteTool, { 
                    enabled: true
                });

                console.log(`🔧 Registered MCP tool: ${paletteTool.name}`);
                this.emit('tool-registered', mcpTool);
            }

        } catch (error) {
            console.error(`🔌 Failed to register tools for ${serverName}:`, error);
        }
    }

    /**
     * Unregister tools from a server
     */
    private unregisterServerTools(serverName: string): void {
        const allTools = this.toolRegistry.getAllTools();
        
        for (const tool of allTools) {
            if (tool.name.startsWith(`mcp_${serverName}_`)) {
                const mcpToolName = tool.name.substring(`mcp_${serverName}_`.length);
                this.toolRegistry.unregisterTool(tool.name);
                console.log(`🔧 Unregistered MCP tool: ${tool.name}`);
                this.emit('tool-unregistered', mcpToolName, serverName);
            }
        }
    }

    /**
     * Load configuration using the config manager
     */
    private loadConfiguration(): void {
        const configResult = this.configManager.loadConfiguration();
        
        if (!configResult.isValid || !configResult.config) {
            console.error('🔌 Invalid MCP configuration:', configResult.errors);
            
            // Show configuration errors to user
            this.showConfigurationErrors(configResult.errors);
            
            // Use minimal safe configuration
            this.config = {
                enabled: false,
                servers: [],
                maxRetries: 3,
                retryDelay: 5000,
                connectionTimeout: 10000,
                healthCheckInterval: 30000,
                autoRestart: false,
                fallbackMode: 'graceful',
                showSetupGuide: true
            };
            this.isEnabled = false;
            return;
        }
        
        this.config = configResult.config;
        this.isEnabled = this.config.enabled;
        this.fallbackManager.setFallbackMode(this.config.fallbackMode);
        
        console.log(`🔌 MCP configuration loaded: ${this.config.servers.length} servers, enabled: ${this.isEnabled}`);
    }

    /**
     * Handle configuration changes
     */
    private async handleConfigurationChange(newConfig: MCPManagerConfig): Promise<void> {
        const oldConfig = this.config;
        this.config = newConfig;
        this.isEnabled = newConfig.enabled;
        this.fallbackManager.setFallbackMode(newConfig.fallbackMode);
        
        // Restart servers if configuration changed significantly
        const needsRestart = this.needsManagerRestart(oldConfig, newConfig);
        if (needsRestart) {
            console.log('🔌 Restarting MCP Manager due to configuration changes...');
            await this.stop();
            if (this.isEnabled) {
                await this.start();
            }
        }
    }

    /**
     * Check if manager needs restart due to config changes
     */
    private needsManagerRestart(oldConfig: MCPManagerConfig, newConfig: MCPManagerConfig): boolean {
        return (
            oldConfig.enabled !== newConfig.enabled ||
            oldConfig.maxRetries !== newConfig.maxRetries ||
            oldConfig.retryDelay !== newConfig.retryDelay ||
            oldConfig.connectionTimeout !== newConfig.connectionTimeout ||
            oldConfig.autoRestart !== newConfig.autoRestart ||
            JSON.stringify(oldConfig.servers) !== JSON.stringify(newConfig.servers)
        );
    }

    /**
     * Show configuration errors to user
     */
    private showConfigurationErrors(errors: Array<{path: string; message: string; severity: 'error' | 'warning'}>): void {
        const errorMessages = errors.filter(e => e.severity === 'error');
        const warningMessages = errors.filter(e => e.severity === 'warning');
        
        if (errorMessages.length > 0) {
            const message = `MCP Configuration Errors:\n${errorMessages.map(e => `• ${e.message}`).join('\n')}`;
            vscode.window.showErrorMessage(message, 'Open Settings').then(action => {
                if (action === 'Open Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp');
                }
            });
        }
        
        if (warningMessages.length > 0 && this.config.showSetupGuide) {
            const message = `MCP Configuration Warnings:\n${warningMessages.map(e => `• ${e.message}`).join('\n')}`;
            vscode.window.showWarningMessage(message, 'Review Settings').then(action => {
                if (action === 'Review Settings') {
                    vscode.commands.executeCommand('workbench.action.openSettings', 'palette.mcp');
                }
            });
        }
    }

    /**
     * Save configuration to VS Code settings (delegated to config manager)
     */
    private async saveConfiguration(): Promise<void> {
        await this.configManager.saveConfiguration(this.config);
    }

    /**
     * Get manager statistics with fallback information
     */
    getStatistics(): {
        enabled: boolean;
        totalServers: number;
        runningServers: number;
        totalTools: number;
        fallbackTools: number;
        serverStatuses: Record<string, MCPServerStatus>;
        fallbackStatus: Record<string, { hasFallback: boolean; toolCount: number; limitations: string[] }>;
        configurationReport: any;
    } {
        const serverStatuses = this.getAllServerStatuses();
        const runningServers = Object.values(serverStatuses).filter(status => status === 'running').length;
        
        // Count MCP tools in registry
        const allTools = this.toolRegistry.getAllTools();
        const mcpTools = allTools.filter(tool => tool.name.startsWith('mcp_'));
        const fallbackTools = allTools.filter(tool => tool.name.startsWith('fallback_'));
        
        return {
            enabled: this.isEnabled,
            totalServers: this.config.servers.length,
            runningServers,
            totalTools: mcpTools.length,
            fallbackTools: fallbackTools.length,
            serverStatuses,
            fallbackStatus: this.fallbackManager.getFallbackStatus(),
            configurationReport: this.configManager.generateConfigReport()
        };
    }
}