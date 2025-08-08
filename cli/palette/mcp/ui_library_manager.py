"""
MCP UI Library Manager - Orchestrates UI library-specific MCP servers.
Provides unified interface for UI library detection, server management, and context retrieval.
"""

import asyncio
import subprocess
import sys
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import os

from ..intelligence.ui_library_validator import EnhancedUILibraryValidator
from ..errors.decorators import handle_errors
from .ui_library_server_base import UILibraryType, UIComponent, UILibraryContext


class MCPServerStatus(Enum):
    """Status of MCP server connection."""
    AVAILABLE = "available"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    NOT_FOUND = "not_found"


@dataclass
class MCPServerConnection:
    """Represents a connection to an MCP server."""
    server_type: UILibraryType
    server_path: str
    process: Optional[subprocess.Popen] = None
    status: MCPServerStatus = MCPServerStatus.AVAILABLE
    last_error: Optional[str] = None


class MCPUILibraryManager:
    """
    Manages UI library-specific MCP servers and provides unified interface
    for UI library operations with OpenAI optimization.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.ui_validator = EnhancedUILibraryValidator()
        
        # Server registry
        self.server_connections: Dict[UILibraryType, MCPServerConnection] = {}
        self.active_servers: Dict[UILibraryType, Dict[str, Any]] = {}
        
        # Cache for library detection and context
        self._detected_library = None
        self._library_context_cache: Dict[UILibraryType, UILibraryContext] = {}
        
        # Initialize server paths
        self._initialize_server_paths()
    
    def _initialize_server_paths(self):
        """Initialize paths to MCP server implementations."""
        palette_root = Path(__file__).parent.parent.parent.parent
        mcp_servers_dir = palette_root / "mcp-servers"
        
        # Map UI library types to their MCP server paths
        server_paths = {
            UILibraryType.CHAKRA_UI: mcp_servers_dir / "chakra-ui" / "server.py",
            UILibraryType.MATERIAL_UI: mcp_servers_dir / "material-ui" / "server.py",
            UILibraryType.ANT_DESIGN: mcp_servers_dir / "ant-design" / "server.py",
            UILibraryType.SHADCN_UI: mcp_servers_dir / "shadcn-ui" / "server.py",
            UILibraryType.MANTINE: mcp_servers_dir / "mantine" / "server.py",
        }
        
        # Register available servers
        for lib_type, server_path in server_paths.items():
            if server_path.exists():
                self.server_connections[lib_type] = MCPServerConnection(
                    server_type=lib_type,
                    server_path=str(server_path),
                    status=MCPServerStatus.AVAILABLE
                )
            else:
                print(f"⚠️ MCP server not found for {lib_type.value}: {server_path}")
    
    @handle_errors(reraise=True)
    async def detect_project_ui_library(self) -> Optional[UILibraryType]:
        """
        Detect the primary UI library used in the project.
        
        Returns:
            UILibraryType if detected, None if no clear library found
        """
        if self._detected_library is not None:
            return self._detected_library
        
        print("🔍 Detecting project UI library...")
        
        # Get recommendation from enhanced validator
        recommended_lib = self.ui_validator.get_recommended_ui_library(str(self.project_path))
        
        if not recommended_lib or recommended_lib == 'none':
            print("   No specific UI library detected")
            self._detected_library = None
            return None
        
        # Map string library name to UILibraryType
        library_name_map = {
            'chakra-ui': UILibraryType.CHAKRA_UI,
            'material-ui': UILibraryType.MATERIAL_UI,
            'ant-design': UILibraryType.ANT_DESIGN,
            'shadcn/ui': UILibraryType.SHADCN_UI,
            'mantine': UILibraryType.MANTINE,
            'react-bootstrap': UILibraryType.REACT_BOOTSTRAP,
            'headless-ui': UILibraryType.TAILWIND_UI,
        }
        
        detected_type = library_name_map.get(recommended_lib)
        if detected_type:
            print(f"   Detected UI library: {detected_type.value}")
            self._detected_library = detected_type
            return detected_type
        
        print(f"   Unknown library type: {recommended_lib}")
        return None
    
    @handle_errors(reraise=True)
    async def validate_library_compatibility(self, library_type: UILibraryType) -> Dict[str, Any]:
        """
        Validate compatibility of a specific UI library with the project.
        
        Args:
            library_type: UI library type to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = self.ui_validator.validate_ui_library_choice(
            library_type.value, str(self.project_path)
        )
        
        return {
            "library": library_type.value,
            "compatibility": validation_result.compatibility.value,
            "confidence": validation_result.confidence,
            "evidence": validation_result.evidence,
            "warnings": validation_result.warnings,
            "recommendations": validation_result.recommendations,
            "missing_dependencies": validation_result.missing_dependencies,
            "conflicting_systems": validation_result.conflicting_systems
        }
    
    @handle_errors(reraise=True)
    async def start_library_server(self, library_type: UILibraryType) -> bool:
        """
        Start the MCP server for a specific UI library.
        
        Args:
            library_type: UI library type to start server for
            
        Returns:
            True if server started successfully, False otherwise
        """
        if library_type not in self.server_connections:
            print(f"❌ No MCP server available for {library_type.value}")
            return False
        
        connection = self.server_connections[library_type]
        
        if connection.status == MCPServerStatus.RUNNING:
            print(f"✅ MCP server for {library_type.value} already running")
            return True
        
        print(f"🚀 Starting MCP server for {library_type.value}...")
        
        try:
            connection.status = MCPServerStatus.STARTING
            
            # Start the server process
            connection.process = subprocess.Popen(
                [sys.executable, connection.server_path, "--project", str(self.project_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Wait for initialization
            await asyncio.sleep(0.5)
            
            # Check if process is still running
            if connection.process.poll() is None:
                connection.status = MCPServerStatus.RUNNING
                print(f"✅ MCP server for {library_type.value} started successfully")
                
                # Initialize server communication
                await self._initialize_server_communication(library_type)
                return True
            else:
                error_output = connection.process.stderr.read() if connection.process.stderr else "Unknown error"
                connection.last_error = error_output
                connection.status = MCPServerStatus.ERROR
                print(f"❌ Failed to start MCP server for {library_type.value}: {error_output}")
                return False
                
        except Exception as e:
            connection.last_error = str(e)
            connection.status = MCPServerStatus.ERROR
            print(f"❌ Error starting MCP server for {library_type.value}: {e}")
            return False
    
    async def _initialize_server_communication(self, library_type: UILibraryType):
        """Initialize communication with the MCP server."""
        connection = self.server_connections[library_type]
        
        try:
            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            }
            
            connection.process.stdin.write(json.dumps(init_request) + "\n")
            connection.process.stdin.flush()
            
            # Read initialization response
            response_line = connection.process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                if "result" in response:
                    self.active_servers[library_type] = response["result"]
                    print(f"   Server {library_type.value} initialized: {response['result']['server_info']['name']}")
        
        except Exception as e:
            print(f"⚠️ Failed to initialize communication with {library_type.value} server: {e}")
    
    @handle_errors(reraise=True)
    async def get_library_context(self, library_type: UILibraryType) -> Optional[UILibraryContext]:
        """
        Get comprehensive context for a UI library.
        
        Args:
            library_type: UI library type to get context for
            
        Returns:
            UILibraryContext if available, None otherwise
        """
        # Check cache first
        if library_type in self._library_context_cache:
            return self._library_context_cache[library_type]
        
        # Ensure server is running
        if not await self.start_library_server(library_type):
            return None
        
        try:
            # Get component catalog
            components = await self._call_server_tool(library_type, "get_component_info", {"component_name": "all"})
            
            # Get design tokens
            design_tokens = await self._read_server_resource(library_type, f"ui-library://{library_type.value}/design-tokens")
            
            # Get OpenAI system prompt
            system_prompt = await self._read_server_resource(library_type, f"ui-library://{library_type.value}/openai/system-prompt")
            
            # Get OpenAI examples
            examples = await self._read_server_resource(library_type, f"ui-library://{library_type.value}/openai/examples")
            
            # Build context
            context = UILibraryContext(
                library_type=library_type,
                version="latest",  # Could be enhanced to detect actual version
                components=components or [],
                design_tokens=design_tokens or {},
                theme_config={},
                installation_guide="",
                best_practices=[],
                common_patterns=[],
                typescript_support=True,
                openai_system_prompt=system_prompt or "",
                openai_examples=examples or []
            )
            
            # Cache the context
            self._library_context_cache[library_type] = context
            return context
            
        except Exception as e:
            print(f"❌ Failed to get context for {library_type.value}: {e}")
            return None
    
    async def _call_server_tool(self, library_type: UILibraryType, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        connection = self.server_connections.get(library_type)
        if not connection or connection.status != MCPServerStatus.RUNNING:
            return None
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            connection.process.stdin.write(json.dumps(request) + "\n")
            connection.process.stdin.flush()
            
            response_line = connection.process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                return response.get("result")
        
        except Exception as e:
            print(f"⚠️ Error calling tool {tool_name} on {library_type.value} server: {e}")
            return None
    
    async def _read_server_resource(self, library_type: UILibraryType, uri: str) -> Any:
        """Read a resource from the MCP server."""
        connection = self.server_connections.get(library_type)
        if not connection or connection.status != MCPServerStatus.RUNNING:
            return None
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {
                    "uri": uri
                }
            }
            
            connection.process.stdin.write(json.dumps(request) + "\n")
            connection.process.stdin.flush()
            
            response_line = connection.process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                result = response.get("result", {})
                contents = result.get("contents", [])
                if contents and contents[0].get("type") == "text":
                    text_content = contents[0]["text"]
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return text_content
        
        except Exception as e:
            print(f"⚠️ Error reading resource {uri} from {library_type.value} server: {e}")
            return None
    
    @handle_errors(reraise=True)
    async def generate_openai_prompt(self, 
                                   user_request: str,
                                   library_type: Optional[UILibraryType] = None,
                                   component_type: Optional[str] = None,
                                   complexity_level: str = "intermediate") -> Dict[str, Any]:
        """
        Generate OpenAI-optimized prompt with UI library context.
        
        Args:
            user_request: User's component generation request
            library_type: UI library to use (auto-detected if None)
            component_type: Type of component requested
            complexity_level: Complexity level for generation
            
        Returns:
            Dictionary with system prompt, user prompt, and context
        """
        # Auto-detect library if not specified
        if library_type is None:
            library_type = await self.detect_project_ui_library()
        
        # If no UI library detected or available, use generic prompts
        if library_type is None or library_type not in self.server_connections:
            return {
                "system_prompt": self._get_generic_system_prompt(),
                "enhanced_user_prompt": self._enhance_generic_user_prompt(
                    user_request, component_type, complexity_level
                ),
                "library_context": "generic",
                "complexity_level": complexity_level,
                "relevant_examples": 0
            }
        
        # Use library-specific MCP server
        if not await self.start_library_server(library_type):
            # Fallback to generic if server fails
            return await self.generate_openai_prompt(user_request, None, component_type, complexity_level)
        
        # Call the server to generate optimized prompt
        prompt_result = await self._call_server_tool(
            library_type,
            "generate_openai_prompt",
            {
                "user_request": user_request,
                "component_type": component_type,
                "complexity_level": complexity_level
            }
        )
        
        if prompt_result:
            return prompt_result
        
        # Fallback to generic if server call fails
        return await self.generate_openai_prompt(user_request, None, component_type, complexity_level)
    
    def _get_generic_system_prompt(self) -> str:
        """Get generic system prompt when no UI library is available."""
        return """You are an expert React developer who creates high-quality, accessible, and responsive React components. 

**Component Standards:**
- Write TypeScript by default with proper prop interfaces
- Use semantic HTML and proper ARIA attributes for accessibility
- Implement responsive design with mobile-first approach
- Follow React best practices and hooks guidelines
- Use consistent naming conventions (PascalCase for components)

**Code Quality:**
- Export components as default exports
- Include proper imports and dependencies
- Add helpful comments for complex logic
- Handle edge cases and error states
- Implement proper loading and error states

**Styling Approach:**
- Use CSS modules, styled-components, or utility classes as appropriate
- Maintain visual hierarchy with proper spacing and typography
- Apply consistent color schemes and design patterns
- Ensure good color contrast for accessibility

Generate clean, production-ready code that follows modern React standards."""
    
    def _enhance_generic_user_prompt(self, user_request: str, component_type: str = None, complexity_level: str = "intermediate") -> str:
        """Enhance user prompt with generic context."""
        enhanced_prompt = f"User request: {user_request}\n\n"
        
        if component_type:
            enhanced_prompt += f"Component type: {component_type}\n"
        
        enhanced_prompt += f"Complexity level: {complexity_level}\n\n"
        enhanced_prompt += f"Generate a {complexity_level} {component_type or 'component'} using modern React patterns and TypeScript."
        
        return enhanced_prompt
    
    @handle_errors(reraise=True)
    async def validate_component_with_library(self, 
                                            component_code: str,
                                            library_type: Optional[UILibraryType] = None) -> Dict[str, Any]:
        """
        Validate component code against UI library-specific rules.
        
        Args:
            component_code: Component code to validate
            library_type: UI library to validate against (auto-detected if None)
            
        Returns:
            Validation result dictionary
        """
        # Auto-detect library if not specified
        if library_type is None:
            library_type = await self.detect_project_ui_library()
        
        # If no library detected, perform generic validation
        if library_type is None or library_type not in self.server_connections:
            return {
                "valid": True,
                "score": 75,
                "issues": [],
                "suggestions": ["Consider using a UI library for better consistency"],
                "library": "generic"
            }
        
        # Start library server
        if not await self.start_library_server(library_type):
            return {"error": f"Failed to start server for {library_type.value}"}
        
        # Validate using library-specific server
        validation_result = await self._call_server_tool(
            library_type,
            "validate_library_usage",
            {
                "component_code": component_code,
                "strict_mode": False
            }
        )
        
        return validation_result or {"error": "Validation failed"}
    
    @handle_errors(reraise=True)
    async def get_component_suggestions(self, 
                                      query: str,
                                      library_type: Optional[UILibraryType] = None) -> Dict[str, Any]:
        """
        Search for component suggestions from the UI library.
        
        Args:
            query: Search query for components
            library_type: UI library to search (auto-detected if None)
            
        Returns:
            Dictionary with search results
        """
        # Auto-detect library if not specified
        if library_type is None:
            library_type = await self.detect_project_ui_library()
        
        if library_type is None or library_type not in self.server_connections:
            return {
                "query": query,
                "library": "none",
                "results": [],
                "message": "No UI library detected - consider adding one for better suggestions"
            }
        
        # Start library server
        if not await self.start_library_server(library_type):
            return {"error": f"Failed to start server for {library_type.value}"}
        
        # Search components using library-specific server
        search_result = await self._call_server_tool(
            library_type,
            "search_components",
            {
                "query": query,
                "limit": 10
            }
        )
        
        return search_result or {"error": "Search failed"}
    
    async def shutdown_all_servers(self):
        """Shutdown all running MCP servers."""
        print("🔌 Shutting down MCP servers...")
        
        for library_type, connection in self.server_connections.items():
            if connection.process and connection.status == MCPServerStatus.RUNNING:
                try:
                    connection.process.terminate()
                    await asyncio.sleep(0.1)
                    if connection.process.poll() is None:
                        connection.process.kill()
                    connection.status = MCPServerStatus.AVAILABLE
                    print(f"   Stopped {library_type.value} server")
                except Exception as e:
                    print(f"   Error stopping {library_type.value} server: {e}")
        
        self.active_servers.clear()
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        status = {}
        
        for library_type, connection in self.server_connections.items():
            status[library_type.value] = {
                "status": connection.status.value,
                "server_path": connection.server_path,
                "last_error": connection.last_error,
                "is_running": connection.status == MCPServerStatus.RUNNING
            }
        
        return {
            "servers": status,
            "detected_library": self._detected_library.value if self._detected_library else None,
            "total_servers": len(self.server_connections),
            "running_servers": len([c for c in self.server_connections.values() if c.status == MCPServerStatus.RUNNING])
        }