import * as vscode from 'vscode';
import { GoogleGenerativeAI } from '@google/generative-ai';
import OpenAI from 'openai';

/**
 * Interface for different LLM providers (OpenAI, Claude, Gemini)
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
 * Gemini client implementation (primary provider)
 */
export class GeminiClient implements ModelClient {
    private genAI: GoogleGenerativeAI | null = null;

    constructor() {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const apiKey = config.get<string>('geminiApiKey', '');
        
        if (apiKey) {
            this.genAI = new GoogleGenerativeAI(apiKey);
        }
    }

    async generateCompletion(prompt: string, options?: CompletionOptions): Promise<string> {
        if (!this.genAI) {
            throw new Error('Gemini API key not configured. Please set ui-copilot.geminiApiKey in settings.');
        }

        try {
            const model = this.genAI.getGenerativeModel({ 
                model: options?.model || 'gemini-2.0-flash-exp' 
            });

            const result = await model.generateContent(prompt);
            const response = await result.response;
            return response.text() || '';
        } catch (error) {
            throw new Error(`Gemini API error: ${error}`);
        }
    }

    async* generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string> {
        if (!this.genAI) {
            throw new Error('Gemini API key not configured. Please set ui-copilot.geminiApiKey in settings.');
        }

        try {
            const model = this.genAI.getGenerativeModel({ 
                model: options?.model || 'gemini-2.0-flash-exp' 
            });

            const result = await model.generateContentStream(prompt);
            
            for await (const chunk of result.stream) {
                const chunkText = chunk.text();
                if (chunkText) {
                    yield chunkText;
                }
            }
        } catch (error) {
            throw new Error(`Gemini streaming error: ${error}`);
        }
    }
}

/**
 * Factory to create the appropriate client based on configuration
 */
export class ModelClientFactory {
    static createClient(): ModelClient {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        const provider = config.get<string>('apiProvider', 'gemini');

        switch (provider) {
            case 'openai':
                return new OpenAIClient();
            case 'gemini':
                return new GeminiClient();
            default:
                return new GeminiClient(); // Default to Gemini
        }
    }
}