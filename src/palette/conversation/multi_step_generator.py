"""
Multi-Step Feature Generation System

This module handles complex multi-step feature generation that spans multiple
components, files, and implementation phases.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

@dataclass
class GenerationStep:
    """Represents a single step in multi-step generation"""
    step_id: str
    step_type: str  # 'component', 'hook', 'util', 'page', 'api', 'test', 'story'
    description: str
    file_path: str
    content: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FeaturePlan:
    """Represents a complete feature generation plan"""
    feature_name: str
    description: str
    steps: List[GenerationStep]
    estimated_complexity: str  # simple, moderate, complex
    framework_specific: Dict[str, Any] = field(default_factory=dict)

class FeatureComplexity(Enum):
    SIMPLE = "simple"        # 1-3 files, basic functionality
    MODERATE = "moderate"    # 4-8 files, some integration
    COMPLEX = "complex"      # 9+ files, advanced features

class MultiStepGenerator:
    """Generates complex features across multiple steps and files"""
    
    def __init__(self, project_path: str, conversation_engine):
        self.project_path = Path(project_path)
        self.conversation_engine = conversation_engine
        self.current_plan: Optional[FeaturePlan] = None
        self.generation_templates = self._load_generation_templates()
        
    def _load_generation_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load templates for different types of features"""
        return {
            'auth_system': {
                'components': ['LoginForm', 'SignupForm', 'AuthProvider', 'ProtectedRoute'],
                'hooks': ['useAuth', 'useUser'],
                'utils': ['authApi', 'tokenStorage'],
                'pages': ['LoginPage', 'SignupPage'],
                'complexity': FeatureComplexity.COMPLEX
            },
            'user_profile': {
                'components': ['ProfileCard', 'EditProfileForm', 'AvatarUpload'],
                'hooks': ['useProfile', 'useAvatar'],
                'utils': ['profileApi'],
                'pages': ['ProfilePage'],
                'complexity': FeatureComplexity.MODERATE
            },
            'dashboard': {
                'components': ['DashboardLayout', 'StatsCard', 'Chart', 'QuickActions'],
                'hooks': ['useDashboardData', 'useStats'],
                'utils': ['dashboardApi'],
                'pages': ['DashboardPage'],
                'complexity': FeatureComplexity.MODERATE
            },
            'data_table': {
                'components': ['DataTable', 'TableRow', 'TableHeader', 'TableFilters', 'Pagination'],
                'hooks': ['useTable', 'usePagination', 'useSort'],
                'utils': ['tableUtils'],
                'complexity': FeatureComplexity.MODERATE
            },
            'shopping_cart': {
                'components': ['CartItem', 'CartSummary', 'CheckoutForm', 'PaymentForm'],
                'hooks': ['useCart', 'useCheckout'],
                'utils': ['cartStorage', 'paymentApi'],
                'complexity': FeatureComplexity.COMPLEX
            },
            'blog_system': {
                'components': ['BlogPost', 'BlogList', 'BlogEditor', 'CommentSection'],
                'hooks': ['useBlog', 'useComments'],
                'utils': ['blogApi', 'markdownParser'],
                'pages': ['BlogPage', 'BlogListPage', 'BlogEditorPage'],
                'complexity': FeatureComplexity.COMPLEX
            },
            'search_functionality': {
                'components': ['SearchBar', 'SearchResults', 'SearchFilters', 'SearchSuggestions'],
                'hooks': ['useSearch', 'useDebounce'],
                'utils': ['searchApi', 'searchUtils'],
                'complexity': FeatureComplexity.MODERATE
            },
            'notification_system': {
                'components': ['NotificationProvider', 'NotificationItem', 'NotificationList'],
                'hooks': ['useNotifications'],
                'utils': ['notificationService'],
                'complexity': FeatureComplexity.MODERATE
            }
        }

    def analyze_feature_request(self, user_message: str) -> Tuple[str, FeatureComplexity, List[str]]:
        """Analyze user request to determine feature type and complexity"""
        message_lower = user_message.lower()
        
        # Detect feature type
        feature_type = "custom"
        confidence = 0
        
        for template_name, template_data in self.generation_templates.items():
            # Check for keywords that match this template
            keywords = template_name.split('_')
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            
            # Also check component names
            component_matches = sum(1 for comp in template_data.get('components', []) 
                                  if comp.lower().replace('form', '').replace('page', '') in message_lower)
            
            total_score = matches + component_matches * 0.5
            if total_score > confidence:
                confidence = total_score
                feature_type = template_name
        
        # Determine complexity based on request
        complexity = self._estimate_complexity(user_message, feature_type)
        
        # Extract specific requirements
        requirements = self._extract_requirements(user_message)
        
        return feature_type, complexity, requirements

    def _estimate_complexity(self, message: str, feature_type: str) -> FeatureComplexity:
        """Estimate the complexity of the requested feature"""
        message_lower = message.lower()
        
        # Get default complexity from template
        if feature_type in self.generation_templates:
            default_complexity = self.generation_templates[feature_type]['complexity']
        else:
            default_complexity = FeatureComplexity.MODERATE
        
        # Complexity indicators
        complex_indicators = [
            'authentication', 'auth', 'login', 'security', 'payment', 'checkout',
            'real-time', 'websocket', 'chat', 'notification', 'email',
            'admin', 'dashboard', 'analytics', 'reporting', 'export',
            'multi-step', 'wizard', 'workflow', 'approval', 'review'
        ]
        
        simple_indicators = [
            'simple', 'basic', 'minimal', 'quick', 'small',
            'single', 'one page', 'just a', 'only'
        ]
        
        complex_score = sum(1 for indicator in complex_indicators if indicator in message_lower)
        simple_score = sum(1 for indicator in simple_indicators if indicator in message_lower)
        
        if simple_score > complex_score and simple_score > 1:
            return FeatureComplexity.SIMPLE
        elif complex_score > 2:
            return FeatureComplexity.COMPLEX
        else:
            return default_complexity

    def _extract_requirements(self, message: str) -> List[str]:
        """Extract specific requirements from user message"""
        requirements = []
        
        # Common requirement patterns
        patterns = {
            'responsive': r'(responsive|mobile|tablet|desktop)',
            'accessibility': r'(accessible|a11y|screen reader|aria)',
            'dark_mode': r'(dark mode|theme|light\/dark)',
            'typescript': r'(typescript|ts|typed)',
            'testing': r'(test|testing|jest|cypress)',
            'animation': r'(animate|animation|transition|motion)',
            'form_validation': r'(validation|validate|error handling)',
            'data_fetching': r'(api|fetch|axios|swr|tanstack)',
            'state_management': r'(state|redux|zustand|context)',
            'routing': r'(routing|router|navigate|redirect)'
        }
        
        message_lower = message.lower()
        for req_name, pattern in patterns.items():
            if re.search(pattern, message_lower):
                requirements.append(req_name)
        
        return requirements

    def create_feature_plan(self, feature_type: str, complexity: FeatureComplexity, 
                          requirements: List[str], user_message: str) -> FeaturePlan:
        """Create a detailed plan for feature generation"""
        
        feature_name = self._generate_feature_name(user_message, feature_type)
        
        steps = []
        step_counter = 1
        
        # Get template or create custom plan
        if feature_type in self.generation_templates:
            template = self.generation_templates[feature_type]
            steps.extend(self._create_steps_from_template(template, step_counter, requirements))
        else:
            steps.extend(self._create_custom_steps(user_message, complexity, step_counter, requirements))
        
        # Add framework-specific steps
        framework_steps = self._add_framework_specific_steps(steps, requirements)
        steps.extend(framework_steps)
        
        # Add testing steps if requested
        if 'testing' in requirements:
            test_steps = self._create_test_steps(steps, len(steps) + 1)
            steps.extend(test_steps)
        
        plan = FeaturePlan(
            feature_name=feature_name,
            description=user_message,
            steps=steps,
            estimated_complexity=complexity.value,
            framework_specific=self._get_framework_config(requirements)
        )
        
        return plan

    def _generate_feature_name(self, message: str, feature_type: str) -> str:
        """Generate a feature name from user message"""
        if feature_type != "custom":
            return feature_type.replace('_', ' ').title()
        
        # Extract key nouns from message
        words = re.findall(r'\b[a-zA-Z]+\b', message.lower())
        key_words = [word for word in words if len(word) > 3 and word not in [
            'create', 'build', 'make', 'need', 'want', 'would', 'like', 'please',
            'with', 'that', 'have', 'component', 'feature', 'system'
        ]]
        
        if key_words:
            return ' '.join(key_words[:3]).title()
        else:
            return "Custom Feature"

    def _create_steps_from_template(self, template: Dict[str, Any], 
                                  start_counter: int, requirements: List[str]) -> List[GenerationStep]:
        """Create generation steps from a template"""
        steps = []
        counter = start_counter
        
        # Create component steps
        for component in template.get('components', []):
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="component",
                description=f"Create {component} component",
                file_path=self._get_component_path(component),
                dependencies=self._get_component_dependencies(component, template),
                metadata={'template_based': True, 'component_name': component}
            ))
            counter += 1
        
        # Create hook steps
        for hook in template.get('hooks', []):
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="hook",
                description=f"Create {hook} custom hook",
                file_path=self._get_hook_path(hook),
                metadata={'template_based': True, 'hook_name': hook}
            ))
            counter += 1
        
        # Create utility steps
        for util in template.get('utils', []):
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="util",
                description=f"Create {util} utility",
                file_path=self._get_util_path(util),
                metadata={'template_based': True, 'util_name': util}
            ))
            counter += 1
        
        # Create page steps
        for page in template.get('pages', []):
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="page",
                description=f"Create {page} page",
                file_path=self._get_page_path(page),
                metadata={'template_based': True, 'page_name': page}
            ))
            counter += 1
        
        return steps

    def _create_custom_steps(self, message: str, complexity: FeatureComplexity, 
                           start_counter: int, requirements: List[str]) -> List[GenerationStep]:
        """Create custom steps based on user message analysis"""
        steps = []
        counter = start_counter
        
        # Analyze message to determine what components are needed
        message_lower = message.lower()
        
        # Detect component types mentioned
        component_indicators = {
            'form': ['form', 'input', 'submit', 'validation'],
            'list': ['list', 'table', 'grid', 'items'],
            'card': ['card', 'item', 'post', 'product'],
            'modal': ['modal', 'dialog', 'popup', 'overlay'],
            'navigation': ['nav', 'menu', 'header', 'sidebar'],
            'button': ['button', 'action', 'click', 'submit'],
            'layout': ['layout', 'page', 'container', 'wrapper']
        }
        
        detected_components = []
        for comp_type, indicators in component_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                detected_components.append(comp_type.title())
        
        # Create steps for detected components
        for component in detected_components:
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="component",
                description=f"Create {component} component",
                file_path=self._get_component_path(component),
                metadata={'custom': True, 'component_name': component}
            ))
            counter += 1
        
        # Add a main page/container component if complexity is moderate or higher
        if complexity in [FeatureComplexity.MODERATE, FeatureComplexity.COMPLEX]:
            feature_name = self._generate_feature_name(message, "custom")
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="page",
                description=f"Create main {feature_name} page",
                file_path=self._get_page_path(f"{feature_name.replace(' ', '')}Page"),
                metadata={'custom': True, 'main_page': True}
            ))
            counter += 1
        
        # Add hook if state management is needed
        if 'state_management' in requirements or complexity == FeatureComplexity.COMPLEX:
            feature_name = self._generate_feature_name(message, "custom")
            hook_name = f"use{feature_name.replace(' ', '')}"
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="hook",
                description=f"Create {hook_name} hook for state management",
                file_path=self._get_hook_path(hook_name),
                metadata={'custom': True, 'hook_name': hook_name}
            ))
            counter += 1
        
        return steps

    def _add_framework_specific_steps(self, existing_steps: List[GenerationStep], 
                                    requirements: List[str]) -> List[GenerationStep]:
        """Add framework-specific steps (Next.js API routes, etc.)"""
        steps = []
        counter = len(existing_steps) + 1
        
        # Add API routes for Next.js if data fetching is needed
        if 'data_fetching' in requirements:
            steps.append(GenerationStep(
                step_id=f"step_{counter}",
                step_type="api",
                description="Create API route for data fetching",
                file_path="pages/api/data.ts",  # or app/api/data/route.ts for App Router
                metadata={'framework_specific': True, 'api_route': True}
            ))
            counter += 1
        
        return steps

    def _create_test_steps(self, main_steps: List[GenerationStep], start_counter: int) -> List[GenerationStep]:
        """Create test steps for components"""
        test_steps = []
        counter = start_counter
        
        for step in main_steps:
            if step.step_type in ['component', 'hook']:
                test_name = step.metadata.get('component_name', step.metadata.get('hook_name', 'Component'))
                test_steps.append(GenerationStep(
                    step_id=f"test_step_{counter}",
                    step_type="test",
                    description=f"Create tests for {test_name}",
                    file_path=step.file_path.replace('.tsx', '.test.tsx').replace('.ts', '.test.ts'),
                    dependencies=[step.step_id],
                    metadata={'test_for': step.step_id, 'test_name': f"{test_name}Test"}
                ))
                counter += 1
        
        return test_steps

    def _get_component_path(self, component_name: str) -> str:
        """Get the file path for a component"""
        # Try to determine project structure
        if (self.project_path / 'src' / 'components').exists():
            return f"src/components/{component_name}.tsx"
        elif (self.project_path / 'components').exists():
            return f"components/{component_name}.tsx"
        else:
            return f"src/{component_name}.tsx"

    def _get_hook_path(self, hook_name: str) -> str:
        """Get the file path for a custom hook"""
        if (self.project_path / 'src' / 'hooks').exists():
            return f"src/hooks/{hook_name}.ts"
        elif (self.project_path / 'hooks').exists():
            return f"hooks/{hook_name}.ts"
        else:
            return f"src/{hook_name}.ts"

    def _get_util_path(self, util_name: str) -> str:
        """Get the file path for a utility"""
        if (self.project_path / 'src' / 'utils').exists():
            return f"src/utils/{util_name}.ts"
        elif (self.project_path / 'utils').exists():
            return f"utils/{util_name}.ts"
        else:
            return f"src/{util_name}.ts"

    def _get_page_path(self, page_name: str) -> str:
        """Get the file path for a page"""
        if (self.project_path / 'src' / 'pages').exists():
            return f"src/pages/{page_name}.tsx"
        elif (self.project_path / 'pages').exists():
            return f"pages/{page_name}.tsx"
        elif (self.project_path / 'app').exists():  # Next.js App Router
            return f"app/{page_name.lower().replace('page', '')}/page.tsx"
        else:
            return f"src/{page_name}.tsx"

    def _get_component_dependencies(self, component: str, template: Dict[str, Any]) -> List[str]:
        """Get dependencies for a component based on template"""
        dependencies = []
        
        # Simple dependency mapping
        if component.endswith('Form') and 'Provider' in str(template.get('components', [])):
            dependencies.append('provider')
        elif component.endswith('Page'):
            # Pages typically depend on multiple components
            deps = [comp.lower() for comp in template.get('components', []) 
                   if not comp.endswith('Page') and not comp.endswith('Provider')]
            dependencies.extend(deps[:3])  # Limit dependencies
        
        return dependencies

    def _get_framework_config(self, requirements: List[str]) -> Dict[str, Any]:
        """Get framework-specific configuration"""
        config = {}
        
        if 'routing' in requirements:
            config['routing'] = True
        if 'state_management' in requirements:
            config['state_management'] = 'context'  # Could be enhanced to detect preferred solution
        if 'typescript' in requirements:
            config['typescript'] = True
        
        return config

    async def execute_feature_plan(self, plan: FeaturePlan) -> Dict[str, Any]:
        """Execute the feature generation plan step by step"""
        self.current_plan = plan
        results = {
            'feature_name': plan.feature_name,
            'total_steps': len(plan.steps),
            'completed_steps': 0,
            'generated_files': [],
            'errors': [],
            'step_results': {}
        }
        
        print(f"🚀 Starting multi-step generation for: {plan.feature_name}")
        print(f"📋 Total steps: {len(plan.steps)}")
        
        # Execute steps in dependency order
        for step in plan.steps:
            try:
                print(f"⏳ Step {step.step_id}: {step.description}")
                step.status = "in_progress"
                
                # Generate content for this step
                step_result = await self._execute_single_step(step, plan)
                
                if step_result['success']:
                    step.status = "completed"
                    step.content = step_result['content']
                    results['completed_steps'] += 1
                    results['generated_files'].append(step.file_path)
                    results['step_results'][step.step_id] = step_result
                    print(f"✅ Completed: {step.description}")
                else:
                    step.status = "failed"
                    results['errors'].append({
                        'step_id': step.step_id,
                        'error': step_result['error']
                    })
                    print(f"❌ Failed: {step.description} - {step_result['error']}")
                
            except Exception as e:
                step.status = "failed"
                error_msg = str(e)
                results['errors'].append({
                    'step_id': step.step_id,
                    'error': error_msg
                })
                print(f"❌ Error in step {step.step_id}: {error_msg}")
        
        # Generate summary
        success_rate = (results['completed_steps'] / results['total_steps']) * 100
        print(f"🎯 Feature generation complete: {success_rate:.1f}% success rate")
        print(f"📁 Generated {len(results['generated_files'])} files")
        
        return results

    async def _execute_single_step(self, step: GenerationStep, plan: FeaturePlan) -> Dict[str, Any]:
        """Execute a single step in the feature plan"""
        try:
            # Build context for this step
            step_context = self._build_step_context(step, plan)
            
            # Create step-specific prompt
            step_prompt = self._create_step_prompt(step, step_context)
            
            # Generate using conversation engine
            if step.step_type == "component":
                content = self.conversation_engine.ui_generator.generate_component(
                    step_prompt, step_context
                )
            elif step.step_type in ["hook", "util"]:
                content = self.conversation_engine.ui_generator.generate_component(
                    step_prompt, step_context
                )
            elif step.step_type == "page":
                content = self.conversation_engine.ui_generator.generate_component(
                    step_prompt, step_context
                )
            elif step.step_type == "test":
                content = self._generate_test_content(step, step_context)
            else:
                content = self._generate_generic_content(step, step_context)
            
            return {
                'success': True,
                'content': content,
                'file_path': step.file_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _build_step_context(self, step: GenerationStep, plan: FeaturePlan) -> Dict[str, Any]:
        """Build context for a specific step"""
        # Get base context from conversation engine
        base_context = self.conversation_engine._build_generation_context()
        
        # Add step-specific context
        step_context = {
            **base_context,
            'feature_name': plan.feature_name,
            'feature_description': plan.description,
            'step_type': step.step_type,
            'step_description': step.description,
            'file_path': step.file_path,
            'multi_step_generation': True,
            'total_steps': len(plan.steps),
            'current_step': step.step_id
        }
        
        # Add dependency context
        if step.dependencies:
            dependency_info = []
            for dep_id in step.dependencies:
                dep_step = next((s for s in plan.steps if s.step_id == dep_id), None)
                if dep_step and dep_step.status == "completed":
                    dependency_info.append({
                        'name': dep_step.metadata.get('component_name', 'Dependency'),
                        'type': dep_step.step_type,
                        'path': dep_step.file_path
                    })
            step_context['dependencies'] = dependency_info
        
        # Add template information if available
        if step.metadata.get('template_based'):
            step_context['template_based'] = True
            step_context['component_name'] = step.metadata.get('component_name')
        
        return step_context

    def _create_step_prompt(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Create a specific prompt for this step"""
        base_prompt = f"Create a {step.step_type} for the {context['feature_name']} feature.\n\n"
        base_prompt += f"Step description: {step.description}\n"
        base_prompt += f"File path: {step.file_path}\n\n"
        
        # Add step-type specific guidance
        if step.step_type == "component":
            base_prompt += self._get_component_prompt_guidance(step, context)
        elif step.step_type == "hook":
            base_prompt += self._get_hook_prompt_guidance(step, context)
        elif step.step_type == "util":
            base_prompt += self._get_util_prompt_guidance(step, context)
        elif step.step_type == "page":
            base_prompt += self._get_page_prompt_guidance(step, context)
        
        # Add dependency information
        if context.get('dependencies'):
            base_prompt += "\nThis component should integrate with:\n"
            for dep in context['dependencies']:
                base_prompt += f"- {dep['name']} ({dep['type']}) at {dep['path']}\n"
        
        return base_prompt

    def _get_component_prompt_guidance(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Get component-specific prompt guidance"""
        component_name = step.metadata.get('component_name', 'Component')
        guidance = f"Create a React component named {component_name}.\n\n"
        
        # Add specific guidance based on component type
        if 'form' in component_name.lower():
            guidance += "Include proper form validation, error handling, and submit functionality.\n"
        elif 'list' in component_name.lower() or 'table' in component_name.lower():
            guidance += "Include proper data rendering, loading states, and empty states.\n"
        elif 'card' in component_name.lower():
            guidance += "Include a clean card layout with proper spacing and visual hierarchy.\n"
        elif 'modal' in component_name.lower() or 'dialog' in component_name.lower():
            guidance += "Include proper modal behavior, backdrop, close functionality, and accessibility.\n"
        
        guidance += f"Follow the existing design system patterns and maintain consistency.\n"
        
        return guidance

    def _get_hook_prompt_guidance(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Get hook-specific prompt guidance"""
        hook_name = step.metadata.get('hook_name', 'useHook')
        guidance = f"Create a React custom hook named {hook_name}.\n\n"
        guidance += "Include proper TypeScript types, error handling, and return the necessary state and functions.\n"
        guidance += "Follow React hooks best practices and conventions.\n"
        
        return guidance

    def _get_util_prompt_guidance(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Get utility-specific prompt guidance"""
        util_name = step.metadata.get('util_name', 'util')
        guidance = f"Create a utility module named {util_name}.\n\n"
        guidance += "Include proper TypeScript types and comprehensive error handling.\n"
        guidance += "Make functions pure and well-tested where possible.\n"
        
        return guidance

    def _get_page_prompt_guidance(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Get page-specific prompt guidance"""
        page_name = step.metadata.get('page_name', 'Page')
        guidance = f"Create a React page component named {page_name}.\n\n"
        guidance += "Include proper layout, SEO considerations, and integration with other components.\n"
        guidance += "Follow the existing page structure and routing patterns.\n"
        
        return guidance

    def _generate_test_content(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Generate test content for a step"""
        test_name = step.metadata.get('test_name', 'ComponentTest')
        component_name = test_name.replace('Test', '')
        
        # Simple test template - could be enhanced
        test_content = f'''import {{ render, screen }} from '@testing-library/react';
import {{ {component_name} }} from './{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
  }});

  it('displays expected content', () => {{
    render(<{component_name} />);
    // Add specific test assertions based on component
  }});
}});
'''
        return test_content

    def _generate_generic_content(self, step: GenerationStep, context: Dict[str, Any]) -> str:
        """Generate generic content for unknown step types"""
        return f"// Generated content for {step.step_type}: {step.description}\n// TODO: Implement {step.step_type} functionality\n"

    def get_plan_summary(self, plan: FeaturePlan) -> str:
        """Get a human-readable summary of the feature plan"""
        summary = f"## 📋 Feature Plan: {plan.feature_name}\n\n"
        summary += f"**Description:** {plan.description}\n"
        summary += f"**Complexity:** {plan.estimated_complexity.title()}\n"
        summary += f"**Total Steps:** {len(plan.steps)}\n\n"
        
        # Group steps by type
        step_groups = {}
        for step in plan.steps:
            if step.step_type not in step_groups:
                step_groups[step.step_type] = []
            step_groups[step.step_type].append(step)
        
        summary += "### 🔧 Generation Steps:\n\n"
        for step_type, steps in step_groups.items():
            summary += f"**{step_type.title()}s:**\n"
            for step in steps:
                summary += f"- {step.description} (`{step.file_path}`)\n"
            summary += "\n"
        
        return summary