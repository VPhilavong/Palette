"""
Package Analysis System for comprehensive project dependency validation.
Analyzes package.json, yarn.lock, package-lock.json and provides insights for import validation.
"""

import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from ..errors.decorators import handle_errors


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    BUN = "bun"
    UNKNOWN = "unknown"


class DependencyType(Enum):
    """Types of dependencies."""
    PRODUCTION = "dependencies"
    DEVELOPMENT = "devDependencies"
    PEER = "peerDependencies"
    OPTIONAL = "optionalDependencies"


@dataclass
class PackageInfo:
    """Information about a specific package."""
    name: str
    version: str
    dependency_type: DependencyType
    is_installed: bool = False
    install_path: Optional[str] = None
    exports: List[str] = field(default_factory=list)
    main_entry: Optional[str] = None
    types_entry: Optional[str] = None


@dataclass
class ProjectDependencyAnalysis:
    """Complete analysis of project dependencies."""
    package_manager: PackageManager
    total_packages: int
    production_packages: int
    dev_packages: int
    missing_packages: List[str] = field(default_factory=list)
    outdated_packages: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # name -> (current, latest)
    security_vulnerabilities: List[str] = field(default_factory=list)
    package_details: Dict[str, PackageInfo] = field(default_factory=dict)
    ui_libraries_detected: List[str] = field(default_factory=list)
    styling_systems_detected: List[str] = field(default_factory=list)
    framework_detected: Optional[str] = None
    typescript_support: bool = False
    analysis_errors: List[str] = field(default_factory=list)


class PackageAnalyzer:
    """
    Comprehensive package analysis system that provides deep insights
    into project dependencies for import validation and project understanding.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self._initialize_package_mappings()
    
    def _initialize_package_mappings(self):
        """Initialize mappings for different types of packages."""
        
        # UI Library mappings
        self.ui_library_packages = {
            '@chakra-ui/react': 'chakra-ui',
            '@mui/material': 'material-ui',
            'antd': 'ant-design',
            '@mantine/core': 'mantine',
            'react-bootstrap': 'react-bootstrap',
            'semantic-ui-react': 'semantic-ui',
            'grommet': 'grommet',
            '@headlessui/react': 'headless-ui',
            '@radix-ui/react-slot': 'shadcn/ui',  # Primary indicator for shadcn/ui
        }
        
        # Styling system packages
        self.styling_packages = {
            'tailwindcss': 'tailwind',
            'styled-components': 'styled-components',
            '@emotion/react': 'emotion',
            '@emotion/styled': 'emotion',
            'sass': 'sass',
            'less': 'less',
            'stylus': 'stylus',
        }
        
        # Framework packages
        self.framework_packages = {
            'next': 'next.js',
            'react': 'react',
            'vue': 'vue',
            '@angular/core': 'angular',
            'svelte': 'svelte',
            'gatsby': 'gatsby',
            'vite': 'vite',
        }
        
        # Critical packages for React development
        self.critical_react_packages = {
            'react',
            'react-dom',
            '@types/react',
            '@types/react-dom',
            'typescript'
        }
    
    @handle_errors(reraise=True)
    def analyze_project_dependencies(self) -> ProjectDependencyAnalysis:
        """
        Perform comprehensive analysis of project dependencies.
        
        Returns:
            Complete dependency analysis with insights and recommendations
        """
        
        analysis = ProjectDependencyAnalysis(
            package_manager=self._detect_package_manager(),
            total_packages=0,
            production_packages=0,
            dev_packages=0
        )
        
        try:
            # Load and analyze package.json
            package_json_data = self._load_package_json()
            if not package_json_data:
                analysis.analysis_errors.append("No package.json found or invalid JSON")
                return analysis
            
            # Extract basic dependency info
            self._analyze_basic_dependencies(package_json_data, analysis)
            
            # Detect frameworks and UI libraries
            self._detect_frameworks_and_libraries(package_json_data, analysis)
            
            # Analyze installed packages
            self._analyze_installed_packages(analysis)
            
            # Check for missing packages
            self._check_missing_packages(package_json_data, analysis)
            
            # Security and outdated package analysis
            self._analyze_security_and_outdated(analysis)
            
            # TypeScript support analysis
            self._analyze_typescript_support(package_json_data, analysis)
            
        except Exception as e:
            analysis.analysis_errors.append(f"Analysis failed: {str(e)}")
        
        return analysis
    
    def _detect_package_manager(self) -> PackageManager:
        """Detect which package manager is being used."""
        
        # Check for lock files to determine package manager
        if (self.project_path / "bun.lockb").exists():
            return PackageManager.BUN
        elif (self.project_path / "pnpm-lock.yaml").exists():
            return PackageManager.PNPM
        elif (self.project_path / "yarn.lock").exists():
            return PackageManager.YARN
        elif (self.project_path / "package-lock.json").exists():
            return PackageManager.NPM
        else:
            # Fall back to checking which command is available
            for pm in [PackageManager.BUN, PackageManager.PNPM, PackageManager.YARN, PackageManager.NPM]:
                try:
                    result = subprocess.run([pm.value, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return pm
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            return PackageManager.UNKNOWN
    
    def _load_package_json(self) -> Optional[Dict]:
        """Load and parse package.json."""
        
        package_json_path = self.project_path / "package.json"
        
        if not package_json_path.exists():
            return None
        
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def _analyze_basic_dependencies(self, package_data: Dict, analysis: ProjectDependencyAnalysis):
        """Analyze basic dependency information from package.json."""
        
        # Count different types of dependencies
        deps = package_data.get('dependencies', {})
        dev_deps = package_data.get('devDependencies', {})
        peer_deps = package_data.get('peerDependencies', {})
        optional_deps = package_data.get('optionalDependencies', {})
        
        analysis.production_packages = len(deps)
        analysis.dev_packages = len(dev_deps)
        analysis.total_packages = len(deps) + len(dev_deps) + len(peer_deps) + len(optional_deps)
        
        # Create PackageInfo objects for all dependencies
        for dep_type, deps_dict in [
            (DependencyType.PRODUCTION, deps),
            (DependencyType.DEVELOPMENT, dev_deps),
            (DependencyType.PEER, peer_deps),
            (DependencyType.OPTIONAL, optional_deps),
        ]:
            for name, version in deps_dict.items():
                analysis.package_details[name] = PackageInfo(
                    name=name,
                    version=version,
                    dependency_type=dep_type
                )
    
    def _detect_frameworks_and_libraries(self, package_data: Dict, analysis: ProjectDependencyAnalysis):
        """Detect frameworks and UI libraries from dependencies."""
        
        all_deps = {}
        all_deps.update(package_data.get('dependencies', {}))
        all_deps.update(package_data.get('devDependencies', {}))
        
        # Detect UI libraries
        for package_name, ui_lib in self.ui_library_packages.items():
            if package_name in all_deps:
                analysis.ui_libraries_detected.append(ui_lib)
        
        # Detect styling systems
        for package_name, styling_system in self.styling_packages.items():
            if package_name in all_deps:
                analysis.styling_systems_detected.append(styling_system)
        
        # Detect framework (prioritize more specific frameworks)
        framework_priority = ['next', '@angular/core', 'gatsby', 'svelte', 'vue', 'react']
        for package_name in framework_priority:
            if package_name in all_deps and package_name in self.framework_packages:
                analysis.framework_detected = self.framework_packages[package_name]
                break
    
    def _analyze_installed_packages(self, analysis: ProjectDependencyAnalysis):
        """Analyze which packages are actually installed in node_modules."""
        
        node_modules_path = self.project_path / "node_modules"
        
        if not node_modules_path.exists():
            analysis.analysis_errors.append("node_modules directory not found - packages may not be installed")
            return
        
        for package_name, package_info in analysis.package_details.items():
            package_path = node_modules_path / package_name
            
            if package_path.exists():
                package_info.is_installed = True
                package_info.install_path = str(package_path)
                
                # Try to read package.json for additional info
                try:
                    package_json_path = package_path / "package.json"
                    if package_json_path.exists():
                        with open(package_json_path, 'r', encoding='utf-8') as f:
                            pkg_data = json.load(f)
                        
                        package_info.main_entry = pkg_data.get('main')
                        package_info.types_entry = pkg_data.get('types') or pkg_data.get('typings')
                        
                        # Extract exports if available
                        exports = pkg_data.get('exports', {})
                        if isinstance(exports, dict):
                            package_info.exports = list(exports.keys())
                
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
    
    def _check_missing_packages(self, package_data: Dict, analysis: ProjectDependencyAnalysis):
        """Check for packages that are declared but not installed."""
        
        all_declared = set()
        all_declared.update(package_data.get('dependencies', {}).keys())
        all_declared.update(package_data.get('devDependencies', {}).keys())
        
        for package_name in all_declared:
            if package_name in analysis.package_details:
                if not analysis.package_details[package_name].is_installed:
                    analysis.missing_packages.append(package_name)
    
    def _analyze_security_and_outdated(self, analysis: ProjectDependencyAnalysis):
        """Analyze security vulnerabilities and outdated packages."""
        
        try:
            # Run npm audit if npm is available (works with most package managers)
            if analysis.package_manager in [PackageManager.NPM, PackageManager.YARN]:
                audit_cmd = [analysis.package_manager.value, "audit", "--json"]
                result = subprocess.run(audit_cmd, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=30,
                                      cwd=self.project_path)
                
                if result.returncode == 0 or result.stdout:  # npm audit returns non-zero even with vulnerabilities
                    try:
                        audit_data = json.loads(result.stdout)
                        if 'vulnerabilities' in audit_data:
                            for vuln_name, vuln_info in audit_data['vulnerabilities'].items():
                                severity = vuln_info.get('severity', 'unknown')
                                analysis.security_vulnerabilities.append(f"{vuln_name} ({severity})")
                    except json.JSONDecodeError:
                        pass
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Security analysis is optional, don't fail the entire analysis
            pass
        
        # Check for outdated packages (simplified version)
        try:
            if analysis.package_manager == PackageManager.NPM:
                outdated_cmd = ["npm", "outdated", "--json"]
                result = subprocess.run(outdated_cmd, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=30,
                                      cwd=self.project_path)
                
                if result.stdout:
                    try:
                        outdated_data = json.loads(result.stdout)
                        for package_name, package_info in outdated_data.items():
                            current = package_info.get('current', 'unknown')
                            latest = package_info.get('latest', 'unknown')
                            analysis.outdated_packages[package_name] = (current, latest)
                    except json.JSONDecodeError:
                        pass
        
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Outdated check is optional
            pass
    
    def _analyze_typescript_support(self, package_data: Dict, analysis: ProjectDependencyAnalysis):
        """Analyze TypeScript support in the project."""
        
        all_deps = {}
        all_deps.update(package_data.get('dependencies', {}))
        all_deps.update(package_data.get('devDependencies', {}))
        
        # Check for TypeScript-related packages
        ts_packages = ['typescript', '@types/react', '@types/node', '@types/react-dom']
        has_typescript = any(pkg in all_deps for pkg in ts_packages)
        
        # Check for TypeScript config files
        ts_config_files = ['tsconfig.json', 'jsconfig.json']
        has_ts_config = any((self.project_path / config).exists() for config in ts_config_files)
        
        analysis.typescript_support = has_typescript or has_ts_config
    
    @handle_errors(reraise=True)
    def validate_package_for_import(self, package_name: str) -> Tuple[bool, str, List[str]]:
        """
        Validate if a package is available and provide import suggestions.
        
        Args:
            package_name: Name of the package to validate
            
        Returns:
            Tuple of (is_available, version, suggested_imports)
        """
        
        analysis = self.analyze_project_dependencies()
        
        if package_name in analysis.package_details:
            package_info = analysis.package_details[package_name]
            
            if package_info.is_installed:
                # Package is installed, provide suggestions based on known patterns
                suggested_imports = self._get_common_imports_for_package(package_name)
                return True, package_info.version, suggested_imports
            else:
                # Package is declared but not installed
                return False, package_info.version, []
        else:
            # Package not found in dependencies
            return False, "not found", []
    
    def _get_common_imports_for_package(self, package_name: str) -> List[str]:
        """Get common import patterns for a given package."""
        
        common_imports = {
            'react': ['React', 'useState', 'useEffect', 'useContext'],
            '@chakra-ui/react': ['Box', 'Button', 'Text', 'VStack', 'HStack'],
            '@mui/material': ['Button', 'TextField', 'Typography', 'Paper', 'Grid'],
            'antd': ['Button', 'Input', 'Card', 'Row', 'Col'],
            '@mantine/core': ['Button', 'TextInput', 'Paper', 'Group', 'Stack'],
            'clsx': ['clsx'],
            'classnames': ['classnames'],
            'tailwind-merge': ['twMerge'],
        }
        
        return common_imports.get(package_name, [])
    
    def get_installation_command(self, packages: List[str], package_manager: Optional[PackageManager] = None) -> str:
        """
        Generate installation command for missing packages.
        
        Args:
            packages: List of package names to install
            package_manager: Package manager to use (auto-detected if not provided)
            
        Returns:
            Installation command string
        """
        
        if not packages:
            return ""
        
        pm = package_manager or self._detect_package_manager()
        packages_str = " ".join(packages)
        
        commands = {
            PackageManager.NPM: f"npm install {packages_str}",
            PackageManager.YARN: f"yarn add {packages_str}",
            PackageManager.PNPM: f"pnpm add {packages_str}",
            PackageManager.BUN: f"bun add {packages_str}",
        }
        
        return commands.get(pm, f"npm install {packages_str}")
    
    @handle_errors(reraise=True)
    def suggest_missing_dependencies(self, ui_library: str) -> List[str]:
        """
        Suggest missing dependencies for a given UI library.
        
        Args:
            ui_library: UI library name (e.g., 'chakra-ui', 'material-ui')
            
        Returns:
            List of missing package names that should be installed
        """
        
        analysis = self.analyze_project_dependencies()
        
        # Map UI library to required packages
        required_packages = {
            'chakra-ui': ['@chakra-ui/react', '@emotion/react', '@emotion/styled', 'framer-motion'],
            'material-ui': ['@mui/material', '@emotion/react', '@emotion/styled', '@mui/icons-material'],
            'ant-design': ['antd', '@ant-design/icons'],
            'mantine': ['@mantine/core', '@mantine/hooks'],
            'react-bootstrap': ['react-bootstrap', 'bootstrap'],
            'semantic-ui': ['semantic-ui-react', 'semantic-ui-css'],
            'grommet': ['grommet', 'grommet-icons'],
            'headless-ui': ['@headlessui/react'],
            'shadcn/ui': ['@radix-ui/react-slot', 'class-variance-authority', 'clsx', 'tailwind-merge'],
        }
        
        if ui_library not in required_packages:
            return []
        
        missing = []
        for package in required_packages[ui_library]:
            if package not in analysis.package_details or not analysis.package_details[package].is_installed:
                missing.append(package)
        
        return missing
    
    def get_analysis_summary(self, analysis: ProjectDependencyAnalysis) -> str:
        """Generate a human-readable summary of the dependency analysis."""
        
        summary_lines = [
            f"Package Manager: {analysis.package_manager.value}",
            f"Total Packages: {analysis.total_packages}",
            f"Production: {analysis.production_packages}, Development: {analysis.dev_packages}",
        ]
        
        if analysis.framework_detected:
            summary_lines.append(f"Framework: {analysis.framework_detected}")
        
        if analysis.ui_libraries_detected:
            ui_libs = ", ".join(analysis.ui_libraries_detected)
            summary_lines.append(f"UI Libraries: {ui_libs}")
        
        if analysis.styling_systems_detected:
            styling = ", ".join(analysis.styling_systems_detected)
            summary_lines.append(f"Styling Systems: {styling}")
        
        if analysis.typescript_support:
            summary_lines.append("TypeScript: Supported")
        
        if analysis.missing_packages:
            summary_lines.append(f"Missing Packages: {len(analysis.missing_packages)}")
        
        if analysis.security_vulnerabilities:
            summary_lines.append(f"Security Issues: {len(analysis.security_vulnerabilities)}")
        
        if analysis.outdated_packages:
            summary_lines.append(f"Outdated Packages: {len(analysis.outdated_packages)}")
        
        return "\n".join(summary_lines)