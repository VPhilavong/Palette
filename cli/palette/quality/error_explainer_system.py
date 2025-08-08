"""
Error Explainer System - Provides clear, actionable debugging information.

This system takes validation errors and transforms them into user-friendly explanations
with step-by-step fix instructions, code examples, and context-aware guidance.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .renderability_validator import RenderabilityResult, RenderError
from .validator import ValidationIssue, ValidationLevel


class ExplanationLevel(Enum):
    """Levels of explanation detail."""

    BRIEF = "brief"  # One-line summary
    DETAILED = "detailed"  # Full explanation with context
    TUTORIAL = "tutorial"  # Step-by-step guide with examples


@dataclass
class ErrorExplanation:
    """Detailed explanation of a validation error."""

    title: str
    description: str
    cause: str
    fix_steps: List[str]
    code_examples: Dict[str, str] = field(default_factory=dict)  # "before" -> "after"
    related_docs: List[str] = field(default_factory=list)
    severity_impact: str = ""
    estimated_fix_time: str = ""


@dataclass
class ExplanationReport:
    """Complete error explanation report."""

    summary: str
    total_errors: int
    critical_errors: int
    explanations: List[ErrorExplanation] = field(default_factory=list)
    quick_fixes: List[str] = field(default_factory=list)
    learning_resources: List[str] = field(default_factory=list)


class ErrorExplainerSystem:
    """
    Intelligent error explanation system for component validation.

    Provides context-aware, actionable debugging information that helps users
    understand and fix component rendering issues quickly.
    """

    def __init__(self, project_framework: str = "react"):
        self.project_framework = project_framework

        # Error explanation templates
        self.error_explanations = {
            # Import/Dependency Errors
            "missing_dependency": {
                "title": "Missing Package Dependency",
                "description": "A required package is not installed in your project.",
                "cause": "The component uses a library that isn't available in your node_modules.",
                "fix_steps": [
                    "Install the missing package using npm or yarn",
                    "Restart your development server",
                    "Verify the import path is correct",
                ],
                "code_examples": {
                    "install": "npm install {package_name}",
                    "import": "import {{ Component }} from '{package_name}';",
                },
                "severity_impact": "CRITICAL - Component will not render without this dependency",
                "estimated_fix_time": "1-2 minutes",
            },
            # Next.js Specific Errors
            "nextjs_use_client": {
                "title": "Missing 'use client' Directive",
                "description": "Next.js client components must declare 'use client' at the top.",
                "cause": "Component uses client-side features (hooks, event handlers) but lacks the directive.",
                "fix_steps": [
                    "Add '\"use client\";' at the very top of your file",
                    "Place it before any imports",
                    "Ensure there's a blank line after the directive",
                ],
                "code_examples": {
                    "before": "import React from 'react';\\n\\nconst Component = () => {",
                    "after": "\"use client\";\\n\\nimport React from 'react';\\n\\nconst Component = () => {",
                },
                "severity_impact": "CRITICAL - Component will crash in Next.js production",
                "estimated_fix_time": "30 seconds",
            },
            "nextjs_image_props": {
                "title": "Next.js Image Missing Required Props",
                "description": "Next.js Image components require width and height props for optimization.",
                "cause": "Image component is missing required width/height for Next.js's image optimization.",
                "fix_steps": [
                    "Add width prop with pixel value",
                    "Add height prop with pixel value",
                    "Consider using fill prop for responsive images",
                    "Add sizes prop for responsive images",
                ],
                "code_examples": {
                    "before": "<Image src='/photo.jpg' alt='Photo' />",
                    "after": "<Image src='/photo.jpg' alt='Photo' width={400} height={300} />",
                },
                "severity_impact": "ERROR - Image will not display properly",
                "estimated_fix_time": "1 minute",
            },
            # Styling System Conflicts
            "styling_conflict": {
                "title": "Styling System Conflict",
                "description": "Mixing different styling approaches can cause conflicts and unexpected behavior.",
                "cause": "Component uses CSS classes from multiple styling systems (e.g., Tailwind + Chakra UI).",
                "fix_steps": [
                    "Choose one consistent styling approach",
                    "Replace conflicting classes with the chosen system",
                    "Update component props accordingly",
                    "Remove unused styling imports",
                ],
                "code_examples": {
                    "tailwind_to_chakra": "className='bg-blue-500' → bg='blue.500'",
                    "chakra_to_tailwind": "bg='blue.500' → className='bg-blue-500'",
                },
                "severity_impact": "ERROR - Styling may not work as expected",
                "estimated_fix_time": "3-5 minutes",
            },
            # TypeScript Errors
            "missing_interface": {
                "title": "Missing TypeScript Interface",
                "description": "Component props should have proper TypeScript interfaces for type safety.",
                "cause": "Component accepts props but doesn't define their types.",
                "fix_steps": [
                    "Define an interface for your component props",
                    "Include all expected prop types",
                    "Mark optional props with '?'",
                    "Apply interface to component function",
                ],
                "code_examples": {
                    "before": "const Button = (props) => {",
                    "after": "interface ButtonProps {\\n  title: string;\\n  onClick?: () => void;\\n}\\n\\nconst Button: React.FC<ButtonProps> = (props) => {",
                },
                "severity_impact": "WARNING - Reduces type safety and IDE support",
                "estimated_fix_time": "2-3 minutes",
            },
            # JSX/Syntax Errors
            "jsx_syntax": {
                "title": "JSX Syntax Error",
                "description": "JSX has specific syntax rules that must be followed.",
                "cause": "Invalid JSX syntax such as unclosed tags or incorrect self-closing elements.",
                "fix_steps": [
                    "Ensure all JSX tags are properly closed",
                    "Use '/>' for self-closing elements",
                    "Check for matching opening and closing tags",
                    "Validate JSX attribute syntax",
                ],
                "code_examples": {
                    "before": "<img src='photo.jpg'>",
                    "after": "<img src='photo.jpg' />",
                },
                "severity_impact": "CRITICAL - Component will not compile",
                "estimated_fix_time": "1-2 minutes",
            },
            "jsx_key": {
                "title": "Missing Key Props in Lists",
                "description": "React requires unique 'key' props when rendering lists of elements.",
                "cause": "Elements created in .map() or similar loops don't have unique key props.",
                "fix_steps": [
                    "Add a unique 'key' prop to each mapped element",
                    "Use stable, unique identifiers (not array index if possible)",
                    "Ensure keys are unique within the list",
                    "Keys should remain consistent between renders",
                ],
                "code_examples": {
                    "before": "items.map(item => <div>{item.name}</div>)",
                    "after": "items.map(item => <div key={item.id}>{item.name}</div>)",
                },
                "severity_impact": "WARNING - Can cause performance issues and bugs",
                "estimated_fix_time": "1 minute",
            },
        }

        # Framework-specific documentation links
        self.doc_links = {
            "nextjs": [
                "https://nextjs.org/docs/app/building-your-application/rendering/client-components",
                "https://nextjs.org/docs/app/api-reference/components/image",
            ],
            "react": [
                "https://react.dev/reference/react",
                "https://react.dev/learn/describing-the-ui",
            ],
            "chakra": [
                "https://chakra-ui.com/getting-started",
                "https://chakra-ui.com/docs/components",
            ],
            "tailwind": [
                "https://tailwindcss.com/docs",
                "https://tailwindcss.com/docs/utility-first",
            ],
        }

    def explain_errors(
        self,
        errors: List[ValidationIssue],
        renderability_result: Optional[RenderabilityResult] = None,
        level: ExplanationLevel = ExplanationLevel.DETAILED,
    ) -> ExplanationReport:
        """
        Generate comprehensive error explanations.

        Args:
            errors: List of validation errors to explain
            renderability_result: Optional renderability validation result
            level: Level of detail for explanations

        Returns:
            ExplanationReport with detailed error analysis
        """

        explanations = []
        quick_fixes = []

        # Group errors by category for better organization
        error_groups = self._group_errors_by_category(errors)

        # Generate explanations for each error category
        for category, category_errors in error_groups.items():
            if category in self.error_explanations:
                explanation = self._create_explanation(category, category_errors, level)
                explanations.append(explanation)

                # Add quick fixes for critical errors
                if any(
                    error.level == ValidationLevel.ERROR for error in category_errors
                ):
                    quick_fixes.extend(explanation.fix_steps[:2])  # Top 2 steps

        # Add renderability-specific explanations
        if renderability_result and not renderability_result.is_renderable:
            render_explanation = self._create_renderability_explanation(
                renderability_result, level
            )
            explanations.append(render_explanation)

        # Generate summary
        critical_count = len([e for e in errors if e.level == ValidationLevel.ERROR])
        summary = self._generate_summary(len(errors), critical_count, explanations)

        # Add learning resources
        learning_resources = self._get_learning_resources(error_groups.keys())

        return ExplanationReport(
            summary=summary,
            total_errors=len(errors),
            critical_errors=critical_count,
            explanations=explanations,
            quick_fixes=list(set(quick_fixes)),  # Remove duplicates
            learning_resources=learning_resources,
        )

    def _group_errors_by_category(
        self, errors: List[ValidationIssue]
    ) -> Dict[str, List[ValidationIssue]]:
        """Group errors by their category for organized explanations."""

        groups = {}
        for error in errors:
            category = error.category
            if category not in groups:
                groups[category] = []
            groups[category].append(error)

        return groups

    def _create_explanation(
        self, category: str, errors: List[ValidationIssue], level: ExplanationLevel
    ) -> ErrorExplanation:
        """Create detailed explanation for a specific error category."""

        template = self.error_explanations[category]

        # Customize explanation based on specific errors
        description = template["description"]
        fix_steps = template["fix_steps"].copy()
        code_examples = template["code_examples"].copy()

        # Add specific context from errors
        if errors:
            first_error = errors[0]
            if "missing_dependency" in category and "Import" in first_error.message:
                # Extract package name from error message
                package_match = re.search(r"Import '([^']+)'", first_error.message)
                if package_match:
                    package_name = package_match.group(1).split("/")[0]
                    code_examples["install"] = f"npm install {package_name}"
                    fix_steps[0] = (
                        f"Install the missing package: npm install {package_name}"
                    )

        # Adjust detail level
        if level == ExplanationLevel.BRIEF:
            fix_steps = fix_steps[:2]  # Only first 2 steps
            code_examples = {}
        elif level == ExplanationLevel.TUTORIAL:
            # Add more detailed steps
            fix_steps.append("Test the fix by running your development server")
            fix_steps.append("Verify the component renders without errors")

        # Add related documentation
        related_docs = []
        if "nextjs" in category:
            related_docs.extend(self.doc_links.get("nextjs", []))
        if "styling" in category:
            related_docs.extend(self.doc_links.get("chakra", []))
            related_docs.extend(self.doc_links.get("tailwind", []))

        return ErrorExplanation(
            title=template["title"],
            description=description,
            cause=template["cause"],
            fix_steps=fix_steps,
            code_examples=code_examples,
            related_docs=related_docs,
            severity_impact=template["severity_impact"],
            estimated_fix_time=template["estimated_fix_time"],
        )

    def _create_renderability_explanation(
        self, result: RenderabilityResult, level: ExplanationLevel
    ) -> ErrorExplanation:
        """Create explanation for renderability failures."""

        failed_tests = result.render_tests_total - result.render_tests_passed

        return ErrorExplanation(
            title="Component Renderability Issues",
            description=f"Component failed {failed_tests} out of {result.render_tests_total} render tests.",
            cause="Component has structural or logical issues preventing successful rendering.",
            fix_steps=[
                "Review the specific error messages above",
                "Fix critical and error-level issues first",
                "Test component rendering in isolation",
                "Verify all required props are provided",
                "Check for undefined variables or missing imports",
            ],
            code_examples={
                "test_component": "// Test your component:\\nimport Component from './Component';\\n\\n<Component {...requiredProps} />"
            },
            severity_impact="CRITICAL - Component will not work for users",
            estimated_fix_time="5-15 minutes depending on issues",
        )

    def _generate_summary(
        self,
        total_errors: int,
        critical_errors: int,
        explanations: List[ErrorExplanation],
    ) -> str:
        """Generate a concise summary of the error situation."""

        if total_errors == 0:
            return "✅ All validation checks passed! Component is ready to use."

        if critical_errors > 0:
            return f"🚨 Found {critical_errors} critical errors that prevent rendering. Fix these first!"

        if total_errors <= 3:
            return f"⚠️ Found {total_errors} minor issues. Component should render but may have problems."

        return f"⚠️ Found {total_errors} issues across multiple categories. Review each explanation below."

    def _get_learning_resources(self, error_categories: List[str]) -> List[str]:
        """Get relevant learning resources based on error types."""

        resources = []

        # Add framework-specific resources
        if any("nextjs" in cat for cat in error_categories):
            resources.extend(self.doc_links.get("nextjs", []))

        if any("styling" in cat for cat in error_categories):
            resources.extend(self.doc_links.get("chakra", []))
            resources.extend(self.doc_links.get("tailwind", []))

        # Add React resources for JSX issues
        if any("jsx" in cat for cat in error_categories):
            resources.extend(self.doc_links.get("react", []))

        # Add general React resources
        if not resources:
            resources.extend(self.doc_links.get("react", []))

        return list(set(resources))  # Remove duplicates

    def format_explanation_for_cli(self, report: ExplanationReport) -> str:
        """Format explanation report for command-line display."""

        output = []

        # Header
        output.append("=" * 70)
        output.append("🔍 ERROR EXPLANATION REPORT")
        output.append("=" * 70)
        output.append("")

        # Summary
        output.append(f"📋 SUMMARY: {report.summary}")
        output.append(f"   Total Issues: {report.total_errors}")
        output.append(f"   Critical: {report.critical_errors}")
        output.append("")

        # Quick fixes
        if report.quick_fixes:
            output.append("⚡ QUICK FIXES:")
            for i, fix in enumerate(report.quick_fixes, 1):
                output.append(f"   {i}. {fix}")
            output.append("")

        # Detailed explanations
        for i, explanation in enumerate(report.explanations, 1):
            output.append(f"📝 ERROR {i}: {explanation.title}")
            output.append(f"   {explanation.severity_impact}")
            output.append(f"   Estimated fix time: {explanation.estimated_fix_time}")
            output.append("")
            output.append(f"   💡 CAUSE: {explanation.cause}")
            output.append("")
            output.append("   🔧 FIX STEPS:")
            for j, step in enumerate(explanation.fix_steps, 1):
                output.append(f"      {j}. {step}")
            output.append("")

            # Code examples
            if explanation.code_examples:
                output.append("   📄 CODE EXAMPLES:")
                for label, code in explanation.code_examples.items():
                    output.append(f"      {label.upper()}:")
                    for line in code.split("\\n"):
                        output.append(f"        {line}")
                output.append("")

            output.append("-" * 50)
            output.append("")

        # Learning resources
        if report.learning_resources:
            output.append("📚 LEARNING RESOURCES:")
            for resource in report.learning_resources:
                output.append(f"   • {resource}")

        return "\\n".join(output)
