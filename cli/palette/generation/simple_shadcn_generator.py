"""
Simple shadcn/ui Generator

A streamlined generator focused exclusively on Vite + React + TypeScript + shadcn/ui projects.
This replaces the complex multi-framework UIGenerator with a focused approach.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from openai import OpenAI
import anthropic

from ..analysis.simple_vite_analyzer import SimpleViteAnalyzer
from ..mcp.client import PaletteMCPClient


class SimpleShadcnGenerator:
    """Streamlined generator for shadcn/ui components"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize clients
        self.openai_client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        self.anthropic_client = anthropic.Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None
        
        # Initialize analyzers
        self.vite_analyzer = SimpleViteAnalyzer()
        self.mcp_client = PaletteMCPClient(design_context={"project_path": project_path}) if project_path else None
        
        # Get project context
        self.project_context = self._get_project_context()
        
    def _get_project_context(self) -> Dict[str, Any]:
        """Get simplified project context for generation"""
        if not self.project_path:
            return self._get_default_context()
            
        analysis = self.vite_analyzer.analyze_project(self.project_path)
        return {
            "framework": "vite-react-typescript",
            "ui_library": "shadcn/ui",
            "styling": "tailwind-css",
            "components_directory": "src/components/ui",
            "utils_path": "src/lib/utils",
            "available_components": analysis.get("available_components", []),
            "import_style": "@/components/ui/",
            "typescript": True,
            "css_variables": True
        }
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Default context when no project is specified"""
        return {
            "framework": "vite-react-typescript", 
            "ui_library": "shadcn/ui",
            "styling": "tailwind-css",
            "components_directory": "src/components/ui",
            "utils_path": "src/lib/utils",
            "available_components": [],
            "import_style": "@/components/ui/",
            "typescript": True,
            "css_variables": True
        }
    
    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a shadcn/ui component based on prompt"""
        
        # Merge contexts
        generation_context = {**self.project_context}
        if context:
            generation_context.update(context)
        
        # Build system prompt
        system_prompt = self._build_system_prompt(generation_context)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(prompt, generation_context)
        
        # Try MCP client first for better results
        if self.mcp_client:
            try:
                import asyncio
                try:
                    # Check if we're already in an event loop
                    loop = asyncio.get_running_loop()
                    # If we are, we need to use a different approach
                    # For now, skip MCP and use LLM directly to avoid loop issues
                    print("Already in event loop, using LLM generation")
                except RuntimeError:
                    # No running loop, safe to use asyncio.run
                    mcp_result = asyncio.run(self._try_mcp_generation(prompt, generation_context))
                    if mcp_result:
                        return mcp_result
            except Exception as e:
                print(f"MCP generation failed, falling back to LLM: {e}")
        
        # Fallback to LLM generation
        return self._generate_with_llm(system_prompt, user_prompt, generation_context)
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt for shadcn/ui generation"""
        
        available_components = context.get("available_components", [])
        components_list = ", ".join(available_components) if available_components else "none installed yet"
        
        system_prompt = f"""You are an expert frontend developer specializing in modern React applications with shadcn/ui.

PROJECT CONTEXT:
- Framework: Vite + React + TypeScript
- UI Library: shadcn/ui with Radix UI primitives  
- Styling: Tailwind CSS with CSS variables
- Components: {context.get('components_directory', 'src/components/ui')}
- Utils: {context.get('utils_path', 'src/lib/utils')} (cn utility available)
- Available components: {components_list}

GENERATION REQUIREMENTS:
1. Generate TypeScript (.tsx) components only
2. Use shadcn/ui patterns and conventions
3. Import from "@/components/ui/*" for existing components
4. Use "cn()" utility for className merging
5. Follow shadcn/ui naming conventions (kebab-case files, PascalCase exports)
6. Use Tailwind CSS with semantic color variables
7. Include proper TypeScript interfaces for props
8. Add JSDoc comments for component description
9. Use Radix UI primitives when appropriate
10. Follow accessibility best practices

STYLING GUIDELINES:
- Use Tailwind's semantic color system: bg-background, text-foreground, border-border
- Leverage CSS variables: hsl(var(--primary)), hsl(var(--secondary))
- Use proper spacing scale: p-4, m-2, gap-4
- Include hover, focus, and active states
- Support dark mode with appropriate color variants
- Use proper component size variants (sm, md, lg)

COMPONENT STRUCTURE:
- Export interface for props (ComponentNameProps)
- Use forwardRef for DOM elements when needed
- Include displayName for debugging
- Add default props when appropriate
- Handle edge cases and loading states
"""
        
        return system_prompt
    
    def _build_user_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build user prompt with context"""
        
        user_prompt = f"""Create a component based on this requirement: {prompt}

Please provide:
1. Complete TypeScript component code
2. Usage example showing how to import and use it
3. Any additional components or utilities needed

Format the response as:
```typescript
// Component code here
```

```typescript
// Usage example here
```

Make sure the component follows shadcn/ui patterns and is production-ready."""
        
        return user_prompt
    
    async def _try_mcp_generation(self, prompt: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try generating with MCP shadcn server using 2025 SDK"""
        if not self.mcp_client:
            return None
            
        try:
            # Initialize MCP servers if not already done
            await self.mcp_client.initialize_all_servers()
            
            # Call design tool for component generation  
            result = await self.mcp_client.call_design_tool(
                "generate_component", 
                {
                    "prompt": prompt,
                    "component_type": context.get("component_type"),
                    "style_preference": context.get("style_preference"),
                    "framework": "vite-react-typescript",
                    "ui_library": "shadcn/ui"
                },
                server_name="shadcn-ui"
            )
            
            if result and result.get("success"):
                # Extract content from MCP response
                content = result.get("content", [])
                component_code = ""
                usage_example = ""
                description = ""
                
                for item in content:
                    if item.get("type") == "text":
                        text_content = item.get("content", "")
                        if "```" in text_content:
                            component_code = text_content
                        elif not description:
                            description = text_content
                        elif not usage_example:
                            usage_example = text_content
                
                return {
                    "code": component_code,
                    "usage": usage_example,
                    "description": description,
                    "files": {"component.tsx": component_code},
                    "generator": "mcp-2025"
                }
                
        except Exception as e:
            print(f"MCP 2025 generation error: {e}")
            
        return None
    
    def _generate_with_llm(self, system_prompt: str, user_prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate component using LLM (OpenAI or Anthropic)"""
        
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                content = response.choices[0].message.content
                return self._parse_llm_response(content, context)
                
            except Exception as e:
                print(f"OpenAI generation failed: {e}")
        
        # Try Anthropic as fallback
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                )
                
                content = response.content[0].text
                return self._parse_llm_response(content, context)
                
            except Exception as e:
                print(f"Anthropic generation failed: {e}")
        
        # Fallback response
        return {
            "code": "// Error: No API key available",
            "usage": "// Please set OPENAI_API_KEY or ANTHROPIC_API_KEY",
            "error": "No API clients available",
            "generator": "fallback"
        }
    
    def _parse_llm_response(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response to extract code and usage"""
        
        # Extract code blocks
        import re
        
        code_blocks = re.findall(r'```(?:typescript|tsx?|javascript|jsx?)?\n(.*?)```', content, re.DOTALL)
        
        result = {
            "raw_response": content,
            "generator": "llm"
        }
        
        if code_blocks:
            # First block is usually the component
            result["code"] = code_blocks[0].strip()
            
            # Second block is usually usage example
            if len(code_blocks) > 1:
                result["usage"] = code_blocks[1].strip()
        else:
            # If no code blocks, try to extract the whole response
            result["code"] = content.strip()
        
        # Extract component name if possible
        if "code" in result:
            component_match = re.search(r'(?:export\s+(?:default\s+)?(?:const\s+|function\s+)?)(\w+)', result["code"])
            if component_match:
                result["component_name"] = component_match.group(1)
        
        return result
    
    def get_available_components(self) -> List[str]:
        """Get list of available shadcn/ui components in project"""
        if not self.project_path:
            return []
            
        analysis = self.vite_analyzer.analyze_project(self.project_path)
        return analysis.get("available_components", [])
    
    def install_component(self, component_name: str) -> Dict[str, Any]:
        """Install a shadcn/ui component"""
        if not self.project_path:
            return {"error": "No project path specified"}
        
        try:
            import subprocess
            result = subprocess.run(
                ["npx", "shadcn-ui@latest", "add", component_name],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "component": component_name,
                    "output": result.stdout
                }
            else:
                return {
                    "success": False, 
                    "error": result.stderr,
                    "component": component_name
                }
                
        except Exception as e:
            return {"success": False, "error": str(e), "component": component_name}
    
    def customize_component(self, component_name: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a customized version of an existing component"""
        
        prompt = f"Customize the {component_name} component with these changes: {customizations}"
        
        context = {
            **self.project_context,
            "component_type": "customization",
            "base_component": component_name,
            "customizations": customizations
        }
        
        return self.generate(prompt, context)