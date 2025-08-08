"""
Remote MCP Client for OpenAI's Responses API
Uses OpenAI's native MCP tool support instead of local MCP SDK
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os


@dataclass
class RemoteMCPServer:
    """Configuration for a remote MCP server."""
    server_label: str
    server_url: str
    require_approval: str = "always"  # "always", "never", or dict
    allowed_tools: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None


class RemoteMCPClient:
    """Client for using remote MCP servers with OpenAI's Responses API."""
    
    # Predefined remote MCP servers
    AVAILABLE_SERVERS = {
        "deepwiki": RemoteMCPServer(
            server_label="deepwiki",
            server_url="https://mcp.deepwiki.com/mcp",
            require_approval="never"  # Public server, no auth needed
        ),
        "stripe": RemoteMCPServer(
            server_label="stripe", 
            server_url="https://mcp.stripe.com",
            require_approval="always",
            headers={"Authorization": f"Bearer {os.getenv('STRIPE_API_KEY', '')}"}
        ),
        "cloudflare": RemoteMCPServer(
            server_label="cloudflare",
            server_url="https://mcp.cloudflare.com",
            require_approval="always",
            headers={"Authorization": f"Bearer {os.getenv('CLOUDFLARE_API_KEY', '')}"}
        ),
        "shopify": RemoteMCPServer(
            server_label="shopify",
            server_url="https://shopify.dev/mcp",
            require_approval="always"
        ),
        "zapier": RemoteMCPServer(
            server_label="zapier",
            server_url="https://zapier.com/mcp",
            require_approval="always",
            headers={"Authorization": f"Bearer {os.getenv('ZAPIER_API_KEY', '')}"}
        )
    }
    
    def __init__(self, servers: Optional[List[str]] = None):
        """Initialize with list of server names to enable."""
        self.enabled_servers = servers or []
        
    def get_tools_config(self) -> List[Dict[str, Any]]:
        """Get the tools configuration for OpenAI Responses API."""
        tools = []
        
        for server_name in self.enabled_servers:
            if server_name in self.AVAILABLE_SERVERS:
                server = self.AVAILABLE_SERVERS[server_name]
                
                tool_config = {
                    "type": "mcp",
                    "server_label": server.server_label,
                    "server_url": server.server_url,
                    "require_approval": server.require_approval
                }
                
                if server.allowed_tools:
                    tool_config["allowed_tools"] = server.allowed_tools
                    
                if server.headers:
                    # Only include headers if API keys are actually set
                    filtered_headers = {k: v for k, v in server.headers.items() if v and "Bearer " not in v or len(v) > 7}
                    if filtered_headers:
                        tool_config["headers"] = filtered_headers
                
                tools.append(tool_config)
                
        return tools
    
    def auto_discover_servers(self, project_type: str) -> List[str]:
        """Auto-discover which remote MCP servers would be useful."""
        discovered = []
        
        # DeepWiki is useful for any project that uses GitHub repos
        discovered.append("deepwiki")
        
        # Add more based on project type
        if project_type == "ecommerce":
            discovered.extend(["stripe", "shopify"])
        elif project_type == "automation":
            discovered.append("zapier")
        elif project_type == "infrastructure":
            discovered.append("cloudflare")
            
        return discovered
    
    @staticmethod
    def create_responses_request(
        prompt: str,
        servers: List[str],
        model: str = "gpt-4o",
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """Create a request body for OpenAI Responses API with MCP tools."""
        client = RemoteMCPClient(servers)
        tools = client.get_tools_config()
        
        # Override approval requirement if specified
        if not require_approval:
            for tool in tools:
                tool["require_approval"] = "never"
        
        return {
            "model": model,
            "tools": tools,
            "input": prompt
        }


# Example usage function
def example_remote_mcp_usage():
    """Example of how to use remote MCP with OpenAI."""
    from openai import OpenAI
    
    # Initialize OpenAI client
    client = OpenAI()
    
    # Create remote MCP client with DeepWiki
    mcp_client = RemoteMCPClient(["deepwiki"])
    
    # Create the request
    request_body = RemoteMCPClient.create_responses_request(
        prompt="What design patterns does the React repository use for state management?",
        servers=["deepwiki"],
        require_approval=False  # DeepWiki is safe
    )
    
    # Make the request
    response = client.responses.create(**request_body)
    
    return response.output_text


if __name__ == "__main__":
    # Demo the configuration
    client = RemoteMCPClient(["deepwiki", "stripe"])
    tools = client.get_tools_config()
    
    print("Remote MCP Tools Configuration:")
    for tool in tools:
        print(f"\n{tool['server_label']}:")
        print(f"  URL: {tool['server_url']}")
        print(f"  Approval: {tool['require_approval']}")
        if 'headers' in tool:
            print(f"  Auth: {'Configured' if tool['headers'] else 'Not configured'}")