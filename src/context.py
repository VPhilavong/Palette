import os
import json
import re
from typing import Dict, List, Optional
from pathlib import Path

class ProjectAnalyzer:
    """Analyzes project structure to extract design patterns and context"""
    
    def __init__(self):
        self.supported_frameworks = {
            'next.js': ['next.config.js', 'next.config.ts', 'app/', 'pages/'],
            'react': ['src/', 'public/', 'package.json'],
            'vite': ['vite.config.js', 'vite.config.ts'],
        }
        
        self.component_libraries = {
            'shadcn/ui': ['components/ui/', '@radix-ui', 'class-variance-authority'],
            'chakra-ui': ['@chakra-ui'],
            'material-ui': ['@mui/material', '@material-ui'],
            'ant-design': ['antd'],
        }
    
    def analyze_project(self, project_path: str) -> Dict:
        """Extract design patterns for UI generation"""
        
        context = {
            'framework': self._detect_framework(project_path),
            'styling': self._detect_styling_system(project_path),
            'component_library': self._detect_component_library(project_path),
            'design_tokens': self._extract_design_tokens(project_path),
            'component_patterns': self._analyze_component_patterns(project_path),
            'project_structure': self._analyze_project_structure(project_path)
        }
        
        return context
    
    def _detect_framework(self, project_path: str) -> str:
        """Detect the React framework being used"""
        
        package_json_path = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get('dependencies', {}), 
                                  **package_data.get('devDependencies', {})}
                    
                    if 'next' in dependencies:
                        return 'next.js'
                    elif 'vite' in dependencies:
                        return 'vite'
                    elif 'react' in dependencies:
                        return 'react'
            except json.JSONDecodeError:
                pass
        
        # Check for framework-specific files
        for framework, indicators in self.supported_frameworks.items():
            for indicator in indicators:
                if os.path.exists(os.path.join(project_path, indicator)):
                    return framework
        
        return 'unknown'
    
    def _detect_styling_system(self, project_path: str) -> str:
        """Detect the styling system (Tailwind, CSS modules, etc.)"""
        
        # Check for Tailwind config
        tailwind_configs = ['tailwind.config.js', 'tailwind.config.ts']
        for config in tailwind_configs:
            if os.path.exists(os.path.join(project_path, config)):
                return 'tailwind'
        
        # Check package.json for styling dependencies
        package_json_path = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get('dependencies', {}), 
                                  **package_data.get('devDependencies', {})}
                    
                    if 'tailwindcss' in dependencies:
                        return 'tailwind'
                    elif 'styled-components' in dependencies:
                        return 'styled-components'
                    elif 'emotion' in dependencies or '@emotion/react' in dependencies:
                        return 'emotion'
            except json.JSONDecodeError:
                pass
        
        return 'css'
    
    def _detect_component_library(self, project_path: str) -> str:
        """Detect component library being used"""
        
        package_json_path = os.path.join(project_path, 'package.json')
        if not os.path.exists(package_json_path):
            return 'none'
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                dependencies = {**package_data.get('dependencies', {}), 
                              **package_data.get('devDependencies', {})}
                
                for library, indicators in self.component_libraries.items():
                    for indicator in indicators:
                        if indicator in dependencies:
                            return library
                        # Check for directory structure indicators
                        if indicator.endswith('/') and os.path.exists(os.path.join(project_path, indicator)):
                            return library
        except json.JSONDecodeError:
            pass
        
        return 'none'
    
    def _extract_design_tokens(self, project_path: str) -> Dict:
        """Extract design tokens from Tailwind config and existing components"""
        
        tokens = {
            'colors': self._extract_tailwind_colors(project_path),
            'spacing': self._extract_spacing_patterns(project_path),
            'typography': self._extract_typography_scale(project_path),
            'shadows': self._extract_shadow_patterns(project_path),
            'border_radius': self._extract_border_patterns(project_path)
        }
        
        return tokens
    
    def _extract_tailwind_colors(self, project_path: str) -> List[str]:
        """Extract color palette from Tailwind config"""
        
        tailwind_configs = ['tailwind.config.js', 'tailwind.config.ts']
        colors = []
        
        for config in tailwind_configs:
            config_path = os.path.join(project_path, config)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                        # Extract custom colors from config
                        color_matches = re.findall(r'colors:\s*{([^}]+)}', content, re.DOTALL)
                        for match in color_matches:
                            # Extract color names
                            color_names = re.findall(r'([a-zA-Z][a-zA-Z0-9-]*)', match)
                            colors.extend(color_names[:5])  # Limit to first 5 colors
                except:
                    pass
        
        # Default Tailwind colors if none found
        if not colors:
            colors = ['blue', 'gray', 'green', 'red', 'yellow']
        
        return colors
    
    def _extract_spacing_patterns(self, project_path: str) -> List[str]:
        """Extract spacing patterns from existing components"""
        
        spacing_patterns = []
        
        # Look for common component directories
        component_dirs = ['src/components', 'components', 'app/components']
        
        for comp_dir in component_dirs:
            dir_path = os.path.join(project_path, comp_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith(('.tsx', '.jsx', '.ts', '.js')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    # Extract Tailwind spacing classes
                                    spacing_matches = re.findall(r'[mp][xybtlr]?-(\d+)', content)
                                    spacing_patterns.extend(spacing_matches)
                            except:
                                continue
        
        # Get unique spacing values, limit to common ones
        unique_spacing = list(set(spacing_patterns))
        common_spacing = ['2', '4', '6', '8', '12', '16']
        
        return [s for s in common_spacing if s in unique_spacing] or common_spacing[:4]
    
    def _extract_typography_scale(self, project_path: str) -> List[str]:
        """Extract typography scale from existing components"""
        
        typography = []
        
        # Look for common component directories
        component_dirs = ['src/components', 'components', 'app/components']
        
        for comp_dir in component_dirs:
            dir_path = os.path.join(project_path, comp_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith(('.tsx', '.jsx', '.ts', '.js')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r') as f:
                                    content = f.read()
                                    # Extract Tailwind text size classes
                                    text_matches = re.findall(r'text-(xs|sm|base|lg|xl|2xl|3xl|4xl)', content)
                                    typography.extend(text_matches)
                            except:
                                continue
        
        # Default typography scale
        default_typography = ['sm', 'base', 'lg', 'xl', '2xl']
        unique_typography = list(set(typography))
        
        return [t for t in default_typography if t in unique_typography] or default_typography[:3]
    
    def _extract_shadow_patterns(self, project_path: str) -> List[str]:
        """Extract shadow patterns from existing components"""
        return ['sm', 'md', 'lg']  # Default shadows
    
    def _extract_border_patterns(self, project_path: str) -> List[str]:
        """Extract border radius patterns from existing components"""
        return ['sm', 'md', 'lg']  # Default border radius
    
    def _analyze_component_patterns(self, project_path: str) -> Dict:
        """Analyze existing component patterns"""
        
        return {
            'button_variants': self._analyze_button_patterns(project_path),
            'layout_patterns': self._analyze_layout_structures(project_path),
            'animation_styles': self._extract_animation_patterns(project_path)
        }
    
    def _analyze_button_patterns(self, project_path: str) -> List[str]:
        """Analyze button component patterns"""
        return ['primary', 'secondary', 'outline']  # Default button variants
    
    def _analyze_layout_structures(self, project_path: str) -> List[str]:
        """Analyze layout patterns"""
        return ['grid', 'flex', 'container']  # Default layout patterns
    
    def _extract_animation_patterns(self, project_path: str) -> List[str]:
        """Extract animation patterns"""
        return ['fade', 'slide', 'scale']  # Default animations
    
    def _analyze_project_structure(self, project_path: str) -> Dict:
        """Analyze project structure for component placement"""
        
        structure = {
            'components_dir': self._find_components_directory(project_path),
            'pages_dir': self._find_pages_directory(project_path),
            'styles_dir': self._find_styles_directory(project_path)
        }
        
        return structure
    
    def _find_components_directory(self, project_path: str) -> Optional[str]:
        """Find the main components directory"""
        
        possible_dirs = ['src/components', 'components', 'app/components']
        
        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path
        
        return 'src/components'  # Default
    
    def _find_pages_directory(self, project_path: str) -> Optional[str]:
        """Find the pages directory"""
        
        possible_dirs = ['src/pages', 'pages', 'app', 'src/app']
        
        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path
        
        return 'src/pages'  # Default
    
    def _find_styles_directory(self, project_path: str) -> Optional[str]:
        """Find the styles directory"""
        
        possible_dirs = ['src/styles', 'styles', 'src/css', 'css']
        
        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path
        
        return 'src/styles'  # Default