/**
 * TypeScript Intelligence Engine
 * Main orchestrator for project analysis and intelligent suggestions
 */

import * as vscode from 'vscode';
import { ProjectAnalyzer } from './project-analyzer';
import { CodePatternRecognizer } from './code-pattern-recognizer';
import { ComponentSuggestionEngine } from './component-suggestion-engine';
import { DesignSystemAnalyzer } from './design-system-analyzer';
import { 
    IntelligenceContext, 
    AnalysisResult, 
    IntelligenceOptions,
    CacheEntry
} from './types';

export class TypeScriptIntelligenceEngine {
    private static instance: TypeScriptIntelligenceEngine | null = null;
    
    private projectAnalyzer: ProjectAnalyzer;
    private patternRecognizer: CodePatternRecognizer;
    private suggestionEngine: ComponentSuggestionEngine;
    private designSystemAnalyzer: DesignSystemAnalyzer;
    
    private contextCache: Map<string, CacheEntry<IntelligenceContext>> = new Map();
    private analysisCache: Map<string, CacheEntry<AnalysisResult>> = new Map();
    
    private constructor() {
        this.projectAnalyzer = new ProjectAnalyzer();
        this.patternRecognizer = new CodePatternRecognizer();
        this.suggestionEngine = new ComponentSuggestionEngine();
        this.designSystemAnalyzer = new DesignSystemAnalyzer();
        
        console.log('🧠 TypeScript Intelligence Engine initialized');
    }

    static getInstance(): TypeScriptIntelligenceEngine {
        if (!this.instance) {
            this.instance = new TypeScriptIntelligenceEngine();
        }
        return this.instance;
    }

    /**
     * Main analysis method - orchestrates all intelligence components
     */
    async analyze(
        workspacePath?: string, 
        options: IntelligenceOptions = {}
    ): Promise<AnalysisResult> {
        try {
            console.log('🧠 Starting intelligence analysis...');
            const startTime = Date.now();

            // Determine workspace path
            const targetPath = workspacePath || this.getCurrentWorkspacePath();
            if (!targetPath) {
                throw new Error('No workspace folder available for analysis');
            }

            // Check cache first
            const cacheKey = this.generateCacheKey(targetPath, options);
            const cachedResult = this.getFromAnalysisCache(cacheKey, options.maxCacheAge);
            if (cachedResult) {
                console.log(`🧠 Returning cached analysis result`);
                return cachedResult;
            }

            // Build or retrieve intelligence context
            const context = await this.buildIntelligenceContext(targetPath, options);

            // Generate suggestions and insights
            const suggestions = options.includeSuggestions !== false 
                ? await this.suggestionEngine.generateSuggestions(context, options)
                : [];

            const patterns = options.includePatterns !== false
                ? await this.patternRecognizer.recognizePatterns(context, options)
                : [];

            const insights = options.includeInsights !== false
                ? await this.generateProjectInsights(context, patterns)
                : [];

            // Calculate overall confidence based on data quality
            const confidence = this.calculateAnalysisConfidence(context, patterns, suggestions);

            const result: AnalysisResult = {
                context,
                suggestions,
                patterns,
                insights,
                confidence,
                cached: false,
                timestamp: new Date().toISOString()
            };

            // Cache the result
            this.cacheAnalysisResult(cacheKey, result);

            const duration = Date.now() - startTime;
            console.log(`🧠 Analysis completed in ${duration}ms`);
            console.log(`🧠 Found ${patterns.length} patterns, ${suggestions.length} suggestions, ${insights.length} insights`);

            return result;

        } catch (error: any) {
            console.error('🧠 Intelligence analysis failed:', error);
            
            // Return minimal result on error
            return {
                context: await this.getMinimalContext(),
                suggestions: [],
                patterns: [],
                insights: [],
                confidence: 0,
                cached: false,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Build comprehensive intelligence context
     */
    private async buildIntelligenceContext(
        workspacePath: string, 
        options: IntelligenceOptions
    ): Promise<IntelligenceContext> {
        // Check context cache first
        const contextCacheKey = `context-${workspacePath}`;
        const cachedContext = this.getFromContextCache(contextCacheKey, options.maxCacheAge);
        if (cachedContext) {
            return cachedContext;
        }

        console.log('🧠 Building intelligence context...');

        // Run analysis components in parallel for performance
        const [workspace, project, codebase, designSystem] = await Promise.all([
            this.projectAnalyzer.analyzeWorkspace(workspacePath),
            this.projectAnalyzer.analyzeProject(workspacePath),
            this.projectAnalyzer.analyzeCodebase(workspacePath, options),
            this.designSystemAnalyzer.analyze(workspacePath)
        ]);

        const context: IntelligenceContext = {
            workspace,
            project,
            codebase,
            designSystem
        };

        // Cache the context
        this.cacheIntelligenceContext(contextCacheKey, context);

        return context;
    }

    /**
     * Generate project-wide insights based on context and patterns
     */
    private async generateProjectInsights(
        context: IntelligenceContext,
        patterns: any[]
    ): Promise<any[]> {
        const insights: any[] = [];

        // Architecture insights
        if (context.project.framework && context.codebase.components.length > 0) {
            insights.push({
                category: 'architecture',
                title: 'Project Architecture Analysis',
                description: `Detected ${context.project.framework} project with ${context.codebase.components.length} components`,
                impact: 'medium',
                actionable: true,
                recommendation: `Consider ${context.project.framework} best practices for component organization`
            });
        }

        // Design system insights
        if (context.designSystem.library) {
            insights.push({
                category: 'design-system',
                title: `${context.designSystem.library} Integration`,
                description: `Using ${context.designSystem.library} with ${context.designSystem.components.length} available components`,
                impact: 'high',
                actionable: true,
                recommendation: `Leverage existing ${context.designSystem.library} components for consistency`
            });
        }

        // Pattern insights
        const complexPatterns = patterns.filter(p => p.confidence > 0.8);
        if (complexPatterns.length > 0) {
            insights.push({
                category: 'patterns',
                title: 'Strong Code Patterns Detected',
                description: `Found ${complexPatterns.length} consistent patterns in your codebase`,
                impact: 'high',
                actionable: true,
                recommendation: 'These patterns can be leveraged for generating similar components'
            });
        }

        return insights;
    }

    /**
     * Calculate confidence score based on available data
     */
    private calculateAnalysisConfidence(
        context: IntelligenceContext,
        patterns: any[],
        suggestions: any[]
    ): number {
        let score = 0;
        let maxScore = 0;

        // Context completeness (40% of score)
        maxScore += 40;
        if (context.project.framework !== 'Unknown') score += 10;
        if (context.codebase.components.length > 0) score += 10;
        if (context.designSystem.library) score += 10;
        if (context.project.dependencies && Object.keys(context.project.dependencies).length > 0) score += 10;

        // Pattern recognition (30% of score)
        maxScore += 30;
        if (patterns.length > 0) {
            const avgConfidence = patterns.reduce((acc, p) => acc + p.confidence, 0) / patterns.length;
            score += Math.round(avgConfidence * 30);
        }

        // Suggestion quality (30% of score)
        maxScore += 30;
        if (suggestions.length > 0) {
            const avgConfidence = suggestions.reduce((acc, s) => acc + s.confidence, 0) / suggestions.length;
            score += Math.round(avgConfidence * 30);
        }

        return Math.round((score / maxScore) * 100);
    }

    /**
     * Get minimal context for error cases
     */
    private async getMinimalContext(): Promise<IntelligenceContext> {
        const workspacePath = this.getCurrentWorkspacePath() || '';
        
        return {
            workspace: {
                path: workspacePath,
                folders: []
            },
            project: {
                framework: 'Unknown',
                buildTool: 'Unknown',
                packageManager: 'npm',
                dependencies: {},
                devDependencies: {},
                scripts: {},
                structure: {
                    srcDir: 'src'
                }
            },
            codebase: {
                components: [],
                hooks: [],
                utilities: [],
                types: [],
                patterns: [],
                conventions: {
                    naming: {
                        components: 'PascalCase',
                        files: 'camelCase',
                        variables: 'camelCase'
                    },
                    structure: {
                        fileOrganization: 'mixed',
                        importStyle: 'mixed',
                        exportStyle: 'mixed'
                    },
                    styling: {
                        approach: 'mixed',
                        conventions: []
                    }
                }
            },
            designSystem: {
                tokens: {
                    colors: {},
                    spacing: {},
                    typography: {},
                    breakpoints: {},
                    shadows: {},
                    borderRadius: {}
                },
                components: [],
                patterns: []
            }
        };
    }

    /**
     * Cache management methods
     */
    private generateCacheKey(path: string, options: IntelligenceOptions): string {
        const optionsHash = JSON.stringify(options);
        return `${path}-${Buffer.from(optionsHash).toString('base64').substring(0, 10)}`;
    }

    private getFromContextCache(key: string, maxAge?: number): IntelligenceContext | null {
        const entry = this.contextCache.get(key);
        if (!entry) return null;

        const age = Date.now() - entry.timestamp;
        const maxCacheAge = maxAge || 5 * 60 * 1000; // 5 minutes default

        if (age > maxCacheAge) {
            this.contextCache.delete(key);
            return null;
        }

        return entry.data;
    }

    private getFromAnalysisCache(key: string, maxAge?: number): AnalysisResult | null {
        const entry = this.analysisCache.get(key);
        if (!entry) return null;

        const age = Date.now() - entry.timestamp;
        const maxCacheAge = maxAge || 2 * 60 * 1000; // 2 minutes default

        if (age > maxCacheAge) {
            this.analysisCache.delete(key);
            return null;
        }

        return { ...entry.data, cached: true };
    }

    private cacheIntelligenceContext(key: string, context: IntelligenceContext): void {
        this.contextCache.set(key, {
            data: context,
            timestamp: Date.now(),
            version: '1.0.0',
            dependencies: []
        });

        // Clean old entries
        if (this.contextCache.size > 10) {
            const firstKey = this.contextCache.keys().next().value;
            if (firstKey) {
                this.contextCache.delete(firstKey);
            }
        }
    }

    private cacheAnalysisResult(key: string, result: AnalysisResult): void {
        this.analysisCache.set(key, {
            data: result,
            timestamp: Date.now(),
            version: '1.0.0',
            dependencies: []
        });

        // Clean old entries
        if (this.analysisCache.size > 20) {
            const firstKey = this.analysisCache.keys().next().value;
            if (firstKey) {
                this.analysisCache.delete(firstKey);
            }
        }
    }

    private getCurrentWorkspacePath(): string | undefined {
        return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    /**
     * Clear all caches (useful for testing or forced refresh)
     */
    clearCaches(): void {
        this.contextCache.clear();
        this.analysisCache.clear();
        console.log('🧠 Intelligence caches cleared');
    }

    /**
     * Get cache statistics for debugging
     */
    getCacheStats(): { context: number; analysis: number } {
        return {
            context: this.contextCache.size,
            analysis: this.analysisCache.size
        };
    }

    /**
     * Health check for the intelligence engine
     */
    async healthCheck(): Promise<{ healthy: boolean; issues: string[] }> {
        const issues: string[] = [];

        // Check workspace availability
        if (!vscode.workspace.workspaceFolders?.length) {
            issues.push('No workspace folder available');
        }

        // Check if we can analyze a project
        try {
            const workspacePath = this.getCurrentWorkspacePath();
            if (workspacePath) {
                await this.projectAnalyzer.analyzeWorkspace(workspacePath);
            }
        } catch (error) {
            issues.push(`Project analysis failed: ${error}`);
        }

        return {
            healthy: issues.length === 0,
            issues
        };
    }
}