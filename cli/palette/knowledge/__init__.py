"""
Knowledge base management for Palette.
Supports both local knowledge base and OpenAI File Search.
"""

from .file_search import PaletteKnowledgeBase, KnowledgeEnhancedGenerator
from .local_knowledge import LocalKnowledgeBase, LocalKnowledgeEnhancedGenerator, HAS_LOCAL_KNOWLEDGE

__all__ = [
    'PaletteKnowledgeBase', 
    'KnowledgeEnhancedGenerator',
    'LocalKnowledgeBase',
    'LocalKnowledgeEnhancedGenerator',
    'HAS_LOCAL_KNOWLEDGE'
]