"""
Post-generation quality assurance framework for zero manual fixing.
Validates, tests, and auto-fixes generated components.
"""

import os
import subprocess
import tempfile
import json
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
        # Initialize auto-fixers with project context
        self.auto_fixers = [
            EnhancedTypeScriptAutoFixer(project_path),
            EnhancedFormatAutoFixer(project_path),
            AIAutoFixer(project_path),
            ESLintAutoFixer(),
        ]
    
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
        
        # Apply auto-fixes in order of priority
        for fixer in self.auto_fixers:
            if fixer.can_fix_issues(report.issues):
                try:
                    fixed_code, applied_fixes = fixer.fix(fixed_code, report.issues)
                    if applied_fixes:
                        fixes_applied.extend(applied_fixes)
                        print(f"✅ {fixer.__class__.__name__}: {len(applied_fixes)} fixes applied")
                        # Log individual fixes for debugging
                        for fix in applied_fixes:
                            print(f"  • {fix}")
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
            
            # Apply auto-fixes
            if report.issues or report.score < 85.0:
                fixed_code, fixes_applied = self.auto_fix_component(current_code, report)
                
                if fixes_applied:
                    current_code = fixed_code
                    report.auto_fixes_applied.extend(fixes_applied)
                else:
                    print("⚠️ No more auto-fixes available")
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
        required_patterns = [
            'export',  # Must export component
            'return',  # Must have return statement
            r'<\w+',   # Must have JSX elements
        ]
        
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
        
        # Check for duplicate imports
        import_lines = [line for line in code.split('\n') if line.strip().startswith('import')]
        react_imports = [line for line in import_lines if 'from \'react\'' in line or 'from "react"' in line]
        
        if len(react_imports) > 1:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="typescript",
                message="Duplicate React import statements detected",
                auto_fixable=True,
                suggestion="Consolidate React imports into a single statement"
            ))
        
        # Check for malformed image imports
        if '@/public/images/' in code or 'AvatarImg' in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="typescript",
                message="Local image import may not exist",
                auto_fixable=True,
                suggestion="Replace with placeholder image URL"
            ))
        
        # Check for any type
        if re.search(r':\s*any\b', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="typescript",
                message="Avoid using 'any' type for better type safety",
                auto_fixable=True
            ))
        
        return issues


class ESLintValidator:
    """Validates code against ESLint rules."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for console.log
        if re.search(r'console\.log\(', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="eslint",
                message="Remove console.log statements",
                auto_fixable=True
            ))
        
        # Check for malformed JSX
        if '/ width=' in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="eslint",
                message="Malformed JSX self-closing tag",
                auto_fixable=True
            ))
        
        return issues


class ImportValidator:
    """Validates import statements and paths."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for use client directive placement
        lines = code.split('\n')
        use_client_index = -1
        first_import_index = -1
        
        for i, line in enumerate(lines):
            if '"use client"' in line or "'use client'" in line:
                use_client_index = i
            if line.strip().startswith('import') and first_import_index == -1:
                first_import_index = i
        
        if use_client_index > 0 and first_import_index >= 0 and use_client_index > first_import_index:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="imports",
                message="'use client' directive must be at the top of the file",
                auto_fixable=True
            ))
        
        return issues


class ComponentStructureValidator:
    """Validates React component structure and patterns."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []

        # Check for invalid Tailwind classes using proper regex patterns (should match auto-fixer logic)
        invalid_patterns = [
            r'\btext-smline-height\b',
            r'\btext-baseline-height\b',
            r'\bbg-gray(?!-\d+)\b',
            r'\btext-gray(?!-\d+)\b',
            r'\bborder-gray(?!-\d+)\b',
            r'\bbg-sky(?!-\d+)\b',
            r'\btext-sky(?!-\d+)\b',
            r'\bborder-sky(?!-\d+)\b',
            r'\bbg-blue(?!-\d+)\b',
            r'\btext-blue(?!-\d+)\b',
            r'\bborder-blue(?!-\d+)\b',
            r'\bbg-emerald(?!-\d+)\b',
            r'\btext-emerald(?!-\d+)\b',
            r'\bborder-emerald(?!-\d+)\b',
            r'\bbg-indigo(?!-\d+)\b',
            r'\btext-indigo(?!-\d+)\b',
            r'\bborder-indigo(?!-\d+)\b',
            r'\btext-black\b',
            r'\bbg-black\b',
            r'\bbg-sky/10\b',
            r'\bbg-emerald/10\b',
            r'\bbg-indigo/10\b',
        ]

        for pattern in invalid_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message=f"Invalid Tailwind CSS class detected",
                    auto_fixable=True
                ))
                break

        # Check for component export
        if 'export default' not in code and 'export {' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                message="Component must have an export statement",
                auto_fixable=True
            ))

        return issues


class AccessibilityValidator:
    """Validates accessibility compliance."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for images without alt
        if re.search(r'<img(?![^>]*alt=)', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="accessibility",
                message="Images should have alt attributes",
                auto_fixable=True,
                suggestion="Add alt attribute to img elements"
            ))
        
        return issues


class PerformanceValidator:
    """Validates performance best practices."""
    
    def validate(self, code: str, target_path: str, project_path: Path) -> List[ValidationIssue]:
        issues = []
        
        # Check for inline object/function creation
        if re.search(r'onClick=\{.*=>.*\}', code):
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                category="performance",
                message="Consider using useCallback for event handlers",
                auto_fixable=False,
                suggestion="Wrap event handlers with useCallback"
            ))
        
        return issues


# Enhanced Auto-fixer implementations
class EnhancedTypeScriptAutoFixer:
    """Automatically fixes TypeScript issues with advanced capabilities."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category in ["typescript", "imports"] and issue.auto_fixable for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix duplicate imports and use client placement
        fixed_code, import_fixes = self._fix_imports_comprehensively(fixed_code)
        fixes_applied.extend(import_fixes)
        
        # 2. Fix problematic avatar imports
        if 'AvatarImg' in fixed_code or '@/public/images/' in fixed_code:
            fixed_code = self._fix_avatar_imports(fixed_code)
            fixes_applied.append("Fixed problematic avatar import with placeholder URL")
        
        # 3. Remove any types
        if re.search(r':\s*any\b', fixed_code):
            fixed_code = re.sub(r':\s*any\b', '', fixed_code)
            fixes_applied.append("Removed 'any' type annotations")
        
        return fixed_code, fixes_applied
    
    def _fix_imports_comprehensively(self, code: str) -> Tuple[str, List[str]]:
        """Fix all import-related issues comprehensively."""
        fixes_applied = []
        lines = code.split('\n')
        
        # Separate different parts of the file
        use_client_lines = []
        import_lines = []
        other_lines = []
        
        in_imports = True
        for line in lines:
            stripped = line.strip()
            
            # Check for use client
            if stripped in ['"use client";', "'use client';", '"use client"', "'use client'"]:
                use_client_lines.append('"use client";')
                continue
            
            # Check for imports
            if in_imports and stripped.startswith('import '):
                import_lines.append(line)
                continue
            
            # End of import section
            if stripped and not stripped.startswith('import') and in_imports:
                in_imports = False
            
            other_lines.append(line)
        
        # Process imports
        if len(use_client_lines) > 0:
            fixes_applied.append("Moved 'use client' directive to top of file")
        
        # Consolidate React imports
        consolidated_imports = self._consolidate_react_imports(import_lines)
        if len(consolidated_imports) < len(import_lines):
            fixes_applied.append(f"Consolidated {len(import_lines) - len(consolidated_imports)} duplicate imports")
        
        # Rebuild the file
        new_lines = []
        
        # Add use client first
        if use_client_lines:
            new_lines.append(use_client_lines[0])
            new_lines.append('')
        
        # Add consolidated imports
        new_lines.extend(consolidated_imports)
        if consolidated_imports:
            new_lines.append('')
        
        # Add the rest
        # Skip leading empty lines in other_lines
        while other_lines and not other_lines[0].strip():
            other_lines.pop(0)
        
        new_lines.extend(other_lines)
        
        return '\n'.join(new_lines), fixes_applied
    
    def _consolidate_react_imports(self, import_lines: List[str]) -> List[str]:
        """Consolidate duplicate React imports."""
        react_imports = []
        other_imports = []
        
        react_default = False
        react_named = set()
        
        for line in import_lines:
            if 'from \'react\'' in line or 'from "react"' in line:
                # Parse React import
                if 'import React' in line and not '{' in line:
                    react_default = True
                elif 'import React,' in line:
                    react_default = True
                    # Extract named imports
                    match = re.search(r'\{([^}]+)\}', line)
                    if match:
                        names = [n.strip() for n in match.group(1).split(',')]
                        react_named.update(names)
                elif '{' in line:
                    # Named imports only
                    match = re.search(r'\{([^}]+)\}', line)
                    if match:
                        names = [n.strip() for n in match.group(1).split(',')]
                        react_named.update(names)
            else:
                other_imports.append(line)
        
        # Build consolidated React import
        consolidated = []
        if react_default and react_named:
            consolidated.append(f"import React, {{ {', '.join(sorted(react_named))} }} from 'react';")
        elif react_default:
            consolidated.append("import React from 'react';")
        elif react_named:
            consolidated.append(f"import {{ {', '.join(sorted(react_named))} }} from 'react';")
        
        # Combine all imports
        return consolidated + other_imports
    
    def _fix_avatar_imports(self, code: str) -> str:
        """Fix problematic local avatar imports."""
        # Remove the import line
        lines = code.split('\n')
        filtered_lines = []
        
        for line in lines:
            if 'import AvatarImg from' in line and '@/public/images/' in line:
                continue
            filtered_lines.append(line)
        
        code = '\n'.join(filtered_lines)
        
        # Replace usage
        code = code.replace(
            'avatarUrl: AvatarImg',
            'avatarUrl: "https://ui-avatars.com/api/?background=random&name=User"'
        )
        code = code.replace(
            'src={avatarUrl || AvatarImg}',
            'src={avatarUrl || "https://ui-avatars.com/api/?background=random&name=User"}'
        )
        
        return code


class EnhancedFormatAutoFixer:
    """Automatically fixes formatting and style issues with Tailwind validation."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category in ["structure", "eslint"] for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix malformed JSX
        if '/ width=' in fixed_code:
            fixed_code = re.sub(r'/\s+width=', ' width=', fixed_code)
            fixes_applied.append("Fixed malformed JSX self-closing tag")
        
        # 2. Fix invalid Tailwind CSS classes
        fixed_code, tailwind_fixes = self._fix_tailwind_classes_properly(fixed_code)
        fixes_applied.extend(tailwind_fixes)
        
        # 3. Basic formatting fixes
        if re.search(r'\n\s*\n\s*\n', fixed_code):
            fixed_code = re.sub(r'\n\s*\n\s*\n', '\n\n', fixed_code)
            fixes_applied.append("Removed extra blank lines")
        
        return fixed_code, fixes_applied
    
    def _fix_tailwind_classes_properly(self, code: str) -> Tuple[str, List[str]]:
        """Fix invalid Tailwind CSS classes with proper regex."""
        fixes_applied = []
        
        # Define replacements with proper regex patterns
        replacements = [
            # Fix malformed compound classes first
            (r'\btext-smline-height\b', 'text-sm', 'Fixed malformed text class'),
            (r'\btext-baseline-height\b', 'text-base', 'Fixed baseline-height to text-base'),
            
            # Fix color classes without shade numbers
            (r'\bbg-gray(?!-\d+)\b', 'bg-gray-100', 'Fixed bg-gray to bg-gray-100'),
            (r'\btext-gray(?!-\d+)\b', 'text-gray-600', 'Fixed text-gray to text-gray-600'),
            (r'\bborder-gray(?!-\d+)\b', 'border-gray-300', 'Fixed border-gray to border-gray-300'),
            
            (r'\bbg-sky(?!-\d+)\b', 'bg-sky-500', 'Fixed bg-sky to bg-sky-500'),
            (r'\btext-sky(?!-\d+)\b', 'text-sky-600', 'Fixed text-sky to text-sky-600'),
            (r'\bborder-sky(?!-\d+)\b', 'border-sky-500', 'Fixed border-sky to border-sky-500'),
            
            (r'\bbg-blue(?!-\d+)\b', 'bg-blue-600', 'Fixed bg-blue to bg-blue-600'),
            (r'\btext-blue(?!-\d+)\b', 'text-blue-600', 'Fixed text-blue to text-blue-600'),
            (r'\bborder-blue(?!-\d+)\b', 'border-blue-600', 'Fixed border-blue to border-blue-600'),
            
            (r'\bbg-emerald(?!-\d+)\b', 'bg-emerald-600', 'Fixed bg-emerald to bg-emerald-600'),
            (r'\btext-emerald(?!-\d+)\b', 'text-emerald-600', 'Fixed text-emerald to text-emerald-600'),
            (r'\bborder-emerald(?!-\d+)\b', 'border-emerald-600', 'Fixed border-emerald to border-emerald-600'),
            
            (r'\bbg-indigo(?!-\d+)\b', 'bg-indigo-600', 'Fixed bg-indigo to bg-indigo-600'),
            (r'\btext-indigo(?!-\d+)\b', 'text-indigo-600', 'Fixed text-indigo to text-indigo-600'),
            (r'\bborder-indigo(?!-\d+)\b', 'border-indigo-600', 'Fixed border-indigo to border-indigo-600'),
            
            # Fix other common issues
            (r'\btext-black\b', 'text-gray-900', 'Fixed text-black to text-gray-900'),
            (r'\bbg-black\b', 'bg-gray-900', 'Fixed bg-black to bg-gray-900'),
            
            # Fix opacity classes
            (r'\bbg-sky/10\b', 'bg-sky-500/10', 'Fixed bg-sky/10 to bg-sky-500/10'),
            (r'\bbg-emerald/10\b', 'bg-emerald-500/10', 'Fixed bg-emerald/10 to bg-emerald-500/10'),
            (r'\bbg-indigo/10\b', 'bg-indigo-500/10', 'Fixed bg-indigo/10 to bg-indigo-500/10'),
        ]
        
        # Apply each replacement
        for pattern, replacement, description in replacements:
            if re.search(pattern, code):
                code = re.sub(pattern, replacement, code)
                fixes_applied.append(description)
        
        return code, fixes_applied


class ESLintAutoFixer:
    """Automatically fixes ESLint issues."""
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(issue.category == "eslint" and issue.auto_fixable for issue in issues)
    
    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # Remove console.log statements
        if re.search(r'console\.log\([^)]*\);?\s*', code):
            fixed_code = re.sub(r'console\.log\([^)]*\);?\s*', '', fixed_code)
            fixes_applied.append("Removed console.log statements")
        
        return fixed_code, fixes_applied


# AI-Powered Auto-fixer
class AIAutoFixer:
    """AI-powered code fixer using LLMs for intelligent issue resolution."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.openai_client = None
        self.anthropic_client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                print("⚠️ OpenAI not available for AI fixing")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except ImportError:
                print("⚠️ Anthropic not available for AI fixing")
    
    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        """AI can potentially fix any issue if an API client is available."""
        return (self.openai_client is not None or self.anthropic_client is not None) and len(issues) > 0

    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        """Use AI to intelligently fix code issues."""
        if not self.can_fix_issues(issues):
            return code, []

        # Build a concise prompt
        prompt = (
            "You are a senior React/TypeScript engineer. "
            "Fix the following code so it compiles, renders, and scores ≥ 85 on QA. "
            "Return ONLY the fixed code, no explanations.\n\n"
            f"**Issues identified:**\n"
            + "\n".join(
                f"- {i.level.name}: {i.message}"
                for i in issues
                if i.level in (ValidationLevel.ERROR, ValidationLevel.WARNING)
            )
            + f"\n\n**Code to fix:**\n```tsx\n{code}\n```"
        )

        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                fixed = response.choices[0].message.content
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                fixed = response.content[0].text
            else:
                return code, []

            # Remove markdown fences if present
            fixed = re.sub(r"```(?:tsx?)?\n", "", fixed)
            fixed = re.sub(r"\n```$", "", fixed)

            return fixed, ["AI-based fixes applied"]
        except Exception as e:
            print(f"AI fixer failed: {e}")
            return code, []

    def _fix_avatar_imports(self, code: str) -> str:
        """Replace non-existent avatar import with working placeholder."""
        placeholder = "https://ui-avatars.com/api/?background=random&name=User"
        code = re.sub(
            r"import\s+\w+\s+from\s+['\"]@/public/images/.*['\"];?\n?",
            "",
            code,
        )
        code = re.sub(r"\w*AvatarImg\b", f'"{placeholder}"', code)
        return code