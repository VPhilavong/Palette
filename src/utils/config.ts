import * as vscode from 'vscode';

/**
 * Configuration management utility
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
    static getApiProvider(): 'openai' | 'gemini' | 'claude' {
        return Config.get('apiProvider', 'gemini');
    }

    /**
     * Get API key for current provider
     */
    static getApiKey(): string {
        const provider = Config.getApiProvider();
        return Config.get(`${provider}ApiKey`, '');
    }

    /**
     * Get model for current provider
     */
    static getModel(): string {
        const provider = Config.getApiProvider();
        const defaultModels = {
            'openai': 'gpt-4',
            'gemini': 'gemini-2.0-flash-exp',
            'claude': 'claude-3-sonnet-20240229'
        };
        return Config.get(`${provider}Model`, defaultModels[provider]);
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