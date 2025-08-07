/**
 * Conversation persistence and session management for VS Code extension
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ConversationMessage } from '../conversation/ConversationClient';

export interface ConversationSession {
    id: string;
    name: string;
    projectPath: string;
    createdAt: string;
    lastMessageAt: string;
    messages: ConversationMessage[];
    metadata: {
        messageCount: number;
        framework?: string;
        lastIntent?: string;
        tags?: string[];
    };
}

export class ConversationStorage {
    private context: vscode.ExtensionContext;
    private storageDir: string;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
        this.storageDir = path.join(context.globalStorageUri.fsPath, 'conversations');
        this.ensureStorageDirectory();
    }

    private ensureStorageDirectory(): void {
        if (!fs.existsSync(this.storageDir)) {
            fs.mkdirSync(this.storageDir, { recursive: true });
        }
    }

    async saveSession(session: ConversationSession): Promise<void> {
        try {
            const sessionPath = path.join(this.storageDir, `${session.id}.json`);
            
            // Update metadata
            session.metadata.messageCount = session.messages.length;
            session.lastMessageAt = new Date().toISOString();
            
            // Get last user message for better naming
            const lastUserMessage = session.messages
                .filter(msg => msg.role === 'user')
                .pop();
            
            if (lastUserMessage && !session.name.startsWith('Chat')) {
                // Update session name based on last message
                const shortName = this.generateSessionName(lastUserMessage.content);
                if (shortName !== session.name) {
                    session.name = shortName;
                }
            }

            await fs.promises.writeFile(
                sessionPath, 
                JSON.stringify(session, null, 2),
                'utf8'
            );
        } catch (error) {
            console.error('Failed to save conversation session:', error);
            throw new Error(`Failed to save conversation: ${error}`);
        }
    }

    async loadSession(sessionId: string): Promise<ConversationSession | null> {
        try {
            const sessionPath = path.join(this.storageDir, `${sessionId}.json`);
            
            if (!fs.existsSync(sessionPath)) {
                return null;
            }

            const data = await fs.promises.readFile(sessionPath, 'utf8');
            const session = JSON.parse(data) as ConversationSession;
            
            return session;
        } catch (error) {
            console.error('Failed to load conversation session:', error);
            return null;
        }
    }

    async listSessions(projectPath?: string): Promise<ConversationSession[]> {
        try {
            const files = await fs.promises.readdir(this.storageDir);
            const sessionFiles = files.filter(file => file.endsWith('.json'));
            
            const sessions: ConversationSession[] = [];
            
            for (const file of sessionFiles) {
                try {
                    const sessionPath = path.join(this.storageDir, file);
                    const data = await fs.promises.readFile(sessionPath, 'utf8');
                    const session = JSON.parse(data) as ConversationSession;
                    
                    // Filter by project if specified
                    if (projectPath && session.projectPath !== projectPath) {
                        continue;
                    }
                    
                    sessions.push(session);
                } catch (error) {
                    console.error(`Failed to load session file ${file}:`, error);
                }
            }
            
            // Sort by last message time (most recent first)
            sessions.sort((a, b) => 
                new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime()
            );
            
            return sessions;
        } catch (error) {
            console.error('Failed to list conversation sessions:', error);
            return [];
        }
    }

    async deleteSession(sessionId: string): Promise<boolean> {
        try {
            const sessionPath = path.join(this.storageDir, `${sessionId}.json`);
            
            if (fs.existsSync(sessionPath)) {
                await fs.promises.unlink(sessionPath);
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Failed to delete conversation session:', error);
            return false;
        }
    }

    async createSession(projectPath: string, name?: string): Promise<ConversationSession> {
        const sessionId = this.generateSessionId();
        const session: ConversationSession = {
            id: sessionId,
            name: name || this.generateDefaultSessionName(),
            projectPath: projectPath,
            createdAt: new Date().toISOString(),
            lastMessageAt: new Date().toISOString(),
            messages: [],
            metadata: {
                messageCount: 0
            }
        };

        await this.saveSession(session);
        return session;
    }

    async updateSession(sessionId: string, updates: Partial<ConversationSession>): Promise<boolean> {
        try {
            const session = await this.loadSession(sessionId);
            if (!session) {
                return false;
            }

            Object.assign(session, updates);
            await this.saveSession(session);
            return true;
        } catch (error) {
            console.error('Failed to update conversation session:', error);
            return false;
        }
    }

    async addMessage(sessionId: string, message: ConversationMessage): Promise<boolean> {
        try {
            const session = await this.loadSession(sessionId);
            if (!session) {
                return false;
            }

            session.messages.push(message);
            
            // Update metadata
            if (message.metadata?.intent) {
                session.metadata.lastIntent = message.metadata.intent;
            }
            
            if (message.metadata?.componentType && !session.metadata.tags?.includes(message.metadata.componentType)) {
                session.metadata.tags = session.metadata.tags || [];
                session.metadata.tags.push(message.metadata.componentType);
            }

            await this.saveSession(session);
            return true;
        } catch (error) {
            console.error('Failed to add message to session:', error);
            return false;
        }
    }

    async searchSessions(query: string, projectPath?: string): Promise<ConversationSession[]> {
        const sessions = await this.listSessions(projectPath);
        const queryLower = query.toLowerCase();

        return sessions.filter(session => {
            // Search in session name
            if (session.name.toLowerCase().includes(queryLower)) {
                return true;
            }

            // Search in message content
            return session.messages.some(message => 
                message.content.toLowerCase().includes(queryLower)
            );
        });
    }

    async getRecentSessions(count: number = 10, projectPath?: string): Promise<ConversationSession[]> {
        const sessions = await this.listSessions(projectPath);
        return sessions.slice(0, count);
    }

    async exportSession(sessionId: string, format: 'json' | 'markdown' = 'json'): Promise<string> {
        const session = await this.loadSession(sessionId);
        if (!session) {
            throw new Error('Session not found');
        }

        if (format === 'json') {
            return JSON.stringify(session, null, 2);
        } else {
            return this.sessionToMarkdown(session);
        }
    }

    async cleanupOldSessions(olderThanDays: number = 30): Promise<number> {
        const sessions = await this.listSessions();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

        let deletedCount = 0;

        for (const session of sessions) {
            const lastMessageDate = new Date(session.lastMessageAt);
            if (lastMessageDate < cutoffDate) {
                if (await this.deleteSession(session.id)) {
                    deletedCount++;
                }
            }
        }

        return deletedCount;
    }

    // Helper methods

    private generateSessionId(): string {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    private generateDefaultSessionName(): string {
        const date = new Date();
        const timeStr = date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        return `Chat ${timeStr}`;
    }

    private generateSessionName(firstMessage: string): string {
        // Extract key terms from first message to create a meaningful name
        const cleanMessage = firstMessage
            .replace(/[^a-zA-Z0-9\s]/g, '')
            .toLowerCase()
            .trim();

        const words = cleanMessage.split(/\s+/);
        
        // Look for component types
        const componentTypes = [
            'button', 'card', 'form', 'modal', 'navbar', 'header', 'footer', 
            'sidebar', 'menu', 'table', 'list', 'grid', 'hero', 'banner',
            'pricing', 'dashboard', 'chart', 'gallery', 'carousel'
        ];

        const foundType = componentTypes.find(type => 
            words.includes(type) || words.includes(type + 's')
        );

        if (foundType) {
            const adjectives = ['modern', 'beautiful', 'responsive', 'custom', 'dynamic'];
            const foundAdjective = adjectives.find(adj => words.includes(adj));
            
            if (foundAdjective) {
                return `${foundAdjective} ${foundType}`.replace(/^\w/, c => c.toUpperCase());
            } else {
                return foundType.replace(/^\w/, c => c.toUpperCase());
            }
        }

        // Fallback to first few words
        const shortName = words.slice(0, 3).join(' ');
        if (shortName.length > 0) {
            return shortName.replace(/^\w/, c => c.toUpperCase());
        }

        return this.generateDefaultSessionName();
    }

    private sessionToMarkdown(session: ConversationSession): string {
        let markdown = `# ${session.name}\n\n`;
        markdown += `**Created:** ${new Date(session.createdAt).toLocaleString()}\n`;
        markdown += `**Last Message:** ${new Date(session.lastMessageAt).toLocaleString()}\n`;
        markdown += `**Project:** ${session.projectPath}\n`;
        markdown += `**Messages:** ${session.metadata.messageCount}\n\n`;

        if (session.metadata.tags && session.metadata.tags.length > 0) {
            markdown += `**Tags:** ${session.metadata.tags.join(', ')}\n\n`;
        }

        markdown += `---\n\n`;

        for (const message of session.messages) {
            const timestamp = new Date(message.timestamp).toLocaleTimeString();
            const role = message.role === 'user' ? '👤 User' : '🤖 Assistant';
            
            markdown += `## ${role} (${timestamp})\n\n`;
            markdown += `${message.content}\n\n`;
            
            if (message.metadata?.componentCode) {
                markdown += `### Generated Code\n\n`;
                markdown += `\`\`\`tsx\n${message.metadata.componentCode}\n\`\`\`\n\n`;
            }
        }

        return markdown;
    }

    // VS Code integration helpers

    async showSessionPicker(projectPath?: string): Promise<ConversationSession | null> {
        const sessions = await this.getRecentSessions(20, projectPath);
        
        if (sessions.length === 0) {
            vscode.window.showInformationMessage('No conversation sessions found.');
            return null;
        }

        const items = sessions.map(session => ({
            label: session.name,
            description: `${session.metadata.messageCount} messages`,
            detail: `Last activity: ${new Date(session.lastMessageAt).toLocaleString()}`,
            session: session
        }));

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select a conversation to continue',
            matchOnDescription: true,
            matchOnDetail: true
        });

        return selected?.session || null;
    }

    async showDeleteConfirmation(session: ConversationSession): Promise<boolean> {
        const result = await vscode.window.showWarningMessage(
            `Delete conversation "${session.name}"?`,
            { modal: true },
            'Delete'
        );
        
        return result === 'Delete';
    }
}