"""
Core MCP (Model Context Protocol) client for connecting to MCP servers.
Integrates with OpenAI Assistant for enhanced processing.
"""

import json
import asyncio
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# MCP-related imports (these would come from the official MCP Python SDK)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False
    print("⚠️ MCP SDK not installed. Install with: pip install mcp")


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    type: str  # "stdio" or "http"
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30
    enabled: bool = True


@dataclass
class MCPTool:
    """Represents an MCP tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    server: str


@dataclass
class MCPResource:
    """Represents an MCP resource."""
    uri: str
    name: str
    mime_type: str
    server: str
    description: Optional[str] = None


class MCPClient:
    """Main MCP client for managing connections to multiple MCP servers."""
    
    def __init__(self, openai_assistant=None, servers=None):
        self.openai_assistant = openai_assistant
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connections: Dict[str, Any] = {}
        self.available_tools: Dict[str, MCPTool] = {}
        self.available_resources: Dict[str, MCPResource] = {}
        self.logger = logging.getLogger(__name__)
        self.fallback_mode = not HAS_MCP_SDK
        
        if not HAS_MCP_SDK:
            self.logger.warning("MCP SDK not available. Using fallback mode.")
        
        # Add servers if provided
        if servers:
            for server in servers:
                self.servers[server.name] = server
    
    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add and connect to an MCP server."""
        self.servers[config.name] = config
        
        if config.enabled:
            return await self.connect_server(config.name)
        return True
    
    async def connect_server(self, server_name: str) -> bool:
        """Connect to a specific MCP server."""
        if server_name not in self.servers:
            self.logger.error(f"Server {server_name} not configured")
            return False
        
        config = self.servers[server_name]
        
        try:
            if config.type == "stdio":
                return await self._connect_stdio_server(server_name, config)
            elif config.type == "http":
                return await self._connect_http_server(server_name, config)
            else:
                self.logger.error(f"Unsupported server type: {config.type}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _connect_stdio_server(self, server_name: str, config: MCPServerConfig) -> bool:
        """Connect to an MCP server via stdio."""
        if not HAS_MCP_SDK:
            # Fallback implementation without official SDK
            return await self._connect_stdio_fallback(server_name, config)
        
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env or {}
            )
            
            # Connect using stdio client
            async with stdio_client(server_params) as (read, write):
                session = ClientSession(read, write)
                
                # Initialize the session
                init_result = await session.initialize()
                
                # Store connection
                self.connections[server_name] = session
                
                # Discover tools and resources
                await self._discover_server_capabilities(server_name, session)
                
                self.logger.info(f"✅ Connected to MCP server: {server_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to connect to stdio server {server_name}: {e}")
            return False
    
    async def _connect_stdio_fallback(self, server_name: str, config: MCPServerConfig) -> bool:
        """Fallback stdio connection without official MCP SDK."""
        try:
            # Start the server process
            cmd = [config.command] + (config.args or [])
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=config.env
            )
            
            # Store the process as connection
            self.connections[server_name] = {
                "type": "stdio_fallback",
                "process": process,
                "config": config
            }
            
            # Try to initialize with basic MCP handshake
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "palette",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send initialization
            message_data = json.dumps(init_message) + "\n"
            process.stdin.write(message_data.encode())
            await process.stdin.drain()
            
            # Read response (with timeout)
            try:
                response_data = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=config.timeout
                )
                
                if response_data:
                    response = json.loads(response_data.decode().strip())
                    if response.get("result"):
                        self.logger.info(f"✅ Connected to MCP server (fallback): {server_name}")
                        
                        # Discover capabilities
                        await self._discover_capabilities_fallback(server_name)
                        return True
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout connecting to {server_name}")
                
        except Exception as e:
            self.logger.error(f"Fallback connection failed for {server_name}: {e}")
            
        return False
    
    async def _connect_http_server(self, server_name: str, config: MCPServerConfig) -> bool:
        """Connect to an MCP server via HTTP."""
        # HTTP implementation would use aiohttp or similar
        self.logger.info(f"HTTP MCP servers not yet implemented for {server_name}")
        return False
    
    async def _discover_server_capabilities(self, server_name: str, session) -> None:
        """Discover tools and resources from an MCP server."""
        try:
            # List tools
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                tool_obj = MCPTool(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema,
                    server=server_name
                )
                self.available_tools[f"{server_name}.{tool.name}"] = tool_obj
            
            # List resources
            resources_result = await session.list_resources()
            for resource in resources_result.resources:
                resource_obj = MCPResource(
                    uri=resource.uri,
                    name=resource.name,
                    mime_type=resource.mimeType or "application/octet-stream",
                    description=resource.description,
                    server=server_name
                )
                self.available_resources[resource.uri] = resource_obj
                
        except Exception as e:
            self.logger.error(f"Failed to discover capabilities for {server_name}: {e}")
    
    async def _discover_capabilities_fallback(self, server_name: str) -> None:
        """Discover capabilities using fallback method."""
        connection = self.connections.get(server_name)
        if not connection or connection["type"] != "stdio_fallback":
            return
        
        process = connection["process"]
        
        try:
            # List tools
            tools_message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            message_data = json.dumps(tools_message) + "\n"
            process.stdin.write(message_data.encode())
            await process.stdin.drain()
            
            # Read tools response
            response_data = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10
            )
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                if "result" in response and "tools" in response["result"]:
                    for tool_data in response["result"]["tools"]:
                        tool_obj = MCPTool(
                            name=tool_data["name"],
                            description=tool_data.get("description", ""),
                            parameters=tool_data.get("inputSchema", {}),
                            server=server_name
                        )
                        self.available_tools[f"{server_name}.{tool_data['name']}"] = tool_obj
            
            # List resources
            resources_message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {}
            }
            
            message_data = json.dumps(resources_message) + "\n"
            process.stdin.write(message_data.encode())
            await process.stdin.drain()
            
            # Read resources response
            response_data = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=10
            )
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                if "result" in response and "resources" in response["result"]:
                    for resource_data in response["result"]["resources"]:
                        resource_obj = MCPResource(
                            uri=resource_data["uri"],
                            name=resource_data["name"],
                            mime_type=resource_data.get("mimeType", "application/octet-stream"),
                            description=resource_data.get("description"),
                            server=server_name
                        )
                        self.available_resources[resource_data["uri"]] = resource_obj
                        
        except Exception as e:
            self.logger.error(f"Failed to discover capabilities (fallback) for {server_name}: {e}")
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on an MCP server."""
        full_tool_name = f"{server_name}.{tool_name}"
        
        if full_tool_name not in self.available_tools:
            return {
                "error": f"Tool {full_tool_name} not available",
                "available_tools": list(self.available_tools.keys())
            }
        
        if server_name not in self.connections:
            return {"error": f"Not connected to server {server_name}"}
        
        try:
            connection = self.connections[server_name]
            
            if isinstance(connection, dict) and connection.get("type") == "stdio_fallback":
                return await self._call_tool_fallback(server_name, tool_name, arguments)
            else:
                # Use official SDK
                result = await connection.call_tool(tool_name, arguments)
                return {"success": True, "result": result.content}
                
        except Exception as e:
            self.logger.error(f"Tool call failed for {full_tool_name}: {e}")
            return {"error": str(e)}
    
    async def _call_tool_fallback(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool using fallback method."""
        connection = self.connections[server_name]
        process = connection["process"]
        
        try:
            # Prepare tool call message
            tool_message = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Send message
            message_data = json.dumps(tool_message) + "\n"
            process.stdin.write(message_data.encode())
            await process.stdin.drain()
            
            # Read response
            response_data = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30
            )
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                if "result" in response:
                    return {"success": True, "result": response["result"]}
                elif "error" in response:
                    return {"error": response["error"]}
            
            return {"error": "No response from server"}
            
        except Exception as e:
            return {"error": f"Tool call failed: {str(e)}"}
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get a resource from an MCP server."""
        if uri not in self.available_resources:
            return {
                "error": f"Resource {uri} not available",
                "available_resources": list(self.available_resources.keys())
            }
        
        resource = self.available_resources[uri]
        server_name = resource.server
        
        if server_name not in self.connections:
            return {"error": f"Not connected to server {server_name}"}
        
        try:
            connection = self.connections[server_name]
            
            if isinstance(connection, dict) and connection.get("type") == "stdio_fallback":
                return await self._get_resource_fallback(uri, resource)
            else:
                # Use official SDK
                result = await connection.read_resource(uri)
                return {
                    "success": True,
                    "content": result.contents,
                    "mime_type": resource.mime_type
                }
                
        except Exception as e:
            self.logger.error(f"Resource read failed for {uri}: {e}")
            return {"error": str(e)}
    
    async def _get_resource_fallback(self, uri: str, resource: MCPResource) -> Dict[str, Any]:
        """Get resource using fallback method."""
        connection = self.connections[resource.server]
        process = connection["process"]
        
        try:
            # Prepare resource read message
            resource_message = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "resources/read",
                "params": {
                    "uri": uri
                }
            }
            
            # Send message
            message_data = json.dumps(resource_message) + "\n"
            process.stdin.write(message_data.encode())
            await process.stdin.drain()
            
            # Read response
            response_data = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30
            )
            
            if response_data:
                response = json.loads(response_data.decode().strip())
                if "result" in response:
                    return {
                        "success": True,
                        "content": response["result"].get("contents", []),
                        "mime_type": resource.mime_type
                    }
                elif "error" in response:
                    return {"error": response["error"]}
            
            return {"error": "No response from server"}
            
        except Exception as e:
            return {"error": f"Resource read failed: {str(e)}"}
    
    async def call_tool_with_ai(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an MCP tool and enhance the result with OpenAI processing."""
        # First call the MCP tool
        mcp_result = await self.call_tool(server_name, tool_name, arguments)
        
        # If we have an OpenAI assistant, enhance the result
        if self.openai_assistant and mcp_result.get("success"):
            try:
                enhanced_result = await self.openai_assistant.process_mcp_result(mcp_result)
                return {
                    "success": True,
                    "mcp_result": mcp_result,
                    "ai_enhanced": enhanced_result,
                    "enhanced": True
                }
            except Exception as e:
                self.logger.warning(f"AI enhancement failed: {e}")
                return mcp_result
        
        return mcp_result
    
    async def search_resources(
        self, 
        server_name: str, 
        query: str,
        resource_type: Optional[str] = None
    ) -> List[MCPResource]:
        """Search for resources matching a query."""
        matching_resources = []
        
        for uri, resource in self.available_resources.items():
            if resource.server != server_name:
                continue
            
            # Simple text matching
            if (query.lower() in resource.name.lower() or 
                (resource.description and query.lower() in resource.description.lower())):
                
                if resource_type is None or resource.mime_type.startswith(resource_type):
                    matching_resources.append(resource)
        
        return matching_resources
    
    def list_available_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """List all available tools, optionally filtered by server."""
        if server_name:
            return [tool for tool in self.available_tools.values() 
                   if tool.server == server_name]
        return list(self.available_tools.values())
    
    def list_available_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """List all available resources, optionally filtered by server."""
        if server_name:
            return [resource for resource in self.available_resources.values() 
                   if resource.server == server_name]
        return list(self.available_resources.values())
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured servers."""
        status = {}
        
        for server_name, config in self.servers.items():
            status[server_name] = {
                "configured": True,
                "enabled": config.enabled,
                "connected": server_name in self.connections,
                "type": config.type,
                "tools_count": len([t for t in self.available_tools.values() 
                                  if t.server == server_name]),
                "resources_count": len([r for r in self.available_resources.values() 
                                      if r.server == server_name])
            }
        
        return status
    
    def disconnect_server(self, server_name: str) -> bool:
        """Disconnect from an MCP server."""
        if server_name not in self.connections:
            return False
        
        try:
            connection = self.connections[server_name]
            
            if isinstance(connection, dict) and connection.get("type") == "stdio_fallback":
                # Terminate the process
                process = connection["process"]
                process.terminate()
            
            # Remove from connections
            del self.connections[server_name]
            
            # Remove associated tools and resources
            tools_to_remove = [key for key, tool in self.available_tools.items() 
                             if tool.server == server_name]
            for key in tools_to_remove:
                del self.available_tools[key]
            
            resources_to_remove = [uri for uri, resource in self.available_resources.items() 
                                 if resource.server == server_name]
            for uri in resources_to_remove:
                del self.available_resources[uri]
            
            self.logger.info(f"Disconnected from MCP server: {server_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect from {server_name}: {e}")
            return False
    
    async def close_all_connections(self):
        """Close all MCP server connections."""
        server_names = list(self.connections.keys())
        for server_name in server_names:
            self.disconnect_server(server_name)
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            asyncio.create_task(self.close_all_connections())
        except:
            pass