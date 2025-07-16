import os
import re
from pathlib import Path
from typing import Dict, Optional


class FileManager:
    """Smart file placement and component management"""

    def __init__(self):
        self.component_extensions = {"typescript": ".tsx", "javascript": ".jsx"}

    def save_component(
        self,
        component_code: str,
        output_path: Optional[str],
        context: Dict,
        user_prompt: str = "",
    ) -> str:
        """Save component to appropriate location based on intent"""

        if output_path:
            # User specified path
            file_path = self._ensure_extension(output_path, context)
        else:
            # Auto-detect path based on user intent and component name
            component_name = self._extract_component_name(component_code)
            is_page = self._is_page_request(user_prompt, component_name)

            if is_page:
                file_path = self._auto_generate_page_path(
                    component_name, context, user_prompt
                )
            else:
                file_path = self._auto_generate_component_path(component_name, context)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Clean and format component code
        clean_code = self._format_component_code(component_code, context)

        # Write file
        with open(file_path, "w") as f:
            f.write(clean_code)

        return file_path

    def _extract_component_name(self, component_code: str) -> str:
        """Extract component name from code"""

        # Look for component declaration patterns
        patterns = [
            r"const\s+(\w+)\s*=",
            r"function\s+(\w+)",
            r"export\s+default\s+function\s+(\w+)",
            r"export\s+const\s+(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, component_code)
            if match:
                return match.group(1)

        # Fallback to generic name
        return "Component"

    def _is_page_request(self, user_prompt: str, component_name: str) -> bool:
        """Determine if this is a page request vs component request"""

        page_keywords = [
            "page",
            "screen",
            "view",
            "route",
            "dashboard",
            "landing",
            "homepage",
            "login page",
            "profile page",
            "settings page",
            "about page",
            "contact page",
            "pricing page",
            "checkout page",
        ]

        component_keywords = [
            "component",
            "widget",
            "element",
            "button",
            "card",
            "modal",
            "dropdown",
            "menu",
            "form",
            "input",
            "table",
            "list",
        ]

        prompt_lower = user_prompt.lower()

        # Check for explicit page keywords
        for keyword in page_keywords:
            if keyword in prompt_lower:
                return True

        # Check for explicit component keywords
        for keyword in component_keywords:
            if keyword in prompt_lower:
                return False

        # Check component name for page indicators
        name_lower = component_name.lower()
        if any(
            keyword in name_lower for keyword in ["page", "screen", "view", "dashboard"]
        ):
            return True

        # Default to component if unclear
        return False

    def _auto_generate_page_path(
        self, component_name: str, context: Dict, user_prompt: str
    ) -> str:
        """Auto-generate page path for Next.js App Router"""

        # Extract page name from prompt or component name
        page_name = self._extract_page_name(user_prompt, component_name)

        # Check if this is a Next.js App Router project
        framework = context.get("framework", "")
        project_structure = context.get("project_structure", {})

        if framework == "next.js" and self._has_app_directory(project_structure):
            # Next.js App Router: app/[page]/page.tsx
            return f"app/{page_name}/page.tsx"
        elif framework == "next.js":
            # Next.js Pages Router: pages/[page].tsx
            return f"pages/{page_name}.tsx"
        else:
            # Other frameworks: treat as component
            return self._auto_generate_component_path(component_name, context)

    def _auto_generate_component_path(self, component_name: str, context: Dict) -> str:
        """Auto-generate component path with descriptive naming"""

        # Get components directory from context
        components_dir = context.get("project_structure", {}).get(
            "components_dir", "src/components"
        )

        # Use descriptive component name (PascalCase)
        file_name = self._ensure_pascal_case(component_name)

        # Determine file extension
        extension = ".tsx" if self._is_typescript_project(context) else ".jsx"

        # Build full path
        file_path = os.path.join(components_dir, f"{file_name}{extension}")

        return file_path

    def _extract_page_name(self, user_prompt: str, component_name: str) -> str:
        """Extract page name from prompt or component name"""

        # Common page name mappings
        page_mappings = {
            "login": "login",
            "signin": "login",
            "signup": "register",
            "register": "register",
            "profile": "profile",
            "dashboard": "dashboard",
            "settings": "settings",
            "about": "about",
            "contact": "contact",
            "pricing": "pricing",
            "checkout": "checkout",
            "cart": "cart",
            "home": "home",
            "landing": "home",
        }

        prompt_lower = user_prompt.lower()

        # Check for common page names in prompt
        for key, value in page_mappings.items():
            if key in prompt_lower:
                return value

        # Extract from component name
        name_lower = component_name.lower()
        for key, value in page_mappings.items():
            if key in name_lower:
                return value

        # Default to kebab-case version of component name
        return self._pascal_to_kebab(component_name)

    def _has_app_directory(self, project_structure: Dict) -> bool:
        """Check if project uses Next.js App Router (has app/ directory)"""

        pages_dir = project_structure.get("pages_dir", "")
        return "app" in pages_dir.lower()

    def _ensure_pascal_case(self, name: str) -> str:
        """Ensure name is in PascalCase"""

        # Handle kebab-case and snake_case
        if "-" in name or "_" in name:
            parts = name.replace("-", "_").split("_")
            return "".join(word.capitalize() for word in parts)

        # Handle camelCase
        if name and name[0].islower():
            return name[0].upper() + name[1:]

        return name

    def _auto_generate_path(self, component_name: str, context: Dict) -> str:
        """Auto-generate file path based on component name and project structure"""

        # Get components directory from context
        components_dir = context.get("project_structure", {}).get(
            "components_dir", "src/components"
        )

        # Convert PascalCase to kebab-case for file name
        file_name = self._pascal_to_kebab(component_name)

        # Determine file extension
        extension = ".tsx" if self._is_typescript_project(context) else ".jsx"

        # Build full path
        file_path = os.path.join(components_dir, f"{file_name}{extension}")

        return file_path

    def _ensure_extension(self, file_path: str, context: Dict) -> str:
        """Ensure file has appropriate extension"""

        if not file_path.endswith((".tsx", ".jsx", ".ts", ".js")):
            extension = ".tsx" if self._is_typescript_project(context) else ".jsx"
            file_path += extension

        return file_path

    def _is_typescript_project(self, context: Dict) -> bool:
        """Check if project uses TypeScript"""

        # Check for TypeScript indicators
        ts_indicators = ["tsconfig.json", "package.json with @types"]

        # Simple heuristic: if framework is detected and common, assume TypeScript
        framework = context.get("framework", "")
        if framework in ["next.js", "vite"]:
            return True

        return False

    def _pascal_to_kebab(self, pascal_case: str) -> str:
        """Convert PascalCase to kebab-case"""

        # Insert hyphens before uppercase letters (except the first one)
        kebab = re.sub(r"(?<!^)(?=[A-Z])", "-", pascal_case)
        return kebab.lower()

    def _format_component_code(self, code: str, context: Dict) -> str:
        """Format and clean component code"""

        # Remove any markdown code blocks
        if "```" in code:
            start_marker = code.find("```")
            if start_marker != -1:
                start_content = code.find("\n", start_marker) + 1
                end_marker = code.find("```", start_content)
                if end_marker != -1:
                    code = code[start_content:end_marker].strip()

        # Add proper imports if missing
        code = self._add_missing_imports(code, context)

        # Ensure proper formatting
        lines = code.split("\n")
        formatted_lines = []

        for line in lines:
            # Remove excessive whitespace but preserve indentation
            if line.strip():
                formatted_lines.append(line.rstrip())
            else:
                formatted_lines.append("")

        # Remove trailing empty lines
        while formatted_lines and not formatted_lines[-1].strip():
            formatted_lines.pop()

        # Ensure file ends with newline
        formatted_code = "\n".join(formatted_lines) + "\n"

        return formatted_code

    def _add_missing_imports(self, code: str, context: Dict) -> str:
        """Add missing React imports if not present"""

        imports_to_add = []

        # Check for React import
        if "React" in code and "import React" not in code:
            imports_to_add.append("import React from 'react';")

        # Check for specific React hooks
        hooks = ["useState", "useEffect", "useCallback", "useMemo", "useRef"]
        used_hooks = [hook for hook in hooks if hook in code]

        if used_hooks and "import {" not in code:
            hooks_import = f"import {{ {', '.join(used_hooks)} }} from 'react';"
            imports_to_add.append(hooks_import)

        # Add component library imports based on context
        component_library = context.get("component_library", "none")
        if component_library == "shadcn/ui" and "cn(" in code:
            if "import { cn }" not in code:
                imports_to_add.append("import { cn } from '@/lib/utils';")

        # Add imports to the beginning of the file
        if imports_to_add:
            existing_imports = []
            code_lines = code.split("\n")

            # Find existing imports
            for i, line in enumerate(code_lines):
                if line.strip().startswith("import "):
                    existing_imports.append(line)
                elif line.strip() and not line.strip().startswith("//"):
                    # First non-import, non-comment line
                    break

            # Combine imports
            all_imports = imports_to_add + existing_imports

            # Remove existing imports from code
            code_without_imports = []
            skip_imports = True

            for line in code_lines:
                if skip_imports:
                    if line.strip().startswith("import "):
                        continue
                    elif line.strip() and not line.strip().startswith("//"):
                        skip_imports = False

                if not skip_imports:
                    code_without_imports.append(line)

            # Reconstruct code with proper imports
            final_code = (
                "\n".join(all_imports) + "\n\n" + "\n".join(code_without_imports)
            )
            return final_code

        return code

    def create_component_directory(self, component_name: str, context: Dict) -> str:
        """Create a directory for complex components with multiple files"""

        components_dir = context.get("project_structure", {}).get(
            "components_dir", "src/components"
        )
        component_dir = os.path.join(
            components_dir, self._pascal_to_kebab(component_name)
        )

        os.makedirs(component_dir, exist_ok=True)

        return component_dir

    def create_index_file(self, component_name: str, component_dir: str) -> str:
        """Create an index file for component export"""

        index_content = f"export {{ default }} from './{component_name}';\n"
        index_path = os.path.join(component_dir, "index.ts")

        with open(index_path, "w") as f:
            f.write(index_content)

        return index_path
