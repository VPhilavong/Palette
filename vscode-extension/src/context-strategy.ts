/**
 * Context Strategy for managing token budgets across different AI models
 * Optimizes context size based on model capabilities and token limits
 */

export interface ContextConfig {
    maxSystemPrompt: number;
    maxProjectContext: number;
    maxConversationHistory: number;
    componentsLimit: number;
    designTokensMode: 'minimal' | 'essential' | 'full';
    historyMessageLimit: number;
}

export class ContextStrategy {
    /**
     * Get context configuration based on AI model
     */
    static getStrategy(model: string): ContextConfig {
        // GPT-5 models have strict 10K TPM limits
        if (model.startsWith('gpt-5')) {
            return {
                maxSystemPrompt: 100,        // Ultra-minimal prompt
                maxProjectContext: 3000,     // Severely limited context
                maxConversationHistory: 1000, // Only last message
                componentsLimit: 3,          // Top 3 components only
                designTokensMode: 'minimal', // Just colors
                historyMessageLimit: 1       // Single conversation turn
            };
        }

    // Legacy GPT-4o-mini path (kept for backward compatibility)
        if (model.includes('4o-mini')) {
            return {
                maxSystemPrompt: 800,
                maxProjectContext: 6000,
                maxConversationHistory: 2000,
                componentsLimit: 8,
                designTokensMode: 'essential',
                historyMessageLimit: 3
            };
        }

    // Legacy GPT-4o and other high-capacity models (back-compat)
        if (model.includes('4o') || model.includes('4-turbo')) {
            return {
                maxSystemPrompt: 1500,
                maxProjectContext: 10000,
                maxConversationHistory: 4000,
                componentsLimit: 15,
                designTokensMode: 'full',
                historyMessageLimit: 5
            };
        }

        // Default strategy for unknown models (conservative)
        return {
            maxSystemPrompt: 600,
            maxProjectContext: 4000,
            maxConversationHistory: 1500,
            componentsLimit: 6,
            designTokensMode: 'essential',
            historyMessageLimit: 2
        };
    }

    /**
     * Estimate token count for text (rough approximation)
     */
    static estimateTokens(text: string): number {
        // Rough estimation: ~4 characters per token on average
        return Math.ceil(text.length / 4);
    }

    /**
     * Truncate text to fit within token limit
     */
    static truncateToTokenLimit(text: string, maxTokens: number): string {
        const estimatedTokens = this.estimateTokens(text);
        
        if (estimatedTokens <= maxTokens) {
            return text;
        }

        // Truncate to approximate character limit
        const maxChars = maxTokens * 4;
        const truncated = text.substring(0, maxChars - 50); // Leave buffer
        
        // Try to break at a reasonable point (end of sentence or word)
        const lastPeriod = truncated.lastIndexOf('.');
        const lastSpace = truncated.lastIndexOf(' ');
        
        if (lastPeriod > truncated.length * 0.8) {
            return truncated.substring(0, lastPeriod + 1);
        } else if (lastSpace > truncated.length * 0.8) {
            return truncated.substring(0, lastSpace);
        }
        
        return truncated + '...';
    }

    /**
     * Log strategy information for debugging
     */
    static logStrategy(model: string, config: ContextConfig): void {
        console.log(`🎨 Context Strategy for ${model}:`, {
            systemPrompt: `${config.maxSystemPrompt} tokens`,
            projectContext: `${config.maxProjectContext} tokens`, 
            conversationHistory: `${config.maxConversationHistory} tokens`,
            components: config.componentsLimit,
            historyMessages: config.historyMessageLimit
        });
    }
}