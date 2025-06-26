import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { EventEmitter } from 'events';
import { 
    CodebaseIndex, 
    FileMetadata, 
    SymbolLocation, 
    DependencyGraph,
    SemanticChunk,
    EmbeddingVector,
    IndexStatus
} from './types';

/**
 * High-performance codebase indexer for workspace-wide code understanding
 * Implements incremental indexing, semantic chunking, and fast symbol lookup
 */
export class CodebaseIndexer extends EventEmitter {
    private index: CodebaseIndex;
    private indexStatus: IndexStatus = 'idle';
    private readonly maxFileSize = 100 * 1024; // 100KB limit for performance
    private readonly chunkSize = 512; // tokens per semantic chunk
    private readonly maxConcurrentFiles = 10;
    
    constructor() {
        super();
        this.index = {
            files: new Map(),
            symbols: new Map(),
            dependencies: { nodes: [], edges: [], clusters: [], metrics: { density: 0, modularity: 0, avgPathLength: 0, centralityScores: {} } },
            embeddings: new Map(),
            lastUpdated: new Date(),
            totalFiles: 0,
            indexedFiles: 0
        };
    }

    /**
     * Perform full workspace indexing with progress reporting
     */
    async indexWorkspace(rootPath: string, progress?: vscode.Progress<{message?: string; increment?: number}>): Promise<void> {
        this.indexStatus = 'indexing';
        this.emit('indexingStarted');
        
        try {
            console.log('🚀 Starting comprehensive workspace indexing...');
            
            // Find all relevant files
            const filePaths = await this.findIndexableFiles(rootPath);
            this.index.totalFiles = filePaths.length;
            
            console.log(`📊 Found ${filePaths.length} files to index`);
            
            // Process files in batches for better performance
            const batchSize = this.maxConcurrentFiles;
            let processed = 0;
            
            for (let i = 0; i < filePaths.length; i += batchSize) {
                const batch = filePaths.slice(i, i + batchSize);
                
                // Process batch in parallel
                await Promise.all(batch.map(async (filePath) => {
                    try {
                        await this.indexFile(filePath, rootPath);
                        processed++;
                        this.index.indexedFiles = processed;
                        
                        // Report progress
                        if (progress) {
                            progress.report({
                                message: `Indexing: ${path.basename(filePath)} (${processed}/${filePaths.length})`,
                                increment: (1 / filePaths.length) * 100
                            });
                        }
                        
                        this.emit('fileIndexed', filePath, processed, filePaths.length);
                    } catch (error) {
                        console.warn(`Failed to index ${filePath}:`, error);
                    }
                }));
                
                // Small delay to prevent overwhelming the system
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            
            // Build cross-file relationships
            await this.buildGlobalIndex();
            
            this.index.lastUpdated = new Date();
            this.indexStatus = 'ready';
            
            console.log(`✅ Workspace indexing complete: ${this.index.indexedFiles} files indexed`);
            this.emit('indexingCompleted', this.index);
            
        } catch (error) {
            this.indexStatus = 'error';
            console.error('Workspace indexing failed:', error);
            this.emit('indexingError', error);
            throw error;
        }
    }

    /**
     * Index a single file with semantic analysis
     */
    private async indexFile(filePath: string, rootPath: string): Promise<void> {
        const stat = fs.statSync(filePath);
        
        // Skip large files for performance
        if (stat.size > this.maxFileSize) {
            console.warn(`Skipping large file: ${filePath} (${stat.size} bytes)`);
            return;
        }
        
        const content = fs.readFileSync(filePath, 'utf8');
        const relativePath = path.relative(rootPath, filePath);
        const extension = path.extname(filePath);
        
        // Create file metadata
        const metadata: FileMetadata = {
            path: relativePath,
            absolutePath: filePath,
            size: stat.size,
            modified: stat.mtime,
            extension,
            language: this.detectLanguage(extension),
            lineCount: content.split('\n').length,
            symbols: [],
            imports: [],
            exports: [],
            chunks: []
        };
        
        // Extract symbols and imports/exports
        await this.extractSymbols(content, metadata);
        await this.extractImportsExports(content, metadata);
        
        // Create semantic chunks for better context
        metadata.chunks = await this.createSemanticChunks(content, metadata);
        
        // Store in index
        this.index.files.set(relativePath, metadata);
        
        // Index symbols for fast lookup
        metadata.symbols.forEach(symbol => {
            if (!this.index.symbols.has(symbol.name)) {
                this.index.symbols.set(symbol.name, []);
            }
            this.index.symbols.get(symbol.name)!.push({
                ...symbol,
                filePath: relativePath
            });
        });
    }

    /**
     * Extract symbols (functions, classes, variables) from code
     */
    private async extractSymbols(content: string, metadata: FileMetadata): Promise<void> {
        const symbols: SymbolLocation[] = [];
        
        // TypeScript/JavaScript symbol extraction
        if (metadata.language === 'typescript' || metadata.language === 'javascript') {
            // Function declarations
            const functionRegex = /(?:export\s+)?(?:async\s+)?function\s+(\w+)/g;
            let match;
            while ((match = functionRegex.exec(content)) !== null) {
                const line = content.substring(0, match.index).split('\n').length;
                symbols.push({
                    name: match[1],
                    type: 'function',
                    line,
                    column: match.index - content.lastIndexOf('\n', match.index) - 1,
                    definition: this.extractDefinition(content, match.index)
                });
            }
            
            // Class declarations
            const classRegex = /(?:export\s+)?class\s+(\w+)/g;
            while ((match = classRegex.exec(content)) !== null) {
                const line = content.substring(0, match.index).split('\n').length;
                symbols.push({
                    name: match[1],
                    type: 'class',
                    line,
                    column: match.index - content.lastIndexOf('\n', match.index) - 1,
                    definition: this.extractDefinition(content, match.index)
                });
            }
            
            // Interface declarations
            const interfaceRegex = /(?:export\s+)?interface\s+(\w+)/g;
            while ((match = interfaceRegex.exec(content)) !== null) {
                const line = content.substring(0, match.index).split('\n').length;
                symbols.push({
                    name: match[1],
                    type: 'interface',
                    line,
                    column: match.index - content.lastIndexOf('\n', match.index) - 1,
                    definition: this.extractDefinition(content, match.index)
                });
            }
            
            // Const/let/var declarations
            const variableRegex = /(?:export\s+)?(?:const|let|var)\s+(\w+)/g;
            while ((match = variableRegex.exec(content)) !== null) {
                const line = content.substring(0, match.index).split('\n').length;
                symbols.push({
                    name: match[1],
                    type: 'variable',
                    line,
                    column: match.index - content.lastIndexOf('\n', match.index) - 1,
                    definition: this.extractDefinition(content, match.index, 100) // Shorter for variables
                });
            }
        }
        
        metadata.symbols = symbols;
    }

    /**
     * Extract import/export statements for dependency analysis
     */
    private async extractImportsExports(content: string, metadata: FileMetadata): Promise<void> {
        const imports: string[] = [];
        const exports: string[] = [];
        
        // Import statements
        const importRegex = /import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]/g;
        let match;
        while ((match = importRegex.exec(content)) !== null) {
            imports.push(match[1]);
        }
        
        // Export statements
        const exportRegex = /export\s+(?:default\s+)?(?:class|function|const|let|var|interface|type)\s+(\w+)/g;
        while ((match = exportRegex.exec(content)) !== null) {
            exports.push(match[1]);
        }
        
        // Default exports
        const defaultExportRegex = /export\s+default\s+(\w+)/g;
        while ((match = defaultExportRegex.exec(content)) !== null) {
            exports.push(`default:${match[1]}`);
        }
        
        metadata.imports = imports;
        metadata.exports = exports;
    }

    /**
     * Create semantic chunks for better context selection
     */
    private async createSemanticChunks(content: string, metadata: FileMetadata): Promise<SemanticChunk[]> {
        const chunks: SemanticChunk[] = [];
        const lines = content.split('\n');
        
        // Create chunks based on logical boundaries (functions, classes, etc.)
        let currentChunk: string[] = [];
        let currentType: 'function' | 'class' | 'interface' | 'general' = 'general';
        let startLine = 0;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Detect logical boundaries
            if (line.match(/^(?:export\s+)?(?:class|interface|function)/)) {
                // Save previous chunk if exists
                if (currentChunk.length > 0) {
                    chunks.push({
                        content: currentChunk.join('\n'),
                        startLine,
                        endLine: i - 1,
                        type: currentType,
                        tokens: this.estimateTokens(currentChunk.join('\n'))
                    });
                }
                
                // Start new chunk
                currentChunk = [line];
                currentType = this.detectChunkType(line);
                startLine = i;
            } else {
                currentChunk.push(line);
            }
            
            // Create chunk if it gets too large
            if (this.estimateTokens(currentChunk.join('\n')) > this.chunkSize) {
                chunks.push({
                    content: currentChunk.join('\n'),
                    startLine,
                    endLine: i,
                    type: currentType,
                    tokens: this.estimateTokens(currentChunk.join('\n'))
                });
                
                currentChunk = [];
                startLine = i + 1;
            }
        }
        
        // Add final chunk
        if (currentChunk.length > 0) {
            chunks.push({
                content: currentChunk.join('\n'),
                startLine,
                endLine: lines.length - 1,
                type: currentType,
                tokens: this.estimateTokens(currentChunk.join('\n'))
            });
        }
        
        return chunks;
    }

    /**
     * Build global index for cross-file relationships
     */
    private async buildGlobalIndex(): Promise<void> {
        console.log('🔗 Building global dependency relationships...');
        
        // Build dependency graph
        const nodes: any[] = [];
        const edges: any[] = [];
        
        this.index.files.forEach((metadata, filePath) => {
            nodes.push({
                id: filePath,
                name: path.basename(filePath),
                path: filePath,
                type: 'file',
                weight: metadata.symbols.length,
                connections: 0
            });
            
            // Create edges based on imports
            metadata.imports.forEach(importPath => {
                // Try to resolve relative imports
                let resolvedPath = importPath;
                if (importPath.startsWith('.')) {
                    const dir = path.dirname(filePath);
                    resolvedPath = path.normalize(path.join(dir, importPath));
                    
                    // Add common extensions if not present
                    if (!path.extname(resolvedPath)) {
                        const candidates = [
                            resolvedPath + '.ts',
                            resolvedPath + '.tsx',
                            resolvedPath + '.js',
                            resolvedPath + '.jsx',
                            resolvedPath + '/index.ts',
                            resolvedPath + '/index.tsx'
                        ];
                        
                        for (const candidate of candidates) {
                            if (this.index.files.has(candidate)) {
                                resolvedPath = candidate;
                                break;
                            }
                        }
                    }
                }
                
                if (this.index.files.has(resolvedPath)) {
                    edges.push({
                        from: filePath,
                        to: resolvedPath,
                        type: 'import',
                        weight: 1
                    });
                }
            });
        });
        
        // Update connection counts
        const connectionCounts = new Map<string, number>();
        edges.forEach(edge => {
            connectionCounts.set(edge.from, (connectionCounts.get(edge.from) || 0) + 1);
            connectionCounts.set(edge.to, (connectionCounts.get(edge.to) || 0) + 1);
        });
        
        nodes.forEach(node => {
            node.connections = connectionCounts.get(node.id) || 0;
        });
        
        this.index.dependencies = {
            nodes,
            edges,
            clusters: [],
            metrics: {
                density: edges.length / (nodes.length * (nodes.length - 1)),
                modularity: 0, // Would need community detection algorithm
                avgPathLength: 0, // Would need graph traversal
                centralityScores: {}
            }
        };
    }

    /**
     * Fast symbol lookup across the entire codebase
     */
    findSymbol(name: string): SymbolLocation[] {
        return this.index.symbols.get(name) || [];
    }

    /**
     * Find files containing specific text or patterns
     */
    searchFiles(query: string, options: { caseSensitive?: boolean; regex?: boolean } = {}): FileMetadata[] {
        const results: FileMetadata[] = [];
        const searchPattern = options.regex ? 
            new RegExp(query, options.caseSensitive ? 'g' : 'gi') :
            options.caseSensitive ? query : query.toLowerCase();
        
        this.index.files.forEach((metadata) => {
            let searchContent = '';
            
            // Search in file path
            searchContent += metadata.path;
            
            // Search in symbol names
            metadata.symbols.forEach(symbol => {
                searchContent += ' ' + symbol.name + ' ' + symbol.definition;
            });
            
            // Search in chunks
            metadata.chunks.forEach(chunk => {
                searchContent += ' ' + chunk.content;
            });
            
            if (!options.caseSensitive) {
                searchContent = searchContent.toLowerCase();
            }
            
            const matches = options.regex ?
                (searchPattern as RegExp).test(searchContent) :
                searchContent.includes(searchPattern as string);
            
            if (matches) {
                results.push(metadata);
            }
        });
        
        return results;
    }

    /**
     * Get files that are most relevant to a specific file
     */
    getRelatedFiles(filePath: string, maxResults: number = 10): FileMetadata[] {
        const file = this.index.files.get(filePath);
        if (!file) return [];
        
        const related = new Map<string, number>();
        
        // Score based on shared imports
        file.imports.forEach(importPath => {
            this.index.files.forEach((otherFile, otherPath) => {
                if (otherPath !== filePath && otherFile.imports.includes(importPath)) {
                    related.set(otherPath, (related.get(otherPath) || 0) + 1);
                }
            });
        });
        
        // Score based on shared symbols
        file.symbols.forEach(symbol => {
            const symbolLocations = this.index.symbols.get(symbol.name) || [];
            symbolLocations.forEach(location => {
                if (location.filePath && location.filePath !== filePath) {
                    related.set(location.filePath, (related.get(location.filePath) || 0) + 0.5);
                }
            });
        });
        
        // Sort by relevance score
        const sortedFiles = Array.from(related.entries())
            .sort(([,a], [,b]) => b - a)
            .slice(0, maxResults)
            .map(([path]) => this.index.files.get(path)!)
            .filter(Boolean);
        
        return sortedFiles;
    }

    /**
     * Get current index status and statistics
     */
    getIndexStatus(): { status: IndexStatus; stats: any } {
        return {
            status: this.indexStatus,
            stats: {
                totalFiles: this.index.totalFiles,
                indexedFiles: this.index.indexedFiles,
                totalSymbols: this.index.symbols.size,
                lastUpdated: this.index.lastUpdated,
                dependencyNodes: this.index.dependencies.nodes.length,
                dependencyEdges: this.index.dependencies.edges.length
            }
        };
    }

    /**
     * Incremental update for changed files
     */
    async updateFile(filePath: string, rootPath: string): Promise<void> {
        const relativePath = path.relative(rootPath, filePath);
        
        // Remove old data
        const oldFile = this.index.files.get(relativePath);
        if (oldFile) {
            // Remove old symbols
            oldFile.symbols.forEach(symbol => {
                const locations = this.index.symbols.get(symbol.name) || [];
                const filtered = locations.filter(loc => loc.filePath !== relativePath);
                if (filtered.length === 0) {
                    this.index.symbols.delete(symbol.name);
                } else {
                    this.index.symbols.set(symbol.name, filtered);
                }
            });
        }
        
        // Re-index the file
        await this.indexFile(filePath, rootPath);
        
        // Update global relationships (lightweight)
        // For now, just emit event - full rebuild would be expensive
        this.emit('fileUpdated', relativePath);
    }

    /**
     * Helper methods
     */
    private async findIndexableFiles(rootPath: string): Promise<string[]> {
        const files: string[] = [];
        const extensions = new Set(['.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cs', '.cpp', '.c', '.h']);
        const ignorePatterns = ['node_modules', '.git', 'dist', 'build', '.next', 'coverage'];
        
        const walk = (dir: string) => {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    if (!ignorePatterns.some(pattern => entry.name.includes(pattern))) {
                        walk(fullPath);
                    }
                } else if (entry.isFile()) {
                    const ext = path.extname(entry.name);
                    if (extensions.has(ext)) {
                        files.push(fullPath);
                    }
                }
            }
        };
        
        walk(rootPath);
        return files;
    }

    private detectLanguage(extension: string): string {
        const langMap: Record<string, string> = {
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.py': 'python',
            '.java': 'java',
            '.cs': 'csharp',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        };
        return langMap[extension] || 'unknown';
    }

    private extractDefinition(content: string, index: number, maxLength: number = 200): string {
        const start = Math.max(0, index);
        const end = Math.min(content.length, index + maxLength);
        return content.substring(start, end).trim();
    }

    private detectChunkType(line: string): 'function' | 'class' | 'interface' | 'general' {
        if (line.includes('function')) return 'function';
        if (line.includes('class')) return 'class';
        if (line.includes('interface')) return 'interface';
        return 'general';
    }

    private estimateTokens(text: string): number {
        // Rough estimation: ~4 characters per token
        return Math.ceil(text.length / 4);
    }

    /**
     * Get the current index for direct access
     */
    getIndex(): CodebaseIndex {
        return this.index;
    }

    /**
     * Cleanup resources
     */
    dispose(): void {
        this.removeAllListeners();
        this.index.files.clear();
        this.index.symbols.clear();
        this.index.embeddings.clear();
    }
}