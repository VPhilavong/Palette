"""
OpenAI File Search integration for Palette knowledge base.
Replaces the complex MCP architecture with a simpler, more reliable approach.
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class PaletteKnowledgeBase:
    """Manages knowledge base using OpenAI File Search."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.vector_stores: Dict[str, str] = {}  # name -> vector_store_id
        self.config_path = Path.home() / ".palette" / "knowledge_base.json"
        self._load_config()
    
    def _load_config(self):
        """Load existing vector store configurations."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.vector_stores = config.get('vector_stores', {})
            except Exception as e:
                logger.warning(f"Failed to load knowledge base config: {e}")
    
    def _save_config(self):
        """Save vector store configurations."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        config = {
            'vector_stores': self.vector_stores,
            'created_at': str(Path(__file__).stat().st_mtime)
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def create_core_knowledge_base(self) -> str:
        """Create the core knowledge base with fundamental patterns."""
        if 'core' in self.vector_stores:
            logger.info(f"Core knowledge base already exists: {self.vector_stores['core']}")
            return self.vector_stores['core']
        
        print("🧠 Creating core knowledge base...")
        
        # Create vector store
        vector_store = self.client.vector_stores.create(
            name="palette_core_knowledge"
        )
        
        # Knowledge sources to include
        knowledge_sources = [
            {
                "url": "https://react.dev/reference/react",
                "description": "React Documentation - Components and Hooks"
            },
            {
                "url": "https://tailwindcss.com/docs",
                "description": "Tailwind CSS Documentation"
            },
            {
                "url": "https://web.dev/accessibility/",
                "description": "Web Accessibility Guidelines"
            }
        ]
        
        # For now, we'll create the structure and add files later
        # In a real implementation, you'd upload actual documentation files
        
        self.vector_stores['core'] = vector_store.id
        self._save_config()
        
        print(f"✅ Core knowledge base created: {vector_store.id}")
        return vector_store.id
    
    def search_knowledge(
        self, 
        query: str, 
        context: Dict[str, Any],
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search the knowledge base for relevant information."""
        
        # Enhance query with context
        enhanced_query = self._enhance_query_with_context(query, context)
        
        try:
            # Use core knowledge base if available
            vector_store_id = self.vector_stores.get('core')
            if not vector_store_id:
                logger.warning("No knowledge base available, creating core knowledge base")
                vector_store_id = self.create_core_knowledge_base()
            
            # Search using OpenAI File Search
            response = self.client.responses.create(
                model="gpt-4o-mini",
                input=enhanced_query,
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [vector_store_id],
                    "max_num_results": max_results
                }],
                include=["file_search_call.results"]
            )
            
            return self._process_search_response(response)
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "knowledge": [],
                "citations": []
            }
    
    def _enhance_query_with_context(self, query: str, context: Dict[str, Any]) -> str:
        """Enhance the search query with project context."""
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'css')
        component_library = context.get('component_library', 'none')
        
        enhanced_query = f"""
        {query}
        
        Context:
        - Framework: {framework}
        - Styling: {styling}
        - Component Library: {component_library}
        - TypeScript: {context.get('typescript', True)}
        
        Focus on best practices, accessibility, and modern patterns.
        """
        
        return enhanced_query.strip()
    
    def _process_search_response(self, response) -> Dict[str, Any]:
        """Process the File Search response into a usable format."""
        result = {
            "success": True,
            "knowledge": [],
            "citations": [],
            "raw_response": response
        }
        
        # Extract search results and citations
        for output in response.output:
            if output.type == "file_search_call":
                # Handle search results if available
                if hasattr(output, 'search_results') and output.search_results:
                    for search_result in output.search_results:
                        result["knowledge"].append({
                            "content": search_result.content,
                            "score": getattr(search_result, 'score', 0),
                            "file_id": getattr(search_result, 'file_id', None)
                        })
            
            elif output.type == "message":
                # Extract knowledge from the response
                for content in output.content:
                    if content.type == "output_text":
                        result["knowledge"].append({
                            "content": content.text,
                            "type": "generated_knowledge"
                        })
                        
                        # Extract citations
                        if hasattr(content, 'annotations'):
                            for annotation in content.annotations:
                                if annotation.type == "file_citation":
                                    result["citations"].append({
                                        "file_id": annotation.file_id,
                                        "filename": getattr(annotation, 'filename', 'unknown'),
                                        "index": annotation.index
                                    })
        
        return result
    
    def create_project_knowledge_base(self, project_path: str) -> str:
        """Create a project-specific knowledge base."""
        project_name = Path(project_path).name
        kb_name = f"project_{project_name}"
        
        if kb_name in self.vector_stores:
            return self.vector_stores[kb_name]
        
        print(f"📁 Creating knowledge base for project: {project_name}")
        
        # Create vector store for this project
        vector_store = self.client.vector_stores.create(
            name=f"palette_project_{project_name}"
        )
        
        # TODO: Upload relevant project files
        # - README.md
        # - Design system files
        # - Existing components
        # - Style guides
        
        self.vector_stores[kb_name] = vector_store.id
        self._save_config()
        
        return vector_store.id
    
    def get_available_knowledge_bases(self) -> List[Dict[str, str]]:
        """Get list of available knowledge bases."""
        bases = []
        for name, vector_store_id in self.vector_stores.items():
            try:
                # Verify the vector store still exists
                vs = self.client.vector_stores.retrieve(vector_store_id)
                bases.append({
                    "name": name,
                    "id": vector_store_id,
                    "display_name": vs.name,
                    "status": "active"
                })
            except Exception as e:
                logger.warning(f"Vector store {name} ({vector_store_id}) is invalid: {e}")
                bases.append({
                    "name": name,
                    "id": vector_store_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return bases


class KnowledgeEnhancedGenerator:
    """Generator that uses knowledge base to enhance component generation."""
    
    def __init__(self, knowledge_base: PaletteKnowledgeBase):
        self.kb = knowledge_base
    
    def enhance_prompt_with_knowledge(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> tuple[str, List[Dict]]:
        """Enhance generation prompt with relevant knowledge."""
        
        print("📚 Searching knowledge base for best practices...")
        
        # Search for relevant patterns
        search_result = self.kb.search_knowledge(
            query=f"Best practices and patterns for: {prompt}",
            context=context,
            max_results=3
        )
        
        if not search_result["success"]:
            logger.warning(f"Knowledge search failed: {search_result.get('error')}")
            return prompt, []
        
        # Build enhanced prompt
        knowledge_sections = []
        citations = search_result.get("citations", [])
        
        for knowledge in search_result.get("knowledge", []):
            if knowledge.get("content"):
                knowledge_sections.append(knowledge["content"])
        
        if knowledge_sections:
            enhanced_prompt = f"""
            {prompt}
            
            RELEVANT KNOWLEDGE AND BEST PRACTICES:
            {chr(10).join(f"- {section}" for section in knowledge_sections[:3])}
            
            Please incorporate these best practices into the generated component.
            """
            
            print(f"✅ Enhanced prompt with {len(knowledge_sections)} knowledge sources")
            return enhanced_prompt.strip(), citations
        else:
            print("⚠️ No relevant knowledge found, using original prompt")
            return prompt, []