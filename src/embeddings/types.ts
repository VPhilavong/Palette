/**
 * Types specific to embedding and vector operations
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