"""
Generation Strategy Registry.
Central registry for managing framework-specific generation strategies
with automatic selection based on project configuration.
"""

from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass

from .base import GenerationStrategy, GenerationResult
from .chakra_ui_strategy import ChakraUIGenerationStrategy
from ...intelligence.configuration_hub import ProjectConfiguration, Framework
from ...intelligence.styling_analyzer import StylingSystem
from ...errors.decorators import handle_errors


@dataclass
class StrategyInfo:
    """Information about a generation strategy."""
    name: str
    strategy: GenerationStrategy
    supported_frameworks: List[Framework]
    supported_styling_systems: List[StylingSystem]
    priority: int = 0  # Higher priority strategies are preferred


class GenerationStrategyRegistry:
    """
    Central registry of framework-specific generation strategies.
    Automatically selects the best strategy based on project configuration.
    """
    
    def __init__(self):
        self.strategies: Dict[str, StrategyInfo] = {}
        self.strategy_combinations: Dict[Tuple, str] = {}
        
        # Initialize built-in strategies
        self._initialize_builtin_strategies()
        self._initialize_strategy_combinations()
    
    def _initialize_builtin_strategies(self):
        """Initialize built-in generation strategies."""
        
        # Chakra UI Strategy
        chakra_strategy = ChakraUIGenerationStrategy()
        self.register_strategy(
            name="ChakraUI",
            strategy=chakra_strategy,
            supported_frameworks=[Framework.NEXT_JS, Framework.REACT, Framework.VITE_REACT],
            supported_styling_systems=[StylingSystem.CHAKRA_UI],
            priority=10  # High priority for critical fixes
        )
        
        # TODO: Add other strategies as they are implemented
        # These would be implemented in future phases
        
        # Tailwind Strategy (placeholder)
        # tailwind_strategy = TailwindGenerationStrategy()
        # self.register_strategy(
        #     name="Tailwind",
        #     strategy=tailwind_strategy,
        #     supported_frameworks=[Framework.NEXT_JS, Framework.REACT, Framework.VITE_REACT],
        #     supported_styling_systems=[StylingSystem.TAILWIND],
        #     priority=8
        # )
        
        # Material UI Strategy (placeholder) 
        # mui_strategy = MaterialUIGenerationStrategy()
        # self.register_strategy(
        #     name="MaterialUI",
        #     strategy=mui_strategy,
        #     supported_frameworks=[Framework.NEXT_JS, Framework.REACT, Framework.VITE_REACT],
        #     supported_styling_systems=[StylingSystem.MATERIAL_UI],
        #     priority=8
        # )
        
        # Shadcn/ui Strategy (placeholder)
        # shadcn_strategy = ShadcnUIGenerationStrategy()
        # self.register_strategy(
        #     name="ShadcnUI", 
        #     strategy=shadcn_strategy,
        #     supported_frameworks=[Framework.NEXT_JS, Framework.REACT, Framework.VITE_REACT],
        #     supported_styling_systems=[StylingSystem.SHADCN_UI],
        #     priority=9
        # )
    
    def _initialize_strategy_combinations(self):
        """Initialize strategy combinations for specific framework/styling pairs."""
        
        # Exact combinations for optimal strategy selection
        self.strategy_combinations = {
            # Chakra UI combinations
            (Framework.NEXT_JS, StylingSystem.CHAKRA_UI): "ChakraUI",
            (Framework.REACT, StylingSystem.CHAKRA_UI): "ChakraUI",
            (Framework.VITE_REACT, StylingSystem.CHAKRA_UI): "ChakraUI",
            
            # TODO: Add other combinations as strategies are implemented
            # (Framework.NEXT_JS, StylingSystem.TAILWIND): "Tailwind",
            # (Framework.REACT, StylingSystem.TAILWIND): "Tailwind",
            # (Framework.NEXT_JS, StylingSystem.SHADCN_UI): "ShadcnUI",
            # (Framework.REACT, StylingSystem.MATERIAL_UI): "MaterialUI",
        }
    
    def register_strategy(
        self,
        name: str,
        strategy: GenerationStrategy,
        supported_frameworks: List[Framework],
        supported_styling_systems: List[StylingSystem],
        priority: int = 0
    ):
        """
        Register a new generation strategy.
        
        Args:
            name: Unique name for the strategy
            strategy: Strategy implementation
            supported_frameworks: List of supported frameworks
            supported_styling_systems: List of supported styling systems
            priority: Priority level (higher = preferred)
        """
        self.strategies[name] = StrategyInfo(
            name=name,
            strategy=strategy,
            supported_frameworks=supported_frameworks,
            supported_styling_systems=supported_styling_systems,
            priority=priority
        )
    
    @handle_errors(reraise=True)
    def get_strategy(self, config: ProjectConfiguration) -> Optional[GenerationStrategy]:
        """
        Get the optimal generation strategy for a project configuration.
        
        This is the main method that addresses framework detection issues
        by selecting the appropriate strategy based on validated configuration.
        
        Args:
            config: Project configuration from ConfigurationIntelligenceHub
            
        Returns:
            Best matching generation strategy or None if no match
        """
        
        # Try exact combination match first (highest priority)
        combination_key = (config.framework, config.styling_system)
        if combination_key in self.strategy_combinations:
            strategy_name = self.strategy_combinations[combination_key]
            if strategy_name in self.strategies:
                print(f"✅ Selected strategy: {strategy_name} (exact match)")
                return self.strategies[strategy_name].strategy
        
        # Find compatible strategies
        compatible_strategies = []
        
        for strategy_info in self.strategies.values():
            # Check if strategy supports the configuration
            framework_match = config.framework in strategy_info.supported_frameworks
            styling_match = config.styling_system in strategy_info.supported_styling_systems
            
            if framework_match and styling_match:
                compatible_strategies.append(strategy_info)
        
        if compatible_strategies:
            # Sort by priority and return the best one
            best_strategy = max(compatible_strategies, key=lambda x: x.priority)
            print(f"✅ Selected strategy: {best_strategy.name} (priority match)")
            return best_strategy.strategy
        
        # Fallback: try to find strategy that supports just the styling system
        for strategy_info in self.strategies.values():
            if config.styling_system in strategy_info.supported_styling_systems:
                print(f"⚠️ Fallback strategy: {strategy_info.name} (styling system match only)")
                return strategy_info.strategy
        
        print(f"❌ No compatible strategy found for {config.framework.value} + {config.styling_system.value}")
        return None
    
    def get_strategy_by_name(self, name: str) -> Optional[GenerationStrategy]:
        """Get strategy by name."""
        strategy_info = self.strategies.get(name)
        return strategy_info.strategy if strategy_info else None
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all registered strategies with their capabilities."""
        strategies_list = []
        
        for strategy_info in self.strategies.values():
            strategies_list.append({
                'name': strategy_info.name,
                'supported_frameworks': [fw.value for fw in strategy_info.supported_frameworks],
                'supported_styling_systems': [ss.value for ss in strategy_info.supported_styling_systems],
                'priority': strategy_info.priority,
                'capabilities': strategy_info.strategy.get_strategy_info()
            })
        
        return sorted(strategies_list, key=lambda x: x['priority'], reverse=True)
    
    def get_compatible_strategies(self, config: ProjectConfiguration) -> List[str]:
        """Get list of compatible strategy names for a configuration."""
        compatible = []
        
        for name, strategy_info in self.strategies.items():
            framework_match = config.framework in strategy_info.supported_frameworks
            styling_match = config.styling_system in strategy_info.supported_styling_systems
            
            if framework_match and styling_match:
                compatible.append(name)
        
        return compatible
    
    def validate_strategy_coverage(self) -> Dict[str, Any]:
        """Validate strategy coverage across framework/styling combinations."""
        
        all_frameworks = list(Framework)
        all_styling_systems = list(StylingSystem)
        
        coverage_matrix = {}
        total_combinations = 0
        covered_combinations = 0
        
        for framework in all_frameworks:
            coverage_matrix[framework.value] = {}
            
            for styling_system in all_styling_systems:
                total_combinations += 1
                combination_key = (framework, styling_system)
                
                # Check if combination is covered
                is_covered = False
                covering_strategies = []
                
                if combination_key in self.strategy_combinations:
                    is_covered = True
                    covering_strategies.append(self.strategy_combinations[combination_key])
                else:
                    # Check for compatible strategies
                    for name, strategy_info in self.strategies.items():
                        if (framework in strategy_info.supported_frameworks and 
                            styling_system in strategy_info.supported_styling_systems):
                            is_covered = True
                            covering_strategies.append(name)
                
                if is_covered:
                    covered_combinations += 1
                
                coverage_matrix[framework.value][styling_system.value] = {
                    'covered': is_covered,
                    'strategies': covering_strategies
                }
        
        coverage_percentage = (covered_combinations / total_combinations) * 100
        
        return {
            'coverage_percentage': coverage_percentage,
            'total_combinations': total_combinations,
            'covered_combinations': covered_combinations,
            'coverage_matrix': coverage_matrix,
            'uncovered_combinations': [
                f"{fw} + {ss}" 
                for fw, fw_data in coverage_matrix.items()
                for ss, ss_data in fw_data.items()
                if not ss_data['covered']
            ]
        }
    
    def recommend_strategy_implementation(self) -> List[str]:
        """Recommend which strategies should be implemented next."""
        coverage = self.validate_strategy_coverage()
        
        # Count uncovered combinations by styling system
        styling_gaps = {}
        for combo in coverage['uncovered_combinations']:
            _, styling = combo.split(' + ')
            if styling not in styling_gaps:
                styling_gaps[styling] = 0
            styling_gaps[styling] += 1
        
        # Sort by frequency to prioritize
        recommendations = []
        for styling, count in sorted(styling_gaps.items(), key=lambda x: x[1], reverse=True):
            recommendations.append(
                f"Implement {styling} strategy (covers {count} framework combinations)"
            )
        
        return recommendations
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about strategy usage and capabilities."""
        
        stats = {
            'total_strategies': len(self.strategies),
            'strategy_breakdown': {},
            'framework_support': {},
            'styling_system_support': {},
            'priority_distribution': {}
        }
        
        # Strategy breakdown
        for name, strategy_info in self.strategies.items():
            stats['strategy_breakdown'][name] = {
                'frameworks': len(strategy_info.supported_frameworks),
                'styling_systems': len(strategy_info.supported_styling_systems),
                'priority': strategy_info.priority
            }
        
        # Framework support analysis
        for framework in Framework:
            supporting_strategies = [
                name for name, info in self.strategies.items()
                if framework in info.supported_frameworks
            ]
            stats['framework_support'][framework.value] = {
                'strategy_count': len(supporting_strategies),
                'strategies': supporting_strategies
            }
        
        # Styling system support analysis
        for styling_system in StylingSystem:
            supporting_strategies = [
                name for name, info in self.strategies.items()
                if styling_system in info.supported_styling_systems
            ]
            stats['styling_system_support'][styling_system.value] = {
                'strategy_count': len(supporting_strategies),
                'strategies': supporting_strategies
            }
        
        # Priority distribution
        priorities = [info.priority for info in self.strategies.values()]
        if priorities:
            stats['priority_distribution'] = {
                'min': min(priorities),
                'max': max(priorities),
                'average': sum(priorities) / len(priorities)
            }
        
        return stats


# Global registry instance
_strategy_registry_instance = None

def get_strategy_registry() -> GenerationStrategyRegistry:
    """Get the global strategy registry instance."""
    global _strategy_registry_instance
    if _strategy_registry_instance is None:
        _strategy_registry_instance = GenerationStrategyRegistry()
    return _strategy_registry_instance