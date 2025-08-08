"""
Smart Prompt Suggestions System - Context-aware prompt recommendations.

Analyzes current file/directory context to suggest relevant component prompts
and auto-complete user intentions based on project patterns.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

from ..intelligence.configuration_hub import ConfigurationIntelligenceHub
from ..intelligence.pattern_extractor import ProjectPatternExtractor


@dataclass
class PromptSuggestion:
    """A contextual prompt suggestion."""
    prompt: str
    category: str
    confidence: float
    reasoning: str
    related_files: List[str]
    complexity: str  # 'simple', 'medium', 'complex'


class SmartSuggestionEngine:
    """Engine for generating context-aware prompt suggestions."""
    
    def __init__(self):
        self.config_hub = ConfigurationIntelligenceHub()
        self.pattern_extractor = ProjectPatternExtractor()
        
        # Component relationship patterns
        self.component_relationships = {
            # User-related components
            'user': ['profile', 'avatar', 'card', 'list', 'settings', 'dashboard'],
            'profile': ['avatar', 'card', 'editor', 'settings', 'summary'],
            'avatar': ['uploader', 'editor', 'gallery', 'placeholder'],
            
            # Navigation components  
            'nav': ['menu', 'breadcrumb', 'sidebar', 'header', 'footer'],
            'menu': ['item', 'dropdown', 'mobile', 'context'],
            'sidebar': ['toggle', 'navigation', 'collapsible', 'menu'],
            
            # Form components
            'form': ['field', 'validation', 'wizard', 'builder', 'input'],
            'input': ['field', 'validation', 'autocomplete', 'picker'],
            'field': ['error', 'label', 'wrapper', 'group'],
            
            # Data display
            'table': ['row', 'cell', 'header', 'pagination', 'filter'],
            'card': ['header', 'body', 'footer', 'grid', 'list'],
            'list': ['item', 'group', 'infinite', 'virtualized'],
            
            # Layout components  
            'layout': ['container', 'grid', 'flex', 'stack', 'section'],
            'header': ['navigation', 'logo', 'search', 'actions'],
            'footer': ['links', 'copyright', 'social', 'newsletter'],
            
            # Interactive components
            'modal': ['dialog', 'overlay', 'drawer', 'popup'],
            'dropdown': ['menu', 'select', 'multiselect', 'trigger'],
            'button': ['group', 'toggle', 'split', 'floating'],
            
            # Dashboard components
            'dashboard': ['widget', 'chart', 'metric', 'analytics', 'overview'],
            'chart': ['bar', 'line', 'pie', 'area', 'scatter'],
            'metric': ['card', 'widget', 'counter', 'gauge']
        }
    
    def get_contextual_suggestions(self, current_path: str = ".") -> List[PromptSuggestion]:
        """Get context-aware prompt suggestions based on current location."""
        
        suggestions = []
        
        # Analyze current context
        context = self._analyze_current_context(current_path)
        
        # Get suggestions based on directory structure
        directory_suggestions = self._get_directory_based_suggestions(context)
        suggestions.extend(directory_suggestions)
        
        # Get suggestions based on existing components
        component_suggestions = self._get_component_based_suggestions(context)
        suggestions.extend(component_suggestions)
        
        # Get suggestions based on project type
        project_suggestions = self._get_project_type_suggestions(context)
        suggestions.extend(project_suggestions)
        
        # Get suggestions based on missing patterns
        gap_suggestions = self._get_gap_based_suggestions(context)
        suggestions.extend(gap_suggestions)
        
        # Sort by confidence and remove duplicates
        unique_suggestions = self._deduplicate_suggestions(suggestions)
        return sorted(unique_suggestions, key=lambda s: s.confidence, reverse=True)[:10]
    
    def get_prompt_completions(self, partial_prompt: str, current_path: str = ".") -> List[PromptSuggestion]:
        """Get auto-completions for partial prompts based on context."""
        
        if len(partial_prompt.strip()) < 2:
            return []
        
        context = self._analyze_current_context(current_path)
        completions = []
        
        # Analyze partial prompt
        prompt_lower = partial_prompt.lower()
        words = prompt_lower.split()
        last_word = words[-1] if words else ""
        
        # Component name completion
        if len(words) <= 2:  # Still building component name
            completions.extend(self._get_component_completions(prompt_lower, context))
        
        # Feature completion
        completions.extend(self._get_feature_completions(prompt_lower, context))
        
        # Framework-specific completions
        completions.extend(self._get_framework_completions(prompt_lower, context))
        
        return sorted(completions, key=lambda s: s.confidence, reverse=True)[:5]
    
    def _analyze_current_context(self, current_path: str) -> Dict:
        """Analyze the current directory and file context."""
        
        context = {
            'current_dir': Path(current_path).resolve(),
            'directory_type': None,
            'existing_components': [],
            'component_patterns': [],
            'project_config': None,
            'nearby_files': [],
            'parent_context': []
        }
        
        try:
            # Get project configuration
            context['project_config'] = self.config_hub.analyze_configuration(current_path)
            
            # Analyze directory structure
            context['directory_type'] = self._determine_directory_type(context['current_dir'])
            
            # Find existing components
            context['existing_components'] = self._find_existing_components(context['current_dir'])
            
            # Get nearby files for context
            context['nearby_files'] = self._get_nearby_files(context['current_dir'])
            
            # Get parent directory context
            context['parent_context'] = self._get_parent_context(context['current_dir'])
            
        except Exception as e:
            print(f"Context analysis error: {e}")
        
        return context
    
    def _determine_directory_type(self, current_dir: Path) -> Optional[str]:
        """Determine what type of directory we're in based on path and contents."""
        
        dir_name = current_dir.name.lower()
        dir_path = str(current_dir).lower()
        
        # Check directory name patterns
        if 'component' in dir_name:
            if 'ui' in dir_name or 'common' in dir_name:
                return 'ui_components'
            return 'components'
        
        if dir_name in ['pages', 'views', 'routes']:
            return 'pages'
        
        if dir_name in ['layouts', 'templates']:
            return 'layouts'
        
        if 'dashboard' in dir_path:
            return 'dashboard'
        
        if 'admin' in dir_path:
            return 'admin'
        
        if 'auth' in dir_path or 'login' in dir_path:
            return 'auth'
        
        # Check for common UI patterns
        ui_indicators = ['ui', 'design', 'theme', 'style']
        if any(indicator in dir_path for indicator in ui_indicators):
            return 'ui_system'
        
        return None
    
    def _find_existing_components(self, current_dir: Path) -> List[Dict]:
        """Find existing component files in current and nearby directories."""
        
        components = []
        
        # Search current directory and subdirectories
        for ext in ['.tsx', '.ts', '.jsx', '.js', '.vue']:
            pattern = f"**/*{ext}"
            for file_path in current_dir.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    component_info = self._analyze_component_file(file_path)
                    if component_info:
                        components.append(component_info)
        
        return components
    
    def _analyze_component_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a component file to extract information."""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract component name from filename
            component_name = file_path.stem
            if component_name.lower() in ['index', 'main']:
                component_name = file_path.parent.name
            
            # Extract component type from content
            component_type = self._determine_component_type(content, component_name)
            
            return {
                'name': component_name,
                'path': str(file_path),
                'type': component_type,
                'has_props': 'interface' in content or 'Props' in content,
                'has_state': 'useState' in content or 'state' in content,
                'is_page': 'page' in file_path.name.lower() or file_path.parent.name.lower() == 'pages'
            }
            
        except Exception:
            return None
    
    def _determine_component_type(self, content: str, component_name: str) -> str:
        """Determine component type from content and name."""
        
        name_lower = component_name.lower()
        content_lower = content.lower()
        
        # UI component types
        if any(ui_type in name_lower for ui_type in ['button', 'input', 'field', 'form']):
            return 'form'
        
        if any(ui_type in name_lower for ui_type in ['card', 'panel', 'box']):
            return 'container'
        
        if any(ui_type in name_lower for ui_type in ['nav', 'menu', 'header', 'footer']):
            return 'navigation'
        
        if any(ui_type in name_lower for ui_type in ['modal', 'dialog', 'popup']):
            return 'overlay'
        
        if any(ui_type in name_lower for ui_type in ['table', 'list', 'grid']):
            return 'data_display'
        
        # Check content patterns
        if 'userouter' in content_lower or 'route' in content_lower:
            return 'page'
        
        if 'usestate' in content_lower and 'useeffect' in content_lower:
            return 'stateful'
        
        return 'component'
    
    def _get_nearby_files(self, current_dir: Path) -> List[str]:
        """Get nearby files that might provide context."""
        
        nearby_files = []
        
        # Check current directory
        for file_path in current_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ['.tsx', '.ts', '.jsx', '.js', '.vue']:
                nearby_files.append(file_path.name)
        
        return nearby_files[:10]  # Limit to avoid noise
    
    def _get_parent_context(self, current_dir: Path) -> List[str]:
        """Get context from parent directories."""
        
        parent_context = []
        parent = current_dir.parent
        
        # Go up to 3 levels to understand context
        for _ in range(3):
            if parent and parent.name:
                parent_context.append(parent.name.lower())
                parent = parent.parent
            else:
                break
        
        return parent_context
    
    def _get_directory_based_suggestions(self, context: Dict) -> List[PromptSuggestion]:
        """Get suggestions based on current directory type."""
        
        suggestions = []
        directory_type = context.get('directory_type')
        
        if directory_type == 'ui_components':
            suggestions.extend([
                PromptSuggestion(
                    prompt="Create a reusable Button component with variants",
                    category="UI Component",
                    confidence=0.9,
                    reasoning="Common UI component in components/ui directory",
                    related_files=[],
                    complexity="simple"
                ),
                PromptSuggestion(
                    prompt="Create an Input field component with validation",
                    category="Form Component", 
                    confidence=0.85,
                    reasoning="Essential form component for UI library",
                    related_files=[],
                    complexity="medium"
                )
            ])
        
        elif directory_type == 'dashboard':
            suggestions.extend([
                PromptSuggestion(
                    prompt="Create a metric card component for dashboard",
                    category="Dashboard Widget",
                    confidence=0.9,
                    reasoning="In dashboard directory, metric cards are essential",
                    related_files=[],
                    complexity="simple"
                ),
                PromptSuggestion(
                    prompt="Create a chart component with multiple data visualization types",
                    category="Data Visualization",
                    confidence=0.8,
                    reasoning="Dashboard context suggests need for data visualization",
                    related_files=[],
                    complexity="complex"
                )
            ])
        
        elif directory_type == 'auth':
            suggestions.extend([
                PromptSuggestion(
                    prompt="Create a login form with email and password validation",
                    category="Authentication",
                    confidence=0.95,
                    reasoning="In auth directory, login forms are primary need",
                    related_files=[],
                    complexity="medium"
                ),
                PromptSuggestion(
                    prompt="Create a user registration form with form validation",
                    category="Authentication",
                    confidence=0.9,
                    reasoning="Auth context suggests user registration functionality",
                    related_files=[],
                    complexity="medium"
                )
            ])
        
        return suggestions
    
    def _get_component_based_suggestions(self, context: Dict) -> List[PromptSuggestion]:
        """Get suggestions based on existing components."""
        
        suggestions = []
        existing_components = context.get('existing_components', [])
        
        # Find component patterns and suggest related components
        component_names = [comp['name'].lower() for comp in existing_components]
        
        for component_name in component_names:
            # Find base component name (remove common suffixes)
            base_name = re.sub(r'(component|card|item|list|form|page)$', '', component_name).strip()
            
            if base_name in self.component_relationships:
                related_components = self.component_relationships[base_name]
                
                for related in related_components:
                    if related not in component_names:  # Don't suggest existing components
                        suggestions.append(PromptSuggestion(
                            prompt=f"Create a {base_name} {related} component",
                            category="Related Component",
                            confidence=0.75,
                            reasoning=f"Related to existing {component_name} component",
                            related_files=[comp['path'] for comp in existing_components if comp['name'].lower() == component_name],
                            complexity="medium"
                        ))
        
        return suggestions
    
    def _get_project_type_suggestions(self, context: Dict) -> List[PromptSuggestion]:
        """Get suggestions based on project type and configuration."""
        
        suggestions = []
        project_config = context.get('project_config')
        
        if not project_config:
            return suggestions
        
        # Framework-specific suggestions
        if project_config.framework and project_config.framework.value == "NEXT_JS":
            suggestions.append(PromptSuggestion(
                prompt="Create a Next.js page component with SSR data fetching",
                category="Next.js Specific",
                confidence=0.8,
                reasoning="Next.js project detected, page components are common pattern",
                related_files=[],
                complexity="medium"
            ))
        
        # Styling system specific suggestions
        if project_config.styling_system:
            if project_config.styling_system.value == "CHAKRA_UI":
                suggestions.append(PromptSuggestion(
                    prompt="Create a responsive layout using Chakra UI components",
                    category="Chakra UI Layout",
                    confidence=0.8,
                    reasoning="Chakra UI detected, layout components are foundational",
                    related_files=[],
                    complexity="medium"
                ))
            elif project_config.styling_system.value == "TAILWIND":
                suggestions.append(PromptSuggestion(
                    prompt="Create a responsive component using Tailwind utility classes",
                    category="Tailwind Component", 
                    confidence=0.8,
                    reasoning="Tailwind CSS detected, utility-first approach recommended",
                    related_files=[],
                    complexity="simple"
                ))
        
        return suggestions
    
    def _get_gap_based_suggestions(self, context: Dict) -> List[PromptSuggestion]:
        """Get suggestions based on missing common patterns."""
        
        suggestions = []
        existing_components = context.get('existing_components', [])
        component_names = set(comp['name'].lower() for comp in existing_components)
        
        # Common components that every project needs
        essential_components = {
            'button': ("Essential interactive component", "simple"),
            'input': ("Basic form input component", "simple"),
            'card': ("Versatile container component", "simple"),
            'modal': ("Overlay component for dialogs", "medium"),
            'header': ("Navigation and branding component", "medium"),
            'footer': ("Bottom page content component", "simple"),
            'loading': ("Loading state component", "simple"),
            'error': ("Error display component", "simple")
        }
        
        for component, (description, complexity) in essential_components.items():
            if component not in component_names:
                suggestions.append(PromptSuggestion(
                    prompt=f"Create a {component} component",
                    category="Essential Component",
                    confidence=0.6,
                    reasoning=f"{description} - missing from project",
                    related_files=[],
                    complexity=complexity
                ))
        
        return suggestions
    
    def _get_component_completions(self, partial_prompt: str, context: Dict) -> List[PromptSuggestion]:
        """Get component name completions."""
        
        completions = []
        words = partial_prompt.split()
        
        if not words:
            return completions
        
        last_word = words[-1]
        
        # Component type completions
        component_types = ['button', 'input', 'card', 'modal', 'table', 'form', 'nav', 'header', 'footer']
        
        for comp_type in component_types:
            if comp_type.startswith(last_word) and len(last_word) > 1:
                completed_prompt = ' '.join(words[:-1] + [comp_type, 'component'])
                completions.append(PromptSuggestion(
                    prompt=completed_prompt,
                    category="Component Completion",
                    confidence=0.8,
                    reasoning=f"Auto-completing '{last_word}' to '{comp_type}'",
                    related_files=[],
                    complexity="simple"
                ))
        
        return completions
    
    def _get_feature_completions(self, partial_prompt: str, context: Dict) -> List[PromptSuggestion]:
        """Get feature-based completions."""
        
        completions = []
        
        # Feature keywords and their completions
        feature_completions = {
            'with': ['validation', 'animation', 'loading states', 'error handling', 'responsive design'],
            'responsive': ['design', 'layout', 'grid', 'navigation'],
            'dark': ['mode support', 'theme toggle', 'mode switcher']
        }
        
        for trigger, options in feature_completions.items():
            if trigger in partial_prompt:
                for option in options:
                    if option not in partial_prompt:
                        completed_prompt = f"{partial_prompt} {option}"
                        completions.append(PromptSuggestion(
                            prompt=completed_prompt,
                            category="Feature Enhancement", 
                            confidence=0.7,
                            reasoning=f"Enhanced with {option}",
                            related_files=[],
                            complexity="medium"
                        ))
        
        return completions
    
    def _get_framework_completions(self, partial_prompt: str, context: Dict) -> List[PromptSuggestion]:
        """Get framework-specific completions."""
        
        completions = []
        project_config = context.get('project_config')
        
        if not project_config:
            return completions
        
        # Framework-specific enhancements
        if project_config.framework and project_config.framework.value == "NEXT_JS":
            if 'page' in partial_prompt and 'ssr' not in partial_prompt:
                completions.append(PromptSuggestion(
                    prompt=f"{partial_prompt} with SSR data fetching",
                    category="Next.js Enhancement",
                    confidence=0.8,
                    reasoning="Next.js page with server-side rendering",
                    related_files=[],
                    complexity="medium"
                ))
        
        return completions
    
    def _deduplicate_suggestions(self, suggestions: List[PromptSuggestion]) -> List[PromptSuggestion]:
        """Remove duplicate suggestions while keeping highest confidence ones."""
        
        seen_prompts = set()
        unique_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.prompt not in seen_prompts:
                seen_prompts.add(suggestion.prompt)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions