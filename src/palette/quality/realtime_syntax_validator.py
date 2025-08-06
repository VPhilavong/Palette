"""
Real-Time Syntax Validator - Validates syntax during component generation.

This system provides real-time syntax validation during the generation process,
catching errors as they occur and providing immediate feedback to prevent
malformed code from being generated.
"""

import ast
import re
import json
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .validator import ValidationIssue, ValidationLevel


class SyntaxValidationMode(Enum):
    """Modes for syntax validation."""
    
    STRICT = "strict"      # Fail on any syntax error
    LENIENT = "lenient"    # Allow minor syntax issues
    PROGRESSIVE = "progressive"  # Fix issues during generation


class ValidationPhase(Enum):
    """Phases of code generation where validation occurs."""
    
    IMPORTS = "imports"
    COMPONENT_SIGNATURE = "component_signature"
    PROPS_INTERFACE = "props_interface"
    JSX_STRUCTURE = "jsx_structure"
    EVENT_HANDLERS = "event_handlers"
    STYLING = "styling"
    EXPORT = "export"
    COMPLETE = "complete"


@dataclass
class SyntaxValidationResult:
    """Result of real-time syntax validation."""
    
    is_valid: bool
    phase: ValidationPhase
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    auto_fixes: List[str] = field(default_factory=list)
    corrected_code: Optional[str] = None


@dataclass
class GenerationContext:
    """Context information for the generation process."""
    
    framework: str = "react"
    styling_system: str = "tailwind"
    typescript: bool = True
    component_name: str = "Component"
    target_file: str = "Component.tsx"
    requirements: List[str] = field(default_factory=list)


class RealtimeSyntaxValidator:
    """
    Real-time syntax validation during component generation.
    
    Provides immediate feedback and auto-correction during the generation process
    to ensure syntactically correct code is produced.
    """
    
    def __init__(self, mode: SyntaxValidationMode = SyntaxValidationMode.PROGRESSIVE):
        self.mode = mode
        self.validation_rules = self._initialize_validation_rules()
        self.auto_fix_patterns = self._initialize_auto_fix_patterns()
        
        # Track validation state during generation
        self.current_context: Optional[GenerationContext] = None
        self.phase_results: Dict[ValidationPhase, SyntaxValidationResult] = {}
    
    def start_validation_session(self, context: GenerationContext) -> None:
        """Start a new validation session for component generation."""
        
        self.current_context = context
        self.phase_results = {}
        print(f"🔍 Starting real-time validation for {context.component_name}")
    
    def validate_phase(self, phase: ValidationPhase, code_fragment: str) -> SyntaxValidationResult:
        """
        Validate a specific phase of code generation.
        
        Args:
            phase: The generation phase being validated
            code_fragment: The code fragment to validate
            
        Returns:
            SyntaxValidationResult with validation details
        """
        
        if not self.current_context:
            raise ValueError("No validation session active. Call start_validation_session() first.")
        
        print(f"   🧪 Validating {phase.value} phase...")
        
        # Get validation rules for this phase
        phase_rules = self.validation_rules.get(phase, [])
        
        errors = []
        warnings = []
        suggestions = []
        auto_fixes = []
        corrected_code = code_fragment
        
        # Apply validation rules
        for rule in phase_rules:
            rule_result = rule(code_fragment, self.current_context)
            
            errors.extend(rule_result.get('errors', []))
            warnings.extend(rule_result.get('warnings', []))
            suggestions.extend(rule_result.get('suggestions', []))
            
            # Apply auto-fixes if in progressive mode
            if self.mode == SyntaxValidationMode.PROGRESSIVE and rule_result.get('auto_fix'):
                try:
                    fixed_code = rule_result['auto_fix'](corrected_code)
                    if fixed_code != corrected_code:
                        auto_fixes.append(rule_result.get('fix_description', 'Applied automatic fix'))
                        corrected_code = fixed_code
                except Exception as e:
                    warnings.append(ValidationIssue(
                        ValidationLevel.WARNING,
                        f"Auto-fix failed: {str(e)}",
                        "auto_fix_error",
                        0,
                        "Manual intervention may be required"
                    ))
        
        # Determine if validation passed
        is_valid = (
            len(errors) == 0 and 
            (self.mode != SyntaxValidationMode.STRICT or len(warnings) == 0)
        )
        
        result = SyntaxValidationResult(
            is_valid=is_valid,
            phase=phase,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            auto_fixes=auto_fixes,
            corrected_code=corrected_code if corrected_code != code_fragment else None
        )
        
        # Store result for this phase
        self.phase_results[phase] = result
        
        # Log result
        if is_valid:
            print(f"      ✅ {phase.value} phase passed")
        else:
            print(f"      ❌ {phase.value} phase failed ({len(errors)} errors, {len(warnings)} warnings)")
        
        if auto_fixes:
            print(f"      🔧 Applied {len(auto_fixes)} auto-fixes")
        
        return result
    
    def validate_complete_component(self, complete_code: str) -> SyntaxValidationResult:
        """Validate the complete generated component."""
        
        return self.validate_phase(ValidationPhase.COMPLETE, complete_code)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation session."""
        
        if not self.current_context:
            return {"error": "No active validation session"}
        
        total_errors = sum(len(result.errors) for result in self.phase_results.values())
        total_warnings = sum(len(result.warnings) for result in self.phase_results.values())
        total_fixes = sum(len(result.auto_fixes) for result in self.phase_results.values())
        
        phases_passed = sum(1 for result in self.phase_results.values() if result.is_valid)
        phases_total = len(self.phase_results)
        
        return {
            "component_name": self.current_context.component_name,
            "phases_validated": phases_total,
            "phases_passed": phases_passed,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "auto_fixes_applied": total_fixes,
            "validation_success": total_errors == 0,
            "phase_results": {phase.value: result for phase, result in self.phase_results.items()}
        }
    
    def _initialize_validation_rules(self) -> Dict[ValidationPhase, List[Callable]]:
        """Initialize validation rules for each phase."""
        
        return {
            ValidationPhase.IMPORTS: [
                self._validate_import_syntax,
                self._validate_import_ordering,
                self._validate_framework_imports,
                self._validate_react_imports
            ],
            ValidationPhase.COMPONENT_SIGNATURE: [
                self._validate_component_name,
                self._validate_component_syntax,
                self._validate_typescript_signature
            ],
            ValidationPhase.PROPS_INTERFACE: [
                self._validate_interface_syntax,
                self._validate_interface_naming,
                self._validate_prop_types
            ],
            ValidationPhase.JSX_STRUCTURE: [
                self._validate_jsx_syntax,
                self._validate_jsx_nesting,
                self._validate_jsx_attributes
            ],
            ValidationPhase.EVENT_HANDLERS: [
                self._validate_event_handler_syntax,
                self._validate_handler_naming
            ],
            ValidationPhase.STYLING: [
                self._validate_styling_syntax,
                self._validate_class_names,
                self._validate_styling_system_usage
            ],
            ValidationPhase.EXPORT: [
                self._validate_export_syntax,
                self._validate_export_naming
            ],
            ValidationPhase.COMPLETE: [
                self._validate_complete_syntax,
                self._validate_component_structure,
                self._validate_framework_compliance
            ]
        }
    
    def _initialize_auto_fix_patterns(self) -> Dict[str, Callable]:
        """Initialize auto-fix patterns for common issues."""
        
        return {
            "missing_semicolon": self._fix_missing_semicolon,
            "incorrect_jsx_closing": self._fix_jsx_closing_tags,
            "missing_key_prop": self._add_key_props,
            "incorrect_import": self._fix_import_syntax,
            "missing_export": self._add_default_export,
            "incorrect_component_name": self._fix_component_naming,
            "missing_typescript_types": self._add_typescript_types,
            "missing_react_import": self._add_react_import
        }
    
    # Validation rule implementations
    
    def _validate_import_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate import statement syntax."""
        
        errors = []
        warnings = []
        suggestions = []
        
        import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('import')]
        
        for i, line in enumerate(import_lines):
            # Check for missing semicolon
            if not line.endswith(';'):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Missing semicolon in import statement: {line}",
                    "missing_semicolon",
                    i + 1,
                    "Add semicolon at end of import statement"
                ))
            
            # Check for invalid import syntax
            if not re.match(r'^import\s+.*\s+from\s+[\'"][^\'\"]+[\'"];?$', line) and not re.match(r'^import\s+[\'"][^\'\"]+[\'"];?$', line):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Invalid import syntax: {line}",
                    "invalid_import",
                    i + 1,
                    "Use correct import syntax: import { Component } from 'package';"
                ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "auto_fix": self._fix_import_syntax if errors else None,
            "fix_description": "Fixed import syntax and added missing semicolons"
        }
    
    def _validate_import_ordering(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate import statement ordering."""
        
        warnings = []
        suggestions = []
        
        import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('import')]
        
        # Check if React import is first
        if import_lines and not any('react' in line.lower() for line in import_lines[:1]):
            suggestions.append("Consider placing React imports first")
        
        # Check for mixed import styles
        default_imports = [line for line in import_lines if ' from ' in line and not '{' in line]
        named_imports = [line for line in import_lines if ' from ' in line and '{' in line]
        
        if default_imports and named_imports:
            # Mixed import styles are fine, but could be organized better
            suggestions.append("Consider grouping default imports before named imports")
        
        return {
            "errors": [],
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_framework_imports(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate framework-specific import requirements."""
        
        errors = []
        warnings = []
        
        if context.framework == "nextjs":
            # Check for Next.js specific imports
            if 'Image' in code and 'next/image' not in code:
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Using Image component without importing from next/image",
                    "missing_nextjs_import",
                    0,
                    "Add: import Image from 'next/image';"
                ))
            
            if 'Link' in code and 'next/link' not in code:
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Using Link component without importing from next/link",
                    "missing_nextjs_import",
                    0,
                    "Add: import Link from 'next/link';"
                ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": []
        }
    
    def _validate_react_imports(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate React import requirements based on JSX usage."""
        
        errors = []
        warnings = []
        suggestions = []
        
        # Check if React import is present
        has_react_import = any(pattern in code for pattern in [
            "import React from 'react'",
            'import React from "react"',
            "import * as React from 'react'",
            'import * as React from "react"',
            "from 'react'",
            'from "react"'
        ])
        
        # Detect JSX usage patterns that require React
        jsx_patterns = [
            r'<[A-Z][a-zA-Z0-9]*[^>]*>',  # React components (PascalCase)
            r'<[a-z][a-zA-Z0-9]*[^>]*>',  # HTML elements
            r'<Fragment',                  # React Fragment
            r'<React\.',                   # React.Component usage
            r'<>',                         # Fragment shorthand
            r'</>'                         # Fragment shorthand closing
        ]
        
        has_jsx = any(re.search(pattern, code) for pattern in jsx_patterns)
        
        # Check for React hooks usage
        react_hooks = [
            'useState', 'useEffect', 'useContext', 'useReducer', 'useMemo', 
            'useCallback', 'useRef', 'useImperativeHandle', 'useLayoutEffect',
            'useDebugValue', 'useDeferredValue', 'useTransition', 'useId'
        ]
        
        uses_hooks = any(hook in code for hook in react_hooks)
        
        # Check for React types usage (TypeScript)
        react_types = [
            'React.FC', 'React.Component', 'React.ReactElement', 'React.JSX',
            'ReactNode', 'ReactElement', 'FC', 'Component'
        ]
        
        uses_react_types = context.typescript and any(rtype in code for rtype in react_types)
        
        # Determine if React import is needed
        needs_react_import = has_jsx or uses_hooks or uses_react_types
        
        if needs_react_import and not has_react_import:
            # Determine specific reason for import
            reasons = []
            if has_jsx:
                reasons.append("JSX usage")
            if uses_hooks:
                hook_matches = [hook for hook in react_hooks if hook in code]
                reasons.append(f"React hooks: {', '.join(hook_matches[:3])}")
            if uses_react_types:
                reasons.append("React TypeScript types")
            
            reason_text = "; ".join(reasons)
            
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                f"Missing React import required for {reason_text}",
                "missing_react_import",
                1,  # Usually at the top of the file
                "Add: import React from 'react';"
            ))
        
        # Check for unnecessary React import (React 17+ JSX Transform)
        elif has_react_import and not uses_hooks and not uses_react_types:
            # If only JSX is used and no hooks/types, suggest JSX transform
            if has_jsx and not any(pattern in code for pattern in ['React.', 'createElement']):
                suggestions.append(
                    "Consider using React 17+ JSX transform to avoid importing React for JSX-only usage"
                )
        
        # Check for specific import requirements
        if 'Fragment' in code and not any(pattern in code for pattern in [
            "import { Fragment }",
            "React.Fragment",
            "import React"
        ]):
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                "Fragment usage requires React import or named import",
                "missing_fragment_import",
                0,
                "Add: import { Fragment } from 'react'; or use React.Fragment"
            ))
        
        # Check for hook imports when only hooks are used
        if uses_hooks and not has_jsx and not uses_react_types:
            hook_list = [hook for hook in react_hooks if hook in code]
            if len(hook_list) <= 3:  # For small number of hooks, suggest named imports
                suggestions.append(
                    f"Consider named imports for hooks: import {{ {', '.join(hook_list)} }} from 'react';"
                )
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "auto_fix": self._add_react_import if errors else None,
            "fix_description": "Added missing React import"
        }
    
    def _validate_component_name(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate component naming conventions."""
        
        errors = []
        warnings = []
        
        # Extract component name from code
        component_match = re.search(r'(?:const|function)\s+([A-Za-z][A-Za-z0-9]*)', code)
        
        if component_match:
            component_name = component_match.group(1)
            
            # Check PascalCase
            if not component_name[0].isupper():
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Component name '{component_name}' should start with uppercase letter",
                    "invalid_component_name",
                    0,
                    "Use PascalCase for component names"
                ))
            
            # Check for reserved words
            reserved_words = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while']
            if component_name.lower() in reserved_words:
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Component name '{component_name}' is a reserved word",
                    "reserved_component_name",
                    0,
                    "Choose a different component name"
                ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": [],
            "auto_fix": self._fix_component_naming if errors else None,
            "fix_description": "Fixed component naming to follow PascalCase convention"
        }
    
    def _validate_component_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate component function syntax."""
        
        errors = []
        warnings = []
        
        # Check for valid component patterns
        component_patterns = [
            r'const\s+\w+\s*[:=]\s*\([^)]*\)\s*=>',  # Arrow function
            r'function\s+\w+\s*\([^)]*\)',  # Function declaration
            r'const\s+\w+\s*[:=]\s*React\.FC'  # React.FC
        ]
        
        has_valid_pattern = any(re.search(pattern, code) for pattern in component_patterns)
        
        if not has_valid_pattern:
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                "Invalid component function syntax",
                "invalid_component_syntax",
                0,
                "Use valid React component syntax: const Component = () => {} or function Component() {}"
            ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": []
        }
    
    def _validate_typescript_signature(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate TypeScript component signature."""
        
        errors = []
        warnings = []
        suggestions = []
        
        if not context.typescript:
            return {"errors": [], "warnings": [], "suggestions": []}
        
        # Check for proper TypeScript typing
        if 'props' in code.lower() and not any(pattern in code for pattern in ['React.FC', ': FC', 'interface', 'type']):
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Component with props should have TypeScript types",
                "missing_typescript_types",
                0,
                "Add TypeScript interface or use React.FC<Props>"
            ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "auto_fix": self._add_typescript_types if warnings else None,
            "fix_description": "Added TypeScript types for component props"
        }
    
    def _validate_interface_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate TypeScript interface syntax."""
        
        errors = []
        
        if not context.typescript:
            return {"errors": [], "warnings": [], "suggestions": []}
        
        # Find interface declarations
        interface_pattern = r'interface\s+(\w+)\s*\{([^}]*)\}'
        interfaces = re.findall(interface_pattern, code, re.DOTALL)
        
        for interface_name, interface_body in interfaces:
            # Check interface naming convention
            if not interface_name.endswith('Props') and 'props' in interface_name.lower():
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Interface '{interface_name}' should end with 'Props'",
                    "interface_naming",
                    0,
                    "Use naming convention: ComponentNameProps"
                ))
            
            # Check for empty interface
            if not interface_body.strip():
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Interface '{interface_name}' is empty",
                    "empty_interface",
                    0,
                    "Add properties to interface or remove it"
                ))
        
        return {"errors": errors, "warnings": [], "suggestions": []}
    
    def _validate_interface_naming(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate interface naming conventions."""
        
        errors = []
        warnings = []
        
        if not context.typescript:
            return {"errors": [], "warnings": [], "suggestions": []}
        
        # Find interface declarations
        interface_pattern = r'interface\s+(\w+)'
        interfaces = re.findall(interface_pattern, code)
        
        for interface_name in interfaces:
            # Check if Props interfaces follow naming convention
            if 'props' in interface_name.lower() and not interface_name.endswith('Props'):
                warnings.append(ValidationIssue(
                    ValidationLevel.WARNING,
                    f"Interface '{interface_name}' should end with 'Props' for consistency",
                    "interface_naming_convention",
                    0,
                    f"Consider renaming to '{interface_name}Props'"
                ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_prop_types(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate prop type definitions."""
        
        warnings = []
        
        if not context.typescript:
            return {"errors": [], "warnings": [], "suggestions": []}
        
        # Check for any prop that might need validation
        if 'props' in code.lower() and 'any' in code:
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Consider using specific types instead of 'any'",
                "generic_type_usage",
                0,
                "Define specific prop types for better type safety"
            ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_jsx_nesting(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate JSX nesting rules."""
        
        warnings = []
        
        # Basic nesting validation - check for deeply nested structures
        nesting_level = 0
        max_nesting = 0
        
        for char in code:
            if char == '<':
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
            elif char == '>':
                nesting_level = max(0, nesting_level - 1)
        
        if max_nesting > 6:
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Deeply nested JSX structure detected",
                "deep_jsx_nesting",
                0,
                "Consider breaking down into smaller components"
            ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_event_handler_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate event handler syntax."""
        
        errors = []
        warnings = []
        
        # Check for inline arrow functions in event handlers
        inline_handler_pattern = r'on\w+={[^}]*=>[^}]*}'
        if re.search(inline_handler_pattern, code):
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Inline arrow functions in event handlers can cause unnecessary re-renders",
                "inline_event_handler",
                0,
                "Consider extracting event handlers to useCallback or component methods"
            ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_handler_naming(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate event handler naming conventions."""
        
        warnings = []
        
        # Check handler naming convention
        handler_pattern = r'(on\w+)='
        handlers = re.findall(handler_pattern, code)
        
        for handler in handlers:
            if not handler.startswith('on'):
                warnings.append(ValidationIssue(
                    ValidationLevel.WARNING,
                    f"Event handler '{handler}' should start with 'on'",
                    "handler_naming_convention",
                    0,
                    "Use 'onEventName' naming convention for event handlers"
                ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_class_names(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate className usage."""
        
        errors = []
        warnings = []
        
        # Check for className instead of class
        if 'class=' in code and 'className=' not in code:
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                "Use 'className' instead of 'class' in JSX",
                "jsx_class_attribute",
                0,
                "Replace 'class=' with 'className=' in JSX elements"
            ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_styling_system_usage(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate styling system specific usage."""
        
        errors = []
        warnings = []
        
        if context.styling_system == "chakra":
            # Check for Tailwind-like classes in Chakra components
            tailwind_classes = ['bg-', 'text-', 'p-', 'm-', 'w-', 'h-', 'flex', 'grid']
            for tw_class in tailwind_classes:
                if f'{tw_class}' in code and 'className=' in code:
                    warnings.append(ValidationIssue(
                        ValidationLevel.WARNING,
                        f"Consider using Chakra UI props instead of className with '{tw_class}' classes",
                        "styling_system_mixing",
                        0,
                        "Use Chakra UI's built-in styling props for consistency"
                    ))
                    break
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_export_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate export syntax."""
        
        errors = []
        warnings = []
        
        # Check for default export
        if 'export' not in code:
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Component should have an export statement",
                "missing_export",
                0,
                "Add 'export default ComponentName;' to make component importable"
            ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_export_naming(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate export naming consistency."""
        
        warnings = []
        
        # Check if export name matches component name
        component_match = re.search(r'(?:const|function)\s+(\w+)', code)
        export_match = re.search(r'export\s+default\s+(\w+)', code)
        
        if component_match and export_match:
            component_name = component_match.group(1)
            export_name = export_match.group(1)
            
            if component_name != export_name:
                warnings.append(ValidationIssue(
                    ValidationLevel.WARNING,
                    f"Component name '{component_name}' doesn't match export name '{export_name}'",
                    "export_name_mismatch",
                    0,
                    "Ensure component name matches the exported name for consistency"
                ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_component_structure(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate overall component structure."""
        
        warnings = []
        
        # Check for return statement in component
        if not re.search(r'return\s*\(', code) and not re.search(r'return\s*<', code):
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Component should have a return statement",
                "missing_return",
                0,
                "Add return statement with JSX content"
            ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_framework_compliance(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate framework-specific compliance."""
        
        warnings = []
        
        if context.framework == "nextjs":
            # Check for client-side hooks in server components
            client_hooks = ['useState', 'useEffect', 'useContext', 'useReducer']
            has_client_hooks = any(hook in code for hook in client_hooks)
            has_use_client = "'use client'" in code or '"use client"' in code
            
            if has_client_hooks and not has_use_client:
                warnings.append(ValidationIssue(
                    ValidationLevel.WARNING,
                    "Component uses client-side hooks but missing 'use client' directive",
                    "missing_use_client",
                    0,
                    "Add 'use client'; at top of file for client-side functionality"
                ))
        
        return {"errors": [], "warnings": warnings, "suggestions": []}
    
    def _validate_jsx_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate JSX syntax."""
        
        errors = []
        warnings = []
        
        # Check for unclosed JSX tags
        jsx_tag_pattern = r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>'
        closing_tag_pattern = r'</([a-zA-Z][a-zA-Z0-9]*)>'
        
        opening_tags = re.findall(jsx_tag_pattern, code)
        closing_tags = re.findall(closing_tag_pattern, code)
        
        # Check for mismatched tags (basic check)
        for tag in opening_tags:
            if tag not in closing_tags and not re.search(f'<{tag}[^>]*/>', code):
                # Might be self-closing or mismatched
                if tag.lower() not in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                    warnings.append(ValidationIssue(
                        ValidationLevel.WARNING,
                        f"Potential unclosed JSX tag: {tag}",
                        "unclosed_jsx_tag",
                        0,
                        f"Ensure <{tag}> tag is properly closed"
                    ))
        
        # Enhanced self-closing tag detection
        self_closing_errors = self._detect_self_closing_issues(code)
        errors.extend(self_closing_errors)
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": [],
            "auto_fix": self._fix_jsx_closing_tags if errors else None,
            "fix_description": "Fixed JSX self-closing tags"
        }
    
    def _validate_jsx_attributes(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate JSX attributes."""
        
        errors = []
        warnings = []
        
        # Check for missing key props in mapped elements
        if '.map(' in code and 'key=' not in code:
            warnings.append(ValidationIssue(
                ValidationLevel.WARNING,
                "Missing key prop in mapped JSX elements",
                "missing_key_prop",
                0,
                "Add unique key prop to mapped elements"
            ))
        
        # Check for invalid attribute names
        invalid_attrs = re.findall(r'(class|for)=', code)
        for attr in invalid_attrs:
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                f"Invalid JSX attribute '{attr}' - use '{attr}Name' instead",
                "invalid_jsx_attribute",
                0,
                f"Replace '{attr}=' with '{'className' if attr == 'class' else 'htmlFor'}='"
            ))
        
        return {
            "errors": errors,
            "warnings": warnings,
            "suggestions": [],
            "auto_fix": self._add_key_props if 'missing_key_prop' in [w.category for w in warnings] else None,
            "fix_description": "Added key props to mapped elements"
        }
    
    def _validate_styling_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate styling-related syntax."""
        
        errors = []
        warnings = []
        
        if context.styling_system == "chakra":
            # Check for Tailwind classes in Chakra components
            tailwind_pattern = r'className=["\'][^"\']*(?:bg-|text-|p-|m-|w-|h-|flex|grid)[^"\']*["\']'
            if re.search(tailwind_pattern, code):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Tailwind classes found in Chakra UI component",
                    "styling_system_conflict",
                    0,
                    "Use Chakra UI props instead of Tailwind classes"
                ))
        
        elif context.styling_system == "tailwind":
            # Check for invalid Tailwind class patterns
            invalid_patterns = [
                r'className=["\'][^"\']*bg-\d+-\d+[^"\']*["\']',  # Invalid color format
                r'className=["\'][^"\']*text-\d+px[^"\']*["\']'    # Invalid size format
            ]
            
            for pattern in invalid_patterns:
                if re.search(pattern, code):
                    warnings.append(ValidationIssue(
                        ValidationLevel.WARNING,
                        "Potentially invalid Tailwind class detected",
                        "invalid_tailwind_class",
                        0,
                        "Use valid Tailwind CSS class names"
                    ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    def _validate_complete_syntax(self, code: str, context: GenerationContext) -> Dict[str, Any]:
        """Validate the complete component syntax."""
        
        errors = []
        warnings = []
        
        # Try to parse as Python AST to check basic syntax structure
        try:
            # Basic bracket matching
            if code.count('(') != code.count(')'):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Mismatched parentheses",
                    "syntax_error",
                    0,
                    "Check for unmatched parentheses"
                ))
            
            if code.count('{') != code.count('}'):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Mismatched braces",
                    "syntax_error",
                    0,
                    "Check for unmatched braces"
                ))
            
            if code.count('[') != code.count(']'):
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Mismatched brackets",
                    "syntax_error",
                    0,
                    "Check for unmatched brackets"
                ))
        
        except Exception as e:
            errors.append(ValidationIssue(
                ValidationLevel.ERROR,
                f"Syntax validation error: {str(e)}",
                "syntax_error",
                0,
                "Fix syntax errors in the component"
            ))
        
        return {"errors": errors, "warnings": warnings, "suggestions": []}
    
    # Auto-fix implementations
    
    def _fix_missing_semicolon(self, code: str) -> str:
        """Fix missing semicolons in statements."""
        
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.endswith((';', '{', '}', ',')) and not stripped.startswith('//'):
                # Add semicolon to statements that need it
                if any(keyword in stripped for keyword in ['import', 'export', 'const', 'let', 'var']):
                    line = line.rstrip() + ';'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_import_syntax(self, code: str) -> str:
        """Fix import syntax issues."""
        
        lines = code.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip().startswith('import') and not line.strip().endswith(';'):
                fixed_lines.append(line + ';')
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _detect_self_closing_issues(self, code: str) -> List[ValidationIssue]:
        """Enhanced detection of self-closing tag issues."""
        
        errors = []
        
        # Comprehensive list of void/self-closing HTML elements
        void_elements = {
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        }
        
        # React-specific self-closing elements that should be self-closed
        react_void_elements = {
            'Fragment', 'React.Fragment'
        }
        
        # Pattern to match opening tags with their attributes
        tag_pattern = r'<([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*)([^>]*)>'
        
        # Find all opening tags
        for match in re.finditer(tag_pattern, code):
            tag_name = match.group(1)
            attributes = match.group(2)
            full_match = match.group(0)
            line_number = code[:match.start()].count('\n') + 1
            
            # Check if this is a void element that should be self-closing
            if tag_name.lower() in void_elements:
                if not attributes.strip().endswith('/'):
                    errors.append(ValidationIssue(
                        ValidationLevel.ERROR,
                        f"Void element <{tag_name}> must be self-closing in React",
                        "void_element_not_self_closed",
                        line_number,
                        f"Use <{tag_name}{attributes} /> instead of <{tag_name}{attributes}>"
                    ))
            
            # Check for React Fragments
            elif tag_name in react_void_elements:
                # Fragment can be self-closing if it has no children
                fragment_content = self._extract_element_content(code, match.start(), tag_name)
                if fragment_content is not None and fragment_content.strip() == '':
                    if not attributes.strip().endswith('/'):
                        errors.append(ValidationIssue(
                            ValidationLevel.ERROR,
                            f"Empty <{tag_name}> should be self-closing",
                            "empty_fragment_not_self_closed",
                            line_number,
                            f"Use <{tag_name} /> for empty fragments"
                        ))
        
        # Check for incorrect self-closing non-void elements
        self_closing_pattern = r'<([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)*)[^>]*/>'
        for match in re.finditer(self_closing_pattern, code):
            tag_name = match.group(1)
            line_number = code[:match.start()].count('\n') + 1
            
            # If it's not a void element and not a React component, it might be incorrect
            if (tag_name.lower() not in void_elements and 
                tag_name not in react_void_elements and
                tag_name[0].islower()):  # HTML elements start with lowercase
                
                # Check if this element typically has content
                content_elements = {
                    'div', 'span', 'p', 'button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'section', 'article', 'header', 'footer', 'nav', 'main', 'aside',
                    'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot'
                }
                
                if tag_name.lower() in content_elements:
                    errors.append(ValidationIssue(
                        ValidationLevel.ERROR,
                        f"Element <{tag_name}> should not be self-closing",
                        "content_element_self_closed",
                        line_number,
                        f"Use <{tag_name}></{tag_name}> instead of <{tag_name} /> for content elements"
                    ))
        
        # Check for missing space before self-closing slash
        malformed_self_closing = r'<[^>]+/>'
        space_before_slash = r'<[^>]+\s+/>'
        
        for match in re.finditer(malformed_self_closing, code):
            if not re.match(space_before_slash, match.group(0)):
                line_number = code[:match.start()].count('\n') + 1
                errors.append(ValidationIssue(
                    ValidationLevel.ERROR,
                    "Missing space before self-closing slash",
                    "malformed_self_closing",
                    line_number,
                    "Add space before '/>' in self-closing tags"
                ))
        
        return errors
    
    def _extract_element_content(self, code: str, start_pos: int, tag_name: str) -> Optional[str]:
        """Extract content between opening and closing tags."""
        
        try:
            # Find the end of the opening tag
            open_end = code.find('>', start_pos)
            if open_end == -1:
                return None
            
            # Look for the closing tag
            closing_tag = f'</{tag_name}>'
            close_start = code.find(closing_tag, open_end)
            
            if close_start == -1:
                return None
            
            return code[open_end + 1:close_start]
        
        except Exception:
            return None
    
    def _fix_jsx_closing_tags(self, code: str) -> str:
        """Enhanced JSX self-closing tag fixes."""
        
        # Comprehensive list of void elements
        void_elements = [
            'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'
        ]
        
        for tag in void_elements:
            # Fix void elements that are not self-closed
            # Handle both <tag> and <tag attributes>
            pattern = f'<{tag}((?:[^>](?!/))*)>'
            replacement = f'<{tag}\\1 />'
            code = re.sub(pattern, replacement, code)
        
        # Fix space before self-closing slash
        # Match tags that end with "/>" but don't have space before the slash
        malformed_pattern = r'<([^>]+)(?<!\s)/>'
        code = re.sub(malformed_pattern, r'<\1 />', code)
        
        # Fix React Fragments
        code = re.sub(r'<(React\.)?Fragment\s*></\1Fragment>', r'<\1Fragment />', code)
        
        return code
    
    def _add_key_props(self, code: str) -> str:
        """Add key props to mapped JSX elements."""
        
        # Basic pattern to add key props
        map_pattern = r'(\.map\([^}]+=>\s*<)(\w+)([^>]*?)>'
        replacement = r'\1\2 key={index}\3>'
        
        return re.sub(map_pattern, replacement, code)
    
    def _fix_component_naming(self, code: str) -> str:
        """Fix component naming to follow PascalCase."""
        
        def to_pascal_case(match):
            name = match.group(1)
            return name[0].upper() + name[1:] if name else name
        
        # Fix component names in declarations
        code = re.sub(r'(const|function)\s+([a-z][a-zA-Z0-9]*)', 
                      lambda m: f"{m.group(1)} {to_pascal_case(m)}", code)
        
        return code
    
    def _add_typescript_types(self, code: str) -> str:
        """Add basic TypeScript types to component."""
        
        if 'interface' not in code and 'props' in code.lower():
            # Add basic props interface
            interface = "interface Props {\n  // Define your props here\n}\n\n"
            return interface + code
        
        return code
    
    def _add_default_export(self, code: str) -> str:
        """Add default export to component."""
        
        if 'export default' not in code:
            # Try to find component name
            component_match = re.search(r'(?:const|function)\s+(\w+)', code)
            if component_match:
                component_name = component_match.group(1)
                return code + f'\n\nexport default {component_name};'
        
        return code
    
    def _add_react_import(self, code: str) -> str:
        """Add missing React import to the code."""
        
        # Check if there are already imports
        import_lines = [line for line in code.split('\n') if line.strip().startswith('import')]
        
        # Determine the best React import style based on usage
        lines = code.split('\n')
        
        # Check for JSX usage patterns
        has_jsx = any(re.search(r'<[A-Za-z][^>]*>', line) for line in lines)
        
        # Check for React hooks
        react_hooks = [
            'useState', 'useEffect', 'useContext', 'useReducer', 'useMemo', 
            'useCallback', 'useRef', 'useImperativeHandle', 'useLayoutEffect'
        ]
        used_hooks = [hook for hook in react_hooks if any(hook in line for line in lines)]
        
        # Check for Fragment usage
        has_fragment = any('Fragment' in line and 'React.Fragment' not in line for line in lines)
        
        # Determine import style
        if has_jsx or len(used_hooks) > 3 or any('React.' in line for line in lines):
            # Use default React import for JSX or when using React.* patterns
            react_import = "import React from 'react';"
        elif used_hooks and not has_jsx:
            # Use named imports for hooks only
            if has_fragment:
                used_hooks.append('Fragment')
            react_import = f"import {{ {', '.join(used_hooks)} }} from 'react';"
        elif has_fragment:
            # Just Fragment import
            react_import = "import { Fragment } from 'react';"
        else:
            # Default case
            react_import = "import React from 'react';"
        
        # Add the import at the beginning or after other imports
        if import_lines:
            # Find the last import line
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('import'):
                    last_import_idx = i
            
            if last_import_idx >= 0:
                # Insert after last import
                lines.insert(last_import_idx + 1, react_import)
            else:
                # Insert at beginning
                lines.insert(0, react_import)
        else:
            # No imports, add at the beginning
            # Skip initial comments and directives
            insert_idx = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('//') and not stripped.startswith('/*') and not stripped.startswith("'use") and not stripped.startswith('"use'):
                    insert_idx = i
                    break
            
            lines.insert(insert_idx, react_import)
            lines.insert(insert_idx + 1, '')  # Add blank line after import
        
        return '\n'.join(lines)