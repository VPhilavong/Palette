"""
Multi-Model LLM Orchestration System.
Intelligently orchestrates multiple LLM models to leverage their individual strengths
for different aspects of component generation.
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from openai import OpenAI

from ..errors import GenerationError
from ..errors.decorators import handle_errors, retry_on_error


class ModelCapability(Enum):
    """Capabilities that different models excel at."""
    CODE_GENERATION = "code_generation"
    DESIGN_ANALYSIS = "design_analysis"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    CREATIVE_DESIGN = "creative_design"
    TECHNICAL_WRITING = "technical_writing"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"


class ModelProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    # Could extend to other providers like Google, Cohere, etc.


class TaskType(Enum):
    """Types of tasks for model orchestration."""
    INITIAL_GENERATION = "initial_generation"
    CODE_REVIEW = "code_review"
    ACCESSIBILITY_CHECK = "accessibility_check"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DESIGN_ENHANCEMENT = "design_enhancement"
    TESTING_GENERATION = "testing_generation"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    ERROR_FIXING = "error_fixing"


class OrchestrationStrategy(Enum):
    """Strategies for model orchestration."""
    SEQUENTIAL = "sequential"  # One model after another
    PARALLEL = "parallel"     # Multiple models simultaneously
    COMPETITIVE = "competitive"  # Multiple models compete, best result wins
    COLLABORATIVE = "collaborative"  # Models work together on different aspects
    HIERARCHICAL = "hierarchical"  # Primary model with specialist assistants


@dataclass
class ModelSpec:
    """Specification for a model including its capabilities and configuration."""
    name: str
    provider: ModelProvider
    capabilities: List[ModelCapability]
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    max_tokens: int = 4000
    temperature: float = 0.7
    cost_per_token: float = 0.0  # Cost considerations
    latency_estimate: float = 1.0  # Relative latency
    quality_score: float = 0.8  # Overall quality rating
    specializations: List[str] = field(default_factory=list)


@dataclass
class TaskSpec:
    """Specification for a task that needs to be orchestrated."""
    task_type: TaskType
    description: str
    required_capabilities: List[ModelCapability]
    preferred_models: List[str] = field(default_factory=list)
    max_execution_time: float = 30.0
    quality_threshold: float = 0.7
    retry_attempts: int = 2


@dataclass
class ModelResponse:
    """Response from a model execution."""
    model_name: str
    task_type: TaskType
    content: str
    confidence: float
    execution_time: float
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class OrchestrationResult:
    """Result of model orchestration."""
    primary_result: str
    strategy_used: OrchestrationStrategy
    model_responses: List[ModelResponse]
    total_execution_time: float
    total_cost: float = 0.0
    quality_score: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiModelOrchestrator:
    """
    Orchestrates multiple LLM models to leverage their individual strengths
    for different aspects of component generation.
    """
    
    def __init__(self):
        self.models: Dict[str, ModelSpec] = {}
        self.clients: Dict[str, Union[OpenAI, anthropic.Anthropic]] = {}
        self.task_routing: Dict[TaskType, List[str]] = {}
        
        # Initialize model configurations
        self._initialize_model_specs()
        self._initialize_clients()
        self._setup_task_routing()
        
        # Execution tracking
        self.execution_history: List[OrchestrationResult] = []
        self.model_performance: Dict[str, Dict[str, float]] = {}
    
    def _initialize_model_specs(self):
        """Initialize specifications for different models."""
        
        # GPT-4o - Excellent for complex reasoning and code generation
        self.models["gpt-4o"] = ModelSpec(
            name="gpt-4o",
            provider=ModelProvider.OPENAI,
            capabilities=[
                ModelCapability.CODE_GENERATION,
                ModelCapability.ARCHITECTURE,
                ModelCapability.DEBUGGING,
                ModelCapability.REFACTORING,
                ModelCapability.TESTING
            ],
            strengths=[
                "Complex code generation",
                "System architecture",
                "Debugging complex issues",
                "Technical reasoning"
            ],
            weaknesses=[
                "Sometimes overly verbose",
                "Can be slower"
            ],
            max_tokens=4000,
            temperature=0.7,
            cost_per_token=0.00003,
            latency_estimate=2.0,
            quality_score=0.95,
            specializations=["React", "TypeScript", "Complex algorithms"]
        )
        
        # GPT-4o-mini - Fast and efficient for simpler tasks
        self.models["gpt-4o-mini"] = ModelSpec(
            name="gpt-4o-mini",
            provider=ModelProvider.OPENAI,
            capabilities=[
                ModelCapability.CODE_GENERATION,
                ModelCapability.TECHNICAL_WRITING,
                ModelCapability.REFACTORING
            ],
            strengths=[
                "Fast generation",
                "Cost effective",
                "Good for simple components",
                "Clean code style"
            ],
            weaknesses=[
                "Less sophisticated reasoning",
                "May miss edge cases"
            ],
            max_tokens=4000,
            temperature=0.7,
            cost_per_token=0.000003,
            latency_estimate=0.8,
            quality_score=0.85,
            specializations=["Simple components", "Utility functions", "Documentation"]
        )
        
        # Claude 3.5 Sonnet - Excellent for design and accessibility
        self.models["claude-3-5-sonnet-20241022"] = ModelSpec(
            name="claude-3-5-sonnet-20241022",
            provider=ModelProvider.ANTHROPIC,
            capabilities=[
                ModelCapability.DESIGN_ANALYSIS,
                ModelCapability.ACCESSIBILITY,
                ModelCapability.CREATIVE_DESIGN,
                ModelCapability.CODE_GENERATION,
                ModelCapability.TECHNICAL_WRITING
            ],
            strengths=[
                "Excellent design sense",
                "Strong accessibility knowledge",
                "Creative problem solving",
                "Clear technical writing"
            ],
            weaknesses=[
                "Can be conservative",
                "Sometimes less performant code"
            ],
            max_tokens=4000,
            temperature=0.7,
            cost_per_token=0.000015,
            latency_estimate=1.5,
            quality_score=0.92,
            specializations=["UI/UX design", "Accessibility", "User experience"]
        )
        
        # Claude 3 Haiku - Fast for simple tasks and reviews
        self.models["claude-3-haiku-20240307"] = ModelSpec(
            name="claude-3-haiku-20240307",
            provider=ModelProvider.ANTHROPIC,
            capabilities=[
                ModelCapability.CODE_GENERATION,
                ModelCapability.DEBUGGING,
                ModelCapability.TECHNICAL_WRITING
            ],
            strengths=[
                "Very fast",
                "Cost effective",
                "Good for reviews",
                "Concise responses"
            ],
            weaknesses=[
                "Less sophisticated analysis",
                "May miss subtle issues"
            ],
            max_tokens=4000,
            temperature=0.7,
            cost_per_token=0.00000025,
            latency_estimate=0.5,
            quality_score=0.8,
            specializations=["Code review", "Simple fixes", "Quick analysis"]
        )
    
    def _initialize_clients(self):
        """Initialize API clients for different providers."""
        
        # OpenAI client
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            try:
                self.clients["openai"] = OpenAI(api_key=openai_api_key)
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI client: {e}")
        
        # Anthropic client
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            try:
                self.clients["anthropic"] = anthropic.Anthropic(api_key=anthropic_api_key)
            except Exception as e:
                print(f"⚠️ Failed to initialize Anthropic client: {e}")
    
    def _setup_task_routing(self):
        """Setup default task routing to models based on their strengths."""
        
        self.task_routing = {
            TaskType.INITIAL_GENERATION: ["gpt-4o", "claude-3-5-sonnet-20241022"],
            TaskType.CODE_REVIEW: ["claude-3-haiku-20240307", "gpt-4o-mini"],
            TaskType.ACCESSIBILITY_CHECK: ["claude-3-5-sonnet-20241022"],
            TaskType.PERFORMANCE_OPTIMIZATION: ["gpt-4o"],
            TaskType.DESIGN_ENHANCEMENT: ["claude-3-5-sonnet-20241022"],
            TaskType.TESTING_GENERATION: ["gpt-4o", "gpt-4o-mini"],
            TaskType.DOCUMENTATION: ["claude-3-5-sonnet-20241022", "gpt-4o-mini"],
            TaskType.REFACTORING: ["gpt-4o", "claude-3-5-sonnet-20241022"],
            TaskType.ERROR_FIXING: ["gpt-4o", "claude-3-haiku-20240307"]
        }
    
    @handle_errors(reraise=True)
    async def orchestrate_generation(
        self,
        task_spec: TaskSpec,
        context: Dict[str, Any],
        strategy: OrchestrationStrategy = OrchestrationStrategy.SEQUENTIAL
    ) -> OrchestrationResult:
        """
        Orchestrate model execution for a given task.
        
        Args:
            task_spec: Specification of the task to execute
            context: Context information for the task
            strategy: Orchestration strategy to use
            
        Returns:
            OrchestrationResult with the best result and metadata
        """
        start_time = time.time()
        
        print(f"🎭 Orchestrating {task_spec.task_type.value} using {strategy.value} strategy")
        
        # Select models for the task
        selected_models = self._select_models_for_task(task_spec)
        
        if not selected_models:
            raise GenerationError(f"No suitable models found for task: {task_spec.task_type}")
        
        # Execute based on strategy
        if strategy == OrchestrationStrategy.SEQUENTIAL:
            result = await self._execute_sequential(task_spec, context, selected_models)
        elif strategy == OrchestrationStrategy.PARALLEL:
            result = await self._execute_parallel(task_spec, context, selected_models)
        elif strategy == OrchestrationStrategy.COMPETITIVE:
            result = await self._execute_competitive(task_spec, context, selected_models)
        elif strategy == OrchestrationStrategy.COLLABORATIVE:
            result = await self._execute_collaborative(task_spec, context, selected_models)
        elif strategy == OrchestrationStrategy.HIERARCHICAL:
            result = await self._execute_hierarchical(task_spec, context, selected_models)
        else:
            raise GenerationError(f"Unsupported orchestration strategy: {strategy}")
        
        # Calculate final metrics
        result.total_execution_time = time.time() - start_time
        result.strategy_used = strategy
        
        # Update performance tracking
        self._update_performance_tracking(result)
        
        # Store in history
        self.execution_history.append(result)
        
        print(f"✅ Orchestration completed in {result.total_execution_time:.2f}s with {len(result.model_responses)} model responses")
        
        return result
    
    def _select_models_for_task(self, task_spec: TaskSpec) -> List[str]:
        """Select the most appropriate models for a given task."""
        
        # Start with task routing defaults
        candidate_models = self.task_routing.get(task_spec.task_type, [])
        
        # Add preferred models if specified
        if task_spec.preferred_models:
            candidate_models.extend(task_spec.preferred_models)
        
        # Filter by required capabilities
        suitable_models = []
        for model_name in candidate_models:
            if model_name in self.models:
                model_spec = self.models[model_name]
                if any(cap in model_spec.capabilities for cap in task_spec.required_capabilities):
                    suitable_models.append(model_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in suitable_models:
            if model not in seen:
                seen.add(model)
                unique_models.append(model)
        
        # Sort by quality score and specialization match
        def model_score(model_name: str) -> float:
            spec = self.models[model_name]
            base_score = spec.quality_score
            
            # Bonus for capability match
            capability_match = sum(1 for cap in task_spec.required_capabilities 
                                 if cap in spec.capabilities)
            capability_bonus = capability_match * 0.1
            
            return base_score + capability_bonus
        
        unique_models.sort(key=model_score, reverse=True)
        
        return unique_models[:3]  # Limit to top 3 models
    
    async def _execute_sequential(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        models: List[str]
    ) -> OrchestrationResult:
        """Execute models sequentially, using each result to improve the next."""
        
        responses = []
        current_context = context.copy()
        best_result = ""
        
        for i, model_name in enumerate(models):
            print(f"🔄 Sequential execution step {i+1}/{len(models)}: {model_name}")
            
            # For subsequent models, include previous results in context
            if responses:
                current_context["previous_attempts"] = [
                    {
                        "model": resp.model_name,
                        "result": resp.content,
                        "confidence": resp.confidence
                    }
                    for resp in responses
                ]
            
            try:
                response = await self._execute_single_model(model_name, task_spec, current_context)
                responses.append(response)
                
                # Use the best result so far
                if not best_result or response.confidence > max(r.confidence for r in responses[:-1]):
                    best_result = response.content
                    
            except Exception as e:
                print(f"⚠️ Model {model_name} failed: {e}")
                error_response = ModelResponse(
                    model_name=model_name,
                    task_type=task_spec.task_type,
                    content="",
                    confidence=0.0,
                    execution_time=0.0,
                    success=False,
                    error=str(e)
                )
                responses.append(error_response)
        
        # Calculate overall quality
        successful_responses = [r for r in responses if r.success]
        quality_score = max(r.confidence for r in successful_responses) if successful_responses else 0.0
        confidence = sum(r.confidence for r in successful_responses) / len(successful_responses) if successful_responses else 0.0
        
        return OrchestrationResult(
            primary_result=best_result,
            strategy_used=OrchestrationStrategy.SEQUENTIAL,
            model_responses=responses,
            total_execution_time=sum(r.execution_time for r in responses),
            quality_score=quality_score,
            confidence=confidence
        )
    
    async def _execute_parallel(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        models: List[str]
    ) -> OrchestrationResult:
        """Execute multiple models in parallel and combine results."""
        
        print(f"⚡ Parallel execution with {len(models)} models")
        
        # Create tasks for parallel execution
        tasks = []
        for model_name in models:
            task = self._execute_single_model(model_name, task_spec, context)
            tasks.append(task)
        
        # Execute all tasks concurrently
        responses = []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_response = ModelResponse(
                    model_name=models[i],
                    task_type=task_spec.task_type,
                    content="",
                    confidence=0.0,
                    execution_time=0.0,
                    success=False,
                    error=str(result)
                )
                responses.append(error_response)
            else:
                responses.append(result)
        
        # Select best result based on confidence
        successful_responses = [r for r in responses if r.success]
        if not successful_responses:
            raise GenerationError("All parallel executions failed")
        
        best_response = max(successful_responses, key=lambda x: x.confidence)
        
        # Calculate metrics
        total_time = max(r.execution_time for r in responses)  # Parallel execution time
        quality_score = best_response.confidence
        confidence = sum(r.confidence for r in successful_responses) / len(successful_responses)
        
        return OrchestrationResult(
            primary_result=best_response.content,
            strategy_used=OrchestrationStrategy.PARALLEL,
            model_responses=responses,
            total_execution_time=total_time,
            quality_score=quality_score,
            confidence=confidence
        )
    
    async def _execute_competitive(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        models: List[str]
    ) -> OrchestrationResult:
        """Execute multiple models competitively and select the best result."""
        
        print(f"🏆 Competitive execution with {len(models)} models")
        
        # Execute in parallel (similar to parallel strategy)
        parallel_result = await self._execute_parallel(task_spec, context, models)
        
        # Add competitive scoring based on multiple criteria
        successful_responses = [r for r in parallel_result.model_responses if r.success]
        
        # Score each response on multiple dimensions
        scored_responses = []
        for response in successful_responses:
            model_spec = self.models[response.model_name]
            
            # Multi-dimensional scoring
            capability_score = len(set(task_spec.required_capabilities) & set(model_spec.capabilities)) / len(task_spec.required_capabilities)
            quality_score = model_spec.quality_score
            confidence_score = response.confidence
            speed_score = 1.0 / (response.execution_time + 0.1)  # Avoid division by zero
            
            # Weighted total score
            total_score = (
                confidence_score * 0.4 +
                capability_score * 0.3 +
                quality_score * 0.2 +
                speed_score * 0.1
            )
            
            scored_responses.append((response, total_score))
        
        # Select winner
        winner, best_score = max(scored_responses, key=lambda x: x[1])
        
        print(f"🏅 Winner: {winner.model_name} with score {best_score:.3f}")
        
        return OrchestrationResult(
            primary_result=winner.content,
            strategy_used=OrchestrationStrategy.COMPETITIVE,
            model_responses=parallel_result.model_responses,
            total_execution_time=parallel_result.total_execution_time,
            quality_score=best_score,
            confidence=winner.confidence,
            metadata={"winner": winner.model_name, "competition_score": best_score}
        )
    
    async def _execute_collaborative(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        models: List[str]
    ) -> OrchestrationResult:
        """Execute models collaboratively, with each handling different aspects."""
        
        print(f"🤝 Collaborative execution with {len(models)} models")
        
        responses = []
        
        # Assign different aspects to different models based on their strengths
        if len(models) >= 2:
            # First model: Initial generation
            print(f"📝 Initial generation: {models[0]}")
            initial_context = context.copy()
            initial_context["role"] = "Generate the initial component implementation"
            
            initial_response = await self._execute_single_model(models[0], task_spec, initial_context)
            responses.append(initial_response)
            
            if initial_response.success:
                # Second model: Enhancement and refinement
                print(f"✨ Enhancement: {models[1]}")
                enhancement_context = context.copy()
                enhancement_context["initial_code"] = initial_response.content
                enhancement_context["role"] = "Enhance and refine the initial implementation, focusing on design, accessibility, and best practices"
                
                enhanced_task = TaskSpec(
                    task_type=TaskType.DESIGN_ENHANCEMENT,
                    description=f"Enhance the initial implementation: {task_spec.description}",
                    required_capabilities=[ModelCapability.DESIGN_ANALYSIS, ModelCapability.ACCESSIBILITY]
                )
                
                enhancement_response = await self._execute_single_model(models[1], enhanced_task, enhancement_context)
                responses.append(enhancement_response)
                
                # Use enhanced result if successful
                final_result = enhancement_response.content if enhancement_response.success else initial_response.content
            else:
                final_result = ""
        else:
            # Fallback to sequential if not enough models
            return await self._execute_sequential(task_spec, context, models)
        
        # Calculate collaborative metrics
        total_time = sum(r.execution_time for r in responses)
        successful_responses = [r for r in responses if r.success]
        quality_score = sum(r.confidence for r in successful_responses) / len(successful_responses) if successful_responses else 0.0
        confidence = max(r.confidence for r in successful_responses) if successful_responses else 0.0
        
        return OrchestrationResult(
            primary_result=final_result,
            strategy_used=OrchestrationStrategy.COLLABORATIVE,
            model_responses=responses,
            total_execution_time=total_time,
            quality_score=quality_score,
            confidence=confidence,
            metadata={"collaboration_phases": len(responses)}
        )
    
    async def _execute_hierarchical(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        models: List[str]
    ) -> OrchestrationResult:
        """Execute with primary model and specialist assistants."""
        
        print(f"🏗️ Hierarchical execution: primary + {len(models)-1} assistants")
        
        responses = []
        
        # Primary model does the main generation
        primary_model = models[0]
        print(f"👑 Primary model: {primary_model}")
        
        primary_response = await self._execute_single_model(primary_model, task_spec, context)
        responses.append(primary_response)
        
        if not primary_response.success:
            raise GenerationError(f"Primary model {primary_model} failed")
        
        final_result = primary_response.content
        
        # Assistant models provide specialized feedback and improvements
        for assistant_model in models[1:]:
            print(f"🔧 Assistant model: {assistant_model}")
            
            assistant_context = context.copy()
            assistant_context["primary_result"] = primary_response.content
            assistant_context["role"] = f"Review and provide specialized improvements to the primary implementation"
            
            # Create specialized task based on model capabilities
            model_spec = self.models[assistant_model]
            if ModelCapability.ACCESSIBILITY in model_spec.capabilities:
                assistant_task = TaskSpec(
                    task_type=TaskType.ACCESSIBILITY_CHECK,
                    description=f"Review accessibility of: {task_spec.description}",
                    required_capabilities=[ModelCapability.ACCESSIBILITY]
                )
            elif ModelCapability.PERFORMANCE in model_spec.capabilities:
                assistant_task = TaskSpec(
                    task_type=TaskType.PERFORMANCE_OPTIMIZATION,
                    description=f"Optimize performance of: {task_spec.description}",
                    required_capabilities=[ModelCapability.PERFORMANCE]
                )
            else:
                assistant_task = TaskSpec(
                    task_type=TaskType.CODE_REVIEW,
                    description=f"Review and improve: {task_spec.description}",
                    required_capabilities=[ModelCapability.CODE_GENERATION]
                )
            
            try:
                assistant_response = await self._execute_single_model(assistant_model, assistant_task, assistant_context)
                responses.append(assistant_response)
                
                # If assistant provides improvements, incorporate them
                if assistant_response.success and assistant_response.confidence > 0.7:
                    final_result = assistant_response.content
                    
            except Exception as e:
                print(f"⚠️ Assistant model {assistant_model} failed: {e}")
        
        # Calculate hierarchical metrics
        total_time = sum(r.execution_time for r in responses)
        successful_responses = [r for r in responses if r.success]
        quality_score = primary_response.confidence + sum(r.confidence * 0.2 for r in responses[1:] if r.success)
        confidence = primary_response.confidence
        
        return OrchestrationResult(
            primary_result=final_result,
            strategy_used=OrchestrationStrategy.HIERARCHICAL,
            model_responses=responses,
            total_execution_time=total_time,
            quality_score=min(1.0, quality_score),
            confidence=confidence,
            metadata={"primary_model": primary_model, "assistants": len(models) - 1}
        )
    
    async def _execute_single_model(
        self, 
        model_name: str, 
        task_spec: TaskSpec, 
        context: Dict[str, Any]
    ) -> ModelResponse:
        """Execute a single model for a given task."""
        
        if model_name not in self.models:
            raise GenerationError(f"Unknown model: {model_name}")
        
        model_spec = self.models[model_name]
        start_time = time.time()
        
        try:
            # Prepare the prompt
            system_prompt, user_prompt = self._prepare_prompts(task_spec, context, model_spec)
            
            # Execute based on provider
            if model_spec.provider == ModelProvider.OPENAI:
                content, token_usage = await self._execute_openai_model(model_spec, system_prompt, user_prompt)
            elif model_spec.provider == ModelProvider.ANTHROPIC:
                content, token_usage = await self._execute_anthropic_model(model_spec, system_prompt, user_prompt)
            else:
                raise GenerationError(f"Unsupported provider: {model_spec.provider}")
            
            execution_time = time.time() - start_time
            
            # Calculate confidence based on various factors
            confidence = self._calculate_response_confidence(content, model_spec, task_spec)
            
            return ModelResponse(
                model_name=model_name,
                task_type=task_spec.task_type,
                content=content,
                confidence=confidence,
                execution_time=execution_time,
                token_usage=token_usage,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ModelResponse(
                model_name=model_name,
                task_type=task_spec.task_type,
                content="",
                confidence=0.0,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
    
    def _prepare_prompts(
        self, 
        task_spec: TaskSpec, 
        context: Dict[str, Any], 
        model_spec: ModelSpec
    ) -> Tuple[str, str]:
        """Prepare system and user prompts for the model."""
        
        # Base system prompt
        system_prompt = f"""You are an expert frontend developer specializing in React and TypeScript.
Task: {task_spec.description}
Task Type: {task_spec.task_type.value}

Your strengths include: {', '.join(model_spec.strengths)}
Focus on: {', '.join(model_spec.specializations)}

Guidelines:
- Generate clean, maintainable, and accessible code
- Follow React best practices and modern patterns
- Use TypeScript for type safety
- Consider performance and user experience
- Include proper error handling
"""
        
        # Add role-specific instructions
        role = context.get("role", "")
        if role:
            system_prompt += f"\nRole: {role}"
        
        # User prompt with context
        user_prompt_parts = [f"Request: {task_spec.description}"]
        
        # Add context information
        if "framework" in context:
            user_prompt_parts.append(f"Framework: {context['framework']}")
        
        if "styling_approach" in context:
            user_prompt_parts.append(f"Styling: {context['styling_approach']}")
        
        if "design_token_analysis" in context:
            tokens = context["design_token_analysis"]
            if tokens.get("specific_recommendations"):
                user_prompt_parts.append("Design Token Recommendations:")
                for rec in tokens["specific_recommendations"][:3]:  # Top 3
                    user_prompt_parts.append(f"- {rec['token_name']}: {rec['reasoning']}")
        
        if "asset_recommendations" in context:
            assets = context["asset_recommendations"]
            if assets.get("recommended_assets"):
                user_prompt_parts.append("Asset Recommendations:")
                for asset in assets["recommended_assets"][:3]:  # Top 3
                    user_prompt_parts.append(f"- {asset['name']} ({asset['type']}): {asset['reasoning']}")
        
        if "previous_attempts" in context:
            user_prompt_parts.append("Previous attempts to learn from:")
            for attempt in context["previous_attempts"][-2:]:  # Last 2 attempts
                user_prompt_parts.append(f"- {attempt['model']}: {attempt['result'][:100]}...")
        
        if "initial_code" in context:
            user_prompt_parts.append(f"Initial code to enhance:\n```tsx\n{context['initial_code']}\n```")
        
        if "primary_result" in context:
            user_prompt_parts.append(f"Primary implementation to review:\n```tsx\n{context['primary_result']}\n```")
        
        user_prompt = "\n\n".join(user_prompt_parts)
        
        return system_prompt, user_prompt
    
    async def _execute_openai_model(
        self, 
        model_spec: ModelSpec, 
        system_prompt: str, 
        user_prompt: str
    ) -> Tuple[str, Dict[str, int]]:
        """Execute OpenAI model."""
        
        client = self.clients.get("openai")
        if not client:
            raise GenerationError("OpenAI client not available")
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model_spec.name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=model_spec.max_tokens,
            temperature=model_spec.temperature
        )
        
        content = response.choices[0].message.content
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return content, token_usage
    
    async def _execute_anthropic_model(
        self, 
        model_spec: ModelSpec, 
        system_prompt: str, 
        user_prompt: str
    ) -> Tuple[str, Dict[str, int]]:
        """Execute Anthropic model."""
        
        client = self.clients.get("anthropic")
        if not client:
            raise GenerationError("Anthropic client not available")
        
        response = await asyncio.to_thread(
            client.messages.create,
            model=model_spec.name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=model_spec.max_tokens,
            temperature=model_spec.temperature
        )
        
        content = response.content[0].text
        token_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
        }
        
        return content, token_usage
    
    def _calculate_response_confidence(
        self, 
        content: str, 
        model_spec: ModelSpec, 
        task_spec: TaskSpec
    ) -> float:
        """Calculate confidence score for a model response."""
        
        confidence = model_spec.quality_score  # Base confidence from model quality
        
        # Adjust based on content quality indicators
        if content:
            # Check for code structure
            if "```" in content or "tsx" in content or "jsx" in content:
                confidence += 0.1
            
            # Check for TypeScript
            if "interface" in content or "type " in content or ": " in content:
                confidence += 0.05
            
            # Check for React patterns
            if "useState" in content or "useEffect" in content or "props" in content:
                confidence += 0.05
            
            # Check for accessibility
            if "aria-" in content or "role=" in content:
                confidence += 0.05
            
            # Check for proper error handling
            if "try" in content or "catch" in content or "Error" in content:
                confidence += 0.05
        
        return min(1.0, confidence)
    
    def _update_performance_tracking(self, result: OrchestrationResult):
        """Update performance tracking for models."""
        
        for response in result.model_responses:
            if response.model_name not in self.model_performance:
                self.model_performance[response.model_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "average_confidence": 0.0,
                    "average_execution_time": 0.0
                }
            
            perf = self.model_performance[response.model_name]
            perf["total_executions"] += 1
            
            if response.success:
                perf["successful_executions"] += 1
                
                # Update rolling averages
                n = perf["successful_executions"]
                perf["average_confidence"] = (perf["average_confidence"] * (n-1) + response.confidence) / n
                perf["average_execution_time"] = (perf["average_execution_time"] * (n-1) + response.execution_time) / n
    
    def get_model_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models."""
        
        stats = {}
        for model_name, perf in self.model_performance.items():
            success_rate = perf["successful_executions"] / perf["total_executions"] if perf["total_executions"] > 0 else 0
            
            stats[model_name] = {
                "success_rate": success_rate,
                "average_confidence": perf["average_confidence"],
                "average_execution_time": perf["average_execution_time"],
                "total_executions": perf["total_executions"]
            }
        
        return stats
    
    def recommend_strategy_for_task(self, task_spec: TaskSpec) -> OrchestrationStrategy:
        """Recommend the best orchestration strategy for a given task."""
        
        # Simple heuristics for strategy recommendation
        if task_spec.task_type in [TaskType.INITIAL_GENERATION, TaskType.REFACTORING]:
            if len(self._select_models_for_task(task_spec)) > 1:
                return OrchestrationStrategy.COMPETITIVE
            else:
                return OrchestrationStrategy.SEQUENTIAL
        
        elif task_spec.task_type in [TaskType.CODE_REVIEW, TaskType.ACCESSIBILITY_CHECK]:
            return OrchestrationStrategy.HIERARCHICAL
        
        elif task_spec.task_type == TaskType.DESIGN_ENHANCEMENT:
            return OrchestrationStrategy.COLLABORATIVE
        
        else:
            return OrchestrationStrategy.SEQUENTIAL  # Safe default
    
    def export_orchestration_analysis(self) -> Dict[str, Any]:
        """Export comprehensive orchestration analysis."""
        
        return {
            "total_orchestrations": len(self.execution_history),
            "strategies_used": {
                strategy.value: len([r for r in self.execution_history if r.strategy_used == strategy])
                for strategy in OrchestrationStrategy
            },
            "model_performance": self.get_model_performance_stats(),
            "average_quality_score": sum(r.quality_score for r in self.execution_history) / len(self.execution_history) if self.execution_history else 0,
            "average_execution_time": sum(r.total_execution_time for r in self.execution_history) / len(self.execution_history) if self.execution_history else 0,
            "available_models": list(self.models.keys()),
            "model_capabilities": {
                name: [cap.value for cap in spec.capabilities]
                for name, spec in self.models.items()
            }
        }


# Global instance
_multi_model_orchestrator_instance = None

def get_multi_model_orchestrator() -> MultiModelOrchestrator:
    """Get the global multi-model orchestrator instance."""
    global _multi_model_orchestrator_instance
    if _multi_model_orchestrator_instance is None:
        _multi_model_orchestrator_instance = MultiModelOrchestrator()
    return _multi_model_orchestrator_instance