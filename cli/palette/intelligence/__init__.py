"""
Intelligence module for enhanced understanding and collaboration.
Advanced project configuration detection and analysis.
"""

from .asset_manager import AssetContext, AssetIntelligence, AssetSuggestion
from .component_mapper import (
    ComponentRelationshipEngine,
    RelationshipContext,
    RelationshipType,
)
from .intent_analyzer import ComponentIntent, IntentAnalyzer, IntentContext, UserGoal

# Configuration intelligence components
from .configuration_hub import ConfigurationIntelligenceHub, ProjectConfiguration, Framework, ComponentLibrary
from .styling_analyzer import StylingSystemAnalyzer, StylingAnalysis, StylingSystem
from .framework_detector import EnhancedFrameworkDetector, FrameworkAnalysis
from .pattern_extractor import ProjectPatternExtractor, PatternAnalysis
from .compatibility_checker import CompatibilityChecker, ValidationResult

# Component reuse and strategy systems
from .component_reuse_analyzer import (
    ComponentReuseAnalyzer, 
    ReuseAnalysisResult, 
    ComponentMatch, 
    CompositionOpportunity,
    ReuseOpportunityType
)
from .generation_strategy_engine import (
    GenerationStrategyEngine, 
    StrategyDecision, 
    GenerationStrategy, 
    StrategyConfig
)

# Cross-library compatibility
from .cross_library_compatibility import (
    CrossLibraryCompatibilityChecker,
    LibraryCompatibilityResult,
    ComponentMapping,
    CompatibilityLevel,
    MigrationComplexity
)

__all__ = [
    "IntentAnalyzer",
    "IntentContext",
    "ComponentIntent",
    "UserGoal",
    "AssetIntelligence",
    "AssetContext",
    "AssetSuggestion",
    "ComponentRelationshipEngine",
    "RelationshipContext",
    "RelationshipType",
    # Configuration intelligence
    "ConfigurationIntelligenceHub",
    "ProjectConfiguration",
    "Framework", 
    "ComponentLibrary",
    "StylingSystemAnalyzer",
    "StylingAnalysis",
    "StylingSystem",
    "EnhancedFrameworkDetector",
    "FrameworkAnalysis",
    "ProjectPatternExtractor",
    "PatternAnalysis",
    "CompatibilityChecker",
    "ValidationResult",
    # Component reuse systems
    "ComponentReuseAnalyzer",
    "ReuseAnalysisResult",
    "ComponentMatch",
    "CompositionOpportunity",
    "ReuseOpportunityType",
    "GenerationStrategyEngine",
    "StrategyDecision",
    "GenerationStrategy",
    "StrategyConfig",
    # Cross-library compatibility
    "CrossLibraryCompatibilityChecker",
    "LibraryCompatibilityResult",
    "ComponentMapping",
    "CompatibilityLevel",
    "MigrationComplexity"
]
