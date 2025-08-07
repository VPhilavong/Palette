"""
Project Structure Detection for Vite + React Codebases
Analyzes filesystem and package.json to determine correct file paths.
"""

import os
import json
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class FrameworkType(Enum):
    """Detected framework types"""
    REACT_APP = "react_app"  # Vite + React
    UNKNOWN = "unknown"


class ProjectStructure(Enum):
    """Project directory structures"""
    REACT_SRC = "react_src"  # src/pages/[Page].tsx + src/components/
    REACT_ROOT = "react_root"  # components/ at root level


@dataclass
class ProjectInfo:
    """Information about detected project structure"""
    framework: FrameworkType
    structure: ProjectStructure
    routes_dir: str
    components_dir: str
    has_typescript: bool
    has_src_dir: bool
    

class IntentType(Enum):
    """Content intent types"""
    PAGE = "page"
    COMPONENT = "component"
    LAYOUT = "layout"
    API_ROUTE = "api"
    MIDDLEWARE = "middleware"


class ProjectStructureDetector:
    """Detects project structure and determines correct file paths"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self._project_info = None
        
    def detect_project_structure(self) -> ProjectInfo:
        """Analyze project and detect structure"""
        if self._project_info is None:
            self._project_info = self._analyze_project()
        return self._project_info
    
    def _analyze_project(self) -> ProjectInfo:
        """Perform comprehensive project analysis"""
        # 1. Check package.json for framework detection
        is_nextjs = self._is_nextjs_project()
        has_typescript = self._has_typescript()
        has_src = self._has_src_directory()
        
        # 2. Analyze directory structure
        structure = self._detect_directory_structure()
        
        # 3. Determine framework type
        framework = self._determine_framework_type(is_nextjs, structure)
        
        # 4. Map directories
        routes_dir, components_dir = self._map_directories(structure, has_src)
        
        return ProjectInfo(
            framework=framework,
            structure=structure,
            routes_dir=routes_dir,
            components_dir=components_dir,
            has_typescript=has_typescript,
            has_src_dir=has_src
        )
    
    def _is_nextjs_project(self) -> bool:
        """Check if this is a Next.js project"""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return False
            
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                return 'next' in deps
        except (json.JSONDecodeError, IOError):
            return False
    
    def _has_typescript(self) -> bool:
        """Check if project uses TypeScript"""
        indicators = [
            "tsconfig.json",
            "next.config.ts",
            "tailwind.config.ts"
        ]
        
        for indicator in indicators:
            if (self.project_path / indicator).exists():
                return True
                
        # Check package.json for TypeScript
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    return 'typescript' in deps or '@types/react' in deps
            except (json.JSONDecodeError, IOError):
                pass
                
        return False
    
    def _has_src_directory(self) -> bool:
        """Check if project uses src/ directory"""
        return (self.project_path / "src").is_dir()
    
    def _detect_directory_structure(self) -> ProjectStructure:
        """Detect the directory structure pattern"""
        # Simplified: Check for src directory
        if self._has_src_directory():
            return ProjectStructure.REACT_SRC
        else:
            return ProjectStructure.REACT_ROOT
    
    def _determine_framework_type(self, is_nextjs: bool, structure: ProjectStructure) -> FrameworkType:
        """Determine the specific framework type"""
        # Simplified: Always return REACT_APP for Vite projects
        return FrameworkType.REACT_APP
    
    def _map_directories(self, structure: ProjectStructure, has_src: bool) -> Tuple[str, str]:
        """Map structure to actual directory paths"""
        mapping = {
            ProjectStructure.REACT_SRC: ("src/pages", "src/components"),
            ProjectStructure.REACT_ROOT: ("pages", "components")
        }
        
        return mapping.get(structure, ("src/pages", "src/components"))
    
    def detect_intent(self, prompt: str) -> IntentType:
        """Detect what the user wants to create based on prompt"""
        prompt_lower = prompt.lower()
        
        # Page indicators (strongest signals first)
        page_patterns = [
            # Explicit page mentions
            r'\b\w+\s+page\b',  # "pricing page", "about page"
            r'\bpage\s+for\b',  # "page for pricing"
            r'\bcreate\s+a\s+page\b',  # "create a page"
            
            # Route-like patterns
            r'\b(home|landing|index)\b',
            r'\b(about|contact|pricing|dashboard|profile)\b(?!\s+component)',
            r'\b(login|signup|register|auth)\b(?!\s+component)',
            
            # Page-specific features
            r'\bwith\s+\d+\s+(plans?|options?|tiers?)\b',  # "with 3 plans"
            r'\bfull\s+page\b',
        ]
        
        # Component indicators
        component_patterns = [
            r'\b\w+\s+component\b',  # "pricing component", "hero component"
            r'\bcomponent\s+for\b',  # "component for navigation"
            r'\b(section|card|button|form|modal|navbar|header|footer)\b',
            r'\b(hero|banner|cta|testimonial)\b',
            r'\breusable\b',
        ]
        
        # Layout indicators  
        layout_patterns = [
            r'\b\w+\s+layout\b',  # "dashboard layout"
            r'\blayout\s+for\b',  # "layout for admin"
            r'\bmain\s+layout\b',
        ]
        
        # Check patterns in order of priority
        import re
        
        for pattern in page_patterns:
            if re.search(pattern, prompt_lower):
                return IntentType.PAGE
                
        for pattern in layout_patterns:
            if re.search(pattern, prompt_lower):
                return IntentType.LAYOUT
                
        for pattern in component_patterns:
            if re.search(pattern, prompt_lower):
                return IntentType.COMPONENT
        
        # Default heuristics based on common words
        if any(word in prompt_lower for word in ['page', 'route', 'screen']):
            return IntentType.PAGE
        elif any(word in prompt_lower for word in ['layout', 'template']):
            return IntentType.LAYOUT
        else:
            return IntentType.COMPONENT
    
    def generate_file_path(self, prompt: str, intent: Optional[IntentType] = None) -> str:
        """Generate the correct file path based on prompt and project structure"""
        project_info = self.detect_project_structure()
        
        if intent is None:
            intent = self.detect_intent(prompt)
        
        # Extract name from prompt
        name = self._extract_name_from_prompt(prompt, intent)
        
        # Generate path based on intent and project structure
        if intent == IntentType.PAGE:
            return self._generate_page_path(name, project_info)
        elif intent == IntentType.LAYOUT:
            return self._generate_layout_path(name, project_info)
        elif intent == IntentType.COMPONENT:
            return self._generate_component_path(name, project_info)
        else:
            return self._generate_component_path(name, project_info)
    
    def _extract_name_from_prompt(self, prompt: str, intent: IntentType) -> str:
        """Extract a meaningful name from the prompt"""
        prompt_lower = prompt.lower()
        
        # Common name patterns
        name_patterns = {
            'pricing': ['pricing', 'price', 'plan'],
            'about': ['about', 'about-us'],
            'contact': ['contact', 'contact-us'],
            'dashboard': ['dashboard', 'admin'],
            'profile': ['profile', 'user-profile'],
            'hero': ['hero'],
            'navigation': ['nav', 'navigation', 'navbar'],
            'footer': ['footer'],
            'header': ['header'],
            'card': ['card'],
            'button': ['button', 'btn'],
            'form': ['form'],
            'modal': ['modal', 'dialog'],
            'landing': ['landing', 'home', 'index'],
            'auth': ['auth', 'login', 'signin', 'signup', 'register'],
        }
        
        # Try to match known patterns
        for name, patterns in name_patterns.items():
            if any(pattern in prompt_lower for pattern in patterns):
                return name
        
        # Extract first meaningful word
        words = prompt.replace('-', ' ').replace('_', ' ').split()
        stop_words = {'a', 'an', 'the', 'with', 'and', 'or', 'for', 'create', 'make', 'build', 'generate'}
        
        for word in words:
            clean_word = word.lower().strip('.,!?;:')
            if len(clean_word) > 2 and clean_word not in stop_words:
                return clean_word
        
        # Fallback names based on intent
        fallback_names = {
            IntentType.PAGE: 'page',
            IntentType.COMPONENT: 'component', 
            IntentType.LAYOUT: 'layout'
        }
        
        return fallback_names.get(intent, 'component')
    
    def _generate_page_path(self, name: str, project_info: ProjectInfo) -> str:
        """Generate page file path"""
        ext = ".tsx" if project_info.has_typescript else ".jsx"
        
        # React App: src/pages/[Page].tsx
        page_name = name.capitalize() + "Page"
        return f"{project_info.routes_dir}/{page_name}{ext}"
    
    def _generate_layout_path(self, name: str, project_info: ProjectInfo) -> str:
        """Generate layout file path"""
        ext = ".tsx" if project_info.has_typescript else ".jsx"
        
        # For React apps, treat as component
        layout_name = name.capitalize() + "Layout"
        return f"{project_info.components_dir}/{layout_name}{ext}"
    
    def _generate_component_path(self, name: str, project_info: ProjectInfo) -> str:
        """Generate component file path"""
        ext = ".tsx" if project_info.has_typescript else ".jsx"
        
        # Component naming patterns
        component_patterns = {
            'hero': 'HeroSection',
            'nav': 'Navigation',
            'navigation': 'Navigation',
            'navbar': 'Navigation',
            'pricing': 'PricingSection',
            'about': 'AboutSection',
            'contact': 'ContactSection',
            'card': 'Card',
            'button': 'Button',
            'form': 'Form',
            'modal': 'Modal',
            'header': 'Header',
            'footer': 'Footer',
        }
        
        component_name = component_patterns.get(name, name.capitalize() + "Component")
        return f"{project_info.components_dir}/{component_name}{ext}"