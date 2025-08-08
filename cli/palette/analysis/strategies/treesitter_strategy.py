"""
Tree-sitter based analysis strategy for high-accuracy AST parsing.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import AnalysisStrategy
from ...interfaces import ComponentInfo


class TreeSitterStrategy(AnalysisStrategy):
    """
    Analysis strategy using Tree-sitter for accurate AST parsing.
    Best for TypeScript/JavaScript projects with complex patterns.
    """
    
    def __init__(self):
        self.analyzer = None
        self._init_analyzer()
        self.confidence = 0.95 if self.analyzer else 0.0
    
    def _init_analyzer(self):
        """Initialize Tree-sitter analyzer if available."""
        try:
            from ..treesitter_analyzer import TreeSitterAnalyzer
            self.analyzer = TreeSitterAnalyzer()
        except ImportError:
            print("Warning: Tree-sitter not available for analysis")
    
    def analyze_components(self, project_path: Path) -> List[ComponentInfo]:
        """Analyze components using Tree-sitter AST parsing."""
        if not self.analyzer:
            return []
        
        components = []
        
        # Use Tree-sitter's file discovery
        component_files = self._find_component_files(project_path)
        
        for file_path in component_files:
            component = self.extract_component_details(file_path)
            if component:
                components.append(component)
        
        return components
    
    def extract_component_details(self, file_path: Path) -> Optional[ComponentInfo]:
        """Extract detailed component information using AST."""
        if not self.analyzer:
            return None
        
        try:
            # Use Tree-sitter to analyze the component
            ast_component = self.analyzer._analyze_component_with_treesitter(file_path)
            if not ast_component:
                return None
            
            # Convert to ComponentInfo
            props = []
            for prop_pattern in ast_component.props:
                props.append({
                    "name": prop_pattern.name,
                    "type": prop_pattern.type_annotation or "unknown",
                    "required": not prop_pattern.is_optional
                })
            
            # Build import path (simplified)
            rel_path = file_path.relative_to(file_path.parent.parent.parent)
            import_path = f"@/{str(rel_path.parent)}/{file_path.stem}"
            
            return ComponentInfo(
                name=ast_component.name,
                file_path=str(file_path),
                import_path=import_path,
                purpose=ast_component.purpose or f"{ast_component.name} component",
                type=self._infer_component_type(ast_component.name),
                props=props,
                description=ast_component.description,
                examples=ast_component.examples
            )
            
        except Exception as e:
            print(f"Tree-sitter analysis failed for {file_path}: {e}")
            return None
    
    def supports_file_type(self, file_path: Path) -> bool:
        """Check if Tree-sitter supports this file type."""
        return file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']
    
    def get_confidence_score(self) -> float:
        """Get confidence score for Tree-sitter analysis."""
        return self.confidence
    
    def _find_component_files(self, project_path: Path) -> List[Path]:
        """Find component files in the project."""
        component_files = []
        
        # Common component directories
        search_dirs = [
            project_path / "src" / "components",
            project_path / "components",
            project_path / "app" / "components",
            project_path / "src" / "app" / "components",
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for file_path in search_dir.rglob("*"):
                    if self.supports_file_type(file_path):
                        component_files.append(file_path)
        
        return component_files
    
    def _infer_component_type(self, component_name: str) -> str:
        """Infer component type from name."""
        name_lower = component_name.lower()
        
        type_patterns = {
            "button": ["button", "btn", "action"],
            "form": ["form", "input", "field", "select"],
            "container": ["card", "panel", "box", "container"],
            "navigation": ["nav", "menu", "breadcrumb", "tabs"],
            "feedback": ["alert", "toast", "notification", "message"],
            "overlay": ["modal", "dialog", "popup", "drawer"],
            "data-display": ["table", "list", "grid"],
            "layout": ["layout", "wrapper", "section"],
        }
        
        for comp_type, patterns in type_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return comp_type
        
        return "component"