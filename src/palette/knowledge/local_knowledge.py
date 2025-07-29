"""
Local knowledge base using sentence transformers and FAISS for semantic search.
No API calls, no rate limits, fast local computation.
"""

import json
import pickle
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Try to import dependencies, with graceful fallback
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_LOCAL_KNOWLEDGE = True
except ImportError:
    HAS_LOCAL_KNOWLEDGE = False
    # Create mock numpy for graceful fallback
    class MockNumpy:
        def mean(self, data):
            return sum(data) / len(data) if data else 0
    np = MockNumpy()

logger = logging.getLogger(__name__)


class KnowledgeChunk:
    """Represents a chunk of knowledge with metadata."""
    
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata
        self.embedding = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeChunk':
        return cls(data["text"], data["metadata"])


class LocalKnowledgeBase:
    """Local semantic search knowledge base using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.index = None
        self.chunks: List[KnowledgeChunk] = []
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
        
        # Storage paths
        self.data_dir = Path.home() / ".palette" / "knowledge"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunks_file = self.data_dir / "chunks.json"
        self.index_file = self.data_dir / "faiss.index"
        
        if HAS_LOCAL_KNOWLEDGE:
            self._initialize()
        else:
            logger.warning("Local knowledge dependencies not installed. Install with: pip install sentence-transformers faiss-cpu")
    
    def _initialize(self):
        """Initialize the model and load existing data."""
        try:
            print("🧠 Initializing local knowledge base...")
            self.model = SentenceTransformer(self.model_name)
            
            # Create or load FAISS index
            if self.index_file.exists():
                self.index = faiss.read_index(str(self.index_file))
                print(f"✅ Loaded existing FAISS index with {self.index.ntotal} embeddings")
            else:
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
                print("✅ Created new FAISS index")
            
            # Load existing chunks
            if self.chunks_file.exists():
                with open(self.chunks_file, 'r') as f:
                    chunks_data = json.load(f)
                    self.chunks = [KnowledgeChunk.from_dict(chunk) for chunk in chunks_data]
                print(f"✅ Loaded {len(self.chunks)} knowledge chunks")
            
            # Initialize with core knowledge if empty
            if len(self.chunks) == 0:
                self._populate_core_knowledge()
                
        except Exception as e:
            logger.error(f"Failed to initialize local knowledge base: {e}")
            raise
    
    def _populate_core_knowledge(self):
        """Populate the knowledge base with core React/TypeScript/Tailwind patterns."""
        print("📚 Populating core knowledge base...")
        
        core_knowledge = [
            {
                "text": "React functional components should use TypeScript interfaces for props. Always define prop types explicitly. Example: interface ButtonProps { onClick: () => void; children: React.ReactNode; disabled?: boolean; }",
                "metadata": {"category": "react", "topic": "props", "framework": "react", "language": "typescript"}
            },
            {
                "text": "For form validation in React, use controlled components with useState for form state and validation state. Provide immediate feedback on validation errors. Use aria-invalid and aria-describedby for accessibility.",
                "metadata": {"category": "react", "topic": "forms", "framework": "react", "accessibility": True}
            },
            {
                "text": "Tailwind CSS button patterns: Use consistent padding (px-4 py-2), focus states (focus:ring-2 focus:ring-offset-2), and hover effects (hover:bg-opacity-90). Include disabled states with disabled:opacity-50 disabled:cursor-not-allowed.",
                "metadata": {"category": "tailwind", "topic": "buttons", "styling": "tailwind"}
            },
            {
                "text": "For accessibility, interactive elements must have proper ARIA labels, keyboard navigation support, and sufficient color contrast (4.5:1 for normal text). Use semantic HTML elements when possible.",
                "metadata": {"category": "accessibility", "topic": "general", "accessibility": True}
            },
            {
                "text": "Next.js App Router components should be async server components by default. Use 'use client' directive only when needed for interactivity. File-based routing: page.tsx for routes, layout.tsx for layouts.",
                "metadata": {"category": "nextjs", "topic": "routing", "framework": "next.js"}
            },
            {
                "text": "TypeScript React component best practices: Use React.FC sparingly, prefer function declarations, use proper event types (React.MouseEvent, React.ChangeEvent), and export interfaces separately from components.",
                "metadata": {"category": "typescript", "topic": "react", "framework": "react", "language": "typescript"}
            },
            {
                "text": "Loading states should be implemented with proper UX patterns: skeleton loaders for content, spinners for actions, and error boundaries for error handling. Use Suspense for data fetching.",
                "metadata": {"category": "react", "topic": "loading", "framework": "react", "ux": True}
            },
            {
                "text": "Tailwind responsive design: Use mobile-first approach with sm:, md:, lg:, xl: prefixes. Common breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px). Example: text-sm lg:text-base",
                "metadata": {"category": "tailwind", "topic": "responsive", "styling": "tailwind"}
            },
            {
                "text": "Form input validation patterns: Validate on blur for better UX, show success states, group related fields, use proper input types (email, tel, url), and provide clear error messages near the input.",
                "metadata": {"category": "forms", "topic": "validation", "ux": True, "accessibility": True}
            },
            {
                "text": "React hooks best practices: useEffect cleanup functions prevent memory leaks, useCallback for event handlers passed to children, useMemo for expensive calculations, custom hooks for reusable logic.",
                "metadata": {"category": "react", "topic": "hooks", "framework": "react", "performance": True}
            }
        ]
        
        for knowledge in core_knowledge:
            self.add_knowledge(knowledge["text"], knowledge["metadata"])
        
        print(f"✅ Added {len(core_knowledge)} core knowledge items")
    
    def add_knowledge(self, text: str, metadata: Dict[str, Any]) -> None:
        """Add a new piece of knowledge to the base."""
        if not HAS_LOCAL_KNOWLEDGE:
            logger.warning("Cannot add knowledge: dependencies not installed")
            return
        
        chunk = KnowledgeChunk(text, metadata)
        
        # Generate embedding
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        
        # Add to FAISS index
        self.index.add(embedding.reshape(1, -1))
        
        # Add to chunks list
        self.chunks.append(chunk)
        
        # Save to disk
        self._save_data()
    
    def search(
        self, 
        query: str, 
        k: int = 5, 
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Search for relevant knowledge chunks."""
        if not HAS_LOCAL_KNOWLEDGE or not self.model:
            logger.warning("Local knowledge search not available")
            return []
        
        if len(self.chunks) == 0:
            logger.warning("No knowledge chunks available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding.reshape(1, -1), min(k * 2, len(self.chunks)))
            
            # Get results with scores
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks):  # Valid index
                    chunk = self.chunks[idx]
                    
                    # Apply metadata filtering
                    if self._matches_filter(chunk.metadata, filter_metadata):
                        results.append((chunk, float(score)))
            
            # Sort by score (higher is better for inner product)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k results
            return results[:k]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Optional[Dict[str, Any]]) -> bool:
        """Check if metadata matches the filter criteria."""
        if not filter_metadata:
            return True
        
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        
        return True
    
    def _save_data(self):
        """Save chunks and index to disk."""
        try:
            # Save chunks as JSON
            chunks_data = [chunk.to_dict() for chunk in self.chunks]
            with open(self.chunks_file, 'w') as f:
                json.dump(chunks_data, f, indent=2)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        if not HAS_LOCAL_KNOWLEDGE:
            return {"available": False, "reason": "Dependencies not installed"}
        
        categories = {}
        frameworks = {}
        topics = {}
        
        for chunk in self.chunks:
            # Count categories
            category = chunk.metadata.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            # Count frameworks
            framework = chunk.metadata.get("framework")
            if framework:
                frameworks[framework] = frameworks.get(framework, 0) + 1
            
            # Count topics
            topic = chunk.metadata.get("topic")
            if topic:
                topics[topic] = topics.get(topic, 0) + 1
        
        return {
            "available": True,
            "total_chunks": len(self.chunks),
            "embedding_model": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "categories": categories,
            "frameworks": frameworks,
            "topics": topics,
            "storage_path": str(self.data_dir)
        }


class LocalKnowledgeEnhancedGenerator:
    """Generator that uses local knowledge base for prompt enhancement."""
    
    def __init__(self, knowledge_base: LocalKnowledgeBase):
        self.kb = knowledge_base
    
    def enhance_prompt_with_knowledge(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> Tuple[str, List[Dict]]:
        """Enhance generation prompt with relevant local knowledge."""
        
        if not HAS_LOCAL_KNOWLEDGE:
            logger.info("Local knowledge not available, using original prompt")
            return prompt, []
        
        print("📚 Searching local knowledge base...")
        
        # Create search query
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'css')
        search_query = f"{prompt} {framework} {styling} best practices"
        
        # Create filter based on context
        filter_metadata = {"framework": framework} if framework != "unknown" else None
        
        # Search for relevant knowledge
        results = self.kb.search(
            query=search_query,
            k=3,
            filter_metadata=filter_metadata
        )
        
        if not results:
            print("⚠️ No relevant knowledge found, using original prompt")
            return prompt, []
        
        # Build enhanced prompt
        knowledge_sections = []
        citations = []
        
        for chunk, score in results:
            knowledge_sections.append(chunk.text)
            citations.append({
                "text": chunk.text[:100] + "...",
                "metadata": chunk.metadata,
                "relevance_score": score
            })
        
        enhanced_prompt = f"""
        {prompt}
        
        RELEVANT BEST PRACTICES AND PATTERNS:
        {chr(10).join(f"- {section}" for section in knowledge_sections)}
        
        Please incorporate these best practices into the generated component while maintaining consistency with the project context.
        """
        
        print(f"✅ Enhanced prompt with {len(knowledge_sections)} knowledge sources (avg score: {np.mean([score for _, score in results]):.3f})")
        return enhanced_prompt.strip(), citations