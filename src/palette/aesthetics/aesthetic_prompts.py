"""
Advanced Aesthetic Prompt System for Beautiful UI Generation

This module provides sophisticated design-focused prompts that ensure
generated components are visually stunning and follow modern design principles.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class DesignStyle(Enum):
    """Design style presets for different aesthetic approaches"""
    MODERN_MINIMAL = "modern_minimal"
    BOLD_VIBRANT = "bold_vibrant"
    ENTERPRISE = "enterprise"
    PLAYFUL = "playful"
    GLASSMORPHISM = "glassmorphism"
    NEUBRUTALISM = "neubrutalism"
    DARK_ELEGANT = "dark_elegant"


@dataclass
class AestheticConfig:
    """Configuration for aesthetic generation"""
    style: DesignStyle = DesignStyle.MODERN_MINIMAL
    enable_animations: bool = True
    enable_gradients: bool = True
    shadow_intensity: str = "medium"  # light, medium, heavy
    border_radius: str = "medium"  # none, small, medium, large, full
    color_vibrancy: str = "balanced"  # muted, balanced, vibrant


class AestheticPromptBuilder:
    """Builds design-focused prompts for beautiful UI generation"""
    
    def __init__(self):
        self.shadcn_patterns = self._load_shadcn_patterns()
        self.animation_patterns = self._load_animation_patterns()
        self.color_systems = self._load_color_systems()
        
    def build_aesthetic_prompt(self, 
                              component_type: str,
                              config: AestheticConfig,
                              context: Dict) -> str:
        """Build comprehensive aesthetic-focused prompt"""
        
        base_prompt = self._get_base_aesthetic_principles()
        style_prompt = self._get_style_specific_prompt(config.style)
        component_prompt = self._get_component_beauty_patterns(component_type)
        shadcn_prompt = self._get_shadcn_integration(component_type)
        animation_prompt = self._get_animation_patterns(config) if config.enable_animations else ""
        color_prompt = self._get_sophisticated_color_system(config, context)
        spacing_prompt = self._get_spacing_system()
        
        return f"""
{base_prompt}

{style_prompt}

{component_prompt}

{shadcn_prompt}

{color_prompt}

{spacing_prompt}

{animation_prompt}

CRITICAL VISUAL REQUIREMENTS:
✨ Every element must be visually polished and professional
🎨 Use consistent design tokens throughout
📐 Follow 8pt grid system strictly
🌈 Apply sophisticated color theory
✏️ Include subtle micro-interactions
🎯 Ensure visual hierarchy is clear
💫 Add delightful details that enhance UX
"""

    def _get_base_aesthetic_principles(self) -> str:
        """Core design principles for all components"""
        return """
🎨 MODERN DESIGN PRINCIPLES - MANDATORY FOR ALL COMPONENTS:

1. VISUAL HIERARCHY:
   - Clear primary, secondary, and tertiary elements
   - Use size, weight, and color to establish importance
   - Consistent spacing creates visual groupings
   - Z-index layers: base → card → modal → tooltip → notification

2. SOPHISTICATED SPACING (8pt Grid System):
   - Micro: p-1 (4px) for tight elements
   - Small: p-2 (8px) for compact spacing  
   - Medium: p-4 (16px) for standard spacing
   - Large: p-6 (24px) for section spacing
   - XL: p-8 (32px) for major sections
   - Container padding: px-4 sm:px-6 lg:px-8

3. PROFESSIONAL SHADOWS (Elevation System):
   - Subtle: shadow-sm (0 1px 2px rgba(0,0,0,0.05))
   - Card: shadow-md (0 4px 6px rgba(0,0,0,0.07))  
   - Raised: shadow-lg (0 10px 15px rgba(0,0,0,0.1))
   - Floating: shadow-xl (0 20px 25px rgba(0,0,0,0.1))
   - Use colored shadows for vibrant elements: shadow-xl shadow-blue-500/25

4. TYPOGRAPHY EXCELLENCE:
   - Clear hierarchy: text-xs → sm → base → lg → xl → 2xl → 3xl
   - Line height optimization: leading-tight for headings, leading-relaxed for body
   - Font weight progression: font-normal → medium → semibold → bold
   - Letter spacing: tracking-tight for headings, tracking-normal for body
   - Color contrast: text-gray-900 on light, text-white on dark

5. COLOR SOPHISTICATION:
   - Never use pure black (#000) or pure white (#FFF) - use gray-950 and gray-50
   - Maintain consistent color temperature
   - Use opacity for layering: bg-white/80, bg-black/50
   - Apply color psychology: blue for trust, green for success, red for urgency
"""

    def _get_style_specific_prompt(self, style: DesignStyle) -> str:
        """Style-specific design instructions"""
        styles = {
            DesignStyle.MODERN_MINIMAL: """
📱 MODERN MINIMAL STYLE:
- Abundant whitespace: Use negative space as a design element
- Subtle color palette: Mostly grays with one accent color
- Delicate shadows: shadow-sm to shadow-md maximum
- Clean lines: border border-gray-200 (1px borders)
- Refined typography: Clean, sans-serif, generous line-height
- Micro-animations: transition-all duration-200 ease-in-out
- Hover states: hover:bg-gray-50 (subtle background changes)
- Focus on content: Let content breathe with p-6 to p-8
- Monochromatic with accents: gray-50/100/200 with primary-500 accents
""",
            DesignStyle.BOLD_VIBRANT: """
🎯 BOLD & VIBRANT STYLE:
- Dynamic gradients: from-purple-500 via-pink-500 to-red-500
- Strong shadows: shadow-lg to shadow-2xl with colored shadows
- Vibrant colors: Use 400-600 range for backgrounds
- Bold typography: font-bold to font-black for headings
- Animated elements: animate-pulse, animate-bounce for CTAs
- High contrast: Dark elements on light, light on dark
- Geometric shapes: Use absolute positioned decorative elements
- Hover transformations: hover:scale-105 hover:-translate-y-1
- Energetic spacing: Tighter spacing for energy, p-3 to p-5
""",
            DesignStyle.ENTERPRISE: """
💼 ENTERPRISE PROFESSIONAL:
- Conservative colors: Blues, grays, subtle greens
- Structured layouts: Clear grid systems, aligned elements
- Readable typography: text-base to text-lg for body content
- Consistent borders: border border-gray-300 everywhere
- Subtle interactions: hover:bg-gray-100 transitions
- Data-focused: Tables, charts, metrics prominently displayed
- Accessibility first: High contrast, clear focus states
- Professional spacing: Consistent p-4 throughout
- Trust indicators: Badges, certifications, security icons
""",
            DesignStyle.GLASSMORPHISM: """
🔮 GLASSMORPHISM STYLE:
- Glass effects: backdrop-blur-md bg-white/30 dark:bg-gray-900/30
- Layered transparency: Multiple glass layers with different opacities
- Vibrant backgrounds: Gradient meshes behind glass panels
- Subtle borders: border border-white/20 for glass edges
- Soft shadows: shadow-xl for depth behind glass
- Light refraction: Use gradients within glass for light effects
- Frosted appearance: backdrop-saturate-150 for color enhancement
- Floating elements: Elements appear to float above background
- Depth layers: Create 3-4 distinct depth levels
""",
            DesignStyle.PLAYFUL: """
🎈 PLAYFUL & FUN STYLE:
- Rounded everything: rounded-2xl to rounded-full
- Bright colors: Use 400-500 range, multiple colors
- Bouncy animations: animate-bounce, custom spring animations
- Playful shadows: Colored shadows matching elements
- Hand-drawn effects: Slight rotations, imperfect alignments
- Fun typography: Mix weights, sizes playfully
- Interactive elements: Everything responds to hover/click
- Emoji integration: Use emojis as design elements
- Asymmetric layouts: Break the grid intentionally
"""
        }
        return styles.get(style, styles[DesignStyle.MODERN_MINIMAL])

    def _get_component_beauty_patterns(self, component_type: str) -> str:
        """Component-specific beauty patterns"""
        patterns = {
            "button": """
BUTTON BEAUTY PATTERNS:
- Primary: bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700
- Padding: px-6 py-3 for standard, px-4 py-2 for small, px-8 py-4 for large
- Shadows: shadow-lg shadow-blue-500/25 for primary buttons
- Transitions: transition-all duration-200 hover:scale-105 active:scale-95
- Icon integration: inline-flex items-center gap-2
- Loading states: animate-pulse or custom spinner
- Disabled: opacity-50 cursor-not-allowed
""",
            "card": """
CARD BEAUTY PATTERNS:
- Container: bg-white dark:bg-gray-800 rounded-xl to rounded-2xl
- Shadows: shadow-lg hover:shadow-xl transition-shadow duration-300
- Padding: p-6 for content, p-0 for image cards with p-6 for content area
- Image handling: aspect-video object-cover rounded-t-xl
- Hover lift: hover:-translate-y-1 transition-transform
- Border option: border border-gray-200 dark:border-gray-700
- Glass option: backdrop-blur-md bg-white/80 dark:bg-gray-900/80
""",
            "form": """
FORM BEAUTY PATTERNS:
- Input fields: rounded-lg border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20
- Field spacing: space-y-6 between form groups
- Labels: text-sm font-medium text-gray-700 mb-2
- Help text: text-xs text-gray-500 mt-1
- Error states: border-red-500 text-red-600 with error message
- Success states: border-green-500 with checkmark icon
- Floating labels: For modern look, use peer and peer-focus transforms
- Button alignment: justify-end for form actions
""",
            "hero": """
HERO SECTION BEAUTY PATTERNS:
- Background: bg-gradient-to-br from-blue-50 via-white to-purple-50
- Or mesh gradient: Multiple gradients with different blend modes
- Height: min-h-screen or h-[90vh] for impact
- Content layout: max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
- Typography: text-5xl to text-7xl for headings with font-bold
- Subtitle: text-xl to text-2xl text-gray-600 leading-relaxed
- CTA buttons: Large with strong shadows and hover effects
- Decorative elements: Absolute positioned shapes/gradients
- Image/illustration: w-full h-full object-cover with overlay gradients
""",
            "navbar": """
NAVIGATION BEAUTY PATTERNS:
- Container: backdrop-blur-md bg-white/90 dark:bg-gray-900/90 border-b
- Height: h-16 to h-20 for comfortable click targets
- Logo area: font-bold text-xl with optional gradient text
- Menu items: px-4 py-2 hover:bg-gray-100 rounded-lg transitions
- Active state: bg-blue-50 text-blue-600 or bottom border indicator
- Mobile menu: Slide from right with overlay backdrop
- Sticky behavior: sticky top-0 z-50 with shadow on scroll
- Icons: Consistent 20x20 or 24x24 size with hover colors
"""
        }
        
        # Return specific pattern or generic beautiful component pattern
        return patterns.get(component_type, """
GENERIC COMPONENT BEAUTY:
- Consistent rounded corners: rounded-lg to rounded-xl
- Proper shadows: shadow-md for depth
- Smooth transitions: transition-all duration-200
- Hover states: Subtle color/shadow changes
- Focus states: ring-2 ring-offset-2 ring-blue-500
- Padding harmony: Use consistent padding scale
""")

    def _get_shadcn_integration(self, component_type: str) -> str:
        """shadcn/ui specific patterns for consistency with v0.dev"""
        return f"""
🎯 SHADCN/UI INTEGRATION (Follow v0.dev patterns):

Component Structure:
- Use shadcn/ui component patterns when available
- Apply cn() utility for className merging: cn("base-classes", conditional && "conditional-classes")
- Implement forwardRef for all components
- Use Radix UI primitives for complex interactions

Specific shadcn patterns for {component_type}:
- Import from @/components/ui/{component_type} if it exists
- Use CSS variables for theming: --background, --foreground, --primary, etc.
- Apply consistent variants: default, secondary, outline, ghost, link
- Size variants: default, sm, lg following shadcn conventions
- Destructure props with ...props for extensibility

Example structure:
```tsx
const {component_type.capitalize()} = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {{
    variant?: "default" | "secondary" | "outline"
    size?: "default" | "sm" | "lg"
  }}
>({{ className, variant = "default", size = "default", ...props }}, ref) => (
  <div
    ref={{ref}}
    className={{cn(
      {component_type}Variants({{ variant, size }}),
      className
    )}}
    {{...props}}
  />
))
```
"""

    def _get_animation_patterns(self, config: AestheticConfig) -> str:
        """Animation and micro-interaction patterns"""
        if not config.enable_animations:
            return ""
            
        return """
✨ ANIMATION & MICRO-INTERACTIONS:

Entrance Animations:
- Fade in: animate-in fade-in duration-500
- Slide up: animate-in slide-in-from-bottom duration-500
- Scale: animate-in zoom-in-90 duration-300
- Stagger children: [&>*]:animate-in [&>*]:slide-in-from-bottom [&>*]:stagger

Hover Interactions:
- Lift: hover:-translate-y-1 transition-transform duration-200
- Scale: hover:scale-105 transition-transform duration-200
- Glow: hover:shadow-xl hover:shadow-blue-500/25 transition-shadow
- Color shift: hover:bg-gradient-to-r hover:from-blue-500 hover:to-purple-500

Loading States:
- Skeleton: animate-pulse bg-gray-200 rounded
- Spinner: animate-spin for rotating elements
- Dots: animate-bounce with animation-delay for sequence
- Progress: transition-all duration-300 for width changes

Micro-interactions:
- Button press: active:scale-95 transition-transform
- Focus ring: focus:ring-2 focus:ring-offset-2 transition-all
- Toggle: transition-all duration-200 for state changes
- Tooltip: opacity-0 hover:opacity-100 transition-opacity

Advanced Animations:
- Parallax: transform-gpu for smooth performance
- Morphing: transition-all duration-500 for shape changes
- Spring physics: Use custom CSS with spring easing
- Sequence: animation-delay-100, animation-delay-200, etc.
"""

    def _get_sophisticated_color_system(self, config: AestheticConfig, context: Dict) -> str:
        """Advanced color theory and gradient systems"""
        project_colors = context.get('design_tokens', {}).get('colors', [])
        
        return f"""
🎨 SOPHISTICATED COLOR SYSTEM:

Color Harmony Rules:
- Primary: Use 500-600 for main actions
- Secondary: Use 100-200 for backgrounds, 700-800 for text
- Accent: Complementary color at 30% saturation of primary
- Neutral: gray-50 to gray-900 palette
- Never use pure black/white: gray-950/gray-50 instead

Beautiful Gradients:
1. Subtle Background Gradients:
   - from-gray-50 to-white (light mode)
   - from-gray-900 to-gray-800 (dark mode)
   - from-blue-50 to-indigo-50 (colored tint)
   - from-white via-gray-50 to-white (subtle wave)

2. Vibrant Accent Gradients:
   - from-blue-400 via-blue-500 to-indigo-600 (professional)
   - from-purple-400 via-pink-500 to-red-500 (creative)
   - from-green-400 to-blue-500 (fresh)
   - from-yellow-400 via-red-500 to-pink-500 (warm)

3. Mesh Gradients (Advanced):
   - Multiple gradients with mix-blend-mode
   - Radial gradients: bg-gradient-radial for orbs
   - Conic gradients: bg-gradient-conic for unique effects

4. Glass Effects:
   - backdrop-blur-md bg-white/30 (light glass)
   - backdrop-blur-xl bg-gray-900/50 (dark glass)
   - border border-white/20 for glass edges

Color Application:
- Text: High contrast (gray-900 on light, white on dark)
- Borders: Subtle (gray-200 light, gray-700 dark)
- Shadows: Colored shadows for vibrancy (shadow-blue-500/25)
- Overlays: Use opacity (bg-black/50) instead of solid colors

Project Colors Available: {', '.join(project_colors[:5]) if project_colors else 'blue, indigo, purple'}
"""

    def _get_spacing_system(self) -> str:
        """Consistent spacing system based on 8pt grid"""
        return """
📐 SPACING SYSTEM (8pt Grid):

Padding Scale:
- p-0: 0px (no padding)
- p-1: 4px (micro spacing)
- p-2: 8px (compact)
- p-3: 12px (snug)
- p-4: 16px (comfortable)
- p-5: 20px (relaxed)
- p-6: 24px (spacious)
- p-8: 32px (generous)
- p-10: 40px (extra spacious)
- p-12: 48px (hero sections)

Margin Scale:
- Use negative margins for overlaps: -mt-8
- Section spacing: my-16 to my-24
- Component spacing: mb-4 to mb-8
- Inline spacing: gap-2 to gap-4 in flex/grid

Container Standards:
- max-w-7xl mx-auto for main containers
- px-4 sm:px-6 lg:px-8 for responsive padding
- Container queries for responsive components

Grid Systems:
- grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4
- gap-4 to gap-8 for grid spacing
- Use aspect-ratio for consistent card heights
"""

    def _load_shadcn_patterns(self) -> Dict:
        """Load shadcn/ui component patterns"""
        return {
            "button": {
                "variants": ["default", "destructive", "outline", "secondary", "ghost", "link"],
                "sizes": ["default", "sm", "lg", "icon"],
                "classes": "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
            },
            "card": {
                "classes": "rounded-lg border bg-card text-card-foreground shadow-sm",
                "header": "flex flex-col space-y-1.5 p-6",
                "content": "p-6 pt-0"
            },
            "input": {
                "classes": "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            }
        }

    def _load_animation_patterns(self) -> Dict:
        """Load animation pattern library"""
        return {
            "fade": "animate-in fade-in duration-500",
            "slide": "animate-in slide-in-from-bottom duration-500",
            "scale": "animate-in zoom-in-95 duration-300",
            "bounce": "animate-bounce",
            "pulse": "animate-pulse",
            "spin": "animate-spin"
        }

    def _load_color_systems(self) -> Dict:
        """Load sophisticated color systems"""
        return {
            "monochromatic": {
                "base": "gray",
                "shades": [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
            },
            "complementary": {
                "primary": "blue-500",
                "secondary": "orange-500"
            },
            "triadic": {
                "primary": "blue-500",
                "secondary": "red-500",
                "tertiary": "yellow-500"
            },
            "analogous": {
                "primary": "blue-500",
                "secondary": "indigo-500",
                "tertiary": "violet-500"
            }
        }


def get_design_style_from_prompt(prompt: str) -> DesignStyle:
    """Determine design style from user prompt"""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ["minimal", "clean", "simple", "minimalist"]):
        return DesignStyle.MODERN_MINIMAL
    elif any(word in prompt_lower for word in ["bold", "vibrant", "colorful", "dynamic"]):
        return DesignStyle.BOLD_VIBRANT
    elif any(word in prompt_lower for word in ["professional", "enterprise", "corporate", "business"]):
        return DesignStyle.ENTERPRISE
    elif any(word in prompt_lower for word in ["playful", "fun", "friendly", "casual"]):
        return DesignStyle.PLAYFUL
    elif any(word in prompt_lower for word in ["glass", "glassmorphism", "transparent", "blur"]):
        return DesignStyle.GLASSMORPHISM
    elif any(word in prompt_lower for word in ["dark", "elegant", "sophisticated", "luxury"]):
        return DesignStyle.DARK_ELEGANT
    elif any(word in prompt_lower for word in ["brutalist", "neubrutalism", "bold typography"]):
        return DesignStyle.NEUBRUTALISM
    
    return DesignStyle.MODERN_MINIMAL  # Default to modern minimal