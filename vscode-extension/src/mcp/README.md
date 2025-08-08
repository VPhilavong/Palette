# MCP (Model Context Protocol) Integration

This directory contains a robust MCP server integration system for Palette VSCode extension, designed to handle connection errors gracefully and provide users with fallback functionality.

## Architecture Overview

### Core Components

1. **MCPManager** (`mcp-manager.ts`)
   - Central orchestrator for all MCP server connections
   - Manages server lifecycle (start, stop, restart)
   - Handles health monitoring and auto-reconnection
   - Integrates with tool registry for seamless tool access

2. **MCPConfigManager** (`mcp-config-manager.ts`) 
   - Validates and manages MCP configuration using Zod schemas
   - Handles VS Code settings integration
   - Provides configuration validation and error reporting
   - Supports dynamic configuration updates

3. **MCPFallbackManager** (`mcp-fallback-manager.ts`)
   - Implements graceful degradation when MCP servers are unavailable
   - Provides local implementations of common MCP tools
   - Supports three fallback modes: disabled, graceful, always
   - Maintains tool compatibility during server outages

4. **MCPClientImpl** (`mcp-client.ts`)
   - Enhanced client with exponential backoff retry logic
   - Connection timeout and automatic reconnection
   - Process management and error handling
   - Support for multiple connection attempts

5. **MCPCommands** (`mcp-commands.ts`)
   - User-facing commands for MCP management
   - Status monitoring and server configuration
   - Setup guidance and troubleshooting tools
   - Interactive server management via VS Code UI

## Key Features

### ✅ Robust Error Handling

- **Connection Timeouts**: Configurable timeouts prevent hanging connections
- **Exponential Backoff**: Retry logic with jitter prevents server overload
- **Graceful Degradation**: Automatic fallback to local tools when servers fail
- **User Communication**: Clear error messages and actionable guidance

### ✅ Configuration Management

- **Schema Validation**: Zod schemas ensure configuration correctness
- **VS Code Integration**: Full integration with VS Code settings UI
- **Default Templates**: Pre-configured templates for common servers
- **Dynamic Updates**: Configuration changes apply without restart

### ✅ Fallback System

- **Git Operations**: Uses VS Code Git API when git server unavailable
- **File Operations**: Uses VS Code Workspace API for file access
- **Component Management**: Provides guidance for shadcn/ui operations
- **Tool Compatibility**: Maintains consistent tool interface

### ✅ User Experience

- **Setup Guidance**: Interactive guides for server configuration
- **Status Monitoring**: Real-time server status and statistics
- **Command Integration**: Easy access via Command Palette
- **Error Recovery**: Automatic recovery suggestions and actions

## Configuration Schema

The system uses comprehensive VS Code settings:

```json
{
  "palette.mcp.enabled": true,
  "palette.mcp.servers": [...],
  "palette.mcp.maxRetries": 3,
  "palette.mcp.retryDelay": 5000,
  "palette.mcp.connectionTimeout": 10000,
  "palette.mcp.healthCheckInterval": 30000,
  "palette.mcp.autoRestart": true,
  "palette.mcp.fallbackMode": "graceful",
  "palette.mcp.showSetupGuide": true
}
```

## Usage Examples

### Starting MCP Manager
```typescript
const mcpManager = MCPManager.getInstance();
await mcpManager.start();
```

### Adding a Server Configuration
```typescript
const config: MCPServerConfig = {
  name: 'git',
  description: 'Git operations',
  command: 'npx',
  args: ['-y', '@modelcontextprotocol/server-git'],
  enabled: true,
  autoStart: false
};

await mcpManager.addServerConfig(config);
```

### Using Commands
Users can access MCP functionality via:
- `Palette: MCP Status` - View server status and statistics
- `Palette: Configure MCP` - Open configuration options
- `Palette: Restart MCP` - Restart all servers
- `Palette: MCP Setup Guide` - Interactive setup assistance

## Fallback Modes

### Graceful (Default)
- Uses MCP servers when available
- Falls back to local tools when servers fail
- Shows warnings but continues functioning
- Recommended for most users

### Always
- Always uses fallback tools
- Ignores MCP server status
- Useful for environments without MCP support
- Provides consistent experience

### Disabled
- Requires MCP servers to function
- No fallback tools available
- May reduce functionality when servers fail
- For environments with reliable MCP servers

## Error Scenarios Handled

1. **Server Process Fails to Start**
   - Retry with exponential backoff
   - Enable fallback tools if configured
   - Show user guidance for configuration

2. **Connection Timeout**
   - Configurable timeout prevents hanging
   - Automatic retry with increased delay
   - Fallback activation for continued functionality

3. **Server Disconnects Unexpectedly**
   - Automatic reconnection attempts
   - Health monitoring detects failures
   - Seamless fallback tool registration

4. **Invalid Configuration**
   - Schema validation catches errors early
   - Clear error messages with suggestions
   - Fallback to safe default configuration

5. **Missing Dependencies**
   - Command availability checking
   - User guidance for installation
   - Alternative tool suggestions

## Best Practices

### For Users
1. Start with default configuration and enable servers as needed
2. Use "graceful" fallback mode for reliability
3. Monitor server status regularly via status command
4. Follow setup guide for proper server installation

### For Developers
1. Always handle MCP server unavailability
2. Implement fallback tools for critical functionality
3. Use configuration manager for all settings
4. Provide clear error messages and recovery options

## Future Enhancements

- Server discovery and automatic configuration
- Performance monitoring and optimization
- Advanced fallback tool implementations
- Integration with more MCP server types
- Enhanced logging and debugging tools

This architecture ensures that Palette remains functional even when MCP servers are unavailable, while providing a smooth user experience and clear guidance for setup and troubleshooting.