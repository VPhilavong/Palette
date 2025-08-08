#!/usr/bin/env python3
"""
Simple project analyzer - detects framework, styling, and UI library
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path


class SimpleAnalyzer:
    """Simplified project analysis that actually works"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
    
    def analyze(self) -> Dict:
        """Analyze project and return essential configuration"""
        
        context = {
            'framework': self._detect_framework(),
            'styling': self._detect_styling(),
            'ui_library': self._detect_ui_library(),
            'typescript': self._has_typescript(),
            'project_path': str(self.project_path)
        }
        
        return context
    
    def _detect_framework(self) -> str:
        """Detect React framework (Next.js, Vite, CRA, etc.)"""
        
        package_json = self._read_package_json()
        if not package_json:
            return 'react'  # Default assumption
        
        dependencies = {**package_json.get('dependencies', {}), 
                       **package_json.get('devDependencies', {})}
        
        # Check for specific frameworks
        if 'next' in dependencies:
            return 'next.js'
        elif 'gatsby' in dependencies:
            return 'gatsby'
        elif '@remix-run/react' in dependencies:
            return 'remix'
        elif 'vite' in dependencies:
            return 'vite'
        elif 'react-scripts' in dependencies:
            return 'create-react-app'
        elif 'react' in dependencies:
            return 'react'
        else:
            return 'react'  # Default
    
    def _detect_styling(self) -> str:
        """Detect styling solution"""
        
        # Check for Tailwind config
        tailwind_files = [
            'tailwind.config.js', 'tailwind.config.ts', 
            'tailwind.config.cjs', 'tailwind.config.mjs'
        ]
        
        for config_file in tailwind_files:
            if (self.project_path / config_file).exists():
                return 'tailwind'
        
        package_json = self._read_package_json()
        if package_json:
            dependencies = {**package_json.get('dependencies', {}), 
                           **package_json.get('devDependencies', {})}
            
            # Check for styling libraries
            if 'tailwindcss' in dependencies:
                return 'tailwind'
            elif 'styled-components' in dependencies:
                return 'styled-components'
            elif '@emotion/react' in dependencies:
                return 'emotion'
            elif 'sass' in dependencies or 'node-sass' in dependencies:
                return 'sass'
        
        # Check for CSS files
        if list(self.project_path.glob('**/*.css')):
            return 'css'
        
        return 'css'  # Default
    
    def _detect_ui_library(self) -> str:
        """Detect UI component library"""
        
        package_json = self._read_package_json()
        if not package_json:
            return 'none'
        
        dependencies = {**package_json.get('dependencies', {}), 
                       **package_json.get('devDependencies', {})}
        
        # Check for common UI libraries
        ui_libraries = {
            '@radix-ui/react-slot': 'shadcn/ui',
            '@mui/material': 'material-ui', 
            '@chakra-ui/react': 'chakra-ui',
            'antd': 'ant-design',
            '@headlessui/react': 'headless-ui',
            '@mantine/core': 'mantine',
            'react-bootstrap': 'react-bootstrap'
        }
        
        for dep, library in ui_libraries.items():
            if dep in dependencies:
                return library
        
        # Check for shadcn/ui specific indicators
        if (self.project_path / 'components' / 'ui').exists():
            return 'shadcn/ui'
        
        return 'none'
    
    def _has_typescript(self) -> bool:
        """Check if project uses TypeScript"""
        
        # Check for tsconfig.json
        if (self.project_path / 'tsconfig.json').exists():
            return True
        
        # Check for .ts or .tsx files
        if list(self.project_path.glob('**/*.ts')) or list(self.project_path.glob('**/*.tsx')):
            return True
        
        # Check package.json for TypeScript dependency
        package_json = self._read_package_json()
        if package_json:
            dependencies = {**package_json.get('dependencies', {}), 
                           **package_json.get('devDependencies', {})}
            if 'typescript' in dependencies or '@types/react' in dependencies:
                return True
        
        return False
    
    def _read_package_json(self) -> Optional[Dict]:
        """Read and parse package.json"""
        
        package_path = self.project_path / 'package.json'
        if not package_path.exists():
            return None
        
        try:
            with open(package_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def get_components_directory(self) -> Optional[str]:
        """Find the components directory"""
        
        common_paths = [
            'src/components',
            'components', 
            'src/app/components',
            'app/components',
            'lib/components'
        ]
        
        for path in common_paths:
            full_path = self.project_path / path
            if full_path.exists() and full_path.is_dir():
                return str(full_path)
        
        return None
    
    def print_analysis(self):
        """Print analysis results in a nice format"""
        
        context = self.analyze()
        
        print("📊 PROJECT ANALYSIS:")
        print("-" * 40)
        print(f"Framework:      {context['framework']}")
        print(f"Styling:        {context['styling']}")  
        print(f"UI Library:     {context['ui_library']}")
        print(f"TypeScript:     {'Yes' if context['typescript'] else 'No'}")
        
        components_dir = self.get_components_directory()
        if components_dir:
            print(f"Components:     {components_dir}")
        
        print("-" * 40)