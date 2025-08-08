"""
Cross-Component Consistency Management

This module ensures consistency across multiple components in terms of styling,
patterns, naming conventions, and overall design cohesion.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from enum import Enum

@dataclass
class ConsistencyRule:
    """A rule for maintaining consistency across components"""
    rule_id: str
    rule_type: str  # 'styling', 'naming', 'structure', 'behavior'
    description: str
    pattern: str
    violations: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

@dataclass
class ComponentSignature:
    """Signature of a component for consistency checking"""
    name: str
    props: List[str]
    styling_patterns: Dict[str, List[str]]
    structure_patterns: List[str]
    naming_conventions: Dict[str, str]
    behavioral_patterns: List[str]

@dataclass
class ConsistencyReport:
    """Report on component consistency across a project"""
    total_components: int
    consistency_score: float
    violations: List[ConsistencyRule]
    recommendations: List[str]
    style_guide: Dict[str, str]

class ConsistencyType(Enum):
    STYLING = "styling"         # Colors, spacing, typography consistency
    NAMING = "naming"           # Prop names, component names, conventions
    STRUCTURE = "structure"     # Component architecture patterns
    BEHAVIOR = "behavior"       # Event handling, state management patterns
    ACCESSIBILITY = "accessibility"  # ARIA patterns, keyboard navigation
    RESPONSIVE = "responsive"   # Breakpoint usage, responsive patterns

class ConsistencyManager:
    """Manages consistency across multiple components"""
    
    def __init__(self, conversation_engine):
        self.conversation_engine = conversation_engine
        self.component_signatures: Dict[str, ComponentSignature] = {}
        self.consistency_rules: List[ConsistencyRule] = []
        self.established_patterns: Dict[str, Any] = {}
        self.style_guide: Dict[str, str] = {}
        
        # Initialize base consistency rules
        self._initialize_consistency_rules()

    def _initialize_consistency_rules(self):
        """Initialize base consistency rules"""
        self.consistency_rules = [
            ConsistencyRule(
                rule_id="consistent_button_sizing",
                rule_type=ConsistencyType.STYLING.value,
                description="Buttons should use consistent size classes",
                pattern="padding classes should follow sm/md/lg pattern",
                suggestions=[
                    "Use px-2 py-1 for small buttons",
                    "Use px-4 py-2 for medium buttons", 
                    "Use px-6 py-3 for large buttons"
                ]
            ),
            ConsistencyRule(
                rule_id="consistent_color_usage",
                rule_type=ConsistencyType.STYLING.value,
                description="Colors should follow established design tokens",
                pattern="primary/secondary/success/warning/error semantic colors",
                suggestions=[
                    "Use established color variables",
                    "Maintain color hierarchy across components"
                ]
            ),
            ConsistencyRule(
                rule_id="consistent_prop_naming",
                rule_type=ConsistencyType.NAMING.value,
                description="Props should follow consistent naming conventions",
                pattern="camelCase for props, boolean props with 'is/has/can' prefixes",
                suggestions=[
                    "Use camelCase for prop names",
                    "Use descriptive boolean prop names",
                    "Avoid abbreviations in prop names"
                ]
            ),
            ConsistencyRule(
                rule_id="consistent_spacing",
                rule_type=ConsistencyType.STYLING.value,
                description="Spacing should follow consistent scale",
                pattern="Use spacing scale: 1, 2, 3, 4, 6, 8, 12, 16, 20, 24",
                suggestions=[
                    "Use Tailwind's spacing scale",
                    "Avoid arbitrary spacing values"
                ]
            ),
            ConsistencyRule(
                rule_id="consistent_accessibility",
                rule_type=ConsistencyType.ACCESSIBILITY.value,
                description="Interactive elements should have consistent accessibility patterns",
                pattern="Buttons need aria-label, forms need proper labeling",
                suggestions=[
                    "Add aria-label for icon buttons",
                    "Use proper semantic HTML elements",
                    "Ensure keyboard navigation support"
                ]
            )
        ]

    def analyze_component_signature(self, component_code: str, component_name: str) -> ComponentSignature:
        """Extract component signature for consistency analysis"""
        return ComponentSignature(
            name=component_name,
            props=self._extract_props(component_code),
            styling_patterns=self._extract_styling_patterns(component_code),
            structure_patterns=self._extract_structure_patterns(component_code),
            naming_conventions=self._extract_naming_conventions(component_code),
            behavioral_patterns=self._extract_behavioral_patterns(component_code)
        )

    def _extract_props(self, component_code: str) -> List[str]:
        """Extract component props"""
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

    def _extract_styling_patterns(self, component_code: str) -> Dict[str, List[str]]:
        """Extract styling patterns from component"""
        patterns = {
            'colors': [],
            'spacing': [],
            'typography': [],
            'layout': [],
            'shadows': [],
            'borders': []
        }
        
        # Extract Tailwind classes
        class_matches = re.findall(r'className\s*=\s*[\'"`]([^\'"`]+)[\'"`]', component_code)
        all_classes = []
        for match in class_matches:
            all_classes.extend(match.split())
        
        # Categorize classes
        for cls in all_classes:
            if cls.startswith(('bg-', 'text-', 'border-')) and any(color in cls for color in ['blue', 'red', 'green', 'gray', 'yellow', 'purple']):
                patterns['colors'].append(cls)
            elif cls.startswith(('p-', 'm-', 'px-', 'py-', 'mx-', 'my-', 'mt-', 'mb-', 'ml-', 'mr-')):
                patterns['spacing'].append(cls)
            elif cls.startswith(('text-', 'font-', 'leading-', 'tracking-')):
                patterns['typography'].append(cls)
            elif cls.startswith(('flex', 'grid', 'block', 'inline', 'absolute', 'relative', 'w-', 'h-')):
                patterns['layout'].append(cls)
            elif cls.startswith('shadow'):
                patterns['shadows'].append(cls)
            elif cls.startswith(('border', 'rounded')):
                patterns['borders'].append(cls)
        
        return patterns

    def _extract_structure_patterns(self, component_code: str) -> List[str]:
        """Extract structural patterns from component"""
        patterns = []
        
        # Check for common structural patterns
        if 'forwardRef' in component_code:
            patterns.append('forwardRef')
        
        if re.search(r'useState\s*\(', component_code):
            patterns.append('useState')
        
        if re.search(r'useEffect\s*\(', component_code):
            patterns.append('useEffect')
        
        if re.search(r'useCallback\s*\(', component_code):
            patterns.append('useCallback')
        
        if re.search(r'useMemo\s*\(', component_code):
            patterns.append('useMemo')
        
        # Check for conditional rendering patterns
        if '&&' in component_code and '{' in component_code:
            patterns.append('conditional_rendering')
        
        # Check for mapping patterns
        if '.map(' in component_code:
            patterns.append('array_mapping')
        
        return patterns

    def _extract_naming_conventions(self, component_code: str) -> Dict[str, str]:
        """Extract naming conventions used in component"""
        conventions = {}
        
        # Analyze prop naming
        props = self._extract_props(component_code)
        if props:
            camel_case_props = sum(1 for prop in props if re.match(r'^[a-z][a-zA-Z0-9]*$', prop))
            snake_case_props = sum(1 for prop in props if '_' in prop)
            
            if camel_case_props > snake_case_props:
                conventions['prop_case'] = 'camelCase'
            else:
                conventions['prop_case'] = 'snake_case'
        
        # Analyze boolean prop prefixes
        boolean_props = [prop for prop in props if re.match(r'^(is|has|can|should|will|did)[A-Z]', prop)]
        if boolean_props:
            conventions['boolean_prefix'] = 'semantic'
        
        # Analyze handler naming
        handlers = re.findall(r'(on[A-Z]\w*)', component_code)
        if handlers:
            conventions['event_handlers'] = 'on_prefix'
        
        return conventions

    def _extract_behavioral_patterns(self, component_code: str) -> List[str]:
        """Extract behavioral patterns from component"""
        patterns = []
        
        # Check for event handling patterns
        if 'onClick' in component_code:
            patterns.append('click_handling')
        
        if 'onChange' in component_code:
            patterns.append('change_handling')
        
        if 'onSubmit' in component_code:
            patterns.append('form_submission')
        
        # Check for loading states
        if re.search(r'loading|isLoading', component_code, re.IGNORECASE):
            patterns.append('loading_state')
        
        # Check for error handling
        if re.search(r'error|isError|hasError', component_code, re.IGNORECASE):
            patterns.append('error_handling')
        
        # Check for disabled states
        if 'disabled' in component_code:
            patterns.append('disabled_state')
        
        return patterns

    def register_component(self, component_code: str, component_name: str):
        """Register a component for consistency tracking"""
        signature = self.analyze_component_signature(component_code, component_name)
        self.component_signatures[component_name] = signature
        
        # Update established patterns
        self._update_established_patterns(signature)

    def _update_established_patterns(self, signature: ComponentSignature):
        """Update established patterns based on new component"""
        # Update styling patterns
        for category, classes in signature.styling_patterns.items():
            if category not in self.established_patterns:
                self.established_patterns[category] = Counter()
            
            for cls in classes:
                self.established_patterns[category][cls] += 1
        
        # Update naming conventions
        for convention_type, convention in signature.naming_conventions.items():
            if convention_type not in self.established_patterns:
                self.established_patterns[convention_type] = Counter()
            
            self.established_patterns[convention_type][convention] += 1
        
        # Update structural patterns
        if 'structure_patterns' not in self.established_patterns:
            self.established_patterns['structure_patterns'] = Counter()
        
        for pattern in signature.structure_patterns:
            self.established_patterns['structure_patterns'][pattern] += 1

    def check_component_consistency(self, component_code: str, component_name: str) -> List[ConsistencyRule]:
        """Check a component against established consistency rules"""
        signature = self.analyze_component_signature(component_code, component_name)
        violations = []
        
        for rule in self.consistency_rules:
            violation = self._check_rule(signature, rule)
            if violation:
                violations.append(violation)
        
        return violations

    def _check_rule(self, signature: ComponentSignature, rule: ConsistencyRule) -> Optional[ConsistencyRule]:
        """Check a specific consistency rule against a component"""
        if rule.rule_type == ConsistencyType.STYLING.value:
            return self._check_styling_consistency(signature, rule)
        elif rule.rule_type == ConsistencyType.NAMING.value:
            return self._check_naming_consistency(signature, rule)
        elif rule.rule_type == ConsistencyType.STRUCTURE.value:
            return self._check_structure_consistency(signature, rule)
        elif rule.rule_type == ConsistencyType.ACCESSIBILITY.value:
            return self._check_accessibility_consistency(signature, rule)
        
        return None

    def _check_styling_consistency(self, signature: ComponentSignature, rule: ConsistencyRule) -> Optional[ConsistencyRule]:
        """Check styling consistency"""
        violations = []
        
        if rule.rule_id == "consistent_button_sizing":
            if 'button' in signature.name.lower():
                padding_classes = signature.styling_patterns.get('spacing', [])
                valid_patterns = ['px-2 py-1', 'px-4 py-2', 'px-6 py-3']
                
                current_padding = ' '.join([cls for cls in padding_classes if cls.startswith(('px-', 'py-'))])
                if current_padding and current_padding not in valid_patterns:
                    violations.append(f"Button {signature.name} uses non-standard padding: {current_padding}")
        
        elif rule.rule_id == "consistent_spacing":
            spacing_classes = signature.styling_patterns.get('spacing', [])
            arbitrary_spacing = [cls for cls in spacing_classes if re.match(r'[pm][xy]?-\[.+\]', cls)]
            if arbitrary_spacing:
                violations.append(f"Component uses arbitrary spacing: {arbitrary_spacing}")
        
        elif rule.rule_id == "consistent_color_usage":
            color_classes = signature.styling_patterns.get('colors', [])
            # Check if colors follow established patterns
            if self.established_patterns.get('colors'):
                common_colors = self.established_patterns['colors'].most_common(10)
                used_colors = set(color_classes)
                common_color_set = set([color for color, _ in common_colors])
                
                inconsistent_colors = used_colors - common_color_set
                if inconsistent_colors and len(used_colors) > 0:
                    consistency_ratio = len(common_color_set & used_colors) / len(used_colors)
                    if consistency_ratio < 0.7:  # Less than 70% consistency
                        violations.append(f"Component uses inconsistent colors: {inconsistent_colors}")
        
        if violations:
            violated_rule = ConsistencyRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                description=rule.description,
                pattern=rule.pattern,
                violations=violations,
                suggestions=rule.suggestions
            )
            return violated_rule
        
        return None

    def _check_naming_consistency(self, signature: ComponentSignature, rule: ConsistencyRule) -> Optional[ConsistencyRule]:
        """Check naming consistency"""
        violations = []
        
        if rule.rule_id == "consistent_prop_naming":
            # Check if prop naming follows established convention
            if self.established_patterns.get('prop_case'):
                most_common_case = self.established_patterns['prop_case'].most_common(1)[0][0]
                current_case = signature.naming_conventions.get('prop_case')
                
                if current_case and current_case != most_common_case:
                    violations.append(f"Component uses {current_case} while project uses {most_common_case}")
            
            # Check boolean prop naming
            boolean_props = [prop for prop in signature.props if re.match(r'^(is|has|can|should|will|did)[A-Z]', prop)]
            non_semantic_booleans = [prop for prop in signature.props if prop not in boolean_props and 
                                   any(word in prop.lower() for word in ['flag', 'check', 'toggle', 'enable', 'disable'])]
            
            if non_semantic_booleans:
                violations.append(f"Boolean props should use semantic prefixes: {non_semantic_booleans}")
        
        if violations:
            violated_rule = ConsistencyRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                description=rule.description,
                pattern=rule.pattern,
                violations=violations,
                suggestions=rule.suggestions
            )
            return violated_rule
        
        return None

    def _check_structure_consistency(self, signature: ComponentSignature, rule: ConsistencyRule) -> Optional[ConsistencyRule]:
        """Check structural consistency"""
        # Implementation for structural consistency checks
        # This could check for consistent use of hooks, component patterns, etc.
        return None

    def _check_accessibility_consistency(self, signature: ComponentSignature, rule: ConsistencyRule) -> Optional[ConsistencyRule]:
        """Check accessibility consistency"""
        violations = []
        
        if rule.rule_id == "consistent_accessibility":
            # This is a simplified check - in reality, you'd need to parse JSX more thoroughly
            component_code = ""  # Would need to store component code in signature
            
            # Check for interactive elements without proper accessibility
            if 'button' in signature.name.lower():
                if 'aria-label' not in component_code and 'children' not in signature.props:
                    violations.append("Icon buttons should have aria-label")
        
        if violations:
            violated_rule = ConsistencyRule(
                rule_id=rule.rule_id,
                rule_type=rule.rule_type,
                description=rule.description,
                pattern=rule.pattern,
                violations=violations,
                suggestions=rule.suggestions
            )
            return violated_rule
        
        return None

    def generate_consistency_report(self) -> ConsistencyReport:
        """Generate a comprehensive consistency report"""
        total_violations = []
        total_components = len(self.component_signatures)
        
        # Check all registered components
        for component_name, signature in self.component_signatures.items():
            # Would need to store component code to do full check
            # For now, generate report based on established patterns
            pass
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Generate style guide based on established patterns
        style_guide = self._generate_style_guide()
        
        return ConsistencyReport(
            total_components=total_components,
            consistency_score=consistency_score,
            violations=total_violations,
            recommendations=recommendations,
            style_guide=style_guide
        )

    def _calculate_consistency_score(self) -> float:
        """Calculate overall consistency score (0-100)"""
        if not self.component_signatures:
            return 100.0
        
        # Simple scoring based on pattern consistency
        scores = []
        
        # Styling consistency
        if self.established_patterns.get('colors'):
            color_consistency = self._calculate_pattern_consistency('colors')
            scores.append(color_consistency)
        
        # Naming consistency
        if self.established_patterns.get('prop_case'):
            naming_consistency = self._calculate_pattern_consistency('prop_case')
            scores.append(naming_consistency)
        
        return sum(scores) / len(scores) if scores else 100.0

    def _calculate_pattern_consistency(self, pattern_type: str) -> float:
        """Calculate consistency for a specific pattern type"""
        if pattern_type not in self.established_patterns:
            return 100.0
        
        pattern_counts = self.established_patterns[pattern_type]
        total_uses = sum(pattern_counts.values())
        
        if total_uses == 0:
            return 100.0
        
        # Calculate diversity - lower diversity = higher consistency
        unique_patterns = len(pattern_counts)
        most_common_usage = pattern_counts.most_common(1)[0][1]
        
        consistency = (most_common_usage / total_uses) * 100
        diversity_penalty = min(unique_patterns * 5, 30)  # Max 30% penalty
        
        return max(consistency - diversity_penalty, 0)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on established patterns"""
        recommendations = []
        
        # Color recommendations
        if self.established_patterns.get('colors'):
            most_common_colors = self.established_patterns['colors'].most_common(5)
            color_names = [color for color, _ in most_common_colors]
            recommendations.append(f"Use established colors: {', '.join(color_names)}")
        
        # Spacing recommendations
        if self.established_patterns.get('spacing'):
            most_common_spacing = self.established_patterns['spacing'].most_common(3)
            spacing_names = [spacing for spacing, _ in most_common_spacing]
            recommendations.append(f"Use consistent spacing: {', '.join(spacing_names)}")
        
        # Naming recommendations
        if self.established_patterns.get('prop_case'):
            most_common_case = self.established_patterns['prop_case'].most_common(1)[0][0]
            recommendations.append(f"Use {most_common_case} for prop naming")
        
        return recommendations

    def _generate_style_guide(self) -> Dict[str, str]:
        """Generate a style guide based on established patterns"""
        style_guide = {}
        
        # Colors
        if self.established_patterns.get('colors'):
            common_colors = self.established_patterns['colors'].most_common(10)
            style_guide['colors'] = ', '.join([color for color, _ in common_colors])
        
        # Spacing
        if self.established_patterns.get('spacing'):
            common_spacing = self.established_patterns['spacing'].most_common(10)
            style_guide['spacing'] = ', '.join([spacing for spacing, _ in common_spacing])
        
        # Typography
        if self.established_patterns.get('typography'):
            common_typography = self.established_patterns['typography'].most_common(5)
            style_guide['typography'] = ', '.join([typo for typo, _ in common_typography])
        
        return style_guide

    def get_consistency_context_for_generation(self) -> Dict[str, Any]:
        """Get consistency context for new component generation"""
        context = {}
        
        # Add established patterns
        if self.established_patterns:
            context['established_patterns'] = {}
            
            for pattern_type, pattern_counter in self.established_patterns.items():
                most_common = pattern_counter.most_common(5)
                context['established_patterns'][pattern_type] = [
                    pattern for pattern, _ in most_common
                ]
        
        # Add consistency rules
        context['consistency_rules'] = [rule.description for rule in self.consistency_rules]
        
        # Add style guide
        context['style_guide'] = self._generate_style_guide()
        
        # Add recommendations
        context['consistency_recommendations'] = self._generate_recommendations()
        
        return context

    def suggest_consistency_improvements(self, component_code: str, component_name: str) -> List[str]:
        """Suggest improvements to make a component more consistent"""
        violations = self.check_component_consistency(component_code, component_name)
        suggestions = []
        
        for violation in violations:
            suggestions.extend(violation.suggestions)
            suggestions.extend([f"Fix: {v}" for v in violation.violations])
        
        # Add general consistency suggestions
        if self.established_patterns:
            signature = self.analyze_component_signature(component_code, component_name)
            
            # Suggest consistent colors
            if signature.styling_patterns.get('colors'):
                established_colors = self.established_patterns.get('colors', Counter()).most_common(3)
                if established_colors:
                    color_names = [color for color, _ in established_colors]
                    suggestions.append(f"Consider using established project colors: {', '.join(color_names)}")
            
            # Suggest consistent spacing
            if signature.styling_patterns.get('spacing'):
                established_spacing = self.established_patterns.get('spacing', Counter()).most_common(3)
                if established_spacing:
                    spacing_names = [spacing for spacing, _ in established_spacing]
                    suggestions.append(f"Use consistent spacing patterns: {', '.join(spacing_names)}")
        
        return list(set(suggestions))  # Remove duplicates