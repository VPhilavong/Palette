"""
Design System Semantic Analyzer - Deep understanding of design systems and their relationships.
Analyzes design tokens, color theory, typography scales, and spatial relationships.
"""

import colorsys
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..errors.decorators import handle_errors


class ColorRole(Enum):
    """Semantic roles for colors in a design system."""
    
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    NEUTRAL = "neutral"
    SEMANTIC_SUCCESS = "success"
    SEMANTIC_WARNING = "warning"
    SEMANTIC_ERROR = "error"
    SEMANTIC_INFO = "info"
    BACKGROUND = "background"
    SURFACE = "surface"
    TEXT = "text"
    BORDER = "border"
    SHADOW = "shadow"


class SpacingRole(Enum):
    """Semantic roles for spacing values."""
    
    NONE = "none"
    TIGHT = "tight"
    COMFORTABLE = "comfortable"
    LOOSE = "loose"
    SECTION = "section"
    LAYOUT = "layout"


class TypographyRole(Enum):
    """Semantic roles for typography."""
    
    DISPLAY = "display"
    HEADING = "heading"
    BODY = "body"
    CAPTION = "caption"
    OVERLINE = "overline"
    BUTTON = "button"
    LABEL = "label"


@dataclass
class ColorAnalysis:
    """Analysis of a color and its properties."""
    
    name: str
    hex_value: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[float, float, float]
    role: Optional[ColorRole] = None
    luminance: float = 0.0
    is_light: bool = False
    contrast_ratio_with_black: float = 0.0
    contrast_ratio_with_white: float = 0.0
    complementary_color: Optional[str] = None
    analogous_colors: List[str] = field(default_factory=list)
    triadic_colors: List[str] = field(default_factory=list)
    accessibility_level: str = "fail"  # "fail", "aa", "aaa"


@dataclass
class SpacingAnalysis:
    """Analysis of spacing values and their relationships."""
    
    name: str
    value: str  # e.g., "16px", "1rem", "0.5em"
    pixels: float  # Normalized to pixels
    role: Optional[SpacingRole] = None
    scale_position: int = 0  # Position in the spacing scale
    ratio_to_base: float = 1.0  # Ratio relative to base spacing
    use_cases: List[str] = field(default_factory=list)


@dataclass
class TypographyAnalysis:
    """Analysis of typography styles."""
    
    name: str
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    font_family: Optional[str] = None
    letter_spacing: Optional[str] = None
    role: Optional[TypographyRole] = None
    scale_ratio: float = 1.0
    accessibility_considerations: List[str] = field(default_factory=list)


@dataclass
class DesignSystemAnalysis:
    """Comprehensive analysis of a design system."""
    
    colors: Dict[str, ColorAnalysis] = field(default_factory=dict)
    spacing: Dict[str, SpacingAnalysis] = field(default_factory=dict)
    typography: Dict[str, TypographyAnalysis] = field(default_factory=dict)
    
    # Derived insights
    color_palette_type: str = "unknown"  # "monochromatic", "complementary", "triadic", etc.
    primary_color_family: Optional[str] = None
    spacing_scale_type: str = "unknown"  # "linear", "geometric", "fibonacci", etc.
    typography_scale_ratio: float = 1.0
    
    # Semantic relationships
    color_relationships: Dict[str, List[str]] = field(default_factory=dict)
    spacing_relationships: Dict[str, List[str]] = field(default_factory=dict)
    typography_hierarchy: List[str] = field(default_factory=list)
    
    # Brand characteristics
    brand_personality: List[str] = field(default_factory=list)  # "professional", "playful", etc.
    accessibility_compliance: str = "unknown"  # "AA", "AAA", "partial", "poor"
    consistency_score: float = 0.0  # 0-1 score for system consistency


class DesignSystemAnalyzer:
    """
    Analyzes design systems to understand semantic relationships and provide intelligent suggestions.
    """
    
    def __init__(self):
        self.color_analyzer = ColorSemanticAnalyzer()
        self.spacing_analyzer = SpacingSemanticAnalyzer()
        self.typography_analyzer = TypographySemanticAnalyzer()
    
    @handle_errors(reraise=True)
    def analyze_design_system(self, design_tokens: Dict[str, Any]) -> DesignSystemAnalysis:
        """
        Perform comprehensive analysis of a design system.
        
        Args:
            design_tokens: Design tokens from the project
            
        Returns:
            Comprehensive design system analysis
        """
        analysis = DesignSystemAnalysis()
        
        # Analyze colors
        if design_tokens.get('colors'):
            colors = design_tokens['colors']
            if isinstance(colors, dict):
                for name, value in colors.items():
                    color_analysis = self.color_analyzer.analyze_color(name, value)
                    analysis.colors[name] = color_analysis
            elif isinstance(colors, list):
                for color in colors:
                    if isinstance(color, dict) and 'name' in color and 'value' in color:
                        color_analysis = self.color_analyzer.analyze_color(color['name'], color['value'])
                        analysis.colors[color['name']] = color_analysis
        
        # Analyze spacing
        if design_tokens.get('spacing'):
            spacing = design_tokens['spacing']
            if isinstance(spacing, dict):
                for name, value in spacing.items():
                    spacing_analysis = self.spacing_analyzer.analyze_spacing(name, value)
                    analysis.spacing[name] = spacing_analysis
            elif isinstance(spacing, list):
                for i, value in enumerate(spacing):
                    name = f"spacing-{i}"
                    spacing_analysis = self.spacing_analyzer.analyze_spacing(name, value)
                    analysis.spacing[name] = spacing_analysis
        
        # Analyze typography
        if design_tokens.get('typography'):
            typography = design_tokens['typography']
            if isinstance(typography, dict):
                for name, styles in typography.items():
                    if isinstance(styles, dict):
                        typography_analysis = self.typography_analyzer.analyze_typography(name, styles)
                        analysis.typography[name] = typography_analysis
        
        # Derive higher-level insights
        self._derive_color_insights(analysis)
        self._derive_spacing_insights(analysis)
        self._derive_typography_insights(analysis)
        self._derive_brand_insights(analysis)
        self._calculate_consistency_score(analysis)
        
        return analysis
    
    def _derive_color_insights(self, analysis: DesignSystemAnalysis):
        """Derive insights about the color system."""
        colors = list(analysis.colors.values())
        if not colors:
            return
        
        # Determine primary color family
        color_families = {}
        for color in colors:
            hue = color.hsl[0]
            family = self._get_color_family(hue)
            if family not in color_families:
                color_families[family] = 0
            color_families[family] += 1
        
        analysis.primary_color_family = max(color_families.items(), key=lambda x: x[1])[0]
        
        # Analyze color palette type
        hues = [color.hsl[0] for color in colors if color.role not in [ColorRole.NEUTRAL, ColorRole.TEXT]]
        if len(hues) >= 2:
            analysis.color_palette_type = self._determine_palette_type(hues)
        
        # Build color relationships
        for color in colors:
            related = []
            for other_color in colors:
                if color.name != other_color.name:
                    relationship = self._get_color_relationship(color, other_color)
                    if relationship:
                        related.append(f"{other_color.name} ({relationship})")
            analysis.color_relationships[color.name] = related
        
        # Assess accessibility
        accessibility_scores = []
        for color in colors:
            if color.role in [ColorRole.TEXT, ColorRole.PRIMARY, ColorRole.SECONDARY]:
                if color.accessibility_level == "aaa":
                    accessibility_scores.append(3)
                elif color.accessibility_level == "aa":
                    accessibility_scores.append(2)
                else:
                    accessibility_scores.append(1)
        
        if accessibility_scores:
            avg_score = sum(accessibility_scores) / len(accessibility_scores)
            if avg_score >= 2.5:
                analysis.accessibility_compliance = "AAA"
            elif avg_score >= 2.0:
                analysis.accessibility_compliance = "AA"
            elif avg_score >= 1.5:
                analysis.accessibility_compliance = "partial"
            else:
                analysis.accessibility_compliance = "poor"
    
    def _derive_spacing_insights(self, analysis: DesignSystemAnalysis):
        """Derive insights about the spacing system."""
        spacing_values = list(analysis.spacing.values())
        if len(spacing_values) < 3:
            return
        
        # Sort by pixel value
        sorted_spacing = sorted(spacing_values, key=lambda x: x.pixels)
        
        # Determine scale type
        ratios = []
        for i in range(1, len(sorted_spacing)):
            if sorted_spacing[i-1].pixels > 0:
                ratio = sorted_spacing[i].pixels / sorted_spacing[i-1].pixels
                ratios.append(ratio)
        
        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            ratio_variance = sum((r - avg_ratio) ** 2 for r in ratios) / len(ratios)
            
            if ratio_variance < 0.1:  # Low variance = consistent ratio
                if abs(avg_ratio - 1.618) < 0.2:  # Golden ratio
                    analysis.spacing_scale_type = "golden_ratio"
                elif abs(avg_ratio - 1.5) < 0.1:
                    analysis.spacing_scale_type = "major_third"
                elif abs(avg_ratio - 1.414) < 0.1:  # √2
                    analysis.spacing_scale_type = "major_second"
                else:
                    analysis.spacing_scale_type = "geometric"
            elif all(abs(r - 1.0) < 0.1 for r in ratios):  # Linear progression
                analysis.spacing_scale_type = "linear"
            else:
                analysis.spacing_scale_type = "custom"
        
        # Build spacing relationships
        for spacing in spacing_values:
            related = []
            for other_spacing in spacing_values:
                if spacing.name != other_spacing.name:
                    relationship = self._get_spacing_relationship(spacing, other_spacing)
                    if relationship:
                        related.append(f"{other_spacing.name} ({relationship})")
            analysis.spacing_relationships[spacing.name] = related
    
    def _derive_typography_insights(self, analysis: DesignSystemAnalysis):
        """Derive insights about the typography system."""
        typography_values = list(analysis.typography.values())
        if not typography_values:
            return
        
        # Determine typography hierarchy
        role_order = [
            TypographyRole.DISPLAY,
            TypographyRole.HEADING,
            TypographyRole.BODY,
            TypographyRole.CAPTION,
            TypographyRole.OVERLINE
        ]
        
        hierarchy = []
        for role in role_order:
            for typo in typography_values:
                if typo.role == role:
                    hierarchy.append(typo.name)
        
        # Add any remaining typography styles
        for typo in typography_values:
            if typo.name not in hierarchy:
                hierarchy.append(typo.name)
        
        analysis.typography_hierarchy = hierarchy
        
        # Calculate scale ratio
        font_sizes = []
        for typo in typography_values:
            if typo.font_size:
                size_px = self._parse_font_size_to_px(typo.font_size)
                if size_px:
                    font_sizes.append(size_px)
        
        if len(font_sizes) >= 2:
            font_sizes.sort()
            ratios = []
            for i in range(1, len(font_sizes)):
                ratio = font_sizes[i] / font_sizes[i-1]
                ratios.append(ratio)
            
            if ratios:
                analysis.typography_scale_ratio = sum(ratios) / len(ratios)
    
    def _derive_brand_insights(self, analysis: DesignSystemAnalysis):
        """Derive brand personality insights from the design system."""
        personality_traits = []
        
        # Analyze color personality
        colors = list(analysis.colors.values())
        if colors:
            # Check for bright, saturated colors
            high_saturation_count = sum(1 for c in colors if c.hsl[1] > 0.7)
            if high_saturation_count > len(colors) * 0.3:
                personality_traits.append("energetic")
            
            # Check for muted colors
            low_saturation_count = sum(1 for c in colors if c.hsl[1] < 0.3)
            if low_saturation_count > len(colors) * 0.5:
                personality_traits.append("sophisticated")
            
            # Check for warm vs cool colors
            warm_colors = sum(1 for c in colors if 0 <= c.hsl[0] <= 60 or 300 <= c.hsl[0] <= 360)
            cool_colors = sum(1 for c in colors if 180 <= c.hsl[0] <= 300)
            
            if warm_colors > cool_colors * 1.5:
                personality_traits.append("warm")
            elif cool_colors > warm_colors * 1.5:
                personality_traits.append("cool")
        
        # Analyze spacing personality
        spacing_values = list(analysis.spacing.values())
        if spacing_values:
            avg_spacing = sum(s.pixels for s in spacing_values) / len(spacing_values)
            if avg_spacing > 20:
                personality_traits.append("spacious")
            elif avg_spacing < 8:
                personality_traits.append("compact")
        
        # Analyze typography personality
        typography_values = list(analysis.typography.values())
        if typography_values:
            # Check for serif vs sans-serif
            serif_count = sum(1 for t in typography_values 
                            if t.font_family and 'serif' in t.font_family.lower() and 'sans' not in t.font_family.lower())
            if serif_count > 0:
                personality_traits.append("traditional")
            else:
                personality_traits.append("modern")
        
        analysis.brand_personality = list(set(personality_traits))
    
    def _calculate_consistency_score(self, analysis: DesignSystemAnalysis):
        """Calculate overall consistency score for the design system."""
        scores = []
        
        # Color consistency
        if analysis.colors:
            # Check for consistent color roles
            role_counts = {}
            for color in analysis.colors.values():
                if color.role:
                    role_counts[color.role] = role_counts.get(color.role, 0) + 1
            
            # Penalize having too many primary colors, etc.
            color_score = 1.0
            if role_counts.get(ColorRole.PRIMARY, 0) > 2:
                color_score -= 0.2
            if role_counts.get(ColorRole.SECONDARY, 0) > 2:
                color_score -= 0.1
            
            scores.append(max(0.0, color_score))
        
        # Spacing consistency
        if analysis.spacing and analysis.spacing_scale_type != "custom":
            # Geometric or mathematical scales get higher scores
            if analysis.spacing_scale_type in ["golden_ratio", "geometric", "major_third"]:
                scores.append(0.9)
            elif analysis.spacing_scale_type == "linear":
                scores.append(0.7)
            else:
                scores.append(0.5)
        
        # Typography consistency
        if analysis.typography and analysis.typography_scale_ratio > 0:
            # Consistent scale ratios get higher scores
            if 1.2 <= analysis.typography_scale_ratio <= 1.8:
                scores.append(0.8)
            else:
                scores.append(0.6)
        
        analysis.consistency_score = sum(scores) / len(scores) if scores else 0.0
    
    def _get_color_family(self, hue: float) -> str:
        """Get color family name from hue."""
        if 0 <= hue < 30 or 330 <= hue <= 360:
            return "red"
        elif 30 <= hue < 60:
            return "orange"
        elif 60 <= hue < 90:
            return "yellow"
        elif 90 <= hue < 150:
            return "green"
        elif 150 <= hue < 210:
            return "cyan"
        elif 210 <= hue < 270:
            return "blue"
        elif 270 <= hue < 330:
            return "purple"
        else:
            return "unknown"
    
    def _determine_palette_type(self, hues: List[float]) -> str:
        """Determine the type of color palette."""
        if len(hues) < 2:
            return "monochromatic"
        
        # Check for complementary (opposite hues)
        for i, hue1 in enumerate(hues):
            for hue2 in hues[i+1:]:
                diff = abs(hue1 - hue2)
                if 150 <= diff <= 210:  # Roughly opposite
                    return "complementary"
        
        # Check for triadic (120° apart)
        if len(hues) >= 3:
            sorted_hues = sorted(hues)
            for i in range(len(sorted_hues) - 2):
                if (abs(sorted_hues[i+1] - sorted_hues[i]) >= 100 and
                    abs(sorted_hues[i+2] - sorted_hues[i+1]) >= 100):
                    return "triadic"
        
        # Check for analogous (adjacent hues)
        hue_range = max(hues) - min(hues)
        if hue_range <= 60:
            return "analogous"
        
        return "complex"
    
    def _get_color_relationship(self, color1: ColorAnalysis, color2: ColorAnalysis) -> Optional[str]:
        """Get the relationship between two colors."""
        hue_diff = abs(color1.hsl[0] - color2.hsl[0])
        sat_diff = abs(color1.hsl[1] - color2.hsl[1])
        light_diff = abs(color1.hsl[2] - color2.hsl[2])
        
        # Complementary
        if 150 <= hue_diff <= 210:
            return "complementary"
        
        # Analogous
        if hue_diff <= 30:
            return "analogous"
        
        # Triadic
        if 110 <= hue_diff <= 130:
            return "triadic"
        
        # Similar lightness
        if light_diff <= 0.1 and sat_diff <= 0.2:
            return "similar_tone"
        
        # High contrast
        if light_diff >= 0.7:
            return "high_contrast"
        
        return None
    
    def _get_spacing_relationship(self, spacing1: SpacingAnalysis, spacing2: SpacingAnalysis) -> Optional[str]:
        """Get the relationship between two spacing values."""
        ratio = max(spacing1.pixels, spacing2.pixels) / min(spacing1.pixels, spacing2.pixels)
        
        if abs(ratio - 2.0) < 0.1:
            return "double"
        elif abs(ratio - 1.5) < 0.1:
            return "1.5x"
        elif abs(ratio - 1.618) < 0.1:
            return "golden_ratio"
        elif abs(ratio - 1.414) < 0.1:
            return "√2"
        elif ratio > 3:
            return "much_larger"
        
        return None
    
    def _parse_font_size_to_px(self, font_size: str) -> Optional[float]:
        """Parse font size string to pixels."""
        if not font_size:
            return None
        
        # Remove spaces and convert to lowercase
        size = font_size.strip().lower()
        
        # Parse pixel values
        if size.endswith('px'):
            try:
                return float(size[:-2])
            except ValueError:
                return None
        
        # Parse rem values (assume 16px base)
        if size.endswith('rem'):
            try:
                return float(size[:-3]) * 16
            except ValueError:
                return None
        
        # Parse em values (assume 16px base)
        if size.endswith('em'):
            try:
                return float(size[:-2]) * 16
            except ValueError:
                return None
        
        # Try to parse as just a number (assume pixels)
        try:
            return float(size)
        except ValueError:
            return None
    
    def generate_design_recommendations(self, analysis: DesignSystemAnalysis, user_request: str) -> List[str]:
        """Generate design recommendations based on the analysis and user request."""
        recommendations = []
        request_lower = user_request.lower()
        
        # Color recommendations
        if analysis.colors:
            if analysis.accessibility_compliance in ["poor", "partial"]:
                recommendations.append(
                    "Consider improving color contrast ratios for better accessibility compliance"
                )
            
            if analysis.primary_color_family:
                recommendations.append(
                    f"Your primary color family is {analysis.primary_color_family}. "
                    f"Consider using {analysis.primary_color_family} tones for primary actions and highlights"
                )
            
            # Context-specific color recommendations
            if "button" in request_lower:
                primary_colors = [c for c in analysis.colors.values() if c.role == ColorRole.PRIMARY]
                if primary_colors:
                    recommendations.append(
                        f"Use {primary_colors[0].name} for primary buttons to maintain brand consistency"
                    )
        
        # Spacing recommendations
        if analysis.spacing:
            if analysis.spacing_scale_type == "geometric":
                recommendations.append(
                    "Your spacing system uses a geometric scale. Maintain this ratio for consistent visual rhythm"
                )
            elif analysis.spacing_scale_type == "custom":
                recommendations.append(
                    "Consider adopting a more systematic spacing scale (geometric or linear) for better consistency"
                )
        
        # Typography recommendations
        if analysis.typography:
            if analysis.typography_scale_ratio > 0:
                recommendations.append(
                    f"Your typography scale ratio is {analysis.typography_scale_ratio:.2f}. "
                    f"Use this ratio when adding new text styles"
                )
        
        # Brand personality recommendations
        if analysis.brand_personality:
            personality = ", ".join(analysis.brand_personality)
            recommendations.append(
                f"Your design system has a {personality} personality. "
                f"Ensure new components align with this brand character"
            )
        
        return recommendations[:5]  # Top 5 recommendations


class ColorSemanticAnalyzer:
    """Analyzes colors and their semantic meaning."""
    
    def analyze_color(self, name: str, value: str) -> ColorAnalysis:
        """Analyze a single color."""
        # Parse hex color
        hex_value = self._normalize_hex_color(value)
        rgb = self._hex_to_rgb(hex_value)
        hsl = self._rgb_to_hsl(*rgb)
        
        # Calculate luminance and contrast ratios
        luminance = self._calculate_luminance(*rgb)
        contrast_black = self._calculate_contrast_ratio(luminance, 0.0)
        contrast_white = self._calculate_contrast_ratio(luminance, 1.0)
        
        # Determine accessibility level
        accessibility_level = "fail"
        if contrast_white >= 7.0 or contrast_black >= 7.0:
            accessibility_level = "aaa"
        elif contrast_white >= 4.5 or contrast_black >= 4.5:
            accessibility_level = "aa"
        
        # Determine semantic role
        role = self._infer_color_role(name, hsl)
        
        return ColorAnalysis(
            name=name,
            hex_value=hex_value,
            rgb=rgb,
            hsl=hsl,
            role=role,
            luminance=luminance,
            is_light=luminance > 0.5,
            contrast_ratio_with_black=contrast_black,
            contrast_ratio_with_white=contrast_white,
            accessibility_level=accessibility_level
        )
    
    def _normalize_hex_color(self, color: str) -> str:
        """Normalize color to hex format."""
        color = color.strip()
        if color.startswith('#'):
            return color.upper()
        elif color.startswith('rgb'):
            # Parse rgb() format
            match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
            if match:
                r, g, b = map(int, match.groups())
                return f"#{r:02X}{g:02X}{b:02X}"
        
        # Assume it's already a hex color without #
        return f"#{color.upper()}"
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSL."""
        r, g, b = r/255.0, g/255.0, b/255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        return (h * 360, s, l)
    
    def _calculate_luminance(self, r: int, g: int, b: int) -> float:
        """Calculate relative luminance of a color."""
        def linearize(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r_lin = linearize(r)
        g_lin = linearize(g)
        b_lin = linearize(b)
        
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
    
    def _calculate_contrast_ratio(self, lum1: float, lum2: float) -> float:
        """Calculate contrast ratio between two luminance values."""
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)
    
    def _infer_color_role(self, name: str, hsl: Tuple[float, float, float]) -> Optional[ColorRole]:
        """Infer the semantic role of a color from its name and properties."""
        name_lower = name.lower()
        
        # Direct role matches
        role_keywords = {
            ColorRole.PRIMARY: ['primary', 'brand', 'main'],
            ColorRole.SECONDARY: ['secondary', 'accent'],
            ColorRole.ACCENT: ['accent', 'highlight'],
            ColorRole.NEUTRAL: ['neutral', 'gray', 'grey'],
            ColorRole.SEMANTIC_SUCCESS: ['success', 'green', 'positive'],
            ColorRole.SEMANTIC_WARNING: ['warning', 'yellow', 'caution'],
            ColorRole.SEMANTIC_ERROR: ['error', 'danger', 'red', 'negative'],
            ColorRole.SEMANTIC_INFO: ['info', 'blue', 'information'],
            ColorRole.BACKGROUND: ['background', 'bg'],
            ColorRole.SURFACE: ['surface', 'card'],
            ColorRole.TEXT: ['text', 'foreground', 'fg'],
            ColorRole.BORDER: ['border', 'outline'],
            ColorRole.SHADOW: ['shadow', 'drop']
        }
        
        for role, keywords in role_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return role
        
        # Infer from HSL properties
        hue, saturation, lightness = hsl
        
        # Very light colors might be backgrounds
        if lightness > 0.9 and saturation < 0.1:
            return ColorRole.BACKGROUND
        
        # Very dark colors might be text
        if lightness < 0.2:
            return ColorRole.TEXT
        
        # Highly saturated colors might be primary/accent
        if saturation > 0.7:
            return ColorRole.PRIMARY if lightness < 0.7 else ColorRole.ACCENT
        
        # Low saturation colors might be neutral
        if saturation < 0.2:
            return ColorRole.NEUTRAL
        
        return None


class SpacingSemanticAnalyzer:
    """Analyzes spacing values and their semantic meaning."""
    
    def analyze_spacing(self, name: str, value: str) -> SpacingAnalysis:
        """Analyze a single spacing value."""
        pixels = self._parse_spacing_to_pixels(value)
        role = self._infer_spacing_role(name, pixels)
        
        # Determine use cases based on size
        use_cases = self._get_spacing_use_cases(pixels)
        
        return SpacingAnalysis(
            name=name,
            value=value,
            pixels=pixels,
            role=role,
            use_cases=use_cases
        )
    
    def _parse_spacing_to_pixels(self, value: str) -> float:
        """Parse spacing value to pixels."""
        if not value:
            return 0.0
        
        value = value.strip().lower()
        
        # Parse pixel values
        if value.endswith('px'):
            try:
                return float(value[:-2])
            except ValueError:
                return 0.0
        
        # Parse rem values (assume 16px base)
        if value.endswith('rem'):
            try:
                return float(value[:-3]) * 16
            except ValueError:
                return 0.0
        
        # Parse em values (assume 16px base)
        if value.endswith('em'):
            try:
                return float(value[:-2]) * 16
            except ValueError:
                return 0.0
        
        # Try to parse as number
        try:
            return float(value)
        except ValueError:
            return 0.0
    
    def _infer_spacing_role(self, name: str, pixels: float) -> Optional[SpacingRole]:
        """Infer the semantic role of a spacing value."""
        name_lower = name.lower()
        
        # Direct role matches
        if any(keyword in name_lower for keyword in ['none', 'zero']):
            return SpacingRole.NONE
        elif any(keyword in name_lower for keyword in ['tight', 'dense', 'compact']):
            return SpacingRole.TIGHT
        elif any(keyword in name_lower for keyword in ['comfortable', 'normal', 'default']):
            return SpacingRole.COMFORTABLE
        elif any(keyword in name_lower for keyword in ['loose', 'relaxed', 'spacious']):
            return SpacingRole.LOOSE
        elif any(keyword in name_lower for keyword in ['section', 'block']):
            return SpacingRole.SECTION
        elif any(keyword in name_lower for keyword in ['layout', 'container']):
            return SpacingRole.LAYOUT
        
        # Infer from pixel value
        if pixels == 0:
            return SpacingRole.NONE
        elif pixels <= 8:
            return SpacingRole.TIGHT
        elif pixels <= 16:
            return SpacingRole.COMFORTABLE
        elif pixels <= 32:
            return SpacingRole.LOOSE
        elif pixels <= 64:
            return SpacingRole.SECTION
        else:
            return SpacingRole.LAYOUT
    
    def _get_spacing_use_cases(self, pixels: float) -> List[str]:
        """Get typical use cases for a spacing value."""
        if pixels == 0:
            return ["Reset margins/padding", "No spacing needed"]
        elif pixels <= 4:
            return ["Icon spacing", "Text letter-spacing", "Border spacing"]
        elif pixels <= 8:
            return ["Small component padding", "List item spacing", "Icon-text gaps"]
        elif pixels <= 16:
            return ["Button padding", "Form field spacing", "Card padding"]
        elif pixels <= 24:
            return ["Component margins", "Grid gaps", "Content spacing"]
        elif pixels <= 32:
            return ["Section padding", "Large component margins", "Layout spacing"]
        elif pixels <= 48:
            return ["Page margins", "Major section spacing", "Container padding"]
        else:
            return ["Layout containers", "Page-level spacing", "Hero sections"]


class TypographySemanticAnalyzer:
    """Analyzes typography styles and their semantic meaning."""
    
    def analyze_typography(self, name: str, styles: Dict[str, Any]) -> TypographyAnalysis:
        """Analyze a typography style."""
        role = self._infer_typography_role(name, styles)
        accessibility_considerations = self._get_accessibility_considerations(styles)
        
        return TypographyAnalysis(
            name=name,
            font_size=styles.get('fontSize'),
            font_weight=styles.get('fontWeight'),
            line_height=styles.get('lineHeight'),
            font_family=styles.get('fontFamily'),
            letter_spacing=styles.get('letterSpacing'),
            role=role,
            accessibility_considerations=accessibility_considerations
        )
    
    def _infer_typography_role(self, name: str, styles: Dict[str, Any]) -> Optional[TypographyRole]:
        """Infer the semantic role of a typography style."""
        name_lower = name.lower()
        
        # Direct role matches
        role_keywords = {
            TypographyRole.DISPLAY: ['display', 'hero', 'title'],
            TypographyRole.HEADING: ['heading', 'header', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
            TypographyRole.BODY: ['body', 'text', 'paragraph', 'content'],
            TypographyRole.CAPTION: ['caption', 'small', 'meta', 'subtitle'],
            TypographyRole.OVERLINE: ['overline', 'eyebrow', 'kicker'],
            TypographyRole.BUTTON: ['button', 'action', 'cta'],
            TypographyRole.LABEL: ['label', 'form', 'input']
        }
        
        for role, keywords in role_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return role
        
        # Infer from font size
        font_size = styles.get('fontSize', '')
        if font_size:
            size_px = self._parse_font_size_to_px(font_size)
            if size_px:
                if size_px >= 32:
                    return TypographyRole.DISPLAY
                elif size_px >= 24:
                    return TypographyRole.HEADING
                elif size_px >= 14:
                    return TypographyRole.BODY
                else:
                    return TypographyRole.CAPTION
        
        return None
    
    def _parse_font_size_to_px(self, font_size: str) -> Optional[float]:
        """Parse font size to pixels (same as in main analyzer)."""
        if not font_size:
            return None
        
        size = font_size.strip().lower()
        
        if size.endswith('px'):
            try:
                return float(size[:-2])
            except ValueError:
                return None
        elif size.endswith('rem'):
            try:
                return float(size[:-3]) * 16
            except ValueError:
                return None
        elif size.endswith('em'):
            try:
                return float(size[:-2]) * 16
            except ValueError:
                return None
        
        try:
            return float(size)
        except ValueError:
            return None
    
    def _get_accessibility_considerations(self, styles: Dict[str, Any]) -> List[str]:
        """Get accessibility considerations for typography styles."""
        considerations = []
        
        # Check font size
        font_size = styles.get('fontSize', '')
        if font_size:
            size_px = self._parse_font_size_to_px(font_size)
            if size_px and size_px < 16:
                considerations.append("Font size may be too small for accessibility (recommend 16px minimum)")
        
        # Check line height
        line_height = styles.get('lineHeight')
        if line_height:
            try:
                lh_value = float(line_height)
                if lh_value < 1.2:
                    considerations.append("Line height may be too tight (recommend 1.4-1.6 for body text)")
            except ValueError:
                pass
        
        # Check font weight
        font_weight = styles.get('fontWeight')
        if font_weight:
            try:
                weight = int(font_weight)
                if weight < 300:
                    considerations.append("Very light font weights may have poor readability")
            except (ValueError, TypeError):
                pass
        
        return considerations


# Global analyzer instance
_analyzer_instance = None

def get_design_system_analyzer() -> DesignSystemAnalyzer:
    """Get the global design system analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = DesignSystemAnalyzer()
    return _analyzer_instance