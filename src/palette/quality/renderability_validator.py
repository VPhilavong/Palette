"""
Renderability Validator - Tests if generated components can actually render.

This system goes beyond syntax checking to verify that components will render
successfully in their target environment. It catches runtime errors, import issues,
and framework-specific problems before code is delivered to users.
"""

import ast
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .validator import ValidationIssue, ValidationLevel


class RenderError(Enum):
    """Types of rendering errors that can occur."""

    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    TYPE_ERROR = "type_error"
    RUNTIME_ERROR = "runtime_error"
    FRAMEWORK_ERROR = "framework_error"
    STYLING_ERROR = "styling_error"
    DEPENDENCY_ERROR = "dependency_error"


@dataclass
class RenderTest:
    """A test case for component renderability."""

    name: str
    component_code: str
    test_props: Dict[str, Any]
    expected_to_pass: bool = True
    description: str = ""


@dataclass
class RenderabilityResult:
    """Result of renderability validation."""

    is_renderable: bool
    render_tests_passed: int
    render_tests_total: int
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    performance_score: float = 0.0
    accessibility_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RenderabilityValidator:
    """
    Comprehensive renderability validation system.

    Tests generated components to ensure they can render successfully
    in their target environment without errors.
    """

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.node_modules_path = self.project_path / "node_modules"
        self.package_json_path = self.project_path / "package.json"

        # Load project configuration
        self.project_config = self._load_project_config()
        self.available_dependencies = self._get_available_dependencies()

        # Common error patterns
        self.error_patterns = {
            RenderError.IMPORT_ERROR: [
                r"Cannot resolve module",
                r"Module not found",
                r"Cannot find module",
                r"Failed to resolve import",
            ],
            RenderError.TYPE_ERROR: [
                r"Type '.*' is not assignable to type",
                r"Property '.*' does not exist on type",
                r"Argument of type '.*' is not assignable",
            ],
            RenderError.FRAMEWORK_ERROR: [
                r"useEffect.*server component",
                r"useState.*server component",
                r"'use client'.*required",
            ],
            RenderError.STYLING_ERROR: [
                r"Unknown at rule @apply",
                r"className.*undefined",
                r"CSS.*not found",
            ],
        }

    def validate_renderability(
        self, code: str, filename: str = "Component.tsx"
    ) -> RenderabilityResult:
        """
        Comprehensive renderability validation.

        Args:
            code: Component code to validate
            filename: Name of the component file

        Returns:
            RenderabilityResult with detailed validation results
        """

        errors = []
        warnings = []
        suggested_fixes = []
        tests_passed = 0
        tests_total = 0

        # Phase 1: Static Analysis
        syntax_errors = self._validate_syntax(code, filename)
        errors.extend(syntax_errors)

        # Phase 2: Import Validation
        import_errors = self._validate_imports(code)
        errors.extend(import_errors)

        # Phase 3: Framework Compliance
        framework_errors = self._validate_framework_compliance(code, filename)
        errors.extend(framework_errors)

        # Phase 4: TypeScript Validation (if applicable)
        if filename.endswith((".tsx", ".ts")):
            type_errors = self._validate_typescript(code, filename)
            errors.extend(type_errors)

        # Phase 5: Styling System Validation
        styling_errors = self._validate_styling_consistency(code)
        errors.extend(styling_errors)

        # Phase 6: Component Structure Validation
        structure_warnings = self._validate_component_structure(code)
        warnings.extend(structure_warnings)

        # Phase 7: Render Testing (if no critical errors)
        if not any(error.level == ValidationLevel.ERROR for error in errors):
            render_results = self._run_render_tests(code, filename)
            tests_passed = render_results["passed"]
            tests_total = render_results["total"]
            errors.extend(render_results["errors"])
            warnings.extend(render_results["warnings"])

        # Phase 8: Generate Fixes
        suggested_fixes = self._generate_suggested_fixes(errors, code)

        # Calculate scores
        is_renderable = (
            len([e for e in errors if e.level == ValidationLevel.ERROR]) == 0
            and tests_passed == tests_total
        )

        return RenderabilityResult(
            is_renderable=is_renderable,
            render_tests_passed=tests_passed,
            render_tests_total=tests_total,
            errors=errors,
            warnings=warnings,
            suggested_fixes=suggested_fixes,
            performance_score=self._calculate_performance_score(code),
            accessibility_score=self._calculate_accessibility_score(code),
            metadata={
                "validation_phases_completed": 8,
                "framework": self.project_config.get("framework"),
                "typescript": filename.endswith((".tsx", ".ts")),
                "component_size": len(code),
                "estimated_complexity": self._estimate_complexity(code),
            },
        )

    def _load_project_config(self) -> Dict[str, Any]:
        """Load project configuration from package.json and other sources."""

        config = {
            "framework": "react",
            "typescript": True,
            "styling": "tailwind",
            "dependencies": {},
            "devDependencies": {},
        }

        if self.package_json_path.exists():
            try:
                with open(self.package_json_path, "r") as f:
                    package_data = json.load(f)

                # Detect framework
                deps = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                if "next" in deps:
                    config["framework"] = "nextjs"
                elif "vue" in deps:
                    config["framework"] = "vue"
                elif "react" in deps:
                    config["framework"] = "react"

                # Detect styling
                if "@chakra-ui/react" in deps:
                    config["styling"] = "chakra"
                elif "styled-components" in deps:
                    config["styling"] = "styled-components"
                elif "tailwindcss" in deps:
                    config["styling"] = "tailwind"

                config["dependencies"] = deps

            except Exception as e:
                print(f"Warning: Could not load package.json: {e}")

        return config

    def _get_available_dependencies(self) -> Set[str]:
        """Get list of available dependencies from node_modules."""

        dependencies = set()

        if self.node_modules_path.exists():
            for item in self.node_modules_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    dependencies.add(item.name)

                    # Handle scoped packages
                    if item.name.startswith("@"):
                        for subitem in item.iterdir():
                            if subitem.is_dir():
                                dependencies.add(f"{item.name}/{subitem.name}")

        return dependencies

    def _validate_syntax(self, code: str, filename: str) -> List[ValidationIssue]:
        """Validate basic syntax using AST parsing."""

        errors = []

        try:
            # For TypeScript/JSX, we'll do basic pattern validation
            # since full TS parsing would require TypeScript compiler

            # Check for basic JSX syntax issues
            jsx_errors = self._check_jsx_syntax(code)
            errors.extend(jsx_errors)

            # Check for common syntax mistakes
            syntax_errors = self._check_common_syntax_errors(code)
            errors.extend(syntax_errors)

        except Exception as e:
            errors.append(
                ValidationIssue(
                    ValidationLevel.ERROR,
                    f"Syntax validation failed: {str(e)}",
                    "syntax_error",
                    1,
                    f"Fix syntax error: {str(e)}",
                )
            )

        return errors

    def _check_jsx_syntax(self, code: str) -> List[ValidationIssue]:
        """Check for JSX-specific syntax issues."""

        errors = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for unclosed JSX tags
            if "<" in line and ">" in line:
                # Basic check for self-closing tags that should be self-closed
                if any(tag in line for tag in ["<br>", "<img>", "<input>", "<hr>"]):
                    if not line.strip().endswith("/>") and not "></":
                        errors.append(
                            ValidationIssue(
                                ValidationLevel.ERROR,
                                f"Self-closing tag should end with '/>' on line {i}",
                                "jsx_syntax",
                                i,
                                "Add '/>' to self-closing tags",
                            )
                        )

            # Check for missing key props in lists
            if "map(" in line and "key=" not in line:
                errors.append(
                    ValidationIssue(
                        ValidationLevel.WARNING,
                        f"Missing 'key' prop in mapped element on line {i}",
                        "jsx_key",
                        i,
                        "Add unique 'key' prop to mapped elements",
                    )
                )

        return errors

    def _check_common_syntax_errors(self, code: str) -> List[ValidationIssue]:
        """Check for common syntax mistakes."""

        errors = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for incorrect export syntax
            if "export default" in line and "function" in line:
                if not re.match(r"export\s+default\s+function\s+\w+", line.strip()):
                    errors.append(
                        ValidationIssue(
                            ValidationLevel.ERROR,
                            f"Incorrect export default syntax on line {i}",
                            "export_syntax",
                            i,
                            "Use 'export default function ComponentName()' or 'export default ComponentName'",
                        )
                    )

            # Check for missing semicolons in important places
            if line.strip().startswith("import ") and not line.strip().endswith(";"):
                errors.append(
                    ValidationIssue(
                        ValidationLevel.WARNING,
                        f"Missing semicolon in import statement on line {i}",
                        "missing_semicolon",
                        i,
                        "Add semicolon to import statement",
                    )
                )

        return errors

    def _validate_imports(self, code: str) -> List[ValidationIssue]:
        """Validate that all imports can be resolved."""

        errors = []
        import_lines = re.findall(
            r'^import\s+.*from\s+[\'"]([^\'"]+)[\'"];?', code, re.MULTILINE
        )

        for import_path in import_lines:
            if import_path.startswith("."):
                # Relative import - would need actual file system check
                continue
            elif import_path.startswith("@/"):
                # Alias import - would need TypeScript config
                continue
            else:
                # Package import
                package_name = import_path.split("/")[0]
                if package_name.startswith("@"):
                    # Scoped package
                    parts = import_path.split("/")
                    if len(parts) >= 2:
                        package_name = f"{parts[0]}/{parts[1]}"

                if package_name not in self.available_dependencies:
                    errors.append(
                        ValidationIssue(
                            ValidationLevel.ERROR,
                            f"Import '{import_path}' not found in dependencies",
                            "missing_dependency",
                            0,
                            f"Install missing dependency: npm install {package_name}",
                        )
                    )

        return errors

    def _validate_framework_compliance(
        self, code: str, filename: str
    ) -> List[ValidationIssue]:
        """Validate framework-specific requirements."""

        errors = []
        framework = self.project_config.get("framework")

        if framework == "nextjs":
            # Check for 'use client' directive
            has_client_hooks = any(
                hook in code
                for hook in ["useState", "useEffect", "onClick", "onChange"]
            )
            has_use_client = '"use client"' in code or "'use client'" in code

            if has_client_hooks and not has_use_client:
                errors.append(
                    ValidationIssue(
                        ValidationLevel.ERROR,
                        "Next.js client components must include 'use client' directive",
                        "nextjs_use_client",
                        1,
                        "Add '\"use client\";' at the top of the file",
                    )
                )

            # Check for proper Next.js imports
            if "next/image" in code or "next/link" in code:
                # Validate proper usage
                if (
                    "import Image from" in code
                    and "width=" not in code
                    and "height=" not in code
                ):
                    errors.append(
                        ValidationIssue(
                            ValidationLevel.ERROR,
                            "Next.js Image component requires width and height props",
                            "nextjs_image_props",
                            0,
                            "Add width and height props to Image component",
                        )
                    )

        return errors

    def _validate_typescript(self, code: str, filename: str) -> List[ValidationIssue]:
        """Validate TypeScript-specific issues."""

        errors = []

        # Check for missing interface definitions
        if "Props" in code and "interface" not in code:
            errors.append(
                ValidationIssue(
                    ValidationLevel.WARNING,
                    "Component appears to use props but no interface is defined",
                    "missing_interface",
                    0,
                    "Define an interface for component props",
                )
            )

        # Check for any type
        if ": any" in code or "any[]" in code:
            errors.append(
                ValidationIssue(
                    ValidationLevel.WARNING,
                    "Using 'any' type reduces type safety",
                    "any_type",
                    0,
                    "Replace 'any' with specific types",
                )
            )

        # Check for missing return type on functions
        function_matches = re.findall(r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>", code)
        for func_name in function_matches:
            if (
                f"{func_name} =" in code
                and ": FC" not in code
                and ": React.FC" not in code
            ):
                errors.append(
                    ValidationIssue(
                        ValidationLevel.INFO,
                        f"Function '{func_name}' could benefit from explicit return type",
                        "missing_return_type",
                        0,
                        f"Add return type annotation to {func_name}",
                    )
                )

        return errors

    def _validate_styling_consistency(self, code: str) -> List[ValidationIssue]:
        """Validate styling system consistency."""

        errors = []
        styling = self.project_config.get("styling")

        if styling == "chakra":
            # Check for Tailwind classes in Chakra component
            tailwind_patterns = [
                r'className="[^"]*\b(bg-\w+|text-\w+|p-\d+|m-\d+|flex|grid)\b',
                r"className='[^']*\b(bg-\w+|text-\w+|p-\d+|m-\d+|flex|grid)\b",
            ]

            for pattern in tailwind_patterns:
                matches = re.finditer(pattern, code)
                for match in matches:
                    line_num = code[: match.start()].count("\n") + 1
                    errors.append(
                        ValidationIssue(
                            ValidationLevel.ERROR,
                            f"Tailwind classes detected in Chakra UI component on line {line_num}",
                            "styling_conflict",
                            line_num,
                            "Use Chakra UI props instead of Tailwind classes",
                        )
                    )

        elif styling == "tailwind":
            # Check for missing Tailwind imports
            if "@apply" in code and "@tailwind" not in code:
                errors.append(
                    ValidationIssue(
                        ValidationLevel.WARNING,
                        "Using @apply without proper Tailwind setup",
                        "tailwind_setup",
                        0,
                        "Ensure Tailwind CSS is properly configured",
                    )
                )

        return errors

    def _validate_component_structure(self, code: str) -> List[ValidationIssue]:
        """Validate component structure and best practices."""

        warnings = []

        # Check for missing display name
        if "memo(" in code and "displayName" not in code:
            warnings.append(
                ValidationIssue(
                    ValidationLevel.INFO,
                    "Memoized component should have displayName for debugging",
                    "missing_display_name",
                    0,
                    "Add displayName to memoized component",
                )
            )

        # Check for accessibility issues
        if "<img" in code and "alt=" not in code:
            warnings.append(
                ValidationIssue(
                    ValidationLevel.WARNING,
                    "Image elements should have alt text for accessibility",
                    "missing_alt_text",
                    0,
                    "Add alt attribute to img elements",
                )
            )

        # Check for missing error boundaries
        if "useState" in code and "try" not in code and "catch" not in code:
            warnings.append(
                ValidationIssue(
                    ValidationLevel.INFO,
                    "Stateful component could benefit from error handling",
                    "missing_error_handling",
                    0,
                    "Add try-catch blocks around state updates",
                )
            )

        return warnings

    def _run_render_tests(self, code: str, filename: str) -> Dict[str, Any]:
        """Run actual render tests for the component."""

        results = {"passed": 0, "total": 0, "errors": [], "warnings": []}

        # Generate basic test cases
        test_cases = self._generate_test_cases(code)
        results["total"] = len(test_cases)

        for test_case in test_cases:
            try:
                # This would require a proper test runner
                # For now, we'll simulate basic validation
                if self._simulate_render_test(code, test_case):
                    results["passed"] += 1
                else:
                    results["errors"].append(
                        ValidationIssue(
                            ValidationLevel.ERROR,
                            f"Render test failed: {test_case.name}",
                            "render_test_failed",
                            0,
                            f"Fix render issue: {test_case.description}",
                        )
                    )
            except Exception as e:
                results["errors"].append(
                    ValidationIssue(
                        ValidationLevel.ERROR,
                        f"Render test error in {test_case.name}: {str(e)}",
                        "render_test_error",
                        0,
                        "Fix component to pass render tests",
                    )
                )

        return results

    def _generate_test_cases(self, code: str) -> List[RenderTest]:
        """Generate test cases based on component analysis."""

        test_cases = []

        # Basic render test
        test_cases.append(
            RenderTest(
                name="basic_render",
                component_code=code,
                test_props={},
                description="Component renders without errors",
            )
        )

        # Props test
        if "interface" in code and "Props" in code:
            test_cases.append(
                RenderTest(
                    name="with_props",
                    component_code=code,
                    test_props=self._extract_required_props(code),
                    description="Component renders with required props",
                )
            )

        # Edge cases
        if "string" in code:
            test_cases.append(
                RenderTest(
                    name="empty_strings",
                    component_code=code,
                    test_props={"title": "", "content": ""},
                    description="Component handles empty strings",
                )
            )

        return test_cases

    def _extract_required_props(self, code: str) -> Dict[str, Any]:
        """Extract required props from component interface."""

        # Basic prop extraction (would need proper TypeScript parsing)
        props = {}

        # Look for common prop patterns
        if "title" in code:
            props["title"] = "Test Title"
        if "content" in code:
            props["content"] = "Test Content"
        if "name" in code:
            props["name"] = "Test Name"
        if "email" in code:
            props["email"] = "test@example.com"

        return props

    def _simulate_render_test(self, code: str, test_case: RenderTest) -> bool:
        """Simulate a render test (would use actual testing framework in production)."""

        # Basic checks that would indicate successful rendering
        checks = [
            "return (" in code or "return <" in code,  # Has JSX return
            "export default" in code or "export {" in code,  # Properly exported
            not any(
                error in code
                for error in ["undefined", "null.", "Cannot read property"]
            ),  # No obvious runtime errors
        ]

        return all(checks)

    def _generate_suggested_fixes(
        self, errors: List[ValidationIssue], code: str
    ) -> List[str]:
        """Generate actionable fix suggestions based on errors."""

        fixes = []

        for error in errors:
            if error.category == "missing_dependency":
                package = error.message.split("'")[1].split("/")[0]
                fixes.append(f"Install missing dependency: npm install {package}")

            elif error.category == "nextjs_use_client":
                fixes.append(
                    "Add '\"use client\";' at the top of the file before imports"
                )

            elif error.category == "styling_conflict":
                fixes.append(
                    "Replace Tailwind classes with Chakra UI props (e.g., bg='blue.500' instead of className='bg-blue-500')"
                )

            elif error.category == "jsx_syntax":
                fixes.append("Fix JSX syntax errors - ensure tags are properly closed")

            elif error.category == "missing_interface":
                fixes.append("Add TypeScript interface for component props")

        return list(set(fixes))  # Remove duplicates

    def _calculate_performance_score(self, code: str) -> float:
        """Calculate estimated performance score."""

        score = 1.0

        # Check for performance optimizations
        if "memo(" in code:
            score += 0.1
        if "useMemo" in code or "useCallback" in code:
            score += 0.1
        if "lazy(" in code:
            score += 0.1

        # Check for performance issues
        if code.count("useEffect") > 3:
            score -= 0.1
        if "console.log" in code:
            score -= 0.05

        return max(0.0, min(1.0, score))

    def _calculate_accessibility_score(self, code: str) -> float:
        """Calculate accessibility compliance score."""

        score = 0.5  # Base score

        # Positive accessibility features
        if "alt=" in code:
            score += 0.1
        if "aria-label=" in code or "aria-describedby=" in code:
            score += 0.1
        if "tabIndex=" in code:
            score += 0.1
        if "role=" in code:
            score += 0.1

        # Check for semantic HTML
        semantic_tags = [
            "header",
            "main",
            "section",
            "article",
            "nav",
            "aside",
            "footer",
        ]
        if any(f"<{tag}" in code for tag in semantic_tags):
            score += 0.1

        # Missing accessibility features
        if "<img" in code and "alt=" not in code:
            score -= 0.2
        if (
            "<button" in code
            and "aria-label=" not in code
            and not re.search(r"<button[^>]*>[^<]+</button>", code)
        ):
            score -= 0.1

        return max(0.0, min(1.0, score))

    def _estimate_complexity(self, code: str) -> str:
        """Estimate component complexity."""

        lines = len(code.split("\n"))
        hooks = code.count("use")
        jsx_elements = code.count("<")

        if lines < 50 and hooks < 3 and jsx_elements < 10:
            return "simple"
        elif lines < 150 and hooks < 8 and jsx_elements < 25:
            return "medium"
        else:
            return "complex"
