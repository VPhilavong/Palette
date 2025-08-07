import glob
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Import TreeSitter analyzer
try:
    from .treesitter_analyzer import TreeSitterAnalyzer as ASTAnalyzer
    AST_ANALYZER_TYPE = "tree-sitter"
except ImportError:
    print("Warning: TreeSitter analyzer not available")
    ASTAnalyzer = None
    AST_ANALYZER_TYPE = "none"

# Import ProjectStructureDetector for enhanced project analysis
from .project_structure import ProjectStructureDetector, FrameworkType


class ProjectAnalyzer:
    """Analyzes project structure to extract design patterns and context"""

    def __init__(self, project_path: str = None):
        # Simplified: Only support Vite + React projects
        self.supported_frameworks = {
            "vite": ["vite.config.js", "vite.config.ts", "vite.config.mjs"],
        }

        # We primarily support shadcn/ui
        self.component_libraries = {
            "shadcn/ui": ["components/ui/", "@radix-ui", "class-variance-authority"],
        }

        # Store the main CSS file path for debugging/info purposes
        self.main_css_file_path = None
        
        # Store project path if provided
        self.project_path = project_path
        
        # Initialize AST analyzer
        if ASTAnalyzer:
            try:
                self.ast_analyzer = ASTAnalyzer()
                print(f"Info: AST analysis initialized using {AST_ANALYZER_TYPE} backend")
            except Exception as e:
                print(f"Warning: AST analysis initialization failed: {e}")
                self.ast_analyzer = None
        else:
            self.ast_analyzer = None

    def analyze_project(self, project_path: str) -> Dict:
        """Extract design patterns for UI generation"""

        # Enhanced project structure detection
        enhanced_structure = self._get_enhanced_project_structure(project_path)
        
        context = {
            "framework": enhanced_structure.get("framework", self._detect_framework(project_path)),
            "styling": self._detect_styling_system(project_path),
            "component_library": self._detect_component_library(project_path),
            "design_tokens": self._extract_design_tokens(project_path),
            "component_patterns": self._analyze_component_patterns(project_path),
            "project_structure": enhanced_structure,
            "available_imports": self.get_available_imports(project_path),
            "main_css_file": self.main_css_file_path,
        }

        # Add AST analysis if available
        if self.ast_analyzer:
            try:
                print("Info: Running AST analysis...")
                ast_analysis = self.ast_analyzer.analyze_project(project_path)
                context["ast_analysis"] = ast_analysis
                
                # AST analysis includes component patterns
                if "components" in ast_analysis:
                    print(f"Info: Found {len(ast_analysis['components'])} components")
                    
            except Exception as e:
                print(f"Warning: AST analysis failed: {e}")
                context["ast_analysis"] = {"error": str(e)}

        return context

    def _detect_framework(self, project_path: str) -> str:
        """Detect if this is a Vite + React project"""
        
        # Check for Vite config files
        vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
        has_vite_config = any(
            os.path.exists(os.path.join(project_path, config))
            for config in vite_configs
        )
        
        # Check package.json
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            framework = self._analyze_package_json(package_json_path)
            if framework == "vite":
                return "vite"
        
        # If we have Vite config, assume it's a Vite project
        if has_vite_config:
            return "vite"
        
        return "unknown"

    def _get_enhanced_project_structure(self, project_path: str) -> Dict:
        """Get enhanced project structure analysis using ProjectStructureDetector."""
        try:
            detector = ProjectStructureDetector(project_path)
            project_info = detector.detect_project_structure()
            
            # Convert ProjectInfo to format expected by analyze_project
            enhanced_structure = {
                "framework": self._convert_framework_type_to_string(project_info.framework),
                "structure_type": project_info.structure.value,
                "routes_directory": project_info.routes_dir,
                "components_directory": project_info.components_dir,
                "has_typescript": project_info.has_typescript,
                "has_src_directory": project_info.has_src_dir,
                "project_info": project_info,  # Keep original for detailed access
            }
            
            print(f"✅ Enhanced project structure: {enhanced_structure['framework']} ({enhanced_structure['structure_type']})")
            return enhanced_structure
            
        except Exception as e:
            print(f"⚠️ Enhanced project structure detection failed: {e}")
            
            # Fallback to basic structure info
            return {
                "framework": self._detect_framework(project_path),
                "structure_type": "unknown",
                "routes_directory": "app",
                "components_directory": "components",
                "has_typescript": os.path.exists(os.path.join(project_path, "tsconfig.json")),
                "has_src_directory": os.path.exists(os.path.join(project_path, "src")),
                "project_info": None,
            }
    
    def _convert_framework_type_to_string(self, framework_type: FrameworkType) -> str:
        """Convert FrameworkType enum to string format used by the rest of the system."""
        # Simplified: Only support Vite projects
        if framework_type == FrameworkType.REACT_APP:
            return "vite"
        return "unknown"


    def _analyze_package_json(self, package_json_path: str) -> str:
        """Analyze a package.json file to check for Vite + React"""
        
        try:
            with open(package_json_path, "r") as f:
                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check for Vite and React
                has_vite = "vite" in dependencies
                has_react = "react" in dependencies
                
                if has_vite and has_react:
                    return "vite"
        except json.JSONDecodeError:
            pass
        
        return "unknown"


    def _detect_styling_system(self, project_path: str) -> str:
        """Detect the styling system (Tailwind, CSS modules, etc.)"""

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
        """Detect if shadcn/ui is being used"""

        # Check main package.json only
        package_json_paths = [os.path.join(project_path, "package.json")]

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
            except json.JSONDecodeError:
                pass

        return "none"

    def _is_shadcn_ui_project(self, project_path: str, dependencies: dict) -> bool:
        """Validate if project actually has shadcn/ui setup"""

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

        has_components_ui = os.path.exists(components_ui_path) or os.path.exists(
            src_components_ui_path
        )
        has_lib_utils = os.path.exists(lib_utils_path) or os.path.exists(
            src_lib_utils_path
        )

        # Only return true if both dependencies and structure exist
        return has_shadcn_deps and has_components_ui and has_lib_utils

    def _extract_design_tokens(self, project_path: str) -> Dict:
        """Extract design tokens from Tailwind config and existing components"""

        # First, try to get tokens from tailwind.config.js
        tailwind_config = self._parse_tailwind_config(project_path)

        # Extract colors with semantic structure
        color_data = self._extract_colors_from_config(tailwind_config, project_path)

        tokens = {
            "colors": color_data["custom"],  # For backward compatibility
            "semantic_colors": color_data["semantic"],  # New semantic colors
            "color_structure": color_data["structure"],  # Full color structure
            "spacing": self._extract_spacing_from_config(tailwind_config, project_path),
            "typography": self._extract_typography_from_config(
                tailwind_config, project_path
            ),
            "shadows": self._extract_shadows_from_config(tailwind_config),
            "border_radius": self._extract_border_radius_from_config(tailwind_config),
        }

        return tokens


    def _parse_tailwind_config(self, project_path: str) -> Dict:
        """Parse tailwind.config.js using Node.js helper script or CSS parsing"""

        # Look for Tailwind config files
        config_files = [
            "tailwind.config.js",
            "tailwind.config.ts",
            "tailwind.config.mjs",
        ]
        config_path = None

        for config_file in config_files:
            potential_path = os.path.join(project_path, config_file)
            if os.path.exists(potential_path):
                config_path = potential_path
                break

        if config_path:
            # Show which config file was found
            config_name = os.path.basename(config_path)
            print(f"Info: Found Tailwind config: {config_name}")
            # Use Node.js parser for JS config files
            return self._parse_js_config(config_path, project_path)
        else:
            # Fallback to CSS parsing mode
            print("Info: No tailwind config found, trying CSS parsing mode...")
            return self._parse_css_for_theme(project_path)

    def _parse_js_config(self, config_path: str, project_path: str) -> Dict:
        """Parse JavaScript/TypeScript config file using Node.js helper script"""

        try:
            # Get the path to our Node.js helper script
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            parser_script = os.path.join(script_dir, "utils", "tailwind_parser.js")

            # Convert config_path to absolute path for subprocess
            abs_config_path = os.path.abspath(config_path)
            
            # Run the Node.js script to parse the config
            result = subprocess.run(
                ["node", parser_script, abs_config_path],
                capture_output=True,
                text=True,
                timeout=15,  # Increased timeout for resolveConfig
            )

            if result.returncode == 0:
                try:
                    parsed_config = json.loads(result.stdout)
                    
                    # Check if we got a fully resolved config
                    if parsed_config.get('_resolved', False):
                        print(f"Info: Successfully resolved full Tailwind theme with defaults")
                        # Process resolved theme
                        return self._process_resolved_theme(parsed_config, project_path)
                    else:
                        print(f"Info: Using basic Tailwind config parsing (no resolveConfig)")
                        return parsed_config
                        
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse JSON from tailwind parser: {e}")
                    print(f"Raw stdout: {result.stdout[:500]}")
                    print(f"Raw stderr: {result.stderr[:500]}")
                    return {}
            else:
                print(f"Warning: Tailwind parser failed: {result.stderr}")
                return {}

        except subprocess.TimeoutExpired:
            print("Warning: Tailwind config parsing timed out")
            return {}
        except FileNotFoundError:
            print(
                "Warning: Node.js not found. Install Node.js to enable advanced Tailwind config parsing."
            )
            return {}
        except Exception as e:
            print(f"Warning: Error parsing Tailwind config: {e}")
            return {}

    def _process_resolved_theme(self, resolved_config: Dict, project_path: str) -> Dict:
        """Process a fully resolved Tailwind theme"""
        
        # Extract and clean resolved theme data
        processed_config = {
            'colors': self._process_resolved_colors(resolved_config.get('colors', {})),
            'spacing': self._process_resolved_spacing(resolved_config.get('spacing', {})),
            'fontSize': self._process_resolved_font_sizes(resolved_config.get('fontSize', {})),
            'fontFamily': self._process_resolved_font_families(resolved_config.get('fontFamily', {})),
            'fontWeight': resolved_config.get('fontWeight', {}),
            'borderRadius': resolved_config.get('borderRadius', {}),
            'boxShadow': resolved_config.get('boxShadow', {}),
            'screens': resolved_config.get('screens', {}),
            'lineHeight': resolved_config.get('lineHeight', {}),
            'letterSpacing': resolved_config.get('letterSpacing', {}),
            'opacity': resolved_config.get('opacity', {}),
            'zIndex': resolved_config.get('zIndex', {}),
            'extend': resolved_config.get('extend', {}),
            '_resolved': True
        }
        
        print(f"Info: Processed resolved theme with {len(processed_config['colors'])} colors, "
              f"{len(processed_config['spacing'])} spacing values, "
              f"{len(processed_config['fontSize'])} font sizes")
        
        return processed_config

    def _process_resolved_colors(self, colors: Dict) -> Dict:
        """Process resolved color values, handling nested structures"""
        
        processed_colors = {}
        
        for color_name, color_value in colors.items():
            if isinstance(color_value, dict):
                # Handle color scales like blue: { 50: '#...', 100: '#...' }
                processed_colors[color_name] = color_value
            elif isinstance(color_value, str):
                # Handle single color values
                processed_colors[color_name] = color_value
            else:
                # Handle functions or other complex values
                processed_colors[color_name] = str(color_value)
        
        return processed_colors

    def _process_resolved_spacing(self, spacing: Dict) -> Dict:
        """Process resolved spacing values"""
        
        processed_spacing = {}
        
        for spacing_key, spacing_value in spacing.items():
            if isinstance(spacing_value, str):
                processed_spacing[spacing_key] = spacing_value
            else:
                processed_spacing[spacing_key] = str(spacing_value)
        
        return processed_spacing

    def _process_resolved_font_sizes(self, font_sizes: Dict) -> Dict:
        """Process resolved font size values"""
        
        processed_font_sizes = {}
        
        for size_name, size_value in font_sizes.items():
            if isinstance(size_value, list):
                # Handle [fontSize, lineHeight] format
                processed_font_sizes[size_name] = size_value[0] if size_value else size_name
            elif isinstance(size_value, str):
                processed_font_sizes[size_name] = size_value
            else:
                processed_font_sizes[size_name] = str(size_value)
        
        return processed_font_sizes

    def _process_resolved_font_families(self, font_families: Dict) -> Dict:
        """Process resolved font family values"""
        
        processed_font_families = {}
        
        for family_name, family_value in font_families.items():
            if isinstance(family_value, list):
                # Handle font stack arrays
                processed_font_families[family_name] = ', '.join(family_value)
            elif isinstance(family_value, str):
                processed_font_families[family_name] = family_value
            else:
                processed_font_families[family_name] = str(family_value)
        
        return processed_font_families

    def _parse_css_for_theme(self, project_path: str) -> Dict:
        """Parse CSS files for @theme and @import statements using new pipeline"""

        # Step 1: Find all CSS files
        css_files = self.find_all_css_files(project_path)

        if not css_files:
            print("Info: No CSS files found for theme parsing")
            return {}

        # Store the main CSS file path (first one is the main file)
        if css_files:
            self.main_css_file_path = os.path.abspath(css_files[0])
            print(f"Info: Main CSS file found: {self.main_css_file_path}")

        # Step 2: Aggregate all CSS content
        aggregated_content = self.aggregate_css_content(css_files)

        # Step 3: Extract theme blocks
        theme_content = self.extract_theme_blocks(aggregated_content)

        # Step 4: Parse and classify theme tokens using new logic
        classified_tokens = self.parse_and_classify_theme(theme_content)

        # Step 5: If no colors found in @theme, extract from components
        if not classified_tokens["colors"]:
            component_colors = self._extract_colors_from_components(project_path)
            # Convert component color names to proper color structure
            for color_name in component_colors:
                classified_tokens["colors"][
                    color_name
                ] = f"<{color_name}>"  # Placeholder value

        # Step 6: Structure the data for tailwind.config.js format
        structured_data = {
            "colors": classified_tokens["colors"],
            "fontFamily": classified_tokens["fonts"],
            "fontSize": classified_tokens["typography"],
            "spacing": classified_tokens["spacing"],
            "extend": {
                "colors": classified_tokens["colors"],
                "fontFamily": classified_tokens["fonts"],
                "spacing": classified_tokens["spacing"],
            },
        }

        print(
            f"Info: Structured {len(classified_tokens['colors'])} colors, {len(classified_tokens['fonts'])} fonts, {len(classified_tokens['typography'])} typography, {len(classified_tokens['spacing'])} spacing tokens"
        )

        return structured_data

    def _find_main_css_file(self, project_path: str) -> Optional[str]:
        """Find the main CSS entry point by recursively searching all subdirectories"""

        # Common CSS file names to look for (prioritized by importance)
        css_filenames = [
            "style.css",
            "styles.css",
            "globals.css",
            "global.css",
            "tailwind.css",
            "app.css",
            "main.css",
        ]

        # First, try the predefined paths for faster lookup
        predefined_candidates = [
            "style.css",
            "styles.css",
            "globals.css",
            "global.css",
            "tailwind.css",
            "app.css",
            "main.css",
            "src/styles.css",
            "src/style.css",
            "src/globals.css",
            "src/app/globals.css",
            "styles/globals.css",
            "styles/style.css",
            "app/globals.css",
            "app/css/style.css",
            "app/css/styles.css",
            "test_css/style.css",
            "test_css/styles.css",
            "css/style.css",
            "css/styles.css",
        ]

        for candidate in predefined_candidates:
            css_path = os.path.join(project_path, candidate)
            if os.path.exists(css_path):
                return css_path

        # If no predefined paths work, recursively search through all directories
        print(f"Info: No CSS file found in common locations, searching recursively...")

        for root, dirs, files in os.walk(project_path):
            # Skip common directories that shouldn't contain main CSS files
            dirs[:] = [
                d
                for d in dirs
                if d
                not in [
                    ".git",
                    "node_modules",
                    ".next",
                    "dist",
                    "build",
                    "__pycache__",
                    ".vscode",
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                ]
            ]

            for filename in files:
                if filename in css_filenames:
                    css_path = os.path.join(root, filename)
                    print(f"Info: Found CSS file during recursive search: {css_path}")
                    return css_path

        return None

    def find_all_css_files(self, project_path: str) -> List[str]:
        """Find main CSS file and collect all imported CSS files"""

        # Step 1: Find the main CSS entry point
        main_css_file = self._find_main_css_file(project_path)

        if not main_css_file:
            print(f"Info: No main CSS file found in {project_path}")
            return []

        print(f"Info: Found main CSS file: {main_css_file}")

        # Step 2: Collect all CSS files by following @import statements
        all_css_files = []
        visited_files = set()
        files_to_process = [main_css_file]

        while files_to_process:
            current_file = files_to_process.pop(0)

            # Skip if already processed
            if current_file in visited_files:
                continue

            visited_files.add(current_file)
            all_css_files.append(current_file)

            # Find @import statements in current file
            imported_files = self._extract_imports_from_css_file(
                current_file, project_path
            )

            # Add new files to process queue
            for imported_file in imported_files:
                if imported_file not in visited_files:
                    files_to_process.append(imported_file)

        print(f"Info: Found {len(all_css_files)} CSS files total")
        return all_css_files

    def _extract_imports_from_css_file(
        self, css_file_path: str, project_path: str
    ) -> List[str]:
        """Extract @import statements from a CSS file and return absolute paths"""

        imported_files = []

        try:
            with open(css_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find all @import statements
            import_pattern = r'@import\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)

            for import_path in imports:
                # Skip known Tailwind v4 imports that don't resolve to local files
                if import_path in [
                    "tailwindcss",
                    "tailwindcss/base",
                    "tailwindcss/components",
                    "tailwindcss/utilities",
                ]:
                    print(f"Info: Skipping Tailwind v4 import: {import_path}")
                    continue

                # Resolve relative paths
                if import_path.startswith("./") or import_path.startswith("../"):
                    # Relative to current CSS file
                    base_dir = os.path.dirname(css_file_path)
                    resolved_path = os.path.normpath(
                        os.path.join(base_dir, import_path)
                    )
                else:
                    # Relative to project root
                    resolved_path = os.path.join(project_path, import_path)

                # Only include if file exists
                if os.path.exists(resolved_path):
                    imported_files.append(resolved_path)
                else:
                    # Only show warning for non-Tailwind imports
                    if not import_path.startswith("tailwind") and not import_path in [
                        "normalize.css",
                        "reset.css",
                    ]:
                        print(
                            f"Warning: Import not found: {import_path} -> {resolved_path}"
                        )

        except Exception as e:
            print(f"Warning: Error reading CSS file {css_file_path}: {e}")

        return imported_files

    def aggregate_css_content(self, css_file_paths: List[str]) -> str:
        """Combine all CSS files into a single string"""

        if not css_file_paths:
            print("Info: No CSS files to aggregate")
            return ""

        combined_content = []

        for css_file_path in css_file_paths:
            try:
                with open(css_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Add a comment header to identify the source file
                file_name = os.path.basename(css_file_path)
                header = f"\n/* === Content from {file_name} === */\n"

                combined_content.append(header)
                combined_content.append(content)
                combined_content.append("\n")  # Add spacing between files

                print(
                    f"Info: Added content from {css_file_path} ({len(content)} characters)"
                )

            except Exception as e:
                print(f"Warning: Error reading CSS file {css_file_path}: {e}")
                continue

        # Join all content into a single string
        aggregated_content = "".join(combined_content)

        print(
            f"Info: Aggregated {len(css_file_paths)} CSS files into {len(aggregated_content)} characters"
        )

        return aggregated_content

    def extract_theme_blocks(self, css_content: str) -> str:
        """Extract content from @theme { ... } blocks and :root { ... } blocks"""

        if not css_content:
            print("Info: No CSS content to extract theme blocks from")
            return ""

        # Multiple patterns to match different @theme block formats
        theme_patterns = [
            # Standard @theme { ... } blocks
            r"@theme\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
            # Tailwind v4 style with potential nested structures
            r"@theme\s*\{([\s\S]*?)\}(?=\s*(?:@|\.|#|$))",
            # More permissive pattern for complex nested blocks
            r"@theme\s*\{((?:[^{}]|\{[^{}]*\})*)\}",
        ]

        # Patterns to match :root blocks with CSS custom properties
        root_patterns = [
            # Standard :root { ... } blocks
            r":root\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
            # More permissive :root pattern
            r":root\s*\{([\s\S]*?)\}(?=\s*(?:\.|#|:|@|$))",
        ]

        all_theme_matches = []

        # Try @theme patterns first
        for i, pattern in enumerate(theme_patterns):
            theme_matches = re.findall(pattern, css_content, re.DOTALL | re.MULTILINE)
            if theme_matches:
                print(f"Info: @theme pattern {i+1} found {len(theme_matches)} @theme blocks")
                all_theme_matches.extend(theme_matches)
                break  # Use the first pattern that finds matches

        # Try :root patterns
        for i, pattern in enumerate(root_patterns):
            root_matches = re.findall(pattern, css_content, re.DOTALL | re.MULTILINE)
            if root_matches:
                print(f"Info: :root pattern {i+1} found {len(root_matches)} :root blocks")
                all_theme_matches.extend(root_matches)
                break  # Use the first pattern that finds matches

        # If no patterns worked, try a more aggressive approach
        if not all_theme_matches:
            # Manual parsing approach for complex cases
            theme_blocks = self._manual_theme_extraction(css_content)
            if theme_blocks:
                all_theme_matches.extend(theme_blocks)

        if not all_theme_matches:
            print("Info: No @theme or :root blocks found in CSS content")
            print("Debug: First 500 characters of CSS content:")
            print(css_content[:500])
            return ""

        print(f"Info: Found {len(all_theme_matches)} theme/root blocks total")

        # Combine all theme block contents
        combined_theme_content = []

        for i, theme_content in enumerate(all_theme_matches):
            theme_content = theme_content.strip()
            print(f"Info: Theme block {i+1}: {len(theme_content)} characters")
            combined_theme_content.append(theme_content)

        # Join all theme blocks with newlines
        result = "\n".join(combined_theme_content)

        print(f"Info: Extracted {len(result)} characters from @theme blocks")

        return result

    def _manual_theme_extraction(self, css_content: str) -> List[str]:
        """Manual extraction for complex @theme blocks that regex might miss"""

        theme_blocks = []
        lines = css_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Look for @theme declaration
            if line.startswith("@theme") and "{" in line:
                theme_content = []
                brace_count = line.count("{") - line.count("}")

                # If the opening brace is on the same line, extract content after it
                if "{" in line:
                    content_start = line.find("{") + 1
                    remaining_content = line[content_start:].strip()
                    if remaining_content and not remaining_content.startswith("}"):
                        theme_content.append(remaining_content)
                    brace_count = line.count("{") - line.count("}")

                i += 1

                # Continue reading until we close all braces
                while i < len(lines) and brace_count > 0:
                    current_line = lines[i]
                    theme_content.append(current_line)
                    brace_count += current_line.count("{") - current_line.count("}")
                    i += 1

                # Remove the closing brace from the last line if present
                if theme_content and "}" in theme_content[-1]:
                    last_line = theme_content[-1]
                    closing_brace_pos = last_line.rfind("}")
                    if closing_brace_pos >= 0:
                        theme_content[-1] = last_line[:closing_brace_pos]

                # Join and clean up the theme content
                block_content = "\n".join(theme_content).strip()
                if block_content:
                    theme_blocks.append(block_content)
                    print(
                        f"Info: Manual extraction found @theme block with {len(block_content)} characters"
                    )
            else:
                i += 1

        return theme_blocks

    def parse_and_classify_theme(self, theme_content: str) -> dict:
        """
        Parses a string of CSS theme content and classifies tokens
        into colors, fonts, typography, and spacing.
        """
        tokens = {"colors": {}, "fonts": {}, "typography": {}, "spacing": {}}

        # Regex to find CSS custom properties or theme key-value pairs
        # Handles lines like '--color-primary: #ffffff;' or 'primary: #ffffff;'
        token_pattern = re.compile(r"(--[\w-]+|[\w-]+)\s*:\s*([^;]+);")

        for line in theme_content.splitlines():
            line = line.strip()
            if not line or line.startswith("@"):
                continue  # Skip empty lines and directives like @keyframes

            match = token_pattern.match(line)
            if not match:
                continue

            name = match.group(1).strip()
            value = match.group(2).strip()

            # --- CLASSIFICATION LOGIC ---
            # Clean up common prefixes for better classification
            clean_name = (
                name.replace("--color-", "")
                .replace("--font-", "")
                .replace("--spacing-", "")
                .replace("--text-", "")
                .replace("--", "")
            )

            # Color classification (check first as it's most specific)
            if (
                "color" in name.lower()
                or "#" in value
                or "rgb" in value
                or "hsl" in value
                or re.match(r"^\d+\s+\d+%\s+\d+%", value)  # HSL without hsl() wrapper
                or name.lower()
                in [
                    "--primary",
                    "--secondary", 
                    "--accent",
                    "--background",
                    "--foreground",
                    "--muted",
                    "--card",
                    "--popover",
                    "--destructive",
                    "--border",
                    "--input",
                    "--ring",
                    "--chart-1",
                    "--chart-2", 
                    "--chart-3",
                    "--chart-4",
                    "--chart-5",
                    "--sidebar-background",
                    "--sidebar-foreground",
                    "--sidebar-primary",
                    "--sidebar-accent",
                    "--sidebar-border",
                    "--sidebar-ring",
                ]
            ):
                tokens["colors"][clean_name] = value
            # Typography classification (check before general font classification)
            elif (
                "font-size" in name.lower()
                or "text-" in name.lower()
                or ("size" in name.lower() and ("rem" in value or "px" in value))
            ):
                tokens["typography"][clean_name] = value
            # Font family classification
            elif (
                "font-family" in name.lower()
                or "font" in name.lower()
                or ("family" in name.lower() and " " in value and "," in value)
            ):
                tokens["fonts"][clean_name] = value
            # Spacing classification
            elif "spacing" in name.lower() or "radius" in name.lower() or (
                ("rem" in value or "px" in value or "em" in value)
                and (
                    "spacing" in name.lower()
                    or "gap" in name.lower()
                    or "margin" in name.lower()
                    or "padding" in name.lower()
                    or "radius" in name.lower()
                )
            ):
                tokens["spacing"][clean_name] = value
            # Fallback for font families (space-separated values with commas)
            elif " " in value and "," in value:
                tokens["fonts"][clean_name] = value
            # Fallback for numeric values that could be spacing
            elif "rem" in value or "px" in value:
                tokens["spacing"][clean_name] = value

        return tokens

    def parse_theme_tokens(self, theme_content: str) -> Dict[str, str]:
        """Parse theme block content into a dictionary of key-value pairs"""

        if not theme_content:
            print("Info: No theme content to parse")
            return {}

        theme_tokens = {}

        # Split content into lines and process each line
        lines = theme_content.split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("/*") or line.startswith("//"):
                continue

            # Skip @ rules like @keyframes, @media, etc.
            if line.startswith("@"):
                continue

            # Parse CSS custom properties (--variable: value;)
            css_var_match = re.match(r"--([^:]+):\s*([^;]+);?", line)
            if css_var_match:
                key = css_var_match.group(1).strip()
                value = css_var_match.group(2).strip()

                # Remove outer quotes from string values (but keep inner quotes)
                # Don't remove quotes if they're part of a CSS value like font-family
                if (
                    value.startswith('"')
                    and value.endswith('"')
                    and value.count('"') == 2
                ):
                    value = value[1:-1]
                elif (
                    value.startswith("'")
                    and value.endswith("'")
                    and value.count("'") == 2
                ):
                    value = value[1:-1]

                theme_tokens[key] = value
                continue

            # Parse regular CSS properties (property: value;)
            css_prop_match = re.match(r"([a-zA-Z][a-zA-Z0-9-]*)\s*:\s*([^;]+);?", line)
            if css_prop_match:
                key = css_prop_match.group(1).strip()
                value = css_prop_match.group(2).strip()

                # Remove outer quotes from string values (but keep inner quotes)
                # Don't remove quotes if they're part of a CSS value like font-family
                if (
                    value.startswith('"')
                    and value.endswith('"')
                    and value.count('"') == 2
                ):
                    value = value[1:-1]
                elif (
                    value.startswith("'")
                    and value.endswith("'")
                    and value.count("'") == 2
                ):
                    value = value[1:-1]

                theme_tokens[key] = value
                continue

            # If line doesn't match expected patterns, log it
            if line:
                print(f"Warning: Could not parse theme line: {line}")

        print(f"Info: Parsed {len(theme_tokens)} theme tokens")

        # Log some examples
        if theme_tokens:
            print("Info: Sample theme tokens:")
            for i, (key, value) in enumerate(list(theme_tokens.items())[:3]):
                print(f"  {key}: {value}")
            if len(theme_tokens) > 3:
                print(f"  ... and {len(theme_tokens) - 3} more")

        return theme_tokens

    def _classify_token(self, key: str, value: str) -> str:
        """Intelligently classify a token based on its name and value"""

        key_lower = key.lower()
        value_lower = value.lower()

        # Rule 1: If token name starts with font-, classify as font
        if key_lower.startswith("font-"):
            return "font"

        # Rule 2: If token name starts with text-, classify as typography
        if key_lower.startswith("text-"):
            return "typography"

        # Rule 3: If value contains color indicators, classify as color
        # Check for hex colors, rgb/rgba, hsl/hsla functions, and named colors
        color_indicators = [
            "#",
            "rgb(",
            "rgba(",
            "hsl(",
            "hsla(",
            "rgb ",
            "rgba ",
            "hsl ",
            "hsla ",
        ]
        if any(color_indicator in value_lower for color_indicator in color_indicators):
            return "color"

        # Additional check for CSS color keywords (but not if it's just a number)
        css_color_keywords = [
            "red",
            "blue",
            "green",
            "white",
            "black",
            "transparent",
            "currentcolor",
        ]
        value_stripped = value_lower.strip()
        if value_stripped in css_color_keywords:
            return "color"

        # Don't classify pure numbers as colors
        try:
            float(value_stripped)
            # If it's a pure number, it's not a color, continue to other rules
        except ValueError:
            # Not a pure number, could still be a color
            pass

        # Rule 4: If value contains size units, classify as spacing
        if any(unit in value_lower for unit in ["rem", "px", "em", "vh", "vw", "%"]):
            # But if the key suggests it's font-related, it's typography
            if any(
                font_word in key_lower
                for font_word in ["size", "height", "weight", "leading", "tracking"]
            ):
                return "typography"
            return "spacing"

        # Fallback rules based on key names
        if any(
            color_word in key_lower
            for color_word in [
                "color",
                "primary",
                "secondary",
                "accent",
                "background",
                "foreground",
                "muted",
                "border",
            ]
        ):
            return "color"
        elif any(font_word in key_lower for font_word in ["font", "family", "weight"]):
            return "font"
        elif any(
            typo_word in key_lower
            for typo_word in ["size", "height", "leading", "tracking", "line"]
        ):
            return "typography"
        elif any(
            spacing_word in key_lower
            for spacing_word in [
                "spacing",
                "margin",
                "padding",
                "gap",
                "width",
                "height",
            ]
        ):
            return "spacing"

        return "other"

    def _structure_css_theme_tokens(self, theme_tokens: Dict[str, str]) -> Dict:
        """Structure CSS theme tokens using intelligent classification"""

        if not theme_tokens:
            return {}

        # Separate tokens by category using intelligent classification
        colors = {}
        fonts = {}
        typography = {}
        spacing = {}
        other = {}

        for key, value in theme_tokens.items():
            classification = self._classify_token(key, value)

            if classification == "color":
                # Remove color- prefix if present
                color_key = (
                    key.replace("color-", "") if key.startswith("color-") else key
                )
                colors[color_key] = value
            elif classification == "font":
                # Remove font- prefix if present
                font_key = key.replace("font-", "") if key.startswith("font-") else key
                fonts[font_key] = value
            elif classification == "typography":
                # Remove text- prefix if present
                typo_key = key.replace("text-", "") if key.startswith("text-") else key
                typography[typo_key] = value
            elif classification == "spacing":
                # Remove spacing- prefix if present
                spacing_key = (
                    key.replace("spacing-", "") if key.startswith("spacing-") else key
                )
                spacing[spacing_key] = value
            else:
                other[key] = value

        # Structure like tailwind.config.js
        structured_data = {
            "colors": colors,
            "fontFamily": fonts,
            "fontSize": typography,
            "spacing": spacing,
            "extend": {"colors": colors, "fontFamily": fonts, "spacing": spacing},
        }

        print(
            f"Info: Structured {len(colors)} colors, {len(fonts)} fonts, {len(typography)} typography, {len(spacing)} spacing tokens"
        )

        return structured_data

    def _collect_all_css_files(
        self, main_css_file: str, project_path: str
    ) -> List[str]:
        """Collect all CSS files by following @import statements"""

        css_files = [main_css_file]
        visited = set()

        def process_file(file_path: str):
            if file_path in visited:
                return
            visited.add(file_path)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find all @import statements
                import_pattern = r'@import\s+[\'"]([^\'\"]+)[\'"]'
                imports = re.findall(import_pattern, content)

                for import_path in imports:
                    # Resolve relative paths
                    if import_path.startswith("./") or import_path.startswith("../"):
                        base_dir = os.path.dirname(file_path)
                        resolved_path = os.path.normpath(
                            os.path.join(base_dir, import_path)
                        )
                    else:
                        resolved_path = os.path.join(project_path, import_path)

                    if os.path.exists(resolved_path):
                        css_files.append(resolved_path)
                        process_file(resolved_path)

            except Exception as e:
                print(f"Warning: Error reading CSS file {file_path}: {e}")

        process_file(main_css_file)
        return css_files

    def _extract_theme_from_css_files(self, css_files: List[str]) -> Dict:
        """Extract theme data from CSS files"""

        theme_data = {"colors": {}, "fonts": {}, "spacing": {}, "other": {}}

        for css_file in css_files:
            try:
                with open(css_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract @theme blocks
                theme_blocks = self._extract_theme_blocks(content)

                for theme_block in theme_blocks:
                    self._parse_theme_block(theme_block, theme_data)

            except Exception as e:
                print(f"Warning: Error parsing CSS file {css_file}: {e}")

        return theme_data

    def _extract_theme_blocks(self, css_content: str) -> List[str]:
        """Extract @theme { ... } blocks from CSS content"""

        # Pattern to match @theme { ... } blocks
        pattern = r"@theme\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
        matches = re.findall(pattern, css_content, re.DOTALL)

        return matches

    def _parse_theme_block(self, theme_block: str, theme_data: Dict):
        """Parse a @theme block and extract key-value pairs"""

        # Parse CSS custom properties (--variable: value;)
        css_var_pattern = r"--([^:]+):\s*([^;]+);"
        css_vars = re.findall(css_var_pattern, theme_block)

        # Parse regular CSS properties (property: value;)
        css_prop_pattern = r"([a-zA-Z-]+):\s*([^;]+);"
        css_props = re.findall(css_prop_pattern, theme_block)

        # Process CSS variables
        for var_name, var_value in css_vars:
            var_name = var_name.strip()
            var_value = var_value.strip()

            if "color" in var_name:
                theme_data["colors"][var_name.replace("color-", "")] = var_value
            elif "font" in var_name:
                theme_data["fonts"][var_name.replace("font-", "")] = var_value
            elif any(
                spacing_word in var_name
                for spacing_word in ["spacing", "size", "width", "height"]
            ):
                theme_data["spacing"][var_name] = var_value
            else:
                theme_data["other"][var_name] = var_value

        # Process regular CSS properties
        for prop_name, prop_value in css_props:
            prop_name = prop_name.strip()
            prop_value = prop_value.strip()

            if prop_name in [
                "primary",
                "secondary",
                "accent",
                "background",
                "foreground",
            ]:
                theme_data["colors"][prop_name] = prop_value
            elif "font" in prop_name:
                theme_data["fonts"][prop_name] = prop_value
            else:
                theme_data["other"][prop_name] = prop_value

    def _structure_css_theme_data(self, theme_data: Dict) -> Dict:
        """Structure CSS theme data like a tailwind.config.js would"""

        structured_data = {
            "colors": {},
            "fontSize": {},
            "fontFamily": {},
            "spacing": {},
            "extend": {
                "colors": theme_data["colors"],
                "fontFamily": theme_data["fonts"],
            },
        }

        # Add colors to both main and extended
        structured_data["colors"] = theme_data["colors"]

        # Add font data
        structured_data["fontFamily"] = theme_data["fonts"]

        # Add spacing data
        structured_data["spacing"] = theme_data["spacing"]

        return structured_data

    def _extract_colors_from_config(
        self, tailwind_config: Dict, project_path: str
    ) -> Dict:
        """Extract color palette from parsed Tailwind config with detailed structure"""

        colors = {
            "semantic": [],  # bg-primary, text-foreground style
            "custom": [],  # Custom color names
            "structure": {},  # Full color structure for reference
        }

        # Check if this is a resolved config with full Tailwind defaults
        is_resolved = tailwind_config.get('_resolved', False)

        # First, try to get colors from new structured config
        if "colors" in tailwind_config and tailwind_config["colors"]:
            config_colors = tailwind_config["colors"]
            colors["structure"].update(config_colors)

            # Extract color names, prioritizing custom colors
            for color_name, color_value in config_colors.items():
                if isinstance(color_value, dict) or isinstance(color_value, str):
                    colors["custom"].append(color_name)

                # For resolved configs, distinguish between default Tailwind colors and custom ones
                if is_resolved:
                    # Common Tailwind default colors
                    default_colors = {
                        'inherit', 'current', 'transparent', 'black', 'white',
                        'slate', 'gray', 'zinc', 'neutral', 'stone',
                        'red', 'orange', 'amber', 'yellow', 'lime', 'green',
                        'emerald', 'teal', 'cyan', 'sky', 'blue', 'indigo',
                        'violet', 'purple', 'fuchsia', 'pink', 'rose'
                    }
                    
                    # Only add to semantic if it's not a default Tailwind color
                    if color_name not in default_colors:
                        colors["semantic"].append(color_name)
                else:
                    # All CSS-parsed colors are semantic (single values)
                    if isinstance(color_value, str):
                        colors["semantic"].append(color_name)

        # Get extended colors (most important for custom themes)
        if "extend" in tailwind_config and "colors" in tailwind_config["extend"]:
            extend_colors = tailwind_config["extend"]["colors"]
            colors["structure"].update(extend_colors)

            for color_name, color_value in extend_colors.items():
                if color_name not in colors["custom"]:
                    colors["custom"].append(color_name)

                # Extended colors are usually custom semantic colors
                if color_name not in colors["semantic"]:
                    colors["semantic"].append(color_name)

        # For resolved configs, extract the most commonly used colors
        if is_resolved and len(colors["custom"]) > 20:
            # Filter to most useful colors for UI generation
            priority_colors = []
            
            # Add semantic colors first
            priority_colors.extend(colors["semantic"][:10])
            
            # Add common color scales
            common_scales = ['blue', 'gray', 'green', 'red', 'yellow', 'purple', 'indigo']
            for scale in common_scales:
                if scale in colors["custom"] and scale not in priority_colors:
                    priority_colors.append(scale)
                    if len(priority_colors) >= 15:
                        break
            
            colors["custom"] = priority_colors

        # Fallback to component-based extraction if no colors found
        if not colors["custom"]:
            component_colors = self._extract_colors_from_components(project_path)
            colors["custom"] = component_colors

        # Fallback to regex-based extraction if still no colors found
        if not colors["custom"]:
            fallback_colors = self._extract_tailwind_colors_fallback(project_path)
            colors["custom"] = fallback_colors

        # Default colors if still none found
        if not colors["custom"]:
            colors["custom"] = ["blue", "gray", "green", "red", "yellow"]

        print(
            f"Info: Found {len(colors['custom'])} custom colors, {len(colors['semantic'])} semantic colors"
            f" (resolved: {is_resolved})"
        )

        return colors

    def _extract_colors_from_components(self, project_path: str) -> List[str]:
        """Extract color names from Tailwind classes used in component files"""

        colors = set()

        # Common file extensions for components
        extensions = ["*.tsx", "*.jsx", "*.ts", "*.js", "*.vue", "*.html"]

        # Common directories to search
        directories = ["components", "src", "app", "pages", "."]

        # Regex to match Tailwind color classes
        color_patterns = [
            r"(?:bg|text|border|ring|shadow|outline|decoration|accent|caret|divide|placeholder)-([a-z]+)-\d+",  # bg-blue-500
            r'(?:bg|text|border|ring|shadow|outline|decoration|accent|caret|divide|placeholder)-([a-z]+)(?:\s|"|\'|>|$)',  # bg-blue
            r"(?:from|via|to)-([a-z]+)-\d+",  # gradient colors
            r'(?:from|via|to)-([a-z]+)(?:\s|"|\'|>|$)',  # gradient colors
        ]

        compiled_patterns = [re.compile(pattern) for pattern in color_patterns]

        for directory in directories:
            dir_path = os.path.join(project_path, directory)
            if not os.path.exists(dir_path):
                continue

            for extension in extensions:
                pattern = os.path.join(dir_path, "**", extension)
                files = glob.glob(pattern, recursive=True)

                for file_path in files[:20]:  # Limit to 20 files for performance
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                            for pattern in compiled_patterns:
                                matches = pattern.findall(content)
                                for match in matches:
                                    # Only include valid Tailwind color names
                                    valid_colors = [
                                        "red",
                                        "orange",
                                        "amber",
                                        "yellow",
                                        "lime",
                                        "green",
                                        "emerald",
                                        "teal",
                                        "cyan",
                                        "sky",
                                        "blue",
                                        "indigo",
                                        "violet",
                                        "purple",
                                        "fuchsia",
                                        "pink",
                                        "rose",
                                        "gray",
                                        "slate",
                                        "zinc",
                                        "neutral",
                                        "stone",
                                        "white",
                                        "black",
                                    ]
                                    if match in valid_colors:
                                        colors.add(match)
                    except Exception:
                        continue

        # Sort and limit colors
        color_list = sorted(list(colors))[:8]  # Return up to 8 colors

        print(
            f"Info: Extracted {len(color_list)} colors from component files: {color_list}"
        )

        return color_list

    def _extract_tailwind_colors_fallback(self, project_path: str) -> List[str]:
        """Fallback method: Extract color palette from Tailwind config using regex"""

        tailwind_configs = ["tailwind.config.js", "tailwind.config.ts"]
        colors = []

        for config in tailwind_configs:
            config_path = os.path.join(project_path, config)
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        content = f.read()
                        # Extract custom colors from config
                        color_matches = re.findall(
                            r"colors:\s*{([^}]+)}", content, re.DOTALL
                        )
                        for match in color_matches:
                            # Extract color names
                            color_names = re.findall(r"([a-zA-Z][a-zA-Z0-9-]*)", match)
                            colors.extend(color_names[:5])  # Limit to first 5 colors
                except:
                    pass

        return colors

    def _extract_spacing_from_config(
        self, tailwind_config: Dict, project_path: str
    ) -> List[str]:
        """Extract spacing patterns from parsed Tailwind config"""

        spacing = []

        # Check if this is CSS parsing results (has spacing dict with named keys)
        if "spacing" in tailwind_config and isinstance(tailwind_config["spacing"], dict):
            css_spacing = tailwind_config["spacing"]
            # Include named spacing tokens (like radius, margin, padding)
            for spacing_key, spacing_value in css_spacing.items():
                spacing.append(f"{spacing_key}={spacing_value}")

        # Get numeric spacing from traditional tailwind config
        if "spacing" in tailwind_config and isinstance(tailwind_config["spacing"], dict):
            config_spacing = tailwind_config["spacing"]
            # Extract numeric spacing values
            for spacing_key in config_spacing.keys():
                if spacing_key.isdigit():
                    spacing.append(spacing_key)

        # Get extended spacing
        if "extend" in tailwind_config and "spacing" in tailwind_config["extend"]:
            extend_spacing = tailwind_config["extend"]["spacing"]
            for spacing_key in extend_spacing.keys():
                if spacing_key.isdigit() and spacing_key not in spacing:
                    spacing.append(spacing_key)

        # Fallback to component analysis if no spacing found
        if not spacing:
            spacing = self._extract_spacing_patterns(project_path)

        # Default spacing if still none found
        if not spacing:
            spacing = ["2", "4", "6", "8", "12", "16"]

        return spacing[:8]  # Limit to 8 spacing values

    def _extract_typography_from_config(
        self, tailwind_config: Dict, project_path: str
    ) -> List[str]:
        """Extract typography scale from parsed Tailwind config"""

        typography = []

        # Get font sizes from new structured config
        if "fontSize" in tailwind_config and tailwind_config["fontSize"]:
            config_font_sizes = tailwind_config["fontSize"]

            # Extract font size names (could be dict or already processed)
            if isinstance(config_font_sizes, dict):
                for font_size_name in config_font_sizes.keys():
                    typography.append(font_size_name)
            elif isinstance(config_font_sizes, list):
                typography.extend(config_font_sizes)

        # Get extended font sizes
        if "extend" in tailwind_config and "fontSize" in tailwind_config["extend"]:
            extend_font_sizes = tailwind_config["extend"]["fontSize"]
            if isinstance(extend_font_sizes, dict):
                for font_size_name in extend_font_sizes.keys():
                    if font_size_name not in typography:
                        typography.append(font_size_name)
            elif isinstance(extend_font_sizes, list):
                for font_size_name in extend_font_sizes:
                    if font_size_name not in typography:
                        typography.append(font_size_name)

        # Fallback to component analysis if no typography found
        if not typography:
            typography = self._extract_typography_scale(project_path)

        # Default typography if still none found
        if not typography:
            typography = ["sm", "base", "lg", "xl", "2xl"]

        return typography[:8]  # Limit to 8 typography values

    def _extract_shadows_from_config(self, tailwind_config: Dict) -> List[str]:
        """Extract shadow patterns from parsed Tailwind config"""

        shadows = []

        # Get shadows from config
        if "boxShadow" in tailwind_config and tailwind_config["boxShadow"]:
            config_shadows = tailwind_config["boxShadow"]

            # Extract shadow names
            for shadow_name in config_shadows.keys():
                shadows.append(shadow_name)

        # Get extended shadows
        if "extend" in tailwind_config and "boxShadow" in tailwind_config["extend"]:
            extend_shadows = tailwind_config["extend"]["boxShadow"]
            for shadow_name in extend_shadows.keys():
                if shadow_name not in shadows:
                    shadows.append(shadow_name)

        # Default shadows if none found
        if not shadows:
            shadows = ["sm", "md", "lg", "xl"]

        return shadows[:6]  # Limit to 6 shadow values

    def _extract_border_radius_from_config(self, tailwind_config: Dict) -> List[str]:
        """Extract border radius patterns from parsed Tailwind config"""

        border_radius = []

        # Get border radius from config
        if "borderRadius" in tailwind_config and tailwind_config["borderRadius"]:
            config_border_radius = tailwind_config["borderRadius"]

            # Extract border radius names
            for radius_name in config_border_radius.keys():
                border_radius.append(radius_name)

        # Get extended border radius
        if "extend" in tailwind_config and "borderRadius" in tailwind_config["extend"]:
            extend_border_radius = tailwind_config["extend"]["borderRadius"]
            for radius_name in extend_border_radius.keys():
                if radius_name not in border_radius:
                    border_radius.append(radius_name)

        # Default border radius if none found
        if not border_radius:
            border_radius = ["sm", "md", "lg", "xl"]

        return border_radius[:6]  # Limit to 6 border radius values

    def _extract_spacing_patterns(self, project_path: str) -> List[str]:
        """Extract spacing patterns from existing components"""

        spacing_patterns = []

        # Look for common component directories
        component_dirs = ["src/components", "components", "app/components"]

        for comp_dir in component_dirs:
            dir_path = os.path.join(project_path, comp_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith((".tsx", ".jsx", ".ts", ".js")):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, "r") as f:
                                    content = f.read()
                                    # Extract Tailwind spacing classes
                                    spacing_matches = re.findall(
                                        r"[mp][xybtlr]?-(\d+)", content
                                    )
                                    spacing_patterns.extend(spacing_matches)
                            except:
                                continue

        # Get unique spacing values, limit to common ones
        unique_spacing = list(set(spacing_patterns))
        common_spacing = ["2", "4", "6", "8", "12", "16"]

        return [s for s in common_spacing if s in unique_spacing] or common_spacing[:4]

    def _extract_typography_scale(self, project_path: str) -> List[str]:
        """Extract typography scale from existing components"""

        typography = []

        # Look for common component directories
        component_dirs = ["src/components", "components", "app/components"]

        for comp_dir in component_dirs:
            dir_path = os.path.join(project_path, comp_dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.endswith((".tsx", ".jsx", ".ts", ".js")):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, "r") as f:
                                    content = f.read()
                                    # Extract Tailwind text size classes
                                    text_matches = re.findall(
                                        r"text-(xs|sm|base|lg|xl|2xl|3xl|4xl)", content
                                    )
                                    typography.extend(text_matches)
                            except:
                                continue

        # Default typography scale
        default_typography = ["sm", "base", "lg", "xl", "2xl"]
        unique_typography = list(set(typography))

        return [
            t for t in default_typography if t in unique_typography
        ] or default_typography[:3]

    def _extract_shadow_patterns(self, project_path: str) -> List[str]:
        """Extract shadow patterns from existing components"""
        return ["sm", "md", "lg"]  # Default shadows

    def _extract_border_patterns(self, project_path: str) -> List[str]:
        """Extract border radius patterns from existing components"""
        return ["sm", "md", "lg"]  # Default border radius

    def _analyze_component_patterns(self, project_path: str) -> Dict:
        """Analyze existing component patterns"""

        return {
            "button_variants": self._analyze_button_patterns(project_path),
            "layout_patterns": self._analyze_layout_structures(project_path),
            "animation_styles": self._extract_animation_patterns(project_path),
        }

    def _analyze_button_patterns(self, project_path: str) -> List[str]:
        """Analyze button component patterns"""
        return ["primary", "secondary", "outline"]  # Default button variants

    def _analyze_layout_structures(self, project_path: str) -> List[str]:
        """Analyze layout patterns"""
        return ["grid", "flex", "container"]  # Default layout patterns

    def _extract_animation_patterns(self, project_path: str) -> List[str]:
        """Extract animation patterns"""
        return ["fade", "slide", "scale"]  # Default animations

    def _analyze_project_structure(self, project_path: str) -> Dict:
        """Analyze project structure for component placement"""

        structure = {
            "components_dir": self._find_components_directory(project_path),
            "pages_dir": self._find_pages_directory(project_path),
            "styles_dir": self._find_styles_directory(project_path),
        }

        return structure

    def get_available_imports(self, project_path: str) -> Dict:
        """Get available imports and dependencies for component generation"""

        package_json_path = os.path.join(project_path, "package.json")
        dependencies = {}

        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {}),
                    }
            except json.JSONDecodeError:
                pass

        available_imports = {
            "react_hooks": self._get_available_react_hooks(dependencies),
            "ui_components": self._get_available_ui_components(
                project_path, dependencies
            ),
            "utilities": self._get_available_utilities(project_path, dependencies),
            "icons": self._get_available_icons(dependencies),
            "styling": self._get_available_styling_utilities(dependencies),
        }

        return available_imports

    def _get_available_react_hooks(self, dependencies: dict) -> List[str]:
        """Get available React hooks based on React version"""

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

    def _get_available_ui_components(
        self, project_path: str, dependencies: dict
    ) -> Dict:
        """Get available UI components and their import paths"""

        ui_components = {"shadcn_ui": [], "custom": [], "third_party": []}

        # Check for shadcn/ui components
        if self._is_shadcn_ui_project(project_path, dependencies):
            ui_components["shadcn_ui"] = self._scan_shadcn_ui_components(project_path)

        # Check for custom components
        ui_components["custom"] = self._scan_custom_components(project_path)

        # Check for third-party component libraries
        if "@mui/material" in dependencies:
            ui_components["third_party"].append("mui")
        if "antd" in dependencies:
            ui_components["third_party"].append("antd")
        if "@chakra-ui/react" in dependencies:
            ui_components["third_party"].append("chakra-ui")

        return ui_components

    def _get_available_utilities(self, project_path: str, dependencies: dict) -> Dict:
        """Get available utility functions and their import paths"""

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

        # Check for clsx
        if "clsx" in dependencies:
            utilities["clsx"] = True

        # Check for classnames
        if "classnames" in dependencies:
            utilities["classnames"] = True

        return utilities

    def _get_available_icons(self, dependencies: dict) -> List[str]:
        """Get available icon libraries"""

        icons = []

        if "lucide-react" in dependencies:
            icons.append("lucide-react")
        if "react-icons" in dependencies:
            icons.append("react-icons")
        if "@heroicons/react" in dependencies:
            icons.append("heroicons")

        return icons

    def _get_available_styling_utilities(self, dependencies: dict) -> List[str]:
        """Get available styling utilities"""

        styling = []

        if "tailwind-merge" in dependencies:
            styling.append("tailwind-merge")
        if "class-variance-authority" in dependencies:
            styling.append("class-variance-authority")

        return styling

    def _scan_shadcn_ui_components(self, project_path: str) -> List[str]:
        """Scan for available shadcn/ui components"""

        components = []
        ui_paths = [
            os.path.join(project_path, "components", "ui"),
            os.path.join(project_path, "src", "components", "ui"),
        ]

        for ui_path in ui_paths:
            if os.path.exists(ui_path):
                for file in os.listdir(ui_path):
                    if file.endswith((".tsx", ".ts", ".jsx", ".js")):
                        component_name = (
                            file.replace(".tsx", "")
                            .replace(".ts", "")
                            .replace(".jsx", "")
                            .replace(".js", "")
                        )
                        components.append(component_name)
                break

        return components

    def _scan_custom_components(self, project_path: str) -> List[str]:
        """Scan for custom components"""

        components = []
        component_paths = [
            os.path.join(project_path, "components"),
            os.path.join(project_path, "src", "components"),
        ]

        for comp_path in component_paths:
            if os.path.exists(comp_path):
                for root, dirs, files in os.walk(comp_path):
                    # Skip ui directory (handled separately)
                    if "ui" in dirs:
                        dirs.remove("ui")

                    for file in files:
                        if file.endswith((".tsx", ".ts", ".jsx", ".js")):
                            component_name = (
                                file.replace(".tsx", "")
                                .replace(".ts", "")
                                .replace(".jsx", "")
                                .replace(".js", "")
                            )
                            if component_name not in components:
                                components.append(component_name)
                break

        return components[:10]  # Limit to 10 components

    def _find_components_directory(self, project_path: str) -> Optional[str]:
        """Find the main components directory"""

        possible_dirs = ["src/components", "components", "app/components"]

        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path

        return "src/components"  # Default

    def _find_pages_directory(self, project_path: str) -> Optional[str]:
        """Find the pages directory"""

        possible_dirs = ["src/pages", "pages", "app", "src/app"]

        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path

        return "src/pages"  # Default

    def _find_styles_directory(self, project_path: str) -> Optional[str]:
        """Find the styles directory"""

        possible_dirs = ["src/styles", "styles", "src/css", "css"]

        for dir_path in possible_dirs:
            full_path = os.path.join(project_path, dir_path)
            if os.path.exists(full_path):
                return dir_path

        return "src/styles"  # Default


def test_css_file_finder():
    """Test function to verify CSS file finder and content aggregator work"""

    # Test with current directory
    analyzer = ProjectAnalyzer()
    css_files = analyzer.find_all_css_files(os.getcwd())

    print(f"Found CSS files: {css_files}")

    for css_file in css_files:
        print(f"- {css_file}")

    # Test content aggregator
    if css_files:
        print("\n--- Testing Content Aggregator ---")
        aggregated_content = analyzer.aggregate_css_content(css_files)
        print(f"Aggregated content length: {len(aggregated_content)} characters")
        print("First 200 characters:")
        print(aggregated_content[:200])
        print("...")

        # Test theme block extractor
        print("\n--- Testing Theme Block Extractor ---")
        theme_content = analyzer.extract_theme_blocks(aggregated_content)
        print(f"Theme content length: {len(theme_content)} characters")
        print("Theme content:")
        print(theme_content)

        # Test key-value parser
        print("\n--- Testing Key-Value Parser ---")
        theme_tokens = analyzer.parse_theme_tokens(theme_content)
        print(f"Parsed {len(theme_tokens)} theme tokens")
        print("Theme tokens dictionary:")
        for key, value in theme_tokens.items():
            print(f"  '{key}': '{value}'")

        return css_files, aggregated_content, theme_content, theme_tokens

    return css_files, "", "", {}

    # Additional methods for API endpoints
    def detect_framework(self) -> str:
        """Detect framework for current project"""
        if self.project_path:
            return self._detect_framework(self.project_path)
        return "unknown"
    
    def detect_styling_library(self) -> str:
        """Detect styling library for current project"""
        if self.project_path:
            return self._detect_styling_system(self.project_path)
        return "unknown"
    
    def has_typescript(self) -> bool:
        """Check if project uses TypeScript"""
        if not self.project_path:
            return False
        
        # Check for tsconfig.json
        if os.path.exists(os.path.join(self.project_path, "tsconfig.json")):
            return True
            
        # Check package.json for TypeScript dependency
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    return "typescript" in deps or "@types/node" in deps
            except:
                pass
                
        return False
    
    def detect_tailwind(self) -> bool:
        """Check if project uses Tailwind CSS"""
        if not self.project_path:
            return False
            
        # Check for tailwind config files
        config_files = ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"]
        for config_file in config_files:
            if os.path.exists(os.path.join(self.project_path, config_file)):
                return True
                
        # Check package.json for tailwindcss dependency
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    return "tailwindcss" in deps
            except:
                pass
                
        return False
    
    def detect_build_tool(self) -> str:
        """Detect build tool used in project"""
        if not self.project_path:
            return "unknown"
            
        # Check for config files
        if os.path.exists(os.path.join(self.project_path, "vite.config.js")) or \
           os.path.exists(os.path.join(self.project_path, "vite.config.ts")):
            return "vite"
        elif os.path.exists(os.path.join(self.project_path, "webpack.config.js")):
            return "webpack"
        elif os.path.exists(os.path.join(self.project_path, "next.config.js")):
            return "next"
        else:
            return "unknown"
    
    def detect_package_manager(self) -> str:
        """Detect package manager used in project"""
        if not self.project_path:
            return "unknown"
            
        if os.path.exists(os.path.join(self.project_path, "pnpm-lock.yaml")):
            return "pnpm"
        elif os.path.exists(os.path.join(self.project_path, "yarn.lock")):
            return "yarn"
        elif os.path.exists(os.path.join(self.project_path, "package-lock.json")):
            return "npm"
        else:
            return "npm"  # Default assumption

    # Public methods expected by FastAPI server
    def detect_framework(self) -> str:
        """Public method to detect framework - delegates to internal method"""
        if self.project_path:
            return self._detect_framework(self.project_path)
        return "unknown"
    
    def detect_styling_library(self) -> str:
        """Public method to detect styling library"""
        if self.project_path:
            styling_result = self._detect_styling_system(self.project_path)
            if isinstance(styling_result, dict):
                return styling_result.get("main", "unknown")
            return str(styling_result)
        return "unknown"
    
    def has_typescript(self) -> bool:
        """Public method to check if project uses TypeScript"""
        if not self.project_path:
            return False
            
        # Check for TypeScript config
        ts_configs = ["tsconfig.json", "tsconfig.app.json", "tsconfig.build.json"]
        for config in ts_configs:
            if os.path.exists(os.path.join(self.project_path, config)):
                return True
        
        # Check package.json for TypeScript dependency
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    return "typescript" in deps or "@types/react" in deps
            except:
                pass
                
        return False


if __name__ == "__main__":
    test_css_file_finder()
