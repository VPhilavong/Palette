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
        self.supported_frameworks = {
            "next.js": ["next.config.js", "next.config.ts", "app/", "pages/"],
            "remix": ["remix.config.js", "remix.config.ts", "app/routes/", "app/root.tsx"],
            "react": ["src/", "public/", "package.json"],
            "vite": ["vite.config.js", "vite.config.ts", "frontend/vite.config.js", "frontend/vite.config.ts"],
            "monorepo": ["turbo.json", "yarn.lock", "workspaces", "apps/", "packages/"],
            "fullstack": ["frontend/", "backend/", "docker-compose.yml"],
        }
        
        self.monorepo_patterns = {
            "calcom": ["@calcom/", "turbo.json", "packages/config/tailwind-preset.js"],
            "nx": ["nx.json", "workspace.json"],
            "lerna": ["lerna.json"],
            "rush": ["rush.json"],
        }
    
    def detect(self, project_path: str) -> ProjectStructure:
        """
        Detect project structure and framework.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectStructure with detected information
        """
        framework = self._detect_framework(project_path)
        styling = self._detect_styling_system(project_path)
        component_library = self._detect_component_library(project_path)
        monorepo_type = self._detect_monorepo_type(project_path)
        
        # Get directory structure
        components_dir = self._find_components_directory(project_path)
        pages_dir = self._find_pages_directory(project_path)
        
        # Check for TypeScript and Tailwind
        has_typescript = self._has_typescript(project_path)
        has_tailwind = styling == "tailwind"
        
        return ProjectStructure(
            framework=framework,
            styling=styling,
            component_library=component_library,
            is_monorepo=monorepo_type is not None,
            monorepo_type=monorepo_type,
            components_dir=components_dir,
            pages_dir=pages_dir,
            has_typescript=has_typescript,
            has_tailwind=has_tailwind
        )
    
    def _detect_framework(self, project_path: str) -> str:
        """Detect the React framework being used."""
        # First check for monorepo patterns
        monorepo_type = self._detect_monorepo_type(project_path)
        if monorepo_type:
            return f"monorepo-{monorepo_type}"
        
        # Check for full-stack structure
        fullstack_type = self._detect_fullstack_structure(project_path)
        if fullstack_type:
            return f"fullstack-{fullstack_type}"
        
        # Check package.json dependencies
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
                
                # Check for Remix first (before Vite, as Remix uses Vite)
                if any(dep.startswith("@remix-run/") for dep in dependencies):
                    return "remix"
                elif "next" in dependencies:
                    return "next.js"
                elif "vite" in dependencies:
                    return "vite"
                elif "react" in dependencies:
                    return "react"
            except json.JSONDecodeError:
                pass
        
        # Fallback to file-based detection
        for framework, indicators in self.supported_frameworks.items():
            if framework in ["monorepo", "fullstack"]:
                continue
            
            matches = sum(1 for indicator in indicators
                         if os.path.exists(os.path.join(project_path, indicator)))
            
            if matches >= 2:
                return framework
        
        return "unknown"
    
    def _detect_monorepo_type(self, project_path: str) -> Optional[str]:
        """Detect monorepo type and return the specific type."""
        for monorepo_type, indicators in self.monorepo_patterns.items():
            matches = 0
            for indicator in indicators:
                if os.path.exists(os.path.join(project_path, indicator)):
                    matches += 1
            
            # Require at least 2 matches for confidence
            if matches >= 2:
                return monorepo_type
        
        # Generic monorepo detection
        monorepo_files = ["turbo.json", "yarn.lock", "lerna.json", "nx.json"]
        monorepo_dirs = ["apps/", "packages/", "libs/"]
        
        has_config = any(os.path.exists(os.path.join(project_path, f)) for f in monorepo_files)
        has_structure = any(os.path.exists(os.path.join(project_path, d)) for d in monorepo_dirs)
        
        if has_config and has_structure:
            return "generic"
        
        return None
    
    def _detect_fullstack_structure(self, project_path: str) -> Optional[str]:
        """Detect if this is a full-stack project structure."""
        frontend_dir = os.path.join(project_path, "frontend")
        backend_dir = os.path.join(project_path, "backend")
        
        if os.path.exists(frontend_dir) and os.path.exists(backend_dir):
            # Check what's in the frontend
            frontend_package = os.path.join(frontend_dir, "package.json")
            if os.path.exists(frontend_package):
                try:
                    with open(frontend_package, "r") as f:
                        package_data = json.load(f)
                        deps = {**package_data.get("dependencies", {}),
                               **package_data.get("devDependencies", {})}
                        
                        if "next" in deps:
                            return "next.js"
                        elif "vite" in deps:
                            return "vite"
                        elif "react" in deps:
                            return "react"
                except json.JSONDecodeError:
                    pass
            
            return "generic"
        
        return None
    
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
        """Detect component library being used."""
        # Component library patterns
        component_libraries = {
            "shadcn/ui": ["components/ui/", "@radix-ui", "class-variance-authority"],
            "calcom": ["@calcom/ui", "class-variance-authority", "packages/ui"],
            "chakra-ui": ["@chakra-ui/react", "chakra-ui"],
            "material-ui": ["@mui/material", "@material-ui"],
            "ant-design": ["antd"],
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
    
    def _find_pages_directory(self, project_path: str) -> Optional[str]:
        """Find the pages/routes directory."""
        possible_dirs = ["app", "pages", "src/pages", "app/routes"]
        
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