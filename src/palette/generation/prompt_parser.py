"""
Semantic prompt parser for better understanding of component requirements.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re


@dataclass
class ComponentRequirements:
    """Parsed component requirements from user prompt."""

    component_type: str
    features: List[str]
    styling_requirements: List[str]
    data_requirements: List[str]
    interaction_requirements: List[str]
    layout_type: Optional[str] = None


class PromptParser:
    """Parse user prompts to extract semantic meaning and requirements."""

    def __init__(self):
        # Component type patterns - ordered by specificity
        self.component_patterns = [
            # Compound types first
            (r"product\s+card\s+grid", "product_grid"),
            (r"product\s+grid", "product_grid"),
            (r"dashboard\s+header", "dashboard_header"),
            (r"pricing\s+section", "pricing_section"),
            (r"hero\s+section", "hero_section"),
            (r"navigation\s+bar", "navigation_bar"),
            (r"data\s+table", "data_table"),
            (r"contact\s+form", "contact_form"),
            # Single types
            (r"\bcard\b", "card"),
            (r"\bbutton\b", "button"),
            (r"\bform\b", "form"),
            (r"\bmodal\b", "modal"),
            (r"\btable\b", "table"),
            (r"\bheader\b", "header"),
            (r"\bfooter\b", "footer"),
            (r"\bmenu\b", "menu"),
            (r"\blist\b", "list"),
        ]

        # Feature patterns
        self.feature_patterns = {
            "search": r"\bsearch\b|\bfilter\b",
            "notifications": r"\bnotification\b|\bbadge\s+count\b|\bbell\b",
            "dropdown": r"\bdropdown\b|\bselect\b",
            "avatar": r"\bavatar\b|\bprofile\s+pic\b",
            "breadcrumbs": r"\bbreadcrumb\b",
            "pricing_tiers": r"\btier\b|\bplan\b|\bpricing\b",
            "ratings": r"\brating\b|\bstar\b",
            "discount": r"\bdiscount\b|\bsale\b|\bbadge\b",
            "cart": r"\bcart\b|\badd\s+to\s+cart\b",
            "wishlist": r"\bwishlist\b|\bfavorite\b|\bheart\b",
            "image": r"\bimage\b|\bphoto\b|\bpicture\b|\bplaceholder\b",
            "checkmarks": r"\bcheckmark\b|\bcheck\s+list\b|\bfeature\s+list\b",
            "cta": r"\bcta\b|\bcall\s+to\s+action\b|\bbutton\b",
        }

        # Styling patterns
        self.styling_patterns = {
            "gradient": r"\bgradient\b",
            "hover": r"\bhover\b|\banimation\b",
            "responsive": r"\bresponsive\b|\bmobile\b",
            "dark_mode": r"\bdark\s+mode\b|\btheme\b",
            "shadow": r"\bshadow\b",
            "rounded": r"\brounded\b|\bborder\s+radius\b",
        }

        # Layout patterns
        self.layout_patterns = {
            "grid": r"\bgrid\b",
            "flex": r"\bflex\b",
            "columns": r"\bcolumn\b|\bcol\b",
            "rows": r"\brow\b",
            "sidebar": r"\bsidebar\b",
            "split": r"\bsplit\b",
        }

    def parse(self, prompt: str) -> ComponentRequirements:
        """Parse a user prompt to extract component requirements."""
        prompt_lower = prompt.lower()

        # Detect component type
        component_type = self._detect_component_type(prompt_lower)

        # Extract features
        features = self._extract_features(prompt_lower)

        # Extract styling requirements
        styling_requirements = self._extract_styling(prompt_lower)

        # Extract data requirements
        data_requirements = self._extract_data_requirements(prompt_lower)

        # Extract interaction requirements
        interaction_requirements = self._extract_interactions(prompt_lower)

        # Detect layout type
        layout_type = self._detect_layout_type(prompt_lower)

        return ComponentRequirements(
            component_type=component_type,
            features=features,
            styling_requirements=styling_requirements,
            data_requirements=data_requirements,
            interaction_requirements=interaction_requirements,
            layout_type=layout_type,
        )

    def _detect_component_type(self, prompt: str) -> str:
        """Detect the primary component type from prompt."""
        for pattern, comp_type in self.component_patterns:
            if re.search(pattern, prompt):
                return comp_type
        return "component"

    def _extract_features(self, prompt: str) -> List[str]:
        """Extract feature requirements from prompt."""
        features = []
        for feature, pattern in self.feature_patterns.items():
            if re.search(pattern, prompt):
                features.append(feature)
        return features

    def _extract_styling(self, prompt: str) -> List[str]:
        """Extract styling requirements from prompt."""
        styling = []
        for style, pattern in self.styling_patterns.items():
            if re.search(pattern, prompt):
                styling.append(style)

        # Check for design system mentions
        if "design system" in prompt or "project colors" in prompt:
            styling.append("use_design_tokens")

        return styling

    def _extract_data_requirements(self, prompt: str) -> List[str]:
        """Extract data/content requirements from prompt."""
        data_reqs = []

        # Check for specific data mentions
        if re.search(r"\b\d+\s+(tier|plan|card|item)", prompt):
            match = re.search(r"\b(\d+)\s+(tier|plan|card|item)", prompt)
            if match:
                data_reqs.append(f"{match.group(1)}_{match.group(2)}s")

        # Check for data types
        if "product" in prompt:
            data_reqs.append("products")
        if "user" in prompt or "profile" in prompt:
            data_reqs.append("user_data")
        if "price" in prompt or "pricing" in prompt:
            data_reqs.append("pricing_data")

        return data_reqs

    def _extract_interactions(self, prompt: str) -> List[str]:
        """Extract interaction requirements from prompt."""
        interactions = []

        interaction_patterns = {
            "click": r"\bclick\b|\bbutton\b",
            "hover": r"\bhover\b",
            "dropdown": r"\bdropdown\b|\btoggle\b",
            "search": r"\bsearch\b|\bfilter\b",
            "add_to_cart": r"\badd\s+to\s+cart\b",
            "navigation": r"\bnavigate\b|\blink\b",
        }

        for interaction, pattern in interaction_patterns.items():
            if re.search(pattern, prompt):
                interactions.append(interaction)

        return interactions

    def _detect_layout_type(self, prompt: str) -> Optional[str]:
        """Detect the layout type from prompt."""
        for layout, pattern in self.layout_patterns.items():
            if re.search(pattern, prompt):
                return layout

        # Default layouts based on component type
        if "grid" in prompt or "cards" in prompt:
            return "grid"
        elif "header" in prompt or "navigation" in prompt:
            return "flex"

        return None


def extract_component_name_from_requirements(
    requirements: ComponentRequirements,
) -> str:
    """Generate appropriate component name from requirements."""
    type_to_name = {
        "product_grid": "ProductCardGrid",
        "dashboard_header": "DashboardHeader",
        "pricing_section": "PricingSection",
        "hero_section": "HeroSection",
        "navigation_bar": "NavigationBar",
        "data_table": "DataTable",
        "contact_form": "ContactForm",
        "card": "Card",
        "button": "Button",
        "form": "Form",
        "modal": "Modal",
        "table": "Table",
        "header": "Header",
        "footer": "Footer",
        "menu": "Menu",
        "list": "List",
        "component": "Component",
    }

    return type_to_name.get(requirements.component_type, "Component")
