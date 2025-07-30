"""
Enhanced UI Generator using local knowledge base.
Fast, unlimited semantic search without rate limits or API dependencies.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .generator import UIGenerator
from ..knowledge import (
    LocalKnowledgeBase,
    LocalKnowledgeEnhancedGenerator,
    HAS_LOCAL_KNOWLEDGE
)
from ..quality import QualityReport


class KnowledgeUIGenerator(UIGenerator):
    """UI Generator enhanced with local knowledge base."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_base = None
        self.knowledge_generator = None
        self._setup_knowledge_base()
    
    def _setup_knowledge_base(self):
        """Set up the local knowledge base system."""
        if HAS_LOCAL_KNOWLEDGE:
            try:
                print("🧠 Initializing local knowledge base...")
                self.knowledge_base = LocalKnowledgeBase()
                self.knowledge_generator = LocalKnowledgeEnhancedGenerator(self.knowledge_base)
                print("✅ Local knowledge base ready (no rate limits)")
                return
            except Exception as e:
                print(f"⚠️ Local knowledge base failed: {e}")
        
        # No knowledge enhancement available
        print("⚠️ Local knowledge base not available")
        print("   Install dependencies: pip install sentence-transformers faiss-cpu numpy")
        self.knowledge_base = None
        self.knowledge_generator = None
    
    def generate_component_with_qa(
        self, 
        prompt: str, 
        context: Dict, 
        target_path: str = None
    ) -> Tuple[str, QualityReport]:
        """Generate component with knowledge base enhancement."""
        
        if self.knowledge_generator:
            print("🎨 Generating component with knowledge enhancement...")
            
            # Enhance prompt with knowledge base
            try:
                enhanced_prompt, citations = self.knowledge_generator.enhance_prompt_with_knowledge(
                    prompt, context
                )
                
                if citations:
                    print(f"📚 Using knowledge from {len(citations)} sources")
                
                # Use enhanced prompt for generation
                prompt = enhanced_prompt
                
            except Exception as e:
                print(f"⚠️ Knowledge enhancement failed, using original prompt: {e}")
        else:
            print("🎨 Generating component with traditional approach...")
        
        # Continue with standard QA process
        return super().generate_component_with_qa(prompt, context, target_path)
    
    def generate_component(self, prompt: str, context: Dict) -> str:
        """Generate component with optional knowledge enhancement."""
        
        if self.knowledge_generator:
            try:
                # Enhance prompt with knowledge
                enhanced_prompt, citations = self.knowledge_generator.enhance_prompt_with_knowledge(
                    prompt, context
                )
                
                # Use enhanced prompt
                prompt = enhanced_prompt
                
            except Exception as e:
                print(f"⚠️ Knowledge search failed: {e}")
        
        # Generate with enhanced (or original) prompt
        return super().generate_component(prompt, context)
    
    def get_knowledge_status(self) -> Dict[str, Any]:
        """Get status of the local knowledge base system."""
        if not self.knowledge_base:
            return {
                "available": False,
                "reason": "Local knowledge base not initialized",
                "type": "none"
            }
        
        # Local knowledge base status
        return {
            "available": True,
            "type": "local",
            "rate_limits": False,
            **self.knowledge_base.get_stats()
        }
    
    def create_project_knowledge_base(self) -> Optional[str]:
        """Create a knowledge base for the current project (local only)."""
        if not self.knowledge_base or not self.project_path:
            return None
        
        # Note: Local knowledge base doesn't support project-specific creation yet
        # This would need to be implemented to analyze project files and add them
        print("⚠️ Project-specific knowledge base creation not yet implemented for local knowledge base")
        return None