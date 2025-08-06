"""
Generation strategies for different framework and styling system combinations.
Provides specialized generation approaches that ensure framework-appropriate code.
"""

from .base import GenerationStrategy, GenerationResult
from .chakra_ui_strategy import ChakraUIGenerationStrategy
from .registry import GenerationStrategyRegistry

# TODO: Import other strategies as they are implemented
# from .tailwind_strategy import TailwindGenerationStrategy
# from .material_ui_strategy import MaterialUIGenerationStrategy
# from .shadcn_ui_strategy import ShadcnUIGenerationStrategy

__all__ = [
    'GenerationStrategy',
    'GenerationResult',
    'ChakraUIGenerationStrategy',
    'GenerationStrategyRegistry'
    # TODO: Add other strategies as they are implemented
    # 'TailwindGenerationStrategy', 
    # 'MaterialUIGenerationStrategy',
    # 'ShadcnUIGenerationStrategy',
]