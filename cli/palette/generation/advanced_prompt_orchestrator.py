"""
Advanced Prompt Orchestrator for sophisticated LLM frontend code generation.
Implements Chain-of-Thought, Reflection, Role-Based, and Contextual prompting strategies.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..errors import GenerationError
from ..errors.decorators import handle_errors, retry_on_error


class PromptStrategy(Enum):
    """Different prompting strategies for various scenarios."""
    
    SIMPLE = "simple"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REFLECTION = "reflection"
    ROLE_BASED = "role_based"
    MULTI_STAGE = "multi_stage"


class ComponentComplexity(Enum):
    """Component complexity levels for strategy selection."""
    
    SIMPLE = "simple"  # Basic components (Button, Card, etc.)
    MODERATE = "moderate"  # Components with state, interactions
    COMPLEX = "complex"  # Multi-part components, advanced patterns
    ARCHITECTURAL = "architectural"  # Pages, layouts, feature modules


@dataclass
class PromptContext:
    """Rich context for prompt generation."""
    
    user_request: str
    component_complexity: ComponentComplexity
    project_context: Dict[str, Any]
    design_tokens: Dict[str, Any]
    available_components: List[Dict[str, Any]]
    framework_patterns: Dict[str, Any]
    previous_attempts: List[str] = None
    quality_requirements: Dict[str, Any] = None
    accessibility_level: str = "aa"
    performance_requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.previous_attempts is None:
            self.previous_attempts = []
        if self.quality_requirements is None:
            self.quality_requirements = {}
        if self.performance_requirements is None:
            self.performance_requirements = {}


class PromptStrategyBase(ABC):
    """Base class for prompt strategies."""
    
    @abstractmethod
    def generate_system_prompt(self, context: PromptContext) -> str:
        """Generate system prompt for the strategy."""
        pass
    
    @abstractmethod
    def generate_user_prompt(self, context: PromptContext) -> str:
        """Generate user prompt for the strategy."""
        pass
    
    @abstractmethod
    def supports_complexity(self, complexity: ComponentComplexity) -> bool:
        """Check if strategy supports given complexity level."""
        pass


class ChainOfThoughtStrategy(PromptStrategyBase):
    """Chain-of-Thought prompting for complex reasoning."""
    
    def supports_complexity(self, complexity: ComponentComplexity) -> bool:
        return complexity in [ComponentComplexity.MODERATE, ComponentComplexity.COMPLEX, ComponentComplexity.ARCHITECTURAL]
    
    def generate_system_prompt(self, context: PromptContext) -> str:
        base_prompt = self._build_base_system_prompt(context)
        
        cot_instructions = """
CRITICAL: Use Chain-of-Thought reasoning for this component generation.

REASONING PROCESS (think step-by-step):
1. ANALYZE the request and break down requirements
2. PLAN the component architecture and structure  
3. DESIGN the data flow and state management
4. CONSIDER accessibility and performance implications
5. IMPLEMENT the solution with detailed reasoning

For each step, explain your reasoning before providing the implementation.

STEP-BY-STEP FORMAT:
## Step 1: Analysis
[Analyze the requirements, complexity, and constraints]

## Step 2: Architecture Planning  
[Plan the component structure, props interface, and relationships]

## Step 3: Design Decisions
[Explain styling approach, state management, and interaction patterns]

## Step 4: Accessibility & Performance
[Consider WCAG compliance, performance optimizations, and responsive design]

## Step 5: Implementation
[Provide the final, complete implementation with reasoning for key decisions]

Show your complete reasoning process before providing the final code."""

        return f"{base_prompt}\n\n{cot_instructions}"
    
    def generate_user_prompt(self, context: PromptContext) -> str:
        complexity_guidance = self._get_complexity_guidance(context.component_complexity)
        
        reasoning_prompt = f"""
REQUEST: {context.user_request}

COMPLEXITY LEVEL: {context.component_complexity.value.upper()}
{complexity_guidance}

REASONING REQUIREMENTS:
- Think through each decision step-by-step
- Explain why you choose specific patterns or approaches
- Consider alternative solutions and explain your choice
- Show how the component fits into the larger application architecture

Remember to follow the Step-by-Step format and show your complete reasoning process."""

        return reasoning_prompt
    
    def _build_base_system_prompt(self, context: PromptContext) -> str:
        """Build the base system prompt with project context."""
        return f"""You are an expert Frontend Engineer specializing in React/TypeScript development.

PROJECT CONTEXT:
{self._format_project_context(context)}

DESIGN SYSTEM:
{self._format_design_tokens(context.design_tokens)}

AVAILABLE COMPONENTS:
{self._format_available_components(context.available_components)}

QUALITY STANDARDS:
- Production-ready code with zero manual fixes needed
- TypeScript with comprehensive type safety
- {context.accessibility_level.upper()}-level WCAG compliance
- Mobile-first responsive design
- Performance optimized with React best practices
- Consistent with project's design system and patterns"""
    
    def _get_complexity_guidance(self, complexity: ComponentComplexity) -> str:
        """Get complexity-specific guidance."""
        guidance = {
            ComponentComplexity.MODERATE: """
For MODERATE complexity:
- Plan state management carefully (useState vs useReducer)
- Consider component composition and reusability
- Think through user interaction patterns
- Plan for loading and error states""",
            
            ComponentComplexity.COMPLEX: """
For COMPLEX complexity:
- Design comprehensive state management strategy
- Plan component hierarchy and data flow
- Consider performance implications (memoization, lazy loading)
- Design for extensibility and maintainability
- Plan comprehensive error boundaries and fallbacks""",
            
            ComponentComplexity.ARCHITECTURAL: """
For ARCHITECTURAL complexity:
- Design overall application structure
- Plan routing and navigation patterns
- Consider code splitting and bundle optimization
- Design data fetching and caching strategies
- Plan for SEO, analytics, and monitoring
- Consider server-side rendering implications"""
        }
        
        return guidance.get(complexity, "")
    
    def _format_project_context(self, context: PromptContext) -> str:
        """Format project context for the prompt."""
        project = context.project_context
        
        framework_info = f"Framework: {project.get('framework', 'React')}"
        styling_info = f"Styling: {project.get('styling', 'Tailwind CSS')}"
        typescript_info = f"TypeScript: {project.get('typescript', True)}"
        
        return f"{framework_info}\n{styling_info}\n{typescript_info}"
    
    def _format_design_tokens(self, design_tokens: Dict[str, Any]) -> str:
        """Format design tokens for the prompt."""
        if not design_tokens:
            return "No specific design tokens detected"
        
        sections = []
        
        if design_tokens.get('colors'):
            colors = design_tokens['colors']
            color_list = list(colors.keys())[:8] if isinstance(colors, dict) else colors[:8]
            sections.append(f"Colors: {', '.join(color_list)}")
        
        if design_tokens.get('spacing'):
            spacing = design_tokens['spacing']
            sections.append(f"Spacing scale: {', '.join(spacing) if isinstance(spacing, list) else 'Custom scale'}")
        
        if design_tokens.get('typography'):
            typography = design_tokens['typography']
            sections.append(f"Typography: {len(typography)} defined styles")
        
        return '\n'.join(sections) if sections else "Custom design system detected"
    
    def _format_available_components(self, components: List[Dict[str, Any]]) -> str:
        """Format available components for the prompt."""
        if not components:
            return "No existing components detected"
        
        component_summaries = []
        for comp in components[:10]:  # Limit to top 10 most relevant
            name = comp.get('name', 'Unknown')
            purpose = comp.get('purpose', 'General component')
            props_count = len(comp.get('props', []))
            
            summary = f"- {name}: {purpose} ({props_count} props)"
            component_summaries.append(summary)
        
        return '\n'.join(component_summaries)


class ReflectionStrategy(PromptStrategyBase):
    """Reflection prompting with self-critique and refinement."""
    
    def supports_complexity(self, complexity: ComponentComplexity) -> bool:
        return complexity in [ComponentComplexity.COMPLEX, ComponentComplexity.ARCHITECTURAL]
    
    def generate_system_prompt(self, context: PromptContext) -> str:
        base_prompt = self._build_base_system_prompt(context)
        
        reflection_instructions = """
CRITICAL: Use Reflection-based reasoning with self-critique.

REFLECTION PROCESS:
1. INITIAL SOLUTION: Generate your first implementation
2. CRITICAL ANALYSIS: Critically evaluate your solution
3. IDENTIFY ISSUES: Find potential problems, improvements, or missing elements
4. REFINED SOLUTION: Provide an improved version addressing the critiques

REFLECTION FORMAT:
## Initial Implementation
[Provide your first solution with reasoning]

## Critical Analysis
[Critically evaluate your solution, considering:]
- Code quality and maintainability
- Performance implications
- Accessibility compliance
- Design system adherence
- Error handling and edge cases
- User experience considerations

## Identified Issues & Improvements
[List specific issues found and potential improvements]

## Refined Implementation  
[Provide the improved solution addressing all identified issues]

Be honest in your self-critique and strive for excellence in the refined version."""

        return f"{base_prompt}\n\n{reflection_instructions}"
    
    def generate_user_prompt(self, context: PromptContext) -> str:
        previous_attempts_context = ""
        if context.previous_attempts:
            previous_attempts_context = f"""
PREVIOUS ATTEMPTS (learn from these):
{self._format_previous_attempts(context.previous_attempts)}
"""

        return f"""
REQUEST: {context.user_request}

{previous_attempts_context}

REFLECTION REQUIREMENTS:
- Be critically honest about your initial solution
- Consider both technical and UX perspectives
- Look for edge cases and potential failure modes
- Ensure the refined solution addresses all critiques
- Validate against project standards and best practices

Use the Reflection format to show your complete thought process."""
    
    def _build_base_system_prompt(self, context: PromptContext) -> str:
        """Build base system prompt (similar to ChainOfThoughtStrategy)."""
        return f"""You are a Senior Frontend Architect with expertise in React/TypeScript and UX design.

PROJECT CONTEXT:
{self._format_project_context(context)}

DESIGN SYSTEM:
{self._format_design_tokens(context.design_tokens)}

AVAILABLE COMPONENTS:
{self._format_available_components(context.available_components)}

QUALITY STANDARDS:
- Production-ready code with comprehensive error handling
- Exceptional TypeScript type safety and developer experience
- Comprehensive accessibility (WCAG {context.accessibility_level.upper()})
- Performance-optimized with monitoring considerations
- Pixel-perfect design system implementation
- Maintainable and extensible architecture"""
    
    def _format_previous_attempts(self, attempts: List[str]) -> str:
        """Format previous attempts for learning."""
        formatted_attempts = []
        for i, attempt in enumerate(attempts[-3:], 1):  # Show last 3 attempts
            formatted_attempts.append(f"Attempt {i}: {attempt[:200]}..." if len(attempt) > 200 else f"Attempt {i}: {attempt}")
        
        return '\n'.join(formatted_attempts)
    
    def _format_project_context(self, context: PromptContext) -> str:
        """Format project context (reuse from ChainOfThoughtStrategy)."""
        project = context.project_context
        return f"Framework: {project.get('framework', 'React')}\nStyling: {project.get('styling', 'Tailwind CSS')}\nTypeScript: {project.get('typescript', True)}"
    
    def _format_design_tokens(self, design_tokens: Dict[str, Any]) -> str:
        """Format design tokens (reuse from ChainOfThoughtStrategy)."""
        if not design_tokens:
            return "No specific design tokens detected"
        
        sections = []
        if design_tokens.get('colors'):
            colors = design_tokens['colors']
            color_list = list(colors.keys())[:8] if isinstance(colors, dict) else colors[:8]
            sections.append(f"Colors: {', '.join(color_list)}")
        
        return '\n'.join(sections) if sections else "Custom design system detected"
    
    def _format_available_components(self, components: List[Dict[str, Any]]) -> str:
        """Format available components (reuse from ChainOfThoughtStrategy)."""
        if not components:
            return "No existing components detected"
        
        component_summaries = []
        for comp in components[:10]:
            name = comp.get('name', 'Unknown')
            purpose = comp.get('purpose', 'General component')
            props_count = len(comp.get('props', []))
            summary = f"- {name}: {purpose} ({props_count} props)"
            component_summaries.append(summary)
        
        return '\n'.join(component_summaries)


class RoleBasedStrategy(PromptStrategyBase):
    """Role-based prompting with specialized expert perspectives."""
    
    def __init__(self):
        self.roles = {
            'ux_designer': 'UX Designer focusing on user experience and interaction design',
            'accessibility_expert': 'Accessibility Expert ensuring WCAG compliance and inclusive design',
            'performance_optimizer': 'Performance Expert optimizing for Core Web Vitals and efficiency',
            'frontend_architect': 'Frontend Architect designing scalable and maintainable code structure'
        }
    
    def supports_complexity(self, complexity: ComponentComplexity) -> bool:
        return True  # Role-based can work for any complexity
    
    def generate_system_prompt(self, context: PromptContext) -> str:
        roles_needed = self._determine_roles_needed(context)
        
        base_prompt = self._build_base_system_prompt(context)
        
        role_instructions = f"""
CRITICAL: Use Role-Based collaborative approach.

COLLABORATIVE ROLES ({len(roles_needed)} experts):
{self._format_roles(roles_needed)}

COLLABORATION PROCESS:
1. Each expert provides their perspective on the requirements
2. Identify potential conflicts between different expert viewpoints
3. Synthesize a solution that addresses all expert concerns
4. Validate the final solution against each expert's criteria

EXPERT CONSULTATION FORMAT:
## Expert Perspectives

{self._generate_expert_prompts(roles_needed)}

## Synthesis & Resolution
[Address any conflicts between expert viewpoints and create unified solution]

## Final Implementation
[Complete implementation addressing all expert requirements]

Ensure all expert perspectives are genuinely considered and integrated."""

        return f"{base_prompt}\n\n{role_instructions}"
    
    def generate_user_prompt(self, context: PromptContext) -> str:
        return f"""
REQUEST: {context.user_request}

EXPERT CONSULTATION REQUIREMENTS:
- Genuinely consider each expert's perspective
- Address potential conflicts between different viewpoints
- Ensure the final solution meets all expert criteria
- Explain how you've integrated different expert requirements

Use the Expert Consultation format to show collaborative reasoning."""
    
    def _determine_roles_needed(self, context: PromptContext) -> List[str]:
        """Determine which expert roles are needed based on context."""
        roles = ['frontend_architect']  # Always include architect
        
        # Add UX designer for interactive components
        if any(keyword in context.user_request.lower() for keyword in ['form', 'button', 'modal', 'navigation', 'dashboard']):
            roles.append('ux_designer')
        
        # Add accessibility expert for public-facing components
        if context.accessibility_level in ['aa', 'aaa'] or any(keyword in context.user_request.lower() for keyword in ['form', 'button', 'navigation']):
            roles.append('accessibility_expert')
        
        # Add performance optimizer for complex components
        if context.component_complexity in [ComponentComplexity.COMPLEX, ComponentComplexity.ARCHITECTURAL]:
            roles.append('performance_optimizer')
        
        return roles
    
    def _format_roles(self, roles: List[str]) -> str:
        """Format the roles for the prompt."""
        formatted_roles = []
        for role in roles:
            role_description = self.roles.get(role, 'Expert')
            formatted_roles.append(f"- {role.replace('_', ' ').title()}: {role_description}")
        
        return '\n'.join(formatted_roles)
    
    def _generate_expert_prompts(self, roles: List[str]) -> str:
        """Generate specific prompts for each expert role."""
        expert_sections = []
        
        for role in roles:
            if role == 'ux_designer':
                expert_sections.append("""### UX Designer Perspective:
[Consider user journey, interaction patterns, visual hierarchy, and user feedback]""")
            
            elif role == 'accessibility_expert':
                expert_sections.append("""### Accessibility Expert Perspective:
[Evaluate WCAG compliance, keyboard navigation, screen reader support, and inclusive design]""")
            
            elif role == 'performance_optimizer':
                expert_sections.append("""### Performance Expert Perspective:
[Analyze bundle size impact, rendering performance, Core Web Vitals, and optimization opportunities]""")
            
            elif role == 'frontend_architect':
                expert_sections.append("""### Frontend Architect Perspective:
[Design code structure, maintainability, scalability, and integration with existing codebase]""")
        
        return '\n\n'.join(expert_sections)
    
    def _build_base_system_prompt(self, context: PromptContext) -> str:
        """Build base system prompt."""
        return f"""You are a collaborative team of Frontend Development Experts working together.

PROJECT CONTEXT:
Framework: {context.project_context.get('framework', 'React')}
Styling: {context.project_context.get('styling', 'Tailwind CSS')}
TypeScript: {context.project_context.get('typescript', True)}

DESIGN SYSTEM:
{self._format_design_tokens(context.design_tokens)}

COLLABORATION PRINCIPLES:
- Each expert provides genuine, specialized insights
- Different perspectives may conflict - address these thoughtfully
- The final solution must satisfy all expert requirements
- Quality over quick solutions - take time to integrate all viewpoints"""
    
    def _format_design_tokens(self, design_tokens: Dict[str, Any]) -> str:
        """Format design tokens."""
        if not design_tokens:
            return "No specific design tokens detected"
        
        sections = []
        if design_tokens.get('colors'):
            colors = design_tokens['colors']
            color_list = list(colors.keys())[:8] if isinstance(colors, dict) else colors[:8]
            sections.append(f"Colors: {', '.join(color_list)}")
        
        return '\n'.join(sections) if sections else "Custom design system detected"


class AdvancedPromptOrchestrator:
    """
    Orchestrates advanced prompting strategies based on component complexity and requirements.
    """
    
    def __init__(self):
        self.strategies = {
            PromptStrategy.CHAIN_OF_THOUGHT: ChainOfThoughtStrategy(),
            PromptStrategy.REFLECTION: ReflectionStrategy(), 
            PromptStrategy.ROLE_BASED: RoleBasedStrategy(),
        }
        
        self.complexity_analyzer = ComponentComplexityAnalyzer()
    
    @handle_errors(reraise=True)
    def orchestrate_generation(
        self, 
        user_request: str, 
        project_context: Dict[str, Any],
        previous_attempts: List[str] = None
    ) -> Tuple[str, str, PromptStrategy]:
        """
        Orchestrate the prompt generation process using the most appropriate strategy.
        
        Args:
            user_request: The user's component request
            project_context: Project context including design tokens, components, etc.
            previous_attempts: List of previous failed attempts (for reflection)
            
        Returns:
            Tuple of (system_prompt, user_prompt, strategy_used)
        """
        # Analyze component complexity
        complexity = self.complexity_analyzer.analyze_complexity(user_request, project_context)
        
        # Select optimal strategy
        strategy_type = self._select_strategy(complexity, previous_attempts)
        strategy = self.strategies[strategy_type]
        
        # Build context
        context = self._build_prompt_context(
            user_request, complexity, project_context, previous_attempts
        )
        
        # Generate prompts
        system_prompt = strategy.generate_system_prompt(context)
        user_prompt = strategy.generate_user_prompt(context)
        
        return system_prompt, user_prompt, strategy_type
    
    def _select_strategy(
        self, 
        complexity: ComponentComplexity, 
        previous_attempts: List[str] = None
    ) -> PromptStrategy:
        """Select the most appropriate prompting strategy."""
        
        # Use reflection if there have been previous attempts
        if previous_attempts and len(previous_attempts) > 0:
            if self.strategies[PromptStrategy.REFLECTION].supports_complexity(complexity):
                return PromptStrategy.REFLECTION
        
        # Use chain-of-thought for complex components
        if complexity in [ComponentComplexity.COMPLEX, ComponentComplexity.ARCHITECTURAL]:
            return PromptStrategy.CHAIN_OF_THOUGHT
        
        # Use role-based for moderate complexity with specific requirements
        if complexity == ComponentComplexity.MODERATE:
            return PromptStrategy.ROLE_BASED
        
        # Default to chain-of-thought for most cases
        return PromptStrategy.CHAIN_OF_THOUGHT
    
    def _build_prompt_context(
        self,
        user_request: str,
        complexity: ComponentComplexity,
        project_context: Dict[str, Any],
        previous_attempts: List[str] = None
    ) -> PromptContext:
        """Build comprehensive prompt context."""
        
        return PromptContext(
            user_request=user_request,
            component_complexity=complexity,
            project_context=project_context,
            design_tokens=project_context.get('design_tokens', {}),
            available_components=project_context.get('components', []),
            framework_patterns=project_context.get('framework_patterns', {}),
            previous_attempts=previous_attempts or [],
            quality_requirements=project_context.get('quality_requirements', {}),
            accessibility_level=project_context.get('accessibility_level', 'aa'),
            performance_requirements=project_context.get('performance_requirements', {})
        )


class ComponentComplexityAnalyzer:
    """Analyzes component complexity to determine optimal prompting strategy."""
    
    def __init__(self):
        self.complexity_indicators = {
            ComponentComplexity.SIMPLE: {
                'keywords': ['button', 'card', 'badge', 'avatar', 'icon', 'label', 'tag'],
                'max_features': 2,
                'has_state': False,
                'has_complex_interactions': False
            },
            ComponentComplexity.MODERATE: {
                'keywords': ['form', 'modal', 'dropdown', 'tabs', 'accordion', 'tooltip', 'slider'],
                'max_features': 5,
                'has_state': True,
                'has_complex_interactions': False
            },
            ComponentComplexity.COMPLEX: {
                'keywords': ['dashboard', 'table', 'chart', 'calendar', 'editor', 'gallery', 'wizard'],
                'max_features': 10,
                'has_state': True,
                'has_complex_interactions': True
            },
            ComponentComplexity.ARCHITECTURAL: {
                'keywords': ['page', 'layout', 'app', 'feature', 'module', 'system', 'platform'],
                'max_features': float('inf'),
                'has_state': True,
                'has_complex_interactions': True
            }
        }
    
    def analyze_complexity(self, user_request: str, project_context: Dict[str, Any]) -> ComponentComplexity:
        """Analyze the complexity of the requested component."""
        request_lower = user_request.lower()
        
        # Count complexity indicators
        complexity_scores = {}
        
        for complexity, indicators in self.complexity_indicators.items():
            score = 0
            
            # Check for keyword matches
            keyword_matches = sum(1 for keyword in indicators['keywords'] if keyword in request_lower)
            score += keyword_matches * 2
            
            # Check for feature complexity
            feature_indicators = self._extract_feature_indicators(request_lower)
            if len(feature_indicators) <= indicators['max_features']:
                score += 1
            
            # Check for state management indicators
            if indicators['has_state'] and self._has_state_indicators(request_lower):
                score += 1
            
            # Check for complex interaction indicators
            if indicators['has_complex_interactions'] and self._has_complex_interaction_indicators(request_lower):
                score += 1
            
            complexity_scores[complexity] = score
        
        # Return complexity with highest score
        return max(complexity_scores.items(), key=lambda x: x[1])[0]
    
    def _extract_feature_indicators(self, request: str) -> List[str]:
        """Extract feature indicators from the request."""
        feature_patterns = [
            'with', 'and', 'including', 'supports', 'handles', 'manages',
            'filter', 'sort', 'search', 'pagination', 'validation', 'animation'
        ]
        
        return [pattern for pattern in feature_patterns if pattern in request]
    
    def _has_state_indicators(self, request: str) -> bool:
        """Check if request indicates state management needs."""
        state_indicators = [
            'toggle', 'open', 'close', 'active', 'selected', 'checked',
            'value', 'input', 'change', 'update', 'manage', 'track'
        ]
        
        return any(indicator in request for indicator in state_indicators)
    
    def _has_complex_interaction_indicators(self, request: str) -> bool:
        """Check if request indicates complex interactions."""
        complex_indicators = [
            'drag', 'drop', 'resize', 'zoom', 'pan', 'gesture',
            'keyboard', 'shortcut', 'multi-select', 'bulk', 'batch'
        ]
        
        return any(indicator in request for indicator in complex_indicators)