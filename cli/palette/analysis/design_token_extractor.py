"""
Design token extraction module.
Responsible for extracting colors, typography, spacing, etc. from projects.
"""

import os
import re
import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict

from ..interfaces import DesignTokens


class DesignTokenExtractor:
    """Extracts design tokens from project configuration and CSS."""
    
    def __init__(self):
        self.main_css_file_path = None
    
    def extract(self, project_path: str) -> DesignTokens:
        """
        Extract all design tokens from the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            DesignTokens with extracted values
        """
        # First, try to get tokens from tailwind.config.js
        tailwind_config = self._parse_tailwind_config(project_path)
        
        # Extract colors with semantic structure
        color_data = self._extract_colors_from_config(tailwind_config, project_path)
        
        tokens = DesignTokens(
            colors=color_data.get("custom", {}),
            semantic_colors=color_data.get("semantic", {}),
            spacing=self._extract_spacing_from_config(tailwind_config, project_path),
            typography=self._extract_typography_from_config(tailwind_config, project_path),
            shadows=self._extract_shadows_from_config(tailwind_config),
            border_radius=self._extract_border_radius_from_config(tailwind_config),
        )
        
        return tokens
    
    def _parse_tailwind_config(self, project_path: str) -> Optional[Dict]:
        """Parse tailwind.config.js using Node.js."""
        config_files = ["tailwind.config.js", "tailwind.config.ts"]
        
        for config_file in config_files:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                try:
                    # Use the JavaScript parser to extract config
                    parser_path = os.path.join(
                        os.path.dirname(__file__), "..", "utils", "tailwind_parser.js"
                    )
                    
                    if not os.path.exists(parser_path):
                        print(f"Warning: Tailwind parser not found at {parser_path}")
                        return self._parse_tailwind_config_fallback(config_path)
                    
                    result = subprocess.run(
                        ["node", parser_path, config_path],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    
                    if result.returncode == 0:
                        try:
                            return json.loads(result.stdout)
                        except json.JSONDecodeError:
                            print(f"Warning: Failed to parse Tailwind config JSON output")
                    else:
                        print(f"Warning: Tailwind parser error: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print("Warning: Tailwind config parsing timed out")
                except Exception as e:
                    print(f"Warning: Failed to parse Tailwind config: {e}")
        
        return None
    
    def _parse_tailwind_config_fallback(self, config_path: str) -> Optional[Dict]:
        """Fallback regex-based Tailwind config parser."""
        try:
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Extract theme extend section
            theme_match = re.search(r'theme:\s*{([\s\S]*?)^}', content, re.MULTILINE)
            if theme_match:
                theme_content = theme_match.group(1)
                
                # Extract colors
                colors_match = re.search(r'colors:\s*{([\s\S]*?)^(\s{2,4})}', theme_content, re.MULTILINE)
                if colors_match:
                    colors_content = colors_match.group(1)
                    # Basic color extraction
                    colors = {}
                    color_pattern = r'"?(\w+)"?\s*:\s*"([^"]+)"'
                    for match in re.finditer(color_pattern, colors_content):
                        colors[match.group(1)] = match.group(2)
                    
                    return {"theme": {"extend": {"colors": colors}}}
        except Exception as e:
            print(f"Warning: Fallback Tailwind parser failed: {e}")
        
        return None
    
    def _extract_colors_from_config(self, config: Optional[Dict], project_path: str) -> Dict:
        """Extract colors from Tailwind config and CSS files."""
        colors = {
            "custom": {},
            "semantic": {},
            "structure": {}
        }
        
        # Extract from Tailwind config
        if config and "theme" in config:
            theme = config["theme"]
            
            # Get extended colors
            if "extend" in theme and "colors" in theme["extend"]:
                colors["structure"] = theme["extend"]["colors"]
                
                # Flatten structure for custom colors
                for color_name, color_value in theme["extend"]["colors"].items():
                    if isinstance(color_value, dict):
                        # Nested color (e.g., gray-100, gray-200)
                        for shade, value in color_value.items():
                            colors["custom"][f"{color_name}-{shade}"] = value
                            
                            # Detect semantic colors
                            if color_name in ["primary", "secondary", "accent", "neutral"]:
                                colors["semantic"][f"{color_name}-{shade}"] = value
                    else:
                        colors["custom"][color_name] = color_value
                        
                        # Single semantic colors
                        if color_name in ["primary", "secondary", "accent", "error", "warning", "success"]:
                            colors["semantic"][color_name] = color_value
        
        # Extract from CSS files
        css_colors = self._extract_css_variables(project_path)
        colors["custom"].update(css_colors.get("colors", {}))
        
        return colors
    
    def _extract_css_variables(self, project_path: str) -> Dict:
        """Extract CSS custom properties from project CSS files."""
        css_vars = {
            "colors": {},
            "spacing": {},
            "typography": {}
        }
        
        # Find and parse CSS files
        css_files = self._find_all_css_files(project_path)
        
        for css_file in css_files:
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract CSS custom properties
                var_pattern = r'--([a-zA-Z0-9-]+):\s*([^;]+);'
                for match in re.finditer(var_pattern, content):
                    var_name = match.group(1)
                    var_value = match.group(2).strip()
                    
                    # Categorize variables
                    if any(keyword in var_name for keyword in ["color", "bg", "text", "border"]):
                        css_vars["colors"][var_name] = var_value
                    elif any(keyword in var_name for keyword in ["space", "gap", "margin", "padding"]):
                        css_vars["spacing"][var_name] = var_value
                    elif any(keyword in var_name for keyword in ["font", "text"]):
                        css_vars["typography"][var_name] = var_value
            
            except Exception as e:
                print(f"Warning: Failed to parse CSS file {css_file}: {e}")
        
        return css_vars
    
    def _find_all_css_files(self, project_path: str) -> List[str]:
        """Find main CSS files in the project."""
        css_files = []
        
        # Common CSS file locations
        css_patterns = [
            "styles/globals.css",
            "src/styles/globals.css",
            "app/globals.css",
            "src/app/globals.css",
            "styles/main.css",
            "src/styles/main.css",
            "index.css",
            "src/index.css",
        ]
        
        for pattern in css_patterns:
            css_path = os.path.join(project_path, pattern)
            if os.path.exists(css_path):
                css_files.append(css_path)
                if not self.main_css_file_path:
                    self.main_css_file_path = css_path
        
        return css_files
    
    def _extract_spacing_from_config(self, config: Optional[Dict], project_path: str) -> Dict[str, str]:
        """Extract spacing values from configuration."""
        spacing = {}
        
        if config and "theme" in config:
            theme = config["theme"]
            
            # Get extended spacing
            if "extend" in theme and "spacing" in theme["extend"]:
                spacing_config = theme["extend"]["spacing"]
                if isinstance(spacing_config, dict):
                    spacing.update(spacing_config)
        
        # Add CSS variable spacing
        css_vars = self._extract_css_variables(project_path)
        spacing.update(css_vars.get("spacing", {}))
        
        # Default spacing if none found
        if not spacing:
            spacing = {
                "xs": "0.5rem",
                "sm": "1rem",
                "md": "1.5rem",
                "lg": "2rem",
                "xl": "3rem",
            }
        
        return spacing
    
    def _extract_typography_from_config(self, config: Optional[Dict], project_path: str) -> Dict[str, str]:
        """Extract typography settings from configuration."""
        typography = {}
        
        if config and "theme" in config:
            theme = config["theme"]
            
            # Get font family
            if "extend" in theme and "fontFamily" in theme["extend"]:
                font_config = theme["extend"]["fontFamily"]
                if isinstance(font_config, dict):
                    for font_name, font_value in font_config.items():
                        if isinstance(font_value, list):
                            typography[font_name] = ", ".join(font_value)
                        else:
                            typography[font_name] = str(font_value)
        
        # Add CSS variable typography
        css_vars = self._extract_css_variables(project_path)
        typography.update(css_vars.get("typography", {}))
        
        # Default typography if none found
        if not typography:
            typography = {
                "sans": "system-ui, -apple-system, sans-serif",
                "serif": "Georgia, serif",
                "mono": "Menlo, monospace",
            }
        
        return typography
    
    def _extract_shadows_from_config(self, config: Optional[Dict]) -> Dict[str, str]:
        """Extract shadow values from configuration."""
        shadows = {}
        
        if config and "theme" in config:
            theme = config["theme"]
            
            # Get extended shadows
            if "extend" in theme and "boxShadow" in theme["extend"]:
                shadow_config = theme["extend"]["boxShadow"]
                if isinstance(shadow_config, dict):
                    shadows.update(shadow_config)
        
        # Default shadows if none found
        if not shadows:
            shadows = {
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
            }
        
        return shadows
    
    def _extract_border_radius_from_config(self, config: Optional[Dict]) -> Dict[str, str]:
        """Extract border radius values from configuration."""
        border_radius = {}
        
        if config and "theme" in config:
            theme = config["theme"]
            
            # Get extended border radius
            if "extend" in theme and "borderRadius" in theme["extend"]:
                radius_config = theme["extend"]["borderRadius"]
                if isinstance(radius_config, dict):
                    border_radius.update(radius_config)
        
        # Default border radius if none found
        if not border_radius:
            border_radius = {
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "full": "9999px",
            }
        
        return border_radius