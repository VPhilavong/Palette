"""
Component Relationship Mapping system for understanding component dependencies
and relationships within a project.
"""

import ast
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class RelationshipType(Enum):
    """Types of relationships between components."""

    PARENT_CHILD = "parent_child"
    SIBLING = "sibling"
    DEPENDENCY = "dependency"
    COMPOSITION = "composition"
    STATE_SHARING = "state_sharing"
    ROUTE_BASED = "route_based"


@dataclass
class ComponentInfo:
    """Information about a component."""

    name: str
    path: str
    type: str  # page, layout, component, hook, util
    imports: List[str]
    exports: List[str]
    props: List[str]
    state_hooks: List[str]
    context_usage: List[str]
    children_components: List[str]
    parent_components: List[str] = None


@dataclass
class ComponentRelationship:
    """Represents a relationship between components."""

    source: str
    target: str
    relationship_type: RelationshipType
    context: str  # Additional context about the relationship
    strength: float = 1.0  # How strong/important the relationship is


@dataclass
class RelationshipContext:
    """Complete relationship context for a new component."""

    parent_layouts: List[ComponentInfo]
    sibling_components: List[ComponentInfo]
    child_components: List[ComponentInfo]
    state_dependencies: Dict[str, List[str]]  # State name -> components using it
    routing_implications: Dict[str, str]  # Route -> component mapping
    common_patterns: List[str]  # Common patterns detected
    suggested_location: str  # Where the new component should be placed


class ComponentRelationshipEngine:
    """Analyzes and maps component relationships in a project."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.components = {}
        self.relationships = []
        self.component_graph = defaultdict(list)
        self._scan_project()

    def _scan_project(self):
        """Scan the project for all components and their relationships."""
        # Common component directories
        component_dirs = [
            "components",
            "src/components",
            "app/components",
            "pages",
            "src/pages",
            "app",
            "layouts",
            "src/layouts",
        ]

        for dir_name in component_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists():
                self._scan_directory(dir_path)

    def _scan_directory(self, directory: Path):
        """Recursively scan a directory for components."""
        component_extensions = {".tsx", ".jsx", ".ts", ".js"}

        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in component_extensions:
                component_info = self._analyze_component(file_path)
                if component_info:
                    self.components[component_info.name] = component_info
                    self._extract_relationships(component_info)

    def _analyze_component(self, file_path: Path) -> Optional[ComponentInfo]:
        """Analyze a single component file."""
        try:
            content = file_path.read_text()

            # Skip test files and stories
            if ".test." in file_path.name or ".stories." in file_path.name:
                return None

            # Extract component name
            component_name = self._extract_component_name(content, file_path)
            if not component_name:
                return None

            # Determine component type
            component_type = self._determine_component_type(file_path)

            # Extract various aspects
            imports = self._extract_imports(content)
            exports = self._extract_exports(content)
            props = self._extract_props(content)
            hooks = self._extract_hooks(content)
            context_usage = self._extract_context_usage(content)
            children = self._extract_children_components(content, imports)

            return ComponentInfo(
                name=component_name,
                path=str(file_path.relative_to(self.project_path)),
                type=component_type,
                imports=imports,
                exports=exports,
                props=props,
                state_hooks=hooks,
                context_usage=context_usage,
                children_components=children,
            )
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_component_name(self, content: str, file_path: Path) -> Optional[str]:
        """Extract the main component name from the file."""
        # Try to find default export
        default_export = re.search(r"export\s+default\s+(?:function\s+)?(\w+)", content)
        if default_export:
            return default_export.group(1)

        # Try to find named component export
        named_export = re.search(r"export\s+(?:const|function)\s+(\w+)", content)
        if named_export:
            return named_export.group(1)

        # Fall back to filename
        return file_path.stem if file_path.stem not in ["index", "Index"] else None

    def _determine_component_type(self, file_path: Path) -> str:
        """Determine the type of component based on its location."""
        path_str = str(file_path).lower()

        if "pages" in path_str or "app/" in path_str:
            return "page"
        elif "layouts" in path_str:
            return "layout"
        elif "hooks" in path_str:
            return "hook"
        elif "utils" in path_str or "lib" in path_str:
            return "util"
        else:
            return "component"

    def _extract_imports(self, content: str) -> List[str]:
        """Extract all imports from the component."""
        imports = []
        import_pattern = r"import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+['\"]([^'\"]+)['\"]"

        for match in re.finditer(import_pattern, content):
            import_path = match.group(1)
            # Focus on relative imports (project components)
            if import_path.startswith("."):
                imports.append(import_path)

        return imports

    def _extract_exports(self, content: str) -> List[str]:
        """Extract all exports from the component."""
        exports = []

        # Default export
        if "export default" in content:
            exports.append("default")

        # Named exports
        named_exports = re.findall(
            r"export\s+(?:const|function|class)\s+(\w+)", content
        )
        exports.extend(named_exports)

        # Re-exports
        reexports = re.findall(r"export\s+{([^}]+)}", content)
        for reexport in reexports:
            exports.extend([e.strip() for e in reexport.split(",")])

        return list(set(exports))

    def _extract_props(self, content: str) -> List[str]:
        """Extract prop names from the component."""
        props = []

        # TypeScript interface
        interface_match = re.search(
            r"interface\s+\w*Props\s*{([^}]+)}", content, re.DOTALL
        )
        if interface_match:
            prop_content = interface_match.group(1)
            prop_names = re.findall(r"^\s*(\w+)\s*[?:]", prop_content, re.MULTILINE)
            props.extend(prop_names)

        # Type alias
        type_match = re.search(r"type\s+\w*Props\s*=\s*{([^}]+)}", content, re.DOTALL)
        if type_match:
            prop_content = type_match.group(1)
            prop_names = re.findall(r"^\s*(\w+)\s*[?:]", prop_content, re.MULTILINE)
            props.extend(prop_names)

        # Destructured props in function
        destructure_match = re.search(
            r"(?:function|const)\s+\w+\s*\(\s*{\s*([^}]+)\s*}", content
        )
        if destructure_match:
            prop_names = [
                p.strip().split(":")[0] for p in destructure_match.group(1).split(",")
            ]
            props.extend(prop_names)

        return list(set(props))

    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used in the component."""
        hooks = []
        hook_pattern = r"(use\w+)\s*\("

        for match in re.finditer(hook_pattern, content):
            hook_name = match.group(1)
            hooks.append(hook_name)

        return list(set(hooks))

    def _extract_context_usage(self, content: str) -> List[str]:
        """Extract React context usage."""
        contexts = []

        # useContext usage
        context_pattern = r"useContext\s*\(\s*(\w+)\s*\)"
        for match in re.finditer(context_pattern, content):
            contexts.append(match.group(1))

        # Context.Consumer pattern
        consumer_pattern = r"(\w+)\.Consumer"
        for match in re.finditer(consumer_pattern, content):
            contexts.append(match.group(1))

        return list(set(contexts))

    def _extract_children_components(
        self, content: str, imports: List[str]
    ) -> List[str]:
        """Extract components used as children."""
        children = []

        # Look for JSX component usage
        jsx_pattern = r"<(\w+)[\s/>]"
        for match in re.finditer(jsx_pattern, content):
            component = match.group(1)
            # Filter out HTML elements
            if component[0].isupper():
                children.append(component)

        return list(set(children))

    def _extract_relationships(self, component: ComponentInfo):
        """Extract relationships from component information."""
        # Parent-child relationships from imports and usage
        for child in component.children_components:
            if child in self.components:
                self.relationships.append(
                    ComponentRelationship(
                        source=component.name,
                        target=child,
                        relationship_type=RelationshipType.PARENT_CHILD,
                        context=f"{component.name} renders {child}",
                    )
                )
                self.component_graph[component.name].append(child)

        # State sharing relationships
        for context in component.context_usage:
            self.relationships.append(
                ComponentRelationship(
                    source=component.name,
                    target=context,
                    relationship_type=RelationshipType.STATE_SHARING,
                    context=f"{component.name} uses {context} context",
                )
            )

    def analyze_component_ecosystem(
        self, new_component_type: str, component_intent: str
    ) -> RelationshipContext:
        """Analyze where a new component fits in the existing ecosystem."""
        context = RelationshipContext(
            parent_layouts=[],
            sibling_components=[],
            child_components=[],
            state_dependencies={},
            routing_implications={},
            common_patterns=[],
            suggested_location="",
        )

        # Find likely parent components
        context.parent_layouts = self._find_likely_parents(
            new_component_type, component_intent
        )

        # Find sibling components
        context.sibling_components = self._find_siblings(
            new_component_type, component_intent
        )

        # Suggest child components
        context.child_components = self._suggest_children(
            new_component_type, component_intent
        )

        # Analyze state needs
        context.state_dependencies = self._analyze_state_needs(
            new_component_type, component_intent
        )

        # Check routing implications
        context.routing_implications = self._check_routing(
            new_component_type, component_intent
        )

        # Detect common patterns
        context.common_patterns = self._detect_patterns(new_component_type)

        # Suggest location
        context.suggested_location = self._suggest_location(
            new_component_type, component_intent
        )

        return context

    def _find_likely_parents(
        self, component_type: str, component_intent: str
    ) -> List[ComponentInfo]:
        """Find components that would likely contain this new component."""
        parents = []

        # Type-based parent detection
        if "hero" in component_type.lower():
            # Hero sections are typically in landing pages or home pages
            for name, comp in self.components.items():
                if comp.type == "page" and any(
                    keyword in comp.name.lower()
                    for keyword in ["home", "landing", "index"]
                ):
                    parents.append(comp)

        elif "header" in component_type.lower() or "nav" in component_type.lower():
            # Headers/nav are typically in layouts
            for name, comp in self.components.items():
                if comp.type == "layout":
                    parents.append(comp)

        elif "card" in component_type.lower() or "item" in component_type.lower():
            # Cards/items are typically in lists or grids
            for name, comp in self.components.items():
                if any(
                    keyword in comp.name.lower()
                    for keyword in ["list", "grid", "collection", "catalog"]
                ):
                    parents.append(comp)

        return parents[:3]  # Return top 3 most likely

    def _find_siblings(
        self, component_type: str, component_intent: str
    ) -> List[ComponentInfo]:
        """Find components that are commonly used together."""
        siblings = []

        # Common sibling patterns
        sibling_patterns = {
            "hero": ["features", "testimonials", "cta", "benefits"],
            "pricing": ["faq", "testimonials", "features", "comparison"],
            "header": ["footer", "sidebar", "navigation"],
            "productcard": ["productgrid", "productlist", "filters"],
            "form": ["validation", "success", "error"],
        }

        # Find matching pattern
        for pattern_key, sibling_names in sibling_patterns.items():
            if pattern_key in component_type.lower():
                for name, comp in self.components.items():
                    if any(sibling in comp.name.lower() for sibling in sibling_names):
                        siblings.append(comp)

        return siblings[:5]

    def _suggest_children(
        self, component_type: str, component_intent: str
    ) -> List[ComponentInfo]:
        """Suggest child components that this new component might need."""
        suggestions = []

        # Common child patterns
        child_patterns = {
            "hero": ["button", "image", "heading", "text"],
            "card": ["image", "title", "description", "button"],
            "form": ["input", "button", "label", "error"],
            "pricing": ["pricingcard", "feature", "button"],
            "navigation": ["navlink", "dropdown", "logo"],
        }

        # Find existing components that match patterns
        for pattern_key, child_names in child_patterns.items():
            if pattern_key in component_type.lower():
                for name, comp in self.components.items():
                    if any(child in comp.name.lower() for child in child_names):
                        suggestions.append(comp)

        return suggestions[:6]

    def _analyze_state_needs(
        self, component_type: str, component_intent: str
    ) -> Dict[str, List[str]]:
        """Analyze what state/context the new component might need."""
        state_needs = defaultdict(list)

        # Common state patterns
        if "dashboard" in component_type.lower() or "admin" in component_type.lower():
            state_needs["AuthContext"] = ["user", "permissions", "isAuthenticated"]
            state_needs["DataContext"] = ["metrics", "filters", "timeRange"]

        elif "cart" in component_type.lower() or "checkout" in component_type.lower():
            state_needs["CartContext"] = ["items", "total", "quantity"]
            state_needs["UserContext"] = ["user", "addresses", "paymentMethods"]

        elif "theme" in component_intent.lower() or "dark" in component_intent.lower():
            state_needs["ThemeContext"] = ["theme", "toggleTheme"]

        # Check what contexts already exist in the project
        existing_contexts = set()
        for comp in self.components.values():
            existing_contexts.update(comp.context_usage)

        # Filter to only existing contexts
        filtered_state = {}
        for context, needs in state_needs.items():
            if context in existing_contexts or any(
                ctx for ctx in existing_contexts if context.lower() in ctx.lower()
            ):
                filtered_state[context] = needs

        return filtered_state

    def _check_routing(
        self, component_type: str, component_intent: str
    ) -> Dict[str, str]:
        """Check routing implications for the new component."""
        routing = {}

        # Page-level components might need routes
        if any(
            keyword in component_type.lower() for keyword in ["page", "view", "screen"]
        ):
            # Suggest route based on component type
            if "pricing" in component_type.lower():
                routing["/pricing"] = component_type
            elif "about" in component_type.lower():
                routing["/about"] = component_type
            elif "contact" in component_type.lower():
                routing["/contact"] = component_type
            elif "dashboard" in component_type.lower():
                routing["/dashboard"] = component_type

        return routing

    def _detect_patterns(self, component_type: str) -> List[str]:
        """Detect common patterns used in similar components."""
        patterns = []

        # Find similar existing components
        similar_components = []
        for name, comp in self.components.items():
            if any(
                keyword in name.lower() for keyword in component_type.lower().split()
            ):
                similar_components.append(comp)

        if similar_components:
            # Analyze common hooks
            common_hooks = defaultdict(int)
            for comp in similar_components:
                for hook in comp.state_hooks:
                    common_hooks[hook] += 1

            # Add most common patterns
            for hook, count in sorted(
                common_hooks.items(), key=lambda x: x[1], reverse=True
            )[:3]:
                if (
                    count > len(similar_components) / 2
                ):  # Used in >50% of similar components
                    patterns.append(f"Commonly uses {hook}")

            # Check for common props
            common_props = defaultdict(int)
            for comp in similar_components:
                for prop in comp.props:
                    common_props[prop] += 1

            for prop, count in sorted(
                common_props.items(), key=lambda x: x[1], reverse=True
            )[:3]:
                if count > len(similar_components) / 2:
                    patterns.append(f"Common prop: {prop}")

        return patterns

    def _suggest_location(self, component_type: str, component_intent: str) -> str:
        """Suggest where the new component should be placed."""
        # Analyze existing component locations
        type_locations = defaultdict(list)

        for comp in self.components.values():
            # Extract directory from path
            parts = Path(comp.path).parts
            if len(parts) > 1:
                directory = "/".join(parts[:-1])
                type_locations[comp.type].append(directory)

        # Determine suggested location based on type
        if "page" in component_type.lower():
            if type_locations["page"]:
                return max(
                    set(type_locations["page"]), key=type_locations["page"].count
                )
            return "src/pages" if (self.project_path / "src").exists() else "pages"

        elif "layout" in component_type.lower():
            if type_locations["layout"]:
                return max(
                    set(type_locations["layout"]), key=type_locations["layout"].count
                )
            return "src/layouts" if (self.project_path / "src").exists() else "layouts"

        else:
            # Regular components
            if type_locations["component"]:
                # Group by feature if possible
                for location in type_locations["component"]:
                    if any(
                        keyword in location.lower()
                        for keyword in component_type.lower().split()
                    ):
                        return location

                # Default to most common component location
                return max(
                    set(type_locations["component"]),
                    key=type_locations["component"].count,
                )

            return (
                "src/components"
                if (self.project_path / "src").exists()
                else "components"
            )

    def get_relationship_summary(self, context: RelationshipContext) -> str:
        """Generate a human-readable summary of relationships."""
        summary_parts = []

        if context.parent_layouts:
            parents = ", ".join(p.name for p in context.parent_layouts[:2])
            summary_parts.append(f"Likely parents: {parents}")

        if context.sibling_components:
            siblings = ", ".join(s.name for s in context.sibling_components[:3])
            summary_parts.append(f"Common siblings: {siblings}")

        if context.suggested_location:
            summary_parts.append(f"Suggested location: {context.suggested_location}")

        if context.common_patterns:
            summary_parts.append(f"Patterns: {', '.join(context.common_patterns[:2])}")

        return (
            " | ".join(summary_parts)
            if summary_parts
            else "No clear relationships found"
        )
