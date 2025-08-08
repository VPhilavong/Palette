"""
Enhanced Project Analyzer with Semantic Understanding
Provides deep analysis of React/TypeScript projects with shadcn/ui integration
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ComponentType(Enum):
    UI_LIBRARY = "ui_library"  # shadcn/ui components
    PAGE = "page"
    FEATURE = "feature"
    LAYOUT = "layout"
    HOOK = "hook"
    UTILITY = "utility"
    UNKNOWN = "unknown"


@dataclass
class ComponentInfo:
    name: str
    file_path: str
    component_type: ComponentType
    exports: List[str]
    imports: List[str]
    props: List[str]
    dependencies: List[str]
    is_typescript: bool
    has_tailwind: bool
    line_count: int
    complexity_score: int


@dataclass
class ProjectStructure:
    framework: str
    build_tool: str
    package_manager: str
    has_typescript: bool
    has_tailwind: bool
    has_shadcn_ui: bool
    components: List[ComponentInfo]
    pages: List[str]
    routes: List[str]
    design_tokens: Dict[str, Any]
    dependencies: Dict[str, str]
    dev_dependencies: Dict[str, str]


class EnhancedProjectAnalyzer:
    """Enhanced project analyzer with semantic understanding"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.src_path = self.project_path / "src"
        self.components_path = self.src_path / "components"
        self.ui_components_path = self.components_path / "ui"
        
    def analyze_project(self) -> ProjectStructure:
        """Perform comprehensive project analysis"""
        print("🔍 Starting enhanced project analysis...")
        
        # Basic project detection
        framework = self._detect_framework()
        build_tool = self._detect_build_tool()
        package_manager = self._detect_package_manager()
        
        # Language and styling detection
        has_typescript = self._detect_typescript()
        has_tailwind = self._detect_tailwind()
        has_shadcn_ui = self._detect_shadcn_ui()
        
        # Component analysis
        components = self._analyze_components()
        
        # Page and routing analysis
        pages = self._analyze_pages()
        routes = self._analyze_routes()
        
        # Design tokens extraction
        design_tokens = self._extract_design_tokens()
        
        # Dependencies
        dependencies, dev_dependencies = self._analyze_dependencies()
        
        return ProjectStructure(
            framework=framework,
            build_tool=build_tool,
            package_manager=package_manager,
            has_typescript=has_typescript,
            has_tailwind=has_tailwind,
            has_shadcn_ui=has_shadcn_ui,
            components=components,
            pages=pages,
            routes=routes,
            design_tokens=design_tokens,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies
        )
    
    def _detect_framework(self) -> str:
        """Detect the frontend framework"""
        package_json = self._read_package_json()
        if not package_json:
            return "unknown"
        
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        
        if "next" in deps:
            return "nextjs"
        elif "vite" in deps and "react" in deps:
            return "vite-react"
        elif "react" in deps:
            return "react"
        elif "vue" in deps:
            return "vue"
        elif "svelte" in deps:
            return "svelte"
        
        return "unknown"
    
    def _detect_build_tool(self) -> str:
        """Detect the build tool"""
        if (self.project_path / "vite.config.ts").exists() or (self.project_path / "vite.config.js").exists():
            return "vite"
        elif (self.project_path / "next.config.js").exists() or (self.project_path / "next.config.ts").exists():
            return "nextjs"
        elif (self.project_path / "webpack.config.js").exists():
            return "webpack"
        elif (self.project_path / "rollup.config.js").exists():
            return "rollup"
        
        return "unknown"
    
    def _detect_package_manager(self) -> str:
        """Detect package manager"""
        if (self.project_path / "pnpm-lock.yaml").exists():
            return "pnpm"
        elif (self.project_path / "yarn.lock").exists():
            return "yarn"
        elif (self.project_path / "package-lock.json").exists():
            return "npm"
        
        return "npm"
    
    def _detect_typescript(self) -> bool:
        """Check if project uses TypeScript"""
        return (
            (self.project_path / "tsconfig.json").exists() or
            any(self.project_path.rglob("*.ts")) or
            any(self.project_path.rglob("*.tsx"))
        )
    
    def _detect_tailwind(self) -> bool:
        """Check if project uses Tailwind CSS"""
        package_json = self._read_package_json()
        if package_json:
            deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
            if "tailwindcss" in deps:
                return True
        
        return (
            (self.project_path / "tailwind.config.js").exists() or
            (self.project_path / "tailwind.config.ts").exists()
        )
    
    def _detect_shadcn_ui(self) -> bool:
        """Check if project uses shadcn/ui"""
        # Check for components.json (shadcn/ui config file)
        if (self.project_path / "components.json").exists():
            return True
        
        # Check for typical shadcn/ui component structure
        if self.ui_components_path.exists():
            ui_files = list(self.ui_components_path.glob("*.tsx"))
            if len(ui_files) > 0:
                # Check if files have shadcn/ui patterns
                for file_path in ui_files[:3]:  # Check first few files
                    content = self._read_file(file_path)
                    if content and self._is_shadcn_component(content):
                        return True
        
        return False
    
    def _is_shadcn_component(self, content: str) -> bool:
        """Check if component content matches shadcn/ui patterns"""
        shadcn_patterns = [
            r'import.*class-variance-authority',
            r'import.*clsx',
            r'import.*tailwind-merge',
            r'cn\s*\(',
            r'cva\s*\(',
            r'VariantProps',
            r'@radix-ui'
        ]
        
        return any(re.search(pattern, content) for pattern in shadcn_patterns)
    
    def _analyze_components(self) -> List[ComponentInfo]:
        """Analyze all components in the project"""
        components = []
        
        if not self.src_path.exists():
            return components
        
        # Find all React component files
        for file_path in self.src_path.rglob("*.tsx"):
            if self._should_analyze_file(file_path):
                component_info = self._analyze_component_file(file_path)
                if component_info:
                    components.append(component_info)
        
        for file_path in self.src_path.rglob("*.jsx"):
            if self._should_analyze_file(file_path):
                component_info = self._analyze_component_file(file_path)
                if component_info:
                    components.append(component_info)
        
        return components
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed"""
        # Skip node_modules, dist, build directories
        exclude_patterns = ["node_modules", "dist", "build", ".next", ".git"]
        path_str = str(file_path)
        
        return not any(pattern in path_str for pattern in exclude_patterns)
    
    def _analyze_component_file(self, file_path: Path) -> Optional[ComponentInfo]:
        """Analyze a single component file"""
        try:
            content = self._read_file(file_path)
            if not content:
                return None
            
            # Extract component information
            name = self._extract_component_name(content, file_path.stem)
            component_type = self._classify_component(file_path, content)
            exports = self._extract_exports(content)
            imports = self._extract_imports(content)
            props = self._extract_props(content)
            dependencies = self._extract_dependencies(imports)
            is_typescript = file_path.suffix == ".tsx"
            has_tailwind = self._has_tailwind_classes(content)
            line_count = len(content.splitlines())
            complexity_score = self._calculate_complexity(content)
            
            return ComponentInfo(
                name=name,
                file_path=str(file_path.relative_to(self.project_path)),
                component_type=component_type,
                exports=exports,
                imports=imports,
                props=props,
                dependencies=dependencies,
                is_typescript=is_typescript,
                has_tailwind=has_tailwind,
                line_count=line_count,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _extract_component_name(self, content: str, fallback_name: str) -> str:
        """Extract the main component name from file content"""
        # Try various patterns to find component name
        patterns = [
            r'export\s+default\s+function\s+(\w+)',
            r'export\s+default\s+(\w+)',
            r'const\s+(\w+):\s*React\.FC',
            r'const\s+(\w+)\s*=\s*forwardRef',
            r'function\s+(\w+)\s*\(',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return fallback_name.title()
    
    def _classify_component(self, file_path: Path, content: str) -> ComponentType:
        """Classify the type of component"""
        path_str = str(file_path).lower()
        
        # Check if it's in ui directory (shadcn/ui components)
        if "/ui/" in path_str:
            return ComponentType.UI_LIBRARY
        
        # Check if it's a page
        if "/pages/" in path_str or "/app/" in path_str:
            return ComponentType.PAGE
        
        # Check if it's a layout
        if "layout" in path_str:
            return ComponentType.LAYOUT
        
        # Check if it's a hook
        if path_str.startswith("use") or "/hooks/" in path_str:
            return ComponentType.HOOK
        
        # Check if it's a utility
        if "/utils/" in path_str or "/lib/" in path_str:
            return ComponentType.UTILITY
        
        # Analyze content for feature indicators
        if any(keyword in content.lower() for keyword in ["form", "modal", "dialog", "dashboard"]):
            return ComponentType.FEATURE
        
        return ComponentType.UNKNOWN
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extract all exports from the file"""
        exports = []
        
        # Default export
        default_match = re.search(r'export\s+default\s+(\w+)', content)
        if default_match:
            exports.append(default_match.group(1))
        
        # Named exports
        named_exports = re.findall(r'export\s+(?:const|function|class)\s+(\w+)', content)
        exports.extend(named_exports)
        
        # Export statements
        export_statements = re.findall(r'export\s*\{\s*([^}]+)\s*\}', content)
        for statement in export_statements:
            names = [name.strip().split(' as ')[0] for name in statement.split(',')]
            exports.extend(names)
        
        return list(set(exports))  # Remove duplicates
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract all imports from the file"""
        imports = []
        
        import_lines = re.findall(r'import.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        imports.extend(import_lines)
        
        # Extract import names for analysis
        import_names = re.findall(r'import\s+(?:\{([^}]+)\}|\*\s+as\s+(\w+)|(\w+))', content)
        for match in import_names:
            names = match[0] or match[1] or match[2]
            if names:
                if match[0]:  # Named imports
                    named = [name.strip().split(' as ')[0] for name in names.split(',')]
                    imports.extend(named)
                else:
                    imports.append(names)
        
        return imports
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract component props"""
        props = []
        
        # TypeScript interface props
        interface_matches = re.findall(r'interface\s+\w+Props\s*\{([^}]+)\}', content, re.DOTALL)
        for match in interface_matches:
            prop_lines = [line.strip() for line in match.split('\n') if line.strip()]
            for line in prop_lines:
                prop_match = re.match(r'(\w+)[\?\:]', line)
                if prop_match:
                    props.append(prop_match.group(1))
        
        # Function parameter destructuring
        param_matches = re.findall(r'function\s+\w+\s*\(\s*\{([^}]+)\}', content)
        for match in param_matches:
            param_names = [name.strip().split(':')[0] for name in match.split(',')]
            props.extend(param_names)
        
        return list(set(props))
    
    def _extract_dependencies(self, imports: List[str]) -> List[str]:
        """Extract external dependencies from imports"""
        dependencies = []
        
        for imp in imports:
            # Skip relative imports
            if imp.startswith('.') or imp.startswith('/'):
                continue
            
            # Extract package name (handle scoped packages)
            if imp.startswith('@'):
                package = '/'.join(imp.split('/')[:2])
            else:
                package = imp.split('/')[0]
            
            dependencies.append(package)
        
        return list(set(dependencies))
    
    def _has_tailwind_classes(self, content: str) -> bool:
        """Check if content contains Tailwind CSS classes"""
        # Look for className with typical Tailwind patterns
        tailwind_patterns = [
            r'className=.*?(?:flex|grid|p-|m-|text-|bg-|border-|rounded)',
            r'class=.*?(?:flex|grid|p-|m-|text-|bg-|border-|rounded)',
            r'cn\(',  # Tailwind merge utility
        ]
        
        return any(re.search(pattern, content) for pattern in tailwind_patterns)
    
    def _calculate_complexity(self, content: str) -> int:
        """Calculate a simple complexity score"""
        score = 0
        
        # Count various complexity indicators
        score += len(re.findall(r'\bif\b', content))  # Conditional statements
        score += len(re.findall(r'\bfor\b|\bwhile\b', content))  # Loops
        score += len(re.findall(r'\bswitch\b', content))  # Switch statements
        score += len(re.findall(r'\bcatch\b', content))  # Error handling
        score += len(re.findall(r'\bfunction\b|\b=>\b', content))  # Functions
        score += len(re.findall(r'useState|useEffect|useCallback', content))  # React hooks
        
        return score
    
    def _analyze_pages(self) -> List[str]:
        """Analyze pages in the project"""
        pages = []
        
        # Common page directories
        page_dirs = ["pages", "app", "routes"]
        
        for dir_name in page_dirs:
            page_dir = self.src_path / dir_name
            if page_dir.exists():
                for file_path in page_dir.rglob("*.tsx"):
                    if file_path.name != "layout.tsx":  # Skip layout files
                        pages.append(str(file_path.relative_to(self.project_path)))
                
                for file_path in page_dir.rglob("*.jsx"):
                    if file_path.name != "layout.jsx":
                        pages.append(str(file_path.relative_to(self.project_path)))
        
        return pages
    
    def _analyze_routes(self) -> List[str]:
        """Analyze routing configuration"""
        routes = []
        
        # Look for common routing files
        routing_files = [
            "App.tsx", "App.jsx", "router.tsx", "router.jsx", 
            "routes.tsx", "routes.jsx", "index.tsx", "index.jsx"
        ]
        
        for filename in routing_files:
            file_path = self.src_path / filename
            if file_path.exists():
                content = self._read_file(file_path)
                if content:
                    # Extract route patterns
                    route_patterns = re.findall(r'path=[\'"]([^\'"]+)[\'"]', content)
                    routes.extend(route_patterns)
        
        return list(set(routes))
    
    def _extract_design_tokens(self) -> Dict[str, Any]:
        """Extract design tokens from various configuration files"""
        design_tokens = {}
        
        # Tailwind config
        tailwind_config = self._parse_tailwind_config()
        if tailwind_config:
            design_tokens["tailwind"] = tailwind_config
        
        # shadcn/ui config
        components_config = self._parse_components_config()
        if components_config:
            design_tokens["shadcn"] = components_config
        
        # CSS variables
        css_variables = self._extract_css_variables()
        if css_variables:
            design_tokens["css_variables"] = css_variables
        
        return design_tokens
    
    def _parse_tailwind_config(self) -> Optional[Dict[str, Any]]:
        """Parse Tailwind configuration"""
        config_files = ["tailwind.config.js", "tailwind.config.ts"]
        
        for config_file in config_files:
            config_path = self.project_path / config_file
            if config_path.exists():
                # For now, just note that Tailwind is configured
                # In a full implementation, we'd parse the JS/TS config
                return {"configured": True, "config_file": config_file}
        
        return None
    
    def _parse_components_config(self) -> Optional[Dict[str, Any]]:
        """Parse shadcn/ui components.json config"""
        config_path = self.project_path / "components.json"
        if config_path.exists():
            try:
                content = self._read_file(config_path)
                return json.loads(content) if content else None
            except json.JSONDecodeError:
                return {"error": "Invalid JSON in components.json"}
        
        return None
    
    def _extract_css_variables(self) -> Dict[str, List[str]]:
        """Extract CSS variables from stylesheets"""
        css_vars = {}
        
        css_files = list(self.project_path.rglob("*.css"))
        
        for css_file in css_files:
            content = self._read_file(css_file)
            if content:
                # Find CSS custom properties
                variables = re.findall(r'--[\w-]+:\s*[^;]+', content)
                if variables:
                    css_vars[str(css_file.relative_to(self.project_path))] = variables
        
        return css_vars
    
    def _analyze_dependencies(self) -> tuple[Dict[str, str], Dict[str, str]]:
        """Analyze project dependencies"""
        package_json = self._read_package_json()
        if not package_json:
            return {}, {}
        
        dependencies = package_json.get("dependencies", {})
        dev_dependencies = package_json.get("devDependencies", {})
        
        return dependencies, dev_dependencies
    
    def _read_package_json(self) -> Optional[Dict[str, Any]]:
        """Read and parse package.json"""
        package_path = self.project_path / "package.json"
        if package_path.exists():
            try:
                content = self._read_file(package_path)
                return json.loads(content) if content else None
            except json.JSONDecodeError:
                return None
        
        return None
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Safely read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (OSError, UnicodeDecodeError):
            return None
    
    def get_analysis_summary(self, structure: ProjectStructure) -> Dict[str, Any]:
        """Generate a summary of the analysis"""
        ui_components = [c for c in structure.components if c.component_type == ComponentType.UI_LIBRARY]
        page_components = [c for c in structure.components if c.component_type == ComponentType.PAGE]
        feature_components = [c for c in structure.components if c.component_type == ComponentType.FEATURE]
        
        return {
            "project_type": f"{structure.framework} with {structure.build_tool}",
            "technology_stack": {
                "typescript": structure.has_typescript,
                "tailwind": structure.has_tailwind,
                "shadcn_ui": structure.has_shadcn_ui,
                "package_manager": structure.package_manager
            },
            "components_summary": {
                "total": len(structure.components),
                "ui_library": len(ui_components),
                "pages": len(page_components),
                "features": len(feature_components),
                "average_complexity": sum(c.complexity_score for c in structure.components) / len(structure.components) if structure.components else 0
            },
            "available_components": [c.name for c in ui_components],
            "pages": structure.pages,
            "routes": structure.routes,
            "dependencies_count": len(structure.dependencies),
            "design_system_configured": bool(structure.design_tokens)
        }


# Convenience function for external use
def analyze_project_intelligence(project_path: str) -> Dict[str, Any]:
    """Analyze project with enhanced intelligence and return summary"""
    analyzer = EnhancedProjectAnalyzer(project_path)
    structure = analyzer.analyze_project()
    summary = analyzer.get_analysis_summary(structure)
    
    return {
        "structure": asdict(structure),
        "summary": summary
    }