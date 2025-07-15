/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { ILogService } from '../../../platform/log/common/logService';

export interface FileModification {
    type: 'create' | 'update' | 'delete' | 'rename' | 'move';
    filePath: string;
    content?: string;
    newPath?: string;
    searchPattern?: string;
    replacement?: string;
    insertAfter?: string;
    insertBefore?: string;
}

export interface FileOperationResult {
    success: boolean;
    filePath: string;
    operation: string;
    error?: string;
    affectedLines?: number[];
    backupPath?: string;
}

export class FileOperationsTool {
    constructor(private readonly logService: ILogService) {}

    async modifyFiles(modifications: FileModification[]): Promise<FileOperationResult[]> {
        const results: FileOperationResult[] = [];
        const backups: Map<string, string> = new Map();

        try {
            // Create backups for files being modified
            for (const mod of modifications) {
                if (mod.type === 'update' && fs.existsSync(mod.filePath)) {
                    const backupPath = await this.createBackup(mod.filePath);
                    backups.set(mod.filePath, backupPath);
                }
            }

            // Execute modifications
            for (const modification of modifications) {
                const result = await this.executeModification(modification);
                if (backups.has(modification.filePath)) {
                    result.backupPath = backups.get(modification.filePath);
                }
                results.push(result);
            }

            return results;
        } catch (error) {
            // Restore backups on error
            await this.restoreBackups(backups);
            throw error;
        }
    }

    private async executeModification(modification: FileModification): Promise<FileOperationResult> {
        try {
            switch (modification.type) {
                case 'create':
                    return await this.createFile(modification);
                case 'update':
                    return await this.updateFile(modification);
                case 'delete':
                    return await this.deleteFile(modification);
                case 'rename':
                    return await this.renameFile(modification);
                case 'move':
                    return await this.moveFile(modification);
                default:
                    throw new Error(`Unknown modification type: ${(modification as any).type}`);
            }
        } catch (error) {
            this.logService.error(`FileOperationsTool: Error executing ${modification.type}`, error);
            return {
                success: false,
                filePath: modification.filePath,
                operation: modification.type,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private async createFile(modification: FileModification): Promise<FileOperationResult> {
        const { filePath, content = '' } = modification;
        
        // Ensure directory exists
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // Check if file already exists
        if (fs.existsSync(filePath)) {
            throw new Error(`File already exists: ${filePath}`);
        }

        fs.writeFileSync(filePath, content, 'utf8');

        return {
            success: true,
            filePath,
            operation: 'create'
        };
    }

    private async updateFile(modification: FileModification): Promise<FileOperationResult> {
        const { filePath, content, searchPattern, replacement, insertAfter, insertBefore } = modification;
        
        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }

        const originalContent = fs.readFileSync(filePath, 'utf8');
        let newContent = originalContent;
        const affectedLines: number[] = [];

        if (content !== undefined) {
            // Complete file replacement
            newContent = content;
        } else if (searchPattern && replacement !== undefined) {
            // Search and replace
            const regex = new RegExp(searchPattern, 'g');
            const matches = [...originalContent.matchAll(regex)];
            
            if (matches.length === 0) {
                throw new Error(`Pattern not found: ${searchPattern}`);
            }

            newContent = originalContent.replace(regex, replacement);
            
            // Calculate affected lines
            const lines = originalContent.split('\n');
            matches.forEach(match => {
                const lineIndex = originalContent.substring(0, match.index).split('\n').length - 1;
                affectedLines.push(lineIndex + 1);
            });
        } else if (insertAfter) {
            // Insert content after a specific line/pattern
            const lines = originalContent.split('\n');
            const insertIndex = lines.findIndex(line => line.includes(insertAfter));
            
            if (insertIndex === -1) {
                throw new Error(`Insert target not found: ${insertAfter}`);
            }

            lines.splice(insertIndex + 1, 0, content || '');
            newContent = lines.join('\n');
            affectedLines.push(insertIndex + 2);
        } else if (insertBefore) {
            // Insert content before a specific line/pattern
            const lines = originalContent.split('\n');
            const insertIndex = lines.findIndex(line => line.includes(insertBefore));
            
            if (insertIndex === -1) {
                throw new Error(`Insert target not found: ${insertBefore}`);
            }

            lines.splice(insertIndex, 0, content || '');
            newContent = lines.join('\n');
            affectedLines.push(insertIndex + 1);
        } else {
            throw new Error('Update operation requires content, searchPattern, insertAfter, or insertBefore');
        }

        fs.writeFileSync(filePath, newContent, 'utf8');

        return {
            success: true,
            filePath,
            operation: 'update',
            affectedLines
        };
    }

    private async deleteFile(modification: FileModification): Promise<FileOperationResult> {
        const { filePath } = modification;
        
        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }

        fs.unlinkSync(filePath);

        return {
            success: true,
            filePath,
            operation: 'delete'
        };
    }

    private async renameFile(modification: FileModification): Promise<FileOperationResult> {
        const { filePath, newPath } = modification;
        
        if (!newPath) {
            throw new Error('Rename operation requires newPath');
        }

        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }

        if (fs.existsSync(newPath)) {
            throw new Error(`Target file already exists: ${newPath}`);
        }

        // Ensure target directory exists
        const dir = path.dirname(newPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        fs.renameSync(filePath, newPath);

        return {
            success: true,
            filePath: newPath,
            operation: 'rename'
        };
    }

    private async moveFile(modification: FileModification): Promise<FileOperationResult> {
        const { filePath, newPath } = modification;
        
        if (!newPath) {
            throw new Error('Move operation requires newPath');
        }

        if (!fs.existsSync(filePath)) {
            throw new Error(`File does not exist: ${filePath}`);
        }

        if (fs.existsSync(newPath)) {
            throw new Error(`Target file already exists: ${newPath}`);
        }

        // Ensure target directory exists
        const dir = path.dirname(newPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }

        // Copy file to new location
        fs.copyFileSync(filePath, newPath);
        
        // Delete original file
        fs.unlinkSync(filePath);

        return {
            success: true,
            filePath: newPath,
            operation: 'move'
        };
    }

    private async createBackup(filePath: string): Promise<string> {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const backupPath = `${filePath}.backup-${timestamp}`;
        
        fs.copyFileSync(filePath, backupPath);
        
        return backupPath;
    }

    private async restoreBackups(backups: Map<string, string>): Promise<void> {
        for (const [originalPath, backupPath] of backups) {
            try {
                if (fs.existsSync(backupPath)) {
                    fs.copyFileSync(backupPath, originalPath);
                    fs.unlinkSync(backupPath);
                }
            } catch (error) {
                this.logService.error(`Failed to restore backup: ${originalPath}`, error);
            }
        }
    }

    // Multi-file operations
    async updateImports(filePaths: string[], oldImport: string, newImport: string): Promise<FileOperationResult[]> {
        const modifications: FileModification[] = filePaths.map(filePath => ({
            type: 'update',
            filePath,
            searchPattern: oldImport.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), // Escape regex
            replacement: newImport
        }));

        return await this.modifyFiles(modifications);
    }

    async addImportToFiles(filePaths: string[], importStatement: string): Promise<FileOperationResult[]> {
        const modifications: FileModification[] = filePaths.map(filePath => ({
            type: 'update',
            filePath,
            insertAfter: 'import', // Insert after last import
            content: importStatement
        }));

        return await this.modifyFiles(modifications);
    }

    async createDirectoryStructure(basePath: string, structure: { [key: string]: string | { [key: string]: any } }): Promise<FileOperationResult[]> {
        const results: FileOperationResult[] = [];
        
        for (const [name, content] of Object.entries(structure)) {
            const fullPath = path.join(basePath, name);
            
            if (typeof content === 'string') {
                // It's a file
                const result = await this.executeModification({
                    type: 'create',
                    filePath: fullPath,
                    content
                });
                results.push(result);
            } else {
                // It's a directory
                if (!fs.existsSync(fullPath)) {
                    fs.mkdirSync(fullPath, { recursive: true });
                }
                
                // Recursively create subdirectory structure
                const subResults = await this.createDirectoryStructure(fullPath, content as { [key: string]: any });
                results.push(...subResults);
            }
        }
        
        return results;
    }
}