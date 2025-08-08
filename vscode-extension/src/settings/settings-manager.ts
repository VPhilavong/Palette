/**
 * Settings Manager
 * Handles VS Code extension settings, API keys, and user preferences
 * Following VS Code API best practices: https://code.visualstudio.com/api/references/contribution-points#contributes.configuration
 */

import * as vscode from 'vscode';
import { AIProviderRegistry } from '../ai-providers';

export interface PaletteSettings {
    // AI Provider Settings
    defaultModel: string;
    openaiApiKey: string;
    // Anthropics removed
    enableStreaming: boolean;
    maxTokens: number;
    temperature: number;
    
    // UI/UX Settings
    enableCodeLens: boolean;
    showWelcomeMessage: boolean;
    autoOpenFiles: boolean;
    fileCreationConfirmation: boolean;
    
    // Project Analysis Settings
    analysisDepth: 'shallow' | 'normal' | 'deep';
    cacheAnalysis: boolean;
    analyzeOnStartup: boolean;
    
    // shadcn/ui Settings
    shadcnAutoInstall: boolean;
    preferredUILibrary: 'shadcn-ui' | 'mui' | 'chakra' | 'mantine';
    
    // Code Generation Settings
    generateComments: boolean;
    generateTests: boolean;
    useTypeScript: boolean;
    formatOnGenerate: boolean;
    
    // Advanced Settings
    logLevel: 'error' | 'warn' | 'info' | 'debug';
    telemetryEnabled: boolean;
    experimentalFeatures: boolean;
}

export interface SettingsValidationResult {
    isValid: boolean;
    errors: string[];
    warnings: string[];
}

export class SettingsManager {
    private static instance: SettingsManager;
    private configuration: vscode.WorkspaceConfiguration | null = null;
    private disposables: vscode.Disposable[] = [];

    private constructor() {
        this.initialize();
    }

    static getInstance(): SettingsManager {
        if (!SettingsManager.instance) {
            SettingsManager.instance = new SettingsManager();
        }
        return SettingsManager.instance;
    }

    /**
     * Initialize settings manager and set up configuration watching
     */
    private initialize(): void {
        this.configuration = vscode.workspace.getConfiguration('palette');
        
        // Watch for configuration changes
        const configWatcher = vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('palette')) {
                this.onConfigurationChanged(event);
            }
        });
        
        this.disposables.push(configWatcher);
        console.log('⚙️ Settings manager initialized');
    }

    /**
     * Get all current settings
     */
    getAllSettings(): PaletteSettings {
        const config = this.getConfiguration();
        
        return {
            // AI Provider Settings
            defaultModel: config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07',
            openaiApiKey: config.get<string>('openaiApiKey') || '',
            // No anthropic key in settings anymore
            enableStreaming: config.get<boolean>('enableStreaming') ?? true,
            maxTokens: config.get<number>('maxTokens') || 2000,
            temperature: config.get<number>('temperature') || 0.7,
            
            // UI/UX Settings
            enableCodeLens: config.get<boolean>('enableCodeLens') ?? true,
            showWelcomeMessage: config.get<boolean>('showWelcomeMessage') ?? true,
            autoOpenFiles: config.get<boolean>('autoOpenFiles') ?? true,
            fileCreationConfirmation: config.get<boolean>('fileCreationConfirmation') ?? true,
            
            // Project Analysis Settings
            analysisDepth: config.get<'shallow' | 'normal' | 'deep'>('analysisDepth') || 'normal',
            cacheAnalysis: config.get<boolean>('cacheAnalysis') ?? true,
            analyzeOnStartup: config.get<boolean>('analyzeOnStartup') ?? false,
            
            // shadcn/ui Settings
            shadcnAutoInstall: config.get<boolean>('shadcnAutoInstall') ?? false,
            preferredUILibrary: config.get<'shadcn-ui' | 'mui' | 'chakra' | 'mantine'>('preferredUILibrary') || 'shadcn-ui',
            
            // Code Generation Settings
            generateComments: config.get<boolean>('generateComments') ?? true,
            generateTests: config.get<boolean>('generateTests') ?? false,
            useTypeScript: config.get<boolean>('useTypeScript') ?? true,
            formatOnGenerate: config.get<boolean>('formatOnGenerate') ?? true,
            
            // Advanced Settings
            logLevel: config.get<'error' | 'warn' | 'info' | 'debug'>('logLevel') || 'info',
            telemetryEnabled: config.get<boolean>('telemetryEnabled') ?? true,
            experimentalFeatures: config.get<boolean>('experimentalFeatures') ?? false
        };
    }

    /**
     * Get a specific setting value
     */
    getSetting<T>(key: keyof PaletteSettings): T | undefined {
        return this.getConfiguration().get<T>(key);
    }

    /**
     * Update a specific setting
     */
    async updateSetting<T>(
        key: keyof PaletteSettings, 
        value: T, 
        target: vscode.ConfigurationTarget = vscode.ConfigurationTarget.Global
    ): Promise<void> {
        try {
            await this.getConfiguration().update(key, value, target);
            console.log(`⚙️ Setting updated: ${key} = ${value}`);
        } catch (error) {
            console.error(`Failed to update setting ${key}:`, error);
            vscode.window.showErrorMessage(`Failed to update setting: ${error}`);
        }
    }

    /**
     * Validate current settings
     */
    validateSettings(): SettingsValidationResult {
        const settings = this.getAllSettings();
        const errors: string[] = [];
        const warnings: string[] = [];

        // Validate API keys
        if (!settings.openaiApiKey) {
            errors.push('OpenAI API key must be configured');
        }

        if (settings.openaiApiKey && !this.isValidApiKeyFormat(settings.openaiApiKey, 'openai')) {
            errors.push('Invalid OpenAI API key format');
        }

    // Anthropic validation removed

        // Validate model selection
    const availableModels = AIProviderRegistry.getAvailableModels();
        if (!availableModels.includes(settings.defaultModel)) {
            warnings.push(`Selected model "${settings.defaultModel}" may not be available`);
        }

        // Validate temperature range
        if (settings.temperature < 0 || settings.temperature > 2) {
            errors.push('Temperature must be between 0 and 2');
        }

        // Validate max tokens
        if (settings.maxTokens < 100 || settings.maxTokens > 32000) {
            warnings.push('Max tokens should be between 100 and 32000');
        }

        return {
            isValid: errors.length === 0,
            errors,
            warnings
        };
    }

    /**
     * Show settings configuration UI
     */
    async showSettingsUI(): Promise<void> {
        const choice = await vscode.window.showQuickPick([
            {
                label: '⚙️ Open Settings UI',
                description: 'Open VS Code settings interface',
                action: 'ui'
            },
            {
                label: '🔑 Configure API Keys',
                description: 'Set up AI provider API keys',
                action: 'apikeys'
            },
            {
                label: '🎨 Model Selection',
                description: 'Choose default AI model',
                action: 'model'
            },
            {
                label: '🔍 Analysis Settings',
                description: 'Configure project analysis options',
                action: 'analysis'
            },
            {
                label: '✅ Validate Settings',
                description: 'Check current settings for issues',
                action: 'validate'
            }
        ], {
            placeHolder: 'Select settings action',
            title: 'Palette Settings'
        });

        if (!choice) return;

        switch (choice.action) {
            case 'ui':
                await vscode.commands.executeCommand('workbench.action.openSettings', '@ext:palette');
                break;
            case 'apikeys':
                await this.configureApiKeys();
                break;
            case 'model':
                await this.selectModel();
                break;
            case 'analysis':
                await this.configureAnalysisSettings();
                break;
            case 'validate':
                await this.showValidationResults();
                break;
        }
    }

    /**
     * Configure API keys through input dialogs
     */
    private async configureApiKeys(): Promise<void> {
        const settings = this.getAllSettings();

        const choice = await vscode.window.showQuickPick([
            {
                label: '🤖 OpenAI API Key',
                description: settings.openaiApiKey ? 'Currently configured' : 'Not configured',
                provider: 'openai'
            }
        ], {
            placeHolder: 'Select provider to configure',
            title: 'API Key Configuration'
        });

        if (!choice) return;

    const currentKey = settings.openaiApiKey;
    const placeholder = `Enter your OpenAI API key`;
        
        const newKey = await vscode.window.showInputBox({
            prompt: `OpenAI API Key`,
            placeHolder: placeholder,
            value: currentKey ? '••••••••••••••••' : '',
            password: true,
            validateInput: (value) => {
                if (!value || value === '••••••••••••••••') return null;
                if (!this.isValidApiKeyFormat(value, 'openai')) {
                    return `Invalid ${choice.provider} API key format`;
                }
                return null;
            }
        });

        if (newKey && newKey !== '••••••••••••••••') {
            await this.updateSetting('openaiApiKey', newKey, vscode.ConfigurationTarget.Global);
            vscode.window.showInformationMessage(`OpenAI API key updated successfully`);
        }
    }

    /**
     * Model selection interface
     */
    private async selectModel(): Promise<void> {
        const settings = this.getAllSettings();
    const availableModels = AIProviderRegistry.getAvailableModels();
        
        const modelChoices = availableModels.map(model => ({
            label: model,
            description: AIProviderRegistry.getModelDescription(model),
            picked: model === settings.defaultModel
        }));

        const choice = await vscode.window.showQuickPick(modelChoices, {
            placeHolder: 'Select default AI model',
            title: 'Model Selection'
        });

        if (choice && choice.label !== settings.defaultModel) {
            await this.updateSetting('defaultModel', choice.label);
            vscode.window.showInformationMessage(`Default model changed to ${choice.label}`);
        }
    }

    /**
     * Analysis settings configuration
     */
    private async configureAnalysisSettings(): Promise<void> {
        const settings = this.getAllSettings();

        const choices = [
            {
                label: `Analysis Depth: ${settings.analysisDepth}`,
                description: 'How deep to analyze project structure',
                setting: 'analysisDepth'
            },
            {
                label: `Cache Analysis: ${settings.cacheAnalysis ? 'Enabled' : 'Disabled'}`,
                description: 'Cache analysis results for better performance',
                setting: 'cacheAnalysis'
            },
            {
                label: `Analyze on Startup: ${settings.analyzeOnStartup ? 'Enabled' : 'Disabled'}`,
                description: 'Automatically analyze project when opening',
                setting: 'analyzeOnStartup'
            }
        ];

        const choice = await vscode.window.showQuickPick(choices, {
            placeHolder: 'Select analysis setting to configure',
            title: 'Analysis Settings'
        });

        if (!choice) return;

        switch (choice.setting) {
            case 'analysisDepth':
                await this.selectAnalysisDepth();
                break;
            case 'cacheAnalysis':
                await this.updateSetting('cacheAnalysis', !settings.cacheAnalysis);
                break;
            case 'analyzeOnStartup':
                await this.updateSetting('analyzeOnStartup', !settings.analyzeOnStartup);
                break;
        }
    }

    /**
     * Analysis depth selection
     */
    private async selectAnalysisDepth(): Promise<void> {
        const choices = [
            {
                label: 'Shallow',
                description: 'Basic file structure and imports only',
                value: 'shallow' as const
            },
            {
                label: 'Normal',
                description: 'Standard analysis with component relationships',
                value: 'normal' as const
            },
            {
                label: 'Deep',
                description: 'Comprehensive analysis including patterns and dependencies',
                value: 'deep' as const
            }
        ];

        const choice = await vscode.window.showQuickPick(choices, {
            placeHolder: 'Select analysis depth',
            title: 'Analysis Depth Configuration'
        });

        if (choice) {
            await this.updateSetting('analysisDepth', choice.value);
            vscode.window.showInformationMessage(`Analysis depth set to ${choice.label}`);
        }
    }

    /**
     * Show validation results
     */
    private async showValidationResults(): Promise<void> {
        const validation = this.validateSettings();
        
        if (validation.isValid) {
            vscode.window.showInformationMessage('✅ All settings are valid!');
        } else {
            const items = [
                ...validation.errors.map(error => `❌ ${error}`),
                ...validation.warnings.map(warning => `⚠️ ${warning}`)
            ];
            
            const choice = await vscode.window.showQuickPick(items, {
                placeHolder: 'Settings validation results',
                title: 'Settings Issues Found'
            });
            
            // Could offer quick fixes based on the selected issue
            if (choice?.includes('API key')) {
                await this.configureApiKeys();
            }
        }
    }

    /**
     * Handle configuration changes
     */
    private onConfigurationChanged(event: vscode.ConfigurationChangeEvent): void {
        console.log('⚙️ Configuration changed');
        this.configuration = vscode.workspace.getConfiguration('palette');
        
        // Validate new configuration
        const validation = this.validateSettings();
        if (!validation.isValid) {
            console.warn('⚠️ Invalid settings detected:', validation.errors);
        }
        
        // Notify other parts of the extension about settings changes
        this.notifySettingsChanged(event);
    }

    /**
     * Notify other components about settings changes
     */
    private notifySettingsChanged(event: vscode.ConfigurationChangeEvent): void {
        // Could emit events or call callbacks here
        // For now, just log the changes
        const changedKeys = [];
        
        if (event.affectsConfiguration('palette.defaultModel')) {
            changedKeys.push('defaultModel');
        }
        if (event.affectsConfiguration('palette.openaiApiKey')) {
            changedKeys.push('openaiApiKey');
        }
    // No anthropic API key in settings
        
        if (changedKeys.length > 0) {
            console.log('⚙️ Settings changed:', changedKeys.join(', '));
        }
    }

    /**
     * Export settings for backup/sharing
     */
    async exportSettings(): Promise<void> {
        const settings = this.getAllSettings();
        
        // Remove sensitive data
        const exportData = {
            ...settings,
            openaiApiKey: settings.openaiApiKey ? '[CONFIGURED]' : '',
            // remove anthropic key
        };
        
        const json = JSON.stringify(exportData, null, 2);
        
        const choice = await vscode.window.showQuickPick([
            'Copy to Clipboard',
            'Save to File'
        ], {
            placeHolder: 'How would you like to export settings?'
        });
        
        if (choice === 'Copy to Clipboard') {
            await vscode.env.clipboard.writeText(json);
            vscode.window.showInformationMessage('Settings copied to clipboard');
        } else if (choice === 'Save to File') {
            const uri = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.file('palette-settings.json'),
                filters: {
                    'JSON files': ['json']
                }
            });
            
            if (uri) {
                await vscode.workspace.fs.writeFile(uri, Buffer.from(json, 'utf8'));
                vscode.window.showInformationMessage(`Settings saved to ${uri.fsPath}`);
            }
        }
    }

    /**
     * Reset settings to defaults
     */
    async resetSettings(): Promise<void> {
        const choice = await vscode.window.showWarningMessage(
            'This will reset all Palette settings to their default values. This action cannot be undone.',
            { modal: true },
            'Reset Settings',
            'Cancel'
        );
        
        if (choice === 'Reset Settings') {
            const config = this.getConfiguration();
            const keys = Object.keys(this.getAllSettings()) as (keyof PaletteSettings)[];
            
            for (const key of keys) {
                await config.update(key, undefined, vscode.ConfigurationTarget.Global);
            }
            
            vscode.window.showInformationMessage('Settings have been reset to defaults');
        }
    }

    // Helper methods
    private getConfiguration(): vscode.WorkspaceConfiguration {
        if (!this.configuration) {
            this.configuration = vscode.workspace.getConfiguration('palette');
        }
        return this.configuration;
    }

    private isValidApiKeyFormat(apiKey: string, provider: 'openai'): boolean {
        if (provider === 'openai') {
            return /^sk-[a-zA-Z0-9]{20,}/.test(apiKey);
        }
        return false;
    }

    // Removed duplicated model list/description; centralized in AIProviderRegistry

    /**
     * Dispose of resources
     */
    dispose(): void {
        this.disposables.forEach(d => d.dispose());
        this.disposables = [];
    }
}

// Factory function for easy access
export function getSettingsManager(): SettingsManager {
    return SettingsManager.getInstance();
}