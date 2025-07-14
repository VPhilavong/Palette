import * as vscode from 'vscode';

/**
 * Configuration Manager
 * 
 * This file manages VS Code extension configuration settings:
 * - Provides type-safe access to extension configuration
 * - Handles OpenAI API key and model settings
 * - Manages indexing and context configuration
 * - Validates configuration values and provides defaults
 * - Centralizes all configuration access across the extension
 * 
 * Single source of truth for extension settings.
 */
export class Config {
    private static readonly EXTENSION_NAME = 'ui-copilot';

    /**
     * Get configuration value
     */
    static get<T>(key: string, defaultValue?: T): T {
        const config = vscode.workspace.getConfiguration(Config.EXTENSION_NAME);
        return config.get(key, defaultValue as T);
    }

    /**
     * Set configuration value
     */
    static async set(key: string, value: any, target?: vscode.ConfigurationTarget): Promise<void> {
        const config = vscode.workspace.getConfiguration(Config.EXTENSION_NAME);
        await config.update(key, value, target);
    }

    /**
     * Get API provider setting
     */
    static getApiProvider(): 'openai' {
        return Config.get('apiProvider', 'openai');
    }

    /**
     * Get API key for current provider
     */
    static getApiKey(): string {
        return Config.get('openaiApiKey', '');
    }

    /**
     * Get model for current provider
     */
    static getModel(): string {
        return Config.get('openaiModel', 'gpt-4');
    }

    /**
     * Check if indexing is enabled
     */
    static isIndexingEnabled(): boolean {
        return Config.get('indexing.enabled', true);
    }

    /**
     * Get indexing configuration
     */
    static getIndexingConfig() {
        return {
            enabled: Config.get('indexing.enabled', true),
            maxFileSize: Config.get('indexing.maxFileSize', 102400),
            excludePatterns: Config.get('indexing.excludePatterns', [
                'node_modules', '.git', 'dist', 'build', '.next'
            ])
        };
    }

    /**
     * Get context configuration
     */
    static getContextConfig() {
        return {
            maxTokens: Config.get('context.maxTokens', 12000),
            maxFiles: Config.get('context.maxFiles', 20)
        };
    }
}