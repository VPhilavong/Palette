/**
 * Generation Orchestrator
 * Main interface for AI SDK 5 generation that orchestrates the entire process
 * Handles routing, context building, and result processing
 */

import * as vscode from 'vscode';
import { AICapabilityRouter, GenerationRequest, GenerationResult, ProjectContext } from './capability-router';

export interface OrchestrationOptions {
    stream?: boolean;
    maxTokens?: number;
    temperature?: number;
    includeContext?: boolean;
    validateOutput?: boolean;
}

/**
 * Main orchestrator class that coordinates AI generation
 */
export class GenerationOrchestrator {
    private static instance: GenerationOrchestrator | null = null;
    private contextCache: Map<string, ProjectContext> = new Map();

    private constructor() {}

    static getInstance(): GenerationOrchestrator {
        if (!this.instance) {
            this.instance = new GenerationOrchestrator();
        }
        return this.instance;
    }

    /**
     * Main generation method - orchestrates the entire process
     */
    async generate(
        message: string, 
        options: OrchestrationOptions = {}
    ): Promise<GenerationResult> {
        try {
            console.log(`🎨 GenerationOrchestrator: Starting generation`);

            // Step 1: Get current model from VS Code configuration
            const model = this.getCurrentModel();
            
            // Step 2: Build project context if requested
            const context = options.includeContext !== false 
                ? await this.buildProjectContext()
                : undefined;

            // Step 3: Create generation request
            const request: GenerationRequest = {
                message,
                model,
                context,
                options: {
                    maxTokens: options.maxTokens,
                    temperature: options.temperature,
                    stream: options.stream
                }
            };

            // Step 4: Route to appropriate strategy
            const result = await AICapabilityRouter.route(request);

            // Step 5: Post-process result if needed
            if (options.validateOutput && result.success) {
                await this.validateResult(result);
            }

            // Step 6: Log generation metrics
            this.logGenerationMetrics(result);

            return result;

        } catch (error: any) {
            console.error(`🎨 GenerationOrchestrator error:`, error);
            return {
                success: false,
                content: '',
                error: `Generation orchestration failed: ${error.message}`
            };
        }
    }

    /**
     * Generate with streaming support
     */
    async generateStreaming(
        message: string,
        onChunk: (chunk: string) => void,
        options: OrchestrationOptions = {}
    ): Promise<GenerationResult> {
        const model = this.getCurrentModel();
        const capabilities = AICapabilityRouter.getModelCapabilities(model);
        
        if (!capabilities.streaming) {
            console.warn(`🎨 Model ${model} doesn't support streaming, falling back to standard generation`);
            return this.generate(message, { ...options, stream: false });
        }

        // For streaming, we need to handle the async iteration differently
        // This is a simplified version - in practice you'd integrate with the UI streaming
        return this.generate(message, { ...options, stream: true });
    }

    /**
     * Generate structured data (Enhanced tier only)
     */
    async generateStructured(
        message: string,
        schema?: any,
        options: OrchestrationOptions = {}
    ): Promise<GenerationResult> {
        const model = this.getCurrentModel();
        const capabilities = AICapabilityRouter.getModelCapabilities(model);
        
        if (!capabilities.structuredData) {
            console.warn(`🎨 Model ${model} doesn't support structured data, using text generation`);
            return this.generate(message, options);
        }

        // Enhanced models can use structured generation
        return this.generate(message, options);
    }

    /**
     * Build project context from current workspace
     */
    private async buildProjectContext(): Promise<ProjectContext> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return {};
        }

        const workspacePath = workspaceFolder.uri.fsPath;
        
        // Check cache first
        const cacheKey = `${workspacePath}-${Date.now() - (Date.now() % 60000)}`; // Cache for 1 minute
        if (this.contextCache.has(cacheKey)) {
            return this.contextCache.get(cacheKey)!;
        }

        try {
            console.log(`🎨 Building project context for: ${workspacePath}`);

            const context: ProjectContext = {
                workspacePath,
                framework: await this.detectFramework(workspacePath),
                components: await this.scanComponents(workspacePath),
                designTokens: await this.extractDesignTokens(workspacePath),
                tsConfig: await this.loadTsConfig(workspacePath)
            };

            // Cache the context
            this.contextCache.set(cacheKey, context);
            
            // Clean old cache entries
            if (this.contextCache.size > 10) {
                const firstKey = this.contextCache.keys().next().value;
                if (firstKey) {
                    this.contextCache.delete(firstKey);
                }
            }

            return context;

        } catch (error: any) {
            console.warn(`🎨 Failed to build project context:`, error);
            return { workspacePath };
        }
    }

    /**
     * Detect framework from package.json
     */
    private async detectFramework(workspacePath: string): Promise<string> {
        try {
            const packageJsonUri = vscode.Uri.file(`${workspacePath}/package.json`);
            const packageJsonContent = await vscode.workspace.fs.readFile(packageJsonUri);
            const packageJson = JSON.parse(packageJsonContent.toString());

            const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
            
            if (dependencies.next) return 'Next.js';
            if (dependencies.vite) return 'Vite + React';
            if (dependencies.react) return 'React';
            if (dependencies.vue) return 'Vue.js';
            if (dependencies.svelte) return 'Svelte';

            return 'Unknown';
        } catch {
            return 'Unknown';
        }
    }

    /**
     * Scan for existing components
     */
    private async scanComponents(workspacePath: string): Promise<string[]> {
        try {
            const componentsPattern = new vscode.RelativePattern(workspacePath, '**/components/**/*.{tsx,jsx,ts,js}');
            const componentFiles = await vscode.workspace.findFiles(componentsPattern, '**/node_modules/**', 20);
            
            return componentFiles.map(file => {
                const relativePath = vscode.workspace.asRelativePath(file);
                const fileName = relativePath.split('/').pop()?.replace(/\.(tsx?|jsx?)$/, '') || '';
                return fileName;
            });
        } catch {
            return [];
        }
    }

    /**
     * Extract design tokens from common locations
     */
    private async extractDesignTokens(workspacePath: string): Promise<Record<string, any>> {
        try {
            // Try to read Tailwind config
            const tailwindConfigUri = vscode.Uri.file(`${workspacePath}/tailwind.config.js`);
            
            try {
                await vscode.workspace.fs.stat(tailwindConfigUri);
                // If file exists, return basic info (parsing JS config is complex)
                return { hasTailwind: true, configType: 'tailwind' };
            } catch {
                // No Tailwind config found
            }

            // Try to read CSS custom properties
            const cssPattern = new vscode.RelativePattern(workspacePath, '**/*.css');
            const cssFiles = await vscode.workspace.findFiles(cssPattern, '**/node_modules/**', 5);
            
            if (cssFiles.length > 0) {
                return { hasCustomCSS: true, cssFiles: cssFiles.length };
            }

            return {};
        } catch {
            return {};
        }
    }

    /**
     * Load TypeScript configuration
     */
    private async loadTsConfig(workspacePath: string): Promise<any> {
        try {
            const tsConfigUri = vscode.Uri.file(`${workspacePath}/tsconfig.json`);
            const tsConfigContent = await vscode.workspace.fs.readFile(tsConfigUri);
            return JSON.parse(tsConfigContent.toString());
        } catch {
            return null;
        }
    }

    /**
     * Get current model from VS Code configuration
     */
    private getCurrentModel(): string {
        const config = vscode.workspace.getConfiguration('palette');
        return config.get<string>('defaultModel') || 'gpt-5-mini-2025-08-07';
    }

    /**
     * Validate generation result
     */
    private async validateResult(result: GenerationResult): Promise<void> {
        if (!result.success || !result.metadata?.files) {
            return;
        }

        // Basic validation - check if generated files have valid syntax
        for (const file of result.metadata.files) {
            if (file.type === 'component' && !file.content.includes('export')) {
                console.warn(`🎨 Validation warning: ${file.path} may be missing export statement`);
            }
        }
    }

    /**
     * Log generation metrics for monitoring
     */
    private logGenerationMetrics(result: GenerationResult): void {
        const metrics = {
            success: result.success,
            model: result.metadata?.model,
            tier: result.metadata?.tier,
            tokensUsed: result.metadata?.tokensUsed,
            filesGenerated: result.metadata?.files?.length || 0,
            strategy: result.metadata?.strategy,
            timestamp: new Date().toISOString()
        };

        console.log(`🎨 Generation metrics:`, metrics);

        // In a production environment, you might send this to telemetry
        // this.sendTelemetry(metrics);
    }

    /**
     * Clear context cache (useful for testing or manual refresh)
     */
    clearContextCache(): void {
        this.contextCache.clear();
        console.log(`🎨 Context cache cleared`);
    }

    /**
     * Get cached context for debugging
     */
    getCachedContext(workspacePath?: string): ProjectContext | undefined {
        if (!workspacePath) {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) return undefined;
            workspacePath = workspaceFolder.uri.fsPath;
        }

        // Find the most recent cache entry for this workspace
        for (const [key, context] of this.contextCache.entries()) {
            if (key.startsWith(workspacePath)) {
                return context;
            }
        }

        return undefined;
    }

    /**
     * Health check for orchestrator
     */
    async healthCheck(): Promise<{ healthy: boolean; issues: string[] }> {
        const issues: string[] = [];

        // Check API key
        const config = vscode.workspace.getConfiguration('palette');
        const apiKey = config.get<string>('openaiApiKey');
        if (!apiKey) {
            issues.push('OpenAI API key not configured');
        }

        // Check workspace
        if (!vscode.workspace.workspaceFolders?.length) {
            issues.push('No workspace folder open');
        }

        // Check model configuration
        const currentModel = this.getCurrentModel();
        const capabilities = AICapabilityRouter.getModelCapabilities(currentModel);
        if (capabilities.tier === 'core' && capabilities.maxTokens < 1000) {
            issues.push(`Current model (${currentModel}) has very limited token capacity`);
        }

        return {
            healthy: issues.length === 0,
            issues
        };
    }
}