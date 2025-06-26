import * as vscode from 'vscode';
import * as path from 'path';
import { 
    ContextRequest, 
    CodebaseContext, 
    ContextSelectionStrategy,
    FileMetadata,
    SymbolLocation,
    ContextChunk
} from './types';
import { CodebaseIndexer } from './codebaseIndexer';

/**
 * Enhanced context manager optimized for Gemini 2.0 Flash's massive 2M token context window
 * Unlike Claude's 200K limit, we can include ENTIRE codebases
 */
export class GeminiContextManager {
    private readonly maxTokens: number;
    private readonly tokenBuffer: number;
    private readonly maxFiles: number;
    
    constructor(
        private indexer: CodebaseIndexer,
        maxTokens: number = 2000000, // 2M tokens for Gemini!
        maxFiles: number = 200 // Much higher limit
    ) {
        this.maxTokens = maxTokens;
        this.tokenBuffer = Math.floor(maxTokens * 0.05); // Only 5% buffer
        this.maxFiles = maxFiles;
    }

    /**
     * Build MASSIVE context for Gemini 2.0 Flash
     * Include entire codebase if needed
     */
    async buildMassiveContext(request: ContextRequest): Promise<CodebaseContext> {
        console.log('🚀 Building MASSIVE context for Gemini 2.0 Flash...');
        
        const startTime = Date.now();
        const availableTokens = this.maxTokens - this.tokenBuffer;
        
        // Get current file context
        const currentFileContext = await this.getCurrentFileContext(request);
        
        // Get ALL relevant files (much more aggressive than Claude)
        const allRelevantFiles = await this.findAllRelevantFiles(request);
        
        // Build comprehensive context with minimal filtering
        const massiveContext = await this.buildComprehensiveContext(
            request,
            currentFileContext,
            allRelevantFiles,
            availableTokens
        );
        
        const buildTime = Date.now() - startTime;
        
        console.log(`✅ MASSIVE context built in ${buildTime}ms with ${massiveContext.chunks.length} chunks`);
        console.log(`📊 Context stats: ${massiveContext.files.length} files, ${massiveContext.totalTokens} tokens`);
        
        return {
            request,
            currentFile: currentFileContext,
            relatedFiles: massiveContext.files,
            chunks: massiveContext.chunks,
            dependencies: massiveContext.dependencies,
            symbols: massiveContext.symbols,
            metadata: {
                totalTokens: massiveContext.totalTokens,
                strategy: 'massive_context' as ContextSelectionStrategy,
                buildTime,
                relevanceScore: massiveContext.averageRelevance,
                filesIncluded: massiveContext.files.length,
                chunksIncluded: massiveContext.chunks.length
            }
        };
    }

    /**
     * Get current file context with full content
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
     * Find ALL relevant files - much more comprehensive than Claude version
     */
    private async findAllRelevantFiles(request: ContextRequest): Promise<FileMetadata[]> {
        const allFiles: FileMetadata[] = [];
        const processedPaths = new Set<string>();
        
        // Strategy 1: Include ALL files if small codebase
        const indexStats = this.indexer.getIndexStatus();
        if (indexStats.stats.totalFiles <= 50) {
            console.log('📁 Small codebase detected - including ALL files');
            const allIndexedFiles = Array.from(this.indexer.getIndex().files.values());
            return allIndexedFiles;
        }
        
        // Strategy 2: Keyword/semantic search with higher limits
        if (request.query) {
            const keywordMatches = this.indexer.searchFiles(request.query, { caseSensitive: false });
            keywordMatches.slice(0, 100).forEach(file => { // Higher limit
                if (!processedPaths.has(file.path)) {
                    allFiles.push(file);
                    processedPaths.add(file.path);
                }
            });
        }
        
        // Strategy 3: Dependency-based inclusion (deeper traversal)
        if (request.currentFile) {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                const relativePath = path.relative(workspaceFolder.uri.fsPath, request.currentFile);
                
                // Get direct dependencies
                const directRelated = this.indexer.getRelatedFiles(relativePath, 50);
                directRelated.forEach(file => {
                    if (!processedPaths.has(file.path)) {
                        allFiles.push(file);
                        processedPaths.add(file.path);
                    }
                });
                
                // Get dependencies of dependencies (2nd degree)
                const secondDegree: FileMetadata[] = [];
                directRelated.forEach(file => {
                    const related = this.indexer.getRelatedFiles(file.path, 10);
                    related.forEach(r => {
                        if (!processedPaths.has(r.path)) {
                            secondDegree.push(r);
                            processedPaths.add(r.path);
                        }
                    });
                });
                allFiles.push(...secondDegree);
            }
        }
        
        // Strategy 4: Symbol-based inclusion (more comprehensive)
        if (request.symbols && request.symbols.length > 0) {
            request.symbols.forEach(symbolName => {
                const locations = this.indexer.findSymbol(symbolName);
                locations.forEach(location => {
                    if (location.filePath) {
                        const file = this.indexer.getIndex().files.get(location.filePath);
                        if (file && !processedPaths.has(file.path)) {
                            allFiles.push(file);
                            processedPaths.add(file.path);
                        }
                    }
                });
            });
        }
        
        // Strategy 5: Include files by type/category
        const allIndexedFiles = Array.from(this.indexer.getIndex().files.values());
        
        // Include all TypeScript definition files
        allIndexedFiles.filter(f => f.path.endsWith('.d.ts')).forEach(file => {
            if (!processedPaths.has(file.path)) {
                allFiles.push(file);
                processedPaths.add(file.path);
            }
        });
        
        // Include all config files
        allIndexedFiles.filter(f => 
            f.path.includes('config') || 
            f.path.includes('tsconfig') ||
            f.path.includes('package.json')
        ).forEach(file => {
            if (!processedPaths.has(file.path)) {
                allFiles.push(file);
                processedPaths.add(file.path);
            }
        });
        
        // Include main entry points
        allIndexedFiles.filter(f => 
            f.path.includes('index.') || 
            f.path.includes('main.') ||
            f.path.includes('app.')
        ).forEach(file => {
            if (!processedPaths.has(file.path)) {
                allFiles.push(file);
                processedPaths.add(file.path);
            }
        });
        
        console.log(`📊 Found ${allFiles.length} relevant files for massive context`);
        return allFiles;
    }

    /**
     * Build comprehensive context with minimal filtering
     */
    private async buildComprehensiveContext(
        request: ContextRequest,
        currentFile: FileMetadata | null,
        candidates: FileMetadata[],
        availableTokens: number
    ): Promise<{
        files: FileMetadata[];
        chunks: ContextChunk[];
        dependencies: string[];
        symbols: SymbolLocation[];
        totalTokens: number;
        averageRelevance: number;
    }> {
        const selectedFiles: FileMetadata[] = [];
        const selectedChunks: ContextChunk[] = [];
        const dependencies: string[] = [];
        const symbols: SymbolLocation[] = [];
        let usedTokens = 0;
        
        // Always include current file with FULL content
        if (currentFile) {
            selectedFiles.push(currentFile);
            const fullFileChunks = this.createFullFileChunks(currentFile);
            selectedChunks.push(...fullFileChunks);
            usedTokens += this.estimateFileTokens(currentFile);
            
            console.log(`📄 Included current file: ${currentFile.path} (${this.estimateFileTokens(currentFile)} tokens)`);
        }
        
        // Sort candidates by relevance
        const sortedCandidates = candidates
            .filter(f => !currentFile || f.path !== currentFile.path)
            .sort((a, b) => this.calculateFileRelevance(b, request) - this.calculateFileRelevance(a, request));
        
        // Include as many files as possible within token limit
        const remainingTokens = availableTokens - usedTokens;
        let filesIncluded = 0;
        
        for (const candidate of sortedCandidates) {
            const fileTokens = this.estimateFileTokens(candidate);
            
            // Be more generous with token allocation
            if (usedTokens + fileTokens <= remainingTokens && filesIncluded < this.maxFiles) {
                selectedFiles.push(candidate);
                
                // Include FULL file content for small files
                if (fileTokens < 5000) {
                    const fullChunks = this.createFullFileChunks(candidate);
                    selectedChunks.push(...fullChunks);
                    usedTokens += fileTokens;
                } else {
                    // Include key chunks for larger files
                    const keyChunks = this.selectKeyChunks(candidate, request, fileTokens * 0.7);
                    selectedChunks.push(...keyChunks);
                    usedTokens += keyChunks.reduce((sum, chunk) => sum + chunk.tokens, 0);
                }
                
                // Add to dependencies and symbols
                dependencies.push(...candidate.imports);
                symbols.push(...candidate.symbols);
                
                filesIncluded++;
                
                if (filesIncluded % 20 === 0) {
                    console.log(`📊 Included ${filesIncluded} files, ${usedTokens} tokens used`);
                }
            }
            
            // Stop if we're getting close to the limit
            if (usedTokens >= remainingTokens * 0.95) break;
        }
        
        console.log(`✅ Final context: ${selectedFiles.length} files, ${selectedChunks.length} chunks, ${usedTokens} tokens`);
        
        const averageRelevance = selectedFiles.length > 0 ? 
            selectedFiles.reduce((sum, f) => sum + this.calculateFileRelevance(f, request), 0) / selectedFiles.length :
            0;
        
        return {
            files: selectedFiles,
            chunks: selectedChunks,
            dependencies: [...new Set(dependencies)],
            symbols: symbols.slice(0, 200), // Higher limit
            totalTokens: usedTokens,
            averageRelevance
        };
    }

    /**
     * Create chunks for entire file content
     */
    private createFullFileChunks(file: FileMetadata): ContextChunk[] {
        return file.chunks.map(chunk => ({
            content: chunk.content,
            filePath: file.path,
            startLine: chunk.startLine,
            endLine: chunk.endLine,
            type: chunk.type,
            tokens: chunk.tokens,
            relevanceScore: 1.0,
            context: 'full_file'
        }));
    }

    /**
     * Select key chunks from larger files
     */
    private selectKeyChunks(file: FileMetadata, request: ContextRequest, maxTokens: number): ContextChunk[] {
        const chunks: ContextChunk[] = [];
        let usedTokens = 0;
        
        // Prioritize functions, classes, and interfaces
        const prioritizedChunks = file.chunks
            .map(chunk => ({
                chunk,
                score: this.scoreChunkRelevance(chunk, request, file)
            }))
            .sort((a, b) => b.score - a.score);
        
        for (const { chunk, score } of prioritizedChunks) {
            if (usedTokens + chunk.tokens <= maxTokens) {
                chunks.push({
                    content: chunk.content,
                    filePath: file.path,
                    startLine: chunk.startLine,
                    endLine: chunk.endLine,
                    type: chunk.type,
                    tokens: chunk.tokens,
                    relevanceScore: score,
                    context: 'key_chunk'
                });
                usedTokens += chunk.tokens;
            }
        }
        
        return chunks;
    }

    /**
     * Calculate file relevance for Gemini context
     */
    private calculateFileRelevance(file: FileMetadata, request: ContextRequest): number {
        let score = 0.5; // Base score
        
        // Higher scores for TypeScript files
        if (file.language === 'typescript') score += 0.2;
        
        // Score based on file type
        if (file.path.includes('component')) score += 0.3;
        if (file.path.includes('util') || file.path.includes('helper')) score += 0.2;
        if (file.path.includes('type') || file.path.includes('interface')) score += 0.25;
        if (file.path.includes('config')) score += 0.15;
        
        // Score based on exports (more exports = more important)
        score += Math.min(file.exports.length * 0.05, 0.3);
        
        // Score based on symbols
        score += Math.min(file.symbols.length * 0.02, 0.2);
        
        // Query-based scoring
        if (request.query) {
            const query = request.query.toLowerCase();
            if (file.path.toLowerCase().includes(query)) score += 0.4;
            
            const hasQueryInContent = file.chunks.some(chunk => 
                chunk.content.toLowerCase().includes(query)
            );
            if (hasQueryInContent) score += 0.3;
        }
        
        return Math.min(score, 1.0);
    }

    /**
     * Score chunk relevance for key chunk selection
     */
    private scoreChunkRelevance(chunk: any, request: ContextRequest, file: FileMetadata): number {
        let score = 0;
        
        // Base score by type
        const typeScores: Record<string, number> = {
            'function': 0.8,
            'class': 0.9,
            'interface': 0.85,
            'general': 0.3
        };
        score += typeScores[chunk.type] || 0.3;
        
        // Size-based scoring (prefer substantial chunks)
        if (chunk.tokens > 100 && chunk.tokens < 1000) score += 0.2;
        
        // Query matching
        if (request.query) {
            const query = request.query.toLowerCase();
            if (chunk.content.toLowerCase().includes(query)) {
                score += 0.5;
            }
        }
        
        // Export detection
        if (chunk.content.includes('export')) score += 0.2;
        
        return Math.min(score, 1.0);
    }

    /**
     * Estimate file tokens (more accurate for large context)
     */
    private estimateFileTokens(file: FileMetadata): number {
        return file.chunks.reduce((total, chunk) => total + chunk.tokens, 0);
    }

    /**
     * Get context window utilization
     */
    getContextUtilization(context: CodebaseContext): {
        utilizationPercentage: number;
        tokensUsed: number;
        tokensAvailable: number;
        filesIncluded: number;
        efficiency: number;
    } {
        const tokensUsed = context.metadata.totalTokens;
        const tokensAvailable = this.maxTokens - tokensUsed;
        const utilizationPercentage = (tokensUsed / this.maxTokens) * 100;
        const efficiency = context.relatedFiles.length / tokensUsed; // files per token
        
        return {
            utilizationPercentage,
            tokensUsed,
            tokensAvailable,
            filesIncluded: context.relatedFiles.length,
            efficiency
        };
    }

    /**
     * Build context for multimodal requests
     */
    async buildMultimodalContext(
        request: ContextRequest, 
        imagePaths: string[]
    ): Promise<CodebaseContext> {
        console.log(`🖼️ Building multimodal context with ${imagePaths.length} images...`);
        
        // Reserve tokens for images (rough estimate: 1000 tokens per image)
        const imageTokens = imagePaths.length * 1000;
        const adjustedMaxTokens = this.maxTokens - imageTokens;
        
        // Temporarily reduce max tokens for text context
        const originalMaxTokens = this.maxTokens;
        (this as any).maxTokens = adjustedMaxTokens;
        
        try {
            const context = await this.buildMassiveContext(request);
            
            // Add image information to context metadata
            context.metadata = {
                ...context.metadata,
                multimodal: true,
                imageCount: imagePaths.length,
                estimatedImageTokens: imageTokens
            };
            
            return context;
        } finally {
            // Restore original max tokens
            (this as any).maxTokens = originalMaxTokens;
        }
    }
}