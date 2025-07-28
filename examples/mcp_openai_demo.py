#!/usr/bin/env python3
"""
Demo script showing MCP + OpenAI integration for zero-manual-fixing.
"""

import asyncio
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from palette.openai_integration.assistant import PaletteAssistant
from palette.openai_integration.structured_output import StructuredOutputGenerator
from palette.mcp.client import MCPClient, MCPServerConfig
from palette.quality.zero_fix_pipeline import ZeroFixPipeline


async def demo_mcp_openai_integration():
    """Demonstrate the full MCP + OpenAI integration."""
    
    print("🎨 Palette MCP + OpenAI Integration Demo")
    print("=" * 50)
    
    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Please set your OpenAI API key.")
        return
    
    # Initialize components
    print("🔧 Initializing components...")
    
    # 1. OpenAI Assistant with Code Interpreter
    assistant = PaletteAssistant()
    
    # 2. MCP Client
    mcp_client = MCPClient(openai_assistant=assistant)
    
    # 3. Add design system server
    design_server_config = MCPServerConfig(
        name="design-system",
        type="stdio",
        command="python3",
        args=[str(Path(__file__).parent.parent / "mcp-servers" / "design-system" / "server.py"), "--project", "."],
        enabled=True
    )
    
    print("🔌 Connecting to MCP servers...")
    success = await mcp_client.add_server(design_server_config)
    
    if success:
        print("✅ Connected to design system MCP server")
        
        # List available tools
        tools = mcp_client.list_available_tools("design-system")
        print(f"📚 Available tools: {[tool.name for tool in tools]}")
    else:
        print("⚠️ Could not connect to MCP server, continuing with OpenAI only")
    
    # 4. Initialize Zero-Fix Pipeline
    pipeline = ZeroFixPipeline(
        openai_assistant=assistant,
        mcp_client=mcp_client if success else None,
        project_path="."
    )
    
    print("🚀 Running component generation demo...")
    
    # Example: Generate a button component
    context = {
        "framework": "react",
        "styling": "tailwind",
        "component_library": "none",
        "typescript": True,
        "design_tokens": {
            "colors": ["blue", "gray", "green", "red", "yellow"],
            "spacing": ["2", "4", "6", "8", "12", "16"],
            "typography": ["sm", "base", "lg", "xl", "2xl"]
        }
    }
    
    # Simple component generation
    print("\n📝 Generating component with structured output...")
    generator = StructuredOutputGenerator()
    
    try:
        component = generator.generate_component(
            "Create a Button component with variants (primary, secondary, outline) and sizes (sm, md, lg)",
            context
        )
        
        print("✅ Component generated successfully!")
        print(f"   Name: {component.component_name}")
        print(f"   Props: {len(component.props)} defined")
        print(f"   Dependencies: {component.dependencies}")
        
        # Show code preview
        print("\n📄 Generated component (first 10 lines):")
        code_lines = component.component_code.split('\n')[:10]
        for i, line in enumerate(code_lines, 1):
            print(f"   {i:2d}: {line}")
        
        if len(component.component_code.split('\n')) > 10:
            print("   ... (truncated)")
        
        # Run through zero-fix pipeline
        print("\n🔧 Running through zero-fix pipeline...")
        result = await pipeline.process(component.component_code, context)
        
        print(f"📊 Pipeline Results:")
        print(f"   Success: {'✅' if result.success else '❌'}")
        print(f"   Iterations: {result.iterations}")
        print(f"   Original issues: {result.original_issues}")
        print(f"   Final issues: {result.final_issues}")
        print(f"   Confidence: {result.confidence_score:.2%}")
        print(f"   OpenAI fixes applied: {len(result.openai_fixes)}")
        
        if result.success:
            print("🎉 Component is production-ready with zero manual fixes needed!")
        else:
            print("⚠️ Some issues remain - manual review recommended")
            if result.error:
                print(f"   Error: {result.error}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test MCP tools if available
    if success and mcp_client:
        print("\n🎨 Testing MCP design system tools...")
        
        try:
            # Get design tokens
            tokens_result = await mcp_client.call_tool(
                "design-system",
                "get_design_tokens",
                {"token_type": "colors", "format": "json"}
            )
            
            if tokens_result.get("success"):
                print("✅ Retrieved design tokens via MCP")
                colors = tokens_result["result"]["tokens"].get("colors", {})
                print(f"   Found {len(colors)} color definitions")
            else:
                print(f"⚠️ MCP tool call failed: {tokens_result.get('error')}")
        
        except Exception as e:
            print(f"⚠️ MCP test failed: {e}")
    
    # Cleanup
    if mcp_client:
        await mcp_client.close_all_connections()
    
    print("\n✨ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_mcp_openai_integration())