import * as vscode from 'vscode';
import * as path from 'path';
import { 
    ContextRequest, 
    CodebaseContext, 
    ContextSelectionStrategy,
    ContextWindow,
    RelevanceScore,
    FileMetadata,
    SymbolLocation,
    ContextChunk
} from './types';
import { CodebaseIndexer } from './codebaseIndexer';

/**
 * Intelligent context manager for AI requests
 * Handles context window optimization, relevance ranking, and token management
 */
export class ContextManager {
    private readonly maxTokens: number;
    private readonly tokenBuffer: number;
    private readonly maxFiles: number;
    
    constructor(
        private indexer: CodebaseIndexer,
        maxTokens: number = 12000, // Conservative limit for Claude
        maxFiles: number = 20
    ) {
        this.maxTokens = maxTokens;
        this.tokenBuffer = Math.floor(maxTokens * 0.1); // 10% buffer for response
        this.maxFiles = maxFiles;
    }

    /**
     * Build optimized context for AI request
     */
    async buildContext(request: ContextRequest): Promise<CodebaseContext> {
        console.log('🧠 Building intelligent context for request...');
        
        const startTime = Date.now();
        const availableTokens = this.maxTokens - this.tokenBuffer;
        
        // Get current file context
        const currentFileContext = await this.getCurrentFileContext(request);
        
        // Find relevant files based on different strategies
        const relevantFiles = await this.findRelevantFiles(request);
        
        // Rank and select best context
        const selectedContext = await this.selectOptimalContext(
            request,
            currentFileContext,
            relevantFiles,
            availableTokens
        );
        
        const buildTime = Date.now() - startTime;
        
        console.log(`✅ Context built in ${buildTime}ms with ${selectedContext.chunks.length} chunks`);
        
        return {
            request,
            currentFile: currentFileContext,
            relatedFiles: selectedContext.files,
            chunks: selectedContext.chunks,
            dependencies: selectedContext.dependencies,
            symbols: selectedContext.symbols,
            metadata: {
                totalTokens: selectedContext.totalTokens,
                strategy: selectedContext.strategy,
                buildTime,
                relevanceScore: selectedContext.averageRelevance,
                filesIncluded: selectedContext.files.length,
                chunksIncluded: selectedContext.chunks.length
            }
        };
    }

    /**
     * Get context for the current file being edited
     */
    private async getCurrentFileContext(request: ContextRequest): Promise<FileMetadata | null> {
        if (!request.currentFile) return null;
        
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return null;
        
        const relativePath = path.relative(workspaceFolder.uri.fsPath, request.currentFile);
        const fileMetadata = this.indexer.getIndex().files.get(relativePath);
        
        return fileMetadata || null;
    }

    /**
     * Find files relevant to the request using multiple strategies
     */
    private async findRelevantFiles(request: ContextRequest): Promise<RelevanceScore[]> {
        const relevantFiles: RelevanceScore[] = [];
        
        // Strategy 1: Keyword/semantic search
        if (request.query) {
            const keywordMatches = this.indexer.searchFiles(request.query, { caseSensitive: false });
            keywordMatches.forEach(file => {
                relevantFiles.push({
                    file,
                    score: this.calculateKeywordRelevance(request.query!, file),
                    reasons: ['keyword_match'],
                    strategy: 'keyword_search'
                });
            });
        }
        
        // Strategy 2: Related files (imports, dependencies)
        if (request.currentFile) {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                const relativePath = path.relative(workspaceFolder.uri.fsPath, request.currentFile!);
                const relatedFiles = this.indexer.getRelatedFiles(relativePath, 15);
                
                relatedFiles.forEach(file => {
                    relevantFiles.push({
                        file,
                        score: this.calculateDependencyRelevance(file, relativePath),
                        reasons: ['dependency_relationship'],
                        strategy: 'dependency_analysis'
                    });
                });
            }
        }
        
        // Strategy 3: Symbol-based relevance
        if (request.symbols && request.symbols.length > 0) {
            request.symbols.forEach(symbolName => {
                const locations = this.indexer.findSymbol(symbolName);
                locations.forEach(location => {
                    const file = location.filePath ? this.indexer.getIndex().files.get(location.filePath) : null;
                    if (file) {
                        relevantFiles.push({
                            file,
                            score: this.calculateSymbolRelevance(symbolName, file),
                            reasons: ['symbol_usage'],
                            strategy: 'symbol_analysis'
                        });
                    }
                });
            });
        }
        
        // Strategy 4: Recently modified files (if no specific context)
        if (relevantFiles.length === 0) {
            const recentFiles = this.getRecentlyModifiedFiles(10);
            recentFiles.forEach(file => {
                relevantFiles.push({
                    file,
                    score: 0.3, // Lower baseline score
                    reasons: ['recently_modified'],
                    strategy: 'recency_fallback'
                });
            });
        }
        
        // Deduplicate and merge scores for same files
        const fileScores = new Map<string, RelevanceScore>();
        relevantFiles.forEach(item => {
            const path = item.file.path;
            const existing = fileScores.get(path);
            
            if (existing) {
                // Combine scores and reasons
                existing.score = Math.max(existing.score, item.score * 0.8); // Slight penalty for multiple matches
                existing.reasons = [...new Set([...existing.reasons, ...item.reasons])];
                existing.strategy = existing.strategy === item.strategy ? existing.strategy : 'multi_strategy';
            } else {
                fileScores.set(path, { ...item });
            }
        });
        
        // Sort by relevance score
        return Array.from(fileScores.values())
            .sort((a, b) => b.score - a.score)
            .slice(0, this.maxFiles * 2); // Get more than needed for final selection
    }

    /**
     * Select optimal context within token limits
     */
    private async selectOptimalContext(
        request: ContextRequest,
        currentFile: FileMetadata | null,
        candidates: RelevanceScore[],
        availableTokens: number
    ): Promise<{
        files: FileMetadata[];
        chunks: ContextChunk[];
        dependencies: string[];
        symbols: SymbolLocation[];
        totalTokens: number;
        strategy: ContextSelectionStrategy;
        averageRelevance: number;
    }> {
        const selectedFiles: FileMetadata[] = [];
        const selectedChunks: ContextChunk[] = [];
        const dependencies: string[] = [];
        const symbols: SymbolLocation[] = [];
        let usedTokens = 0;
        
        // Always include current file context if available
        if (currentFile) {
            const currentFileTokens = this.estimateFileTokens(currentFile);
            if (currentFileTokens <= availableTokens * 0.4) { // Max 40% for current file
                selectedFiles.push(currentFile);
                selectedChunks.push(...this.createContextChunks(currentFile, 'current_file'));
                usedTokens += currentFileTokens;
            } else {
                // Include partial current file context
                const partialChunks = this.selectRelevantChunks(currentFile, request, availableTokens * 0.4);
                selectedChunks.push(...partialChunks);
                usedTokens += partialChunks.reduce((sum, chunk) => sum + chunk.tokens, 0);
            }
        }
        
        // Select additional files by relevance, respecting token limits
        const remainingTokens = availableTokens - usedTokens;
        let strategy: ContextSelectionStrategy = 'relevance_based';
        
        for (const candidate of candidates) {
            const fileTokens = this.estimateFileTokens(candidate.file);
            
            // Skip if already included
            if (selectedFiles.some(f => f.path === candidate.file.path)) continue;
            
            // Check if we have space for this file
            if (usedTokens + fileTokens <= remainingTokens && selectedFiles.length < this.maxFiles) {
                selectedFiles.push(candidate.file);
                
                // Select most relevant chunks from this file
                const chunks = this.selectRelevantChunks(candidate.file, request, fileTokens);
                selectedChunks.push(...chunks);
                
                // Add to dependencies and symbols
                dependencies.push(...candidate.file.imports);
                symbols.push(...candidate.file.symbols);
                
                usedTokens += chunks.reduce((sum, chunk) => sum + chunk.tokens, 0);
            } else if (usedTokens < remainingTokens) {
                // Include partial file content
                const availableForChunks = remainingTokens - usedTokens;
                const chunks = this.selectRelevantChunks(candidate.file, request, availableForChunks);
                
                if (chunks.length > 0) {
                    selectedChunks.push(...chunks);
                    usedTokens += chunks.reduce((sum, chunk) => sum + chunk.tokens, 0);
                    strategy = 'chunk_based';
                }
            }
            
            // Stop if we're getting close to the limit
            if (usedTokens >= remainingTokens * 0.9) break;
        }
        
        const averageRelevance = candidates.length > 0 ? 
            candidates.slice(0, selectedFiles.length).reduce((sum, c) => sum + c.score, 0) / selectedFiles.length :
            0;
        
        return {
            files: selectedFiles,
            chunks: selectedChunks,
            dependencies: [...new Set(dependencies)], // Remove duplicates
            symbols: symbols.slice(0, 50), // Limit symbols to avoid noise
            totalTokens: usedTokens,
            strategy,
            averageRelevance
        };
    }

    /**
     * Select most relevant chunks from a file
     */
    private selectRelevantChunks(file: FileMetadata, request: ContextRequest, maxTokens: number): ContextChunk[] {
        const chunks: ContextChunk[] = [];
        let usedTokens = 0;
        
        // Score chunks by relevance to request
        const scoredChunks = file.chunks.map(chunk => ({
            chunk,
            score: this.scoreChunkRelevance(chunk, request)
        })).sort((a, b) => b.score - a.score);
        
        // Select chunks within token limit
        for (const { chunk, score } of scoredChunks) {
            if (usedTokens + chunk.tokens <= maxTokens) {
                chunks.push({
                    content: chunk.content,
                    filePath: file.path,
                    startLine: chunk.startLine,
                    endLine: chunk.endLine,
                    type: chunk.type,
                    tokens: chunk.tokens,
                    relevanceScore: score,
                    context: 'code_chunk'
                });
                usedTokens += chunk.tokens;
            }
        }
        
        return chunks;
    }

    /**
     * Create context chunks for entire file
     */
    private createContextChunks(file: FileMetadata, context: string): ContextChunk[] {
        return file.chunks.map(chunk => ({
            content: chunk.content,
            filePath: file.path,
            startLine: chunk.startLine,
            endLine: chunk.endLine,
            type: chunk.type,
            tokens: chunk.tokens,
            relevanceScore: 1.0,
            context
        }));
    }

    /**
     * Score chunk relevance to request
     */
    private scoreChunkRelevance(chunk: any, request: ContextRequest): number {
        let score = 0;
        
        // Base score by chunk type
        const typeScores: Record<string, number> = {
            'function': 0.8,
            'class': 0.9,
            'interface': 0.7,
            'general': 0.5
        };
        score += typeScores[chunk.type] || 0.5;
        
        // Keyword matching
        if (request.query) {
            const keywords = request.query.toLowerCase().split(/\s+/);
            const content = chunk.content.toLowerCase();
            
            keywords.forEach(keyword => {
                if (content.includes(keyword)) {
                    score += 0.3;
                }
            });
        }
        
        // Symbol relevance
        if (request.symbols) {
            request.symbols.forEach(symbol => {
                if (chunk.content.includes(symbol)) {
                    score += 0.4;
                }
            });
        }
        
        // Position-based scoring (functions and classes are more important)
        if (chunk.type === 'function' || chunk.type === 'class') {
            score += 0.2;
        }
        
        return Math.min(score, 1.0); // Cap at 1.0
    }

    /**
     * Calculate relevance scores
     */
    private calculateKeywordRelevance(query: string, file: FileMetadata): number {
        const keywords = query.toLowerCase().split(/\s+/);
        let matches = 0;
        let totalPossible = 0;
        
        const searchText = [
            file.path,
            ...file.symbols.map(s => s.name),
            ...file.chunks.map(c => c.content)
        ].join(' ').toLowerCase();
        
        keywords.forEach(keyword => {
            totalPossible++;
            if (searchText.includes(keyword)) {
                matches++;
            }
        });
        
        return totalPossible > 0 ? matches / totalPossible : 0;
    }

    private calculateDependencyRelevance(file: FileMetadata, currentFilePath: string): number {
        // Higher score for direct dependencies
        let score = 0.5; // Base score for being related
        
        // Check if current file imports this file
        const currentFile = this.indexer.getIndex().files.get(currentFilePath);
        if (currentFile?.imports.some(imp => this.resolvesTo(imp, file.path))) {
            score += 0.3;
        }
        
        // Check if this file imports current file
        if (file.imports.some(imp => this.resolvesTo(imp, currentFilePath))) {
            score += 0.2;
        }
        
        return Math.min(score, 1.0);
    }

    private calculateSymbolRelevance(symbolName: string, file: FileMetadata): number {
        let score = 0;
        
        // Higher score if file defines the symbol
        if (file.symbols.some(s => s.name === symbolName)) {
            score += 0.8;
        }
        
        // Lower score if file just uses the symbol
        if (file.chunks.some(c => c.content.includes(symbolName))) {
            score += 0.4;
        }
        
        return Math.min(score, 1.0);
    }

    /**
     * Utility methods
     */
    private estimateFileTokens(file: FileMetadata): number {
        return file.chunks.reduce((total, chunk) => total + chunk.tokens, 0);
    }

    private getRecentlyModifiedFiles(limit: number): FileMetadata[] {
        const files = Array.from(this.indexer.getIndex().files.values());
        return files
            .sort((a, b) => b.modified.getTime() - a.modified.getTime())
            .slice(0, limit);
    }

    private resolvesTo(importPath: string, filePath: string): boolean {
        // Simplified resolution logic
        if (importPath.startsWith('.')) {
            // Relative import - would need proper resolution
            return importPath.includes(path.basename(filePath, path.extname(filePath)));
        }
        return false;
    }

    /**
     * Context window management
     */
    createContextWindow(context: CodebaseContext): ContextWindow {
        return {
            request: context.request,
            totalTokens: context.metadata.totalTokens,
            availableTokens: this.maxTokens - context.metadata.totalTokens,
            efficiency: context.metadata.totalTokens / this.maxTokens,
            files: context.relatedFiles,
            chunks: context.chunks,
            metadata: context.metadata
        };
    }

    /**
     * Optimize context for specific AI model constraints
     */
    async optimizeForModel(context: CodebaseContext, modelTokenLimit: number): Promise<CodebaseContext> {
        if (context.metadata.totalTokens <= modelTokenLimit) {
            return context; // Already within limits
        }
        
        // Re-select with stricter token limit
        const optimizedRequest: ContextRequest = {
            ...context.request,
            maxTokens: modelTokenLimit
        };
        
        return this.buildContext(optimizedRequest);
    }

    /**
     * Get context statistics
     */
    getContextStats(): {
        indexStatus: any;
        averageContextSize: number;
        totalRequests: number;
    } {
        return {
            indexStatus: this.indexer.getIndexStatus(),
            averageContextSize: 0, // Would track across requests
            totalRequests: 0 // Would track across requests
        };
    }
}