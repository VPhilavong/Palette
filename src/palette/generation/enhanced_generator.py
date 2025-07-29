"""
Enhanced UI Generator with Professional Frontend MCP Integration.
Integrates UI Knowledge, Code Analysis, and Design Enforcement for professional-grade components.
"""

from typing import Dict, Optional, Tuple, List, Any
import asyncio
import os
from pathlib import Path
from ..mcp.client import MCPClient
from ..mcp.registry import MCPServerRegistry
from .generator import UIGenerator
from ..quality import QualityReport


class EnhancedUIGenerator(UIGenerator):
    """Enhanced generator that leverages frontend MCP servers for professional output."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_client = None
        self.mcp_registry = MCPServerRegistry()
        self._setup_mcp_servers()
    
    def _setup_mcp_servers(self):
        """Set up the professional frontend MCP servers."""
        # Find MCP servers - check project directory first, then Palette installation
        mcp_path = None
        if (Path(self.project_path) / "mcp-servers").exists():
            mcp_path = Path(self.project_path) / "mcp-servers"
        else:
            # Check Palette installation directory
            palette_dir = Path(__file__).parent.parent.parent.parent
            if (palette_dir / "mcp-servers").exists():
                mcp_path = palette_dir / "mcp-servers"
        
        if not mcp_path:
            print("⚠️ MCP servers not found")
            return
        
        # Register our custom MCP servers
        servers_to_register = [
            {
                "name": "ui-knowledge",
                "command": "python",
                "args": [str(mcp_path / "ui-knowledge/server.py")]
            },
            {
                "name": "code-analysis", 
                "command": "python",
                "args": [str(mcp_path / "code-analysis/server.py")]
            },
            {
                "name": "design-enforcer",
                "command": "python", 
                "args": [str(mcp_path / "design-enforcer/server.py")]
            }
        ]
        
        for server in servers_to_register:
            self.mcp_registry.register_server(server["name"], server)
        
        # Initialize MCP client with registered servers
        self.mcp_client = MCPClient(servers=self.mcp_registry.get_all_servers())
    
    async def generate_with_mcp_enhancement(
        self,
        prompt: str,
        context: Dict,
        target_path: Optional[str] = None
    ) -> Tuple[str, QualityReport]:
        """Generate component with full MCP enhancement cycle."""
        
        print("🎨 Enhanced generation with Professional Frontend MCP...")
        
        # Phase 1: Extract component requirements
        component_type = self._extract_component_type(prompt)
        requirements = self._extract_requirements(prompt)
        
        # Phase 2: Gather UI knowledge BEFORE generation
        ui_knowledge = await self._gather_ui_knowledge(component_type, requirements)
        
        # Phase 3: Enrich context with professional knowledge
        enhanced_context = {
            **context,
            **ui_knowledge,
            "professional_mode": True
        }
        
        # Phase 4: Generate initial component with enriched context
        print("🔨 Generating component with professional context...")
        initial_code = self.generate_component(prompt, enhanced_context)
        initial_code = self.clean_response(initial_code)
        
        # Phase 5: Analyze generated code
        analysis_results = await self._analyze_generated_code(initial_code)
        
        # Phase 6: Apply design system enforcement
        enforced_code = await self._enforce_design_system(initial_code, component_type)
        
        # Phase 7: Fix issues based on analysis
        if analysis_results["issues"]:
            print("🔧 Fixing identified issues...")
            fixed_code = await self._fix_with_mcp_knowledge(
                enforced_code,
                analysis_results,
                ui_knowledge
            )
        else:
            fixed_code = enforced_code
        
        # Phase 8: Final validation
        final_report = await self._final_validation(fixed_code)
        
        # Phase 9: Generate extras (Storybook, tests, etc.)
        if final_report.passed:
            extras = await self._generate_extras(fixed_code, component_type)
            if extras:
                print("📚 Generated Storybook stories and tests")
        
        return fixed_code, final_report
    
    async def _gather_ui_knowledge(
        self,
        component_type: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Gather comprehensive UI/UX knowledge from MCP."""
        print(f"📚 Gathering professional knowledge for {component_type}...")
        
        knowledge = {}
        
        try:
            # Get component patterns
            patterns_result = await self.mcp_client.call_tool(
                "ui-knowledge",
                "get_component_patterns",
                {
                    "component_type": component_type,
                    "framework": self._project_context.get("framework", "react"),
                    "requirements": requirements
                }
            )
            knowledge["patterns"] = patterns_result.get("data", {})
            
            # Get design principles
            principles_result = await self.mcp_client.call_tool(
                "ui-knowledge",
                "get_design_principles",
                {
                    "category": "accessibility",
                    "context": component_type
                }
            )
            knowledge["design_principles"] = principles_result.get("principles", {})
            
            # Get styling guide
            styling_result = await self.mcp_client.call_tool(
                "ui-knowledge",
                "get_styling_guide",
                {
                    "topic": "components",
                    "library": self._project_context.get("styling_approach", "tailwind")
                }
            )
            knowledge["styling_guide"] = styling_result
            
            # Get framework patterns
            framework_result = await self.mcp_client.call_tool(
                "ui-knowledge",
                "get_framework_patterns",
                {
                    "framework": self._project_context.get("framework", "react"),
                    "pattern_type": "component-patterns"
                }
            )
            knowledge["framework_patterns"] = framework_result.get("patterns", {})
            
            # Get accessibility guidelines
            a11y_result = await self.mcp_client.call_tool(
                "ui-knowledge",
                "get_accessibility_guidelines",
                {
                    "component_type": component_type,
                    "level": "AA"
                }
            )
            knowledge["accessibility"] = a11y_result
            
        except Exception as e:
            print(f"⚠️ Failed to gather some knowledge: {e}")
        
        return knowledge
    
    async def _analyze_generated_code(self, code: str) -> Dict[str, Any]:
        """Analyze generated code for issues and improvements."""
        print("🔍 Analyzing generated code...")
        
        analysis = {
            "issues": [],
            "suggestions": [],
            "patterns": []
        }
        
        try:
            # Deep component analysis
            component_analysis = await self.mcp_client.call_tool(
                "code-analysis",
                "analyze_component",
                {
                    "code": code,
                    "framework": self._project_context.get("framework", "react")
                }
            )
            analysis["component_analysis"] = component_analysis
            analysis["issues"].extend(component_analysis.get("issues", []))
            
            # Accessibility check
            a11y_check = await self.mcp_client.call_tool(
                "code-analysis",
                "check_accessibility",
                {
                    "code": code,
                    "level": "AA"
                }
            )
            analysis["accessibility"] = a11y_check
            analysis["issues"].extend(a11y_check.get("violations", []))
            
            # Performance analysis
            perf_analysis = await self.mcp_client.call_tool(
                "code-analysis",
                "analyze_performance",
                {
                    "code": code,
                    "framework": self._project_context.get("framework", "react")
                }
            )
            analysis["performance"] = perf_analysis
            analysis["issues"].extend(perf_analysis.get("issues", []))
            
            # Best practices validation
            practices_check = await self.mcp_client.call_tool(
                "code-analysis",
                "validate_best_practices",
                {
                    "code": code,
                    "framework": self._project_context.get("framework", "react")
                }
            )
            analysis["best_practices"] = practices_check
            analysis["issues"].extend(practices_check.get("violations", []))
            
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}")
        
        return analysis
    
    async def _enforce_design_system(self, code: str, component_type: str) -> str:
        """Enforce design system consistency."""
        print("🎨 Enforcing design system consistency...")
        
        try:
            # Validate against design system
            validation = await self.mcp_client.call_tool(
                "design-enforcer",
                "validate_component",
                {
                    "code": code,
                    "component_type": component_type,
                    "strict": True
                }
            )
            
            # If violations found, try to fix them
            if not validation.get("valid", True):
                # Get design tokens
                tokens = await self.mcp_client.call_tool(
                    "design-enforcer",
                    "get_design_system",
                    {"category": "all"}
                )
                
                # Apply design system enforcement
                enforced = await self.mcp_client.call_tool(
                    "design-enforcer",
                    "enforce_styling",
                    {"code": code}
                )
                
                if enforced.get("changes_made"):
                    code = enforced.get("converted_code", code)
                    print("✅ Applied design system corrections")
            
            # Check naming consistency
            consistency = await self.mcp_client.call_tool(
                "design-enforcer",
                "check_consistency",
                {"code": code}
            )
            
            if not consistency.get("consistent", True):
                print("⚠️ Naming inconsistencies found - will address in fixes")
            
        except Exception as e:
            print(f"⚠️ Design enforcement failed: {e}")
        
        return code
    
    async def _fix_with_mcp_knowledge(
        self,
        code: str,
        analysis_results: Dict[str, Any],
        ui_knowledge: Dict[str, Any]
    ) -> str:
        """Fix code issues using MCP knowledge."""
        
        # Collect all issues
        all_issues = []
        all_issues.extend(analysis_results.get("issues", []))
        
        if analysis_results.get("accessibility", {}).get("violations"):
            all_issues.extend([
                f"Accessibility: {v}" for v in 
                analysis_results["accessibility"]["violations"]
            ])
        
        if not all_issues:
            return code
        
        # Build fix prompt with professional knowledge
        fix_prompt = f"""
Fix the following issues in this component while maintaining professional standards:

Issues to fix:
{self._format_issues(all_issues)}

Apply these patterns and best practices:
- Component patterns: {ui_knowledge.get('patterns', {}).get('patterns', [])}
- Best practices: {ui_knowledge.get('patterns', {}).get('best_practices', [])}
- Accessibility requirements: {ui_knowledge.get('accessibility', {}).get('guidelines', [])}

Component code:
{code}

Return only the fixed component code.
"""
        
        # Use the AI to fix with professional knowledge
        fixed_code = self.generate_component(fix_prompt, {
            "fixing_mode": True,
            "professional_knowledge": ui_knowledge
        })
        
        return self.clean_response(fixed_code)
    
    async def _final_validation(self, code: str) -> QualityReport:
        """Perform final validation of the component."""
        print("✅ Performing final validation...")
        
        # Use existing validator if available
        if self.validator:
            report = self.validator.validate_component(code, "component.tsx")
            
            # Enhance with MCP validation
            try:
                mcp_validation = await self.mcp_client.call_tool(
                    "design-enforcer",
                    "validate_component",
                    {"code": code, "strict": True}
                )
                
                if not mcp_validation.get("valid", True):
                    for violation in mcp_validation.get("violations", []):
                        report.add_error("design_system", str(violation))
                
            except Exception as e:
                print(f"⚠️ MCP validation failed: {e}")
            
            return report
        
        # Fallback to basic report
        report = QualityReport()
        report.passed = True
        return report
    
    async def _generate_extras(self, code: str, component_type: str) -> Dict[str, str]:
        """Generate Storybook stories, tests, etc."""
        extras = {}
        
        try:
            # Extract component name
            import re
            match = re.search(r'(?:function|const|class)\s+(\w+)', code)
            component_name = match.group(1) if match else "Component"
            
            # Generate Storybook story
            story_result = await self.mcp_client.call_tool(
                "design-enforcer",
                "export_to_storybook",
                {
                    "component_code": code,
                    "component_name": component_name
                }
            )
            
            if story_result.get("story_code"):
                extras["storybook"] = story_result["story_code"]
            
        except Exception as e:
            print(f"⚠️ Failed to generate extras: {e}")
        
        return extras
    
    def _extract_component_type(self, prompt: str) -> str:
        """Extract component type from prompt."""
        prompt_lower = prompt.lower()
        
        component_types = [
            "button", "form", "modal", "table", "card", "list",
            "navigation", "navbar", "sidebar", "dropdown", "select",
            "input", "checkbox", "radio", "toggle", "tabs", "accordion"
        ]
        
        for comp_type in component_types:
            if comp_type in prompt_lower:
                return comp_type
        
        return "component"
    
    def _extract_requirements(self, prompt: str) -> List[str]:
        """Extract requirements from prompt."""
        requirements = []
        
        prompt_lower = prompt.lower()
        
        # Common requirement keywords
        if "accessible" in prompt_lower or "a11y" in prompt_lower:
            requirements.append("accessibility")
        if "responsive" in prompt_lower:
            requirements.append("responsive")
        if "dark mode" in prompt_lower:
            requirements.append("dark mode")
        if "loading" in prompt_lower:
            requirements.append("loading state")
        if "error" in prompt_lower:
            requirements.append("error handling")
        if "animation" in prompt_lower or "transition" in prompt_lower:
            requirements.append("animations")
        
        return requirements
    
    def _format_issues(self, issues: List[Any]) -> str:
        """Format issues for display."""
        formatted = []
        for issue in issues:
            if isinstance(issue, dict):
                formatted.append(f"- {issue.get('message', str(issue))}")
            else:
                formatted.append(f"- {issue}")
        return "\n".join(formatted)
    
    async def generate_component_with_qa(
        self,
        prompt: str,
        context: Dict,
        target_path: Optional[str] = None
    ) -> Tuple[str, QualityReport]:
        """Override parent method to use MCP enhancement."""
        
        # Check if MCP servers are available
        if self.mcp_client:
            try:
                # Try enhanced generation
                return await self.generate_with_mcp_enhancement(prompt, context, target_path)
            except Exception as e:
                print(f"⚠️ MCP enhancement failed, falling back to standard: {e}")
        
        # Fallback to parent implementation
        return super().generate_component_with_qa(prompt, context, target_path)


def create_enhanced_generator(*args, **kwargs) -> EnhancedUIGenerator:
    """Factory function to create enhanced generator."""
    return EnhancedUIGenerator(*args, **kwargs)