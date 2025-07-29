#!/usr/bin/env python3
"""Test MCP integration from external directory."""

import os
import sys
import asyncio
from pathlib import Path

# Add Palette to path
palette_dir = Path(__file__).parent
sys.path.insert(0, str(palette_dir))

from src.palette.generation.enhanced_generator import EnhancedUIGenerator


async def test_mcp_integration():
    """Test MCP integration with enhanced generator."""
    print("🧪 Testing MCP Integration...")
    print(f"Running from: {os.getcwd()}")
    print(f"Palette directory: {palette_dir}")
    
    # Initialize generator
    gen = EnhancedUIGenerator(
        model="gpt-4o-mini",
        project_path=".",
        enhanced_mode=True,
        quality_assurance=True
    )
    
    print(f"\n✅ Generator initialized")
    print(f"MCP Client: {gen.mcp_client}")
    print(f"MCP Registry servers: {list(gen.mcp_registry.servers.keys())}")
    print(f"MCP servers found: {len(gen.mcp_registry.servers)}")
    
    # List enabled servers
    enabled_servers = [name for name, server in gen.mcp_registry.servers.items() if server.enabled]
    print(f"\n🟢 Enabled servers: {enabled_servers}")
    
    # Test MCP functionality if available
    if gen.mcp_client and not gen.mcp_client.fallback_mode:
        print("\n🔌 Testing MCP server connections...")
        
        # Try to connect to servers
        for server_name in enabled_servers[:3]:  # Test first 3
            try:
                result = await gen.mcp_client.connect_server(server_name)
                if result:
                    print(f"  ✅ Connected to {server_name}")
                else:
                    print(f"  ❌ Failed to connect to {server_name}")
            except Exception as e:
                print(f"  ❌ Error connecting to {server_name}: {e}")
        
        # Test tool call
        if "ui-knowledge" in enabled_servers:
            print("\n🛠️ Testing tool call to ui-knowledge server...")
            try:
                result = await gen.mcp_client.call_tool(
                    "ui-knowledge",
                    "get_component_patterns",
                    {
                        "component_type": "button",
                        "framework": "react",
                        "requirements": ["primary", "accessible"]
                    }
                )
                print(f"  ✅ Tool call successful: {result.get('status', 'unknown')}")
            except Exception as e:
                print(f"  ❌ Tool call failed: {e}")
    else:
        print("\n⚠️ MCP in fallback mode - skipping connection tests")
        
        # Test fallback functionality
        if gen.mcp_client:
            print("\n🔄 Testing fallback mode...")
            try:
                result = await gen.mcp_client.call_tool(
                    "ui-knowledge",
                    "get_component_patterns",
                    {
                        "component_type": "button",
                        "framework": "react",
                        "requirements": ["primary", "accessible"]
                    }
                )
                print(f"  ✅ Fallback tool call successful")
                if result.get("data"):
                    print(f"  📦 Received data with {len(result['data'])} keys")
            except Exception as e:
                print(f"  ❌ Fallback tool call failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp_integration())