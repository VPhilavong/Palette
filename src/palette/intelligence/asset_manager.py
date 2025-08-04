"""
Asset Intelligence System for cataloging and suggesting project assets.
Scans projects for images, icons, fonts, and other resources.
"""

import json
import mimetypes
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class AssetType(Enum):
    """Types of assets in a project."""

    IMAGE = "image"
    ICON = "icon"
    FONT = "font"
    VIDEO = "video"
    ANIMATION = "animation"
    LOGO = "logo"
    PATTERN = "pattern"
    PLACEHOLDER = "placeholder"


@dataclass
class Asset:
    """Represents a project asset."""

    path: str
    type: AssetType
    name: str
    size: int
    mime_type: str
    dimensions: Optional[Tuple[int, int]] = None
    format: Optional[str] = None
    tags: List[str] = None
    usage_count: int = 0
    last_modified: float = 0


@dataclass
class AssetContext:
    """Complete asset context for a project."""

    images: Dict[str, List[Asset]]  # Categorized images
    icons: Dict[str, Asset]  # Icon mapping
    fonts: List[str]  # Available fonts
    colors: Dict[str, str]  # Brand colors
    logos: List[Asset]  # Logo variations
    patterns: List[Asset]  # Background patterns
    animations: List[Asset]  # Animation files
    placeholders: Dict[str, str]  # Placeholder suggestions


@dataclass
class AssetSuggestion:
    """Suggestion for asset usage in a component."""

    asset_type: AssetType
    suggested_asset: Optional[Asset]
    placeholder_fallback: str
    usage_context: str
    priority: str = "medium"  # high, medium, low


class AssetIntelligence:
    """Intelligent asset management and suggestion system."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self._init_patterns()
        self._init_placeholder_templates()

    def _init_patterns(self):
        """Initialize patterns for asset detection."""
        self.asset_patterns = {
            "hero_image": r"hero|banner|jumbotron|header.*image",
            "logo": r"logo|brand|mark",
            "icon": r"icon|glyph|symbol",
            "avatar": r"avatar|profile|user.*image",
            "product": r"product|item|catalog",
            "background": r"bg|background|pattern",
            "thumbnail": r"thumb|thumbnail|preview",
        }

        self.icon_systems = {
            "heroicons": r"heroicons?",
            "feather": r"feather",
            "fontawesome": r"fa-|font.*awesome",
            "material": r"material.*icons?|mui.*icons?",
            "tabler": r"tabler",
            "lucide": r"lucide",
        }

    def _init_placeholder_templates(self):
        """Initialize placeholder templates for different asset types."""
        self.placeholders = {
            "hero_image": "https://images.unsplash.com/photo-1557683316-973673baf926?w=1200&h=600",
            "product_image": "https://via.placeholder.com/400x300/f3f4f6/9ca3af?text=Product",
            "avatar": "https://ui-avatars.com/api/?name=User&background=6366f1&color=fff",
            "logo": "https://via.placeholder.com/200x50/1f2937/f3f4f6?text=Logo",
            "icon": "<!-- Icon placeholder -->",
            "pattern": "data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E",
        }

    def analyze_project_assets(self) -> AssetContext:
        """Analyze and catalog all project assets."""
        context = AssetContext(
            images={},
            icons={},
            fonts=[],
            colors={},
            logos=[],
            patterns=[],
            animations=[],
            placeholders=self.placeholders,
        )

        # Scan for images
        context.images = self._scan_images()

        # Detect icon system
        context.icons = self._detect_icon_system()

        # Extract fonts
        context.fonts = self._extract_fonts()

        # Find logos
        context.logos = self._find_logos()

        # Find patterns
        context.patterns = self._find_patterns()

        # Detect animations
        context.animations = self._find_animations()

        # Extract brand colors from CSS/config
        context.colors = self._extract_brand_colors()

        return context

    def _scan_images(self) -> Dict[str, List[Asset]]:
        """Scan project for images and categorize them."""
        images = {
            "hero": [],
            "product": [],
            "avatar": [],
            "thumbnail": [],
            "background": [],
            "general": [],
        }

        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
        common_dirs = ["public", "assets", "images", "static", "src/assets"]

        for dir_name in common_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.suffix.lower() in image_extensions:
                        asset = self._create_image_asset(file_path)
                        category = self._categorize_image(asset)
                        images[category].append(asset)

        return images

    def _create_image_asset(self, file_path: Path) -> Asset:
        """Create an Asset object for an image file."""
        relative_path = file_path.relative_to(self.project_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))

        # Try to extract dimensions for raster images
        dimensions = None
        if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            dimensions = self._get_image_dimensions(file_path)

        return Asset(
            path=str(relative_path),
            type=AssetType.IMAGE,
            name=file_path.stem,
            size=file_path.stat().st_size if file_path.exists() else 0,
            mime_type=mime_type or "image/unknown",
            dimensions=dimensions,
            format=file_path.suffix[1:].lower(),
            tags=self._extract_tags_from_filename(file_path.name),
            last_modified=file_path.stat().st_mtime if file_path.exists() else 0,
        )

    def _categorize_image(self, asset: Asset) -> str:
        """Categorize an image based on its name and path."""
        name_lower = asset.name.lower()
        path_lower = asset.path.lower()

        for category, pattern in self.asset_patterns.items():
            if re.search(pattern, name_lower) or re.search(pattern, path_lower):
                # Map pattern categories to image categories
                if category in ["hero_image", "background"]:
                    return "hero"
                elif category == "product":
                    return "product"
                elif category == "avatar":
                    return "avatar"
                elif category == "thumbnail":
                    return "thumbnail"

        # Size-based categorization
        if asset.dimensions:
            width, height = asset.dimensions
            if width > 1200 or height > 600:
                return "hero"
            elif width < 200 and height < 200:
                return "thumbnail"

        return "general"

    def _detect_icon_system(self) -> Dict[str, Asset]:
        """Detect which icon system the project uses."""
        icons = {}

        # Check package.json for icon libraries
        package_json = self.project_path / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                try:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }

                    for system, pattern in self.icon_systems.items():
                        if any(re.search(pattern, dep) for dep in deps.keys()):
                            icons["system"] = Asset(
                                path=system,
                                type=AssetType.ICON,
                                name=system,
                                size=0,
                                mime_type="text/plain",
                                tags=[system, "icon-library"],
                            )
                            break
                except json.JSONDecodeError:
                    pass

        # Scan for SVG icons
        svg_icons = self._scan_svg_icons()
        icons.update(svg_icons)

        return icons

    def _scan_svg_icons(self) -> Dict[str, Asset]:
        """Scan for SVG icon files."""
        icons = {}
        icon_dirs = ["icons", "assets/icons", "src/icons", "public/icons"]

        for dir_name in icon_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists():
                for svg_file in dir_path.glob("**/*.svg"):
                    # Check if it's likely an icon (small size, simple name)
                    if svg_file.stat().st_size < 10000:  # Less than 10KB
                        icon_name = svg_file.stem
                        icons[icon_name] = Asset(
                            path=str(svg_file.relative_to(self.project_path)),
                            type=AssetType.ICON,
                            name=icon_name,
                            size=svg_file.stat().st_size,
                            mime_type="image/svg+xml",
                            format="svg",
                            tags=self._extract_tags_from_filename(icon_name),
                        )

        return icons

    def _extract_fonts(self) -> List[str]:
        """Extract font information from CSS and config files."""
        fonts = set()

        # Check CSS files for font-family declarations
        css_patterns = [
            r"font-family:\s*['\"]?([^;'\"]+)['\"]?",
            r"--font-.*:\s*['\"]?([^;'\"]+)['\"]?",
        ]

        for css_file in self.project_path.rglob("*.css"):
            try:
                content = css_file.read_text()
                for pattern in css_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Clean up font names
                        font_names = [f.strip() for f in match.split(",")]
                        fonts.update(f for f in font_names if not f.startswith("-"))
            except Exception:
                continue

        # Check for Google Fonts or other font imports
        font_imports = self._find_font_imports()
        fonts.update(font_imports)

        # Filter out generic fonts
        generic_fonts = {
            "serif",
            "sans-serif",
            "monospace",
            "cursive",
            "fantasy",
            "inherit",
        }
        return sorted(list(fonts - generic_fonts))

    def _find_font_imports(self) -> Set[str]:
        """Find imported fonts from various sources."""
        fonts = set()

        # Check HTML files for font links
        for html_file in self.project_path.rglob("*.html"):
            try:
                content = html_file.read_text()
                # Google Fonts
                google_fonts = re.findall(
                    r"fonts\.googleapis\.com/css[^'\"]*family=([^&'\"]+)", content
                )
                for font_param in google_fonts:
                    font_names = font_param.replace("+", " ").split("|")
                    fonts.update(f.split(":")[0] for f in font_names)
            except Exception:
                continue

        return fonts

    def _find_logos(self) -> List[Asset]:
        """Find logo files in the project."""
        logos = []
        logo_patterns = ["logo", "brand", "mark"]

        for pattern in logo_patterns:
            for file_path in self.project_path.rglob(f"*{pattern}*"):
                if file_path.is_file() and file_path.suffix.lower() in {
                    ".png",
                    ".svg",
                    ".jpg",
                    ".jpeg",
                }:
                    asset = self._create_image_asset(file_path)
                    asset.type = AssetType.LOGO
                    logos.append(asset)

        return logos

    def _find_patterns(self) -> List[Asset]:
        """Find background patterns and textures."""
        patterns = []
        pattern_keywords = ["pattern", "texture", "background", "bg"]

        for keyword in pattern_keywords:
            for file_path in self.project_path.rglob(f"*{keyword}*"):
                if file_path.is_file() and file_path.suffix.lower() in {
                    ".png",
                    ".svg",
                    ".jpg",
                }:
                    asset = self._create_image_asset(file_path)
                    asset.type = AssetType.PATTERN
                    patterns.append(asset)

        return patterns

    def _find_animations(self) -> List[Asset]:
        """Find animation files (Lottie, GIF, etc.)."""
        animations = []
        animation_extensions = {".json", ".gif", ".mp4", ".webm"}

        # Look for Lottie animations
        for json_file in self.project_path.rglob("*.json"):
            if (
                "lottie" in json_file.name.lower()
                or "animation" in json_file.name.lower()
            ):
                try:
                    with open(json_file) as f:
                        data = json.load(f)
                        # Simple check for Lottie structure
                        if isinstance(data, dict) and "v" in data and "fr" in data:
                            animations.append(
                                Asset(
                                    path=str(json_file.relative_to(self.project_path)),
                                    type=AssetType.ANIMATION,
                                    name=json_file.stem,
                                    size=json_file.stat().st_size,
                                    mime_type="application/json",
                                    format="lottie",
                                    tags=["lottie", "animation"],
                                )
                            )
                except Exception:
                    continue

        # Look for GIF animations
        for gif_file in self.project_path.rglob("*.gif"):
            animations.append(
                Asset(
                    path=str(gif_file.relative_to(self.project_path)),
                    type=AssetType.ANIMATION,
                    name=gif_file.stem,
                    size=gif_file.stat().st_size,
                    mime_type="image/gif",
                    format="gif",
                    tags=["gif", "animation"],
                )
            )

        return animations

    def _extract_brand_colors(self) -> Dict[str, str]:
        """Extract brand colors from CSS variables and config files."""
        colors = {}

        # CSS variable patterns
        color_patterns = [
            r"--([a-zA-Z-]+):\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))",
            r"(primary|secondary|accent|brand).*:\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\([^)]+\))",
        ]

        for css_file in self.project_path.rglob("*.css"):
            try:
                content = css_file.read_text()
                for pattern in color_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for name, value in matches:
                        clean_name = name.replace("--", "").replace("-color", "")
                        colors[clean_name] = value
            except Exception:
                continue

        # Check Tailwind config
        tailwind_config = self.project_path / "tailwind.config.js"
        if tailwind_config.exists():
            # Simple extraction (would need proper JS parsing for accuracy)
            try:
                content = tailwind_config.read_text()
                # Look for color definitions
                color_section = re.search(r"colors:\s*{([^}]+)}", content, re.DOTALL)
                if color_section:
                    # Extract color definitions (simplified)
                    color_defs = re.findall(
                        r"(\w+):\s*['\"]([^'\"]+)['\"]", color_section.group(1)
                    )
                    colors.update(dict(color_defs))
            except Exception:
                pass

        return colors

    def _extract_tags_from_filename(self, filename: str) -> List[str]:
        """Extract meaningful tags from filename."""
        # Remove extension and split by common separators
        name = Path(filename).stem
        parts = re.split(r"[-_\s]+", name.lower())

        # Filter out numbers and very short parts
        tags = [part for part in parts if len(part) > 2 and not part.isdigit()]

        return tags

    def _get_image_dimensions(self, file_path: Path) -> Optional[Tuple[int, int]]:
        """Get image dimensions (requires PIL, returns None if not available)."""
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                return img.size
        except ImportError:
            return None
        except Exception:
            return None

    def suggest_assets_for_component(
        self, component_type: str, component_intent: str, assets: AssetContext
    ) -> List[AssetSuggestion]:
        """Suggest appropriate assets for a component type."""
        suggestions = []

        if "hero" in component_type.lower() or "landing" in component_intent.lower():
            # Hero section needs hero image
            hero_images = assets.images.get("hero", [])
            if hero_images:
                suggestions.append(
                    AssetSuggestion(
                        asset_type=AssetType.IMAGE,
                        suggested_asset=hero_images[0],
                        placeholder_fallback=self.placeholders["hero_image"],
                        usage_context="Hero background image",
                        priority="high",
                    )
                )
            else:
                suggestions.append(
                    AssetSuggestion(
                        asset_type=AssetType.IMAGE,
                        suggested_asset=None,
                        placeholder_fallback=self.placeholders["hero_image"],
                        usage_context="Hero background image (using placeholder)",
                        priority="high",
                    )
                )

            # Logo for hero
            if assets.logos:
                suggestions.append(
                    AssetSuggestion(
                        asset_type=AssetType.LOGO,
                        suggested_asset=assets.logos[0],
                        placeholder_fallback=self.placeholders["logo"],
                        usage_context="Brand logo in hero section",
                        priority="high",
                    )
                )

        elif "product" in component_type.lower():
            # Product components need product images
            product_images = assets.images.get("product", [])
            if product_images:
                for i, img in enumerate(product_images[:4]):  # First 4 images
                    suggestions.append(
                        AssetSuggestion(
                            asset_type=AssetType.IMAGE,
                            suggested_asset=img,
                            placeholder_fallback=self.placeholders["product_image"],
                            usage_context=f"Product image {i+1}",
                            priority="high" if i < 2 else "medium",
                        )
                    )
            else:
                # Suggest placeholders
                for i in range(4):
                    suggestions.append(
                        AssetSuggestion(
                            asset_type=AssetType.IMAGE,
                            suggested_asset=None,
                            placeholder_fallback=self.placeholders["product_image"],
                            usage_context=f"Product image placeholder {i+1}",
                            priority="medium",
                        )
                    )

        elif "pricing" in component_type.lower():
            # Pricing sections might need icons
            if assets.icons.get("system"):
                suggestions.append(
                    AssetSuggestion(
                        asset_type=AssetType.ICON,
                        suggested_asset=assets.icons["system"],
                        placeholder_fallback=self.placeholders["icon"],
                        usage_context="Feature icons for pricing tiers",
                        priority="medium",
                    )
                )

            # Background pattern for pricing
            if assets.patterns:
                suggestions.append(
                    AssetSuggestion(
                        asset_type=AssetType.PATTERN,
                        suggested_asset=assets.patterns[0],
                        placeholder_fallback=self.placeholders["pattern"],
                        usage_context="Subtle background pattern",
                        priority="low",
                    )
                )

        elif "testimonial" in component_type.lower():
            # Testimonials need avatars
            avatar_images = assets.images.get("avatar", [])
            if avatar_images:
                for i, img in enumerate(avatar_images[:3]):
                    suggestions.append(
                        AssetSuggestion(
                            asset_type=AssetType.IMAGE,
                            suggested_asset=img,
                            placeholder_fallback=self.placeholders["avatar"],
                            usage_context=f"Testimonial avatar {i+1}",
                            priority="medium",
                        )
                    )
            else:
                # Avatar placeholders
                for i in range(3):
                    suggestions.append(
                        AssetSuggestion(
                            asset_type=AssetType.IMAGE,
                            suggested_asset=None,
                            placeholder_fallback=self.placeholders["avatar"],
                            usage_context=f"Testimonial avatar placeholder {i+1}",
                            priority="medium",
                        )
                    )

        return suggestions

    def generate_asset_imports(self, suggestions: List[AssetSuggestion]) -> str:
        """Generate import statements for suggested assets."""
        imports = []

        for suggestion in suggestions:
            if suggestion.suggested_asset:
                asset = suggestion.suggested_asset
                if asset.format in ["png", "jpg", "jpeg", "svg", "webp"]:
                    # Generate import name from filename
                    import_name = self._to_camel_case(asset.name)
                    imports.append(f"import {import_name} from '{asset.path}';")

        return (
            "\n".join(imports)
            if imports
            else "// No local assets found, using placeholders"
        )

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        parts = re.split(r"[-_\s]+", text)
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
