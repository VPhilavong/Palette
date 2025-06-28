import * as vscode from 'vscode';

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
    private apiKey: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        this.apiKey = config.get('openaiApiKey', '');
    }

    async generateCompletion(prompt: string, options?: CompletionOptions): Promise<string> {
        // TODO: Implement OpenAI API calls
        throw new Error('Not implemented yet - Phase 5');
    }

    async* generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string> {
        // TODO: Implement streaming
        throw new Error('Not implemented yet - Phase 5');
    }
}

/**
 * Claude client implementation  
 */
export class ClaudeClient implements ModelClient {
    private apiKey: string;

    constructor() {
        const config = vscode.workspace.getConfiguration('ui-copilot');
        this.apiKey = config.get('claudeApiKey', '');
    }

    async generateCompletion(prompt: string, options?: CompletionOptions): Promise<string> {
        // TODO: Implement Claude API calls
        throw new Error('Not implemented yet - Phase 5');
    }

    async* generateStream(prompt: string, options?: CompletionOptions): AsyncGenerator<string> {
        // TODO: Implement streaming
        throw new Error('Not implemented yet - Phase 5');
    }
}