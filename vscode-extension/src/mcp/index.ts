/**
 * MCP (Model Context Protocol) Integration
 * Exports for MCP server management and tool integration
 */

export * from './types';
export * from './mcp-client';
export * from './mcp-manager';

// Re-export key classes for convenience
export { MCPManager } from './mcp-manager';
export { MCPClientImpl } from './mcp-client';
export type { 
    MCPServerConfig, 
    MCPTool, 
    MCPResource, 
    MCPServerInstance,
    MCPManagerConfig
} from './types';