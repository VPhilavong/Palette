"""
Component Relationship Mapper - Understanding how UI components work together.
Analyzes component dependencies, composition patterns, and semantic relationships.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .ui_pattern_ontology import get_ui_pattern_ontology, UIPattern, ComplexityLevel
from ..errors.decorators import handle_errors


class RelationshipType(Enum):
    """Types of relationships between components."""
    
    CONTAINS = "contains"           # Parent contains child (Form contains Input)
    REQUIRES = "requires"           # Component requires another (Modal requires Button)
    ENHANCES = "enhances"          # Component enhances another (Label enhances Input)
    CONFLICTS = "conflicts"        # Components shouldn't be used together
    ALTERNATIVES = "alternatives"   # Components are alternative solutions
    COLLABORATES = "collaborates"  # Components work well together
    EXTENDS = "extends"            # Component extends another's functionality


@dataclass
class ComponentRelationship:
    """A relationship between two components."""
    
    source_component: str
    target_component: str
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0, how strong the relationship is
    context: Optional[str] = None  # When this relationship applies
    reason: Optional[str] = None   # Why this relationship exists
    examples: List[str] = field(default_factory=list)


@dataclass
class CompositionPattern:
    """A pattern showing how multiple components are composed together."""
    
    name: str
    description: str
    components: List[str]  # List of component names
    structure: Dict[str, Any]  # Hierarchical structure
    use_cases: List[str]
    code_example: Optional[str] = None
    best_practices: List[str] = field(default_factory=list)


@dataclass
class ComponentAnalysis:
    """Analysis of a component's relationships and usage patterns."""
    
    component_name: str
    complexity_level: ComplexityLevel
    typical_children: List[str] = field(default_factory=list)
    typical_parents: List[str] = field(default_factory=list)
    required_props: List[str] = field(default_factory=list)
    optional_props: List[str] = field(default_factory=list)
    state_dependencies: List[str] = field(default_factory=list)
    styling_dependencies: List[str] = field(default_factory=list)
    accessibility_requirements: List[str] = field(default_factory=list)


class ComponentRelationshipMapper:
    """
    Maps and analyzes relationships between UI components.
    Helps LLMs understand component composition and dependencies.
    """
    
    def __init__(self):
        self.relationships: List[ComponentRelationship] = []
        self.composition_patterns: List[CompositionPattern] = []
        self.component_analyses: Dict[str, ComponentAnalysis] = {}
        self.ontology = get_ui_pattern_ontology()
        
        self._initialize_relationships()
        self._initialize_composition_patterns()
        self._build_component_analyses()
    
    def _initialize_relationships(self):
        """Initialize common component relationships."""
        
        # Form relationships
        self._add_relationship("Form", "Input", RelationshipType.CONTAINS, 0.9,
                             "Forms typically contain multiple input fields")
        self._add_relationship("Form", "Button", RelationshipType.CONTAINS, 0.8,
                             "Forms need submit and cancel buttons")
        self._add_relationship("Form", "Label", RelationshipType.CONTAINS, 0.7,
                             "Form inputs should have labels")
        
        # Input relationships
        self._add_relationship("Input", "Label", RelationshipType.REQUIRES, 0.9,
                             "All inputs should have associated labels for accessibility")
        self._add_relationship("Input", "ErrorMessage", RelationshipType.ENHANCES, 0.7,
                             "Inputs benefit from validation feedback")
        self._add_relationship("Input", "HelperText", RelationshipType.ENHANCES, 0.5,
                             "Inputs can have helper text for guidance")
        
        # Card relationships
        self._add_relationship("Card", "CardHeader", RelationshipType.CONTAINS, 0.8,
                             "Cards often have headers")
        self._add_relationship("Card", "CardContent", RelationshipType.CONTAINS, 0.9,
                             "Cards contain main content")
        self._add_relationship("Card", "CardFooter", RelationshipType.CONTAINS, 0.6,
                             "Cards may have footers with actions")
        self._add_relationship("Card", "Button", RelationshipType.CONTAINS, 0.7,
                             "Cards often contain action buttons")
        
        # Modal relationships
        self._add_relationship("Modal", "ModalHeader", RelationshipType.CONTAINS, 0.8,
                             "Modals should have clear headers")
        self._add_relationship("Modal", "ModalContent", RelationshipType.CONTAINS, 0.9,
                             "Modals contain main content")
        self._add_relationship("Modal", "ModalFooter", RelationshipType.CONTAINS, 0.7,
                             "Modals typically have action buttons in footer")
        self._add_relationship("Modal", "Button", RelationshipType.REQUIRES, 0.9,
                             "Modals need close/cancel buttons")
        self._add_relationship("Modal", "Overlay", RelationshipType.REQUIRES, 0.9,
                             "Modals require background overlay")
        
        # Navigation relationships
        self._add_relationship("Navbar", "Logo", RelationshipType.CONTAINS, 0.8,
                             "Navigation bars typically include branding")
        self._add_relationship("Navbar", "NavItem", RelationshipType.CONTAINS, 0.9,
                             "Navigation bars contain navigation items")
        self._add_relationship("Navbar", "UserMenu", RelationshipType.CONTAINS, 0.7,
                             "Navigation bars often include user menus")
        self._add_relationship("Navbar", "SearchInput", RelationshipType.CONTAINS, 0.5,
                             "Navigation may include search functionality")
        
        # Table relationships
        self._add_relationship("DataTable", "TableHeader", RelationshipType.CONTAINS, 0.9,
                             "Tables require headers for accessibility")
        self._add_relationship("DataTable", "TableRow", RelationshipType.CONTAINS, 0.9,
                             "Tables contain data rows")
        self._add_relationship("DataTable", "TableCell", RelationshipType.CONTAINS, 0.9,
                             "Tables are made up of cells")
        self._add_relationship("DataTable", "Pagination", RelationshipType.ENHANCES, 0.7,
                             "Tables with many rows benefit from pagination")
        self._add_relationship("DataTable", "SearchInput", RelationshipType.ENHANCES, 0.6,
                             "Tables can be enhanced with search functionality")
        
        # Layout relationships
        self._add_relationship("SidebarLayout", "Sidebar", RelationshipType.CONTAINS, 0.9,
                             "Sidebar layouts contain a sidebar")
        self._add_relationship("SidebarLayout", "MainContent", RelationshipType.CONTAINS, 0.9,
                             "Sidebar layouts have main content area")
        self._add_relationship("SidebarLayout", "Header", RelationshipType.CONTAINS, 0.7,
                             "Sidebar layouts often have a header")
        
        # Dropdown relationships
        self._add_relationship("Dropdown", "DropdownTrigger", RelationshipType.REQUIRES, 0.9,
                             "Dropdowns need a trigger element")
        self._add_relationship("Dropdown", "DropdownContent", RelationshipType.REQUIRES, 0.9,
                             "Dropdowns contain the dropdown content")
        self._add_relationship("Dropdown", "DropdownItem", RelationshipType.CONTAINS, 0.8,
                             "Dropdowns contain selectable items")
        
        # Conflict relationships
        self._add_relationship("Modal", "Drawer", RelationshipType.CONFLICTS, 0.8,
                             "Don't use modals and drawers simultaneously")
        self._add_relationship("Tooltip", "Popover", RelationshipType.ALTERNATIVES, 0.7,
                             "Tooltips and popovers serve similar purposes")
        
        # Enhancement relationships
        self._add_relationship("Button", "LoadingSpinner", RelationshipType.ENHANCES, 0.7,
                             "Buttons can show loading states")
        self._add_relationship("Button", "Icon", RelationshipType.ENHANCES, 0.6,
                             "Buttons can include icons")
        self._add_relationship("Input", "Icon", RelationshipType.ENHANCES, 0.5,
                             "Inputs can have decorative or functional icons")
    
    def _add_relationship(self, source: str, target: str, rel_type: RelationshipType, 
                         strength: float, reason: str = None):
        """Add a component relationship."""
        relationship = ComponentRelationship(
            source_component=source,
            target_component=target,
            relationship_type=rel_type,
            strength=strength,
            reason=reason
        )
        self.relationships.append(relationship)
    
    def _initialize_composition_patterns(self):
        """Initialize common composition patterns."""
        
        # Login Form Pattern
        login_form_pattern = CompositionPattern(
            name="LoginForm",
            description="Standard login form with email/username and password fields",
            components=["Form", "TextInput", "PasswordInput", "Button", "Link", "Checkbox"],
            structure={
                "Form": {
                    "children": [
                        {"TextInput": {"props": ["label=Email", "type=email", "required=true"]}},
                        {"PasswordInput": {"props": ["label=Password", "required=true"]}},
                        {"Checkbox": {"props": ["label=Remember me"]}},
                        {"Button": {"props": ["type=submit", "variant=primary"], "children": "Sign In"}},
                        {"Link": {"props": ["href=/forgot-password"], "children": "Forgot Password?"}}
                    ]
                }
            },
            use_cases=["User authentication", "Admin login", "App sign-in"],
            best_practices=[
                "Include password visibility toggle",
                "Provide forgot password link",
                "Show clear error messages",
                "Support keyboard navigation"
            ]
        )
        self.composition_patterns.append(login_form_pattern)
        
        # Product Card Pattern
        product_card_pattern = CompositionPattern(
            name="ProductCard",
            description="E-commerce product display card with image, details, and actions",
            components=["Card", "Image", "Text", "Button", "Badge", "Rating"],
            structure={
                "Card": {
                    "children": [
                        {"Image": {"props": ["src", "alt"], "role": "product-image"}},
                        {"Badge": {"props": ["variant=sale"], "content": "Sale", "conditional": True}},
                        {"CardContent": {
                            "children": [
                                {"Text": {"variant": "h3", "content": "Product Name"}},
                                {"Rating": {"props": ["value", "readonly=true"]}},
                                {"Text": {"variant": "price", "content": "Price"}},
                                {"Text": {"variant": "description", "content": "Short description"}}
                            ]
                        }},
                        {"CardFooter": {
                            "children": [
                                {"Button": {"variant": "primary", "content": "Add to Cart"}},
                                {"Button": {"variant": "outline", "content": "Quick View"}}
                            ]
                        }}
                    ]
                }
            },
            use_cases=["E-commerce listings", "Product catalogs", "Marketplace displays"],
            best_practices=[
                "Use consistent image aspect ratios",
                "Include accessibility labels",
                "Show clear pricing information",
                "Provide multiple action options"
            ]
        )
        self.composition_patterns.append(product_card_pattern)
        
        # Dashboard Header Pattern
        dashboard_header_pattern = CompositionPattern(
            name="DashboardHeader",
            description="Application header with navigation, search, and user controls",
            components=["Header", "Logo", "SearchInput", "Button", "Avatar", "Dropdown", "Badge"],
            structure={
                "Header": {
                    "layout": "flex justify-between items-center",
                    "children": [
                        {"div": {
                            "className": "flex items-center gap-4",
                            "children": [
                                {"Logo": {"props": ["size=md"]}},
                                {"SearchInput": {"props": ["placeholder=Search...", "size=md"]}}
                            ]
                        }},
                        {"div": {
                            "className": "flex items-center gap-2",
                            "children": [
                                {"Button": {"variant": "ghost", "size": "sm", "children": "Notifications", "badge": True}},
                                {"Dropdown": {
                                    "trigger": {"Avatar": {"props": ["src", "alt=User"]}},
                                    "content": ["Profile", "Settings", "Logout"]
                                }}
                            ]
                        }}
                    ]
                }
            },
            use_cases=["Admin dashboards", "Application headers", "SaaS interfaces"],
            best_practices=[
                "Keep branding prominent but not overwhelming",
                "Make search easily accessible",
                "Include notification indicators",
                "Provide easy access to user settings"
            ]
        )
        self.composition_patterns.append(dashboard_header_pattern)
        
        # Data Table with Filters Pattern
        data_table_pattern = CompositionPattern(
            name="FilterableDataTable",
            description="Data table with search, filtering, and pagination controls",
            components=["Card", "SearchInput", "Select", "DataTable", "Pagination", "Button"],
            structure={
                "Card": {
                    "children": [
                        {"CardHeader": {
                            "children": [
                                {"div": {
                                    "className": "flex justify-between items-center",
                                    "children": [
                                        {"Text": {"variant": "h2", "content": "Data Table"}},
                                        {"Button": {"variant": "primary", "content": "Add New"}}
                                    ]
                                }}
                            ]
                        }},
                        {"CardContent": {
                            "children": [
                                {"div": {
                                    "className": "flex gap-4 mb-4",
                                    "children": [
                                        {"SearchInput": {"props": ["placeholder=Search records..."]}},
                                        {"Select": {"props": ["placeholder=Filter by category"]}},
                                        {"Select": {"props": ["placeholder=Sort by"]}}
                                    ]
                                }},
                                {"DataTable": {"props": ["data", "columns", "sortable=true"]}},
                                {"Pagination": {"props": ["currentPage", "totalPages", "onPageChange"]}}
                            ]
                        }}
                    ]
                }
            },
            use_cases=["Admin tables", "Data management", "Report displays"],
            best_practices=[
                "Provide multiple filtering options",
                "Include bulk actions when appropriate",
                "Show loading states during data fetching",
                "Implement proper sorting and pagination"
            ]
        )
        self.composition_patterns.append(data_table_pattern)
    
    def _build_component_analyses(self):
        """Build detailed analyses for each component."""
        
        # Get all patterns from ontology
        for pattern_name, pattern in self.ontology.patterns.items():
            analysis = ComponentAnalysis(
                component_name=pattern_name,
                complexity_level=pattern.complexity,
                required_props=[prop["name"] for prop in pattern.typical_props if prop.get("required", False)],
                optional_props=[prop["name"] for prop in pattern.typical_props if not prop.get("required", False)],
                accessibility_requirements=[req.requirement for req in pattern.accessibility_requirements]
            )
            
            # Find typical children and parents from relationships
            for rel in self.relationships:
                if rel.source_component == pattern_name and rel.relationship_type == RelationshipType.CONTAINS:
                    analysis.typical_children.append(rel.target_component)
                elif rel.target_component == pattern_name and rel.relationship_type == RelationshipType.CONTAINS:
                    analysis.typical_parents.append(rel.source_component)
            
            self.component_analyses[pattern_name] = analysis
    
    @handle_errors(reraise=True)
    def analyze_component_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze a component request to suggest related components and composition patterns.
        
        Args:
            user_request: User's component request
            
        Returns:
            Analysis with component suggestions and composition recommendations
        """
        request_lower = user_request.lower()
        
        # Find primary component being requested
        primary_components = self._identify_primary_components(user_request)
        
        # Find related components for each primary component
        suggestions = {}
        for component in primary_components:
            related = self.get_related_components(component)
            suggestions[component] = {
                "related_components": related,
                "composition_patterns": self._find_matching_patterns(component),
                "typical_structure": self._get_typical_structure(component),
                "best_practices": self._get_component_best_practices(component)
            }
        
        # Find matching composition patterns
        matching_patterns = []
        for pattern in self.composition_patterns:
            if any(comp.lower() in request_lower for comp in pattern.components):
                matching_patterns.append({
                    "name": pattern.name,
                    "description": pattern.description,
                    "components": pattern.components,
                    "use_cases": pattern.use_cases,
                    "relevance_score": self._calculate_pattern_relevance(pattern, user_request)
                })
        
        # Sort patterns by relevance
        matching_patterns.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {
            "primary_components": primary_components,
            "component_suggestions": suggestions,
            "matching_patterns": matching_patterns[:3],  # Top 3 most relevant
            "composition_recommendations": self._get_composition_recommendations(user_request),
            "architectural_considerations": self._get_architectural_considerations(primary_components)
        }
    
    def _identify_primary_components(self, user_request: str) -> List[str]:
        """Identify the main components being requested."""
        request_lower = user_request.lower()
        primary_components = []
        
        # Check against known component patterns
        for pattern_name in self.ontology.patterns.keys():
            if pattern_name.lower() in request_lower:
                primary_components.append(pattern_name)
        
        # Check for common component keywords
        component_keywords = {
            "form": "Form",
            "table": "DataTable",
            "card": "Card",
            "button": "Button",
            "modal": "Modal",
            "navigation": "Navbar",
            "sidebar": "Sidebar",
            "input": "TextInput",
            "dashboard": "Dashboard"
        }
        
        for keyword, component in component_keywords.items():
            if keyword in request_lower and component not in primary_components:
                primary_components.append(component)
        
        return primary_components if primary_components else ["Card"]  # Default fallback
    
    def get_related_components(self, component_name: str) -> Dict[str, List[str]]:
        """Get components related to the specified component.""" 
        related = {
            "required": [],
            "enhances": [],
            "contains": [],
            "alternatives": [],
            "collaborates": []
        }
        
        for rel in self.relationships:
            if rel.source_component == component_name:
                if rel.relationship_type == RelationshipType.REQUIRES:
                    related["required"].append(rel.target_component)
                elif rel.relationship_type == RelationshipType.ENHANCES:
                    related["enhances"].append(rel.target_component)
                elif rel.relationship_type == RelationshipType.CONTAINS:
                    related["contains"].append(rel.target_component)
                elif rel.relationship_type == RelationshipType.ALTERNATIVES:
                    related["alternatives"].append(rel.target_component)
                elif rel.relationship_type == RelationshipType.COLLABORATES:
                    related["collaborates"].append(rel.target_component)
        
        return related
    
    def _find_matching_patterns(self, component_name: str) -> List[Dict[str, Any]]:
        """Find composition patterns that include the specified component."""
        matching = []
        
        for pattern in self.composition_patterns:
            if component_name in pattern.components:
                matching.append({
                    "name": pattern.name,
                    "description": pattern.description,
                    "structure": pattern.structure,
                    "use_cases": pattern.use_cases
                })
        
        return matching
    
    def _get_typical_structure(self, component_name: str) -> Dict[str, Any]:
        """Get typical structure for a component."""
        analysis = self.component_analyses.get(component_name)
        if not analysis:
            return {}
        
        return {
            "typical_children": analysis.typical_children,
            "typical_parents": analysis.typical_parents,
            "required_props": analysis.required_props,
            "optional_props": analysis.optional_props,
            "complexity_level": analysis.complexity_level.value
        }
    
    def _get_component_best_practices(self, component_name: str) -> List[str]:
        """Get best practices for a component."""
        pattern = self.ontology.get_pattern(component_name)
        if pattern:
            return pattern.best_practices[:5]  # Top 5 best practices
        return []
    
    def _calculate_pattern_relevance(self, pattern: CompositionPattern, user_request: str) -> float:
        """Calculate how relevant a composition pattern is to the user request."""
        request_lower = user_request.lower()
        score = 0.0
        
        # Check pattern name match
        if pattern.name.lower() in request_lower:
            score += 0.4
        
        # Check component matches
        component_matches = sum(1 for comp in pattern.components if comp.lower() in request_lower)
        score += (component_matches / len(pattern.components)) * 0.3
        
        # Check use case matches
        use_case_matches = sum(1 for use_case in pattern.use_cases 
                              if any(word in request_lower for word in use_case.lower().split()))
        score += (use_case_matches / len(pattern.use_cases)) * 0.3
        
        return min(1.0, score)
    
    def _get_composition_recommendations(self, user_request: str) -> List[str]:
        """Get composition recommendations based on the request."""
        request_lower = user_request.lower()
        recommendations = []
        
        # Form-related recommendations
        if "form" in request_lower:
            recommendations.extend([
                "Include proper form validation with clear error messaging",
                "Use consistent input spacing and alignment", 
                "Provide submit and cancel actions",
                "Consider multi-step forms for complex data collection"
            ])
        
        # Dashboard recommendations
        if "dashboard" in request_lower:
            recommendations.extend([
                "Organize information by importance and frequency of use",
                "Use consistent card layouts for different data types",
                "Include filtering and search capabilities",
                "Provide customization options when possible"
            ])
        
        # Table recommendations
        if "table" in request_lower:
            recommendations.extend([
                "Implement sorting and filtering for better data navigation",
                "Use pagination for large datasets",
                "Include bulk actions when appropriate",
                "Ensure mobile responsiveness with column prioritization"
            ])
        
        # Navigation recommendations
        if any(word in request_lower for word in ["nav", "menu", "header"]):
            recommendations.extend([
                "Maintain consistent navigation across the application",
                "Show current location clearly",
                "Implement responsive navigation patterns",
                "Include search functionality when appropriate"
            ])
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_architectural_considerations(self, components: List[str]) -> List[str]:
        """Get architectural considerations for the requested components."""
        considerations = []
        
        # Check complexity levels
        complexity_levels = []
        for component in components:
            analysis = self.component_analyses.get(component)
            if analysis:
                complexity_levels.append(analysis.complexity_level)
        
        if any(level in [ComplexityLevel.ORGANISM, ComplexityLevel.TEMPLATE, ComplexityLevel.PAGE] 
               for level in complexity_levels):
            considerations.extend([
                "Consider code splitting for large components",
                "Implement proper error boundaries",
                "Plan for loading and empty states",
                "Design with responsive behavior in mind"
            ])
        
        if "Form" in components:
            considerations.extend([
                "Implement proper form state management",
                "Consider using form libraries like React Hook Form",
                "Plan for client and server-side validation"
            ])
        
        if "DataTable" in components:
            considerations.extend([
                "Consider virtualization for large datasets",
                "Implement proper sorting and filtering architecture",
                "Plan for data loading and caching strategies"
            ])
        
        return considerations[:5]  # Top 5 considerations
    
    def get_composition_pattern(self, pattern_name: str) -> Optional[CompositionPattern]:
        """Get a specific composition pattern by name."""
        for pattern in self.composition_patterns:
            if pattern.name == pattern_name:
                return pattern
        return None
    
    def suggest_component_architecture(self, components: List[str]) -> Dict[str, Any]:
        """Suggest how to architect multiple components together."""
        suggestions = {
            "component_hierarchy": {},
            "state_management": [],
            "data_flow": [],
            "styling_approach": [],
            "testing_strategy": []
        }
        
        # Analyze component relationships
        for component in components:
            related = self.get_related_components(component)
            suggestions["component_hierarchy"][component] = {
                "children": related.get("contains", []),
                "dependencies": related.get("required", []),
                "enhancements": related.get("enhances", [])
            }
        
        # State management suggestions
        if len(components) > 3:
            suggestions["state_management"].append("Consider using a state management library")
        if any(comp in ["Form", "DataTable", "Modal"] for comp in components):
            suggestions["state_management"].append("Implement proper form/data state handling")
        
        # Data flow suggestions
        if "DataTable" in components:
            suggestions["data_flow"].append("Plan for data fetching, caching, and updates")
        if "Form" in components:
            suggestions["data_flow"].append("Design form submission and validation flow")
        
        return suggestions


# Global mapper instance
_mapper_instance = None

def get_component_relationship_mapper() -> ComponentRelationshipMapper:
    """Get the global component relationship mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = ComponentRelationshipMapper()
    return _mapper_instance