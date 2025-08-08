/**
 * Tool Registry
 * Central registry for managing and organizing AI tools
 */

import * as vscode from 'vscode';
import { 
    PaletteTool, 
    ToolCategory, 
    ToolRegistrationOptions, 
    ToolExecutionContext,
    ToolUsageMetrics,
    ToolExecutionLog
} from './types';

export class ToolRegistry {
    private static instance: ToolRegistry | null = null;
    
    private tools: Map<string, PaletteTool> = new Map();
    private toolOptions: Map<string, ToolRegistrationOptions> = new Map();
    private metrics: Map<string, ToolUsageMetrics> = new Map();
    private executionLogs: ToolExecutionLog[] = [];
    
    private constructor() {
        console.log('🔧 Tool Registry initialized');
    }
    
    static getInstance(): ToolRegistry {
        if (!this.instance) {
            this.instance = new ToolRegistry();
        }
        return this.instance;
    }

    /**
     * Register a tool in the registry
     */
    registerTool(tool: PaletteTool, options: ToolRegistrationOptions = {}): void {
        // Validate tool
        if (!tool.name || !tool.description || !tool.inputSchema || !tool.execute) {
            throw new Error(`Invalid tool definition: ${tool.name}`);
        }

        // Check for duplicates
        if (this.tools.has(tool.name)) {
            throw new Error(`Tool already registered: ${tool.name}`);
        }

        // Register tool
        this.tools.set(tool.name, tool);
        this.toolOptions.set(tool.name, options);
        
        // Initialize metrics
        this.metrics.set(tool.name, {
            toolName: tool.name,
            executionCount: 0,
            successCount: 0,
            averageExecutionTime: 0,
            lastUsed: new Date().toISOString(),
            errorTypes: {}
        });

        console.log(`🔧 Registered tool: ${tool.name} (${tool.category})`);
    }

    /**
     * Unregister a tool
     */
    unregisterTool(toolName: string): boolean {
        const removed = this.tools.delete(toolName);
        if (removed) {
            this.toolOptions.delete(toolName);
            this.metrics.delete(toolName);
            console.log(`🔧 Unregistered tool: ${toolName}`);
        }
        return removed;
    }

    /**
     * Get a tool by name
     */
    getTool(toolName: string): PaletteTool | undefined {
        return this.tools.get(toolName);
    }

    /**
     * Get tool options
     */
    getToolOptions(toolName: string): ToolRegistrationOptions | undefined {
        return this.toolOptions.get(toolName);
    }

    /**
     * Get all tools
     */
    getAllTools(): PaletteTool[] {
        return Array.from(this.tools.values());
    }

    /**
     * Get tools by category
     */
    getToolsByCategory(category: ToolCategory): PaletteTool[] {
        return Array.from(this.tools.values()).filter(tool => tool.category === category);
    }

    /**
     * Get enabled tools only
     */
    getEnabledTools(): PaletteTool[] {
        return Array.from(this.tools.values()).filter(tool => {
            const options = this.toolOptions.get(tool.name);
            return options?.enabled !== false; // Default to enabled
        });
    }

    /**
     * Convert tools to AI SDK 5 format
     */
    getToolsForAISDK(): Record<string, any> {
        const aiTools: Record<string, any> = {};
        
        for (const tool of this.getEnabledTools()) {
            aiTools[tool.name] = {
                description: tool.description,
                parameters: tool.inputSchema,
                // Note: execute function will be handled by ToolExecutor
            };
        }
        
        return aiTools;
    }

    /**
     * Check if tool requires approval
     */
    requiresApproval(toolName: string): boolean {
        const tool = this.tools.get(toolName);
        const options = this.toolOptions.get(toolName);
        
        return tool?.requiresApproval === true || 
               options?.requiresApproval === true ||
               tool?.dangerLevel === 'dangerous';
    }

    /**
     * Get tool danger level
     */
    getDangerLevel(toolName: string): 'safe' | 'caution' | 'dangerous' {
        const tool = this.tools.get(toolName);
        return tool?.dangerLevel || 'safe';
    }

    /**
     * Log tool execution
     */
    logExecution(log: ToolExecutionLog): void {
        this.executionLogs.push(log);
        
        // Update metrics
        const metrics = this.metrics.get(log.toolName);
        if (metrics) {
            metrics.executionCount++;
            if (log.success) {
                metrics.successCount++;
            } else if (log.error) {
                const errorType = log.error.code || 'unknown';
                metrics.errorTypes = metrics.errorTypes || {};
                metrics.errorTypes[errorType] = (metrics.errorTypes[errorType] || 0) + 1;
            }
            
            // Update average execution time
            metrics.averageExecutionTime = 
                (metrics.averageExecutionTime * (metrics.executionCount - 1) + log.executionTime) 
                / metrics.executionCount;
            
            metrics.lastUsed = log.timestamp;
        }

        // Limit log size
        if (this.executionLogs.length > 1000) {
            this.executionLogs = this.executionLogs.slice(-500);
        }
    }

    /**
     * Get tool usage metrics
     */
    getMetrics(toolName?: string): ToolUsageMetrics[] {
        if (toolName) {
            const metrics = this.metrics.get(toolName);
            return metrics ? [metrics] : [];
        }
        
        return Array.from(this.metrics.values());
    }

    /**
     * Get recent execution logs
     */
    getExecutionLogs(limit: number = 50, toolName?: string): ToolExecutionLog[] {
        let logs = this.executionLogs.slice(-limit);
        
        if (toolName) {
            logs = logs.filter(log => log.toolName === toolName);
        }
        
        return logs.reverse(); // Most recent first
    }

    /**
     * Enable/disable a tool
     */
    setToolEnabled(toolName: string, enabled: boolean): void {
        const options = this.toolOptions.get(toolName) || {};
        options.enabled = enabled;
        this.toolOptions.set(toolName, options);
        
        console.log(`🔧 Tool ${toolName} ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Clear all tools (for testing)
     */
    clearAll(): void {
        this.tools.clear();
        this.toolOptions.clear();
        this.metrics.clear();
        this.executionLogs = [];
        console.log('🔧 Tool registry cleared');
    }

    /**
     * Get registry statistics
     */
    getStatistics(): {
        totalTools: number;
        enabledTools: number;
        categories: Record<ToolCategory, number>;
        totalExecutions: number;
        successRate: number;
        averageExecutionTime: number;
    } {
        const allTools = Array.from(this.tools.values());
        const enabledTools = this.getEnabledTools();
        
        // Count by category
        const categories: Record<ToolCategory, number> = {
            'file-operations': 0,
            'project-analysis': 0,
            'component-management': 0,
            'git-operations': 0,
            'workspace-management': 0,
            'external-api': 0
        };
        
        allTools.forEach(tool => {
            categories[tool.category]++;
        });

        // Calculate overall metrics
        const allMetrics = Array.from(this.metrics.values());
        const totalExecutions = allMetrics.reduce((sum, m) => sum + m.executionCount, 0);
        const totalSuccess = allMetrics.reduce((sum, m) => sum + m.successCount, 0);
        const avgExecutionTime = allMetrics.length > 0 
            ? allMetrics.reduce((sum, m) => sum + m.averageExecutionTime, 0) / allMetrics.length 
            : 0;

        return {
            totalTools: allTools.length,
            enabledTools: enabledTools.length,
            categories,
            totalExecutions,
            successRate: totalExecutions > 0 ? (totalSuccess / totalExecutions) * 100 : 0,
            averageExecutionTime: avgExecutionTime
        };
    }

    /**
     * Validate tool parameters against schema
     */
    validateToolParams(toolName: string, params: any): { valid: boolean; error?: string } {
        const tool = this.tools.get(toolName);
        if (!tool) {
            return { valid: false, error: `Tool not found: ${toolName}` };
        }

        try {
            tool.inputSchema.parse(params);
            return { valid: true };
        } catch (error: any) {
            return { 
                valid: false, 
                error: `Parameter validation failed: ${error.message}` 
            };
        }
    }

    /**
     * Search tools by name or description
     */
    searchTools(query: string): PaletteTool[] {
        const lowerQuery = query.toLowerCase();
        return Array.from(this.tools.values()).filter(tool => 
            tool.name.toLowerCase().includes(lowerQuery) ||
            tool.description.toLowerCase().includes(lowerQuery)
        );
    }
}