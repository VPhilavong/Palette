"""
UI Pattern Ontology - Structured knowledge base of UI/UX patterns and their relationships.
Provides semantic understanding of component patterns, interactions, and design principles.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..errors import GenerationError
from ..errors.decorators import handle_errors


class PatternCategory(Enum):
    """Categories of UI patterns."""
    
    LAYOUT = "layout"
    NAVIGATION = "navigation"
    INPUT = "input"
    FEEDBACK = "feedback"
    DISPLAY = "display"
    INTERACTION = "interaction"
    CONTENT = "content"
    UTILITY = "utility"


class ComplexityLevel(Enum):
    """Complexity levels for UI patterns."""
    
    ATOMIC = "atomic"        # Basic building blocks (Button, Input)
    MOLECULAR = "molecular"  # Simple combinations (SearchBox, CardHeader)
    ORGANISM = "organism"    # Complex components (Header, ProductGrid)
    TEMPLATE = "template"    # Page-level structures
    PAGE = "page"           # Complete pages


@dataclass
class DesignPrinciple:
    """A design principle associated with a pattern."""
    
    name: str
    description: str
    importance: str  # "critical", "important", "recommended"
    examples: List[str] = field(default_factory=list)


@dataclass
class AccessibilityRequirement:
    """Accessibility requirement for a pattern."""
    
    wcag_guideline: str
    level: str  # "A", "AA", "AAA"
    requirement: str
    implementation: str
    testing_method: str = ""


@dataclass
class InteractionPattern:
    """Interaction pattern for a UI component."""
    
    trigger: str  # "click", "hover", "focus", "keyboard", etc.
    response: str
    states: List[str] = field(default_factory=list)
    animations: List[str] = field(default_factory=list)


@dataclass
class UIPattern:
    """A structured UI pattern with comprehensive metadata."""
    
    name: str
    category: PatternCategory
    complexity: ComplexityLevel
    description: str
    purpose: str
    
    # Relationships
    parent_patterns: List[str] = field(default_factory=list)
    child_patterns: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    
    # Design & UX
    design_principles: List[DesignPrinciple] = field(default_factory=list)
    interaction_patterns: List[InteractionPattern] = field(default_factory=list)
    accessibility_requirements: List[AccessibilityRequirement] = field(default_factory=list)
    
    # Technical
    typical_props: List[Dict[str, Any]] = field(default_factory=list)
    required_dependencies: List[str] = field(default_factory=list)
    common_variations: List[str] = field(default_factory=list)
    
    # Context
    usage_contexts: List[str] = field(default_factory=list)
    antipatterns: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    
    # Implementation
    framework_implementations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    styling_considerations: List[str] = field(default_factory=list)
    
    # Metadata
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class UIPatternOntology:
    """
    Comprehensive knowledge base of UI patterns with semantic relationships.
    """
    
    def __init__(self):
        self.patterns: Dict[str, UIPattern] = {}
        self.category_index: Dict[PatternCategory, List[str]] = {}
        self.complexity_index: Dict[ComplexityLevel, List[str]] = {}
        self.keyword_index: Dict[str, List[str]] = {}
        
        self._initialize_patterns()
        self._build_indexes()
    
    def _initialize_patterns(self):
        """Initialize the ontology with common UI patterns."""
        
        # Atomic Level Patterns
        self._add_button_patterns()
        self._add_input_patterns()
        self._add_feedback_patterns()
        
        # Molecular Level Patterns
        self._add_form_patterns()
        self._add_card_patterns()
        self._add_navigation_patterns()
        
        # Organism Level Patterns
        self._add_layout_patterns()
        self._add_data_display_patterns()
        
        # Template Level Patterns
        self._add_page_patterns()
    
    def _add_button_patterns(self):
        """Add button-related patterns."""
        
        button_pattern = UIPattern(
            name="Button",
            category=PatternCategory.INTERACTION,
            complexity=ComplexityLevel.ATOMIC,
            description="Interactive element that triggers actions when activated",
            purpose="Enable user actions and navigation",
            
            design_principles=[
                DesignPrinciple(
                    name="Clarity",
                    description="Button purpose should be immediately clear",
                    importance="critical",
                    examples=["Use action verbs", "Avoid ambiguous labels like 'OK'"]
                ),
                DesignPrinciple(
                    name="Accessibility",
                    description="Must be keyboard accessible and screen reader friendly",
                    importance="critical",
                    examples=["Focus states", "ARIA labels", "Sufficient contrast"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="click",
                    response="Execute action",
                    states=["default", "hover", "active", "focus", "disabled"],
                    animations=["scale", "color-transition", "loading-spinner"]
                ),
                InteractionPattern(
                    trigger="keyboard",
                    response="Execute action on Enter/Space",
                    states=["focus", "active"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="2.1.1",
                    level="A",
                    requirement="Keyboard accessible",
                    implementation="Handle Enter and Space key events"
                ),
                AccessibilityRequirement(
                    wcag_guideline="1.4.3",
                    level="AA",
                    requirement="Sufficient color contrast",
                    implementation="Minimum 4.5:1 contrast ratio"
                )
            ],
            
            typical_props=[
                {"name": "variant", "type": "string", "options": ["primary", "secondary", "outline", "ghost"]},
                {"name": "size", "type": "string", "options": ["sm", "md", "lg"]},
                {"name": "disabled", "type": "boolean"},
                {"name": "loading", "type": "boolean"},
                {"name": "onClick", "type": "function"},
                {"name": "children", "type": "ReactNode"}
            ],
            
            common_variations=["IconButton", "ToggleButton", "SplitButton", "DropdownButton"],
            
            usage_contexts=[
                "Forms (submit, cancel)",
                "Navigation (links, menu items)",
                "Actions (delete, save, edit)",
                "Modals (confirm, cancel)"
            ],
            
            antipatterns=[
                "Using buttons for non-interactive elements",
                "Missing focus states",
                "Unclear or generic labels",
                "Too many primary buttons in one area"
            ],
            
            best_practices=[
                "Use descriptive action-oriented labels",
                "Implement all interaction states",
                "Provide immediate feedback on click",
                "Group related actions together",
                "Use consistent sizing and spacing"
            ],
            
            framework_implementations={
                "react": {
                    "base_component": "button",
                    "common_libraries": ["@radix-ui/react-button", "react-aria"],
                    "styling_approaches": ["tailwind-classes", "css-modules", "styled-components"]
                }
            },
            
            styling_considerations=[
                "Ensure sufficient touch target size (44px minimum)",
                "Provide clear visual hierarchy",
                "Use consistent spacing and alignment",
                "Consider loading and disabled states"
            ],
            
            keywords=["button", "cta", "action", "click", "submit", "interactive"],
            tags=["atomic", "interaction", "form", "navigation"]
        )
        
        self.patterns["Button"] = button_pattern
    
    def _add_input_patterns(self):
        """Add input-related patterns."""
        
        text_input_pattern = UIPattern(
            name="TextInput",
            category=PatternCategory.INPUT,
            complexity=ComplexityLevel.ATOMIC,
            description="Field for text data entry",
            purpose="Collect textual information from users",
            
            design_principles=[
                DesignPrinciple(
                    name="Clarity",
                    description="Purpose and format should be clear",
                    importance="critical",
                    examples=["Clear labels", "Helpful placeholders", "Format hints"]
                ),
                DesignPrinciple(
                    name="Feedback",
                    description="Provide immediate validation feedback",
                    importance="important",
                    examples=["Real-time validation", "Error messages", "Success indicators"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="focus",
                    response="Show active state and cursor",
                    states=["default", "focus", "error", "disabled", "readonly"]
                ),
                InteractionPattern(
                    trigger="input",
                    response="Update value and validate",
                    states=["typing", "valid", "invalid"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="3.3.2",
                    level="A",
                    requirement="Labels or instructions",
                    implementation="Associate labels with inputs using for/id"
                ),
                AccessibilityRequirement(
                    wcag_guideline="3.3.1",
                    level="A",
                    requirement="Error identification",
                    implementation="Clearly identify and describe errors"
                )
            ],
            
            typical_props=[
                {"name": "value", "type": "string"},
                {"name": "onChange", "type": "function"},
                {"name": "placeholder", "type": "string"},
                {"name": "disabled", "type": "boolean"},
                {"name": "required", "type": "boolean"},
                {"name": "error", "type": "string | boolean"},
                {"name": "label", "type": "string"},
                {"name": "type", "type": "string", "options": ["text", "email", "password", "tel", "url"]}
            ],
            
            common_variations=["PasswordInput", "EmailInput", "SearchInput", "TextArea"],
            
            parent_patterns=["FormField"],
            child_patterns=["InputLabel", "InputError", "InputHelper"],
            
            usage_contexts=[
                "Forms (contact, registration, login)",
                "Search interfaces",
                "Settings and configuration",
                "Content creation and editing"
            ],
            
            antipatterns=[
                "Missing labels",
                "Unclear error messages",
                "No validation feedback",
                "Inaccessible placeholder-only labels"
            ],
            
            best_practices=[
                "Always provide accessible labels",
                "Use appropriate input types",
                "Provide clear validation feedback",
                "Support keyboard navigation",
                "Use reasonable default values when possible"
            ],
            
            keywords=["input", "field", "form", "text", "entry", "data"],
            tags=["atomic", "input", "form", "data-entry"]
        )
        
        self.patterns["TextInput"] = text_input_pattern
    
    def _add_feedback_patterns(self):
        """Add feedback-related patterns."""
        
        alert_pattern = UIPattern(
            name="Alert",
            category=PatternCategory.FEEDBACK,
            complexity=ComplexityLevel.ATOMIC,
            description="Display important messages to users",
            purpose="Communicate status, warnings, or information",
            
            design_principles=[
                DesignPrinciple(
                    name="Urgency Hierarchy",
                    description="Visual treatment should match message importance",
                    importance="critical",
                    examples=["Error = red", "Warning = yellow", "Success = green", "Info = blue"]
                ),
                DesignPrinciple(
                    name="Clarity",
                    description="Message should be clear and actionable",
                    importance="critical",
                    examples=["Specific error descriptions", "Clear next steps", "Plain language"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="display",
                    response="Show with appropriate visual treatment",
                    states=["visible", "hidden"],
                    animations=["fade-in", "slide-down"]
                ),
                InteractionPattern(
                    trigger="dismiss",
                    response="Hide alert",
                    animations=["fade-out", "slide-up"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="4.1.3",
                    level="AA",
                    requirement="Status messages",
                    implementation="Use role='alert' for important messages"
                )
            ],
            
            typical_props=[
                {"name": "variant", "type": "string", "options": ["error", "warning", "success", "info"]},
                {"name": "title", "type": "string"},
                {"name": "children", "type": "ReactNode"},
                {"name": "dismissible", "type": "boolean"},
                {"name": "onDismiss", "type": "function"},
                {"name": "icon", "type": "ReactNode | boolean"}
            ],
            
            common_variations=["Toast", "Banner", "InlineAlert", "StatusMessage"],
            
            usage_contexts=[
                "Form validation errors",
                "System status updates",
                "Action confirmations",
                "Warning messages"
            ],
            
            antipatterns=[
                "Overusing alerts for non-critical messages",
                "Generic or unclear error messages",
                "Missing dismiss functionality",
                "Poor color contrast"
            ],
            
            best_practices=[
                "Match visual treatment to message severity",
                "Provide clear, actionable messages",
                "Allow dismissal when appropriate",
                "Use consistent positioning and timing",
                "Include relevant icons for quick recognition"
            ],
            
            keywords=["alert", "message", "notification", "error", "warning", "success", "feedback"],
            tags=["atomic", "feedback", "status", "communication"]
        )
        
        self.patterns["Alert"] = alert_pattern
    
    def _add_form_patterns(self):
        """Add form-related patterns."""
        
        form_pattern = UIPattern(
            name="Form",
            category=PatternCategory.INPUT,
            complexity=ComplexityLevel.ORGANISM,
            description="Collection of input fields for data submission",
            purpose="Gather structured information from users",
            
            child_patterns=["TextInput", "Button", "FormField", "FormGroup"],
            related_patterns=["Modal", "Card", "Alert"],
            
            design_principles=[
                DesignPrinciple(
                    name="Progressive Disclosure",
                    description="Show information in logical chunks",
                    importance="important",
                    examples=["Multi-step forms", "Conditional fields", "Grouped sections"]
                ),
                DesignPrinciple(
                    name="Error Prevention",
                    description="Help users avoid mistakes",
                    importance="critical",
                    examples=["Real-time validation", "Format hints", "Clear constraints"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="submit",
                    response="Validate and process data",
                    states=["idle", "validating", "submitting", "success", "error"]
                ),
                InteractionPattern(
                    trigger="field-change",
                    response="Update validation state",
                    states=["dirty", "valid", "invalid"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="3.3.2",
                    level="A",
                    requirement="Labels or instructions",
                    implementation="All form controls have labels"
                ),
                AccessibilityRequirement(
                    wcag_guideline="3.3.4",
                    level="AA",
                    requirement="Error prevention",
                    implementation="Provide error prevention for legal/financial data"
                )
            ],
            
            typical_props=[
                {"name": "onSubmit", "type": "function"},
                {"name": "loading", "type": "boolean"},
                {"name": "disabled", "type": "boolean"},
                {"name": "validationSchema", "type": "object"},
                {"name": "initialValues", "type": "object"},
                {"name": "children", "type": "ReactNode"}
            ],
            
            common_variations=["LoginForm", "ContactForm", "RegistrationForm", "SearchForm"],
            
            usage_contexts=[
                "User registration and login",
                "Contact and feedback collection",
                "E-commerce checkout",
                "Settings and preferences",
                "Content creation and editing"
            ],
            
            antipatterns=[
                "Too many required fields",
                "Poor error handling",
                "No progress indication for long forms",
                "Losing data on validation errors"
            ],
            
            best_practices=[
                "Group related fields logically",
                "Provide clear progress indication",
                "Validate fields in real-time when helpful",
                "Preserve user input on errors",
                "Use appropriate input types",
                "Make required fields clear"
            ],
            
            keywords=["form", "input", "data", "submit", "validation", "fields"],
            tags=["organism", "input", "data-collection", "validation"]
        )
        
        self.patterns["Form"] = form_pattern
    
    def _add_card_patterns(self):
        """Add card-related patterns."""
        
        card_pattern = UIPattern(
            name="Card",
            category=PatternCategory.DISPLAY,
            complexity=ComplexityLevel.MOLECULAR,
            description="Container for related information and actions",
            purpose="Group and present related content in a scannable format",
            
            child_patterns=["CardHeader", "CardContent", "CardFooter", "Button"],
            
            design_principles=[
                DesignPrinciple(
                    name="Content Hierarchy",
                    description="Clear visual hierarchy within the card",
                    importance="important",
                    examples=["Header → Content → Actions", "Typography scale", "Visual weight"]
                ),
                DesignPrinciple(
                    name="Scannability",
                    description="Easy to scan and compare with other cards",
                    importance="important",
                    examples=["Consistent layout", "Key info prominence", "Visual grouping"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="hover",
                    response="Show interactive state",
                    states=["default", "hover", "focus"],
                    animations=["elevation-change", "scale", "border-highlight"]
                )
            ],
            
            typical_props=[
                {"name": "children", "type": "ReactNode"},
                {"name": "clickable", "type": "boolean"},
                {"name": "onClick", "type": "function"},
                {"name": "variant", "type": "string", "options": ["elevated", "outlined", "filled"]},
                {"name": "padding", "type": "string"},
                {"name": "className", "type": "string"}
            ],
            
            common_variations=["ProductCard", "UserCard", "ArticleCard", "MetricCard"],
            
            usage_contexts=[
                "Product listings",
                "User profiles",
                "Article previews",
                "Dashboard widgets",
                "Settings panels"
            ],
            
            antipatterns=[
                "Overcrowding with too much information",
                "Inconsistent card sizes in grids",
                "Missing visual hierarchy",
                "Poor mobile responsive behavior"
            ],
            
            best_practices=[
                "Maintain consistent card dimensions in grids",
                "Use clear visual hierarchy",
                "Include relevant actions",
                "Optimize for mobile viewing",
                "Group related cards together"
            ],
            
            keywords=["card", "container", "content", "display", "group", "preview"],
            tags=["molecular", "display", "container", "content"]
        )
        
        self.patterns["Card"] = card_pattern
    
    def _add_navigation_patterns(self):
        """Add navigation-related patterns."""
        
        navbar_pattern = UIPattern(
            name="Navbar",
            category=PatternCategory.NAVIGATION,
            complexity=ComplexityLevel.ORGANISM,
            description="Primary navigation interface for applications",
            purpose="Provide access to main sections and functionality",
            
            child_patterns=["Button", "Logo", "MenuButton", "UserMenu"],
            related_patterns=["Sidebar", "Breadcrumbs", "Tabs"],
            
            design_principles=[
                DesignPrinciple(
                    name="Discoverability",
                    description="Users should easily find navigation options",
                    importance="critical",
                    examples=["Clear labels", "Logical grouping", "Visual prominence"]
                ),
                DesignPrinciple(
                    name="Context Awareness",
                    description="Show current location and relevant options",
                    importance="important",
                    examples=["Active states", "Breadcrumbs", "Context-sensitive menus"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="responsive",
                    response="Adapt layout for different screen sizes",
                    states=["desktop", "tablet", "mobile", "collapsed"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="2.4.3",
                    level="A",
                    requirement="Focus order",
                    implementation="Logical keyboard navigation order"
                ),
                AccessibilityRequirement(
                    wcag_guideline="2.4.1",
                    level="A",
                    requirement="Bypass blocks",
                    implementation="Skip navigation link"
                )
            ],
            
            typical_props=[
                {"name": "brand", "type": "ReactNode"},
                {"name": "menuItems", "type": "array"},
                {"name": "userMenu", "type": "ReactNode"},
                {"name": "mobileMenuOpen", "type": "boolean"},
                {"name": "onMobileMenuToggle", "type": "function"},
                {"name": "sticky", "type": "boolean"}
            ],
            
            common_variations=["AppBar", "TopNav", "HeaderNav", "BrandNav"],
            
            usage_contexts=[
                "Application headers",
                "Website navigation",
                "Admin dashboards",
                "E-commerce sites"
            ],
            
            antipatterns=[
                "Too many top-level navigation items",
                "Poor mobile responsive behavior",
                "Missing active/current states",
                "Inaccessible dropdown menus"
            ],
            
            best_practices=[
                "Limit top-level navigation items (5-7 max)",
                "Implement responsive navigation patterns",
                "Show current page/section clearly",
                "Ensure keyboard accessibility",
                "Maintain consistent positioning"
            ],
            
            keywords=["navbar", "navigation", "header", "menu", "app-bar", "top-nav"],
            tags=["organism", "navigation", "layout", "responsive"]
        )
        
        self.patterns["Navbar"] = navbar_pattern
    
    def _add_layout_patterns(self):
        """Add layout-related patterns."""
        
        sidebar_layout_pattern = UIPattern(
            name="SidebarLayout",
            category=PatternCategory.LAYOUT,
            complexity=ComplexityLevel.TEMPLATE,
            description="Layout with navigation sidebar and main content area",
            purpose="Organize application interface with persistent navigation",
            
            child_patterns=["Sidebar", "MainContent", "Header"],
            related_patterns=["Navbar", "Breadcrumbs"],
            
            design_principles=[
                DesignPrinciple(
                    name="Space Efficiency",
                    description="Optimize space usage across different screen sizes",
                    importance="critical",
                    examples=["Collapsible sidebar", "Responsive breakpoints", "Flexible content area"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="sidebar-toggle",
                    response="Show/hide sidebar",
                    states=["expanded", "collapsed", "overlay"],
                    animations=["slide", "fade"]
                )
            ],
            
            typical_props=[
                {"name": "sidebarWidth", "type": "string"},
                {"name": "collapsible", "type": "boolean"},
                {"name": "defaultCollapsed", "type": "boolean"},
                {"name": "sidebar", "type": "ReactNode"},
                {"name": "children", "type": "ReactNode"}
            ],
            
            usage_contexts=[
                "Admin dashboards",
                "Documentation sites",
                "Application interfaces",
                "Content management systems"
            ],
            
            keywords=["sidebar", "layout", "navigation", "dashboard", "admin"],
            tags=["template", "layout", "navigation", "responsive"]
        )
        
        self.patterns["SidebarLayout"] = sidebar_layout_pattern
    
    def _add_data_display_patterns(self):
        """Add data display patterns.""" 
        
        data_table_pattern = UIPattern(
            name="DataTable",
            category=PatternCategory.DISPLAY,
            complexity=ComplexityLevel.ORGANISM,
            description="Structured display of tabular data with interactive features",
            purpose="Present and manipulate large datasets efficiently",
            
            child_patterns=["TableHeader", "TableRow", "TableCell", "Pagination"],
            related_patterns=["SearchInput", "FilterDropdown", "SortButton"],
            
            design_principles=[
                DesignPrinciple(
                    name="Scannability",
                    description="Easy to scan rows and columns",
                    importance="critical",
                    examples=["Alternating row colors", "Clear column alignment", "Consistent spacing"]
                ),
                DesignPrinciple(
                    name="Progressive Disclosure",
                    description="Show most important data first",
                    importance="important",
                    examples=["Column prioritization", "Expandable rows", "Responsive hiding"]
                )
            ],
            
            interaction_patterns=[
                InteractionPattern(
                    trigger="sort",
                    response="Reorder table data",
                    states=["unsorted", "ascending", "descending"]
                ),
                InteractionPattern(
                    trigger="filter",
                    response="Show subset of data",
                    states=["unfiltered", "filtered"]
                )
            ],
            
            accessibility_requirements=[
                AccessibilityRequirement(
                    wcag_guideline="1.3.1",
                    level="A",
                    requirement="Info and relationships",
                    implementation="Use proper table markup with headers"
                )
            ],
            
            typical_props=[
                {"name": "data", "type": "array"},
                {"name": "columns", "type": "array"},
                {"name": "sortable", "type": "boolean"},
                {"name": "filterable", "type": "boolean"},
                {"name": "selectable", "type": "boolean"},
                {"name": "pagination", "type": "object"},
                {"name": "loading", "type": "boolean"}
            ],
            
            common_variations=["SimpleTable", "SortableTable", "EditableTable", "TreeTable"],
            
            usage_contexts=[
                "Admin interfaces",
                "Data dashboards",
                "Report viewing",
                "Content management",
                "E-commerce product lists"
            ],
            
            antipatterns=[
                "Too many columns on mobile",
                "Poor loading states",
                "Inaccessible sorting controls",
                "Missing empty states"
            ],
            
            best_practices=[
                "Implement responsive column hiding",
                "Provide clear loading and empty states",
                "Use proper table semantics",
                "Include keyboard navigation",
                "Optimize for large datasets"
            ],
            
            keywords=["table", "data", "grid", "list", "sort", "filter", "pagination"],
            tags=["organism", "data-display", "interactive", "complex"]
        )
        
        self.patterns["DataTable"] = data_table_pattern
    
    def _add_page_patterns(self):
        """Add page-level patterns."""
        
        dashboard_pattern = UIPattern(
            name="Dashboard",
            category=PatternCategory.LAYOUT,
            complexity=ComplexityLevel.PAGE,
            description="Overview page showing key metrics and data",
            purpose="Provide at-a-glance view of important information",
            
            child_patterns=["Card", "Chart", "MetricCard", "DataTable", "Header"],
            related_patterns=["SidebarLayout", "Navbar"],
            
            design_principles=[
                DesignPrinciple(
                    name="Information Hierarchy",
                    description="Most important information should be most prominent",
                    importance="critical",
                    examples=["Key metrics first", "Visual weight hierarchy", "Progressive disclosure"]
                ),
                DesignPrinciple(
                    name="Actionability",
                    description="Users should be able to act on the information",
                    importance="important",
                    examples=["Drill-down capabilities", "Quick actions", "Contextual links"]
                )
            ],
            
            typical_props=[
                {"name": "widgets", "type": "array"},
                {"name": "layout", "type": "string", "options": ["grid", "masonry", "custom"]},
                {"name": "customizable", "type": "boolean"},
                {"name": "refreshInterval", "type": "number"},
                {"name": "loading", "type": "boolean"}
            ],
            
            common_variations=["AnalyticsDashboard", "AdminDashboard", "UserDashboard"],
            
            usage_contexts=[
                "Business intelligence",
                "Admin panels",
                "User portals",
                "Monitoring systems"
            ],
            
            antipatterns=[
                "Information overload",
                "No clear hierarchy",
                "Poor mobile experience",
                "Slow loading performance"
            ],
            
            best_practices=[
                "Show most important metrics first",
                "Use consistent card layouts",
                "Implement progressive loading",
                "Provide customization options",
                "Ensure mobile responsiveness"
            ],
            
            keywords=["dashboard", "overview", "metrics", "analytics", "widgets", "summary"],
            tags=["page", "layout", "data-display", "overview"]
        )
        
        self.patterns["Dashboard"] = dashboard_pattern
    
    def _build_indexes(self):
        """Build search indexes for efficient pattern lookup."""
        
        # Category index
        for pattern_name, pattern in self.patterns.items():
            if pattern.category not in self.category_index:
                self.category_index[pattern.category] = []
            self.category_index[pattern.category].append(pattern_name)
        
        # Complexity index
        for pattern_name, pattern in self.patterns.items():
            if pattern.complexity not in self.complexity_index:
                self.complexity_index[pattern.complexity] = []
            self.complexity_index[pattern.complexity].append(pattern_name)
        
        # Keyword index
        for pattern_name, pattern in self.patterns.items():
            for keyword in pattern.keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(pattern_name)
    
    @handle_errors(reraise=True)
    def find_patterns(
        self,
        query: str = None,
        category: PatternCategory = None,
        complexity: ComplexityLevel = None,
        keywords: List[str] = None
    ) -> List[UIPattern]:
        """
        Find UI patterns based on various criteria.
        
        Args:
            query: Free text search query
            category: Pattern category filter
            complexity: Pattern complexity filter
            keywords: List of keywords to match
            
        Returns:
            List of matching UI patterns
        """
        candidates = set(self.patterns.keys())
        
        # Filter by category
        if category:
            category_patterns = set(self.category_index.get(category, []))
            candidates = candidates.intersection(category_patterns)
        
        # Filter by complexity
        if complexity:
            complexity_patterns = set(self.complexity_index.get(complexity, []))
            candidates = candidates.intersection(complexity_patterns)
        
        # Filter by keywords
        if keywords:
            keyword_patterns = set()
            for keyword in keywords:
                keyword_patterns.update(self.keyword_index.get(keyword.lower(), []))
            candidates = candidates.intersection(keyword_patterns)
        
        # Filter by query
        if query:
            query_lower = query.lower()
            query_patterns = set()
            
            for pattern_name, pattern in self.patterns.items():
                # Check name, description, purpose
                if (query_lower in pattern.name.lower() or
                    query_lower in pattern.description.lower() or
                    query_lower in pattern.purpose.lower()):
                    query_patterns.add(pattern_name)
                
                # Check keywords
                if any(query_lower in keyword.lower() for keyword in pattern.keywords):
                    query_patterns.add(pattern_name)
            
            candidates = candidates.intersection(query_patterns)
        
        # Return pattern objects
        return [self.patterns[name] for name in candidates]
    
    def get_pattern(self, pattern_name: str) -> Optional[UIPattern]:
        """Get a specific pattern by name."""
        return self.patterns.get(pattern_name)
    
    def get_related_patterns(self, pattern_name: str) -> List[UIPattern]:
        """Get patterns related to the specified pattern."""
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return []
        
        related_names = (
            pattern.parent_patterns + 
            pattern.child_patterns + 
            pattern.related_patterns
        )
        
        return [self.patterns[name] for name in related_names if name in self.patterns]
    
    def get_pattern_hierarchy(self, pattern_name: str) -> Dict[str, List[str]]:
        """Get the hierarchical relationships for a pattern."""
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return {}
        
        return {
            "parents": pattern.parent_patterns,
            "children": pattern.child_patterns,
            "related": pattern.related_patterns
        }
    
    def analyze_pattern_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze a user request to suggest relevant patterns.
        
        Args:
            user_request: User's component request
            
        Returns:
            Analysis with suggested patterns and rationale
        """
        request_lower = user_request.lower()
        
        # Extract keywords from request
        request_keywords = []
        for keyword in self.keyword_index.keys():
            if keyword in request_lower:
                request_keywords.append(keyword)
        
        # Find matching patterns
        matching_patterns = self.find_patterns(
            query=user_request,
            keywords=request_keywords
        )
        
        # Analyze complexity needs
        complexity_indicators = {
            ComplexityLevel.ATOMIC: ["button", "input", "icon", "label"],
            ComplexityLevel.MOLECULAR: ["search", "card", "menu", "field"],
            ComplexityLevel.ORGANISM: ["form", "table", "navigation", "header"],
            ComplexityLevel.TEMPLATE: ["layout", "page", "template", "structure"],
            ComplexityLevel.PAGE: ["dashboard", "profile", "settings", "admin"]
        }
        
        suggested_complexity = ComplexityLevel.ATOMIC
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                suggested_complexity = complexity
                break
        
        return {
            "matching_patterns": [p.name for p in matching_patterns],
            "suggested_complexity": suggested_complexity.value,
            "extracted_keywords": request_keywords,
            "pattern_suggestions": self._get_pattern_suggestions(matching_patterns, user_request),
            "design_considerations": self._get_design_considerations(matching_patterns)
        }
    
    def _get_pattern_suggestions(self, patterns: List[UIPattern], request: str) -> List[Dict[str, Any]]:
        """Get specific suggestions based on matching patterns."""
        suggestions = []
        
        for pattern in patterns[:3]:  # Top 3 matches
            suggestion = {
                "pattern": pattern.name,
                "relevance_score": self._calculate_relevance_score(pattern, request),
                "why_relevant": f"Matches {pattern.category.value} category and common {pattern.complexity.value} level patterns",
                "key_considerations": pattern.best_practices[:3],
                "common_props": [prop["name"] for prop in pattern.typical_props[:5]]
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_relevance_score(self, pattern: UIPattern, request: str) -> float:
        """Calculate how relevant a pattern is to the request."""
        request_lower = request.lower()
        score = 0.0
        
        # Name match
        if pattern.name.lower() in request_lower:
            score += 0.4
        
        # Keyword matches
        keyword_matches = sum(1 for keyword in pattern.keywords if keyword in request_lower)
        score += (keyword_matches / len(pattern.keywords)) * 0.3
        
        # Description/purpose match
        if any(word in pattern.description.lower() or word in pattern.purpose.lower() 
               for word in request_lower.split()):
            score += 0.3
        
        return min(1.0, score)
    
    def _get_design_considerations(self, patterns: List[UIPattern]) -> List[str]:
        """Extract design considerations from matching patterns."""
        considerations = set()
        
        for pattern in patterns:
            for principle in pattern.design_principles:
                if principle.importance in ["critical", "important"]:
                    considerations.add(principle.description)
            
            considerations.update(pattern.best_practices[:2])
        
        return list(considerations)[:5]  # Top 5 considerations
    
    def export_pattern_summary(self) -> Dict[str, Any]:
        """Export a summary of all patterns in the ontology."""
        return {
            "total_patterns": len(self.patterns),
            "by_category": {cat.value: len(patterns) for cat, patterns in self.category_index.items()},
            "by_complexity": {comp.value: len(patterns) for comp, patterns in self.complexity_index.items()},
            "pattern_list": list(self.patterns.keys())
        }


# Global ontology instance
_ontology_instance = None

def get_ui_pattern_ontology() -> UIPatternOntology:
    """Get the global UI pattern ontology instance."""
    global _ontology_instance
    if _ontology_instance is None:
        _ontology_instance = UIPatternOntology()
    return _ontology_instance