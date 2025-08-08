"""
Enhanced MCP (Model Context Protocol) client for Palette.
Uses official MCP Python SDK (2025) for connecting to MCP servers.
Optimized for UI/UX design prototyping workflow.
"""

import json
import asyncio
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Official MCP Python SDK (2025) - Required for Palette
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import Tool, Resource, TextContent, ImageContent
    HAS_MCP_SDK = True
except ImportError as e:
    HAS_MCP_SDK = False
    logging.error(f"❌ MCP SDK not installed. Install with: pip install mcp (Error: {e})")
    raise ImportError("MCP SDK is required for Palette to function properly")


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


class PaletteMCPClient:
    """
    Enhanced MCP client optimized for UI/UX design prototyping.
    Manages connections to multiple MCP servers for design tools.
    """
    
    def __init__(self, design_context: Optional[Dict[str, Any]] = None):
        self.design_context = design_context or {}
        self.servers: Dict[str, MCPServerConfig] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, MCPTool] = {}
        self.available_resources: Dict[str, MCPResource] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize design-focused MCP servers
        self._setup_default_servers()
    
    def _setup_default_servers(self):
        """Setup default MCP servers for UI/UX design prototyping"""
        base_path = Path(__file__).parent.parent.parent.parent / "mcp-servers"
        
        default_servers = [
            MCPServerConfig(
                name="shadcn-ui",
                type="stdio", 
                command="python",
                args=[str(base_path / "shadcn-ui-server" / "server.py")],
                enabled=True
            ),
            MCPServerConfig(
                name="design-system",
                type="stdio",
                command="python", 
                args=[str(base_path / "design-system" / "server.py")],
                enabled=True
            ),
            MCPServerConfig(
                name="ui-knowledge",
                type="stdio",
                command="python",
                args=[str(base_path / "ui-knowledge" / "server.py")],
                enabled=True
            )
        ]
        
        for server in default_servers:
            self.servers[server.name] = server
    
    async def initialize_all_servers(self) -> Dict[str, bool]:
        """Initialize all enabled MCP servers for design workflow"""
        results = {}
        
        for server_name, config in self.servers.items():
            if config.enabled:
                results[server_name] = await self.connect_server(server_name)
                
        return results
    
    async def connect_server(self, server_name: str) -> bool:
        """Connect to a specific MCP server using official SDK"""
        if server_name not in self.servers:
            self.logger.error(f"Server {server_name} not configured")
            return False
        
        config = self.servers[server_name]
        
        try:
            if config.type == "stdio":
                return await self._connect_stdio_server_2025(server_name, config)
            else:
                self.logger.error(f"Unsupported server type: {config.type}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _connect_stdio_server_2025(self, server_name: str, config: MCPServerConfig) -> bool:
        """Connect using 2025 MCP SDK - simplified and reliable"""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args or [],
                env=config.env or {}
            )
            
            # Connect using stdio client from SDK
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)
            
            # Initialize the session  
            init_result = await session.initialize()
            self.logger.info(f"✅ Initialized MCP server {server_name}: {init_result.server_info}")
            
            # Store session
            self.sessions[server_name] = session
            
            # Discover capabilities
            await self._discover_server_capabilities_2025(server_name, session)
            
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _discover_server_capabilities_2025(self, server_name: str, session: ClientSession) -> None:
        """Discover tools and resources from MCP server using 2025 SDK"""
        try:
            # List available tools
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                tool_obj = MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=tool.inputSchema.model_dump() if tool.inputSchema else {},
                    server=server_name
                )
                self.available_tools[f"{server_name}.{tool.name}"] = tool_obj
            
            self.logger.info(f"📋 Discovered {len(tools_response.tools)} tools from {server_name}")
            
            # List available resources
            try:
                resources_response = await session.list_resources()
                for resource in resources_response.resources:
                    resource_obj = MCPResource(
                        uri=resource.uri,
                        name=resource.name,
                        mime_type=resource.mimeType or "application/octet-stream",
                        description=resource.description,
                        server=server_name
                    )
                    self.available_resources[resource.uri] = resource_obj
                
                self.logger.info(f"📂 Discovered {len(resources_response.resources)} resources from {server_name}")
            except Exception as e:
                self.logger.warning(f"No resources available from {server_name}: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to discover capabilities for {server_name}: {e}")
    
    async def call_design_tool(self, tool_name: str, arguments: Dict[str, Any], server_name: str = "shadcn-ui") -> Dict[str, Any]:
        """Call a design tool with enhanced context for UI/UX prototyping"""
        full_tool_name = f"{server_name}.{tool_name}"
        
        if full_tool_name not in self.available_tools:
            return {
                "error": f"Design tool {full_tool_name} not available",
                "available_tools": [name for name in self.available_tools.keys() if name.startswith(server_name)]
            }
        
        # Add design context to arguments
        enhanced_arguments = {
            **arguments,
            "design_context": self.design_context
        }
        
        return await self.call_tool(server_name, tool_name, enhanced_arguments)
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server using 2025 SDK"""
        if server_name not in self.sessions:
            return {"error": f"Not connected to server {server_name}"}
        
        session = self.sessions[server_name]
        
        try:
            result = await session.call_tool(tool_name, arguments)
            
            # Process result content
            content_result = []
            for content_item in result.content:
                if isinstance(content_item, TextContent):
                    content_result.append({"type": "text", "content": content_item.text})
                elif isinstance(content_item, ImageContent):
                    content_result.append({"type": "image", "content": content_item.data})
                else:
                    content_result.append({"type": "unknown", "content": str(content_item)})
            
            return {
                "success": True,
                "content": content_result,
                "tool": tool_name,
                "server": server_name
            }
            
        except Exception as e:
            self.logger.error(f"Tool call failed for {server_name}.{tool_name}: {e}")
            return {"error": str(e)}
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get a resource from an MCP server using 2025 SDK"""
        if uri not in self.available_resources:
            return {
                "error": f"Resource {uri} not available",
                "available_resources": list(self.available_resources.keys())
            }
        
        resource = self.available_resources[uri]
        server_name = resource.server
        
        if server_name not in self.sessions:
            return {"error": f"Not connected to server {server_name}"}
        
        session = self.sessions[server_name]
        
        try:
            result = await session.read_resource(uri)
            
            # Process resource content
            content_result = []
            for content_item in result.contents:
                if isinstance(content_item, TextContent):
                    content_result.append({"type": "text", "content": content_item.text})
                elif isinstance(content_item, ImageContent):
                    content_result.append({"type": "image", "content": content_item.data})
                else:
                    content_result.append({"type": "unknown", "content": str(content_item)})
            
            return {
                "success": True,
                "content": content_result,
                "mime_type": resource.mime_type,
                "uri": uri
            }
            
        except Exception as e:
            self.logger.error(f"Resource read failed for {uri}: {e}")
            return {"error": str(e)}
    
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
        # Note: Can't reliably run async cleanup in __del__
        # Connections will be cleaned up by the OS
        pass