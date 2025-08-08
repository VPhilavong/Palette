"""
Smart Component Context Injector for Intelligent Context-Aware Generation
Automatically injects relevant project context, patterns, and constraints into component generation prompts.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import json

from ..errors.decorators import handle_errors
from ..analysis.context import ProjectAnalyzer
from ..mcp.ui_library_manager import MCPUILibraryManager, UILibraryType
from ..intelligence.component_reuse_analyzer import ComponentReuseAnalyzer
from .composition_prompts import CompositionAwarePromptBuilder


class ContextInjectionLevel(Enum):
    """Levels of context injection depth."""
    MINIMAL = "minimal"         # Basic project info only
    STANDARD = "standard"       # Include patterns and conventions
    COMPREHENSIVE = "comprehensive"  # Full context including examples
    ADAPTIVE = "adaptive"       # Dynamically adjust based on request complexity


class ContextRelevanceScore(Enum):
    """Relevance scoring for context injection."""
    CRITICAL = 1.0      # Must include in prompt
    HIGH = 0.8          # Should include if space allows
    MEDIUM = 0.6        # Include if relevant to request
    LOW = 0.4           # Include only in comprehensive mode
    NEGLIGIBLE = 0.2    # Skip unless specifically needed


@dataclass
class ContextFragment:
    """A fragment of contextual information for injection."""
    content: str
    category: str                    # "patterns", "constraints", "examples", etc.
    relevance_score: float          # 0.0 to 1.0 relevance to current request
    priority: int                   # Order priority (1 = highest)
    source: str                     # Where this context came from
    word_count: int = 0             # For prompt length management
    dependencies: List[str] = field(default_factory=list)  # Other fragments this depends on


@dataclass
class SmartContextConfig:
    """Configuration for smart context injection."""
    injection_level: ContextInjectionLevel = ContextInjectionLevel.STANDARD
    max_context_words: int = 1000   # Maximum words to inject
    relevance_threshold: float = 0.6  # Minimum relevance to include
    include_examples: bool = True
    include_constraints: bool = True
    include_patterns: bool = True
    include_library_context: bool = True
    adaptive_filtering: bool = True  # Filter based on request complexity
    preserve_critical_context: bool = True  # Always include critical context


class SmartComponentContextInjector:
    """
    Intelligently injects relevant project context into component generation prompts.
    Analyzes the user request and project state to determine the most relevant context.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        
        # Initialize analysis components
        self.project_analyzer = ProjectAnalyzer()
        self.library_manager = MCPUILibraryManager(project_path)
        self.reuse_analyzer = ComponentReuseAnalyzer(project_path)
        self.composition_builder = CompositionAwarePromptBuilder(project_path)
        
        # Context cache for performance
        self.context_cache = {}
        self.last_analysis_time = 0
        
        # Initialize context extractors
        self._initialize_context_extractors()
    
    def _initialize_context_extractors(self):
        """Initialize context extraction patterns and rules."""
        self.context_extractors = {
            'styling_patterns': self._extract_styling_context,
            'component_patterns': self._extract_component_patterns,
            'import_patterns': self._extract_import_context,
            'library_constraints': self._extract_library_constraints,
            'project_structure': self._extract_project_structure_context,
            'design_tokens': self._extract_design_tokens_context,
            'accessibility_requirements': self._extract_accessibility_context,
            'performance_constraints': self._extract_performance_context,
            'testing_patterns': self._extract_testing_context
        }
        
        # Context relevance patterns for different request types
        self.relevance_patterns = {
            'styling_patterns': [
                (r'style|css|theme|color|spacing|layout', 0.9),
                (r'button|input|card|modal', 0.7),
                (r'component|ui', 0.5)
            ],
            'component_patterns': [
                (r'component|react|tsx?', 0.9),
                (r'hook|state|props', 0.8),
                (r'function|class|interface', 0.6)
            ],
            'import_patterns': [
                (r'import|module|package', 0.9),
                (r'component|library', 0.7),
                (r'react|next|vue', 0.8)
            ],
            'library_constraints': [
                (r'ui library|component library|design system', 0.9),
                (r'chakra|mui|antd|shadcn|tailwind', 0.8),
                (r'button|input|modal|form', 0.6)
            ],
            'accessibility_requirements': [
                (r'accessibility|a11y|aria|screen reader', 0.9),
                (r'keyboard|focus|tab', 0.8),
                (r'form|input|button|modal', 0.7)
            ]
        }
    
    @handle_errors(reraise=True)
    async def inject_smart_context(self, 
                                 user_request: str,
                                 base_prompt: str,
                                 config: Optional[SmartContextConfig] = None) -> str:
        """
        Inject smart context into a base prompt based on the user request.
        
        Args:
            user_request: User's component generation request
            base_prompt: Base prompt to enhance with context
            config: Configuration for context injection
            
        Returns:
            Enhanced prompt with relevant context injected
        """
        config = config or SmartContextConfig()
        
        print(f"🧠 Injecting smart context for: {user_request[:50]}...")
        
        # Analyze request complexity and adjust config if adaptive
        if config.injection_level == ContextInjectionLevel.ADAPTIVE:
            config = self._adapt_config_to_request(user_request, config)
        
        # Extract all relevant context fragments
        context_fragments = await self._extract_context_fragments(user_request, config)
        
        # Score and filter fragments based on relevance
        relevant_fragments = self._filter_fragments_by_relevance(
            context_fragments, user_request, config
        )
        
        # Optimize fragment selection within word limits
        selected_fragments = self._optimize_fragment_selection(
            relevant_fragments, config.max_context_words
        )
        
        # Build the enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            base_prompt, selected_fragments, user_request, config
        )
        
        print(f"   📊 Injected {len(selected_fragments)} context fragments")
        print(f"   📝 Total prompt length: {len(enhanced_prompt)} characters")
        
        return enhanced_prompt
    
    def _adapt_config_to_request(self, user_request: str, config: SmartContextConfig) -> SmartContextConfig:
        """Adapt configuration based on request complexity."""
        request_lower = user_request.lower()
        
        # Determine complexity factors
        complexity_indicators = [
            ('complex', 3), ('advanced', 3), ('custom', 2), ('interactive', 2),
            ('responsive', 2), ('accessible', 2), ('form', 2), ('animation', 3),
            ('compound', 3), ('multi-step', 3), ('dynamic', 2), ('reusable', 2)
        ]
        
        complexity_score = sum(
            weight for keyword, weight in complexity_indicators 
            if keyword in request_lower
        )
        
        # Adjust config based on complexity
        if complexity_score >= 6:
            config.injection_level = ContextInjectionLevel.COMPREHENSIVE
            config.max_context_words = 1500
        elif complexity_score >= 3:
            config.injection_level = ContextInjectionLevel.STANDARD
            config.max_context_words = 1000
        else:
            config.injection_level = ContextInjectionLevel.MINIMAL
            config.max_context_words = 500
        
        return config
    
    async def _extract_context_fragments(self, 
                                       user_request: str,
                                       config: SmartContextConfig) -> List[ContextFragment]:
        """Extract all relevant context fragments."""
        fragments = []
        
        # Get base project analysis
        project_context = self.project_analyzer.analyze_project(str(self.project_path))
        
        # Extract context from each category
        for category, extractor in self.context_extractors.items():
            try:
                category_fragments = await extractor(user_request, project_context, config)
                fragments.extend(category_fragments)
            except Exception as e:
                print(f"Warning: Failed to extract {category} context: {e}")
        
        return fragments
    
    async def _extract_styling_context(self, 
                                     user_request: str,
                                     project_context: Dict,
                                     config: SmartContextConfig) -> List[ContextFragment]:
        """Extract styling-related context."""
        fragments = []
        
        # Design tokens
        design_tokens = project_context.get('design_tokens', {})
        if design_tokens:
            colors = design_tokens.get('colors', {})
            if colors:
                color_list = list(colors.keys())[:8]  # Limit to avoid bloat
                fragment = ContextFragment(
                    content=f"Available colors: {', '.join(color_list)}",
                    category="styling_patterns",
                    relevance_score=self._calculate_relevance(user_request, 'styling_patterns'),
                    priority=2,
                    source="design_tokens",
                    word_count=len(color_list) + 2
                )
                fragments.append(fragment)
            
            # Spacing tokens
            spacing = design_tokens.get('spacing', {})
            if spacing:
                spacing_values = list(spacing.keys())[:6]
                fragment = ContextFragment(
                    content=f"Spacing scale: {', '.join(map(str, spacing_values))}",
                    category="styling_patterns",
                    relevance_score=self._calculate_relevance(user_request, 'styling_patterns'),
                    priority=3,
                    source="design_tokens",
                    word_count=len(spacing_values) + 3
                )
                fragments.append(fragment)
        
        # Styling system
        styling_system = project_context.get('styling_system', '')
        if styling_system:
            fragment = ContextFragment(
                content=f"Styling approach: {styling_system}",
                category="styling_patterns",
                relevance_score=0.8,
                priority=1,
                source="project_analysis",
                word_count=3
            )
            fragments.append(fragment)
        
        return fragments
    
    async def _extract_component_patterns(self,
                                        user_request: str,
                                        project_context: Dict,
                                        config: SmartContextConfig) -> List[ContextFragment]:
        """Extract component-related patterns."""
        fragments = []
        
        # Component naming patterns
        components = project_context.get('components', [])
        if components:
            # Analyze naming conventions
            naming_patterns = self._analyze_naming_patterns(components)
            if naming_patterns:
                fragment = ContextFragment(
                    content=f"Component naming: {naming_patterns}",
                    category="component_patterns",
                    relevance_score=0.9,
                    priority=1,
                    source="component_analysis",
                    word_count=len(naming_patterns.split()) + 2
                )
                fragments.append(fragment)
            
            # Export patterns
            export_patterns = self._analyze_export_patterns(components)
            if export_patterns:
                fragment = ContextFragment(
                    content=f"Export pattern: {export_patterns}",
                    category="component_patterns",
                    relevance_score=0.7,
                    priority=3,
                    source="component_analysis",
                    word_count=len(export_patterns.split()) + 2
                )
                fragments.append(fragment)
        
        return fragments
    
    async def _extract_import_context(self,
                                    user_request: str,
                                    project_context: Dict,
                                    config: SmartContextConfig) -> List[ContextFragment]:
        """Extract import-related context."""
        fragments = []
        
        # Available imports
        available_imports = project_context.get('available_imports', {})
        if available_imports:
            # UI components
            ui_components = available_imports.get('ui_components', [])
            if ui_components:
                component_list = ui_components[:8]  # Limit to most relevant
                fragment = ContextFragment(
                    content=f"Available UI components: {', '.join(component_list)}",
                    category="import_patterns",
                    relevance_score=self._calculate_relevance(user_request, 'component_patterns'),
                    priority=2,
                    source="available_imports",
                    word_count=len(component_list) + 3
                )
                fragments.append(fragment)
            
            # React hooks
            react_hooks = available_imports.get('react_hooks', [])
            if react_hooks and ('hook' in user_request.lower() or 'state' in user_request.lower()):
                hook_list = react_hooks[:6]
                fragment = ContextFragment(
                    content=f"Available hooks: {', '.join(hook_list)}",
                    category="import_patterns",
                    relevance_score=0.8,
                    priority=2,
                    source="available_imports",
                    word_count=len(hook_list) + 2
                )
                fragments.append(fragment)
        
        return fragments
    
    async def _extract_library_constraints(self,
                                         user_request: str,
                                         project_context: Dict,
                                         config: SmartContextConfig) -> List[ContextFragment]:
        """Extract UI library constraints and guidelines."""
        fragments = []
        
        try:
            # Get detected UI library
            ui_library = await self.library_manager.detect_project_ui_library()
            if ui_library:
                library_context = await self.library_manager.get_library_context(ui_library)
                if library_context:
                    # Library-specific guidelines
                    fragment = ContextFragment(
                        content=f"UI Library: {ui_library.value} - Follow {ui_library.value} patterns and conventions",
                        category="library_constraints",
                        relevance_score=0.9,
                        priority=1,
                        source="library_manager",
                        word_count=8
                    )
                    fragments.append(fragment)
                    
                    # Common components available
                    if hasattr(library_context, 'components') and library_context.components:
                        common_components = [comp.name for comp in library_context.components[:6]]
                        fragment = ContextFragment(
                            content=f"Library components available: {', '.join(common_components)}",
                            category="library_constraints",
                            relevance_score=0.7,
                            priority=3,
                            source="library_context",
                            word_count=len(common_components) + 3
                        )
                        fragments.append(fragment)
        
        except Exception as e:
            print(f"Warning: Could not extract library constraints: {e}")
        
        return fragments
    
    async def _extract_project_structure_context(self,
                                                user_request: str,
                                                project_context: Dict,
                                                config: SmartContextConfig) -> List[ContextFragment]:
        """Extract project structure context."""
        fragments = []
        
        # Framework information
        framework = project_context.get('framework', '')
        if framework:
            fragment = ContextFragment(
                content=f"Framework: {framework} - Follow {framework} conventions",
                category="project_structure",
                relevance_score=0.8,
                priority=2,
                source="project_analysis",
                word_count=6
            )
            fragments.append(fragment)
        
        # Project structure type
        structure_type = project_context.get('structure_type', '')
        if structure_type and structure_type != 'unknown':
            fragment = ContextFragment(
                content=f"Project structure: {structure_type}",
                category="project_structure",
                relevance_score=0.6,
                priority=4,
                source="project_analysis",
                word_count=3
            )
            fragments.append(fragment)
        
        return fragments
    
    async def _extract_design_tokens_context(self,
                                           user_request: str,
                                           project_context: Dict,
                                           config: SmartContextConfig) -> List[ContextFragment]:
        """Extract design tokens context."""
        fragments = []
        
        design_tokens = project_context.get('design_tokens', {})
        if not design_tokens:
            return fragments
        
        # Typography tokens
        typography = design_tokens.get('typography', {})
        if typography and ('text' in user_request.lower() or 'font' in user_request.lower()):
            font_sizes = list(typography.keys())[:5]
            fragment = ContextFragment(
                content=f"Typography scale: {', '.join(font_sizes)}",
                category="design_tokens",
                relevance_score=0.8,
                priority=2,
                source="design_tokens",
                word_count=len(font_sizes) + 2
            )
            fragments.append(fragment)
        
        return fragments
    
    async def _extract_accessibility_context(self,
                                           user_request: str,
                                           project_context: Dict,
                                           config: SmartContextConfig) -> List[ContextFragment]:
        """Extract accessibility requirements context."""
        fragments = []
        
        # Check if accessibility is relevant to the request
        a11y_keywords = ['accessible', 'a11y', 'aria', 'keyboard', 'screen reader', 'focus']
        is_a11y_relevant = any(keyword in user_request.lower() for keyword in a11y_keywords)
        
        # Form elements always need accessibility considerations
        form_keywords = ['input', 'form', 'button', 'select', 'checkbox', 'radio']
        is_form_element = any(keyword in user_request.lower() for keyword in form_keywords)
        
        if is_a11y_relevant or is_form_element:
            fragment = ContextFragment(
                content="Accessibility: Include ARIA attributes, keyboard navigation, and screen reader support",
                category="accessibility_requirements",
                relevance_score=0.9 if is_a11y_relevant else 0.7,
                priority=2,
                source="accessibility_guidelines",
                word_count=10
            )
            fragments.append(fragment)
        
        return fragments
    
    async def _extract_performance_context(self,
                                         user_request: str,
                                         project_context: Dict,
                                         config: SmartContextConfig) -> List[ContextFragment]:
        """Extract performance-related context."""
        fragments = []
        
        # Check for performance-relevant requests
        perf_keywords = ['optimize', 'performance', 'fast', 'efficient', 'lazy', 'memo']
        is_perf_relevant = any(keyword in user_request.lower() for keyword in perf_keywords)
        
        if is_perf_relevant:
            fragment = ContextFragment(
                content="Performance: Use React.memo, useMemo, useCallback for optimization",
                category="performance_constraints",
                relevance_score=0.8,
                priority=3,
                source="performance_guidelines",
                word_count=8
            )
            fragments.append(fragment)
        
        return fragments
    
    async def _extract_testing_context(self,
                                     user_request: str,
                                     project_context: Dict,
                                     config: SmartContextConfig) -> List[ContextFragment]:
        """Extract testing-related context."""
        fragments = []
        
        # Check for testing-relevant requests or if testable components needed
        test_keywords = ['test', 'testing', 'testable', 'spec']
        is_test_relevant = any(keyword in user_request.lower() for keyword in test_keywords)
        
        # Always consider testing for complex components
        complexity_keywords = ['form', 'modal', 'interactive', 'dynamic']
        needs_testing = any(keyword in user_request.lower() for keyword in complexity_keywords)
        
        if is_test_relevant or needs_testing:
            fragment = ContextFragment(
                content="Testing: Include data-testid attributes and consider component testing needs",
                category="testing_patterns",
                relevance_score=0.7 if is_test_relevant else 0.5,
                priority=4,
                source="testing_guidelines",
                word_count=9
            )
            fragments.append(fragment)
        
        return fragments
    
    def _calculate_relevance(self, user_request: str, category: str) -> float:
        """Calculate relevance score for a context category."""
        patterns = self.relevance_patterns.get(category, [])
        if not patterns:
            return 0.5  # Default relevance
        
        max_relevance = 0.0
        request_lower = user_request.lower()
        
        for pattern, base_score in patterns:
            if re.search(pattern, request_lower):
                max_relevance = max(max_relevance, base_score)
        
        return max_relevance
    
    def _filter_fragments_by_relevance(self, 
                                     fragments: List[ContextFragment],
                                     user_request: str,
                                     config: SmartContextConfig) -> List[ContextFragment]:
        """Filter fragments based on relevance threshold."""
        filtered = []
        
        for fragment in fragments:
            # Always include critical context
            if config.preserve_critical_context and fragment.relevance_score >= ContextRelevanceScore.CRITICAL.value:
                filtered.append(fragment)
                continue
            
            # Check relevance threshold
            if fragment.relevance_score >= config.relevance_threshold:
                filtered.append(fragment)
        
        # Sort by priority and relevance
        filtered.sort(key=lambda f: (f.priority, -f.relevance_score))
        
        return filtered
    
    def _optimize_fragment_selection(self, 
                                   fragments: List[ContextFragment],
                                   max_words: int) -> List[ContextFragment]:
        """Select optimal set of fragments within word limit."""
        if not fragments:
            return []
        
        # Greedy selection based on relevance/word ratio
        selected = []
        current_words = 0
        
        # Sort by value density (relevance per word)
        fragments_with_density = [
            (fragment, fragment.relevance_score / max(fragment.word_count, 1))
            for fragment in fragments
        ]
        fragments_with_density.sort(key=lambda x: x[1], reverse=True)
        
        for fragment, density in fragments_with_density:
            if current_words + fragment.word_count <= max_words:
                selected.append(fragment)
                current_words += fragment.word_count
            elif fragment.relevance_score >= ContextRelevanceScore.CRITICAL.value:
                # Force include critical context even if over limit
                selected.append(fragment)
                current_words += fragment.word_count
        
        # Sort selected fragments by priority for presentation
        selected.sort(key=lambda f: f.priority)
        
        return selected
    
    def _build_enhanced_prompt(self,
                             base_prompt: str,
                             context_fragments: List[ContextFragment],
                             user_request: str,
                             config: SmartContextConfig) -> str:
        """Build the final enhanced prompt with context."""
        if not context_fragments:
            return base_prompt
        
        # Group fragments by category
        categorized_fragments = {}
        for fragment in context_fragments:
            if fragment.category not in categorized_fragments:
                categorized_fragments[fragment.category] = []
            categorized_fragments[fragment.category].append(fragment)
        
        # Build context sections
        context_sections = []
        
        for category, fragments in categorized_fragments.items():
            if not fragments:
                continue
            
            category_title = category.replace('_', ' ').title()
            section_content = [f"### {category_title}"]
            
            for fragment in fragments:
                section_content.append(f"- {fragment.content}")
            
            context_sections.append('\n'.join(section_content))
        
        # Build the final prompt
        if context_sections:
            context_block = f"""
## Project Context

{chr(10).join(context_sections)}

---

"""
            enhanced_prompt = base_prompt + context_block
        else:
            enhanced_prompt = base_prompt
        
        return enhanced_prompt
    
    def _analyze_naming_patterns(self, components: List[Dict]) -> str:
        """Analyze component naming patterns."""
        if not components:
            return ""
        
        names = [comp.get('name', '') for comp in components if comp.get('name')]
        if not names:
            return ""
        
        # Check for common patterns
        patterns = []
        
        # PascalCase
        if all(name[0].isupper() and not '_' in name for name in names if name):
            patterns.append("PascalCase")
        
        # Component suffix
        if any(name.endswith('Component') for name in names):
            patterns.append("Component suffix")
        
        # Prefixes
        prefixes = set()
        for name in names:
            if len(name) > 2 and name[0].isupper():
                # Look for common prefixes
                for prefix_len in [2, 3, 4]:
                    if len(name) > prefix_len:
                        prefix = name[:prefix_len]
                        if sum(1 for n in names if n.startswith(prefix)) >= 2:
                            prefixes.add(prefix)
        
        if prefixes:
            patterns.append(f"Common prefixes: {', '.join(sorted(prefixes))}")
        
        return ', '.join(patterns) if patterns else "PascalCase"
    
    def _analyze_export_patterns(self, components: List[Dict]) -> str:
        """Analyze component export patterns."""
        # This would need more sophisticated analysis of actual component files
        # For now, return common patterns
        return "default export"