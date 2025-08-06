"""
Palette Conversation Module

This module provides conversational interfaces for UI component generation,
enabling natural language interactions for creating and refining components.
"""

from .conversation_engine import (
    ConversationEngine,
    ConversationIntent,
    ConversationMessage,
    ConversationContext,
    IntentClassifier
)
from .design_system_analyzer import (
    DesignSystemAnalyzer,
    DesignToken,
    ComponentPattern,
    DesignSystemProfile
)
from .component_relationship_analyzer import (
    ComponentRelationshipAnalyzer,
    ComponentDependency,
    StylePattern,
    ComponentFamily
)
from .variant_generator import (
    VariantGenerator,
    VariantSpec,
    ComponentVariantFamily,
    VariantType
)
from .consistency_manager import (
    ConsistencyManager,
    ConsistencyRule,
    ComponentSignature,
    ConsistencyReport,
    ConsistencyType
)

__all__ = [
    'ConversationEngine',
    'ConversationIntent', 
    'ConversationMessage',
    'ConversationContext',
    'IntentClassifier',
    'DesignSystemAnalyzer',
    'DesignToken',
    'ComponentPattern',
    'DesignSystemProfile',
    'ComponentRelationshipAnalyzer',
    'ComponentDependency',
    'StylePattern',
    'ComponentFamily',
    'VariantGenerator',
    'VariantSpec',
    'ComponentVariantFamily',
    'VariantType',
    'ConsistencyManager',
    'ConsistencyRule',
    'ComponentSignature',
    'ConsistencyReport',
    'ConsistencyType'
]