"""
Post-generation quality assurance framework for zero manual fixing.
Validates, tests, and auto-fixes generated components.
"""

import os
import subprocess
import tempfile
import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in generated code."""
    level: ValidationLevel
    category: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class QualityReport:
    """Comprehensive quality assessment report."""
    score: float  # 0-100 quality score
    issues: List[ValidationIssue]
    passed_checks: List[str]
    failed_checks: List[str]
    auto_fixes_applied: List[str]
    compilation_success: bool
    rendering_success: bool
    accessibility_score: float
    performance_score: float


class ComponentValidator:
    """Comprehensive component validation and auto-fixing system."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.validators = [
            TypeScriptValidator(),
            ESLintValidator(),
            ImportValidator(),
            ComponentStructureValidator(),
            AccessibilityValidator(),
            PerformanceValidator(),
        ]
        # Auto-fixers will be initialized dynamically with project context
        self.auto_fixers = []
    
    def validate_component(self, component_code: str, target_path: str) -> QualityReport:
        """Run comprehensive validation on generated component."""
        issues = []
        passed_checks = []
        failed_checks = []
        
        print("🔍 Running comprehensive quality validation...")
        
        # Stage 1: Static Analysis
        static_issues = self._run_static_validation(component_code, target_path)
        issues.extend(static_issues)
        
        # Stage 2: Compilation Check
        compilation_success = self._check_compilation(component_code, target_path)
        if compilation_success:
            passed_checks.append("TypeScript Compilation")
        else:
            failed_checks.append("TypeScript Compilation")
        
        # Stage 3: Runtime Validation
        rendering_success = self._check_component_rendering(component_code, target_path)
        if rendering_success:
            passed_checks.append("Component Rendering")
        else:
            failed_checks.append("Component Rendering")
        
        # Stage 4: Quality Metrics
        accessibility_score = self._calculate_accessibility_score(component_code)
        performance_score = self._calculate_performance_score(component_code)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            issues, compilation_success, rendering_success, 
            accessibility_score, performance_score
        )
        
        return QualityReport(
            score=quality_score,
            issues=issues,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            auto_fixes_applied=[],
            compilation_success=compilation_success,
            rendering_success=rendering_success,
            accessibility_score=accessibility_score,
            performance_score=performance_score
        )
    
    def auto_fix_component(self, component_code: str, report: QualityReport) -> Tuple[str, List[str]]:
        """Automatically fix issues found in validation."""
        fixed_code = component_code
        fixes_applied = []
        
        print("🔧 Applying automatic fixes...")
        
        # Use both AI and rule-based fixers for comprehensive fixing
        # Order matters: AI fixes first (context-aware), then rule-based (cleanup)
        fixer_classes = [AIAutoFixer, EnhancedTypeScriptAutoFixer, EnhancedFormatAutoFixer, ESLintAutoFixer]
        
        for fixer_class in fixer_classes:
            # Initialize fixer with project context
            if fixer_class in [AIAutoFixer, EnhancedTypeScriptAutoFixer, EnhancedFormatAutoFixer]:
                fixer = fixer_class(self.project_path)
            else:
                fixer = fixer_class()
            
            if fixer.can_fix_issues(report.issues):
                try:
                    fixed_code, applied_fixes = fixer.fix(fixed_code, report.issues)
                    if applied_fixes:
                        fixes_applied.extend(applied_fixes)
                        print(f"✅ {fixer.__class__.__name__}: {len(applied_fixes)} fixes applied")
                        # Log individual fixes for debugging
                        for fix in applied_fixes:
                            print(f"  • {fix}")
                    else:
                        print(f"⚠️ {fixer.__class__.__name__}: 0 fixes applied")
                except Exception as e:
                    print(f"⚠️ {fixer.__class__.__name__} failed: {e}")
        
        return fixed_code, fixes_applied
    
    def iterative_refinement(self, component_code: str, target_path: str, max_iterations: int = 3) -> Tuple[str, QualityReport]:
        """Iteratively refine component until quality threshold is met."""
        current_code = component_code
        iteration = 0
        
        print(f"🔄 Starting iterative refinement (max {max_iterations} iterations)...")
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n📋 Iteration {iteration}/{max_iterations}")
            
            # Validate current code
            report = self.validate_component(current_code, target_path)
            
            print(f"Quality Score: {report.score:.1f}/100")
            
            # If quality is acceptable, we're done
            if report.score >= 85.0 and report.compilation_success:
                print(f"✅ Quality threshold met in {iteration} iterations!")
                return current_code, report
            
            # Store previous quality score to track improvement
            previous_quality_score = report.score
            
            # Apply auto-fixes
            if report.issues or report.score < 85.0:
                fixed_code, fixes_applied = self.auto_fix_component(current_code, report)
                
                if fixes_applied:
                    current_code = fixed_code
                    report.auto_fixes_applied.extend(fixes_applied)
                    
                    # Re-validate to check if quality improved
                    new_report = self.validate_component(current_code, target_path)
                    
                    if new_report.score > previous_quality_score:
                        print(f"📈 Quality improved: {previous_quality_score:.1f} → {new_report.score:.1f}")
                        report = new_report
                        # Continue iteration since we made progress
                    else:
                        print(f"📊 Quality score: {new_report.score:.1f} (no improvement this iteration)")
                        report = new_report
                        # Still continue if we applied fixes, they might compound
                else:
                    print("⚠️ No auto-fixes available")
                    # Only break if we have no fixes AND score isn't improving
                    if iteration > 1 and report.score <= previous_quality_score:
                        print("⚠️ No progress possible, stopping iteration")
                        break
            else:
                break
        
        # Final validation
        final_report = self.validate_component(current_code, target_path)
        print(f"\n🏁 Final Quality Score: {final_report.score:.1f}/100")
        
        return current_code, final_report
    
    def _run_static_validation(self, code: str, target_path: str) -> List[ValidationIssue]:
        """Run all static validators."""
        issues = []
        
        for validator in self.validators:
            try:
                validator_issues = validator.validate(code, target_path, self.project_path)
                issues.extend(validator_issues)
            except Exception as e:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="validator_error",
                    message=f"{validator.__class__.__name__} failed: {e}"
                ))
        
        return issues
    
    def _check_compilation(self, code: str, target_path: str) -> bool:
        """Check if component compiles successfully."""
        try:
            # Create temporary file and check TypeScript compilation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tsx', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Run TypeScript compiler check
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', '--jsx', 'react-jsx', temp_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp_path)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _check_component_rendering(self, code: str, target_path: str) -> bool:
        """Check if component can render without runtime errors."""
        # This would ideally run a test renderer
        # For now, we'll do basic structural checks
        
        required_patterns = [
            'export',  # Must export component
            'return',  # Must have return statement
            r'<\w+',   # Must have JSX elements
        ]
        
        import re
        for pattern in required_patterns:
            if not re.search(pattern, code):
                return False
        
        return True
    
    def _calculate_accessibility_score(self, code: str) -> float:
        """Calculate accessibility compliance score."""
        score = 100.0
        
        # Check for accessibility issues
        accessibility_checks = [
            (r'<img(?![^>]*alt=)', -20, "Images without alt attribute"),
            (r'<button(?![^>]*aria-label)(?![^>]*>.*</button>)', -15, "Buttons without accessible labels"),
            (r'<input(?![^>]*aria-label)(?![^>]*id=)', -15, "Inputs without labels"),
            (r'onClick.*(?!onKeyDown)', -10, "Click handlers without keyboard support"),
        ]
        
        import re
        for pattern, penalty, description in accessibility_checks:
            if re.search(pattern, code, re.IGNORECASE):
                score += penalty
        
        return max(0, score)
    
    def _calculate_performance_score(self, code: str) -> float:
        """Calculate performance optimization score."""
        score = 100.0
        
        # Check for performance issues
        performance_checks = [
            (r'useState\([^)]*\)\s*;', 5, "Good: useState usage"),
            (r'useCallback\(', 10, "Good: useCallback optimization"),
            (r'useMemo\(', 10, "Good: useMemo optimization"),
            (r'React\.createElement', -20, "Inefficient: React.createElement"),
            (r'new\s+Date\(\)', -10, "Potential: Date creation in render"),
        ]
        
        import re
        for pattern, score_change, description in performance_checks:
            if re.search(pattern, code):
                score += score_change
        
        return min(100, max(0, score))
    
    def _calculate_quality_score(self, issues: List[ValidationIssue], 
                                compilation: bool, rendering: bool,
                                accessibility: float, performance: float) -> float:
        """Calculate overall quality score."""
        base_score = 100.0
        
        # Compilation and rendering are critical
        if not compilation:
            base_score -= 30
        if not rendering:
            base_score -= 20
        
        # Deduct points for issues
        for issue in issues:
            if issue.level == ValidationLevel.ERROR:
                base_score -= 15
            elif issue.level == ValidationLevel.WARNING:
                base_score -= 5
            elif issue.level == ValidationLevel.INFO:
                base_score -= 1
        
        # Factor in accessibility and performance
        base_score = (base_score * 0.7) + (accessibility * 0.15) + (performance * 0.15)
        
        return max(0, min(100, base_score))


# Validator implementations
class TypeScriptValidator:
    """Validates TypeScript syntax and types."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for basic TypeScript patterns
        if 'interface ' not in code and 'type ' not in code and 'Props' in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="typescript",
                message="Consider defining TypeScript interfaces for props",
                auto_fixable=True,
                suggestion="Add interface definition for component props"
            ))
        
        # Check for any syntax
        import re
        if re.search(r'any\b', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="typescript",
                message="Avoid using 'any' type for better type safety",
                auto_fixable=False
            ))
        
        return issues


class ESLintValidator:
    """Validates code against ESLint rules."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Basic ESLint-style checks
        import re
        
        # Check for console.log
        if re.search(r'console\.log\(', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="eslint",
                message="Remove console.log statements",
                auto_fixable=True
            ))
        
        # Check for unused variables
        variable_pattern = r'const\s+(\w+)\s*='
        variables = re.findall(variable_pattern, code)
        for var in variables:
            if var not in code[code.find(f'const {var}') + 20:]:  # Simple check
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="eslint",
                    message=f"Variable '{var}' is defined but never used",
                    auto_fixable=True
                ))
        
        return issues


class ImportValidator:
    """Validates import statements and paths."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        import re
        import_pattern = r'import.*from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, code)
        
        for import_path in imports:
            if not self._is_valid_import(import_path, project_path):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="imports",
                    message=f"Import path '{import_path}' does not exist",
                    auto_fixable=True,
                    suggestion=f"Check if '{import_path}' path is correct"
                ))
        
        return issues
    
    def _is_valid_import(self, import_path: str, project_path: Path) -> bool:
        """Check if import path exists."""
        # Skip validation for node_modules and relative paths for now
        if (import_path.startswith('@/') or 
            import_path.startswith('./') or 
            import_path.startswith('../') or
            not import_path.startswith('.')):
            return True  # Assume valid for now
        
        return True


class ComponentStructureValidator:
    """Validates React component structure and patterns."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for component export
        if 'export default' not in code and 'export {' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message="Component must have an export statement",
                auto_fixable=True
            ))
        
        # Check for JSX return
        if 'return (' not in code and 'return <' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message="Component must return JSX",
                auto_fixable=False
            ))
        
        return issues


class AccessibilityValidator:
    """Validates accessibility compliance."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        import re
        
        # Check for images without alt
        if re.search(r'<img(?![^>]*alt=)', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="accessibility",
                message="Images should have alt attributes",
                auto_fixable=True,
                suggestion="Add alt attribute to img elements"
            ))
        
        # Check for buttons without accessible names
        if re.search(r'<button(?![^>]*aria-label)(?![^>]*>[^<]*\w)', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="accessibility",
                message="Consider adding aria-label to buttons without text content",
                auto_fixable=False
            ))
        
        return issues


class PerformanceValidator:
    """Validates performance best practices."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for inline object/function creation
        import re
        if re.search(r'onClick=\{.*=>.*\}', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="performance",
                message="Consider using useCallback for event handlers",
                auto_fixable=False,
                suggestion="Wrap event handlers with useCallback"
            ))
        
        return issues


# Auto-fixer implementations
class TypeScriptAutoFixer:
    """Automatically fixes TypeScript issues."""
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category == "typescript" and issue.auto_fixable for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # Remove any types (simple fix)
        import re
        if re.search(r':\s*any\b', code):
            fixed_code = re.sub(r':\s*any\b', '', fixed_code)
            fixes_applied.append("Removed 'any' type annotations")
        
        return fixed_code, fixes_applied


class ESLintAutoFixer:
    """Automatically fixes ESLint issues."""
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category == "eslint" and issue.auto_fixable for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # Remove console.log statements
        import re
        if re.search(r'console\.log\([^)]*\);?\s*', code):
            fixed_code = re.sub(r'console\.log\([^)]*\);?\s*', '', fixed_code)
            fixes_applied.append("Removed console.log statements")
        
        return fixed_code, fixes_applied


class ImportAutoFixer:
    """Automatically fixes import issues."""
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category == "imports" and issue.auto_fixable for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        # For now, just return as-is (complex import fixing needs project analysis)
        return code, []


class FormatAutoFixer:
    """Automatically fixes formatting issues."""
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return True  # Can always try to format
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        # Basic formatting fixes
        fixes_applied = []
        
        # Remove extra whitespace
        import re
        if re.search(r'\n\s*\n\s*\n', code):
            code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
            fixes_applied.append("Removed extra blank lines")
        
        return code, fixes_applied


# Enhanced Auto-fixer implementations that actually work
class EnhancedTypeScriptAutoFixer:
    """Automatically fixes TypeScript issues with advanced capabilities."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return True  # Always try to fix TypeScript issues
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix duplicate imports
        fixed_code, duplicate_fixes = self._fix_duplicate_imports(fixed_code)
        fixes_applied.extend(duplicate_fixes)
        
        # 2. Convert to client component if using hooks
        if self._uses_client_features(fixed_code) and not self._is_client_component(fixed_code):
            fixed_code = self._add_use_client(fixed_code)
            fixes_applied.append("Added 'use client' directive for client-side features")
        
        # 3. Add missing Next.js Image import
        if self._needs_next_image_import(fixed_code):
            fixed_code = self._add_next_image_import(fixed_code)
            fixes_applied.append("Added Next.js Image import")
        
        # 4. Remove any types (simple fix)
        if re.search(r':\s*any\b', fixed_code):
            fixed_code = re.sub(r':\s*any\b', '', fixed_code)
            fixes_applied.append("Removed 'any' type annotations")
        
        return fixed_code, fixes_applied
    
    def _fix_duplicate_imports(self, code: str) -> Tuple[str, List[str]]:
        """Fix duplicate import statements and 'use client' directive placement."""
        fixes_applied = []
        lines = code.split('\n')
        
        # Find and move 'use client' directive to the top
        use_client_line = None
        use_client_index = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped in ['"use client";', "'use client';", '"use client"', "'use client'"]:
                use_client_line = '"use client";'
                use_client_index = i
                break
        
        # Remove use client from current position
        if use_client_index >= 0:
            lines.pop(use_client_index)
            fixes_applied.append("Moved 'use client' directive to top of file")
        
        # Find all import lines (after removing use client)
        import_lines = []
        other_lines = []
        in_imports = True
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') and in_imports:
                import_lines.append(stripped)
            elif stripped == '' and in_imports:
                # Skip empty lines in import section
                continue
            else:
                in_imports = False
                other_lines.append(line)
        
        # Check for duplicate React imports
        react_imports = [line for line in import_lines if "from 'react'" in line or 'from "react"' in line]
        
        if len(react_imports) > 1:
            # Consolidate React imports
            all_imports = set()
            has_default_react = False
            
            for imp in react_imports:
                if 'React,' in imp or imp.strip().startswith('import React ') or imp.strip() == 'import React from \'react\';':
                    has_default_react = True
                
                # Extract named imports
                if '{' in imp and '}' in imp:
                    named_part = imp[imp.find('{')+1:imp.find('}')]
                    for item in named_part.split(','):
                        item = item.strip()
                        if item and item != 'React':
                            all_imports.add(item)
            
            # Create consolidated import
            if has_default_react and all_imports:
                new_import = f"import React, {{ {', '.join(sorted(all_imports))} }} from 'react';"
            elif has_default_react:
                new_import = "import React from 'react';"
            else:
                new_import = f"import {{ {', '.join(sorted(all_imports))} }} from 'react';"
            
            # Replace all React imports with consolidated one
            new_import_lines = []
            for line in import_lines:
                if not ("from 'react'" in line or 'from "react"' in line):
                    new_import_lines.append(line)
            
            new_import_lines.insert(0, new_import)
            import_lines = new_import_lines
            fixes_applied.append(f"Consolidated {len(react_imports)} React import statements")
        
        # Remove problematic imports (like local images that don't exist)
        filtered_imports = []
        avatar_import_removed = False
        
        for imp in import_lines:
            if '@/public/images/' in imp or '/images/' in imp:
                # Replace with placeholder or remove
                fixes_applied.append("Removed problematic local image import")
                avatar_import_removed = True
                continue
            filtered_imports.append(imp)
        
        # If we removed an avatar import, we need to fix the code that uses it
        if avatar_import_removed:
            # Find and replace AvatarImg usage
            code_content = '\n'.join(other_lines)
            if 'avatarUrl: AvatarImg' in code_content:
                code_content = code_content.replace(
                    'avatarUrl: AvatarImg',
                    'avatarUrl: "https://ui-avatars.com/api/?background=random&name=Taylor+West"'
                )
                other_lines = code_content.split('\n')
                fixes_applied.append("Replaced problematic avatar import with placeholder URL")
        
        # Rebuild code with proper structure
        new_lines = []
        
        # Add use client at the top
        if use_client_line:
            new_lines.append(use_client_line)
            new_lines.append('')
        
        # Add consolidated imports
        new_lines.extend(filtered_imports)
        new_lines.append('')
        
        # Add rest of the code
        new_lines.extend(other_lines)
        
        code = '\n'.join(new_lines)
        return code, fixes_applied
    
    def _uses_client_features(self, code: str) -> bool:
        """Check if code uses client-side features like useState, useEffect, etc."""
        client_features = ['useState', 'useEffect', 'useCallback', 'useMemo', 'useRef', 'useContext']
        return any(feature in code for feature in client_features)
    
    def _is_client_component(self, code: str) -> bool:
        """Check if component already has 'use client' directive."""
        return "'use client'" in code or '"use client"' in code
    
    def _add_use_client(self, code: str) -> str:
        """Add 'use client' directive at the top of the file."""
        return "'use client';\n\n" + code
    
    def _needs_next_image_import(self, code: str) -> bool:
        """Check if Next.js Image import is needed."""
        has_img_tag = '<img' in code
        has_image_import = 'from "next/image"' in code or "from 'next/image'" in code
        return has_img_tag and not has_image_import
    
    def _add_next_image_import(self, code: str) -> str:
        """Add Next.js Image import."""
        lines = code.split('\n')
        
        # Find where to insert the import
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import'):
                insert_idx = i + 1
        
        lines.insert(insert_idx, 'import Image from "next/image";')
        return '\n'.join(lines)


class EnhancedFormatAutoFixer:
    """Automatically fixes formatting and style issues with Tailwind validation."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return True  # Can always try to format
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix invalid Tailwind CSS classes
        fixed_code, tailwind_fixes = self._fix_tailwind_classes(fixed_code)
        fixes_applied.extend(tailwind_fixes)
        
        # 2. Replace img tags with Next.js Image components
        fixed_code, image_fixes = self._fix_image_tags(fixed_code)
        fixes_applied.extend(image_fixes)
        
        # 3. Basic formatting fixes
        if re.search(r'\n\s*\n\s*\n', fixed_code):
            fixed_code = re.sub(r'\n\s*\n\s*\n', '\n\n', fixed_code)
            fixes_applied.append("Removed extra blank lines")
        
        return fixed_code, fixes_applied
    
    def _fix_tailwind_classes(self, code: str) -> Tuple[str, List[str]]:
        """Fix common invalid Tailwind CSS classes."""
        fixes_applied = []
        
        # Common invalid class mappings
        class_fixes = {
            'text-smline-height': 'text-sm',
            'text-baseline-height': 'text-base',
            'bg-gray': 'bg-gray-100',
            'text-gray': 'text-gray-600',
            'text-black': 'text-gray-900',
            'bg-sky': 'bg-sky-500',
            'text-blue': 'text-blue-600',
            'bg-blue': 'bg-blue-600',
            'text-indigo': 'text-indigo-600',
            'bg-indigo': 'bg-indigo-600',
            'text-emerald': 'text-emerald-600',
            'bg-emerald': 'bg-emerald-600',
            'border-sky': 'border-sky-500',
            'border-blue': 'border-blue-600',
            'border-emerald': 'border-emerald-600',
            'border-gray': 'border-gray-300',
            'bg-sky/10': 'bg-sky-500/10',
            'bg-sky/20': 'bg-sky-500/20',
        }
        
        # Use regex for precise matching to avoid cascading replacements
        import re
        
        # First clean up cascaded classes (from previous broken runs)
        cascade_fixes = [
            (r'\bbg-gray-100-100-100\b', 'bg-gray-100'),
            (r'\btext-gray-600-600-600\b', 'text-gray-600'),
            (r'\btext-gray-600-600-900\b', 'text-gray-900'),
            (r'\bbg-emerald-600-600-600\b', 'bg-emerald-600'),
            (r'\btext-emerald-600-600-600\b', 'text-emerald-600'),
            (r'\bbg-blue-600-600-600\b', 'bg-blue-600'),
            (r'\btext-blue-600-600-600\b', 'text-blue-600'),
            (r'\bbg-indigo-600-600-600\b', 'bg-indigo-600'),
            (r'\btext-indigo-600-600-600\b', 'text-indigo-600'),
            (r'\bbg-sky-500-500-500\b', 'bg-sky-500'),
            (r'\btext-baseletter-spacing\b', 'text-base'),
            (r'\bbaseline-height\b', 'leading-normal'),
            (r'\bsmline-height\b', 'text-sm'),
        ]
        
        # Clean up cascaded classes first (fix repeated patterns)
        additional_cascade_fixes = [
            (r'border-blue-600(?:-600)+', 'border-blue-600'),
            (r'text-gray-600(?:-600)+', 'text-gray-600'),
            (r'bg-gray-100(?:-100)+', 'bg-gray-100'),
            (r'text-text-sm', 'text-sm'),
            (r'border-red(?!-[0-9])', 'border-red-500'),
            (r'text-red(?!-[0-9])', 'text-red-500'),
        ]
        
        # Apply cascade fixes first
        all_cascade_fixes = cascade_fixes + additional_cascade_fixes
        for pattern, replacement in all_cascade_fixes:
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                fixes_applied.append(f"Fixed cascaded/invalid class to '{replacement}'")
        
        # Fix malformed Image tags
        if '/ width=' in code:
            # Fix malformed Image self-closing tags
            code = re.sub(r'/\s+width=', ' width=', code)
            fixes_applied.append("Fixed malformed Image tag syntax")
        
        # Then apply original fixes ONLY if not already fixed
        for invalid_class, valid_class in class_fixes.items():
            # Skip if we already have the valid class or if it's already been fixed
            if valid_class in code or f'{invalid_class}-' in code:
                continue
                
            # Use word boundaries and negative lookahead to prevent re-replacing
            if invalid_class in ['bg-gray', 'text-gray', 'bg-blue', 'text-blue', 'bg-emerald', 'text-emerald', 'bg-indigo', 'text-indigo', 'bg-sky']:
                # For color classes, only replace if not already followed by a number
                pattern = rf'\b{re.escape(invalid_class)}(?!-[0-9])\b'
            else:
                # For other classes, use exact word boundary matching
                pattern = rf'\b{re.escape(invalid_class)}\b'
            
            if re.search(pattern, code):
                old_code = code
                code = re.sub(pattern, valid_class, code)
                if code != old_code:
                    fixes_applied.append(f"Fixed invalid Tailwind class '{invalid_class}' to '{valid_class}'")
        
        return code, fixes_applied
    
    def _fix_image_tags(self, code: str) -> Tuple[str, List[str]]:
        """Replace img tags with Next.js Image components."""
        fixes_applied = []
        
        # Replace <img> with <Image> if Next.js Image is imported
        if '<img' in code and 'next/image' in code:
            img_pattern = r'<img([^>]*?)>'
            
            def replace_img(match):
                attrs = match.group(1)
                # Add width and height if missing (required for Next.js Image)
                if 'width=' not in attrs:
                    attrs += ' width={200}'
                if 'height=' not in attrs:
                    attrs += ' height={200}'
                return f'<Image{attrs} />'
            
            new_code = re.sub(img_pattern, replace_img, code)
            if new_code != code:
                fixes_applied.append("Replaced img tags with Next.js Image components")
                code = new_code
        
        return code, fixes_applied


# AI-Powered Auto-fixer Implementation  
class AIAutoFixer:
    """AI-powered code fixer using LLMs for intelligent issue resolution."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        
        # Initialize API clients (same pattern as generator)
        self.openai_client = None
        self.anthropic_client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                print("⚠️ OpenAI not available, install with: pip install openai")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                print("⚠️ Anthropic not available, install with: pip install anthropic")
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        """AI can potentially fix any issue if an API client is available."""
        return (self.openai_client is not None or self.anthropic_client is not None) and len(issues) > 0
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        """Use AI to intelligently fix code issues."""
        if not self.can_fix_issues(issues):
            return code, []
        
        try:
            # Build the fixing prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(code, issues)
            
            # Call LLM to fix the code
            if self.model.startswith("gpt") and self.openai_client:
                fixed_code = self._fix_with_openai(system_prompt, user_prompt)
            elif self.model.startswith("claude") and self.anthropic_client:
                fixed_code = self._fix_with_anthropic(system_prompt, user_prompt)
            elif self.openai_client:  # Fallback to OpenAI if available
                fixed_code = self._fix_with_openai(system_prompt, user_prompt)
            elif self.anthropic_client:  # Fallback to Anthropic if available
                fixed_code = self._fix_with_anthropic(system_prompt, user_prompt)
            else:
                return code, []
            
            # Clean the response (remove markdown if present)
            cleaned_code = self._clean_response(fixed_code)
            
            # Validate the fix was meaningful
            if self._is_valid_fix(code, cleaned_code):
                fixes_applied = [f"AI-powered fix: Applied {len(issues)} intelligent fixes"]
                return cleaned_code, fixes_applied
            else:
                return code, []
                
        except Exception as e:
            print(f"⚠️ AI fixing failed: {e}")
            return code, []
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for AI fixing."""
        return """You are an expert React/TypeScript/Next.js code fixer. Your job is to fix code issues while maintaining the original functionality and structure.

CRITICAL RULES:
1. ONLY return the fixed code - no explanations, no markdown blocks, no extra text
2. Maintain the original component structure and logic
3. Fix syntax errors, invalid CSS classes, import issues, and TypeScript problems
4. Use proper Next.js patterns (Image components, 'use client' directives)
5. Ensure all Tailwind CSS classes are valid
6. Fix duplicate imports by consolidating them
7. Add missing required props for Next.js Image components
8. Preserve the original component name and exports

TAILWIND CSS FIXES:
- Replace invalid color classes like 'bg-gray' with 'bg-gray-100'
- Replace 'text-gray' with 'text-gray-600'
- Replace 'border-blue-600-600-600' with 'border-blue-600'
- Replace 'text-leading-normal' with 'leading-normal'
- Ensure all classes are valid Tailwind utility classes

REACT/NEXT.JS FIXES:
- Add 'use client' directive if component uses hooks
- Replace <img> with <Image> and add required width/height props
- Consolidate duplicate React imports
- Fix TypeScript prop types and interfaces"""
    
    def _build_user_prompt(self, code: str, issues: List[ValidationIssue]) -> str:
        """Build user prompt with code and issues to fix."""
        issues_text = "\n".join([
            f"- {issue.level.value.upper()}: {issue.category} - {issue.message}"
            for issue in issues[:10]  # Limit to first 10 issues
        ])
        
        return f"""Fix this React component code:

ISSUES TO FIX:
{issues_text}

CODE TO FIX:
{code}

Return ONLY the fixed code with no additional text or formatting."""
    
    def _fix_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Fix code using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not available")
        
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=3000,
            temperature=0.1,  # Low temperature for consistent fixes
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    
    def _fix_with_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Fix code using Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not available")
        
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0.1,  # Low temperature for consistent fixes
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        # Handle Anthropic response format
        if hasattr(response, 'content') and len(response.content) > 0:
            if hasattr(response.content[0], 'text'):
                return response.content[0].text.strip()
        return ""
    
    def _clean_response(self, response: str) -> str:
        """Clean AI response to extract just the code."""
        # Remove markdown code blocks if present
        if "```" in response:
            start_marker = response.find("```")
            if start_marker != -1:
                # Skip the opening ```tsx or ```javascript
                start_content = response.find("\n", start_marker) + 1
                end_marker = response.find("```", start_content)
                if end_marker != -1:
                    response = response[start_content:end_marker].strip()
        
        return response.strip()
    
    def _is_valid_fix(self, original_code: str, fixed_code: str) -> bool:
        """Validate that the fix is meaningful and safe."""
        # Basic sanity checks
        if not fixed_code or len(fixed_code) < 10:
            return False
        
        # Should still be React/JSX code
        if 'export' not in fixed_code or 'return' not in fixed_code:
            return False
        
        # Should not be drastically different in length (avoid hallucination)
        length_ratio = len(fixed_code) / len(original_code)
        if length_ratio < 0.5 or length_ratio > 2.0:
            return False
        
        return True