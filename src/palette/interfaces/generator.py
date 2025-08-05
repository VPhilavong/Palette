"""
Generator interface and related data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .analyzer import AnalysisResult


class GenerationType(Enum):
    """Type of generation requested."""
    SINGLE_COMPONENT = "single"
    MULTI_FILE = "multi"
    PAGE = "page"
    FEATURE = "feature"
    HOOK = "hook"
    UTILITY = "utility"


@dataclass
class GenerationRequest:
    """Request for component generation."""
    prompt: str
    generation_type: GenerationType = GenerationType.SINGLE_COMPONENT
    framework: Optional[str] = None
    styling: Optional[str] = None
    component_library: Optional[str] = None
    output_path: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def with_context(self, **kwargs) -> 'GenerationRequest':
        """Create a new request with additional context."""
        new_context = self.context.copy() if self.context else {}
        new_context.update(kwargs)
        return GenerationRequest(
            prompt=self.prompt,
            generation_type=self.generation_type,
            framework=self.framework,
            styling=self.styling,
            component_library=self.component_library,
            output_path=self.output_path,
            context=new_context
        )


@dataclass
class GeneratedFile:
    """A single generated file."""
    path: str
    content: str
    file_type: str  # 'component', 'test', 'style', 'type', etc.
    description: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of component generation."""
    files: List[GeneratedFile]
    main_component: Optional[str] = None  # Path to main component
    imports_used: List[str] = field(default_factory=list)
    components_reused: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_main_content(self) -> Optional[str]:
        """Get the content of the main component file."""
        if not self.main_component:
            return self.files[0].content if self.files else None
        
        for file in self.files:
            if file.path == self.main_component:
                return file.content
        return None
    
    def add_file(self, path: str, content: str, file_type: str = "component"):
        """Add a generated file to the result."""
        self.files.append(GeneratedFile(path, content, file_type))


class IGenerator(ABC):
    """
    Abstract interface for component generators.
    Generates React components based on prompts and project context.
    """
    
    @abstractmethod
    def generate(self, request: GenerationRequest, analysis: AnalysisResult) -> GenerationResult:
        """
        Generate components based on the request and project analysis.
        
        Args:
            request: Generation request with prompt and options
            analysis: Project analysis result
            
        Returns:
            GenerationResult with generated files and metadata
        """
        pass
    
    @abstractmethod
    def generate_with_intelligence(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate components using full intelligence pipeline.
        Includes intent analysis, asset management, and component mapping.
        
        Args:
            request: Generation request
            
        Returns:
            GenerationResult with enhanced generation
        """
        pass
    
    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """
        Check if the generator supports a specific model.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3')
            
        Returns:
            True if the model is supported
        """
        pass


class IPromptBuilder(ABC):
    """
    Abstract interface for prompt builders.
    Builds prompts for LLM-based generation.
    """
    
    @abstractmethod
    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build the system prompt for the LLM.
        
        Args:
            context: Project context and configuration
            
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    def build_user_prompt(self, request: GenerationRequest, analysis: AnalysisResult) -> str:
        """
        Build the user prompt for component generation.
        
        Args:
            request: Generation request
            analysis: Project analysis result
            
        Returns:
            User prompt string
        """
        pass
    
    @abstractmethod
    def build_few_shot_examples(self, request: GenerationRequest, analysis: AnalysisResult) -> str:
        """
        Build few-shot examples for better generation.
        
        Args:
            request: Generation request
            analysis: Project analysis result
            
        Returns:
            Few-shot examples string
        """
        pass