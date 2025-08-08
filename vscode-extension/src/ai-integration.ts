/**
 * AI Integration for Palette Chatbot
 * Handles communication with backend and AI response generation
 */

import * as vscode from 'vscode';
import { ConversationMessage, CodeBlock } from './conversation-manager';

export interface AIResponse {
    content: string;
    codeBlocks?: CodeBlock[];
    intent?: string;
    suggestedActions?: string[];
}

export interface ProjectContext {
    projectPath?: string;
    framework?: string;
    dependencies?: string[];
    components?: string[];
    styling?: string[];
}

export class AIIntegrationService {
    private static readonly BACKEND_URL = 'http://localhost:8765';
    private static readonly TIMEOUT = 30000; // 30 seconds

    /**
     * Generate AI response using the hybrid approach:
     * 1. Get context from Python backend
     * 2. Generate response using Vercel AI SDK
     */
    static async generateResponse(
        userMessage: string,
        conversationHistory: ConversationMessage[]
    ): Promise<AIResponse> {
        try {
            // Get project context from backend
            const projectContext = await this.getProjectContext();
            
            // Prepare conversation context for AI
            const messages = conversationHistory.map(msg => ({
                role: msg.role,
                content: msg.content
            }));

            // Add current user message
            messages.push({
                role: 'user',
                content: userMessage
            });

            // Get AI model configuration from VS Code settings
            const config = vscode.workspace.getConfiguration('palette');
            const apiKey = config.get<string>('openaiApiKey');
            const model = config.get<string>('defaultModel') || 'gpt-4.1-2025-04-14';

            if (!apiKey) {
                throw new Error('OpenAI API key not configured. Please set it in VS Code settings.');
            }

            // Generate response using OpenAI via our backend
            const response = await this.callBackendGenerate(userMessage, messages, projectContext, apiKey, model);
            
            return response;

        } catch (error: any) {
            console.error('🎨 Error generating AI response:', error);
            
            // Fallback to direct OpenAI call if backend is unavailable
            if (error.message?.includes('ECONNREFUSED') || error.message?.includes('fetch')) {
                console.log('🎨 Backend unavailable, trying direct AI call...');
                return await this.generateDirectResponse(userMessage, conversationHistory);
            }
            
            throw error;
        }
    }

    /**
     * Get project context from Python backend
     */
    private static async getProjectContext(): Promise<ProjectContext> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                return {};
            }

            const response = await fetch(`${this.BACKEND_URL}/api/context`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    projectPath: workspaceFolder.uri.fsPath
                }),
                signal: AbortSignal.timeout(this.TIMEOUT)
            });

            if (!response.ok) {
                throw new Error(`Backend context API error: ${response.status}`);
            }

            const context = await response.json();
            console.log('🎨 Retrieved project context:', context);
            
            return {
                projectPath: context.project_path,
                framework: context.framework,
                dependencies: context.dependencies,
                components: context.components,
                styling: context.styling
            };

        } catch (error: any) {
            console.warn('🎨 Could not get project context from backend:', error.message || error);
            return {};
        }
    }

    /**
     * Call backend generation endpoint
     */
    private static async callBackendGenerate(
        userMessage: string,
        messages: any[],
        projectContext: ProjectContext,
        apiKey: string,
        model: string
    ): Promise<AIResponse> {
        const response = await fetch(`${this.BACKEND_URL}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: userMessage,
                conversation_history: messages,
                project_context: projectContext,
                api_key: apiKey,
                model: model
            }),
            signal: AbortSignal.timeout(this.TIMEOUT)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend generation error: ${response.status} - ${errorText}`);
        }

        const result = await response.json();
        
        return {
            content: result.content,
            codeBlocks: result.code_blocks || [],
            intent: result.intent,
            suggestedActions: result.suggested_actions
        };
    }

    /**
     * Fallback direct AI call - simplified fallback response
     */
    private static async generateDirectResponse(
        userMessage: string,
        conversationHistory: ConversationMessage[]
    ): Promise<AIResponse> {
        // For now, return a helpful fallback message
        // In the future, this could implement direct OpenAI API calls
        const fallbackResponse = `I understand you want me to help with: "${userMessage}"

I'm currently trying to connect to the Palette backend server. Please make sure:
1. The backend server is running (http://localhost:8765)
2. Your OpenAI API key is configured in VS Code settings
3. Try your request again in a moment

Would you like me to help you with:
- Creating React components
- Building pages and layouts
- UI/UX improvements
- Code explanations

I specialize in React, TypeScript, Tailwind CSS, and shadcn/ui components.`;

        return {
            content: fallbackResponse,
            codeBlocks: [],
            intent: this.detectIntent(userMessage),
            suggestedActions: [
                'Check backend server status',
                'Verify API key configuration',
                'Try a simple component request'
            ]
        };
    }

    /**
     * Get system prompt for AI
     */
    private static getSystemPrompt(): string {
        return `You are Palette AI, a helpful assistant for React developers. You specialize in:

1. **Component Generation**: Create React components using TypeScript, Tailwind CSS, and shadcn/ui
2. **Page Creation**: Build complete page layouts and experiences
3. **Code Improvement**: Refactor and enhance existing code
4. **UI/UX Guidance**: Provide design system advice and best practices

Guidelines:
- Always use TypeScript for React components
- Prefer functional components with hooks
- Use Tailwind CSS for styling
- Integrate shadcn/ui components when appropriate
- Write accessible, production-ready code
- Provide clear explanations with your code

When generating code:
- Use proper TypeScript interfaces
- Include proper imports
- Add meaningful component names
- Use semantic HTML elements
- Implement responsive design patterns
- Follow React best practices

Be conversational, helpful, and focus on creating high-quality UI components and experiences.`;
    }

    /**
     * Extract code blocks from AI response
     */
    private static extractCodeBlocks(content: string): CodeBlock[] {
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        const codeBlocks: CodeBlock[] = [];
        let match;

        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const code = match[2].trim();
            
            codeBlocks.push({
                language,
                code,
                filename: this.inferFilename(code, language)
            });
        }

        return codeBlocks;
    }

    /**
     * Infer filename from code content
     */
    private static inferFilename(code: string, language: string): string | undefined {
        // Try to extract component name for React files
        if (language === 'tsx' || language === 'jsx') {
            // Look for export default ComponentName or const ComponentName
            const componentMatch = code.match(/(?:export\s+default\s+function\s+(\w+)|const\s+(\w+):\s*React\.FC|export\s+default\s+(\w+))/);
            if (componentMatch) {
                const componentName = componentMatch[1] || componentMatch[2] || componentMatch[3];
                return `${componentName}.${language}`;
            }
        }

        // Default filenames based on language
        const extensions: Record<string, string> = {
            'tsx': 'Component.tsx',
            'jsx': 'Component.jsx',
            'ts': 'index.ts',
            'js': 'index.js',
            'css': 'styles.css',
            'html': 'index.html',
            'json': 'config.json'
        };

        return extensions[language];
    }

    /**
     * Detect intent from user message
     */
    private static detectIntent(message: string): string {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('generate') || lowerMessage.includes('create') || lowerMessage.includes('make')) {
            if (lowerMessage.includes('page')) return 'generate_page';
            if (lowerMessage.includes('component')) return 'generate_component';
            return 'generate_new';
        }
        
        if (lowerMessage.includes('fix') || lowerMessage.includes('improve') || lowerMessage.includes('refactor')) {
            return 'improve_code';
        }
        
        if (lowerMessage.includes('explain') || lowerMessage.includes('how') || lowerMessage.includes('what')) {
            return 'explain';
        }
        
        return 'general';
    }

    /**
     * Test backend connection
     */
    static async testConnection(): Promise<boolean> {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            return response.ok;
        } catch (error: any) {
            console.warn('🎨 Backend connection test failed:', error);
            return false;
        }
    }

    /**
     * Get backend status
     */
    static async getBackendStatus(): Promise<{
        connected: boolean;
        version?: string;
        error?: string;
    }> {
        try {
            const response = await fetch(`${this.BACKEND_URL}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    connected: true,
                    version: data.version
                };
            } else {
                return {
                    connected: false,
                    error: `HTTP ${response.status}`
                };
            }
        } catch (error: any) {
            return {
                connected: false,
                error: error.message || 'Unknown error'
            };
        }
    }
}

/**
 * Main function to generate AI response (backwards compatibility)
 */
export async function generateAIResponse(
    userMessage: string,
    conversationHistory: ConversationMessage[]
): Promise<AIResponse> {
    return await AIIntegrationService.generateResponse(userMessage, conversationHistory);
}