/**
 * File Operations Tools
 * VS Code file system integration tools for creating, reading, updating, and deleting files
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { z } from 'zod';
import { 
    PaletteTool, 
    ToolExecutionContext, 
    ToolResult, 
    FileOperationResult 
} from './types';

/**
 * Create file tool - creates new files with content
 */
export const createFileTool: PaletteTool = {
    name: 'create_file',
    description: 'Create a new file with the specified content',
    category: 'file-operations',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        filePath: z.string().describe('Relative path from workspace root'),
        content: z.string().describe('File content to write'),
        createDirectories: z.boolean().optional().default(true).describe('Create parent directories if they don\'t exist'),
        overwrite: z.boolean().optional().default(false).describe('Overwrite file if it already exists')
    }),
    async execute(params, context: ToolExecutionContext): Promise<FileOperationResult> {
        const { filePath, content, createDirectories, overwrite } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, filePath);
            const fileUri = vscode.Uri.file(fullPath);
            
            // Check if file already exists
            let exists = false;
            try {
                await vscode.workspace.fs.stat(fileUri);
                exists = true;
            } catch {
                // File doesn't exist, which is expected
            }

            if (exists && !overwrite) {
                return {
                    success: false,
                    error: {
                        code: 'FILE_EXISTS',
                        message: `File already exists: ${filePath}`,
                        recoverable: true,
                        suggestedAction: 'Use overwrite: true to replace the file'
                    }
                };
            }

            // Create directories if needed
            if (createDirectories) {
                const dirPath = path.dirname(fullPath);
                const dirUri = vscode.Uri.file(dirPath);
                
                try {
                    await vscode.workspace.fs.createDirectory(dirUri);
                } catch (error) {
                    console.warn(`Directory creation failed (may already exist): ${dirPath}`);
                }
            }

            // Write the file
            const contentBytes = new TextEncoder().encode(content);
            await vscode.workspace.fs.writeFile(fileUri, contentBytes);

            // Open the file in editor
            try {
                const document = await vscode.workspace.openTextDocument(fileUri);
                await vscode.window.showTextDocument(document);
            } catch (error) {
                console.warn('Failed to open created file in editor:', error);
            }

            return {
                success: true,
                data: { filePath, size: contentBytes.length },
                filesCreated: [filePath],
                totalSize: contentBytes.length,
                followUpSuggestions: [
                    'File created successfully and opened in editor',
                    exists ? 'Existing file was overwritten' : 'New file created'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'FILE_CREATION_ERROR',
                    message: `Failed to create file: ${error.message}`,
                    details: error,
                    recoverable: true,
                    suggestedAction: 'Check file path and permissions'
                }
            };
        }
    }
};

/**
 * Read file tool - reads file content
 */
export const readFileTool: PaletteTool = {
    name: 'read_file',
    description: 'Read the contents of a file',
    category: 'file-operations',
    dangerLevel: 'safe',
    inputSchema: z.object({
        filePath: z.string().describe('Relative path from workspace root'),
        encoding: z.string().optional().default('utf8').describe('File encoding')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        const { filePath } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, filePath);
            const fileUri = vscode.Uri.file(fullPath);
            
            const contentBytes = await vscode.workspace.fs.readFile(fileUri);
            const content = new TextDecoder().decode(contentBytes);
            
            return {
                success: true,
                data: { 
                    filePath, 
                    content, 
                    size: contentBytes.length,
                    lineCount: content.split('\n').length
                }
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'FILE_READ_ERROR',
                    message: `Failed to read file: ${error.message}`,
                    details: error,
                    recoverable: true,
                    suggestedAction: 'Check if file exists and is readable'
                }
            };
        }
    }
};

/**
 * Update file tool - updates existing file content
 */
export const updateFileTool: PaletteTool = {
    name: 'update_file',
    description: 'Update the contents of an existing file',
    category: 'file-operations',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        filePath: z.string().describe('Relative path from workspace root'),
        content: z.string().describe('New file content'),
        createIfNotExists: z.boolean().optional().default(false).describe('Create file if it doesn\'t exist')
    }),
    async execute(params, context: ToolExecutionContext): Promise<FileOperationResult> {
        const { filePath, content, createIfNotExists } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, filePath);
            const fileUri = vscode.Uri.file(fullPath);
            
            // Check if file exists
            let exists = false;
            try {
                await vscode.workspace.fs.stat(fileUri);
                exists = true;
            } catch {
                // File doesn't exist
            }

            if (!exists && !createIfNotExists) {
                return {
                    success: false,
                    error: {
                        code: 'FILE_NOT_EXISTS',
                        message: `File does not exist: ${filePath}`,
                        recoverable: true,
                        suggestedAction: 'Use createIfNotExists: true to create the file'
                    }
                };
            }

            // Write the file
            const contentBytes = new TextEncoder().encode(content);
            await vscode.workspace.fs.writeFile(fileUri, contentBytes);

            return {
                success: true,
                data: { filePath, size: contentBytes.length },
                filesUpdated: exists ? [filePath] : [],
                filesCreated: exists ? [] : [filePath],
                totalSize: contentBytes.length,
                followUpSuggestions: [
                    exists ? 'File updated successfully' : 'File created successfully'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'FILE_UPDATE_ERROR',
                    message: `Failed to update file: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Delete file tool - deletes a file
 */
export const deleteFileTool: PaletteTool = {
    name: 'delete_file',
    description: 'Delete a file from the workspace',
    category: 'file-operations',
    requiresApproval: true,
    dangerLevel: 'dangerous',
    inputSchema: z.object({
        filePath: z.string().describe('Relative path from workspace root'),
        force: z.boolean().optional().default(false).describe('Force deletion even if file is important')
    }),
    async execute(params, context: ToolExecutionContext): Promise<FileOperationResult> {
        const { filePath, force } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, filePath);
            const fileUri = vscode.Uri.file(fullPath);
            
            // Safety check for important files
            const importantFiles = ['package.json', 'tsconfig.json', '.gitignore', 'README.md'];
            const fileName = path.basename(filePath);
            
            if (importantFiles.includes(fileName) && !force) {
                return {
                    success: false,
                    error: {
                        code: 'PROTECTED_FILE',
                        message: `Cannot delete important file: ${fileName}`,
                        recoverable: true,
                        suggestedAction: 'Use force: true if you really want to delete this file'
                    }
                };
            }

            // Delete the file
            await vscode.workspace.fs.delete(fileUri);

            return {
                success: true,
                data: { filePath },
                filesDeleted: [filePath],
                followUpSuggestions: [
                    'File deleted successfully'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'FILE_DELETE_ERROR',
                    message: `Failed to delete file: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * List files tool - lists files in a directory
 */
export const listFilesTool: PaletteTool = {
    name: 'list_files',
    description: 'List files and directories in a workspace path',
    category: 'file-operations',
    dangerLevel: 'safe',
    inputSchema: z.object({
        directoryPath: z.string().optional().default('.').describe('Directory path relative to workspace root'),
        includeHidden: z.boolean().optional().default(false).describe('Include hidden files and directories'),
        recursive: z.boolean().optional().default(false).describe('List files recursively'),
        pattern: z.string().optional().describe('Glob pattern to filter files')
    }),
    async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
        const { directoryPath, includeHidden, recursive, pattern } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        try {
            const fullPath = path.resolve(context.workspacePath, directoryPath);
            const dirUri = vscode.Uri.file(fullPath);
            
            let files: string[] = [];
            
            if (pattern) {
                // Use VS Code's file search with glob pattern
                const searchPattern = new vscode.RelativePattern(context.workspacePath, 
                    path.join(directoryPath, pattern));
                const foundFiles = await vscode.workspace.findFiles(searchPattern);
                files = foundFiles.map(uri => vscode.workspace.asRelativePath(uri));
            } else {
                // List directory contents
                const entries = await vscode.workspace.fs.readDirectory(dirUri);
                
                for (const [name, type] of entries) {
                    if (!includeHidden && name.startsWith('.')) {
                        continue;
                    }
                    
                    const relativePath = path.join(directoryPath, name);
                    files.push(relativePath);
                    
                    // Recursive listing
                    if (recursive && type === vscode.FileType.Directory) {
                        try {
                            const subResult = await this.execute({
                                directoryPath: relativePath,
                                includeHidden,
                                recursive: true
                            }, context);
                            
                            if (subResult.success && subResult.data?.files) {
                                files.push(...subResult.data.files);
                            }
                        } catch (error) {
                            console.warn(`Failed to read subdirectory: ${relativePath}`);
                        }
                    }
                }
            }
            
            return {
                success: true,
                data: { 
                    directoryPath,
                    files: files.sort(),
                    count: files.length
                }
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'DIRECTORY_READ_ERROR',
                    message: `Failed to list files: ${error.message}`,
                    details: error,
                    recoverable: true
                }
            };
        }
    }
};

/**
 * Create multiple files tool - creates multiple files in batch
 */
export const createMultipleFilesTool: PaletteTool = {
    name: 'create_multiple_files',
    description: 'Create multiple files at once with their content',
    category: 'file-operations',
    requiresApproval: true,
    dangerLevel: 'caution',
    inputSchema: z.object({
        files: z.array(z.object({
            filePath: z.string(),
            content: z.string(),
            createDirectories: z.boolean().optional().default(true)
        })).describe('Array of files to create'),
        overwrite: z.boolean().optional().default(false).describe('Overwrite existing files')
    }),
    async execute(params, context: ToolExecutionContext): Promise<FileOperationResult> {
        const { files, overwrite } = params;
        
        if (!context.workspacePath) {
            return {
                success: false,
                error: {
                    code: 'NO_WORKSPACE',
                    message: 'No workspace folder is open',
                    recoverable: false
                }
            };
        }

        const createdFiles: string[] = [];
        const errors: string[] = [];
        let totalSize = 0;

        for (const file of files) {
            try {
                const result = await createFileTool.execute({
                    filePath: file.filePath,
                    content: file.content,
                    createDirectories: file.createDirectories,
                    overwrite
                }, context);

                if (result.success) {
                    createdFiles.push(file.filePath);
                    totalSize += (result as FileOperationResult).totalSize || 0;
                } else {
                    errors.push(`${file.filePath}: ${result.error?.message}`);
                }
            } catch (error: any) {
                errors.push(`${file.filePath}: ${error.message}`);
            }
        }

        const allSucceeded = errors.length === 0;

        return {
            success: allSucceeded,
            data: {
                requestedFiles: files.length,
                createdFiles: createdFiles.length,
                errors: errors.length,
                errorDetails: errors
            },
            filesCreated: createdFiles,
            totalSize,
            error: allSucceeded ? undefined : {
                code: 'PARTIAL_FAILURE',
                message: `Created ${createdFiles.length}/${files.length} files. ${errors.length} errors.`,
                details: errors,
                recoverable: true
            },
            followUpSuggestions: allSucceeded 
                ? ['All files created successfully']
                : [`Successfully created ${createdFiles.length} files, ${errors.length} failed`]
        };
    }
};

/**
 * File operations tools collection
 */
export class FileOperationsTools {
    static getAllTools(): PaletteTool[] {
        return [
            createFileTool,
            readFileTool,
            updateFileTool,
            deleteFileTool,
            listFilesTool,
            createMultipleFilesTool
        ];
    }

    static registerAll(registry: any): void {
        this.getAllTools().forEach(tool => {
            registry.registerTool(tool, { enabled: true });
        });
        console.log('🔧 Registered file operation tools');
    }
}