"""
Regex-based analysis strategy for lightweight component discovery.
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import AnalysisStrategy
from ...interfaces import ComponentInfo


class RegexStrategy(AnalysisStrategy):
    """
    Analysis strategy using regex patterns for component discovery.
    Lightweight fallback when AST parsing is not available.
    """
    
    def __init__(self):
        self.confidence = 0.7  # Lower confidence than AST
        
        # Component patterns
        self.component_patterns = [
            # Function components
            r'export\s+(?:default\s+)?function\s+(\w+)',
            r'export\s+default\s+function\s+(\w+)',
            r'function\s+(\w+)\s*\([^)]*\)\s*:\s*(?:React\.)?(?:FC|FunctionComponent|ReactElement)',
            
            # Arrow function components  
            r'export\s+const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*[({]',
            r'const\s+(\w+)\s*:\s*(?:React\.)?FC\s*=',
            r'const\s+(\w+)\s*=\s*React\.forwardRef',
            
            # Class components (legacy)
            r'export\s+(?:default\s+)?class\s+(\w+)\s+extends\s+(?:React\.)?Component',
        ]
        
        # Props patterns
        self.props_patterns = [
            # TypeScript interface
            r'interface\s+\w*Props\s*{\s*([^}]+)\s*}',
            r'type\s+\w*Props\s*=\s*{\s*([^}]+)\s*}',
            
            # Inline props
            r'function\s+\w+\s*\(\s*{\s*([^}]+)\s*}\s*:\s*\w*Props?\s*\)',
            r'=\s*\(\s*{\s*([^}]+)\s*}\s*:\s*\w*Props?\s*\)\s*=>',
        ]
    
    def analyze_components(self, project_path: Path) -> List[ComponentInfo]:
        """Analyze components using regex patterns."""
        components = []
        
        # Find component files
        component_files = self._find_component_files(project_path)
        
        for file_path in component_files:
            component = self.extract_component_details(file_path)
            if component:
                components.append(component)
        
        return components
    
    def extract_component_details(self, file_path: Path) -> Optional[ComponentInfo]:
        """Extract component details using regex patterns."""
        content = self.preprocess_file(file_path)
        if not content:
            return None
        
        # Find component name
        component_name = None
        for pattern in self.component_patterns:
            match = re.search(pattern, content)
            if match:
                component_name = match.group(1)
                break
        
        if not component_name:
            return None
        
        # Extract props
        props = self._extract_props(content)
        
        # Extract description
        description = self._extract_description(content, component_name)
        
        # Build import path
        import_path = self._build_import_path(file_path)
        
        return ComponentInfo(
            name=component_name,
            file_path=str(file_path),
            import_path=import_path,
            purpose=self._infer_purpose(component_name, content),
            type=self._infer_component_type(component_name),
            props=props,
            description=description
        )
    
    def supports_file_type(self, file_path: Path) -> bool:
        """Check if regex strategy supports this file type."""
        return file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']
    
    def get_confidence_score(self) -> float:
        """Get confidence score for regex analysis."""
        return self.confidence
    
    def _find_component_files(self, project_path: Path) -> List[Path]:
        """Find potential component files."""
        component_files = []
        
        # Search patterns
        include_patterns = ['*.tsx', '*.jsx', '*.ts', '*.js']
        exclude_patterns = [
            'test', 'spec', 'stories', 'mock',
            'index', 'config', 'setup', 'utils'
        ]
        
        # Search in common directories
        search_dirs = [
            project_path / "src",
            project_path / "components",
            project_path / "app",
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for pattern in include_patterns:
                for file_path in search_dir.rglob(pattern):
                    # Skip excluded patterns
                    if any(exc in str(file_path).lower() for exc in exclude_patterns):
                        continue
                    
                    # Skip node_modules and hidden directories
                    if 'node_modules' in str(file_path) or '/.' in str(file_path):
                        continue
                    
                    component_files.append(file_path)
        
        return component_files
    
    def _extract_props(self, content: str) -> List[Dict[str, Any]]:
        """Extract props using regex patterns."""
        props = []
        
        for pattern in self.props_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                props_content = match.group(1)
                
                # Extract individual props
                prop_pattern = r'(\w+)(\?)?\s*:\s*([^;,\n]+)'
                for prop_match in re.finditer(prop_pattern, props_content):
                    prop_name = prop_match.group(1)
                    is_optional = prop_match.group(2) == '?'
                    prop_type = prop_match.group(3).strip()
                    
                    # Clean up prop type
                    prop_type = prop_type.split('//')[0].strip()  # Remove comments
                    
                    props.append({
                        "name": prop_name,
                        "type": prop_type,
                        "required": not is_optional
                    })
                
                break
        
        return props
    
    def _extract_description(self, content: str, component_name: str) -> Optional[str]:
        """Extract component description from comments."""
        # Look for JSDoc comment before component
        jsdoc_pattern = rf'/\*\*\s*\n((?:\s*\*[^\n]*\n)*)\s*\*/\s*(?:export\s+)?(?:default\s+)?(?:function|const|class)\s+{component_name}'
        match = re.search(jsdoc_pattern, content)
        
        if match:
            jsdoc_content = match.group(1)
            lines = jsdoc_content.split('\n')
            
            desc_lines = []
            for line in lines:
                line = line.strip().lstrip('*').strip()
                if line and not line.startswith('@'):
                    desc_lines.append(line)
            
            if desc_lines:
                return ' '.join(desc_lines)
        
        # Look for single-line comment
        comment_pattern = rf'//\s*(.+)\n\s*(?:export\s+)?(?:default\s+)?(?:function|const|class)\s+{component_name}'
        match = re.search(comment_pattern, content)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _infer_purpose(self, component_name: str, content: str) -> str:
        """Infer component purpose from name and content."""
        name_lower = component_name.lower()
        
        # Check for common patterns in content
        if 'form' in name_lower or '<form' in content:
            return "Form component for user input"
        elif 'button' in name_lower or '<button' in content:
            return "Interactive button component"
        elif 'card' in name_lower:
            return "Card container for content display"
        elif 'modal' in name_lower or 'dialog' in name_lower:
            return "Modal overlay component"
        elif 'nav' in name_lower or '<nav' in content:
            return "Navigation component"
        elif 'table' in name_lower or '<table' in content:
            return "Data table component"
        elif 'list' in name_lower or '<ul' in content or '<ol' in content:
            return "List display component"
        
        return f"{component_name} component"
    
    def _infer_component_type(self, component_name: str) -> str:
        """Infer component type from name."""
        name_lower = component_name.lower()
        
        type_mappings = {
            "button": ["button", "btn", "action"],
            "form": ["form", "input", "field", "select", "checkbox", "radio"],
            "container": ["card", "panel", "box", "container", "wrapper"],
            "navigation": ["nav", "menu", "header", "footer", "breadcrumb"],
            "overlay": ["modal", "dialog", "popup", "drawer", "tooltip"],
            "data-display": ["table", "list", "grid"],
            "feedback": ["alert", "toast", "notification", "error", "success"],
        }
        
        for comp_type, keywords in type_mappings.items():
            if any(keyword in name_lower for keyword in keywords):
                return comp_type
        
        return "component"
    
    def _build_import_path(self, file_path: Path) -> str:
        """Build import path for component."""
        # Try to find src or components directory
        parts = file_path.parts
        
        try:
            # Find index of src or components
            if 'src' in parts:
                idx = parts.index('src')
                relative_parts = parts[idx+1:-1]  # Exclude filename
            elif 'components' in parts:
                idx = parts.index('components')
                relative_parts = parts[idx:-1]  # Exclude filename
            else:
                relative_parts = parts[-2:-1]  # Just parent directory
            
            # Build import path
            import_base = '/'.join(relative_parts)
            return f"@/{import_base}/{file_path.stem}"
            
        except Exception:
            return f"@/components/{file_path.stem}"