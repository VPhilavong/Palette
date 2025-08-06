"""
Pre-Generation Dependency Validator - Validates dependencies before component generation.

This system prevents import errors by checking dependency availability and compatibility
before generating components. It ensures all required packages are installed and
compatible with the project configuration.
"""

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import re

from .validator import ValidationIssue, ValidationLevel


class DependencyType(Enum):
    """Types of dependencies that can be validated."""
    
    CORE = "core"              # Essential dependencies (react, next, etc.)
    UI_LIBRARY = "ui_library"  # UI component libraries (chakra-ui, mui, etc.)
    STYLING = "styling"        # Styling libraries (tailwindcss, styled-components)
    UTILITY = "utility"        # Utility libraries (lodash, date-fns, etc.)
    DEVELOPMENT = "development" # Dev dependencies (typescript, eslint, etc.)


class CompatibilityLevel(Enum):
    """Compatibility levels for dependency checking."""
    
    STRICT = "strict"      # Exact version matching
    COMPATIBLE = "compatible"  # Compatible version ranges
    FLEXIBLE = "flexible"  # Any available version


@dataclass
class DependencyRequirement:
    """Represents a dependency requirement for component generation."""
    
    name: str
    version_range: str
    dependency_type: DependencyType
    required: bool = True
    alternatives: List[str] = field(default_factory=list)
    framework_specific: List[str] = field(default_factory=list)  # e.g., ["nextjs", "react"]
    styling_specific: List[str] = field(default_factory=list)    # e.g., ["chakra", "tailwind"]
    description: str = ""


@dataclass
class DependencyValidationResult:
    """Result of dependency validation."""
    
    all_satisfied: bool
    missing_dependencies: List[DependencyRequirement] = field(default_factory=list)
    version_conflicts: List[Tuple[str, str, str]] = field(default_factory=list)  # (name, required, actual)
    suggestions: List[str] = field(default_factory=list)
    install_commands: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PreGenerationDependencyValidator:
    """
    Pre-generation dependency validation system.
    
    Validates that all required dependencies are available before generating components,
    preventing import errors and ensuring component compatibility.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.package_json_path = self.project_path / "package.json"
        self.node_modules_path = self.project_path / "node_modules"
        
        # Load project dependencies
        self.project_dependencies = self._load_project_dependencies()
        self.available_packages = self._scan_node_modules()
        
        # Initialize dependency requirements catalog
        self.dependency_catalog = self._initialize_dependency_catalog()
    
    def validate_dependencies_for_generation(
        self,
        component_requirements: List[str],
        framework: str = "react",
        styling_system: str = "tailwind",
        component_type: str = "component"
    ) -> DependencyValidationResult:
        """
        Validate dependencies needed for component generation.
        
        Args:
            component_requirements: List of features/libraries the component needs
            framework: Target framework (react, nextjs, vue)
            styling_system: Target styling system (tailwind, chakra, mui)
            component_type: Type of component (component, page, hook, util)
            
        Returns:
            DependencyValidationResult with validation details
        """
        
        # Determine required dependencies based on requirements
        required_deps = self._determine_required_dependencies(
            component_requirements, framework, styling_system, component_type
        )
        
        missing_deps = []
        version_conflicts = []
        suggestions = []
        install_commands = []
        warnings = []
        
        # Validate each required dependency
        for dep_req in required_deps:
            validation_result = self._validate_single_dependency(dep_req)
            
            if not validation_result["satisfied"]:
                if validation_result["missing"]:
                    missing_deps.append(dep_req)
                    install_commands.extend(validation_result["install_commands"])
                
                if validation_result["version_conflict"]:
                    version_conflicts.append(validation_result["version_conflict"])
                
                suggestions.extend(validation_result["suggestions"])
                warnings.extend(validation_result["warnings"])
        
        # Generate installation commands
        if missing_deps:
            install_commands = self._generate_install_commands(missing_deps)
        
        # Add framework-specific suggestions
        suggestions.extend(self._get_framework_suggestions(framework, styling_system))
        
        all_satisfied = len(missing_deps) == 0 and len(version_conflicts) == 0
        
        return DependencyValidationResult(
            all_satisfied=all_satisfied,
            missing_dependencies=missing_deps,
            version_conflicts=version_conflicts,
            suggestions=suggestions,
            install_commands=install_commands,
            warnings=warnings
        )
    
    def _load_project_dependencies(self) -> Dict[str, str]:
        """Load dependencies from package.json."""
        
        dependencies = {}
        
        if self.package_json_path.exists():
            try:
                with open(self.package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Combine dependencies and devDependencies
                dependencies.update(package_data.get('dependencies', {}))
                dependencies.update(package_data.get('devDependencies', {}))
                
            except Exception as e:
                print(f"Warning: Could not load package.json: {e}")
        
        return dependencies
    
    def _scan_node_modules(self) -> Set[str]:
        """Scan node_modules for available packages."""
        
        packages = set()
        
        if self.node_modules_path.exists():
            for item in self.node_modules_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    packages.add(item.name)
                    
                    # Handle scoped packages
                    if item.name.startswith('@'):
                        for subitem in item.iterdir():
                            if subitem.is_dir():
                                packages.add(f"{item.name}/{subitem.name}")
        
        return packages
    
    def _initialize_dependency_catalog(self) -> Dict[str, DependencyRequirement]:
        """Initialize the catalog of known dependency requirements."""
        
        catalog = {}
        
        # Core React dependencies
        catalog["react"] = DependencyRequirement(
            name="react",
            version_range=">=17.0.0",
            dependency_type=DependencyType.CORE,
            description="React library for building user interfaces"
        )
        
        catalog["react-dom"] = DependencyRequirement(
            name="react-dom",
            version_range=">=17.0.0",
            dependency_type=DependencyType.CORE,
            description="React DOM rendering library"
        )
        
        # Next.js dependencies
        catalog["next"] = DependencyRequirement(
            name="next",
            version_range=">=13.0.0",
            dependency_type=DependencyType.CORE,
            framework_specific=["nextjs"],
            description="Next.js React framework"
        )
        
        catalog["next-image"] = DependencyRequirement(
            name="next",  # next/image is part of next
            version_range=">=13.0.0",
            dependency_type=DependencyType.CORE,
            framework_specific=["nextjs"],
            description="Next.js optimized image component"
        )
        
        # TypeScript dependencies
        catalog["typescript"] = DependencyRequirement(
            name="typescript",
            version_range=">=4.5.0",
            dependency_type=DependencyType.DEVELOPMENT,
            description="TypeScript language support"
        )
        
        catalog["@types/react"] = DependencyRequirement(
            name="@types/react",
            version_range=">=17.0.0",
            dependency_type=DependencyType.DEVELOPMENT,
            description="TypeScript definitions for React"
        )
        
        catalog["@types/react-dom"] = DependencyRequirement(
            name="@types/react-dom",
            version_range=">=17.0.0",
            dependency_type=DependencyType.DEVELOPMENT,
            description="TypeScript definitions for React DOM"
        )
        
        # Chakra UI dependencies
        catalog["@chakra-ui/react"] = DependencyRequirement(
            name="@chakra-ui/react",
            version_range=">=2.0.0",
            dependency_type=DependencyType.UI_LIBRARY,
            styling_specific=["chakra"],
            description="Chakra UI React component library"
        )
        
        catalog["@emotion/react"] = DependencyRequirement(
            name="@emotion/react",
            version_range=">=11.0.0",
            dependency_type=DependencyType.STYLING,
            styling_specific=["chakra"],
            description="Emotion CSS-in-JS library (required for Chakra UI)"
        )
        
        catalog["@emotion/styled"] = DependencyRequirement(
            name="@emotion/styled",
            version_range=">=11.0.0",
            dependency_type=DependencyType.STYLING,
            styling_specific=["chakra"],
            description="Emotion styled components (required for Chakra UI)"
        )
        
        catalog["framer-motion"] = DependencyRequirement(
            name="framer-motion",
            version_range=">=6.0.0",
            dependency_type=DependencyType.UTILITY,
            styling_specific=["chakra"],
            required=False,
            description="Animation library (optional for Chakra UI)"
        )
        
        # Tailwind CSS dependencies
        catalog["tailwindcss"] = DependencyRequirement(
            name="tailwindcss",
            version_range=">=3.0.0",
            dependency_type=DependencyType.STYLING,
            styling_specific=["tailwind"],
            description="Tailwind CSS utility-first framework"
        )
        
        catalog["autoprefixer"] = DependencyRequirement(
            name="autoprefixer",
            version_range=">=10.0.0",
            dependency_type=DependencyType.STYLING,
            styling_specific=["tailwind"],
            description="PostCSS plugin to parse CSS and add vendor prefixes"
        )
        
        catalog["postcss"] = DependencyRequirement(
            name="postcss",
            version_range=">=8.0.0",
            dependency_type=DependencyType.STYLING,
            styling_specific=["tailwind"],
            description="Tool for transforming CSS with JavaScript"
        )
        
        # Material-UI dependencies
        catalog["@mui/material"] = DependencyRequirement(
            name="@mui/material",
            version_range=">=5.0.0",
            dependency_type=DependencyType.UI_LIBRARY,
            styling_specific=["mui", "material-ui"],
            description="Material-UI React component library"
        )
        
        catalog["@mui/icons-material"] = DependencyRequirement(
            name="@mui/icons-material",
            version_range=">=5.0.0",
            dependency_type=DependencyType.UI_LIBRARY,
            styling_specific=["mui", "material-ui"],
            required=False,
            description="Material-UI icons"
        )
        
        # Common utility libraries
        catalog["clsx"] = DependencyRequirement(
            name="clsx",
            version_range=">=1.0.0",
            dependency_type=DependencyType.UTILITY,
            required=False,
            alternatives=["classnames", "cn"],
            description="Utility for constructing className strings conditionally"
        )
        
        catalog["classnames"] = DependencyRequirement(
            name="classnames",
            version_range=">=2.0.0",
            dependency_type=DependencyType.UTILITY,
            required=False,
            alternatives=["clsx", "cn"],
            description="Utility for conditionally joining classNames together"
        )
        
        # React Hook Form
        catalog["react-hook-form"] = DependencyRequirement(
            name="react-hook-form",
            version_range=">=7.0.0",
            dependency_type=DependencyType.UTILITY,
            required=False,
            description="Performant, flexible forms with easy validation"
        )
        
        # React Router
        catalog["react-router-dom"] = DependencyRequirement(
            name="react-router-dom",
            version_range=">=6.0.0",
            dependency_type=DependencyType.UTILITY,
            framework_specific=["react", "vite"],
            required=False,
            description="Declarative routing for React"
        )
        
        return catalog
    
    def _determine_required_dependencies(
        self,
        component_requirements: List[str],
        framework: str,
        styling_system: str,
        component_type: str
    ) -> List[DependencyRequirement]:
        """Determine which dependencies are required based on component needs."""
        
        required_deps = []
        
        # Always require React for React-based frameworks
        if framework in ["react", "nextjs", "vite"]:
            required_deps.extend([
                self.dependency_catalog["react"],
                self.dependency_catalog["react-dom"]
            ])
        
        # Framework-specific dependencies
        if framework == "nextjs":
            required_deps.append(self.dependency_catalog["next"])
        
        # TypeScript dependencies (if .tsx/.ts files detected)
        if self._has_typescript_files():
            required_deps.extend([
                self.dependency_catalog["typescript"],
                self.dependency_catalog["@types/react"],
                self.dependency_catalog["@types/react-dom"]
            ])
        
        # Styling system dependencies
        if styling_system == "chakra":
            required_deps.extend([
                self.dependency_catalog["@chakra-ui/react"],
                self.dependency_catalog["@emotion/react"],
                self.dependency_catalog["@emotion/styled"]
            ])
        elif styling_system == "tailwind":
            required_deps.extend([
                self.dependency_catalog["tailwindcss"],
                self.dependency_catalog["autoprefixer"],
                self.dependency_catalog["postcss"]
            ])
        elif styling_system in ["mui", "material-ui"]:
            required_deps.append(self.dependency_catalog["@mui/material"])
        
        # Component requirement-specific dependencies
        for requirement in component_requirements:
            req_lower = requirement.lower()
            
            # Image-related requirements
            if any(keyword in req_lower for keyword in ["image", "photo", "picture", "gallery"]):
                if framework == "nextjs":
                    required_deps.append(self.dependency_catalog["next-image"])
            
            # Form-related requirements
            if any(keyword in req_lower for keyword in ["form", "input", "validation", "submit"]):
                # Optional: suggest react-hook-form
                form_dep = self.dependency_catalog["react-hook-form"]
                form_dep.required = False  # Make it optional
                required_deps.append(form_dep)
            
            # Icon-related requirements
            if any(keyword in req_lower for keyword in ["icon", "button", "menu"]):
                if styling_system in ["mui", "material-ui"]:
                    icons_dep = self.dependency_catalog["@mui/icons-material"]
                    icons_dep.required = False
                    required_deps.append(icons_dep)
            
            # Class name utilities
            if any(keyword in req_lower for keyword in ["conditional", "dynamic", "toggle"]):
                clsx_dep = self.dependency_catalog["clsx"]
                clsx_dep.required = False
                required_deps.append(clsx_dep)
        
        # Remove duplicates
        seen_names = set()
        unique_deps = []
        for dep in required_deps:
            if dep.name not in seen_names:
                unique_deps.append(dep)
                seen_names.add(dep.name)
        
        return unique_deps
    
    def _validate_single_dependency(self, dep_req: DependencyRequirement) -> Dict[str, Any]:
        """Validate a single dependency requirement."""
        
        result = {
            "satisfied": False,
            "missing": False,
            "version_conflict": None,
            "suggestions": [],
            "warnings": [],
            "install_commands": []
        }
        
        # Check if package is installed
        if dep_req.name not in self.project_dependencies:
            if dep_req.name not in self.available_packages:
                result["missing"] = True
                result["install_commands"].append(f"npm install {dep_req.name}")
                
                if dep_req.alternatives:
                    # Check if any alternatives are available
                    available_alternatives = [
                        alt for alt in dep_req.alternatives 
                        if alt in self.project_dependencies or alt in self.available_packages
                    ]
                    if available_alternatives:
                        result["suggestions"].append(
                            f"Alternative packages available: {', '.join(available_alternatives)}"
                        )
                
                if not dep_req.required:
                    result["warnings"].append(
                        f"Optional dependency {dep_req.name} not found - {dep_req.description}"
                    )
                    result["satisfied"] = True  # Optional deps don't fail validation
                
                return result
        
        # Check version compatibility (basic check)
        if dep_req.name in self.project_dependencies:
            installed_version = self.project_dependencies[dep_req.name]
            if self._check_version_compatibility(installed_version, dep_req.version_range):
                result["satisfied"] = True
            else:
                result["version_conflict"] = (dep_req.name, dep_req.version_range, installed_version)
                result["suggestions"].append(
                    f"Update {dep_req.name} to satisfy version requirement {dep_req.version_range}"
                )
        else:
            result["satisfied"] = True  # Package is available in node_modules
        
        return result
    
    def _check_version_compatibility(self, installed: str, required: str) -> bool:
        """Basic version compatibility check."""
        
        # Remove version prefixes and compare
        installed_clean = re.sub(r'^[\^~>=<]', '', installed)
        required_clean = re.sub(r'^[\^~>=<]', '', required)
        
        try:
            # Basic semantic version comparison
            installed_parts = [int(x) for x in installed_clean.split('.')]
            required_parts = [int(x) for x in required_clean.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(installed_parts), len(required_parts))
            installed_parts.extend([0] * (max_len - len(installed_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            # Simple >= comparison
            return installed_parts >= required_parts
            
        except ValueError:
            # If version parsing fails, assume compatible
            return True
    
    def _generate_install_commands(self, missing_deps: List[DependencyRequirement]) -> List[str]:
        """Generate installation commands for missing dependencies."""
        
        commands = []
        
        # Group by dependency type for better organization
        core_deps = [dep for dep in missing_deps if dep.dependency_type == DependencyType.CORE]
        ui_deps = [dep for dep in missing_deps if dep.dependency_type == DependencyType.UI_LIBRARY]
        styling_deps = [dep for dep in missing_deps if dep.dependency_type == DependencyType.STYLING]
        util_deps = [dep for dep in missing_deps if dep.dependency_type == DependencyType.UTILITY and dep.required]
        dev_deps = [dep for dep in missing_deps if dep.dependency_type == DependencyType.DEVELOPMENT]
        
        # Generate grouped install commands
        if core_deps:
            core_names = [dep.name for dep in core_deps]
            commands.append(f"npm install {' '.join(core_names)}")
        
        if ui_deps or styling_deps:
            ui_styling_names = [dep.name for dep in ui_deps + styling_deps]
            commands.append(f"npm install {' '.join(ui_styling_names)}")
        
        if util_deps:
            util_names = [dep.name for dep in util_deps]
            commands.append(f"npm install {' '.join(util_names)}")
        
        if dev_deps:
            dev_names = [dep.name for dep in dev_deps]
            commands.append(f"npm install --save-dev {' '.join(dev_names)}")
        
        return commands
    
    def _get_framework_suggestions(self, framework: str, styling_system: str) -> List[str]:
        """Get framework-specific suggestions."""
        
        suggestions = []
        
        if framework == "nextjs":
            suggestions.append("Consider using Next.js Image component for optimized images")
            suggestions.append("Use 'use client' directive for client-side components")
        
        if styling_system == "chakra":
            suggestions.append("Avoid mixing Tailwind classes with Chakra UI components")
            suggestions.append("Use Chakra UI theme for consistent styling")
        elif styling_system == "tailwind":
            suggestions.append("Configure Tailwind CSS with proper purging for production")
            suggestions.append("Consider using Tailwind CSS IntelliSense for better DX")
        
        return suggestions
    
    def _has_typescript_files(self) -> bool:
        """Check if project has TypeScript files."""
        
        # Check for tsconfig.json
        if (self.project_path / "tsconfig.json").exists():
            return True
        
        # Check for .ts/.tsx files in common directories
        common_dirs = ["src", "components", "pages", "app", "lib", "utils"]
        
        for dir_name in common_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.suffix in [".ts", ".tsx"]:
                        return True
        
        return False
    
    def get_installation_script(self, validation_result: DependencyValidationResult) -> str:
        """Generate a complete installation script for missing dependencies."""
        
        if validation_result.all_satisfied:
            return "# All dependencies are satisfied! ✅"
        
        script_lines = [
            "#!/bin/bash",
            "# Dependency Installation Script",
            "# Generated by Palette Zero-Error System",
            "",
            "echo '🔧 Installing missing dependencies...'",
            ""
        ]
        
        for i, command in enumerate(validation_result.install_commands, 1):
            script_lines.extend([
                f"echo 'Step {i}: {command}'",
                command,
                "if [ $? -ne 0 ]; then",
                f"  echo '❌ Failed to install dependencies in step {i}'",
                "  exit 1",
                "fi",
                ""
            ])
        
        script_lines.extend([
            "echo '✅ All dependencies installed successfully!'",
            "echo '🚀 Ready for component generation!'"
        ])
        
        return "\\n".join(script_lines)