/**
 * Vector Store
 * 
 * Enhanced vector storage and similarity search implementation:
 * - Stores vector embeddings with associated metadata
 * - Performs fast similarity searches using cosine similarity
 * - Manages vector indexing and retrieval operations
 * - Provides efficient nearest neighbor search
 * - Handles vector normalization and distance calculations
 * 
 * Local vector database for component similarity matching.
 */
export class VectorStore {
    private vectors: Map<string, number[]> = new Map();
    private metadata: Map<string, any> = new Map();
    private normalizedVectors: Map<string, number[]> = new Map();

    /**
     * Store embedding with metadata
     */
    store(id: string, embedding: number[], metadata: any): void {
        this.vectors.set(id, embedding);
        this.metadata.set(id, metadata);
        this.normalizedVectors.set(id, this.normalizeVector(embedding));
    }

    /**
     * Find similar vectors using cosine similarity
     */
    findSimilar(queryEmbedding: number[], topK: number = 5): Array<{id: string, score: number, metadata: any}> {
        if (this.vectors.size === 0) {
            return [];
        }

        const normalizedQuery = this.normalizeVector(queryEmbedding);
        const similarities: Array<{id: string, score: number, metadata: any}> = [];

        for (const [id, normalizedVector] of this.normalizedVectors.entries()) {
            const similarity = this.cosineSimilarity(normalizedQuery, normalizedVector);
            const metadata = this.metadata.get(id);
            
            similarities.push({
                id,
                score: similarity,
                metadata
            });
        }

        // Sort by similarity score (descending) and return top K
        return similarities
            .sort((a, b) => b.score - a.score)
            .slice(0, topK);
    }

    /**
     * Calculate cosine similarity between two normalized vectors
     */
    private cosineSimilarity(a: number[], b: number[]): number {
        if (a.length !== b.length) {
            throw new Error('Vector dimensions must match');
        }

        let dotProduct = 0;
        for (let i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
        }

        // Since vectors are normalized, cosine similarity is just the dot product
        return Math.max(0, dotProduct); // Ensure non-negative
    }

    /**
     * Normalize a vector to unit length
     */
    private normalizeVector(vector: number[]): number[] {
        const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
        
        if (magnitude === 0) {
            return new Array(vector.length).fill(0);
        }

        return vector.map(val => val / magnitude);
    }

    /**
     * Find similar items by text query (requires embeddings to be generated)
     */
    async findSimilarByText(
        queryText: string, 
        generateEmbedding: (text: string) => Promise<number[]>,
        topK: number = 5
    ): Promise<Array<{id: string, score: number, metadata: any}>> {
        try {
            const queryEmbedding = await generateEmbedding(queryText);
            return this.findSimilar(queryEmbedding, topK);
        } catch (error) {
            console.error('Error generating embedding for query:', error);
            return [];
        }
    }

    /**
     * Get all stored IDs
     */
    getAllIds(): string[] {
        return Array.from(this.vectors.keys());
    }

    /**
     * Get metadata for a specific ID
     */
    getMetadata(id: string): any {
        return this.metadata.get(id);
    }

    /**
     * Remove a vector by ID
     */
    remove(id: string): boolean {
        const hasVector = this.vectors.has(id);
        this.vectors.delete(id);
        this.metadata.delete(id);
        this.normalizedVectors.delete(id);
        return hasVector;
    }

    /**
     * Get the number of stored vectors
     */
    size(): number {
        return this.vectors.size;
    }

    /**
     * Check if a vector exists
     */
    has(id: string): boolean {
        return this.vectors.has(id);
    }

    /**
     * Clear all stored vectors
     */
    clear(): void {
        this.vectors.clear();
        this.metadata.clear();
        this.normalizedVectors.clear();
    }

    /**
     * Export all data for persistence
     */
    export(): {
        vectors: Array<{id: string, embedding: number[], metadata: any}>;
        count: number;
    } {
        const vectors: Array<{id: string, embedding: number[], metadata: any}> = [];
        
        for (const [id, embedding] of this.vectors.entries()) {
            vectors.push({
                id,
                embedding,
                metadata: this.metadata.get(id)
            });
        }

        return {
            vectors,
            count: vectors.length
        };
    }

    /**
     * Import data from persistence
     */
    import(data: {
        vectors: Array<{id: string, embedding: number[], metadata: any}>;
    }): void {
        this.clear();
        
        for (const item of data.vectors) {
            this.store(item.id, item.embedding, item.metadata);
        }
    }

    /**
     * Batch store multiple vectors
     */
    storeBatch(items: Array<{id: string, embedding: number[], metadata: any}>): void {
        for (const item of items) {
            this.store(item.id, item.embedding, item.metadata);
        }
    }

    /**
     * Find vectors within a similarity threshold
     */
    findWithinThreshold(
        queryEmbedding: number[], 
        threshold: number = 0.7
    ): Array<{id: string, score: number, metadata: any}> {
        return this.findSimilar(queryEmbedding, this.size())
            .filter(result => result.score >= threshold);
    }
}