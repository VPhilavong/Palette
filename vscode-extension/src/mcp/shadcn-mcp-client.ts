/**
 * shadcn/ui MCP Client
 * Specialized client for shadcn/ui MCP server communication
 */

import * as vscode from 'vscode';
import { MCPClientImpl } from './mcp-client';
import { MCPServerConfig } from './types';

export interface ShadcnMCPCapabilities {
    components: {
        install: boolean;
        list: boolean;
        update: boolean;
        remove: boolean;
        search: boolean;
        preview: boolean;
    };
    themes: {
        apply: boolean;
        create: boolean;
        list: boolean;
        customize: boolean;
    };
    registry: {
        custom: boolean;
        multiple: boolean;
        versions: boolean;
    };
}

export interface ShadcnComponent {
    name: string;
    version: string;
    description: string;
    category: string;
    dependencies: string[];
    files: Array<{
        path: string;
        content: string;
        type: 'component' | 'type' | 'style' | 'story';
    }>;
    examples?: Array<{
        name: string;
        code: string;
        preview?: string;
    }>;
    variants?: string[];
    props?: Array<{
        name: string;
        type: string;
        required: boolean;
        description: string;
        default?: string;
    }>;
}

export interface ShadcnThemeConfig {
    name: string;
    type: 'light' | 'dark' | 'auto';
    colors: {
        background: string;
        foreground: string;
        primary: string;
        'primary-foreground': string;
        secondary: string;
        'secondary-foreground': string;
        muted: string;
        'muted-foreground': string;
        accent: string;
        'accent-foreground': string;
        destructive: string;
        'destructive-foreground': string;
        border: string;
        input: string;
        ring: string;
    };
    borderRadius: {
        lg: string;
        md: string;
        sm: string;
    };
}

export class ShadcnMCPClient extends MCPClientImpl {
    private capabilities?: ShadcnMCPCapabilities;

    constructor(config: MCPServerConfig) {
        super(config);
    }

    /**
     * Initialize shadcn/ui specific connection
     */
    async connect(): Promise<void> {
        await super.connect();
        await this.detectCapabilities();
    }

    /**
     * Get available components from registry
     */
    async getAvailableComponents(): Promise<ShadcnComponent[]> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/list', {
                includeMetadata: true,
                includeExamples: true
            });

            return response.components || [];
        } catch (error) {
            console.error('Failed to get available components:', error);
            return [];
        }
    }

    /**
     * Install a component
     */
    async installComponent(
        componentName: string, 
        options: {
            variant?: string;
            overwrite?: boolean;
            dependencies?: boolean;
        } = {}
    ): Promise<{ success: boolean; files: string[]; error?: string }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/install', {
                name: componentName,
                variant: options.variant,
                overwrite: options.overwrite ?? false,
                installDependencies: options.dependencies ?? true
            });

            return {
                success: true,
                files: response.files || []
            };
        } catch (error: any) {
            return {
                success: false,
                files: [],
                error: error.message
            };
        }
    }

    /**
     * Install multiple components
     */
    async installComponents(
        componentNames: string[],
        options: {
            overwrite?: boolean;
            dependencies?: boolean;
            preset?: string;
        } = {}
    ): Promise<{
        success: boolean;
        installed: string[];
        failed: Array<{ name: string; error: string }>;
        dependencies: string[];
    }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/install-batch', {
                components: componentNames,
                overwrite: options.overwrite ?? false,
                installDependencies: options.dependencies ?? true,
                preset: options.preset
            });

            return {
                success: response.failed?.length === 0,
                installed: response.installed || [],
                failed: response.failed || [],
                dependencies: response.dependencies || []
            };
        } catch (error: any) {
            return {
                success: false,
                installed: [],
                failed: componentNames.map(name => ({ name, error: error.message })),
                dependencies: []
            };
        }
    }

    /**
     * Get component details and code
     */
    async getComponentDetails(componentName: string): Promise<ShadcnComponent | null> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/get', {
                name: componentName,
                includeCode: true,
                includeExamples: true,
                includeProps: true
            });

            return response.component || null;
        } catch (error) {
            console.error(`Failed to get component details for ${componentName}:`, error);
            return null;
        }
    }

    /**
     * Generate component code with customizations
     */
    async generateComponentCode(
        componentName: string,
        options: {
            variant?: string;
            customProps?: Record<string, any>;
            wrapperProps?: Record<string, any>;
            includeTypes?: boolean;
        } = {}
    ): Promise<{ code: string; types?: string; examples?: string[] }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/generate', {
                name: componentName,
                variant: options.variant,
                customProps: options.customProps,
                wrapperProps: options.wrapperProps,
                includeTypes: options.includeTypes ?? true
            });

            return {
                code: response.code || '',
                types: response.types,
                examples: response.examples || []
            };
        } catch (error) {
            console.error(`Failed to generate component code for ${componentName}:`, error);
            return { code: '' };
        }
    }

    /**
     * Initialize shadcn/ui in project
     */
    async initializeProject(
        options: {
            style?: 'default' | 'new-york';
            theme?: 'light' | 'dark';
            cssVars?: boolean;
            tailwindConfig?: string;
            components?: string;
            utils?: string;
        } = {}
    ): Promise<{ success: boolean; files: string[]; error?: string }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/init', {
                style: options.style ?? 'default',
                theme: options.theme ?? 'light',
                cssVars: options.cssVars ?? true,
                tailwindConfig: options.tailwindConfig ?? 'tailwind.config.js',
                components: options.components ?? 'src/components',
                utils: options.utils ?? 'src/lib/utils'
            });

            return {
                success: true,
                files: response.files || []
            };
        } catch (error: any) {
            return {
                success: false,
                files: [],
                error: error.message
            };
        }
    }

    /**
     * Apply theme configuration
     */
    async applyTheme(
        theme: ShadcnThemeConfig
    ): Promise<{ success: boolean; files: string[]; error?: string }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/themes/apply', {
                theme: theme
            });

            return {
                success: true,
                files: response.files || []
            };
        } catch (error: any) {
            return {
                success: false,
                files: [],
                error: error.message
            };
        }
    }

    /**
     * Get available themes
     */
    async getAvailableThemes(): Promise<ShadcnThemeConfig[]> {
        try {
            const response = await this.sendShadcnRequest('shadcn/themes/list', {});
            return response.themes || [];
        } catch (error) {
            console.error('Failed to get available themes:', error);
            return [];
        }
    }

    /**
     * Search components by query
     */
    async searchComponents(
        query: string,
        filters: {
            category?: string;
            hasExamples?: boolean;
            hasVariants?: boolean;
        } = {}
    ): Promise<ShadcnComponent[]> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/search', {
                query,
                filters
            });

            return response.components || [];
        } catch (error) {
            console.error(`Failed to search components with query "${query}":`, error);
            return [];
        }
    }

    /**
     * Update component to latest version
     */
    async updateComponent(
        componentName: string,
        options: {
            preserveCustomizations?: boolean;
            backupCurrent?: boolean;
        } = {}
    ): Promise<{ success: boolean; version?: string; changes?: string[]; error?: string }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/update', {
                name: componentName,
                preserveCustomizations: options.preserveCustomizations ?? true,
                backupCurrent: options.backupCurrent ?? true
            });

            return {
                success: true,
                version: response.version,
                changes: response.changes || []
            };
        } catch (error: any) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Remove/uninstall component
     */
    async removeComponent(
        componentName: string,
        options: {
            removeStyles?: boolean;
            removeTypes?: boolean;
            removeDependencies?: boolean;
        } = {}
    ): Promise<{ success: boolean; removed: string[]; error?: string }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/remove', {
                name: componentName,
                removeStyles: options.removeStyles ?? false,
                removeTypes: options.removeTypes ?? false,
                removeDependencies: options.removeDependencies ?? false
            });

            return {
                success: true,
                removed: response.removed || []
            };
        } catch (error: any) {
            return {
                success: false,
                removed: [],
                error: error.message
            };
        }
    }

    /**
     * Analyze current project setup
     */
    async analyzeProject(): Promise<{
        isInitialized: boolean;
        installedComponents: string[];
        missingDependencies: string[];
        configIssues: string[];
        suggestions: string[];
    }> {
        try {
            const response = await this.sendShadcnRequest('shadcn/analyze', {
                deep: true,
                suggestions: true
            });

            return {
                isInitialized: response.initialized ?? false,
                installedComponents: response.components || [],
                missingDependencies: response.missingDependencies || [],
                configIssues: response.issues || [],
                suggestions: response.suggestions || []
            };
        } catch (error) {
            console.error('Failed to analyze project:', error);
            return {
                isInitialized: false,
                installedComponents: [],
                missingDependencies: [],
                configIssues: [],
                suggestions: []
            };
        }
    }

    /**
     * Get component usage examples
     */
    async getComponentExamples(
        componentName: string,
        variant?: string
    ): Promise<Array<{
        name: string;
        description: string;
        code: string;
        preview?: string;
    }>> {
        try {
            const response = await this.sendShadcnRequest('shadcn/components/examples', {
                name: componentName,
                variant
            });

            return response.examples || [];
        } catch (error) {
            console.error(`Failed to get examples for ${componentName}:`, error);
            return [];
        }
    }

    /**
     * Detect server capabilities
     */
    private async detectCapabilities(): Promise<void> {
        try {
            const response = await this.sendShadcnRequest('shadcn/capabilities', {});
            this.capabilities = response.capabilities;
        } catch (error) {
            console.warn('Could not detect shadcn/ui server capabilities:', error);
            // Set default capabilities
            this.capabilities = {
                components: {
                    install: true,
                    list: true,
                    update: false,
                    remove: false,
                    search: false,
                    preview: false
                },
                themes: {
                    apply: false,
                    create: false,
                    list: false,
                    customize: false
                },
                registry: {
                    custom: false,
                    multiple: false,
                    versions: false
                }
            };
        }
    }

    /**
     * Get server capabilities
     */
    getCapabilities(): ShadcnMCPCapabilities | undefined {
        return this.capabilities;
    }

    /**
     * Check if capability is supported
     */
    supportsCapability(category: keyof ShadcnMCPCapabilities, capability: string): boolean {
        return this.capabilities?.[category]?.[capability as keyof typeof this.capabilities[typeof category]] ?? false;
    }

    /**
     * Send shadcn/ui specific request
     */
    private async sendShadcnRequest(method: string, params: any): Promise<any> {
        // Use parent class method for actual communication
        return (this as any).sendRequest(method, params);
    }
}