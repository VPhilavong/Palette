/**
 * Simple AI SDK Agent
 * Lightweight implementation without complex tool definitions
 */

import * as vscode from 'vscode';

// Defensive imports for AI SDK packages
let aiSdkOpenai: any = null;
let aiSdkAnthropic: any = null;
let aiSdkCore: any = null;

try {
    aiSdkOpenai = require('@ai-sdk/openai');
    console.log('AI SDK OpenAI imported successfully');
} catch (error) {
    console.error('Failed to import @ai-sdk/openai:', error);
}

try {
    aiSdkAnthropic = require('@ai-sdk/anthropic');
    console.log('AI SDK Anthropic imported successfully');
} catch (error) {
    console.error('Failed to import @ai-sdk/anthropic:', error);
}

try {
    aiSdkCore = require('ai');
    console.log('AI SDK Core imported successfully');
} catch (error) {
    console.error('Failed to import ai:', error);
}

export interface SimpleAISDKAgentConfig {
    provider: 'openai' | 'anthropic';
    model?: string;
    temperature?: number;
    enableStreaming?: boolean;
}

export interface AgentResponse {
    content: string;
    isComplete: boolean;
}

/**
 * Simple Palette AI Agent using Vercel AI SDK
 * Focused on text generation with manual tool handling
 */
export class SimpleAISDKAgent {
    private config: SimpleAISDKAgentConfig;
    
    constructor(config: Partial<SimpleAISDKAgentConfig> = {}) {
        // Get configuration from VS Code settings
        const vscodeConfig = vscode.workspace.getConfiguration('palette');
        
        this.config = {
            provider: config.provider || 'openai',
            model: config.model || vscodeConfig.get('defaultModel', 'gpt-4o-mini'),
            temperature: config.temperature ?? 0.7,
            enableStreaming: config.enableStreaming ?? true,
            ...config
        };
    }
    
    /**
     * Get the appropriate model based on configuration
     */
    private getModel() {
        const apiKey = this.getApiKey();
        
        if (this.config.provider === 'anthropic') {
            if (!aiSdkAnthropic?.anthropic) {
                throw new Error('Anthropic AI SDK not available. Check if @ai-sdk/anthropic is installed.');
            }
            return aiSdkAnthropic.anthropic(this.config.model || 'claude-3-5-sonnet-20241022');
        } else {
            if (!aiSdkOpenai?.openai) {
                throw new Error('OpenAI AI SDK not available. Check if @ai-sdk/openai is installed.');
            }
            return aiSdkOpenai.openai(this.config.model || 'gpt-4o-mini');
        }
    }
    
    /**
     * Get API key from VS Code configuration or environment
     */
    private getApiKey(): string {
        const vscodeConfig = vscode.workspace.getConfiguration('palette');
        
        if (this.config.provider === 'anthropic') {
            return vscodeConfig.get<string>('anthropicApiKey') || 
                   process.env.ANTHROPIC_API_KEY || '';
        } else {
            return vscodeConfig.get<string>('openaiApiKey') || 
                   process.env.OPENAI_API_KEY || '';
        }
    }
    
    /**
     * Process user message with streaming support
     */
    async processMessage(
        message: string,
        onStream?: (chunk: string) => void
    ): Promise<AgentResponse> {
        const model = this.getModel();
        const systemPrompt = this.getSystemPrompt();
        
        try {
            if (this.config.enableStreaming && onStream) {
                // Streaming mode
                if (!aiSdkCore?.streamText) {
                    throw new Error('AI SDK Core streamText not available. Check if ai package is installed.');
                }
                
                const { textStream } = await aiSdkCore.streamText({
                    model,
                    system: systemPrompt,
                    messages: [{ role: 'user', content: message }],
                    temperature: this.config.temperature,
                });
                
                let fullContent = '';
                for await (const delta of textStream) {
                    fullContent += delta;
                    onStream(delta);
                }
                
                return {
                    content: fullContent,
                    isComplete: true
                };
            } else {
                // Non-streaming mode
                if (!aiSdkCore?.generateText) {
                    throw new Error('AI SDK Core generateText not available. Check if ai package is installed.');
                }
                
                const { text } = await aiSdkCore.generateText({
                    model,
                    system: systemPrompt,
                    messages: [{ role: 'user', content: message }],
                    temperature: this.config.temperature,
                });
                
                return {
                    content: text,
                    isComplete: true
                };
            }
        } catch (error) {
            console.error('Simple AI Agent error:', error);
            throw error;
        }
    }
    
    /**
     * Get system prompt for the design agent
     */
    private getSystemPrompt(): string {
        return `You are Palette, an expert UI/UX design prototyping agent similar to Vercel v0. Your mission is to help users create complete, beautiful, and functional web pages and features using modern technologies.

## Your Capabilities:
- Generate complete pages and features (not individual components)
- Analyze project structures and design systems
- Provide guidance for shadcn/ui components
- Help with Vite development server setup
- Create and recommend file structures
- Provide design system guidance

## Key Principles:
1. **Always build complete experiences** - Generate full pages with multiple sections that users can see and interact with
2. **Focus on design prototyping** - Think like v0.dev: rapid iteration, beautiful designs, modern patterns
3. **Use shadcn/ui + Tailwind CSS** - Leverage the modern React + TypeScript + Vite stack
4. **Provide actionable guidance** - Give specific steps the user can follow
5. **Follow design systems** - Analyze existing patterns and maintain consistency

## Available Actions:
When the user asks you to perform actions, provide clear step-by-step instructions for:
- Generating complete pages with proper file structure
- Installing shadcn/ui components needed
- Starting the dev server for live preview
- Creating and updating files
- Setting up project structure

## Examples of Good Requests:
- "Create a modern SaaS landing page with hero, features, and pricing sections"
- "Build an e-commerce product grid with filters and search"
- "Design a dashboard with sidebar navigation and data visualization"
- "Make a blog homepage with featured articles and categories"

Remember: You're creating complete design experiences that users can see, use, and iterate on immediately. Always provide complete, working code examples and clear implementation steps.`;
    }
    
    /**
     * Analyze user intent and determine what actions to take
     */
    async analyzeIntent(message: string): Promise<{
        intent: 'generate' | 'analyze' | 'preview' | 'install' | 'manage_files' | 'conversation';
        confidence: number;
        suggestedActions: string[];
    }> {
        const lowerMessage = message.toLowerCase();
        
        // Simple intent detection based on keywords
        if (lowerMessage.includes('generate') || lowerMessage.includes('create') || lowerMessage.includes('build')) {
            return {
                intent: 'generate',
                confidence: 0.8,
                suggestedActions: [
                    'Analyze the request to understand what type of design is needed',
                    'Generate complete page/feature code',
                    'Provide file structure and implementation steps',
                    'Suggest shadcn/ui components to install'
                ]
            };
        } else if (lowerMessage.includes('analyze') || lowerMessage.includes('understand') || lowerMessage.includes('project')) {
            return {
                intent: 'analyze',
                confidence: 0.7,
                suggestedActions: [
                    'Examine project structure and dependencies',
                    'Identify design tokens and patterns',
                    'Provide recommendations for improvements'
                ]
            };
        } else if (lowerMessage.includes('preview') || lowerMessage.includes('server') || lowerMessage.includes('dev')) {
            return {
                intent: 'preview',
                confidence: 0.8,
                suggestedActions: [
                    'Provide steps to start the Vite dev server',
                    'Guide user to open preview in browser',
                    'Explain hot reload capabilities'
                ]
            };
        } else if (lowerMessage.includes('install') || lowerMessage.includes('component')) {
            return {
                intent: 'install',
                confidence: 0.7,
                suggestedActions: [
                    'Identify required shadcn/ui components',
                    'Provide installation commands',
                    'Explain component usage'
                ]
            };
        } else {
            return {
                intent: 'conversation',
                confidence: 0.6,
                suggestedActions: [
                    'Provide helpful guidance about design prototyping',
                    'Ask clarifying questions if needed',
                    'Suggest specific actions the user can take'
                ]
            };
        }
    }
    
    /**
     * Update agent configuration
     */
    updateConfig(newConfig: Partial<SimpleAISDKAgentConfig>) {
        this.config = { ...this.config, ...newConfig };
    }
}

/**
 * Factory function to create a Simple AI SDK Agent instance
 */
export function createSimpleAISDKAgent(config: Partial<SimpleAISDKAgentConfig> = {}): SimpleAISDKAgent {
    return new SimpleAISDKAgent(config);
}