/**
 * Tool System for Palette AI
 * Provides AI SDK 5 tool calling integration with VS Code operations
 */

export { ToolRegistry } from './tool-registry';
export { ToolExecutor } from './tool-executor';
export { FileOperationsTools } from './file-operations';
export { ProjectAnalysisTools } from './project-analysis';
export { ShadcnTools } from './shadcn-tools';
export { GitOperationsTools } from './git-operations';

export type {
    PaletteTool,
    ToolResult,
    ToolExecutionContext,
    ToolError,
    FileOperationResult,
    ProjectAnalysisResult,
    ComponentInstallResult
} from './types';

/**
 * Initialize all tool systems
 */
export async function initializeToolSystem(): Promise<void> {
    console.log('🔧 Initializing tool system...');
    
    const { ToolRegistry } = await import('./tool-registry');
    const { FileOperationsTools } = await import('./file-operations');
    const { ProjectAnalysisTools } = await import('./project-analysis');
    const { ShadcnTools } = await import('./shadcn-tools');
    const { GitOperationsTools } = await import('./git-operations');
    
    const registry = ToolRegistry.getInstance();
    
    // Register core tools
    FileOperationsTools.registerAll(registry);
    ProjectAnalysisTools.registerAll(registry);
    ShadcnTools.registerAll(registry);
    GitOperationsTools.registerAll(registry);
    
    console.log('🔧 Tool system initialized');
}