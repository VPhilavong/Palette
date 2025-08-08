/**
 * AI Capability Router
 * Routes requests based on model capabilities (GPT-5 vs GPT-4.1)
 * Implements tiered architecture for different model limitations
 */

import * as vscode from 'vscode';

export interface ModelCapabilities {
    streaming: boolean;
    functionCalling: boolean;
    structuredData: boolean;
    maxTokens: number;
    tier: 'core' | 'enhanced';
}

export interface GenerationRequest {
    message: string;
    model: string;
    context?: ProjectContext;
    options?: GenerationOptions;
}

export interface GenerationOptions {
    maxTokens?: number;
    temperature?: number;
    stream?: boolean;
}

export interface ProjectContext {
    workspacePath?: string;
    framework?: string;
    components?: string[];
    designTokens?: Record<string, any>;
    tsConfig?: any;
}

export interface GenerationResult {
    success: boolean;
    content: string;
    metadata?: {
        model: string;
        tier: 'core' | 'enhanced';
        tokensUsed?: number;
        codeBlocks?: CodeBlock[];
        files?: FileSpec[];
        strategy?: GenerationStrategy;
        toolResults?: any[];
        stepsUsed?: number;
    };
    error?: string;
}

export interface CodeBlock {
    language: string;
    code: string;
    filename?: string;
}

export interface FileSpec {
    path: string;
    content: string;
    type: 'component' | 'hook' | 'util' | 'test' | 'style';
}

export type GenerationStrategy = 'REUSE' | 'COMPOSE' | 'EXTEND' | 'GENERATE';

export class AICapabilityRouter {
    private static readonly MODEL_CAPABILITIES: Record<string, ModelCapabilities> = {
        // Enhanced Tier - Full AI SDK 5 capabilities
        'gpt-4.1-2025-04-14': {
            streaming: true,
            functionCalling: true,
            structuredData: true,
            maxTokens: 8000,
            tier: 'enhanced'
        },
        
        // Core Tier - GPT-5 models with limitations
        'gpt-5-2025-08-07': {
            streaming: false,
            functionCalling: false,
            structuredData: false,
            maxTokens: 2000,
            tier: 'core'
        },
        'gpt-5-mini-2025-08-07': {
            streaming: false,
            functionCalling: false,
            structuredData: false,
            maxTokens: 2000,
            tier: 'core'
        },
        'gpt-5-nano-2025-08-07': {
            streaming: false,
            functionCalling: false,
            structuredData: false,
            maxTokens: 1500,
            tier: 'core'
        }
    };

    /**
     * Get model capabilities for routing decisions
     */
    static getModelCapabilities(model: string): ModelCapabilities {
        return this.MODEL_CAPABILITIES[model] || {
            streaming: false,
            functionCalling: false,
            structuredData: false,
            maxTokens: 1500,
            tier: 'core'
        };
    }

    /**
     * Detect model tier for strategy selection
     */
    static detectModelTier(model: string): 'core' | 'enhanced' {
        const capabilities = this.getModelCapabilities(model);
        return capabilities.tier;
    }

    /**
     * Validate if requested features are supported by model
     */
    static validateRequest(request: GenerationRequest): { valid: boolean; reason?: string } {
        const capabilities = this.getModelCapabilities(request.model);
        
        // Check if streaming is requested but not supported
        if (request.options?.stream && !capabilities.streaming) {
            return {
                valid: false,
                reason: 'Streaming not supported by this model. Falling back to standard generation.'
            };
        }

        // Check token limits
        if (request.options?.maxTokens && request.options.maxTokens > capabilities.maxTokens) {
            return {
                valid: false,
                reason: `Requested ${request.options.maxTokens} tokens exceeds model limit of ${capabilities.maxTokens}`
            };
        }

        return { valid: true };
    }

    /**
     * Route request to appropriate generation strategy
     */
    static async route(request: GenerationRequest): Promise<GenerationResult> {
        const validation = this.validateRequest(request);
        if (!validation.valid) {
            console.warn(`🎨 AICapabilityRouter: ${validation.reason}`);
        }

        const capabilities = this.getModelCapabilities(request.model);
        const tier = capabilities.tier;

        console.log(`🎨 Routing request to ${tier} tier (${request.model})`);

        try {
            // Import strategy manager dynamically to avoid circular dependencies
            const { ModelStrategyManager } = await import('./model-strategy-manager');
            const strategy = ModelStrategyManager.getStrategy(tier);
            
            // Adjust request based on model capabilities
            const adjustedRequest = this.adjustRequestForCapabilities(request, capabilities);
            
            const result = await strategy.execute(adjustedRequest);
            
            // Add routing metadata
            result.metadata = {
                ...result.metadata,
                model: request.model,
                tier: tier
            };

            return result;

        } catch (error: any) {
            console.error(`🎨 AICapabilityRouter error:`, error);
            
            return {
                success: false,
                content: '',
                error: `Generation failed: ${error.message}`,
                metadata: {
                    model: request.model,
                    tier: tier
                }
            };
        }
    }

    /**
     * Adjust request parameters based on model capabilities
     */
    private static adjustRequestForCapabilities(
        request: GenerationRequest, 
        capabilities: ModelCapabilities
    ): GenerationRequest {
        const adjustedOptions = { ...request.options };

        // Adjust token limits
        if (!adjustedOptions.maxTokens || adjustedOptions.maxTokens > capabilities.maxTokens) {
            adjustedOptions.maxTokens = Math.floor(capabilities.maxTokens * 0.9); // Leave some buffer
        }

        // Disable streaming if not supported
        if (adjustedOptions.stream && !capabilities.streaming) {
            adjustedOptions.stream = false;
        }

        return {
            ...request,
            options: adjustedOptions
        };
    }

    /**
     * Get recommended models for current VS Code workspace
     */
    static async getRecommendedModels(): Promise<string[]> {
        const config = vscode.workspace.getConfiguration('palette');
        const hasOpenAIKey = !!config.get<string>('openaiApiKey');
        
        if (!hasOpenAIKey) {
            return [];
        }

        // Return models in order of recommendation (Enhanced first, then Core)
        return [
            'gpt-4.1-2025-04-14',  // Enhanced capabilities
            'gpt-5-2025-08-07',    // Latest GPT-5
            'gpt-5-mini-2025-08-07', // Balanced performance
            'gpt-5-nano-2025-08-07'  // Fast responses
        ];
    }

    /**
     * Get current model from VS Code configuration
     */
    static getCurrentModel(): string {
        const config = vscode.workspace.getConfiguration('palette');
        return config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
    }

    /**
     * Check if model supports specific feature
     */
    static supportsFeature(model: string, feature: keyof ModelCapabilities): boolean {
        const capabilities = this.getModelCapabilities(model);
        return capabilities[feature] as boolean;
    }
}