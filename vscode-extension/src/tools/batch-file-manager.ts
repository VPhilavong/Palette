/**
 * Batch File Manager
 * Handles batch file operations with conflict resolution and rollback capabilities
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { 
    PaletteTool, 
    ToolExecutionContext, 
    ToolResult, 
    FileOperationResult 
} from './types';
import { createFileTool, updateFileTool, deleteFileTool } from './file-operations';
import { EnhancedApprovalHandler } from './enhanced-approval-handler';

export interface BatchFileOperation {
    id: string;
    operation: 'create' | 'update' | 'delete' | 'move';
    filePath: string;
    content?: string;
    newPath?: string; // for move operations
    backup?: string; // backup content for rollback
}

export interface BatchFileResult {
    success: boolean;
    operations: Array<{
        operation: BatchFileOperation;
        result: ToolResult;
        executed: boolean;
        backed_up?: boolean;
    }>;
    summary: {
        total: number;
        successful: number;
        failed: number;
        rolledBack: number;
    };
    error?: string;
}

export interface ConflictResolution {
    strategy: 'overwrite' | 'merge' | 'skip' | 'rename';
    newName?: string; // for rename strategy
}

export class BatchFileManager {
    private approvalHandler: EnhancedApprovalHandler;
    private activeOperations: Map<string, BatchFileOperation[]> = new Map();

    constructor(extensionUri: vscode.Uri) {
        this.approvalHandler = new EnhancedApprovalHandler(extensionUri);
    }

    /**
     * Execute multiple file operations as a batch
     */
    async executeBatch(
        operations: BatchFileOperation[],
        context: ToolExecutionContext,
        options: {
            createBackups?: boolean;
            rollbackOnFailure?: boolean;
            conflictResolution?: 'prompt' | 'overwrite' | 'skip';
        } = {}
    ): Promise<BatchFileResult> {
        const batchId = this.generateBatchId();
        this.activeOperations.set(batchId, operations);

        const result: BatchFileResult = {
            success: false,
            operations: operations.map(op => ({
                operation: op,
                result: { success: false },
                executed: false
            })),
            summary: {
                total: operations.length,
                successful: 0,
                failed: 0,
                rolledBack: 0
            }
        };

        try {
            console.log(`📦 Starting batch file operation: ${batchId} (${operations.length} operations)`);

            // 1. Analyze conflicts
            const conflicts = await this.analyzeConflicts(operations, context);
            
            // 2. Request user approval with conflict information
            const approval = await this.requestBatchApproval(operations, conflicts);
            if (!approval.approved) {
                result.error = 'User rejected batch operation';
                return result;
            }

            // 3. Create backups if requested
            if (options.createBackups) {
                await this.createBackups(operations, context);
            }

            // 4. Execute operations with progress tracking
            const progressResults = await this.executeWithProgress(operations, context, result);

            // 5. Handle rollback if needed
            if (options.rollbackOnFailure && result.summary.failed > 0) {
                await this.rollbackOperations(result.operations, context);
            }

            result.success = result.summary.failed === 0;

            // 6. Show summary
            await this.showBatchSummary(result);

            console.log(`📦 Batch operation completed: ${result.summary.successful}/${result.summary.total} successful`);

        } catch (error: any) {
            console.error('📦 Batch operation error:', error);
            result.error = `Batch operation failed: ${error.message}`;
            
            // Attempt rollback on critical error
            if (options.rollbackOnFailure) {
                await this.rollbackOperations(result.operations, context);
            }
        } finally {
            this.activeOperations.delete(batchId);
        }

        return result;
    }

    /**
     * Create a batch tool for creating multiple files with conflict resolution
     */
    createBatchFilesTool(): PaletteTool {
        return {
            name: 'create_files_batch',
            description: 'Create multiple files with conflict resolution and batch approval',
            category: 'file-operations',
            requiresApproval: true,
            dangerLevel: 'caution',
            inputSchema: require('zod').object({
                files: require('zod').array(require('zod').object({
                    filePath: require('zod').string(),
                    content: require('zod').string(),
                    createDirectories: require('zod').boolean().optional().default(true)
                })),
                conflictResolution: require('zod').enum(['prompt', 'overwrite', 'skip']).optional().default('prompt'),
                createBackups: require('zod').boolean().optional().default(true)
            }),
            async execute(params, context: ToolExecutionContext): Promise<FileOperationResult> {
                const operations: BatchFileOperation[] = params.files.map((file: any, index: number) => ({
                    id: `create_${index}`,
                    operation: 'create' as const,
                    filePath: file.filePath,
                    content: file.content
                }));

                const batchManager = new BatchFileManager(context.extensionContext?.extensionUri || vscode.Uri.file(''));
                const result = await batchManager.executeBatch(operations, context, {
                    createBackups: params.createBackups,
                    rollbackOnFailure: true,
                    conflictResolution: params.conflictResolution
                });

                return {
                    success: result.success,
                    data: {
                        batchId: 'batch_' + Date.now(),
                        summary: result.summary
                    },
                    filesCreated: result.operations
                        .filter(op => op.result.success && op.operation.operation === 'create')
                        .map(op => op.operation.filePath),
                    totalSize: result.operations
                        .filter(op => op.result.success)
                        .reduce((sum, op) => sum + (op.operation.content?.length || 0), 0),
                    error: result.error ? {
                        code: 'BATCH_OPERATION_ERROR',
                        message: result.error,
                        recoverable: true
                    } : undefined,
                    followUpSuggestions: [
                        `Batch operation: ${result.summary.successful}/${result.summary.total} files created`,
                        result.summary.failed > 0 ? `${result.summary.failed} operations failed` : 'All operations succeeded'
                    ]
                };
            }
        };
    }

    /**
     * Analyze potential conflicts in batch operations
     */
    private async analyzeConflicts(
        operations: BatchFileOperation[],
        context: ToolExecutionContext
    ): Promise<Array<{ operation: BatchFileOperation; conflictType: string; existingContent?: string }>> {
        const conflicts: Array<{ operation: BatchFileOperation; conflictType: string; existingContent?: string }> = [];

        if (!context.workspacePath) {
            return conflicts;
        }

        for (const operation of operations) {
            try {
                const fullPath = path.resolve(context.workspacePath, operation.filePath);
                const fileUri = vscode.Uri.file(fullPath);
                
                // Check if file exists
                try {
                    await vscode.workspace.fs.stat(fileUri);
                    
                    // File exists, check for conflicts
                    if (operation.operation === 'create') {
                        const contentBytes = await vscode.workspace.fs.readFile(fileUri);
                        const existingContent = new TextDecoder().decode(contentBytes);
                        
                        conflicts.push({
                            operation,
                            conflictType: 'file_exists',
                            existingContent
                        });
                    }
                } catch {
                    // File doesn't exist, no conflict
                }
            } catch (error) {
                console.warn(`Failed to analyze conflict for ${operation.filePath}:`, error);
            }
        }

        return conflicts;
    }

    /**
     * Request approval for batch operations
     */
    private async requestBatchApproval(
        operations: BatchFileOperation[],
        conflicts: Array<{ operation: BatchFileOperation; conflictType: string }>
    ): Promise<{ approved: boolean }> {
        const files = operations.map(op => ({
            path: op.filePath,
            operation: op.operation,
            content: op.content || '',
            exists: conflicts.some(c => c.operation.id === op.id)
        }));

        const approval = await this.approvalHandler.requestFileCreationApproval(
            files.map(f => ({
                path: f.path,
                content: f.content,
                existingContent: f.exists ? 'existing content' : undefined
            }))
        );

        return { approved: approval.approved };
    }

    /**
     * Create backups for operations that modify existing files
     */
    private async createBackups(
        operations: BatchFileOperation[],
        context: ToolExecutionContext
    ): Promise<void> {
        if (!context.workspacePath) return;

        for (const operation of operations) {
            if (operation.operation === 'update' || operation.operation === 'delete') {
                try {
                    const fullPath = path.resolve(context.workspacePath, operation.filePath);
                    const fileUri = vscode.Uri.file(fullPath);
                    
                    const contentBytes = await vscode.workspace.fs.readFile(fileUri);
                    operation.backup = new TextDecoder().decode(contentBytes);
                    
                    console.log(`📦 Created backup for ${operation.filePath}`);
                } catch (error) {
                    console.warn(`Failed to create backup for ${operation.filePath}:`, error);
                }
            }
        }
    }

    /**
     * Execute operations with progress tracking
     */
    private async executeWithProgress(
        operations: BatchFileOperation[],
        context: ToolExecutionContext,
        result: BatchFileResult
    ): Promise<void> {
        await this.approvalHandler.showOperationProgress(
            'Executing batch file operations',
            operations.map(op => `${op.operation}: ${op.filePath}`),
            () => {
                console.log('📦 Batch operation cancelled by user');
            }
        );

        for (let i = 0; i < operations.length; i++) {
            const operation = operations[i];
            const resultItem = result.operations[i];

            try {
                resultItem.result = await this.executeOperation(operation, context);
                resultItem.executed = true;

                if (resultItem.result.success) {
                    result.summary.successful++;
                } else {
                    result.summary.failed++;
                }
            } catch (error: any) {
                resultItem.result = {
                    success: false,
                    error: {
                        code: 'OPERATION_ERROR',
                        message: error.message,
                        recoverable: true
                    }
                };
                result.summary.failed++;
            }
        }
    }

    /**
     * Execute a single operation
     */
    private async executeOperation(
        operation: BatchFileOperation,
        context: ToolExecutionContext
    ): Promise<ToolResult> {
        switch (operation.operation) {
            case 'create':
                return await createFileTool.execute({
                    filePath: operation.filePath,
                    content: operation.content || '',
                    createDirectories: true,
                    overwrite: true
                }, context);

            case 'update':
                return await updateFileTool.execute({
                    filePath: operation.filePath,
                    content: operation.content || '',
                    createIfNotExists: false
                }, context);

            case 'delete':
                return await deleteFileTool.execute({
                    filePath: operation.filePath,
                    force: false
                }, context);

            default:
                throw new Error(`Unsupported operation: ${operation.operation}`);
        }
    }

    /**
     * Rollback operations if needed
     */
    private async rollbackOperations(
        operations: Array<{ operation: BatchFileOperation; result: ToolResult; executed: boolean }>,
        context: ToolExecutionContext
    ): Promise<void> {
        console.log('📦 Starting rollback of batch operations...');

        for (const item of operations.reverse()) {
            if (!item.executed || !item.result.success) continue;

            try {
                await this.rollbackOperation(item.operation, context);
                console.log(`📦 Rolled back: ${item.operation.filePath}`);
            } catch (error) {
                console.error(`📦 Rollback failed for ${item.operation.filePath}:`, error);
            }
        }
    }

    /**
     * Rollback a single operation
     */
    private async rollbackOperation(
        operation: BatchFileOperation,
        context: ToolExecutionContext
    ): Promise<void> {
        if (!context.workspacePath) return;

        const fullPath = path.resolve(context.workspacePath, operation.filePath);
        const fileUri = vscode.Uri.file(fullPath);

        switch (operation.operation) {
            case 'create':
                // Delete the created file
                await vscode.workspace.fs.delete(fileUri);
                break;

            case 'update':
                // Restore from backup
                if (operation.backup) {
                    const contentBytes = new TextEncoder().encode(operation.backup);
                    await vscode.workspace.fs.writeFile(fileUri, contentBytes);
                }
                break;

            case 'delete':
                // Restore from backup
                if (operation.backup) {
                    const contentBytes = new TextEncoder().encode(operation.backup);
                    await vscode.workspace.fs.writeFile(fileUri, contentBytes);
                }
                break;
        }
    }

    /**
     * Show batch operation summary
     */
    private async showBatchSummary(result: BatchFileResult): Promise<void> {
        const successful = result.operations.filter(op => op.result.success).map(op => op.operation.filePath);
        const failed = result.operations
            .filter(op => !op.result.success)
            .map(op => ({
                path: op.operation.filePath,
                error: op.result.error?.message || 'Unknown error'
            }));

        await this.approvalHandler.showOperationSummary(
            'Batch File Operations',
            {
                successful,
                failed,
                skipped: []
            }
        );
    }

    /**
     * Generate unique batch ID
     */
    private generateBatchId(): string {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substring(2, 8);
        return `batch-${timestamp}-${random}`;
    }

    /**
     * Get active batch operations
     */
    getActiveOperations(): Map<string, BatchFileOperation[]> {
        return new Map(this.activeOperations);
    }

    /**
     * Cancel a batch operation
     */
    async cancelBatch(batchId: string): Promise<boolean> {
        if (this.activeOperations.has(batchId)) {
            this.activeOperations.delete(batchId);
            console.log(`📦 Cancelled batch operation: ${batchId}`);
            return true;
        }
        return false;
    }

    /**
     * Dispose of resources
     */
    dispose(): void {
        this.approvalHandler.dispose();
        this.activeOperations.clear();
    }
}