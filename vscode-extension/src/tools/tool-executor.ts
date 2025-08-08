/**
 * Tool Executor
 * Handles safe execution of tools with approval, validation, and error handling
 */

import * as vscode from 'vscode';
import { 
    PaletteTool, 
    ToolResult, 
    ToolExecutionContext, 
    ToolError,
    UserApprovalHandler,
    ApprovalRequest,
    ApprovalResponse,
    FilePreview,
    BatchOperation,
    PendingOperation,
    ToolExecutionLog
} from './types';
import { ToolRegistry } from './tool-registry';

export class ToolExecutor {
    private static instance: ToolExecutor | null = null;
    private registry: ToolRegistry;
    private approvalHandler?: UserApprovalHandler;
    private batchOperations: Map<string, BatchOperation> = new Map();

    private constructor() {
        this.registry = ToolRegistry.getInstance();
        console.log('⚡ Tool Executor initialized');
    }

    static getInstance(): ToolExecutor {
        if (!this.instance) {
            this.instance = new ToolExecutor();
        }
        return this.instance;
    }

    /**
     * Set the user approval handler
     */
    setApprovalHandler(handler: UserApprovalHandler): void {
        this.approvalHandler = handler;
    }

    /**
     * Execute a single tool
     */
    async executeTool(
        toolName: string, 
        params: any, 
        context: ToolExecutionContext
    ): Promise<ToolResult> {
        const startTime = Date.now();
        let result: ToolResult = {
            success: false,
            error: {
                code: 'INITIALIZATION_ERROR',
                message: 'Tool execution not completed',
                recoverable: true
            }
        };
        
        try {
            console.log(`⚡ Executing tool: ${toolName}`);
            
            // Get tool
            const tool = this.registry.getTool(toolName);
            if (!tool) {
                throw new Error(`Tool not found: ${toolName}`);
            }

            // Validate parameters
            const validation = this.registry.validateToolParams(toolName, params);
            if (!validation.valid) {
                throw new Error(`Parameter validation failed: ${validation.error}`);
            }

            // Check if approval is required
            if (this.registry.requiresApproval(toolName)) {
                const approvalGranted = await this.requestApproval(tool, params, context);
                if (!approvalGranted) {
                    result = {
                        success: false,
                        error: {
                            code: 'USER_DENIED',
                            message: 'User denied approval for tool execution',
                            recoverable: true
                        }
                    };
                    return result;
                }
            }

            // Execute before hooks
            const options = this.registry.getToolOptions(toolName);
            if (options?.onBeforeExecute) {
                await options.onBeforeExecute(params, context);
            }

            // Execute the tool
            result = await this.executeWithTimeout(tool, params, context);

            // Execute after hooks
            if (options?.onAfterExecute) {
                await options.onAfterExecute(result, context);
            }

            console.log(`⚡ Tool ${toolName} executed: ${result.success ? 'SUCCESS' : 'FAILED'}`);

        } catch (error: any) {
            console.error(`⚡ Tool execution error for ${toolName}:`, error);
            result = {
                success: false,
                error: {
                    code: 'EXECUTION_ERROR',
                    message: error.message || 'Unknown execution error',
                    details: error,
                    recoverable: true,
                    suggestedAction: 'Check tool parameters and try again'
                }
            };
        } finally {
            // Log execution
            const executionTime = Date.now() - startTime;
            this.logExecution(toolName, params, result, executionTime);
        }

        return result;
    }

    /**
     * Execute multiple tools in a batch with single approval
     */
    async executeBatch(
        operations: Array<{ tool: string; params: any }>,
        context: ToolExecutionContext
    ): Promise<BatchOperation> {
        const batchId = this.generateBatchId();
        const pendingOperations: PendingOperation[] = [];

        // Prepare all operations
        for (let i = 0; i < operations.length; i++) {
            const { tool, params } = operations[i];
            const toolInstance = this.registry.getTool(tool);
            
            if (!toolInstance) {
                console.warn(`⚡ Skipping unknown tool: ${tool}`);
                continue;
            }

            // Generate preview for approval
            const preview = await this.generateToolPreview(toolInstance, params, context);
            
            pendingOperations.push({
                id: `${batchId}-${i}`,
                tool,
                params,
                preview,
                approved: false,
                executed: false
            });
        }

        // Create batch operation
        const batch: BatchOperation = {
            id: batchId,
            operations: pendingOperations,
            status: 'pending',
            createdAt: new Date().toISOString()
        };

        this.batchOperations.set(batchId, batch);

        // Request batch approval
        if (this.approvalHandler) {
            const approvalRequest: ApprovalRequest = {
                operation: 'Batch Operation',
                description: `Execute ${pendingOperations.length} tools`,
                files: pendingOperations.flatMap(op => op.preview),
                dangerLevel: this.getBatchDangerLevel(pendingOperations),
                canSkipInFuture: true
            };

            const approval = await this.approvalHandler.requestApproval(approvalRequest);
            
            if (approval.approved) {
                batch.status = 'approved';
                batch.approvedAt = new Date().toISOString();
                
                // Execute all operations
                await this.executeBatchOperations(batch, context);
            } else {
                batch.status = 'rejected';
            }
        }

        return batch;
    }

    /**
     * Execute approved batch operations
     */
    private async executeBatchOperations(
        batch: BatchOperation,
        context: ToolExecutionContext
    ): Promise<void> {
        for (const operation of batch.operations) {
            try {
                operation.result = await this.executeTool(operation.tool, operation.params, context);
                operation.executed = true;
                
                // Update batch status if any operation fails
                if (!operation.result.success) {
                    console.warn(`⚡ Batch operation ${operation.id} failed:`, operation.result.error);
                }
            } catch (error) {
                console.error(`⚡ Batch operation ${operation.id} error:`, error);
                operation.result = {
                    success: false,
                    error: {
                        code: 'BATCH_EXECUTION_ERROR',
                        message: `Failed to execute ${operation.tool}: ${error}`,
                        recoverable: true
                    }
                };
            }
        }

        batch.status = 'completed';
    }

    /**
     * Get batch operation by ID
     */
    getBatchOperation(batchId: string): BatchOperation | undefined {
        return this.batchOperations.get(batchId);
    }

    /**
     * Get all batch operations
     */
    getAllBatchOperations(): BatchOperation[] {
        return Array.from(this.batchOperations.values());
    }

    /**
     * Clear completed batch operations
     */
    clearCompletedBatches(): void {
        for (const [id, batch] of this.batchOperations.entries()) {
            if (batch.status === 'completed' || batch.status === 'rejected') {
                this.batchOperations.delete(id);
            }
        }
    }

    /**
     * Execute tool with timeout protection
     */
    private async executeWithTimeout(
        tool: PaletteTool,
        params: any,
        context: ToolExecutionContext,
        timeoutMs: number = 30000 // 30 seconds
    ): Promise<ToolResult> {
        return Promise.race([
            tool.execute(params, context),
            new Promise<ToolResult>((_, reject) => {
                setTimeout(() => {
                    reject(new Error(`Tool execution timeout: ${tool.name}`));
                }, timeoutMs);
            })
        ]);
    }

    /**
     * Request user approval for tool execution
     */
    private async requestApproval(
        tool: PaletteTool,
        params: any,
        context: ToolExecutionContext
    ): Promise<boolean> {
        if (!this.approvalHandler) {
            console.warn('⚡ No approval handler set, denying dangerous operation');
            return false;
        }

        const preview = await this.generateToolPreview(tool, params, context);
        
        const request: ApprovalRequest = {
            operation: tool.name,
            description: tool.description,
            files: preview,
            dangerLevel: tool.dangerLevel || 'safe',
            canSkipInFuture: tool.dangerLevel !== 'dangerous'
        };

        const response = await this.approvalHandler.requestApproval(request);
        return response.approved;
    }

    /**
     * Generate preview of what the tool will do
     */
    private async generateToolPreview(
        tool: PaletteTool,
        params: any,
        context: ToolExecutionContext
    ): Promise<FilePreview[]> {
        // This is a simplified preview generation
        // In practice, tools might implement their own preview methods
        
        try {
            // For file operations, try to determine what files will be affected
            if (tool.category === 'file-operations') {
                return this.generateFileOperationPreview(params, context);
            }
            
            // For other operations, return minimal preview
            return [{
                path: context.workspacePath || 'unknown',
                operation: 'update',
                content: `Tool: ${tool.name}\nDescription: ${tool.description}`,
                exists: false
            }];
            
        } catch (error) {
            console.warn('⚡ Failed to generate tool preview:', error);
            return [];
        }
    }

    /**
     * Generate preview for file operations
     */
    private generateFileOperationPreview(
        params: any,
        context: ToolExecutionContext
    ): FilePreview[] {
        const previews: FilePreview[] = [];
        
        // Extract file paths from common parameter names
        const possibleFilePaths = [
            params.filePath,
            params.path,
            params.targetPath,
            params.files,
            ...(Array.isArray(params.files) ? params.files : [])
        ].filter(Boolean);

        for (const filePath of possibleFilePaths) {
            previews.push({
                path: filePath,
                operation: params.operation || 'create',
                content: params.content || params.code || '',
                exists: false // Would need to check filesystem
            });
        }

        return previews;
    }

    /**
     * Determine danger level for batch operations
     */
    private getBatchDangerLevel(operations: PendingOperation[]): 'safe' | 'caution' | 'dangerous' {
        let maxDanger: 'safe' | 'caution' | 'dangerous' = 'safe';
        
        for (const op of operations) {
            const tool = this.registry.getTool(op.tool);
            const danger = tool?.dangerLevel || 'safe';
            
            if (danger === 'dangerous') {
                return 'dangerous';
            } else if (danger === 'caution' && maxDanger === 'safe') {
                maxDanger = 'caution';
            }
        }
        
        return maxDanger;
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
     * Log tool execution
     */
    private logExecution(
        toolName: string,
        params: any,
        result: ToolResult,
        executionTime: number
    ): void {
        const log: ToolExecutionLog = {
            toolName,
            timestamp: new Date().toISOString(),
            success: result.success,
            executionTime,
            params,
            result: result.success ? result : undefined,
            error: result.error
        };

        this.registry.logExecution(log);
    }

    /**
     * Get execution statistics
     */
    getExecutionStatistics(): {
        totalExecutions: number;
        successRate: number;
        averageExecutionTime: number;
        activeTools: string[];
        recentErrors: string[];
    } {
        const metrics = this.registry.getMetrics();
        const logs = this.registry.getExecutionLogs(100);
        
        const totalExecutions = metrics.reduce((sum, m) => sum + m.executionCount, 0);
        const totalSuccess = metrics.reduce((sum, m) => sum + m.successCount, 0);
        const avgTime = metrics.length > 0 
            ? metrics.reduce((sum, m) => sum + m.averageExecutionTime, 0) / metrics.length
            : 0;
        
        const activeTools = metrics
            .filter(m => m.executionCount > 0)
            .map(m => m.toolName);
        
        const recentErrors = logs
            .filter(log => !log.success && log.error)
            .slice(0, 10)
            .map(log => `${log.toolName}: ${log.error?.message}`);

        return {
            totalExecutions,
            successRate: totalExecutions > 0 ? (totalSuccess / totalExecutions) * 100 : 0,
            averageExecutionTime: avgTime,
            activeTools,
            recentErrors
        };
    }
}