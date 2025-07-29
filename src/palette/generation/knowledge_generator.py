"""
Enhanced UI Generator using OpenAI File Search knowledge base.
Replaces the complex MCP architecture with a simpler, more reliable approach.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .generator import UIGenerator
from ..knowledge import PaletteKnowledgeBase, KnowledgeEnhancedGenerator
from ..quality import QualityReport


class KnowledgeUIGenerator(UIGenerator):
    """UI Generator enhanced with File Search knowledge base."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.knowledge_base = None
        self.knowledge_generator = None
        self._setup_knowledge_base()
    
    def _setup_knowledge_base(self):
        """Set up the knowledge base system."""
        try:
            # Check if OpenAI API key is available
            if not os.getenv("OPENAI_API_KEY"):
                print("⚠️ OpenAI API key not found, knowledge enhancement disabled")
                return
            
            print("🧠 Initializing knowledge base...")
            self.knowledge_base = PaletteKnowledgeBase()
            self.knowledge_generator = KnowledgeEnhancedGenerator(self.knowledge_base)
            
            # Ensure core knowledge base exists
            self.knowledge_base.create_core_knowledge_base()
            print("✅ Knowledge base ready")
            
        except Exception as e:
            print(f"⚠️ Knowledge base initialization failed: {e}")
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
                "knowledge_bases": []
            }
        
        try:
            bases = self.knowledge_base.get_available_knowledge_bases()
            return {
                "available": True,
                "knowledge_bases": bases,
                "total_bases": len(bases),
                "active_bases": len([b for b in bases if b["status"] == "active"])
            }
        except Exception as e:
            return {
                "available": False,
                "reason": str(e),
                "knowledge_bases": []
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