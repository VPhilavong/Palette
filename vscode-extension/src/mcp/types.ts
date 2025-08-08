/**
 * MCP (Model Context Protocol) Types
 * Type definitions for MCP server integration
 */

import { z } from 'zod';

/**
 * MCP Server Configuration
 */
export interface MCPServerConfig {
    name: string;
    description: string;
    command: string;
    args?: string[];
    env?: Record<string, string>;
    workingDirectory?: string;
    enabled: boolean;
    autoStart: boolean;
    tools?: string[]; // Available tool names
    resources?: string[]; // Available resource types
}

/**
 * MCP Server Status
 */
export type MCPServerStatus = 'stopped' | 'starting' | 'running' | 'error' | 'disconnected';

/**
 * MCP Server Instance
 */
export interface MCPServerInstance {
    config: MCPServerConfig;
    status: MCPServerStatus;
    process?: any; // Node.js ChildProcess
    client?: MCPClient;
    lastError?: string;
    startedAt?: Date;
    lastHeartbeat?: Date;
}

/**
 * MCP Tool Definition (from server)
 */
export interface MCPTool {
    name: string;
    description: string;
    inputSchema: z.ZodSchema<any>;
    serverName: string; // Which MCP server provides this tool
}

/**
 * MCP Resource Definition
 */
export interface MCPResource {
    uri: string;
    name: string;
    description?: string;
    mimeType?: string;
    serverName: string;
}

/**
 * MCP Tool Call Request
 */
export interface MCPToolCallRequest {
    toolName: string;
    parameters: Record<string, any>;
    serverName: string;
}

/**
 * MCP Tool Call Response
 */
export interface MCPToolCallResponse {
    success: boolean;
    result?: any;
    error?: {
        code: string;
        message: string;
        details?: any;
    };
}

/**
 * MCP Client Interface
 */
export interface MCPClient {
    serverName: string;
    isConnected: boolean;
    
    // Connection management
    connect(): Promise<void>;
    disconnect(): Promise<void>;
    
    // Tool operations
    listTools(): Promise<MCPTool[]>;
    callTool(request: MCPToolCallRequest): Promise<MCPToolCallResponse>;
    
    // Resource operations
    listResources(): Promise<MCPResource[]>;
    getResource(uri: string): Promise<any>;
    
    // Health check
    ping(): Promise<boolean>;
}

/**
 * MCP Connection Events
 */
export interface MCPConnectionEvents {
    'server-started': (serverName: string) => void;
    'server-stopped': (serverName: string) => void;
    'server-error': (serverName: string, error: string) => void;
    'tool-registered': (tool: MCPTool) => void;
    'tool-unregistered': (toolName: string, serverName: string) => void;
}

/**
 * MCP Manager Extended Configuration
 * Extends the basic configuration with additional management options
 */

/**
 * MCP Manager Configuration
 */
export interface MCPManagerConfig {
    enabled: boolean;
    servers: MCPServerConfig[];
    maxRetries: number;
    retryDelay: number;
    connectionTimeout: number;
    healthCheckInterval: number;
    autoRestart: boolean;
    fallbackMode: 'disabled' | 'graceful' | 'always';
    showSetupGuide: boolean;
}