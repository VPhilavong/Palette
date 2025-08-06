"""
Modular generator implementation using dependency injection.
Implements the IGenerator interface with better separation of concerns.
"""

import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from ..interfaces import (
    IGenerator, IAnalyzer, IValidator, IPromptBuilder, IMCPClient,
    GenerationRequest, GenerationResult, GeneratedFile,
    AnalysisResult, ValidationResult
)
from ..interfaces.generator import GenerationType
from .prompts import UIUXCopilotPromptBuilder
from .enhanced_prompts import EnhancedPromptBuilder


class ModularGenerator(IGenerator):
    """
    Modular implementation of component generator.
    Uses dependency injection for all dependencies.
    """
    
    def __init__(
        self,
        analyzer: IAnalyzer,
        prompt_builder: Optional[IPromptBuilder] = None,
        validator: Optional[IValidator] = None,
        mcp_client: Optional[IMCPClient] = None,
        model: Optional[str] = None
    ):
        # Injected dependencies
        self.analyzer = analyzer
        self.prompt_builder = prompt_builder or self._create_default_prompt_builder()
        self.validator = validator
        self.mcp_client = mcp_client
        
        # Configuration
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self._init_api_clients()
        
        # Intelligence components (optional)
        self.intent_analyzer = None
        self.asset_intelligence = None
        self.component_mapper = None
        self._init_intelligence_components()
    
    def _create_default_prompt_builder(self) -> IPromptBuilder:
        """Create default prompt builder based on environment."""
        enhanced_mode = os.getenv("PALETTE_ENHANCED_MODE", "true").lower() == "true"
        
        if enhanced_mode:
            try:
                return EnhancedPromptBuilder()
            except Exception:
                pass
        
        return UIUXCopilotPromptBuilder()
    
    def _init_api_clients(self):
        """Initialize API clients based on available keys."""
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                print("Warning: OpenAI client not available")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except ImportError:
                print("Warning: Anthropic client not available")
    
    def _init_intelligence_components(self):
        """Initialize optional intelligence components."""
        try:
            from ..intelligence import IntentAnalyzer, AssetIntelligence, ComponentRelationshipEngine
            self.intent_analyzer = IntentAnalyzer()
            
            # These need project path, will initialize on first use
            self.asset_intelligence = None
            self.component_mapper = None
        except ImportError:
            print("Info: Intelligence components not available")
    
    def generate(self, request: GenerationRequest, analysis: AnalysisResult) -> GenerationResult:
        """
        Generate components based on the request and project analysis.
        
        Args:
            request: Generation request with prompt and options
            analysis: Project analysis result
            
        Returns:
            GenerationResult with generated files and metadata
        """
        try:
            # Build prompts
            system_prompt = self.prompt_builder.build_system_prompt(self._build_context(analysis))
            user_prompt = self.prompt_builder.build_user_prompt(request, analysis)
            
            # Add few-shot examples if available
            few_shot = self.prompt_builder.build_few_shot_examples(request, analysis)
            if few_shot:
                system_prompt = f"{system_prompt}\n\n{few_shot}"
            
            # Generate with appropriate API
            raw_response = self._call_llm(system_prompt, user_prompt)
            
            # Parse response into files
            files = self._parse_response(raw_response, request)
            
            # Create result
            result = GenerationResult(
                files=files,
                success=True,
                imports_used=self._extract_imports(raw_response),
                components_reused=self._extract_reused_components(raw_response, analysis)
            )
            
            # Set main component
            if files:
                result.main_component = files[0].path
            
            # Validate if validator available
            if self.validator and files:
                for file in files:
                    validation = self.validator.validate(file.content, file.path)
                    if not validation.passed:
                        result.metadata["validation_issues"] = validation.issues
            
            return result
            
        except Exception as e:
            return GenerationResult(
                files=[],
                success=False,
                error=str(e)
            )
    
    def generate_with_intelligence(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate components using full intelligence pipeline.
        
        Args:
            request: Generation request
            
        Returns:
            GenerationResult with enhanced generation
        """
        try:
            # Analyze project if not provided
            project_path = request.context.get("project_path", os.getcwd())
            analysis = self.analyzer.analyze(project_path)
            
            # Analyze intent if available
            if self.intent_analyzer:
                intent_context = self.intent_analyzer.analyze(request.prompt)
                request = request.with_context(intent_context=intent_context.dict())
            
            # Initialize project-specific intelligence
            if project_path and not self.asset_intelligence:
                try:
                    from ..intelligence import AssetIntelligence, ComponentRelationshipEngine
                    self.asset_intelligence = AssetIntelligence(project_path)
                    self.component_mapper = ComponentRelationshipEngine(project_path)
                except Exception as e:
                    print(f"Warning: Could not initialize intelligence: {e}")
            
            # Get asset suggestions
            if self.asset_intelligence:
                assets = self.asset_intelligence.suggest_assets(request.prompt)
                request = request.with_context(suggested_assets=assets)
            
            # Get component relationships
            if self.component_mapper and analysis.components:
                relationships = self.component_mapper.analyze_relationships(
                    request.prompt, 
                    analysis.components
                )
                request = request.with_context(component_relationships=relationships)
            
            # Generate with enhanced context
            return self.generate(request, analysis)
            
        except Exception as e:
            return GenerationResult(
                files=[],
                success=False,
                error=f"Intelligence generation failed: {str(e)}"
            )
    
    def supports_model(self, model: str) -> bool:
        """Check if the generator supports a specific model."""
        supported_models = set()
        
        if self.openai_client:
            supported_models.update([
                "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
                "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
            ])
        
        if self.anthropic_client:
            supported_models.update([
                "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
                "claude-2.1", "claude-2", "claude-instant"
            ])
        
        return model in supported_models
    
    def _build_context(self, analysis: AnalysisResult) -> Dict[str, Any]:
        """Build context dictionary from analysis result."""
        return {
            "framework": analysis.project_structure.framework,
            "styling": analysis.project_structure.styling,
            "component_library": analysis.project_structure.component_library,
            "design_tokens": analysis.design_tokens.__dict__,
            "available_imports": analysis.available_imports,
            "component_patterns": analysis.component_patterns,
        }
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the appropriate LLM API."""
        if self.model.startswith("gpt") and self.openai_client:
            return self._call_openai(system_prompt, user_prompt)
        elif self.model.startswith("claude") and self.anthropic_client:
            return self._call_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"No API client available for model: {self.model}")
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""
        response = self.anthropic_client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=4000
        )
        return response.content[0].text
    
    def _parse_response(self, response: str, request: GenerationRequest) -> List[GeneratedFile]:
        """Parse LLM response into generated files."""
        files = []
        
        # Extract code blocks
        import re
        code_blocks = re.findall(r'```(?:tsx?|jsx?|typescript|javascript)\n(.*?)```', response, re.DOTALL)
        
        if code_blocks:
            # Determine file name
            component_name = self._extract_component_name(code_blocks[0])
            file_ext = ".tsx" if "typescript" in response.lower() else ".jsx"
            file_path = f"{component_name}{file_ext}"
            
            # Create main component file
            files.append(GeneratedFile(
                path=file_path,
                content=code_blocks[0].strip(),
                file_type="component",
                description=f"Main {component_name} component"
            ))
            
            # Look for additional files (tests, styles, etc.)
            for i, block in enumerate(code_blocks[1:], 1):
                if "test" in response[response.find(code_blocks[i-1]):response.find(block)].lower():
                    files.append(GeneratedFile(
                        path=f"{component_name}.test{file_ext}",
                        content=block.strip(),
                        file_type="test"
                    ))
                elif "style" in response[response.find(code_blocks[i-1]):response.find(block)].lower():
                    files.append(GeneratedFile(
                        path=f"{component_name}.module.css",
                        content=block.strip(),
                        file_type="style"
                    ))
        
        return files
    
    def _extract_component_name(self, code: str) -> str:
        """Extract component name from code."""
        import re
        
        # Try to find component name from various patterns
        patterns = [
            r'export\s+default\s+function\s+(\w+)',
            r'export\s+function\s+(\w+)',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'function\s+(\w+)\s*\([^)]*\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                return match.group(1)
        
        # Fallback
        return "Component"
    
    def _extract_imports(self, response: str) -> List[str]:
        """Extract import statements used in the response."""
        import re
        imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"\n]+)[\'"]', response)
        return list(set(imports))
    
    def _extract_reused_components(self, response: str, analysis: AnalysisResult) -> List[str]:
        """Extract which existing components were reused."""
        reused = []
        
        # Check for imports of existing components
        for component in analysis.components:
            if component.name in response and component.import_path in response:
                reused.append(component.name)
        
        return reused