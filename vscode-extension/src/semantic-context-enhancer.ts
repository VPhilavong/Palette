/**
 * Semantic Context Enhancer using LangChain
 * Provides intelligent component discovery and context enhancement for AI generation
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { OpenAIEmbeddings } from '@langchain/openai';
import { MemoryVectorStore } from 'langchain/vectorstores/memory';
import { Document } from 'langchain/document';

export interface ComponentMetadata {
    name: string;
    filePath: string;
    description: string;
    props?: string[];
    dependencies?: string[];
    category?: string; // 'form', 'navigation', 'layout', 'data', 'feedback'
}

export interface SemanticContext {
    relevantComponents: ComponentMetadata[];
    designPatterns: string[];
    similarImplementations: string[];
    relatedConcepts: string[];
}

export class SemanticContextEnhancer {
    private static instance: SemanticContextEnhancer;
    private vectorStore: MemoryVectorStore | null = null;
    private embeddings: OpenAIEmbeddings | null = null;
    private isInitialized = false;
    private componentMetadata: Map<string, ComponentMetadata> = new Map();

    private constructor() {}

    static getInstance(): SemanticContextEnhancer {
        if (!SemanticContextEnhancer.instance) {
            SemanticContextEnhancer.instance = new SemanticContextEnhancer();
        }
        return SemanticContextEnhancer.instance;
    }

    /**
     * Initialize the semantic context enhancer
     */
    async initialize(): Promise<void> {
        if (this.isInitialized) {
            return;
        }

        try {
            console.log('🎨 Initializing Semantic Context Enhancer...');
            
            // Get OpenAI API key from VSCode settings
            const config = vscode.workspace.getConfiguration('palette');
            const apiKey = config.get<string>('openaiApiKey');
            
            if (!apiKey) {
                console.warn('🎨 No OpenAI API key found, semantic features disabled');
                return;
            }

            // Initialize embeddings
            this.embeddings = new OpenAIEmbeddings({
                openAIApiKey: apiKey,
                modelName: 'text-embedding-3-small', // Cost-effective embedding model
            });

            // Initialize vector store
            this.vectorStore = new MemoryVectorStore(this.embeddings);

            // Index the current workspace
            await this.indexWorkspace();

            this.isInitialized = true;
            console.log('🎨 Semantic Context Enhancer initialized successfully');
        } catch (error) {
            console.error('🎨 Failed to initialize Semantic Context Enhancer:', error);
        }
    }

    /**
     * Index the workspace for semantic search
     */
    private async indexWorkspace(): Promise<void> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            return;
        }

        console.log('🎨 Indexing workspace for semantic search...');
        
        try {
            // Find all component files
            const componentFiles = await this.findComponentFiles(workspaceFolder.uri.fsPath);
            console.log(`🎨 Found ${componentFiles.length} component files to index`);

            // Process each component file
            const documents: Document[] = [];
            for (const filePath of componentFiles) {
                try {
                    const metadata = await this.analyzeComponent(filePath);
                    if (metadata) {
                        this.componentMetadata.set(filePath, metadata);

                        // Create document for vector store
                        const document = new Document({
                            pageContent: this.buildComponentDescription(metadata),
                            metadata: {
                                type: 'component',
                                filePath: metadata.filePath,
                                name: metadata.name,
                                category: metadata.category
                            }
                        });
                        documents.push(document);
                    }
                } catch (error) {
                    console.warn(`🎨 Failed to analyze component ${filePath}:`, error);
                }
            }

            // Add documents to vector store
            if (documents.length > 0 && this.vectorStore) {
                await this.vectorStore.addDocuments(documents);
                console.log(`🎨 Indexed ${documents.length} components for semantic search`);
            }
        } catch (error) {
            console.error('🎨 Failed to index workspace:', error);
        }
    }

    /**
     * Find component files in the workspace
     */
    private async findComponentFiles(workspacePath: string): Promise<string[]> {
        const componentPaths: string[] = [];
        
        // Common component directories
        const searchPaths = [
            path.join(workspacePath, 'src', 'components'),
            path.join(workspacePath, 'components'),
            path.join(workspacePath, 'src', 'ui'),
            path.join(workspacePath, 'src', 'components', 'ui')
        ];

        for (const searchPath of searchPaths) {
            if (fs.existsSync(searchPath)) {
                const files = await this.findFilesRecursive(searchPath, ['.tsx', '.ts', '.jsx', '.js']);
                componentPaths.push(...files);
            }
        }

        return componentPaths;
    }

    /**
     * Recursively find files with given extensions
     */
    private async findFilesRecursive(dir: string, extensions: string[]): Promise<string[]> {
        const files: string[] = [];
        
        try {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory() && !entry.name.startsWith('.')) {
                    const subFiles = await this.findFilesRecursive(fullPath, extensions);
                    files.push(...subFiles);
                } else if (entry.isFile()) {
                    const ext = path.extname(entry.name);
                    if (extensions.includes(ext)) {
                        files.push(fullPath);
                    }
                }
            }
        } catch (error) {
            console.warn(`🎨 Could not read directory ${dir}:`, error);
        }

        return files;
    }

    /**
     * Analyze a component file to extract metadata
     */
    private async analyzeComponent(filePath: string): Promise<ComponentMetadata | null> {
        try {
            const content = fs.readFileSync(filePath, 'utf-8');
            const fileName = path.basename(filePath, path.extname(filePath));
            
            // Extract component name (simple heuristic)
            const componentName = this.extractComponentName(content, fileName);
            if (!componentName) {
                return null;
            }

            // Extract props
            const props = this.extractProps(content);
            
            // Extract dependencies
            const dependencies = this.extractDependencies(content);
            
            // Categorize component
            const category = this.categorizeComponent(componentName, content);
            
            // Generate description
            const description = this.generateComponentDescription(componentName, props, dependencies, category);

            return {
                name: componentName,
                filePath,
                description,
                props,
                dependencies,
                category
            };
        } catch (error) {
            console.warn(`🎨 Failed to analyze component ${filePath}:`, error);
            return null;
        }
    }

    /**
     * Extract component name from file content
     */
    private extractComponentName(content: string, fileName: string): string | null {
        // Look for export default, function, or const declarations
        const patterns = [
            /export\s+default\s+function\s+(\w+)/,
            /export\s+default\s+(\w+)/,
            /const\s+(\w+):\s*React\.FC/,
            /function\s+(\w+)\s*\(/,
            /const\s+(\w+)\s*=.*=>/, 
        ];

        for (const pattern of patterns) {
            const match = content.match(pattern);
            if (match) {
                return match[1];
            }
        }

        // Fallback to file name
        return fileName.charAt(0).toUpperCase() + fileName.slice(1);
    }

    /**
     * Extract props from component
     */
    private extractProps(content: string): string[] {
        const props: string[] = [];
        
        // Look for interface/type definitions
        const interfaceMatch = content.match(/interface\s+\w+Props\s*{([^}]*)}/);
        const typeMatch = content.match(/type\s+\w+Props\s*=\s*{([^}]*)}/);
        
        const propsContent = interfaceMatch?.[1] || typeMatch?.[1] || '';
        
        if (propsContent) {
            // Extract prop names (simple heuristic)
            const propMatches = propsContent.match(/(\w+)(?:\?)?:/g);
            if (propMatches) {
                props.push(...propMatches.map(p => p.replace(/[?:]/g, '')));
            }
        }

        return props;
    }

    /**
     * Extract dependencies from imports
     */
    private extractDependencies(content: string): string[] {
        const dependencies: string[] = [];
        
        // Extract import statements
        const importMatches = content.match(/import\s+.*?from\s+['"]([^'"]+)['"]/g);
        if (importMatches) {
            for (const importMatch of importMatches) {
                const pathMatch = importMatch.match(/from\s+['"]([^'"]+)['"]/);
                if (pathMatch) {
                    const importPath = pathMatch[1];
                    if (importPath.startsWith('@/') || importPath.startsWith('./') || importPath.startsWith('../')) {
                        dependencies.push(importPath);
                    }
                }
            }
        }

        return dependencies;
    }

    /**
     * Categorize component based on name and content
     */
    private categorizeComponent(name: string, content: string): string {
        const lowerName = name.toLowerCase();
        const lowerContent = content.toLowerCase();

        // Form components
        if (lowerName.includes('form') || lowerName.includes('input') || lowerName.includes('button') || 
            lowerName.includes('select') || lowerName.includes('checkbox') || lowerName.includes('radio')) {
            return 'form';
        }

        // Navigation components
        if (lowerName.includes('nav') || lowerName.includes('menu') || lowerName.includes('breadcrumb') ||
            lowerName.includes('tab') || lowerName.includes('sidebar')) {
            return 'navigation';
        }

        // Layout components  
        if (lowerName.includes('layout') || lowerName.includes('grid') || lowerName.includes('container') ||
            lowerName.includes('flex') || lowerName.includes('card') || lowerName.includes('panel')) {
            return 'layout';
        }

        // Data display components
        if (lowerName.includes('table') || lowerName.includes('list') || lowerName.includes('chart') ||
            lowerName.includes('graph') || lowerName.includes('data')) {
            return 'data';
        }

        // Feedback components
        if (lowerName.includes('modal') || lowerName.includes('dialog') || lowerName.includes('toast') ||
            lowerName.includes('alert') || lowerName.includes('notification')) {
            return 'feedback';
        }

        return 'general';
    }

    /**
     * Generate description for component
     */
    private generateComponentDescription(
        name: string,
        props: string[],
        dependencies: string[],
        category: string
    ): string {
        let description = `${name} is a ${category} component`;
        
        if (props.length > 0) {
            description += ` with props: ${props.slice(0, 5).join(', ')}`;
        }
        
        if (dependencies.length > 0) {
            const localDeps = dependencies.filter(d => d.startsWith('@/') || d.startsWith('./') || d.startsWith('../'));
            if (localDeps.length > 0) {
                description += `. Uses: ${localDeps.slice(0, 3).join(', ')}`;
            }
        }

        return description;
    }

    /**
     * Build searchable description for vector store
     */
    private buildComponentDescription(metadata: ComponentMetadata): string {
        return [
            `Component: ${metadata.name}`,
            `Category: ${metadata.category}`,
            `Description: ${metadata.description}`,
            metadata.props && metadata.props.length > 0 ? `Props: ${metadata.props.join(', ')}` : '',
            metadata.dependencies && metadata.dependencies.length > 0 ? `Dependencies: ${metadata.dependencies.join(', ')}` : ''
        ].filter(Boolean).join('\n');
    }

    /**
     * Enhance context with semantic search
     */
    async enhanceContext(userMessage: string, maxComponents: number = 5): Promise<SemanticContext | null> {
        if (!this.isInitialized || !this.vectorStore) {
            console.warn('🎨 Semantic context enhancer not initialized');
            return null;
        }

        try {
            console.log(`🎨 Performing semantic search for: "${userMessage}"`);
            
            // Semantic search for relevant components
            const searchResults = await this.vectorStore.similaritySearchVectorWithScore(
                await this.embeddings!.embedQuery(userMessage),
                maxComponents
            );
            
            const relevantComponents: ComponentMetadata[] = [];
            const designPatterns: string[] = [];
            const relatedConcepts: string[] = [];

            for (const [doc, score] of searchResults) {
                const filePath = doc.metadata.filePath;
                const metadata = this.componentMetadata.get(filePath);
                
                if (metadata && score > 0.1) { // Filter low-relevance results
                    relevantComponents.push(metadata);
                    
                    // Add design patterns based on component category
                    if (metadata.category && !designPatterns.includes(metadata.category)) {
                        designPatterns.push(metadata.category);
                    }
                    
                    // Add related concepts
                    relatedConcepts.push(`${metadata.name} component pattern`);
                }
            }

            console.log(`🎨 Found ${relevantComponents.length} relevant components`);
            
            return {
                relevantComponents,
                designPatterns,
                similarImplementations: [], // TODO: Implement in future
                relatedConcepts
            };
        } catch (error) {
            console.error('🎨 Failed to enhance context:', error);
            return null;
        }
    }

    /**
     * Check if the enhancer is ready to use
     */
    isReady(): boolean {
        return this.isInitialized && this.vectorStore !== null;
    }

    /**
     * Get component metadata by name (for debugging)
     */
    getComponentMetadata(name: string): ComponentMetadata | undefined {
        for (const metadata of this.componentMetadata.values()) {
            if (metadata.name === name) {
                return metadata;
            }
        }
        return undefined;
    }

    /**
     * Re-index workspace (for when files change)
     */
    async reindexWorkspace(): Promise<void> {
        if (!this.isInitialized) {
            return;
        }

        console.log('🎨 Re-indexing workspace...');
        this.componentMetadata.clear();
        
        if (this.vectorStore) {
            // Clear existing vector store
            this.vectorStore = new MemoryVectorStore(this.embeddings!);
        }

        await this.indexWorkspace();
    }
}