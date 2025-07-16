/**
 * Type Definitions
 * 
 * This file contains all TypeScript interfaces and types used throughout
 * the UI Copilot extension. It defines:
 * - File and component metadata structures
 * - Workspace indexing types
 * - Framework detection interfaces
 * - Embedding and similarity result types
 * - Configuration interfaces
 * 
 * These types ensure type safety across the entire codebase.
 */

export interface FileMetadata {
    
    path: string;
    name: string;
    extension: string;
    size: number;
    lastModified: Date;
    isComponent?: boolean;
}

export interface Framework {
    name: string;
    version?: string;
    detected: boolean;
    confidence: number;
    // Add this new field
    variant?: 'app-router' | 'pages-router' | 'standard';
}

export interface ProjectMetadata {
    rootPath: string;
    frameworks: Framework[];
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
    hasTypeScript: boolean;
    uiLibraries: string[];
    stateManagement: string[];
}

export interface ComponentInfo {
    name: string;
    path: string;
    exports: string[];
    imports: ImportInfo[];
    props?: string[];
    hooks?: string[];
    jsxElements?: string[];
    comments?: string[];
    summary?: string;
    embeddingInput?: string;
    embedding?: number[];
}

export interface ImportInfo {
    module: string;
    imports: string[];
    isDefault: boolean;
}

export interface WorkspaceIndex {
    files: FileMetadata[];
    components: ComponentInfo[];
    project: ProjectMetadata;
    lastUpdated: Date;
}

export interface EmbeddingConfig {
    model: string;
    dimensions: number;
    maxTokens: number;
    batchSize: number;
}

export interface SimilarityResult {
    component: ComponentInfo;
    similarity: number;
    rank: number;
}

export interface EmbeddingCache {
    [componentPath: string]: {
        embedding: number[];
        lastModified: number;
        embeddingInput: string;
    };
}