/**
 * MCP Configuration Manager
 * Handles validation, loading, and management of MCP server configurations
 */

import * as vscode from 'vscode';
import { z } from 'zod';
import { MCPServerConfig, MCPManagerConfig } from './types';

// Zod schemas for validation
const MCPServerConfigSchema = z.object({
    name: z.string().min(1, 'Server name cannot be empty'),
    description: z.string().optional().default(''),
    command: z.string().min(1, 'Command cannot be empty'),
    args: z.array(z.string()).optional().default([]),
    env: z.record(z.string()).optional(),
    workingDirectory: z.string().optional(),
    enabled: z.boolean().default(true),
    autoStart: z.boolean().default(false),
    tools: z.array(z.string()).optional().default([]),
    resources: z.array(z.string()).optional().default([])
});

const MCPManagerConfigSchema = z.object({
    enabled: z.boolean().default(true),
    servers: z.array(MCPServerConfigSchema).default([]),
    maxRetries: z.number().min(0).max(10).default(3),
    retryDelay: z.number().min(1000).max(30000).default(5000),
    connectionTimeout: z.number().min(5000).max(60000).default(10000),
    healthCheckInterval: z.number().min(10000).max(300000).default(30000),
    autoRestart: z.boolean().default(true),
    fallbackMode: z.enum(['disabled', 'graceful', 'always']).default('graceful'),
    showSetupGuide: z.boolean().default(true)
});

export interface MCPConfigValidationResult {
    isValid: boolean;
    errors: Array<{
        path: string;
        message: string;
        severity: 'error' | 'warning';
    }>;
    config?: MCPManagerConfig;
}

export class MCPConfigManager {
    private static instance: MCPConfigManager | null = null;
    private configChangeEmitter = new vscode.EventEmitter<MCPManagerConfig>();
    
    public readonly onConfigChange = this.configChangeEmitter.event;

    private constructor() {
        // Listen for configuration changes
        vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('palette.mcp')) {
                const newConfig = this.loadConfiguration();
                if (newConfig.isValid && newConfig.config) {
                    this.configChangeEmitter.fire(newConfig.config);
                }
            }
        });
    }

    static getInstance(): MCPConfigManager {
        if (!this.instance) {
            this.instance = new MCPConfigManager();
        }
        return this.instance;
    }

    /**
     * Load and validate configuration from VS Code settings
     */
    loadConfiguration(): MCPConfigValidationResult {
        try {
            const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
            
            const rawConfig = {
                enabled: vsConfig.get<boolean>('enabled', true),
                servers: vsConfig.get<MCPServerConfig[]>('servers', []),
                maxRetries: vsConfig.get<number>('maxRetries', 3),
                retryDelay: vsConfig.get<number>('retryDelay', 5000),
                connectionTimeout: vsConfig.get<number>('connectionTimeout', 10000),
                healthCheckInterval: vsConfig.get<number>('healthCheckInterval', 30000),
                autoRestart: vsConfig.get<boolean>('autoRestart', true),
                fallbackMode: vsConfig.get<'disabled' | 'graceful' | 'always'>('fallbackMode', 'graceful'),
                showSetupGuide: vsConfig.get<boolean>('showSetupGuide', true)
            };

            return this.validateConfiguration(rawConfig);

        } catch (error: any) {
            return {
                isValid: false,
                errors: [{
                    path: 'configuration',
                    message: `Failed to load configuration: ${error.message}`,
                    severity: 'error'
                }]
            };
        }
    }

    /**
     * Validate configuration using Zod schemas
     */
    validateConfiguration(config: any): MCPConfigValidationResult {
        try {
            const validatedConfig = MCPManagerConfigSchema.parse(config);
            const errors: Array<{ path: string; message: string; severity: 'error' | 'warning' }> = [];

            // Additional validation checks
            const serverNames = new Set<string>();
            validatedConfig.servers.forEach((server, index) => {
                // Check for duplicate server names
                if (serverNames.has(server.name)) {
                    errors.push({
                        path: `servers[${index}].name`,
                        message: `Duplicate server name: ${server.name}`,
                        severity: 'error'
                    });
                }
                serverNames.add(server.name);

                // Check for missing command paths
                if (server.enabled && !this.isCommandAvailable(server.command)) {
                    errors.push({
                        path: `servers[${index}].command`,
                        message: `Command may not be available: ${server.command}`,
                        severity: 'warning'
                    });
                }

                // Check working directory exists
                if (server.workingDirectory && !this.isDirectoryValid(server.workingDirectory)) {
                    errors.push({
                        path: `servers[${index}].workingDirectory`,
                        message: `Working directory does not exist: ${server.workingDirectory}`,
                        severity: 'warning'
                    });
                }
            });

            // Check if any servers are enabled
            if (validatedConfig.enabled && !validatedConfig.servers.some(s => s.enabled)) {
                errors.push({
                    path: 'servers',
                    message: 'MCP is enabled but no servers are configured or enabled',
                    severity: 'warning'
                });
            }

            return {
                isValid: errors.filter(e => e.severity === 'error').length === 0,
                errors,
                config: validatedConfig
            };

        } catch (error: any) {
            if (error instanceof z.ZodError) {
                return {
                    isValid: false,
                    errors: error.errors.map(e => ({
                        path: e.path.join('.'),
                        message: e.message,
                        severity: 'error' as const
                    }))
                };
            }

            return {
                isValid: false,
                errors: [{
                    path: 'configuration',
                    message: `Configuration validation failed: ${error.message}`,
                    severity: 'error'
                }]
            };
        }
    }

    /**
     * Save configuration to VS Code settings
     */
    async saveConfiguration(config: MCPManagerConfig): Promise<void> {
        const vsConfig = vscode.workspace.getConfiguration('palette.mcp');
        
        await Promise.all([
            vsConfig.update('enabled', config.enabled, vscode.ConfigurationTarget.Global),
            vsConfig.update('servers', config.servers, vscode.ConfigurationTarget.Global),
            vsConfig.update('maxRetries', config.maxRetries, vscode.ConfigurationTarget.Global),
            vsConfig.update('retryDelay', config.retryDelay, vscode.ConfigurationTarget.Global),
            vsConfig.update('connectionTimeout', config.connectionTimeout, vscode.ConfigurationTarget.Global),
            vsConfig.update('healthCheckInterval', config.healthCheckInterval, vscode.ConfigurationTarget.Global),
            vsConfig.update('autoRestart', config.autoRestart, vscode.ConfigurationTarget.Global),
            vsConfig.update('fallbackMode', config.fallbackMode, vscode.ConfigurationTarget.Global),
            vsConfig.update('showSetupGuide', config.showSetupGuide, vscode.ConfigurationTarget.Global)
        ]);
    }

    /**
     * Update a specific server configuration
     */
    async updateServerConfig(serverName: string, updates: Partial<MCPServerConfig>): Promise<void> {
        const currentConfig = this.loadConfiguration();
        if (!currentConfig.isValid || !currentConfig.config) {
            throw new Error('Cannot update server config: current configuration is invalid');
        }

        const serverIndex = currentConfig.config.servers.findIndex(s => s.name === serverName);
        if (serverIndex === -1) {
            throw new Error(`Server not found: ${serverName}`);
        }

        currentConfig.config.servers[serverIndex] = {
            ...currentConfig.config.servers[serverIndex],
            ...updates
        };

        await this.saveConfiguration(currentConfig.config);
    }

    /**
     * Add a new server configuration
     */
    async addServerConfig(serverConfig: MCPServerConfig): Promise<void> {
        const currentConfig = this.loadConfiguration();
        if (!currentConfig.isValid || !currentConfig.config) {
            throw new Error('Cannot add server config: current configuration is invalid');
        }

        // Check for duplicate names
        if (currentConfig.config.servers.some(s => s.name === serverConfig.name)) {
            throw new Error(`Server with name '${serverConfig.name}' already exists`);
        }

        currentConfig.config.servers.push(serverConfig);
        await this.saveConfiguration(currentConfig.config);
    }

    /**
     * Remove a server configuration
     */
    async removeServerConfig(serverName: string): Promise<void> {
        const currentConfig = this.loadConfiguration();
        if (!currentConfig.isValid || !currentConfig.config) {
            throw new Error('Cannot remove server config: current configuration is invalid');
        }

        currentConfig.config.servers = currentConfig.config.servers.filter(s => s.name !== serverName);
        await this.saveConfiguration(currentConfig.config);
    }

    /**
     * Get default configuration for common MCP servers
     */
    getDefaultServerConfigs(): MCPServerConfig[] {
        return [
            {
                name: 'filesystem',
                description: 'File system operations and directory management',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
                enabled: false,
                autoStart: false,
                tools: ['read_file', 'write_file', 'create_directory', 'list_directory', 'move_file', 'search_files'],
                resources: ['file', 'directory']
            },
            {
                name: 'git',
                description: 'Git version control operations',
                command: 'npx',
                args: ['-y', '@modelcontextprotocol/server-git'],
                enabled: false,
                autoStart: false,
                tools: ['git_status', 'git_add', 'git_commit', 'git_log', 'git_diff', 'git_branch'],
                resources: ['repository', 'commit', 'branch']
            }
        ];
    }

    /**
     * Reset configuration to defaults
     */
    async resetToDefaults(): Promise<void> {
        const defaultConfig: MCPManagerConfig = {
            enabled: true,
            servers: this.getDefaultServerConfigs(),
            maxRetries: 3,
            retryDelay: 5000,
            connectionTimeout: 10000,
            healthCheckInterval: 30000,
            autoRestart: true,
            fallbackMode: 'graceful',
            showSetupGuide: true
        };

        await this.saveConfiguration(defaultConfig);
    }

    /**
     * Generate configuration report
     */
    generateConfigReport(): {
        summary: string;
        details: {
            totalServers: number;
            enabledServers: number;
            autoStartServers: number;
            configurationErrors: number;
            configurationWarnings: number;
        };
        recommendations: string[];
    } {
        const result = this.loadConfiguration();
        const recommendations: string[] = [];

        if (!result.config) {
            return {
                summary: 'Configuration is invalid and cannot be loaded',
                details: {
                    totalServers: 0,
                    enabledServers: 0,
                    autoStartServers: 0,
                    configurationErrors: result.errors.filter(e => e.severity === 'error').length,
                    configurationWarnings: result.errors.filter(e => e.severity === 'warning').length
                },
                recommendations: ['Fix configuration errors before using MCP features']
            };
        }

        const config = result.config;
        const enabledServers = config.servers.filter(s => s.enabled);
        const autoStartServers = config.servers.filter(s => s.autoStart && s.enabled);

        // Generate recommendations
        if (!config.enabled) {
            recommendations.push('Consider enabling MCP integration for enhanced functionality');
        } else if (enabledServers.length === 0) {
            recommendations.push('Enable at least one MCP server to use MCP features');
        }

        if (config.maxRetries > 5) {
            recommendations.push('High retry count may cause delays - consider reducing maxRetries');
        }

        if (config.connectionTimeout < 10000) {
            recommendations.push('Low connection timeout may cause frequent failures');
        }

        if (autoStartServers.length > 3) {
            recommendations.push('Many auto-start servers may slow down VS Code startup');
        }

        return {
            summary: `MCP configuration: ${enabledServers.length} enabled servers, ${result.errors.length} issues`,
            details: {
                totalServers: config.servers.length,
                enabledServers: enabledServers.length,
                autoStartServers: autoStartServers.length,
                configurationErrors: result.errors.filter(e => e.severity === 'error').length,
                configurationWarnings: result.errors.filter(e => e.severity === 'warning').length
            },
            recommendations
        };
    }

    /**
     * Check if a command is available in the system PATH
     */
    private isCommandAvailable(command: string): boolean {
        try {
            // Simple check - in a real implementation, you might want to use which/where
            return command.includes('/') || ['node', 'npm', 'npx', 'python', 'python3'].includes(command);
        } catch {
            return false;
        }
    }

    /**
     * Check if a directory path is valid
     */
    private isDirectoryValid(path: string): boolean {
        try {
            // In VS Code environment, we'd need to use workspace.fs to check
            // For now, just check if it's a reasonable path
            return path.length > 0 && !path.includes('..') && !path.includes('*');
        } catch {
            return false;
        }
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        this.configChangeEmitter.dispose();
    }
}

export type { MCPManagerConfig };