"""
Hybrid analysis strategy combining multiple approaches.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import AnalysisStrategy
from .treesitter_strategy import TreeSitterStrategy
from .regex_strategy import RegexStrategy
from ...interfaces import ComponentInfo


class HybridStrategy(AnalysisStrategy):
    """
    Hybrid analysis strategy that combines multiple strategies.
    Uses Tree-sitter when available, falls back to regex.
    """
    
    def __init__(self):
        self.primary_strategy = TreeSitterStrategy()
        self.fallback_strategy = RegexStrategy()
        
        # Use primary if available, otherwise fallback
        self.active_strategy = (
            self.primary_strategy 
            if self.primary_strategy.get_confidence_score() > 0 
            else self.fallback_strategy
        )
    
    def analyze_components(self, project_path: Path) -> List[ComponentInfo]:
        """Analyze components using the best available strategy."""
        components = []
        
        # Try primary strategy first
        if self.primary_strategy.get_confidence_score() > 0:
            try:
                components = self.primary_strategy.analyze_components(project_path)
            except Exception as e:
                print(f"Primary strategy failed: {e}")
        
        # If no components found or primary failed, try fallback
        if not components:
            try:
                components = self.fallback_strategy.analyze_components(project_path)
            except Exception as e:
                print(f"Fallback strategy failed: {e}")
        
        # Deduplicate components by name
        seen = set()
        unique_components = []
        for comp in components:
            if comp.name not in seen:
                seen.add(comp.name)
                unique_components.append(comp)
        
        return unique_components
    
    def extract_component_details(self, file_path: Path) -> Optional[ComponentInfo]:
        """Extract component details using the best strategy for the file."""
        # Try primary first
        if self.primary_strategy.supports_file_type(file_path):
            result = self.primary_strategy.extract_component_details(file_path)
            if result:
                return result
        
        # Fall back to regex
        if self.fallback_strategy.supports_file_type(file_path):
            return self.fallback_strategy.extract_component_details(file_path)
        
        return None
    
    def supports_file_type(self, file_path: Path) -> bool:
        """Check if any strategy supports this file type."""
        return (
            self.primary_strategy.supports_file_type(file_path) or
            self.fallback_strategy.supports_file_type(file_path)
        )
    
    def get_confidence_score(self) -> float:
        """Get the confidence score of the active strategy."""
        return self.active_strategy.get_confidence_score()
    
    def merge_component_info(
        self, 
        primary: Optional[ComponentInfo], 
        fallback: Optional[ComponentInfo]
    ) -> Optional[ComponentInfo]:
        """
        Merge component information from multiple sources.
        Primary takes precedence but missing fields are filled from fallback.
        """
        if not primary:
            return fallback
        if not fallback:
            return primary
        
        # Start with primary
        merged = primary
        
        # Fill missing fields from fallback
        if not merged.description and fallback.description:
            merged.description = fallback.description
        
        if not merged.props and fallback.props:
            merged.props = fallback.props
        
        if not merged.examples and fallback.examples:
            merged.examples = fallback.examples
        
        return merged