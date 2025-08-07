"""
MCP-based Shadcn/UI Generator

This module integrates with the shadcn-ui MCP server to generate beautiful,
professional UI components using the same methodology as v0.dev and other
modern UI generation tools.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from ..mcp.client import MCPClient
from ..aesthetics.aesthetic_prompts import DesignStyle, get_design_style_from_prompt
from ..analysis.context import ProjectAnalyzer


class MCPShadcnGenerator:
    """Generator that uses MCP servers for beautiful shadcn/ui components"""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.mcp_client = None
        self.shadcn_server_path = self._get_shadcn_server_path()
        
    def _get_shadcn_server_path(self) -> str:
        """Get path to the shadcn-ui MCP server"""
        current_dir = Path(__file__).parent
        server_path = current_dir.parent.parent.parent / "mcp-servers" / "shadcn-ui-server" / "server.py"
        return str(server_path)
    
    async def initialize(self) -> bool:
        """Initialize MCP connection to shadcn-ui server"""
        try:
            self.mcp_client = MCPClient()
            await self.mcp_client.connect_stdio(self.shadcn_server_path)
            print("✅ Connected to shadcn-ui MCP server")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to shadcn-ui server: {e}")
            return False
    
    async def generate_beautiful_component(self, 
                                          prompt: str,
                                          component_type: Optional[str] = None,
                                          style_preference: Optional[str] = None) -> Dict[str, Any]:
        """Generate a beautiful component using the MCP shadcn server"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        # Analyze the prompt to determine component type and style
        detected_type = self._detect_component_type(prompt) if not component_type else component_type
        detected_style = get_design_style_from_prompt(prompt) if not style_preference else DesignStyle(style_preference)
        
        # Determine additional parameters
        size = self._determine_size_from_prompt(prompt)
        animations_enabled = self._should_enable_animations(prompt)
        
        # Call the MCP server to generate the component
        try:
            result = await self.mcp_client.call_tool(
                "generate_shadcn_component",
                {
                    "description": prompt,
                    "component_type": detected_type,
                    "style": detected_style.value,
                    "size": size,
                    "with_animations": animations_enabled
                }
            )
            
            # Parse the result
            if result and len(result) > 0:
                component_data = json.loads(result[0].text)
                return await self._enhance_component_output(component_data, prompt)
            else:
                raise RuntimeError("No result from MCP server")
                
        except Exception as e:
            print(f"❌ Error generating component via MCP: {e}")
            raise
    
    async def compose_beautiful_layout(self, 
                                      layout_description: str,
                                      components: List[str],
                                      responsive: bool = True) -> Dict[str, Any]:
        """Compose multiple components into a beautiful layout"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")
        
        try:
            result = await self.mcp_client.call_tool(
                "compose_component_layout",
                {
                    "layout_description": layout_description,
                    "components": components,
                    "responsive": responsive
                }
            )
            
            if result and len(result) > 0:
                layout_data = json.loads(result[0].text)
                return await self._enhance_layout_output(layout_data, layout_description)
            else:
                raise RuntimeError("No layout result from MCP server")
                
        except Exception as e:
            print(f"❌ Error composing layout via MCP: {e}")
            raise
    
    async def get_component_suggestions(self, component_name: str) -> Dict[str, Any]:
        """Get available variants and options for a component"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")
        
        try:
            result = await self.mcp_client.call_tool(
                "get_component_variants",
                {"component_name": component_name}
            )
            
            if result and len(result) > 0:
                return json.loads(result[0].text)
            else:
                return {}
                
        except Exception as e:
            print(f"❌ Error getting component variants: {e}")
            return {}
    
    async def analyze_and_recommend(self, project_path: str) -> Dict[str, Any]:
        """Analyze project and recommend shadcn/ui implementation strategy"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")
        
        try:
            result = await self.mcp_client.call_tool(
                "analyze_design_system",
                {"project_path": project_path}
            )
            
            if result and len(result) > 0:
                analysis = json.loads(result[0].text)
                return self._format_analysis_recommendations(analysis)
            else:
                return {"error": "No analysis result"}
                
        except Exception as e:
            print(f"❌ Error analyzing design system: {e}")
            return {"error": str(e)}
    
    async def generate_theme_config(self, 
                                   brand_colors: Optional[Dict[str, str]] = None,
                                   style_preference: str = "modern") -> Dict[str, Any]:
        """Generate shadcn/ui theme configuration for the project"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized")
        
        # Extract brand colors from project if not provided
        if not brand_colors and self.project_path:
            brand_colors = await self._extract_brand_colors()
        
        try:
            result = await self.mcp_client.call_tool(
                "generate_theme_config",
                {
                    "brand_colors": brand_colors or {},
                    "style_preference": style_preference
                }
            )
            
            if result and len(result) > 0:
                return json.loads(result[0].text)
            else:
                return {}
                
        except Exception as e:
            print(f"❌ Error generating theme config: {e}")
            return {"error": str(e)}
    
    def _detect_component_type(self, prompt: str) -> str:
        """Detect component type from prompt"""
        prompt_lower = prompt.lower()
        
        # Component type detection logic
        if any(word in prompt_lower for word in ["button", "btn", "click", "action", "cta"]):
            return "button"
        elif any(word in prompt_lower for word in ["card", "panel", "container", "box"]):
            return "card"
        elif any(word in prompt_lower for word in ["form", "input", "field", "submit", "validate"]):
            return "form"
        elif any(word in prompt_lower for word in ["modal", "dialog", "popup", "overlay"]):
            return "modal"
        elif any(word in prompt_lower for word in ["table", "data", "grid", "rows", "columns"]):
            return "table"
        elif any(word in prompt_lower for word in ["nav", "navigation", "menu", "header"]):
            return "navigation"
        elif any(word in prompt_lower for word in ["hero", "banner", "landing", "header section"]):
            return "hero"
        elif any(word in prompt_lower for word in ["dashboard", "metrics", "stats", "analytics"]):
            return "dashboard"
        else:
            return "button"  # Default fallback
    
    def _determine_size_from_prompt(self, prompt: str) -> str:
        """Determine component size from prompt"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ["large", "big", "xl", "jumbo"]):
            return "lg"
        elif any(word in prompt_lower for word in ["small", "compact", "mini", "sm"]):
            return "sm"
        else:
            return "default"
    
    def _should_enable_animations(self, prompt: str) -> bool:
        """Determine if animations should be enabled based on prompt"""
        prompt_lower = prompt.lower()
        
        # Disable animations if explicitly requested
        if any(word in prompt_lower for word in ["no animation", "static", "no transition", "no motion"]):
            return False
        
        # Enable animations for interactive or dynamic requests
        if any(word in prompt_lower for word in ["animate", "transition", "hover", "interactive", "dynamic"]):
            return True
        
        return True  # Default to enabled
    
    async def _enhance_component_output(self, component_data: Dict[str, Any], original_prompt: str) -> Dict[str, Any]:
        """Enhance the component output with additional context and metadata"""
        
        # Add prompt context
        component_data["original_prompt"] = original_prompt
        component_data["generation_timestamp"] = asyncio.get_event_loop().time()
        
        # Add project-specific enhancements if project path is available
        if self.project_path:
            project_context = await self._get_project_context()
            component_data["project_context"] = project_context
        
        # Add usage recommendations
        component_data["usage_recommendations"] = self._generate_usage_recommendations(
            component_data, original_prompt
        )
        
        # Add testing suggestions
        component_data["testing_suggestions"] = self._generate_testing_suggestions(component_data)
        
        return component_data
    
    async def _enhance_layout_output(self, layout_data: Dict[str, Any], description: str) -> Dict[str, Any]:
        """Enhance layout output with additional metadata"""
        
        layout_data["original_description"] = description
        layout_data["generation_timestamp"] = asyncio.get_event_loop().time()
        
        # Add responsive recommendations
        layout_data["responsive_recommendations"] = self._generate_responsive_recommendations(layout_data)
        
        # Add accessibility notes
        layout_data["accessibility_notes"] = self._generate_accessibility_notes(layout_data)
        
        return layout_data
    
    async def _extract_brand_colors(self) -> Dict[str, str]:
        """Extract brand colors from the project"""
        if not self.project_path:
            return {}
        
        try:
            analyzer = ProjectAnalyzer()
            context = analyzer.analyze(self.project_path)
            design_tokens = context.get("design_tokens", {})
            colors = design_tokens.get("colors", {})
            
            # Convert to brand color format
            brand_colors = {}
            if isinstance(colors, dict) and colors:
                color_keys = list(colors.keys())
                if len(color_keys) >= 1:
                    brand_colors["primary"] = color_keys[0]
                if len(color_keys) >= 2:
                    brand_colors["secondary"] = color_keys[1]
                if len(color_keys) >= 3:
                    brand_colors["accent"] = color_keys[2]
            
            return brand_colors
            
        except Exception as e:
            print(f"⚠️  Could not extract brand colors: {e}")
            return {}
    
    async def _get_project_context(self) -> Dict[str, Any]:
        """Get relevant project context for component generation"""
        if not self.project_path:
            return {}
        
        try:
            analyzer = ProjectAnalyzer()
            return analyzer.analyze(self.project_path)
        except Exception as e:
            print(f"⚠️  Could not analyze project context: {e}")
            return {}
    
    def _generate_usage_recommendations(self, component_data: Dict[str, Any], prompt: str) -> List[str]:
        """Generate usage recommendations for the component"""
        recommendations = [
            "Import the component and its dependencies",
            "Ensure shadcn/ui is properly configured in your project",
            "Test the component in different screen sizes",
            "Verify accessibility with screen readers"
        ]
        
        # Add specific recommendations based on component type
        if "button" in prompt.lower():
            recommendations.extend([
                "Consider loading states for async actions",
                "Add proper aria-labels for icon-only buttons",
                "Test keyboard navigation (Tab, Enter, Space)"
            ])
        elif "form" in prompt.lower():
            recommendations.extend([
                "Implement proper form validation",
                "Add error handling and user feedback",
                "Ensure proper focus management"
            ])
        
        return recommendations
    
    def _generate_testing_suggestions(self, component_data: Dict[str, Any]) -> List[str]:
        """Generate testing suggestions for the component"""
        return [
            "Write unit tests for component props and behavior",
            "Test accessibility with axe-core or similar tools",
            "Verify responsive design across breakpoints",
            "Test keyboard navigation and focus management",
            "Validate color contrast ratios",
            "Test with different theme configurations"
        ]
    
    def _generate_responsive_recommendations(self, layout_data: Dict[str, Any]) -> List[str]:
        """Generate responsive design recommendations"""
        return [
            "Test layout on mobile devices (320px - 768px)",
            "Verify tablet experience (768px - 1024px)", 
            "Ensure desktop optimization (1024px+)",
            "Check for horizontal scrolling issues",
            "Validate touch targets are at least 44px",
            "Test with different content lengths"
        ]
    
    def _generate_accessibility_notes(self, layout_data: Dict[str, Any]) -> List[str]:
        """Generate accessibility notes for layouts"""
        return [
            "Ensure proper heading hierarchy (h1, h2, h3...)",
            "Add skip navigation links for complex layouts",
            "Verify color contrast meets WCAG AA standards",
            "Test with screen readers (NVDA, JAWS, VoiceOver)",
            "Ensure all interactive elements are keyboard accessible",
            "Add ARIA landmarks for layout sections"
        ]
    
    def _format_analysis_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format analysis recommendations for better presentation"""
        formatted = analysis.copy()
        
        # Add priority levels to recommendations
        if "shadcn_recommendations" in formatted:
            recommendations = formatted["shadcn_recommendations"]
            formatted["prioritized_recommendations"] = {
                "high_priority": recommendations[:3] if len(recommendations) >= 3 else recommendations,
                "medium_priority": recommendations[3:6] if len(recommendations) > 3 else [],
                "low_priority": recommendations[6:] if len(recommendations) > 6 else []
            }
        
        return formatted
    
    async def cleanup(self):
        """Clean up MCP connection"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            self.mcp_client = None


# Convenience function for direct usage
async def generate_beautiful_component(prompt: str, 
                                      project_path: Optional[str] = None,
                                      component_type: Optional[str] = None,
                                      style: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a beautiful shadcn/ui component using MCP server
    
    Args:
        prompt: Natural language description of the component
        project_path: Optional path to the project for context
        component_type: Optional component type override
        style: Optional style preference override
        
    Returns:
        Dictionary containing the generated component and metadata
    """
    generator = MCPShadcnGenerator(project_path)
    
    try:
        await generator.initialize()
        result = await generator.generate_beautiful_component(prompt, component_type, style)
        return result
    finally:
        await generator.cleanup()


    async def customize_existing_component(self, 
                                          component_code: str,
                                          customization_request: str) -> Dict[str, Any]:
        """Customize an existing shadcn/ui component based on user request"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        try:
            result = await self.mcp_client.call_tool(
                "customize_component",
                {
                    "existing_code": component_code,
                    "customization": customization_request,
                    "maintain_compatibility": True
                }
            )
            
            if result and len(result) > 0:
                customization_data = json.loads(result[0].text)
                return await self._enhance_customization_output(customization_data, customization_request)
            else:
                raise RuntimeError("No result from MCP customization")
                
        except Exception as e:
            print(f"❌ Error customizing component via MCP: {e}")
            # Fallback to basic customization logic
            return await self._fallback_customization(component_code, customization_request)
    
    async def refine_component_iteratively(self,
                                          component_code: str,
                                          feedback: str,
                                          iteration: int = 1) -> Dict[str, Any]:
        """Iteratively refine a component based on user feedback"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        try:
            result = await self.mcp_client.call_tool(
                "refine_component",
                {
                    "current_code": component_code,
                    "user_feedback": feedback,
                    "iteration_number": iteration,
                    "preserve_structure": True
                }
            )
            
            if result and len(result) > 0:
                refinement_data = json.loads(result[0].text)
                return await self._enhance_refinement_output(refinement_data, feedback, iteration)
            else:
                raise RuntimeError("No result from MCP refinement")
                
        except Exception as e:
            print(f"❌ Error refining component via MCP: {e}")
            return await self._fallback_refinement(component_code, feedback)
    
    async def generate_component_variants(self,
                                        base_component: str,
                                        variant_types: List[str]) -> Dict[str, Any]:
        """Generate multiple variants of a component (size, color, style)"""
        
        if not self.mcp_client:
            raise RuntimeError("MCP client not initialized. Call initialize() first.")
        
        try:
            result = await self.mcp_client.call_tool(
                "generate_variants",
                {
                    "base_component": base_component,
                    "variants": variant_types,
                    "maintain_api": True
                }
            )
            
            if result and len(result) > 0:
                variants_data = json.loads(result[0].text)
                return await self._enhance_variants_output(variants_data, variant_types)
            else:
                raise RuntimeError("No result from MCP variant generation")
                
        except Exception as e:
            print(f"❌ Error generating variants via MCP: {e}")
            return await self._fallback_variants(base_component, variant_types)
    
    async def _enhance_customization_output(self, customization_data: Dict[str, Any], 
                                          request: str) -> Dict[str, Any]:
        """Enhance customization output with metadata"""
        
        customization_data["customization_request"] = request
        customization_data["customization_timestamp"] = asyncio.get_event_loop().time()
        customization_data["type"] = "customization"
        
        # Add migration notes if significant changes were made
        if self._has_breaking_changes(customization_data):
            customization_data["migration_notes"] = self._generate_migration_notes(customization_data)
        
        return customization_data
    
    async def _enhance_refinement_output(self, refinement_data: Dict[str, Any], 
                                       feedback: str, iteration: int) -> Dict[str, Any]:
        """Enhance refinement output with iteration context"""
        
        refinement_data["user_feedback"] = feedback
        refinement_data["iteration"] = iteration
        refinement_data["refinement_timestamp"] = asyncio.get_event_loop().time()
        refinement_data["type"] = "refinement"
        
        # Add improvement summary
        refinement_data["improvements"] = self._extract_improvements(refinement_data, feedback)
        
        return refinement_data
    
    async def _enhance_variants_output(self, variants_data: Dict[str, Any], 
                                     variant_types: List[str]) -> Dict[str, Any]:
        """Enhance variants output with usage guidance"""
        
        variants_data["requested_variants"] = variant_types
        variants_data["generation_timestamp"] = asyncio.get_event_loop().time()
        variants_data["type"] = "variants"
        
        # Add usage recommendations for each variant
        variants_data["variant_usage"] = self._generate_variant_usage_guide(variants_data)
        
        return variants_data
    
    async def _fallback_customization(self, component_code: str, request: str) -> Dict[str, Any]:
        """Fallback customization when MCP fails"""
        
        return {
            "success": False,
            "error": "MCP customization unavailable",
            "fallback": True,
            "original_code": component_code,
            "request": request,
            "suggestion": "Please try regenerating the component with your customization request included in the initial prompt."
        }
    
    async def _fallback_refinement(self, component_code: str, feedback: str) -> Dict[str, Any]:
        """Fallback refinement when MCP fails"""
        
        return {
            "success": False,
            "error": "MCP refinement unavailable", 
            "fallback": True,
            "original_code": component_code,
            "feedback": feedback,
            "suggestion": "Please try generating a new component incorporating your feedback."
        }
    
    async def _fallback_variants(self, base_component: str, variant_types: List[str]) -> Dict[str, Any]:
        """Fallback variant generation when MCP fails"""
        
        return {
            "success": False,
            "error": "MCP variant generation unavailable",
            "fallback": True,
            "base_component": base_component,
            "requested_variants": variant_types,
            "suggestion": "Please describe the specific variants you want and I'll generate them individually."
        }
    
    def _has_breaking_changes(self, customization_data: Dict[str, Any]) -> bool:
        """Check if customization introduces breaking changes"""
        # Simple heuristic - check for prop name changes or interface modifications
        changes = customization_data.get("changes", [])
        breaking_patterns = ["props interface", "prop name", "breaking change", "API change"]
        
        return any(pattern in str(changes).lower() for pattern in breaking_patterns)
    
    def _generate_migration_notes(self, customization_data: Dict[str, Any]) -> List[str]:
        """Generate migration notes for breaking changes"""
        return [
            "⚠️  This customization may introduce breaking changes",
            "📝 Please review prop interfaces and component usage",
            "🔄 Consider updating existing implementations to match the new API"
        ]
    
    def _extract_improvements(self, refinement_data: Dict[str, Any], feedback: str) -> List[str]:
        """Extract list of improvements made"""
        # Parse the refinement to extract key improvements
        improvements = []
        changes = refinement_data.get("changes", "")
        
        if "accessibility" in feedback.lower():
            improvements.append("Enhanced accessibility features")
        if "performance" in feedback.lower():
            improvements.append("Performance optimizations") 
        if "style" in feedback.lower() or "design" in feedback.lower():
            improvements.append("Visual design improvements")
        if "responsive" in feedback.lower():
            improvements.append("Responsive behavior enhancements")
            
        return improvements if improvements else ["General improvements based on feedback"]
    
    def _generate_variant_usage_guide(self, variants_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate usage guide for different variants"""
        usage_guide = {}
        variants = variants_data.get("variants", {})
        
        for variant_name, variant_code in variants.items():
            if "small" in variant_name or "sm" in variant_name:
                usage_guide[variant_name] = "Use for compact spaces, mobile interfaces"
            elif "large" in variant_name or "lg" in variant_name:
                usage_guide[variant_name] = "Use for prominent actions, desktop interfaces"
            elif "destructive" in variant_name:
                usage_guide[variant_name] = "Use for delete/remove actions, warnings"
            elif "outline" in variant_name:
                usage_guide[variant_name] = "Use for secondary actions, less emphasis"
            elif "ghost" in variant_name:
                usage_guide[variant_name] = "Use for subtle actions, minimal emphasis"
            else:
                usage_guide[variant_name] = "Use based on your design requirements"
                
        return usage_guide


# Example usage for testing
async def main():
    """Example usage of the MCP shadcn generator"""
    generator = MCPShadcnGenerator()
    
    try:
        await generator.initialize()
        
        # Generate a beautiful button
        result = await generator.generate_beautiful_component(
            "Create a vibrant primary button with a gradient background and hover animations",
            component_type="button",
            style_preference="bold_vibrant"
        )
        
        print("Generated Component:")
        print(json.dumps(result, indent=2))
        
    finally:
        await generator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())