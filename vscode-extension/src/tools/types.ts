/**
 * Tool System Types
 * Type definitions for the Palette AI tool calling system
 */

import * as vscode from 'vscode';
import { z } from 'zod';

/**
 * Base tool interface for Palette AI
 */
export interface PaletteTool {
    name: string;
    description: string;
    inputSchema: z.ZodSchema<any>;
    execute: (params: any, context: ToolExecutionContext) => Promise<ToolResult>;
    category: ToolCategory;
    requiresApproval?: boolean;
    dangerLevel?: 'safe' | 'caution' | 'dangerous';
}

export type ToolCategory = 
    | 'file-operations'
    | 'project-analysis' 
    | 'component-management'
    | 'git-operations'
    | 'workspace-management'
    | 'external-api';

/**
 * Tool execution context
 */
export interface ToolExecutionContext {
    workspacePath?: string;
    extensionContext: vscode.ExtensionContext;
    outputChannel: vscode.OutputChannel;
    progressToken?: vscode.CancellationToken;
    userApproval?: UserApprovalHandler;
}

/**
 * Tool execution result
 */
export interface ToolResult {
    success: boolean;
    data?: any;
    error?: ToolError;
    requiresUserAction?: boolean;
    followUpSuggestions?: string[];
    filesChanged?: string[];
    metadata?: Record<string, any>;
}

/**
 * Tool execution error
 */
export interface ToolError {
    code: string;
    message: string;
    details?: any;
    recoverable?: boolean;
    suggestedAction?: string;
}

/**
 * User approval handler for dangerous operations
 */
export interface UserApprovalHandler {
    requestApproval(operation: ApprovalRequest): Promise<ApprovalResponse>;
}

export interface ApprovalRequest {
    operation: string;
    description: string;
    files?: FilePreview[];
    dangerLevel: 'safe' | 'caution' | 'dangerous';
    canSkipInFuture?: boolean;
}

export interface ApprovalResponse {
    approved: boolean;
    skipInFuture?: boolean;
    modifiedFiles?: FilePreview[];
}

export interface FilePreview {
    path: string;
    operation: 'create' | 'update' | 'delete';
    content?: string;
    diff?: string;
    exists: boolean;
}

/**
 * File operation specific types
 */
export interface FileOperationResult extends ToolResult {
    filesCreated?: string[];
    filesUpdated?: string[];
    filesDeleted?: string[];
    totalSize?: number;
}

/**
 * Project analysis specific types
 */
export interface ProjectAnalysisResult extends ToolResult {
    framework?: string;
    components?: ComponentInfo[];
    dependencies?: string[];
    structure?: ProjectStructure;
}

export interface ComponentInfo {
    name: string;
    path: string;
    type: 'functional' | 'class' | 'forwardRef';
    props?: PropDefinition[];
    complexity: 'simple' | 'medium' | 'complex';
}

export interface PropDefinition {
    name: string;
    type: string;
    required: boolean;
    description?: string;
}

export interface ProjectStructure {
    srcDir: string;
    componentsDir?: string;
    pagesDir?: string;
    libDir?: string;
}

/**
 * Component installation specific types
 */
export interface ComponentInstallResult extends ToolResult {
    componentsInstalled?: string[];
    dependenciesAdded?: string[];
    configUpdated?: boolean;
}

/**
 * Tool registration types
 */
export interface ToolRegistrationOptions {
    enabled?: boolean;
    requiresApproval?: boolean;
    customValidator?: (params: any) => boolean;
    onBeforeExecute?: (params: any, context: ToolExecutionContext) => Promise<void>;
    onAfterExecute?: (result: ToolResult, context: ToolExecutionContext) => Promise<void>;
}

/**
 * MCP integration types
 */
export interface MCPServerConfig {
    name: string;
    command: string;
    args?: string[];
    env?: Record<string, string>;
    enabled: boolean;
    timeout?: number;
}

export interface MCPTool {
    name: string;
    description?: string;
    inputSchema: any; // JSON schema from MCP
    server: string;
}

/**
 * Batch operations types
 */
export interface BatchOperation {
    id: string;
    operations: PendingOperation[];
    status: 'pending' | 'approved' | 'rejected' | 'completed';
    createdAt: string;
    approvedAt?: string;
}

export interface PendingOperation {
    id: string;
    tool: string;
    params: any;
    preview: FilePreview[];
    approved?: boolean;
    executed?: boolean;
    result?: ToolResult;
}

/**
 * Tool analytics and monitoring types
 */
export interface ToolUsageMetrics {
    toolName: string;
    executionCount: number;
    successCount: number;
    averageExecutionTime: number;
    lastUsed: string;
    errorTypes?: Record<string, number>;
}

export interface ToolExecutionLog {
    toolName: string;
    timestamp: string;
    success: boolean;
    executionTime: number;
    params: any;
    result?: ToolResult;
    error?: ToolError;
}