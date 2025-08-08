"""
MCP (Model Context Protocol) interface and related data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class MCPServerType(Enum):
    """Types of MCP servers."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    type: MCPServerType
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPTool:
    """An MCP tool provided by a server."""
    name: str
    description: str
    parameters: Dict[str, Any]
    server: str
    
    def get_required_params(self) -> List[str]:
        """Get list of required parameters."""
        if "required" in self.parameters:
            return self.parameters["required"]
        return []


@dataclass
class MCPResource:
    """A resource provided by an MCP server."""
    uri: str
    name: str
    mime_type: str
    server: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResponse:
    """Response from an MCP operation."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    server: Optional[str] = None
    tool: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class IMCPClient(ABC):
    """
    Abstract interface for MCP client implementations.
    Manages connections to MCP servers and tool execution.
    """
    
    @abstractmethod
    async def connect_server(self, config: MCPServerConfig) -> bool:
        """
        Connect to an MCP server.
        
        Args:
            config: Server configuration
            
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    async def disconnect_server(self, server_name: str) -> bool:
        """
        Disconnect from an MCP server.
        
        Args:
            server_name: Name of the server to disconnect
            
        Returns:
            True if disconnection successful
        """
        pass
    
    @abstractmethod
    async def list_tools(self, server_name: Optional[str] = None) -> List[MCPTool]:
        """
        List available tools from connected servers.
        
        Args:
            server_name: Optional server name to filter tools
            
        Returns:
            List of available MCP tools
        """
        pass
    
    @abstractmethod
    async def list_resources(self, server_name: Optional[str] = None) -> List[MCPResource]:
        """
        List available resources from connected servers.
        
        Args:
            server_name: Optional server name to filter resources
            
        Returns:
            List of available MCP resources
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """
        Call an MCP tool with parameters.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            
        Returns:
            MCPResponse with the result
        """
        pass
    
    @abstractmethod
    async def get_resource(self, uri: str) -> MCPResponse:
        """
        Get a resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            MCPResponse with the resource content
        """
        pass
    
    @abstractmethod
    def get_connected_servers(self) -> List[str]:
        """
        Get list of currently connected server names.
        
        Returns:
            List of connected server names
        """
        pass
    
    @abstractmethod
    async def health_check(self, server_name: str) -> bool:
        """
        Check if a server is healthy and responding.
        
        Args:
            server_name: Name of the server to check
            
        Returns:
            True if server is healthy
        """
        pass