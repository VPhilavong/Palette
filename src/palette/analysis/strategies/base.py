"""
Base analysis strategy interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path

from ...interfaces import ComponentInfo


class AnalysisStrategy(ABC):
    """
    Abstract base class for analysis strategies.
    Different strategies can be used based on project characteristics.
    """
    
    @abstractmethod
    def analyze_components(self, project_path: Path) -> List[ComponentInfo]:
        """
        Analyze components in the project using this strategy.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of discovered components
        """
        pass
    
    @abstractmethod
    def extract_component_details(self, file_path: Path) -> Optional[ComponentInfo]:
        """
        Extract detailed information from a component file.
        
        Args:
            file_path: Path to the component file
            
        Returns:
            ComponentInfo if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def supports_file_type(self, file_path: Path) -> bool:
        """
        Check if this strategy supports analyzing the given file type.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file type is supported
        """
        pass
    
    @abstractmethod
    def get_confidence_score(self) -> float:
        """
        Get the confidence score for this strategy's analysis.
        
        Returns:
            Confidence score between 0 and 1
        """
        pass
    
    def preprocess_file(self, file_path: Path) -> Optional[str]:
        """
        Preprocess file content before analysis.
        Can be overridden by strategies that need special preprocessing.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Preprocessed content or None if file can't be read
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None