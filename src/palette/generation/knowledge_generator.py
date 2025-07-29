"""
Enhanced UI Generator using OpenAI File Search knowledge base.
Replaces the complex MCP architecture with a simpler, more reliable approach.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .generator import UIGenerator
from ..knowledge import (
    PaletteKnowledgeBase, 
    KnowledgeEnhancedGenerator,
    LocalKnowledgeBase,
    LocalKnowledgeEnhancedGenerator,
    HAS_LOCAL_KNOWLEDGE
)
from ..quality import QualityReport


class KnowledgeUIGenerator(UIGenerator):
    """UI Generator enhanced with File Search knowledge base."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_base = None
        self.knowledge_generator = None
        self._setup_knowledge_base()
    
    def _setup_knowledge_base(self):
        """Set up the knowledge base system with local-first approach."""
        # Try local knowledge base first (no rate limits, faster)
        if HAS_LOCAL_KNOWLEDGE:
            try:
                print("🧠 Initializing local knowledge base...")
                self.knowledge_base = LocalKnowledgeBase()
                self.knowledge_generator = LocalKnowledgeEnhancedGenerator(self.knowledge_base)
                print("✅ Local knowledge base ready (no rate limits)")
                return
            except Exception as e:
                print(f"⚠️ Local knowledge base failed: {e}")
        
        # Fallback to OpenAI File Search if local not available
        if os.getenv("OPENAI_API_KEY"):
            try:
                print("🌐 Falling back to OpenAI File Search knowledge base...")
                self.knowledge_base = PaletteKnowledgeBase()
                self.knowledge_generator = KnowledgeEnhancedGenerator(self.knowledge_base)
                
                # Ensure core knowledge base exists
                self.knowledge_base.create_core_knowledge_base()
                print("✅ Remote knowledge base ready (rate limited)")
                return
            except Exception as e:
                print(f"⚠️ Remote knowledge base failed: {e}")
        
        # No knowledge enhancement available
        print("⚠️ No knowledge base available - install dependencies or set OPENAI_API_KEY")
        print("   Install local knowledge: pip install sentence-transformers faiss-cpu")
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
        """Get status of the knowledge base system."""
        if not self.knowledge_base:
            return {
                "available": False,
                "reason": "Knowledge base not initialized",
                "type": "none"
            }
        
        # Local knowledge base
        if isinstance(self.knowledge_base, LocalKnowledgeBase):
            return {
                "available": True,
                "type": "local",
                "rate_limits": False,
                **self.knowledge_base.get_stats()
            }
        
        # Remote knowledge base (OpenAI File Search)
        try:
            bases = self.knowledge_base.get_available_knowledge_bases()
            return {
                "available": True,
                "type": "remote",
                "rate_limits": True,
                "knowledge_bases": bases,
                "total_bases": len(bases),
                "active_bases": len([b for b in bases if b["status"] == "active"])
            }
        except Exception as e:
            return {
                "available": False,
                "type": "remote",
                "reason": str(e)
            }
    
    def create_project_knowledge_base(self) -> Optional[str]:
        """Create a knowledge base for the current project."""
        if not self.knowledge_base or not self.project_path:
            return None
        
        try:
            return self.knowledge_base.create_project_knowledge_base(self.project_path)
        except Exception as e:
            print(f"⚠️ Failed to create project knowledge base: {e}")
            return None