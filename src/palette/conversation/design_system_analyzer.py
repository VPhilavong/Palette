"""
Design System Pattern Recognition and Analysis

This module analyzes existing codebases to extract design system patterns,
component structures, and styling conventions for better contextual generation.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from collections import defaultdict, Counter

@dataclass 
class DesignToken:
    """Represents a design token (color, spacing, typography, etc.)"""
    name: str
    value: str
    category: str  # 'color', 'spacing', 'typography', 'shadow', etc.
    usage_count: int = 0
    context: List[str] = None

    def __post_init__(self):
        if self.context is None:
            self.context = []

@dataclass
class ComponentPattern:
    """Represents a component pattern found in the codebase"""
    name: str
    props: List[str]
    variants: List[str]
    styling_patterns: List[str]
    usage_examples: List[str]
    file_path: str

@dataclass
class DesignSystemProfile:
    """Complete design system profile of a project"""
    framework: str
    styling_system: str
    tokens: Dict[str, List[DesignToken]]
    components: Dict[str, ComponentPattern]
    naming_conventions: Dict[str, str]
    common_patterns: List[str]


class DesignSystemAnalyzer:
    """Analyzes codebase to extract design system patterns"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.design_profile: Optional[DesignSystemProfile] = None
        
        # Common design system file patterns
        self.design_files = [
            'tailwind.config.js', 'tailwind.config.ts',
            'theme.ts', 'theme.js', 'tokens.ts', 'tokens.js',
            'design-tokens.json', 'design-system.ts',
            'globals.css', 'index.css', 'styles.css'
        ]
        
        # Component file patterns
        self.component_patterns = [
            'components/**/*.{tsx,ts,jsx,js}',
            'src/components/**/*.{tsx,ts,jsx,js}',
            'app/components/**/*.{tsx,ts,jsx,js}',
            'ui/**/*.{tsx,ts,jsx,js}',
            'src/ui/**/*.{tsx,ts,jsx,js}'
        ]

    def analyze_design_system(self) -> DesignSystemProfile:
        """Analyze the entire design system of the project"""
        print("🎨 Analyzing design system patterns...")
        
        # Detect framework and styling system
        framework = self._detect_framework()
        styling_system = self._detect_styling_system()
        
        # Extract design tokens
        tokens = self._extract_design_tokens()
        
        # Analyze components
        components = self._analyze_components()
        
        # Extract naming conventions
        naming_conventions = self._analyze_naming_conventions(components)
        
        # Identify common patterns
        common_patterns = self._identify_common_patterns(components)
        
        self.design_profile = DesignSystemProfile(
            framework=framework,
            styling_system=styling_system,
            tokens=tokens,
            components=components,
            naming_conventions=naming_conventions,
            common_patterns=common_patterns
        )
        
        return self.design_profile

    def _detect_framework(self) -> str:
        """Detect the UI framework being used"""
        package_json = self.project_path / 'package.json'
        
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if 'next' in deps:
                    return 'next.js'
                elif 'react' in deps:
                    return 'react'
                elif 'vue' in deps:
                    return 'vue'
                elif '@angular/core' in deps:
                    return 'angular'
                
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return 'unknown'

    def _detect_styling_system(self) -> str:
        """Detect the styling system being used"""
        # Check for Tailwind
        tailwind_config = self.project_path / 'tailwind.config.js'
        if tailwind_config.exists() or (self.project_path / 'tailwind.config.ts').exists():
            return 'tailwind'
        
        # Check package.json for styling libraries
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                
                if '@emotion/react' in deps or '@emotion/styled' in deps:
                    return 'emotion'
                elif 'styled-components' in deps:
                    return 'styled-components'
                elif 'sass' in deps or 'scss' in deps:
                    return 'sass'
                
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Check for CSS modules
        if list(self.project_path.glob('**/*.module.css')):
            return 'css-modules'
        
        return 'css'

    def _extract_design_tokens(self) -> Dict[str, List[DesignToken]]:
        """Extract design tokens from various sources"""
        tokens = defaultdict(list)
        
        # Extract from Tailwind config
        tailwind_tokens = self._extract_tailwind_tokens()
        for category, token_list in tailwind_tokens.items():
            tokens[category].extend(token_list)
        
        # Extract from CSS custom properties
        css_tokens = self._extract_css_tokens()
        for category, token_list in css_tokens.items():
            tokens[category].extend(token_list)
        
        # Extract from theme files
        theme_tokens = self._extract_theme_tokens()
        for category, token_list in theme_tokens.items():
            tokens[category].extend(token_list)
        
        return dict(tokens)

    def _extract_tailwind_tokens(self) -> Dict[str, List[DesignToken]]:
        """Extract tokens from Tailwind config"""
        tokens = defaultdict(list)
        
        config_files = ['tailwind.config.js', 'tailwind.config.ts']
        
        for config_file in config_files:
            config_path = self.project_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    # Extract colors
                    color_matches = re.findall(r'(\w+):\s*[\'"]([^\'\"]+)[\'"]', content)
                    for name, value in color_matches:
                        if self._looks_like_color(value):
                            tokens['color'].append(DesignToken(
                                name=name,
                                value=value,
                                category='color'
                            ))
                    
                    # Extract spacing
                    spacing_matches = re.findall(r'spacing:\s*{([^}]+)}', content, re.DOTALL)
                    if spacing_matches:
                        spacing_content = spacing_matches[0]
                        space_tokens = re.findall(r'(\w+):\s*[\'"]([^\'\"]+)[\'"]', spacing_content)
                        for name, value in space_tokens:
                            tokens['spacing'].append(DesignToken(
                                name=name,
                                value=value,
                                category='spacing'
                            ))
                    
                except FileNotFoundError:
                    continue
        
        return dict(tokens)

    def _extract_css_tokens(self) -> Dict[str, List[DesignToken]]:
        """Extract design tokens from CSS custom properties"""
        tokens = defaultdict(list)
        
        css_files = []
        for pattern in ['**/*.css', '**/*.scss', '**/*.sass']:
            css_files.extend(self.project_path.glob(pattern))
        
        for css_file in css_files[:10]:  # Limit to first 10 files for performance
            # Skip directories and non-readable files
            if css_file.is_dir() or not css_file.is_file():
                continue
            
            try:
                with open(css_file, 'r') as f:
                    content = f.read()
                
                # Extract CSS custom properties
                custom_props = re.findall(r'--([^:]+):\s*([^;]+);', content)
                
                for name, value in custom_props:
                    name = name.strip()
                    value = value.strip()
                    
                    category = self._categorize_token(name, value)
                    tokens[category].append(DesignToken(
                        name=name,
                        value=value,
                        category=category,
                        context=[str(css_file)]
                    ))
                    
            except (UnicodeDecodeError, FileNotFoundError):
                continue
        
        return dict(tokens)

    def _extract_theme_tokens(self) -> Dict[str, List[DesignToken]]:
        """Extract tokens from theme files"""
        tokens = defaultdict(list)
        
        theme_files = ['theme.ts', 'theme.js', 'tokens.ts', 'tokens.js']
        
        for theme_file in theme_files:
            theme_path = self.project_path / theme_file
            if theme_path.exists():
                try:
                    with open(theme_path, 'r') as f:
                        content = f.read()
                    
                    # Simple extraction of object properties
                    # This could be enhanced with actual JS/TS parsing
                    prop_matches = re.findall(r'(\w+):\s*[\'"]([^\'\"]+)[\'"]', content)
                    
                    for name, value in prop_matches:
                        category = self._categorize_token(name, value)
                        tokens[category].append(DesignToken(
                            name=name,
                            value=value,
                            category=category,
                            context=[theme_file]
                        ))
                        
                except FileNotFoundError:
                    continue
        
        return dict(tokens)

    def _analyze_components(self) -> Dict[str, ComponentPattern]:
        """Analyze component patterns in the codebase"""
        components = {}
        
        # Find component files
        component_files = []
        for pattern in self.component_patterns:
            component_files.extend(self.project_path.glob(pattern))
        
        for component_file in component_files[:20]:  # Limit for performance
            # Skip directories and non-readable files
            if component_file.is_dir() or not component_file.is_file():
                continue
            
            try:
                with open(component_file, 'r') as f:
                    content = f.read()
                
                component_pattern = self._analyze_single_component(content, str(component_file))
                if component_pattern:
                    components[component_pattern.name] = component_pattern
                    
            except (UnicodeDecodeError, FileNotFoundError):
                continue
        
        return components

    def _analyze_single_component(self, content: str, file_path: str) -> Optional[ComponentPattern]:
        """Analyze a single component file"""
        # Extract component name from file path or content
        file_name = Path(file_path).stem
        component_name = file_name
        
        # Look for React component definition
        component_match = re.search(
            r'(?:export\s+(?:default\s+)?(?:const|function)\s+|const\s+)(\w+)\s*[=:]', 
            content
        )
        if component_match:
            component_name = component_match.group(1)
        
        # Extract props interface
        props = self._extract_component_props(content)
        
        # Extract variants (common prop patterns)
        variants = self._extract_component_variants(content)
        
        # Extract styling patterns
        styling_patterns = self._extract_styling_patterns(content)
        
        # Extract usage examples from comments or stories
        usage_examples = self._extract_usage_examples(content)
        
        return ComponentPattern(
            name=component_name,
            props=props,
            variants=variants,
            styling_patterns=styling_patterns,
            usage_examples=usage_examples,
            file_path=file_path
        )

    def _extract_component_props(self, content: str) -> List[str]:
        """Extract component props from TypeScript interfaces"""
        props = []
        
        # Look for interface definitions
        interface_matches = re.findall(
            r'interface\s+\w*Props\s*{([^}]+)}', 
            content, 
            re.DOTALL
        )
        
        for interface_content in interface_matches:
            prop_matches = re.findall(r'(\w+)\??:', interface_content)
            props.extend(prop_matches)
        
        # Also look for destructured props
        destructure_matches = re.findall(
            r'{\s*([^}]+)\s*}\s*:\s*\w*Props', 
            content
        )
        
        for destructure_content in destructure_matches:
            prop_names = [p.strip() for p in destructure_content.split(',')]
            props.extend(prop_names)
        
        return list(set(props))  # Remove duplicates

    def _extract_component_variants(self, content: str) -> List[str]:
        """Extract component variants (size, color, etc.)"""
        variants = []
        
        # Look for variant prop patterns
        variant_patterns = [
            r'variant:\s*[\'"](\w+)[\'"]',
            r'size:\s*[\'"](\w+)[\'"]',
            r'color:\s*[\'"](\w+)[\'"]',
            r'type:\s*[\'"](\w+)[\'"]'
        ]
        
        for pattern in variant_patterns:
            matches = re.findall(pattern, content)
            variants.extend(matches)
        
        return list(set(variants))

    def _extract_styling_patterns(self, content: str) -> List[str]:
        """Extract styling patterns used in the component"""
        patterns = []
        
        # Extract Tailwind classes
        tailwind_matches = re.findall(r'className\s*=\s*[\'"]([^\'\"]+)[\'"]', content)
        for match in tailwind_matches:
            patterns.extend(match.split())
        
        # Extract styled-components patterns
        styled_matches = re.findall(r'styled\.\w+`([^`]+)`', content, re.DOTALL)
        patterns.extend(styled_matches)
        
        return list(set(patterns))

    def _extract_usage_examples(self, content: str) -> List[str]:
        """Extract usage examples from comments or JSDoc"""
        examples = []
        
        # Look for example comments
        example_matches = re.findall(r'@example\s+([^\n]+)', content)
        examples.extend(example_matches)
        
        # Look for usage in comments
        usage_matches = re.findall(r'//\s*Usage:\s*([^\n]+)', content)
        examples.extend(usage_matches)
        
        return examples

    def _analyze_naming_conventions(self, components: Dict[str, ComponentPattern]) -> Dict[str, str]:
        """Analyze naming conventions used in the codebase"""
        conventions = {}
        
        component_names = list(components.keys())
        
        # Analyze case patterns
        if component_names:
            pascal_case = sum(1 for name in component_names if name[0].isupper() and '_' not in name)
            camel_case = sum(1 for name in component_names if name[0].islower() and '_' not in name)
            snake_case = sum(1 for name in component_names if '_' in name)
            
            if pascal_case > camel_case and pascal_case > snake_case:
                conventions['component_naming'] = 'PascalCase'
            elif camel_case > pascal_case and camel_case > snake_case:
                conventions['component_naming'] = 'camelCase'
            else:
                conventions['component_naming'] = 'snake_case'
        
        # Analyze prop patterns
        all_props = []
        for component in components.values():
            all_props.extend(component.props)
        
        if all_props:
            camel_props = sum(1 for prop in all_props if prop[0].islower() and '_' not in prop)
            snake_props = sum(1 for prop in all_props if '_' in prop)
            
            conventions['prop_naming'] = 'camelCase' if camel_props > snake_props else 'snake_case'
        
        return conventions

    def _identify_common_patterns(self, components: Dict[str, ComponentPattern]) -> List[str]:
        """Identify common patterns across components"""
        patterns = []
        
        # Analyze common styling patterns
        all_styles = []
        for component in components.values():
            all_styles.extend(component.styling_patterns)
        
        style_counter = Counter(all_styles)
        common_styles = [style for style, count in style_counter.most_common(10) if count > 1]
        
        patterns.extend([f"Common styling: {style}" for style in common_styles[:5]])
        
        # Analyze common prop patterns
        all_props = []
        for component in components.values():
            all_props.extend(component.props)
        
        prop_counter = Counter(all_props)
        common_props = [prop for prop, count in prop_counter.most_common(10) if count > 2]
        
        patterns.extend([f"Common prop: {prop}" for prop in common_props[:3]])
        
        return patterns

    def _looks_like_color(self, value: str) -> bool:
        """Check if a value looks like a color"""
        color_patterns = [
            r'^#[0-9a-fA-F]{3,8}$',  # Hex colors
            r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$',  # RGB
            r'^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)$',  # RGBA
            r'^hsl\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*\)$',  # HSL
        ]
        
        return any(re.match(pattern, value.strip()) for pattern in color_patterns)

    def _categorize_token(self, name: str, value: str) -> str:
        """Categorize a design token based on name and value"""
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['color', 'bg', 'text', 'border']):
            return 'color'
        elif any(keyword in name_lower for keyword in ['spacing', 'margin', 'padding', 'gap']):
            return 'spacing'
        elif any(keyword in name_lower for keyword in ['font', 'text', 'size']):
            return 'typography'
        elif any(keyword in name_lower for keyword in ['shadow', 'elevation']):
            return 'shadow'
        elif any(keyword in name_lower for keyword in ['radius', 'rounded']):
            return 'border-radius'
        else:
            return 'other'

    def get_context_for_generation(self) -> Dict[str, Any]:
        """Get design system context for component generation"""
        if not self.design_profile:
            self.analyze_design_system()
        
        context = {
            'framework': self.design_profile.framework,
            'styling_system': self.design_profile.styling_system,
            'naming_conventions': self.design_profile.naming_conventions,
            'common_patterns': self.design_profile.common_patterns
        }
        
        # Add most common tokens
        for category, tokens in self.design_profile.tokens.items():
            if tokens:
                context[f'common_{category}_tokens'] = [
                    f"{token.name}: {token.value}" for token in tokens[:5]
                ]
        
        # Add component examples
        context['existing_components'] = list(self.design_profile.components.keys())[:10]
        
        return context