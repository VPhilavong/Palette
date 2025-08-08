"""
Component Reuse Analyzer for intelligent component reuse and composition decisions.
Analyzes existing project components to determine reuse opportunities before generation.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json
import difflib

from ..errors.decorators import handle_errors
from .component_mapper import ComponentRelationshipEngine, ComponentInfo
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..mcp.ui_library_manager import MCPUILibraryManager, UILibraryType
    from ..mcp.ui_library_server_base import UILibraryContext, UIComponent
else:
    # Lazy imports to avoid circular dependency
    MCPUILibraryManager = None
    UILibraryType = None
    UILibraryContext = None
    UIComponent = None


class ReuseOpportunityType(Enum):
    """Types of component reuse opportunities."""
    EXACT_MATCH = "exact_match"          # Component exists that exactly matches need
    CLOSE_MATCH = "close_match"          # Component exists with minor differences
    COMPOSITION = "composition"          # Multiple components can be combined
    EXTENSION = "extension"              # Existing component can be extended/modified
    PATTERN_MATCH = "pattern_match"      # Similar patterns exist for reference
    NO_MATCH = "no_match"               # No suitable components found


@dataclass
class ComponentMatch:
    """Represents a potential component reuse match."""
    component: ComponentInfo
    match_type: ReuseOpportunityType
    confidence: float                    # 0.0 to 1.0 confidence score
    semantic_similarity: float           # How similar the purpose/intent is
    structural_similarity: float         # How similar the code structure is
    api_compatibility: float             # How compatible the props/API is
    reasoning: str                       # Explanation of why this is a match
    usage_example: Optional[str] = None  # How to use the existing component
    modifications_needed: List[str] = field(default_factory=list)  # What changes needed
    related_components: List[str] = field(default_factory=list)    # Other components to consider
    library_component: Optional[Any] = None  # Associated UI library component
    library_context: Optional[str] = None            # UI library context for this match


@dataclass
class CompositionOpportunity:
    """Represents an opportunity to compose multiple existing components."""
    components: List[ComponentInfo]
    composition_type: str                # "wrapper", "layout", "aggregate"
    confidence: float
    reasoning: str
    composition_template: str            # Template for how to combine them
    benefits: List[str] = field(default_factory=list)


@dataclass
class ReuseAnalysisResult:
    """Complete analysis of component reuse opportunities."""
    user_prompt: str
    intent_analysis: Dict[str, Any]      # Analyzed user intent
    exact_matches: List[ComponentMatch] = field(default_factory=list)
    close_matches: List[ComponentMatch] = field(default_factory=list)
    composition_opportunities: List[CompositionOpportunity] = field(default_factory=list)
    extension_opportunities: List[ComponentMatch] = field(default_factory=list)
    pattern_references: List[ComponentMatch] = field(default_factory=list)
    analysis_confidence: float = 0.0     # Overall confidence in analysis
    recommendation: str = ""             # Primary recommendation
    reasoning: str = ""                  # Why this recommendation was made


class ComponentReuseAnalyzer:
    """
    Intelligent component reuse analyzer that determines the best strategy
    for leveraging existing components before generating new ones.
    Enhanced with MCP UI library integration for library-aware component matching.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        
        # Initialize existing systems
        self.component_mapper = ComponentRelationshipEngine(str(project_path))
        self.search_index = self._initialize_search_index()
        
        # Initialize MCP UI library integration
        self.library_manager = None
        self.detected_library = None
        self.library_context = None
        
        # Initialize MCP integration lazily
        self._init_mcp_integration(str(project_path))
        
        # Build search index from discovered components
        self._build_search_index()
        
        # Initialize intent analysis patterns
        self._initialize_intent_patterns()
        
        # Component fingerprinting for better matching
        self._build_component_fingerprints()
        
        # Note: Library context will be initialized lazily during first analysis
    
    def _init_mcp_integration(self, project_path: str):
        """Initialize MCP integration with lazy imports."""
        try:
            from ..mcp.ui_library_manager import MCPUILibraryManager, UILibraryType
            from ..mcp.ui_library_server_base import UILibraryContext, UIComponent
            
            # Store the imported types
            global MCPUILibraryManager, UILibraryType, UILibraryContext, UIComponent
            
            self.library_manager = MCPUILibraryManager(project_path)
            self.detected_library = None
            self.library_context = None
            
        except ImportError as e:
            print(f"⚠️ MCP integration unavailable: {e}")
            self.library_manager = None
    
    def _initialize_search_index(self):
        """Initialize search index with lazy import to avoid circular dependency."""
        try:
            from ..generation.enhanced_prompts import ComponentSearchIndex
            return ComponentSearchIndex()
        except ImportError:
            # Fallback to a simple dict-based index if enhanced prompts not available
            return {}
    
    async def _initialize_library_context(self):
        """Initialize UI library context for enhanced component matching."""
        if not self.library_manager:
            print("   MCP integration unavailable - using generic analysis")
            return
            
        try:
            print("🎯 Initializing UI library context for component reuse analysis...")
            
            # Detect project UI library
            self.detected_library = await self.library_manager.detect_project_ui_library()
            
            if self.detected_library:
                print(f"   Detected UI library: {self.detected_library.value}")
                
                # Get library context
                self.library_context = await self.library_manager.get_library_context(self.detected_library)
                
                if self.library_context:
                    print(f"   Loaded {len(self.library_context.components)} library components")
                    print(f"   Available design tokens: {list(self.library_context.design_tokens.keys())[:5]}")
                else:
                    print("   Warning: Could not load library context")
            else:
                print("   No specific UI library detected - using generic analysis")
        
        except Exception as e:
            print(f"   Warning: Library context initialization failed: {e}")
    
    def _build_search_index(self):
        """Build searchable index from existing components."""
        if isinstance(self.search_index, dict):
            # Simple fallback indexing
            for name, component in self.component_mapper.components.items():
                self.search_index[name] = component
            return
        
        # Full enhanced indexing
        try:
            from ..generation.enhanced_prompts import ComponentExample
            
            for name, component in self.component_mapper.components.items():
                try:
                    # Read component source code
                    component_path = self.project_path / component.path
                    if component_path.exists():
                        with open(component_path, 'r', encoding='utf-8') as f:
                            source_code = f.read()
                        
                        # Create ComponentExample for search index
                        example = ComponentExample(
                            name=component.name,
                            file_path=component.path,
                            source_code=source_code,
                            props=component.props,
                            styling_patterns=self._extract_styling_patterns(source_code),
                            complexity_score=self._calculate_complexity(source_code)
                        )
                        
                        self.search_index.add_component(example)
                except Exception as e:
                    print(f"Warning: Could not index component {name}: {e}")
        except ImportError:
            # Fallback to simple indexing
            for name, component in self.component_mapper.components.items():
                self.search_index[name] = component
    
    def _initialize_intent_patterns(self):
        """Initialize patterns for understanding user intent."""
        self.intent_keywords = {
            'button': ['button', 'btn', 'click', 'submit', 'action', 'cta'],
            'form': ['form', 'input', 'field', 'validation', 'submit'],
            'card': ['card', 'tile', 'panel', 'box', 'container'],
            'modal': ['modal', 'dialog', 'popup', 'overlay', 'lightbox'],
            'navigation': ['nav', 'menu', 'header', 'navbar', 'breadcrumb'],
            'layout': ['layout', 'grid', 'flex', 'container', 'wrapper'],
            'list': ['list', 'table', 'grid', 'collection', 'items'],
            'hero': ['hero', 'banner', 'jumbotron', 'landing', 'splash'],
            'pricing': ['pricing', 'plans', 'subscription', 'tier'],
        }
        
        self.ui_patterns = {
            'interactive': ['hover', 'click', 'active', 'focus', 'disabled'],
            'responsive': ['mobile', 'tablet', 'desktop', 'responsive', 'breakpoint'],
            'state': ['loading', 'error', 'success', 'pending', 'active'],
            'styling': ['theme', 'color', 'size', 'variant', 'style'],
        }
    
    def _build_component_fingerprints(self):
        """Build fingerprints for all components for better matching."""
        self.component_fingerprints = {}
        
        for name, component in self.component_mapper.components.items():
            fingerprint = self._generate_component_fingerprint(component)
            self.component_fingerprints[name] = fingerprint
    
    def _generate_component_fingerprint(self, component: ComponentInfo) -> Dict[str, Any]:
        """Generate a semantic fingerprint for a component."""
        fingerprint = {
            'name_tokens': self._tokenize_name(component.name),
            'prop_signature': sorted(component.props),
            'hook_usage': sorted(component.state_hooks),
            'type': component.type,
            'complexity_indicators': {
                'prop_count': len(component.props),
                'hook_count': len(component.state_hooks),
                'child_count': len(component.children_components),
            },
        }
        
        # Add semantic meaning from component usage
        if hasattr(component, 'source_code'):
            fingerprint['semantic_patterns'] = self._extract_semantic_patterns(component.source_code)
        
        return fingerprint
    
    def _tokenize_name(self, name: str) -> List[str]:
        """Tokenize component name into meaningful parts."""
        # Split camelCase and PascalCase
        tokens = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', name)
        return [token.lower() for token in tokens]
    
    def _extract_styling_patterns(self, source_code: str) -> List[str]:
        """Extract styling patterns from component source code."""
        patterns = []
        
        # Tailwind classes
        tailwind_matches = re.findall(r'className=["\'`]([^"\'`]+)["\'`]', source_code)
        for match in tailwind_matches:
            patterns.extend(match.split())
        
        # Chakra UI props
        chakra_props = re.findall(r'(\w+)=\{?["\']([^"\']*)["\']?\}?', source_code)
        for prop, value in chakra_props:
            if prop in ['bg', 'color', 'size', 'variant', 'colorScheme']:
                patterns.append(f"{prop}:{value}")
        
        # CSS-in-JS patterns
        css_patterns = re.findall(r'styled\.\w+|css`|emotion', source_code)
        patterns.extend(css_patterns)
        
        return list(set(patterns))
    
    def _extract_semantic_patterns(self, source_code: str) -> List[str]:
        """Extract semantic patterns that indicate component purpose."""
        patterns = []
        
        # JSX element patterns
        jsx_elements = re.findall(r'<(\w+)', source_code)
        patterns.extend(jsx_elements)
        
        # Event handler patterns
        event_handlers = re.findall(r'on(\w+)=', source_code)
        patterns.extend([f"handles:{handler.lower()}" for handler in event_handlers])
        
        # State patterns
        state_patterns = re.findall(r'useState\s*<([^>]+)>', source_code)
        patterns.extend([f"state:{pattern}" for pattern in state_patterns])
        
        # Form patterns
        if 'onSubmit' in source_code or 'handleSubmit' in source_code:
            patterns.append('purpose:form')
        
        # Navigation patterns
        if 'useRouter' in source_code or 'Link' in source_code:
            patterns.append('purpose:navigation')
        
        return list(set(patterns))
    
    def _calculate_complexity(self, source_code: str) -> int:
        """Calculate component complexity score."""
        complexity = 0
        
        # Lines of code
        complexity += len(source_code.split('\n')) // 10
        
        # Number of hooks
        hooks = len(re.findall(r'use\w+\s*\(', source_code))
        complexity += hooks * 2
        
        # Number of JSX elements
        jsx_elements = len(re.findall(r'<\w+', source_code))
        complexity += jsx_elements
        
        # Conditional rendering
        conditionals = len(re.findall(r'\{.*\?.*:.*\}|\{.*&&.*\}', source_code))
        complexity += conditionals * 3
        
        return min(complexity, 100)  # Cap at 100
    
    @handle_errors(reraise=True)
    async def analyze_reuse_opportunities(self, user_prompt: str) -> ReuseAnalysisResult:
        """
        Analyze component reuse opportunities for a given user prompt.
        
        Args:
            user_prompt: User's component generation request
            
        Returns:
            Comprehensive analysis of reuse opportunities
        """
        
        result = ReuseAnalysisResult(
            user_prompt=user_prompt,
            intent_analysis=self._analyze_user_intent(user_prompt)
        )
        
        print(f"🔍 Analyzing reuse opportunities for: '{user_prompt}'")
        
        # Ensure library context is initialized
        if self.detected_library is None:
            await self._initialize_library_context()
        
        # Step 1: Find library-aware exact matches
        result.exact_matches = await self._find_exact_matches(user_prompt, result.intent_analysis)
        
        # Step 2: Find library-aware close matches
        result.close_matches = await self._find_close_matches(user_prompt, result.intent_analysis)
        
        # Step 3: Find library-aware composition opportunities
        result.composition_opportunities = await self._find_composition_opportunities(user_prompt, result.intent_analysis)
        
        # Step 4: Find extension opportunities
        result.extension_opportunities = await self._find_extension_opportunities(user_prompt, result.intent_analysis)
        
        # Step 5: Find pattern references
        result.pattern_references = await self._find_pattern_references(user_prompt, result.intent_analysis)
        
        # Step 6: Calculate overall confidence and recommendation
        result.analysis_confidence = self._calculate_analysis_confidence(result)
        result.recommendation, result.reasoning = self._generate_recommendation(result)
        
        print(f"   Found {len(result.exact_matches)} exact matches")
        print(f"   Found {len(result.close_matches)} close matches")
        print(f"   Found {len(result.composition_opportunities)} composition opportunities")
        print(f"   Overall confidence: {result.analysis_confidence:.1%}")
        
        return result
    
    def _analyze_user_intent(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze user intent from the prompt."""
        intent = {
            'primary_component_type': None,
            'secondary_types': [],
            'features': [],
            'styling_hints': [],
            'interaction_patterns': [],
            'keywords': [],
        }
        
        prompt_lower = user_prompt.lower()
        words = re.findall(r'\w+', prompt_lower)
        
        # Primary component type detection
        for component_type, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    if not intent['primary_component_type']:
                        intent['primary_component_type'] = component_type
                    else:
                        intent['secondary_types'].append(component_type)
                    break
        
        # Feature detection
        for pattern_type, keywords in self.ui_patterns.items():
            found_features = [kw for kw in keywords if kw in prompt_lower]
            if found_features:
                intent['features'].extend(found_features)
        
        # Extract styling hints
        styling_words = ['primary', 'secondary', 'large', 'small', 'red', 'blue', 'dark', 'light']
        intent['styling_hints'] = [word for word in words if word in styling_words]
        
        # Extract interaction patterns
        interaction_words = ['click', 'hover', 'submit', 'toggle', 'open', 'close']
        intent['interaction_patterns'] = [word for word in words if word in interaction_words]
        
        intent['keywords'] = list(set(words))
        
        return intent
    
    async def _find_exact_matches(self, user_prompt: str, intent: Dict[str, Any]) -> List[ComponentMatch]:
        """Find components that exactly match the user's request."""
        matches = []
        
        primary_type = intent['primary_component_type']
        if not primary_type:
            return matches
        
        # Look for components with matching names and purposes
        for name, component in self.component_mapper.components.items():
            name_tokens = self._tokenize_name(component.name)
            
            # Check if component name contains the primary type
            if primary_type in name_tokens or any(kw in name_tokens for kw in self.intent_keywords[primary_type]):
                
                # Calculate similarity scores
                semantic_sim = await self._calculate_enhanced_semantic_similarity(user_prompt, component)
                structural_sim = await self._calculate_enhanced_structural_similarity(intent, component)
                api_sim = await self._calculate_enhanced_api_compatibility(intent, component)
                
                overall_confidence = (semantic_sim * 0.5 + structural_sim * 0.3 + api_sim * 0.2)
                
                if overall_confidence >= 0.85:  # High threshold for exact matches
                    # Check for associated UI library component
                    library_component, library_context_info = await self._get_library_component_match(component, primary_type)
                    
                    match = ComponentMatch(
                        component=component,
                        match_type=ReuseOpportunityType.EXACT_MATCH,
                        confidence=overall_confidence,
                        semantic_similarity=semantic_sim,
                        structural_similarity=structural_sim,
                        api_compatibility=api_sim,
                        reasoning=f"Component '{component.name}' appears to be an exact match for {primary_type}",
                        usage_example=await self._generate_enhanced_usage_example(component, intent),
                        library_component=library_component,
                        library_context=library_context_info
                    )
                    matches.append(match)
        
        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:3]  # Return top 3 exact matches
    
    async def _find_close_matches(self, user_prompt: str, intent: Dict[str, Any]) -> List[ComponentMatch]:
        """Find components that are close matches with minor differences."""
        matches = []
        
        for name, component in self.component_mapper.components.items():
            semantic_sim = await self._calculate_enhanced_semantic_similarity(user_prompt, component)
            structural_sim = await self._calculate_enhanced_structural_similarity(intent, component)
            api_sim = await self._calculate_enhanced_api_compatibility(intent, component)
            
            overall_confidence = (semantic_sim * 0.5 + structural_sim * 0.3 + api_sim * 0.2)
            
            # Close matches are between 0.65 and 0.85 confidence
            if 0.65 <= overall_confidence < 0.85:
                modifications = await self._identify_library_aware_modifications(intent, component)
                library_component, library_context_info = await self._get_library_component_match(component, intent.get('primary_component_type'))
                
                match = ComponentMatch(
                    component=component,
                    match_type=ReuseOpportunityType.CLOSE_MATCH,
                    confidence=overall_confidence,
                    semantic_similarity=semantic_sim,
                    structural_similarity=structural_sim,
                    api_compatibility=api_sim,
                    reasoning=f"Component '{component.name}' is similar but may need minor modifications",
                    modifications_needed=modifications,
                    usage_example=await self._generate_enhanced_usage_example(component, intent),
                    library_component=library_component,
                    library_context=library_context_info
                )
                matches.append(match)
        
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:5]  # Return top 5 close matches
    
    async def _find_composition_opportunities(self, user_prompt: str, intent: Dict[str, Any]) -> List[CompositionOpportunity]:
        """Find opportunities to compose multiple existing components."""
        opportunities = []
        
        # Look for components that could be composed together
        primary_type = intent.get('primary_component_type')
        if not primary_type:
            return opportunities
        
        # Find components that are commonly used together
        related_components = []
        for name, component in self.component_mapper.components.items():
            # Check if this component is commonly used with the primary type
            if self._are_components_related(primary_type, component):
                related_components.append(component)
        
        # Generate composition opportunities
        if len(related_components) >= 2:
            # Group components by common usage patterns
            composition_groups = self._group_components_for_composition(related_components, intent)
            
            for group in composition_groups:
                if len(group) >= 2:
                    confidence = self._calculate_composition_confidence(group, intent)
                    
                    if confidence >= 0.7:
                        opportunity = CompositionOpportunity(
                            components=group,
                            composition_type=self._determine_composition_type(group),
                            confidence=confidence,
                            reasoning=f"Components {[c.name for c in group]} can be composed for {primary_type}",
                            composition_template=self._generate_composition_template(group, intent),
                            benefits=[
                                "Reuses existing components",
                                "Maintains design consistency",
                                "Reduces code duplication"
                            ]
                        )
                        opportunities.append(opportunity)
        
        opportunities.sort(key=lambda o: o.confidence, reverse=True)
        return opportunities[:3]  # Return top 3 composition opportunities
    
    async def _find_extension_opportunities(self, user_prompt: str, intent: Dict[str, Any]) -> List[ComponentMatch]:
        """Find components that could be extended or modified."""
        matches = []
        
        for name, component in self.component_mapper.components.items():
            semantic_sim = self._calculate_semantic_similarity(user_prompt, component)
            
            # Extension opportunities are components with moderate similarity
            # that could be enhanced to meet the request
            if 0.5 <= semantic_sim < 0.7:
                extensions = self._identify_possible_extensions(intent, component)
                
                if extensions:
                    match = ComponentMatch(
                        component=component,
                        match_type=ReuseOpportunityType.EXTENSION,
                        confidence=semantic_sim * 0.8,  # Reduce confidence for extensions
                        semantic_similarity=semantic_sim,
                        structural_similarity=0.0,  # Will change with extension
                        api_compatibility=0.0,      # Will change with extension
                        reasoning=f"Component '{component.name}' could be extended to meet requirements",
                        modifications_needed=extensions,
                        usage_example=self._generate_extension_example(component, intent, extensions)
                    )
                    matches.append(match)
        
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:3]  # Return top 3 extension opportunities
    
    async def _find_pattern_references(self, user_prompt: str, intent: Dict[str, Any]) -> List[ComponentMatch]:
        """Find components that can serve as pattern references."""
        matches = []
        
        # Find components with similar patterns even if not directly reusable
        for name, component in self.component_mapper.components.items():
            pattern_sim = self._calculate_pattern_similarity(intent, component)
            
            if pattern_sim >= 0.4:
                match = ComponentMatch(
                    component=component,
                    match_type=ReuseOpportunityType.PATTERN_MATCH,
                    confidence=pattern_sim,
                    semantic_similarity=pattern_sim,
                    structural_similarity=0.0,
                    api_compatibility=0.0,
                    reasoning=f"Component '{component.name}' uses similar patterns",
                    usage_example=f"Reference {component.name} for similar implementation patterns"
                )
                matches.append(match)
        
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:5]  # Return top 5 pattern references
    
    def _calculate_semantic_similarity(self, user_prompt: str, component: ComponentInfo) -> float:
        """Calculate semantic similarity between user request and component."""
        prompt_words = set(re.findall(r'\w+', user_prompt.lower()))
        
        # Component name similarity
        component_words = set(self._tokenize_name(component.name))
        name_overlap = len(prompt_words & component_words) / max(len(prompt_words), len(component_words))
        
        # Prop name similarity
        prop_words = set(word.lower() for prop in component.props for word in re.findall(r'\w+', prop))
        prop_overlap = len(prompt_words & prop_words) / max(len(prompt_words), 1)
        
        # Type similarity
        type_similarity = 0.5 if component.type in user_prompt.lower() else 0.0
        
        return (name_overlap * 0.6 + prop_overlap * 0.3 + type_similarity * 0.1)
    
    def _calculate_structural_similarity(self, intent: Dict[str, Any], component: ComponentInfo) -> float:
        """Calculate structural similarity based on component features."""
        score = 0.0
        
        # Feature matching
        intent_features = set(intent.get('features', []))
        if hasattr(component, 'features'):
            component_features = set(component.features)
            if intent_features and component_features:
                score += len(intent_features & component_features) / len(intent_features | component_features)
        
        # Hook usage similarity
        intent_interactions = intent.get('interaction_patterns', [])
        if intent_interactions and component.state_hooks:
            # Simple heuristic: interactive components often use state hooks
            score += 0.3 if component.state_hooks else 0.0
        
        return min(score, 1.0)
    
    def _calculate_api_compatibility(self, intent: Dict[str, Any], component: ComponentInfo) -> float:
        """Calculate API compatibility score."""
        # This is a simplified version - in practice, you'd analyze prop types and requirements
        prop_count = len(component.props)
        
        # Components with moderate prop counts are often more flexible
        if 2 <= prop_count <= 8:
            return 0.8
        elif prop_count <= 2:
            return 0.6
        else:
            return 0.4
    
    def _are_components_related(self, primary_type: str, component: ComponentInfo) -> bool:
        """Check if a component is related to the primary type."""
        # Define common relationships
        relationships = {
            'button': ['form', 'modal', 'card'],
            'form': ['input', 'button', 'validation'],
            'card': ['button', 'image', 'text'],
            'modal': ['button', 'form', 'overlay'],
            'navigation': ['link', 'dropdown', 'logo'],
        }
        
        related_types = relationships.get(primary_type, [])
        component_tokens = self._tokenize_name(component.name)
        
        return any(rel_type in component_tokens for rel_type in related_types)
    
    def _group_components_for_composition(self, components: List[ComponentInfo], intent: Dict[str, Any]) -> List[List[ComponentInfo]]:
        """Group components that could work well together."""
        # Simple grouping based on common usage patterns
        groups = []
        
        # Group by component relationships
        for component in components:
            best_group = None
            best_score = 0
            
            for group in groups:
                score = self._calculate_group_compatibility(component, group)
                if score > best_score and score > 0.5:
                    best_score = score
                    best_group = group
            
            if best_group:
                best_group.append(component)
            else:
                groups.append([component])
        
        return [group for group in groups if len(group) >= 2]
    
    def _calculate_group_compatibility(self, component: ComponentInfo, group: List[ComponentInfo]) -> float:
        """Calculate how well a component fits with a group."""
        if not group:
            return 0.0
        
        compatibility_score = 0.0
        
        # Check if component shares children with group members
        component_children = set(component.children_components)
        for group_member in group:
            member_children = set(group_member.children_components)
            if component_children & member_children:
                compatibility_score += 0.3
        
        # Check type compatibility
        if component.type == group[0].type:
            compatibility_score += 0.2
        
        return min(compatibility_score, 1.0)
    
    def _calculate_composition_confidence(self, components: List[ComponentInfo], intent: Dict[str, Any]) -> float:
        """Calculate confidence in a composition opportunity."""
        base_confidence = 0.5
        
        # More components = more complex but potentially more powerful
        component_bonus = min(len(components) * 0.1, 0.3)
        
        # Check if components cover different aspects of the request
        coverage_bonus = 0.2  # Simplified - would analyze how well components cover intent
        
        return min(base_confidence + component_bonus + coverage_bonus, 1.0)
    
    def _determine_composition_type(self, components: List[ComponentInfo]) -> str:
        """Determine the type of composition."""
        if any(comp.type == 'layout' for comp in components):
            return 'layout'
        elif len(components) > 3:
            return 'aggregate'
        else:
            return 'wrapper'
    
    def _generate_composition_template(self, components: List[ComponentInfo], intent: Dict[str, Any]) -> str:
        """Generate a template for composing components."""
        component_names = [comp.name for comp in components]
        
        template = f"""
// Composition using existing components
import {{ {', '.join(component_names)} }} from './components';

export const ComposedComponent = () => {{
  return (
    <{component_names[0]}>
      {chr(10).join(f'      <{name} />' for name in component_names[1:])}
    </{component_names[0]}>
  );
}};
"""
        return template.strip()
    
    def _identify_needed_modifications(self, intent: Dict[str, Any], component: ComponentInfo) -> List[str]:
        """Identify what modifications might be needed for a close match."""
        modifications = []
        
        # Check for missing features
        intent_features = intent.get('features', [])
        if 'responsive' in intent_features:
            modifications.append("Add responsive design support")
        
        if 'loading' in intent_features:
            modifications.append("Add loading state handling")
        
        # Check styling requirements
        styling_hints = intent.get('styling_hints', [])
        if styling_hints:
            modifications.append(f"Adjust styling for: {', '.join(styling_hints)}")
        
        return modifications
    
    def _identify_possible_extensions(self, intent: Dict[str, Any], component: ComponentInfo) -> List[str]:
        """Identify possible extensions for a component."""
        extensions = []
        
        intent_features = intent.get('features', [])
        
        # Suggest common extensions
        if 'interactive' in intent_features and not component.state_hooks:
            extensions.append("Add interactive state management")
        
        if 'responsive' in intent_features:
            extensions.append("Add responsive behavior")
        
        if intent.get('primary_component_type') == 'form' and 'validation' not in component.name.lower():
            extensions.append("Add form validation")
        
        return extensions
    
    def _calculate_pattern_similarity(self, intent: Dict[str, Any], component: ComponentInfo) -> float:
        """Calculate pattern similarity for reference purposes."""
        similarity = 0.0
        
        # Check for similar hooks usage
        if intent.get('interaction_patterns') and component.state_hooks:
            similarity += 0.3
        
        # Check for similar complexity
        target_complexity = len(intent.get('features', []))
        component_complexity = len(component.props) + len(component.state_hooks)
        
        if abs(target_complexity - component_complexity) <= 2:
            similarity += 0.2
        
        return similarity
    
    def _generate_usage_example(self, component: ComponentInfo, intent: Dict[str, Any]) -> str:
        """Generate a usage example for a component."""
        props_example = []
        
        # Generate example props based on component props and intent
        for prop in component.props[:5]:  # Limit to first 5 props
            if prop.lower() in ['children', 'child']:
                props_example.append(f"{prop}={{<span>Content</span>}}")
            elif prop.lower() in ['onclick', 'onsubmit', 'onchange']:
                props_example.append(f"{prop}={{handleAction}}")
            elif 'color' in prop.lower():
                color = intent.get('styling_hints', ['primary'])[0]
                props_example.append(f"{prop}='{color}'")
            elif 'size' in prop.lower():
                size = 'medium' if 'large' not in intent.get('styling_hints', []) else 'large'
                props_example.append(f"{prop}='{size}'")
            else:
                props_example.append(f"{prop}={{value}}")
        
        props_str = ' '.join(props_example)
        
        return f"""
import {{ {component.name} }} from '{component.path.replace('.tsx', '').replace('.jsx', '')}';

<{component.name} {props_str} />
""".strip()
    
    def _generate_extension_example(self, component: ComponentInfo, intent: Dict[str, Any], extensions: List[str]) -> str:
        """Generate an example of how to extend a component."""
        return f"""
// Extend existing {component.name}
import {{ {component.name} }} from '{component.path.replace('.tsx', '').replace('.jsx', '')}';

const Enhanced{component.name} = (props) => {{
  // Extensions: {', '.join(extensions)}
  return <{component.name} {{...props}} />;
}};
""".strip()
    
    def _calculate_analysis_confidence(self, result: ReuseAnalysisResult) -> float:
        """Calculate overall confidence in the reuse analysis."""
        weights = {
            'exact_matches': 0.4,
            'close_matches': 0.3,
            'composition_opportunities': 0.2,
            'extension_opportunities': 0.1,
        }
        
        confidence = 0.0
        
        if result.exact_matches:
            confidence += weights['exact_matches'] * max(m.confidence for m in result.exact_matches)
        
        if result.close_matches:
            confidence += weights['close_matches'] * max(m.confidence for m in result.close_matches)
        
        if result.composition_opportunities:
            confidence += weights['composition_opportunities'] * max(o.confidence for o in result.composition_opportunities)
        
        if result.extension_opportunities:
            confidence += weights['extension_opportunities'] * max(m.confidence for m in result.extension_opportunities)
        
        return min(confidence, 1.0)
    
    def _generate_recommendation(self, result: ReuseAnalysisResult) -> Tuple[str, str]:
        """Generate primary recommendation and reasoning."""
        
        # Priority order: Exact > Close > Composition > Extension > Pattern
        if result.exact_matches and result.exact_matches[0].confidence >= 0.9:
            best_match = result.exact_matches[0]
            return (
                f"REUSE:{best_match.component.name}",
                f"Found exact match '{best_match.component.name}' with {best_match.confidence:.1%} confidence"
            )
        
        elif result.close_matches and result.close_matches[0].confidence >= 0.75:
            best_match = result.close_matches[0]
            return (
                f"MODIFY:{best_match.component.name}",
                f"Component '{best_match.component.name}' is close match needing minor modifications"
            )
        
        elif result.composition_opportunities and result.composition_opportunities[0].confidence >= 0.7:
            best_comp = result.composition_opportunities[0]
            component_names = [c.name for c in best_comp.components]
            return (
                f"COMPOSE:{'+'.join(component_names)}",
                f"Compose {len(best_comp.components)} existing components: {', '.join(component_names)}"
            )
        
        elif result.extension_opportunities and result.extension_opportunities[0].confidence >= 0.6:
            best_ext = result.extension_opportunities[0]
            return (
                f"EXTEND:{best_ext.component.name}",
                f"Extend '{best_ext.component.name}' to meet requirements"
            )
        
        else:
            pattern_count = len(result.pattern_references)
            return (
                "GENERATE",
                f"Generate new component using {pattern_count} existing components as reference patterns"
            )
    
    def get_reuse_summary(self, result: ReuseAnalysisResult) -> str:
        """Generate a human-readable summary of reuse analysis."""
        lines = [
            f"Reuse Analysis for: '{result.user_prompt}'",
            f"Primary Intent: {result.intent_analysis.get('primary_component_type', 'Unknown')}",
            f"Overall Confidence: {result.analysis_confidence:.1%}",
            f"Recommendation: {result.recommendation}",
            "",
            f"Found Opportunities:",
        ]
        
        if result.exact_matches:
            lines.append(f"  • {len(result.exact_matches)} exact matches")
        
        if result.close_matches:
            lines.append(f"  • {len(result.close_matches)} close matches")
        
        if result.composition_opportunities:
            lines.append(f"  • {len(result.composition_opportunities)} composition opportunities")
        
        if result.extension_opportunities:
            lines.append(f"  • {len(result.extension_opportunities)} extension opportunities")
        
        if result.pattern_references:
            lines.append(f"  • {len(result.pattern_references)} pattern references")
        
        lines.append("")
        lines.append(f"Reasoning: {result.reasoning}")
        
        return "\n".join(lines)
    
    # Enhanced library-aware methods
    
    async def _get_library_component_match(self, component: ComponentInfo, component_type: Optional[str]) -> Tuple[Optional[Any], Optional[str]]:
        """Get matching UI library component and context."""
        if not self.library_context or not component_type or not self.library_manager:
            return None, None
        
        try:
            # Import UIComponent locally to avoid circular dependency
            from ..mcp.ui_library_server_base import UIComponent
            
            # Search for matching library component
            search_results = await self.library_manager.get_component_suggestions(
                component_type, self.detected_library
            )
            
            if search_results and "results" in search_results:
                # Find best matching library component
                for result in search_results["results"][:3]:  # Check top 3 results
                    lib_component_name = result.get("name", "").lower()
                    project_component_name = component.name.lower()
                    
                    # Simple name matching heuristic
                    if (component_type in lib_component_name and 
                        any(token in lib_component_name for token in self._tokenize_name(project_component_name))):
                        
                        ui_component = UIComponent(
                            name=result.get("name", ""),
                            description=result.get("description", ""),
                            category=result.get("category", ""),
                            props=result.get("props", []),
                            examples=result.get("examples", []),
                            accessibility_notes=result.get("accessibility", []),
                            styling_options=result.get("styling", {})
                        )
                        
                        context_info = f"Matches {self.detected_library.value} {result.get('name')} component"
                        return ui_component, context_info
            
        except Exception as e:
            print(f"Warning: Library component matching failed: {e}")
        
        return None, None
    
    async def _calculate_enhanced_semantic_similarity(self, user_prompt: str, component: ComponentInfo) -> float:
        """Enhanced semantic similarity calculation with library context."""
        # Start with base semantic similarity
        base_similarity = self._calculate_semantic_similarity(user_prompt, component)
        
        if not self.library_context:
            return base_similarity
        
        # Enhance with library-specific context
        enhancement = 0.0
        
        try:
            # Check if component aligns with library patterns
            component_tokens = set(self._tokenize_name(component.name))
            prompt_tokens = set(re.findall(r'\w+', user_prompt.lower()))
            
            # Check against library component names
            for lib_component in self.library_context.components:
                lib_tokens = set(self._tokenize_name(lib_component.name))
                
                # If project component aligns with library component that matches prompt
                if (lib_tokens & component_tokens and 
                    lib_tokens & prompt_tokens):
                    enhancement += 0.15
                    break
            
            # Check design token alignment
            if hasattr(component, 'styling_patterns'):
                design_tokens = self.library_context.design_tokens
                if "colors" in design_tokens:
                    color_names = set(design_tokens["colors"].keys() if isinstance(design_tokens["colors"], dict) else [])
                    component_colors = {pattern for pattern in component.styling_patterns 
                                     if any(color in pattern for color in color_names)}
                    if component_colors:
                        enhancement += 0.1
        
        except Exception as e:
            print(f"Warning: Enhanced semantic similarity calculation failed: {e}")
        
        return min(base_similarity + enhancement, 1.0)
    
    async def _calculate_enhanced_structural_similarity(self, intent: Dict[str, Any], component: ComponentInfo) -> float:
        """Enhanced structural similarity with library-aware analysis."""
        # Start with base structural similarity
        base_similarity = self._calculate_structural_similarity(intent, component)
        
        if not self.library_context:
            return base_similarity
        
        # Enhance with library-specific patterns
        enhancement = 0.0
        
        try:
            intent_features = set(intent.get('features', []))
            
            # Check if component follows library best practices
            if hasattr(component, 'source_code'):
                source_code = component.source_code
            else:
                # Try to read source code
                try:
                    component_path = self.project_path / component.path
                    if component_path.exists():
                        with open(component_path, 'r', encoding='utf-8') as f:
                            source_code = f.read()
                    else:
                        source_code = ""
                except:
                    source_code = ""
            
            # Check for library-specific imports
            if self.detected_library and hasattr(self.detected_library, 'value'):
                # Import UILibraryType locally
                try:
                    from ..mcp.ui_library_server_base import UILibraryType
                    library_imports = {
                        UILibraryType.CHAKRA_UI: ["@chakra-ui/react", "chakra-ui"],
                        UILibraryType.MATERIAL_UI: ["@mui/material", "@material-ui"],
                        UILibraryType.ANT_DESIGN: ["antd"],
                        UILibraryType.MANTINE: ["@mantine/core"],
                    }.get(self.detected_library, [])
                except ImportError:
                    library_imports = []
                
                if any(lib_import in source_code for lib_import in library_imports):
                    enhancement += 0.2
            
            # Check for responsive design patterns
            if 'responsive' in intent_features:
                responsive_patterns = ['breakpoint', 'responsive', 'mobile', 'tablet', 'desktop']
                if any(pattern in source_code.lower() for pattern in responsive_patterns):
                    enhancement += 0.15
        
        except Exception as e:
            print(f"Warning: Enhanced structural similarity calculation failed: {e}")
        
        return min(base_similarity + enhancement, 1.0)
    
    async def _calculate_enhanced_api_compatibility(self, intent: Dict[str, Any], component: ComponentInfo) -> float:
        """Enhanced API compatibility with library context awareness."""
        # Start with base API compatibility
        base_compatibility = self._calculate_api_compatibility(intent, component)
        
        if not self.library_context:
            return base_compatibility
        
        # Enhance with library-specific prop patterns
        enhancement = 0.0
        
        try:
            component_props = set(prop.lower() for prop in component.props)
            
            # Check for library-standard props
            library_standard_props = set()
            if self.detected_library and hasattr(self.detected_library, 'value'):
                try:
                    from ..mcp.ui_library_server_base import UILibraryType
                    library_standard_props = {
                        UILibraryType.CHAKRA_UI: {"colorscheme", "variant", "size", "isinvalid", "isdisabled"},
                        UILibraryType.MATERIAL_UI: {"variant", "color", "size", "disabled", "error"},
                        UILibraryType.ANT_DESIGN: {"type", "size", "disabled", "danger"},
                        UILibraryType.MANTINE: {"variant", "color", "size", "disabled", "radius"},
                    }.get(self.detected_library, set())
                except ImportError:
                    pass
            
            # Calculate overlap with library standards
            if library_standard_props:
                overlap = len(component_props & library_standard_props)
                if overlap > 0:
                    enhancement += min(overlap * 0.1, 0.3)
            
            # Check for TypeScript interface alignment
            if hasattr(component, 'typescript_interface'):
                enhancement += 0.1
        
        except Exception as e:
            print(f"Warning: Enhanced API compatibility calculation failed: {e}")
        
        return min(base_compatibility + enhancement, 1.0)
    
    async def _identify_library_aware_modifications(self, intent: Dict[str, Any], component: ComponentInfo) -> List[str]:
        """Identify modifications needed with library context awareness."""
        modifications = self._identify_needed_modifications(intent, component)
        
        if not self.library_context or not self.detected_library:
            return modifications
        
        try:
            # Add library-specific modification suggestions
            library_specific = []
            
            if self.detected_library and hasattr(self.detected_library, 'value'):
                try:
                    from ..mcp.ui_library_server_base import UILibraryType
                    
                    if self.detected_library == UILibraryType.CHAKRA_UI:
                        library_specific.extend([
                            "Ensure component uses Chakra UI theme tokens",
                            "Add responsive props using Chakra breakpoints",
                            "Use Chakra color scheme props for theming"
                        ])
                    elif self.detected_library == UILibraryType.MATERIAL_UI:
                        library_specific.extend([
                            "Apply Material Design principles and spacing",
                            "Use Material-UI theme palette colors",
                            "Implement Material Design elevation system"
                        ])
                    elif self.detected_library == UILibraryType.ANT_DESIGN:
                        library_specific.extend([
                            "Follow Ant Design component API patterns",
                            "Use Ant Design icon library consistently",
                            "Apply Ant Design form validation patterns"
                        ])
                except ImportError:
                    pass
            
            # Add relevant library-specific modifications
            component_type = intent.get('primary_component_type', '')
            if component_type in ['form', 'button', 'input']:
                modifications.extend(library_specific)
        
        except Exception as e:
            print(f"Warning: Library-aware modification identification failed: {e}")
        
        return list(set(modifications))  # Remove duplicates
    
    async def _generate_enhanced_usage_example(self, component: ComponentInfo, intent: Dict[str, Any]) -> str:
        """Generate enhanced usage example with library context."""
        base_example = self._generate_usage_example(component, intent)
        
        if not self.library_context or not self.detected_library:
            return base_example
        
        try:
            # Enhance example with library-specific best practices
            library_enhancements = {}
            if self.detected_library and hasattr(self.detected_library, 'value'):
                try:
                    from ..mcp.ui_library_server_base import UILibraryType
                    
                    library_enhancements = {
                        UILibraryType.CHAKRA_UI: {
                            "imports": "import { ChakraProvider } from '@chakra-ui/react';",
                            "wrapper": "// Wrap your app with ChakraProvider for theme access",
                            "props": "colorScheme='blue' size='md'"
                        },
                        UILibraryType.MATERIAL_UI: {
                            "imports": "import { ThemeProvider } from '@mui/material/styles';",
                            "wrapper": "// Wrap your app with ThemeProvider",
                            "props": "variant='contained' color='primary'"
                        },
                        UILibraryType.ANT_DESIGN: {
                            "imports": "import 'antd/dist/antd.css';",
                            "wrapper": "// Import Ant Design styles",
                            "props": "type='primary' size='middle'"
                        }
                    }
                except ImportError:
                    pass
            
            enhancement = library_enhancements.get(self.detected_library, {})
            if enhancement:
                enhanced_example = f"""
{enhancement.get('imports', '')}
{enhancement.get('wrapper', '')}

{base_example}

// Library-specific usage with {self.detected_library.value}
<{component.name} {enhancement.get('props', '')} />
""".strip()
                return enhanced_example
        
        except Exception as e:
            print(f"Warning: Enhanced usage example generation failed: {e}")
        
        return base_example