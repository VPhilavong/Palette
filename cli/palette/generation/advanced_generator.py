"""
Advanced UI Generator with sophisticated prompt orchestration and context management.
Integrates Chain-of-Thought, Reflection, Role-Based prompting with token-aware context optimization.
"""

import os
from typing import Dict, List, Optional, Tuple, Any

import anthropic
from openai import OpenAI

from .advanced_prompt_orchestrator import (
    AdvancedPromptOrchestrator, 
    PromptStrategy, 
    ComponentComplexity
)
from .context_manager import TokenAwareContextManager
from .design_token_semantics import get_design_token_semantics, TokenType, TokenRole
from .smart_asset_recommender import get_smart_asset_recommender
from .generator import UIGenerator
from ..errors import GenerationError
from ..errors.decorators import handle_errors, retry_on_error


class AdvancedUIGenerator(UIGenerator):
    """
    Advanced UI Generator with sophisticated prompting strategies and context optimization.
    Extends the base UIGenerator with advanced LLM interaction capabilities.
    """
    
    def __init__(
        self,
        model: str = None,
        project_path: str = None,
        enhanced_mode: bool = True,
        quality_assurance: bool = True,
        max_tokens: int = 4000,
        enable_advanced_prompting: bool = True
    ):
        # Initialize base generator
        super().__init__(model, project_path, enhanced_mode, quality_assurance)
        
        # Initialize advanced components
        self.max_tokens = max_tokens
        self.enable_advanced_prompting = enable_advanced_prompting
        
        if enable_advanced_prompting:
            self.prompt_orchestrator = AdvancedPromptOrchestrator()
            self.context_manager = TokenAwareContextManager(max_tokens=max_tokens)
            self.design_token_semantics = get_design_token_semantics()
            self.asset_recommender = get_smart_asset_recommender()
            print("✅ Advanced prompt orchestration enabled")
            
            # Analyze project resources
            if project_path:
                self._analyze_project_tokens()
                self._analyze_project_assets()
        else:
            self.prompt_orchestrator = None
            self.context_manager = None
            self.design_token_semantics = None
            self.asset_recommender = None
        
        # Track generation attempts for reflection prompting
        self.generation_attempts = {}
    
    def _analyze_project_tokens(self):
        """Analyze design tokens in the project."""
        try:
            print("🎨 Analyzing project design tokens...")
            analysis = self.design_token_semantics.analyze_project_tokens(self.project_path)
            
            if analysis["tokens_found"] > 0:
                print(f"✅ Found {analysis['tokens_found']} design tokens from {len(analysis['sources'])} sources")
                
                # Log token types discovered
                for token_type, count in analysis["token_types"].items():
                    print(f"   - {token_type}: {count} tokens")
                
                # Show recommendations if any
                if analysis.get("recommendations"):
                    print("💡 Token recommendations:")
                    for rec in analysis["recommendations"]:
                        print(f"   - {rec}")
            else:
                print("⚠️ No design tokens found in project")
        except Exception as e:
            print(f"⚠️ Failed to analyze design tokens: {e}")
    
    def _analyze_project_assets(self):
        """Analyze assets available in the project."""
        try:
            print("🖼️ Analyzing project assets...")
            analysis = self.asset_recommender.analyze_project_assets(self.project_path)
            
            if analysis["assets_found"] > 0:
                print(f"✅ Found {analysis['assets_found']} assets in {len(analysis['asset_directories'])} directories")
                
                # Log asset types discovered
                for asset_type, count in analysis["asset_types"].items():
                    print(f"   - {asset_type}: {count} assets")
                
                # Show recommendations if any
                if analysis.get("recommendations"):
                    print("💡 Asset recommendations:")
                    for rec in analysis["recommendations"]:
                        print(f"   - {rec}")
            else:
                print("⚠️ No assets found in project - will recommend popular libraries")
        except Exception as e:
            print(f"⚠️ Failed to analyze project assets: {e}")
    
    @handle_errors(reraise=True)
    @retry_on_error(
        max_attempts=3,
        delay=1.0,
        error_types=[GenerationError],
        on_retry=lambda e, attempt: print(f"🔄 Retrying generation with reflection prompting (attempt {attempt}/3)")
    )
    def generate_component_advanced(
        self, 
        prompt: str, 
        context: Dict,
        use_reflection: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate component using advanced prompting strategies.
        
        Args:
            prompt: User's component request
            context: Project context including design tokens, components, etc.
            use_reflection: Whether to use reflection prompting (for retry attempts)
            
        Returns:
            Tuple of (generated_code, generation_metadata)
        """
        if not self.enable_advanced_prompting:
            # Fallback to base generator
            code = super().generate_component(prompt, context)
            return code, {'strategy': 'fallback', 'advanced_features': False}
        
        generation_metadata = {
            'strategy': None,
            'context_optimization': {},
            'complexity_analysis': {},
            'advanced_features': True
        }
        
        try:
            # Get previous attempts for reflection
            previous_attempts = self.generation_attempts.get(prompt, []) if use_reflection else []
            
            # Use advanced prompt orchestration
            system_prompt, user_prompt, strategy_used = self.prompt_orchestrator.orchestrate_generation(
                user_request=prompt,
                project_context=context,
                previous_attempts=previous_attempts
            )
            
            generation_metadata['strategy'] = strategy_used.value
            generation_metadata['complexity_analysis'] = {
                'previous_attempts': len(previous_attempts),
                'using_reflection': use_reflection
            }
            
            # Enhance context with design tokens and asset recommendations
            if self.design_token_semantics or self.asset_recommender:
                enhanced_context = self._enhance_context_with_resources(context, prompt)
                generation_metadata['design_tokens'] = enhanced_context.get('design_token_analysis', {})
                generation_metadata['asset_recommendations'] = enhanced_context.get('asset_recommendations', {})
            else:
                enhanced_context = context
            
            # Optimize context within token budget
            if self.context_manager:
                optimized_system, optimized_user, context_stats = self.context_manager.optimize_context(
                    user_request=prompt,
                    project_context=enhanced_context,
                    system_prompt_base=system_prompt,
                    user_prompt_base=user_prompt
                )
                
                generation_metadata['context_optimization'] = context_stats
                
                # Use optimized prompts
                system_prompt = optimized_system
                user_prompt = optimized_user
                
                print(f"📊 Context optimization: {context_stats['token_budget']['utilization']:.1%} token utilization")
            
            # Generate with appropriate API
            if self.model.startswith("gpt"):
                component_code = self._generate_with_openai_advanced(system_prompt, user_prompt)
            elif self.model.startswith("claude"):
                component_code = self._generate_with_anthropic_advanced(system_prompt, user_prompt)
            else:
                raise GenerationError(f"Unsupported model: {self.model}")
            
            # Clean and process the response
            cleaned_code = self.clean_response(component_code)
            
            # Track this attempt for potential reflection
            if prompt not in self.generation_attempts:
                self.generation_attempts[prompt] = []
            self.generation_attempts[prompt].append(cleaned_code)
            
            # Add usage example
            usage_example = self._generate_usage_example(cleaned_code, prompt)
            final_code = cleaned_code + usage_example
            
            print(f"✅ Generated using {strategy_used.value} strategy")
            
            return final_code, generation_metadata
            
        except Exception as e:
            # Track failed attempt
            if prompt not in self.generation_attempts:
                self.generation_attempts[prompt] = []
            self.generation_attempts[prompt].append(f"FAILED: {str(e)}")
            
            # If this was already a reflection attempt, don't retry
            if use_reflection:
                raise GenerationError(f"Advanced generation failed even with reflection: {str(e)}")
            
            # Re-raise to trigger retry with reflection
            raise GenerationError(f"Advanced generation failed: {str(e)}")
    
    def generate_component_with_advanced_qa(
        self,
        prompt: str,
        context: Dict,
        target_path: str = None,
        max_refinement_iterations: int = 2
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate component with advanced QA including iterative refinement.
        
        Args:
            prompt: User's component request
            context: Project context
            target_path: Target file path
            max_refinement_iterations: Maximum refinement attempts
            
        Returns:
            Tuple of (final_code, comprehensive_metadata)
        """
        print("🚀 Starting advanced generation with iterative refinement...")
        
        # Initial generation
        try:
            initial_code, generation_metadata = self.generate_component_advanced(prompt, context)
        except Exception:
            # If advanced generation fails, try with reflection
            print("⚠️ Initial generation failed, trying with reflection...")
            initial_code, generation_metadata = self.generate_component_advanced(
                prompt, context, use_reflection=True
            )
        
        current_code = initial_code
        refinement_history = []
        
        # Iterative refinement
        for iteration in range(max_refinement_iterations):
            print(f"🔍 Quality assessment iteration {iteration + 1}/{max_refinement_iterations}")
            
            if self.validator:
                # Run quality validation
                try:
                    refined_code, quality_report = self.validator.iterative_refinement(
                        current_code, target_path or "Component.tsx", max_iterations=1
                    )
                    
                    # Check if refinement improved the code
                    if quality_report.score > 85 or len(quality_report.issues) == 0:
                        print(f"✅ Quality threshold met (score: {quality_report.score:.1f})")
                        current_code = refined_code
                        break
                    
                    # If significant improvement, continue refining
                    if refined_code != current_code:
                        refinement_history.append({
                            'iteration': iteration + 1,
                            'score': quality_report.score,
                            'issues_count': len(quality_report.issues),
                            'improvements': quality_report.auto_fixes_applied
                        })
                        current_code = refined_code
                    else:
                        print("🔄 No further improvements possible")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Quality validation failed: {e}")
                    break
            else:
                print("⚠️ No validator available, skipping iterative refinement")
                break
        
        # Final formatting
        print("🎨 Final formatting and cleanup...")
        final_code = self.format_and_lint_code(current_code, self.project_path or os.getcwd())
        
        # Prepare comprehensive metadata
        comprehensive_metadata = {
            **generation_metadata,
            'refinement': {
                'iterations': len(refinement_history),
                'history': refinement_history,
                'final_quality_score': refinement_history[-1]['score'] if refinement_history else None
            },
            'final_processing': {
                'formatted': True,
                'linted': True
            }
        }
        
        return final_code, comprehensive_metadata
    
    def _generate_with_openai_advanced(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using OpenAI API with advanced configuration."""
        if not self.openai_client:
            raise GenerationError("OpenAI API key not configured")
        
        try:
            # Use higher temperature for creative prompting strategies
            temperature = 0.8 if any(strategy in system_prompt.lower() for strategy in [
                'chain-of-thought', 'reflection', 'role-based'
            ]) else 0.7
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=min(2000, self.max_tokens // 2),  # Reserve half for response
                temperature=temperature,
                top_p=0.95,  # Slightly more focused sampling
                presence_penalty=0.1,  # Encourage variety
                frequency_penalty=0.1   # Reduce repetition
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise GenerationError(f"OpenAI API error: {str(e)}")
    
    def _generate_with_anthropic_advanced(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using Anthropic API with advanced configuration."""
        if not self.anthropic_client:
            raise GenerationError("Anthropic API key not configured")
        
        try:
            # Use higher temperature for creative prompting strategies
            temperature = 0.8 if any(strategy in system_prompt.lower() for strategy in [
                'chain-of-thought', 'reflection', 'role-based'
            ]) else 0.7
            
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=min(2000, self.max_tokens // 2),
                temperature=temperature,
                top_p=0.95,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            raise GenerationError(f"Anthropic API error: {str(e)}")
    
    def _enhance_context_with_resources(self, context: Dict, prompt: str) -> Dict[str, Any]:
        """Enhance context with intelligent design token and asset recommendations."""
        enhanced_context = context.copy()
        
        try:
            # Extract component type from prompt
            component_type = self._extract_component_type_from_prompt(prompt)
            
            # Design Token Enhancement
            design_token_analysis = {}
            if self.design_token_semantics:
                design_token_analysis = self._get_design_token_analysis(component_type, prompt)
                enhanced_context['design_token_analysis'] = design_token_analysis
                enhanced_context['design_token_guidelines'] = self._get_token_usage_guidelines()
            
            # Asset Recommendation Enhancement
            asset_recommendations = {}
            if self.asset_recommender:
                asset_recommendations = self._get_asset_recommendations(component_type, prompt)
                enhanced_context['asset_recommendations'] = asset_recommendations
                enhanced_context['asset_guidelines'] = self.asset_recommender.get_asset_usage_guidelines(component_type)
            
            total_recommendations = len(design_token_analysis.get('specific_recommendations', [])) + \
                                  len(asset_recommendations.get('recommended_assets', []))
            
            print(f"🎨 Enhanced context with {total_recommendations} resource recommendations")
            
        except Exception as e:
            print(f"⚠️ Failed to enhance context with resources: {e}")
        
        return enhanced_context
    
    def _get_design_token_analysis(self, component_type: str, prompt: str) -> Dict[str, Any]:
        """Get design token analysis for the component."""
        try:
            # Get token usage suggestions for this component type
            token_suggestions = self.design_token_semantics.get_token_usage_suggestions(component_type)
            
            # Add specific token recommendations based on prompt context
            specific_recommendations = {}
            
            # Look for specific contexts in the prompt
            prompt_lower = prompt.lower()
            
            if "button" in prompt_lower:
                if "primary" in prompt_lower:
                    primary_recs = self.design_token_semantics.recommend_token_for_context(
                        "primary button background", TokenType.COLOR, TokenRole.PRIMARY
                    )
                    specific_recommendations["primary_button"] = primary_recs
                if "error" in prompt_lower or "danger" in prompt_lower:
                    error_recs = self.design_token_semantics.recommend_token_for_context(
                        "error button background", TokenType.COLOR, TokenRole.ERROR
                    )
                    specific_recommendations["error_button"] = error_recs
            
            if "card" in prompt_lower:
                card_tokens = self.design_token_semantics.recommend_token_for_context(
                    "card background", TokenType.COLOR, TokenRole.SURFACE
                )
                specific_recommendations["card_background"] = card_tokens
            
            if "form" in prompt_lower:
                form_tokens = self.design_token_semantics.recommend_token_for_context(
                    "form input background", TokenType.COLOR, TokenRole.BACKGROUND
                )
                specific_recommendations["form_input"] = form_tokens
            
            # Create comprehensive design token analysis
            return {
                'component_type': component_type,
                'suggested_tokens': token_suggestions,
                'specific_recommendations': [
                    {
                        'token_name': rec.token_name,
                        'confidence': rec.confidence,
                        'reasoning': rec.reasoning,
                        'alternatives': rec.alternative_tokens
                    }
                    for context_recs in specific_recommendations.values()
                    for rec in context_recs[:2]  # Top 2 per context
                ],
                'available_tokens': self._get_available_tokens_summary()
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get design token analysis: {e}")
            return {}
    
    def _get_asset_recommendations(self, component_type: str, prompt: str) -> Dict[str, Any]:
        """Get asset recommendations for the component."""
        try:
            # Get asset recommendations from the recommender
            asset_recs = self.asset_recommender.recommend_assets_for_component(
                component_type=component_type,
                context=prompt,
                max_recommendations=5
            )
            
            # Format recommendations for context
            recommended_assets = []
            for rec in asset_recs:
                recommended_assets.append({
                    'name': rec.asset.name,
                    'type': rec.asset.asset_type.value,
                    'category': rec.asset.category.value,
                    'confidence': rec.confidence,
                    'reasoning': rec.reasoning,
                    'usage_examples': rec.usage_examples,
                    'path': rec.asset.path,
                    'format': rec.asset.format
                })
            
            return {
                'component_type': component_type,
                'recommended_assets': recommended_assets,
                'total_project_assets': len(self.asset_recommender.assets),
                'available_libraries': list(self.asset_recommender.asset_libraries.keys())
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get asset recommendations: {e}")
            return {}
    
    def _extract_component_type_from_prompt(self, prompt: str) -> str:
        """Extract the main component type from the user prompt."""
        prompt_lower = prompt.lower()
        
        # Common component types in order of specificity
        component_types = [
            "navigation", "navbar", "sidebar", "modal", "dialog", "dropdown",
            "accordion", "tabs", "carousel", "table", "form", "button", "card",
            "list", "input", "checkbox", "radio", "toggle", "select"
        ]
        
        for comp_type in component_types:
            if comp_type in prompt_lower:
                return comp_type
        
        return "component"  # Default fallback
    
    def _get_available_tokens_summary(self) -> Dict[str, int]:
        """Get a summary of available design tokens by type."""
        summary = {}
        
        for token in self.design_token_semantics.tokens.values():
            token_type = token.token_type.value
            if token_type not in summary:
                summary[token_type] = 0
            summary[token_type] += 1
        
        return summary
    
    def _get_token_usage_guidelines(self) -> List[str]:
        """Get general design token usage guidelines."""
        return [
            "Use semantic tokens (primary, success, error) instead of raw colors when possible",
            "Maintain consistent spacing scale across components",
            "Use design system typography tokens for text sizing",
            "Apply border radius tokens consistently for visual cohesion",
            "Use shadow tokens to create proper elevation hierarchy",
            "Ensure color contrast meets accessibility requirements",
            "Use interactive state tokens (hover, focus, active) for user feedback"
        ]
    
    def analyze_generation_performance(self) -> Dict[str, Any]:
        """Analyze generation performance and provide insights."""
        if not self.generation_attempts:
            return {'message': 'No generation attempts recorded'}
        
        stats = {
            'total_prompts': len(self.generation_attempts),
            'total_attempts': sum(len(attempts) for attempts in self.generation_attempts.values()),
            'success_rate': 0,
            'avg_attempts_per_prompt': 0,
            'most_challenging_prompts': []
        }
        
        successful_prompts = 0
        challenging_prompts = []
        
        for prompt, attempts in self.generation_attempts.items():
            successful_attempts = [attempt for attempt in attempts if not attempt.startswith('FAILED:')]
            
            if successful_attempts:
                successful_prompts += 1
            
            if len(attempts) > 2:  # More than 2 attempts indicates challenges
                challenging_prompts.append({
                    'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt,
                    'attempts': len(attempts),
                    'failures': len([a for a in attempts if a.startswith('FAILED:')])
                })
        
        stats['success_rate'] = successful_prompts / len(self.generation_attempts)
        stats['avg_attempts_per_prompt'] = stats['total_attempts'] / len(self.generation_attempts)
        stats['most_challenging_prompts'] = sorted(challenging_prompts, key=lambda x: x['attempts'], reverse=True)[:5]
        
        return stats
    
    def clear_generation_history(self):
        """Clear generation attempt history."""
        self.generation_attempts.clear()
        print("🧹 Generation history cleared")
    
    def get_advanced_capabilities(self) -> Dict[str, bool]:
        """Get information about enabled advanced capabilities."""
        return {
            'advanced_prompting': self.enable_advanced_prompting,
            'prompt_orchestrator': self.prompt_orchestrator is not None,
            'context_manager': self.context_manager is not None,
            'token_optimization': self.context_manager is not None,
            'chain_of_thought': True,
            'reflection_prompting': True,
            'role_based_prompting': True,
            'quality_assurance': self.validator is not None,
            'iterative_refinement': True
        }
    
    def generate_component(self, prompt: str, context: Dict) -> str:
        """
        Override base generate_component to use advanced capabilities when available.
        Maintains backward compatibility while providing enhanced functionality.
        """
        if self.enable_advanced_prompting:
            try:
                # Use advanced generation
                code, metadata = self.generate_component_advanced(prompt, context)
                
                # Log generation insights
                if metadata.get('context_optimization'):
                    utilization = metadata['context_optimization']['token_budget']['utilization']
                    print(f"📊 Token utilization: {utilization:.1%}")
                
                return code
                
            except Exception as e:
                print(f"⚠️ Advanced generation failed, falling back to base generator: {e}")
                # Fallback to base implementation
                return super().generate_component(prompt, context)
        else:
            # Use base implementation
            return super().generate_component(prompt, context)


def create_advanced_generator(*args, **kwargs) -> AdvancedUIGenerator:
    """Factory function to create advanced generator with prompt orchestration."""
    return AdvancedUIGenerator(*args, **kwargs)