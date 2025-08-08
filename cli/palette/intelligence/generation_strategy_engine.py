"""
Generation Strategy Engine for autonomous component reuse decisions.
Determines the optimal strategy (REUSE/COMPOSE/EXTEND/GENERATE) based on reuse analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json

from ..errors.decorators import handle_errors
from .component_reuse_analyzer import (
    ComponentReuseAnalyzer, 
    ReuseAnalysisResult, 
    ComponentMatch, 
    CompositionOpportunity,
    ReuseOpportunityType
)
from .component_mapper import ComponentInfo


class GenerationStrategy(Enum):
    """Strategies for component generation/reuse."""
    REUSE = "reuse"                     # Use existing component directly
    COMPOSE = "compose"                 # Combine multiple existing components
    EXTEND = "extend"                   # Modify/extend existing component  
    GENERATE = "generate"               # Generate new with context
    GENERATE_FRESH = "generate_fresh"   # Generate completely new


@dataclass
class StrategyDecision:
    """A strategic decision about how to handle component generation."""
    strategy: GenerationStrategy
    confidence: float                   # 0.0 to 1.0 confidence in this decision
    primary_components: List[ComponentInfo] = field(default_factory=list)
    reasoning: str = ""
    implementation_details: Dict[str, Any] = field(default_factory=dict)
    user_message: str = ""              # Message to show user about decision
    import_statements: List[str] = field(default_factory=list)
    usage_example: str = ""
    benefits: List[str] = field(default_factory=list)
    considerations: List[str] = field(default_factory=list)


@dataclass
class StrategyConfig:
    """Configuration for strategy decision making."""
    # Confidence thresholds for automatic decisions
    reuse_threshold: float = 0.90       # Auto-reuse if confidence >= 90%
    compose_threshold: float = 0.75     # Auto-compose if confidence >= 75%
    extend_threshold: float = 0.60      # Auto-extend if confidence >= 60%
    
    # Preference weights
    prefer_reuse: bool = True           # Prefer reusing over generating
    prefer_composition: bool = True     # Prefer composing over extending
    max_composition_components: int = 4 # Max components in a composition
    
    # Quality requirements
    min_component_quality: float = 0.7  # Minimum quality score for reuse
    require_type_safety: bool = True    # Require TypeScript types if project uses TS


class GenerationStrategyEngine:
    """
    Intelligent strategy engine that autonomously decides the best approach
    for component generation based on comprehensive reuse analysis.
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.reuse_analyzer = None  # Will be set by UIGenerator
        
        # Decision logic mappings
        self._initialize_decision_logic()
    
    def _initialize_decision_logic(self):
        """Initialize decision logic and strategy mappings."""
        
        # Strategy priority order (higher number = higher priority)
        self.strategy_priorities = {
            GenerationStrategy.REUSE: 100,
            GenerationStrategy.COMPOSE: 80, 
            GenerationStrategy.EXTEND: 60,
            GenerationStrategy.GENERATE: 40,
            GenerationStrategy.GENERATE_FRESH: 20,
        }
        
        # Benefits for each strategy type
        self.strategy_benefits = {
            GenerationStrategy.REUSE: [
                "Zero code duplication",
                "Instant consistency with existing design",
                "Proven, tested component",
                "Immediate availability"
            ],
            GenerationStrategy.COMPOSE: [
                "Leverages multiple existing components",
                "Maintains design system consistency", 
                "Reduces development time",
                "Creates reusable patterns"
            ],
            GenerationStrategy.EXTEND: [
                "Builds on existing foundation",
                "Maintains core functionality",
                "Adds only necessary features",
                "Preserves design patterns"
            ],
            GenerationStrategy.GENERATE: [
                "Uses existing components as reference",
                "Follows established patterns",
                "Fills gaps in component library",
                "Maintains project consistency"
            ],
            GenerationStrategy.GENERATE_FRESH: [
                "Creates novel functionality",
                "No constraints from existing code",
                "Addresses unique requirements",
                "Expands component library"
            ]
        }
        
        # Considerations/warnings for each strategy
        self.strategy_considerations = {
            GenerationStrategy.REUSE: [
                "Ensure component API meets all requirements",
                "Check if styling matches design intent"
            ],
            GenerationStrategy.COMPOSE: [
                "Verify components work well together",
                "Consider composition complexity"
            ],
            GenerationStrategy.EXTEND: [
                "Changes may affect other users of base component",
                "Consider creating new component instead"
            ],
            GenerationStrategy.GENERATE: [
                "New component adds to maintenance burden",
                "Ensure it doesn't duplicate existing functionality"
            ],
            GenerationStrategy.GENERATE_FRESH: [
                "High development cost",
                "May introduce inconsistencies"
            ]
        }
    
    @handle_errors(reraise=True)
    def determine_strategy(self, 
                          reuse_analysis: ReuseAnalysisResult,
                          user_prompt: str,
                          project_context: Optional[Dict[str, Any]] = None) -> StrategyDecision:
        """
        Autonomously determine the best generation strategy based on reuse analysis.
        
        Args:
            reuse_analysis: Comprehensive reuse analysis results
            user_prompt: Original user prompt
            project_context: Additional project context
            
        Returns:
            Strategic decision with implementation details
        """
        
        print(f"🤖 Determining generation strategy...")
        print(f"   Analysis confidence: {reuse_analysis.analysis_confidence:.1%}")
        
        # Evaluate each strategy option
        strategy_candidates = []
        
        # 1. Evaluate REUSE strategy
        if reuse_analysis.exact_matches:
            reuse_decision = self._evaluate_reuse_strategy(reuse_analysis, user_prompt)
            if reuse_decision:
                strategy_candidates.append(reuse_decision)
        
        # 2. Evaluate COMPOSE strategy  
        if reuse_analysis.composition_opportunities:
            compose_decision = self._evaluate_compose_strategy(reuse_analysis, user_prompt)
            if compose_decision:
                strategy_candidates.append(compose_decision)
        
        # 3. Evaluate EXTEND strategy
        if reuse_analysis.close_matches or reuse_analysis.extension_opportunities:
            extend_decision = self._evaluate_extend_strategy(reuse_analysis, user_prompt)
            if extend_decision:
                strategy_candidates.append(extend_decision)
        
        # 4. Always consider GENERATE strategy as fallback
        generate_decision = self._evaluate_generate_strategy(reuse_analysis, user_prompt)
        strategy_candidates.append(generate_decision)
        
        # 5. Select best strategy based on confidence and preferences
        best_strategy = self._select_best_strategy(strategy_candidates, reuse_analysis)
        
        # 6. Enhance decision with implementation details
        enhanced_decision = self._enhance_decision_details(best_strategy, reuse_analysis, project_context)
        
        print(f"   Selected strategy: {enhanced_decision.strategy.value.upper()}")
        print(f"   Confidence: {enhanced_decision.confidence:.1%}")
        print(f"   Reasoning: {enhanced_decision.reasoning}")
        
        return enhanced_decision
    
    def _evaluate_reuse_strategy(self, analysis: ReuseAnalysisResult, user_prompt: str) -> Optional[StrategyDecision]:
        """Evaluate the REUSE strategy option."""
        
        if not analysis.exact_matches:
            return None
        
        best_match = analysis.exact_matches[0]  # Highest confidence exact match
        
        # Only consider reuse if confidence is above threshold
        if best_match.confidence < self.config.reuse_threshold:
            return None
        
        # Check component quality (simplified - could be more sophisticated)
        quality_score = self._assess_component_quality(best_match.component)
        if quality_score < self.config.min_component_quality:
            return None
        
        decision = StrategyDecision(
            strategy=GenerationStrategy.REUSE,
            confidence=best_match.confidence,
            primary_components=[best_match.component],
            reasoning=f"Found exact match '{best_match.component.name}' with {best_match.confidence:.1%} confidence",
            user_message=f"✅ Reusing existing {best_match.component.name} component",
            import_statements=[self._generate_import_statement(best_match.component)],
            usage_example=best_match.usage_example or self._generate_usage_example(best_match.component),
            benefits=self.strategy_benefits[GenerationStrategy.REUSE],
            considerations=self.strategy_considerations[GenerationStrategy.REUSE]
        )
        
        # Add reuse-specific implementation details
        decision.implementation_details = {
            'action': 'import_and_use',
            'component_path': best_match.component.path,
            'component_name': best_match.component.name,
            'props_available': best_match.component.props,
            'semantic_similarity': best_match.semantic_similarity,
            'api_compatibility': best_match.api_compatibility
        }
        
        return decision
    
    def _evaluate_compose_strategy(self, analysis: ReuseAnalysisResult, user_prompt: str) -> Optional[StrategyDecision]:
        """Evaluate the COMPOSE strategy option."""
        
        if not analysis.composition_opportunities:
            return None
        
        best_opportunity = analysis.composition_opportunities[0]  # Highest confidence
        
        # Only consider composition if confidence is above threshold
        if best_opportunity.confidence < self.config.compose_threshold:
            return None
        
        # Don't compose too many components (complexity management)
        if len(best_opportunity.components) > self.config.max_composition_components:
            return None
        
        component_names = [comp.name for comp in best_opportunity.components]
        
        decision = StrategyDecision(
            strategy=GenerationStrategy.COMPOSE,
            confidence=best_opportunity.confidence,
            primary_components=best_opportunity.components,
            reasoning=f"Composing {len(best_opportunity.components)} components: {', '.join(component_names)}",
            user_message=f"✅ Composing {len(best_opportunity.components)} existing components",
            import_statements=[self._generate_import_statement(comp) for comp in best_opportunity.components],
            usage_example=best_opportunity.composition_template,
            benefits=self.strategy_benefits[GenerationStrategy.COMPOSE] + best_opportunity.benefits,
            considerations=self.strategy_considerations[GenerationStrategy.COMPOSE]
        )
        
        decision.implementation_details = {
            'action': 'compose_components',
            'composition_type': best_opportunity.composition_type,
            'component_count': len(best_opportunity.components),
            'composition_template': best_opportunity.composition_template,
            'components': [
                {
                    'name': comp.name,
                    'path': comp.path,
                    'props': comp.props
                } for comp in best_opportunity.components
            ]
        }
        
        return decision
    
    def _evaluate_extend_strategy(self, analysis: ReuseAnalysisResult, user_prompt: str) -> Optional[StrategyDecision]:
        """Evaluate the EXTEND strategy option."""
        
        # Look for the best extension candidate from close matches or extension opportunities
        best_candidate = None
        best_confidence = 0.0
        
        # Check close matches that might be good extension candidates
        for match in analysis.close_matches:
            if match.confidence > best_confidence and match.confidence >= self.config.extend_threshold:
                best_candidate = match
                best_confidence = match.confidence
        
        # Check explicit extension opportunities
        for match in analysis.extension_opportunities:
            if match.confidence > best_confidence and match.confidence >= self.config.extend_threshold:
                best_candidate = match
                best_confidence = match.confidence
        
        if not best_candidate:
            return None
        
        modifications = best_candidate.modifications_needed or ["Enhance to meet specific requirements"]
        
        decision = StrategyDecision(
            strategy=GenerationStrategy.EXTEND,
            confidence=best_candidate.confidence * 0.9,  # Slightly reduce confidence for extensions
            primary_components=[best_candidate.component], 
            reasoning=f"Extending '{best_candidate.component.name}' with modifications: {', '.join(modifications[:2])}",
            user_message=f"✅ Extending existing {best_candidate.component.name} component",
            import_statements=[self._generate_import_statement(best_candidate.component)],
            usage_example=best_candidate.usage_example,
            benefits=self.strategy_benefits[GenerationStrategy.EXTEND],
            considerations=self.strategy_considerations[GenerationStrategy.EXTEND] + [
                f"Modifications needed: {', '.join(modifications)}"
            ]
        )
        
        decision.implementation_details = {
            'action': 'extend_component',
            'base_component': best_candidate.component.name,
            'base_path': best_candidate.component.path,
            'modifications_needed': modifications,
            'extension_type': best_candidate.match_type.value,
            'base_props': best_candidate.component.props
        }
        
        return decision
    
    def _evaluate_generate_strategy(self, analysis: ReuseAnalysisResult, user_prompt: str) -> StrategyDecision:
        """Evaluate the GENERATE strategy (always available as fallback)."""
        
        # Determine if we should generate with heavy context or fresh
        reference_components = []
        context_quality = 0.0
        
        # Collect reference components from pattern matches
        for pattern_match in analysis.pattern_references[:3]:  # Use top 3 pattern references
            reference_components.append(pattern_match.component)
            context_quality += pattern_match.confidence
        
        # Also include close matches as references
        for close_match in analysis.close_matches[:2]:  # Use top 2 close matches
            if close_match.component not in reference_components:
                reference_components.append(close_match.component)
                context_quality += close_match.confidence * 0.8
        
        # Calculate generation confidence based on available context
        if reference_components:
            generation_confidence = min(0.8, context_quality / len(reference_components))
            strategy = GenerationStrategy.GENERATE
            user_message = f"✅ Generating new component using {len(reference_components)} references"
            reasoning = f"Generating with context from {len(reference_components)} existing components"
        else:
            generation_confidence = 0.5
            strategy = GenerationStrategy.GENERATE_FRESH 
            user_message = "✅ Generating fresh component for unique requirements"
            reasoning = "No suitable existing components found - generating fresh implementation"
        
        decision = StrategyDecision(
            strategy=strategy,
            confidence=generation_confidence,
            primary_components=reference_components,
            reasoning=reasoning,
            user_message=user_message,
            benefits=self.strategy_benefits[strategy],
            considerations=self.strategy_considerations[strategy]
        )
        
        decision.implementation_details = {
            'action': 'generate_new',
            'context_components': [
                {
                    'name': comp.name,
                    'path': comp.path,
                    'relevance': 'pattern_reference'
                } for comp in reference_components
            ],
            'generation_type': 'contextual' if reference_components else 'fresh',
            'reference_count': len(reference_components)
        }
        
        return decision
    
    def _select_best_strategy(self, candidates: List[StrategyDecision], analysis: ReuseAnalysisResult) -> StrategyDecision:
        """Select the best strategy from candidates based on confidence and preferences."""
        
        if not candidates:
            # Fallback - should not happen
            return StrategyDecision(
                strategy=GenerationStrategy.GENERATE_FRESH,
                confidence=0.5,
                reasoning="No viable strategies found"
            )
        
        # Score each candidate based on confidence and priority
        scored_candidates = []
        
        for candidate in candidates:
            # Base score from confidence
            score = candidate.confidence
            
            # Apply priority weighting
            priority_weight = self.strategy_priorities[candidate.strategy] / 100.0
            score *= priority_weight
            
            # Apply preference bonuses
            if candidate.strategy == GenerationStrategy.REUSE and self.config.prefer_reuse:
                score *= 1.2
            elif candidate.strategy == GenerationStrategy.COMPOSE and self.config.prefer_composition:
                score *= 1.1
            
            scored_candidates.append((score, candidate))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        return scored_candidates[0][1]  # Return highest scored candidate
    
    def _enhance_decision_details(self, 
                                decision: StrategyDecision, 
                                analysis: ReuseAnalysisResult,
                                project_context: Optional[Dict[str, Any]]) -> StrategyDecision:
        """Enhance decision with additional implementation details."""
        
        # Add project-specific context
        if project_context:
            decision.implementation_details['project_context'] = {
                'framework': project_context.get('framework', 'unknown'),
                'styling_system': project_context.get('styling_system', 'unknown'),
                'typescript': project_context.get('typescript', False)
            }
        
        # Add analysis metadata
        decision.implementation_details['analysis_metadata'] = {
            'total_components_analyzed': len(analysis.exact_matches) + len(analysis.close_matches) + len(analysis.pattern_references),
            'intent_analysis': analysis.intent_analysis,
            'user_prompt': analysis.user_prompt,
            'analysis_confidence': analysis.analysis_confidence
        }
        
        # Generate detailed usage instructions based on strategy
        if decision.strategy == GenerationStrategy.REUSE:
            decision.implementation_details['usage_instructions'] = self._generate_reuse_instructions(decision)
        elif decision.strategy == GenerationStrategy.COMPOSE:
            decision.implementation_details['usage_instructions'] = self._generate_compose_instructions(decision)
        elif decision.strategy == GenerationStrategy.EXTEND:
            decision.implementation_details['usage_instructions'] = self._generate_extend_instructions(decision)
        else:
            decision.implementation_details['usage_instructions'] = self._generate_generate_instructions(decision, analysis)
        
        return decision
    
    def _assess_component_quality(self, component: ComponentInfo) -> float:
        """Assess the quality of a component for reuse purposes."""
        quality_score = 0.5  # Base score
        
        # Factor in component completeness
        if component.props:
            quality_score += 0.2  # Has defined props
        
        if component.exports:
            quality_score += 0.1  # Has proper exports
        
        # Factor in component type appropriateness
        if component.type in ['component', 'layout']:
            quality_score += 0.2  # Appropriate for reuse
        
        return min(quality_score, 1.0)
    
    def _generate_import_statement(self, component: ComponentInfo) -> str:
        """Generate import statement for a component."""
        # Remove file extension and generate import path
        import_path = component.path.replace('.tsx', '').replace('.jsx', '').replace('.ts', '').replace('.js', '')
        
        # Handle relative imports (simplified)
        if not import_path.startswith('.'):
            import_path = f'./{import_path}'
        
        return f"import {{ {component.name} }} from '{import_path}';"
    
    def _generate_usage_example(self, component: ComponentInfo) -> str:
        """Generate a basic usage example for a component."""
        props_example = []
        
        # Generate example props (simplified)
        for prop in component.props[:3]:  # Limit to first 3 props
            if 'on' in prop.lower():
                props_example.append(f"{prop}={{handleAction}}")
            elif 'children' in prop.lower():
                props_example.append(f"{prop}={{<span>Content</span>}}")
            else:
                props_example.append(f"{prop}={{value}}")
        
        props_str = ' '.join(props_example)
        return f"<{component.name} {props_str} />"
    
    def _generate_reuse_instructions(self, decision: StrategyDecision) -> Dict[str, Any]:
        """Generate detailed instructions for REUSE strategy."""
        component = decision.primary_components[0]
        
        return {
            'step_by_step': [
                f"1. Import the {component.name} component",
                f"2. Use it directly in your JSX",
                "3. Pass appropriate props based on your requirements"
            ],
            'code_example': decision.usage_example,
            'available_props': component.props,
            'notes': [
                "This component is ready to use as-is",
                "Check the original component for prop documentation"
            ]
        }
    
    def _generate_compose_instructions(self, decision: StrategyDecision) -> Dict[str, Any]:
        """Generate detailed instructions for COMPOSE strategy.""" 
        components = decision.primary_components
        
        return {
            'step_by_step': [
                f"1. Import all required components: {', '.join(c.name for c in components)}",
                "2. Create a new component that combines them",
                "3. Define the composition structure",
                "4. Pass props appropriately to child components"
            ],
            'code_example': decision.usage_example,
            'components_involved': [
                {
                    'name': comp.name,
                    'role': 'container' if i == 0 else 'content',
                    'props': comp.props
                } for i, comp in enumerate(components)
            ],
            'notes': [
                "This creates a new composed component",
                "Consider creating it as a reusable component if you'll use it multiple times"
            ]
        }
    
    def _generate_extend_instructions(self, decision: StrategyDecision) -> Dict[str, Any]:
        """Generate detailed instructions for EXTEND strategy."""
        base_component = decision.primary_components[0]
        modifications = decision.implementation_details.get('modifications_needed', [])
        
        return {
            'step_by_step': [
                f"1. Import the base {base_component.name} component",
                "2. Create a new component that wraps/extends it",
                "3. Add the required modifications",
                "4. Export the enhanced component"
            ],
            'base_component': base_component.name,
            'modifications_needed': modifications,
            'code_pattern': f"""
// Extend existing {base_component.name}
import {{ {base_component.name} }} from '{base_component.path}';

const Enhanced{base_component.name} = (props) => {{
  // Add modifications here
  return <{base_component.name} {{...props}} />;
}};

export default Enhanced{base_component.name};
""".strip(),
            'notes': [
                "This preserves the original component while adding new functionality",
                "Consider if modifications should be added to the original component instead"
            ]
        }
    
    def _generate_generate_instructions(self, decision: StrategyDecision, analysis: ReuseAnalysisResult) -> Dict[str, Any]:
        """Generate detailed instructions for GENERATE strategy."""
        reference_components = decision.primary_components
        
        instructions = {
            'step_by_step': [
                "1. Generate new component using AI with project context",
                "2. Follow established patterns from existing components",
                "3. Ensure consistency with project design system",
                "4. Add proper TypeScript types if applicable"
            ],
            'generation_context': {
                'intent': analysis.intent_analysis,
                'reference_components': [comp.name for comp in reference_components],
                'patterns_to_follow': analysis.pattern_references[:3] if analysis.pattern_references else []
            },
            'notes': []
        }
        
        if reference_components:
            instructions['notes'].append(f"Using {len(reference_components)} existing components as reference patterns")
            instructions['notes'].append("Generated component will follow established project conventions")
        else:
            instructions['notes'].append("Generating fresh component with minimal existing context")
            instructions['notes'].append("Ensure the new component fits well with your existing design system")
        
        return instructions
    
    def get_strategy_summary(self, decision: StrategyDecision) -> str:
        """Generate a human-readable summary of the strategy decision."""
        lines = [
            f"Strategy Decision: {decision.strategy.value.upper()}",
            f"Confidence: {decision.confidence:.1%}",
            f"Reasoning: {decision.reasoning}",
            ""
        ]
        
        if decision.primary_components:
            component_names = [comp.name for comp in decision.primary_components]
            lines.append(f"Components Involved: {', '.join(component_names)}")
        
        if decision.benefits:
            lines.append("Benefits:")
            for benefit in decision.benefits[:3]:
                lines.append(f"  • {benefit}")
        
        if decision.considerations:
            lines.append("Considerations:")
            for consideration in decision.considerations[:2]:
                lines.append(f"  • {consideration}")
        
        return "\n".join(lines)