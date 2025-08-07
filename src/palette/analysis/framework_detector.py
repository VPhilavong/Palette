"""
Framework detection module.
Responsible for detecting React frameworks and project structures.
"""

import os
import json
from typing import Optional, Dict, List
from pathlib import Path

from ..interfaces import ProjectStructure


class FrameworkDetector:
    """Detects React frameworks and project structures."""
    
    def __init__(self):
        # Simplified: Only support Vite + React projects
        self.supported_frameworks = {
            "vite": ["vite.config.js", "vite.config.ts", "vite.config.mjs"],
        }
    
    def detect(self, project_path: str) -> ProjectStructure:
        """
        Detect project structure for Vite + React projects.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectStructure with detected information
        """
        framework = self._detect_framework(project_path)
        styling = self._detect_styling_system(project_path)
        component_library = self._detect_component_library(project_path)
        
        # Get directory structure
        components_dir = self._find_components_directory(project_path)
        pages_dir = None  # Vite projects don't have pages directories
        
        # Check for TypeScript and Tailwind
        has_typescript = self._has_typescript(project_path)
        has_tailwind = styling == "tailwind"
        
        return ProjectStructure(
            framework=framework,
            styling=styling,
            component_library=component_library,
            is_monorepo=False,  # We don't support monorepos anymore
            monorepo_type=None,
            components_dir=components_dir,
            pages_dir=pages_dir,
            has_typescript=has_typescript,
            has_tailwind=has_tailwind
        )
    
    def _detect_framework(self, project_path: str) -> str:
        """Detect if this is a Vite + React project."""
        # Check for Vite config files
        vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
        has_vite_config = any(
            os.path.exists(os.path.join(project_path, config))
            for config in vite_configs
        )
        
        # Check package.json for Vite and React
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
                    
                    has_vite = "vite" in dependencies
                    has_react = "react" in dependencies
                    
                    if has_vite and has_react:
                        return "vite"
            except json.JSONDecodeError:
                pass
        
        # If we have Vite config, assume it's a Vite project
        if has_vite_config:
            return "vite"
        
        return "unknown"
    
    
    
    def _detect_styling_system(self, project_path: str) -> str:
        """Detect the styling system (Tailwind, CSS modules, etc.)."""
        # Check for Tailwind config
        tailwind_configs = ["tailwind.config.js", "tailwind.config.ts"]
        for config in tailwind_configs:
            if os.path.exists(os.path.join(project_path, config)):
                return "tailwind"
        
        # Check package.json for styling dependencies
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
                    
                    if "tailwindcss" in dependencies:
                        return "tailwind"
                    elif "styled-components" in dependencies:
                        return "styled-components"
                    elif "emotion" in dependencies or "@emotion/react" in dependencies:
                        return "emotion"
            except json.JSONDecodeError:
                pass
        
        return "css"
    
    def _detect_component_library(self, project_path: str) -> str:
        """Detect if shadcn/ui is being used."""
        # We primarily support shadcn/ui
        component_libraries = {
            "shadcn/ui": ["components/ui/", "@radix-ui", "class-variance-authority"],
        }
        
        # Check package.json dependencies
        package_json_paths = [os.path.join(project_path, "package.json")]
        
        # Also check frontend/package.json for full-stack projects
        frontend_package_path = os.path.join(project_path, "frontend", "package.json")
        if os.path.exists(frontend_package_path):
            package_json_paths.append(frontend_package_path)
        
        for package_json_path in package_json_paths:
            if not os.path.exists(package_json_path):
                continue
            
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
                    
                    # Check for shadcn/ui with proper validation
                    if self._is_shadcn_ui_project(os.path.dirname(package_json_path), dependencies):
                        return "shadcn/ui"
                    
                    # Check other component libraries
                    for library, indicators in component_libraries.items():
                        if library == "shadcn/ui":
                            continue  # Already checked above
                        
                        for indicator in indicators:
                            if indicator in dependencies:
                                return library
                            # Check for directory structure indicators
                            if indicator.endswith("/") and os.path.exists(
                                os.path.join(os.path.dirname(package_json_path), indicator)
                            ):
                                return library
            except json.JSONDecodeError:
                pass
        
        return "none"
    
    def _is_shadcn_ui_project(self, project_path: str, dependencies: dict) -> bool:
        """Validate if project actually has shadcn/ui setup."""
        # Check for shadcn/ui indicators in dependencies
        shadcn_indicators = [
            "@radix-ui",
            "class-variance-authority",
            "clsx",
            "tailwind-merge",
        ]
        has_shadcn_deps = any(
            indicator in dep
            for dep in dependencies.keys()
            for indicator in shadcn_indicators
        )
        
        # Check for required directory structure
        components_ui_path = os.path.join(project_path, "components", "ui")
        lib_utils_path = os.path.join(project_path, "lib", "utils.ts")
        
        # Alternative paths
        src_components_ui_path = os.path.join(project_path, "src", "components", "ui")
        src_lib_utils_path = os.path.join(project_path, "src", "lib", "utils.ts")
        
        has_components_ui = os.path.exists(components_ui_path) or os.path.exists(src_components_ui_path)
        has_lib_utils = os.path.exists(lib_utils_path) or os.path.exists(src_lib_utils_path)
        
        # Only return true if both dependencies and structure exist
        return has_shadcn_deps and has_components_ui and has_lib_utils
    
    def _find_components_directory(self, project_path: str) -> Optional[str]:
        """Find the main components directory."""
        possible_dirs = ["src/components", "components", "app/components"]
        
        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                return dir_path
        
        return None
    
    
    def _has_typescript(self, project_path: str) -> bool:
        """Check if the project uses TypeScript."""
        # Check for tsconfig.json
        if os.path.exists(os.path.join(project_path, "tsconfig.json")):
            return True
        
        # Check package.json for TypeScript dependency
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
                    return "typescript" in dependencies
            except json.JSONDecodeError:
                pass
        
        return False