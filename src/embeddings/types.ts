/**
 * Embedding Types
 * 
 * This file defines TypeScript interfaces for embedding and vector operations:
 * - EmbeddingResult: Structure for storing embeddings with metadata
 * - SimilarityResult: Results from similarity searches with scores
 * - VectorSearchOptions: Configuration for vector search operations
 * 
 * These types ensure type safety for all embedding-related operations
 * and provide clear interfaces for vector search functionality.
 */

export interface EmbeddingResult {
    id: string;
    embedding: number[];
    metadata: {
        componentName: string;
        filePath: string;
        framework: string;
        hooks: string[];
        exports: string[];
    };
}

export interface SimilarityResult {
    id: string;
    score: number;
    metadata: any;
}

export interface VectorSearchOptions {
    topK?: number;
    threshold?: number;
    includeMetadata?: boolean;
}