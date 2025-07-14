/**
 * Codebase Analyzer
 * 
 * This file analyzes the project codebase to understand patterns and structure:
 * - Detects styling approaches (CSS modules, Tailwind, styled-components)
 * - Identifies component structure patterns (single-file vs directory-based)
 * - Extracts import patterns and common props
 * - Analyzes API patterns and custom hooks
 * - Detects UI component libraries and theming approaches
 * - Finds loading/error handling patterns
 * 
 * Provides rich context for intelligent code generation.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { WorkspaceIndex, ComponentInfo } from '../types';
import { indexWorkspace } from './fileIndexer';
import { EmbeddingGenerator } from '../embeddings/embeddingGenerator';
import { ContextRanker } from '../embeddings/contextRanker';

export interface CodebasePatterns {
    stylingApproach: 'css-modules' | 'tailwind' | 'styled-components' | 'regular-css' | 'scss';
    componentStructure: 'single-file' | 'directory-based' | 'mixed';
    importPatterns: string[];
    commonProps: string[];
    stylePaths: string[];
    existingComponents: ComponentInfo[];
    apiPatterns: {
        baseUrls: string[];
        customHooks: string[];
    };
    uiComponents: {
        componentLibrary: 'custom' | 'material-ui' | 'ant-design' | 'chakra-ui' | 'none';
        commonComponents: Record<string, number>;
        importPatterns: string[];
    };
    themePatterns: {
        approach: 'css-variables' | 'tailwind' | 'styled-components' | 'none';
        cssVariables: string[];
        darkModeSupport: boolean;
        colorClasses: string[];
    };
    loadingErrorPatterns: {
        loadingComponents: string[];
        skeletonComponents: string[];
        errorComponents: string[];
    };
}


export class CodebaseAnalyzer {
    private embeddingGenerator: EmbeddingGenerator;

    constructor() {
        this.embeddingGenerator = new EmbeddingGenerator();
    }

    /**
     * Find similar components using embeddings for context-aware generation
     */
    async findSimilarComponents(userPrompt: string, components: ComponentInfo[], maxResults: number = 5): Promise<ComponentInfo[]> {
        try {
            // Filter components that have embeddings
            const componentsWithEmbeddings = components.filter(comp => comp.embedding && comp.embedding.length > 0);
            
            if (componentsWithEmbeddings.length === 0) {
                console.log('No components with embeddings found, returning empty array');
                return [];
            }

            // Generate embedding for the user prompt
            const promptEmbedding = await this.embeddingGenerator.generateTextEmbedding(userPrompt);
            
            if (!promptEmbedding || promptEmbedding.length === 0) {
                console.log('Failed to generate embedding for prompt, returning empty array');
                return [];
            }

            // Find similar components using cosine similarity
            const similarResults = ContextRanker.findSimilarComponents(
                promptEmbedding,
                componentsWithEmbeddings,
                maxResults,
                0.3 // similarity threshold
            );

            console.log(`Found ${similarResults.length} similar components for prompt: "${userPrompt}"`);
            
            return similarResults.map(result => result.component);

        } catch (error) {
            console.error('Error finding similar components:', error);
            return [];
        }
    }

    /**
     * Build context information from similar components for prompt generation
     */
    buildContextFromSimilar(similarComponents: ComponentInfo[], patterns: CodebasePatterns): string {
        if (!similarComponents || similarComponents.length === 0) {
            return '';
        }

        let context = '\n\nSimilar components found in your codebase for reference:\n';
        
        similarComponents.slice(0, 3).forEach((comp, index) => {
            context += `\n${index + 1}. ${comp.name} (${comp.path}):\n`;
            if (comp.summary) {
                context += `   Summary: ${comp.summary}\n`;
            }
            if (comp.props && comp.props.length > 0) {
                context += `   Props: ${comp.props.slice(0, 5).join(', ')}\n`;
            }
            if (comp.hooks && comp.hooks.length > 0) {
                context += `   Hooks: ${comp.hooks.slice(0, 3).join(', ')}\n`;
            }
        });

        context += '\nUse these as inspiration for structure, patterns, and naming conventions.\n';
        return context;
    }

    async analyzeWorkspaceFromPath(projectRoot: string): Promise<CodebasePatterns> {
        const workspaceIndex = await indexWorkspace(projectRoot);
        return this.analyzeWorkspace(workspaceIndex);
    }


    
    
    async analyzeWorkspace(workspaceIndex: WorkspaceIndex): Promise<CodebasePatterns> {
        const patterns: CodebasePatterns = {
            stylingApproach: 'regular-css',
            componentStructure: 'single-file',
            importPatterns: [],
            commonProps: [],
            stylePaths: [],
            existingComponents: workspaceIndex.components,
            apiPatterns: {
                baseUrls: [],
                customHooks: []
            },
            uiComponents: {
                componentLibrary: 'none',
                commonComponents: {},
                importPatterns: []
            },
            themePatterns: {
                approach: 'none',
                cssVariables: [],
                darkModeSupport: false,
                colorClasses: []
            },
            loadingErrorPatterns: {
                loadingComponents: [],
                skeletonComponents: [],
                errorComponents: []
            }
        };
        

        // Analyze styling approach
        patterns.stylingApproach = this.detectStylingApproach(workspaceIndex);
        
        // Analyze component structure
        patterns.componentStructure = this.detectComponentStructure(workspaceIndex);
        
        // Extract common import patterns
        patterns.importPatterns = this.extractImportPatterns(workspaceIndex.components);
        
        // Extract style file paths
        const stylePath = await this.findStylePaths();
        patterns.stylePaths = stylePath ? [stylePath] : [];
        
        // Analyze common props
        patterns.commonProps = this.extractCommonProps(workspaceIndex.components);

        return patterns;
    }

    private detectStylingApproach(workspaceIndex: WorkspaceIndex): CodebasePatterns['stylingApproach'] {
        const files = workspaceIndex.files;
        
        // Check for Tailwind
        if (workspaceIndex.project.dependencies['tailwindcss'] || 
            workspaceIndex.project.devDependencies['tailwindcss'] ||
            files.some(f => f.name.includes('tailwind'))) {
            return 'tailwind';
        }
        
        // Check for styled-components
        if (workspaceIndex.project.dependencies['styled-components'] ||
            workspaceIndex.project.devDependencies['styled-components']) {
            return 'styled-components';
        }
        
        // Check for CSS modules
        if (files.some(f => f.name.includes('.module.css') || f.name.includes('.module.scss'))) {
            return 'css-modules';
        }
        
        // Check for SCSS
        if (files.some(f => f.extension === '.scss' || f.extension === '.sass')) {
            return 'scss';
        }
        
        return 'regular-css';
    }

    private detectComponentStructure(workspaceIndex: WorkspaceIndex): CodebasePatterns['componentStructure'] {
        const components = workspaceIndex.components;
        const componentDirs = new Set<string>();
        
        components.forEach(comp => {
            const dir = path.dirname(comp.path);
            componentDirs.add(dir);
        });
        
        // If components are spread across many directories, likely directory-based
        if (componentDirs.size > components.length * 0.7) {
            return 'directory-based';
        }
        
        // If most components are in similar directories, single-file approach
        if (componentDirs.size < components.length * 0.3) {
            return 'single-file';
        }
        
        return 'mixed';
    }

    private extractImportPatterns(components: ComponentInfo[]): string[] {
        const patterns = new Set<string>();
        
        components.forEach(comp => {
            comp.imports.forEach(imp => {
                // Track common import sources
                if (imp.module.startsWith('.') || imp.module.startsWith('@/') || imp.module.includes('components')) {
                    patterns.add(imp.module);
                }
                
                // Track UI library imports
                if (imp.module.includes('react') || imp.module.includes('vue') || 
                    imp.module.includes('@mui') || imp.module.includes('antd') ||
                    imp.module.includes('chakra') || imp.module.includes('mantine')) {
                    patterns.add(imp.module);
                }
            });
        });
        
        return Array.from(patterns).slice(0, 10); // Top 10 patterns
    }

    private async findStylePaths(): Promise<string> {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) return '';

        const rootPath = workspaceFolders[0].uri.fsPath;
        const commonStylePaths = [
            'src/styles',
            'src/css', 
            'styles',
            'css',
            'assets/styles',
            'assets/css',
            'src/assets/styles'
        ];

        for (const stylePath of commonStylePaths) {
            const fullPath = path.join(rootPath, stylePath);
            if (fs.existsSync(fullPath)) {
                return stylePath;
            }
        }

        // Fallback: look for any CSS files in common locations
        const srcPath = path.join(rootPath, 'src');
        if (fs.existsSync(srcPath)) {
            return 'src';
        }

        return '';
    }

    private extractCommonProps(components: ComponentInfo[]): string[] {
        const propCounts = new Map<string, number>();
        
        components.forEach(comp => {
            comp.props?.forEach(prop => {
                propCounts.set(prop, (propCounts.get(prop) || 0) + 1);
            });
        });
        
        // Return props used in multiple components
        return Array.from(propCounts.entries())
            .filter(([_, count]) => count > 1)
            .sort(([_, a], [__, b]) => b - a)
            .slice(0, 10)
            .map(([prop, _]) => prop);
    }
}