/**
 * Conversation Manager for Palette AI Chatbot
 * Handles session persistence, memory management, and conversation context
 */

import * as vscode from 'vscode';

export interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: {
        codeBlocks?: CodeBlock[];
        intent?: string;
        context?: any;
        availableActions?: string[];
        error?: string;
        isSetup?: boolean;
        showSettings?: boolean;
    };
}

export interface CodeBlock {
    language: string;
    code: string;
    filename?: string;
}

export interface ConversationSession {
    id: string;
    messages: ConversationMessage[];
    startTime: string;
    lastActivity: string;
    metadata?: {
        projectPath?: string;
        totalMessages?: number;
        topics?: string[];
    };
}

export class ConversationManager {
    private static readonly STORAGE_KEY = 'palette.conversation';
    private static readonly MAX_MESSAGES = 100; // Limit to prevent token overflow
    private static readonly SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours
    
    private context: vscode.ExtensionContext;
    private currentSession: ConversationSession | null = null;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.initializeSession();
    }

    /**
     * Initialize or restore conversation session
     */
    private async initializeSession(): Promise<void> {
        try {
            const storedSession = await this.getStoredSession();
            
            if (storedSession && !this.isSessionExpired(storedSession)) {
                this.currentSession = storedSession;
                console.log('🎨 Restored conversation session:', this.currentSession.id);
            } else {
                await this.createNewSession();
            }
        } catch (error) {
            console.error('🎨 Error initializing session:', error);
            await this.createNewSession();
        }
    }

    /**
     * Create a new conversation session
     */
    private async createNewSession(): Promise<void> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        
        this.currentSession = {
            id: this.generateSessionId(),
            messages: [],
            startTime: new Date().toISOString(),
            lastActivity: new Date().toISOString(),
            metadata: {
                projectPath: workspaceFolder?.uri.fsPath,
                totalMessages: 0,
                topics: []
            }
        };

        await this.saveSession();
        console.log('🎨 Created new conversation session:', this.currentSession.id);
    }

    /**
     * Add a message to the current conversation
     */
    async addMessage(role: 'user' | 'assistant', content: string, metadata?: any): Promise<void> {
        if (!this.currentSession) {
            await this.createNewSession();
        }

        const message: ConversationMessage = {
            role,
            content,
            timestamp: new Date().toISOString(),
            metadata
        };

        this.currentSession!.messages.push(message);
        this.currentSession!.lastActivity = new Date().toISOString();
        this.currentSession!.metadata!.totalMessages = this.currentSession!.messages.length;

        // Trim messages if exceeding limit
        if (this.currentSession!.messages.length > ConversationManager.MAX_MESSAGES) {
            // Keep the first few and last messages to maintain context
            const keepFirst = 10;
            const keepLast = ConversationManager.MAX_MESSAGES - keepFirst;
            
            const firstMessages = this.currentSession!.messages.slice(0, keepFirst);
            const lastMessages = this.currentSession!.messages.slice(-keepLast);
            
            this.currentSession!.messages = [...firstMessages, ...lastMessages];
            
            console.log('🎨 Trimmed conversation to maintain context within limits');
        }

        // Extract and store topics for context
        if (role === 'user') {
            this.extractAndStoreTopics(content);
        }

        await this.saveSession();
    }

    /**
     * Get conversation history for AI context
     */
    async getConversationHistory(): Promise<ConversationMessage[]> {
        if (!this.currentSession) {
            await this.createNewSession();
        }

        return this.currentSession!.messages;
    }

    /**
     * Get formatted conversation context for AI
     */
    async getContextForAI(): Promise<any[]> {
        const history = await this.getConversationHistory();
        
        // Convert to format expected by AI SDK
        return history.map(msg => ({
            role: msg.role,
            content: msg.content
        }));
    }

    /**
     * Clear current conversation
     */
    async clearConversation(): Promise<void> {
        if (this.currentSession) {
            this.currentSession.messages = [];
            this.currentSession.metadata!.totalMessages = 0;
            this.currentSession.metadata!.topics = [];
            await this.saveSession();
        }
    }

    /**
     * Get conversation statistics
     */
    getStatistics(): {
        messageCount: number;
        sessionAge: string;
        topics: string[];
    } {
        if (!this.currentSession) {
            return {
                messageCount: 0,
                sessionAge: 'No active session',
                topics: []
            };
        }

        const sessionStart = new Date(this.currentSession.startTime);
        const now = new Date();
        const ageMs = now.getTime() - sessionStart.getTime();
        const ageHours = Math.floor(ageMs / (1000 * 60 * 60));
        const ageMinutes = Math.floor((ageMs % (1000 * 60 * 60)) / (1000 * 60));

        return {
            messageCount: this.currentSession.messages.length,
            sessionAge: `${ageHours}h ${ageMinutes}m`,
            topics: this.currentSession.metadata?.topics || []
        };
    }

    /**
     * Export conversation history
     */
    async exportConversation(): Promise<string> {
        const history = await this.getConversationHistory();
        
        let exportText = `# Palette AI Conversation Export\n`;
        exportText += `Session ID: ${this.currentSession?.id}\n`;
        exportText += `Export Date: ${new Date().toISOString()}\n`;
        exportText += `Messages: ${history.length}\n\n`;

        for (const message of history) {
            const timestamp = new Date(message.timestamp).toLocaleString();
            exportText += `## ${message.role.toUpperCase()} [${timestamp}]\n\n`;
            exportText += `${message.content}\n\n`;
            
            if (message.metadata?.codeBlocks) {
                for (const codeBlock of message.metadata.codeBlocks) {
                    exportText += `\`\`\`${codeBlock.language}\n${codeBlock.code}\n\`\`\`\n\n`;
                }
            }
            
            exportText += `---\n\n`;
        }

        return exportText;
    }

    /**
     * Save current session to VS Code storage
     */
    private async saveSession(): Promise<void> {
        if (this.currentSession) {
            await this.context.globalState.update(ConversationManager.STORAGE_KEY, this.currentSession);
        }
    }

    /**
     * Get stored session from VS Code storage
     */
    private async getStoredSession(): Promise<ConversationSession | null> {
        return this.context.globalState.get<ConversationSession>(ConversationManager.STORAGE_KEY) || null;
    }

    /**
     * Check if session is expired
     */
    private isSessionExpired(session: ConversationSession): boolean {
        const lastActivity = new Date(session.lastActivity);
        const now = new Date();
        const timeDiff = now.getTime() - lastActivity.getTime();
        
        return timeDiff > ConversationManager.SESSION_TIMEOUT;
    }

    /**
     * Generate unique session ID
     */
    private generateSessionId(): string {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2);
        return `session_${timestamp}_${random}`;
    }

    /**
     * Extract topics from user message for context
     */
    private extractAndStoreTopics(content: string): void {
        if (!this.currentSession?.metadata?.topics) {
            return;
        }

        // Simple topic extraction based on keywords
        const topicKeywords = [
            'component', 'page', 'form', 'button', 'modal', 'navigation',
            'dashboard', 'landing', 'header', 'footer', 'sidebar',
            'react', 'tailwind', 'shadcn', 'typescript', 'javascript',
            'responsive', 'mobile', 'desktop', 'dark mode', 'theme'
        ];

        const extractedTopics = topicKeywords.filter(keyword => 
            content.toLowerCase().includes(keyword.toLowerCase())
        );

        // Add new topics while avoiding duplicates
        for (const topic of extractedTopics) {
            if (!this.currentSession.metadata.topics.includes(topic)) {
                this.currentSession.metadata.topics.push(topic);
                
                // Limit topics to prevent storage bloat
                if (this.currentSession.metadata.topics.length > 20) {
                    this.currentSession.metadata.topics = this.currentSession.metadata.topics.slice(-20);
                }
            }
        }
    }

    /**
     * Get conversation summary for context compression
     */
    async getConversationSummary(): Promise<string> {
        if (!this.currentSession || this.currentSession.messages.length === 0) {
            return 'No conversation history';
        }

        const stats = this.getStatistics();
        const recentMessages = this.currentSession.messages.slice(-10);
        
        let summary = `Conversation Summary (${stats.messageCount} messages, ${stats.sessionAge} old):\n`;
        summary += `Topics discussed: ${stats.topics.join(', ')}\n\n`;
        summary += `Recent conversation:\n`;
        
        for (const msg of recentMessages) {
            const preview = msg.content.substring(0, 100) + (msg.content.length > 100 ? '...' : '');
            summary += `${msg.role}: ${preview}\n`;
        }

        return summary;
    }

    /**
     * Reset session (for testing or manual reset)
     */
    async resetSession(): Promise<void> {
        await this.context.globalState.update(ConversationManager.STORAGE_KEY, undefined);
        await this.createNewSession();
        console.log('🎨 Session reset successfully');
    }
}