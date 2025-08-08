"""
OpenAI UI Library Optimizer - Enhances prompts with UI library-specific context.
Integrates with MCP UI Library Manager for library-specific prompt optimization.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from ..mcp.ui_library_manager import MCPUILibraryManager, UILibraryType
from ..mcp.ui_library_server_base import UILibraryContext
from ..errors.decorators import handle_errors


class PromptComplexity(Enum):
    """Prompt complexity levels for generation."""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class OptimizedPrompt:
    """Optimized prompt with UI library context."""
    system_prompt: str
    user_prompt: str
    library_context: str
    complexity_level: PromptComplexity
    component_hints: List[str]
    design_tokens: Dict[str, Any]
    best_practices: List[str]
    examples_count: int
    confidence_score: float


class OpenAIUILibraryOptimizer:
    """
    Optimizes OpenAI prompts with UI library-specific context and patterns.
    Works with MCP UI Library Manager to provide the best possible prompts.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.library_manager = MCPUILibraryManager(project_path)
        
        # Component type patterns for better optimization
        self._initialize_component_patterns()
        
        # Complexity mappings
        self._initialize_complexity_mappings()
    
    def _initialize_component_patterns(self):
        """Initialize patterns for component type detection."""
        self.component_patterns = {
            "button": ["button", "btn", "action", "submit", "click", "cta"],
            "form": ["form", "input", "field", "validation", "submit", "login", "register"],
            "card": ["card", "tile", "panel", "box", "container", "item"],
            "modal": ["modal", "dialog", "popup", "overlay", "lightbox"],
            "navigation": ["nav", "menu", "header", "navbar", "breadcrumb", "sidebar"],
            "layout": ["layout", "grid", "flex", "container", "wrapper", "section"],
            "list": ["list", "table", "grid", "collection", "items", "feed"],
            "hero": ["hero", "banner", "jumbotron", "landing", "splash"],
            "pricing": ["pricing", "plans", "subscription", "tier", "package"],
            "dashboard": ["dashboard", "admin", "analytics", "stats", "metrics"],
            "profile": ["profile", "user", "account", "settings", "avatar"],
            "shopping": ["cart", "product", "shop", "ecommerce", "checkout"],
            "media": ["gallery", "image", "video", "carousel", "slideshow"],
            "feedback": ["toast", "notification", "alert", "message", "status"],
            "data": ["chart", "graph", "visualization", "progress", "meter"]
        }
    
    def _initialize_complexity_mappings(self):
        """Initialize complexity level mappings."""
        self.complexity_features = {
            PromptComplexity.SIMPLE: {
                "max_props": 3,
                "state_complexity": "minimal",
                "styling_approach": "basic",
                "features": ["basic functionality", "simple styling", "minimal props"]
            },
            PromptComplexity.INTERMEDIATE: {
                "max_props": 7,
                "state_complexity": "moderate", 
                "styling_approach": "responsive",
                "features": ["responsive design", "state management", "proper TypeScript", "accessibility"]
            },
            PromptComplexity.ADVANCED: {
                "max_props": 12,
                "state_complexity": "complex",
                "styling_approach": "comprehensive",
                "features": ["advanced state", "animations", "optimizations", "error handling", "variants"]
            },
            PromptComplexity.EXPERT: {
                "max_props": 20,
                "state_complexity": "sophisticated",
                "styling_approach": "production-ready",
                "features": ["enterprise-grade", "performance optimized", "full accessibility", "comprehensive testing", "documentation"]
            }
        }
    
    @handle_errors(reraise=True)
    async def optimize_prompt_for_library(self,
                                        user_request: str,
                                        library_type: Optional[UILibraryType] = None,
                                        complexity: PromptComplexity = PromptComplexity.INTERMEDIATE) -> OptimizedPrompt:
        """
        Optimize prompt with UI library-specific context.
        
        Args:
            user_request: User's component generation request
            library_type: Specific UI library to use (auto-detected if None)
            complexity: Desired complexity level
            
        Returns:
            OptimizedPrompt with library-specific enhancements
        """
        print(f"🎯 Optimizing prompt for {complexity.value} complexity...")
        
        # Auto-detect library if not provided
        if library_type is None:
            library_type = await self.library_manager.detect_project_ui_library()
        
        # Analyze user request
        component_type = self._detect_component_type(user_request)
        component_hints = self._extract_component_hints(user_request)
        
        print(f"   Component type: {component_type or 'generic'}")
        print(f"   Library: {library_type.value if library_type else 'generic'}")
        
        # Get library-specific context
        library_context = None
        if library_type:
            library_context = await self.library_manager.get_library_context(library_type)
        
        # Generate optimized prompt
        if library_context:
            return await self._create_library_optimized_prompt(
                user_request, library_context, component_type, component_hints, complexity
            )
        else:
            return self._create_generic_optimized_prompt(
                user_request, component_type, component_hints, complexity
            )
    
    def _detect_component_type(self, user_request: str) -> Optional[str]:
        """Detect the type of component being requested."""
        request_lower = user_request.lower()
        
        # Score each component type based on keyword matches
        type_scores = {}
        
        for comp_type, keywords in self.component_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in request_lower:
                    # Give higher score for exact matches
                    if f" {keyword} " in f" {request_lower} " or request_lower.startswith(keyword) or request_lower.endswith(keyword):
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                type_scores[comp_type] = score
        
        # Return the highest scoring type
        if type_scores:
            return max(type_scores, key=type_scores.get)
        
        return None
    
    def _extract_component_hints(self, user_request: str) -> List[str]:
        """Extract helpful hints from the user request."""
        hints = []
        request_lower = user_request.lower()
        
        # Style hints
        style_keywords = {
            "responsive": ["responsive", "mobile", "tablet", "desktop"],
            "interactive": ["click", "hover", "toggle", "interactive"],
            "animated": ["animated", "animation", "transition", "smooth"],
            "accessible": ["accessible", "screen reader", "aria", "a11y"],
            "dark mode": ["dark mode", "theme", "light/dark"],
            "loading states": ["loading", "skeleton", "spinner", "pending"],
            "error handling": ["error", "validation", "invalid", "required"],
            "variants": ["variant", "size", "color", "style options"],
        }
        
        for hint_type, keywords in style_keywords.items():
            if any(keyword in request_lower for keyword in keywords):
                hints.append(hint_type)
        
        # Functional hints
        if "form" in request_lower or "input" in request_lower:
            hints.append("form validation")
        
        if "data" in request_lower or "api" in request_lower:
            hints.append("data fetching")
        
        if "search" in request_lower or "filter" in request_lower:
            hints.append("search/filter")
        
        return hints
    
    async def _create_library_optimized_prompt(self,
                                             user_request: str,
                                             library_context: UILibraryContext,
                                             component_type: Optional[str],
                                             component_hints: List[str],
                                             complexity: PromptComplexity) -> OptimizedPrompt:
        """Create prompt optimized for specific UI library."""
        
        # Use library's system prompt as base
        system_prompt = library_context.openai_system_prompt
        
        # Enhance system prompt with complexity requirements
        complexity_features = self.complexity_features[complexity]
        system_prompt += f"\n\n**Complexity Level: {complexity.value.upper()}**\n"
        system_prompt += f"- Target {complexity_features['max_props']} or fewer props\n"
        system_prompt += f"- {complexity_features['state_complexity'].capitalize()} state management\n"
        system_prompt += f"- {complexity_features['styling_approach'].capitalize()} styling approach\n"
        system_prompt += f"- Include: {', '.join(complexity_features['features'])}\n"
        
        # Build enhanced user prompt
        user_prompt = f"**User Request:** {user_request}\n\n"
        
        if component_type:
            user_prompt += f"**Component Type:** {component_type}\n\n"
            
            # Add library-specific component suggestions
            relevant_components = await self._get_relevant_library_components(
                component_type, library_context
            )
            if relevant_components:
                user_prompt += f"**Suggested {library_context.library_type.value} Components:**\n"
                for comp in relevant_components[:3]:
                    user_prompt += f"- {comp['name']}: {comp.get('description', 'No description')}\n"
                user_prompt += "\n"
        
        if component_hints:
            user_prompt += f"**Required Features:** {', '.join(component_hints)}\n\n"
        
        # Add design tokens context
        if library_context.design_tokens:
            user_prompt += "**Available Design Tokens:**\n"
            if "colors" in library_context.design_tokens:
                colors = library_context.design_tokens["colors"]
                if isinstance(colors, dict):
                    color_names = list(colors.keys())[:8]  # Show first 8 colors
                    user_prompt += f"- Colors: {', '.join(color_names)}\n"
            
            if "spacing" in library_context.design_tokens:
                user_prompt += "- Use consistent spacing scale from design tokens\n"
            
            user_prompt += "\n"
        
        # Add relevant examples
        relevant_examples = self._filter_relevant_examples(
            library_context.openai_examples, component_type, complexity
        )
        
        if relevant_examples:
            user_prompt += "**Reference Examples:**\n"
            for i, example in enumerate(relevant_examples[:2], 1):
                user_prompt += f"Example {i}: {example.get('prompt', 'No prompt')}\n"
                user_prompt += f"Shows: {self._extract_example_features(example.get('response', ''))}\n\n"
        
        # Add complexity-specific instructions
        user_prompt += f"**Generation Instructions:**\n"
        user_prompt += f"- Create a {complexity.value} {component_type or 'component'} using {library_context.library_type.value}\n"
        user_prompt += f"- Follow {library_context.library_type.value} best practices and conventions\n"
        user_prompt += f"- Ensure TypeScript compatibility with proper interfaces\n"
        user_prompt += f"- Include accessibility features and responsive design\n"
        
        if complexity in [PromptComplexity.ADVANCED, PromptComplexity.EXPERT]:
            user_prompt += f"- Add error handling and loading states\n"
            user_prompt += f"- Include comprehensive prop validation\n"
            user_prompt += f"- Implement performance optimizations\n"
        
        return OptimizedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            library_context=library_context.library_type.value,
            complexity_level=complexity,
            component_hints=component_hints,
            design_tokens=library_context.design_tokens,
            best_practices=library_context.best_practices,
            examples_count=len(relevant_examples),
            confidence_score=0.9  # High confidence with library context
        )
    
    def _create_generic_optimized_prompt(self,
                                       user_request: str,
                                       component_type: Optional[str],
                                       component_hints: List[str],
                                       complexity: PromptComplexity) -> OptimizedPrompt:
        """Create generic optimized prompt when no library context is available."""
        
        # Generic system prompt
        system_prompt = """You are an expert React developer who creates high-quality, accessible, and responsive React components using modern best practices.

**Development Standards:**
- Write TypeScript by default with comprehensive prop interfaces
- Use semantic HTML and proper ARIA attributes for accessibility
- Implement responsive design with mobile-first approach
- Follow React best practices and modern hooks patterns
- Use consistent naming conventions (PascalCase for components)

**Code Quality Requirements:**
- Export components as default exports
- Include proper imports and error handling
- Add helpful JSDoc comments for complex logic
- Handle edge cases and loading states
- Implement proper prop validation and defaults

**Styling Guidelines:**
- Use utility-first CSS or styled-components as appropriate
- Maintain visual hierarchy with consistent spacing and typography
- Apply accessible color schemes with proper contrast ratios
- Support both light and dark mode themes when relevant"""
        
        # Add complexity-specific requirements
        complexity_features = self.complexity_features[complexity]
        system_prompt += f"\n\n**Complexity Level: {complexity.value.upper()}**\n"
        system_prompt += f"- Target {complexity_features['max_props']} or fewer props for clarity\n"
        system_prompt += f"- Implement {complexity_features['state_complexity']} state management patterns\n"
        system_prompt += f"- Use {complexity_features['styling_approach']} styling approach\n"
        system_prompt += f"- Include these features: {', '.join(complexity_features['features'])}\n"
        
        # Build user prompt
        user_prompt = f"**User Request:** {user_request}\n\n"
        
        if component_type:
            user_prompt += f"**Component Type:** {component_type}\n\n"
            user_prompt += self._get_generic_component_guidance(component_type)
        
        if component_hints:
            user_prompt += f"**Required Features:** {', '.join(component_hints)}\n\n"
        
        # Add generic best practices
        user_prompt += "**Implementation Guidelines:**\n"
        user_prompt += f"- Create a {complexity.value} {component_type or 'React component'}\n"
        user_prompt += "- Use modern React patterns with hooks and functional components\n"
        user_prompt += "- Ensure full TypeScript support with proper interfaces\n"
        user_prompt += "- Include comprehensive accessibility features\n"
        user_prompt += "- Implement responsive design for all screen sizes\n"
        
        if complexity in [PromptComplexity.ADVANCED, PromptComplexity.EXPERT]:
            user_prompt += "- Add comprehensive error boundaries and loading states\n"
            user_prompt += "- Include performance optimizations (memo, callbacks)\n"
            user_prompt += "- Implement thorough prop validation and documentation\n"
        
        return OptimizedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            library_context="generic",
            complexity_level=complexity,
            component_hints=component_hints,
            design_tokens={},
            best_practices=[
                "Use semantic HTML elements",
                "Implement proper ARIA attributes",
                "Follow responsive design principles",
                "Use consistent spacing and typography",
                "Handle loading and error states"
            ],
            examples_count=0,
            confidence_score=0.7  # Lower confidence without library context
        )
    
    async def _get_relevant_library_components(self, 
                                             component_type: str,
                                             library_context: UILibraryContext) -> List[Dict[str, Any]]:
        """Get relevant components from the library based on component type."""
        relevant = []
        
        # Use the library manager to search for components
        search_result = await self.library_manager.get_component_suggestions(
            component_type, library_context.library_type
        )
        
        if search_result and "results" in search_result:
            relevant = search_result["results"][:5]  # Get top 5 results
        
        return relevant
    
    def _filter_relevant_examples(self,
                                examples: List[Dict[str, str]],
                                component_type: Optional[str],
                                complexity: PromptComplexity) -> List[Dict[str, str]]:
        """Filter examples based on relevance to component type and complexity."""
        if not examples or not component_type:
            return examples[:2]  # Return first 2 examples as fallback
        
        scored_examples = []
        
        for example in examples:
            score = 0
            prompt = example.get("prompt", "").lower()
            response = example.get("response", "").lower()
            
            # Score based on component type relevance
            if component_type in prompt or component_type in response:
                score += 10
            
            # Score based on matching keywords
            type_keywords = self.component_patterns.get(component_type, [])
            for keyword in type_keywords:
                if keyword in prompt:
                    score += 3
                if keyword in response:
                    score += 2
            
            # Score based on complexity indicators
            complexity_indicators = {
                PromptComplexity.SIMPLE: ["simple", "basic", "minimal"],
                PromptComplexity.INTERMEDIATE: ["responsive", "typescript", "props"],
                PromptComplexity.ADVANCED: ["state", "hooks", "complex", "validation"],
                PromptComplexity.EXPERT: ["performance", "optimized", "enterprise", "advanced"]
            }
            
            indicators = complexity_indicators.get(complexity, [])
            for indicator in indicators:
                if indicator in prompt or indicator in response:
                    score += 1
            
            if score > 0:
                scored_examples.append((score, example))
        
        # Sort by score and return top examples
        scored_examples.sort(key=lambda x: x[0], reverse=True)
        return [example for score, example in scored_examples[:3]]
    
    def _extract_example_features(self, response_code: str) -> str:
        """Extract key features from example response code."""
        features = []
        
        if "interface" in response_code or "type" in response_code:
            features.append("TypeScript")
        
        if "useState" in response_code or "useEffect" in response_code:
            features.append("React hooks")
        
        if "responsive" in response_code or "breakpoint" in response_code:
            features.append("responsive design")
        
        if "aria-" in response_code or "role=" in response_code:
            features.append("accessibility")
        
        if "loading" in response_code or "isLoading" in response_code:
            features.append("loading states")
        
        return ", ".join(features) if features else "basic implementation"
    
    def _get_generic_component_guidance(self, component_type: str) -> str:
        """Get generic guidance for component types."""
        guidance = {
            "button": "**Button Guidance:**\n- Support multiple variants (primary, secondary, outline)\n- Include loading and disabled states\n- Proper focus management and keyboard support\n- Size variations (sm, md, lg)\n\n",
            
            "form": "**Form Guidance:**\n- Comprehensive validation with clear error messages\n- Proper form submission handling\n- Field grouping with fieldset/legend where appropriate\n- Loading states during submission\n\n",
            
            "card": "**Card Guidance:**\n- Flexible content layout (header, body, footer)\n- Hover states and optional shadow variations\n- Support for media content (images, videos)\n- Proper spacing and typography hierarchy\n\n",
            
            "modal": "**Modal Guidance:**\n- Focus trap and keyboard navigation (ESC to close)\n- Backdrop click handling\n- Portal rendering for proper z-index management\n- Animation enter/exit states\n\n",
            
            "navigation": "**Navigation Guidance:**\n- Mobile-responsive with hamburger menu\n- Proper semantic HTML (nav, ul, li structure)\n- Active/current page indication\n- Keyboard navigation support\n\n"
        }
        
        return guidance.get(component_type, "")
    
    @handle_errors(reraise=True)
    async def optimize_for_variations(self,
                                    base_request: str,
                                    variation_count: int = 3,
                                    library_type: Optional[UILibraryType] = None) -> List[OptimizedPrompt]:
        """
        Generate multiple optimized prompt variations for different approaches.
        
        Args:
            base_request: Base user request
            variation_count: Number of variations to generate
            library_type: UI library to use (auto-detected if None)
            
        Returns:
            List of optimized prompts with different approaches
        """
        variations = []
        complexity_levels = [PromptComplexity.SIMPLE, PromptComplexity.INTERMEDIATE, PromptComplexity.ADVANCED]
        
        for i in range(min(variation_count, len(complexity_levels))):
            complexity = complexity_levels[i]
            
            optimized = await self.optimize_prompt_for_library(
                base_request, library_type, complexity
            )
            
            # Customize each variation
            optimized.user_prompt += f"\n**Variation Focus:** "
            if complexity == PromptComplexity.SIMPLE:
                optimized.user_prompt += "Clean, minimal implementation with essential functionality"
            elif complexity == PromptComplexity.INTERMEDIATE:
                optimized.user_prompt += "Balanced implementation with good practices and features"
            else:
                optimized.user_prompt += "Comprehensive implementation with advanced features"
            
            variations.append(optimized)
        
        return variations
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics about the optimization process."""
        return {
            "supported_libraries": len(self.library_manager.server_connections),
            "component_patterns": len(self.component_patterns),
            "complexity_levels": len(self.complexity_features),
            "library_manager_status": "initialized",
            "project_path": self.project_path
        }