"""
Structured Output implementation for guaranteed schema-compliant component generation.
Uses OpenAI's structured output feature to ensure zero manual fixing.
"""

import json
from typing import Dict, List, Optional, Any, Type, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pydantic import BaseModel, Field

from openai import OpenAI


class ImportType(str, Enum):
    """Types of imports in a component."""
    DEFAULT = "default"
    NAMED = "named"
    NAMESPACE = "namespace"
    SIDE_EFFECT = "side_effect"


class PropType(str, Enum):
    """Common prop types for React components."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    FUNCTION = "function"
    REACT_NODE = "ReactNode"
    CUSTOM = "custom"


class ComponentImport(BaseModel):
    """Schema for component imports."""
    source: str = Field(description="Import source path")
    imports: List[str] = Field(description="List of imported items")
    import_type: ImportType = Field(default=ImportType.NAMED, description="Type of import")
    is_type_import: bool = Field(default=False, description="Whether this is a type-only import")


class ComponentProp(BaseModel):
    """Schema for component props."""
    name: str = Field(description="Prop name")
    type: str = Field(description="TypeScript type definition")
    required: bool = Field(default=True, description="Whether prop is required")
    default_value: Optional[str] = Field(default=None, description="Default value if any")
    description: Optional[str] = Field(default=None, description="Prop description")


class ComponentTest(BaseModel):
    """Schema for component tests."""
    test_name: str = Field(description="Name of the test")
    test_code: str = Field(description="Test implementation code")
    test_type: str = Field(default="unit", description="Type of test (unit, integration, e2e)")


class GeneratedComponent(BaseModel):
    """Complete schema for a generated React component."""
    component_name: str = Field(description="Name of the component")
    component_code: str = Field(description="Complete component implementation")
    imports: List[ComponentImport] = Field(description="All imports needed")
    props: List[ComponentProp] = Field(description="Component props definition")
    props_interface: str = Field(description="TypeScript interface for props")
    dependencies: List[str] = Field(default_factory=list, description="NPM dependencies needed")
    css_code: Optional[str] = Field(default=None, description="CSS/SCSS code if needed")
    test_code: Optional[str] = Field(default=None, description="Test code for the component")
    storybook_code: Optional[str] = Field(default=None, description="Storybook story code")
    usage_example: str = Field(description="Example usage of the component")
    accessibility_notes: List[str] = Field(default_factory=list, description="Accessibility considerations")
    performance_notes: List[str] = Field(default_factory=list, description="Performance considerations")


class ValidationResult(BaseModel):
    """Schema for validation results."""
    is_valid: bool = Field(description="Whether the code is valid")
    has_errors: bool = Field(description="Whether there are errors")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors found")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="List of warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    fixed_code: Optional[str] = Field(default=None, description="Fixed code if auto-fixable")
    confidence_score: float = Field(default=1.0, description="Confidence in the validation")


class StructuredOutputGenerator:
    """Generate components with guaranteed structured output."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key)
        
    def generate_component(
        self,
        prompt: str,
        context: Dict[str, Any],
        model: str = "gpt-4-turbo-preview"
    ) -> GeneratedComponent:
        """Generate a component with structured output guarantee."""
        
        # Build the system prompt with context
        system_prompt = self._build_system_prompt(context)
        
        # Create the messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Make the API call with structured output
        response = self.client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            temperature=0.7,
            response_format=GeneratedComponent,
        )
        
        # Extract the parsed component
        component = response.choices[0].message.parsed
        
        # Post-process the component
        component = self._post_process_component(component, context)
        
        return component
    
    def validate_with_structure(
        self,
        code: str,
        validation_context: Dict[str, Any],
        model: str = "gpt-4-turbo-preview"
    ) -> ValidationResult:
        """Validate code and get structured results."""
        
        validation_prompt = f"""
        Validate this React component code thoroughly:
        
        ```typescript
        {code}
        ```
        
        Context:
        - Project uses: {validation_context.get('framework', 'React')}
        - Styling: {validation_context.get('styling', 'Tailwind CSS')}
        - TypeScript: {validation_context.get('typescript', True)}
        
        Check for all possible issues and provide fixes.
        """
        
        messages = [
            {
                "role": "system", 
                "content": "You are an expert code validator. Provide thorough validation results."
            },
            {"role": "user", "content": validation_prompt}
        ]
        
        response = self.client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            temperature=0.3,  # Lower temperature for validation
            response_format=ValidationResult,
        )
        
        return response.choices[0].message.parsed
    
    def generate_with_iterations(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_iterations: int = 3
    ) -> Tuple[GeneratedComponent, List[ValidationResult]]:
        """Generate component with validation iterations until perfect."""
        
        validations = []
        component = None
        
        for iteration in range(max_iterations):
            # Generate or regenerate component
            if iteration == 0:
                component = self.generate_component(prompt, context)
            else:
                # Regenerate with fixes
                fix_prompt = self._build_fix_prompt(
                    prompt, 
                    component,
                    validations[-1]
                )
                component = self.generate_component(fix_prompt, context)
            
            # Validate the generated component
            validation = self.validate_with_structure(
                component.component_code,
                context
            )
            validations.append(validation)
            
            # If valid, we're done
            if validation.is_valid and not validation.has_errors:
                print(f"✅ Component validated successfully after {iteration + 1} iteration(s)")
                break
            
            print(f"🔄 Iteration {iteration + 1}: Found {len(validation.errors)} errors, regenerating...")
        
        return component, validations
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build a comprehensive system prompt with context."""
        
        prompt_parts = [
            "You are an expert React component generator.",
            "Generate production-ready components that require ZERO manual fixing.",
            "Follow these requirements strictly:"
        ]
        
        # Framework-specific instructions
        if context.get("framework") == "next.js":
            prompt_parts.append("- Use Next.js 14+ App Router patterns")
            prompt_parts.append("- Prefer server components unless client interactivity is needed")
            prompt_parts.append("- Use 'use client' directive when necessary")
        
        # Styling instructions
        if context.get("styling") == "tailwind":
            prompt_parts.append("- Use Tailwind CSS classes exclusively")
            prompt_parts.append("- Follow mobile-first responsive design")
            if context.get("design_tokens", {}).get("colors"):
                colors = context["design_tokens"]["colors"][:10]
                prompt_parts.append(f"- Use these color classes: {', '.join(colors)}")
        
        # Component library instructions
        if context.get("component_library") == "shadcn/ui":
            prompt_parts.append("- Import shadcn/ui components from '@/components/ui/*'")
            prompt_parts.append("- Use cn() utility for className composition")
            prompt_parts.append("- Follow shadcn/ui patterns and conventions")
        
        # TypeScript instructions
        if context.get("typescript", True):
            prompt_parts.append("- Use strict TypeScript with explicit types")
            prompt_parts.append("- Define proper interfaces for all props")
            prompt_parts.append("- Avoid using 'any' type")
        
        # Quality requirements
        prompt_parts.extend([
            "- Ensure WCAG 2.1 AA accessibility compliance",
            "- Include proper ARIA labels and roles",
            "- Handle all edge cases and error states",
            "- Add loading and empty states where appropriate",
            "- Use React.memo() for performance when beneficial",
            "- Follow React best practices and hooks rules",
            "- Include helpful comments for complex logic"
        ])
        
        return "\n".join(prompt_parts)
    
    def _post_process_component(
        self, 
        component: GeneratedComponent,
        context: Dict[str, Any]
    ) -> GeneratedComponent:
        """Post-process the generated component for consistency."""
        
        # Ensure imports are properly formatted
        component.imports = self._consolidate_imports(component.imports)
        
        # Add common dependencies based on imports
        component.dependencies = self._infer_dependencies(component.imports)
        
        # Generate props interface if not provided
        if not component.props_interface and component.props:
            component.props_interface = self._generate_props_interface(
                component.component_name,
                component.props
            )
        
        # Add default accessibility notes if empty
        if not component.accessibility_notes:
            component.accessibility_notes = self._get_default_accessibility_notes(
                component.component_code
            )
        
        return component
    
    def _consolidate_imports(self, imports: List[ComponentImport]) -> List[ComponentImport]:
        """Consolidate and organize imports."""
        
        # Group imports by source
        import_map: Dict[str, ComponentImport] = {}
        
        for imp in imports:
            if imp.source in import_map:
                # Merge imports from same source
                existing = import_map[imp.source]
                existing.imports.extend(imp.imports)
                existing.imports = list(set(existing.imports))  # Remove duplicates
            else:
                import_map[imp.source] = imp
        
        # Sort imports: React first, then external, then internal
        sorted_imports = []
        
        # React imports
        for source, imp in import_map.items():
            if source == "react":
                sorted_imports.append(imp)
        
        # External imports
        for source, imp in import_map.items():
            if not source.startswith(".") and not source.startswith("@/") and source != "react":
                sorted_imports.append(imp)
        
        # Internal imports
        for source, imp in import_map.items():
            if source.startswith(".") or source.startswith("@/"):
                sorted_imports.append(imp)
        
        return sorted_imports
    
    def _infer_dependencies(self, imports: List[ComponentImport]) -> List[str]:
        """Infer NPM dependencies from imports."""
        
        dependencies = set()
        
        for imp in imports:
            source = imp.source
            
            # Skip relative and alias imports
            if source.startswith(".") or source.startswith("@/"):
                continue
            
            # Skip built-in React
            if source == "react":
                continue
            
            # Extract package name
            if source.startswith("@"):
                # Scoped package
                parts = source.split("/")
                if len(parts) >= 2:
                    package = f"{parts[0]}/{parts[1]}"
                    dependencies.add(package)
            else:
                # Regular package
                package = source.split("/")[0]
                dependencies.add(package)
        
        return sorted(list(dependencies))
    
    def _generate_props_interface(
        self,
        component_name: str,
        props: List[ComponentProp]
    ) -> str:
        """Generate TypeScript interface from props."""
        
        if not props:
            return f"interface {component_name}Props {{}}"
        
        lines = [f"interface {component_name}Props {{"]
        
        for prop in props:
            # Add description as comment if available
            if prop.description:
                lines.append(f"  /** {prop.description} */")
            
            # Build the prop definition
            prop_def = f"  {prop.name}"
            if not prop.required:
                prop_def += "?"
            prop_def += f": {prop.type};"
            
            lines.append(prop_def)
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _get_default_accessibility_notes(self, code: str) -> List[str]:
        """Extract or generate accessibility notes from component code."""
        
        notes = []
        
        # Check for common accessibility patterns
        if "button" in code.lower():
            notes.append("Ensure button has accessible label via children or aria-label")
        
        if "img" in code.lower() and "alt=" not in code:
            notes.append("Add alt text to all images")
        
        if "form" in code.lower():
            notes.append("Ensure form inputs have associated labels")
            notes.append("Provide clear error messages for validation")
        
        if "modal" in code.lower() or "dialog" in code.lower():
            notes.append("Implement focus trap for modal/dialog")
            notes.append("Ensure ESC key closes the modal")
        
        if not notes:
            notes.append("Component follows WCAG 2.1 AA standards")
        
        return notes
    
    def _build_fix_prompt(
        self,
        original_prompt: str,
        component: GeneratedComponent,
        validation: ValidationResult
    ) -> str:
        """Build a prompt to fix validation issues."""
        
        fix_prompt = f"""
        Original request: {original_prompt}
        
        The previously generated component has these issues:
        
        Errors:
        {json.dumps([asdict(e) if hasattr(e, '__dict__') else e for e in validation.errors], indent=2)}
        
        Warnings:
        {json.dumps([asdict(w) if hasattr(w, '__dict__') else w for w in validation.warnings], indent=2)}
        
        Please regenerate the component fixing all these issues.
        The component must be production-ready with ZERO errors.
        
        Previous component code for reference:
        ```typescript
        {component.component_code}
        ```
        """
        
        return fix_prompt