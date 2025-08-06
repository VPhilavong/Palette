"""
Configuration-Aware Quality Pipeline.
Multi-stage quality assurance pipeline that adapts validation based on project configuration.
Ensures generated code meets framework and styling system specific requirements.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set

from .validator import ComponentValidator, QualityReport, ValidationIssue, ValidationLevel
from ..intelligence.configuration_hub import ProjectConfiguration, Framework
from ..intelligence.styling_analyzer import StylingSystem
from ..generation.strategies.base import ValidationIssue as StrategyValidationIssue
from ..errors.decorators import handle_errors


class ValidationStage(Enum):
    """Stages in the quality validation pipeline."""
    SYNTAX = "syntax"
    IMPORTS = "imports"
    FRAMEWORK_COMPLIANCE = "framework_compliance"
    STYLING_CONSISTENCY = "styling_consistency"
    ACCESSIBILITY = "accessibility"
    PATTERN_MATCHING = "pattern_matching"
    CONFIGURATION_SPECIFIC = "configuration_specific"


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"    # Prevents code from working
    ERROR = "error"          # Likely to cause issues
    WARNING = "warning"      # Best practices violation
    INFO = "info"           # Suggestions for improvement


@dataclass
class ConfigurationValidationRule:
    """A configuration-specific validation rule."""
    name: str
    description: str
    stage: ValidationStage
    severity: ValidationSeverity
    pattern: Optional[str] = None
    checker_function: Optional[callable] = None
    auto_fix_function: Optional[callable] = None
    applicable_frameworks: List[Framework] = field(default_factory=list)
    applicable_styling_systems: List[StylingSystem] = field(default_factory=list)


@dataclass
class QualityPipelineResult:
    """Result from the quality pipeline."""
    final_code: str
    quality_score: float
    stages_passed: List[ValidationStage]
    issues_found: List[ValidationIssue] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    configuration_compliance: Dict[str, bool] = field(default_factory=dict)
    stage_results: Dict[ValidationStage, Dict[str, Any]] = field(default_factory=dict)
    pipeline_metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationAwareQualityPipeline:
    """
    Multi-stage quality assurance pipeline with configuration awareness.
    
    Provides comprehensive validation that adapts to:
    1. Framework-specific requirements (Next.js, React, etc.)
    2. Styling system requirements (Chakra UI, Tailwind, etc.)
    3. Project-specific patterns and conventions
    4. Quality thresholds and auto-fixing capabilities
    """
    
    def __init__(self):
        self.base_validator = None  # Will be initialized when needed with project path
        self.validation_rules: Dict[str, ConfigurationValidationRule] = {}
        
        # Initialize configuration-specific rules
        self._initialize_framework_rules()
        self._initialize_styling_rules()
        self._initialize_accessibility_rules()
        self._initialize_pattern_rules()
    
    def _initialize_framework_rules(self):
        """Initialize framework-specific validation rules."""
        
        # Next.js specific rules
        self.add_validation_rule(ConfigurationValidationRule(
            name="nextjs_use_client",
            description="Client components must use 'use client' directive",
            stage=ValidationStage.FRAMEWORK_COMPLIANCE,
            severity=ValidationSeverity.ERROR,
            pattern=r'useState|useEffect|onClick|onChange',
            checker_function=self._check_nextjs_client_directive,
            auto_fix_function=self._fix_nextjs_client_directive,
            applicable_frameworks=[Framework.NEXT_JS]
        ))
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="nextjs_image_component",
            description="Use next/image instead of img tag",
            stage=ValidationStage.FRAMEWORK_COMPLIANCE,
            severity=ValidationSeverity.WARNING,
            pattern=r'<img\s',
            checker_function=self._check_nextjs_image_usage,
            auto_fix_function=self._fix_nextjs_image_usage,
            applicable_frameworks=[Framework.NEXT_JS]
        ))
        
        # React specific rules
        self.add_validation_rule(ConfigurationValidationRule(
            name="react_hooks_rules",
            description="Hooks must be called at the top level",
            stage=ValidationStage.FRAMEWORK_COMPLIANCE,
            severity=ValidationSeverity.ERROR,
            checker_function=self._check_react_hooks_rules,
            applicable_frameworks=[Framework.REACT, Framework.NEXT_JS, Framework.VITE_REACT]
        ))
        
        # TypeScript rules
        self.add_validation_rule(ConfigurationValidationRule(
            name="typescript_interfaces",
            description="Components should have proper TypeScript interfaces",
            stage=ValidationStage.FRAMEWORK_COMPLIANCE,
            severity=ValidationSeverity.WARNING,
            checker_function=self._check_typescript_interfaces,
            auto_fix_function=self._fix_typescript_interfaces,
            applicable_frameworks=[Framework.NEXT_JS, Framework.REACT, Framework.VITE_REACT]
        ))
    
    def _initialize_styling_rules(self):
        """Initialize styling system-specific validation rules."""
        
        # Chakra UI rules (CRITICAL for fixing framework detection issues)
        self.add_validation_rule(ConfigurationValidationRule(
            name="chakra_no_tailwind_classes",
            description="CRITICAL: No Tailwind CSS classes allowed in Chakra UI projects",
            stage=ValidationStage.STYLING_CONSISTENCY,
            severity=ValidationSeverity.CRITICAL,
            pattern=r'className="[^"]*(?:bg-|text-|p-|m-|w-|h-|flex|grid)[^"]*"',
            checker_function=self._check_chakra_no_tailwind,
            auto_fix_function=self._fix_chakra_tailwind_classes,
            applicable_styling_systems=[StylingSystem.CHAKRA_UI]
        ))
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="chakra_imports",
            description="Must import from @chakra-ui/react",
            stage=ValidationStage.IMPORTS,
            severity=ValidationSeverity.ERROR,
            pattern=r'@chakra-ui/react',
            checker_function=self._check_chakra_imports,
            auto_fix_function=self._fix_chakra_imports,
            applicable_styling_systems=[StylingSystem.CHAKRA_UI]
        ))
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="chakra_component_usage",
            description="Should use Chakra UI components instead of HTML elements",
            stage=ValidationStage.STYLING_CONSISTENCY,
            severity=ValidationSeverity.WARNING,
            checker_function=self._check_chakra_component_usage,
            auto_fix_function=self._fix_chakra_component_usage,
            applicable_styling_systems=[StylingSystem.CHAKRA_UI]
        ))
        
        # Tailwind CSS rules
        self.add_validation_rule(ConfigurationValidationRule(
            name="tailwind_valid_classes",
            description="Use valid Tailwind CSS classes",
            stage=ValidationStage.STYLING_CONSISTENCY,
            severity=ValidationSeverity.ERROR,
            checker_function=self._check_tailwind_valid_classes,
            applicable_styling_systems=[StylingSystem.TAILWIND]
        ))
        
        # Material-UI rules
        self.add_validation_rule(ConfigurationValidationRule(
            name="mui_imports",
            description="Must import from @mui/material",
            stage=ValidationStage.IMPORTS,
            severity=ValidationSeverity.ERROR,
            pattern=r'@mui/material',
            checker_function=self._check_mui_imports,
            applicable_styling_systems=[StylingSystem.MATERIAL_UI]
        ))
    
    def _initialize_accessibility_rules(self):
        """Initialize accessibility validation rules."""
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="aria_labels",
            description="Interactive elements should have aria-labels",
            stage=ValidationStage.ACCESSIBILITY,
            severity=ValidationSeverity.WARNING,
            checker_function=self._check_aria_labels
        ))
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="button_accessibility", 
            description="Buttons should be accessible",
            stage=ValidationStage.ACCESSIBILITY,
            severity=ValidationSeverity.WARNING,
            checker_function=self._check_button_accessibility,
            auto_fix_function=self._fix_button_accessibility
        ))
    
    def _initialize_pattern_rules(self):
        """Initialize pattern matching validation rules."""
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="component_naming",
            description="Components should follow naming conventions",
            stage=ValidationStage.PATTERN_MATCHING,
            severity=ValidationSeverity.INFO,
            checker_function=self._check_component_naming
        ))
        
        self.add_validation_rule(ConfigurationValidationRule(
            name="export_default",
            description="Component should have default export",
            stage=ValidationStage.PATTERN_MATCHING,
            severity=ValidationSeverity.WARNING,
            pattern=r'export\s+default',
            checker_function=self._check_default_export,
            auto_fix_function=self._fix_default_export
        ))
    
    def add_validation_rule(self, rule: ConfigurationValidationRule):
        """Add a custom validation rule."""
        self.validation_rules[rule.name] = rule
    
    @handle_errors(reraise=True)
    def validate_and_fix(
        self,
        code: str,
        configuration: ProjectConfiguration,
        target_path: str = "Component.tsx",
        max_iterations: int = 3
    ) -> QualityPipelineResult:
        """
        Run the complete quality pipeline with configuration awareness.
        
        Args:
            code: Generated code to validate
            configuration: Project configuration
            target_path: Target file path
            max_iterations: Maximum fix iterations
            
        Returns:
            Comprehensive quality pipeline result
        """
        
        print(f"🔍 Starting quality pipeline for {configuration.framework.value} + {configuration.styling_system.value}")
        
        # Initialize base validator if needed
        if self.base_validator is None:
            # Extract project path from target_path or use current directory
            import os
            project_path = os.path.dirname(target_path) if target_path else "."
            self.base_validator = ComponentValidator(project_path)
        
        current_code = code
        all_issues = []
        all_fixes = []
        stages_passed = []
        stage_results = {}
        
        # Get applicable rules for this configuration
        applicable_rules = self._get_applicable_rules(configuration)
        print(f"📋 Running {len(applicable_rules)} configuration-specific validation rules")
        
        # Run validation stages in order
        validation_stages = [
            ValidationStage.SYNTAX,
            ValidationStage.IMPORTS,
            ValidationStage.FRAMEWORK_COMPLIANCE,
            ValidationStage.STYLING_CONSISTENCY,
            ValidationStage.ACCESSIBILITY,
            ValidationStage.PATTERN_MATCHING,
            ValidationStage.CONFIGURATION_SPECIFIC
        ]
        
        for iteration in range(max_iterations):
            print(f"🔄 Quality iteration {iteration + 1}/{max_iterations}")
            
            iteration_issues = []
            iteration_fixes = []
            
            for stage in validation_stages:
                stage_issues, stage_fixes, stage_passed = self._run_validation_stage(
                    current_code, stage, applicable_rules, configuration
                )
                
                iteration_issues.extend(stage_issues)
                iteration_fixes.extend(stage_fixes)
                
                if stage_passed:
                    stages_passed.append(stage)
                
                # Apply fixes from this stage
                if stage_fixes:
                    for fix_description, fixed_code in stage_fixes:
                        current_code = fixed_code
                        print(f"   ✅ {fix_description}")
                
                # Record stage results
                stage_results[stage] = {
                    'issues_count': len(stage_issues),
                    'fixes_applied': len(stage_fixes),
                    'passed': stage_passed
                }
            
            all_issues.extend(iteration_issues)
            all_fixes.extend([fix[0] for fix in iteration_fixes])
            
            # Check if we have critical issues remaining
            critical_issues = [issue for issue in iteration_issues if issue.level.value == 'error']
            if not critical_issues:
                print(f"✅ No critical issues remaining after iteration {iteration + 1}")
                break
            else:
                print(f"⚠️ {len(critical_issues)} critical issues remaining")
        
        # Calculate final quality score
        quality_score = self._calculate_quality_score(current_code, all_issues, configuration)
        
        # Check configuration compliance
        compliance = self._check_configuration_compliance(current_code, configuration)
        
        result = QualityPipelineResult(
            final_code=current_code,
            quality_score=quality_score,
            stages_passed=list(set(stages_passed)),
            issues_found=all_issues,
            fixes_applied=all_fixes,
            configuration_compliance=compliance,
            stage_results=stage_results,
            pipeline_metadata={
                'iterations': iteration + 1,
                'rules_applied': len(applicable_rules),
                'configuration': {
                    'framework': configuration.framework.value,
                    'styling_system': configuration.styling_system.value,
                    'confidence': configuration.confidence_score
                }
            }
        )
        
        print(f"🎯 Final quality score: {quality_score:.1f}/100")
        print(f"🔧 Applied {len(all_fixes)} fixes across {len(set(stages_passed))} stages")
        
        return result
    
    def _get_applicable_rules(self, configuration: ProjectConfiguration) -> List[ConfigurationValidationRule]:
        """Get validation rules applicable to the configuration."""
        
        applicable_rules = []
        
        for rule in self.validation_rules.values():
            # Check if rule applies to this framework
            if rule.applicable_frameworks and configuration.framework not in rule.applicable_frameworks:
                continue
            
            # Check if rule applies to this styling system
            if rule.applicable_styling_systems and configuration.styling_system not in rule.applicable_styling_systems:
                continue
            
            applicable_rules.append(rule)
        
        return applicable_rules
    
    def _run_validation_stage(
        self,
        code: str,
        stage: ValidationStage,
        applicable_rules: List[ConfigurationValidationRule],
        configuration: ProjectConfiguration
    ) -> Tuple[List[ValidationIssue], List[Tuple[str, str]], bool]:
        """Run a specific validation stage."""
        
        stage_rules = [rule for rule in applicable_rules if rule.stage == stage]
        if not stage_rules:
            return [], [], True
        
        stage_issues = []
        stage_fixes = []
        
        for rule in stage_rules:
            # Run the validation rule
            issues = self._run_validation_rule(code, rule)
            stage_issues.extend(issues)
            
            # Apply auto-fixes if available
            if rule.auto_fix_function and issues:
                try:
                    fixed_code = rule.auto_fix_function(code)
                    if fixed_code != code:
                        stage_fixes.append((f"Applied {rule.name} fix", fixed_code))
                        code = fixed_code  # Update code for next rule
                except Exception as e:
                    print(f"⚠️ Auto-fix for {rule.name} failed: {e}")
        
        # Stage passes if no critical or error issues
        critical_or_error_issues = [
            issue for issue in stage_issues 
            if issue.level.value == 'error'  # All critical and error issues are now mapped to ERROR level
        ]
        stage_passed = len(critical_or_error_issues) == 0
        
        return stage_issues, stage_fixes, stage_passed
    
    def _run_validation_rule(self, code: str, rule: ConfigurationValidationRule) -> List[ValidationIssue]:
        """Run a single validation rule."""
        
        issues = []
        
        try:
            if rule.checker_function:
                # Use custom checker function
                rule_issues = rule.checker_function(code)
                if isinstance(rule_issues, list):
                    issues.extend(rule_issues)
                elif rule_issues:  # Single issue or boolean
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR if rule.severity == ValidationSeverity.CRITICAL or rule.severity == ValidationSeverity.ERROR else ValidationLevel.WARNING,
                        category=rule.name,
                        message=rule.description,
                        line=None,
                        suggestion=f"Apply {rule.name} fix"
                    ))
            
            elif rule.pattern:
                # Use regex pattern matching
                matches = re.findall(rule.pattern, code, re.MULTILINE)
                if matches:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR if rule.severity == ValidationSeverity.CRITICAL or rule.severity == ValidationSeverity.ERROR else ValidationLevel.WARNING,
                        category=rule.name,
                        message=f"{rule.description}: Found {len(matches)} violations",
                        line=None,
                        suggestion=f"Fix {rule.name} violations"
                    ))
        
        except Exception as e:
            print(f"⚠️ Error running validation rule {rule.name}: {e}")
        
        return issues
    
    # Framework-specific validation methods
    
    def _check_nextjs_client_directive(self, code: str) -> List[ValidationIssue]:
        """Check if Next.js client components have 'use client' directive."""
        issues = []
        
        # Check if code uses client-side features
        client_features = ['useState', 'useEffect', 'onClick', 'onChange', 'onSubmit']
        uses_client_features = any(feature in code for feature in client_features)
        
        if uses_client_features and 'use client' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="nextjs_use_client",
                message="Client component missing 'use client' directive",
                suggestion="Add 'use client' at the top of the file"
            ))
        
        return issues
    
    def _fix_nextjs_client_directive(self, code: str) -> str:
        """Fix Next.js client directive issue."""
        if 'use client' not in code:
            return "'use client';\n\n" + code
        return code
    
    def _check_nextjs_image_usage(self, code: str) -> List[ValidationIssue]:
        """Check for img tag usage instead of next/image."""
        issues = []
        
        img_tags = re.findall(r'<img\s[^>]*>', code)
        if img_tags:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="nextjs_image_usage",
                message=f"Found {len(img_tags)} img tags - consider using next/image",
                suggestion="Replace <img> with Next.js Image component"
            ))
        
        return issues
    
    def _fix_nextjs_image_usage(self, code: str) -> str:
        """Fix Next.js image usage."""
        # Add import if not present
        if 'next/image' not in code and '<img' in code:
            code = "import Image from 'next/image';\n" + code
        
        # Replace simple img tags (basic replacement)
        code = re.sub(
            r'<img\s+src="([^"]+)"\s+alt="([^"]+)"[^>]*>',
            r'<Image src="\1" alt="\2" width={500} height={300} />',
            code
        )
        
        return code
    
    def _check_react_hooks_rules(self, code: str) -> List[ValidationIssue]:
        """Check React hooks rules."""
        issues = []
        
        # Check for hooks in conditions or loops (basic check)
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'use[A-Z]\w*\(', line):  # Hook usage
                # Check if it's inside a condition or loop
                indent_level = len(line) - len(line.lstrip())
                if indent_level > 8:  # Likely inside nested structure
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="react_hooks_rules",
                        message="Hooks should be called at the top level",
                        line=i + 1,
                        suggestion="Move hook to component top level"
                    ))
        
        return issues
    
    def _check_typescript_interfaces(self, code: str) -> List[ValidationIssue]:
        """Check TypeScript interfaces."""
        issues = []
        
        # Check if component has props but no interface
        has_props = 'props' in code or ': React.FC<' in code
        has_interface = 'interface' in code or 'type' in code
        
        if has_props and not has_interface:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="typescript_interfaces",
                message="Component with props should have TypeScript interface",
                suggestion="Add proper TypeScript interface for props"
            ))
        
        return issues
    
    def _fix_typescript_interfaces(self, code: str) -> str:
        """Fix TypeScript interfaces."""
        if 'props' in code and 'interface' not in code:
            # Add basic interface
            interface = "interface Props {\n  // Define your props here\n}\n\n"
            return interface + code
        return code
    
    # Styling-specific validation methods (CRITICAL for framework detection fixes)
    
    def _check_chakra_no_tailwind(self, code: str) -> List[ValidationIssue]:
        """CRITICAL: Check for Tailwind classes in Chakra UI code."""
        issues = []
        
        # Patterns for Tailwind classes
        tailwind_patterns = [
            r'className="[^"]*bg-(?:red|blue|green|gray|slate|zinc|neutral|stone|amber|yellow|lime|emerald|teal|cyan|sky|indigo|violet|purple|fuchsia|pink|rose)-\d+',
            r'className="[^"]*text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)',
            r'className="[^"]*(?:p|px|py|pt|pb|pl|pr)-\d+',
            r'className="[^"]*(?:m|mx|my|mt|mb|ml|mr)-\d+',
            r'className="[^"]*(?:w|h)-(?:full|screen|\d+)',
            r'className="[^"]*(?:flex|grid|block|inline|hidden)'
        ]
        
        for pattern in tailwind_patterns:
            matches = re.findall(pattern, code)
            if matches:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="chakra_no_tailwind",
                    message=f"CRITICAL: Tailwind classes found in Chakra UI code: {matches[:3]}",
                    suggestion="Use Chakra UI component props instead of CSS classes"
                ))
        
        return issues
    
    def _fix_chakra_tailwind_classes(self, code: str) -> str:
        """CRITICAL: Fix Tailwind classes in Chakra UI code."""
        
        # Common Tailwind to Chakra conversions
        conversions = [
            # Colors
            (r'className="([^"]*)?bg-blue-(\d+)([^"]*?)"', r'bg="blue.\2"'),
            (r'className="([^"]*)?bg-red-(\d+)([^"]*?)"', r'bg="red.\2"'),
            (r'className="([^"]*)?bg-green-(\d+)([^"]*?)"', r'bg="green.\2"'),
            (r'className="([^"]*)?text-blue-(\d+)([^"]*?)"', r'color="blue.\2"'),
            (r'className="([^"]*)?text-red-(\d+)([^"]*?)"', r'color="red.\2"'),
            
            # Spacing
            (r'className="([^"]*)?p-(\d+)([^"]*?)"', r'p={\2}'),
            (r'className="([^"]*)?px-(\d+)([^"]*?)"', r'px={\2}'),
            (r'className="([^"]*)?py-(\d+)([^"]*?)"', r'py={\2}'),
            (r'className="([^"]*)?m-(\d+)([^"]*?)"', r'm={\2}'),
            
            # Size
            (r'className="([^"]*)?w-full([^"]*?)"', r'w="full"'),
            (r'className="([^"]*)?h-full([^"]*?)"', r'h="full"'),
            
            # Border radius
            (r'className="([^"]*)?rounded-lg([^"]*?)"', r'rounded="lg"'),
            (r'className="([^"]*)?rounded-md([^"]*?)"', r'rounded="md"'),
            
            # Shadow
            (r'className="([^"]*)?shadow-md([^"]*?)"', r'shadow="md"'),
            (r'className="([^"]*)?shadow-lg([^"]*?)"', r'shadow="lg"'),
        ]
        
        for pattern, replacement in conversions:
            code = re.sub(pattern, replacement, code)
        
        # Remove empty className attributes
        code = re.sub(r'className=""\s*', '', code)
        code = re.sub(r'className="[\s]*"\s*', '', code)
        
        return code
    
    def _check_chakra_imports(self, code: str) -> List[ValidationIssue]:
        """Check Chakra UI imports."""
        issues = []
        
        # Check if Chakra components are used but not imported
        chakra_components = ['Box', 'Button', 'Text', 'Flex', 'Stack', 'VStack', 'HStack']
        used_components = []
        
        for component in chakra_components:
            if f'<{component}' in code:
                used_components.append(component)
        
        if used_components and '@chakra-ui/react' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="chakra_imports",
                message=f"Missing Chakra UI imports for: {', '.join(used_components)}",
                suggestion="Add import from @chakra-ui/react"
            ))
        
        return issues
    
    def _fix_chakra_imports(self, code: str) -> str:
        """Fix Chakra UI imports."""
        chakra_components = ['Box', 'Button', 'Text', 'Flex', 'Stack', 'VStack', 'HStack']
        used_components = []
        
        for component in chakra_components:
            if f'<{component}' in code and component not in used_components:
                used_components.append(component)
        
        if used_components and '@chakra-ui/react' not in code:
            import_statement = f"import {{ {', '.join(used_components)} }} from '@chakra-ui/react';\n"
            
            # Add after React import if present
            if 'import React' in code:
                code = code.replace(
                    'import React from \'react\';',
                    'import React from \'react\';\n' + import_statement
                )
            else:
                code = "import React from 'react';\n" + import_statement + code
        
        return code
    
    def _check_chakra_component_usage(self, code: str) -> List[ValidationIssue]:
        """Check Chakra UI component usage."""
        issues = []
        
        # Check for HTML elements that should be Chakra components
        html_to_chakra = {
            '<div': '<Box',
            '<button': '<Button',
            '<p>': '<Text>',
            '<span': '<Text as="span"'
        }
        
        for html_element, chakra_component in html_to_chakra.items():
            if html_element in code:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="chakra_component_usage",
                    message=f"Consider using {chakra_component} instead of {html_element}",
                    suggestion=f"Replace {html_element} with Chakra UI component"
                ))
        
        return issues
    
    def _fix_chakra_component_usage(self, code: str) -> str:
        """Fix Chakra UI component usage."""
        html_to_chakra = {
            '<div': '<Box',
            '</div>': '</Box>',
            '<button': '<Button',
            '</button>': '</Button>',
            '<p>': '<Text>',
            '</p>': '</Text>',
        }
        
        for html_element, chakra_component in html_to_chakra.items():
            code = code.replace(html_element, chakra_component)
        
        return code
    
    def _check_tailwind_valid_classes(self, code: str) -> List[ValidationIssue]:
        """Check for valid Tailwind classes."""
        # This would require a comprehensive list of valid Tailwind classes
        # For now, just check for common invalid patterns
        issues = []
        
        invalid_patterns = [
            r'className="[^"]*bg-\d+-\d+',  # Invalid color format
            r'className="[^"]*text-\d+px',  # Invalid size format
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="tailwind_valid_classes",
                    message="Invalid Tailwind class format detected",
                    suggestion="Use valid Tailwind class names"
                ))
        
        return issues
    
    def _check_mui_imports(self, code: str) -> List[ValidationIssue]:
        """Check Material-UI imports."""
        issues = []
        
        mui_components = ['Button', 'Box', 'Typography', 'Container', 'Grid']
        used_components = []
        
        for component in mui_components:
            if f'<{component}' in code:
                used_components.append(component)
        
        if used_components and '@mui/material' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="mui_imports",
                message=f"Missing Material-UI imports for: {', '.join(used_components)}",
                suggestion="Add import from @mui/material"
            ))
        
        return issues
    
    # Accessibility validation methods
    
    def _check_aria_labels(self, code: str) -> List[ValidationIssue]:
        """Check for aria-labels on interactive elements."""
        issues = []
        
        # Check for buttons without aria-label or text content
        button_pattern = r'<Button[^>]*>[\s]*</Button>'
        if re.search(button_pattern, code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="aria_labels",
                message="Button without text content should have aria-label",
                suggestion="Add aria-label or text content to buttons"
            ))
        
        return issues
    
    def _check_button_accessibility(self, code: str) -> List[ValidationIssue]:
        """Check button accessibility."""
        issues = []
        
        # Check for buttons with only icons
        icon_button_pattern = r'<Button[^>]*><[^>]*Icon[^>]*></Button>'
        if re.search(icon_button_pattern, code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="button_accessibility",
                message="Icon buttons should have aria-label for accessibility",
                suggestion="Add aria-label to icon buttons"
            ))
        
        return issues
    
    def _fix_button_accessibility(self, code: str) -> str:
        """Fix button accessibility issues."""
        # Add aria-label to icon buttons (basic fix)
        code = re.sub(
            r'(<Button[^>]*>)(<[^>]*Icon[^>]*>)(</Button>)',
            r'\1<Button aria-label="Button">\2\3',
            code
        )
        return code
    
    # Pattern validation methods
    
    def _check_component_naming(self, code: str) -> List[ValidationIssue]:
        """Check component naming conventions."""
        issues = []
        
        # Check for PascalCase component names
        component_pattern = r'(?:const|function)\s+([a-z][a-zA-Z0-9]*)\s*[=:].*React\.FC'
        matches = re.findall(component_pattern, code)
        
        if matches:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="component_naming",
                message=f"Component names should use PascalCase: {matches}",
                suggestion="Use PascalCase for component names"
            ))
        
        return issues
    
    def _check_default_export(self, code: str) -> List[ValidationIssue]:
        """Check for default export."""
        issues = []
        
        if 'export default' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="default_export",
                message="Component should have default export",
                suggestion="Add export default statement"
            ))
        
        return issues
    
    def _fix_default_export(self, code: str) -> str:
        """Fix default export."""
        if 'export default' not in code:
            # Try to find component name and add export
            component_match = re.search(r'(?:const|function)\s+([A-Z][a-zA-Z0-9]*)', code)
            if component_match:
                component_name = component_match.group(1)
                code += f'\n\nexport default {component_name};'
        return code
    
    def _calculate_quality_score(
        self, 
        code: str, 
        issues: List[ValidationIssue], 
        configuration: ProjectConfiguration
    ) -> float:
        """Calculate quality score based on issues and configuration."""
        
        base_score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.level.value == 'error':
                base_score -= 15  # Deduct for both critical and error issues
            elif issue.level.value == 'warning':
                base_score -= 5
            elif issue.level.value == 'info':
                base_score -= 2
        
        # Bonus for configuration compliance
        compliance = self._check_configuration_compliance(code, configuration)
        compliance_bonus = sum(5 for passed in compliance.values() if passed)
        base_score += compliance_bonus
        
        # Bonus for good practices
        if self._has_typescript_types(code):
            base_score += 5
        
        if self._has_accessibility_features(code):
            base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    def _check_configuration_compliance(
        self, 
        code: str, 
        configuration: ProjectConfiguration
    ) -> Dict[str, bool]:
        """Check compliance with configuration requirements."""
        
        compliance = {}
        
        # Framework compliance
        if configuration.framework == Framework.NEXT_JS:
            compliance['nextjs_patterns'] = 'next/' in code or "'use client'" in code
        
        # Styling system compliance
        if configuration.styling_system == StylingSystem.CHAKRA_UI:
            compliance['chakra_imports'] = '@chakra-ui/react' in code
            compliance['no_tailwind_classes'] = not re.search(r'className="[^"]*bg-\w+-\d+', code)
            compliance['chakra_components'] = any(comp in code for comp in ['<Box', '<Button', '<Text'])
        
        elif configuration.styling_system == StylingSystem.TAILWIND:
            compliance['tailwind_classes'] = 'className=' in code
            compliance['no_component_lib_imports'] = '@chakra-ui' not in code and '@mui' not in code
        
        # TypeScript compliance
        if configuration.typescript:
            compliance['typescript_types'] = 'interface' in code or ': React.FC' in code
        
        return compliance
    
    def _has_typescript_types(self, code: str) -> bool:
        """Check if code has TypeScript types."""
        return any(pattern in code for pattern in ['interface', 'type ', ': React.FC', ': string', ': number'])
    
    def _has_accessibility_features(self, code: str) -> bool:
        """Check if code has accessibility features."""
        return any(pattern in code for pattern in ['aria-', 'alt=', 'role=', 'tabIndex'])