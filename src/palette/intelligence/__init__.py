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
    "ValidationResult"
]
