"""
Advanced Context Manager for optimizing LLM context window usage.
Implements token-aware prioritization, hierarchical loading, and context compression.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..errors import GenerationError
from ..errors.decorators import handle_errors


class ContextPriority(Enum):
    """Context priority levels for token budget allocation."""
    
    CRITICAL = "critical"        # Must include (core requirements, user request)
    HIGH = "high"               # Very important (design tokens, framework patterns)
    MEDIUM = "medium"           # Important (component examples, project structure)
    LOW = "low"                 # Nice to have (extended documentation, additional examples)


class ContextType(Enum):
    """Types of context information."""
    
    USER_REQUEST = "user_request"
    DESIGN_TOKENS = "design_tokens"
    FRAMEWORK_PATTERNS = "framework_patterns"
    COMPONENT_EXAMPLES = "component_examples"
    PROJECT_STRUCTURE = "project_structure"
    AVAILABLE_IMPORTS = "available_imports"
    QUALITY_REQUIREMENTS = "quality_requirements"
    ACCESSIBILITY_GUIDELINES = "accessibility_guidelines"
    PERFORMANCE_HINTS = "performance_hints"


@dataclass
class ContextChunk:
    """A chunk of context with metadata for prioritization."""
    
    content: str
    context_type: ContextType
    priority: ContextPriority
    token_estimate: int
    relevance_score: float = 0.0
    compression_ratio: float = 1.0  # How much this can be compressed (1.0 = no compression)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.token_estimate == 0:
            self.token_estimate = self._estimate_tokens(self.content)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters for English)."""
        return max(1, len(text) // 4)


@dataclass
class ContextBudget:
    """Token budget allocation for different context types."""
    
    total_tokens: int
    system_prompt_tokens: int
    user_prompt_tokens: int
    reserved_tokens: int = 500  # Reserve for response
    
    @property
    def available_tokens(self) -> int:
        return self.total_tokens - self.reserved_tokens
    
    @property
    def context_tokens(self) -> int:
        return self.available_tokens - self.system_prompt_tokens - self.user_prompt_tokens


class ContextCompressor(ABC):
    """Base class for context compression strategies."""
    
    @abstractmethod
    def compress(self, content: str, target_ratio: float) -> str:
        """Compress content to target ratio of original size."""
        pass
    
    @abstractmethod
    def get_compression_ratio(self, content: str) -> float:
        """Get maximum compression ratio possible for this content."""
        pass


class SemanticCompressor(ContextCompressor):
    """Semantic compression that preserves meaning while reducing tokens."""
    
    def compress(self, content: str, target_ratio: float) -> str:
        """Compress content semantically while preserving key information."""
        if target_ratio >= 1.0:
            return content
        
        # Extract key information types
        if self._is_component_example(content):
            return self._compress_component_example(content, target_ratio)
        elif self._is_design_tokens(content):
            return self._compress_design_tokens(content, target_ratio)
        elif self._is_project_structure(content):
            return self._compress_project_structure(content, target_ratio)
        else:
            return self._generic_compression(content, target_ratio)
    
    def get_compression_ratio(self, content: str) -> float:
        """Estimate maximum compression ratio."""
        if self._is_component_example(content):
            return 0.3  # Can compress heavily by keeping just key patterns
        elif self._is_design_tokens(content):
            return 0.5  # Moderate compression by summarizing
        elif self._is_project_structure(content):
            return 0.4  # Good compression by keeping essential info
        else:
            return 0.7  # Conservative generic compression
    
    def _is_component_example(self, content: str) -> bool:
        """Check if content is a component example."""
        return any(pattern in content for pattern in ['import React', 'export default', 'const ', 'function '])
    
    def _is_design_tokens(self, content: str) -> bool:
        """Check if content is design tokens."""
        return any(pattern in content for pattern in ['colors:', 'spacing:', 'typography:', 'Colors:', 'Spacing:'])
    
    def _is_project_structure(self, content: str) -> bool:
        """Check if content is project structure info."""
        return any(pattern in content for pattern in ['Framework:', 'Styling:', 'Components found:', 'package.json'])
    
    def _compress_component_example(self, content: str, target_ratio: float) -> str:
        """Compress component examples by keeping essential patterns."""
        lines = content.split('\n')
        
        # Always keep imports, interface definitions, and component signature
        essential_lines = []
        in_component = False
        brace_count = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Keep imports
            if stripped.startswith('import '):
                essential_lines.append(line)
                continue
            
            # Keep interface/type definitions
            if stripped.startswith(('interface ', 'type ')):
                essential_lines.append(line)
                continue
            
            # Keep component signature
            if ('const ' in line and '=' in line and '=>' in line) or stripped.startswith('function '):
                in_component = True
                essential_lines.append(line)
                continue
            
            # Keep return statement and first few lines of JSX
            if in_component and 'return' in stripped:
                essential_lines.append(line)
                # Add a few more lines of JSX structure
                continue
            
            # Keep export statements
            if stripped.startswith('export '):
                essential_lines.append(line)
                continue
        
        compressed = '\n'.join(essential_lines)
        
        # If still too long, further reduce
        if len(compressed) > len(content) * target_ratio:
            # Keep only the most essential parts
            essential_parts = [line for line in essential_lines if any(pattern in line for pattern in [
                'import ', 'interface ', 'const ', 'return', 'export'
            ])]
            compressed = '\n'.join(essential_parts[:10])  # Limit to 10 most essential lines
        
        return compressed + '\n// ... (abbreviated)'
    
    def _compress_design_tokens(self, content: str, target_ratio: float) -> str:
        """Compress design tokens by summarizing."""
        lines = content.split('\n')
        compressed_lines = []
        
        for line in lines:
            if ':' in line:
                # Keep key-value pairs but truncate long lists
                key, value = line.split(':', 1)
                if ',' in value and len(value) > 50:
                    # Truncate long lists
                    items = value.split(',')
                    if len(items) > 5:
                        value = ', '.join(items[:5]) + f', ... ({len(items)} total)'
                compressed_lines.append(f"{key}:{value}")
            else:
                compressed_lines.append(line)
        
        return '\n'.join(compressed_lines)
    
    def _compress_project_structure(self, content: str, target_ratio: float) -> str:
        """Compress project structure by keeping essential info."""
        lines = content.split('\n')
        essential_lines = []
        
        for line in lines:
            # Keep framework, styling, and key configuration info
            if any(pattern in line for pattern in ['Framework:', 'Styling:', 'TypeScript:', 'Components:', 'Key features:']):
                essential_lines.append(line)
            # Keep first few components
            elif line.strip().startswith('- ') and len(essential_lines) < 20:
                essential_lines.append(line)
        
        return '\n'.join(essential_lines)
    
    def _generic_compression(self, content: str, target_ratio: float) -> str:
        """Generic compression for unknown content types."""
        lines = content.split('\n')
        target_lines = int(len(lines) * target_ratio)
        
        # Keep first and last portions, skip middle
        if target_lines < 10:
            return '\n'.join(lines[:target_lines])
        else:
            first_part = lines[:target_lines//2]
            last_part = lines[-(target_lines//2):]
            return '\n'.join(first_part + ['... (content abbreviated) ...'] + last_part)


class HierarchicalContextLoader:
    """Loads context in hierarchical layers based on priority and relevance."""
    
    def __init__(self, compressor: ContextCompressor = None):
        self.compressor = compressor or SemanticCompressor()
        self.relevance_analyzer = RelevanceAnalyzer()
    
    def load_context_hierarchically(
        self, 
        context_chunks: List[ContextChunk],
        budget: ContextBudget,
        user_request: str
    ) -> Tuple[List[ContextChunk], Dict[str, Any]]:
        """
        Load context hierarchically within token budget.
        
        Returns:
            Tuple of (selected_chunks, loading_stats)
        """
        # Calculate relevance scores
        for chunk in context_chunks:
            chunk.relevance_score = self.relevance_analyzer.calculate_relevance(
                chunk, user_request
            )
        
        # Sort by priority first, then relevance
        priority_order = [ContextPriority.CRITICAL, ContextPriority.HIGH, ContextPriority.MEDIUM, ContextPriority.LOW]
        sorted_chunks = sorted(
            context_chunks,
            key=lambda x: (priority_order.index(x.priority), -x.relevance_score)
        )
        
        # Load context within budget
        selected_chunks = []
        used_tokens = 0
        compression_applied = 0
        
        for chunk in sorted_chunks:
            if used_tokens + chunk.token_estimate <= budget.context_tokens:
                # Can fit without compression
                selected_chunks.append(chunk)
                used_tokens += chunk.token_estimate
            else:
                # Try compression
                available_tokens = budget.context_tokens - used_tokens
                if available_tokens > 0:
                    max_compression = self.compressor.get_compression_ratio(chunk.content)
                    required_ratio = available_tokens / chunk.token_estimate
                    
                    if required_ratio >= max_compression:
                        # Can compress and fit
                        compressed_content = self.compressor.compress(chunk.content, required_ratio)
                        compressed_chunk = ContextChunk(
                            content=compressed_content,
                            context_type=chunk.context_type,
                            priority=chunk.priority,
                            token_estimate=available_tokens,
                            relevance_score=chunk.relevance_score,
                            compression_ratio=required_ratio,
                            metadata={**chunk.metadata, 'compressed': True}
                        )
                        selected_chunks.append(compressed_chunk)
                        used_tokens += available_tokens
                        compression_applied += 1
                        break
        
        loading_stats = {
            'total_chunks': len(context_chunks),
            'selected_chunks': len(selected_chunks),
            'used_tokens': used_tokens,
            'available_tokens': budget.context_tokens,
            'utilization': used_tokens / budget.context_tokens,
            'compression_applied': compression_applied
        }
        
        return selected_chunks, loading_stats


class RelevanceAnalyzer:
    """Analyzes the relevance of context chunks to the user request."""
    
    def calculate_relevance(self, chunk: ContextChunk, user_request: str) -> float:
        """Calculate relevance score (0.0 to 1.0) for a context chunk."""
        request_lower = user_request.lower()
        content_lower = chunk.content.lower()
        
        # Base score by context type
        type_scores = {
            ContextType.USER_REQUEST: 1.0,
            ContextType.DESIGN_TOKENS: 0.8,
            ContextType.FRAMEWORK_PATTERNS: 0.8,
            ContextType.COMPONENT_EXAMPLES: 0.9,
            ContextType.PROJECT_STRUCTURE: 0.7,
            ContextType.AVAILABLE_IMPORTS: 0.6,
            ContextType.QUALITY_REQUIREMENTS: 0.5,
            ContextType.ACCESSIBILITY_GUIDELINES: 0.4,
            ContextType.PERFORMANCE_HINTS: 0.3
        }
        
        base_score = type_scores.get(chunk.context_type, 0.5)
        
        # Keyword matching
        request_keywords = self._extract_keywords(request_lower)
        content_keywords = self._extract_keywords(content_lower)
        
        if request_keywords and content_keywords:
            keyword_overlap = len(request_keywords.intersection(content_keywords))
            total_keywords = len(request_keywords.union(content_keywords))
            keyword_score = keyword_overlap / total_keywords if total_keywords > 0 else 0
        else:
            keyword_score = 0
        
        # Component type matching
        component_score = self._calculate_component_type_relevance(request_lower, content_lower)
        
        # Combine scores
        relevance = (base_score * 0.5) + (keyword_score * 0.3) + (component_score * 0.2)
        
        return min(1.0, relevance)
    
    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # Remove common code artifacts and get words
        text = re.sub(r'[{}();,.\'":]', ' ', text)
        words = set(text.split())
        
        # Filter for meaningful keywords
        meaningful_words = set()
        ui_terms = {
            'button', 'card', 'modal', 'form', 'input', 'select', 'table',
            'navbar', 'sidebar', 'dropdown', 'tooltip', 'dialog', 'alert',
            'spinner', 'loader', 'badge', 'avatar', 'tabs', 'accordion'
        }
        
        for word in words:
            if word in ui_terms or (len(word) > 3 and word not in {
                'const', 'return', 'import', 'export', 'function', 'interface'
            }):
                meaningful_words.add(word)
        
        return meaningful_words
    
    def _calculate_component_type_relevance(self, request: str, content: str) -> float:
        """Calculate relevance based on component type matching."""
        component_types = {
            'button': ['button', 'btn', 'click', 'action'],
            'form': ['form', 'input', 'field', 'validation'],
            'card': ['card', 'panel', 'container'],
            'modal': ['modal', 'dialog', 'popup'],
            'table': ['table', 'list', 'data', 'grid'],
            'navigation': ['nav', 'menu', 'sidebar', 'header']
        }
        
        request_types = set()
        content_types = set()
        
        for comp_type, keywords in component_types.items():
            if any(keyword in request for keyword in keywords):
                request_types.add(comp_type)
            if any(keyword in content for keyword in keywords):
                content_types.add(comp_type)
        
        if request_types and content_types:
            overlap = len(request_types.intersection(content_types))
            total = len(request_types.union(content_types))
            return overlap / total
        
        return 0.0


class TokenAwareContextManager:
    """
    Main context manager that coordinates token-aware context optimization.
    """
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.hierarchical_loader = HierarchicalContextLoader()
        self.context_builder = ContextBuilder()
    
    @handle_errors(reraise=True)
    def optimize_context(
        self,
        user_request: str,
        project_context: Dict[str, Any],
        system_prompt_base: str,
        user_prompt_base: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Optimize context within token budget.
        
        Returns:
            Tuple of (optimized_system_prompt, optimized_user_prompt, optimization_stats)
        """
        # Estimate token usage for base prompts
        system_tokens = self._estimate_tokens(system_prompt_base)
        user_tokens = self._estimate_tokens(user_prompt_base)
        
        # Create budget
        budget = ContextBudget(
            total_tokens=self.max_tokens,
            system_prompt_tokens=system_tokens,
            user_prompt_tokens=user_tokens
        )
        
        # Build context chunks
        context_chunks = self.context_builder.build_context_chunks(project_context, user_request)
        
        # Load context hierarchically
        selected_chunks, loading_stats = self.hierarchical_loader.load_context_hierarchically(
            context_chunks, budget, user_request
        )
        
        # Build optimized prompts
        context_content = self._format_selected_chunks(selected_chunks)
        
        optimized_system_prompt = f"{system_prompt_base}\n\n{context_content}"
        optimized_user_prompt = user_prompt_base
        
        # Prepare optimization stats
        optimization_stats = {
            'token_budget': {
                'total': budget.total_tokens,
                'available': budget.available_tokens,
                'context_used': loading_stats['used_tokens'],
                'utilization': loading_stats['utilization']
            },
            'context_optimization': loading_stats,
            'chunks_by_type': self._get_chunks_by_type_stats(selected_chunks)
        }
        
        return optimized_system_prompt, optimized_user_prompt, optimization_stats
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return max(1, len(text) // 4)
    
    def _format_selected_chunks(self, chunks: List[ContextChunk]) -> str:
        """Format selected context chunks into a coherent context section."""
        if not chunks:
            return ""
        
        # Group chunks by type for better organization
        chunks_by_type = {}
        for chunk in chunks:
            chunk_type = chunk.context_type
            if chunk_type not in chunks_by_type:
                chunks_by_type[chunk_type] = []
            chunks_by_type[chunk_type].append(chunk)
        
        # Format each type section
        sections = []
        type_order = [
            ContextType.DESIGN_TOKENS,
            ContextType.FRAMEWORK_PATTERNS,
            ContextType.COMPONENT_EXAMPLES,
            ContextType.PROJECT_STRUCTURE,
            ContextType.AVAILABLE_IMPORTS
        ]
        
        for context_type in type_order:
            if context_type in chunks_by_type:
                type_chunks = chunks_by_type[context_type]
                section_content = '\n'.join(chunk.content for chunk in type_chunks)
                
                # Add section header
                type_name = context_type.value.replace('_', ' ').title()
                sections.append(f"{type_name}:\n{section_content}")
        
        return '\n\n'.join(sections)
    
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


class ContextBuilder:
    """Builds context chunks from project context."""
    
    def build_context_chunks(
        self, 
        project_context: Dict[str, Any], 
        user_request: str
    ) -> List[ContextChunk]:
        """Build context chunks from project context."""
        chunks = []
        
        # Design tokens
        if project_context.get('design_tokens'):
            content = self._format_design_tokens(project_context['design_tokens'])
            chunks.append(ContextChunk(
                content=content,
                context_type=ContextType.DESIGN_TOKENS,
                priority=ContextPriority.HIGH,
                token_estimate=0  # Will be calculated automatically
            ))
        
        # Framework patterns
        if project_context.get('framework'):
            content = self._format_framework_info(project_context)
            chunks.append(ContextChunk(
                content=content,
                context_type=ContextType.FRAMEWORK_PATTERNS,
                priority=ContextPriority.HIGH,
                token_estimate=0
            ))
        
        # Component examples
        if project_context.get('components'):
            for component in project_context['components'][:5]:  # Limit to 5 most relevant
                content = self._format_component_example(component)
                chunks.append(ContextChunk(
                    content=content,
                    context_type=ContextType.COMPONENT_EXAMPLES,
                    priority=ContextPriority.MEDIUM,
                    token_estimate=0,
                    metadata={'component_name': component.get('name', 'Unknown')}
                ))
        
        # Project structure
        if project_context.get('project_structure'):
            content = self._format_project_structure(project_context['project_structure'])
            chunks.append(ContextChunk(
                content=content,
                context_type=ContextType.PROJECT_STRUCTURE,
                priority=ContextPriority.MEDIUM,
                token_estimate=0
            ))
        
        return chunks
    
    def _format_design_tokens(self, design_tokens: Dict[str, Any]) -> str:
        """Format design tokens for context."""
        sections = []
        
        if design_tokens.get('colors'):
            colors = design_tokens['colors']
            if isinstance(colors, dict):
                color_list = ', '.join(list(colors.keys())[:10])
            else:
                color_list = ', '.join(colors[:10])
            sections.append(f"Colors: {color_list}")
        
        if design_tokens.get('spacing'):
            spacing = design_tokens['spacing']
            sections.append(f"Spacing: {', '.join(spacing) if isinstance(spacing, list) else 'Custom scale'}")
        
        if design_tokens.get('typography'):
            typography = design_tokens['typography']
            sections.append(f"Typography: {len(typography)} defined styles")
        
        return '\n'.join(sections)
    
    def _format_framework_info(self, project_context: Dict[str, Any]) -> str:
        """Format framework information."""
        framework = project_context.get('framework', 'React')
        styling = project_context.get('styling', 'CSS')
        typescript = project_context.get('typescript', False)
        
        return f"Framework: {framework}\nStyling: {styling}\nTypeScript: {typescript}"
    
    def _format_component_example(self, component: Dict[str, Any]) -> str:
        """Format component example."""
        name = component.get('name', 'Unknown')
        purpose = component.get('purpose', 'Component')
        props = component.get('props', [])
        
        props_summary = f"{len(props)} props" if props else "No props"
        
        return f"Component: {name}\nPurpose: {purpose}\nProps: {props_summary}"
    
    def _format_project_structure(self, structure: Dict[str, Any]) -> str:
        """Format project structure information."""
        return f"Project Structure: {structure.get('type', 'Standard React')}"