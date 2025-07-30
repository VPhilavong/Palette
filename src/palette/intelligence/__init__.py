"""
Intelligence module for enhanced understanding and collaboration.
"""

from .asset_manager import AssetContext, AssetIntelligence, AssetSuggestion
from .component_mapper import (
    ComponentRelationshipEngine,
    RelationshipContext,
    RelationshipType,
)
from .intent_analyzer import ComponentIntent, IntentAnalyzer, IntentContext, UserGoal

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
]
