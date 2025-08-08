"""
Configuration-Aware Context Manager.
Enhances context management with project configuration intelligence,
optimizing context prioritization and token utilization based on detected frameworks and styling systems.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set

from .context_manager import TokenAwareContextManager, ContextType, ContextChunk, ContextPriority
from ..intelligence.configuration_hub import ProjectConfiguration, Framework
from ..intelligence.styling_analyzer import StylingSystem
from ..errors.decorators import handle_errors


class ConfigurationContextType(Enum):
    """Extended context types for configuration-aware management."""
    FRAMEWORK_EXAMPLES = "framework_examples"
    STYLING_GUIDELINES = "styling_guidelines"
    COMPONENT_LIBRARY_DOCS = "component_library_docs"
    PATTERN_EXAMPLES = "pattern_examples"
    VALIDATION_RULES = "validation_rules"
    COMPATIBILITY_NOTES = "compatibility_notes"
    MIGRATION_HINTS = "migration_hints"


@dataclass
class ConfigurationContext:
    """Enhanced context with configuration-specific information."""
    base_context: Dict[str, Any]
    configuration: ProjectConfiguration
    framework_specific_context: Dict[str, Any] = field(default_factory=dict)
    styling_specific_context: Dict[str, Any] = field(default_factory=dict)
    priority_weights: Dict[str, float] = field(default_factory=dict)
    excluded_patterns: List[str] = field(default_factory=list)


class ConfigurationAwareContextManager(TokenAwareContextManager):
    """
    Enhanced context manager that adapts prioritization based on project configuration.
    
    This addresses the context optimization issues by:
    1. Adjusting priorities based on detected framework and styling system
    2. Filtering irrelevant context for specific configurations
    3. Adding configuration-specific examples and guidelines
    4. Optimizing token usage for different project types
    """
    
    def __init__(self, max_tokens: int = 4000):
        super().__init__(max_tokens=max_tokens)
        self._initialize_configuration_priorities()
        self._initialize_context_filters()
    
    def _initialize_configuration_priorities(self):
        """Initialize priority weights for different configurations."""
        
        # Framework-specific priorities
        self.framework_priorities = {
            Framework.NEXT_JS: {
                ContextType.FRAMEWORK_PATTERNS: 0.9,
                ContextType.COMPONENT_EXAMPLES: 0.7,
                ContextType.DESIGN_TOKENS: 0.6,
                ContextType.PROJECT_STRUCTURE: 0.8,
                ConfigurationContextType.FRAMEWORK_EXAMPLES: 0.9,
                ConfigurationContextType.VALIDATION_RULES: 0.7
            },
            Framework.REACT: {
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ContextType.COMPONENT_EXAMPLES: 0.8,
                ContextType.DESIGN_TOKENS: 0.6,
                ContextType.PROJECT_STRUCTURE: 0.6,
                ConfigurationContextType.COMPONENT_LIBRARY_DOCS: 0.8
            },
            Framework.VITE_REACT: {
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ContextType.COMPONENT_EXAMPLES: 0.8,
                ContextType.DESIGN_TOKENS: 0.7,
                ConfigurationContextType.FRAMEWORK_EXAMPLES: 0.8
            }
        }
        
        # Styling system specific priorities
        self.styling_priorities = {
            StylingSystem.CHAKRA_UI: {
                ContextType.COMPONENT_EXAMPLES: 0.95,  # Highest priority
                ContextType.DESIGN_TOKENS: 0.4,        # Lower priority
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ConfigurationContextType.STYLING_GUIDELINES: 0.9,
                ConfigurationContextType.VALIDATION_RULES: 0.8,
                ConfigurationContextType.COMPATIBILITY_NOTES: 0.7
            },
            StylingSystem.TAILWIND: {
                ContextType.COMPONENT_EXAMPLES: 0.6,
                ContextType.DESIGN_TOKENS: 0.9,        # Highest priority
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ConfigurationContextType.STYLING_GUIDELINES: 0.8,
                ConfigurationContextType.PATTERN_EXAMPLES: 0.7
            },
            StylingSystem.MATERIAL_UI: {
                ContextType.COMPONENT_EXAMPLES: 0.9,
                ContextType.DESIGN_TOKENS: 0.5,
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ConfigurationContextType.COMPONENT_LIBRARY_DOCS: 0.9,
                ConfigurationContextType.STYLING_GUIDELINES: 0.8
            },
            StylingSystem.SHADCN_UI: {
                ContextType.COMPONENT_EXAMPLES: 0.85,
                ContextType.DESIGN_TOKENS: 0.8,
                ContextType.FRAMEWORK_PATTERNS: 0.8,
                ConfigurationContextType.STYLING_GUIDELINES: 0.9,
                ConfigurationContextType.PATTERN_EXAMPLES: 0.8
            }
        }
    
    def _initialize_context_filters(self):
        """Initialize context filters for different configurations."""
        
        # Patterns to exclude for specific styling systems
        self.styling_filters = {
            StylingSystem.CHAKRA_UI: [
                # Exclude Tailwind-related content when using Chakra UI
                "tailwind", "bg-", "text-", "p-", "m-", "w-", "h-",
                "className.*(?:bg-|text-|p-|m-)",
                "utility.*class", "atomic.*css",
                "styled-components", "emotion", "css-in-js"
            ],
            StylingSystem.TAILWIND: [
                # Exclude component library content when using Tailwind
                "@chakra-ui", "@mui", "@mantine", "antd",
                "component.*prop", "theme.*prop", "variant.*prop"
            ],
            StylingSystem.MATERIAL_UI: [
                # Exclude other component libraries
                "@chakra-ui", "@mantine", "antd", "tailwind",
                "bg-", "text-", "p-", "m-"
            ]
        }
        
        # Framework-specific filters
        self.framework_filters = {
            Framework.NEXT_JS: [
                # Include Next.js specific patterns, exclude others
                "create-react-app", "vite.*config", "webpack.*config"
            ],
            Framework.VITE_REACT: [
                # Exclude Next.js and CRA specific content
                "next.*config", "pages.*router", "getServerSideProps",
                "getStaticProps", "create-react-app"
            ],
            Framework.CREATE_REACT_APP: [
                # Exclude advanced framework features
                "next.*config", "vite.*config", "server.*side"
            ]
        }
    
    @handle_errors(reraise=True)
    def optimize_context_with_configuration(
        self,
        user_request: str,
        project_context: Dict[str, Any],
        configuration: ProjectConfiguration,
        system_prompt_base: str = "",
        user_prompt_base: str = ""
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Optimize context with configuration awareness.
        
        This is the main method that enhances context management by:
        1. Adjusting priorities based on project configuration
        2. Filtering irrelevant context
        3. Adding configuration-specific enhancements
        4. Optimizing token utilization
        
        Args:
            user_request: User's component request
            project_context: Base project context
            configuration: Project configuration from ConfigurationIntelligenceHub
            system_prompt_base: Base system prompt
            user_prompt_base: Base user prompt
            
        Returns:
            Tuple of (optimized_system_prompt, optimized_user_prompt, optimization_stats)
        """
        
        print(f"🎯 Optimizing context for {configuration.framework.value} + {configuration.styling_system.value}")
        
        # Create configuration-aware context
        config_context = self._create_configuration_context(
            project_context, configuration
        )
        
        # Get configuration-specific priority weights
        priority_weights = self._get_configuration_priority_weights(configuration)
        
        # Filter context based on configuration
        filtered_context = self._filter_context_by_configuration(
            config_context, configuration
        )
        
        # Add configuration-specific enhancements
        enhanced_context = self._add_configuration_enhancements(
            filtered_context, configuration, user_request
        )
        
        # Create context chunks with configuration priorities
        context_chunks = self._create_configuration_aware_chunks(
            enhanced_context, priority_weights
        )
        
        # Optimize within token budget
        optimized_system, optimized_user, optimization_stats = self._optimize_with_configuration_priorities(
            user_request, context_chunks, system_prompt_base, user_prompt_base, priority_weights
        )
        
        # Add configuration-specific optimization stats
        optimization_stats.update({
            'configuration': {
                'framework': configuration.framework.value,
                'styling_system': configuration.styling_system.value,
                'confidence': configuration.confidence_score,
                'strategy': configuration.generation_strategy
            },
            'context_filtering': {
                'filters_applied': len(self._get_active_filters(configuration)),
                'excluded_patterns': len(config_context.excluded_patterns)
            },
            'priority_adjustments': priority_weights
        })
        
        print(f"📊 Context optimized: {optimization_stats['token_budget']['utilization']:.1%} utilization")
        
        return optimized_system, optimized_user, optimization_stats
    
    def _create_configuration_context(
        self, 
        base_context: Dict[str, Any], 
        configuration: ProjectConfiguration
    ) -> ConfigurationContext:
        """Create configuration-aware context structure."""
        
        # Extract framework-specific context
        framework_context = self._extract_framework_context(base_context, configuration.framework)
        
        # Extract styling-specific context
        styling_context = self._extract_styling_context(base_context, configuration.styling_system)
        
        # Get priority weights for this configuration
        priority_weights = self._get_configuration_priority_weights(configuration)
        
        # Get exclusion patterns
        excluded_patterns = self._get_active_filters(configuration)
        
        return ConfigurationContext(
            base_context=base_context,
            configuration=configuration,
            framework_specific_context=framework_context,
            styling_specific_context=styling_context,
            priority_weights=priority_weights,
            excluded_patterns=excluded_patterns
        )
    
    def _extract_framework_context(
        self, 
        context: Dict[str, Any], 
        framework: Framework
    ) -> Dict[str, Any]:
        """Extract framework-specific context elements."""
        
        framework_context = {}
        
        if framework == Framework.NEXT_JS:
            framework_context.update({
                'routing': context.get('next_routing_patterns', []),
                'ssr_patterns': context.get('ssr_examples', []),
                'app_router': context.get('app_router_patterns', []),
                'api_routes': context.get('api_patterns', []),
                'image_optimization': context.get('next_image_examples', [])
            })
        
        elif framework == Framework.REACT:
            framework_context.update({
                'hooks': context.get('react_hooks_examples', []),
                'context_api': context.get('context_patterns', []),
                'state_management': context.get('state_examples', []),
                'lifecycle': context.get('lifecycle_patterns', [])
            })
        
        elif framework == Framework.VITE_REACT:
            framework_context.update({
                'vite_config': context.get('vite_patterns', []),
                'fast_refresh': context.get('hmr_examples', []),
                'build_optimization': context.get('vite_build_patterns', [])
            })
        
        return framework_context
    
    def _extract_styling_context(
        self, 
        context: Dict[str, Any], 
        styling_system: StylingSystem
    ) -> Dict[str, Any]:
        """Extract styling system-specific context elements."""
        
        styling_context = {}
        
        if styling_system == StylingSystem.CHAKRA_UI:
            styling_context.update({
                'component_props': context.get('chakra_props_examples', []),
                'theme_usage': context.get('chakra_theme_patterns', []),
                'responsive_props': context.get('chakra_responsive_examples', []),
                'color_mode': context.get('chakra_color_mode_examples', []),
                'composition': context.get('chakra_composition_patterns', [])
            })
        
        elif styling_system == StylingSystem.TAILWIND:
            styling_context.update({
                'utility_classes': context.get('tailwind_utility_examples', []),
                'responsive_design': context.get('tailwind_responsive_patterns', []),
                'dark_mode': context.get('tailwind_dark_mode_examples', []),
                'custom_utilities': context.get('tailwind_custom_patterns', [])
            })
        
        elif styling_system == StylingSystem.MATERIAL_UI:
            styling_context.update({
                'mui_components': context.get('mui_component_examples', []),
                'theme_customization': context.get('mui_theme_patterns', []),
                'styling_api': context.get('mui_styling_examples', [])
            })
        
        return styling_context
    
    def _get_configuration_priority_weights(self, configuration: ProjectConfiguration) -> Dict[str, float]:
        """Get priority weights for the specific configuration."""
        
        # Start with base priorities
        priorities = {
            ContextType.USER_REQUEST.value: 1.0,
            ContextType.FRAMEWORK_PATTERNS.value: 0.8,
            ContextType.COMPONENT_EXAMPLES.value: 0.7,
            ContextType.DESIGN_TOKENS.value: 0.6,
            ContextType.PROJECT_STRUCTURE.value: 0.5
        }
        
        # Apply framework-specific priorities
        framework_priorities = self.framework_priorities.get(configuration.framework, {})
        for context_type, weight in framework_priorities.items():
            if hasattr(context_type, 'value'):
                priorities[context_type.value] = weight
            else:
                priorities[str(context_type)] = weight
        
        # Apply styling system-specific priorities
        styling_priorities = self.styling_priorities.get(configuration.styling_system, {})
        for context_type, weight in styling_priorities.items():
            if hasattr(context_type, 'value'):
                priorities[context_type.value] = weight
            else:
                priorities[str(context_type)] = weight
        
        # Boost priorities for high-confidence configurations
        if configuration.confidence_score > 0.8:
            for key in priorities:
                if key in ['framework_patterns', 'component_examples', 'styling_guidelines']:
                    priorities[key] *= 1.1
        
        return priorities
    
    def _filter_context_by_configuration(
        self, 
        config_context: ConfigurationContext, 
        configuration: ProjectConfiguration
    ) -> ConfigurationContext:
        """Filter context based on configuration to remove irrelevant content."""
        
        excluded_patterns = config_context.excluded_patterns
        
        # Filter base context
        filtered_base = self._apply_content_filters(
            config_context.base_context, excluded_patterns
        )
        
        # Filter framework-specific context
        filtered_framework = self._apply_content_filters(
            config_context.framework_specific_context, excluded_patterns
        )
        
        # Filter styling-specific context  
        filtered_styling = self._apply_content_filters(
            config_context.styling_specific_context, excluded_patterns
        )
        
        return ConfigurationContext(
            base_context=filtered_base,
            configuration=configuration,
            framework_specific_context=filtered_framework,
            styling_specific_context=filtered_styling,
            priority_weights=config_context.priority_weights,
            excluded_patterns=excluded_patterns
        )
    
    def _apply_content_filters(
        self, 
        content: Dict[str, Any], 
        excluded_patterns: List[str]
    ) -> Dict[str, Any]:
        """Apply content filters to remove irrelevant information while preserving relevant content."""
        
        if not excluded_patterns:
            return content
        
        filtered_content = {}
        
        for key, value in content.items():
            # Never filter out core content keys
            core_keys = ['existing_components', 'styling_patterns', 'framework_patterns', 'design_tokens']
            if any(core_key in key.lower() for core_key in core_keys):
                filtered_content[key] = value
                continue
            
            # For keys containing our styling system name, keep them regardless of other patterns
            if 'chakra' in key.lower():
                filtered_content[key] = value
                continue
            
            # Skip if key matches excluded patterns (but not for core keys)
            if any(pattern.lower() in key.lower() for pattern in excluded_patterns):
                continue
            
            # Filter string content
            if isinstance(value, str):
                # Keep content that mentions our styling system
                if 'chakra' in value.lower():
                    filtered_content[key] = value
                    continue
                    
                should_exclude = any(pattern.lower() in value.lower() for pattern in excluded_patterns)
                if not should_exclude:
                    filtered_content[key] = value
            
            # Filter list content
            elif isinstance(value, list):
                filtered_list = []
                for item in value:
                    if isinstance(item, str):
                        # Keep items that mention our styling system
                        if 'chakra' in item.lower():
                            filtered_list.append(item)
                            continue
                            
                        should_exclude = any(pattern.lower() in item.lower() for pattern in excluded_patterns)
                        if not should_exclude:
                            filtered_list.append(item)
                    else:
                        filtered_list.append(item)
                
                # Always include the list if it has any content
                if filtered_list or isinstance(value, list):
                    filtered_content[key] = filtered_list
            
            # Keep other types as-is
            else:
                filtered_content[key] = value
        
        return filtered_content
    
    def _get_active_filters(self, configuration: ProjectConfiguration) -> List[str]:
        """Get active content filters for the configuration."""
        
        filters = []
        
        # Add styling system filters
        styling_filters = self.styling_filters.get(configuration.styling_system, [])
        filters.extend(styling_filters)
        
        # Add framework filters
        framework_filters = self.framework_filters.get(configuration.framework, [])
        filters.extend(framework_filters)
        
        return filters
    
    def _add_configuration_enhancements(
        self,
        config_context: ConfigurationContext,
        configuration: ProjectConfiguration,
        user_request: str
    ) -> ConfigurationContext:
        """Add configuration-specific enhancements to context."""
        
        enhanced_base = config_context.base_context.copy()
        
        # Add framework-specific guidelines
        framework_guidelines = self._get_framework_guidelines(configuration.framework)
        enhanced_base['framework_guidelines'] = framework_guidelines
        
        # Add styling system guidelines
        styling_guidelines = self._get_styling_guidelines(configuration.styling_system)
        enhanced_base['styling_guidelines'] = styling_guidelines
        
        # Add validation rules
        validation_rules = self._get_validation_rules(configuration)
        enhanced_base['validation_rules'] = validation_rules
        
        # Add compatibility notes if there are issues
        if configuration.compatibility_issues:
            enhanced_base['compatibility_warnings'] = configuration.compatibility_issues
        
        # Add pattern-specific examples based on user request
        pattern_examples = self._get_pattern_examples(configuration, user_request)
        enhanced_base['pattern_examples'] = pattern_examples
        
        return ConfigurationContext(
            base_context=enhanced_base,
            configuration=configuration,
            framework_specific_context=config_context.framework_specific_context,
            styling_specific_context=config_context.styling_specific_context,
            priority_weights=config_context.priority_weights,
            excluded_patterns=config_context.excluded_patterns
        )
    
    def _get_framework_guidelines(self, framework: Framework) -> List[str]:
        """Get framework-specific guidelines."""
        
        guidelines = {
            Framework.NEXT_JS: [
                'Use "use client" directive for client-side components',
                'Prefer App Router patterns over Pages Router when possible',
                'Use next/image for optimized image loading',
                'Implement proper SEO with next/head or metadata API',
                'Follow Next.js naming conventions for routes and files'
            ],
            Framework.REACT: [
                'Use functional components with hooks',
                'Implement proper prop types or TypeScript interfaces',
                'Follow React naming conventions (PascalCase for components)',
                'Use React.memo for performance optimization when needed',
                'Handle side effects properly with useEffect'
            ],
            Framework.VITE_REACT: [
                'Leverage Vite\'s fast refresh capabilities',
                'Use ES modules and modern JavaScript features',
                'Optimize bundle splitting with dynamic imports',
                'Configure environment variables with VITE_ prefix'
            ]
        }
        
        return guidelines.get(framework, [])
    
    def _get_styling_guidelines(self, styling_system: StylingSystem) -> List[str]:
        """Get styling system-specific guidelines."""
        
        guidelines = {
            StylingSystem.CHAKRA_UI: [
                'NEVER use className with CSS utility classes',
                'Use Chakra UI component props for all styling',
                'Leverage theme-aware props (colorScheme, variant, size)',
                'Use Chakra\'s responsive prop syntax',
                'Import components from @chakra-ui/react',
                'Use Chakra\'s spacing and color systems'
            ],
            StylingSystem.TAILWIND: [
                'Use utility-first approach with Tailwind classes',
                'Follow mobile-first responsive design principles',
                'Use Tailwind\'s design tokens and spacing scale',
                'Leverage pseudo-class variants (hover:, focus:, etc.)',
                'Use @apply sparingly, prefer utilities'
            ],
            StylingSystem.MATERIAL_UI: [
                'Use Material-UI components and theme system',
                'Leverage sx prop for styling when needed',
                'Follow Material Design principles',
                'Use theme breakpoints for responsive design',
                'Import from @mui/material'
            ]
        }
        
        return guidelines.get(styling_system, [])
    
    def _get_validation_rules(self, configuration: ProjectConfiguration) -> List[str]:
        """Get validation rules for the configuration."""
        
        rules = []
        
        # Framework-specific validation rules
        if configuration.framework == Framework.NEXT_JS:
            rules.extend([
                'Components in app directory must be Server Components by default',
                'Client components must use "use client" directive',
                'Pages must export default component'
            ])
        
        # Styling system validation rules
        if configuration.styling_system == StylingSystem.CHAKRA_UI:
            rules.extend([
                'Must import from @chakra-ui/react',
                'No Tailwind CSS classes allowed',
                'Use component props instead of className for styling'
            ])
        elif configuration.styling_system == StylingSystem.TAILWIND:
            rules.extend([
                'Use valid Tailwind utility classes',
                'Follow utility-first methodology',
                'Use responsive prefixes correctly'
            ])
        
        # TypeScript validation rules
        if configuration.typescript:
            rules.extend([
                'Must include proper TypeScript types',
                'Props interfaces should be well-defined',
                'Avoid using any type'
            ])
        
        return rules
    
    def _get_pattern_examples(
        self, 
        configuration: ProjectConfiguration, 
        user_request: str
    ) -> List[str]:
        """Get relevant pattern examples based on configuration and request."""
        
        examples = []
        request_lower = user_request.lower()
        
        # Add examples based on request content and configuration
        if 'button' in request_lower and configuration.styling_system == StylingSystem.CHAKRA_UI:
            examples.extend([
                '<Button colorScheme="blue" variant="solid" size="md">Click me</Button>',
                '<Button leftIcon={<AddIcon />} colorScheme="green">Add Item</Button>',
                '<Button isLoading loadingText="Submitting">Submit</Button>'
            ])
        
        elif 'form' in request_lower and configuration.styling_system == StylingSystem.CHAKRA_UI:
            examples.extend([
                '''<FormControl>
  <FormLabel>Email</FormLabel>
  <Input type="email" />
  <FormHelperText>Enter your email address</FormHelperText>
</FormControl>''',
                '''<VStack spacing={4}>
  <Input placeholder="Name" />
  <Button colorScheme="blue" type="submit">Submit</Button>
</VStack>'''
            ])
        
        elif 'card' in request_lower and configuration.styling_system == StylingSystem.CHAKRA_UI:
            examples.extend([
                '''<Box bg="white" shadow="md" rounded="lg" p={6}>
  <Text fontSize="xl" fontWeight="bold">Card Title</Text>
  <Text color="gray.600" mt={2}>Card content</Text>
</Box>'''
            ])
        
        return examples
    
    def _create_configuration_aware_chunks(
        self,
        config_context: ConfigurationContext,
        priority_weights: Dict[str, float]
    ) -> List[ContextChunk]:
        """Create context chunks with configuration-aware priorities."""
        
        chunks = []
        
        # Create chunks from base context
        for key, value in config_context.base_context.items():
            if isinstance(value, (str, list)) and value:
                priority = priority_weights.get(key, 0.5)
                content = value if isinstance(value, str) else '\n'.join(map(str, value))
                
                chunk = ContextChunk(
                    content=content,
                    context_type=ContextType.PROJECT_STRUCTURE,  # Default type
                    priority=ContextPriority.MEDIUM,  # Convert float to ContextPriority
                    token_estimate=self._estimate_tokens(content),
                    metadata={'source': key, 'configuration_aware': True}
                )
                chunks.append(chunk)
        
        # Add framework-specific chunks
        for key, value in config_context.framework_specific_context.items():
            if isinstance(value, (str, list)) and value:
                content = value if isinstance(value, str) else '\n'.join(map(str, value))
                priority = priority_weights.get('framework_patterns', 0.8) + 0.1  # Boost framework-specific
                
                chunk = ContextChunk(
                    content=content,
                    context_type=ContextType.FRAMEWORK_PATTERNS,
                    priority=ContextPriority.HIGH,  # Framework patterns are high priority
                    token_estimate=self._estimate_tokens(content),
                    metadata={'source': f'framework_{key}', 'framework_specific': True}
                )
                chunks.append(chunk)
        
        # Add styling-specific chunks
        for key, value in config_context.styling_specific_context.items():
            if isinstance(value, (str, list)) and value:
                content = value if isinstance(value, str) else '\n'.join(map(str, value))
                priority = priority_weights.get('component_examples', 0.7) + 0.1  # Boost styling-specific
                
                chunk = ContextChunk(
                    content=content,
                    context_type=ContextType.COMPONENT_EXAMPLES,
                    priority=ContextPriority.HIGH,  # Component examples are high priority
                    token_estimate=self._estimate_tokens(content),
                    metadata={'source': f'styling_{key}', 'styling_specific': True}
                )
                chunks.append(chunk)
        
        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {
            ContextPriority.CRITICAL: 4,
            ContextPriority.HIGH: 3,
            ContextPriority.MEDIUM: 2,
            ContextPriority.LOW: 1
        }
        return sorted(chunks, key=lambda x: priority_order.get(x.priority, 0), reverse=True)
    
    def _optimize_with_configuration_priorities(
        self,
        user_request: str,
        context_chunks: List[ContextChunk],
        system_prompt_base: str,
        user_prompt_base: str,
        priority_weights: Dict[str, float]
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Optimize context with configuration-specific priorities."""
        
        if not context_chunks:
            # Return basic prompts if no context chunks available
            return system_prompt_base, user_prompt_base, {
                'token_budget': {
                    'total': self.max_tokens,
                    'available': self.max_tokens - 1000,
                    'context_used': 0,
                    'utilization': 0.0
                }
            }
        
        # Format chunks into coherent context content
        context_content = self._format_context_chunks(context_chunks)
        
        # Calculate token usage
        system_tokens = self._estimate_tokens(system_prompt_base)
        user_tokens = self._estimate_tokens(user_prompt_base)
        context_tokens = self._estimate_tokens(context_content)
        
        # Build optimized prompts
        optimized_system_prompt = f"{system_prompt_base}\n\n## Project Context\n{context_content}"
        optimized_user_prompt = user_prompt_base
        
        # Calculate utilization
        total_used = system_tokens + user_tokens + context_tokens
        available_tokens = self.max_tokens - 500  # Reserve for response
        utilization = min(1.0, total_used / available_tokens) if available_tokens > 0 else 0
        
        optimization_stats = {
            'token_budget': {
                'total': self.max_tokens,
                'available': available_tokens,
                'context_used': context_tokens,
                'utilization': utilization
            },
            'context_optimization': {
                'total_chunks': len(context_chunks),
                'selected_chunks': len(context_chunks),
                'used_tokens': context_tokens,
                'available_tokens': available_tokens,
                'utilization': utilization,
                'compression_applied': 0
            },
            'chunks_by_type': self._get_chunks_by_type_stats(context_chunks)
        }
        
        return optimized_system_prompt, optimized_user_prompt, optimization_stats
    
    def _format_context_chunks(self, chunks: List[ContextChunk]) -> str:
        """Format context chunks into a coherent context string."""
        if not chunks:
            return ""
        
        sections = {}
        for chunk in chunks:
            section_name = chunk.context_type.value.replace('_', ' ').title()
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(chunk.content)
        
        formatted_sections = []
        for section_name, contents in sections.items():
            if contents:
                formatted_sections.append(f"## {section_name}\n" + "\n".join(contents))
        
        return "\n\n".join(formatted_sections)
    
    def _get_chunks_by_type_stats(self, chunks: List[ContextChunk]) -> Dict[str, Any]:
        """Get statistics about chunks by type."""
        stats = {}
        for chunk in chunks:
            chunk_type = chunk.context_type.value
            if chunk_type not in stats:
                stats[chunk_type] = {
                    'count': 0,
                    'tokens': 0,
                    'compressed': 0
                }
            
            stats[chunk_type]['count'] += 1
            stats[chunk_type]['tokens'] += chunk.token_estimate
            if chunk.metadata.get('compressed', False):
                stats[chunk_type]['compressed'] += 1
        
        return stats
    
    def get_configuration_stats(self, configuration: ProjectConfiguration) -> Dict[str, Any]:
        """Get statistics about configuration-aware context management."""
        
        return {
            'configuration': {
                'framework': configuration.framework.value,
                'styling_system': configuration.styling_system.value,
                'confidence': configuration.confidence_score,
                'strategy': configuration.generation_strategy
            },
            'priority_weights': self._get_configuration_priority_weights(configuration),
            'active_filters': len(self._get_active_filters(configuration)),
            'framework_guidelines': len(self._get_framework_guidelines(configuration.framework)),
            'styling_guidelines': len(self._get_styling_guidelines(configuration.styling_system)),
            'validation_rules': len(self._get_validation_rules(configuration))
        }