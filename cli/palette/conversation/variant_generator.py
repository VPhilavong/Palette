"""
Component Variant Generation System

This module handles the generation of component variants, allowing users to
create different versions of existing components with consistent styling patterns.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class VariantSpec:
    """Specification for a component variant"""
    name: str
    base_component: str
    changes: Dict[str, Any]  # What to modify from the base
    description: str
    variant_type: str  # 'size', 'color', 'style', 'state', 'layout'

@dataclass
class ComponentVariantFamily:
    """A family of related component variants"""
    base_name: str
    base_component_code: str
    variants: List[VariantSpec]
    common_props: List[str]
    variant_props: Dict[str, List[str]]  # prop -> possible values

class VariantType(Enum):
    SIZE = "size"           # sm, md, lg, xl
    COLOR = "color"         # primary, secondary, success, warning, error
    STYLE = "style"         # filled, outline, ghost, text
    STATE = "state"         # default, hover, active, disabled, loading
    LAYOUT = "layout"       # horizontal, vertical, grid, list
    SEMANTIC = "semantic"   # destructive, constructive, neutral

class VariantGenerator:
    """Generates component variants with consistent patterns"""
    
    def __init__(self, conversation_engine):
        self.conversation_engine = conversation_engine
        self.variant_patterns = self._load_variant_patterns()
        self.discovered_variants = {}

    def _load_variant_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common variant patterns for different component types"""
        return {
            'button': {
                'size_variants': {
                    'sm': {'padding': 'px-2 py-1', 'text': 'text-sm', 'description': 'Small button'},
                    'md': {'padding': 'px-4 py-2', 'text': 'text-base', 'description': 'Medium button'},  
                    'lg': {'padding': 'px-6 py-3', 'text': 'text-lg', 'description': 'Large button'},
                    'xl': {'padding': 'px-8 py-4', 'text': 'text-xl', 'description': 'Extra large button'}
                },
                'style_variants': {
                    'filled': {'bg': 'bg-blue-600', 'text': 'text-white', 'description': 'Solid background button'},
                    'outline': {'bg': 'bg-transparent', 'border': 'border-2 border-blue-600', 'text': 'text-blue-600', 'description': 'Outline button'},
                    'ghost': {'bg': 'bg-transparent', 'text': 'text-blue-600 hover:bg-blue-50', 'description': 'Ghost button'},
                    'text': {'bg': 'bg-transparent', 'text': 'text-blue-600', 'description': 'Text-only button'}
                },
                'semantic_variants': {
                    'primary': {'bg': 'bg-blue-600', 'hover': 'hover:bg-blue-700'},
                    'secondary': {'bg': 'bg-gray-600', 'hover': 'hover:bg-gray-700'},
                    'success': {'bg': 'bg-green-600', 'hover': 'hover:bg-green-700'},
                    'warning': {'bg': 'bg-yellow-600', 'hover': 'hover:bg-yellow-700'},
                    'error': {'bg': 'bg-red-600', 'hover': 'hover:bg-red-700'}
                }
            },
            'card': {
                'style_variants': {
                    'elevated': {'shadow': 'shadow-lg', 'border': '', 'description': 'Card with elevation shadow'},
                    'outline': {'shadow': '', 'border': 'border border-gray-200', 'description': 'Card with border outline'},
                    'flat': {'shadow': '', 'border': '', 'bg': 'bg-gray-50', 'description': 'Flat card with background'},
                },
                'size_variants': {
                    'compact': {'padding': 'p-3', 'description': 'Compact card'},
                    'normal': {'padding': 'p-6', 'description': 'Normal card'},
                    'spacious': {'padding': 'p-8', 'description': 'Spacious card'}
                }
            },
            'input': {
                'size_variants': {
                    'sm': {'padding': 'px-2 py-1', 'text': 'text-sm', 'height': 'h-8'},
                    'md': {'padding': 'px-3 py-2', 'text': 'text-base', 'height': 'h-10'},
                    'lg': {'padding': 'px-4 py-3', 'text': 'text-lg', 'height': 'h-12'}
                },
                'state_variants': {
                    'default': {'border': 'border-gray-300', 'bg': 'bg-white'},
                    'error': {'border': 'border-red-500', 'bg': 'bg-white'},
                    'success': {'border': 'border-green-500', 'bg': 'bg-white'},
                    'disabled': {'border': 'border-gray-200', 'bg': 'bg-gray-100'}
                }
            },
            'modal': {
                'size_variants': {
                    'sm': {'width': 'max-w-sm', 'description': 'Small modal'},
                    'md': {'width': 'max-w-md', 'description': 'Medium modal'},
                    'lg': {'width': 'max-w-lg', 'description': 'Large modal'},
                    'xl': {'width': 'max-w-xl', 'description': 'Extra large modal'},
                    'full': {'width': 'max-w-full', 'height': 'h-full', 'description': 'Full screen modal'}
                }
            },
            'alert': {
                'semantic_variants': {
                    'info': {'bg': 'bg-blue-50', 'border': 'border-blue-200', 'text': 'text-blue-800', 'icon': 'info'},
                    'success': {'bg': 'bg-green-50', 'border': 'border-green-200', 'text': 'text-green-800', 'icon': 'check'},
                    'warning': {'bg': 'bg-yellow-50', 'border': 'border-yellow-200', 'text': 'text-yellow-800', 'icon': 'warning'},
                    'error': {'bg': 'bg-red-50', 'border': 'border-red-200', 'text': 'text-red-800', 'icon': 'error'}
                }
            }
        }

    def analyze_component_for_variants(self, component_code: str, component_name: str) -> ComponentVariantFamily:
        """Analyze a component to determine possible variants"""
        # Extract current styling patterns
        current_styles = self._extract_component_styles(component_code)
        current_props = self._extract_component_props(component_code)
        
        # Determine component type
        component_type = self._classify_component_type(component_name, component_code)
        
        # Generate variant specifications
        possible_variants = self._generate_variant_specs(
            component_type, component_name, current_styles, current_props
        )
        
        return ComponentVariantFamily(
            base_name=component_name,
            base_component_code=component_code,
            variants=possible_variants,
            common_props=current_props,
            variant_props=self._extract_variant_props(possible_variants)
        )

    def _extract_component_styles(self, component_code: str) -> Dict[str, List[str]]:
        """Extract styling information from component code"""
        styles = {
            'tailwind_classes': [],
            'conditional_classes': [],
            'style_props': []
        }
        
        # Extract className attributes
        class_matches = re.findall(r'className\s*=\s*[\'"`]([^\'"`]+)[\'"`]', component_code)
        for match in class_matches:
            styles['tailwind_classes'].extend(match.split())
        
        # Extract conditional className (template literals)
        conditional_matches = re.findall(r'className\s*=\s*`([^`]+)`', component_code)
        for match in conditional_matches:
            styles['conditional_classes'].append(match)
        
        # Extract className with expressions
        expression_matches = re.findall(r'className\s*=\s*\{([^}]+)\}', component_code)
        styles['conditional_classes'].extend(expression_matches)
        
        return styles

    def _extract_component_props(self, component_code: str) -> List[str]:
        """Extract component props from interface or destructuring"""
        props = []
        
        # Extract from interface
        interface_matches = re.findall(r'interface\s+\w*Props\s*\{([^}]+)\}', component_code, re.DOTALL)
        for interface_content in interface_matches:
            prop_matches = re.findall(r'(\w+)\??:', interface_content)
            props.extend(prop_matches)
        
        # Extract from destructuring
        destructure_matches = re.findall(r'\{\s*([^}]+)\s*\}\s*:\s*\w*Props', component_code)
        for destructure_content in destructure_matches:
            prop_names = [p.strip() for p in destructure_content.split(',')]
            props.extend(prop_names)
        
        return list(set(props))

    def _classify_component_type(self, component_name: str, component_code: str) -> str:
        """Classify component type based on name and content"""
        name_lower = component_name.lower()
        code_lower = component_code.lower()
        
        # Classification based on name
        type_indicators = {
            'button': ['button', 'btn'],
            'card': ['card'],
            'input': ['input', 'textfield', 'textarea'],
            'modal': ['modal', 'dialog', 'popup'],
            'alert': ['alert', 'notification', 'toast', 'banner'],
            'badge': ['badge', 'chip', 'tag'],
            'avatar': ['avatar', 'profile'],
            'navigation': ['nav', 'menu', 'breadcrumb']
        }
        
        for comp_type, indicators in type_indicators.items():
            if any(indicator in name_lower for indicator in indicators):
                return comp_type
        
        # Classification based on content
        if 'onclick' in code_lower or 'button' in code_lower:
            return 'button'
        elif 'input' in code_lower or 'value' in code_lower:
            return 'input'
        elif 'modal' in code_lower or 'overlay' in code_lower:
            return 'modal'
        elif any(word in code_lower for word in ['error', 'success', 'warning', 'info']):
            return 'alert'
        
        return 'generic'

    def _generate_variant_specs(self, component_type: str, component_name: str, 
                              current_styles: Dict[str, List[str]], 
                              current_props: List[str]) -> List[VariantSpec]:
        """Generate variant specifications for a component"""
        variants = []
        
        if component_type not in self.variant_patterns:
            # Generate generic variants for unknown types
            return self._generate_generic_variants(component_name, current_styles)
        
        patterns = self.variant_patterns[component_type]
        
        # Generate size variants
        if 'size_variants' in patterns:
            for size, styles in patterns['size_variants'].items():
                variants.append(VariantSpec(
                    name=f"{component_name}{size.title()}",
                    base_component=component_name,
                    changes=styles,
                    description=styles.get('description', f"{size.title()} variant of {component_name}"),
                    variant_type=VariantType.SIZE.value
                ))
        
        # Generate style variants
        if 'style_variants' in patterns:
            for style, styles in patterns['style_variants'].items():
                variants.append(VariantSpec(
                    name=f"{component_name}{style.title()}",
                    base_component=component_name,
                    changes=styles,
                    description=styles.get('description', f"{style.title()} style of {component_name}"),
                    variant_type=VariantType.STYLE.value
                ))
        
        # Generate semantic variants
        if 'semantic_variants' in patterns:
            for semantic, styles in patterns['semantic_variants'].items():
                variants.append(VariantSpec(
                    name=f"{component_name}{semantic.title()}",
                    base_component=component_name,
                    changes=styles,
                    description=f"{semantic.title()} {component_name}",
                    variant_type=VariantType.SEMANTIC.value
                ))
        
        # Generate state variants
        if 'state_variants' in patterns:
            for state, styles in patterns['state_variants'].items():
                if state != 'default':  # Skip default state
                    variants.append(VariantSpec(
                        name=f"{component_name}{state.title()}",
                        base_component=component_name,
                        changes=styles,
                        description=f"{state.title()} state of {component_name}",
                        variant_type=VariantType.STATE.value
                    ))
        
        return variants

    def _generate_generic_variants(self, component_name: str, 
                                 current_styles: Dict[str, List[str]]) -> List[VariantSpec]:
        """Generate generic variants for unknown component types"""
        variants = []
        
        # Analyze current styles to suggest variants
        tailwind_classes = current_styles.get('tailwind_classes', [])
        
        # Size variants based on current padding/size classes
        if any('p-' in cls or 'px-' in cls or 'py-' in cls for cls in tailwind_classes):
            variants.extend([
                VariantSpec(
                    name=f"{component_name}Small",
                    base_component=component_name,
                    changes={'padding': 'p-2', 'text': 'text-sm'},
                    description=f"Small variant of {component_name}",
                    variant_type=VariantType.SIZE.value
                ),
                VariantSpec(
                    name=f"{component_name}Large", 
                    base_component=component_name,
                    changes={'padding': 'p-6', 'text': 'text-lg'},
                    description=f"Large variant of {component_name}",
                    variant_type=VariantType.SIZE.value
                )
            ])
        
        # Color variants if color classes are present
        if any('bg-' in cls or 'text-' in cls for cls in tailwind_classes):
            variants.extend([
                VariantSpec(
                    name=f"{component_name}Primary",
                    base_component=component_name,
                    changes={'bg': 'bg-blue-600', 'text': 'text-white'},
                    description=f"Primary variant of {component_name}",
                    variant_type=VariantType.SEMANTIC.value
                ),
                VariantSpec(
                    name=f"{component_name}Secondary",
                    base_component=component_name,
                    changes={'bg': 'bg-gray-600', 'text': 'text-white'},
                    description=f"Secondary variant of {component_name}",
                    variant_type=VariantType.SEMANTIC.value
                )
            ])
        
        return variants

    def _extract_variant_props(self, variants: List[VariantSpec]) -> Dict[str, List[str]]:
        """Extract variant props from variant specifications"""
        variant_props = {}
        
        # Group variants by type
        by_type = {}
        for variant in variants:
            if variant.variant_type not in by_type:
                by_type[variant.variant_type] = []
            by_type[variant.variant_type].append(variant)
        
        # Create props for each variant type
        for variant_type, type_variants in by_type.items():
            prop_name = variant_type
            if variant_type == VariantType.SIZE.value:
                prop_name = 'size'
            elif variant_type == VariantType.STYLE.value:
                prop_name = 'variant'
            elif variant_type == VariantType.SEMANTIC.value:
                prop_name = 'color'
            
            # Extract variant names (removing component name prefix)
            variant_names = []
            for variant in type_variants:
                name = variant.name
                base_name = variant.base_component
                if name.startswith(base_name):
                    variant_name = name[len(base_name):].lower()
                    if variant_name:
                        variant_names.append(variant_name)
            
            if variant_names:
                variant_props[prop_name] = variant_names
        
        return variant_props

    def generate_variant_code(self, base_code: str, variant_spec: VariantSpec) -> str:
        """Generate code for a specific variant"""
        # Start with the base component code
        variant_code = base_code
        
        # Replace component name
        old_name = variant_spec.base_component
        new_name = variant_spec.name
        
        # Replace component name in export and function declaration
        variant_code = re.sub(
            rf'\b{old_name}\b(?=\s*[:=]|\s*\()',
            new_name,
            variant_code
        )
        
        # Apply styling changes
        variant_code = self._apply_styling_changes(variant_code, variant_spec.changes)
        
        # Add variant-specific props if needed
        variant_code = self._add_variant_props(variant_code, variant_spec)
        
        return variant_code

    def _apply_styling_changes(self, code: str, changes: Dict[str, Any]) -> str:
        """Apply styling changes to component code"""
        modified_code = code
        
        for change_type, change_value in changes.items():
            if change_type in ['padding', 'bg', 'text', 'border', 'shadow', 'width', 'height']:
                # Replace or add Tailwind classes
                modified_code = self._update_tailwind_classes(
                    modified_code, change_type, change_value
                )
        
        return modified_code

    def _update_tailwind_classes(self, code: str, class_type: str, new_value: str) -> str:
        """Update Tailwind classes in component code"""
        # Map class types to their prefixes
        class_prefixes = {
            'padding': ['p-', 'px-', 'py-'],
            'bg': ['bg-'],
            'text': ['text-'],
            'border': ['border-', 'border'],
            'shadow': ['shadow-', 'shadow'],
            'width': ['w-', 'max-w-'],
            'height': ['h-', 'max-h-', 'min-h-']
        }
        
        if class_type not in class_prefixes:
            return code
        
        prefixes = class_prefixes[class_type]
        
        # Find className attributes and update them
        def replace_classes(match):
            class_string = match.group(1)
            classes = class_string.split()
            
            # Remove old classes of this type
            filtered_classes = []
            for cls in classes:
                if not any(cls.startswith(prefix) for prefix in prefixes):
                    filtered_classes.append(cls)
            
            # Add new class
            if new_value and new_value not in filtered_classes:
                filtered_classes.append(new_value)
            
            return f'className="{" ".join(filtered_classes)}"'
        
        # Update className attributes
        pattern = r'className\s*=\s*"([^"]*)"'
        modified_code = re.sub(pattern, replace_classes, code)
        
        return modified_code

    def _add_variant_props(self, code: str, variant_spec: VariantSpec) -> str:
        """Add variant-specific props to component interface"""
        # This is a simplified implementation
        # In a real scenario, you might want to add props based on the variant type
        
        if variant_spec.variant_type == VariantType.SIZE.value:
            # Could add size prop to interface
            pass
        elif variant_spec.variant_type == VariantType.SEMANTIC.value:
            # Could add color prop to interface
            pass
        
        return code

    def suggest_variants(self, component_name: str, user_request: str = None) -> List[VariantSpec]:
        """Suggest variants for a component based on name and optional user request"""
        
        # Try to find existing component in relationship analyzer
        if (self.conversation_engine.relationship_analyzer and 
            hasattr(self.conversation_engine.relationship_analyzer, 'component_data')):
            
            component_data = self.conversation_engine.relationship_analyzer.component_data
            if component_name in component_data:
                component_info = component_data[component_name]
                variant_family = self.analyze_component_for_variants(
                    component_info['content'], component_name
                )
                return variant_family.variants
        
        # Fallback: generate variants based on name and request
        component_type = self._classify_component_type(component_name, "")
        
        if user_request:
            # Parse user request for specific variant types
            request_lower = user_request.lower()
            
            requested_variants = []
            
            if 'size' in request_lower or 'small' in request_lower or 'large' in request_lower:
                if component_type in self.variant_patterns:
                    size_patterns = self.variant_patterns[component_type].get('size_variants', {})
                    for size, styles in size_patterns.items():
                        requested_variants.append(VariantSpec(
                            name=f"{component_name}{size.title()}",
                            base_component=component_name,
                            changes=styles,
                            description=styles.get('description', f"{size} {component_name}"),
                            variant_type=VariantType.SIZE.value
                        ))
            
            if 'color' in request_lower or 'primary' in request_lower or 'secondary' in request_lower:
                if component_type in self.variant_patterns:
                    semantic_patterns = self.variant_patterns[component_type].get('semantic_variants', {})
                    for semantic, styles in semantic_patterns.items():
                        requested_variants.append(VariantSpec(
                            name=f"{component_name}{semantic.title()}",
                            base_component=component_name,
                            changes=styles,
                            description=f"{semantic} {component_name}",
                            variant_type=VariantType.SEMANTIC.value
                        ))
            
            if requested_variants:
                return requested_variants
        
        # Default: return common variants for the component type
        return self._generate_variant_specs(component_type, component_name, {}, [])

    def create_variant_system_code(self, base_component: str, variants: List[VariantSpec]) -> str:
        """Create a variant system with props-based variant selection"""
        
        variant_family = ComponentVariantFamily(
            base_name=base_component,
            base_component_code="",
            variants=variants,
            common_props=[],
            variant_props=self._extract_variant_props(variants)
        )
        
        # Generate TypeScript types for variants
        types_code = self._generate_variant_types(variant_family)
        
        # Generate variant mapping object
        mapping_code = self._generate_variant_mapping(variant_family)
        
        # Generate main component with variant support
        component_code = self._generate_variant_component(variant_family)
        
        return f"""// Generated variant system for {base_component}

{types_code}

{mapping_code}

{component_code}"""

    def _generate_variant_types(self, family: ComponentVariantFamily) -> str:
        """Generate TypeScript types for the variant system"""
        types = []
        
        for prop_name, values in family.variant_props.items():
            type_name = f"{family.base_name}{prop_name.title()}Variant"
            values_string = " | ".join(f'"{value}"' for value in values)
            types.append(f"type {type_name} = {values_string};")
        
        # Main props interface
        prop_types = []
        for prop_name, values in family.variant_props.items():
            type_name = f"{family.base_name}{prop_name.title()}Variant"
            prop_types.append(f"  {prop_name}?: {type_name};")
        
        interface = f"""interface {family.base_name}Props {{
{chr(10).join(prop_types)}
  className?: string;
  children?: React.ReactNode;
}}"""
        
        return "\n".join(types) + "\n\n" + interface

    def _generate_variant_mapping(self, family: ComponentVariantFamily) -> str:
        """Generate variant mapping object"""
        mappings = {}
        
        for variant in family.variants:
            for prop_name, values in family.variant_props.items():
                variant_value = variant.name.replace(family.base_name, "").lower()
                if variant_value in values:
                    if prop_name not in mappings:
                        mappings[prop_name] = {}
                    
                    # Convert variant changes to class string
                    classes = []
                    for change_key, change_value in variant.changes.items():
                        if isinstance(change_value, str) and change_value:
                            classes.append(change_value)
                    
                    mappings[prop_name][variant_value] = " ".join(classes)
        
        mapping_code = f"const {family.base_name.lower()}Variants = {{\n"
        for prop_name, prop_mappings in mappings.items():
            mapping_code += f"  {prop_name}: {{\n"
            for value, classes in prop_mappings.items():
                mapping_code += f'    {value}: "{classes}",\n'
            mapping_code += "  },\n"
        mapping_code += "};"
        
        return mapping_code

    def _generate_variant_component(self, family: ComponentVariantFamily) -> str:
        """Generate the main component with variant support"""
        prop_args = []
        class_building = []
        
        for prop_name in family.variant_props.keys():
            prop_args.append(prop_name)
            class_building.append(f"{family.base_name.lower()}Variants.{prop_name}?.[{prop_name}]")
        
        prop_args.append("className")
        prop_args.append("children")
        prop_args.append("...props")
        
        component_code = f"""export const {family.base_name}: React.FC<{family.base_name}Props> = ({{
  {", ".join(prop_args)}
}}) => {{
  const variantClasses = cn(
    {", ".join(class_building + ["className"])}
  );
  
  return (
    <div className={{variantClasses}} {{...props}}>
      {{children}}
    </div>
  );
}};"""
        
        return component_code