"""
Component Relationship Analysis for Style Consistency

This module analyzes relationships between components to maintain 
consistent styling and patterns across component generation.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict, Counter

@dataclass
class ComponentDependency:
    """Represents a dependency between components"""
    source: str
    target: str
    relationship_type: str  # 'imports', 'composes', 'extends', 'styles_like'
    context: str = ""

@dataclass
class StylePattern:
    """Represents a styling pattern found across components"""
    pattern_name: str
    pattern_definition: str
    components_using: List[str]
    frequency: int
    category: str  # 'layout', 'color', 'typography', 'spacing', 'interaction'

@dataclass
class ComponentFamily:
    """Represents a family of related components"""
    family_name: str
    components: List[str]
    shared_patterns: List[str]
    base_component: Optional[str] = None

class ComponentRelationshipAnalyzer:
    """Analyzes relationships between components for consistency"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dependencies: List[ComponentDependency] = []
        self.style_patterns: Dict[str, StylePattern] = {}
        self.component_families: Dict[str, ComponentFamily] = {}
        self.component_files: List[Path] = []
        self.component_data: Dict[str, Dict[str, Any]] = {}
        
    def analyze_relationships(self) -> Dict[str, Any]:
        """Analyze all component relationships"""
        print("🔗 Analyzing component relationships...")
        
        # Find all component files
        self._discover_components()
        
        # Parse each component
        self._parse_components()
        
        # Analyze dependencies
        self._analyze_dependencies()
        
        # Extract style patterns
        self._extract_style_patterns()
        
        # Group into families
        self._group_component_families()
        
        return {
            'dependencies': self.dependencies,
            'style_patterns': self.style_patterns,
            'component_families': self.component_families,
            'component_data': self.component_data
        }

    def _discover_components(self) -> None:
        """Discover all component files in the project"""
        component_patterns = [
            '**/*{C,c}omponent*.{tsx,ts,jsx,js}',
            '**/components/**/*.{tsx,ts,jsx,js}',
            '**/ui/**/*.{tsx,ts,jsx,js}',
            'src/**/*.{tsx,ts,jsx,js}'
        ]
        
        for pattern in component_patterns:
            files = self.project_path.glob(pattern)
            for file in files:
                if file.is_file() and file.stem not in ['index', 'types']:
                    self.component_files.append(file)
        
        # Remove duplicates
        self.component_files = list(set(self.component_files))

    def _parse_components(self) -> None:
        """Parse each component file to extract metadata"""
        for component_file in self.component_files[:30]:  # Limit for performance
            try:
                with open(component_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                component_name = self._extract_component_name(content, component_file)
                if component_name:
                    self.component_data[component_name] = {
                        'file_path': str(component_file),
                        'imports': self._extract_imports(content),
                        'props': self._extract_props(content),
                        'styling': self._extract_styling_info(content),
                        'jsx_elements': self._extract_jsx_elements(content),
                        'hooks': self._extract_hooks(content),
                        'content': content
                    }
                    
            except (UnicodeDecodeError, FileNotFoundError) as e:
                print(f"Warning: Could not read {component_file}: {e}")
                continue

    def _extract_component_name(self, content: str, file_path: Path) -> Optional[str]:
        """Extract the main component name from file content"""
        # Try to find export default or export const patterns
        patterns = [
            r'export\s+default\s+(?:function\s+)?(\w+)',
            r'export\s+(?:const|function)\s+(\w+)',
            r'const\s+(\w+)\s*=.*forwardRef',
            r'function\s+(\w+)\s*\(',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        # Fallback to filename
        return file_path.stem

    def _extract_imports(self, content: str) -> List[Dict[str, str]]:
        """Extract import statements"""
        imports = []
        
        # Find import statements
        import_pattern = r'import\s+(?:{[^}]+}|\w+|[^;]+)\s+from\s+[\'"]([^\'"]+)[\'"];?'
        matches = re.findall(import_pattern, content)
        
        for match in matches:
            # Check if it's a relative import (component dependency)
            if match.startswith('.'):
                imports.append({
                    'type': 'relative',
                    'path': match,
                    'is_component': self._looks_like_component_import(match)
                })
            else:
                imports.append({
                    'type': 'external',
                    'path': match,
                    'is_component': False
                })
        
        return imports

    def _extract_props(self, content: str) -> Dict[str, Any]:
        """Extract component props information"""
        props_info = {
            'interface_props': [],
            'destructured_props': [],
            'prop_types': {}
        }
        
        # Extract interface definitions
        interface_matches = re.findall(
            r'interface\s+(\w*Props)\s*\{([^}]+)\}', 
            content, 
            re.DOTALL
        )
        
        for interface_name, interface_body in interface_matches:
            prop_matches = re.findall(r'(\w+)\??:\s*([^;,\n]+)', interface_body)
            for prop_name, prop_type in prop_matches:
                props_info['interface_props'].append(prop_name)
                props_info['prop_types'][prop_name] = prop_type.strip()
        
        # Extract destructured props
        destructure_matches = re.findall(
            r'\{\s*([^}]+)\s*\}\s*:\s*\w*Props', 
            content
        )
        
        for destructure_content in destructure_matches:
            prop_names = [p.strip() for p in destructure_content.split(',')]
            props_info['destructured_props'].extend(prop_names)
        
        return props_info

    def _extract_styling_info(self, content: str) -> Dict[str, Any]:
        """Extract styling information from component"""
        styling_info = {
            'tailwind_classes': [],
            'css_modules': [],
            'styled_components': [],
            'style_objects': [],
            'css_variables': []
        }
        
        # Extract Tailwind classes
        tailwind_matches = re.findall(r'className\s*=\s*[\'"`]([^\'"`]+)[\'"`]', content)
        for match in tailwind_matches:
            classes = match.split()
            styling_info['tailwind_classes'].extend(classes)
        
        # Extract template literal classes (for conditional styling)
        template_matches = re.findall(r'className\s*=\s*`([^`]+)`', content)
        for match in template_matches:
            # Simple extraction, could be enhanced to parse template literals better
            classes = re.findall(r'[\w-]+', match)
            styling_info['tailwind_classes'].extend(classes)
        
        # Extract CSS modules
        css_module_matches = re.findall(r'styles\.(\w+)', content)
        styling_info['css_modules'].extend(css_module_matches)
        
        # Extract styled-components
        styled_matches = re.findall(r'styled\.(\w+)`([^`]*)`', content, re.DOTALL)
        for element, styles in styled_matches:
            styling_info['styled_components'].append({
                'element': element,
                'styles': styles.strip()
            })
        
        # Extract CSS custom properties
        css_var_matches = re.findall(r'var\(--([^)]+)\)', content)
        styling_info['css_variables'].extend(css_var_matches)
        
        return styling_info

    def _extract_jsx_elements(self, content: str) -> List[str]:
        """Extract JSX elements used in the component"""
        elements = []
        
        # Find JSX opening tags
        jsx_pattern = r'<(\w+)(?:\s+[^>]*)?/?>'
        matches = re.findall(jsx_pattern, content)
        
        # Filter out HTML elements, keep component elements
        for match in matches:
            if match[0].isupper():  # Component (starts with uppercase)
                elements.append(match)
        
        return list(set(elements))  # Remove duplicates

    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used in the component"""
        hooks = []
        
        hook_pattern = r'(use\w+)\s*\('
        matches = re.findall(hook_pattern, content)
        
        return list(set(matches))

    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between components"""
        for component_name, component_data in self.component_data.items():
            # Analyze imports
            for import_info in component_data['imports']:
                if import_info['is_component']:
                    target_name = self._resolve_import_to_component(import_info['path'])
                    if target_name and target_name in self.component_data:
                        self.dependencies.append(ComponentDependency(
                            source=component_name,
                            target=target_name,
                            relationship_type='imports',
                            context=import_info['path']
                        ))
            
            # Analyze JSX composition
            for jsx_element in component_data['jsx_elements']:
                if jsx_element in self.component_data:
                    self.dependencies.append(ComponentDependency(
                        source=component_name,
                        target=jsx_element,
                        relationship_type='composes',
                        context='JSX composition'
                    ))

    def _extract_style_patterns(self) -> None:
        """Extract common styling patterns across components"""
        all_tailwind_classes = []
        class_component_map = defaultdict(list)
        
        # Collect all styling information
        for component_name, component_data in self.component_data.items():
            styling = component_data['styling']
            for class_name in styling['tailwind_classes']:
                all_tailwind_classes.append(class_name)
                class_component_map[class_name].append(component_name)
        
        # Find common patterns
        class_counter = Counter(all_tailwind_classes)
        
        for class_name, frequency in class_counter.most_common(50):
            if frequency > 1:  # Used in multiple components
                pattern_category = self._categorize_style_pattern(class_name)
                
                self.style_patterns[class_name] = StylePattern(
                    pattern_name=class_name,
                    pattern_definition=class_name,  # For Tailwind, the class IS the definition
                    components_using=class_component_map[class_name],
                    frequency=frequency,
                    category=pattern_category
                )

    def _group_component_families(self) -> None:
        """Group related components into families"""
        # Group by naming patterns
        name_groups = defaultdict(list)
        
        for component_name in self.component_data.keys():
            # Group by prefix (Button, Card, Input, etc.)
            base_name = self._extract_base_name(component_name)
            name_groups[base_name].append(component_name)
        
        # Create families for groups with multiple components
        for base_name, components in name_groups.items():
            if len(components) > 1:
                shared_patterns = self._find_shared_patterns(components)
                base_component = self._find_base_component(components)
                
                self.component_families[base_name] = ComponentFamily(
                    family_name=base_name,
                    components=components,
                    shared_patterns=shared_patterns,
                    base_component=base_component
                )

    def _looks_like_component_import(self, import_path: str) -> bool:
        """Check if an import path looks like a component import"""
        return (
            import_path.startswith('./') or import_path.startswith('../')
        ) and not import_path.endswith('.css')

    def _resolve_import_to_component(self, import_path: str) -> Optional[str]:
        """Resolve an import path to a component name"""
        # Simple resolution - extract the last part of the path
        path_parts = import_path.split('/')
        last_part = path_parts[-1]
        
        # Remove file extension if present
        if '.' in last_part:
            last_part = last_part.split('.')[0]
        
        return last_part if last_part != 'index' else path_parts[-2] if len(path_parts) > 1 else None

    def _categorize_style_pattern(self, class_name: str) -> str:
        """Categorize a style pattern"""
        if any(prefix in class_name for prefix in ['flex', 'grid', 'block', 'inline', 'absolute', 'relative']):
            return 'layout'
        elif any(prefix in class_name for prefix in ['bg-', 'text-', 'border-']):
            return 'color'
        elif any(prefix in class_name for prefix in ['text-', 'font-', 'leading-']):
            return 'typography'
        elif any(prefix in class_name for prefix in ['p-', 'm-', 'px-', 'py-', 'mt-', 'mb-', 'ml-', 'mr-']):
            return 'spacing'
        elif any(prefix in class_name for prefix in ['hover:', 'focus:', 'active:']):
            return 'interaction'
        else:
            return 'other'

    def _extract_base_name(self, component_name: str) -> str:
        """Extract the base name from a component name"""
        # Remove common suffixes
        suffixes = ['Button', 'Card', 'Input', 'Component', 'Item', 'Element']
        
        for suffix in suffixes:
            if component_name.endswith(suffix) and len(component_name) > len(suffix):
                return suffix
        
        # Remove version numbers or variants
        base = re.sub(r'(V\d+|\d+|Variant\w*|Primary|Secondary)$', '', component_name)
        
        return base if base else component_name

    def _find_shared_patterns(self, components: List[str]) -> List[str]:
        """Find shared styling patterns among components"""
        shared_patterns = []
        
        if not components:
            return shared_patterns
        
        # Get styling from first component
        first_component_styles = set(
            self.component_data[components[0]]['styling']['tailwind_classes']
        )
        
        # Find patterns shared with all other components
        for other_component in components[1:]:
            other_styles = set(
                self.component_data[other_component]['styling']['tailwind_classes']
            )
            first_component_styles &= other_styles
        
        return list(first_component_styles)[:10]  # Limit to 10 most relevant

    def _find_base_component(self, components: List[str]) -> Optional[str]:
        """Find the base component in a family"""
        # Look for the simplest name
        shortest = min(components, key=len)
        
        # Prefer components without suffixes like "Variant", "V2", etc.
        for component in components:
            if not re.search(r'(Variant|V\d+|\d+|Primary|Secondary)$', component):
                return component
        
        return shortest

    def get_context_for_generation(self, target_component: str = None) -> Dict[str, Any]:
        """Get relationship context for component generation"""
        context = {
            'total_components': len(self.component_data),
            'component_families': list(self.component_families.keys()),
            'common_patterns': list(self.style_patterns.keys())[:10],
            'common_hooks': [],
            'styling_consistency': {}
        }
        
        # Find most common hooks
        all_hooks = []
        for comp_data in self.component_data.values():
            all_hooks.extend(comp_data['hooks'])
        
        hook_counter = Counter(all_hooks)
        context['common_hooks'] = [hook for hook, count in hook_counter.most_common(5)]
        
        # Styling consistency patterns
        for category in ['layout', 'color', 'typography', 'spacing']:
            category_patterns = [
                pattern.pattern_name for pattern in self.style_patterns.values() 
                if pattern.category == category and pattern.frequency > 2
            ]
            context['styling_consistency'][category] = category_patterns[:5]
        
        # If target component specified, add specific context
        if target_component and target_component in self.component_data:
            context['target_component'] = {
                'existing_props': self.component_data[target_component]['props']['interface_props'],
                'current_styling': self.component_data[target_component]['styling']['tailwind_classes'][:10],
                'dependencies': [
                    dep.target for dep in self.dependencies 
                    if dep.source == target_component
                ]
            }
        
        return context

    def suggest_consistent_styling(self, component_type: str) -> Dict[str, Any]:
        """Suggest consistent styling for a new component based on existing patterns"""
        suggestions = {
            'base_classes': [],
            'variant_patterns': [],
            'layout_patterns': [],
            'interaction_patterns': []
        }
        
        # Find patterns used in similar components
        similar_components = []
        for comp_name in self.component_data.keys():
            if component_type.lower() in comp_name.lower():
                similar_components.append(comp_name)
        
        if similar_components:
            # Collect common patterns from similar components
            common_styles = []
            for comp_name in similar_components:
                comp_styles = self.component_data[comp_name]['styling']['tailwind_classes']
                common_styles.extend(comp_styles)
            
            style_counter = Counter(common_styles)
            
            # Categorize suggestions
            for style, count in style_counter.most_common(20):
                category = self._categorize_style_pattern(style)
                if category == 'layout':
                    suggestions['layout_patterns'].append(style)
                elif category == 'interaction':
                    suggestions['interaction_patterns'].append(style)
                elif count > len(similar_components) * 0.5:  # Used by at least half
                    suggestions['base_classes'].append(style)
        
        # Add family-based suggestions if component belongs to a known family
        for family_name, family in self.component_families.items():
            if family_name.lower() in component_type.lower():
                suggestions['variant_patterns'].extend(family.shared_patterns)
                break
        
        return suggestions