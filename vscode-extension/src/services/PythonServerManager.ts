/**
 * PythonServerManager - Auto-managed Python intelligence server
 * Handles lifecycle, health monitoring, and communication with Python backend
 */

import * as vscode from 'vscode';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as net from 'net';

export interface ServerStatus {
    isRunning: boolean;
    port: number;
    pid?: number;
    startTime?: Date;
    lastHealthCheck?: Date;
    version?: string;
}

export interface ServerConfig {
    host: string;
    minPort: number;
    maxPort: number;
    startupTimeout: number;
    healthCheckInterval: number;
    maxRestartAttempts: number;
}

export class PythonServerManager {
    private static instance: PythonServerManager | null = null;
    
    private serverProcess: ChildProcess | null = null;
    private currentPort: number = 0;
    private healthCheckTimer: NodeJS.Timeout | null = null;
    private restartAttempts: number = 0;
    private outputChannel: vscode.OutputChannel;
    
    private readonly config: ServerConfig = {
        host: '127.0.0.1',
        minPort: 8765,
        maxPort: 8800,
        startupTimeout: 30000, // 30 seconds
        healthCheckInterval: 15000, // 15 seconds
        maxRestartAttempts: 3
    };
    
    private constructor() {
        this.outputChannel = vscode.window.createOutputChannel('Palette Python Server');
    }
    
    public static getInstance(): PythonServerManager {
        if (!PythonServerManager.instance) {
            PythonServerManager.instance = new PythonServerManager();
        }
        return PythonServerManager.instance;
    }
    
    /**
     * Ensure Python server is running and return connection info
     */
    public async ensureServerRunning(): Promise<ServerStatus> {
        const status = await this.getServerStatus();
        
        if (status.isRunning) {
            this.outputChannel.appendLine(`Python server already running on port ${status.port}`);
            return status;
        }
        
        this.outputChannel.appendLine('Starting Python intelligence server...');
        return await this.startServer();
    }
    
    /**
     * Get current server status
     */
    public async getServerStatus(): Promise<ServerStatus> {
        const baseStatus: ServerStatus = {
            isRunning: false,
            port: this.currentPort,
            pid: this.serverProcess?.pid
        };
        
        if (!this.serverProcess || this.currentPort === 0) {
            return baseStatus;
        }
        
        try {
            const isHealthy = await this.performHealthCheck();
            return {
                ...baseStatus,
                isRunning: isHealthy,
                lastHealthCheck: new Date()
            };
        } catch (error) {
            return baseStatus;
        }
    }
    
    /**
     * Start the Python server
     */
    private async startServer(): Promise<ServerStatus> {
        if (this.restartAttempts >= this.config.maxRestartAttempts) {
            throw new Error(`Failed to start server after ${this.config.maxRestartAttempts} attempts`);
        }
        
        this.restartAttempts++;
        
        try {
            // Clean up any existing process
            await this.stopServer();
            
            // Find available port
            this.currentPort = await this.findAvailablePort();
            this.outputChannel.appendLine(`Using port ${this.currentPort}`);
            
            // Find Python and Palette paths
            const pythonPath = await this.findPythonPath();
            const palettePath = await this.findPalettePath();
            
            this.outputChannel.appendLine(`Python path: ${pythonPath}`);
            this.outputChannel.appendLine(`Palette path: ${palettePath}`);
            
            // Start the server process
            const serverModule = 'palette.server.main:app';
            const args = [
                '-m', 'uvicorn',
                serverModule,
                '--host', this.config.host,
                '--port', this.currentPort.toString(),
                '--reload'
            ];
            
            this.outputChannel.appendLine(`Starting: ${pythonPath} ${args.join(' ')}`);
            
            this.serverProcess = spawn(pythonPath, args, {
                cwd: palettePath,
                env: {
                    ...process.env,
                    PYTHONPATH: path.join(palettePath, 'src'),
                    PALETTE_DEV_MODE: 'true'
                },
                stdio: ['ignore', 'pipe', 'pipe']
            });
            
            // Handle process events
            this.setupProcessEventHandlers();
            
            // Wait for server to be ready
            await this.waitForServerReady();
            
            // Start health monitoring
            this.startHealthMonitoring();
            
            // Reset restart attempts on successful start
            this.restartAttempts = 0;
            
            const status: ServerStatus = {
                isRunning: true,
                port: this.currentPort,
                pid: this.serverProcess.pid,
                startTime: new Date()
            };
            
            this.outputChannel.appendLine(`✅ Python server started successfully on port ${this.currentPort}`);
            return status;
            
        } catch (error) {
            this.outputChannel.appendLine(`❌ Failed to start server: ${error instanceof Error ? error.message : String(error)}`);
            throw error;
        }
    }
    
    /**
     * Stop the Python server
     */
    public async stopServer(): Promise<void> {
        this.outputChannel.appendLine('Stopping Python server...');
        
        // Stop health monitoring
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = null;
        }
        
        // Kill the process
        if (this.serverProcess) {
            this.serverProcess.kill('SIGTERM');
            
            // Wait for graceful shutdown, then force kill if needed
            await new Promise<void>((resolve) => {
                const timeout = setTimeout(() => {
                    if (this.serverProcess && !this.serverProcess.killed) {
                        this.outputChannel.appendLine('Force killing server process...');
                        this.serverProcess.kill('SIGKILL');
                    }
                    resolve();
                }, 5000);
                
                if (this.serverProcess) {
                    this.serverProcess.on('exit', () => {
                        clearTimeout(timeout);
                        resolve();
                    });
                }
            });
            
            this.serverProcess = null;
        }
        
        this.currentPort = 0;
        this.outputChannel.appendLine('✅ Python server stopped');
    }
    
    /**
     * Find an available port in the configured range
     */
    private async findAvailablePort(): Promise<number> {
        for (let port = this.config.minPort; port <= this.config.maxPort; port++) {
            if (await this.isPortAvailable(port)) {
                return port;
            }
        }
        throw new Error(`No available ports in range ${this.config.minPort}-${this.config.maxPort}`);
    }
    
    /**
     * Check if a port is available
     */
    private isPortAvailable(port: number): Promise<boolean> {
        return new Promise((resolve) => {
            const server = net.createServer();
            
            server.listen(port, this.config.host, () => {
                server.close(() => resolve(true));
            });
            
            server.on('error', () => resolve(false));
        });
    }
    
    /**
     * Find Python executable path
     */
    private async findPythonPath(): Promise<string> {
        // Check VS Code settings first
        const config = vscode.workspace.getConfiguration('palette');
        const pythonPath = config.get<string>('pythonPath');
        
        if (pythonPath && fs.existsSync(pythonPath)) {
            return pythonPath;
        }
        
        // Try to find Python in virtual environment
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (workspaceRoot) {
            const venvPython = path.join(workspaceRoot, '..', 'venv', 'bin', 'python');
            if (fs.existsSync(venvPython)) {
                return venvPython;
            }
        }
        
        // Default to system python
        return 'python3';
    }
    
    /**
     * Find Palette project root path
     */
    private async findPalettePath(): Promise<string> {
        // Check VS Code settings first
        const config = vscode.workspace.getConfiguration('palette');
        const projectPath = config.get<string>('projectPath');
        
        if (projectPath && fs.existsSync(path.join(projectPath, 'src', 'palette'))) {
            return projectPath;
        }
        
        // Try to find relative to workspace
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (workspaceRoot) {
            const parentPath = path.join(workspaceRoot, '..');
            if (fs.existsSync(path.join(parentPath, 'src', 'palette'))) {
                return parentPath;
            }
        }
        
        throw new Error('Could not find Palette project root. Please set palette.projectPath in VS Code settings.');
    }
    
    /**
     * Setup process event handlers
     */
    private setupProcessEventHandlers(): void {
        if (!this.serverProcess) return;
        
        this.serverProcess.stdout?.on('data', (data) => {
            this.outputChannel.appendLine(`[SERVER] ${data.toString().trim()}`);
        });
        
        this.serverProcess.stderr?.on('data', (data) => {
            this.outputChannel.appendLine(`[SERVER ERROR] ${data.toString().trim()}`);
        });
        
        this.serverProcess.on('exit', (code, signal) => {
            this.outputChannel.appendLine(`Server process exited with code ${code}, signal ${signal}`);
            this.serverProcess = null;
            
            if (code !== 0 && this.restartAttempts < this.config.maxRestartAttempts) {
                this.outputChannel.appendLine('Server crashed, attempting restart...');
                setTimeout(() => this.startServer().catch(console.error), 2000);
            }
        });
        
        this.serverProcess.on('error', (error) => {
            this.outputChannel.appendLine(`Server process error: ${error.message}`);
        });
    }
    
    /**
     * Wait for server to be ready
     */
    private async waitForServerReady(): Promise<void> {
        const startTime = Date.now();
        
        while (Date.now() - startTime < this.config.startupTimeout) {
            try {
                const isHealthy = await this.performHealthCheck();
                if (isHealthy) {
                    this.outputChannel.appendLine('Server health check passed');
                    return;
                }
            } catch (error) {
                // Health check failed, continue waiting
            }
            
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        throw new Error(`Server failed to start within ${this.config.startupTimeout}ms timeout`);
    }
    
    /**
     * Perform health check on the server
     */
    private async performHealthCheck(): Promise<boolean> {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(
                `http://${this.config.host}:${this.currentPort}/health`,
                { 
                    signal: controller.signal,
                    method: 'GET'
                }
            );
            
            clearTimeout(timeoutId);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Start health monitoring
     */
    private startHealthMonitoring(): void {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
        }
        
        this.healthCheckTimer = setInterval(async () => {
            try {
                const isHealthy = await this.performHealthCheck();
                if (!isHealthy) {
                    this.outputChannel.appendLine('❌ Health check failed, restarting server...');
                    await this.startServer();
                }
            } catch (error) {
                this.outputChannel.appendLine(`Health check error: ${error instanceof Error ? error.message : String(error)}`);
            }
        }, this.config.healthCheckInterval);
    }
    
    /**
     * Get server URL for API requests
     */
    public getServerUrl(): string {
        return `http://${this.config.host}:${this.currentPort}`;
    }
    
    /**
     * Clean up resources
     */
    public async dispose(): Promise<void> {
        await this.stopServer();
        this.outputChannel.dispose();
    }
}