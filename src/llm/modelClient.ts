/**
 * OpenAI Model Client
 * 
 * This file provides the interface and implementation for communicating
 * with OpenAI's API directly. It handles:
 * - OpenAI API authentication and configuration
 * - Text completion generation (sync and streaming)
 * - Error handling and API key validation
 * - Support for both chat completions and embeddings
 * 
 * Uses OpenAI API directly for maximum control and feature access.
 */

import * as vscode from 'vscode';
import OpenAI from 'openai';

/**
 * Interface for AI model provider
 */
export interface ModelClient {
    generateCompletion(prompt: string, options?: CompletionOptions): Promise<string>;
    generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string>;
    isAvailable(): Promise<boolean>;
}

export interface CompletionOptions {
    maxTokens?: number;
    temperature?: number;
    model?: string;
}

/**
 * OpenAI client implementation
 */
export class OpenAIClient implements ModelClient {
    private openai: OpenAI | null = null;

    constructor() {
        this.initializeOpenAI();
    }

    private initializeOpenAI(): void {
        // Try to get API key from multiple sources (for development flexibility)
        let apiKey = '';
        
        // 1. Try VS Code settings first (for end users)
        const config = vscode.workspace.getConfiguration();
        apiKey = config.get<string>('palette.openai.apiKey', '');
        console.log('Palette: API key from VS Code settings:', apiKey ? `${apiKey.substring(0, 10)}...` : 'not found');
        
        // 2. Fall back to environment variable (for development)
        if (!apiKey && process.env.OPENAI_API_KEY) {
            apiKey = process.env.OPENAI_API_KEY;
            console.log('Palette: Using OpenAI API key from environment variable:', `${apiKey.substring(0, 10)}...`);
        }
        
        console.log('Palette: Final API key status:', apiKey ? 'found' : 'not found');
        console.log('Palette: All environment variables:', Object.keys(process.env).filter(key => key.includes('OPENAI')));
        
        if (apiKey) {
            this.openai = new OpenAI({ 
                apiKey,
                dangerouslyAllowBrowser: false
            });
            console.log('Palette: OpenAI client initialized successfully');
        } else {
            console.log('Palette: No OpenAI API key found in settings or environment');
        }
    }

    async isAvailable(): Promise<boolean> {
        if (!this.openai) {
            return false;
        }
        
        try {
            // Test with a minimal request
            await this.openai.models.list();
            return true;
        } catch {
            return false;
        }
    }

    async generateCompletion(prompt: string, options?: CompletionOptions): Promise<string> {
        if (!this.openai) {
            throw new Error('OpenAI API key not configured. Please set palette.openai.apiKey in settings.');
        }

        try {
            const response = await this.openai.chat.completions.create({
                model: options?.model || 'gpt-4o',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options?.maxTokens || 4000,
                temperature: options?.temperature || 0.7,
            });

            return response.choices[0]?.message?.content || '';
        } catch (error: any) {
            if (error.status === 401) {
                throw new Error('Invalid OpenAI API key. Please check your palette.openai.apiKey setting.');
            } else if (error.status === 429) {
                throw new Error('OpenAI API rate limit exceeded. Please try again later.');
            } else if (error.status === 403) {
                throw new Error('OpenAI API access denied. Please check your API key permissions.');
            } else {
                throw new Error(`OpenAI API error: ${error.message || error}`);
            }
        }
    }

    async* generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string> {
        if (!this.openai) {
            throw new Error('OpenAI API key not configured. Please set palette.openai.apiKey in settings.');
        }

        try {
            const stream = await this.openai.chat.completions.create({
                model: options?.model || 'gpt-4o',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options?.maxTokens || 4000,
                temperature: options?.temperature || 0.7,
                stream: true,
            });

            for await (const chunk of stream) {
                const content = chunk.choices[0]?.delta?.content;
                if (content) {
                    yield content;
                }
            }
        } catch (error: any) {
            if (error.status === 401) {
                throw new Error('Invalid OpenAI API key. Please check your palette.openai.apiKey setting.');
            } else if (error.status === 429) {
                throw new Error('OpenAI API rate limit exceeded. Please try again later.');
            } else {
                throw new Error(`OpenAI streaming error: ${error.message || error}`);
            }
        }
    }
}

/**
 * Factory to create OpenAI model client
 */
export class ModelClientFactory {
    static createClient(): ModelClient {
        return new OpenAIClient();
    }
    
    /**
     * Check if OpenAI is properly configured
     */
    static async isConfigured(): Promise<boolean> {
        // Check VS Code settings first
        const config = vscode.workspace.getConfiguration();
        let apiKey = config.get<string>('palette.openai.apiKey', '');
        
        // Fall back to environment variable (for development)
        if (!apiKey && process.env.OPENAI_API_KEY) {
            apiKey = process.env.OPENAI_API_KEY;
        }
        
        return apiKey.length > 0;
    }
    
    /**
     * Show configuration help to user
     */
    static showConfigurationHelp(): void {
        vscode.window.showInformationMessage(
            'OpenAI API key required for Palette to work.',
            'Open Settings',
            'Get API Key'
        ).then(selection => {
            if (selection === 'Open Settings') {
                vscode.commands.executeCommand('workbench.action.openSettings', 'palette.openai.apiKey');
            } else if (selection === 'Get API Key') {
                vscode.env.openExternal(vscode.Uri.parse('https://platform.openai.com/api-keys'));
            }
        });
    }
}
