"""
Modular analyzer implementation using separate focused components.
Implements the IAnalyzer interface with better separation of concerns.
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..interfaces import (
    IAnalyzer, ICache, AnalysisResult, ComponentInfo,
    DesignTokens, ProjectStructure
)
from .framework_detector import FrameworkDetector
from .design_token_extractor import DesignTokenExtractor
from .component_scanner import ComponentScanner
from .strategies import AnalysisStrategy, HybridStrategy
from ..cache.decorators import cache_result
from ..errors import AnalysisError
from ..errors.decorators import handle_errors, retry_on_error


class ModularAnalyzer(IAnalyzer):
    """
    Modular implementation of project analyzer.
    Delegates specific responsibilities to focused components.
    """
    
    def __init__(self, strategy: Optional[AnalysisStrategy] = None, cache: Optional[ICache] = None):
        # Initialize sub-components
        self.framework_detector = FrameworkDetector()
        self.token_extractor = DesignTokenExtractor()
        self.component_scanner = ComponentScanner()
        
        # Analysis strategy (default to hybrid)
        self.strategy = strategy or HybridStrategy()
        
        # Cache for expensive operations
        self.cache = cache
        
        # Optional AST analyzer (for backward compatibility)
        self.ast_analyzer = None
        self._init_ast_analyzer()
    
    def _init_ast_analyzer(self):
        """Initialize AST analyzer if available."""
        try:
            from .treesitter_analyzer import TreeSitterAnalyzer
            self.ast_analyzer = TreeSitterAnalyzer()
            print("Info: AST analysis initialized using tree-sitter backend")
        except ImportError:
            print("Warning: TreeSitter analyzer not available")
    
    @handle_errors(reraise=True)
    def analyze(self, project_path: str) -> AnalysisResult:
        """
        Analyze a project and extract all relevant information.
        Uses caching for expensive operations when available.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            AnalysisResult containing all extracted information
            
        Raises:
            AnalysisError: If project path doesn't exist or analysis fails
        """
        # Validate project path
        if not os.path.exists(project_path):
            raise AnalysisError(
                f"Project path does not exist: {project_path}",
                file_path=project_path
            )
        
        if not os.path.isdir(project_path):
            raise AnalysisError(
                f"Project path is not a directory: {project_path}",
                file_path=project_path
            )
        
        # Try cache first if available
        if self.cache:
            cache_key = f"analysis:{project_path}"
            cached_result = self.cache.get(cache_key)
            if cached_result and isinstance(cached_result, AnalysisResult):
                return cached_result
        
        try:
            # Perform analysis
            result = self._perform_analysis(project_path)
            
            # Cache result if available
            if self.cache and result:
                self.cache.set(cache_key, result, ttl=3600)  # 1 hour TTL
            
            return result
        except Exception as e:
            if isinstance(e, AnalysisError):
                raise
            else:
                raise AnalysisError(
                    f"Failed to analyze project: {str(e)}",
                    file_path=project_path,
                    cause=e
                )
    
    def _perform_analysis(self, project_path: str) -> AnalysisResult:
        """
        Analyze a project and extract all relevant information.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            AnalysisResult containing all extracted information
        """
        # Detect project structure
        project_structure = self.detect_project_structure(project_path)
        
        # Extract design tokens
        design_tokens = self.extract_design_tokens(project_path)
        
        # Scan components using strategy
        strategy_components = self.strategy.analyze_components(Path(project_path))
        
        # Also use component scanner for comprehensive discovery
        scanner_components = self.component_scanner.scan(project_path)
        
        # Merge components from both sources
        components = self._merge_components(strategy_components, scanner_components)
        
        # Get available imports
        available_imports = self._get_available_imports(project_path, project_structure, components)
        
        # Analyze component patterns
        component_patterns = self._analyze_component_patterns(components)
        
        # Run AST analysis if available (with caching)
        ast_analysis = None
        if self.ast_analyzer:
            ast_analysis = self._run_ast_analysis_cached(project_path, components)
        
        # Build result
        return AnalysisResult(
            project_structure=project_structure,
            design_tokens=design_tokens,
            components=components,
            available_imports=available_imports,
            ast_analysis=ast_analysis,
            component_patterns=component_patterns,
            main_css_file=self.token_extractor.main_css_file_path
        )
    
    def analyze_component(self, file_path: str) -> Optional[ComponentInfo]:
        """
        Analyze a single component file.
        
        Args:
            file_path: Path to the component file
            
        Returns:
            ComponentInfo if the file is a valid component, None otherwise
        """
        if not os.path.exists(file_path):
            return None
        
        # Extract component name from file
        file_name = os.path.basename(file_path)
        component_name = (
            file_name.replace(".tsx", "")
            .replace(".ts", "")
            .replace(".jsx", "")
            .replace(".js", "")
        )
        
        # Use component scanner methods
        purpose = self.component_scanner._analyze_component_purpose(file_path, component_name)
        component_type = self.component_scanner._infer_component_type(component_name)
        props = self.component_scanner._extract_component_props(file_path)
        description = self.component_scanner._extract_component_description(file_path)
        
        # Build import path (simplified)
        import_path = f"@/components/{component_name}"
        
        return ComponentInfo(
            name=component_name,
            file_path=file_path,
            import_path=import_path,
            purpose=purpose,
            type=component_type,
            props=props,
            description=description
        )
    
    def extract_design_tokens(self, project_path: str) -> DesignTokens:
        """
        Extract design tokens from the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            DesignTokens containing colors, spacing, typography, etc.
        """
        return self.token_extractor.extract(project_path)
    
    def detect_project_structure(self, project_path: str) -> ProjectStructure:
        """
        Detect the project structure and framework.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectStructure with framework and configuration details
        """
        return self.framework_detector.detect(project_path)
    
    def _get_available_imports(
        self, 
        project_path: str, 
        project_structure: ProjectStructure,
        components: List[ComponentInfo]
    ) -> Dict[str, Any]:
        """Get available imports and dependencies for component generation."""
        package_json_path = os.path.join(project_path, "package.json")
        dependencies = {}
        
        if os.path.exists(package_json_path):
            try:
                import json
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
            except json.JSONDecodeError:
                pass
        
        # Organize components by type
        shadcn_components = [c for c in components if c.is_shadcn]
        custom_components = [c for c in components if not c.is_shadcn]
        
        available_imports = {
            "react_hooks": self._get_available_react_hooks(dependencies),
            "ui_components": {
                "shadcn_ui": shadcn_components,
                "custom": custom_components,
                "third_party": self._get_third_party_libraries(dependencies)
            },
            "utilities": self._get_available_utilities(project_path, dependencies),
            "icons": self._get_available_icons(dependencies),
            "styling": self._get_available_styling_utilities(dependencies),
        }
        
        return available_imports
    
    def _get_available_react_hooks(self, dependencies: dict) -> List[str]:
        """Get available React hooks based on React version."""
        basic_hooks = [
            "useState",
            "useEffect",
            "useContext",
            "useReducer",
            "useCallback",
            "useMemo",
            "useRef",
        ]
        
        if "react" in dependencies:
            # All modern React versions support these hooks
            return basic_hooks
        
        return []
    
    def _get_third_party_libraries(self, dependencies: dict) -> List[str]:
        """Get available third-party component libraries."""
        libraries = []
        
        if "@mui/material" in dependencies:
            libraries.append("mui")
        if "antd" in dependencies:
            libraries.append("antd")
        if "@chakra-ui/react" in dependencies:
            libraries.append("chakra-ui")
        
        return libraries
    
    def _get_available_utilities(self, project_path: str, dependencies: dict) -> Dict:
        """Get available utility functions and their import paths."""
        utilities = {
            "cn": False,
            "clsx": False,
            "classnames": False,
            "custom_utils": [],
        }
        
        # Check for cn utility (shadcn/ui)
        lib_utils_paths = [
            os.path.join(project_path, "lib", "utils.ts"),
            os.path.join(project_path, "src", "lib", "utils.ts"),
            os.path.join(project_path, "lib", "utils.js"),
            os.path.join(project_path, "src", "lib", "utils.js"),
        ]
        
        for path in lib_utils_paths:
            if os.path.exists(path):
                utilities["cn"] = True
                break
        
        # Check for class utilities in dependencies
        if "clsx" in dependencies:
            utilities["clsx"] = True
        if "classnames" in dependencies:
            utilities["classnames"] = True
        
        return utilities
    
    def _get_available_icons(self, dependencies: dict) -> List[str]:
        """Get available icon libraries."""
        icon_libraries = []
        
        icon_packages = {
            "lucide-react": "lucide",
            "react-icons": "react-icons",
            "@heroicons/react": "heroicons",
            "@tabler/icons-react": "tabler",
            "react-feather": "feather",
        }
        
        for package, name in icon_packages.items():
            if package in dependencies:
                icon_libraries.append(name)
        
        return icon_libraries
    
    def _get_available_styling_utilities(self, dependencies: dict) -> List[str]:
        """Get available styling utilities."""
        styling = []
        
        if "tailwind-merge" in dependencies:
            styling.append("tailwind-merge")
        if "class-variance-authority" in dependencies:
            styling.append("class-variance-authority")
        
        return styling
    
    def _analyze_component_patterns(self, components: List[ComponentInfo]) -> Dict:
        """Analyze patterns from discovered components."""
        patterns = {
            "button_variants": [],
            "layout_patterns": [],
            "animation_styles": [],
        }
        
        # Extract button variants
        button_components = [c for c in components if c.type == "button"]
        for button in button_components:
            # Look for variant props
            for prop in button.props:
                if prop.get("name") == "variant":
                    # Extract variant values if possible
                    prop_type = prop.get("type", "")
                    if "|" in prop_type:
                        variants = [v.strip().strip("'\"") for v in prop_type.split("|")]
                        patterns["button_variants"].extend(variants)
        
        # Deduplicate
        patterns["button_variants"] = list(set(patterns["button_variants"]))
        
        # Default patterns if none found
        if not patterns["button_variants"]:
            patterns["button_variants"] = ["primary", "secondary", "outline", "ghost"]
        
        patterns["layout_patterns"] = ["grid", "flex", "container"]
        patterns["animation_styles"] = ["fade", "slide", "scale"]
        
        return patterns
    
    def _convert_ast_components(self, ast_components: List[Dict]) -> List[ComponentInfo]:
        """Convert AST component data to ComponentInfo objects."""
        components = []
        
        for ast_comp in ast_components:
            # Convert props format
            props = []
            for prop_data in ast_comp.get("props", []):
                if isinstance(prop_data, dict):
                    props.append({
                        "name": prop_data.get("name", ""),
                        "type": prop_data.get("type_annotation", "unknown"),
                        "required": not prop_data.get("is_optional", False)
                    })
            
            # Create ComponentInfo
            comp_info = ComponentInfo(
                name=ast_comp["name"],
                file_path=ast_comp["file_path"],
                import_path=f"@/components/{ast_comp['name']}",  # Simplified
                purpose=ast_comp.get("purpose", f"{ast_comp['name']} component"),
                type=self.component_scanner._infer_component_type(ast_comp["name"]),
                props=props,
                description=ast_comp.get("description"),
                examples=ast_comp.get("examples", [])
            )
            
            components.append(comp_info)
        
        return components
    
    def _merge_components(
        self, 
        strategy_components: List[ComponentInfo], 
        scanner_components: List[ComponentInfo]
    ) -> List[ComponentInfo]:
        """Merge components from different sources, avoiding duplicates."""
        # Use a dict to track components by name
        component_map = {}
        
        # Add strategy components first (higher confidence)
        for comp in strategy_components:
            component_map[comp.name] = comp
        
        # Add scanner components if not already present
        for comp in scanner_components:
            if comp.name not in component_map:
                component_map[comp.name] = comp
            else:
                # Merge additional information if available
                existing = component_map[comp.name]
                if not existing.description and comp.description:
                    existing.description = comp.description
                if not existing.props and comp.props:
                    existing.props = comp.props
        
        return list(component_map.values())
    
    def _run_ast_analysis_cached(self, project_path: str, components: List[ComponentInfo]) -> Optional[Dict[str, Any]]:
        """Run AST analysis with caching."""
        # Check cache if available
        if self.cache:
            cache_key = f"ast_analysis:{project_path}"
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Run analysis
        try:
            print("Info: Running AST analysis...")
            ast_analysis = self.ast_analyzer.analyze_project(project_path)
            
            # Merge AST-discovered components with scanner results
            if "components" in ast_analysis:
                ast_components = self._convert_ast_components(ast_analysis["components"])
                # Merge without duplicates
                existing_names = {c.name for c in components}
                for ast_comp in ast_components:
                    if ast_comp.name not in existing_names:
                        components.append(ast_comp)
                
                print(f"Info: Found {len(ast_analysis['components'])} components via AST")
            
            # Cache result
            if self.cache:
                self.cache.set(cache_key, ast_analysis, ttl=1800)  # 30 min TTL
            
            return ast_analysis
            
        except Exception as e:
            print(f"Warning: AST analysis failed: {e}")
            return {"error": str(e)}