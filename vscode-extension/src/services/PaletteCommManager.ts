/**
 * PaletteCommManager - Unified communication manager for VS Code extension
 * Orchestrates between AI SDK and Python intelligence layer with intelligent routing
 */

import * as vscode from 'vscode';
import { RequestRouter, GenerationProvider, GenerationResult, StreamingCallback, RoutingDecision } from '../intelligence/RequestRouter';
import { ComplexityAnalyzer, DesignRequest, RequestComplexity } from '../intelligence/ComplexityAnalyzer';
import { PythonServerManager } from './PythonServerManager';

export interface PaletteMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    metadata?: {
        provider?: GenerationProvider;
        complexity?: RequestComplexity;
        duration?: number;
        fallbackUsed?: boolean;
    };
}

export interface PaletteSession {
    id: string;
    messages: PaletteMessage[];
    workspacePath: string;
    createdAt: string;
    lastActivity: string;
    preferences: SessionPreferences;
}

export interface SessionPreferences {
    preferredProvider: 'auto' | 'ai_sdk' | 'python_backend';
    enableAnalysis: boolean;
    streamingEnabled: boolean;
    qualityThreshold: 'low' | 'medium' | 'high';
}

export interface PaletteResponse {
    content: string;
    provider: GenerationProvider;
    routing: RoutingDecision;
    performance: {
        duration: number;
        classification: RequestComplexity;
        fallbackUsed: boolean;
    };
    quality?: {
        score: number;
        suggestions: string[];
    };
}

export interface StreamingOptions {
    onMessage?: (chunk: string, metadata?: any) => void;
    onStatusUpdate?: (status: string, phase?: string) => void;
    onRouting?: (decision: RoutingDecision) => void;
    onComplete?: (response: PaletteResponse) => void;
    onError?: (error: string) => void;
}

export class PaletteCommManager {
    private static instance: PaletteCommManager | null = null;
    
    private requestRouter: RequestRouter;
    private complexityAnalyzer: ComplexityAnalyzer;
    private pythonServerManager: PythonServerManager;
    private outputChannel: vscode.OutputChannel;
    
    private currentSession: PaletteSession | null = null;
    private sessionHistory: Map<string, PaletteSession> = new Map();
    
    private readonly defaultPreferences: SessionPreferences = {
        preferredProvider: 'auto',
        enableAnalysis: true,
        streamingEnabled: true,
        qualityThreshold: 'medium'
    };

    private constructor() {
        this.requestRouter = RequestRouter.getInstance();
        this.complexityAnalyzer = ComplexityAnalyzer.getInstance();
        this.pythonServerManager = PythonServerManager.getInstance();
        this.outputChannel = vscode.window.createOutputChannel('Palette Communications');
        
        this.loadSession();
    }

    public static getInstance(): PaletteCommManager {
        if (!PaletteCommManager.instance) {
            PaletteCommManager.instance = new PaletteCommManager();
        }
        return PaletteCommManager.instance;
    }

    /**
     * Main entry point for processing user messages
     */
    public async processMessage(
        message: string,
        options: StreamingOptions = {}
    ): Promise<PaletteResponse> {
        this.outputChannel.appendLine(`\n🎨 Processing message: "${message.substring(0, 100)}..."`);
        
        try {
            // Ensure session exists
            await this.ensureSession();
            
            // Create design request with context
            const request = await this.createDesignRequest(message);
            
            // Get routing decision
            const routing = await this.requestRouter.routeRequest(request);
            
            if (options.onRouting) {
                options.onRouting(routing);
            }

            // Create streaming callback
            const callback: StreamingCallback = {
                onChunk: (chunk: string, metadata?: any) => {
                    if (options.onMessage) {
                        options.onMessage(chunk, metadata);
                    }
                },
                onStatusUpdate: (status: string, phase?: string) => {
                    this.outputChannel.appendLine(`📊 ${phase || 'status'}: ${status}`);
                    if (options.onStatusUpdate) {
                        options.onStatusUpdate(status, phase);
                    }
                },
                onError: (error: string) => {
                    this.outputChannel.appendLine(`❌ Error: ${error}`);
                    if (options.onError) {
                        options.onError(error);
                    }
                },
                onComplete: (result: GenerationResult) => {
                    this.outputChannel.appendLine(`✅ Completed with ${result.provider} in ${result.duration}ms`);
                }
            };

            // Process with routing
            const result = await this.requestRouter.processRequest(request, callback);
            
            // Create response
            const response: PaletteResponse = {
                content: result.content,
                provider: result.provider,
                routing: routing,
                performance: {
                    duration: result.duration,
                    classification: result.metadata.complexity,
                    fallbackUsed: result.metadata.fallbackUsed
                },
                quality: result.metadata.quality as { score: number; suggestions: string[]; } | undefined
            };

            // Update session
            await this.updateSession(message, response);
            
            if (options.onComplete) {
                options.onComplete(response);
            }

            this.outputChannel.appendLine(`🎯 Response generated successfully (${result.duration}ms)`);
            return response;

        } catch (error) {
            const errorMessage = `Failed to process message: ${error instanceof Error ? error.message : String(error)}`;
            this.outputChannel.appendLine(`💥 ${errorMessage}`);
            
            if (options.onError) {
                options.onError(errorMessage);
            }
            
            throw error;
        }
    }

    /**
     * Create a design request with full context
     */
    private async createDesignRequest(message: string): Promise<DesignRequest> {
        // Get workspace context
        const workspaceContext = await this.complexityAnalyzer.getWorkspaceContext();
        
        // Get conversation history
        const conversationHistory = this.currentSession?.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp
        })) || [];

        // Detect if existing code analysis is needed
        const requiresAnalysis = 
            message.toLowerCase().includes('analyze') ||
            message.toLowerCase().includes('existing') ||
            message.toLowerCase().includes('current') ||
            workspaceContext?.hasComponents;

        return {
            message,
            fileCount: this.estimateFileCount(message),
            hasExistingCode: workspaceContext?.hasComponents || false,
            requiresAnalysis,
            workspaceContext,
            conversationHistory: conversationHistory as any[], // Type assertion for compatibility
            userIntent: this.extractUserIntent(message)
        };
    }

    /**
     * Estimate how many files will be generated
     */
    private estimateFileCount(message: string): number {
        const multiFileIndicators = [
            'page', 'dashboard', 'app', 'site', 'feature',
            'multi-file', 'multiple files', 'complete',
            'routing', 'navigation'
        ];

        const lowerMessage = message.toLowerCase();
        const matches = multiFileIndicators.filter(indicator => 
            lowerMessage.includes(indicator)
        ).length;

        if (matches > 2) return 5; // Complex multi-file
        if (matches > 0) return 2; // Simple multi-file
        return 1; // Single file
    }

    /**
     * Extract user intent from message
     */
    private extractUserIntent(message: string): string {
        const intents = [
            { pattern: /^(create|make|build|generate)/, intent: 'create' },
            { pattern: /^(modify|change|update|edit)/, intent: 'modify' },
            { pattern: /^(fix|repair|correct)/, intent: 'fix' },
            { pattern: /^(analyze|review|check)/, intent: 'analyze' },
            { pattern: /^(optimize|improve|enhance)/, intent: 'optimize' }
        ];

        for (const { pattern, intent } of intents) {
            if (pattern.test(message.toLowerCase())) {
                return intent;
            }
        }

        return 'general';
    }

    /**
     * Ensure we have an active session
     */
    private async ensureSession(): Promise<void> {
        if (!this.currentSession) {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '';
            
            this.currentSession = {
                id: this.generateSessionId(),
                messages: [],
                workspacePath,
                createdAt: new Date().toISOString(),
                lastActivity: new Date().toISOString(),
                preferences: { ...this.defaultPreferences }
            };
            
            this.outputChannel.appendLine(`🆕 Created new session: ${this.currentSession.id}`);
        }
    }

    /**
     * Update session with new message and response
     */
    private async updateSession(userMessage: string, response: PaletteResponse): Promise<void> {
        if (!this.currentSession) return;

        // Add user message
        this.currentSession.messages.push({
            role: 'user',
            content: userMessage,
            timestamp: new Date().toISOString()
        });

        // Add assistant response
        this.currentSession.messages.push({
            role: 'assistant',
            content: response.content,
            timestamp: new Date().toISOString(),
            metadata: {
                provider: response.provider,
                complexity: response.performance.classification,
                duration: response.performance.duration,
                fallbackUsed: response.performance.fallbackUsed
            }
        });

        this.currentSession.lastActivity = new Date().toISOString();
        
        // Save session
        await this.saveSession();
    }

    /**
     * Get system status
     */
    public async getSystemStatus() {
        const pythonStatus = await this.pythonServerManager.getServerStatus();
        const routingStats = this.requestRouter.getRoutingStats();
        
        return {
            session: {
                id: this.currentSession?.id,
                messageCount: this.currentSession?.messages.length || 0,
                workspacePath: this.currentSession?.workspacePath
            },
            pythonBackend: pythonStatus,
            routing: routingStats,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Update session preferences
     */
    public updatePreferences(preferences: Partial<SessionPreferences>): void {
        if (this.currentSession) {
            this.currentSession.preferences = {
                ...this.currentSession.preferences,
                ...preferences
            };
            this.saveSession();
            this.outputChannel.appendLine(`⚙️ Updated preferences: ${JSON.stringify(preferences)}`);
        }
    }

    /**
     * Clear conversation history
     */
    public async clearConversation(): Promise<void> {
        if (this.currentSession) {
            this.currentSession.messages = [];
            this.currentSession.lastActivity = new Date().toISOString();
            await this.saveSession();
            this.outputChannel.appendLine('🧹 Cleared conversation history');
        }
    }

    /**
     * Export conversation
     */
    public exportConversation(): any {
        if (!this.currentSession) return null;
        
        return {
            ...this.currentSession,
            exportedAt: new Date().toISOString()
        };
    }

    /**
     * Generate unique session ID
     */
    private generateSessionId(): string {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Load session from VS Code storage
     */
    private async loadSession(): Promise<void> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) return;

            const sessionFile = vscode.Uri.joinPath(workspaceFolder.uri, '.vscode', 'palette-session.json');
            const content = await vscode.workspace.fs.readFile(sessionFile);
            const sessionData = JSON.parse(content.toString());

            if (sessionData && sessionData.id) {
                this.currentSession = sessionData;
                this.sessionHistory.set(sessionData.id, sessionData);
                this.outputChannel.appendLine(`📂 Loaded session: ${sessionData.id}`);
            }
        } catch (error) {
            // No existing session, will create new one
            this.outputChannel.appendLine('📝 No existing session found, will create new one');
        }
    }

    /**
     * Save session to VS Code storage
     */
    private async saveSession(): Promise<void> {
        try {
            if (!this.currentSession) return;

            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) return;

            const sessionFile = vscode.Uri.joinPath(workspaceFolder.uri, '.vscode', 'palette-session.json');
            
            // Ensure .vscode directory exists
            const vscodeDir = vscode.Uri.joinPath(workspaceFolder.uri, '.vscode');
            try {
                await vscode.workspace.fs.createDirectory(vscodeDir);
            } catch {
                // Directory already exists
            }

            const content = Buffer.from(JSON.stringify(this.currentSession, null, 2));
            await vscode.workspace.fs.writeFile(sessionFile, content);
            
            // Also update history
            this.sessionHistory.set(this.currentSession.id, this.currentSession);

        } catch (error) {
            this.outputChannel.appendLine(`⚠️ Failed to save session: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Get conversation history
     */
    public getConversationHistory(): PaletteMessage[] {
        return this.currentSession?.messages || [];
    }

    /**
     * Get session preferences
     */
    public getPreferences(): SessionPreferences {
        return this.currentSession?.preferences || this.defaultPreferences;
    }

    /**
     * Dispose resources
     */
    public async dispose(): Promise<void> {
        await this.saveSession();
        this.outputChannel.dispose();
    }
}