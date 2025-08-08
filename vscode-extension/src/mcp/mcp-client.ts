/**
 * MCP Client Implementation
 * Handles communication with individual MCP servers
 */

import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';
import { 
    MCPClient, 
    MCPServerConfig, 
    MCPTool, 
    MCPResource, 
    MCPToolCallRequest, 
    MCPToolCallResponse,
    MCPServerStatus
} from './types';
import { z } from 'zod';

export class MCPClientImpl extends EventEmitter implements MCPClient {
    public readonly serverName: string;
    public isConnected: boolean = false;

    private config: MCPServerConfig;
    private process?: ChildProcess;
    private messageId: number = 0;
    private pendingRequests: Map<number, {
        resolve: (value: any) => void;
        reject: (error: any) => void;
        timeout: NodeJS.Timeout;
    }> = new Map();
    
    // Enhanced connection management
    private retryCount: number = 0;
    private maxRetries: number = 2; // Reduced from 3 for faster failure
    private baseRetryDelay: number = 1500; // 1.5 seconds base delay
    private connectionTimeout: number = 8000; // Reduced to 8 seconds for faster failure
    private reconnectTimer?: NodeJS.Timeout;
    private isReconnecting: boolean = false;

    constructor(config: MCPServerConfig, options?: {
        maxRetries?: number;
        baseRetryDelay?: number;
        connectionTimeout?: number;
    }) {
        super();
        this.config = config;
        this.serverName = config.name;
        
        // Apply configuration options
        if (options) {
            this.maxRetries = options.maxRetries ?? this.maxRetries;
            this.baseRetryDelay = options.baseRetryDelay ?? this.baseRetryDelay;
            this.connectionTimeout = options.connectionTimeout ?? this.connectionTimeout;
        }
    }

    /**
     * Connect to the MCP server with retry logic
     */
    async connect(): Promise<void> {
        if (this.isConnected) {
            return;
        }

        this.retryCount = 0;
        return this.attemptConnection();
    }

    /**
     * Attempt connection with exponential backoff retry
     */
    private async attemptConnection(): Promise<void> {
        try {
            console.log(`🔌 Connecting to MCP server: ${this.serverName} (attempt ${this.retryCount + 1}/${this.maxRetries + 1})`);
            
            // Create connection timeout promise
            const timeoutPromise = new Promise<never>((_, reject) => {
                setTimeout(() => reject(new Error(`Connection timeout after ${this.connectionTimeout}ms`)), this.connectionTimeout);
            });

            // Create connection promise
            const connectionPromise = this.createConnection();

            // Race connection against timeout
            await Promise.race([connectionPromise, timeoutPromise]);
            
            this.isConnected = true;
            this.retryCount = 0; // Reset retry count on successful connection
            console.log(`🔌 Connected to MCP server: ${this.serverName}`);
            this.emit('connected');

        } catch (error: any) {
            console.error(`🔌 Connection attempt failed for ${this.serverName}:`, error.message);
            
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                const retryDelay = this.calculateRetryDelay();
                
                console.log(`🔌 Retrying connection to ${this.serverName} in ${retryDelay}ms...`);
                
                await new Promise(resolve => setTimeout(resolve, retryDelay));
                return this.attemptConnection();
            } else {
                console.error(`🔌 Max retries exceeded for ${this.serverName}`);
                this.isConnected = false;
                throw new Error(`Failed to connect to MCP server after ${this.maxRetries + 1} attempts: ${error.message}`);
            }
        }
    }

    /**
     * Create the actual server connection
     */
    private async createConnection(): Promise<void> {
        // Start the server process
        this.process = spawn(this.config.command, this.config.args || [], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env, ...this.config.env },
            cwd: this.config.workingDirectory
        });

        if (!this.process.stdout || !this.process.stdin || !this.process.stderr) {
            throw new Error('Failed to create server process pipes');
        }

        // Set up process event handlers
        this.process.on('error', (error) => {
            console.error(`🔌 MCP server process error (${this.serverName}):`, error);
            this.handleConnectionError(error);
        });

        this.process.on('exit', (code, signal) => {
            console.log(`🔌 MCP server exited (${this.serverName}): code=${code}, signal=${signal}`);
            this.handleConnectionLoss(code, signal);
        });

        // Set up message handling
        this.setupMessageHandling();

        // Send initialization request with timeout
        await this.initialize();
    }

    /**
     * Calculate retry delay with exponential backoff and jitter
     */
    private calculateRetryDelay(): number {
        const exponentialDelay = this.baseRetryDelay * Math.pow(2, this.retryCount);
        const jitter = Math.random() * 1000; // Add up to 1 second of jitter
        return Math.min(exponentialDelay + jitter, 30000); // Cap at 30 seconds
    }

    /**
     * Handle connection errors with retry logic
     */
    private handleConnectionError(error: any): void {
        this.isConnected = false;
        this.emit('error', error);
        
        // Don't auto-reconnect if we're already trying to reconnect
        if (this.isReconnecting) {
            return;
        }
        
        // Auto-reconnect if configured
        const shouldReconnect = this.retryCount < this.maxRetries;
        if (shouldReconnect) {
            this.scheduleReconnect();
        }
    }

    /**
     * Handle connection loss with auto-reconnect
     */
    private handleConnectionLoss(code: number | null, signal: string | null): void {
        this.isConnected = false;
        this.emit('disconnected', { code, signal });
        
        // Don't auto-reconnect if disconnection was intentional (code 0) or if already reconnecting
        if (code === 0 || this.isReconnecting) {
            return;
        }
        
        // Schedule reconnect for unexpected disconnections
        this.scheduleReconnect();
    }

    /**
     * Schedule automatic reconnection
     */
    private scheduleReconnect(): void {
        if (this.isReconnecting || this.retryCount >= this.maxRetries) {
            return;
        }

        this.isReconnecting = true;
        const retryDelay = this.calculateRetryDelay();
        
        console.log(`🔌 Scheduling reconnect for ${this.serverName} in ${retryDelay}ms...`);
        
        this.reconnectTimer = setTimeout(async () => {
            try {
                this.isReconnecting = false;
                await this.attemptConnection();
            } catch (error) {
                console.error(`🔌 Auto-reconnect failed for ${this.serverName}:`, error);
                this.isReconnecting = false;
            }
        }, retryDelay);
    }

    /**
     * Disconnect from the MCP server
     */
    async disconnect(): Promise<void> {
        try {
            console.log(`🔌 Disconnecting from MCP server: ${this.serverName}`);
            
            // Stop any pending reconnection attempts
            this.isReconnecting = false;
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = undefined;
            }
            
            // Cancel pending requests
            for (const [id, { reject, timeout }] of this.pendingRequests) {
                clearTimeout(timeout);
                reject(new Error('Connection closed'));
            }
            this.pendingRequests.clear();

            // Terminate the process if it exists
            if (this.process) {
                this.process.kill('SIGTERM');
                
                // Wait a bit for graceful shutdown
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                if (this.process && !this.process.killed) {
                    this.process.kill('SIGKILL');
                }
            }

            this.isConnected = false;
            this.process = undefined;
            this.retryCount = 0; // Reset retry count
            
            console.log(`🔌 Disconnected from MCP server: ${this.serverName}`);
            this.emit('disconnected');

        } catch (error) {
            console.error(`🔌 Error disconnecting from MCP server (${this.serverName}):`, error);
            throw error;
        }
    }

    /**
     * List available tools from the server
     */
    async listTools(): Promise<MCPTool[]> {
        if (!this.isConnected) {
            throw new Error(`MCP server not connected: ${this.serverName}`);
        }

        try {
            const response = await this.sendRequest('tools/list', {});
            
            return (response.tools || []).map((tool: any) => ({
                name: tool.name,
                description: tool.description || '',
                inputSchema: this.parseSchema(tool.inputSchema),
                serverName: this.serverName
            }));

        } catch (error) {
            console.error(`🔌 Failed to list tools from ${this.serverName}:`, error);
            throw error;
        }
    }

    /**
     * Call a tool on the server
     */
    async callTool(request: MCPToolCallRequest): Promise<MCPToolCallResponse> {
        if (!this.isConnected) {
            throw new Error(`MCP server not connected: ${this.serverName}`);
        }

        try {
            const response = await this.sendRequest('tools/call', {
                name: request.toolName,
                arguments: request.parameters
            });

            return {
                success: !response.isError,
                result: response.content,
                error: response.isError ? {
                    code: response.error?.code || 'UNKNOWN_ERROR',
                    message: response.error?.message || 'Tool execution failed',
                    details: response.error
                } : undefined
            };

        } catch (error) {
            console.error(`🔌 Failed to call tool ${request.toolName} on ${this.serverName}:`, error);
            return {
                success: false,
                error: {
                    code: 'TOOL_CALL_ERROR',
                    message: `Failed to call tool: ${error}`,
                    details: error
                }
            };
        }
    }

    /**
     * List available resources from the server
     */
    async listResources(): Promise<MCPResource[]> {
        if (!this.isConnected) {
            throw new Error(`MCP server not connected: ${this.serverName}`);
        }

        try {
            const response = await this.sendRequest('resources/list', {});
            
            return (response.resources || []).map((resource: any) => ({
                uri: resource.uri,
                name: resource.name,
                description: resource.description,
                mimeType: resource.mimeType,
                serverName: this.serverName
            }));

        } catch (error) {
            console.error(`🔌 Failed to list resources from ${this.serverName}:`, error);
            throw error;
        }
    }

    /**
     * Get a resource from the server
     */
    async getResource(uri: string): Promise<any> {
        if (!this.isConnected) {
            throw new Error(`MCP server not connected: ${this.serverName}`);
        }

        try {
            const response = await this.sendRequest('resources/read', { uri });
            return response.contents;

        } catch (error) {
            console.error(`🔌 Failed to get resource ${uri} from ${this.serverName}:`, error);
            throw error;
        }
    }

    /**
     * Health check ping
     */
    async ping(): Promise<boolean> {
        if (!this.isConnected || !this.process) {
            return false;
        }

        try {
            await this.sendRequest('ping', {}, 5000); // 5 second timeout
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Setup message handling for the server process
     */
    private setupMessageHandling(): void {
        if (!this.process || !this.process.stdout) {
            return;
        }

        let buffer = '';

        this.process.stdout.on('data', (chunk: Buffer) => {
            buffer += chunk.toString();
            
            // Process complete JSON messages
            let newlineIndex;
            while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
                const line = buffer.slice(0, newlineIndex);
                buffer = buffer.slice(newlineIndex + 1);
                
                if (line.trim()) {
                    try {
                        const message = JSON.parse(line);
                        this.handleMessage(message);
                    } catch (error) {
                        console.warn(`🔌 Failed to parse message from ${this.serverName}:`, line);
                    }
                }
            }
        });

        this.process.stderr?.on('data', (chunk: Buffer) => {
            console.warn(`🔌 MCP server stderr (${this.serverName}):`, chunk.toString());
        });
    }

    /**
     * Handle incoming messages from the server
     */
    private handleMessage(message: any): void {
        if (message.id !== undefined) {
            // Response to a request
            const pending = this.pendingRequests.get(message.id);
            if (pending) {
                clearTimeout(pending.timeout);
                this.pendingRequests.delete(message.id);
                
                if (message.error) {
                    pending.reject(new Error(message.error.message || 'Request failed'));
                } else {
                    pending.resolve(message.result);
                }
            }
        } else {
            // Notification from server
            this.emit('notification', message);
        }
    }

    /**
     * Send a request to the server
     */
    private async sendRequest(method: string, params: any, timeoutMs: number = 10000): Promise<any> { // Reduced default from 30s to 10s
        if (!this.process || !this.process.stdin) {
            throw new Error('Server process not available');
        }

        const id = ++this.messageId;
        const request = {
            jsonrpc: '2.0',
            id,
            method,
            params
        };

        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.pendingRequests.delete(id);
                reject(new Error(`Request timeout: ${method}`));
            }, timeoutMs);

            this.pendingRequests.set(id, { resolve, reject, timeout });
            
            try {
                this.process!.stdin!.write(JSON.stringify(request) + '\n');
            } catch (error) {
                clearTimeout(timeout);
                this.pendingRequests.delete(id);
                reject(error);
            }
        });
    }

    /**
     * Initialize the MCP connection
     */
    private async initialize(): Promise<void> {
        const response = await this.sendRequest('initialize', {
            protocolVersion: '2024-11-05',
            capabilities: {
                tools: {},
                resources: {}
            },
            clientInfo: {
                name: 'Palette VS Code Extension',
                version: '1.0.0'
            }
        }, 6000); // 6 second timeout for initialization (shorter for faster failure)

        if (response.protocolVersion !== '2024-11-05') {
            console.warn(`🔌 Protocol version mismatch for ${this.serverName}: expected 2024-11-05, got ${response.protocolVersion}`);
        }

        // Send initialized notification
        await this.sendRequest('initialized', {}, 3000); // 3 second timeout for initialized confirmation
    }

    /**
     * Parse JSON schema to Zod schema (simplified)
     */
    private parseSchema(jsonSchema: any): z.ZodSchema<any> {
        if (!jsonSchema) {
            return z.any();
        }

        // This is a simplified schema parser
        // In practice, you might want to use a library like json-schema-to-zod
        if (jsonSchema.type === 'object') {
            return z.object({});
        } else if (jsonSchema.type === 'string') {
            return z.string();
        } else if (jsonSchema.type === 'number') {
            return z.number();
        } else if (jsonSchema.type === 'boolean') {
            return z.boolean();
        }

        return z.any();
    }
}