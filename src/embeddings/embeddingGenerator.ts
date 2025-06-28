import OpenAI from 'openai';
import * as vscode from 'vscode';
import { ComponentInfo, EmbeddingConfig, EmbeddingCache } from '../types';
import { Config } from '../utils/config';
import { Logger } from '../utils/logger';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Generates embeddings for components and code chunks using OpenAI's API
 */
export class EmbeddingGenerator {
    private openai: OpenAI | null = null;
    private config: EmbeddingConfig;
    private cache: EmbeddingCache = {};
    private cacheFilePath: string;
    private logger = Logger.getInstance();
    private tokenCount = 0;
    private apiCallCount = 0;
    private lastApiCall = 0;
    private readonly minApiInterval = 100; // 100ms between API calls

    constructor() {
        this.config = {
            model: 'text-embedding-3-large',
            dimensions: 3072,
            maxTokens: 8191,
            batchSize: 2048
        };
        
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
        this.cacheFilePath = path.join(workspacePath, '.vscode', 'ui-copilot-embeddings.json');
        this.loadCache();
        this.initializeOpenAI();
    }

    private initializeOpenAI(): void {
        const apiKey = Config.get('openaiApiKey', '');
        if (!apiKey) {
            this.logger.warn('OpenAI API key not configured for embeddings');
            return;
        }

        this.openai = new OpenAI({
            apiKey,
            timeout: 60000 // 60 second timeout
        });
    }

    /**
     * Generate embedding for a single component
     */
    async generateComponentEmbedding(component: ComponentInfo): Promise<number[]> {
        if (!component.embeddingInput) {
            this.generateComponentSummary(component);
        }

        if (!component.embeddingInput) {
            throw new Error(`No embedding input generated for component ${component.name}`);
        }

        return this.generateTextEmbedding(component.embeddingInput);
    }

    /**
     * Generate embedding for text with caching and rate limiting
     */
    async generateTextEmbedding(text: string): Promise<number[]> {
        if (!this.openai) {
            throw new Error('OpenAI client not initialized. Please set your OpenAI API key.');
        }

        // Check cache first
        const cacheKey = this.generateCacheKey(text);
        if (this.cache[cacheKey]) {
            this.logger.debug(`Cache hit for text: ${text.substring(0, 50)}...`);
            return this.cache[cacheKey].embedding;
        }

        // Rate limiting
        await this.rateLimitDelay();

        // Token count validation
        const tokenCount = this.estimateTokenCount(text);
        if (tokenCount > this.config.maxTokens) {
            throw new Error(`Text too long: ${tokenCount} tokens (max: ${this.config.maxTokens})`);
        }

        try {
            this.logger.debug(`Generating embedding for text (${tokenCount} tokens): ${text.substring(0, 100)}...`);
            
            const response = await this.openai.embeddings.create({
                model: this.config.model,
                input: text,
                dimensions: this.config.dimensions
            });

            this.apiCallCount++;
            this.tokenCount += tokenCount;
            
            const embedding = response.data[0].embedding;
            
            // Cache the result
            this.cache[cacheKey] = {
                embedding,
                lastModified: Date.now(),
                embeddingInput: text
            };
            
            this.saveCache();
            
            this.logger.debug(`Generated embedding: ${embedding.length} dimensions`);
            return embedding;
            
        } catch (error: any) {
            this.logger.error(`Failed to generate embedding: ${error.message}`);
            
            if (error.status === 429) {
                // Rate limit hit - wait and retry once
                await this.exponentialBackoff(1);
                return this.generateTextEmbedding(text);
            }
            
            throw error;
        }
    }

    /**
     * Generate embeddings in batch for performance
     */
    async generateBatchEmbeddings(texts: string[]): Promise<number[][]> {
        if (!this.openai) {
            throw new Error('OpenAI client not initialized. Please set your OpenAI API key.');
        }

        const results: number[][] = [];
        const uncachedTexts: { text: string; index: number }[] = [];

        // Check cache for each text
        for (let i = 0; i < texts.length; i++) {
            const text = texts[i];
            const cacheKey = this.generateCacheKey(text);
            
            if (this.cache[cacheKey]) {
                results[i] = this.cache[cacheKey].embedding;
            } else {
                uncachedTexts.push({ text, index: i });
            }
        }

        // Process uncached texts in batches
        const batchSize = Math.min(this.config.batchSize, 100); // OpenAI batch limit
        
        for (let i = 0; i < uncachedTexts.length; i += batchSize) {
            const batch = uncachedTexts.slice(i, i + batchSize);
            const batchTexts = batch.map(item => item.text);
            
            // Validate token counts
            const totalTokens = batchTexts.reduce((sum, text) => sum + this.estimateTokenCount(text), 0);
            if (totalTokens > this.config.maxTokens * batchTexts.length) {
                this.logger.warn(`Batch ${i} exceeds token limits, processing individually`);
                
                // Process individually if batch is too large
                for (const item of batch) {
                    try {
                        const embedding = await this.generateTextEmbedding(item.text);
                        results[item.index] = embedding;
                    } catch (error) {
                        this.logger.error(`Failed to generate embedding for batch item: ${error}`);
                        // Fill with zeros as fallback
                        results[item.index] = new Array(this.config.dimensions).fill(0);
                    }
                }
                continue;
            }

            await this.rateLimitDelay();

            try {
                this.logger.debug(`Processing batch ${i / batchSize + 1} of ${Math.ceil(uncachedTexts.length / batchSize)} (${batchTexts.length} items)`);
                
                const response = await this.openai.embeddings.create({
                    model: this.config.model,
                    input: batchTexts,
                    dimensions: this.config.dimensions
                });

                this.apiCallCount++;
                this.tokenCount += totalTokens;

                // Store results and cache
                for (let j = 0; j < batch.length; j++) {
                    const embedding = response.data[j].embedding;
                    const item = batch[j];
                    
                    results[item.index] = embedding;
                    
                    // Cache the result
                    const cacheKey = this.generateCacheKey(item.text);
                    this.cache[cacheKey] = {
                        embedding,
                        lastModified: Date.now(),
                        embeddingInput: item.text
                    };
                }
                
            } catch (error: any) {
                this.logger.error(`Batch embedding failed: ${error.message}`);
                
                if (error.status === 429) {
                    await this.exponentialBackoff(Math.floor(i / batchSize) + 1);
                    i -= batchSize; // Retry this batch
                    continue;
                }
                
                // Fill with zeros as fallback
                for (const item of batch) {
                    results[item.index] = new Array(this.config.dimensions).fill(0);
                }
            }
        }

        this.saveCache();
        return results;
    }

    /**
     * Generate human-readable summary for component
     */
    generateComponentSummary(component: ComponentInfo): void {
        const parts: string[] = [];
        
        // Framework detection
        const framework = this.detectFramework(component);
        parts.push(`${framework} component`);
        
        // Component name and purpose
        parts.push(`'${component.name}'`);
        
        // Hook usage patterns
        if (component.hooks && component.hooks.length > 0) {
            const hookDescriptions = this.describeHooks(component.hooks);
            parts.push(`uses ${hookDescriptions}`);
        }
        
        // UI elements and interactions
        if (component.jsxElements && component.jsxElements.length > 0) {
            const uiDescription = this.describeUIElements(component.jsxElements);
            parts.push(`renders ${uiDescription}`);
        }
        
        // Purpose from comments
        if (component.comments && component.comments.length > 0) {
            const purposeComment = component.comments.find(comment => 
                comment.toLowerCase().includes('component') ||
                comment.toLowerCase().includes('renders') ||
                comment.toLowerCase().includes('displays')
            );
            if (purposeComment) {
                parts.push(purposeComment.split('.')[0]); // First sentence only
            }
        }
        
        // File path context
        const pathContext = this.getPathContext(component.path);
        if (pathContext) {
            parts.push(`located in ${pathContext}`);
        }
        
        component.summary = parts.join(', ');
        component.embeddingInput = this.optimizeForEmbedding(component.summary);
    }

    /**
     * Optimize text for embedding generation
     */
    private optimizeForEmbedding(summary: string): string {
        return summary
            .replace(/[\n\r]+/g, ' ') // Remove newlines
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim()
            .substring(0, 500); // Limit length
    }

    /**
     * Detect framework from component metadata
     */
    private detectFramework(component: ComponentInfo): string {
        const imports = component.imports.map(imp => imp.module.toLowerCase());
        
        if (imports.some(imp => imp.includes('vue'))) return 'Vue';
        if (imports.some(imp => imp.includes('next'))) return 'Next.js';
        if (imports.some(imp => imp.includes('react'))) return 'React';
        if (component.path.endsWith('.vue')) return 'Vue';
        
        return 'JavaScript';
    }

    /**
     * Describe hooks in human-readable format
     */
    private describeHooks(hooks: string[]): string {
        const hookDescriptions: Record<string, string> = {
            'useState': 'state management',
            'useEffect': 'side effects',
            'useContext': 'context data',
            'useRouter': 'routing',
            'useUser': 'user authentication',
            'useQuery': 'data fetching',
            'useMutation': 'data updates',
            'ref': 'reactive references',
            'reactive': 'reactive state',
            'computed': 'computed values',
            'watch': 'data watching'
        };
        
        const descriptions = hooks
            .map(hook => hookDescriptions[hook] || hook)
            .slice(0, 3); // Limit to first 3
            
        return descriptions.join(', ');
    }

    /**
     * Describe UI elements in human-readable format
     */
    private describeUIElements(elements: string[]): string {
        const elementDescriptions: Record<string, string> = {
            'form': 'a form',
            'table': 'a data table',
            'button': 'buttons',
            'input': 'input fields',
            'modal': 'a modal dialog',
            'card': 'cards',
            'list': 'lists',
            'grid': 'a grid layout',
            'nav': 'navigation',
            'header': 'a header',
            'footer': 'a footer'
        };
        
        const uniqueElements = [...new Set(elements)];
        const descriptions = uniqueElements
            .map(element => elementDescriptions[element.toLowerCase()] || element)
            .slice(0, 4); // Limit to first 4
            
        return descriptions.join(', ');
    }

    /**
     * Get path context for component location
     */
    private getPathContext(filePath: string): string {
        const pathParts = filePath.split('/');
        const meaningfulParts = pathParts.filter(part => 
            !['src', 'components', 'pages', 'views', 'lib'].includes(part.toLowerCase()) &&
            !part.includes('.') &&
            part.length > 2
        );
        
        return meaningfulParts.slice(-2).join('/') || '';
    }

    /**
     * Rate limiting delay
     */
    private async rateLimitDelay(): Promise<void> {
        const now = Date.now();
        const timeSinceLastCall = now - this.lastApiCall;
        
        if (timeSinceLastCall < this.minApiInterval) {
            await new Promise(resolve => setTimeout(resolve, this.minApiInterval - timeSinceLastCall));
        }
        
        this.lastApiCall = Date.now();
    }

    /**
     * Exponential backoff for retries
     */
    private async exponentialBackoff(attempt: number): Promise<void> {
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000); // Max 30 seconds
        this.logger.warn(`Rate limit hit, waiting ${delay}ms before retry`);
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    /**
     * Estimate token count (rough approximation)
     */
    private estimateTokenCount(text: string): number {
        // Rough estimation: 1 token ≈ 4 characters for English text
        return Math.ceil(text.length / 4);
    }

    /**
     * Generate cache key for text
     */
    private generateCacheKey(text: string): string {
        // Simple hash function for cache key
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return `embed_${Math.abs(hash).toString(36)}`;
    }

    /**
     * Load cache from disk
     */
    private loadCache(): void {
        try {
            if (fs.existsSync(this.cacheFilePath)) {
                const cacheData = fs.readFileSync(this.cacheFilePath, 'utf-8');
                this.cache = JSON.parse(cacheData);
                this.logger.debug(`Loaded ${Object.keys(this.cache).length} cached embeddings`);
            }
        } catch (error) {
            this.logger.warn(`Failed to load embedding cache: ${error}`);
            this.cache = {};
        }
    }

    /**
     * Save cache to disk
     */
    private saveCache(): void {
        try {
            const cacheDir = path.dirname(this.cacheFilePath);
            if (!fs.existsSync(cacheDir)) {
                fs.mkdirSync(cacheDir, { recursive: true });
            }
            
            fs.writeFileSync(this.cacheFilePath, JSON.stringify(this.cache, null, 2));
            this.logger.debug(`Saved ${Object.keys(this.cache).length} embeddings to cache`);
        } catch (error) {
            this.logger.warn(`Failed to save embedding cache: ${error}`);
        }
    }

    /**
     * Get usage statistics
     */
    getUsageStats(): { apiCalls: number; tokens: number; cacheHits: number } {
        return {
            apiCalls: this.apiCallCount,
            tokens: this.tokenCount,
            cacheHits: Object.keys(this.cache).length
        };
    }

    /**
     * Clear cache
     */
    clearCache(): void {
        this.cache = {};
        if (fs.existsSync(this.cacheFilePath)) {
            fs.unlinkSync(this.cacheFilePath);
        }
        this.logger.info('Embedding cache cleared');
    }
}