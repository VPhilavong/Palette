/**
 * AI Provider Abstraction Layer using AI SDK
 * Unified interface for OpenAI, Anthropic, Google, and other providers
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
        // OpenAI Models
        'gpt-4o': {
            provider: 'openai',
            model: 'gpt-4o',
            maxTokens: 4096,
            supportsStreaming: true,
            supportsFunctions: true,
            defaultTemperature: 0.7
        },
        'gpt-4o-mini': {
            provider: 'openai',
            model: 'gpt-4o-mini',
            maxTokens: 16384,
            supportsStreaming: true,
            supportsFunctions: true,
            defaultTemperature: 0.7
        },
        'gpt-5': {
            provider: 'openai',
            model: 'gpt-5',
            maxTokens: 2000, // Conservative limit for 10K TPM
            supportsStreaming: true,
            supportsFunctions: false,
            // GPT-5 uses default temperature only
        },
        'gpt-5-mini': {
            provider: 'openai',
            model: 'gpt-5-mini',
            maxTokens: 2000,
            supportsStreaming: true,
            supportsFunctions: false,
        },
        'gpt-5-2025-08-07': {
            provider: 'openai',
            model: 'gpt-5-2025-08-07',
            maxTokens: 2000, // Conservative for 10K TPM limit
            supportsStreaming: true,
            supportsFunctions: false,
        },
        'gpt-3.5-turbo': {
            provider: 'openai',
            model: 'gpt-3.5-turbo',
            maxTokens: 4096,
            supportsStreaming: true,
            supportsFunctions: true,
            defaultTemperature: 0.7
        },
        
        
        // Anthropic Models
        'claude-3-5-sonnet-20241022': {
            provider: 'anthropic',
            model: 'claude-3-5-sonnet-20241022',
            maxTokens: 8192,
            supportsStreaming: true,
            supportsFunctions: false,
            defaultTemperature: 0.7
        },
        'claude-3-5-haiku-20241022': {
            provider: 'anthropic',
            model: 'claude-3-5-haiku-20241022',
            maxTokens: 8192,
            supportsStreaming: true,
            supportsFunctions: false,
            defaultTemperature: 0.7
        },
        'claude-3-opus-20240229': {
            provider: 'anthropic',
            model: 'claude-3-opus-20240229',
            maxTokens: 4096,
            supportsStreaming: true,
            supportsFunctions: false,
            defaultTemperature: 0.7
        }
    };

    /**
     * Get provider configuration for a model
     */
    static getProviderConfig(modelName: string): ProviderConfig {
        const config = this.PROVIDER_CONFIGS[modelName];
        if (!config) {
            console.warn(`🎨 Unknown model ${modelName}, using gpt-4o-mini as fallback`);
            return this.PROVIDER_CONFIGS['gpt-4o-mini'];
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
        } else if (config.provider === 'anthropic') {
            const { anthropic } = await import('@ai-sdk/anthropic');
            return anthropic(config.model);
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
            case 'anthropic':
                return config.get<string>('anthropicApiKey');
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
                error: `${config.provider.toUpperCase()} API key not configured. Please set it in VS Code settings.`
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
     * Get recommended model based on use case
     */
    static getRecommendedModel(useCase: 'speed' | 'quality' | 'cost'): string {
        switch (useCase) {
            case 'speed':
                return 'gpt-4o-mini';
            case 'quality':
                return 'gpt-4o';
            case 'cost':
                return 'gpt-3.5-turbo';
            default:
                return 'gpt-4o-mini';
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