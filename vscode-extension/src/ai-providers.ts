/**
 * AI Provider Abstraction Layer using AI SDK
 * Unified interface for OpenAI (GPT-5 family)
 */

import * as vscode from 'vscode';

export interface ProviderConfig {
    provider: string;
    model: string;
    maxTokens: number;
    supportsStreaming: boolean;
    supportsFunctions: boolean;
    defaultTemperature?: number;
}

export class AIProviderRegistry {
    private static readonly PROVIDER_CONFIGS: Record<string, ProviderConfig> = {
        // OpenAI GPT-5 family (only)
        'gpt-5-2025-08-07': {
            provider: 'openai',
            model: 'gpt-5-2025-08-07',
            maxTokens: 2000, // Conservative for 10K TPM limit
            supportsStreaming: false, // Disabled until org verification
            supportsFunctions: false,
        },
        'gpt-5-mini-2025-08-07': {
            provider: 'openai',
            model: 'gpt-5-mini-2025-08-07',
            maxTokens: 2000,
            supportsStreaming: false, // Disabled until org verification
            supportsFunctions: false,
        },
        'gpt-5-nano-2025-08-07': {
            provider: 'openai',
            model: 'gpt-5-nano-2025-08-07',
            maxTokens: 1500,
            supportsStreaming: false, // Disabled until org verification
            supportsFunctions: false,
        }
    };

    /**
     * Optional human-readable descriptions for models
     * Centralizing here prevents duplication across the extension.
     */
    private static readonly MODEL_DESCRIPTIONS: Record<string, string> = {
        'gpt-5-2025-08-07': 'GPT-5 (pinned 2025-08-07)',
        'gpt-5-mini-2025-08-07': 'GPT-5 Mini (balanced default)',
        'gpt-5-nano-2025-08-07': 'GPT-5 Nano (fastest, cheapest)'
    };

    /**
     * Get provider configuration for a model
     */
    static getProviderConfig(modelName: string): ProviderConfig {
        const config = this.PROVIDER_CONFIGS[modelName];
        if (!config) {
            console.warn(`🎨 Unknown model ${modelName}, using gpt-5-mini-2025-08-07 as fallback`);
            return this.PROVIDER_CONFIGS['gpt-5-mini-2025-08-07'];
        }
        return config;
    }

    /**
     * Get AI SDK provider instance
     */
    static async getProvider(modelName: string) {
        const config = this.getProviderConfig(modelName);
        
    if (config.provider === 'openai') {
            const { openai } = await import('@ai-sdk/openai');
            return openai(config.model);
        } else {
            throw new Error(`Unsupported provider: ${config.provider}`);
        }
    }

    /**
     * Get API key for provider
     */
    static getApiKey(providerName: string): string | undefined {
        const config = vscode.workspace.getConfiguration('palette');
        
        switch (providerName) {
            case 'openai':
                return config.get<string>('openaiApiKey');
            default:
                return undefined;
        }
    }

    /**
     * Validate provider setup
     */
    static validateProvider(modelName: string): { valid: boolean; error?: string } {
        const config = this.getProviderConfig(modelName);
        const apiKey = this.getApiKey(config.provider);
        
    if (!apiKey) {
            return {
                valid: false,
        error: `OpenAI API key not configured. Please set it in VS Code settings.`
            };
        }

        return { valid: true };
    }

    /**
     * Get all available models
     */
    static getAvailableModels(): string[] {
        return Object.keys(this.PROVIDER_CONFIGS);
    }

    /**
     * Get human-readable description for a model
     */
    static getModelDescription(modelName: string): string {
        return this.MODEL_DESCRIPTIONS[modelName] || 'AI model';
    }

    /**
     * Helper to present choices in quick pick UIs
     */
    static getModelChoices(): Array<{ label: string; description: string }>{
        return this.getAvailableModels().map(name => ({
            label: name,
            description: this.getModelDescription(name)
        }));
    }

    /**
     * Get recommended model based on use case
     */
    static getRecommendedModel(useCase: 'speed' | 'quality' | 'cost'): string {
        switch (useCase) {
            case 'speed':
                return 'gpt-5-nano-2025-08-07';
            case 'quality':
                return 'gpt-5-2025-08-07';
            case 'cost':
                return 'gpt-5-nano-2025-08-07';
            default:
                return 'gpt-5-mini-2025-08-07';
        }
    }

    /**
     * Check if model supports streaming
     */
    static supportsStreaming(modelName: string): boolean {
        return this.getProviderConfig(modelName).supportsStreaming;
    }

    /**
     * Get model-specific generation parameters
     */
    static getGenerationParams(modelName: string, maxTokens?: number) {
        const config = this.getProviderConfig(modelName);
        
        const params: any = {
            maxTokens: maxTokens || config.maxTokens,
        };

        // Add temperature if supported (GPT-5 models don't support custom temperature)
        if (config.defaultTemperature !== undefined) {
            params.temperature = config.defaultTemperature;
        }

        return params;
    }
}