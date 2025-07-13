/**
 * Component Analyzer
 * 
 * This file analyzes React components in the codebase:
 * - Parses component files to extract structure and metadata
 * - Identifies component names, props, hooks, and JSX elements
 * - Extracts import/export information
 * - Collects component statistics and usage patterns
 * - Filters and categorizes components by type and complexity
 * 
 * Uses AST parsing to understand component structure for context-aware generation.
 */

import * as vscode from 'vscode';
import { ComponentInfo, FileMetadata } from '../types';
import { SimpleComponentParser } from './simpleComponentParser';

export class ComponentAnalyzer {
    private componentParser: SimpleComponentParser;

    constructor() {
        this.componentParser = new SimpleComponentParser();
    }

    async analyzeComponents(files: FileMetadata[]): Promise<ComponentInfo[]> {
        // Filter for component files - include Vue files!
        const componentFiles = files.filter(file => 
            file.isComponent && 
            ['.js', '.jsx', '.ts', '.tsx', '.vue'].includes(file.extension)
        );

        console.log(`Analyzing ${componentFiles.length} potential component files...`);
        console.log(`Total files: ${files.length}, Component files: ${componentFiles.length}`);
        console.log(`Vue files:`, componentFiles.filter(f => f.extension === '.vue').length);
        console.log(`React files:`, componentFiles.filter(f => ['.jsx', '.tsx'].includes(f.extension)).length);

        const components: ComponentInfo[] = [];
        
        // Process files in batches to avoid overwhelming the system
        const batchSize = 5;
        for (let i = 0; i < componentFiles.length; i += batchSize) {
            const batch = componentFiles.slice(i, i + batchSize);
            const batchUris = batch.map(file => {
                // Handle both absolute and relative paths
                if (file.path.startsWith('/')) {
                    return vscode.Uri.file(file.path);
                } else {
                    return vscode.Uri.joinPath(vscode.workspace.workspaceFolders![0].uri, file.path);
                }
            });

            try {
                const batchComponents = await this.componentParser.parseComponentsFromFiles(batchUris);
                components.push(...batchComponents);
                
                // Provide progress feedback
                console.log(`Processed batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(componentFiles.length/batchSize)}: ${batchComponents.length} components found`);
            } catch (error) {
                console.warn(`Failed to process batch starting at ${i}:`, error);
            }
        }

        console.log(`Component analysis complete: ${components.length} components found`);
        return components;
    }

    async analyzeWorkspaceComponents(): Promise<ComponentInfo[]> {
        // Find all potential component files
        const files = await vscode.workspace.findFiles(
            '**/*.{js,jsx,ts,tsx}',
            '{node_modules,dist,build,.next,out}/**',
            100 // Limit for performance
        );

        console.log(`Found ${files.length} JS/TS files to analyze`);

        const components = await this.componentParser.parseComponentsFromFiles(files);
        
        console.log(`Extracted ${components.length} components from workspace`);
        return components;
    }

    getComponentStats(components: ComponentInfo[]): {
        totalComponents: number;
        functionalComponents: number;
        classComponents: number;
        hooksUsage: Record<string, number>;
        commonImports: Record<string, number>;
    } {
        const stats = {
            totalComponents: components.length,
            functionalComponents: 0,
            classComponents: 0,
            hooksUsage: {} as Record<string, number>,
            commonImports: {} as Record<string, number>
        };

        components.forEach(component => {
            // Count component types (simplified)
            if (component.hooks && component.hooks.length > 0) {
                stats.functionalComponents++;
            }

            // Count hook usage
            if (component.hooks) {
                component.hooks.forEach(hook => {
                    stats.hooksUsage[hook] = (stats.hooksUsage[hook] || 0) + 1;
                });
            }

            // Count common imports
            component.imports.forEach(importInfo => {
                stats.commonImports[importInfo.module] = (stats.commonImports[importInfo.module] || 0) + 1;
            });
        });

        return stats;
    }
}