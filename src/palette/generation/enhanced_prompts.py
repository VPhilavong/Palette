"""
Enhanced prompt engineering with few-shot learning and RAG capabilities.
Leverages Tree-sitter analysis to provide contextual component examples.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from .prompts import UIUXCopilotPromptBuilder
from ..analysis.treesitter_analyzer import TreeSitterAnalyzer, ComponentPattern


@dataclass
class ComponentExample:
    """Represents a high-quality component example for few-shot learning."""

    name: str
    file_path: str
    source_code: str
    props: List[str]
    styling_patterns: List[str]
    complexity_score: int
    relevance_score: float = 0.0

    def __hash__(self):
        """Make ComponentExample hashable for use as dict keys."""
        return hash((self.name, self.file_path))

    def __eq__(self, other):
        """Define equality for ComponentExample objects."""
        if not isinstance(other, ComponentExample):
            return False
        return self.name == other.name and self.file_path == other.file_path


class ComponentSearchIndex:
    """Searchable index of project components for RAG."""

    def __init__(self):
        self.components: List[ComponentExample] = []
        self.style_index: Dict[str, List[ComponentExample]] = defaultdict(list)
        self.prop_index: Dict[str, List[ComponentExample]] = defaultdict(list)
        self.pattern_index: Dict[str, List[ComponentExample]] = defaultdict(list)

    def add_component(self, component: ComponentExample):
        """Add a component to the searchable index."""
        self.components.append(component)

        # Index by styling patterns
        for pattern in component.styling_patterns:
            self.style_index[pattern].append(component)

        # Index by props
        for prop in component.props:
            self.prop_index[prop].append(component)

        # Index by code patterns (keywords extracted from source)
        patterns = self._extract_code_patterns(component.source_code)
        for pattern in patterns:
            self.pattern_index[pattern].append(component)

    def _extract_code_patterns(self, source_code: str) -> List[str]:
        """Extract searchable patterns from component source code."""
        patterns = []

        # Extract JSX element types
        jsx_elements = re.findall(r"<(\w+)", source_code)
        patterns.extend(jsx_elements)

        # Extract hook usage
        hooks = re.findall(r"use(\w+)", source_code)
        patterns.extend([f"use{hook}" for hook in hooks])

        # Extract common UI patterns
        ui_patterns = [
            "button",
            "card",
            "modal",
            "form",
            "input",
            "select",
            "table",
            "navbar",
            "sidebar",
            "dropdown",
            "tooltip",
            "dialog",
            "alert",
            "spinner",
            "loader",
            "badge",
            "avatar",
            "tabs",
            "accordion",
        ]

        for pattern in ui_patterns:
            if pattern in source_code.lower():
                patterns.append(pattern)

        return list(set(patterns))

    def search(
        self, query: str, query_props: List[str] = None, max_results: int = 3
    ) -> List[ComponentExample]:
        """Search for relevant components using multiple strategies."""
        query_lower = query.lower()
        candidates = defaultdict(float)

        # Strategy 1: Semantic similarity using keyword matching
        semantic_score = self._calculate_semantic_similarity(query_lower)
        for component, score in semantic_score.items():
            candidates[component] += score

        # Strategy 2: Direct name/pattern matches
        for pattern, components in self.pattern_index.items():
            if pattern.lower() in query_lower:
                for component in components:
                    candidates[component] += 2.0

        # Strategy 3: Prop similarity
        if query_props:
            for prop in query_props:
                for component in self.prop_index.get(prop, []):
                    candidates[component] += 1.0

        # Strategy 4: Styling pattern similarity
        style_keywords = ["styled", "tailwind", "css", "className", "variant"]
        for keyword in style_keywords:
            if keyword in query_lower:
                for pattern, components in self.style_index.items():
                    if keyword in pattern.lower():
                        for component in components:
                            candidates[component] += 0.5

        # Strategy 5: Component type inference
        type_score = self._infer_component_type(query_lower)
        for component, score in type_score.items():
            candidates[component] += score

        # Sort by relevance score and return top results
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return [component for component, score in sorted_candidates[:max_results]]

    def _calculate_semantic_similarity(
        self, query: str
    ) -> Dict[ComponentExample, float]:
        """Calculate semantic similarity using keyword overlap and context."""
        scores = defaultdict(float)

        # Extract meaningful keywords from query
        query_keywords = self._extract_keywords(query)

        for component in self.components:
            # Calculate similarity based on component source code
            component_keywords = self._extract_keywords(component.source_code.lower())

            # Calculate overlap score
            overlap = len(query_keywords.intersection(component_keywords))
            total_keywords = len(query_keywords.union(component_keywords))

            if total_keywords > 0:
                similarity = overlap / total_keywords
                scores[component] += (
                    similarity * 2.0
                )  # Weight semantic similarity highly

        return scores

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text for semantic matching."""
        import re

        # Remove common code artifacts
        text = re.sub(r"[{}();,.]", " ", text)
        text = re.sub(r"\s+", " ", text)

        # Extract words
        words = set(text.split())

        # Filter meaningful keywords
        meaningful_words = set()

        # Include UI/UX related terms
        ui_terms = {
            "button",
            "card",
            "modal",
            "form",
            "input",
            "select",
            "table",
            "navbar",
            "sidebar",
            "dropdown",
            "tooltip",
            "dialog",
            "alert",
            "spinner",
            "loader",
            "badge",
            "avatar",
            "tabs",
            "accordion",
            "toggle",
            "switch",
            "slider",
            "progress",
            "breadcrumb",
            "pagination",
            "search",
            "filter",
            "sort",
            "responsive",
            "mobile",
            "desktop",
            "hover",
            "focus",
            "active",
            "disabled",
            "loading",
            "error",
            "success",
            "warning",
            "primary",
            "secondary",
        }

        for word in words:
            # Include UI terms
            if word in ui_terms:
                meaningful_words.add(word)
            # Include capitalized words (likely component names)
            elif word and word[0].isupper():
                meaningful_words.add(word.lower())
            # Include words longer than 3 characters that aren't common code words
            elif len(word) > 3 and word not in {
                "const",
                "return",
                "import",
                "export",
                "function",
            }:
                meaningful_words.add(word)

        return meaningful_words

    def _infer_component_type(self, query: str) -> Dict[ComponentExample, float]:
        """Infer component type from query and score accordingly."""
        scores = defaultdict(float)

        # Component type mappings - check compound types first
        type_patterns = {
            "product_grid": [
                "product card grid",
                "product grid",
                "item grid",
                "product listing",
                "product cards",
            ],
            "pricing_section": [
                "pricing section",
                "pricing tier",
                "pricing plan",
                "pricing card",
            ],
            "dashboard_header": ["dashboard header", "admin header", "app header with"],
            "hero_section": ["hero section", "landing hero", "hero banner"],
            "button": ["button", "btn", "click", "action", "submit"],
            "form": ["form", "input", "field", "validation", "submit"],
            "card": ["card", "panel", "container", "box"],
            "modal": ["modal", "dialog", "popup", "overlay"],
            "table": ["table", "list", "data", "grid", "row"],
            "navigation": ["nav", "menu", "sidebar", "header"],
            "loading": ["loading", "spinner", "progress", "skeleton"],
            "layout": ["layout", "container", "wrapper", "grid", "flex"],
        }

        # Find matching patterns in query
        matched_types = []
        for component_type, patterns in type_patterns.items():
            if any(pattern in query for pattern in patterns):
                matched_types.append(component_type)

        # Score components based on inferred types
        for component in self.components:
            component_source = component.source_code.lower()
            component_name = component.name.lower()

            for matched_type in matched_types:
                type_patterns_for_type = type_patterns[matched_type]

                # Score based on component name and source content
                name_matches = sum(
                    1 for pattern in type_patterns_for_type if pattern in component_name
                )
                source_matches = sum(
                    1
                    for pattern in type_patterns_for_type
                    if pattern in component_source
                )

                type_score = (name_matches * 2.0) + (source_matches * 0.5)
                scores[component] += type_score

        return scores


class EnhancedPromptBuilder(UIUXCopilotPromptBuilder):
    """Enhanced prompt builder with few-shot learning and RAG capabilities."""

    def __init__(self):
        super().__init__()
        self.tree_sitter = None
        self.component_index = ComponentSearchIndex()
        self.project_path = None

    def initialize_project_analysis(self, project_path: str) -> Dict[str, Any]:
        """Initialize Tree-sitter analysis and build component index."""
        try:
            from ..analysis.treesitter_analyzer import TreeSitterAnalyzer

            self.tree_sitter = TreeSitterAnalyzer()
            self.project_path = Path(project_path)

            # Analyze project components
            analysis_result = self.tree_sitter.analyze_project(project_path)

            # Build component search index
            self._build_component_index(analysis_result)

            return analysis_result

        except ImportError:
            print("Warning: Tree-sitter not available, falling back to basic prompts")
            return {}

    def _build_component_index(self, analysis_result: Dict[str, Any]):
        """Build searchable component index from Tree-sitter analysis."""
        components_data = analysis_result.get("components", [])

        for comp_data in components_data:
            try:
                # Read component source code
                file_path = Path(comp_data["file_path"])
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        source_code = f.read()

                    # Calculate complexity and quality scores
                    complexity = self._calculate_complexity_score(source_code)

                    # Create component example
                    example = ComponentExample(
                        name=comp_data["name"],
                        file_path=comp_data["file_path"],
                        source_code=source_code,
                        props=[prop["name"] for prop in comp_data.get("props", [])],
                        styling_patterns=comp_data.get("styling_patterns", []),
                        complexity_score=complexity,
                    )

                    # Add to index
                    self.component_index.add_component(example)

            except Exception as e:
                print(
                    f"Warning: Could not index component {comp_data.get('name', 'unknown')}: {e}"
                )

    def _calculate_complexity_score(self, source_code: str) -> int:
        """Calculate component complexity score for quality filtering."""
        score = 0

        # Base score from length (moderate length is often better)
        lines = source_code.count("\n")
        if 20 <= lines <= 100:
            score += 3
        elif 10 <= lines <= 150:
            score += 2
        elif lines < 10:
            score += 1

        # TypeScript usage
        if "interface " in source_code or "type " in source_code:
            score += 2

        # Modern React patterns
        modern_patterns = [
            "useState",
            "useEffect",
            "useCallback",
            "useMemo",
            "forwardRef",
        ]
        for pattern in modern_patterns:
            if pattern in source_code:
                score += 1

        # Good practices
        if "export default" in source_code:
            score += 1
        if "React.FC" in source_code or ": FC" in source_code:
            score += 1
        if "className=" in source_code:
            score += 1

        # Avoid overly complex or generated code
        if source_code.count("{") > 50:  # Too many braces
            score -= 2
        if "DO NOT EDIT" in source_code:  # Generated files
            score -= 5

        return max(0, score)

    def build_enhanced_system_prompt(self, context: Dict, user_request: str) -> str:
        """Build enhanced system prompt with frontend engineer persona and component library."""
        # Start with frontend engineer persona
        persona = self._build_frontend_engineer_persona()
        
        # Build component library section FIRST
        component_library = self._build_component_library_section(context)
        
        # Get base system prompt
        base_prompt = self.build_ui_system_prompt(context)
        
        # Build design system section
        design_system = self._build_design_system_section(context)
        
        # Find relevant component examples
        examples = self._find_relevant_examples(user_request, context)
        
        # Build composition examples if we have components
        composition_examples = ""
        if context.get("available_imports", {}).get("ui_components"):
            composition_examples = self._build_composition_examples(context)

        # Build few-shot learning section
        few_shot_section = ""
        if examples:
            few_shot_section = self._build_few_shot_section(examples)

        # Construct the complete enhanced prompt
        enhanced_prompt = f"""{persona}

{component_library}

{design_system}

STRICT COMPONENT DEVELOPMENT RULES:
1. ALWAYS check the component library above FIRST before creating anything new
2. IMPORT and COMPOSE existing components to build the requested UI
3. Only create new base components if absolutely no existing component can fulfill the need
4. Follow the EXACT import patterns shown in the component library
5. Use the project's design tokens and styling patterns
6. Your code should look like it was written by a team member who knows this codebase

{base_prompt}

{composition_examples}

{few_shot_section}

REMEMBER: You are a frontend engineer on this team. Use the existing components and patterns. 
Your goal is to create UIs that seamlessly integrate with the existing codebase."""

        return enhanced_prompt

    def _find_relevant_examples(
        self, user_request: str, context: Dict, max_examples: int = 2
    ) -> List[ComponentExample]:
        """Find the most relevant component examples for the user request."""
        if not self.component_index.components:
            return []

        # Extract potential props from request
        query_props = self._extract_props_from_request(user_request)

        # Search for relevant components
        relevant_components = self.component_index.search(
            user_request, query_props=query_props, max_results=max_examples * 2
        )

        # Filter and rank by quality
        quality_filtered = [
            comp
            for comp in relevant_components
            if comp.complexity_score >= 3 and len(comp.source_code) < 3000
        ]

        # If not enough quality components, include simpler ones
        if len(quality_filtered) < max_examples:
            simple_filtered = [
                comp
                for comp in relevant_components
                if comp.complexity_score >= 1 and len(comp.source_code) < 2000
            ]
            quality_filtered.extend(simple_filtered)

        return quality_filtered[:max_examples]

    def _extract_props_from_request(self, user_request: str) -> List[str]:
        """Extract likely prop names from user request."""
        # Common prop patterns in UI requests
        prop_patterns = {
            "disabled": ["disabled", "disable"],
            "loading": ["loading", "spinner", "pending"],
            "variant": ["variant", "type", "style"],
            "size": ["size", "small", "large", "big"],
            "children": ["content", "text", "label"],
            "onClick": ["click", "press", "action"],
            "className": ["class", "style", "custom"],
            "placeholder": ["placeholder", "hint"],
            "value": ["value", "data"],
            "onChange": ["change", "input", "update"],
        }

        extracted_props = []
        request_lower = user_request.lower()

        for prop, keywords in prop_patterns.items():
            for keyword in keywords:
                if keyword in request_lower:
                    extracted_props.append(prop)
                    break

        return extracted_props

    def _build_few_shot_section(self, examples: List[ComponentExample]) -> str:
        """Build few-shot learning section with component examples."""
        if not examples:
            return ""

        sections = ["REAL PROJECT EXAMPLES (Follow these patterns exactly):"]

        for i, example in enumerate(examples, 1):
            # Truncate very long components for prompt efficiency
            source_code = example.source_code
            if len(source_code) > 1500:
                source_code = self._truncate_component_smartly(source_code)

            sections.append(
                f"""
--- EXAMPLE {i}: {example.name} ---
File: {Path(example.file_path).name}
Props: {', '.join(example.props) if example.props else 'None'}
Styling: {', '.join(example.styling_patterns) if example.styling_patterns else 'Basic'}

{source_code}
--- END EXAMPLE {i} ---"""
            )

        return "\n".join(sections)

    def _truncate_component_smartly(self, source_code: str) -> str:
        """Intelligently truncate component code while preserving structure."""
        lines = source_code.split("\n")

        # Keep imports, interfaces, component signature, and return statement
        important_lines = []
        in_component = False
        in_return = False
        brace_count = 0

        for line in lines:
            line_stripped = line.strip()

            # Always keep imports
            if line_stripped.startswith("import "):
                important_lines.append(line)
                continue

            # Always keep interfaces and types
            if line_stripped.startswith(("interface ", "type ")):
                important_lines.append(line)
                continue

            # Track component function start
            if (
                "const " in line and "=" in line and "=>" in line
            ) or line_stripped.startswith("function "):
                in_component = True
                important_lines.append(line)
                continue

            # Track return statement
            if in_component and "return" in line_stripped:
                in_return = True
                important_lines.append(line)
                continue

            # Keep return JSX structure (first few lines)
            if in_return and len(important_lines) < 30:
                important_lines.append(line)

                # Track braces to know when JSX ends
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0 and (">" in line or ";" in line):
                    break

        # Add export if present
        for line in reversed(lines):
            if "export default" in line:
                important_lines.append(line)
                break

        return "\n".join(important_lines)

    def build_rag_enhanced_user_prompt(self, user_request: str, context: Dict) -> str:
        """Build user prompt enhanced with RAG context."""
        base_prompt = self.build_user_prompt(user_request, context)

        if not self.component_index.components:
            return base_prompt

        # Find similar components for context
        similar_components = self.component_index.search(user_request, max_results=3)

        if not similar_components:
            return base_prompt

        # Build context section
        context_section = self._build_context_section(similar_components, user_request)

        enhanced_prompt = f"""{base_prompt}

{context_section}

Use the context above to ensure your component follows the same patterns and conventions as existing components in this project."""

        return enhanced_prompt

    def _build_context_section(
        self, similar_components: List[ComponentExample], user_request: str
    ) -> str:
        """Build context section with relevant component information."""
        sections = ["RELEVANT PROJECT CONTEXT:"]

        # Extract common patterns
        all_props = []
        all_patterns = []
        import_patterns = set()

        for comp in similar_components:
            all_props.extend(comp.props)
            all_patterns.extend(comp.styling_patterns)

            # Extract import patterns
            imports = re.findall(r'import.*from [\'"]([^\'"]+)[\'"]', comp.source_code)
            import_patterns.update(imports)

        # Summarize common patterns
        if all_props:
            common_props = list(set(all_props))[:8]
            sections.append(
                f"Common props in similar components: {', '.join(common_props)}"
            )

        if all_patterns:
            common_patterns = list(set(all_patterns))[:5]
            sections.append(f"Common styling patterns: {', '.join(common_patterns)}")

        if import_patterns:
            filtered_imports = [
                imp for imp in import_patterns if not imp.startswith(".")
            ][:5]
            sections.append(f"Common imports: {', '.join(filtered_imports)}")

        # Add specific component references
        sections.append("\nSimilar components found in this project:")
        for comp in similar_components[:2]:
            sections.append(
                f"- {comp.name}: {len(comp.props)} props, {', '.join(comp.styling_patterns[:3])}"
            )

        return "\n".join(sections)
    
    def _build_frontend_engineer_persona(self) -> str:
        """Build the frontend engineer persona section"""
        return """YOU ARE A FRONTEND ENGINEER ON THIS PROJECT TEAM

You have deep knowledge of this codebase and always follow the team's established patterns.
You prioritize code reuse and consistency over creating new components from scratch.
You think in terms of composition - combining existing components to create new UIs.
You know the import paths, component APIs, and design patterns used in this project."""
    
    def _build_component_library_section(self, context: Dict) -> str:
        """Build comprehensive component library section with import paths"""
        sections = ["AVAILABLE COMPONENTS IN THIS PROJECT:"]
        
        # Get UI components from context
        ui_components = context.get("available_imports", {}).get("ui_components", {})
        
        # Process shadcn/ui components
        if ui_components.get("shadcn_ui"):
            sections.append("\n## shadcn/ui Components (Installed):")
            for comp_info in ui_components["shadcn_ui"]:
                if isinstance(comp_info, dict):
                    name = comp_info.get("name", "Unknown")
                    import_path = comp_info.get("import_path", f"@/components/ui/{name}")
                    purpose = comp_info.get("purpose", "")
                    sections.append(f"- {name}: import {{ {name} }} from '{import_path}' - {purpose}")
                else:
                    # Fallback for old format
                    sections.append(f"- {comp_info}: import {{ {comp_info} }} from '@/components/ui/{comp_info}'")
        
        # Process custom components
        if ui_components.get("custom"):
            sections.append("\n## Custom Project Components:")
            # Group by type
            components_by_type = defaultdict(list)
            for comp_info in ui_components["custom"]:
                if isinstance(comp_info, dict):
                    comp_type = comp_info.get("type", "component")
                    components_by_type[comp_type].append(comp_info)
                else:
                    # Fallback for old format
                    components_by_type["component"].append({
                        "name": comp_info,
                        "import_path": f"@/components/{comp_info}",
                        "purpose": f"Custom {comp_info} component"
                    })
            
            # Display by type
            type_order = ["button", "form", "container", "navigation", "layout", "data-display", "feedback", "overlay", "section", "user", "component"]
            for comp_type in type_order:
                if comp_type in components_by_type:
                    type_title = comp_type.replace("-", " ").title()
                    sections.append(f"\n### {type_title} Components:")
                    for comp_info in components_by_type[comp_type]:
                        name = comp_info.get("name", "Unknown")
                        import_path = comp_info.get("import_path", f"@/components/{name}")
                        purpose = comp_info.get("purpose", "")
                        sections.append(f"- {name}: import {{ {name} }} from '{import_path}' - {purpose}")
        
        # Add third-party libraries if available
        if ui_components.get("third_party"):
            sections.append("\n## Third-Party UI Libraries:")
            for lib in ui_components["third_party"]:
                if lib == "mui":
                    sections.append("- Material-UI: import { Button, Card, TextField, etc. } from '@mui/material'")
                elif lib == "antd":
                    sections.append("- Ant Design: import { Button, Card, Input, etc. } from 'antd'")
                elif lib == "chakra-ui":
                    sections.append("- Chakra UI: import { Button, Box, Input, etc. } from '@chakra-ui/react'")
        
        # Add utility functions
        utilities = context.get("available_imports", {}).get("utilities", {})
        if utilities:
            sections.append("\n## Utility Functions:")
            if utilities.get("cn"):
                sections.append("- cn: import { cn } from '@/lib/utils' - Class name utility for conditional classes")
            if utilities.get("clsx"):
                sections.append("- clsx: import clsx from 'clsx' - Class name concatenation")
            if utilities.get("classnames"):
                sections.append("- classNames: import classNames from 'classnames' - Dynamic class names")
        
        return "\n".join(sections)
    
    def _build_design_system_section(self, context: Dict) -> str:
        """Build design system section with actual project tokens"""
        sections = ["PROJECT DESIGN SYSTEM:"]
        
        tokens = context.get("design_tokens", {})
        
        # Colors
        if tokens.get("colors") or tokens.get("semantic_colors"):
            sections.append("\n## Color Palette:")
            if tokens.get("semantic_colors"):
                for color_name, color_value in tokens["semantic_colors"].items():
                    sections.append(f"- {color_name}: {color_value}")
            elif tokens.get("colors"):
                for color in tokens["colors"][:10]:  # Limit to top 10
                    sections.append(f"- {color}")
        
        # Spacing
        if tokens.get("spacing"):
            sections.append("\n## Spacing System:")
            spacing_values = tokens["spacing"][:8] if isinstance(tokens["spacing"], list) else list(tokens["spacing"].items())[:8]
            sections.append(f"Values: {', '.join(str(s) for s in spacing_values)}")
        
        # Typography
        if tokens.get("typography"):
            sections.append("\n## Typography:")
            for i, font in enumerate(tokens["typography"][:5]):
                sections.append(f"- {font}")
        
        # Styling approach
        styling = context.get("styling", "")
        if styling:
            sections.append(f"\n## Styling Approach: {styling}")
            if styling == "tailwind":
                sections.append("Use Tailwind CSS classes for all styling. Prefer utility classes over custom CSS.")
            elif styling == "styled-components":
                sections.append("Use styled-components for component styling. Create styled components for reusable elements.")
            elif styling == "css":
                sections.append("Use CSS modules or plain CSS files. Follow BEM naming convention for classes.")
        
        return "\n".join(sections)
    
    def _build_composition_examples(self, context: Dict) -> str:
        """Build examples showing how to compose existing components"""
        sections = ["COMPONENT COMPOSITION EXAMPLES:"]
        
        # Show common patterns
        sections.append("""
Example 1 - Composing a User Profile Card:
```tsx
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Avatar } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'

export function UserProfileCard({ user }) {
  return (
    <Card>
      <CardHeader>
        <Avatar src={user.avatar} alt={user.name} />
        <h3>{user.name}</h3>
      </CardHeader>
      <CardContent>
        <p>{user.bio}</p>
        <Button variant="outline">View Profile</Button>
      </CardContent>
    </Card>
  )
}
```

Example 2 - Building a Form with Existing Components:
```tsx
import { Form } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'

export function ContactForm() {
  return (
    <Form onSubmit={handleSubmit}>
      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" required />
      </div>
      <Button type="submit">Send Message</Button>
    </Form>
  )
}
```

ALWAYS COMPOSE LIKE THIS - Import existing components and combine them!""")
        
        return "\n".join(sections)


def create_enhanced_generator(project_path: str = None):
    """Factory function to create an enhanced generator with project analysis."""
    enhanced_builder = EnhancedPromptBuilder()

    if project_path:
        try:
            analysis = enhanced_builder.initialize_project_analysis(project_path)
            print(
                f"✅ Analyzed {len(analysis.get('components', []))} components for enhanced generation"
            )
        except Exception as e:
            print(f"⚠️ Could not analyze project: {e}")

    return enhanced_builder
