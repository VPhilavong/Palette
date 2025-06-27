import * as vscode from 'vscode';
import * as path from 'path';
import { FileMetadata } from './types';

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
        
        // Use VSCode's built-in file search with exclude patterns
        const includePattern = '**/*.{js,jsx,ts,tsx,json,md}';
        const excludePattern = `{${this.excludePatterns.map(p => `**/${p}/**`).join(',')}}`;

        const fileUris = await vscode.workspace.findFiles(includePattern, excludePattern, 10000);

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

                const metadata: FileMetadata = {
                    path: relativePath,
                    name: fileName,
                    extension,
                    size: stat.size,
                    lastModified: new Date(stat.mtime),
                    isComponent: this.isLikelyComponent(fileName, extension)
                };

                files.push(metadata);
            } catch (error) {
                console.warn(`Failed to index file ${fileUri.fsPath}:`, error);
            }
        }

        return files;
    }

    private isLikelyComponent(fileName: string, extension: string): boolean {
        if (!['.js', '.jsx', '.ts', '.tsx'].includes(extension)) {
            return false;
        }

        // Component naming conventions
        const componentPatterns = [
            /^[A-Z][a-zA-Z0-9]*\.(jsx?|tsx?)$/, // PascalCase
            /^use[A-Z][a-zA-Z0-9]*\.(js|ts)$/, // Custom hooks
            /\.component\.(jsx?|tsx?)$/, // .component files
            /components?\//i, // Files in components folders
        ];

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