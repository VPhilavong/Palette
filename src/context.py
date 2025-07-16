import os
import json
import re
import subprocess
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
        
        # Store the main CSS file path for debugging/info purposes
        self.main_css_file_path = None
    
    def analyze_project(self, project_path: str) -> Dict:
        """Extract design patterns for UI generation"""
        
        context = {
            'framework': self._detect_framework(project_path),
            'styling': self._detect_styling_system(project_path),
            'component_library': self._detect_component_library(project_path),
            'design_tokens': self._extract_design_tokens(project_path),
            'component_patterns': self._analyze_component_patterns(project_path),
            'project_structure': self._analyze_project_structure(project_path),
            'available_imports': self.get_available_imports(project_path),
            'main_css_file': self.main_css_file_path
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
        """Detect component library being used with proper validation"""
        
        package_json_path = os.path.join(project_path, 'package.json')
        if not os.path.exists(package_json_path):
            return 'none'
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                dependencies = {**package_data.get('dependencies', {}), 
                              **package_data.get('devDependencies', {})}
                
                # Check for shadcn/ui with proper validation
                if self._is_shadcn_ui_project(project_path, dependencies):
                    return 'shadcn/ui'
                
                # Check other component libraries
                for library, indicators in self.component_libraries.items():
                    if library == 'shadcn/ui':
                        continue  # Already checked above
                    
                    for indicator in indicators:
                        if indicator in dependencies:
                            return library
                        # Check for directory structure indicators
                        if indicator.endswith('/') and os.path.exists(os.path.join(project_path, indicator)):
                            return library
        except json.JSONDecodeError:
            pass
        
        return 'none'
    
    def _is_shadcn_ui_project(self, project_path: str, dependencies: dict) -> bool:
        """Validate if project actually has shadcn/ui setup"""
        
        # Check for shadcn/ui indicators in dependencies
        shadcn_indicators = ['@radix-ui', 'class-variance-authority', 'clsx', 'tailwind-merge']
        has_shadcn_deps = any(indicator in dep for dep in dependencies.keys() for indicator in shadcn_indicators)
        
        # Check for required directory structure
        components_ui_path = os.path.join(project_path, 'components', 'ui')
        lib_utils_path = os.path.join(project_path, 'lib', 'utils.ts')
        
        # Alternative paths
        src_components_ui_path = os.path.join(project_path, 'src', 'components', 'ui')
        src_lib_utils_path = os.path.join(project_path, 'src', 'lib', 'utils.ts')
        
        has_components_ui = os.path.exists(components_ui_path) or os.path.exists(src_components_ui_path)
        has_lib_utils = os.path.exists(lib_utils_path) or os.path.exists(src_lib_utils_path)
        
        # Only return true if both dependencies and structure exist
        return has_shadcn_deps and has_components_ui and has_lib_utils
    
    def _extract_design_tokens(self, project_path: str) -> Dict:
        """Extract design tokens from Tailwind config and existing components"""
        
        # First, try to get tokens from tailwind.config.js
        tailwind_config = self._parse_tailwind_config(project_path)
        
        # Extract colors with semantic structure
        color_data = self._extract_colors_from_config(tailwind_config, project_path)
        
        tokens = {
            'colors': color_data['custom'],  # For backward compatibility
            'semantic_colors': color_data['semantic'],  # New semantic colors
            'color_structure': color_data['structure'],  # Full color structure
            'spacing': self._extract_spacing_from_config(tailwind_config, project_path),
            'typography': self._extract_typography_from_config(tailwind_config, project_path),
            'shadows': self._extract_shadows_from_config(tailwind_config),
            'border_radius': self._extract_border_radius_from_config(tailwind_config)
        }
        
        return tokens
    
    def _parse_tailwind_config(self, project_path: str) -> Dict:
        """Parse tailwind.config.js using Node.js helper script or CSS parsing"""
        
        # Look for Tailwind config files
        config_files = ['tailwind.config.js', 'tailwind.config.ts', 'tailwind.config.mjs']
        config_path = None
        
        for config_file in config_files:
            potential_path = os.path.join(project_path, config_file)
            if os.path.exists(potential_path):
                config_path = potential_path
                break
        
        if config_path:
            # Use Node.js parser for JS config files
            return self._parse_js_config(config_path, project_path)
        else:
            # Fallback to CSS parsing mode
            print("Info: tailwind.config.js not found, trying CSS parsing mode...")
            return self._parse_css_for_theme(project_path)
    
    def _parse_js_config(self, config_path: str, project_path: str) -> Dict:
        """Parse JavaScript config file using Node.js helper script"""
        
        try:
            # Get the path to our Node.js helper script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parser_script = os.path.join(script_dir, 'tailwind_parser.js')
            
            # Run the Node.js script to parse the config
            result = subprocess.run(
                ['node', parser_script, config_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    parsed_config = json.loads(result.stdout)
                    return parsed_config
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse JSON from tailwind parser")
                    return {}
            else:
                print(f"Warning: Tailwind parser failed: {result.stderr}")
                return {}
                
        except subprocess.TimeoutExpired:
            print("Warning: Tailwind config parsing timed out")
            return {}
        except FileNotFoundError:
            print("Warning: Node.js not found. Install Node.js to enable advanced Tailwind config parsing.")
            return {}
        except Exception as e:
            print(f"Warning: Error parsing Tailwind config: {e}")
            return {}
    
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
        
        # Step 4: Parse theme tokens
        theme_tokens = self.parse_theme_tokens(theme_content)
        
        # Step 5: Structure the data like a tailwind.config.js would
        return self._structure_css_theme_tokens(theme_tokens)
    
    def _find_main_css_file(self, project_path: str) -> Optional[str]:
        """Find the main CSS entry point by recursively searching all subdirectories"""
        
        # Common CSS file names to look for (prioritized by importance)
        css_filenames = [
            'style.css',
            'styles.css', 
            'globals.css',
            'global.css',
            'tailwind.css',
            'app.css',
            'main.css'
        ]
        
        # First, try the predefined paths for faster lookup
        predefined_candidates = [
            'style.css',
            'styles.css', 
            'globals.css',
            'global.css',
            'tailwind.css',
            'app.css',
            'main.css',
            'src/styles.css',
            'src/style.css',
            'src/globals.css',
            'styles/globals.css',
            'styles/style.css',
            'app/globals.css',
            'app/css/style.css',
            'app/css/styles.css',
            'test_css/style.css',
            'test_css/styles.css',
            'css/style.css',
            'css/styles.css'
        ]
        
        for candidate in predefined_candidates:
            css_path = os.path.join(project_path, candidate)
            if os.path.exists(css_path):
                return css_path
        
        # If no predefined paths work, recursively search through all directories
        print(f"Info: No CSS file found in common locations, searching recursively...")
        
        for root, dirs, files in os.walk(project_path):
            # Skip common directories that shouldn't contain main CSS files
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.next', 'dist', 'build', '__pycache__', '.vscode']]
            
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
            imported_files = self._extract_imports_from_css_file(current_file, project_path)
            
            # Add new files to process queue
            for imported_file in imported_files:
                if imported_file not in visited_files:
                    files_to_process.append(imported_file)
        
        print(f"Info: Found {len(all_css_files)} CSS files total")
        return all_css_files
    
    def _extract_imports_from_css_file(self, css_file_path: str, project_path: str) -> List[str]:
        """Extract @import statements from a CSS file and return absolute paths"""
        
        imported_files = []
        
        try:
            with open(css_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all @import statements
            import_pattern = r'@import\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)
            
            for import_path in imports:
                # Resolve relative paths
                if import_path.startswith('./') or import_path.startswith('../'):
                    # Relative to current CSS file
                    base_dir = os.path.dirname(css_file_path)
                    resolved_path = os.path.normpath(os.path.join(base_dir, import_path))
                else:
                    # Relative to project root
                    resolved_path = os.path.join(project_path, import_path)
                
                # Only include if file exists
                if os.path.exists(resolved_path):
                    imported_files.append(resolved_path)
                else:
                    print(f"Warning: Import not found: {import_path} -> {resolved_path}")
                    
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
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add a comment header to identify the source file
                file_name = os.path.basename(css_file_path)
                header = f"\n/* === Content from {file_name} === */\n"
                
                combined_content.append(header)
                combined_content.append(content)
                combined_content.append("\n")  # Add spacing between files
                
                print(f"Info: Added content from {css_file_path} ({len(content)} characters)")
                
            except Exception as e:
                print(f"Warning: Error reading CSS file {css_file_path}: {e}")
                continue
        
        # Join all content into a single string
        aggregated_content = ''.join(combined_content)
        
        print(f"Info: Aggregated {len(css_file_paths)} CSS files into {len(aggregated_content)} characters")
        
        return aggregated_content
    
    def extract_theme_blocks(self, css_content: str) -> str:
        """Extract content from @theme { ... } blocks using regex"""
        
        if not css_content:
            print("Info: No CSS content to extract theme blocks from")
            return ""
        
        # Pattern to match @theme { ... } blocks
        # Uses DOTALL flag to match newlines and handles nested braces
        pattern = r'@theme\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        # Find all @theme blocks
        theme_matches = re.findall(pattern, css_content, re.DOTALL)
        
        if not theme_matches:
            print("Info: No @theme blocks found in CSS content")
            return ""
        
        print(f"Info: Found {len(theme_matches)} @theme blocks")
        
        # Combine all theme block contents
        combined_theme_content = []
        
        for i, theme_content in enumerate(theme_matches):
            theme_content = theme_content.strip()
            print(f"Info: Theme block {i+1}: {len(theme_content)} characters")
            combined_theme_content.append(theme_content)
        
        # Join all theme blocks with newlines
        result = '\n'.join(combined_theme_content)
        
        print(f"Info: Extracted {len(result)} characters from @theme blocks")
        
        return result
    
    def parse_theme_tokens(self, theme_content: str) -> Dict[str, str]:
        """Parse theme block content into a dictionary of key-value pairs"""
        
        if not theme_content:
            print("Info: No theme content to parse")
            return {}
        
        theme_tokens = {}
        
        # Split content into lines and process each line
        lines = theme_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('/*') or line.startswith('//'):
                continue
            
            # Parse CSS custom properties (--variable: value;)
            css_var_match = re.match(r'--([^:]+):\s*([^;]+);?', line)
            if css_var_match:
                key = css_var_match.group(1).strip()
                value = css_var_match.group(2).strip()
                
                # Remove outer quotes from string values (but keep inner quotes)
                # Don't remove quotes if they're part of a CSS value like font-family
                if (value.startswith('"') and value.endswith('"') and 
                    value.count('"') == 2):
                    value = value[1:-1]
                elif (value.startswith("'") and value.endswith("'") and 
                      value.count("'") == 2):
                    value = value[1:-1]
                
                theme_tokens[key] = value
                continue
            
            # Parse regular CSS properties (property: value;)
            css_prop_match = re.match(r'([a-zA-Z][a-zA-Z0-9-]*)\s*:\s*([^;]+);?', line)
            if css_prop_match:
                key = css_prop_match.group(1).strip()
                value = css_prop_match.group(2).strip()
                
                # Remove outer quotes from string values (but keep inner quotes)
                # Don't remove quotes if they're part of a CSS value like font-family
                if (value.startswith('"') and value.endswith('"') and 
                    value.count('"') == 2):
                    value = value[1:-1]
                elif (value.startswith("'") and value.endswith("'") and 
                      value.count("'") == 2):
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
    
    def _structure_css_theme_tokens(self, theme_tokens: Dict[str, str]) -> Dict:
        """Structure CSS theme tokens like a tailwind.config.js would"""
        
        if not theme_tokens:
            return {}
        
        # Separate tokens by category
        colors = {}
        fonts = {}
        spacing = {}
        other = {}
        
        for key, value in theme_tokens.items():
            # Categorize tokens based on key names
            if any(color_word in key.lower() for color_word in ['color', 'primary', 'secondary', 'accent', 'background', 'foreground', 'muted', 'border', 'text']):
                # Remove color- prefix if present
                color_key = key.replace('color-', '') if key.startswith('color-') else key
                colors[color_key] = value
            elif any(font_word in key.lower() for font_word in ['font', 'family', 'size', 'weight']):
                # Remove font- prefix if present
                font_key = key.replace('font-', '') if key.startswith('font-') else key
                fonts[font_key] = value
            elif any(spacing_word in key.lower() for spacing_word in ['spacing', 'size', 'width', 'height', 'margin', 'padding']):
                # Remove spacing- prefix if present
                spacing_key = key.replace('spacing-', '') if key.startswith('spacing-') else key
                spacing[spacing_key] = value
            else:
                other[key] = value
        
        # Structure like tailwind.config.js
        structured_data = {
            'colors': colors,
            'fontFamily': fonts,
            'fontSize': {k: v for k, v in fonts.items() if 'size' in k.lower()},
            'spacing': spacing,
            'extend': {
                'colors': colors,
                'fontFamily': fonts,
                'spacing': spacing
            }
        }
        
        print(f"Info: Structured {len(colors)} colors, {len(fonts)} fonts, {len(spacing)} spacing tokens")
        
        return structured_data
    
    def _collect_all_css_files(self, main_css_file: str, project_path: str) -> List[str]:
        """Collect all CSS files by following @import statements"""
        
        css_files = [main_css_file]
        visited = set()
        
        def process_file(file_path: str):
            if file_path in visited:
                return
            visited.add(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all @import statements
                import_pattern = r'@import\s+[\'"]([^\'\"]+)[\'"]'
                imports = re.findall(import_pattern, content)
                
                for import_path in imports:
                    # Resolve relative paths
                    if import_path.startswith('./') or import_path.startswith('../'):
                        base_dir = os.path.dirname(file_path)
                        resolved_path = os.path.normpath(os.path.join(base_dir, import_path))
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
        
        theme_data = {
            'colors': {},
            'fonts': {},
            'spacing': {},
            'other': {}
        }
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
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
        pattern = r'@theme\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        matches = re.findall(pattern, css_content, re.DOTALL)
        
        return matches
    
    def _parse_theme_block(self, theme_block: str, theme_data: Dict):
        """Parse a @theme block and extract key-value pairs"""
        
        # Parse CSS custom properties (--variable: value;)
        css_var_pattern = r'--([^:]+):\s*([^;]+);'
        css_vars = re.findall(css_var_pattern, theme_block)
        
        # Parse regular CSS properties (property: value;)
        css_prop_pattern = r'([a-zA-Z-]+):\s*([^;]+);'
        css_props = re.findall(css_prop_pattern, theme_block)
        
        # Process CSS variables
        for var_name, var_value in css_vars:
            var_name = var_name.strip()
            var_value = var_value.strip()
            
            if 'color' in var_name:
                theme_data['colors'][var_name.replace('color-', '')] = var_value
            elif 'font' in var_name:
                theme_data['fonts'][var_name.replace('font-', '')] = var_value
            elif any(spacing_word in var_name for spacing_word in ['spacing', 'size', 'width', 'height']):
                theme_data['spacing'][var_name] = var_value
            else:
                theme_data['other'][var_name] = var_value
        
        # Process regular CSS properties
        for prop_name, prop_value in css_props:
            prop_name = prop_name.strip()
            prop_value = prop_value.strip()
            
            if prop_name in ['primary', 'secondary', 'accent', 'background', 'foreground']:
                theme_data['colors'][prop_name] = prop_value
            elif 'font' in prop_name:
                theme_data['fonts'][prop_name] = prop_value
            else:
                theme_data['other'][prop_name] = prop_value
    
    def _structure_css_theme_data(self, theme_data: Dict) -> Dict:
        """Structure CSS theme data like a tailwind.config.js would"""
        
        structured_data = {
            'colors': {},
            'fontSize': {},
            'fontFamily': {},
            'spacing': {},
            'extend': {
                'colors': theme_data['colors'],
                'fontFamily': theme_data['fonts']
            }
        }
        
        # Add colors to both main and extended
        structured_data['colors'] = theme_data['colors']
        
        # Add font data
        structured_data['fontFamily'] = theme_data['fonts']
        
        # Add spacing data
        structured_data['spacing'] = theme_data['spacing']
        
        return structured_data
    
    def _extract_colors_from_config(self, tailwind_config: Dict, project_path: str) -> Dict:
        """Extract color palette from parsed Tailwind config with detailed structure"""
        
        colors = {
            'semantic': [],  # bg-primary, text-foreground style
            'custom': [],    # Custom color names
            'structure': {}  # Full color structure for reference
        }
        
        # Get colors from config
        if 'colors' in tailwind_config and tailwind_config['colors']:
            config_colors = tailwind_config['colors']
            colors['structure'].update(config_colors)
            
            # Extract color names, prioritizing custom colors
            for color_name, color_value in config_colors.items():
                if isinstance(color_value, dict) or isinstance(color_value, str):
                    colors['custom'].append(color_name)
                    
                # All CSS-parsed colors are semantic (single values)
                if isinstance(color_value, str):
                    colors['semantic'].append(color_name)
        
        # Get extended colors (most important for custom themes)
        if 'extend' in tailwind_config and 'colors' in tailwind_config['extend']:
            extend_colors = tailwind_config['extend']['colors']
            colors['structure'].update(extend_colors)
            
            for color_name, color_value in extend_colors.items():
                if color_name not in colors['custom']:
                    colors['custom'].append(color_name)
                    
                # All CSS-parsed colors are semantic (single values)
                if isinstance(color_value, str):
                    colors['semantic'].append(color_name)
        
        # Fallback to regex-based extraction if no colors found
        if not colors['custom']:
            fallback_colors = self._extract_tailwind_colors_fallback(project_path)
            colors['custom'] = fallback_colors
        
        # Default colors if still none found
        if not colors['custom']:
            colors['custom'] = ['blue', 'gray', 'green', 'red', 'yellow']
        
        print(f"Info: Found {len(colors['custom'])} custom colors, {len(colors['semantic'])} semantic colors")
        
        return colors
    
    def _extract_tailwind_colors_fallback(self, project_path: str) -> List[str]:
        """Fallback method: Extract color palette from Tailwind config using regex"""
        
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
        
        return colors
    
    def _extract_spacing_from_config(self, tailwind_config: Dict, project_path: str) -> List[str]:
        """Extract spacing patterns from parsed Tailwind config"""
        
        spacing = []
        
        # Get spacing from config
        if 'spacing' in tailwind_config and tailwind_config['spacing']:
            config_spacing = tailwind_config['spacing']
            
            # Extract numeric spacing values
            for spacing_key in config_spacing.keys():
                if spacing_key.isdigit():
                    spacing.append(spacing_key)
        
        # Get extended spacing
        if 'extend' in tailwind_config and 'spacing' in tailwind_config['extend']:
            extend_spacing = tailwind_config['extend']['spacing']
            for spacing_key in extend_spacing.keys():
                if spacing_key.isdigit() and spacing_key not in spacing:
                    spacing.append(spacing_key)
        
        # Fallback to component analysis if no spacing found
        if not spacing:
            spacing = self._extract_spacing_patterns(project_path)
        
        # Default spacing if still none found
        if not spacing:
            spacing = ['2', '4', '6', '8', '12', '16']
        
        return spacing[:8]  # Limit to 8 spacing values
    
    def _extract_typography_from_config(self, tailwind_config: Dict, project_path: str) -> List[str]:
        """Extract typography scale from parsed Tailwind config"""
        
        typography = []
        
        # Get font sizes from config
        if 'fontSize' in tailwind_config and tailwind_config['fontSize']:
            config_font_sizes = tailwind_config['fontSize']
            
            # Extract font size names
            for font_size_name in config_font_sizes.keys():
                typography.append(font_size_name)
        
        # Get extended font sizes
        if 'extend' in tailwind_config and 'fontSize' in tailwind_config['extend']:
            extend_font_sizes = tailwind_config['extend']['fontSize']
            for font_size_name in extend_font_sizes.keys():
                if font_size_name not in typography:
                    typography.append(font_size_name)
        
        # Fallback to component analysis if no typography found
        if not typography:
            typography = self._extract_typography_scale(project_path)
        
        # Default typography if still none found
        if not typography:
            typography = ['sm', 'base', 'lg', 'xl', '2xl']
        
        return typography[:8]  # Limit to 8 typography values
    
    def _extract_shadows_from_config(self, tailwind_config: Dict) -> List[str]:
        """Extract shadow patterns from parsed Tailwind config"""
        
        shadows = []
        
        # Get shadows from config
        if 'boxShadow' in tailwind_config and tailwind_config['boxShadow']:
            config_shadows = tailwind_config['boxShadow']
            
            # Extract shadow names
            for shadow_name in config_shadows.keys():
                shadows.append(shadow_name)
        
        # Get extended shadows
        if 'extend' in tailwind_config and 'boxShadow' in tailwind_config['extend']:
            extend_shadows = tailwind_config['extend']['boxShadow']
            for shadow_name in extend_shadows.keys():
                if shadow_name not in shadows:
                    shadows.append(shadow_name)
        
        # Default shadows if none found
        if not shadows:
            shadows = ['sm', 'md', 'lg', 'xl']
        
        return shadows[:6]  # Limit to 6 shadow values
    
    def _extract_border_radius_from_config(self, tailwind_config: Dict) -> List[str]:
        """Extract border radius patterns from parsed Tailwind config"""
        
        border_radius = []
        
        # Get border radius from config
        if 'borderRadius' in tailwind_config and tailwind_config['borderRadius']:
            config_border_radius = tailwind_config['borderRadius']
            
            # Extract border radius names
            for radius_name in config_border_radius.keys():
                border_radius.append(radius_name)
        
        # Get extended border radius
        if 'extend' in tailwind_config and 'borderRadius' in tailwind_config['extend']:
            extend_border_radius = tailwind_config['extend']['borderRadius']
            for radius_name in extend_border_radius.keys():
                if radius_name not in border_radius:
                    border_radius.append(radius_name)
        
        # Default border radius if none found
        if not border_radius:
            border_radius = ['sm', 'md', 'lg', 'xl']
        
        return border_radius[:6]  # Limit to 6 border radius values
    
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
    
    def get_available_imports(self, project_path: str) -> Dict:
        """Get available imports and dependencies for component generation"""
        
        package_json_path = os.path.join(project_path, 'package.json')
        dependencies = {}
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get('dependencies', {}), 
                                  **package_data.get('devDependencies', {})}
            except json.JSONDecodeError:
                pass
        
        available_imports = {
            'react_hooks': self._get_available_react_hooks(dependencies),
            'ui_components': self._get_available_ui_components(project_path, dependencies),
            'utilities': self._get_available_utilities(project_path, dependencies),
            'icons': self._get_available_icons(dependencies),
            'styling': self._get_available_styling_utilities(dependencies)
        }
        
        return available_imports
    
    def _get_available_react_hooks(self, dependencies: dict) -> List[str]:
        """Get available React hooks based on React version"""
        
        basic_hooks = ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo', 'useRef']
        
        if 'react' in dependencies:
            # All modern React versions support these hooks
            return basic_hooks
        
        return []
    
    def _get_available_ui_components(self, project_path: str, dependencies: dict) -> Dict:
        """Get available UI components and their import paths"""
        
        ui_components = {
            'shadcn_ui': [],
            'custom': [],
            'third_party': []
        }
        
        # Check for shadcn/ui components
        if self._is_shadcn_ui_project(project_path, dependencies):
            ui_components['shadcn_ui'] = self._scan_shadcn_ui_components(project_path)
        
        # Check for custom components
        ui_components['custom'] = self._scan_custom_components(project_path)
        
        # Check for third-party component libraries
        if '@mui/material' in dependencies:
            ui_components['third_party'].append('mui')
        if 'antd' in dependencies:
            ui_components['third_party'].append('antd')
        if '@chakra-ui/react' in dependencies:
            ui_components['third_party'].append('chakra-ui')
        
        return ui_components
    
    def _get_available_utilities(self, project_path: str, dependencies: dict) -> Dict:
        """Get available utility functions and their import paths"""
        
        utilities = {
            'cn': False,
            'clsx': False,
            'classnames': False,
            'custom_utils': []
        }
        
        # Check for cn utility (shadcn/ui)
        lib_utils_paths = [
            os.path.join(project_path, 'lib', 'utils.ts'),
            os.path.join(project_path, 'src', 'lib', 'utils.ts'),
            os.path.join(project_path, 'lib', 'utils.js'),
            os.path.join(project_path, 'src', 'lib', 'utils.js')
        ]
        
        for path in lib_utils_paths:
            if os.path.exists(path):
                utilities['cn'] = True
                break
        
        # Check for clsx
        if 'clsx' in dependencies:
            utilities['clsx'] = True
        
        # Check for classnames
        if 'classnames' in dependencies:
            utilities['classnames'] = True
        
        return utilities
    
    def _get_available_icons(self, dependencies: dict) -> List[str]:
        """Get available icon libraries"""
        
        icons = []
        
        if 'lucide-react' in dependencies:
            icons.append('lucide-react')
        if 'react-icons' in dependencies:
            icons.append('react-icons')
        if '@heroicons/react' in dependencies:
            icons.append('heroicons')
        
        return icons
    
    def _get_available_styling_utilities(self, dependencies: dict) -> List[str]:
        """Get available styling utilities"""
        
        styling = []
        
        if 'tailwind-merge' in dependencies:
            styling.append('tailwind-merge')
        if 'class-variance-authority' in dependencies:
            styling.append('class-variance-authority')
        
        return styling
    
    def _scan_shadcn_ui_components(self, project_path: str) -> List[str]:
        """Scan for available shadcn/ui components"""
        
        components = []
        ui_paths = [
            os.path.join(project_path, 'components', 'ui'),
            os.path.join(project_path, 'src', 'components', 'ui')
        ]
        
        for ui_path in ui_paths:
            if os.path.exists(ui_path):
                for file in os.listdir(ui_path):
                    if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                        component_name = file.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
                        components.append(component_name)
                break
        
        return components
    
    def _scan_custom_components(self, project_path: str) -> List[str]:
        """Scan for custom components"""
        
        components = []
        component_paths = [
            os.path.join(project_path, 'components'),
            os.path.join(project_path, 'src', 'components')
        ]
        
        for comp_path in component_paths:
            if os.path.exists(comp_path):
                for root, dirs, files in os.walk(comp_path):
                    # Skip ui directory (handled separately)
                    if 'ui' in dirs:
                        dirs.remove('ui')
                    
                    for file in files:
                        if file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                            component_name = file.replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
                            if component_name not in components:
                                components.append(component_name)
                break
        
        return components[:10]  # Limit to 10 components
    
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

if __name__ == '__main__':
    test_css_file_finder()