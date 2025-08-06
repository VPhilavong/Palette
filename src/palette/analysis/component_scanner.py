"""
Component scanner module.
Responsible for discovering and analyzing React components in the project.
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path

from ..interfaces import ComponentInfo


class ComponentScanner:
    """Scans and analyzes React components in the project."""
    
    def scan(self, project_path: str) -> List[ComponentInfo]:
        """
        Scan for all components in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of ComponentInfo objects
        """
        components = []
        
        # Scan shadcn/ui components
        shadcn_components = self._scan_shadcn_ui_components(project_path)
        components.extend(shadcn_components)
        
        # Scan custom components
        custom_components = self._scan_custom_components(project_path)
        components.extend(custom_components)
        
        return components
    
    def _scan_shadcn_ui_components(self, project_path: str) -> List[ComponentInfo]:
        """Scan for available shadcn/ui components with detailed information."""
        components = []
        ui_paths = [
            os.path.join(project_path, "components", "ui"),
            os.path.join(project_path, "src", "components", "ui"),
        ]
        
        for ui_path in ui_paths:
            if os.path.exists(ui_path):
                for file in os.listdir(ui_path):
                    if file.endswith((".tsx", ".ts", ".jsx", ".js")):
                        component_name = (
                            file.replace(".tsx", "")
                            .replace(".ts", "")
                            .replace(".jsx", "")
                            .replace(".js", "")
                        )
                        
                        # Build import path for shadcn/ui components
                        rel_path = os.path.relpath(ui_path, project_path)
                        import_path = self._build_import_path(rel_path, component_name)
                        
                        # Extract component info
                        file_path = os.path.join(ui_path, file)
                        
                        component_info = ComponentInfo(
                            name=component_name,
                            file_path=file_path,
                            import_path=import_path,
                            purpose=self._get_shadcn_component_purpose(component_name),
                            type=self._infer_component_type(component_name),
                            is_shadcn=True
                        )
                        
                        # Extract props if possible
                        props = self._extract_component_props(file_path)
                        if props:
                            component_info.props = props
                        
                        components.append(component_info)
                break
        
        return components
    
    def _scan_custom_components(self, project_path: str) -> List[ComponentInfo]:
        """Scan for custom components with detailed information."""
        components = []
        component_paths = [
            os.path.join(project_path, "components"),
            os.path.join(project_path, "src", "components"),
        ]
        
        for comp_path in component_paths:
            if os.path.exists(comp_path):
                for root, dirs, files in os.walk(comp_path):
                    # Skip ui directory (handled separately)
                    if "ui" in dirs:
                        dirs.remove("ui")
                    
                    for file in files:
                        if file.endswith((".tsx", ".ts", ".jsx", ".js")):
                            component_name = (
                                file.replace(".tsx", "")
                                .replace(".ts", "")
                                .replace(".jsx", "")
                                .replace(".js", "")
                            )
                            
                            # Build import path
                            rel_path = os.path.relpath(root, project_path)
                            import_path = self._build_import_path(rel_path, component_name)
                            
                            # Extract component info
                            file_path = os.path.join(root, file)
                            
                            component_info = ComponentInfo(
                                name=component_name,
                                file_path=file_path,
                                import_path=import_path,
                                purpose=self._analyze_component_purpose(file_path, component_name),
                                type=self._infer_component_type(component_name),
                                is_shadcn=False
                            )
                            
                            # Extract props if possible
                            props = self._extract_component_props(file_path)
                            if props:
                                component_info.props = props
                            
                            # Extract description
                            description = self._extract_component_description(file_path)
                            if description:
                                component_info.description = description
                            
                            # Avoid duplicates
                            if not any(c.name == component_name for c in components):
                                components.append(component_info)
                break
        
        return components
    
    def _build_import_path(self, rel_path: str, component_name: str) -> str:
        """Build the import path for a component."""
        # Convert file system path to import path
        path_parts = rel_path.split(os.sep)
        
        # Common import path patterns
        if path_parts[0] == "src" and len(path_parts) > 1:
            # @/components/ComponentName or ~/components/ComponentName
            import_base = "/".join(path_parts[1:])
            return f"@/{import_base}/{component_name}"
        elif path_parts[0] in ["components", "app"]:
            # Direct from root: /components/ComponentName
            import_base = "/".join(path_parts)
            return f"@/{import_base}/{component_name}"
        else:
            # Relative import
            import_base = "/".join(path_parts)
            return f"./{import_base}/{component_name}"
    
    def _analyze_component_purpose(self, file_path: str, component_name: str) -> str:
        """Analyze component purpose from file content and name."""
        purpose = ""
        
        # First, infer from component name
        purpose = self._infer_purpose_from_name(component_name)
        
        # Try to read file for JSDoc or comments
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # Read first 500 chars
                
                # Look for JSDoc comments
                jsdoc_match = re.search(r'/\*\*\s*\n\s*\*\s*(.+?)(?:\n|\*/)', content)
                if jsdoc_match:
                    doc_line = jsdoc_match.group(1).strip()
                    if not doc_line.startswith('@'):  # Skip JSDoc tags
                        purpose = doc_line
                
                # Look for leading comments
                elif content.strip().startswith('//'):
                    comment_match = re.match(r'//\s*(.+)', content.strip())
                    if comment_match:
                        purpose = comment_match.group(1).strip()
                        
        except Exception:
            pass
        
        return purpose
    
    def _extract_component_description(self, file_path: str) -> Optional[str]:
        """Extract detailed component description from JSDoc."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 chars
                
                # Look for JSDoc comment with description
                jsdoc_pattern = r'/\*\*\s*\n((?:\s*\*[^\n]*\n)*)\s*\*/'
                match = re.search(jsdoc_pattern, content)
                
                if match:
                    jsdoc_content = match.group(1)
                    lines = jsdoc_content.split('\n')
                    
                    desc_lines = []
                    for line in lines:
                        line = line.strip().lstrip('*').strip()
                        if line and not line.startswith('@'):
                            desc_lines.append(line)
                    
                    if desc_lines:
                        return ' '.join(desc_lines)
        except Exception:
            pass
        
        return None
    
    def _extract_component_props(self, file_path: str) -> List[Dict[str, str]]:
        """Extract component props from TypeScript interface or PropTypes."""
        props = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for TypeScript interface
                interface_pattern = r'interface\s+\w*Props\s*{\s*([^}]+)\s*}'
                match = re.search(interface_pattern, content)
                
                if match:
                    props_content = match.group(1)
                    # Extract individual props
                    prop_pattern = r'(\w+)(\?)?\s*:\s*([^;]+);'
                    for prop_match in re.finditer(prop_pattern, props_content):
                        prop_name = prop_match.group(1)
                        is_optional = prop_match.group(2) == '?'
                        prop_type = prop_match.group(3).strip()
                        
                        props.append({
                            "name": prop_name,
                            "type": prop_type,
                            "required": not is_optional
                        })
                
                # Fallback to function parameters
                elif 'function' in content or '=>' in content:
                    # Look for destructured props
                    param_pattern = r'(?:function\s+\w+|const\s+\w+\s*=)\s*\(\s*{\s*([^}]+)\s*}'
                    match = re.search(param_pattern, content)
                    
                    if match:
                        params = match.group(1)
                        # Extract parameter names
                        for param in params.split(','):
                            param = param.strip()
                            if param:
                                props.append({
                                    "name": param.split(':')[0].strip(),
                                    "type": "unknown",
                                    "required": True
                                })
        except Exception:
            pass
        
        return props
    
    def _infer_component_type(self, component_name: str) -> str:
        """Infer the component type from its name."""
        name_lower = component_name.lower()
        
        if any(keyword in name_lower for keyword in ["button", "btn", "action"]):
            return "button"
        elif any(keyword in name_lower for keyword in ["card", "panel", "tile"]):
            return "container"
        elif any(keyword in name_lower for keyword in ["modal", "dialog", "popup"]):
            return "overlay"
        elif any(keyword in name_lower for keyword in ["form", "input", "field", "select", "checkbox", "radio"]):
            return "form"
        elif any(keyword in name_lower for keyword in ["nav", "menu", "sidebar", "header", "footer"]):
            return "navigation"
        elif any(keyword in name_lower for keyword in ["list", "table", "grid"]):
            return "data-display"
        elif any(keyword in name_lower for keyword in ["hero", "banner", "section"]):
            return "section"
        elif any(keyword in name_lower for keyword in ["layout", "container", "wrapper"]):
            return "layout"
        elif any(keyword in name_lower for keyword in ["loading", "spinner", "skeleton"]):
            return "feedback"
        elif any(keyword in name_lower for keyword in ["avatar", "profile", "user"]):
            return "user"
        else:
            return "component"
    
    def _infer_purpose_from_name(self, component_name: str) -> str:
        """Infer component purpose from its name."""
        name_lower = component_name.lower()
        
        # Common component purposes
        purposes = {
            "button": "Interactive button for user actions",
            "card": "Content container with consistent styling",
            "modal": "Overlay dialog for focused interactions",
            "form": "Data input and submission form",
            "header": "Page or section header component",
            "footer": "Page or section footer component",
            "nav": "Navigation menu component",
            "sidebar": "Side navigation or content panel",
            "table": "Data table for displaying structured information",
            "list": "List container for displaying items",
            "input": "User input field component",
            "select": "Dropdown selection component",
            "checkbox": "Checkbox input component",
            "radio": "Radio button input component",
            "toggle": "Toggle switch component",
            "tab": "Tabbed interface component",
            "accordion": "Collapsible content sections",
            "tooltip": "Hover information tooltip",
            "dropdown": "Dropdown menu component",
            "avatar": "User profile image component",
            "badge": "Small labeling component",
            "alert": "Alert message component",
            "toast": "Temporary notification component",
            "progress": "Progress indicator component",
            "spinner": "Loading spinner component",
            "skeleton": "Loading placeholder component",
            "slider": "Range slider component",
            "pagination": "Page navigation component",
            "breadcrumb": "Navigation breadcrumb component",
        }
        
        # Check for matches
        for key, purpose in purposes.items():
            if key in name_lower:
                return purpose
        
        # Default purpose
        return f"{component_name} component for the application"
    
    def _get_shadcn_component_purpose(self, component_name: str) -> str:
        """Get specific purpose for shadcn/ui components."""
        name_lower = component_name.lower()
        
        # shadcn/ui specific component purposes
        shadcn_purposes = {
            "accordion": "Collapsible content sections with animations",
            "alert": "Alert messages with variant styles",
            "alert-dialog": "Modal dialog for important alerts",
            "aspect-ratio": "Maintain aspect ratio for media content",
            "avatar": "User profile image with fallback",
            "badge": "Small count and labeling component",
            "button": "Interactive button with variants and sizes",
            "calendar": "Date picker calendar component",
            "card": "Card container with header, content, and footer",
            "carousel": "Image/content carousel slider",
            "checkbox": "Checkbox input with label",
            "collapsible": "Collapsible content area",
            "command": "Command menu with search and keyboard navigation",
            "context-menu": "Right-click context menu",
            "dialog": "Modal dialog overlay",
            "drawer": "Sliding panel from screen edge",
            "dropdown-menu": "Dropdown menu with keyboard navigation",
            "form": "Form control with validation",
            "hover-card": "Card shown on hover",
            "input": "Text input field with styling",
            "label": "Form label element",
            "menubar": "Application menubar",
            "navigation-menu": "Navigation with dropdowns",
            "pagination": "Page navigation controls",
            "popover": "Floating content panel",
            "progress": "Progress bar indicator",
            "radio-group": "Radio button group",
            "scroll-area": "Custom scrollable area",
            "select": "Select dropdown with search",
            "separator": "Visual separator line",
            "sheet": "Side panel overlay",
            "skeleton": "Loading placeholder",
            "slider": "Range slider input",
            "switch": "Toggle switch control",
            "table": "Data table with features",
            "tabs": "Tabbed interface component",
            "textarea": "Multi-line text input",
            "toast": "Toast notification popup",
            "toggle": "Toggle button component",
            "toggle-group": "Group of toggle buttons",
            "tooltip": "Hover tooltip component",
        }
        
        # Check for exact match first
        if name_lower in shadcn_purposes:
            return shadcn_purposes[name_lower]
        
        # Check for hyphenated version
        hyphenated = name_lower.replace("-", "")
        if hyphenated in shadcn_purposes:
            return shadcn_purposes[hyphenated]
        
        # Fall back to general purpose analysis
        return self._infer_purpose_from_name(component_name)