"""
Base generation strategy interface and common functionality.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

from ...intelligence.styling_analyzer import StylingSystem


class GenerationQuality(Enum):
    """Quality levels for generated code."""
    EXCELLENT = "excellent"
    GOOD = "good" 
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ValidationIssue:
    """Represents a validation issue in generated code."""
    severity: str  # error, warning, info
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass 
class GenerationResult:
    """Result of code generation including metadata and validation."""
    code: str
    quality_score: float
    strategy_used: str
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    auto_fixes_applied: List[str] = field(default_factory=list)


@dataclass
class ComponentSpec:
    """Specification for component to be generated."""
    component_type: str
    complexity: str  # simple, moderate, complex
    requirements: List[str] = field(default_factory=list)
    styling_requirements: List[str] = field(default_factory=list)
    accessibility_requirements: List[str] = field(default_factory=list)


class GenerationStrategy(ABC):
    """
    Abstract base class for framework-specific generation strategies.
    Each strategy handles a specific framework/styling system combination.
    """
    
    def __init__(self, name: str, supported_systems: List[StylingSystem]):
        self.name = name
        self.supported_systems = supported_systems
        self.validation_rules = []
        self.forbidden_patterns = []
        self.required_patterns = []
    
    @abstractmethod
    def generate_component(self, prompt: str, context: Dict) -> GenerationResult:
        """
        Generate component code for this strategy.
        
        Args:
            prompt: User's component request
            context: Project context including styling system info
            
        Returns:
            GenerationResult with code and metadata
        """
        pass
    
    @abstractmethod
    def validate_generated_code(self, code: str) -> List[ValidationIssue]:
        """
        Validate generated code against strategy-specific rules.
        
        Args:
            code: Generated component code
            
        Returns:
            List of validation issues found
        """
        pass
    
    def analyze_requirements(self, prompt: str) -> ComponentSpec:
        """
        Analyze user prompt to extract component requirements.
        
        Args:
            prompt: User's component request
            
        Returns:
            ComponentSpec with analyzed requirements
        """
        prompt_lower = prompt.lower()
        
        # Determine component type
        component_type = self._extract_component_type(prompt_lower)
        
        # Determine complexity
        complexity = self._assess_complexity(prompt_lower)
        
        # Extract requirements
        requirements = self._extract_requirements(prompt_lower)
        styling_requirements = self._extract_styling_requirements(prompt_lower)
        accessibility_requirements = self._extract_accessibility_requirements(prompt_lower)
        
        return ComponentSpec(
            component_type=component_type,
            complexity=complexity,
            requirements=requirements,
            styling_requirements=styling_requirements,
            accessibility_requirements=accessibility_requirements
        )
    
    def _extract_component_type(self, prompt: str) -> str:
        """Extract the main component type from prompt."""
        # Common component types in order of specificity
        component_types = [
            "navigation", "navbar", "sidebar", "modal", "dialog", "dropdown",
            "accordion", "tabs", "carousel", "table", "form", "button", "card",
            "list", "input", "checkbox", "radio", "toggle", "select", "hero",
            "dashboard", "profile", "chart", "calendar"
        ]
        
        for comp_type in component_types:
            if comp_type in prompt:
                return comp_type
        
        return "component"  # Default fallback
    
    def _assess_complexity(self, prompt: str) -> str:
        """Assess component complexity from prompt."""
        complexity_indicators = {
            "complex": ["dashboard", "table with", "form with", "multi-step", "advanced", "complex"],
            "moderate": ["with dropdown", "with menu", "with tabs", "responsive", "interactive"],
            "simple": ["button", "input", "text", "simple", "basic"]
        }
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in prompt for indicator in indicators):
                return complexity
        
        return "moderate"  # Default
    
    def _extract_requirements(self, prompt: str) -> List[str]:
        """Extract functional requirements from prompt."""
        requirements = []
        
        requirement_patterns = {
            "responsive": ["responsive", "mobile", "tablet", "desktop"],
            "interactive": ["click", "hover", "focus", "interactive"],
            "accessible": ["accessible", "aria", "screen reader", "a11y"],
            "animated": ["animate", "transition", "animation", "motion"],
            "themed": ["theme", "dark mode", "light mode", "color scheme"]
        }
        
        for req_type, patterns in requirement_patterns.items():
            if any(pattern in prompt for pattern in patterns):
                requirements.append(req_type)
        
        return requirements
    
    def _extract_styling_requirements(self, prompt: str) -> List[str]:
        """Extract styling-specific requirements."""
        styling_reqs = []
        
        styling_patterns = {
            "gradient": ["gradient", "linear-gradient", "radial-gradient"],
            "shadow": ["shadow", "drop-shadow", "box-shadow"],
            "rounded": ["rounded", "border-radius", "circular"],
            "bordered": ["border", "outline", "stroke"],
            "elevated": ["elevated", "raised", "card-like"]
        }
        
        for style_type, patterns in styling_patterns.items():
            if any(pattern in prompt for pattern in patterns):
                styling_reqs.append(style_type)
        
        return styling_reqs
    
    def _extract_accessibility_requirements(self, prompt: str) -> List[str]:
        """Extract accessibility requirements."""
        a11y_reqs = []
        
        a11y_patterns = {
            "keyboard_navigation": ["keyboard", "tab", "navigation", "focus"],
            "screen_reader": ["screen reader", "aria", "alt text", "label"],
            "high_contrast": ["contrast", "accessibility", "a11y"],
            "motion_reduced": ["motion", "animation", "prefers-reduced-motion"]
        }
        
        for a11y_type, patterns in a11y_patterns.items():
            if any(pattern in prompt for pattern in patterns):
                a11y_reqs.append(a11y_type)
        
        return a11y_reqs
    
    def apply_post_generation_fixes(self, code: str) -> Tuple[str, List[str]]:
        """
        Apply automatic fixes to generated code.
        
        Args:
            code: Generated code to fix
            
        Returns:
            Tuple of (fixed_code, fixes_applied)
        """
        fixes_applied = []
        current_code = code
        
        # Apply strategy-specific fixes
        for fix_method in self._get_fix_methods():
            fixed_code, fix_description = fix_method(current_code)
            if fixed_code != current_code:
                fixes_applied.append(fix_description)
                current_code = fixed_code
        
        return current_code, fixes_applied
    
    def _get_fix_methods(self) -> List:
        """Get list of fix methods for this strategy. Override in subclasses."""
        return [
            self._fix_imports,
            self._fix_typescript_issues,
            self._fix_formatting
        ]
    
    def _fix_imports(self, code: str) -> Tuple[str, str]:
        """Fix import statements. Override in subclasses."""
        return code, ""
    
    def _fix_typescript_issues(self, code: str) -> Tuple[str, str]:
        """Fix TypeScript issues."""
        fixes_applied = []
        
        # Add React import if JSX is used but React not imported
        if '<' in code and 'React' not in code and 'import React' not in code:
            code = "import React from 'react';\n" + code
            fixes_applied.append("Added React import")
        
        # Add interface for props if component has props but no interface
        if 'props' in code and 'interface' not in code and 'type' not in code:
            # Simple interface generation
            interface = "interface Props {\n  // Add prop types here\n}\n\n"
            code = interface + code
            fixes_applied.append("Added Props interface")
        
        return code, "; ".join(fixes_applied) if fixes_applied else ""
    
    def _fix_formatting(self, code: str) -> Tuple[str, str]:
        """Fix basic formatting issues."""
        fixes_applied = []
        
        # Ensure proper spacing around braces
        if re.search(r'\w{', code):
            code = re.sub(r'(\w){', r'\1 {', code)
            fixes_applied.append("Fixed brace spacing")
        
        # Ensure semicolons at end of statements (basic)
        lines = code.split('\n')
        fixed_lines = []
        for line in lines:
            stripped = line.strip()
            if (stripped and not stripped.endswith((';', '{', '}', '>', '//', '/*', '*/')) 
                and not stripped.startswith(('import', 'export', 'interface', 'type', '//'))):
                if not any(keyword in stripped for keyword in ['if', 'for', 'while', 'function', 'const', 'let', 'var']):
                    line += ';'
                    fixes_applied.append("Added missing semicolon")
            fixed_lines.append(line)
        
        if fixes_applied:
            code = '\n'.join(fixed_lines)
        
        return code, "; ".join(fixes_applied) if fixes_applied else ""
    
    def calculate_quality_score(self, 
                               code: str, 
                               validation_issues: List[ValidationIssue]) -> float:
        """
        Calculate quality score for generated code.
        
        Args:
            code: Generated code
            validation_issues: List of validation issues
            
        Returns:
            Quality score from 0.0 to 1.0
        """
        base_score = 0.8  # Start with good baseline
        
        # Deduct for validation issues
        for issue in validation_issues:
            if issue.severity == "error":
                base_score -= 0.2
            elif issue.severity == "warning":
                base_score -= 0.1
            elif issue.severity == "info":
                base_score -= 0.05
        
        # Bonus for good patterns
        if self._has_good_patterns(code):
            base_score += 0.1
        
        # Bonus for accessibility
        if self._has_accessibility_features(code):
            base_score += 0.05
        
        # Bonus for TypeScript
        if self._has_typescript_features(code):
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def _has_good_patterns(self, code: str) -> bool:
        """Check if code follows good patterns."""
        good_patterns = [
            r'interface \w+Props',  # TypeScript interfaces
            r'export default',      # Proper exports
            r'aria-\w+',           # Accessibility
            r'className=',         # Proper styling
        ]
        
        return any(re.search(pattern, code) for pattern in good_patterns)
    
    def _has_accessibility_features(self, code: str) -> bool:
        """Check if code has accessibility features."""
        a11y_patterns = [
            r'aria-\w+',
            r'alt=',
            r'role=',
            r'tabIndex',
            r'onKeyDown',
            r'onKeyPress'
        ]
        
        return any(re.search(pattern, code) for pattern in a11y_patterns)
    
    def _has_typescript_features(self, code: str) -> bool:
        """Check if code uses TypeScript features."""
        ts_patterns = [
            r'interface \w+',
            r'type \w+',
            r': \w+\[\]',
            r': \w+\|',
            r'<\w+>'
        ]
        
        return any(re.search(pattern, code) for pattern in ts_patterns)
    
    def supports_system(self, system: StylingSystem) -> bool:
        """Check if this strategy supports a styling system."""
        return system in self.supported_systems
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get information about this strategy."""
        return {
            'name': self.name,
            'supported_systems': [system.value for system in self.supported_systems],
            'validation_rules_count': len(self.validation_rules),
            'forbidden_patterns_count': len(self.forbidden_patterns),
            'required_patterns_count': len(self.required_patterns)
        }