import { ComponentInfo, SimilarityResult } from '../types';

/**
 * Context Ranker
 * 
 * This file provides semantic search and similarity ranking capabilities:
 * - Calculates cosine similarity between vector embeddings
 * - Ranks components by semantic similarity to queries
 * - Finds similar components for contextual code generation
 * - Filters results by similarity thresholds
 * - Provides utility methods for vector operations
 * - Supports both component-to-component and query-to-component search
 * 
 * Essential for finding relevant context for AI code generation.
 */
export class ContextRanker {
    /**
     * Calculate cosine similarity between two vectors
     */
    private static cosineSimilarity(vectorA: number[], vectorB: number[]): number {
        if (vectorA.length !== vectorB.length) {
            throw new Error('Vectors must have the same length');
        }

        let dotProduct = 0;
        let normA = 0;
        let normB = 0;

        for (let i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }

        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);

        if (normA === 0 || normB === 0) {
            return 0;
        }

        return dotProduct / (normA * normB);
    }

    /**
     * Find the most similar components to a query embedding
     */
    static findSimilarComponents(
        queryEmbedding: number[],
        components: ComponentInfo[],
        maxResults: number = 10,
        minSimilarity: number = 0.5
    ): SimilarityResult[] {
        const results: SimilarityResult[] = [];

        for (const component of components) {
            if (!component.embedding) {
                continue;
            }

            const similarity = this.cosineSimilarity(queryEmbedding, component.embedding);
            
            if (similarity >= minSimilarity) {
                results.push({
                    component,
                    similarity,
                    rank: 0 // Will be set after sorting
                });
            }
        }

        // Sort by similarity (highest first)
        results.sort((a, b) => b.similarity - a.similarity);

        // Set ranks and limit results
        const limitedResults = results.slice(0, maxResults);
        limitedResults.forEach((result, index) => {
            result.rank = index + 1;
        });

        return limitedResults;
    }

    /**
     * Find components similar to a given component
     */
    static findSimilarToComponent(
        targetComponent: ComponentInfo,
        allComponents: ComponentInfo[],
        maxResults: number = 5,
        minSimilarity: number = 0.6
    ): SimilarityResult[] {
        if (!targetComponent.embedding) {
            throw new Error('Target component must have embedding');
        }

        // Exclude the target component itself
        const otherComponents = allComponents.filter(
            comp => comp.path !== targetComponent.path
        );

        return this.findSimilarComponents(
            targetComponent.embedding,
            otherComponents,
            maxResults,
            minSimilarity
        );
    }

    /**
     * Advanced filtering with framework and hook preferences
     */
    static findSimilarWithFilters(
        queryEmbedding: number[],
        components: ComponentInfo[],
        filters: {
            frameworks?: string[];
            hooks?: string[];
            excludePaths?: string[];
            maxResults?: number;
            minSimilarity?: number;
        } = {}
    ): SimilarityResult[] {
        let filteredComponents = components;

        // Apply filters
        if (filters.excludePaths) {
            filteredComponents = filteredComponents.filter(
                comp => !filters.excludePaths!.some(path => comp.path.includes(path))
            );
        }

        if (filters.hooks && filters.hooks.length > 0) {
            filteredComponents = filteredComponents.filter(comp => {
                if (!comp.hooks) return false;
                return filters.hooks!.some(hook => comp.hooks!.includes(hook));
            });
        }

        return this.findSimilarComponents(
            queryEmbedding,
            filteredComponents,
            filters.maxResults || 10,
            filters.minSimilarity || 0.5
        );
    }

    /**
     * Rank components by multiple criteria
     */
    static rankWithMultipleCriteria(
        results: SimilarityResult[],
        criteria: {
            semanticWeight: number;
            hookMatchWeight: number;
            pathSimilarityWeight: number;
            targetHooks?: string[];
            targetPath?: string;
        }
    ): SimilarityResult[] {
        return results.map(result => {
            let score = result.similarity * criteria.semanticWeight;

            // Hook matching bonus
            if (criteria.targetHooks && result.component.hooks) {
                const hookMatches = criteria.targetHooks.filter(hook =>
                    result.component.hooks!.includes(hook)
                ).length;
                const hookScore = hookMatches / criteria.targetHooks.length;
                score += hookScore * criteria.hookMatchWeight;
            }

            // Path similarity bonus (same directory structure)
            if (criteria.targetPath) {
                const targetDir = criteria.targetPath.split('/').slice(0, -1).join('/');
                const componentDir = result.component.path.split('/').slice(0, -1).join('/');
                const pathSimilarity = targetDir === componentDir ? 1 : 0;
                score += pathSimilarity * criteria.pathSimilarityWeight;
            }

            return {
                ...result,
                similarity: score
            };
        }).sort((a, b) => b.similarity - a.similarity);
    }
}