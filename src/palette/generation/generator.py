import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple

import anthropic
from openai import OpenAI

from ..analysis.project_structure import ProjectStructureDetector
from ..intelligence import (
    AssetIntelligence,
    ComponentRelationshipEngine,
    IntentAnalyzer,
    ComponentReuseAnalyzer,
    GenerationStrategyEngine,
    GenerationStrategy,
    StrategyConfig,
)
from .openai_ui_library_optimizer import OpenAIUILibraryOptimizer, PromptComplexity
from ..quality import ComponentValidator, QualityReport
from ..quality.zero_fix_pipeline import ZeroFixPipeline
from ..utils.async_utils import safe_run_async
from .enhanced_prompts import EnhancedPromptBuilder
from .smart_context_injector import SmartComponentContextInjector, SmartContextConfig, ContextInjectionLevel
from .prompt_parser import PromptParser, extract_component_name_from_requirements
from .prompts import UIUXCopilotPromptBuilder


class UIGenerator:
    """Core UI generation logic using LLM APIs"""

    def __init__(
        self,
        model: str = None,
        project_path: str = None,
        enhanced_mode: bool = True,
        quality_assurance: bool = True,
    ):
        # Use environment variable or provided model or fallback
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.project_path = project_path
        self.quality_assurance = quality_assurance

        # Initialize prompt builder (enhanced or basic)
        if enhanced_mode and project_path:
            try:
                self.prompt_builder = EnhancedPromptBuilder()
                self.prompt_builder.initialize_project_analysis(project_path)
                
                # Initialize smart context injector
                self.context_injector = SmartComponentContextInjector(project_path)
                print("✅ Enhanced prompt engineering enabled with project analysis")
                print("✅ Smart context injection enabled")
            except Exception as e:
                print(f"⚠️ Enhanced mode failed, falling back to basic: {e}")
                self.prompt_builder = UIUXCopilotPromptBuilder()
                self.context_injector = None
        else:
            self.prompt_builder = UIUXCopilotPromptBuilder()
            self.context_injector = None

        # Initialize quality validator
        if quality_assurance and project_path:
            try:
                self.validator = ComponentValidator(project_path)
                print("✅ Quality assurance enabled")
            except Exception as e:
                print(f"⚠️ QA initialization failed: {e}")
                self.validator = None
        else:
            self.validator = None

        # Initialize prompt parser
        self.prompt_parser = PromptParser()

        # Initialize intelligence systems
        self.intent_analyzer = IntentAnalyzer()
        self.asset_intelligence = None
        self.component_mapper = None
        self.reuse_analyzer = None
        self.strategy_engine = None
        self.openai_optimizer = None

        if project_path:
            try:
                self.asset_intelligence = AssetIntelligence(project_path)
                self.component_mapper = ComponentRelationshipEngine(project_path)
                
                # Initialize component reuse systems
                self.reuse_analyzer = ComponentReuseAnalyzer(project_path)
                strategy_config = StrategyConfig(
                    reuse_threshold=0.90,
                    compose_threshold=0.75,
                    extend_threshold=0.60,
                    prefer_reuse=True,
                    prefer_composition=True
                )
                self.strategy_engine = GenerationStrategyEngine(strategy_config)
                self.strategy_engine.reuse_analyzer = self.reuse_analyzer
                
                # Initialize OpenAI UI library optimizer
                self.openai_optimizer = OpenAIUILibraryOptimizer(project_path)
                
                print("✅ Intelligence systems initialized (including component reuse analysis and OpenAI optimization)")
            except Exception as e:
                print(f"⚠️ Intelligence initialization failed: {e}")

        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None

        # Initialize project context
        self._project_context = None
        if project_path:
            self._analyze_project(project_path)
            # Auto-discover MCP servers based on project configuration
            self._auto_discover_mcp_servers(project_path)

        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

    def generate_component_with_reuse_analysis(self, prompt: str, context: Dict) -> str:
        """Generate component with intelligent reuse analysis (new autonomous approach)."""
        print("🧠 Analyzing component reuse opportunities...")
        
        # Step 1: Perform reuse analysis
        if self.reuse_analyzer and self.strategy_engine:
            try:
                reuse_analysis = safe_run_async(self.reuse_analyzer.analyze_reuse_opportunities(prompt))
                strategy_decision = self.strategy_engine.determine_strategy(
                    reuse_analysis, prompt, context
                )
                
                # Step 2: Handle strategy decision autonomously
                return self._execute_strategy_decision(strategy_decision, prompt, context, reuse_analysis)
                
            except Exception as e:
                print(f"⚠️ Reuse analysis failed, falling back to traditional generation: {e}")
                return self.generate_component_traditional(prompt, context)
        else:
            print("⚠️ Reuse systems not initialized, using traditional generation")
            return self.generate_component_traditional(prompt, context)

    def generate_component(self, prompt: str, context: Dict) -> str:
        """Generate component using intelligent reuse analysis by default."""
        return self.generate_component_with_reuse_analysis(prompt, context)

    def _execute_strategy_decision(self, strategy_decision, prompt: str, context: Dict, reuse_analysis) -> str:
        """Execute the decided strategy for component generation/reuse."""
        from ..intelligence import GenerationStrategy
        
        print(f"\n🎯 Executing {strategy_decision.strategy.value.upper()} strategy")
        print(f"   {strategy_decision.user_message}")
        
        if strategy_decision.strategy == GenerationStrategy.REUSE:
            return self._execute_reuse_strategy(strategy_decision, prompt, context)
        
        elif strategy_decision.strategy == GenerationStrategy.COMPOSE:
            return self._execute_compose_strategy(strategy_decision, prompt, context)
        
        elif strategy_decision.strategy == GenerationStrategy.EXTEND:
            return self._execute_extend_strategy(strategy_decision, prompt, context)
        
        else:  # GENERATE or GENERATE_FRESH
            return self._execute_generate_strategy(strategy_decision, prompt, context, reuse_analysis)

    def _execute_reuse_strategy(self, strategy_decision, prompt: str, context: Dict) -> str:
        """Execute REUSE strategy - return existing component usage."""
        component = strategy_decision.primary_components[0]
        
        # Return usage instructions and import statement
        result = f"""// Reusing existing {component.name} component
{chr(10).join(strategy_decision.import_statements)}

{strategy_decision.usage_example}

/*
✅ COMPONENT REUSED: {component.name}
• Zero code duplication
• Instant consistency with existing design
• Proven, tested component
• Path: {component.path}
*/"""
        
        return result

    def _execute_compose_strategy(self, strategy_decision, prompt: str, context: Dict) -> str:
        """Execute COMPOSE strategy - compose multiple existing components."""
        components = strategy_decision.primary_components
        component_names = [comp.name for comp in components]
        
        # Generate composition code using the template
        result = f"""// Composing existing components: {', '.join(component_names)}
{chr(10).join(strategy_decision.import_statements)}

{strategy_decision.usage_example}

/*
✅ COMPONENTS COMPOSED: {len(components)} components
• {chr(10).join(['• ' + name for name in component_names])}
• Leverages existing components
• Maintains design consistency
*/"""
        
        return result

    def _execute_extend_strategy(self, strategy_decision, prompt: str, context: Dict) -> str:
        """Execute EXTEND strategy - extend existing component."""
        base_component = strategy_decision.primary_components[0]
        modifications = strategy_decision.implementation_details.get('modifications_needed', [])
        
        # Use the extension template from the strategy decision
        extension_template = strategy_decision.implementation_details.get('usage_instructions', {}).get('code_pattern', '')
        
        if extension_template:
            result = extension_template
        else:
            # Fallback extension template
            result = f"""// Extending existing {base_component.name}
import {{ {base_component.name} }} from '{base_component.path.replace('.tsx', '').replace('.jsx', '')}';

interface Enhanced{base_component.name}Props {{
  // Add new props for extensions
  // Modifications: {', '.join(modifications)}
}}

const Enhanced{base_component.name}: React.FC<Enhanced{base_component.name}Props> = (props) => {{
  // Add extension logic here
  return <{base_component.name} {{...props}} />;
}};

export default Enhanced{base_component.name};"""

        result += f"""

/*
✅ COMPONENT EXTENDED: {base_component.name}
• Base component: {base_component.path}
• Modifications: {', '.join(modifications)}
• Preserves original functionality
*/"""
        
        return result

    def _execute_generate_strategy(self, strategy_decision, prompt: str, context: Dict, reuse_analysis) -> str:
        """Execute GENERATE strategy - generate new component with context using OpenAI optimization."""
        reference_components = strategy_decision.primary_components
        
        # Use OpenAI optimizer if available
        if self.openai_optimizer:
            try:
                print("🎯 Using OpenAI UI library optimizer for generation...")
                
                # Determine complexity based on context and reference components
                complexity = PromptComplexity.INTERMEDIATE  # Default
                if len(reference_components) > 2:
                    complexity = PromptComplexity.ADVANCED
                elif not reference_components:
                    complexity = PromptComplexity.SIMPLE
                
                # Get optimized prompt
                from ..utils.async_utils import safe_run_async
                optimized_prompt = safe_run_async(
                    self.openai_optimizer.optimize_prompt_for_library(
                        prompt, complexity=complexity
                    )
                )
                
                if optimized_prompt:
                    print(f"   Library: {optimized_prompt.library_context}")
                    print(f"   Complexity: {optimized_prompt.complexity_level.value}")
                    print(f"   Examples: {optimized_prompt.examples_count}")
                    
                    # Generate using optimized prompts
                    if self.model.startswith("gpt"):
                        generated_code = self._generate_with_openai(
                            optimized_prompt.system_prompt, 
                            optimized_prompt.user_prompt
                        )
                    else:
                        generated_code = self._generate_with_anthropic(
                            optimized_prompt.system_prompt,
                            optimized_prompt.user_prompt
                        )
                    
                    # Add optimization metadata
                    metadata = f"""/*
✅ COMPONENT GENERATED with OpenAI UI Library Optimization
• Library context: {optimized_prompt.library_context}
• Complexity: {optimized_prompt.complexity_level.value}
• Features: {', '.join(optimized_prompt.component_hints) if optimized_prompt.component_hints else 'standard'}
• Confidence: {optimized_prompt.confidence_score:.1%}
• Reference components: {', '.join(comp.name for comp in reference_components) if reference_components else 'none'}
*/

"""
                    return metadata + generated_code
                    
            except Exception as e:
                print(f"⚠️ OpenAI optimization failed, using fallback: {e}")
        
        # Fallback to traditional method if optimizer fails or unavailable
        if reference_components:
            reference_info = []
            for comp in reference_components:
                reference_info.append(f"- {comp.name}: {comp.path} (props: {', '.join(comp.props[:3])})")
            
            enhanced_prompt = f"""{prompt}

IMPORTANT: Use these existing components as reference patterns:
{chr(10).join(reference_info)}

Follow the established patterns, naming conventions, and styling approach used in these components."""
        else:
            enhanced_prompt = prompt
        
        # Generate using traditional method with enhanced context
        generated_code = self.generate_component_traditional(enhanced_prompt, context)
        
        # Add strategy metadata as comments
        if reference_components:
            metadata = f"""/*
✅ COMPONENT GENERATED with {len(reference_components)} reference patterns
• Reference components: {', '.join(comp.name for comp in reference_components)}
• Follows established project patterns
*/

"""
            generated_code = metadata + generated_code
        else:
            metadata = f"""/*
✅ FRESH COMPONENT GENERATED
• No existing patterns found
• Created with minimal context
*/

"""
            generated_code = metadata + generated_code
        
        return generated_code

    def generate_component_traditional(self, prompt: str, context: Dict) -> str:
        """Generate a React component from a prompt and project context (traditional approach)"""

        # Parse the prompt to understand requirements
        requirements = self.prompt_parser.parse(prompt)

        # Add parsed requirements to context for better generation
        context["parsed_requirements"] = {
            "component_type": requirements.component_type,
            "features": requirements.features,
            "styling": requirements.styling_requirements,
            "expected_name": extract_component_name_from_requirements(requirements),
        }

        # Build prompts using enhanced or basic builder
        if isinstance(self.prompt_builder, EnhancedPromptBuilder):
            # Use enhanced prompts with few-shot learning and RAG
            if hasattr(self.prompt_builder, 'build_composition_enhanced_prompt'):
                # Try composition-enhanced prompts first
                try:
                    system_prompt = safe_run_async(
                        self.prompt_builder.build_composition_enhanced_prompt(prompt, context)
                    )
                except Exception as e:
                    print(f"Warning: Composition-enhanced prompts failed: {e}")
                    system_prompt = self.prompt_builder.build_enhanced_system_prompt(
                        context, prompt
                    )
            else:
                system_prompt = self.prompt_builder.build_enhanced_system_prompt(
                    context, prompt
                )
            user_prompt = self.prompt_builder.build_rag_enhanced_user_prompt(
                prompt, context
            )
        else:
            # Use basic prompts
            system_prompt = self.prompt_builder.build_ui_system_prompt(context)
            user_prompt = self.prompt_builder.build_user_prompt(prompt, context)
        
        # Apply smart context injection if available
        if self.context_injector:
            try:
                # Configure context injection based on prompt complexity
                context_config = SmartContextConfig(
                    injection_level=ContextInjectionLevel.ADAPTIVE,
                    max_context_words=800,
                    relevance_threshold=0.5
                )
                
                # Inject smart context into the system prompt
                system_prompt = safe_run_async(
                    self.context_injector.inject_smart_context(
                        prompt, system_prompt, context_config
                    )
                )
                print("✅ Smart context injection applied")
            except Exception as e:
                print(f"⚠️ Smart context injection failed: {e}")

        # Choose API based on model
        if self.model.startswith("gpt"):
            component_code = self._generate_with_openai(system_prompt, user_prompt)
        elif self.model.startswith("claude"):
            component_code = self._generate_with_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

        # Add usage example to the component
        usage_example = self._generate_usage_example(component_code, prompt)
        return component_code + usage_example

    def generate_component_with_qa(
        self, prompt: str, context: Dict, target_path: str = None
    ) -> Tuple[str, QualityReport]:
        """Generate component with comprehensive quality assurance and intelligent reuse analysis."""
        print("🎨 Generating component with intelligent reuse analysis and quality assurance...")

        # Step 1: Generate initial component (now includes reuse analysis)
        component_code = self.generate_component(prompt, context)

        # Clean the response first
        component_code = self.clean_response(component_code)

        # Step 2: If QA is disabled, return without validation
        if not self.validator:
            print("⚠️ Quality assurance disabled, skipping validation")
            # Create dummy report
            from ..quality.validator import QualityReport, ValidationLevel

            dummy_report = QualityReport(
                score=75.0,
                issues=[],
                passed_checks=["Generation"],
                failed_checks=[],
                auto_fixes_applied=[],
                compilation_success=True,
                rendering_success=True,
                accessibility_score=75.0,
                performance_score=75.0,
            )
            return component_code, dummy_report

        # Step 3: Use Zero-Fix Pipeline for advanced validation
        print("🚀 Using Zero-Fix Pipeline for advanced quality assurance...")

        try:
            # Initialize Zero-Fix Pipeline (without MCP dependencies)
            zero_fix_pipeline = ZeroFixPipeline(
                project_path=self.project_path,
                mcp_client=None,  # No MCP since we removed it
            )

            # Run the pipeline with safe async handling
            pipeline_result = safe_run_async(
                zero_fix_pipeline.process(
                    component_code, context, target_path or "Component.tsx", prompt
                )
            )

            # Convert ZeroFixResult to QualityReport format
            quality_report = self._convert_zero_fix_to_quality_report(pipeline_result)

            # Display pipeline summary
            self._display_zero_fix_summary(pipeline_result)

            # Use the pipeline result as the final code
            final_code = pipeline_result.final_code

            # Step 4: Final formatting (after all fixes)
            print("🎨 Final formatting pass...")
            formatted_code = self.format_and_lint_code(
                final_code, self.project_path or os.getcwd()
            )

            return formatted_code, quality_report

        except Exception as e:
            print(f"⚠️ Zero-Fix Pipeline failed, falling back to traditional QA: {e}")
            # Fall through to traditional validation

        # Traditional validation
        target_file = target_path or "Component.tsx"
        refined_code, quality_report = self.validator.iterative_refinement(
            component_code, target_file, max_iterations=3
        )

        # Add design token validation
        if context.get("design_tokens"):
            uses_tokens, token_issues, token_score = (
                self.validator.validate_design_token_usage(
                    refined_code, context["design_tokens"]
                )
            )

            # Add design token score to report
            print(f"🎨 Design Token Usage: {token_score:.1f}%")

            if token_issues:
                from ..quality.validator import ValidationIssue, ValidationLevel

                for issue in token_issues:
                    quality_report.issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category="design_tokens",
                            message=issue,
                            suggestion="Use project-specific design tokens instead of generic colors",
                        )
                    )

            # Add to checks with score
            if uses_tokens:
                quality_report.passed_checks.append(
                    f"Design token usage ({token_score:.0f}%)"
                )
            else:
                quality_report.failed_checks.append(
                    f"Design token usage ({token_score:.0f}%)"
                )

            # Adjust overall score based on token usage (max 5 point impact)
            token_impact = (token_score / 100) * 5
            quality_report.score = min(100, quality_report.score + token_impact - 2.5)

        # Display quality summary
        self._display_quality_summary(quality_report)

        # Final formatting
        print("🎨 Final formatting pass...")
        formatted_code = self.format_and_lint_code(
            refined_code, self.project_path or os.getcwd()
        )

        return formatted_code, quality_report

    def _convert_zero_fix_to_quality_report(self, zero_fix_result):
        """Convert ZeroFixResult to QualityReport format for compatibility."""
        from ..quality.validator import QualityReport, ValidationLevel

        # Calculate overall score based on success and confidence
        if zero_fix_result.success:
            overall_score = zero_fix_result.confidence_score * 100
        else:
            overall_score = max(
                0,
                (
                    1
                    - zero_fix_result.final_issues
                    / max(1, zero_fix_result.original_issues)
                )
                * 50,
            )

        # Convert pipeline fixes to auto_fixes_applied format
        auto_fixes = zero_fix_result.openai_fixes + [
            f"Pipeline Stage {i+1}"
            for i in range(len(zero_fix_result.validation_reports))
        ]

        return QualityReport(
            score=overall_score,
            issues=[],  # Zero-fix pipeline handles issues internally
            passed_checks=["Zero-Fix Pipeline"] if zero_fix_result.success else [],
            failed_checks=[] if zero_fix_result.success else ["Zero-Fix Pipeline"],
            auto_fixes_applied=auto_fixes,
            compilation_success=zero_fix_result.final_issues == 0,
            rendering_success=zero_fix_result.success,
            accessibility_score=zero_fix_result.confidence_score * 100,
            performance_score=zero_fix_result.confidence_score * 100,
        )

    def _display_zero_fix_summary(self, pipeline_result):
        """Display Zero-Fix Pipeline summary."""
        print(f"\n🚀 Zero-Fix Pipeline Results:")
        print(f"Status: {'✅ SUCCESS' if pipeline_result.success else '❌ FAILED'}")
        print(f"Iterations: {pipeline_result.iterations}")
        print(f"Original Issues: {pipeline_result.original_issues}")
        print(f"Final Issues: {pipeline_result.final_issues}")
        print(f"Confidence Score: {pipeline_result.confidence_score:.2%}")

        if pipeline_result.openai_fixes:
            print(f"\n🔧 AI Fixes Applied: {len(pipeline_result.openai_fixes)}")
            for i, fix in enumerate(pipeline_result.openai_fixes[:3]):  # Show first 3
                print(f"  {i+1}. {fix}")
            if len(pipeline_result.openai_fixes) > 3:
                print(f"  ... and {len(pipeline_result.openai_fixes) - 3} more fixes")

        if pipeline_result.mcp_validations:
            print(f"\n🎨 MCP Validations: {len(pipeline_result.mcp_validations)}")

        if pipeline_result.validation_reports:
            print(f"📊 Validation Stages: {len(pipeline_result.validation_reports)}")

        if pipeline_result.error:
            print(f"❌ Error: {pipeline_result.error}")

    def _display_quality_summary(self, report: QualityReport):
        """Display quality assurance summary."""
        print(f"\n📊 Quality Report:")
        print(f"Overall Score: {report.score:.1f}/100")

        if report.compilation_success:
            print("✅ TypeScript compilation: PASSED")
        else:
            print("❌ TypeScript compilation: FAILED")

        if report.rendering_success:
            print("✅ Component rendering: PASSED")
        else:
            print("❌ Component rendering: FAILED")

        print(f"🛡️ Accessibility: {report.accessibility_score:.1f}/100")
        print(f"⚡ Performance: {report.performance_score:.1f}/100")

        if report.issues:
            print(f"\n⚠️ Issues Found: {len(report.issues)}")
            for issue in report.issues[:5]:  # Show first 5 issues
                level_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                emoji = level_emoji.get(issue.level.value, "•")
                print(f"  {emoji} {issue.category}: {issue.message}")

            if len(report.issues) > 5:
                print(f"  ... and {len(report.issues) - 5} more issues")

        if report.auto_fixes_applied:
            print(f"\n🔧 Auto-fixes Applied: {len(report.auto_fixes_applied)}")
            for fix in report.auto_fixes_applied:
                print(f"  ✅ {fix}")

    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using OpenAI API"""

        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _generate_with_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using Anthropic API"""

        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")

        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def clean_response(self, response: str) -> str:
        """Clean and extract code from LLM response"""

        # Remove markdown code blocks if present
        if "```" in response:
            # Find all code blocks
            parts = response.split("```")
            if len(parts) >= 3:
                # Take the content of the first code block (index 1)
                code_content = parts[1]

                # Remove language specifier from first line if present
                lines = code_content.split("\n")
                if lines and lines[0].strip() in [
                    "tsx",
                    "typescript",
                    "javascript",
                    "jsx",
                    "ts",
                    "js",
                ]:
                    lines = lines[1:]

                response = "\n".join(lines).strip()

        # Additional cleanup - remove any remaining markdown artifacts
        lines = response.split("\n")
        cleaned_lines = []
        for line in lines:
            # Skip lines that are pure markdown artifacts
            stripped = line.strip()
            if stripped in [
                "```tsx",
                "```typescript",
                "```javascript",
                "```jsx",
                "```ts",
                "```js",
                "```",
            ]:
                continue
            cleaned_lines.append(line)

        response = "\n".join(cleaned_lines)
        return response.strip()

    def generate_with_intelligence(self, prompt: str) -> Tuple[str, Dict]:
        """Generate component with full intelligence systems engaged."""
        print("\n🧠 Analyzing your request...")

        # Step 1: Analyze intent
        intent_context = self.intent_analyzer.analyze_intent(
            prompt, self._project_context
        )
        print(f"📊 {self.intent_analyzer.get_intent_summary(intent_context)}")

        # Step 2: Analyze assets if available
        asset_context = None
        asset_suggestions = []
        if self.asset_intelligence:
            print("\n📸 Scanning project assets...")
            asset_context = self.asset_intelligence.analyze_project_assets()
            asset_suggestions = self.asset_intelligence.suggest_assets_for_component(
                prompt, intent_context.primary_intent.value
            )

            if asset_suggestions:
                print(f"🎨 Found {len(asset_suggestions)} relevant assets")
                for suggestion in asset_suggestions[:3]:
                    if suggestion.suggested_asset:
                        print(
                            f"  • {suggestion.usage_context}: {suggestion.suggested_asset.name}"
                        )
                    else:
                        print(f"  • {suggestion.usage_context}: Using placeholder")

        # Step 3: Analyze component relationships
        relationship_context = None
        if self.component_mapper:
            print("\n🔗 Analyzing component relationships...")
            relationship_context = self.component_mapper.analyze_component_ecosystem(
                prompt, intent_context.primary_intent.value
            )
            summary = self.component_mapper.get_relationship_summary(
                relationship_context
            )
            if summary:
                print(f"📍 {summary}")

        # Step 4: Show clarifying questions if needed
        if (
            intent_context.suggested_clarifications
            and intent_context.confidence_score < 0.7
        ):
            print("\n❓ To better understand your needs, consider:")
            for i, question in enumerate(
                intent_context.suggested_clarifications[:3], 1
            ):
                print(f"   {i}. {question}")
            print("   (Proceeding with current understanding)")

        # Step 5: Generate with enhanced context
        print("\n🚀 Generating component with enhanced context...")

        # Build enhanced prompt with all intelligence
        enhanced_request = self._build_intelligent_request(
            prompt, intent_context, asset_context, relationship_context
        )

        # Generate the component
        result = self.generate_component(enhanced_request)

        # Step 6: Add intelligence metadata
        intelligence_data = {
            "intent": {
                "primary": intent_context.primary_intent.value,
                "goals": [g.value for g in intent_context.user_goals],
                "confidence": intent_context.confidence_score,
                "features": intent_context.key_features,
            },
            "assets": {
                "suggested": len(asset_suggestions),
                "used": sum(1 for s in asset_suggestions if s.suggested_asset),
            },
            "relationships": {
                "suggested_location": (
                    relationship_context.suggested_location
                    if relationship_context
                    else None
                ),
                "parent_components": (
                    [p.name for p in relationship_context.parent_layouts[:3]]
                    if relationship_context
                    else []
                ),
                "common_patterns": (
                    relationship_context.common_patterns[:3]
                    if relationship_context
                    else []
                ),
            },
            "next_steps": self._generate_next_steps(prompt, intent_context),
        }

        # Show next steps
        if intelligence_data["next_steps"]:
            print("\n💡 Suggested next steps:")
            for i, step in enumerate(intelligence_data["next_steps"][:3], 1):
                print(f"   {i}. {step}")

        return result, intelligence_data

    def _build_intelligent_request(
        self, prompt: str, intent_context, asset_context, relationship_context
    ) -> str:
        """Build an enhanced prompt with all intelligence insights."""
        enhanced_parts = [prompt]

        # Add implicit requirements
        if intent_context.implicit_requirements:
            enhanced_parts.append(
                "\nImplicit requirements detected: "
                + ", ".join(intent_context.implicit_requirements[:3])
            )

        # Add asset context
        if asset_context and asset_context.logos:
            enhanced_parts.append(
                f"\nProject has {len(asset_context.logos)} logo variations available"
            )

        if asset_context and asset_context.colors:
            color_list = list(asset_context.colors.items())[:5]
            enhanced_parts.append(
                "\nBrand colors detected: "
                + ", ".join(f"{name}: {value}" for name, value in color_list)
            )

        # Add relationship context
        if relationship_context and relationship_context.common_patterns:
            enhanced_parts.append(
                "\nCommon patterns in similar components: "
                + ", ".join(relationship_context.common_patterns[:2])
            )

        return "\n".join(enhanced_parts)

    def _generate_next_steps(self, prompt: str, intent_context) -> List[str]:
        """Generate intelligent next step suggestions."""
        next_steps = []

        if intent_context.primary_intent.value == "landing_page":
            next_steps.extend(
                [
                    "Create a features section to highlight key benefits",
                    "Add testimonials for social proof",
                    "Build a contact form for lead generation",
                ]
            )
        elif intent_context.primary_intent.value == "e_commerce":
            if "pricing" in prompt.lower():
                next_steps.extend(
                    [
                        "Add a comparison table for detailed feature breakdown",
                        "Create a FAQ section to address common questions",
                        "Build testimonials to increase trust",
                    ]
                )
            elif "product" in prompt.lower():
                next_steps.extend(
                    [
                        "Add product filtering and sorting",
                        "Create a product detail modal or page",
                        "Build a shopping cart component",
                    ]
                )
        elif intent_context.primary_intent.value == "dashboard":
            next_steps.extend(
                [
                    "Add data visualization components",
                    "Create filter controls for the data",
                    "Build an export functionality",
                ]
            )

        return next_steps

    def _generate_usage_example(self, component_code: str, prompt: str) -> str:
        """Generate a usage example for the component based on its props."""
        import re

        # Extract component name
        component_match = re.search(
            r"(?:export\s+default\s+)?(?:function|const)\s+(\w+)", component_code
        )
        component_name = component_match.group(1) if component_match else "Component"

        # Try to find interface or type definition with improved regex
        # Handle multiline interfaces and nested types
        props_match = re.search(
            r"interface\s+\w*Props\s*{([^}]+(?:{[^}]*}[^}]*)*)}",
            component_code,
            re.DOTALL,
        )
        if not props_match:
            # Try type alias format
            props_match = re.search(
                r"type\s+\w*Props\s*=\s*{([^}]+(?:{[^}]*}[^}]*)*)}",
                component_code,
                re.DOTALL,
            )

        prompt_lower = prompt.lower()

        # Generate specific examples based on component type
        if "dashboard header" in prompt_lower:
            return f"""

// Usage example:
<{component_name}
  breadcrumbs={{[
    {{ label: 'Home', href: '/' }},
    {{ label: 'Dashboard' }}
  ]}}
  userName="John Doe"
  notificationCount={{3}}
  avatarSrc="/images/avatar.jpg"
/>"""
        elif "product card grid" in prompt_lower or "product grid" in prompt_lower:
            return f"""

// Usage example:
const products = [
  {{ id: 1, name: 'Product 1', price: 29.99, image: '/product1.jpg', rating: 4.5, discount: 10 }},
  {{ id: 2, name: 'Product 2', price: 49.99, image: '/product2.jpg', rating: 5, discount: 0 }},
  // ... more products
];

<{component_name} products={{products}} />"""
        elif props_match:
            props_content = props_match.group(1)
            # Parse props more accurately
            props_info = self._parse_typescript_props(props_content)

            if props_info:
                # Generate example with proper values
                props_examples = []
                for prop_name, prop_type, is_optional in props_info:
                    example_value = self._generate_prop_example_value(
                        prop_name, prop_type
                    )
                    if not is_optional or len(props_examples) < 3:  # Show first 3 props
                        props_examples.append(f"  {prop_name}={{{example_value}}}")

                if props_examples:
                    props_str = "\n".join(props_examples)
                    return f"""

// Usage example:
<{component_name}
{props_str}
/>"""

        return f"""

// Usage example:
<{component_name} />"""

    def _parse_typescript_props(
        self, props_content: str
    ) -> List[Tuple[str, str, bool]]:
        """Parse TypeScript props to extract name, type, and optionality."""
        import re

        props = []
        # Clean up the content
        props_content = props_content.strip()

        # Split by semicolon or newline, handling nested objects
        lines = re.split(r"[;\n]", props_content)

        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Match prop pattern: propName?: type or propName: type
            match = re.match(r"^\s*(\w+)\s*(\?)?:\s*(.+)$", line)
            if match:
                prop_name = match.group(1)
                is_optional = bool(match.group(2))
                prop_type = match.group(3).strip()

                # Clean up the type (remove trailing semicolons, etc.)
                prop_type = prop_type.rstrip(";,")

                props.append((prop_name, prop_type, is_optional))

        return props

    def _generate_prop_example_value(self, prop_name: str, prop_type: str) -> str:
        """Generate an example value based on prop name and type."""
        prop_name_lower = prop_name.lower()
        prop_type_lower = prop_type.lower()

        # Common prop patterns
        if "onclick" in prop_name_lower or "onchange" in prop_name_lower:
            return '() => console.log("' + prop_name + '")'
        elif "children" in prop_name_lower:
            return '"Example content"'
        elif "classname" in prop_name_lower:
            return '"custom-class"'
        elif "src" in prop_name_lower or "url" in prop_name_lower:
            return '"/example-image.jpg"'
        elif "href" in prop_name_lower:
            return '"#"'
        elif "id" in prop_name_lower:
            return '"example-id"'
        elif (
            "name" in prop_name_lower
            or "title" in prop_name_lower
            or "label" in prop_name_lower
        ):
            return '"Example ' + prop_name + '"'
        elif "count" in prop_name_lower:
            return "5"
        elif "price" in prop_name_lower or "amount" in prop_name_lower:
            return "29.99"
        elif "rating" in prop_name_lower:
            return "4.5"
        elif "discount" in prop_name_lower or "percentage" in prop_name_lower:
            return "10"

        # Type-based defaults
        if "string" in prop_type_lower:
            return '"example"'
        elif "number" in prop_type_lower:
            return "42"
        elif "boolean" in prop_type_lower:
            return "true"
        elif "array" in prop_type_lower or prop_type.startswith("["):
            return "[]"
        elif prop_type.startswith("{") or "object" in prop_type_lower:
            return "{}"
        elif "=>" in prop_type or "function" in prop_type_lower:
            return "() => {}"
        else:
            # Default fallback
            return "/* " + prop_type + " */"

    def validate_component(self, code: str) -> bool:
        """Basic validation of generated component code"""

        # Check for basic React component structure
        required_patterns = [
            "export",  # Should export the component
            "return",  # Should have a return statement
            "<",  # Should contain JSX
        ]

        for pattern in required_patterns:
            if pattern not in code:
                return False

        # Check for common syntax issues
        if code.count("(") != code.count(")"):
            return False

        if code.count("{") != code.count("}"):
            return False

        return True

    def format_and_lint_code(self, code: str, project_path: str = None) -> str:
        """Format and lint generated code using Prettier and ESLint"""

        # Clean the code first
        cleaned_code = self.clean_response(code)

        # Try to format with Prettier
        formatted_code = self._format_with_prettier(cleaned_code, project_path)

        # Try to lint with ESLint if available
        linted_code = self._lint_with_eslint(formatted_code, project_path)

        return linted_code

    def _format_with_prettier(self, code: str, project_path: str = None) -> str:
        """Format code using project's own Prettier if available"""

        if not project_path:
            return code

        try:
            # Check if Prettier is available in the project
            if not self._is_prettier_available(project_path):
                print("Info: Prettier not found in project, skipping formatting")
                return code

            # Write code to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tsx", delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Try to run Prettier using the project's own installation
            prettier_config = self._find_prettier_config(project_path)
            prettier_cmd = ["npx", "prettier", "--write", temp_file_path]

            # Add config file if found
            if prettier_config:
                prettier_cmd.extend(["--config", prettier_config])
            else:
                # Use default options for TypeScript/React
                prettier_cmd.extend(
                    [
                        "--parser",
                        "typescript",
                        "--single-quote",
                        "--trailing-comma",
                        "es5",
                        "--tab-width",
                        "2",
                        "--semi",
                    ]
                )

            # Run Prettier in the project directory to use project's dependencies
            result = subprocess.run(
                prettier_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_path,
            )

            if result.returncode == 0:
                # Read the formatted code
                with open(temp_file_path, "r") as f:
                    formatted_code = f.read()

                # Clean up temp file
                os.unlink(temp_file_path)

                return formatted_code
            else:
                # Prettier failed, clean up and return original
                os.unlink(temp_file_path)
                print(f"Info: Prettier formatting skipped: {result.stderr}")
                return code

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Clean up temp file if it exists
            if "temp_file_path" in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            if isinstance(e, FileNotFoundError):
                print("Info: Prettier not available, skipping formatting")
            else:
                print(f"Info: Prettier formatting skipped: {e}")

            return code

    def _lint_with_eslint(self, code: str, project_path: str = None) -> str:
        """Lint code using project's own ESLint if available"""

        if not project_path:
            return code

        try:
            # Check if ESLint is available in the project
            if not self._is_eslint_available(project_path):
                print("Info: ESLint not found in project, skipping linting")
                return code

            # Write code to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tsx", delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Try to run ESLint with auto-fix using project's own installation
            eslint_config = self._find_eslint_config(project_path)
            eslint_cmd = ["npx", "eslint", "--fix", temp_file_path]

            # Add config file if found
            if eslint_config:
                eslint_cmd.extend(["--config", eslint_config])

            # Run ESLint in the project directory
            result = subprocess.run(
                eslint_cmd, capture_output=True, text=True, timeout=10, cwd=project_path
            )

            # ESLint returns 0 for no issues, 1 for warnings/errors
            # We only proceed if it's 0 (no issues) or 1 (fixed issues)
            if result.returncode in [0, 1]:
                # Read the potentially fixed code
                with open(temp_file_path, "r") as f:
                    linted_code = f.read()

                # Clean up temp file
                os.unlink(temp_file_path)

                return linted_code
            else:
                # ESLint failed, clean up and return original
                os.unlink(temp_file_path)
                print(f"Info: ESLint linting skipped: {result.stderr}")
                return code

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Clean up temp file if it exists
            if "temp_file_path" in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            if isinstance(e, FileNotFoundError):
                print("Info: ESLint not available, skipping linting")
            else:
                print(f"Info: ESLint linting skipped: {e}")

            return code

    def _find_prettier_config(self, project_path: str = None) -> Optional[str]:
        """Find Prettier configuration file"""

        if not project_path:
            return None

        config_files = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.js",
            "prettier.config.js",
            ".prettierrc.yaml",
            ".prettierrc.yml",
        ]

        for config_file in config_files:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                return config_path

        return None

    def _find_eslint_config(self, project_path: str = None) -> Optional[str]:
        """Find ESLint configuration file"""

        if not project_path:
            return None

        config_files = [
            ".eslintrc",
            ".eslintrc.json",
            ".eslintrc.js",
            ".eslintrc.yaml",
            ".eslintrc.yml",
            "eslint.config.js",
        ]

        for config_file in config_files:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                return config_path

        return None

    def _is_prettier_available(self, project_path: str) -> bool:
        """Check if Prettier is available in the project"""

        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            return False

        try:
            with open(package_json_path, "r") as f:
                import json

                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check if prettier is in dependencies
                return "prettier" in dependencies
        except (json.JSONDecodeError, Exception):
            return False

    def _is_eslint_available(self, project_path: str) -> bool:
        """Check if ESLint is available in the project"""

        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            return False

        try:
            with open(package_json_path, "r") as f:
                import json

                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check if eslint is in dependencies
                return "eslint" in dependencies
        except (json.JSONDecodeError, Exception):
            return False

    @property
    def project_context(self) -> Dict:
        """Get project analysis context."""
        return self._project_context or {}

    def _analyze_project(self, project_path: str):
        """Analyze project structure and patterns."""
        from ..analysis.context import ProjectAnalyzer

        try:
            analyzer = ProjectAnalyzer()
            self._project_context = analyzer.analyze_project(project_path)
        except Exception as e:
            print(f"⚠️ Project analysis failed: {e}")
            # Use intelligent fallback with basic framework detection
            fallback_framework = self._detect_framework_fallback(project_path)
            self._project_context = {
                "framework": fallback_framework,
                "styling": "tailwind",
                "component_library": "none",
                "typescript": True,
                "project_path": project_path,
            }

    def _detect_framework_fallback(self, project_path: str) -> str:
        """Basic framework detection for fallback scenarios."""
        import json
        import os

        # Check for Next.js first
        next_config_files = ["next.config.js", "next.config.ts", "next.config.mjs"]
        if any(
            os.path.exists(os.path.join(project_path, config))
            for config in next_config_files
        ):
            return "next.js"

        # Check package.json for framework dependencies
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check for framework-specific dependencies
                if "next" in dependencies:
                    return "next.js"
                elif (
                    "@remix-run/dev" in dependencies
                    or "@remix-run/node" in dependencies
                ):
                    return "remix"
                elif "vite" in dependencies:
                    return "vite"
                elif "react" in dependencies:
                    return "react"
            except Exception:
                pass

        # Check for Vite config
        if os.path.exists(
            os.path.join(project_path, "vite.config.js")
        ) or os.path.exists(os.path.join(project_path, "vite.config.ts")):
            return "vite"

        # Check for Remix config
        if os.path.exists(os.path.join(project_path, "remix.config.js")):
            return "remix"

        # Default to react if nothing else is detected
        return "react"

    def _detect_generation_type(self, prompt: str) -> str:
        """Detect generation type from prompt."""
        prompt_lower = prompt.lower()

        # Check for multi-file patterns
        if any(
            word in prompt_lower for word in ["multi", "multiple", "files", "separate"]
        ):
            return "multi"

        # Check for page patterns
        if any(word in prompt_lower for word in ["page", "route", "screen"]):
            return "page"

        # Check for feature patterns
        if any(word in prompt_lower for word in ["feature", "module", "system"]):
            return "feature"

        # Check for utility patterns
        if any(word in prompt_lower for word in ["util", "helper", "function"]):
            return "utils"

        # Check for hook patterns
        if any(word in prompt_lower for word in ["hook", "use"]):
            return "hooks"

        # Default to single component
        return "single"

    def generate(self, request) -> Dict[str, str]:
        """Generate component(s) based on a GenerationRequest."""
        # Convert request to context format
        context = {
            "framework": request.framework.value,
            "styling": request.styling.value,
            "component_library": request.component_library.value,
            "typescript": True,
            "project_path": self.project_path,
        }

        # Add project context if available
        if self._project_context:
            context.update(self._project_context)

        # Generate the component
        if hasattr(self, "validator") and self.validator and self.quality_assurance:
            component_code, quality_report = self.generate_component_with_qa(
                request.prompt, context, target_path="Component.tsx"
            )
        else:
            component_code = self.generate_component(request.prompt, context)

        # Determine the correct file path using smart project structure detection
        file_path = self._determine_file_path_smart(request)

        # Return in the expected format
        return {file_path: component_code}

    def _determine_file_path_smart(self, request) -> str:
        """Use ProjectStructureDetector to determine the correct file path."""
        if not self.project_path:
            # Fallback to current directory if no project path
            project_path = os.getcwd()
        else:
            project_path = self.project_path

        try:
            detector = ProjectStructureDetector(project_path)
            return detector.generate_file_path(request.prompt)
        except Exception as e:
            print(f"⚠️ Smart path detection failed: {e}")
            # Fallback to simple component naming
            return self._fallback_file_path(request.prompt)

    def _fallback_file_path(self, prompt: str) -> str:
        """Fallback file path generation when smart detection fails."""
        prompt_lower = prompt.lower()

        # Check compound types first for better accuracy
        if "product card grid" in prompt_lower or "product grid" in prompt_lower:
            name = "ProductCardGrid"
        elif "dashboard header" in prompt_lower:
            name = "DashboardHeader"
        elif "pricing section" in prompt_lower or "pricing tier" in prompt_lower:
            name = "PricingSection"
        elif "hero" in prompt_lower:
            name = "HeroSection"
        elif "pricing" in prompt_lower:
            name = "PricingSection"
        elif "nav" in prompt_lower:
            name = "Navigation"
        elif "card" in prompt_lower:
            name = "Card"
        elif "button" in prompt_lower:
            name = "Button"
        else:
            name = "Component"

        # Default to components directory with TypeScript extension
        return f"components/{name}.tsx"

    def _auto_discover_mcp_servers(self, project_path: str):
        """Auto-discover and configure MCP servers based on project setup."""
        # MCP support has been removed in favor of local knowledge base
        # Initialize empty discovery results
        self._mcp_discovery = {"discovered": [], "enabled": []}
