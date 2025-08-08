"""
Modular validator implementation using dependency injection.
Implements the IValidator interface with pluggable validation strategies.
"""

import os
import re
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..interfaces import (
    IValidator, ValidationResult, ValidationIssue,
    ValidationSeverity, ValidationType
)


class ModularValidator(IValidator):
    """
    Modular implementation of component validator.
    Uses pluggable validation strategies.
    """
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        
        # Validation strategies
        self._validators = {
            ValidationType.TYPESCRIPT: self._validate_typescript_impl,
            ValidationType.IMPORTS: self._validate_imports_impl,
            ValidationType.STYLING: self._validate_styling_impl,
            ValidationType.NAMING: self._validate_naming_impl,
            ValidationType.STRUCTURE: self._validate_structure_impl,
        }
        
        # Cache for project info
        self._project_info = None
    
    def validate(self, content: str, file_path: str) -> ValidationResult:
        """
        Validate a component file.
        
        Args:
            content: File content to validate
            file_path: Path where the file will be saved
            
        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        
        # Determine file type
        is_typescript = file_path.endswith(('.ts', '.tsx'))
        is_component = any(pattern in file_path.lower() for pattern in ['component', '.tsx', '.jsx'])
        
        # Run appropriate validations
        if is_typescript:
            ts_result = self.validate_typescript(content, file_path)
            result.issues.extend(ts_result.issues)
        
        if is_component:
            # Validate imports
            import_result = self.validate_imports(content, self.project_path)
            result.issues.extend(import_result.issues)
            
            # Validate styling
            styling_result = self.validate_styling(content, self._detect_styling_approach())
            result.issues.extend(styling_result.issues)
            
            # Validate naming
            naming_result = self._validate_naming_impl(content, file_path)
            result.issues.extend(naming_result.issues)
            
            # Validate structure
            structure_result = self._validate_structure_impl(content, file_path)
            result.issues.extend(structure_result.issues)
        
        # Update passed status and score
        result.passed = not result.has_errors()
        result.score = result.calculate_score()
        
        return result
    
    def validate_typescript(self, content: str, file_path: str) -> ValidationResult:
        """
        Validate TypeScript types and syntax.
        
        Args:
            content: TypeScript content
            file_path: File path for context
            
        Returns:
            ValidationResult for TypeScript validation
        """
        return self._validators[ValidationType.TYPESCRIPT](content, file_path)
    
    def validate_imports(self, content: str, project_path: str) -> ValidationResult:
        """
        Validate that all imports are valid and available.
        
        Args:
            content: File content with imports
            project_path: Project root for resolving imports
            
        Returns:
            ValidationResult for import validation
        """
        return self._validators[ValidationType.IMPORTS](content, project_path)
    
    def validate_styling(self, content: str, styling_approach: str) -> ValidationResult:
        """
        Validate styling consistency.
        
        Args:
            content: Component content
            styling_approach: Expected styling approach (tailwind, css, etc.)
            
        Returns:
            ValidationResult for styling validation
        """
        return self._validators[ValidationType.STYLING](content, styling_approach)
    
    def supports_validation_type(self, validation_type: ValidationType) -> bool:
        """Check if the validator supports a specific validation type."""
        return validation_type in self._validators
    
    def _validate_typescript_impl(self, content: str, file_path: str) -> ValidationResult:
        """Implementation of TypeScript validation."""
        result = ValidationResult()
        
        # Check for any type usage
        if re.search(r':\s*any(?:\s|;|,|\))', content):
            result.add_issue(ValidationIssue(
                type=ValidationType.TYPESCRIPT,
                severity=ValidationSeverity.WARNING,
                message="Avoid using 'any' type - use specific types instead",
                suggestion="Replace 'any' with a specific type or interface"
            ))
        
        # Check for missing return types
        function_pattern = r'(?:export\s+)?(?:async\s+)?function\s+\w+\s*\([^)]*\)\s*{'
        matches = re.finditer(function_pattern, content)
        for match in matches:
            # Check if return type is specified
            func_line = content[max(0, match.start()-50):match.end()]
            if not re.search(r'\)\s*:\s*\w+\s*{', func_line):
                result.add_issue(ValidationIssue(
                    type=ValidationType.TYPESCRIPT,
                    severity=ValidationSeverity.INFO,
                    message="Function missing explicit return type",
                    line_number=content[:match.start()].count('\n') + 1,
                    suggestion="Add explicit return type annotation"
                ))
        
        # Check for proper interface usage
        if 'Props' in content and not re.search(r'interface\s+\w*Props', content):
            result.add_issue(ValidationIssue(
                type=ValidationType.TYPESCRIPT,
                severity=ValidationSeverity.WARNING,
                message="Props should be defined using TypeScript interface",
                suggestion="Define props interface: interface ComponentProps { ... }"
            ))
        
        return result
    
    def _validate_imports_impl(self, content: str, project_path: str) -> ValidationResult:
        """Implementation of import validation."""
        result = ValidationResult()
        
        # Extract all imports
        import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        
        for import_path in imports:
            # Check for common issues
            if import_path.startswith('@/') or import_path.startswith('~/'):
                # Check if using path aliases correctly
                if not self._is_path_alias_configured():
                    result.add_issue(ValidationIssue(
                        type=ValidationType.IMPORTS,
                        severity=ValidationSeverity.WARNING,
                        message=f"Path alias '{import_path}' may not be configured",
                        suggestion="Ensure tsconfig.json or jsconfig.json has path aliases configured"
                    ))
            
            # Check for missing file extensions in relative imports
            if import_path.startswith('./') or import_path.startswith('../'):
                if not any(import_path.endswith(ext) for ext in ['.js', '.ts', '.jsx', '.tsx', '.css', '.json']):
                    # This might be a directory import, which is fine
                    pass
            
            # Validate node_modules imports
            if not import_path.startswith('.') and not import_path.startswith('@/') and not import_path.startswith('~/'):
                if not self._is_package_installed(import_path, project_path):
                    result.add_issue(ValidationIssue(
                        type=ValidationType.IMPORTS,
                        severity=ValidationSeverity.ERROR,
                        message=f"Package '{import_path}' not found in dependencies",
                        suggestion=f"Install the package: npm install {import_path.split('/')[0]}"
                    ))
        
        return result
    
    def _validate_styling_impl(self, content: str, styling_approach: str) -> ValidationResult:
        """Implementation of styling validation."""
        result = ValidationResult()
        
        if styling_approach == "tailwind":
            # Check for inline styles when using Tailwind
            if 'style={{' in content or 'style={{' in content:
                result.add_issue(ValidationIssue(
                    type=ValidationType.STYLING,
                    severity=ValidationSeverity.WARNING,
                    message="Avoid inline styles when using Tailwind CSS",
                    suggestion="Use Tailwind utility classes instead of inline styles"
                ))
            
            # Check for proper className usage
            if 'class=' in content and 'className=' not in content:
                result.add_issue(ValidationIssue(
                    type=ValidationType.STYLING,
                    severity=ValidationSeverity.ERROR,
                    message="Use 'className' instead of 'class' in React",
                    suggestion="Replace 'class=' with 'className='"
                ))
        
        elif styling_approach == "css":
            # Check for CSS module imports if using CSS
            if '.module.css' not in content and 'className=' in content:
                # Check if using global classes properly
                pass
        
        return result
    
    def _validate_naming_impl(self, content: str, file_path: str) -> ValidationResult:
        """Implementation of naming convention validation."""
        result = ValidationResult()
        
        # Extract component name from file
        file_name = Path(file_path).stem
        
        # Check if component name is PascalCase
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', file_name):
            result.add_issue(ValidationIssue(
                type=ValidationType.NAMING,
                severity=ValidationSeverity.WARNING,
                message=f"Component file name '{file_name}' should be in PascalCase",
                suggestion="Rename to follow PascalCase convention (e.g., MyComponent)"
            ))
        
        # Check function/component naming in content
        component_pattern = r'(?:export\s+)?(?:default\s+)?(?:function|const)\s+([A-Z]\w+)'
        matches = re.findall(component_pattern, content)
        
        for component_name in matches:
            if component_name != file_name:
                result.add_issue(ValidationIssue(
                    type=ValidationType.NAMING,
                    severity=ValidationSeverity.INFO,
                    message=f"Component name '{component_name}' doesn't match file name '{file_name}'",
                    suggestion="Keep component name and file name consistent"
                ))
        
        return result
    
    def _validate_structure_impl(self, content: str, file_path: str) -> ValidationResult:
        """Implementation of component structure validation."""
        result = ValidationResult()
        
        # Check for proper export
        if 'export' not in content:
            result.add_issue(ValidationIssue(
                type=ValidationType.STRUCTURE,
                severity=ValidationSeverity.ERROR,
                message="Component should be exported",
                suggestion="Add 'export default' or named export"
            ))
        
        # Check for React import (if needed)
        if 'jsx' in content.lower() or '<' in content:
            if 'import React' not in content and 'import { ' not in content:
                # Check if using new JSX transform
                if not self._uses_new_jsx_transform():
                    result.add_issue(ValidationIssue(
                        type=ValidationType.STRUCTURE,
                        severity=ValidationSeverity.WARNING,
                        message="Missing React import",
                        suggestion="Add: import React from 'react'"
                    ))
        
        return result
    
    def _detect_styling_approach(self) -> str:
        """Detect the project's styling approach."""
        if not self._project_info:
            self._project_info = self._load_project_info()
        
        return self._project_info.get("styling", "css")
    
    def _load_project_info(self) -> Dict[str, Any]:
        """Load project information."""
        info = {"styling": "css"}
        
        # Check for Tailwind
        tailwind_config = Path(self.project_path) / "tailwind.config.js"
        if tailwind_config.exists():
            info["styling"] = "tailwind"
        
        # Check package.json
        package_json = Path(self.project_path) / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "tailwindcss" in deps:
                        info["styling"] = "tailwind"
                    elif "styled-components" in deps:
                        info["styling"] = "styled-components"
                    
                    info["dependencies"] = deps
            except Exception:
                pass
        
        return info
    
    def _is_path_alias_configured(self) -> bool:
        """Check if path aliases are configured."""
        # Check tsconfig.json
        tsconfig = Path(self.project_path) / "tsconfig.json"
        if tsconfig.exists():
            try:
                import json
                with open(tsconfig) as f:
                    data = json.load(f)
                    return "paths" in data.get("compilerOptions", {})
            except Exception:
                pass
        
        return False
    
    def _is_package_installed(self, package: str, project_path: str) -> bool:
        """Check if a package is installed."""
        if not self._project_info:
            self._project_info = self._load_project_info()
        
        deps = self._project_info.get("dependencies", {})
        
        # Handle scoped packages
        if package.startswith('@'):
            package_name = '/'.join(package.split('/')[:2])
        else:
            package_name = package.split('/')[0]
        
        return package_name in deps
    
    def _uses_new_jsx_transform(self) -> bool:
        """Check if project uses new JSX transform."""
        # This would check React version and config
        # For now, assume newer projects use it
        return True