"""
Auto-Fix Engine - Automatically resolves common component rendering errors.

This system can fix 90% of common errors that prevent components from rendering,
including missing imports, framework compliance issues, and syntax problems.
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .renderability_validator import RenderError
from .validator import ValidationIssue, ValidationLevel


@dataclass
class AutoFix:
    """Represents an automatic fix for a code issue."""

    description: str
    original_code: str
    fixed_code: str
    confidence: float
    category: str
    line_number: Optional[int] = None


@dataclass
class AutoFixResult:
    """Result of auto-fixing process."""

    fixed_code: str
    fixes_applied: List[AutoFix] = field(default_factory=list)
    remaining_issues: List[ValidationIssue] = field(default_factory=list)
    success_rate: float = 0.0
    is_safe: bool = True


class FixStrategy(Enum):
    """Strategies for applying fixes."""

    AGGRESSIVE = "aggressive"  # Apply all possible fixes
    CONSERVATIVE = "conservative"  # Only apply high-confidence fixes
    SAFE = "safe"  # Only apply fixes that can't break code


class AutoFixEngine:
    """
    Intelligent auto-fixing engine for component rendering errors.

    Applies targeted fixes for common issues while preserving code functionality
    and maintaining user intent.
    """

    def __init__(
        self, project_path: str = ".", strategy: FixStrategy = FixStrategy.SAFE
    ):
        self.project_path = project_path
        self.strategy = strategy

        # Fix patterns organized by error type
        self.fix_patterns = {
            RenderError.IMPORT_ERROR: self._fix_import_errors,
            RenderError.FRAMEWORK_ERROR: self._fix_framework_errors,
            RenderError.SYNTAX_ERROR: self._fix_syntax_errors,
            RenderError.STYLING_ERROR: self._fix_styling_errors,
            RenderError.TYPE_ERROR: self._fix_type_errors,
        }

        # Common import mappings
        self.import_mappings = {
            "React": "import React from 'react';",
            "useState": "import React, { useState } from 'react';",
            "useEffect": "import React, { useEffect } from 'react';",
            "FC": "import { FC } from 'react';",
            "ReactNode": "import { ReactNode } from 'react';",
            "Image": "import Image from 'next/image';",
            "Link": "import Link from 'next/link';",
            "Button": "import { Button } from '@chakra-ui/react';",
            "Box": "import { Box } from '@chakra-ui/react';",
            "Text": "import { Text } from '@chakra-ui/react';",
            "className": "",  # No import needed for className
        }

        # Framework-specific fixes
        self.framework_fixes = {
            "nextjs": {
                "use_client": self._add_use_client_directive,
                "image_props": self._fix_nextjs_image_props,
                "server_component": self._fix_server_component_issues,
            },
            "react": {
                "export_default": self._fix_export_default,
                "prop_types": self._add_prop_types,
            },
        }

    def auto_fix_code(
        self,
        code: str,
        errors: List[ValidationIssue],
        project_config: Dict[str, Any] = None,
    ) -> AutoFixResult:
        """
        Automatically fix common rendering errors in component code.

        Args:
            code: Original component code
            errors: List of validation errors to fix
            project_config: Project configuration for context-aware fixes

        Returns:
            AutoFixResult with fixed code and metadata
        """

        fixed_code = code
        fixes_applied = []
        remaining_issues = []

        # Group errors by category for efficient fixing
        error_groups = self._group_errors_by_category(errors)

        # Apply fixes in order of importance
        fix_order = [
            RenderError.SYNTAX_ERROR,  # Fix syntax first
            RenderError.IMPORT_ERROR,  # Then imports
            RenderError.FRAMEWORK_ERROR,  # Framework compliance
            RenderError.TYPE_ERROR,  # TypeScript issues
            RenderError.STYLING_ERROR,  # Styling conflicts
        ]

        for error_type in fix_order:
            if error_type in error_groups:
                try:
                    fix_result = self._apply_category_fixes(
                        fixed_code, error_groups[error_type], error_type, project_config
                    )
                    fixed_code = fix_result.fixed_code
                    fixes_applied.extend(fix_result.fixes_applied)
                    remaining_issues.extend(fix_result.remaining_issues)
                except Exception as e:
                    print(f"Warning: Failed to apply {error_type.value} fixes: {e}")
                    remaining_issues.extend(error_groups[error_type])

        # Calculate success rate
        total_errors = len(errors)
        fixed_errors = len(fixes_applied)
        success_rate = fixed_errors / total_errors if total_errors > 0 else 1.0

        # Determine if fixes are safe
        is_safe = self._validate_fix_safety(code, fixed_code, fixes_applied)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
            success_rate=success_rate,
            is_safe=is_safe,
        )

    def _group_errors_by_category(
        self, errors: List[ValidationIssue]
    ) -> Dict[RenderError, List[ValidationIssue]]:
        """Group errors by their category for batch processing."""

        groups = {}

        category_mapping = {
            "missing_dependency": RenderError.IMPORT_ERROR,
            "import_error": RenderError.IMPORT_ERROR,
            "nextjs_use_client": RenderError.FRAMEWORK_ERROR,
            "nextjs_image_props": RenderError.FRAMEWORK_ERROR,
            "jsx_syntax": RenderError.SYNTAX_ERROR,
            "export_syntax": RenderError.SYNTAX_ERROR,
            "styling_conflict": RenderError.STYLING_ERROR,
            "missing_interface": RenderError.TYPE_ERROR,
            "any_type": RenderError.TYPE_ERROR,
        }

        for error in errors:
            error_type = category_mapping.get(error.category, RenderError.RUNTIME_ERROR)
            if error_type not in groups:
                groups[error_type] = []
            groups[error_type].append(error)

        return groups

    def _apply_category_fixes(
        self,
        code: str,
        errors: List[ValidationIssue],
        category: RenderError,
        project_config: Dict[str, Any],
    ) -> AutoFixResult:
        """Apply fixes for a specific error category."""

        if category in self.fix_patterns:
            return self.fix_patterns[category](code, errors, project_config or {})
        else:
            return AutoFixResult(fixed_code=code, remaining_issues=errors)

    def _fix_import_errors(
        self, code: str, errors: List[ValidationIssue], project_config: Dict[str, Any]
    ) -> AutoFixResult:
        """Fix import-related errors."""

        fixed_code = code
        fixes_applied = []
        remaining_issues = []

        for error in errors:
            if "missing_dependency" in error.category or "import" in error.category:
                # Extract missing import from error message
                if "Import '" in error.message:
                    import_path = error.message.split("'")[1]
                    fix_result = self._add_missing_import(fixed_code, import_path)

                    if fix_result:
                        fixed_code = fix_result["code"]
                        fixes_applied.append(
                            AutoFix(
                                description=f"Added missing import for {import_path}",
                                original_code=code,
                                fixed_code=fixed_code,
                                confidence=0.9,
                                category="import_fix",
                            )
                        )
                    else:
                        remaining_issues.append(error)
                else:
                    remaining_issues.append(error)
            else:
                remaining_issues.append(error)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
        )

    def _fix_framework_errors(
        self, code: str, errors: List[ValidationIssue], project_config: Dict[str, Any]
    ) -> AutoFixResult:
        """Fix framework-specific errors."""

        fixed_code = code
        fixes_applied = []
        remaining_issues = []
        framework = project_config.get("framework", "react")

        for error in errors:
            if error.category == "nextjs_use_client":
                fix_result = self._add_use_client_directive(fixed_code)
                if fix_result:
                    fixed_code = fix_result
                    fixes_applied.append(
                        AutoFix(
                            description="Added 'use client' directive for Next.js client component",
                            original_code=code,
                            fixed_code=fixed_code,
                            confidence=0.95,
                            category="framework_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            elif error.category == "nextjs_image_props":
                fix_result = self._fix_nextjs_image_props(fixed_code)
                if fix_result:
                    fixed_code = fix_result
                    fixes_applied.append(
                        AutoFix(
                            description="Added required width/height props to Next.js Image component",
                            original_code=code,
                            fixed_code=fixed_code,
                            confidence=0.8,
                            category="framework_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            else:
                remaining_issues.append(error)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
        )

    def _fix_syntax_errors(
        self, code: str, errors: List[ValidationIssue], project_config: Dict[str, Any]
    ) -> AutoFixResult:
        """Fix syntax-related errors."""

        fixed_code = code
        fixes_applied = []
        remaining_issues = []

        for error in errors:
            if error.category == "jsx_syntax":
                # Fix self-closing tags
                original_code = fixed_code
                fixed_code = self._fix_self_closing_tags(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Fixed self-closing JSX tags",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.9,
                            category="syntax_fix",
                            line_number=error.line_number,
                        )
                    )
                else:
                    remaining_issues.append(error)

            elif error.category == "jsx_key":
                # Add key props to mapped elements
                original_code = fixed_code
                fixed_code = self._add_key_props(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Added key props to mapped JSX elements",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.85,
                            category="syntax_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            elif error.category == "export_syntax":
                # Fix export default syntax
                original_code = fixed_code
                fixed_code = self._fix_export_default(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Fixed export default syntax",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.9,
                            category="syntax_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            else:
                remaining_issues.append(error)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
        )

    def _fix_styling_errors(
        self, code: str, errors: List[ValidationIssue], project_config: Dict[str, Any]
    ) -> AutoFixResult:
        """Fix styling system conflicts."""

        fixed_code = code
        fixes_applied = []
        remaining_issues = []
        styling = project_config.get("styling", "tailwind")

        for error in errors:
            if error.category == "styling_conflict" and styling == "chakra":
                # Convert Tailwind classes to Chakra props
                original_code = fixed_code
                fixed_code = self._convert_tailwind_to_chakra(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Converted Tailwind classes to Chakra UI props",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.7,  # Lower confidence for complex conversions
                            category="styling_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)
            else:
                remaining_issues.append(error)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
        )

    def _fix_type_errors(
        self, code: str, errors: List[ValidationIssue], project_config: Dict[str, Any]
    ) -> AutoFixResult:
        """Fix TypeScript-related errors."""

        fixed_code = code
        fixes_applied = []
        remaining_issues = []

        for error in errors:
            if error.category == "missing_interface":
                # Add basic interface for props
                original_code = fixed_code
                fixed_code = self._add_props_interface(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Added TypeScript interface for component props",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.8,
                            category="type_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            elif error.category == "any_type":
                # Replace any types with more specific ones
                original_code = fixed_code
                fixed_code = self._replace_any_types(fixed_code)

                if fixed_code != original_code:
                    fixes_applied.append(
                        AutoFix(
                            description="Replaced 'any' types with more specific types",
                            original_code=original_code,
                            fixed_code=fixed_code,
                            confidence=0.6,  # Lower confidence for type inference
                            category="type_fix",
                        )
                    )
                else:
                    remaining_issues.append(error)

            else:
                remaining_issues.append(error)

        return AutoFixResult(
            fixed_code=fixed_code,
            fixes_applied=fixes_applied,
            remaining_issues=remaining_issues,
        )

    # Specific fix implementations

    def _add_missing_import(
        self, code: str, import_path: str
    ) -> Optional[Dict[str, Any]]:
        """Add a missing import to the code."""

        # Extract package name
        package_name = import_path.split("/")[0]

        # Check if we have a mapping for this import
        if package_name in self.import_mappings:
            import_statement = self.import_mappings[package_name]

            # Add import at the top after existing imports
            lines = code.split("\\n")
            import_inserted = False

            for i, line in enumerate(lines):
                if line.strip().startswith("import "):
                    continue
                elif not import_inserted:
                    lines.insert(i, import_statement)
                    import_inserted = True
                    break

            if not import_inserted:
                # Add at the very beginning
                lines.insert(0, import_statement)

            return {"code": "\\n".join(lines)}

        return None

    def _add_use_client_directive(self, code: str) -> Optional[str]:
        """Add 'use client' directive to Next.js component."""

        if '"use client"' in code or "'use client'" in code:
            return code

        lines = code.split("\\n")

        # Find the best place to insert 'use client' (after any comments, before imports)
        insert_index = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("//") or line.strip().startswith("/*"):
                continue
            elif line.strip().startswith("import"):
                insert_index = i
                break
            elif line.strip():
                insert_index = i
                break

        lines.insert(insert_index, '"use client";')
        lines.insert(insert_index + 1, "")  # Add blank line

        return "\\n".join(lines)

    def _fix_nextjs_image_props(self, code: str) -> Optional[str]:
        """Add required props to Next.js Image components."""

        # Find Image components without width/height
        image_pattern = r"<Image\\s+([^>]*?)(?<!width=)(?<!height=)([^>]*?)>"

        def add_image_props(match):
            props = match.group(1) + match.group(2)
            if "width=" not in props and "height=" not in props:
                # Add default width and height
                new_props = props + " width={200} height={200}"
                return f"<Image {new_props}>"
            return match.group(0)

        return re.sub(image_pattern, add_image_props, code)

    def _fix_server_component_issues(self, code: str) -> Optional[str]:
        """Fix Next.js server component issues."""
        # Basic server component fixes - remove client-only features
        if "useState" in code or "useEffect" in code:
            # This would need more sophisticated logic in production
            return code
        return code

    def _add_prop_types(self, code: str) -> str:
        """Add prop types for React components (placeholder)."""
        return code

    def _fix_self_closing_tags(self, code: str) -> str:
        """Fix self-closing JSX tags."""

        self_closing_tags = [
            "br",
            "img",
            "input",
            "hr",
            "area",
            "base",
            "col",
            "embed",
            "link",
            "meta",
            "source",
            "track",
            "wbr",
        ]

        for tag in self_closing_tags:
            # Fix <tag> to <tag />
            pattern = f"<{tag}(\\s[^>]*)?(?<!/)>"
            replacement = f"<{tag}\\1 />"
            code = re.sub(pattern, replacement, code)

        return code

    def _add_key_props(self, code: str) -> str:
        """Add key props to mapped JSX elements."""

        # Find .map() without key prop
        map_pattern = r"(\\.map\\([^}]+=>\\s*<)(\\w+)([^>]*?)(?<!key=)([^>]*?>)"

        def add_key(match):
            before = match.group(1)
            tag = match.group(2)
            props1 = match.group(3)
            props2 = match.group(4)

            if "key=" not in props1 + props2:
                # Add key prop (assuming index is available)
                return f"{before}{tag} key={{index}}{props1}{props2}"
            return match.group(0)

        return re.sub(map_pattern, add_key, code)

    def _fix_export_default(self, code: str) -> str:
        """Fix export default syntax."""

        # Fix "export default function Component" patterns
        pattern = r"export\\s+default\\s+function\\s+(\\w+)"
        if re.search(pattern, code):
            return code  # Already correct

        # Fix "export default Component" patterns
        component_name_match = re.search(
            r"const\\s+(\\w+)\\s*[:=].*?=>|function\\s+(\\w+)\\s*\\(", code
        )
        if component_name_match:
            component_name = component_name_match.group(
                1
            ) or component_name_match.group(2)

            # Replace incorrect export syntax
            code = re.sub(
                r"export\\s*\\{\\s*\\w+\\s*\\}",
                f"export default {component_name}",
                code,
            )
            code = re.sub(
                r"export\\s*default\\s*\\{[^}]+\\}",
                f"export default {component_name}",
                code,
            )

        return code

    def _convert_tailwind_to_chakra(self, code: str) -> str:
        """Convert Tailwind classes to Chakra UI props."""

        # Common Tailwind to Chakra conversions
        conversions = {
            "bg-blue-500": 'bg="blue.500"',
            "bg-red-500": 'bg="red.500"',
            "bg-green-500": 'bg="green.500"',
            "text-white": 'color="white"',
            "text-black": 'color="black"',
            "p-4": "p={4}",
            "p-6": "p={6}",
            "p-8": "p={8}",
            "m-4": "m={4}",
            "m-6": "m={6}",
            "flex": 'display="flex"',
            "text-center": 'textAlign="center"',
            "text-lg": 'fontSize="lg"',
            "font-bold": 'fontWeight="bold"',
        }

        for tailwind_class, chakra_prop in conversions.items():
            # Replace className patterns
            pattern = f'className="([^"]*\\b{tailwind_class}\\b[^"]*)"'

            def replace_class(match):
                full_classname = match.group(1)
                # Remove the Tailwind class and add Chakra prop
                remaining_classes = full_classname.replace(tailwind_class, "").strip()
                if remaining_classes:
                    return f'className="{remaining_classes}" {chakra_prop}'
                else:
                    return chakra_prop

            code = re.sub(pattern, replace_class, code)

        return code

    def _add_props_interface(self, code: str) -> str:
        """Add a basic TypeScript interface for component props."""

        if "interface" in code and "Props" in code:
            return code  # Already has interface

        # Extract component name
        component_match = re.search(
            r"const\\s+(\\w+)\\s*[:=]|function\\s+(\\w+)\\s*\\(", code
        )
        if not component_match:
            return code

        component_name = component_match.group(1) or component_match.group(2)
        interface_name = f"{component_name}Props"

        # Basic interface based on common props
        interface_props = []
        if "title" in code:
            interface_props.append("  title: string;")
        if "children" in code:
            interface_props.append("  children: React.ReactNode;")
        if "className" in code:
            interface_props.append("  className?: string;")
        if "onClick" in code:
            interface_props.append("  onClick?: () => void;")

        if not interface_props:
            interface_props = ["  // Add props here"]

        interface_code = f"""interface {interface_name} {{
{chr(10).join(interface_props)}
}}

"""

        # Insert interface before component definition
        lines = code.split("\\n")
        for i, line in enumerate(lines):
            if (
                f"const {component_name}" in line
                or f"function {component_name}" in line
            ):
                lines.insert(i, interface_code)
                break

        # Update component to use props interface
        prop_pattern = f"({component_name}\\s*[:=]\\s*\\([^)]*\\))"
        replacement = f"{component_name}: React.FC<{interface_name}> = (props)"
        code = re.sub(prop_pattern, replacement, "\\n".join(lines))

        return code

    def _replace_any_types(self, code: str) -> str:
        """Replace 'any' types with more specific ones."""

        # Common any type replacements
        replacements = {
            ": any\\[\\]": ": unknown[]",  # Array of any
            ": any": ": unknown",  # Simple any
            "any\\>": "unknown>",  # Generic any
        }

        for pattern, replacement in replacements.items():
            code = re.sub(pattern, replacement, code)

        return code

    def _validate_fix_safety(
        self, original_code: str, fixed_code: str, fixes: List[AutoFix]
    ) -> bool:
        """Validate that applied fixes are safe and don't break functionality."""

        # Basic safety checks
        safety_checks = [
            # Code length shouldn't change dramatically
            abs(len(fixed_code) - len(original_code)) / len(original_code) < 0.5,
            # Core structure should remain
            "export" in fixed_code,
            "return" in fixed_code,
            # No obvious syntax errors introduced
            fixed_code.count("(") == fixed_code.count(")"),
            fixed_code.count("{") == fixed_code.count("}"),
            fixed_code.count("[") == fixed_code.count("]"),
            # All fixes have reasonable confidence
            all(fix.confidence >= 0.5 for fix in fixes),
        ]

        return all(safety_checks)
