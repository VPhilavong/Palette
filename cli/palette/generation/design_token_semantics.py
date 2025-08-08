"""
Design Token Semantic Understanding System.
Analyzes design tokens to understand their semantic relationships, hierarchies, and usage patterns.
Provides intelligent token recommendations for component generation.
"""

import re
import json
import colorsys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from pathlib import Path

from ..errors.decorators import handle_errors


class TokenType(Enum):
    """Types of design tokens."""
    COLOR = "color"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    BORDER = "border"
    SHADOW = "shadow"
    TIMING = "timing"
    OPACITY = "opacity"
    SIZE = "size"
    BREAKPOINT = "breakpoint"
    Z_INDEX = "z-index"


class TokenRole(Enum):
    """Semantic roles that tokens can play."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    NEUTRAL = "neutral"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    BACKGROUND = "background"
    SURFACE = "surface"
    TEXT = "text"
    BORDER = "border"
    INTERACTIVE = "interactive"
    FOCUS = "focus"
    DISABLED = "disabled"


class TokenContext(Enum):
    """Contexts where tokens are used."""
    LIGHT_MODE = "light"
    DARK_MODE = "dark"
    HIGH_CONTRAST = "high-contrast"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    PRINT = "print"
    HOVER = "hover"
    ACTIVE = "active"
    FOCUS = "focus"
    DISABLED = "disabled"


@dataclass
class TokenMetadata:
    """Metadata about a design token."""
    name: str
    value: Any
    token_type: TokenType
    description: Optional[str] = None
    roles: List[TokenRole] = field(default_factory=list)
    contexts: List[TokenContext] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    deprecated: bool = False
    category: Optional[str] = None
    subcategory: Optional[str] = None


@dataclass
class TokenRelationship:
    """Relationship between two tokens."""
    source_token: str
    target_token: str
    relationship_type: str  # "variant", "complement", "contrast", "hierarchy"
    strength: float  # 0.0 to 1.0
    context: Optional[str] = None


@dataclass
class TokenRecommendation:
    """A token recommendation with reasoning."""
    token_name: str
    confidence: float
    reasoning: str
    alternative_tokens: List[str] = field(default_factory=list)
    context_specific: bool = False


class DesignTokenSemantics:
    """
    System for understanding design token semantics and relationships.
    Provides intelligent token recommendations for component generation.
    """
    
    def __init__(self):
        self.tokens: Dict[str, TokenMetadata] = {}
        self.relationships: List[TokenRelationship] = []
        self.token_hierarchies: Dict[str, List[str]] = {}
        self.usage_patterns: Dict[str, Dict[str, int]] = {}
        self.semantic_groups: Dict[str, List[str]] = {}
        
        # Color analysis cache
        self._color_analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # Common token patterns
        self._initialize_common_patterns()
    
    def _initialize_common_patterns(self):
        """Initialize common design token patterns and relationships."""
        
        # Common semantic color roles
        self.semantic_groups = {
            "brand_colors": ["primary", "secondary", "tertiary"],
            "semantic_colors": ["success", "warning", "error", "info"],
            "neutral_colors": ["gray", "neutral", "surface", "background"],
            "text_colors": ["text-primary", "text-secondary", "text-muted"],
            "interactive_colors": ["link", "hover", "focus", "active"],
            "spacing_scale": ["xs", "sm", "md", "lg", "xl", "2xl"],
            "typography_scale": ["xs", "sm", "base", "lg", "xl", "2xl", "3xl"],
            "border_weights": ["thin", "normal", "medium", "thick"],
            "shadow_levels": ["sm", "md", "lg", "xl", "2xl"]
        }
    
    @handle_errors(reraise=True)
    def analyze_project_tokens(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze design tokens from various sources in a project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Analysis results with discovered tokens and relationships
        """
        project_path = Path(project_path)
        analysis_results = {
            "tokens_found": 0,
            "sources": [],
            "token_types": {},
            "semantic_coverage": {},
            "recommendations": []
        }
        
        # Look for common token sources
        token_sources = [
            # CSS custom properties
            project_path / "src" / "styles" / "tokens.css",
            project_path / "styles" / "tokens.css",
            project_path / "assets" / "tokens.css",
            
            # Design token JSON files
            project_path / "design-tokens.json",
            project_path / "tokens.json",
            project_path / "src" / "design-tokens.json",
            
            # Tailwind config
            project_path / "tailwind.config.js",
            project_path / "tailwind.config.ts",
            
            # Style dictionary
            project_path / "style-dictionary.json",
            project_path / "tokens" / "tokens.json",
        ]
        
        for source_path in token_sources:
            if source_path.exists():
                try:
                    if source_path.suffix == '.css':
                        tokens = self._parse_css_tokens(source_path)
                    elif source_path.suffix in ['.json']:
                        tokens = self._parse_json_tokens(source_path)
                    elif 'tailwind' in source_path.name:
                        tokens = self._parse_tailwind_config(source_path)
                    else:
                        continue
                    
                    if tokens:
                        analysis_results["sources"].append(str(source_path))
                        analysis_results["tokens_found"] += len(tokens)
                        
                        for token_name, token_data in tokens.items():
                            self.tokens[token_name] = token_data
                            
                            token_type = token_data.token_type.value
                            if token_type not in analysis_results["token_types"]:
                                analysis_results["token_types"][token_type] = 0
                            analysis_results["token_types"][token_type] += 1
                            
                except Exception as e:
                    print(f"⚠️ Failed to parse {source_path}: {e}")
        
        # Analyze semantic relationships
        if self.tokens:
            self._analyze_token_relationships()
            self._build_token_hierarchies()
            self._analyze_semantic_coverage(analysis_results)
        
        return analysis_results
    
    def _parse_css_tokens(self, css_path: Path) -> Dict[str, TokenMetadata]:
        """Parse CSS custom properties as design tokens."""
        tokens = {}
        
        try:
            css_content = css_path.read_text()
            
            # Find CSS custom properties
            custom_prop_pattern = r'--([a-zA-Z0-9-_]+):\s*([^;]+);'
            matches = re.findall(custom_prop_pattern, css_content)
            
            for prop_name, prop_value in matches:
                prop_value = prop_value.strip()
                
                # Determine token type
                token_type = self._infer_token_type(prop_name, prop_value)
                
                # Infer semantic roles
                roles = self._infer_token_roles(prop_name, prop_value)
                
                tokens[f"--{prop_name}"] = TokenMetadata(
                    name=f"--{prop_name}",
                    value=prop_value,
                    token_type=token_type,
                    roles=roles,
                    category=self._categorize_token(prop_name)
                )
                
        except Exception as e:
            print(f"Error parsing CSS tokens: {e}")
        
        return tokens
    
    def _parse_json_tokens(self, json_path: Path) -> Dict[str, TokenMetadata]:
        """Parse JSON design tokens file."""
        tokens = {}
        
        try:
            with open(json_path, 'r') as f:
                token_data = json.load(f)
            
            # Recursive function to parse nested tokens
            def parse_nested_tokens(data: Dict, prefix: str = ""):
                for key, value in data.items():
                    current_name = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        if "value" in value:
                            # This is a token definition
                            token_value = value["value"]
                            token_type = self._infer_token_type(
                                current_name, 
                                str(token_value)
                            )
                            
                            roles = self._infer_token_roles(current_name, str(token_value))
                            
                            tokens[current_name] = TokenMetadata(
                                name=current_name,
                                value=token_value,
                                token_type=token_type,
                                description=value.get("description"),
                                roles=roles,
                                category=value.get("category", self._categorize_token(current_name))
                            )
                        else:
                            # Nested group, recurse
                            parse_nested_tokens(value, current_name)
            
            parse_nested_tokens(token_data)
            
        except Exception as e:
            print(f"Error parsing JSON tokens: {e}")
        
        return tokens
    
    def _parse_tailwind_config(self, config_path: Path) -> Dict[str, TokenMetadata]:
        """Parse Tailwind config for design tokens."""
        tokens = {}
        
        try:
            # Use the existing Tailwind parser utility
            from ..utils.tailwind_parser import parse_tailwind_config
            
            config_data = parse_tailwind_config(str(config_path))
            
            if config_data and "theme" in config_data:
                theme = config_data["theme"]
                
                # Parse color tokens
                if "colors" in theme:
                    for color_name, color_value in theme["colors"].items():
                        if isinstance(color_value, dict):
                            for shade, shade_value in color_value.items():
                                token_name = f"colors.{color_name}.{shade}"
                                tokens[token_name] = TokenMetadata(
                                    name=token_name,
                                    value=shade_value,
                                    token_type=TokenType.COLOR,
                                    roles=self._infer_token_roles(token_name, shade_value),
                                    category="colors"
                                )
                        else:
                            token_name = f"colors.{color_name}"
                            tokens[token_name] = TokenMetadata(
                                name=token_name,
                                value=color_value,
                                token_type=TokenType.COLOR,
                                roles=self._infer_token_roles(token_name, color_value),
                                category="colors"
                            )
                
                # Parse spacing tokens
                if "spacing" in theme:
                    for space_name, space_value in theme["spacing"].items():
                        token_name = f"spacing.{space_name}"
                        tokens[token_name] = TokenMetadata(
                            name=token_name,
                            value=space_value,
                            token_type=TokenType.SPACING,
                            category="spacing"
                        )
                
                # Parse typography tokens
                if "fontSize" in theme:
                    for size_name, size_value in theme["fontSize"].items():
                        token_name = f"fontSize.{size_name}"
                        tokens[token_name] = TokenMetadata(
                            name=token_name,
                            value=size_value,
                            token_type=TokenType.TYPOGRAPHY,
                            category="typography"
                        )
                        
        except Exception as e:
            print(f"Error parsing Tailwind config: {e}")
        
        return tokens
    
    def _infer_token_type(self, name: str, value: str) -> TokenType:
        """Infer the type of a design token from its name and value."""
        name_lower = name.lower()
        value_lower = value.lower()
        
        # Color patterns
        if any(keyword in name_lower for keyword in ['color', 'bg', 'background', 'text', 'border']) or \
           re.match(r'^#[0-9a-f]{3,8}$', value_lower) or \
           re.match(r'^rgb\(', value_lower) or \
           re.match(r'^hsl\(', value_lower) or \
           value_lower in ['transparent', 'currentcolor', 'inherit']:
            return TokenType.COLOR
        
        # Spacing patterns
        if any(keyword in name_lower for keyword in ['space', 'spacing', 'margin', 'padding', 'gap']) or \
           re.match(r'^\d+(\.\d+)?(px|rem|em|%|vh|vw)$', value_lower):
            return TokenType.SPACING
        
        # Typography patterns
        if any(keyword in name_lower for keyword in ['font', 'text', 'line-height', 'letter-spacing']) or \
           re.match(r'^\d+(\.\d+)?(px|rem|em|pt)$', value_lower):
            return TokenType.TYPOGRAPHY
        
        # Border patterns
        if 'border' in name_lower and any(keyword in name_lower for keyword in ['width', 'radius']):
            return TokenType.BORDER
        
        # Shadow patterns
        if 'shadow' in name_lower or 'elevation' in name_lower:
            return TokenType.SHADOW
        
        # Timing patterns
        if any(keyword in name_lower for keyword in ['duration', 'delay', 'timing']) or \
           re.match(r'^\d+(\.\d+)?m?s$', value_lower):
            return TokenType.TIMING
        
        # Opacity patterns
        if 'opacity' in name_lower or 'alpha' in name_lower or \
           re.match(r'^0?\.\d+$', value_lower):
            return TokenType.OPACITY
        
        # Size patterns
        if any(keyword in name_lower for keyword in ['size', 'width', 'height']) and \
           re.match(r'^\d+(\.\d+)?(px|rem|em|%|vh|vw)$', value_lower):
            return TokenType.SIZE
        
        # Breakpoint patterns
        if any(keyword in name_lower for keyword in ['breakpoint', 'screen', 'bp']):
            return TokenType.BREAKPOINT
        
        # Z-index patterns
        if 'z' in name_lower and 'index' in name_lower:
            return TokenType.Z_INDEX
        
        # Default to color if can't determine
        return TokenType.COLOR
    
    def _infer_token_roles(self, name: str, value: str) -> List[TokenRole]:
        """Infer semantic roles from token name and value."""
        name_lower = name.lower()
        roles = []
        
        # Primary role inference
        if any(keyword in name_lower for keyword in ['primary', 'brand']):
            roles.append(TokenRole.PRIMARY)
        elif any(keyword in name_lower for keyword in ['secondary']):
            roles.append(TokenRole.SECONDARY)
        elif any(keyword in name_lower for keyword in ['accent', 'highlight']):
            roles.append(TokenRole.ACCENT)
        
        # Semantic role inference
        if any(keyword in name_lower for keyword in ['success', 'positive', 'green']):
            roles.append(TokenRole.SUCCESS)
        elif any(keyword in name_lower for keyword in ['warning', 'caution', 'yellow', 'orange']):
            roles.append(TokenRole.WARNING)
        elif any(keyword in name_lower for keyword in ['error', 'danger', 'negative', 'red']):
            roles.append(TokenRole.ERROR)
        elif any(keyword in name_lower for keyword in ['info', 'information', 'blue']):
            roles.append(TokenRole.INFO)
        
        # Context-based roles
        if any(keyword in name_lower for keyword in ['background', 'bg']):
            roles.append(TokenRole.BACKGROUND)
        elif any(keyword in name_lower for keyword in ['surface', 'card']):
            roles.append(TokenRole.SURFACE)
        elif any(keyword in name_lower for keyword in ['text', 'foreground']):
            roles.append(TokenRole.TEXT)
        elif any(keyword in name_lower for keyword in ['border', 'outline']):
            roles.append(TokenRole.BORDER)
        
        # State roles
        if any(keyword in name_lower for keyword in ['hover']):
            roles.append(TokenRole.INTERACTIVE)
        elif any(keyword in name_lower for keyword in ['focus']):
            roles.append(TokenRole.FOCUS)
        elif any(keyword in name_lower for keyword in ['disabled', 'inactive']):
            roles.append(TokenRole.DISABLED)
        
        # Neutral if no specific role
        if not roles and any(keyword in name_lower for keyword in ['gray', 'grey', 'neutral']):
            roles.append(TokenRole.NEUTRAL)
        
        return roles
    
    def _categorize_token(self, name: str) -> str:
        """Categorize a token based on its name."""
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['color', 'bg', 'text', 'border']):
            return "colors"
        elif any(keyword in name_lower for keyword in ['space', 'spacing', 'margin', 'padding']):
            return "spacing"
        elif any(keyword in name_lower for keyword in ['font', 'text', 'typography']):
            return "typography"
        elif any(keyword in name_lower for keyword in ['shadow', 'elevation']):
            return "effects"
        elif any(keyword in name_lower for keyword in ['border']):
            return "borders"
        elif any(keyword in name_lower for keyword in ['duration', 'timing']):
            return "animation"
        else:
            return "misc"
    
    def _analyze_token_relationships(self):
        """Analyze relationships between tokens."""
        color_tokens = {name: token for name, token in self.tokens.items() 
                       if token.token_type == TokenType.COLOR}
        
        # Analyze color relationships
        for name1, token1 in color_tokens.items():
            for name2, token2 in color_tokens.items():
                if name1 != name2:
                    relationship = self._analyze_color_relationship(token1, token2)
                    if relationship:
                        self.relationships.append(relationship)
        
        # Analyze spacing relationships (hierarchical)
        spacing_tokens = {name: token for name, token in self.tokens.items() 
                         if token.token_type == TokenType.SPACING}
        
        for name, token in spacing_tokens.items():
            hierarchy_relationships = self._analyze_spacing_hierarchy(name, token, spacing_tokens)
            self.relationships.extend(hierarchy_relationships)
    
    def _analyze_color_relationship(self, token1: TokenMetadata, token2: TokenMetadata) -> Optional[TokenRelationship]:
        """Analyze relationship between two color tokens."""
        try:
            # Convert colors to HSL for analysis
            hsl1 = self._color_to_hsl(token1.value)
            hsl2 = self._color_to_hsl(token2.value)
            
            if not hsl1 or not hsl2:
                return None
            
            h1, s1, l1 = hsl1
            h2, s2, l2 = hsl2
            
            # Check for complementary colors
            hue_diff = abs(h1 - h2)
            if 170 <= hue_diff <= 190:
                return TokenRelationship(
                    source_token=token1.name,
                    target_token=token2.name,
                    relationship_type="complement",
                    strength=0.9
                )
            
            # Check for analogous colors
            if 20 <= hue_diff <= 60:
                return TokenRelationship(
                    source_token=token1.name,
                    target_token=token2.name,
                    relationship_type="analogous",
                    strength=0.7
                )
            
            # Check for variants (same hue, different lightness)
            if abs(h1 - h2) <= 10 and abs(l1 - l2) >= 0.2:
                return TokenRelationship(
                    source_token=token1.name,
                    target_token=token2.name,
                    relationship_type="variant",
                    strength=0.8
                )
            
        except Exception:
            pass
        
        return None
    
    def _color_to_hsl(self, color_value: str) -> Optional[Tuple[float, float, float]]:
        """Convert color value to HSL tuple."""
        if color_value in self._color_analysis_cache:
            return self._color_analysis_cache[color_value].get('hsl')
        
        try:
            # Handle hex colors
            if color_value.startswith('#'):
                hex_color = color_value[1:]
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    hsl = colorsys.rgb_to_hls(r, g, b)
                    self._color_analysis_cache[color_value] = {'hsl': hsl}
                    return hsl
            
            # Handle rgb colors
            rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_value)
            if rgb_match:
                r, g, b = [int(x) / 255.0 for x in rgb_match.groups()]
                hsl = colorsys.rgb_to_hls(r, g, b)
                self._color_analysis_cache[color_value] = {'hsl': hsl}
                return hsl
                
        except Exception:
            pass
        
        return None
    
    def _analyze_spacing_hierarchy(self, token_name: str, token: TokenMetadata, 
                                  all_spacing: Dict[str, TokenMetadata]) -> List[TokenRelationship]:
        """Analyze spacing hierarchy relationships."""
        relationships = []
        
        try:
            # Extract numeric value from spacing token
            current_value = self._extract_numeric_value(token.value)
            if current_value is None:
                return relationships
            
            for other_name, other_token in all_spacing.items():
                if token_name == other_name:
                    continue
                
                other_value = self._extract_numeric_value(other_token.value)
                if other_value is None:
                    continue
                
                # Check for hierarchical relationship
                if current_value < other_value:
                    # Current is smaller, create hierarchy relationship
                    relationships.append(TokenRelationship(
                        source_token=token_name,
                        target_token=other_name,
                        relationship_type="hierarchy",
                        strength=0.8
                    ))
        
        except Exception:
            pass
        
        return relationships
    
    def _extract_numeric_value(self, value: str) -> Optional[float]:
        """Extract numeric value from a token value string."""
        try:
            # Remove units and extract number
            match = re.match(r'(\d+(?:\.\d+)?)', str(value))
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None
    
    def _build_token_hierarchies(self):
        """Build token hierarchy mappings."""
        # Group tokens by type and build hierarchies
        for token_type in TokenType:
            type_tokens = [(name, token) for name, token in self.tokens.items() 
                          if token.token_type == token_type]
            
            if token_type == TokenType.SPACING:
                # Build spacing hierarchy
                spacing_hierarchy = []
                for name, token in type_tokens:
                    numeric_value = self._extract_numeric_value(token.value)
                    if numeric_value is not None:
                        spacing_hierarchy.append((name, numeric_value))
                
                # Sort by value
                spacing_hierarchy.sort(key=lambda x: x[1])
                self.token_hierarchies["spacing"] = [name for name, _ in spacing_hierarchy]
    
    def _analyze_semantic_coverage(self, analysis_results: Dict[str, Any]):
        """Analyze how well semantic roles are covered by tokens."""
        coverage = {}
        
        for role in TokenRole:
            role_tokens = [token for token in self.tokens.values() 
                          if role in token.roles]
            coverage[role.value] = len(role_tokens)
        
        analysis_results["semantic_coverage"] = coverage
        
        # Generate recommendations for missing coverage
        recommendations = []
        if coverage.get("primary", 0) == 0:
            recommendations.append("Consider defining primary brand colors")
        if coverage.get("success", 0) == 0:
            recommendations.append("Consider adding semantic success color")
        if coverage.get("error", 0) == 0:
            recommendations.append("Consider adding semantic error color")
        
        analysis_results["recommendations"] = recommendations
    
    def recommend_token_for_context(
        self, 
        context: str, 
        token_type: TokenType,
        semantic_role: Optional[TokenRole] = None
    ) -> List[TokenRecommendation]:
        """
        Recommend appropriate tokens for a given context.
        
        Args:
            context: Usage context (e.g., "button background", "error text")
            token_type: Type of token needed
            semantic_role: Optional semantic role requirement
            
        Returns:
            List of token recommendations with confidence scores
        """
        recommendations = []
        context_lower = context.lower()
        
        # Filter tokens by type
        candidate_tokens = [(name, token) for name, token in self.tokens.items() 
                           if token.token_type == token_type]
        
        # Score tokens based on context
        for name, token in candidate_tokens:
            confidence = self._calculate_context_confidence(token, context_lower, semantic_role)
            
            if confidence > 0.3:  # Minimum confidence threshold
                reasoning = self._generate_recommendation_reasoning(token, context, semantic_role)
                
                recommendation = TokenRecommendation(
                    token_name=name,
                    confidence=confidence,
                    reasoning=reasoning
                )
                recommendations.append(recommendation)
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        # Add alternatives for top recommendations
        for i, rec in enumerate(recommendations[:3]):
            alternatives = self._find_alternative_tokens(rec.token_name, token_type)
            rec.alternative_tokens = alternatives[:3]
        
        return recommendations[:5]  # Return top 5
    
    def _calculate_context_confidence(
        self, 
        token: TokenMetadata, 
        context: str, 
        semantic_role: Optional[TokenRole]
    ) -> float:
        """Calculate confidence score for token in given context."""
        confidence = 0.0
        
        # Base score from token name matching context
        token_name_lower = token.name.lower()
        context_words = context.split()
        
        for word in context_words:
            if word in token_name_lower:
                confidence += 0.3
        
        # Bonus for semantic role match
        if semantic_role and semantic_role in token.roles:
            confidence += 0.4
        
        # Bonus for category match
        if token.category:
            category_words = token.category.split()
            for word in category_words:
                if word in context:
                    confidence += 0.2
        
        # Context-specific bonuses
        if "button" in context:
            if any(role in token.roles for role in [TokenRole.PRIMARY, TokenRole.ACCENT]):
                confidence += 0.3
            if "background" in context and TokenRole.BACKGROUND in token.roles:
                confidence += 0.2
        
        if "text" in context and TokenRole.TEXT in token.roles:
            confidence += 0.3
        
        if "error" in context and TokenRole.ERROR in token.roles:
            confidence += 0.4
        
        if "success" in context and TokenRole.SUCCESS in token.roles:
            confidence += 0.4
        
        # Cap at 1.0
        return min(1.0, confidence)
    
    def _generate_recommendation_reasoning(
        self, 
        token: TokenMetadata, 
        context: str, 
        semantic_role: Optional[TokenRole]
    ) -> str:
        """Generate human-readable reasoning for token recommendation."""
        reasons = []
        
        if semantic_role and semantic_role in token.roles:
            reasons.append(f"matches {semantic_role.value} semantic role")
        
        if any(word in token.name.lower() for word in context.lower().split()):
            reasons.append("name suggests appropriate usage")
        
        if token.category and any(word in token.category for word in context.split()):
            reasons.append(f"belongs to {token.category} category")
        
        if not reasons:
            reasons.append("general compatibility with context")
        
        return "; ".join(reasons)
    
    def _find_alternative_tokens(self, token_name: str, token_type: TokenType) -> List[str]:
        """Find alternative tokens of the same type."""
        alternatives = []
        
        # Find tokens with relationships to this token
        for rel in self.relationships:
            if rel.source_token == token_name:
                alternatives.append(rel.target_token)
            elif rel.target_token == token_name:
                alternatives.append(rel.source_token)
        
        # Add tokens from same hierarchy
        for hierarchy_name, hierarchy_tokens in self.token_hierarchies.items():
            if token_name in hierarchy_tokens:
                idx = hierarchy_tokens.index(token_name)
                # Add adjacent tokens in hierarchy
                if idx > 0:
                    alternatives.append(hierarchy_tokens[idx - 1])
                if idx < len(hierarchy_tokens) - 1:
                    alternatives.append(hierarchy_tokens[idx + 1])
        
        return list(set(alternatives))  # Remove duplicates
    
    def get_token_usage_suggestions(self, component_type: str) -> Dict[str, List[TokenRecommendation]]:
        """Get comprehensive token usage suggestions for a component type."""
        suggestions = {}
        
        # Common token needs by component type
        component_token_needs = {
            "button": [
                ("background", TokenType.COLOR, TokenRole.PRIMARY),
                ("text", TokenType.COLOR, TokenRole.TEXT),
                ("border", TokenType.COLOR, TokenRole.BORDER),
                ("padding", TokenType.SPACING, None),
                ("border-radius", TokenType.BORDER, None)
            ],
            "card": [
                ("background", TokenType.COLOR, TokenRole.SURFACE),
                ("border", TokenType.COLOR, TokenRole.BORDER),
                ("shadow", TokenType.SHADOW, None),
                ("padding", TokenType.SPACING, None),
                ("border-radius", TokenType.BORDER, None)
            ],
            "form": [
                ("label-text", TokenType.COLOR, TokenRole.TEXT),
                ("input-background", TokenType.COLOR, TokenRole.BACKGROUND),
                ("input-border", TokenType.COLOR, TokenRole.BORDER),
                ("error-text", TokenType.COLOR, TokenRole.ERROR),
                ("spacing", TokenType.SPACING, None)
            ],
            "modal": [
                ("background", TokenType.COLOR, TokenRole.SURFACE),
                ("overlay", TokenType.COLOR, TokenRole.BACKGROUND),
                ("shadow", TokenType.SHADOW, None),
                ("border-radius", TokenType.BORDER, None)
            ]
        }
        
        needs = component_token_needs.get(component_type, [])
        
        for context, token_type, semantic_role in needs:
            recommendations = self.recommend_token_for_context(context, token_type, semantic_role)
            if recommendations:
                suggestions[context] = recommendations
        
        return suggestions
    
    def export_token_analysis(self) -> Dict[str, Any]:
        """Export comprehensive token analysis data."""
        return {
            "tokens": {
                name: {
                    "name": token.name,
                    "value": token.value,
                    "type": token.token_type.value,
                    "roles": [role.value for role in token.roles],
                    "category": token.category,
                    "description": token.description
                }
                for name, token in self.tokens.items()
            },
            "relationships": [
                {
                    "source": rel.source_token,
                    "target": rel.target_token,
                    "type": rel.relationship_type,
                    "strength": rel.strength
                }
                for rel in self.relationships
            ],
            "hierarchies": self.token_hierarchies,
            "semantic_groups": self.semantic_groups
        }


# Global instance
_token_semantics_instance = None

def get_design_token_semantics() -> DesignTokenSemantics:
    """Get the global design token semantics instance."""
    global _token_semantics_instance
    if _token_semantics_instance is None:
        _token_semantics_instance = DesignTokenSemantics()
    return _token_semantics_instance