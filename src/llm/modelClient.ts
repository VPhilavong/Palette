/**
 * OpenAI Model Client
 * 
 * This file provides the interface and implementation for communicating
 * with OpenAI's API. It handles:
 * - OpenAI API authentication and configuration
 * - Text completion generation (sync and streaming)
 * - Error handling and API key validation
 * - Model client factory for creating OpenAI instances
 * 
 * Only OpenAI is supported as the AI provider.
 */

import * as vscode from 'vscode';
import OpenAI from 'openai';

/**
 * Interface for OpenAI LLM provider
 */
export interface ModelClient {
    generateCompletion(prompt: string, options?: CompletionOptions): Promise<string>;
    generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string>;
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
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const apiKey = config.get<string>('openaiApiKey', '');
        
        if (apiKey) {
            this.openai = new OpenAI({ apiKey });
        }
    }

    async generateCompletion(prompt: string, options?: CompletionOptions): Promise<string> {
        if (!this.openai) {
            throw new Error('OpenAI API key not configured. Please set ui-copilot.openaiApiKey in settings.');
        }

        try {
            const response = await this.openai.chat.completions.create({
                model: options?.model || 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options?.maxTokens || 2000,
                temperature: options?.temperature || 0.7,
            });

            return response.choices[0]?.message?.content || '';
        } catch (error) {
            throw new Error(`OpenAI API error: ${error}`);
        }
    }

    async* generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string> {
        if (!this.openai) {
            throw new Error('OpenAI API key not configured. Please set ui-copilot.openaiApiKey in settings.');
        }

        try {
            const stream = await this.openai.chat.completions.create({
                model: options?.model || 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: prompt }],
                max_tokens: options?.maxTokens || 2000,
                temperature: options?.temperature || 0.7,
                stream: true,
            });

            for await (const chunk of stream) {
                const content = chunk.choices[0]?.delta?.content;
                if (content) {
                    yield content;
                }
            }
        } catch (error) {
            throw new Error(`OpenAI streaming error: ${error}`);
        }
    }
}


/**
 * Factory to create the OpenAI client
 */
export class ModelClientFactory {
    static createClient(): ModelClient {
        return new OpenAIClient();
    }
}