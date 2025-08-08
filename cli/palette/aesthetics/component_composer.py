"""
Component Composition Engine for Beautiful Layouts

This module provides sophisticated component composition capabilities,
allowing the system to create complex, beautiful layouts by combining
multiple shadcn/ui components intelligently.
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .aesthetic_prompts import DesignStyle, AestheticConfig


class LayoutType(Enum):
    """Types of layout patterns"""
    HERO_SECTION = "hero_section"
    DASHBOARD = "dashboard" 
    CARD_GRID = "card_grid"
    FORM_LAYOUT = "form_layout"
    NAVIGATION_LAYOUT = "navigation_layout"
    CONTENT_SECTION = "content_section"
    FEATURE_SHOWCASE = "feature_showcase"
    PRICING_SECTION = "pricing_section"
    TESTIMONIAL_GRID = "testimonial_grid"
    FOOTER_SECTION = "footer_section"


@dataclass
class ComponentComposition:
    """Represents a composed layout with multiple components"""
    layout_type: LayoutType
    components: List[Dict[str, Any]]
    container_classes: str
    responsive_behavior: Dict[str, str]
    animations: List[str]
    accessibility_features: List[str]
    code: str
    description: str


class ComponentComposer:
    """Composes multiple components into beautiful layouts"""
    
    def __init__(self):
        self.layout_patterns = self._load_layout_patterns()
        self.responsive_patterns = self._load_responsive_patterns()
        self.animation_sequences = self._load_animation_sequences()
        
    def compose_layout(self,
                      description: str,
                      components: List[str],
                      style: DesignStyle = DesignStyle.MODERN_MINIMAL,
                      responsive: bool = True) -> ComponentComposition:
        """Compose components into a beautiful layout"""
        
        # Detect layout type from description
        layout_type = self._detect_layout_type(description)
        
        # Get layout pattern
        pattern = self.layout_patterns.get(layout_type, self.layout_patterns[LayoutType.CONTENT_SECTION])
        
        # Build composition
        composition = self._build_composition(
            layout_type=layout_type,
            components=components,
            description=description,
            pattern=pattern,
            style=style,
            responsive=responsive
        )
        
        return composition
    
    def _detect_layout_type(self, description: str) -> LayoutType:
        """Detect layout type from description"""
        desc_lower = description.lower()
        
        # Layout type detection patterns
        patterns = {
            LayoutType.HERO_SECTION: ['hero', 'banner', 'landing', 'main section', 'header section'],
            LayoutType.DASHBOARD: ['dashboard', 'admin', 'metrics', 'analytics', 'overview', 'stats'],
            LayoutType.CARD_GRID: ['cards', 'grid of', 'gallery', 'showcase', 'collection'],
            LayoutType.FORM_LAYOUT: ['form', 'contact', 'signup', 'login', 'registration', 'input'],
            LayoutType.NAVIGATION_LAYOUT: ['navigation', 'navbar', 'menu', 'header', 'nav'],
            LayoutType.FEATURE_SHOWCASE: ['features', 'benefits', 'services', 'what we offer'],
            LayoutType.PRICING_SECTION: ['pricing', 'plans', 'packages', 'subscription'],
            LayoutType.TESTIMONIAL_GRID: ['testimonials', 'reviews', 'feedback', 'customer'],
            LayoutType.FOOTER_SECTION: ['footer', 'bottom', 'contact info', 'links']
        }
        
        for layout_type, keywords in patterns.items():
            if any(keyword in desc_lower for keyword in keywords):
                return layout_type
        
        return LayoutType.CONTENT_SECTION  # Default
    
    def _build_composition(self,
                          layout_type: LayoutType,
                          components: List[str],
                          description: str,
                          pattern: Dict[str, Any],
                          style: DesignStyle,
                          responsive: bool) -> ComponentComposition:
        """Build the actual component composition"""
        
        # Generate container classes based on layout type and style
        container_classes = self._generate_container_classes(layout_type, style, responsive)
        
        # Generate responsive behavior
        responsive_behavior = self._generate_responsive_behavior(layout_type) if responsive else {}
        
        # Generate animations based on style
        animations = self._generate_layout_animations(layout_type, style)
        
        # Generate accessibility features
        accessibility_features = self._generate_accessibility_features(layout_type)
        
        # Build the actual code
        code = self._generate_layout_code(
            layout_type=layout_type,
            components=components,
            description=description,
            container_classes=container_classes,
            pattern=pattern,
            style=style,
            responsive=responsive
        )
        
        return ComponentComposition(
            layout_type=layout_type,
            components=[{"name": comp, "type": comp} for comp in components],
            container_classes=container_classes,
            responsive_behavior=responsive_behavior,
            animations=animations,
            accessibility_features=accessibility_features,
            code=code,
            description=description
        )
    
    def _generate_container_classes(self, layout_type: LayoutType, style: DesignStyle, responsive: bool) -> str:
        """Generate container classes for the layout"""
        
        base_classes = "w-full"
        
        # Layout-specific classes
        layout_classes = {
            LayoutType.HERO_SECTION: "min-h-screen flex items-center justify-center",
            LayoutType.DASHBOARD: "min-h-screen bg-gray-50 dark:bg-gray-900",
            LayoutType.CARD_GRID: "py-12",
            LayoutType.FORM_LAYOUT: "min-h-screen flex items-center justify-center",
            LayoutType.NAVIGATION_LAYOUT: "sticky top-0 z-50",
            LayoutType.CONTENT_SECTION: "py-16",
            LayoutType.FEATURE_SHOWCASE: "py-20",
            LayoutType.PRICING_SECTION: "py-16 bg-gradient-to-b from-gray-50 to-white",
            LayoutType.TESTIMONIAL_GRID: "py-16 bg-gray-50 dark:bg-gray-900",
            LayoutType.FOOTER_SECTION: "bg-gray-900 text-white py-12"
        }
        
        layout_specific = layout_classes.get(layout_type, "py-8")
        
        # Style-specific modifications
        style_classes = ""
        if style == DesignStyle.GLASSMORPHISM:
            style_classes = "backdrop-blur-md bg-white/30 dark:bg-gray-900/30"
        elif style == DesignStyle.BOLD_VIBRANT:
            style_classes = "bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50"
        elif style == DesignStyle.DARK_ELEGANT:
            style_classes = "bg-gray-900 text-white"
        
        # Responsive classes
        responsive_classes = "px-4 sm:px-6 lg:px-8" if responsive else "px-8"
        
        return f"{base_classes} {layout_specific} {style_classes} {responsive_classes}".strip()
    
    def _generate_responsive_behavior(self, layout_type: LayoutType) -> Dict[str, str]:
        """Generate responsive behavior patterns"""
        
        patterns = {
            LayoutType.CARD_GRID: {
                "mobile": "grid-cols-1 gap-4",
                "tablet": "sm:grid-cols-2 sm:gap-6", 
                "desktop": "lg:grid-cols-3 lg:gap-8 xl:grid-cols-4"
            },
            LayoutType.DASHBOARD: {
                "mobile": "grid-cols-1 gap-4",
                "tablet": "md:grid-cols-2 md:gap-6",
                "desktop": "lg:grid-cols-3 xl:grid-cols-4 lg:gap-8"
            },
            LayoutType.FEATURE_SHOWCASE: {
                "mobile": "grid-cols-1 gap-8",
                "tablet": "md:grid-cols-2 md:gap-12",
                "desktop": "lg:grid-cols-3 lg:gap-16"
            },
            LayoutType.PRICING_SECTION: {
                "mobile": "grid-cols-1 gap-8",
                "tablet": "md:grid-cols-2 md:gap-6",
                "desktop": "lg:grid-cols-3 lg:gap-8"
            }
        }
        
        return patterns.get(layout_type, {
            "mobile": "grid-cols-1 gap-4",
            "tablet": "md:grid-cols-2 md:gap-6",
            "desktop": "lg:grid-cols-3 lg:gap-8"
        })
    
    def _generate_layout_animations(self, layout_type: LayoutType, style: DesignStyle) -> List[str]:
        """Generate animations for the layout"""
        
        base_animations = ["transition-all", "duration-300"]
        
        # Layout-specific animations
        layout_animations = {
            LayoutType.HERO_SECTION: ["animate-in", "fade-in", "slide-in-from-bottom", "duration-1000"],
            LayoutType.CARD_GRID: ["animate-in", "fade-in", "slide-in-from-bottom", "stagger"],
            LayoutType.DASHBOARD: ["animate-in", "fade-in", "duration-500"],
            LayoutType.FEATURE_SHOWCASE: ["animate-in", "zoom-in-95", "duration-700", "stagger"]
        }
        
        # Style-specific animation modifications
        style_animations = []
        if style == DesignStyle.PLAYFUL:
            style_animations = ["hover:scale-105", "hover:-rotate-1"]
        elif style == DesignStyle.BOLD_VIBRANT:
            style_animations = ["hover:shadow-2xl", "hover:shadow-blue-500/25"]
        
        layout_specific = layout_animations.get(layout_type, base_animations)
        return layout_specific + style_animations
    
    def _generate_accessibility_features(self, layout_type: LayoutType) -> List[str]:
        """Generate accessibility features for the layout"""
        
        base_features = [
            "Semantic HTML structure",
            "ARIA landmarks",
            "Keyboard navigation support",
            "Screen reader compatibility"
        ]
        
        layout_features = {
            LayoutType.HERO_SECTION: [
                "Main landmark role",
                "Proper heading hierarchy",
                "Skip to content links"
            ],
            LayoutType.NAVIGATION_LAYOUT: [
                "Navigation landmark",
                "Menu button aria-expanded",
                "Proper focus management",
                "Mobile menu accessibility"
            ],
            LayoutType.FORM_LAYOUT: [
                "Form landmark",
                "Label associations", 
                "Error announcements",
                "Field validation feedback"
            ],
            LayoutType.DASHBOARD: [
                "Region landmarks",
                "Chart accessibility",
                "Data table headers",
                "Live region updates"
            ]
        }
        
        specific_features = layout_features.get(layout_type, [])
        return base_features + specific_features
    
    def _generate_layout_code(self,
                             layout_type: LayoutType,
                             components: List[str],
                             description: str,
                             container_classes: str,
                             pattern: Dict[str, Any],
                             style: DesignStyle,
                             responsive: bool) -> str:
        """Generate the actual layout code"""
        
        # Get component imports
        imports = self._generate_imports(components)
        
        # Generate layout structure based on type
        layout_structure = self._get_layout_structure(layout_type, components, responsive)
        
        # Apply style-specific modifications
        styled_structure = self._apply_style_modifications(layout_structure, style)
        
        # Generate the complete component
        component_name = self._generate_component_name(layout_type)
        
        code = f'''{imports}

export function {component_name}() {{
  return (
    <div className="{container_classes}">
{styled_structure}
    </div>
  )
}}'''
        
        return code
    
    def _generate_imports(self, components: List[str]) -> str:
        """Generate import statements for components"""
        imports = []
        
        # Standard React imports
        imports.append('import React from "react"')
        
        # shadcn/ui component imports
        for component in components:
            if component.lower() in ['button', 'card', 'input', 'form', 'modal']:
                imports.append(f'import {{ {component.capitalize()} }} from "@/components/ui/{component.lower()}"')
        
        # Add common utility imports
        imports.append('import { cn } from "@/lib/utils"')
        
        return '\n'.join(imports)
    
    def _get_layout_structure(self, layout_type: LayoutType, components: List[str], responsive: bool) -> str:
        """Get the layout structure for the given type"""
        
        structures = {
            LayoutType.HERO_SECTION: self._generate_hero_structure(components, responsive),
            LayoutType.DASHBOARD: self._generate_dashboard_structure(components, responsive),
            LayoutType.CARD_GRID: self._generate_card_grid_structure(components, responsive),
            LayoutType.FORM_LAYOUT: self._generate_form_structure(components, responsive),
            LayoutType.FEATURE_SHOWCASE: self._generate_feature_structure(components, responsive),
            LayoutType.PRICING_SECTION: self._generate_pricing_structure(components, responsive)
        }
        
        return structures.get(layout_type, self._generate_generic_structure(components, responsive))
    
    def _generate_hero_structure(self, components: List[str], responsive: bool) -> str:
        """Generate hero section structure"""
        responsive_classes = "max-w-7xl mx-auto text-center" if responsive else "max-w-4xl mx-auto text-center"
        
        return f'''      <div className="{responsive_classes}">
        <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent mb-6">
          Beautiful Hero Section
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
          This is a stunning hero section with modern design principles
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="shadow-xl shadow-blue-500/25">
            Get Started
          </Button>
          <Button variant="outline" size="lg">
            Learn More  
          </Button>
        </div>
      </div>'''
    
    def _generate_dashboard_structure(self, components: List[str], responsive: bool) -> str:
        """Generate dashboard structure"""
        grid_classes = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" if responsive else "grid grid-cols-4 gap-6"
        
        return f'''      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">Dashboard</h2>
        <div className="{grid_classes}">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">Total Users</h3>
            <p className="text-3xl font-bold text-blue-600">12,345</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">Revenue</h3>
            <p className="text-3xl font-bold text-green-600">$45,678</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">Conversion</h3>
            <p className="text-3xl font-bold text-purple-600">23.4%</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-2">Growth</h3>
            <p className="text-3xl font-bold text-orange-600">+12%</p>
          </Card>
        </div>
      </div>'''
    
    def _generate_card_grid_structure(self, components: List[str], responsive: bool) -> str:
        """Generate card grid structure"""
        grid_classes = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" if responsive else "grid grid-cols-3 gap-8"
        
        return f'''      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Beautiful Cards</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">A collection of beautifully designed cards</p>
        </div>
        <div className="{grid_classes}">
          <Card className="group hover:shadow-xl transition-shadow duration-300">
            <div className="aspect-video bg-gradient-to-br from-blue-400 to-purple-500 rounded-t-lg"></div>
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-2">Card Title</h3>
              <p className="text-gray-600 mb-4">Beautiful card description with elegant styling.</p>
              <Button className="w-full">Learn More</Button>
            </div>
          </Card>
          <Card className="group hover:shadow-xl transition-shadow duration-300">
            <div className="aspect-video bg-gradient-to-br from-green-400 to-blue-500 rounded-t-lg"></div>
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-2">Card Title</h3>
              <p className="text-gray-600 mb-4">Beautiful card description with elegant styling.</p>
              <Button className="w-full">Learn More</Button>
            </div>
          </Card>
          <Card className="group hover:shadow-xl transition-shadow duration-300">
            <div className="aspect-video bg-gradient-to-br from-purple-400 to-pink-500 rounded-t-lg"></div>
            <div className="p-6">
              <h3 className="text-xl font-semibold mb-2">Card Title</h3>
              <p className="text-gray-600 mb-4">Beautiful card description with elegant styling.</p>
              <Button className="w-full">Learn More</Button>
            </div>
          </Card>
        </div>
      </div>'''
    
    def _generate_form_structure(self, components: List[str], responsive: bool) -> str:
        """Generate form structure"""
        return '''      <div className="max-w-md mx-auto">
        <Card className="p-8">
          <h2 className="text-2xl font-bold text-center mb-6">Sign In</h2>
          <form className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <Input type="email" placeholder="Enter your email" className="w-full" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <Input type="password" placeholder="Enter your password" className="w-full" />
            </div>
            <Button type="submit" className="w-full">Sign In</Button>
          </form>
        </Card>
      </div>'''
    
    def _generate_feature_structure(self, components: List[str], responsive: bool) -> str:
        """Generate feature showcase structure"""
        grid_classes = "grid grid-cols-1 md:grid-cols-3 gap-12" if responsive else "grid grid-cols-3 gap-12"
        
        return f'''      <div className="max-w-7xl mx-auto text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">Amazing Features</h2>
        <p className="text-xl text-gray-600 mb-16 max-w-3xl mx-auto">
          Discover the powerful features that make our product exceptional
        </p>
        <div className="{grid_classes}">
          <div className="group">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl mx-auto mb-6 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-blue-500/25">
              ⚡
            </div>
            <h3 className="text-xl font-semibold mb-4">Lightning Fast</h3>
            <p className="text-gray-600">Experience blazing fast performance with optimized code</p>
          </div>
          <div className="group">
            <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-teal-600 rounded-xl mx-auto mb-6 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-green-500/25">
              🎨
            </div>
            <h3 className="text-xl font-semibold mb-4">Beautiful Design</h3>
            <p className="text-gray-600">Stunning visuals that captivate and engage users</p>
          </div>
          <div className="group">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl mx-auto mb-6 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-purple-500/25">
              🔒
            </div>
            <h3 className="text-xl font-semibold mb-4">Secure</h3>
            <p className="text-gray-600">Enterprise-grade security to protect your data</p>
          </div>
        </div>
      </div>'''
    
    def _generate_pricing_structure(self, components: List[str], responsive: bool) -> str:
        """Generate pricing section structure"""
        grid_classes = "grid grid-cols-1 md:grid-cols-3 gap-8" if responsive else "grid grid-cols-3 gap-8"
        
        return f'''      <div className="max-w-7xl mx-auto text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h2>
        <p className="text-xl text-gray-600 mb-16">Select the perfect plan for your needs</p>
        <div className="{grid_classes}">
          <Card className="p-8 relative">
            <h3 className="text-2xl font-bold mb-4">Starter</h3>
            <div className="text-4xl font-bold text-gray-900 mb-6">$29<span className="text-lg text-gray-600">/mo</span></div>
            <ul className="space-y-3 mb-8 text-left">
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Up to 5 projects</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 10GB storage</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Email support</li>
            </ul>
            <Button className="w-full">Get Started</Button>
          </Card>
          <Card className="p-8 border-2 border-blue-500 relative scale-105 shadow-xl shadow-blue-500/25">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
              Most Popular
            </div>
            <h3 className="text-2xl font-bold mb-4">Pro</h3>
            <div className="text-4xl font-bold text-gray-900 mb-6">$59<span className="text-lg text-gray-600">/mo</span></div>
            <ul className="space-y-3 mb-8 text-left">
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Unlimited projects</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 100GB storage</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Priority support</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Advanced features</li>
            </ul>
            <Button className="w-full bg-blue-500 hover:bg-blue-600">Get Started</Button>
          </Card>
          <Card className="p-8 relative">
            <h3 className="text-2xl font-bold mb-4">Enterprise</h3>
            <div className="text-4xl font-bold text-gray-900 mb-6">$99<span className="text-lg text-gray-600">/mo</span></div>
            <ul className="space-y-3 mb-8 text-left">
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Everything in Pro</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 1TB storage</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> 24/7 phone support</li>
              <li className="flex items-center"><span className="text-green-500 mr-2">✓</span> Custom integrations</li>
            </ul>
            <Button className="w-full">Contact Sales</Button>
          </Card>
        </div>
      </div>'''
    
    def _generate_generic_structure(self, components: List[str], responsive: bool) -> str:
        """Generate generic structure for unknown layouts"""
        return '''      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Components will be placed here */}
        </div>
      </div>'''
    
    def _apply_style_modifications(self, structure: str, style: DesignStyle) -> str:
        """Apply style-specific modifications to the structure"""
        
        if style == DesignStyle.GLASSMORPHISM:
            # Add glass effects to cards
            structure = structure.replace(
                'Card className="',
                'Card className="backdrop-blur-md bg-white/30 border border-white/20 '
            )
        elif style == DesignStyle.BOLD_VIBRANT:
            # Add vibrant gradients and shadows
            structure = structure.replace(
                'Card className="',
                'Card className="shadow-xl shadow-purple-500/25 '
            )
        elif style == DesignStyle.DARK_ELEGANT:
            # Apply dark theme modifications
            structure = structure.replace('text-gray-900', 'text-white')
            structure = structure.replace('text-gray-600', 'text-gray-300')
            
        return structure
    
    def _generate_component_name(self, layout_type: LayoutType) -> str:
        """Generate component name based on layout type"""
        names = {
            LayoutType.HERO_SECTION: "HeroSection",
            LayoutType.DASHBOARD: "DashboardLayout",
            LayoutType.CARD_GRID: "CardGrid", 
            LayoutType.FORM_LAYOUT: "FormLayout",
            LayoutType.NAVIGATION_LAYOUT: "NavigationLayout",
            LayoutType.FEATURE_SHOWCASE: "FeatureShowcase",
            LayoutType.PRICING_SECTION: "PricingSection",
            LayoutType.TESTIMONIAL_GRID: "TestimonialGrid",
            LayoutType.FOOTER_SECTION: "FooterSection"
        }
        
        return names.get(layout_type, "ComposedLayout")
    
    def _load_layout_patterns(self) -> Dict[LayoutType, Dict[str, Any]]:
        """Load predefined layout patterns"""
        return {
            LayoutType.HERO_SECTION: {
                "structure": "center-aligned",
                "elements": ["heading", "subtitle", "cta_buttons", "background"],
                "spacing": "generous"
            },
            LayoutType.DASHBOARD: {
                "structure": "grid-based",
                "elements": ["metrics", "charts", "tables", "actions"],
                "spacing": "compact"
            },
            LayoutType.CARD_GRID: {
                "structure": "responsive-grid",
                "elements": ["image", "title", "description", "action"],
                "spacing": "balanced"
            },
            LayoutType.CONTENT_SECTION: {
                "structure": "flexible",
                "elements": ["content", "media", "actions"],
                "spacing": "balanced"
            },
            LayoutType.FORM_LAYOUT: {
                "structure": "vertical",
                "elements": ["fields", "validation", "actions"],
                "spacing": "comfortable"
            },
            LayoutType.FEATURE_SHOWCASE: {
                "structure": "grid-showcase",
                "elements": ["icon", "title", "description"],
                "spacing": "generous"
            },
            LayoutType.PRICING_SECTION: {
                "structure": "comparison-grid",
                "elements": ["plan", "price", "features", "action"],
                "spacing": "balanced"
            }
        }
    
    def _load_responsive_patterns(self) -> Dict[str, Any]:
        """Load responsive design patterns"""
        return {
            "breakpoints": {
                "mobile": "max-width: 768px",
                "tablet": "768px - 1024px", 
                "desktop": "1024px+"
            },
            "grid_patterns": {
                "mobile_first": "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
                "desktop_first": "grid-cols-3 md:grid-cols-2 sm:grid-cols-1"
            }
        }
    
    def _load_animation_sequences(self) -> Dict[str, List[str]]:
        """Load animation sequence patterns"""
        return {
            "fade_in_sequence": ["animate-in", "fade-in", "duration-500", "stagger"],
            "slide_up_sequence": ["animate-in", "slide-in-from-bottom", "duration-700", "stagger"],
            "scale_sequence": ["animate-in", "zoom-in-95", "duration-300", "stagger"],
            "hero_sequence": ["animate-in", "fade-in", "slide-in-from-bottom", "duration-1000"]
        }