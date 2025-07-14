/**
 * File Indexer
 * 
 * This file handles workspace file indexing and monitoring:
 * - Recursively scans workspace directories for relevant files
 * - Filters files by type and size for efficient processing
 * - Creates file metadata with paths, extensions, and modification times
 * - Sets up file watchers for automatic re-indexing on changes
 * - Excludes common directories (node_modules, .git, etc.)
 * 
 * Provides the foundation for codebase analysis and component discovery.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { FileMetadata } from '../types';
import { WorkspaceIndex } from '../types';

export class FileIndexer {
    private excludePatterns: string[] = [
        'node_modules',
        '.git',
        'dist',
        'build',
        '.next',
        'out',
        'coverage'
    ];

    private maxFileSize: number = 102400; // 100KB

    constructor() {
        // Load configuration
        const config = vscode.workspace.getConfiguration('ui-copilot');
        this.excludePatterns = config.get('indexing.excludePatterns', this.excludePatterns);
        this.maxFileSize = config.get('indexing.maxFileSize', this.maxFileSize);
    }

    async indexWorkspace(): Promise<FileMetadata[]> {
        const files: FileMetadata[] = [];
        
        if (!vscode.workspace.workspaceFolders) {
            return files;
        }

        for (const folder of vscode.workspace.workspaceFolders) {
            const workspaceFiles = await this.indexFolder(folder.uri);
            files.push(...workspaceFiles);
        }

        return files;
    }

    private async indexFolder(_folderUri: vscode.Uri): Promise<FileMetadata[]> {
        const files: FileMetadata[] = [];
        
        // Use VSCode's built-in file search with exclude patterns - INCLUDE .vue files!
        const includePattern = '**/*.{js,jsx,ts,tsx,vue,json,md}';
        const excludePattern = `{${this.excludePatterns.map(p => `**/${p}/**`).join(',')}}`;

        console.log(`Searching with pattern: ${includePattern}`);
        const fileUris = await vscode.workspace.findFiles(includePattern, excludePattern, 10000);
        console.log(`Found ${fileUris.length} files total`);

        for (const fileUri of fileUris) {
            try {
                const stat = await vscode.workspace.fs.stat(fileUri);
                
                // Skip files that are too large
                if (stat.size > this.maxFileSize) {
                    continue;
                }

                const relativePath = vscode.workspace.asRelativePath(fileUri);
                const fileName = path.basename(fileUri.fsPath);
                const extension = path.extname(fileName);

                const isComponent = this.isLikelyComponent(fileName, extension);
                const metadata: FileMetadata = {
                    path: relativePath,
                    name: fileName,
                    extension,
                    size: stat.size,
                    lastModified: new Date(stat.mtime),
                    isComponent
                };

                if (extension === '.vue') {
                    console.log(`Vue file: ${relativePath} - isComponent: ${isComponent}`);
                }

                files.push(metadata);
            } catch (error) {
                console.warn(`Failed to index file ${fileUri.fsPath}:`, error);
            }
        }

        return files;
    }

    private isLikelyComponent(fileName: string, extension: string): boolean {
        if (!['.js', '.jsx', '.ts', '.tsx', '.vue'].includes(extension)) {
            return false;
        }

        // Component naming conventions - be more inclusive
        const componentPatterns = [
            /^[A-Z][a-zA-Z0-9]*\.(jsx?|tsx?)$/, // PascalCase files
            /^use[A-Z][a-zA-Z0-9]*\.(js|ts)$/, // Custom hooks
            /\.component\.(jsx?|tsx?)$/, // .component files
            /components?\//i, // Files in components folders
            /pages?\//i, // Files in pages folders (Next.js)
            /routes?\//i, // Files in routes folders
            /\.(jsx|tsx|vue)$/, // All JSX/TSX/Vue files (likely components)
            /[Cc]omponent/, // Files with "component" in name
            /[Ll]ayout/, // Layout files
            /[Hh]eader/, // Header files
            /[Ff]ooter/, // Footer files
            /[Nn]avbar|[Nn]av/, // Navigation files
            /[Mm]enu/, // Menu files
            /\.vue$/, // All Vue Single File Components
            /^VP[A-Z]/, // VitePress components (VP prefix)
        ];

        console.log(`Checking if ${fileName} is component:`, componentPatterns.some(pattern => 
            pattern.test(fileName) || pattern.test(fileName.toLowerCase())
        ));

        return componentPatterns.some(pattern => 
            pattern.test(fileName) || pattern.test(fileName.toLowerCase())
        );
    }

    setupFileWatcher(): vscode.Disposable {
        const watcher = vscode.workspace.onDidChangeTextDocument((event) => {
            // Handle file changes for live updates
            console.log(`File changed: ${event.document.uri.fsPath}`);
            // TODO: Update index incrementally
        });

        return watcher;
    }

    

    
}
export async function indexWorkspace(projectPath: string): Promise<WorkspaceIndex> {
    const fileIndexer = new FileIndexer();
    const files = await fileIndexer.indexWorkspace();

    const components = files
        .filter(f => f.isComponent)
        .map(f => ({
            path: f.path,
            name: f.name,
            extension: f.extension,
            size: f.size,
            lastModified: f.lastModified,
            isComponent: f.isComponent,
            exports: [], // You can extract this later
            imports: [], // You can extract this later
            hooks: [],   // Optional: add if you're extracting hooks
            jsxElements: [], // Optional: extract JSX/HTML elements used
            props: []    // Optional: list of prop names used
        }));

    const workspaceIndex: WorkspaceIndex = {
        files,
        components,
        project: {
            rootPath: projectPath,
            dependencies: {}, // TODO: extract from package.json
            devDependencies: {}, // TODO: extract from package.json
            frameworks: [], // TODO: use your backendDetector here
            hasTypeScript: files.some(f => f.extension === '.ts' || f.extension === '.tsx'),
            uiLibraries: [], // TODO: extract from imports
            stateManagement: [] // TODO: extract (e.g., Redux, Zustand)
        },
        lastUpdated: new Date() // Initialize with the current date
    };

    return workspaceIndex;
}