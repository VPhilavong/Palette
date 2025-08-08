/**
 * MCP Fallback Manager
 * Handles graceful degradation when MCP servers are unavailable
 */

import * as vscode from 'vscode';
import { EventEmitter } from 'events';
import { PaletteTool, ToolExecutionContext, ToolResult } from '../tools/types';
import { ToolRegistry } from '../tools/tool-registry';
import { MCPServerConfig } from './types';

export type FallbackMode = 'disabled' | 'graceful' | 'always';

export interface FallbackToolConfig {
    originalTool: string;
    serverName: string;
    fallbackImplementation: (params: any, context: ToolExecutionContext) => Promise<ToolResult>;
    description: string;
    limitations?: string[];
}

export class MCPFallbackManager extends EventEmitter {
    private static instance: MCPFallbackManager | null = null;
    private fallbackTools: Map<string, FallbackToolConfig> = new Map();
    private toolRegistry: ToolRegistry;
    private fallbackMode: FallbackMode = 'graceful';

    private constructor() {
        super();
        this.toolRegistry = ToolRegistry.getInstance();
        this.initializeFallbackTools();
    }

    static getInstance(): MCPFallbackManager {
        if (!this.instance) {
            this.instance = new MCPFallbackManager();
        }
        return this.instance;
    }

    /**
     * Set the fallback mode
     */
    setFallbackMode(mode: FallbackMode): void {
        this.fallbackMode = mode;
        console.log(`🔄 MCP fallback mode set to: ${mode}`);
    }

    /**
     * Check if fallback should be used for a server
     */
    shouldUseFallback(serverName: string, isServerAvailable: boolean): boolean {
        switch (this.fallbackMode) {
            case 'disabled':
                return false;
            case 'always':
                return true;
            case 'graceful':
                return !isServerAvailable;
            default:
                return false;
        }
    }

    /**
     * Register fallback tools when MCP server is unavailable
     */
    registerFallbackTools(serverName: string): void {
        console.log(`🔄 Registering fallback tools for server: ${serverName}`);

        for (const [toolKey, fallbackConfig] of this.fallbackTools) {
            if (fallbackConfig.serverName === serverName) {
                const fallbackTool: PaletteTool = {
                    name: `fallback_${serverName}_${fallbackConfig.originalTool}`,
                    description: `[Fallback] ${fallbackConfig.description}`,
                    category: 'external-api',
                    dangerLevel: 'safe',
                    inputSchema: require('zod').any(), // Would need proper schema
                    async execute(params: any, context: ToolExecutionContext): Promise<ToolResult> {
                        try {
                            const result = await fallbackConfig.fallbackImplementation(params, context);
                            
                            // Add fallback notice to successful results
                            if (result.success && result.followUpSuggestions) {
                                result.followUpSuggestions.unshift('⚠️ Using fallback implementation (MCP server unavailable)');
                            }

                            return result;
                        } catch (error: any) {
                            return {
                                success: false,
                                error: {
                                    code: 'FALLBACK_ERROR',
                                    message: `Fallback implementation failed: ${error.message}`,
                                    recoverable: true
                                }
                            };
                        }
                    }
                };

                this.toolRegistry.registerTool(fallbackTool, { enabled: true });
                console.log(`🔄 Registered fallback tool: ${fallbackTool.name}`);
            }
        }

        this.emit('fallback-tools-registered', serverName);
    }

    /**
     * Unregister fallback tools when MCP server becomes available
     */
    unregisterFallbackTools(serverName: string): void {
        console.log(`🔄 Unregistering fallback tools for server: ${serverName}`);

        const allTools = this.toolRegistry.getAllTools();
        for (const tool of allTools) {
            if (tool.name.startsWith(`fallback_${serverName}_`)) {
                this.toolRegistry.unregisterTool(tool.name);
                console.log(`🔄 Unregistered fallback tool: ${tool.name}`);
            }
        }

        this.emit('fallback-tools-unregistered', serverName);
    }

    /**
     * Initialize built-in fallback tools for common MCP servers
     */
    private initializeFallbackTools(): void {
        // Git fallback tools
        this.registerGitFallbackTools();
        
        // Filesystem fallback tools
        this.registerFilesystemFallbackTools();
        
        // shadcn-ui fallback tools
        this.registerShadcnFallbackTools();

        console.log(`🔄 Initialized ${this.fallbackTools.size} fallback tool configurations`);
    }

    /**
     * Register Git fallback tools
     */
    private registerGitFallbackTools(): void {
        this.fallbackTools.set('git_status', {
            originalTool: 'git_status',
            serverName: 'git',
            description: 'Get git repository status using VS Code Git API',
            limitations: ['Limited to current workspace', 'May not show all git details'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                try {
                    // Use VS Code's built-in Git API
                    const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
                    if (!gitExtension) {
                        throw new Error('Git extension not available');
                    }

                    const git = gitExtension.getAPI(1);
                    const repositories = git.repositories;

                    if (repositories.length === 0) {
                        return {
                            success: false,
                            error: {
                                code: 'NO_REPOSITORY',
                                message: 'No git repository found in workspace',
                                recoverable: false
                            }
                        };
                    }

                    const repo = repositories[0]; // Use first repository
                    const state = repo.state;

                    return {
                        success: true,
                        data: {
                            branch: state.HEAD?.name || 'unknown',
                            changes: state.workingTreeChanges.length,
                            staged: state.indexChanges.length,
                            ahead: state.HEAD?.ahead || 0,
                            behind: state.HEAD?.behind || 0,
                            clean: state.workingTreeChanges.length === 0 && state.indexChanges.length === 0
                        },
                        followUpSuggestions: [
                            'Repository status retrieved using VS Code Git API',
                            state.workingTreeChanges.length > 0 ? `${state.workingTreeChanges.length} working tree changes` : 'Working tree clean',
                            state.indexChanges.length > 0 ? `${state.indexChanges.length} staged changes` : 'No staged changes'
                        ]
                    };

                } catch (error: any) {
                    return {
                        success: false,
                        error: {
                            code: 'GIT_FALLBACK_ERROR',
                            message: `Git status fallback failed: ${error.message}`,
                            recoverable: true
                        }
                    };
                }
            }
        });

        this.fallbackTools.set('git_branch', {
            originalTool: 'git_branch',
            serverName: 'git',
            description: 'List git branches using VS Code Git API',
            limitations: ['Limited branch information', 'May not show remote branches'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                try {
                    const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
                    if (!gitExtension) {
                        throw new Error('Git extension not available');
                    }

                    const git = gitExtension.getAPI(1);
                    const repositories = git.repositories;

                    if (repositories.length === 0) {
                        throw new Error('No git repository found');
                    }

                    const repo = repositories[0];
                    const refs = repo.state.refs;

                    const branches = refs
                        .filter((ref: any) => ref.type === 1) // Local branches
                        .map((ref: any) => ({
                            name: ref.name || 'unknown',
                            current: ref.name === repo.state.HEAD?.name,
                            commit: ref.commit || 'unknown'
                        }));

                    return {
                        success: true,
                        data: {
                            branches,
                            currentBranch: repo.state.HEAD?.name || 'unknown'
                        },
                        followUpSuggestions: [
                            `Found ${branches.length} local branches`,
                            `Current branch: ${repo.state.HEAD?.name || 'unknown'}`
                        ]
                    };

                } catch (error: any) {
                    return {
                        success: false,
                        error: {
                            code: 'GIT_BRANCH_FALLBACK_ERROR',
                            message: `Git branch fallback failed: ${error.message}`,
                            recoverable: true
                        }
                    };
                }
            }
        });
    }

    /**
     * Register Filesystem fallback tools
     */
    private registerFilesystemFallbackTools(): void {
        this.fallbackTools.set('read_file', {
            originalTool: 'read_file',
            serverName: 'filesystem',
            description: 'Read file using VS Code Workspace API',
            limitations: ['Restricted to workspace files only', 'Limited to text files'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                try {
                    const filePath = params.path || params.file;
                    if (!filePath) {
                        throw new Error('File path is required');
                    }

                    // Only allow reading from workspace
                    if (!context.workspacePath || !filePath.startsWith(context.workspacePath)) {
                        throw new Error('File access restricted to workspace');
                    }

                    const fileUri = vscode.Uri.file(filePath);
                    const content = await vscode.workspace.fs.readFile(fileUri);
                    const textContent = new TextDecoder().decode(content);

                    return {
                        success: true,
                        data: {
                            path: filePath,
                            content: textContent,
                            size: content.length
                        },
                        followUpSuggestions: [
                            `Read ${content.length} bytes from ${filePath}`,
                            'File content retrieved using VS Code Workspace API'
                        ]
                    };

                } catch (error: any) {
                    return {
                        success: false,
                        error: {
                            code: 'FILE_READ_FALLBACK_ERROR',
                            message: `File read fallback failed: ${error.message}`,
                            recoverable: true
                        }
                    };
                }
            }
        });

        this.fallbackTools.set('list_directory', {
            originalTool: 'list_directory',
            serverName: 'filesystem',
            description: 'List directory contents using VS Code Workspace API',
            limitations: ['Restricted to workspace directories only'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                try {
                    const dirPath = params.path || params.directory || context.workspacePath;
                    if (!dirPath) {
                        throw new Error('Directory path is required');
                    }

                    // Only allow listing workspace directories
                    if (!context.workspacePath || !dirPath.startsWith(context.workspacePath)) {
                        throw new Error('Directory access restricted to workspace');
                    }

                    const dirUri = vscode.Uri.file(dirPath);
                    const entries = await vscode.workspace.fs.readDirectory(dirUri);

                    const files = entries
                        .filter(([name, type]) => type === vscode.FileType.File)
                        .map(([name]) => name);

                    const directories = entries
                        .filter(([name, type]) => type === vscode.FileType.Directory)
                        .map(([name]) => name);

                    return {
                        success: true,
                        data: {
                            path: dirPath,
                            files,
                            directories,
                            total: entries.length
                        },
                        followUpSuggestions: [
                            `Found ${files.length} files and ${directories.length} directories`,
                            'Directory listing using VS Code Workspace API'
                        ]
                    };

                } catch (error: any) {
                    return {
                        success: false,
                        error: {
                            code: 'DIR_LIST_FALLBACK_ERROR',
                            message: `Directory listing fallback failed: ${error.message}`,
                            recoverable: true
                        }
                    };
                }
            }
        });
    }

    /**
     * Register shadcn-ui fallback tools
     */
    private registerShadcnFallbackTools(): void {
        this.fallbackTools.set('list_components', {
            originalTool: 'list_components',
            serverName: 'shadcn-ui',
            description: 'List shadcn/ui components using built-in catalog',
            limitations: ['Static component list', 'No dynamic registry access'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                // Use the built-in component catalog from shadcn integration
                const components = [
                    { name: 'accordion', category: 'ui', description: 'A vertically stacked set of interactive headings' },
                    { name: 'alert', category: 'feedback', description: 'Displays a callout for user attention' },
                    { name: 'button', category: 'ui', description: 'Displays a button or a component that looks like a button' },
                    { name: 'card', category: 'layout', description: 'Displays a card with header, content, and footer' },
                    { name: 'dialog', category: 'feedback', description: 'A window overlaid on either the primary window or another dialog window' },
                    { name: 'form', category: 'form', description: 'Building forms with React Hook Form and Zod validation' },
                    { name: 'input', category: 'form', description: 'Displays a form input field' },
                    { name: 'navigation-menu', category: 'navigation', description: 'A collection of links for navigating websites' },
                    { name: 'sheet', category: 'feedback', description: 'Extends the Dialog component to display content that complements the main content' }
                ];

                const filteredComponents = params.category 
                    ? components.filter(c => c.category === params.category)
                    : components;

                return {
                    success: true,
                    data: {
                        components: filteredComponents,
                        total: filteredComponents.length,
                        categories: [...new Set(components.map(c => c.category))]
                    },
                    followUpSuggestions: [
                        `Found ${filteredComponents.length} shadcn/ui components`,
                        'Using built-in component catalog',
                        'Install shadcn CLI for full component management'
                    ]
                };
            }
        });

        this.fallbackTools.set('install_component', {
            originalTool: 'install_component',
            serverName: 'shadcn-ui',
            description: 'Provide shadcn/ui installation guidance',
            limitations: ['Guidance only', 'No actual installation'],
            fallbackImplementation: async (params: any, context: ToolExecutionContext): Promise<ToolResult> => {
                const component = params.component || params.name;
                if (!component) {
                    throw new Error('Component name is required');
                }

                const installCommand = `npx shadcn@latest add ${component}`;
                const manualSteps = [
                    '1. Ensure shadcn/ui is initialized in your project',
                    `2. Run: ${installCommand}`,
                    '3. Import and use the component in your React code',
                    '4. Check components/ui/ directory for the new component'
                ];

                return {
                    success: false, // False because we didn't actually install
                    error: {
                        code: 'INSTALL_GUIDANCE_ONLY',
                        message: 'Cannot install component without MCP server. Follow manual steps.',
                        recoverable: true
                    },
                    data: {
                        component,
                        installCommand,
                        manualSteps,
                        docsUrl: `https://ui.shadcn.com/docs/components/${component}`
                    },
                    followUpSuggestions: [
                        `To install ${component}, run: ${installCommand}`,
                        'Or configure the shadcn-ui MCP server for automatic installation',
                        `Visit documentation: https://ui.shadcn.com/docs/components/${component}`
                    ]
                };
            }
        });
    }

    /**
     * Show user-friendly error when MCP server is unavailable
     */
    showServerUnavailableError(serverName: string, originalError: string): void {
        const config = vscode.workspace.getConfiguration('palette.mcp');
        const showSetupGuide = config.get<boolean>('showSetupGuide', true);

        if (!showSetupGuide) {
            return;
        }

        const message = `⚠️ MCP server '${serverName}' is unavailable. Using fallback functionality.`;
        
        vscode.window.showWarningMessage(
            message,
            'Configure MCP Server',
            'Use Fallback Only',
            'Don\'t Show Again'
        ).then(action => {
            switch (action) {
                case 'Configure MCP Server':
                    vscode.commands.executeCommand('workbench.action.openSettings', `palette.mcp.servers`);
                    break;
                case 'Use Fallback Only':
                    config.update('fallbackMode', 'always', vscode.ConfigurationTarget.Global);
                    break;
                case 'Don\'t Show Again':
                    config.update('showSetupGuide', false, vscode.ConfigurationTarget.Global);
                    break;
            }
        });
    }

    /**
     * Get fallback status for all servers
     */
    getFallbackStatus(): Record<string, {
        hasFallback: boolean;
        toolCount: number;
        limitations: string[];
    }> {
        const status: Record<string, { hasFallback: boolean; toolCount: number; limitations: string[] }> = {};

        for (const [toolKey, config] of this.fallbackTools) {
            const serverName = config.serverName;
            if (!status[serverName]) {
                status[serverName] = {
                    hasFallback: false,
                    toolCount: 0,
                    limitations: []
                };
            }

            status[serverName].hasFallback = true;
            status[serverName].toolCount++;
            if (config.limitations) {
                status[serverName].limitations.push(...config.limitations);
            }
        }

        return status;
    }

    /**
     * Dispose resources
     */
    dispose(): void {
        this.removeAllListeners();
        this.fallbackTools.clear();
    }
}