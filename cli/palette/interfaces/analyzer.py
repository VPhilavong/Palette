"""
Analyzer interface and related data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class ComponentInfo:
    """Information about a discovered component."""
    name: str
    file_path: str
    import_path: str
    purpose: str
    type: str
    props: List[Dict[str, Any]] = field(default_factory=list)
    is_shadcn: bool = False
    description: Optional[str] = None
    examples: List[str] = field(default_factory=list)


@dataclass
class DesignTokens:
    """Design tokens extracted from the project."""
    colors: Dict[str, str] = field(default_factory=dict)
    semantic_colors: Dict[str, str] = field(default_factory=dict)
    spacing: Dict[str, str] = field(default_factory=dict)
    typography: Dict[str, str] = field(default_factory=dict)
    shadows: Dict[str, str] = field(default_factory=dict)
    border_radius: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectStructure:
    """Project structure information."""
    framework: str
    styling: str
    component_library: str
    is_monorepo: bool = False
    monorepo_type: Optional[str] = None
    components_dir: Optional[str] = None
    pages_dir: Optional[str] = None
    has_typescript: bool = False
    has_tailwind: bool = False


@dataclass
class AnalysisResult:
    """Complete analysis result from project analyzer."""
    project_structure: ProjectStructure
    design_tokens: DesignTokens
    components: List[ComponentInfo]
    available_imports: Dict[str, Any]
    ast_analysis: Optional[Dict[str, Any]] = None
    component_patterns: Optional[Dict[str, Any]] = None
    main_css_file: Optional[str] = None
    
    def get_components_by_type(self, component_type: str) -> List[ComponentInfo]:
        """Get all components of a specific type."""
        return [c for c in self.components if c.type == component_type]
    
    def get_shadcn_components(self) -> List[ComponentInfo]:
        """Get all shadcn/ui components."""
        return [c for c in self.components if c.is_shadcn]
    
    def get_custom_components(self) -> List[ComponentInfo]:
        """Get all custom project components."""
        return [c for c in self.components if not c.is_shadcn]


class IAnalyzer(ABC):
    """
    Abstract interface for project analyzers.
    Analyzes project structure, components, and design patterns.
    """
    
    @abstractmethod
    def analyze(self, project_path: str) -> AnalysisResult:
        """
        Analyze a project and extract all relevant information.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            AnalysisResult containing all extracted information
        """
        pass
    
    @abstractmethod
    def analyze_component(self, file_path: str) -> Optional[ComponentInfo]:
        """
        Analyze a single component file.
        
        Args:
            file_path: Path to the component file
            
        Returns:
            ComponentInfo if the file is a valid component, None otherwise
        """
        pass
    
    @abstractmethod
    def extract_design_tokens(self, project_path: str) -> DesignTokens:
        """
        Extract design tokens from the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            DesignTokens containing colors, spacing, typography, etc.
        """
        pass
    
    @abstractmethod
    def detect_project_structure(self, project_path: str) -> ProjectStructure:
        """
        Detect the project structure and framework.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectStructure with framework and configuration details
        """
        pass