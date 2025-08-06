"""
Smart Asset Recommendation System.
Intelligently recommends assets (icons, images, fonts, etc.) based on component context,
design patterns, and project requirements.
"""

import os
import re
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union

from ..errors.decorators import handle_errors


class AssetType(Enum):
    """Types of assets that can be recommended."""
    ICON = "icon"
    IMAGE = "image"
    FONT = "font"
    ILLUSTRATION = "illustration"
    LOGO = "logo"
    PATTERN = "pattern"
    VIDEO = "video"
    AUDIO = "audio"


class AssetPurpose(Enum):
    """Purpose/context where assets are used."""
    DECORATIVE = "decorative"
    FUNCTIONAL = "functional"
    NAVIGATIONAL = "navigational"
    INFORMATIONAL = "informational"
    BRANDING = "branding"
    INTERACTIVE = "interactive"
    PLACEHOLDER = "placeholder"
    BACKGROUND = "background"


class AssetCategory(Enum):
    """Categories for organizing assets."""
    UI_ICONS = "ui-icons"
    BRAND_ICONS = "brand-icons"
    SOCIAL_ICONS = "social-icons"
    BUSINESS_ICONS = "business-icons"
    TECH_ICONS = "tech-icons"
    HERO_IMAGES = "hero-images"
    PRODUCT_IMAGES = "product-images"
    AVATAR_IMAGES = "avatar-images"
    BACKGROUND_IMAGES = "background-images"
    ILLUSTRATIONS = "illustrations"
    LOGOS = "logos"
    PATTERNS = "patterns"


@dataclass
class AssetMetadata:
    """Metadata about an asset."""
    name: str
    path: str
    asset_type: AssetType
    category: AssetCategory
    purpose: List[AssetPurpose] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    size: Optional[Tuple[int, int]] = None  # width, height for images
    format: Optional[str] = None  # SVG, PNG, WOFF2, etc.
    color_scheme: Optional[str] = None  # light, dark, auto
    style: Optional[str] = None  # filled, outlined, duotone, etc.
    weight: Optional[str] = None  # for fonts: normal, bold, light
    license: Optional[str] = None
    usage_count: int = 0


@dataclass
class AssetRecommendation:
    """A recommended asset with context and reasoning."""
    asset: AssetMetadata
    confidence: float  # 0.0 to 1.0
    reasoning: str
    context_match: Dict[str, float] = field(default_factory=dict)
    alternatives: List[AssetMetadata] = field(default_factory=list)
    usage_examples: List[str] = field(default_factory=list)


@dataclass
class AssetLibrary:
    """Information about an asset library or icon set."""
    name: str
    source: str  # local, cdn, api
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    supported_formats: List[str] = field(default_factory=list)
    style_variants: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    license: Optional[str] = None


class SmartAssetRecommender:
    """
    Intelligent asset recommendation system for component generation.
    Analyzes project assets and provides contextual recommendations.
    """
    
    def __init__(self):
        self.assets: Dict[str, AssetMetadata] = {}
        self.asset_libraries: Dict[str, AssetLibrary] = {}
        self.context_patterns: Dict[str, List[str]] = {}
        self.component_asset_patterns: Dict[str, Dict[str, List[str]]] = {}
        
        # Initialize common patterns and libraries
        self._initialize_common_patterns()
        self._initialize_popular_libraries()
    
    def _initialize_common_patterns(self):
        """Initialize common asset usage patterns by component type."""
        
        self.component_asset_patterns = {
            "button": {
                "icons": ["arrow-right", "plus", "check", "x", "chevron-down", "loading"],
                "purposes": [AssetPurpose.FUNCTIONAL, AssetPurpose.INTERACTIVE],
                "categories": [AssetCategory.UI_ICONS],
                "common_contexts": ["submit", "cancel", "add", "remove", "expand", "loading"]
            },
            "navigation": {
                "icons": ["menu", "home", "user", "settings", "search", "notification"],
                "purposes": [AssetPurpose.NAVIGATIONAL, AssetPurpose.FUNCTIONAL],
                "categories": [AssetCategory.UI_ICONS],
                "common_contexts": ["menu", "profile", "dashboard", "search", "notifications"]
            },
            "form": {
                "icons": ["eye", "eye-slash", "calendar", "clock", "upload", "info"],
                "purposes": [AssetPurpose.FUNCTIONAL, AssetPurpose.INFORMATIONAL],
                "categories": [AssetCategory.UI_ICONS],
                "common_contexts": ["password", "date", "time", "file", "help", "validation"]
            },
            "card": {
                "icons": ["heart", "share", "bookmark", "more", "external-link"],
                "images": ["placeholder", "product", "avatar", "hero"],
                "purposes": [AssetPurpose.DECORATIVE, AssetPurpose.FUNCTIONAL],
                "categories": [AssetCategory.UI_ICONS, AssetCategory.PRODUCT_IMAGES],
                "common_contexts": ["favorite", "share", "save", "menu", "link"]
            },
            "modal": {
                "icons": ["x", "info", "warning", "check", "alert"],
                "purposes": [AssetPurpose.FUNCTIONAL, AssetPurpose.INFORMATIONAL],
                "categories": [AssetCategory.UI_ICONS],
                "common_contexts": ["close", "information", "warning", "success", "error"]
            },
            "table": {
                "icons": ["sort-asc", "sort-desc", "filter", "search", "edit", "delete"],
                "purposes": [AssetPurpose.FUNCTIONAL, AssetPurpose.INTERACTIVE],
                "categories": [AssetCategory.UI_ICONS],
                "common_contexts": ["sort", "filter", "search", "actions", "pagination"]
            },
            "hero": {
                "images": ["hero", "background", "illustration"],
                "illustrations": ["team", "growth", "technology", "success"],
                "purposes": [AssetPurpose.DECORATIVE, AssetPurpose.BRANDING],
                "categories": [AssetCategory.HERO_IMAGES, AssetCategory.ILLUSTRATIONS],
                "common_contexts": ["landing", "banner", "introduction", "promotion"]
            },
            "profile": {
                "images": ["avatar", "placeholder"],
                "icons": ["user", "camera", "edit"],
                "purposes": [AssetPurpose.DECORATIVE, AssetPurpose.FUNCTIONAL],
                "categories": [AssetCategory.AVATAR_IMAGES, AssetCategory.UI_ICONS],
                "common_contexts": ["avatar", "photo", "edit", "settings"]
            },
            "dashboard": {
                "icons": ["chart", "analytics", "trends", "calendar", "notification"],
                "illustrations": ["data", "charts", "analytics"],
                "purposes": [AssetPurpose.INFORMATIONAL, AssetPurpose.DECORATIVE],
                "categories": [AssetCategory.BUSINESS_ICONS, AssetCategory.ILLUSTRATIONS],
                "common_contexts": ["metrics", "data", "reports", "calendar", "overview"]
            }
        }
        
        # Context-based asset patterns
        self.context_patterns = {
            "e-commerce": ["shopping-cart", "credit-card", "package", "truck", "star"],
            "social": ["heart", "share", "comment", "like", "follow", "message"],
            "business": ["briefcase", "chart", "dollar", "handshake", "building"],
            "education": ["book", "graduation-cap", "lightbulb", "pencil", "calendar"],
            "healthcare": ["heart", "pill", "stethoscope", "first-aid", "hospital"],
            "technology": ["code", "cpu", "server", "cloud", "database", "api"],
            "finance": ["dollar", "chart", "bank", "credit-card", "calculator", "vault"],
            "entertainment": ["play", "music", "video", "game", "headphones", "tv"]
        }
    
    def _initialize_popular_libraries(self):
        """Initialize popular icon and asset libraries."""
        
        # Heroicons
        self.asset_libraries["heroicons"] = AssetLibrary(
            name="Heroicons",
            source="cdn",
            base_url="https://heroicons.com",
            supported_formats=["SVG", "React", "Vue"],
            style_variants=["outline", "solid", "mini"],
            categories=["ui-icons"],
            license="MIT"
        )
        
        # Lucide Icons
        self.asset_libraries["lucide"] = AssetLibrary(
            name="Lucide Icons",
            source="cdn",
            base_url="https://lucide.dev",
            supported_formats=["SVG", "React", "Vue", "Angular"],
            style_variants=["outline"],
            categories=["ui-icons"],
            license="ISC"
        )
        
        # Tabler Icons
        self.asset_libraries["tabler"] = AssetLibrary(
            name="Tabler Icons",
            source="cdn",
            base_url="https://tabler-icons.io",
            supported_formats=["SVG", "React", "Vue", "Angular"],
            style_variants=["outline", "filled"],
            categories=["ui-icons", "business-icons"],
            license="MIT"
        )
        
        # Font Awesome
        self.asset_libraries["fontawesome"] = AssetLibrary(
            name="Font Awesome",
            source="cdn",
            base_url="https://fontawesome.com",
            supported_formats=["SVG", "Webfont", "React", "Vue"],
            style_variants=["solid", "regular", "light", "brands"],
            categories=["ui-icons", "brand-icons", "social-icons"],
            license="Free/Pro"
        )
        
        # Feather Icons
        self.asset_libraries["feather"] = AssetLibrary(
            name="Feather Icons",
            source="cdn",
            base_url="https://feathericons.com",
            supported_formats=["SVG", "React", "Vue"],
            style_variants=["outline"],
            categories=["ui-icons"],
            license="MIT"
        )
        
        # Phosphor Icons
        self.asset_libraries["phosphor"] = AssetLibrary(
            name="Phosphor Icons",
            source="cdn",
            base_url="https://phosphoricons.com",
            supported_formats=["SVG", "React", "Vue", "Flutter"],
            style_variants=["thin", "light", "regular", "bold", "fill", "duotone"],
            categories=["ui-icons", "tech-icons"],
            license="MIT"
        )
        
        # Unsplash (for images)
        self.asset_libraries["unsplash"] = AssetLibrary(
            name="Unsplash",
            source="api",
            base_url="https://api.unsplash.com",
            supported_formats=["JPEG", "PNG"],
            categories=["hero-images", "background-images", "product-images"],
            license="Unsplash License"
        )
    
    @handle_errors(reraise=True)
    def analyze_project_assets(self, project_path: str) -> Dict[str, Any]:
        """
        Analyze existing assets in a project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Analysis results with discovered assets and recommendations
        """
        project_path = Path(project_path)
        analysis_results = {
            "assets_found": 0,
            "asset_directories": [],
            "asset_types": {},
            "missing_categories": [],
            "recommendations": []
        }
        
        # Common asset directories
        asset_dirs = [
            project_path / "public" / "assets",
            project_path / "public" / "images",
            project_path / "public" / "icons",
            project_path / "src" / "assets",
            project_path / "src" / "images",
            project_path / "src" / "icons",
            project_path / "assets",
            project_path / "static",
            project_path / "media"
        ]
        
        for asset_dir in asset_dirs:
            if asset_dir.exists():
                analysis_results["asset_directories"].append(str(asset_dir))
                assets = self._scan_asset_directory(asset_dir)
                
                for asset in assets:
                    self.assets[asset.name] = asset
                    analysis_results["assets_found"] += 1
                    
                    asset_type = asset.asset_type.value
                    if asset_type not in analysis_results["asset_types"]:
                        analysis_results["asset_types"][asset_type] = 0
                    analysis_results["asset_types"][asset_type] += 1
        
        # Analyze asset gaps
        self._analyze_asset_gaps(analysis_results)
        
        return analysis_results
    
    def _scan_asset_directory(self, directory: Path) -> List[AssetMetadata]:
        """Scan a directory for assets and create metadata."""
        assets = []
        
        # Supported file extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
        font_extensions = {'.woff', '.woff2', '.ttf', '.otf', '.eot'}
        video_extensions = {'.mp4', '.webm', '.ogg', '.avi', '.mov'}
        audio_extensions = {'.mp3', '.wav', '.ogg', '.aac', '.flac'}
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    extension = file_path.suffix.lower()
                    
                    # Determine asset type
                    asset_type = None
                    if extension in image_extensions:
                        if extension == '.svg':
                            asset_type = AssetType.ICON if 'icon' in str(file_path).lower() else AssetType.IMAGE
                        else:
                            asset_type = AssetType.IMAGE
                    elif extension in font_extensions:
                        asset_type = AssetType.FONT
                    elif extension in video_extensions:
                        asset_type = AssetType.VIDEO
                    elif extension in audio_extensions:
                        asset_type = AssetType.AUDIO
                    
                    if asset_type:
                        # Infer category and purpose
                        category = self._infer_asset_category(file_path)
                        purposes = self._infer_asset_purposes(file_path)
                        tags = self._extract_asset_tags(file_path)
                        
                        asset = AssetMetadata(
                            name=file_path.stem,
                            path=str(file_path),
                            asset_type=asset_type,
                            category=category,
                            purpose=purposes,
                            tags=tags,
                            format=extension[1:].upper(),
                            size=self._get_image_dimensions(file_path) if asset_type in [AssetType.IMAGE, AssetType.ICON] else None
                        )
                        
                        assets.append(asset)
        
        except Exception as e:
            print(f"⚠️ Error scanning {directory}: {e}")
        
        return assets
    
    def _infer_asset_category(self, file_path: Path) -> AssetCategory:
        """Infer asset category from file path and name."""
        path_str = str(file_path).lower()
        name = file_path.stem.lower()
        
        # Check path for category hints
        if any(keyword in path_str for keyword in ['icon', 'icons']):
            if any(keyword in path_str for keyword in ['brand', 'logo']):
                return AssetCategory.BRAND_ICONS
            elif any(keyword in path_str for keyword in ['social']):
                return AssetCategory.SOCIAL_ICONS
            elif any(keyword in path_str for keyword in ['business']):
                return AssetCategory.BUSINESS_ICONS
            elif any(keyword in path_str for keyword in ['tech', 'technology']):
                return AssetCategory.TECH_ICONS
            else:
                return AssetCategory.UI_ICONS
        
        # Check for image categories
        if any(keyword in path_str for keyword in ['hero', 'banner']):
            return AssetCategory.HERO_IMAGES
        elif any(keyword in path_str for keyword in ['product']):
            return AssetCategory.PRODUCT_IMAGES
        elif any(keyword in path_str for keyword in ['avatar', 'profile']):
            return AssetCategory.AVATAR_IMAGES
        elif any(keyword in path_str for keyword in ['background', 'bg']):
            return AssetCategory.BACKGROUND_IMAGES
        elif any(keyword in path_str for keyword in ['illustration']):
            return AssetCategory.ILLUSTRATIONS
        elif any(keyword in path_str for keyword in ['logo']):
            return AssetCategory.LOGOS
        elif any(keyword in path_str for keyword in ['pattern']):
            return AssetCategory.PATTERNS
        
        # Default based on asset type
        if file_path.suffix.lower() == '.svg':
            return AssetCategory.UI_ICONS
        else:
            return AssetCategory.HERO_IMAGES  # Default for images
    
    def _infer_asset_purposes(self, file_path: Path) -> List[AssetPurpose]:
        """Infer asset purposes from file path and name."""
        path_str = str(file_path).lower()
        name = file_path.stem.lower()
        purposes = []
        
        # Functional purposes
        if any(keyword in name for keyword in ['button', 'click', 'action', 'submit', 'cancel']):
            purposes.append(AssetPurpose.FUNCTIONAL)
        
        # Navigational purposes
        if any(keyword in name for keyword in ['nav', 'menu', 'home', 'back', 'forward', 'arrow']):
            purposes.append(AssetPurpose.NAVIGATIONAL)
        
        # Informational purposes
        if any(keyword in name for keyword in ['info', 'help', 'question', 'alert', 'warning']):
            purposes.append(AssetPurpose.INFORMATIONAL)
        
        # Branding purposes
        if any(keyword in name for keyword in ['logo', 'brand', 'company']):
            purposes.append(AssetPurpose.BRANDING)
        
        # Interactive purposes
        if any(keyword in name for keyword in ['hover', 'active', 'focus', 'toggle', 'switch']):
            purposes.append(AssetPurpose.INTERACTIVE)
        
        # Decorative if no specific purpose found
        if not purposes:
            purposes.append(AssetPurpose.DECORATIVE)
        
        return purposes
    
    def _extract_asset_tags(self, file_path: Path) -> List[str]:
        """Extract semantic tags from file name and path."""
        path_str = str(file_path).lower()
        name = file_path.stem.lower()
        tags = []
        
        # Extract words from filename
        words = re.findall(r'[a-z]+', name)
        tags.extend(words)
        
        # Add path-based tags
        path_parts = file_path.parts
        for part in path_parts:
            if part.lower() in ['icons', 'images', 'assets']:
                continue
            tags.extend(re.findall(r'[a-z]+', part.lower()))
        
        # Remove duplicates and common words
        common_words = {'icon', 'image', 'img', 'pic', 'photo', 'asset', 'file'}
        tags = list(set(tag for tag in tags if len(tag) > 2 and tag not in common_words))
        
        return tags[:10]  # Limit to 10 tags
    
    def _get_image_dimensions(self, file_path: Path) -> Optional[Tuple[int, int]]:
        """Get image dimensions if possible."""
        try:
            # This would require PIL or similar library
            # For now, return None - can be implemented if needed
            return None
        except Exception:
            return None
    
    def _analyze_asset_gaps(self, analysis_results: Dict[str, Any]):
        """Analyze gaps in asset coverage."""
        missing_categories = []
        recommendations = []
        
        # Check for missing essential categories
        essential_categories = [AssetCategory.UI_ICONS, AssetCategory.HERO_IMAGES]
        found_categories = [cat for assets in self.assets.values() for cat in [assets.category]]
        
        for category in essential_categories:
            if category not in found_categories:
                missing_categories.append(category.value)
                recommendations.append(f"Consider adding {category.value.replace('-', ' ')} to your asset library")
        
        # Check for missing common icons
        common_icons = ['menu', 'close', 'search', 'user', 'home', 'settings']
        found_icons = [asset.name.lower() for asset in self.assets.values() 
                      if asset.asset_type == AssetType.ICON]
        
        for icon in common_icons:
            if not any(icon in found_icon for found_icon in found_icons):
                recommendations.append(f"Consider adding a '{icon}' icon")
        
        analysis_results["missing_categories"] = missing_categories
        analysis_results["recommendations"].extend(recommendations)
    
    def recommend_assets_for_component(
        self, 
        component_type: str, 
        context: str = "",
        max_recommendations: int = 5
    ) -> List[AssetRecommendation]:
        """
        Recommend assets for a specific component type and context.
        
        Args:
            component_type: Type of component (button, form, card, etc.)
            context: Additional context about the component usage
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of asset recommendations with confidence scores
        """
        recommendations = []
        context_lower = context.lower()
        
        # Get component patterns
        component_patterns = self.component_asset_patterns.get(component_type, {})
        
        # Score existing assets
        for asset_name, asset in self.assets.items():
            confidence = self._calculate_asset_confidence(
                asset, component_type, context_lower, component_patterns
            )
            
            if confidence > 0.3:  # Minimum confidence threshold
                reasoning = self._generate_asset_reasoning(
                    asset, component_type, context, confidence
                )
                
                recommendation = AssetRecommendation(
                    asset=asset,
                    confidence=confidence,
                    reasoning=reasoning,
                    context_match=self._analyze_context_match(asset, context_lower),
                    usage_examples=self._generate_usage_examples(asset, component_type)
                )
                recommendations.append(recommendation)
        
        # Add library-based recommendations if no local assets found
        if len(recommendations) < max_recommendations:
            library_recommendations = self._recommend_from_libraries(
                component_type, context, max_recommendations - len(recommendations)
            )
            recommendations.extend(library_recommendations)
        
        # Sort by confidence and return top recommendations
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        return recommendations[:max_recommendations]
    
    def _calculate_asset_confidence(
        self, 
        asset: AssetMetadata, 
        component_type: str, 
        context: str,
        component_patterns: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for asset recommendation."""
        confidence = 0.0
        
        # Base score from asset name matching component patterns
        if component_patterns.get("icons") and asset.asset_type == AssetType.ICON:
            for icon_name in component_patterns["icons"]:
                if icon_name in asset.name.lower() or icon_name in asset.tags:
                    confidence += 0.4
                    break
        
        # Score from category match
        expected_categories = component_patterns.get("categories", [])
        if asset.category in expected_categories:
            confidence += 0.3
        
        # Score from purpose match
        expected_purposes = component_patterns.get("purposes", [])
        if any(purpose in asset.purpose for purpose in expected_purposes):
            confidence += 0.2
        
        # Context-specific scoring
        if context:
            context_words = context.split()
            for word in context_words:
                if word in asset.name.lower() or word in asset.tags:
                    confidence += 0.1
        
        # Boost for commonly used assets
        if asset.usage_count > 5:
            confidence += 0.1
        
        # Boost for high-quality formats
        if asset.format in ['SVG', 'WEBP', 'PNG']:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    def _generate_asset_reasoning(
        self, 
        asset: AssetMetadata, 
        component_type: str, 
        context: str, 
        confidence: float
    ) -> str:
        """Generate human-readable reasoning for asset recommendation."""
        reasons = []
        
        if asset.asset_type == AssetType.ICON:
            reasons.append(f"Icon suitable for {component_type} components")
        
        if any(purpose in [AssetPurpose.FUNCTIONAL, AssetPurpose.INTERACTIVE] for purpose in asset.purpose):
            reasons.append("Designed for interactive use")
        
        if context and any(word in asset.name.lower() for word in context.lower().split()):
            reasons.append("Name matches context requirements")
        
        if asset.format == 'SVG':
            reasons.append("Scalable vector format")
        
        if confidence > 0.7:
            reasons.append("High relevance match")
        elif confidence > 0.5:
            reasons.append("Good relevance match")
        else:
            reasons.append("Moderate relevance match")
        
        return "; ".join(reasons) if reasons else "General compatibility"
    
    def _analyze_context_match(self, asset: AssetMetadata, context: str) -> Dict[str, float]:
        """Analyze how well asset matches the context."""
        context_match = {
            "name_match": 0.0,
            "tag_match": 0.0,
            "purpose_match": 0.0,
            "category_match": 0.0
        }
        
        if context:
            context_words = set(context.lower().split())
            
            # Name match scoring
            asset_name_words = set(asset.name.lower().split())
            name_overlap = len(context_words.intersection(asset_name_words))
            context_match["name_match"] = name_overlap / max(len(context_words), 1)
            
            # Tag match scoring
            asset_tags = set(asset.tags)
            tag_overlap = len(context_words.intersection(asset_tags))
            context_match["tag_match"] = tag_overlap / max(len(context_words), 1)
        
        return context_match
    
    def _generate_usage_examples(self, asset: AssetMetadata, component_type: str) -> List[str]:
        """Generate usage examples for the asset."""
        examples = []
        
        if asset.asset_type == AssetType.ICON:
            if component_type == "button":
                examples.extend([
                    f"<Button icon={asset.name}>Action</Button>",
                    f"<IconButton icon=\"{asset.name}\" />",
                    f"<Button leftIcon={asset.name}>Submit</Button>"
                ])
            elif component_type == "navigation":
                examples.extend([
                    f"<NavItem icon={asset.name}>Menu Item</NavItem>",
                    f"<MenuItem icon=\"{asset.name}\">Option</MenuItem>"
                ])
            elif component_type == "form":
                examples.extend([
                    f"<Input leftIcon={asset.name} />",
                    f"<FormField icon=\"{asset.name}\" />"
                ])
        
        elif asset.asset_type == AssetType.IMAGE:
            if component_type == "card":
                examples.extend([
                    f"<Card image=\"{asset.path}\">Content</Card>",
                    f"<img src=\"{asset.path}\" alt=\"{asset.name}\" />"
                ])
            elif component_type == "hero":
                examples.extend([
                    f"<Hero backgroundImage=\"{asset.path}\">Content</Hero>",
                    f"<Section bg=\"url({asset.path})\">Content</Section>"
                ])
        
        return examples[:3]  # Limit to 3 examples
    
    def _recommend_from_libraries(
        self, 
        component_type: str, 
        context: str, 
        max_recommendations: int
    ) -> List[AssetRecommendation]:
        """Recommend assets from popular libraries."""
        library_recommendations = []
        
        # Get component patterns
        component_patterns = self.component_asset_patterns.get(component_type, {})
        suggested_icons = component_patterns.get("icons", [])
        
        # Recommend from Heroicons (most popular for React/Tailwind projects)
        heroicons_lib = self.asset_libraries.get("heroicons")
        if heroicons_lib and suggested_icons:
            for icon_name in suggested_icons[:max_recommendations]:
                # Create virtual asset metadata
                virtual_asset = AssetMetadata(
                    name=icon_name,
                    path=f"{heroicons_lib.base_url}/{icon_name}",
                    asset_type=AssetType.ICON,
                    category=AssetCategory.UI_ICONS,
                    purpose=[AssetPurpose.FUNCTIONAL],
                    tags=[icon_name.replace("-", " ").split()],
                    format="SVG"
                )
                
                confidence = 0.8  # High confidence for popular library
                reasoning = f"Popular {icon_name} icon from Heroicons library, perfect for {component_type} components"
                
                recommendation = AssetRecommendation(
                    asset=virtual_asset,
                    confidence=confidence,
                    reasoning=reasoning,
                    usage_examples=[
                        f"import {{ {self._to_pascal_case(icon_name)}Icon }} from '@heroicons/react/24/outline'",
                        f"<{self._to_pascal_case(icon_name)}Icon className=\"w-5 h-5\" />",
                        f"<Button icon={{{self._to_pascal_case(icon_name)}Icon}}>Action</Button>"
                    ]
                )
                
                library_recommendations.append(recommendation)
        
        return library_recommendations[:max_recommendations]
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert kebab-case to PascalCase."""
        return ''.join(word.capitalize() for word in name.split('-'))
    
    def get_asset_usage_guidelines(self, component_type: str) -> Dict[str, Any]:
        """Get comprehensive asset usage guidelines for a component type."""
        guidelines = {
            "recommended_libraries": [],
            "size_guidelines": {},
            "format_preferences": [],
            "accessibility": [],
            "performance": [],
            "best_practices": []
        }
        
        # Component-specific guidelines
        if component_type == "button":
            guidelines.update({
                "recommended_libraries": ["Heroicons", "Lucide", "Feather"],
                "size_guidelines": {"icon": "16px-24px", "touch_target": "44px minimum"},
                "format_preferences": ["SVG", "PNG with @2x variants"],
                "accessibility": [
                    "Provide alt text or aria-label for icon-only buttons",
                    "Ensure sufficient color contrast",
                    "Use semantic HTML button element"
                ],
                "performance": [
                    "Use SVG sprites for multiple icons",
                    "Optimize icon file sizes",
                    "Consider icon loading strategies"
                ],
                "best_practices": [
                    "Keep icons simple and recognizable",
                    "Maintain consistent icon style across the app",
                    "Use familiar icons for common actions"
                ]
            })
        
        elif component_type == "card":
            guidelines.update({
                "size_guidelines": {"image": "16:9 or 4:3 aspect ratio", "thumbnail": "150px-300px"},
                "format_preferences": ["WebP with fallback", "JPEG for photos", "PNG for graphics"],
                "accessibility": [
                    "Always provide alt text for images",
                    "Use proper heading hierarchy",
                    "Ensure adequate color contrast"
                ],
                "performance": [
                    "Use responsive images with srcset",
                    "Implement lazy loading for images",
                    "Compress images appropriately"
                ],
                "best_practices": [
                    "Use consistent image aspect ratios",
                    "Provide placeholder states",
                    "Optimize for different screen densities"
                ]
            })
        
        return guidelines
    
    def export_asset_analysis(self) -> Dict[str, Any]:
        """Export comprehensive asset analysis data."""
        return {
            "total_assets": len(self.assets),
            "assets_by_type": {
                asset_type.value: len([a for a in self.assets.values() if a.asset_type == asset_type])
                for asset_type in AssetType
            },
            "assets_by_category": {
                category.value: len([a for a in self.assets.values() if a.category == category])
                for category in AssetCategory
            },
            "available_libraries": {
                name: {
                    "source": lib.source,
                    "formats": lib.supported_formats,
                    "styles": lib.style_variants,
                    "license": lib.license
                }
                for name, lib in self.asset_libraries.items()
            },
            "component_patterns": self.component_asset_patterns,
            "context_patterns": self.context_patterns
        }


# Global instance
_asset_recommender_instance = None

def get_smart_asset_recommender() -> SmartAssetRecommender:
    """Get the global smart asset recommender instance."""
    global _asset_recommender_instance
    if _asset_recommender_instance is None:
        _asset_recommender_instance = SmartAssetRecommender()
    return _asset_recommender_instance