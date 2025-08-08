"""
Simple Vite Project Analyzer

This module provides a lightweight analyzer for Vite + React + shadcn/ui projects,
replacing the complex multi-framework ProjectAnalyzer with a focused approach.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


class SimpleViteAnalyzer:
    """Lightweight analyzer for Vite + React + shadcn/ui projects"""
    
    def __init__(self):
        self.project_path: Optional[str] = None
        self.vite_config_path: Optional[str] = None
        self.shadcn_config_path: Optional[str] = None
        self.package_json_path: Optional[str] = None
        
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze a Vite project and return simplified context"""
        self.project_path = project_path
        
        analysis_result = {
            "framework": "vite",
            "ui_library": "shadcn/ui",
            "styling": "tailwind",
            "typescript": True,
            "components_directory": "src/components/ui",
            "lib_directory": "src/lib",
            "project_type": "vite-react-shadcn",
            "is_valid_project": self._is_valid_vite_project(),
            "available_components": self._get_available_shadcn_components(),
            "project_structure": self._get_project_structure(),
            "tailwind_config": self._get_tailwind_config(),
            "components_config": self._get_components_config()
        }
        
        return analysis_result
    
    def _is_valid_vite_project(self) -> bool:
        """Check if this is a valid Vite project"""
        if not self.project_path:
            return False
            
        # Check for vite.config.js/ts
        vite_configs = ["vite.config.js", "vite.config.ts"]
        for config in vite_configs:
            config_path = os.path.join(self.project_path, config)
            if os.path.exists(config_path):
                self.vite_config_path = config_path
                break
        
        # Check for package.json with Vite dependencies
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            self.package_json_path = package_json_path
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    
                    # Check for React and Vite
                    has_react = 'react' in deps
                    has_vite = 'vite' in dev_deps
                    
                    return has_react and has_vite and self.vite_config_path is not None
            except (json.JSONDecodeError, FileNotFoundError):
                return False
        
        return False
    
    def _get_available_shadcn_components(self) -> List[str]:
        """Get list of available shadcn/ui components in the project"""
        if not self.project_path:
            return []
            
        components_dir = os.path.join(self.project_path, "src", "components", "ui")
        if not os.path.exists(components_dir):
            return []
        
        components = []
        for file in os.listdir(components_dir):
            if file.endswith(('.tsx', '.ts')) and not file.startswith('.'):
                component_name = file.replace('.tsx', '').replace('.ts', '')
                components.append(component_name)
        
        return sorted(components)
    
    def _get_project_structure(self) -> Dict[str, Any]:
        """Get basic project structure info"""
        if not self.project_path:
            return {}
            
        structure = {
            "src_directory": os.path.join(self.project_path, "src"),
            "components_directory": os.path.join(self.project_path, "src", "components"),
            "ui_components_directory": os.path.join(self.project_path, "src", "components", "ui"),
            "lib_directory": os.path.join(self.project_path, "src", "lib"),
            "public_directory": os.path.join(self.project_path, "public"),
            "has_components_dir": os.path.exists(os.path.join(self.project_path, "src", "components")),
            "has_ui_dir": os.path.exists(os.path.join(self.project_path, "src", "components", "ui")),
            "has_lib_dir": os.path.exists(os.path.join(self.project_path, "src", "lib"))
        }
        
        return structure
    
    def _get_tailwind_config(self) -> Optional[Dict[str, Any]]:
        """Get Tailwind CSS configuration if available"""
        if not self.project_path:
            return None
            
        tailwind_configs = ["tailwind.config.js", "tailwind.config.ts"]
        for config in tailwind_configs:
            config_path = os.path.join(self.project_path, config)
            if os.path.exists(config_path):
                # For simplicity, just return that it exists
                # In a full implementation, we could parse the config
                return {
                    "config_file": config,
                    "exists": True,
                    "path": config_path
                }
        
        return None
    
    def _get_components_config(self) -> Optional[Dict[str, Any]]:
        """Get shadcn/ui components.json configuration"""
        if not self.project_path:
            return None
            
        components_config_path = os.path.join(self.project_path, "components.json")
        self.shadcn_config_path = components_config_path
        
        if os.path.exists(components_config_path):
            try:
                with open(components_config_path, 'r') as f:
                    config = json.load(f)
                    return config
            except (json.JSONDecodeError, FileNotFoundError):
                return None
        
        return None
    
    def get_component_path(self, component_name: str) -> str:
        """Get the expected path for a component"""
        if not self.project_path:
            return f"src/components/ui/{component_name}.tsx"
            
        return os.path.join(self.project_path, "src", "components", "ui", f"{component_name}.tsx")
    
    def get_generation_context(self) -> str:
        """Get context string for component generation"""
        if not self.project_path:
            return "Generating for Vite + React + TypeScript + shadcn/ui project"
            
        analysis = self.analyze_project(self.project_path)
        available_components = analysis.get("available_components", [])
        
        context_parts = [
            "Project: Vite + React + TypeScript + shadcn/ui",
            f"Components directory: src/components/ui/",
            f"Utils: src/lib/utils.ts (cn utility available)",
            f"Styling: Tailwind CSS with CSS variables"
        ]
        
        if available_components:
            context_parts.append(f"Available components: {', '.join(available_components)}")
        
        return "\n".join(context_parts)
    
    def should_use_typescript(self) -> bool:
        """Always return True for TypeScript in our simplified setup"""
        return True
    
    def get_import_style(self) -> str:
        """Get the preferred import style for the project"""
        return "import { ComponentName } from '@/components/ui/component-name'"
    
    def get_styling_approach(self) -> str:
        """Get the styling approach for the project"""
        return "tailwind-with-css-variables"