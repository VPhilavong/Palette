"""
Enhanced generator that uses OpenAI's Remote MCP servers
for real-time code analysis and generation assistance.
"""

from typing import Dict, Optional, List, Any
import os
from openai import OpenAI

from ..mcp.remote_client import RemoteMCPClient
from ..mcp.pattern_analyzer import PatternAnalyzer
from .generator import UIGenerator


class RemoteMCPGenerator(UIGenerator):
    """Generator that leverages OpenAI's Remote MCP servers."""
    
    def __init__(self, *args, use_remote_mcp: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_remote_mcp = use_remote_mcp
        self.remote_mcp_client = None
        self.pattern_analyzer = None
        
        if use_remote_mcp:
            self._setup_remote_mcp()
            self.pattern_analyzer = PatternAnalyzer(self.openai_client)
    
    def _setup_remote_mcp(self):
        """Set up remote MCP servers based on project context."""
        # Auto-discover useful remote servers
        servers = ["deepwiki"]  # Always useful for code analysis
        
        # Add more servers based on project type
        if self.project_path:
            # Could analyze project to determine if e-commerce, etc.
            pass
            
        self.remote_mcp_client = RemoteMCPClient(servers)
        print(f"🌐 Remote MCP enabled with servers: {servers}")
    
    def generate_with_remote_mcp(
        self, 
        prompt: str,
        github_repos: Optional[List[str]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Generate component using OpenAI's Responses API with Remote MCP."""
        
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        # Enhance prompt with GitHub context if repos provided
        enhanced_prompt = prompt
        if github_repos:
            repos_str = ", ".join(github_repos)
            enhanced_prompt = f"""
Generate a React component based on this request: {prompt}

Use these GitHub repositories as reference for code patterns and best practices:
{repos_str}

Analyze their component structure, state management patterns, and styling approaches.
Make the generated component consistent with their patterns.
"""
        
        # Create request with Remote MCP tools
        request_body = RemoteMCPClient.create_responses_request(
            prompt=enhanced_prompt,
            servers=["deepwiki"],
            model=self.model,
            require_approval=False  # DeepWiki is safe
        )
        
        try:
            # Use OpenAI Responses API with MCP
            print("🔍 Analyzing reference repositories with Remote MCP...")
            response = self.openai_client.responses.create(**request_body)
            
            # Extract the generated component
            generated_code = response.output_text
            
            # Save to file if path provided
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(generated_code)
                print(f"✅ Component saved to: {output_path}")
            
            return generated_code
            
        except Exception as e:
            print(f"❌ Remote MCP generation failed: {e}")
            # Fall back to regular generation
            return self.generate(prompt, output_path)
    
    def generate_with_pattern_analysis(
        self,
        prompt: str,
        component_type: Optional[str] = None,
        requirements: Optional[List[str]] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Generate component using pattern analysis from popular libraries."""
        
        if not self.pattern_analyzer:
            return self.generate(prompt, output_path)
        
        # Extract component type from prompt if not provided
        if not component_type:
            component_type = self._extract_component_type(prompt)
        
        print(f"🔍 Analyzing {component_type} patterns from top UI libraries...")
        
        # Find best implementation based on requirements
        if requirements:
            best_impl = self.pattern_analyzer.find_best_implementation(
                component_type, requirements
            )
            recommendation = best_impl["recommendation"]
        else:
            # Analyze patterns from top libraries
            patterns = self.pattern_analyzer.analyze_component_patterns(component_type)
            recommendation = self._summarize_patterns(patterns)
        
        # Create enhanced prompt with pattern knowledge
        enhanced_prompt = f"""
{prompt}

Based on analysis of top UI libraries, here are the best practices:
{recommendation}

Generate a component that incorporates these patterns while matching the local project style.
"""
        
        # Use the enhanced prompt for generation
        return self.generate_with_remote_mcp(
            enhanced_prompt,
            github_repos=[p.repository for p in patterns[:3]] if 'patterns' in locals() else None,
            output_path=output_path
        )
    
    def _extract_component_type(self, prompt: str) -> str:
        """Extract component type from prompt."""
        prompt_lower = prompt.lower()
        
        # Common component types
        component_types = [
            "button", "form", "modal", "table", "card",
            "dropdown", "navigation", "navbar", "sidebar",
            "input", "select", "checkbox", "radio"
        ]
        
        for comp_type in component_types:
            if comp_type in prompt_lower:
                return comp_type
        
        return "component"  # Default
    
    def _summarize_patterns(self, patterns: List) -> str:
        """Summarize patterns from multiple libraries."""
        if not patterns:
            return "No specific patterns found."
        
        summary = []
        for pattern in patterns[:3]:  # Top 3
            summary.append(f"\n{pattern.repository}:")
            summary.append(f"- " + "\n- ".join(pattern.best_practices[:3]))
        
        return "\n".join(summary)
    
    def analyze_with_deepwiki(self, repo: str, question: str) -> str:
        """Use DeepWiki to analyze a GitHub repository."""
        
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
            
        request_body = {
            "model": self.model,
            "tools": [{
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                "require_approval": "never"
            }],
            "input": f"Repository: {repo}\n\nQuestion: {question}"
        }
        
        try:
            response = self.openai_client.responses.create(**request_body)
            return response.output_text
        except Exception as e:
            return f"Analysis failed: {e}"


# Example usage
if __name__ == "__main__":
    # Test Remote MCP integration
    generator = RemoteMCPGenerator(
        project_path=".",
        use_remote_mcp=True
    )
    
    # Example 1: Generate component with repo reference
    result = generator.generate_with_remote_mcp(
        prompt="Create a modern dashboard sidebar component with collapsible sections",
        github_repos=["vercel/next.js", "shadcn/ui"],
        output_path="components/DashboardSidebar.tsx"
    )
    
    print("\n" + "="*60)
    print("Generated Component:")
    print("="*60)
    print(result)
    
    # Example 2: Analyze a repository
    analysis = generator.analyze_with_deepwiki(
        repo="facebook/react",
        question="What patterns does React use for component composition?"
    )
    
    print("\n" + "="*60)
    print("Repository Analysis:")
    print("="*60)
    print(analysis)