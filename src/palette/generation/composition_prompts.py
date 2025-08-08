"""
Composition-Aware Prompt Templates for Component Generation
Generates prompts that understand component composition patterns and relationships.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..intelligence.component_reuse_analyzer import (
    ComponentReuseAnalyzer,
    ReuseAnalysisResult,
    ComponentMatch,
    CompositionOpportunity
)
from ..mcp.ui_library_manager import MCPUILibraryManager
from ..analysis.context import ProjectAnalyzer
from ..errors.decorators import handle_errors


class CompositionPattern(Enum):
    """Types of component composition patterns."""
    CONTAINER_CONTENT = "container_content"      # Components that wrap other components
    LIST_ITEM = "list_item"                     # Components designed for repetition
    FORM_FIELD = "form_field"                   # Components that participate in forms
    NAVIGATION_ITEM = "navigation_item"          # Components for navigation structures
    MODAL_CONTENT = "modal_content"             # Components designed for overlays
    CARD_SECTION = "card_section"               # Components that fit within cards
    GRID_ITEM = "grid_item"                     # Components designed for grid layouts
    COMPOUND_COMPONENT = "compound_component"    # Components with sub-components


@dataclass
class CompositionContext:
    """Context about how a component should compose with others."""
    pattern: CompositionPattern
    parent_components: List[str] = field(default_factory=list)
    child_components: List[str] = field(default_factory=list) 
    sibling_components: List[str] = field(default_factory=list)
    composition_props: Dict[str, Any] = field(default_factory=dict)
    layout_considerations: List[str] = field(default_factory=list)
    accessibility_requirements: List[str] = field(default_factory=list)


@dataclass
class CompositionPromptConfig:
    """Configuration for composition-aware prompt generation."""
    include_reuse_examples: bool = True
    include_composition_patterns: bool = True
    include_accessibility_guidance: bool = True
    include_responsive_considerations: bool = True
    max_example_components: int = 3
    focus_on_integration: bool = True


class CompositionAwarePromptBuilder:
    """
    Builds prompts that understand component composition and integration patterns.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.reuse_analyzer = ComponentReuseAnalyzer(project_path)
        self.library_manager = MCPUILibraryManager(project_path)
        self.project_analyzer = ProjectAnalyzer()
        
        # Initialize composition pattern templates
        self._initialize_pattern_templates()
    
    def _initialize_pattern_templates(self):
        """Initialize templates for different composition patterns."""
        self.pattern_templates = {
            CompositionPattern.CONTAINER_CONTENT: {
                "description": "Components that wrap and manage other components",
                "examples": ["Card", "Modal", "Drawer", "Accordion", "Tabs"],
                "considerations": [
                    "Flexible content area with proper spacing",
                    "Support for various child component types",
                    "Consistent padding and margin handling",
                    "Overflow handling for dynamic content"
                ],
                "props_to_include": ["children", "spacing", "padding", "overflow"]
            },
            
            CompositionPattern.LIST_ITEM: {
                "description": "Components designed for repetition in lists or grids",
                "examples": ["ListItem", "TableRow", "GridItem", "CarouselSlide"],
                "considerations": [
                    "Consistent sizing across items",
                    "Hover and selection states",
                    "Keyboard navigation support",
                    "Efficient re-rendering for large lists"
                ],
                "props_to_include": ["selected", "disabled", "index", "onClick"]
            },
            
            CompositionPattern.FORM_FIELD: {
                "description": "Components that participate in form workflows",
                "examples": ["FormField", "InputGroup", "FormSection", "FieldSet"],
                "considerations": [
                    "Label and error message integration",
                    "Validation state handling",
                    "Form submission integration",
                    "Accessibility with screen readers"
                ],
                "props_to_include": ["label", "error", "required", "disabled", "value", "onChange"]
            },
            
            CompositionPattern.NAVIGATION_ITEM: {
                "description": "Components for navigation structures",
                "examples": ["NavItem", "BreadcrumbItem", "TabItem", "MenuIte"],
                "considerations": [
                    "Active and inactive states",
                    "Keyboard navigation (arrow keys, tab)",
                    "Route integration if applicable",
                    "Nested navigation support"
                ],
                "props_to_include": ["active", "href", "onClick", "disabled"]
            },
            
            CompositionPattern.MODAL_CONTENT: {
                "description": "Components designed for overlay contexts",
                "examples": ["ModalBody", "TooltipContent", "PopoverContent", "DropdownItem"],
                "considerations": [
                    "Focus management and trapping",
                    "Escape key handling",
                    "Click outside behavior",
                    "Portal rendering if needed"
                ],
                "props_to_include": ["onClose", "closeOnEscape", "closeOnOverlayClick"]
            },
            
            CompositionPattern.COMPOUND_COMPONENT: {
                "description": "Components with multiple related sub-components", 
                "examples": ["Accordion", "Tabs", "Menu", "Select"],
                "considerations": [
                    "State management between sub-components",
                    "Consistent API across sub-components",
                    "Proper TypeScript types for compound usage",
                    "Context providers for shared state"
                ],
                "props_to_include": ["defaultValue", "value", "onChange", "children"]
            }
        }
    
    @handle_errors(reraise=True)
    async def build_composition_prompt(self, 
                                     request: str,
                                     existing_components: Optional[List[str]] = None,
                                     config: Optional[CompositionPromptConfig] = None) -> str:
        """
        Build a composition-aware prompt for component generation.
        
        Args:
            request: User's component request
            existing_components: List of existing components to consider
            config: Configuration for prompt generation
            
        Returns:
            Composition-aware prompt string
        """
        config = config or CompositionPromptConfig()
        
        # Analyze reuse opportunities
        reuse_analysis = await self.reuse_analyzer.analyze_reuse_opportunities(request)
        
        # Detect composition context
        composition_context = await self._detect_composition_context(
            request, existing_components, reuse_analysis
        )
        
        # Get project context
        project_context = await self._get_project_context()
        
        # Build the prompt
        prompt_sections = [
            self._build_header_section(request),
            self._build_composition_section(composition_context, config),
            self._build_reuse_section(reuse_analysis, config),
            self._build_project_context_section(project_context, config),
            self._build_implementation_section(composition_context, config),
            self._build_constraints_section(config)
        ]
        
        return "\n\n".join(filter(None, prompt_sections))
    
    def _build_header_section(self, request: str) -> str:
        """Build the header section of the prompt."""
        return f"""# Component Generation Request: {request}

You are an expert React component developer creating a component that needs to integrate seamlessly with an existing codebase. Focus on composition patterns, reusability, and proper integration with existing components."""
    
    def _build_composition_section(self, context: Optional[CompositionContext], 
                                 config: CompositionPromptConfig) -> str:
        """Build the composition guidance section."""
        if not context or not config.include_composition_patterns:
            return ""
        
        pattern_info = self.pattern_templates.get(context.pattern, {})
        
        section = f"""## Composition Context

**Pattern**: {context.pattern.value.replace('_', ' ').title()}
**Description**: {pattern_info.get('description', 'Custom composition pattern')}

### Composition Requirements:"""
        
        if context.parent_components:
            section += f"\n- **Parent Components**: {', '.join(context.parent_components)}"
        
        if context.child_components:
            section += f"\n- **Child Components**: {', '.join(context.child_components)}"
            
        if context.sibling_components:
            section += f"\n- **Sibling Components**: {', '.join(context.sibling_components)}"
        
        # Add pattern-specific considerations
        considerations = pattern_info.get('considerations', [])
        if considerations:
            section += "\n\n### Key Considerations:"
            for consideration in considerations:
                section += f"\n- {consideration}"
        
        # Add required props
        required_props = pattern_info.get('props_to_include', [])
        if required_props:
            section += f"\n\n### Required Props: {', '.join(required_props)}"
        
        return section
    
    def _build_reuse_section(self, analysis: Optional[ReuseAnalysisResult],
                           config: CompositionPromptConfig) -> str:
        """Build the component reuse section."""
        if not analysis or not config.include_reuse_examples:
            return ""
        
        section = "## Component Reuse Opportunities"
        
        # Add existing component matches (both exact and close matches)
        all_matches = (analysis.exact_matches or []) + (analysis.close_matches or [])
        if all_matches:
            section += "\n\n### Similar Existing Components:"
            for match in all_matches[:config.max_example_components]:
                section += f"\n- **{match.component.name}** (confidence: {match.confidence:.1%})"
                if match.modifications_needed:
                    section += f"\n  - Modifications: {', '.join(match.modifications_needed[:2])}"
        
        # Add composition opportunities
        if analysis.composition_opportunities:
            section += "\n\n### Composition Opportunities:"
            for opportunity in analysis.composition_opportunities:
                component_names = [comp.name for comp in opportunity.components]
                section += f"\n- **{' + '.join(component_names)}**"
                section += f"\n  - Type: {opportunity.composition_type}"
                section += f"\n  - Confidence: {opportunity.confidence:.1%}"
                if opportunity.benefits:
                    section += f"\n  - Benefits: {', '.join(opportunity.benefits[:2])}"
        
        # Add reuse recommendations
        if hasattr(analysis, 'recommendation') and analysis.recommendation:
            section += "\n\n### Primary Recommendation:"
            section += f"\n- {analysis.recommendation}"
            if analysis.reasoning:
                section += f"\n- Reasoning: {analysis.reasoning}"
        
        return section
    
    async def _get_project_context(self) -> Dict[str, Any]:
        """Get relevant project context for composition."""
        try:
            # Get UI library context
            ui_library = await self.library_manager.detect_project_ui_library()
            library_context = None
            if ui_library:
                library_context = await self.library_manager.get_library_context(ui_library)
            
            # Get project analysis
            project_context = self.project_analyzer.analyze_project(str(self.project_path))
            
            return {
                "ui_library": ui_library,
                "library_context": library_context,
                "project_context": project_context
            }
        
        except Exception as e:
            print(f"Warning: Could not get full project context: {e}")
            return {}
    
    def _build_project_context_section(self, context: Dict[str, Any], 
                                     config: CompositionPromptConfig) -> str:
        """Build the project context section."""
        if not context:
            return ""
        
        section = "## Project Integration Context"
        
        # UI Library information
        ui_library = context.get("ui_library")
        if ui_library:
            section += f"\n\n### UI Library: {ui_library.value}"
            
            library_context = context.get("library_context")
            if library_context:
                # Add design tokens
                if hasattr(library_context, 'design_tokens') and library_context.design_tokens:
                    section += "\n\n### Available Design Tokens:"
                    tokens = library_context.design_tokens
                    if tokens.get('colors'):
                        section += f"\n- Colors: {', '.join(list(tokens['colors'].keys())[:5])}"
                    if tokens.get('spacing'):
                        section += f"\n- Spacing: {', '.join(map(str, list(tokens['spacing'].keys())[:5]))}"
                    if tokens.get('typography'):
                        section += f"\n- Typography: {', '.join(list(tokens['typography'].keys())[:3])}"
        
        # Project patterns
        project_context = context.get("project_context", {})
        if project_context:
            if project_context.get("component_patterns"):
                section += "\n\n### Existing Component Patterns:"
                patterns = project_context["component_patterns"]
                for pattern in list(patterns.keys())[:3]:
                    section += f"\n- {pattern}: {patterns[pattern]}"
        
        return section
    
    def _build_implementation_section(self, context: Optional[CompositionContext],
                                    config: CompositionPromptConfig) -> str:
        """Build the implementation guidance section."""
        section = "## Implementation Guidelines"
        
        section += "\n\n### Component Structure:"
        section += "\n- Use TypeScript with proper prop types"
        section += "\n- Include proper JSDoc documentation"
        section += "\n- Follow existing naming conventions"
        section += "\n- Implement proper error boundaries if needed"
        
        if config.include_accessibility_guidance:
            section += "\n\n### Accessibility Requirements:"
            section += "\n- Include proper ARIA attributes"
            section += "\n- Support keyboard navigation"
            section += "\n- Provide screen reader compatible content"
            section += "\n- Follow WCAG 2.1 guidelines"
            
            if context and context.accessibility_requirements:
                for req in context.accessibility_requirements:
                    section += f"\n- {req}"
        
        if config.include_responsive_considerations:
            section += "\n\n### Responsive Design:"
            section += "\n- Mobile-first approach"
            section += "\n- Use flexible sizing (rem, em, %)"
            section += "\n- Consider touch targets (min 44px)"
            section += "\n- Test across breakpoints"
        
        if config.focus_on_integration:
            section += "\n\n### Integration Focus:"
            section += "\n- Ensure props follow existing patterns"
            section += "\n- Use consistent styling approach"
            section += "\n- Handle edge cases gracefully"
            section += "\n- Provide sensible defaults"
        
        return section
    
    def _build_constraints_section(self, config: CompositionPromptConfig) -> str:
        """Build the constraints and requirements section."""
        section = "## Constraints and Requirements"
        
        section += "\n\n### Code Quality:"
        section += "\n- No console.log statements"
        section += "\n- Proper error handling"
        section += "\n- Performance considerations"
        section += "\n- Clean, readable code"
        
        section += "\n\n### Testing Considerations:"
        section += "\n- Include data-testid attributes"
        section += "\n- Consider unit testing needs"
        section += "\n- Handle loading and error states"
        section += "\n- Provide clear prop interfaces"
        
        return section
    
    async def _detect_composition_context(self, 
                                        request: str,
                                        existing_components: Optional[List[str]],
                                        reuse_analysis: Optional[ReuseAnalysisResult]) -> Optional[CompositionContext]:
        """Detect the composition context based on the request and analysis."""
        request_lower = request.lower()
        
        # Pattern detection based on keywords
        patterns = [
            (CompositionPattern.CONTAINER_CONTENT, ["card", "modal", "drawer", "container", "wrapper", "panel"]),
            (CompositionPattern.LIST_ITEM, ["item", "row", "entry", "tile", "list"]),
            (CompositionPattern.FORM_FIELD, ["form", "input", "field", "control", "validation"]),
            (CompositionPattern.NAVIGATION_ITEM, ["nav", "menu", "breadcrumb", "tab", "link"]),
            (CompositionPattern.MODAL_CONTENT, ["modal", "popup", "overlay", "tooltip", "dropdown"]),
            (CompositionPattern.CARD_SECTION, ["section", "area", "region", "zone"]),
            (CompositionPattern.GRID_ITEM, ["grid", "layout", "column", "cell"]),
            (CompositionPattern.COMPOUND_COMPONENT, ["compound", "multi", "complex", "accordion", "tabs"])
        ]
        
        detected_pattern = None
        for pattern, keywords in patterns:
            if any(keyword in request_lower for keyword in keywords):
                detected_pattern = pattern
                break
        
        if not detected_pattern:
            detected_pattern = CompositionPattern.CONTAINER_CONTENT  # Default
        
        # Build composition context
        context = CompositionContext(pattern=detected_pattern)
        
        # Add composition opportunities from analysis
        if reuse_analysis and reuse_analysis.composition_opportunities:
            for opportunity in reuse_analysis.composition_opportunities:
                context.parent_components.append(opportunity.base_component)
                context.child_components.append(opportunity.enhancement_component)
        
        # Add existing components as potential siblings
        if existing_components:
            context.sibling_components = existing_components[:5]  # Limit to avoid bloat
        
        return context
    
    @handle_errors(reraise=True)
    async def build_compound_component_prompt(self, 
                                            compound_name: str,
                                            sub_components: List[str],
                                            config: Optional[CompositionPromptConfig] = None) -> str:
        """
        Build a prompt specifically for compound components (components with sub-components).
        
        Args:
            compound_name: Name of the main compound component
            sub_components: List of sub-component names
            config: Configuration for prompt generation
            
        Returns:
            Specialized prompt for compound component generation
        """
        config = config or CompositionPromptConfig()
        
        context = CompositionContext(
            pattern=CompositionPattern.COMPOUND_COMPONENT,
            child_components=sub_components
        )
        
        prompt = f"""# Compound Component Generation: {compound_name}

You are creating a compound component system where the main component has several related sub-components that work together. This follows the compound component pattern commonly used in advanced React applications.

## Compound Component Structure

**Main Component**: {compound_name}
**Sub-Components**: {', '.join(sub_components)}

### Implementation Pattern:
- Main component acts as context provider
- Sub-components access shared state via context
- Each sub-component is also exported for direct use
- Provide both compound usage and individual usage patterns

### Required Exports:
```typescript
export const {compound_name} = MainComponent;
"""
        
        for sub in sub_components:
            prompt += f"export const {sub} = {compound_name}.{sub};\n"
        
        prompt += "```"
        
        # Add composition guidance
        composition_section = self._build_composition_section(context, config)
        if composition_section:
            prompt += f"\n\n{composition_section}"
        
        # Add compound-specific guidance
        prompt += """

## Compound Component Best Practices:

### Context Management:
- Use React.createContext for shared state
- Provide type-safe context hooks
- Handle cases where sub-components are used outside context

### API Design:
- Consistent prop naming across sub-components
- Clear relationship between main and sub-component props
- Flexible composition - sub-components work in any order

### TypeScript Support:
- Proper typing for compound component pattern
- IntelliSense support for sub-components
- Generic types where appropriate

### Usage Patterns:
Support both compound usage:
```tsx
<MainComponent>
  <SubComponent1 />
  <SubComponent2 />
</MainComponent>
```

And individual usage:
```tsx
<SubComponent1 standalone />
```
"""
        
        return prompt