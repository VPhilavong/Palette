/**
 * Local HTTP Server for Palette AI Chatbot
 * Serves the chatbot HTML in VSCode Simple Browser
 */

import * as http from 'http';
import * as path from 'path';
import * as fs from 'fs';
import * as vscode from 'vscode';

export class ChatbotServer {
    private server: http.Server | null = null;
    private port: number = 0;
    private extensionPath: string;
    private fileOperationHandler?: (operation: any) => Promise<any>;
    
    constructor(extensionPath: string) {
        this.extensionPath = extensionPath;
    }

    /**
     * Set the file operation handler (called by VSCode extension)
     */
    setFileOperationHandler(handler: (operation: any) => Promise<any>) {
        this.fileOperationHandler = handler;
    }

    /**
     * Start the HTTP server on an available port
     */
    async start(): Promise<string> {
        return new Promise((resolve, reject) => {
            // Find an available port starting from 3001
            this.findAvailablePort(3001).then(port => {
                this.port = port;
                
                this.server = http.createServer((req, res) => {
                    this.handleRequest(req, res);
                });

                this.server.listen(port, 'localhost', () => {
                    const url = `http://localhost:${port}`;
                    console.log(`🎨 Palette Chatbot Server started on ${url}`);
                    resolve(url);
                });

                this.server.on('error', (error) => {
                    console.error('🎨 Chatbot server error:', error);
                    reject(error);
                });
            }).catch(reject);
        });
    }

    /**
     * Stop the HTTP server
     */
    async stop(): Promise<void> {
        return new Promise((resolve) => {
            if (this.server) {
                this.server.close(() => {
                    console.log('🎨 Palette Chatbot Server stopped');
                    this.server = null;
                    this.port = 0;
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }

    /**
     * Get the server URL if running
     */
    getUrl(): string | null {
        if (this.server && this.port) {
            return `http://localhost:${this.port}`;
        }
        return null;
    }

    /**
     * Check if server is running
     */
    isRunning(): boolean {
        return this.server !== null;
    }

    /**
     * Handle HTTP requests
     */
    private handleRequest(req: http.IncomingMessage, res: http.ServerResponse): void {
        // Parse URL to remove query parameters first
        let requestPath = req.url || '/';
        if (requestPath.includes('?')) {
            requestPath = requestPath.split('?')[0];
        }
        
        console.log(`🎨 Server request: ${req.method} ${req.url} -> cleaned: ${requestPath}`);
        
        // Handle API requests
        if (requestPath.startsWith('/api/')) {
            this.handleApiRequest(req, res);
            return;
        }
        
        // Map root to index.html for static file serving
        let filePath = requestPath === '/' ? '/index.html' : requestPath;

        // Security: prevent directory traversal
        if (filePath.includes('..')) {
            console.log(`🎨 Blocked directory traversal: ${filePath}`);
            this.send404(res);
            return;
        }

        // Serve files from chatbot directory
        const fullPath = path.join(this.extensionPath, 'chatbot', filePath);
        console.log(`🎨 Full path: ${fullPath}`);
        
        // Check if file exists
        fs.access(fullPath, fs.constants.F_OK, (err) => {
            if (err) {
                console.log(`🎨 File not found: ${fullPath}`);
                this.send404(res);
                return;
            }

            // Get file extension for content type
            const ext = path.extname(fullPath).toLowerCase();
            const contentType = this.getContentType(ext);

            // Read and serve file
            fs.readFile(fullPath, (err, data) => {
                if (err) {
                    this.send500(res, err);
                    return;
                }

                res.writeHead(200, {
                    'Content-Type': contentType,
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                });
                res.end(data);
                
                console.log(`🎨 Served: ${filePath} (${contentType})`);
            });
        });
    }

    /**
     * Handle API requests for file operations
     */
    private async handleApiRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        // Set CORS headers for Simple Browser compatibility
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
        
        // Handle preflight OPTIONS requests
        if (req.method === 'OPTIONS') {
            res.writeHead(200);
            res.end();
            return;
        }

        const requestPath = req.url!.split('?')[0];
        console.log(`🎨 API request: ${req.method} ${requestPath}`);

        try {
            if (req.method === 'POST' && requestPath === '/api/files/create') {
                await this.handleCreateFile(req, res);
            } else if (req.method === 'GET' && requestPath === '/api/files/list') {
                await this.handleListFiles(req, res);
            } else if (req.method === 'POST' && requestPath === '/api/files/read') {
                await this.handleReadFile(req, res);
            } else if (req.method === 'GET' && requestPath === '/api/workspace/info') {
                await this.handleWorkspaceInfo(req, res);
            } else {
                this.sendApiError(res, 404, 'API_NOT_FOUND', `API endpoint not found: ${requestPath}`);
            }
        } catch (error) {
            console.error('🎨 API error:', error);
            this.sendApiError(res, 500, 'INTERNAL_ERROR', `Internal server error: ${error}`);
        }
    }

    /**
     * Handle file creation API endpoint
     */
    private async handleCreateFile(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        const body = await this.parseRequestBody(req);
        
        if (!body || !body.path || !body.content) {
            this.sendApiError(res, 400, 'INVALID_REQUEST', 'Missing required fields: path, content');
            return;
        }

        if (!this.fileOperationHandler) {
            this.sendApiError(res, 503, 'HANDLER_NOT_AVAILABLE', 'File operation handler not available');
            return;
        }

        try {
            const result = await this.fileOperationHandler({
                type: 'create',
                path: body.path,
                content: body.content,
                language: body.language || 'tsx'
            });

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            }));

        } catch (error: any) {
            console.error('🎨 File creation error:', error);
            this.sendApiError(res, 400, 'FILE_CREATION_FAILED', error.message || 'Failed to create file');
        }
    }

    /**
     * Handle workspace info API endpoint
     */
    private async handleWorkspaceInfo(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        if (!this.fileOperationHandler) {
            this.sendApiError(res, 503, 'HANDLER_NOT_AVAILABLE', 'File operation handler not available');
            return;
        }

        try {
            const result = await this.fileOperationHandler({
                type: 'workspace-info'
            });

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            }));

        } catch (error: any) {
            console.error('🎨 Workspace info error:', error);
            this.sendApiError(res, 400, 'WORKSPACE_INFO_FAILED', error.message || 'Failed to get workspace info');
        }
    }

    /**
     * Handle list files API endpoint
     */
    private async handleListFiles(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        if (!this.fileOperationHandler) {
            this.sendApiError(res, 503, 'HANDLER_NOT_AVAILABLE', 'File operation handler not available');
            return;
        }

        try {
            const result = await this.fileOperationHandler({
                type: 'list'
            });

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            }));

        } catch (error: any) {
            console.error('🎨 List files error:', error);
            this.sendApiError(res, 400, 'LIST_FILES_FAILED', error.message || 'Failed to list files');
        }
    }

    /**
     * Handle read file API endpoint
     */
    private async handleReadFile(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
        const body = await this.parseRequestBody(req);
        
        if (!body || !body.path) {
            this.sendApiError(res, 400, 'INVALID_REQUEST', 'Missing required field: path');
            return;
        }

        if (!this.fileOperationHandler) {
            this.sendApiError(res, 503, 'HANDLER_NOT_AVAILABLE', 'File operation handler not available');
            return;
        }

        try {
            const result = await this.fileOperationHandler({
                type: 'read',
                path: body.path
            });

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            }));

        } catch (error: any) {
            console.error('🎨 Read file error:', error);
            this.sendApiError(res, 400, 'READ_FILE_FAILED', error.message || 'Failed to read file');
        }
    }

    /**
     * Parse request body as JSON
     */
    private async parseRequestBody(req: http.IncomingMessage): Promise<any> {
        return new Promise((resolve, reject) => {
            let body = '';
            
            req.on('data', (chunk) => {
                body += chunk.toString();
            });
            
            req.on('end', () => {
                try {
                    resolve(body ? JSON.parse(body) : null);
                } catch (error) {
                    reject(new Error('Invalid JSON in request body'));
                }
            });
            
            req.on('error', reject);
        });
    }

    /**
     * Send API error response
     */
    private sendApiError(res: http.ServerResponse, statusCode: number, errorCode: string, message: string): void {
        res.writeHead(statusCode, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            success: false,
            error: {
                code: errorCode,
                message,
                timestamp: new Date().toISOString()
            }
        }));
    }

    /**
     * Get content type based on file extension
     */
    private getContentType(ext: string): string {
        const contentTypes: { [key: string]: string } = {
            '.html': 'text/html',
            '.js': 'application/javascript',
            '.css': 'text/css',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon'
        };
        return contentTypes[ext] || 'text/plain';
    }

    /**
     * Send 404 Not Found response
     */
    private send404(res: http.ServerResponse): void {
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>404 - Not Found</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: #1e1e1e; color: #d4d4d4; }
                    h1 { color: #ef4444; }
                </style>
            </head>
            <body>
                <h1>404 - File Not Found</h1>
                <p>The requested file could not be found on the Palette Chatbot server.</p>
                <p><a href="/" style="color: #0e639c;">Return to Chatbot</a></p>
            </body>
            </html>
        `);
        console.log('🎨 Served: 404 Not Found');
    }

    /**
     * Send 500 Internal Server Error response
     */
    private send500(res: http.ServerResponse, error: Error): void {
        res.writeHead(500, { 'Content-Type': 'text/html' });
        res.end(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>500 - Server Error</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background: #1e1e1e; color: #d4d4d4; }
                    h1 { color: #ef4444; }
                </style>
            </head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>An error occurred while serving the requested file.</p>
                <p><a href="/" style="color: #0e639c;">Return to Chatbot</a></p>
            </body>
            </html>
        `);
        console.error('🎨 Server error:', error);
    }

    /**
     * Find an available port starting from the given port
     */
    private async findAvailablePort(startPort: number): Promise<number> {
        return new Promise((resolve, reject) => {
            const testPort = (port: number) => {
                const server = http.createServer();
                
                server.listen(port, 'localhost', () => {
                    server.once('close', () => {
                        resolve(port);
                    });
                    server.close();
                });
                
                server.on('error', (err: any) => {
                    if (err.code === 'EADDRINUSE') {
                        // Port is in use, try next port
                        testPort(port + 1);
                    } else {
                        reject(err);
                    }
                });
            };

            testPort(startPort);
        });
    }
}