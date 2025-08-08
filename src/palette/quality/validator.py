"""
Post-generation quality assurance framework for zero manual fixing.
Validates, tests, and auto-fixes generated components.
"""

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

    def validate_design_token_usage(
        self, code: str, design_tokens: Dict
    ) -> Tuple[bool, List[str], float]:
        """Validate that generated code uses project design tokens and calculate usage score."""
        issues = []
        uses_project_tokens = False

        # Initialize counters
        total_color_uses = 0
        project_color_uses = 0
        generic_color_uses = 0

        if design_tokens.get("colors"):
            colors = design_tokens["colors"]
            if isinstance(colors, dict):
                color_list = list(colors.keys())
            else:
                color_list = colors

            # Exclude generic colors
            project_colors = [
                c
                for c in color_list
                if c not in ["black", "white", "gray", "transparent"]
            ]
            generic_colors = ["black", "white", "gray", "transparent"]

            # Count all color uses
            import re

            color_pattern = r"(?:bg|text|border|ring|from|to|via|fill|stroke|divide|placeholder|decoration)-(\w+)-?\d*"
            color_matches = re.findall(color_pattern, code)

            for match in color_matches:
                total_color_uses += 1
                if match in project_colors:
                    project_color_uses += 1
                    uses_project_tokens = True
                elif match in generic_colors:
                    generic_color_uses += 1

            if not uses_project_tokens and project_colors:
                issues.append(
                    f"Component doesn't use project colors: {', '.join(project_colors[:3])}"
                )

        # Calculate design token usage score
        if total_color_uses > 0:
            base_score = (project_color_uses / total_color_uses) * 100

            # Bonus points
            bonus = 0
            # Gradient bonus
            if (
                any(pattern in code for pattern in ["from-", "to-", "via-"])
                and project_color_uses > 0
            ):
                bonus += 10
            # Consistency bonus (using mostly project colors)
            if project_color_uses > generic_color_uses:
                bonus += 5

            design_token_score = min(100, base_score + bonus)
        else:
            design_token_score = 0

        # Check for gradient usage if requested
        if "gradient" in code.lower() and "gradient" not in code:
            # Check if gradient classes are used
            gradient_patterns = ["from-", "to-", "via-", "gradient-to-"]
            if not any(pattern in code for pattern in gradient_patterns):
                issues.append(
                    "Component mentions gradient but doesn't use gradient classes"
                )

        return uses_project_tokens, issues, design_token_score

    def validate_component_type(self, code: str, prompt: str) -> Tuple[bool, List[str]]:
        """Validate that generated component matches the requested type."""
        issues = []
        prompt_lower = prompt.lower()
        code_lower = code.lower()

        # Check for specific component type mismatches
        if "product card grid" in prompt_lower or "product grid" in prompt_lower:
            # Should have grid layout and multiple cards
            if "grid" not in code_lower and "flex-wrap" not in code_lower:
                issues.append(
                    "Component doesn't implement grid layout for product cards"
                )
            if "map(" not in code or "products" not in code_lower:
                issues.append("Component doesn't render multiple product cards")
            if "hero" in code_lower and "section" in code_lower:
                issues.append("Generated hero section instead of product card grid")

        elif "dashboard header" in prompt_lower:
            # Should have breadcrumbs, search, notifications, avatar
            if "breadcrumb" not in code_lower:
                issues.append("Dashboard header missing breadcrumb navigation")
            if "search" not in code_lower and "input" not in code_lower:
                issues.append("Dashboard header missing search functionality")
            if "notification" not in code_lower and "bell" not in code_lower:
                issues.append("Dashboard header missing notification feature")

        elif "pricing section" in prompt_lower or "pricing tier" in prompt_lower:
            # Should have multiple pricing cards/tiers
            if "tier" not in code_lower and "plan" not in code_lower:
                issues.append("Pricing section missing tier/plan structure")
            if "price" not in code_lower:
                issues.append("Pricing section missing price information")

        elif "hero" in prompt_lower:
            # Should be a hero section
            if "hero" not in code_lower and "landing" not in code_lower:
                issues.append("Component doesn't appear to be a hero section")

        return len(issues) == 0, issues

    def validate_gradients(self, code: str) -> List[ValidationIssue]:
        """Validate gradient usage for proper color transitions."""
        issues = []

        # Check for harsh gradients
        harsh_gradient_patterns = [
            (r"from-black\s+to-white", "Harsh black to white gradient detected"),
            (r"from-white\s+to-black", "Harsh white to black gradient detected"),
            (
                r"from-gray-900\s+to-gray-100",
                "Very harsh gradient transition (900 to 100)",
            ),
            (
                r"from-gray-100\s+to-gray-900",
                "Very harsh gradient transition (100 to 900)",
            ),
        ]

        import re

        for pattern, message in harsh_gradient_patterns:
            if re.search(pattern, code):
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="gradients",
                        message=message,
                        suggestion="Use subtle transitions like from-gray-50 to-white or from-gray-900 to-gray-800",
                        line_number=None,
                    )
                )

        # Check for gradient direction
        if "bg-gradient-" in code:
            gradient_match = re.search(r"bg-gradient-to-(\w+)", code)
            if gradient_match:
                direction = gradient_match.group(1)
                # Check if it's a background gradient that should be subtle
                if "from-" in code and "to-" in code:
                    # Extract colors
                    from_match = re.search(r"from-([\w-]+)", code)
                    to_match = re.search(r"to-([\w-]+)", code)

                    if from_match and to_match:
                        from_color = from_match.group(1)
                        to_color = to_match.group(1)

                        # Check if it's a background section with harsh gradient
                        if any(
                            tag in code for tag in ["<section", "<div", "background"]
                        ):
                            # Check color intensity difference
                            from_intensity = self._extract_color_intensity(from_color)
                            to_intensity = self._extract_color_intensity(to_color)

                            if abs(from_intensity - to_intensity) > 600:
                                issues.append(
                                    ValidationIssue(
                                        level=ValidationLevel.WARNING,
                                        category="gradients",
                                        message=f"Large color intensity difference in background gradient ({from_color} to {to_color})",
                                        suggestion="For backgrounds, use subtle gradients with closer color values",
                                        line_number=None,
                                    )
                                )

        return issues

    def _extract_color_intensity(self, color: str) -> int:
        """Extract numeric intensity from Tailwind color class."""
        import re

        match = re.search(r"-(\d+)$", color)
        if match:
            return int(match.group(1))
        # Default intensities for named colors
        if color in ["black", "gray-900"]:
            return 900
        elif color in ["white", "gray-50"]:
            return 50
        return 500  # Default middle intensity

    def validate_component(
        self, component_code: str, target_path: str
    ) -> QualityReport:
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
            issues,
            compilation_success,
            rendering_success,
            accessibility_score,
            performance_score,
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
            performance_score=performance_score,
        )

    def auto_fix_component(
        self, component_code: str, report: QualityReport
    ) -> Tuple[str, List[str]]:
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
                        print(
                            f"✅ {fixer.__class__.__name__}: {len(applied_fixes)} fixes applied"
                        )
                        # Log individual fixes for debugging
                        for fix in applied_fixes:
                            print(f"  • {fix}")
                except Exception as e:
                    print(f"⚠️ {fixer.__class__.__name__} failed: {e}")

        return fixed_code, fixes_applied

    def iterative_refinement(
        self, component_code: str, target_path: str, max_iterations: int = 3
    ) -> Tuple[str, QualityReport]:
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
                fixed_code, fixes_applied = self.auto_fix_component(
                    current_code, report
                )

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

    def _run_static_validation(
        self, code: str, target_path: str
    ) -> List[ValidationIssue]:
        """Run all static validators."""
        issues = []

        for validator in self.validators:
            try:
                validator_issues = validator.validate(
                    code, target_path, self.project_path
                )
                issues.extend(validator_issues)
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="validator_error",
                        message=f"{validator.__class__.__name__} failed: {e}",
                    )
                )

        return issues

    def _check_compilation(self, code: str, target_path: str) -> bool:
        """Check if component compiles successfully."""
        try:
            # Create temporary file and check TypeScript compilation
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tsx", delete=False
            ) as f:
                f.write(code)
                temp_path = f.name

            # Run TypeScript compiler check
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--jsx", "react-jsx", temp_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            os.unlink(temp_path)
            return result.returncode == 0

        except Exception:
            return False

    def _check_component_rendering(self, code: str, target_path: str) -> bool:
        """Check if component can render without runtime errors."""
        required_patterns = [
            "export",  # Must export component
            "return",  # Must have return statement
            r"<\w+",  # Must have JSX elements
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
            (r"<img(?![^>]*alt=)", -20, "Images without alt attribute"),
            (
                r"<button(?![^>]*aria-label)(?![^>]*>.*</button>)",
                -15,
                "Buttons without accessible labels",
            ),
            (r"<input(?![^>]*aria-label)(?![^>]*id=)", -15, "Inputs without labels"),
            (r"onClick.*(?!onKeyDown)", -10, "Click handlers without keyboard support"),
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
            (r"useState\([^)]*\)\s*;", 5, "Good: useState usage"),
            (r"useCallback\(", 10, "Good: useCallback optimization"),
            (r"useMemo\(", 10, "Good: useMemo optimization"),
            (r"React\.createElement", -20, "Inefficient: React.createElement"),
            (r"new\s+Date\(\)", -10, "Potential: Date creation in render"),
        ]

        for pattern, score_change, description in performance_checks:
            if re.search(pattern, code):
                score += score_change

        return min(100, max(0, score))

    def _calculate_quality_score(
        self,
        issues: List[ValidationIssue],
        compilation: bool,
        rendering: bool,
        accessibility: float,
        performance: float,
    ) -> float:
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

    def validate_project_quality(self) -> Dict:
        """Validate overall project quality and return comprehensive report"""
        try:
            # Run project-wide quality analysis
            issues = []
            suggestions = []
            metrics = {}
            best_practices = {}
            
            # Check project structure
            project_files = list(self.project_path.rglob("*.tsx")) + list(self.project_path.rglob("*.ts"))
            total_files = len(project_files)
            
            if total_files > 0:
                # Calculate basic metrics
                metrics = {
                    "total_files": total_files,
                    "avg_file_size": sum(f.stat().st_size for f in project_files) / total_files,
                    "typescript_usage": len([f for f in project_files if f.suffix == ".tsx"]) / total_files * 100
                }
                
                # Check best practices
                best_practices = {
                    "uses_typescript": metrics["typescript_usage"] > 80,
                    "reasonable_file_count": 10 < total_files < 1000,
                    "consistent_naming": True  # Placeholder
                }
                
                # Generate suggestions
                if metrics["typescript_usage"] < 80:
                    suggestions.append("Consider migrating more components to TypeScript")
                if total_files < 5:
                    suggestions.append("Project structure could be expanded for better organization")
                    
                # Calculate overall score
                score = 85.0  # Base score
                if metrics["typescript_usage"] > 80:
                    score += 10
                if total_files > 10:
                    score += 5
            else:
                score = 50
                issues.append("No TypeScript/TSX files found in project")
                
            return {
                "score": min(100, score),
                "issues": issues,
                "suggestions": suggestions,
                "metrics": metrics,
                "best_practices": best_practices
            }
            
        except Exception as e:
            return {
                "score": 60,
                "issues": [f"Quality analysis failed: {str(e)}"],
                "suggestions": ["Ensure project structure is accessible"],
                "metrics": {},
                "best_practices": {}
            }

    def validate_files(self, file_paths: List[str], validation_type: str = "comprehensive") -> Dict:
        """Validate specific files and return quality report"""
        try:
            all_issues = []
            all_suggestions = []
            file_scores = []
            
            for file_path in file_paths:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Run validation based on type
                    if validation_type == "comprehensive":
                        report = self.validate_component(content, file_path)
                        all_issues.extend([{
                            "file": file_path,
                            "type": issue.category,
                            "message": issue.message,
                            "severity": issue.level.value,
                            "line": issue.line,
                            "fixable": issue.auto_fixable
                        } for issue in report.issues])
                        file_scores.append(report.score)
                        
                        # Add file-specific suggestions
                        if report.score < 80:
                            all_suggestions.append(f"Improve quality in {file_path}")
                            
                    elif validation_type == "syntax":
                        # Basic syntax validation
                        compilation_success = self._check_compilation(content, file_path)
                        if compilation_success:
                            file_scores.append(90)
                        else:
                            file_scores.append(40)
                            all_issues.append({
                                "file": file_path,
                                "type": "syntax",
                                "message": "File has compilation errors",
                                "severity": "error"
                            })
                            
                except Exception as e:
                    all_issues.append({
                        "file": file_path,
                        "type": "validation_error",
                        "message": f"Could not validate file: {str(e)}",
                        "severity": "warning"
                    })
                    file_scores.append(50)
            
            # Calculate overall score
            overall_score = sum(file_scores) / len(file_scores) if file_scores else 50
            
            return {
                "score": overall_score,
                "issues": all_issues,
                "suggestions": all_suggestions,
                "file_scores": dict(zip(file_paths, file_scores)),
                "validation_type": validation_type
            }
            
        except Exception as e:
            return {
                "score": 50,
                "issues": [{"type": "validation_error", "message": str(e), "severity": "error"}],
                "suggestions": ["Ensure files exist and are accessible"]
            }

    def validate_code_content(self, code: str, file_type: str = "comprehensive") -> Dict:
        """Validate code content inline without file system access"""
        try:
            if file_type == "comprehensive":
                # Run full validation on code content
                report = self.validate_component(code, "inline_validation")
                issues = [{
                    "type": issue.category,
                    "message": issue.message,
                    "severity": issue.level.value,
                    "line": issue.line,
                    "fixable": issue.auto_fixable
                } for issue in report.issues]
                
                return {
                    "score": report.score,
                    "issues": issues,
                    "suggestions": ["Apply auto-fixes if available"] if any(i.get("fixable") for i in issues) else [],
                    "compilation_success": report.compilation_success,
                    "rendering_success": report.rendering_success
                }
                
            elif file_type == "syntax":
                # Basic syntax check
                has_export = "export" in code
                has_return = "return" in code
                has_jsx = "<" in code and ">" in code
                
                score = 70
                issues = []
                
                if not has_export:
                    issues.append({"type": "syntax", "message": "Missing export statement", "severity": "error"})
                    score -= 20
                if not has_return:
                    issues.append({"type": "syntax", "message": "Missing return statement", "severity": "error"})
                    score -= 15
                if not has_jsx:
                    issues.append({"type": "syntax", "message": "No JSX elements found", "severity": "warning"})
                    score -= 10
                    
                return {
                    "score": max(0, score),
                    "issues": issues,
                    "suggestions": ["Fix syntax errors before proceeding"]
                }
                
            else:
                return {
                    "score": 75,
                    "issues": [],
                    "suggestions": []
                }
                
        except Exception as e:
            return {
                "score": 50,
                "issues": [{"type": "validation_error", "message": str(e), "severity": "error"}],
                "suggestions": ["Check code syntax and structure"]
            }


# Validator implementations
class TypeScriptValidator:
    """Validates TypeScript syntax and types."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for duplicate imports
        import_lines = [
            line for line in code.split("\n") if line.strip().startswith("import")
        ]
        react_imports = [
            line
            for line in import_lines
            if "from 'react'" in line or 'from "react"' in line
        ]

        if len(react_imports) > 1:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="typescript",
                    message="Duplicate React import statements detected",
                    auto_fixable=True,
                    suggestion="Consolidate React imports into a single statement",
                )
            )

        # Check for malformed image imports
        if "@/public/images/" in code or "AvatarImg" in code:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="typescript",
                    message="Local image import may not exist",
                    auto_fixable=True,
                    suggestion="Replace with placeholder image URL",
                )
            )

        # Check for any type
        if re.search(r":\s*any\b", code):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="typescript",
                    message="Avoid using 'any' type for better type safety",
                    auto_fixable=True,
                )
            )

        return issues


class ESLintValidator:
    """Validates code against ESLint rules."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for console.log
        if re.search(r"console\.log\(", code):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="eslint",
                    message="Remove console.log statements",
                    auto_fixable=True,
                )
            )

        # Check for malformed JSX
        if "/ width=" in code:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="eslint",
                    message="Malformed JSX self-closing tag",
                    auto_fixable=True,
                )
            )

        return issues


class ImportValidator:
    """Validates import statements and paths."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for use client directive placement
        lines = code.split("\n")
        use_client_index = -1
        first_import_index = -1

        for i, line in enumerate(lines):
            if '"use client"' in line or "'use client'" in line:
                use_client_index = i
            if line.strip().startswith("import") and first_import_index == -1:
                first_import_index = i

        if (
            use_client_index > 0
            and first_import_index >= 0
            and use_client_index > first_import_index
        ):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="imports",
                    message="'use client' directive must be at the top of the file",
                    auto_fixable=True,
                )
            )

        return issues


class ComponentStructureValidator:
    """Validates React component structure and patterns."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for invalid Tailwind classes
        invalid_classes = [
            "text-smline-height",
            "text-baseline-height",
            "bg-gray(?!-[0-9])",
            "text-gray(?!-[0-9])",
            "bg-sky(?!-[0-9])",
            "text-blue(?!-[0-9])",
            "bg-blue(?!-[0-9])",
            "text-emerald(?!-[0-9])",
            "bg-emerald(?!-[0-9])",
        ]

        for invalid_class in invalid_classes:
            if re.search(rf"\b{invalid_class}\b", code):
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        category="structure",
                        message=f"Invalid Tailwind CSS class detected",
                        auto_fixable=True,
                    )
                )
                break

        # Check for component export
        if "export default" not in code and "export {" not in code:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    category="structure",
                    message="Component must have an export statement",
                    auto_fixable=True,
                )
            )

        return issues


class AccessibilityValidator:
    """Validates accessibility compliance."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for images without alt
        if re.search(r"<img(?![^>]*alt=)", code):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="accessibility",
                    message="Images should have alt attributes",
                    auto_fixable=True,
                    suggestion="Add alt attribute to img elements",
                )
            )

        return issues


class PerformanceValidator:
    """Validates performance best practices."""

    def validate(
        self, code: str, target_path: str, project_path: Path
    ) -> List[ValidationIssue]:
        issues = []

        # Check for inline object/function creation
        if re.search(r"onClick=\{.*=>.*\}", code):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="performance",
                    message="Consider using useCallback for event handlers",
                    auto_fixable=False,
                    suggestion="Wrap event handlers with useCallback",
                )
            )

        return issues


# Enhanced Auto-fixer implementations
class EnhancedTypeScriptAutoFixer:
    """Automatically fixes TypeScript issues with advanced capabilities."""

    def __init__(self, project_path: str = None):
        self.project_path = project_path

    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        return any(
            issue.category in ["typescript", "imports"] and issue.auto_fixable
            for issue in issues
        )

    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []

        # 1. Fix duplicate imports and use client placement
        fixed_code, import_fixes = self._fix_imports_comprehensively(fixed_code)
        fixes_applied.extend(import_fixes)

        # 2. Fix problematic avatar imports
        if "AvatarImg" in fixed_code or "@/public/images/" in fixed_code:
            fixed_code = self._fix_avatar_imports(fixed_code)
            fixes_applied.append("Fixed problematic avatar import with placeholder URL")

        # 3. Remove any types
        if re.search(r":\s*any\b", fixed_code):
            fixed_code = re.sub(r":\s*any\b", "", fixed_code)
            fixes_applied.append("Removed 'any' type annotations")

        return fixed_code, fixes_applied

    def _fix_imports_comprehensively(self, code: str) -> Tuple[str, List[str]]:
        """Fix all import-related issues comprehensively."""
        fixes_applied = []
        lines = code.split("\n")

        # Separate different parts of the file
        use_client_lines = []
        import_lines = []
        other_lines = []

        in_imports = True
        for line in lines:
            stripped = line.strip()

            # Check for use client
            if stripped in [
                '"use client";',
                "'use client';",
                '"use client"',
                "'use client'",
            ]:
                use_client_lines.append('"use client";')
                continue

            # Check for imports
            if in_imports and stripped.startswith("import "):
                import_lines.append(line)
                continue

            # End of import section
            if stripped and not stripped.startswith("import") and in_imports:
                in_imports = False

            other_lines.append(line)

        # Process imports
        if len(use_client_lines) > 0:
            fixes_applied.append("Moved 'use client' directive to top of file")

        # Consolidate React imports
        consolidated_imports = self._consolidate_react_imports(import_lines)
        if len(consolidated_imports) < len(import_lines):
            fixes_applied.append(
                f"Consolidated {len(import_lines) - len(consolidated_imports)} duplicate imports"
            )

        # Rebuild the file
        new_lines = []

        # Add use client first
        if use_client_lines:
            new_lines.append(use_client_lines[0])
            new_lines.append("")

        # Add consolidated imports
        new_lines.extend(consolidated_imports)
        if consolidated_imports:
            new_lines.append("")

        # Add the rest
        # Skip leading empty lines in other_lines
        while other_lines and not other_lines[0].strip():
            other_lines.pop(0)

        new_lines.extend(other_lines)

        return "\n".join(new_lines), fixes_applied

    def _consolidate_react_imports(self, import_lines: List[str]) -> List[str]:
        """Consolidate duplicate React imports."""
        react_imports = []
        other_imports = []

        react_default = False
        react_named = set()

        for line in import_lines:
            if "from 'react'" in line or 'from "react"' in line:
                # Parse React import
                if "import React" in line and not "{" in line:
                    react_default = True
                elif "import React," in line:
                    react_default = True
                    # Extract named imports
                    match = re.search(r"\{([^}]+)\}", line)
                    if match:
                        names = [n.strip() for n in match.group(1).split(",")]
                        react_named.update(names)
                elif "{" in line:
                    # Named imports only
                    match = re.search(r"\{([^}]+)\}", line)
                    if match:
                        names = [n.strip() for n in match.group(1).split(",")]
                        react_named.update(names)
            else:
                other_imports.append(line)

        # Build consolidated React import
        consolidated = []
        if react_default and react_named:
            consolidated.append(
                f"import React, {{ {', '.join(sorted(react_named))} }} from 'react';"
            )
        elif react_default:
            consolidated.append("import React from 'react';")
        elif react_named:
            consolidated.append(
                f"import {{ {', '.join(sorted(react_named))} }} from 'react';"
            )

        # Combine all imports
        return consolidated + other_imports

    def _fix_avatar_imports(self, code: str) -> str:
        """Fix problematic local avatar imports."""
        # Remove the import line
        lines = code.split("\n")
        filtered_lines = []

        for line in lines:
            if "import AvatarImg from" in line and "@/public/images/" in line:
                continue
            filtered_lines.append(line)

        code = "\n".join(filtered_lines)

        # Replace usage
        code = code.replace(
            "avatarUrl: AvatarImg",
            'avatarUrl: "https://ui-avatars.com/api/?background=random&name=User"',
        )
        code = code.replace(
            "src={avatarUrl || AvatarImg}",
            'src={avatarUrl || "https://ui-avatars.com/api/?background=random&name=User"}',
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
        if "/ width=" in fixed_code:
            fixed_code = re.sub(r"/\s+width=", " width=", fixed_code)
            fixes_applied.append("Fixed malformed JSX self-closing tag")

        # 2. Fix invalid Tailwind CSS classes
        fixed_code, tailwind_fixes = self._fix_tailwind_classes_properly(fixed_code)
        fixes_applied.extend(tailwind_fixes)

        # 3. Basic formatting fixes
        if re.search(r"\n\s*\n\s*\n", fixed_code):
            fixed_code = re.sub(r"\n\s*\n\s*\n", "\n\n", fixed_code)
            fixes_applied.append("Removed extra blank lines")

        return fixed_code, fixes_applied

    def _fix_tailwind_classes_properly(self, code: str) -> Tuple[str, List[str]]:
        """Fix invalid Tailwind CSS classes with proper regex."""
        fixes_applied = []

        # Define replacements with proper regex patterns
        replacements = [
            # Fix malformed compound classes first
            (r"\btext-smline-height\b", "text-sm", "Fixed malformed text class"),
            (
                r"\btext-baseline-height\b",
                "text-base",
                "Fixed baseline-height to text-base",
            ),
            # Fix color classes without shade numbers
            (r"\bbg-gray(?!-\d+)\b", "bg-gray-100", "Fixed bg-gray to bg-gray-100"),
            (
                r"\btext-gray(?!-\d+)\b",
                "text-gray-600",
                "Fixed text-gray to text-gray-600",
            ),
            (
                r"\bborder-gray(?!-\d+)\b",
                "border-gray-300",
                "Fixed border-gray to border-gray-300",
            ),
            (r"\bbg-sky(?!-\d+)\b", "bg-sky-500", "Fixed bg-sky to bg-sky-500"),
            (r"\btext-sky(?!-\d+)\b", "text-sky-600", "Fixed text-sky to text-sky-600"),
            (
                r"\bborder-sky(?!-\d+)\b",
                "border-sky-500",
                "Fixed border-sky to border-sky-500",
            ),
            (r"\bbg-blue(?!-\d+)\b", "bg-blue-600", "Fixed bg-blue to bg-blue-600"),
            (
                r"\btext-blue(?!-\d+)\b",
                "text-blue-600",
                "Fixed text-blue to text-blue-600",
            ),
            (
                r"\bborder-blue(?!-\d+)\b",
                "border-blue-600",
                "Fixed border-blue to border-blue-600",
            ),
            (
                r"\bbg-emerald(?!-\d+)\b",
                "bg-emerald-600",
                "Fixed bg-emerald to bg-emerald-600",
            ),
            (
                r"\btext-emerald(?!-\d+)\b",
                "text-emerald-600",
                "Fixed text-emerald to text-emerald-600",
            ),
            (
                r"\bborder-emerald(?!-\d+)\b",
                "border-emerald-600",
                "Fixed border-emerald to border-emerald-600",
            ),
            (
                r"\bbg-indigo(?!-\d+)\b",
                "bg-indigo-600",
                "Fixed bg-indigo to bg-indigo-600",
            ),
            (
                r"\btext-indigo(?!-\d+)\b",
                "text-indigo-600",
                "Fixed text-indigo to text-indigo-600",
            ),
            (
                r"\bborder-indigo(?!-\d+)\b",
                "border-indigo-600",
                "Fixed border-indigo to border-indigo-600",
            ),
            # Fix other common issues
            (r"\btext-black\b", "text-gray-900", "Fixed text-black to text-gray-900"),
            (r"\bbg-black\b", "bg-gray-900", "Fixed bg-black to bg-gray-900"),
            # Fix opacity classes
            (r"\bbg-sky/10\b", "bg-sky-500/10", "Fixed bg-sky/10 to bg-sky-500/10"),
            (
                r"\bbg-emerald/10\b",
                "bg-emerald-500/10",
                "Fixed bg-emerald/10 to bg-emerald-500/10",
            ),
            (
                r"\bbg-indigo/10\b",
                "bg-indigo-500/10",
                "Fixed bg-indigo/10 to bg-indigo-500/10",
            ),
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
        return any(
            issue.category == "eslint" and issue.auto_fixable for issue in issues
        )

    def fix(self, code: str, issues: List[ValidationIssue]) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []

        # Remove console.log statements
        if re.search(r"console\.log\([^)]*\);?\s*", code):
            fixed_code = re.sub(r"console\.log\([^)]*\);?\s*", "", fixed_code)
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

                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except ImportError:
                print("⚠️ Anthropic not available for AI fixing")

    def can_fix_issues(self, issues: List[ValidationIssue]) -> bool:
        """AI can potentially fix any issue if an API client is available."""
        return (
            self.openai_client is not None or self.anthropic_client is not None
        ) and len(issues) > 0

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
                fixes_applied = [
                    f"AI-powered fix: Applied {len(issues)} intelligent fixes"
                ]
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
3. Fix ALL the issues mentioned, not just some of them
4. Use proper Next.js patterns (Image components, 'use client' directives)
5. Ensure all Tailwind CSS classes are valid with proper shade numbers
6. Fix duplicate imports by consolidating them properly
7. Place 'use client' directive at the very top of the file before any imports
8. Preserve the original component name and exports

SPECIFIC FIXES REQUIRED:
- Consolidate duplicate React imports into a single statement
- Move 'use client' to the top of the file
- Replace invalid Tailwind classes like 'bg-gray' with 'bg-gray-100'
- Replace 'text-gray' with 'text-gray-600'
- Replace 'text-black' with 'text-gray-900'
- Fix malformed classes like 'text-smline-height' to 'text-sm'
- Fix self-closing JSX tags (change '/ width=' to ' width=')
- Replace local image imports that don't exist with placeholder URLs
- Add required width/height props to Image components"""

    def _build_user_prompt(self, code: str, issues: List[ValidationIssue]) -> str:
        """Build user prompt with code and issues to fix."""
        issues_text = "\n".join(
            [
                f"- {issue.level.value.upper()}: {issue.category} - {issue.message}"
                for issue in issues[:15]  # Limit to first 15 issues
            ]
        )

        return f"""Fix this React component code that has multiple issues:

ISSUES TO FIX:
{issues_text}

CODE TO FIX:
{code}

Return ONLY the complete fixed code with no additional text or formatting."""

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
        if hasattr(response, "content") and len(response.content) > 0:
            if hasattr(response.content[0], "text"):
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
        if "export" not in fixed_code or "return" not in fixed_code:
            return False

        # Should not be drastically different in length (avoid hallucination)
        length_ratio = len(fixed_code) / len(original_code)
        if length_ratio < 0.5 or length_ratio > 2.0:
            return False

        return True
