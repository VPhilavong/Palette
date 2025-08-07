/**
 * ComplexityAnalyzer - Intelligent request classification for routing
 * Determines whether requests should go to AI SDK (simple) or Python backend (complex)
 */

import * as vscode from 'vscode';

export enum RequestComplexity {
    SIMPLE_UI_TASK = 'simple',      // Direct AI SDK
    COMPLEX_FEATURE = 'complex',    // Python Backend  
    HYBRID_TASK = 'hybrid',         // Both (orchestrated)
    ANALYSIS_REQUIRED = 'analysis'  // Force Python for analysis
}

export interface DesignRequest {
    message: string;
    fileCount?: number;
    hasExistingCode?: boolean;
    requiresAnalysis?: boolean;
    workspaceContext?: WorkspaceContext;
    conversationHistory?: ConversationMessage[];
    userIntent?: string;
}

export interface WorkspaceContext {
    hasComponents: boolean;
    hasTailwindConfig: boolean;
    hasPackageJson: boolean;
    projectSize: 'small' | 'medium' | 'large';
    frameworks: string[];
    fileTypes: string[];
}

export interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface ClassificationResult {
    complexity: RequestComplexity;
    confidence: number;
    reasoning: string[];
    suggestedActions: string[];
    estimatedDuration: 'fast' | 'medium' | 'slow';
    requiredCapabilities: string[];
}

export class ComplexityAnalyzer {
    private static instance: ComplexityAnalyzer | null = null;
    
    // Pattern definitions for classification
    private readonly simplePatterns = [
        // Basic UI modifications
        /^(change|update|modify|fix)\s+(the\s+)?(color|style|text|font|size|spacing)/i,
        /^(make\s+)?(this|it)\s+(bigger|smaller|bold|italic|centered|left|right)/i,
        /^(add|remove)\s+(some\s+)?(padding|margin|border|shadow)/i,
        
        // Simple component requests
        /^(create|make|add)\s+a\s+(simple|basic|small)\s+(button|input|card|modal|form)/i,
        /^style\s+this\s+(button|input|div|component)/i,
        /^(add|create)\s+(some|a)\s+(text|label|icon|image)/i,
        
        // CSS/styling focused
        /^(apply|add|change)\s+(css|styles|styling)/i,
        /^make\s+it\s+(responsive|mobile|desktop)/i,
        /^(fix|correct)\s+(the\s+)?(layout|alignment|spacing)/i,
    ];

    private readonly complexPatterns = [
        // Complete pages and features
        /^(build|create|design|generate)\s+a\s+(complete|full|entire)\s+(page|website|app|dashboard)/i,
        /^(create|build|make)\s+a\s+(landing\s+page|homepage|about\s+page|contact\s+page)/i,
        /^(design|create)\s+an?\s+(e-commerce|blog|portfolio|admin)\s+(site|page|section)/i,
        /^(build|create)\s+a\s+(shopping\s+cart|checkout|product\s+catalog)/i,
        
        // Multi-file and complex features
        /^(implement|add|create)\s+(routing|navigation|state\s+management)/i,
        /^(integrate|connect|add)\s+(api|database|backend|service)/i,
        /^(create|build)\s+a\s+(multi-step|wizard|complex)\s+form/i,
        /^(add|implement)\s+(authentication|user\s+management|login)/i,
        
        // Analysis and project-level tasks
        /^(analyze|review|audit|check)\s+(my\s+)?(project|codebase|code)/i,
        /^(optimize|improve|refactor)\s+(the\s+)?(performance|structure|architecture)/i,
        /^(migrate|convert|transform)\s+(from|to)/i,
        /^(setup|configure|install)\s+(a\s+)?(new\s+)?(framework|library|tool)/i,
        
        // Advanced UI patterns
        /^(create|build)\s+a\s+(data\s+table|chart|graph|visualization)/i,
        /^(implement|add)\s+(drag\s+and\s+drop|infinite\s+scroll|virtual\s+scrolling)/i,
        /^(build|create)\s+a\s+(realtime|live|dynamic)\s+(dashboard|feed|chat)/i,
    ];

    private readonly keywordWeights: Record<string, number> = {
        // Simple indicators (lower complexity)
        simple: -2,
        basic: -2,
        small: -1,
        quick: -1,
        style: -1,
        color: -1,
        
        // Complex indicators (higher complexity)
        complete: 3,
        full: 2,
        entire: 3,
        complex: 3,
        advanced: 2,
        dashboard: 2,
        ecommerce: 3,
        'e-commerce': 3,
        routing: 2,
        navigation: 1,
        api: 2,
        database: 3,
        authentication: 3,
        'multi-step': 2,
        
        // Analysis indicators
        analyze: 2,
        optimize: 2,
        migrate: 3,
        refactor: 2,
        audit: 2,
        
        // File/structure indicators
        'multi-file': 3,
        project: 1,
        codebase: 2,
        structure: 1,
        architecture: 2,
    };

    public static getInstance(): ComplexityAnalyzer {
        if (!ComplexityAnalyzer.instance) {
            ComplexityAnalyzer.instance = new ComplexityAnalyzer();
        }
        return ComplexityAnalyzer.instance;
    }

    /**
     * Main classification method
     */
    public async classifyRequest(request: DesignRequest): Promise<ClassificationResult> {
        const { message, fileCount = 0, hasExistingCode = false, requiresAnalysis = false } = request;
        
        // Initialize scoring
        let complexityScore = 0;
        let reasoning: string[] = [];
        let requiredCapabilities: string[] = [];

        // Force complex for multi-file requests
        if (fileCount > 1) {
            complexityScore += 5;
            reasoning.push(`Multi-file request (${fileCount} files) requires advanced coordination`);
            requiredCapabilities.push('multi-file-generation');
        }

        // Force complex for analysis requests
        if (requiresAnalysis) {
            return {
                complexity: RequestComplexity.ANALYSIS_REQUIRED,
                confidence: 0.95,
                reasoning: ['Request explicitly requires codebase analysis'],
                suggestedActions: ['Analyze project structure', 'Use Python intelligence layer'],
                estimatedDuration: 'medium',
                requiredCapabilities: ['project-analysis', 'framework-detection']
            };
        }

        // Pattern-based classification
        const simpleMatch = this.simplePatterns.some(pattern => pattern.test(message));
        const complexMatch = this.complexPatterns.some(pattern => pattern.test(message));

        if (complexMatch && !simpleMatch) {
            complexityScore += 4;
            reasoning.push('Matches complex feature patterns');
            requiredCapabilities.push('advanced-generation');
        } else if (simpleMatch && !complexMatch) {
            complexityScore -= 3;
            reasoning.push('Matches simple UI task patterns');
            requiredCapabilities.push('basic-ui-generation');
        }

        // Keyword-based scoring
        const keywordScore = this.calculateKeywordScore(message);
        complexityScore += keywordScore.score;
        reasoning.push(...keywordScore.reasons);

        // Workspace context analysis
        if (request.workspaceContext) {
            const contextScore = this.analyzeWorkspaceContext(request.workspaceContext);
            complexityScore += contextScore.score;
            reasoning.push(...contextScore.reasons);
            requiredCapabilities.push(...contextScore.capabilities);
        }

        // Existing code context
        if (hasExistingCode) {
            complexityScore += 1;
            reasoning.push('Existing codebase requires contextual understanding');
            requiredCapabilities.push('codebase-analysis');
        }

        // Conversation history analysis
        if (request.conversationHistory && request.conversationHistory.length > 0) {
            const historyScore = this.analyzeConversationHistory(request.conversationHistory);
            complexityScore += historyScore.score;
            reasoning.push(...historyScore.reasons);
        }

        // Determine final complexity
        const complexity = this.determineComplexity(complexityScore);
        const confidence = this.calculateConfidence(complexityScore, reasoning.length);
        const estimatedDuration = this.estimateDuration(complexity, complexityScore);

        return {
            complexity,
            confidence,
            reasoning,
            suggestedActions: this.generateSuggestedActions(complexity, requiredCapabilities),
            estimatedDuration,
            requiredCapabilities: Array.from(new Set(requiredCapabilities))
        };
    }

    /**
     * Calculate keyword-based complexity score
     */
    private calculateKeywordScore(message: string): { score: number; reasons: string[] } {
        const words = message.toLowerCase().split(/\s+/);
        let score = 0;
        const reasons: string[] = [];
        const foundKeywords: string[] = [];

        for (const word of words) {
            if (this.keywordWeights[word]) {
                score += this.keywordWeights[word];
                foundKeywords.push(word);
            }
        }

        if (foundKeywords.length > 0) {
            const simpleKeywords = foundKeywords.filter(w => this.keywordWeights[w] < 0);
            const complexKeywords = foundKeywords.filter(w => this.keywordWeights[w] > 0);

            if (simpleKeywords.length > 0) {
                reasons.push(`Simple keywords found: ${simpleKeywords.join(', ')}`);
            }
            if (complexKeywords.length > 0) {
                reasons.push(`Complex keywords found: ${complexKeywords.join(', ')}`);
            }
        }

        return { score, reasons };
    }

    /**
     * Analyze workspace context for complexity indicators
     */
    private analyzeWorkspaceContext(context: WorkspaceContext): { 
        score: number; 
        reasons: string[]; 
        capabilities: string[] 
    } {
        let score = 0;
        const reasons: string[] = [];
        const capabilities: string[] = [];

        // Project size impact
        switch (context.projectSize) {
            case 'large':
                score += 2;
                reasons.push('Large project requires advanced context understanding');
                capabilities.push('large-project-analysis');
                break;
            case 'medium':
                score += 1;
                reasons.push('Medium project benefits from context analysis');
                capabilities.push('project-context');
                break;
        }

        // Framework complexity
        if (context.frameworks.length > 1) {
            score += 1;
            reasons.push(`Multiple frameworks detected: ${context.frameworks.join(', ')}`);
            capabilities.push('multi-framework-support');
        }

        // Configuration files
        if (context.hasTailwindConfig) {
            score += 0.5;
            reasons.push('Tailwind config requires design system analysis');
            capabilities.push('design-system-analysis');
        }

        return { score, reasons, capabilities };
    }

    /**
     * Analyze conversation history for complexity trends
     */
    private analyzeConversationHistory(history: ConversationMessage[]): { score: number; reasons: string[] } {
        let score = 0;
        const reasons: string[] = [];

        // Long conversations suggest complex tasks
        if (history.length > 10) {
            score += 1;
            reasons.push('Extended conversation suggests complex task evolution');
        }

        // Look for escalating complexity in recent messages
        const recentMessages = history.slice(-3);
        const complexTermsInRecent = recentMessages.some(msg =>
            this.complexPatterns.some(pattern => pattern.test(msg.content))
        );

        if (complexTermsInRecent) {
            score += 1;
            reasons.push('Recent messages indicate increasing complexity');
        }

        return { score, reasons };
    }

    /**
     * Determine final complexity classification
     */
    private determineComplexity(score: number): RequestComplexity {
        if (score >= 4) {
            return RequestComplexity.COMPLEX_FEATURE;
        } else if (score >= 1) {
            return RequestComplexity.HYBRID_TASK;
        } else {
            return RequestComplexity.SIMPLE_UI_TASK;
        }
    }

    /**
     * Calculate confidence in classification
     */
    private calculateConfidence(score: number, reasonCount: number): number {
        const baseConfidence = 0.5;
        const scoreConfidence = Math.min(Math.abs(score) * 0.1, 0.4);
        const reasonConfidence = Math.min(reasonCount * 0.05, 0.1);
        
        return Math.min(baseConfidence + scoreConfidence + reasonConfidence, 0.95);
    }

    /**
     * Estimate task duration
     */
    private estimateDuration(complexity: RequestComplexity, score: number): 'fast' | 'medium' | 'slow' {
        switch (complexity) {
            case RequestComplexity.SIMPLE_UI_TASK:
                return 'fast';
            case RequestComplexity.HYBRID_TASK:
                return 'medium';
            case RequestComplexity.COMPLEX_FEATURE:
            case RequestComplexity.ANALYSIS_REQUIRED:
                return score > 6 ? 'slow' : 'medium';
            default:
                return 'medium';
        }
    }

    /**
     * Generate suggested actions based on complexity
     */
    private generateSuggestedActions(
        complexity: RequestComplexity,
        capabilities: string[]
    ): string[] {
        const actions: string[] = [];

        switch (complexity) {
            case RequestComplexity.SIMPLE_UI_TASK:
                actions.push('Use AI SDK for fast response');
                actions.push('Generate component directly');
                break;

            case RequestComplexity.HYBRID_TASK:
                actions.push('Start with AI SDK for immediate feedback');
                actions.push('Use Python backend for validation');
                actions.push('Combine both approaches for optimal result');
                break;

            case RequestComplexity.COMPLEX_FEATURE:
                actions.push('Use Python intelligence layer');
                actions.push('Analyze project structure first');
                actions.push('Generate multi-file coordinated output');
                actions.push('Apply quality assurance pipeline');
                break;

            case RequestComplexity.ANALYSIS_REQUIRED:
                actions.push('Perform comprehensive project analysis');
                actions.push('Use Python backend exclusively');
                actions.push('Provide detailed insights and recommendations');
                break;
        }

        // Add capability-specific actions
        if (capabilities.includes('design-system-analysis')) {
            actions.push('Analyze existing design system');
        }
        if (capabilities.includes('multi-framework-support')) {
            actions.push('Consider framework interactions');
        }

        return actions;
    }

    /**
     * Get workspace context for current VS Code workspace
     */
    public async getWorkspaceContext(): Promise<WorkspaceContext | undefined> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return undefined;
        }

        try {
            const workspaceUri = workspaceFolder.uri;
            
            // Check for key files
            const hasPackageJson = await this.fileExists(workspaceUri, 'package.json');
            const hasTailwindConfig = await this.fileExists(workspaceUri, 'tailwind.config.js') || 
                                    await this.fileExists(workspaceUri, 'tailwind.config.ts');
            const hasComponents = await this.directoryExists(workspaceUri, 'src/components');

            // Analyze project size (simple heuristic)
            const files = await vscode.workspace.findFiles('**/*', '**/node_modules/**', 1000);
            const projectSize = files.length > 500 ? 'large' : files.length > 100 ? 'medium' : 'small';

            // Detect frameworks (basic detection)
            const frameworks: string[] = [];
            if (hasPackageJson) {
                const packageJsonContent = await this.readJsonFile(workspaceUri, 'package.json');
                const deps = { ...packageJsonContent.dependencies, ...packageJsonContent.devDependencies };
                
                if (deps.react) frameworks.push('react');
                if (deps.vue) frameworks.push('vue');
                if (deps.angular) frameworks.push('angular');
                if (deps.svelte) frameworks.push('svelte');
                if (deps.vite) frameworks.push('vite');
            }

            // Get file types
            const fileTypes = Array.from(new Set(
                files.map(file => file.path.split('.').pop()).filter((ext): ext is string => Boolean(ext))
            )).slice(0, 10); // Limit to first 10 types

            return {
                hasComponents,
                hasTailwindConfig,
                hasPackageJson,
                projectSize,
                frameworks,
                fileTypes
            };

        } catch (error) {
            console.warn('Failed to analyze workspace context:', error);
            return undefined;
        }
    }

    private async fileExists(workspaceUri: vscode.Uri, fileName: string): Promise<boolean> {
        try {
            await vscode.workspace.fs.stat(vscode.Uri.joinPath(workspaceUri, fileName));
            return true;
        } catch {
            return false;
        }
    }

    private async directoryExists(workspaceUri: vscode.Uri, dirPath: string): Promise<boolean> {
        try {
            const stat = await vscode.workspace.fs.stat(vscode.Uri.joinPath(workspaceUri, dirPath));
            return stat.type === vscode.FileType.Directory;
        } catch {
            return false;
        }
    }

    private async readJsonFile(workspaceUri: vscode.Uri, fileName: string): Promise<any> {
        try {
            const fileUri = vscode.Uri.joinPath(workspaceUri, fileName);
            const content = await vscode.workspace.fs.readFile(fileUri);
            return JSON.parse(content.toString());
        } catch {
            return {};
        }
    }
}