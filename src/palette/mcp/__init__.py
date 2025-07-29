"""
Model Context Protocol (MCP) integration for Palette.
Provides access to design tools, component libraries, and other resources.
"""

from .client import MCPClient
from .registry import MCPServerRegistry

__all__ = [
    "MCPClient",
    "MCPServerRegistry"
]